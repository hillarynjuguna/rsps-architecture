package com.rsps

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * RSPS Boot Receiver
 *
 * Ensures the cognitive infrastructure restarts when the device reboots.
 * The services themselves are Android system-managed and will restart
 * via BIND_ flags, but certain initialization logic (WorkManager re-schedule,
 * phase transition logging) needs an explicit trigger.
 *
 * Note: NotificationListenerService and AccessibilityService do NOT need
 * explicit restarts here — Android rebinds them automatically if they
 * hold the appropriate permissions. This receiver handles the WorkManager
 * side only.
 *
 * The ρ-archive receives a SYSTEM_REBOOT phase transition entry so the
 * empirical record captures device restart events. These events are
 * structurally meaningful: they represent a discontinuity in the
 * behavioral signal stream that IDSWorker must account for when
 * computing holonomy accumulation rates.
 */
class RSPSBootReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "RSPSBootReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return

        Log.i(TAG, "Device boot detected — reinitializing RSPS cognitive infrastructure")

        // Re-schedule nightly IDS scoring (WorkManager scheduling survives reboot
        // but explicit re-enqueue with KEEP policy is safe to call again)
        com.rsps.ids.IDSWorker.scheduleNightlyScoring(context)

        // Log the reboot as a phase transition in the ρ-archive
        // Note: we cannot use RSPSApplication here as it may not be initialized yet.
        // Instead we write directly to the SharedPreferences that RhoNode uses.
        val prefs = context.getSharedPreferences("rsps_rho_archive", Context.MODE_PRIVATE)
        val existing = prefs.getString("phase_transitions", "[]") ?: "[]"
        try {
            val array = org.json.JSONArray(existing)
            array.put(org.json.JSONObject().apply {
                put("timestamp", System.currentTimeMillis())
                put("event", "SYSTEM_REBOOT")
                put("description", "Device rebooted — cognitive infrastructure reinitializing. Signal stream discontinuity logged.")
                put("iso8601", java.time.Instant.now().toString())
            })
            prefs.edit().putString("phase_transitions", array.toString()).apply()
        } catch (e: Exception) {
            Log.w(TAG, "Could not log reboot to ρ-archive: ${e.message}")
        }

        Log.i(TAG, "RSPS boot initialization complete")
    }
}
