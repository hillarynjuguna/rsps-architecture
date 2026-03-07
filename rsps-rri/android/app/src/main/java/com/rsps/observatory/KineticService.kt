package com.rsps.observatory

import android.app.Notification
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.rsps.RSPSApplication
import com.rsps.nodes.RhoNode
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * RSPS Observatory — Kinetic Service
 *
 * The nervous system of the RSPS v4.3 epistemic membrane. Sits between
 * the Android OS notification stream and the user's attention, intercepting
 * every incoming notification and routing it through the RedLine gate.
 *
 * Two operational modes:
 *   - PASSIVE SONAR: Logs all traffic to the buffer without active enforcement
 *   - ACTIVE ENFORCEMENT: Applies RedLine validation; critical signals bypass,
 *     non-critical signals are held in the membrane buffer
 *
 * The metaphor that structures this: the system does not block notifications —
 * it *holds* them. Holding is different from blocking. The residue of what
 * was held, for how long, and with what cognitive load, becomes data.
 *
 * That data is the ρ-archive's raw material.
 */
class KineticService : NotificationListenerService() {

    companion object {
        private const val TAG = "KineticService"
        const val PASSIVE_SONAR = "PASSIVE_SONAR"
        const val ACTIVE_ENFORCEMENT = "ACTIVE_ENFORCEMENT"

        /**
         * Check if the NotificationListenerService is enabled in system settings.
         * Required before the service can intercept notifications.
         */
        fun isEnabled(context: Context): Boolean {
            val cn = ComponentName(context, KineticService::class.java)
            val flat = android.provider.Settings.Secure.getString(
                context.contentResolver,
                "enabled_notification_listeners"
            )
            return flat?.contains(cn.flattenToString()) == true
        }
    }

    // Coroutine scope tied to service lifecycle
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    // Access the Observatory database through the Application
    private val observatoryDb by lazy {
        ObservatoryDatabase.getInstance(applicationContext)
    }
    private val dao by lazy { observatoryDb.bufferedNotificationDao() }
    private val redLineValidator by lazy { RedLineValidator(applicationContext) }
    private val rhoNode by lazy {
        (application as RSPSApplication).rhoNode
    }

    // Operational mode — set via Intent or persisted preference
    private var operationalMode = ACTIVE_ENFORCEMENT

    // ─────────────────────────────────────────────────────────────────────
    // SERVICE LIFECYCLE
    // ─────────────────────────────────────────────────────────────────────

    override fun onListenerConnected() {
        super.onListenerConnected()
        Log.i(TAG, "KineticService connected — epistemic membrane ONLINE")
        rhoNode.logPhaseTransition(
            event = "KINETIC_SERVICE_CONNECTED",
            description = "Notification listener bound — membrane active"
        )
    }

    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        Log.w(TAG, "KineticService disconnected — epistemic membrane OFFLINE")
        rhoNode.logPhaseTransition(
            event = "KINETIC_SERVICE_DISCONNECTED",
            description = "Membrane offline — notification routing halted"
        )
    }

    // ─────────────────────────────────────────────────────────────────────
    // CORE INTERCEPTION LOGIC
    // ─────────────────────────────────────────────────────────────────────

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        // Never process our own notifications
        if (sbn.packageName == packageName) return

        serviceScope.launch {
            processIncomingNotification(sbn)
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // When a notification is dismissed from the system tray while buffered,
        // we keep our buffered copy — the dismissal might have been accidental.
        // User must explicitly dismiss from the Missed Summary.
        Log.v(TAG, "Notification removed from system: ${sbn.key} — buffer copy retained")
    }

    private suspend fun processIncomingNotification(sbn: StatusBarNotification) {
        val notification = sbn.notification ?: return

        // PASSIVE SONAR: just observe, don't intercept
        if (operationalMode == PASSIVE_SONAR) {
            logToBuffer(sbn, notification, bufferWeight = 0.1f) // low weight — observing only
            return
        }

        // ACTIVE ENFORCEMENT: RedLine check determines routing
        val redLineResult = redLineValidator.evaluate(sbn, notification)

        if (redLineResult.isCritical) {
            // Critical signal — bypass membrane entirely, pass to consciousness
            Log.d(TAG, "RedLine PASS: ${sbn.key} (${redLineResult.reason})")
            rhoNode.logMembraneEvent(
                type = "REDLINE_BYPASS",
                key = sbn.key,
                packageName = sbn.packageName
            )
            // Do NOT buffer — leave the notification as-is in the system tray
            return
        }

        // Non-critical: hold in the membrane buffer
        logToBuffer(sbn, notification, bufferWeight = redLineResult.weight)

        // In strict mode, cancel the notification from the system tray
        // so it doesn't fragment attention while the user is in flow
        if (redLineResult.shouldSuppress) {
            try {
                cancelNotification(sbn.key)
                Log.d(TAG, "Suppressed from tray: ${sbn.key} — held in buffer")
            } catch (e: Exception) {
                Log.w(TAG, "Could not suppress notification: ${e.message}")
            }
        }
    }

    private suspend fun logToBuffer(
        sbn: StatusBarNotification,
        notification: Notification,
        bufferWeight: Float
    ) {
        val extras = notification.extras
        val title = extras?.getString(Notification.EXTRA_TITLE)
        val text = extras?.getCharSequence(Notification.EXTRA_TEXT)?.toString()
            ?.take(512) // Truncate for storage

        val entity = BufferedNotificationEntity(
            sbnKey = sbn.key,
            packageName = sbn.packageName,
            title = title,
            text = text,
            interceptedAtTimestamp = System.currentTimeMillis(),
            bufferWeight = bufferWeight,
            category = notification.category
        )

        dao.bufferNotification(entity)
        Log.v(TAG, "Buffered: ${sbn.packageName} | weight=$bufferWeight")
    }

    // ─────────────────────────────────────────────────────────────────────
    // MODE CONTROL
    // ─────────────────────────────────────────────────────────────────────

    fun setMode(mode: String) {
        operationalMode = mode
        rhoNode.logPhaseTransition(
            event = "MODE_CHANGE",
            description = "KineticService mode → $mode"
        )
        Log.i(TAG, "Mode set to: $mode")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        intent?.getStringExtra("mode")?.let { setMode(it) }
        return START_STICKY
    }
}
