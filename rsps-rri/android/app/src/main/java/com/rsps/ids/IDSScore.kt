package com.rsps.ids

import android.content.Context
import android.util.Log

// ─────────────────────────────────────────────────────────────────────────────
// DATA MODEL
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RSPS IDS — Idea Development Score
 *
 * The primary output metric of the cognitive metabolization system.
 * A Float in [0.00, 1.00] computed nightly by Gemma E2B from the
 * behavioral signal accumulated by the Witness Infrastructure.
 *
 * Formal interpretation:
 *   IDS ≈ holonomy accumulation rate of the cognitive fiber bundle.
 *   As IDS → 1.00, the ρ-archive has accumulated sufficient structural
 *   residue that the bundle's topology approaches full characterization.
 *   The 90-day CDP training window is the time required to map the
 *   fundamental group π₁ of the cognitive base space.
 *
 * Operational interpretation:
 *   IDS measures synthesis readiness — the degree to which consumed
 *   information has been metabolized into integrated knowledge rather
 *   than remaining as unprocessed residue.
 *
 * Phase 0 empirical anchor:
 *   Both Gemma 1B-IT and Gemma E2B independently identified
 *   "relational-intelligence" as the primary cluster. This convergence
 *   from two different model architectures is the validation signal.
 */
data class IDSScore(
    /** The score itself — [0.00, 1.00] */
    val score: Float,

    /** When this score was computed (epoch millis) */
    val computedAt: Long,

    /** Day number in the 90-day CDP training window */
    val cdpDay: Int,

    /** Primary cognitive cluster identified by Gemma */
    val primaryCluster: String,

    /** All identified clusters with their weights */
    val clusterVector: Map<String, Float>,

    /** Number of pause events that fed into this score */
    val pauseEventCount: Int,

    /** Average buffer load during pause events — membrane context */
    val averageBufferLoad: Float,

    /**
     * Holonomy proxy estimate (κ^Berry approximation).
     * Null until orchestration layer is integrated.
     * Represents departure from congruence across the cognitive cycle.
     */
    val holonomyEstimate: Float? = null,

    /**
     * Recommended policy adjustment for the Observatory.
     * Positive = loosen gating (IDS healthy, current policy working).
     * Negative = tighten gating (IDS degraded, reduce membrane noise).
     */
    val recommendedThresholdDelta: Float = 0f,

    /** Human-readable synthesis of what the score indicates */
    val interpretation: String = ""
) {
    val synthesisReadiness: SynthesisReadiness get() = when {
        score >= 0.80f -> SynthesisReadiness.HIGH
        score >= 0.55f -> SynthesisReadiness.MODERATE
        score >= 0.30f -> SynthesisReadiness.BUILDING
        else -> SynthesisReadiness.LOW
    }
}

enum class SynthesisReadiness {
    HIGH,       // → Crystallize: write, build, create
    MODERATE,   // → Continue metabolizing: maintain current input
    BUILDING,   // → Deepen engagement: seek higher-signal input
    LOW         // → Tighten membrane: reduce noise, increase rest
}

// ─────────────────────────────────────────────────────────────────────────────
// CDP MANAGER — 90-day Cognitive Development Profile
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Cognitive Development Profile Manager
 *
 * Manages the 90-day training window over which the IDS accumulates
 * sufficient holonomy to characterize the cognitive fiber bundle's topology.
 *
 * The 90-day window is not arbitrary: it corresponds empirically to the
 * time required to map the fundamental group π₁ of the cognitive base space
 * through repeated daily behavioral signal sampling.
 *
 * After Day 90, the system has enough structural residue to:
 *   - Characterize the primary and secondary cognitive clusters
 *   - Identify stable attractors in the behavioral signal
 *   - Compute reliable policy feedback for the Observatory
 *   - Begin the ν-node gauge search (transmutation phase)
 *
 * The CDPManager is the only component with a graduation criterion:
 * it knows when Phase 2 ends and Phase 3 begins.
 */
class CDPManager(private val context: Context) {

    companion object {
        private const val TAG = "CDPManager"
        private const val CDP_WINDOW_DAYS = 90
        private const val PREFS_NAME = "rsps_cdp"
        private const val KEY_START_DATE = "cdp_start_date_ms"
        private const val KEY_SCORES = "cdp_scores_json"

        // Graduation thresholds
        private const val GRADUATION_MIN_IDS = 0.65f  // IDS must exceed this on Day 90
        private const val GRADUATION_MIN_DAYS_WITH_DATA = 60  // Must have data on 60/90 days
    }

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    val startDateMs: Long get() = prefs.getLong(KEY_START_DATE, 0L).let { stored ->
        if (stored == 0L) {
            val now = System.currentTimeMillis()
            prefs.edit().putLong(KEY_START_DATE, now).apply()
            now
        } else stored
    }

    val currentDay: Int get() {
        val elapsed = System.currentTimeMillis() - startDateMs
        return (elapsed / (24 * 60 * 60 * 1000L)).toInt() + 1
    }

    val daysRemaining: Int get() = maxOf(0, CDP_WINDOW_DAYS - currentDay)

    val isWindowComplete: Boolean get() = currentDay > CDP_WINDOW_DAYS

    /** Check whether the system has graduated — met the criteria to enter Phase 3 */
    fun checkGraduation(recentScores: List<IDSScore>): GraduationStatus {
        if (!isWindowComplete) {
            return GraduationStatus(
                hasGraduated = false,
                reason = "CDP window incomplete: Day $currentDay of $CDP_WINDOW_DAYS",
                daysRemaining = daysRemaining
            )
        }

        val daysWithData = recentScores.count { it.pauseEventCount > 0 }
        if (daysWithData < GRADUATION_MIN_DAYS_WITH_DATA) {
            return GraduationStatus(
                hasGraduated = false,
                reason = "Insufficient data: $daysWithData days with signal (need $GRADUATION_MIN_DAYS_WITH_DATA)",
                daysRemaining = 0
            )
        }

        val latestScore = recentScores.lastOrNull()?.score ?: 0f
        if (latestScore < GRADUATION_MIN_IDS) {
            return GraduationStatus(
                hasGraduated = false,
                reason = "IDS below graduation threshold: $latestScore (need $GRADUATION_MIN_IDS)",
                daysRemaining = 0
            )
        }

        Log.i(TAG, "🎓 CDP GRADUATION: Day $currentDay, IDS=$latestScore, daysWithData=$daysWithData")
        return GraduationStatus(
            hasGraduated = true,
            reason = "All graduation criteria met. ν-node gauge search may begin.",
            daysRemaining = 0
        )
    }

    data class GraduationStatus(
        val hasGraduated: Boolean,
        val reason: String,
        val daysRemaining: Int
    )
}
