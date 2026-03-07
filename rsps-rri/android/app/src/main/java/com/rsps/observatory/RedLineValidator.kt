package com.rsps.observatory

import android.app.Notification
import android.content.Context
import android.service.notification.StatusBarNotification
import android.util.Log

/**
 * RSPS Observatory — RedLine Validator
 *
 * The Hard Deck of the Recursive Sovereign Project Space.
 *
 * Defines the absolute boundary where automated enforcement yields to critical
 * reality: certain notifications bypass the epistemic membrane entirely,
 * regardless of current gating policy, IDS score, or operational mode.
 *
 * The RedLine is not a permission system. It is a recognition system.
 * It asks: does this signal represent something that the human *must*
 * encounter in real time, where the cost of membrane interception exceeds
 * any possible benefit of filtering?
 *
 * Architecture note: The RedLine validator intentionally contains hardcoded
 * logic for categories that should never be configurable at runtime:
 * emergency services, medical alerts, safety-critical communications.
 * The user can extend the configurable tier but cannot remove the hardcoded tier.
 *
 * The distinction matters philosophically: there are some signals where
 * sovereign filtering would be a category error — not an epistemic choice
 * but an abdication of reality contact. Mortal Asymmetry (χ=1) requires
 * these pass unconditionally.
 */
class RedLineValidator(private val context: Context) {

    companion object {
        private const val TAG = "RedLineValidator"

        // ─── TIER 1: HARDCODED — Never configurable ──────────────────────
        // These packages and categories represent unconditional bypass.
        // Removing any of these requires source code change, not settings.

        private val HARDCODED_BYPASS_PACKAGES = setOf(
            // Emergency services
            "com.android.phone",
            "com.google.android.dialer",
            // Medical alert apps (common ones)
            "com.epic.ehr",
            "org.medscape.android"
        )

        private val HARDCODED_BYPASS_CATEGORIES = setOf(
            Notification.CATEGORY_CALL,         // Incoming calls — always bypass
            Notification.CATEGORY_ALARM,        // Alarms — always bypass
            Notification.CATEGORY_REMINDER      // Reminders set by user intent
        )

        // ─── TIER 2: CONFIGURABLE — User-defined critical senders ────────
        // Populated from user preferences (contacts, apps the user designates).
        // Stored in SharedPreferences under key "redline_configured_packages"

        // ─── DEFAULT WEIGHTS by category ─────────────────────────────────
        val CATEGORY_WEIGHTS = mapOf(
            Notification.CATEGORY_MESSAGE to 1.5f,      // Direct messages — higher weight
            Notification.CATEGORY_SOCIAL to 1.0f,
            Notification.CATEGORY_EMAIL to 0.8f,
            Notification.CATEGORY_PROMO to 0.3f,        // Marketing — lower weight
            Notification.CATEGORY_SYS to 0.5f,
            null to 1.0f                                 // Unknown category — baseline
        )
    }

    /**
     * Evaluate a notification against RedLine criteria.
     *
     * @return RedLineResult indicating:
     *   - isCritical: bypass membrane entirely
     *   - shouldSuppress: remove from system tray while buffering
     *   - weight: cognitive load contribution to buffer
     *   - reason: human-readable explanation for ρ-archive logging
     */
    fun evaluate(sbn: StatusBarNotification, notification: Notification): RedLineResult {

        // Tier 1: Hardcoded bypass — unconditional
        if (sbn.packageName in HARDCODED_BYPASS_PACKAGES) {
            return RedLineResult(
                isCritical = true,
                shouldSuppress = false,
                weight = 0f,
                reason = "HARDCODED_PACKAGE: ${sbn.packageName}"
            )
        }

        if (notification.category in HARDCODED_BYPASS_CATEGORIES) {
            return RedLineResult(
                isCritical = true,
                shouldSuppress = false,
                weight = 0f,
                reason = "HARDCODED_CATEGORY: ${notification.category}"
            )
        }

        // Tier 2: Configured bypass — user-designated critical senders
        val configuredPackages = getConfiguredRedLinePackages()
        if (sbn.packageName in configuredPackages) {
            return RedLineResult(
                isCritical = true,
                shouldSuppress = false,
                weight = 0f,
                reason = "CONFIGURED_PACKAGE: ${sbn.packageName}"
            )
        }

        // Not critical — route to membrane buffer
        val weight = computeWeight(sbn, notification)
        val shouldSuppress = weight > 0.5f  // High-weight items get suppressed from tray

        Log.v(TAG, "Non-critical: ${sbn.packageName} | weight=$weight | suppress=$shouldSuppress")

        return RedLineResult(
            isCritical = false,
            shouldSuppress = shouldSuppress,
            weight = weight,
            reason = "BUFFERED: weight=$weight"
        )
    }

    private fun computeWeight(sbn: StatusBarNotification, notification: Notification): Float {
        // Base weight from category
        val categoryWeight = CATEGORY_WEIGHTS[notification.category] ?: 1.0f

        // Boost for ongoing notifications (persistent system state)
        val ongoingBoost = if (notification.flags and Notification.FLAG_ONGOING_EVENT != 0) 0.2f else 0f

        // Reduce for apps that are known low-signal
        val packagePenalty = if (isLowSignalPackage(sbn.packageName)) -0.4f else 0f

        return (categoryWeight + ongoingBoost + packagePenalty).coerceIn(0.1f, 3.0f)
    }

    private fun isLowSignalPackage(packageName: String): Boolean {
        // Packages known to be high-volume low-signal (marketing, news aggregators)
        val lowSignalPatterns = listOf("news", "daily", "promo", "ads", "buzz")
        return lowSignalPatterns.any { packageName.lowercase().contains(it) }
    }

    private fun getConfiguredRedLinePackages(): Set<String> {
        val prefs = context.getSharedPreferences("rsps_redline", Context.MODE_PRIVATE)
        return prefs.getStringSet("configured_packages", emptySet()) ?: emptySet()
    }

    fun addConfiguredPackage(packageName: String) {
        val prefs = context.getSharedPreferences("rsps_redline", Context.MODE_PRIVATE)
        val current = prefs.getStringSet("configured_packages", mutableSetOf())?.toMutableSet()
            ?: mutableSetOf()
        current.add(packageName)
        prefs.edit().putStringSet("configured_packages", current).apply()
        Log.i(TAG, "RedLine configured package added: $packageName")
    }
}

/**
 * Result of RedLine evaluation.
 */
data class RedLineResult(
    /** If true: notification bypasses membrane, reaches consciousness immediately */
    val isCritical: Boolean,
    /** If true AND !isCritical: cancel from system tray while holding in buffer */
    val shouldSuppress: Boolean,
    /** Cognitive load contribution to buffer weight computation */
    val weight: Float,
    /** Reason string for ρ-archive logging */
    val reason: String
)
