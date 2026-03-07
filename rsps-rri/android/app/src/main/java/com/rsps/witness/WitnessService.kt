package com.rsps.witness

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.rsps.RSPSApplication
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * RSPS Witness Infrastructure — Witness Service
 *
 * The attention recording layer of the cognitive metabolization system.
 *
 * The Observatory tells us what was held at the gate (epistemic membrane).
 * The Witness tells us what actually captured attention — and for how long.
 *
 * Architecture: Detects scroll pause events on monitored platforms
 * (TikTok, Instagram, YouTube Shorts, Twitter/X, LinkedIn) and logs
 * the pause signature — duration, platform, timestamp — to the local
 * SQLite Witness database. Nothing leaves the device.
 *
 * The pause signature is the raw behavioral signal from which the
 * IDS (Idea Development Score) will be computed by Gemma in Phase 2.
 *
 * What constitutes a "meaningful pause":
 *   - Duration > PAUSE_MIN_MS (default 1500ms): long enough to be intentional
 *   - Duration < PAUSE_MAX_MS (default 45_000ms): excludes phone-down events
 *   - Following a scroll event: captures genuine content engagement
 *   - Not during keyboard input: excludes typing pauses
 *
 * Phase 0 finding: Both Gemma 1B-IT and E2B models independently identified
 * "relational-intelligence" as the primary cognitive cluster from pause signatures.
 * This is why we record what you pause on, not what you type or tap.
 */
class WitnessService : AccessibilityService() {

    companion object {
        private const val TAG = "WitnessService"
        private const val PAUSE_MIN_MS = 1500L       // Minimum meaningful pause
        private const val PAUSE_MAX_MS = 45_000L     // Maximum before "phone down" territory
        private const val SESSION_GAP_MS = 300_000L  // 5 min gap = new session

        // Packages to monitor — content platforms with scroll feeds
        val MONITORED_PACKAGES = setOf(
            "com.zhiliaoapp.musically",    // TikTok
            "com.ss.android.ugc.trill",    // TikTok (alternate)
            "com.instagram.android",       // Instagram Reels / Feed
            "com.google.android.youtube",  // YouTube Shorts
            "com.twitter.android",         // X/Twitter
            "com.linkedin.android",        // LinkedIn Feed
            "com.reddit.frontpage"         // Reddit
        )
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val witnessDb by lazy { WitnessDatabase.getInstance(applicationContext) }
    private val witnessDao by lazy { witnessDb.witnessDao() }
    private val pauseDetector by lazy { PauseDetector() }
    private val rhoNode by lazy { (application as RSPSApplication).rhoNode }

    private var currentSessionId: String = generateSessionId()
    private var lastActivityTimestamp: Long = 0L

    // ─────────────────────────────────────────────────────────────────────
    // SERVICE LIFECYCLE
    // ─────────────────────────────────────────────────────────────────────

    override fun onServiceConnected() {
        super.onServiceConnected()
        configureAccessibilityService()
        Log.i(TAG, "WitnessService connected — attention recording ONLINE")
        rhoNode.logPhaseTransition(
            event = "WITNESS_SERVICE_CONNECTED",
            description = "Behavioral signal layer active — pause detection online"
        )
    }

    private fun configureAccessibilityService() {
        serviceInfo = AccessibilityServiceInfo().apply {
            // We want window content changes (scroll events) from monitored packages
            eventTypes = AccessibilityEvent.TYPE_VIEW_SCROLLED or
                    AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED or
                    AccessibilityEvent.TYPE_VIEW_FOCUSED

            packageNames = MONITORED_PACKAGES.toTypedArray()

            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC

            // Minimum interval between events from the same source
            notificationTimeout = 100L

            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // EVENT PROCESSING
    // ─────────────────────────────────────────────────────────────────────

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val packageName = event.packageName?.toString() ?: return
        if (packageName !in MONITORED_PACKAGES) return

        val now = System.currentTimeMillis()

        // Session management: gap > SESSION_GAP_MS = new session
        if (now - lastActivityTimestamp > SESSION_GAP_MS && lastActivityTimestamp > 0) {
            currentSessionId = generateSessionId()
            Log.d(TAG, "New session: $currentSessionId")
        }
        lastActivityTimestamp = now

        when (event.eventType) {
            AccessibilityEvent.TYPE_VIEW_SCROLLED -> {
                pauseDetector.onScrollEvent(packageName, now)
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                // Content change after scroll stop may indicate content loaded during pause
                pauseDetector.onContentChangeEvent(packageName, now)
            }
        }

        // Check if PauseDetector has completed a pause event
        pauseDetector.getPendingPauseEvent()?.let { pause ->
            recordPauseEvent(pause, packageName)
        }
    }

    private fun recordPauseEvent(pauseMs: Long, packageName: String) {
        serviceScope.launch {
            // Query current buffer weight from Observatory for cross-reference
            val bufferLoad = try {
                val observatoryDb = com.rsps.observatory.ObservatoryDatabase
                    .getInstance(applicationContext)
                observatoryDb.bufferedNotificationDao().getTotalBufferWeight()
            } catch (e: Exception) {
                null // Observable but non-critical — continue without buffer context
            }

            val event = PauseEvent(
                sessionId = currentSessionId,
                platformPackage = packageName,
                pauseDurationMs = pauseMs,
                timestampMs = System.currentTimeMillis(),
                bufferLoadAtPause = bufferLoad
            )

            witnessDao.insertPauseEvent(event)

            Log.v(TAG, "Pause recorded: ${pauseMs}ms on $packageName | bufferLoad=$bufferLoad")
        }
    }

    override fun onInterrupt() {
        Log.w(TAG, "WitnessService interrupted")
    }

    override fun onUnbind(intent: Intent?): Boolean {
        rhoNode.logPhaseTransition(
            event = "WITNESS_SERVICE_DISCONNECTED",
            description = "Behavioral signal layer offline"
        )
        return super.onUnbind(intent)
    }

    private fun generateSessionId(): String =
        "session_${System.currentTimeMillis()}_${(Math.random() * 10000).toInt()}"
}
