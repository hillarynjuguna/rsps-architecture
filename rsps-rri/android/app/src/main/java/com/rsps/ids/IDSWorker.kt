package com.rsps.ids

import android.content.Context
import android.util.Log
import androidx.work.*
import com.rsps.membrane.PolicyFeedback
import com.rsps.nodes.RhoNode
import com.rsps.witness.WitnessDatabase
import java.util.concurrent.TimeUnit

/**
 * RSPS IDS — IDS Worker (WorkManager)
 *
 * Nightly background job that runs the full IDS scoring pipeline:
 *
 *   1. Fetch recent pause events from Witness database
 *   2. Fetch buffer context from Observatory database (cross-reference)
 *   3. Run Gemma E2B inference to compute IDS score
 *   4. Determine primary cognitive cluster
 *   5. Store IDSScore result
 *   6. Trigger autopoietic policy feedback to Observatory
 *   7. Log phase transition to ρ-archive
 *
 * Scheduled for 2:00 AM by default (when the device is likely idle
 * and on charge, and the day's signal has fully accumulated).
 *
 * Note on Gemma integration: Phase 2 uses MediaPipe LLM Inference API.
 * Until MediaPipe is integrated, the scoring uses a statistical fallback
 * that computes IDS from pause duration distributions. This is marked
 * throughout with TODO(PHASE_2): markers.
 *
 * The architecture is Gemma-ready — the interface is designed so
 * dropping in MediaPipe requires only replacing the inference call
 * in computeIDSWithGemma(), nothing else.
 */
class IDSWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    companion object {
        private const val TAG = "IDSWorker"
        private const val WORK_NAME = "rsps_nightly_ids"
        private const val LOOKBACK_HOURS = 24
        private const val CDP_LOOKBACK_DAYS = 90

        fun scheduleNightlyScoring(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiresBatteryNotLow(false)
                .setRequiredNetworkType(NetworkType.NOT_REQUIRED)  // Fully local
                .build()

            // Calculate initial delay to reach next 2:00 AM
            val request = PeriodicWorkRequestBuilder<IDSWorker>(24, TimeUnit.HOURS)
                .setConstraints(constraints)
                .setInitialDelay(calculateInitialDelayToNextNight(), TimeUnit.MILLISECONDS)
                .setBackoffCriteria(BackoffPolicy.LINEAR, 30, TimeUnit.MINUTES)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request
            )

            Log.i(TAG, "Nightly IDS scoring scheduled for 2:00 AM")
        }

        private fun calculateInitialDelayToNextNight(): Long {
            val now = System.currentTimeMillis()
            val cal = java.util.Calendar.getInstance().apply {
                add(java.util.Calendar.DAY_OF_MONTH, 1)
                set(java.util.Calendar.HOUR_OF_DAY, 2)
                set(java.util.Calendar.MINUTE, 0)
                set(java.util.Calendar.SECOND, 0)
            }
            return maxOf(0L, cal.timeInMillis - now)
        }
    }

    private val witnessDb by lazy { WitnessDatabase.getInstance(applicationContext) }
    private val witnessDao by lazy { witnessDb.witnessDao() }
    private val cdpManager by lazy { CDPManager(applicationContext) }
    private val policyFeedback by lazy { PolicyFeedback(applicationContext) }

    override suspend fun doWork(): Result {
        Log.i(TAG, "IDS scoring run started — Day ${cdpManager.currentDay}")

        return try {
            val sinceMs = System.currentTimeMillis() - (LOOKBACK_HOURS * 3600_000L)

            // Step 1: Fetch pause events with buffer context
            val pauseEvents = witnessDao.getPausesWithBufferContext(sinceMs)
            Log.d(TAG, "Fetched ${pauseEvents.size} pause events for scoring")

            if (pauseEvents.isEmpty()) {
                Log.w(TAG, "No pause events found — skipping scoring")
                return Result.success()
            }

            // Step 2: Compute IDS
            val idsScore = computeIDSScore(pauseEvents)
            Log.i(TAG, "IDS computed: ${idsScore.score} | cluster: ${idsScore.primaryCluster}")

            // Step 3: Store to SharedPreferences (simple persistence for now)
            storeIDSScore(idsScore)

            // Step 4: Autopoietic policy feedback
            policyFeedback.applyIDSFeedback(idsScore)

            // Step 5: Log to ρ-archive
            RhoNode.getInstance(applicationContext).logIDSScoreEvent(idsScore)

            // Step 6: Check CDP graduation
            val historicalScores = loadHistoricalScores()
            val graduation = cdpManager.checkGraduation(historicalScores + idsScore)
            if (graduation.hasGraduated) {
                Log.i(TAG, "🎓 CDP GRADUATION: ${graduation.reason}")
                RhoNode.getInstance(applicationContext).logPhaseTransition(
                    event = "CDP_GRADUATION",
                    description = graduation.reason
                )
            }

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "IDS scoring failed: ${e.message}", e)
            Result.retry()
        }
    }

    private suspend fun computeIDSScore(
        pauseEvents: List<com.rsps.witness.PauseWithBufferContext>
    ): IDSScore {
        // TODO(PHASE_2): Replace with Gemma MediaPipe inference
        // Current implementation: statistical fallback

        val totalPauses = pauseEvents.size
        val avgDuration = pauseEvents.map { it.pauseDurationMs }.average().toFloat()
        val avgBufferLoad = pauseEvents.mapNotNull { it.bufferLoadAtPause }
            .average().toFloat().takeIf { !it.isNaN() } ?: 0f

        // Statistical IDS computation
        // Long pauses indicate deep engagement → higher IDS
        // High buffer load during pauses indicates fragmented attention → lower IDS
        val durationScore = normalizeScore(avgDuration, 1500f, 15000f)
        val bufferPenalty = (avgBufferLoad / 10f).coerceIn(0f, 0.4f)
        val volumeBoost = (totalPauses.toFloat() / 50f).coerceIn(0f, 0.2f)

        val rawScore = (durationScore + volumeBoost - bufferPenalty).coerceIn(0f, 1f)

        // Cluster determination from platform distribution
        val platformCounts = pauseEvents.groupBy { it.platformPackage }
            .mapValues { it.value.size }
        val primaryCluster = determinePrimaryCluster(pauseEvents, platformCounts)

        val thresholdDelta = when {
            rawScore > 0.75f -> 0.05f   // IDS healthy — can loosen membrane slightly
            rawScore < 0.40f -> -0.10f  // IDS degraded — tighten membrane
            else -> 0f
        }

        return IDSScore(
            score = rawScore,
            computedAt = System.currentTimeMillis(),
            cdpDay = cdpManager.currentDay,
            primaryCluster = primaryCluster,
            clusterVector = mapOf(
                primaryCluster to rawScore,
                "attention-fragmentation" to bufferPenalty,
                "engagement-depth" to durationScore
            ),
            pauseEventCount = totalPauses,
            averageBufferLoad = avgBufferLoad,
            recommendedThresholdDelta = thresholdDelta,
            interpretation = generateInterpretation(rawScore, primaryCluster, avgBufferLoad)
        )
    }

    private fun determinePrimaryCluster(
        events: List<com.rsps.witness.PauseWithBufferContext>,
        platformCounts: Map<String, Int>
    ): String {
        // TODO(PHASE_2): Gemma 1B-IT inference on content signatures
        // For now: heuristic from platform + duration patterns

        val longPauses = events.count { it.pauseDurationMs > 8000 }
        val longPauseRatio = longPauses.toFloat() / events.size

        return when {
            longPauseRatio > 0.4f -> "relational-intelligence"  // Deep engagement
            longPauseRatio > 0.25f -> "concept-synthesis"
            longPauseRatio > 0.1f -> "social-signal"
            else -> "information-scan"
        }
    }

    private fun normalizeScore(value: Float, min: Float, max: Float): Float =
        ((value - min) / (max - min)).coerceIn(0f, 1f)

    private fun generateInterpretation(
        score: Float, cluster: String, bufferLoad: Float
    ): String = when (score) {
        in 0.80f..1.00f -> "High synthesis readiness. Primary cognitive cluster: $cluster. " +
                "Consider crystallizing: write, build, or create."
        in 0.55f..0.80f -> "Moderate readiness. $cluster signal building. " +
                "Continue metabolizing current inputs."
        in 0.30f..0.55f -> "Building phase. Deepen engagement with $cluster domain. " +
                if (bufferLoad > 5f) "Note: high membrane load ($bufferLoad) fragmenting attention." else ""
        else -> "Low synthesis signal. Tighten epistemic membrane — reduce input noise."
    }

    private fun storeIDSScore(score: IDSScore) {
        // Simple JSON-based storage; Phase 3 will use Room
        val prefs = applicationContext.getSharedPreferences("rsps_ids", Context.MODE_PRIVATE)
        val json = """
            {
              "score": ${score.score},
              "computedAt": ${score.computedAt},
              "cdpDay": ${score.cdpDay},
              "primaryCluster": "${score.primaryCluster}",
              "pauseEventCount": ${score.pauseEventCount},
              "avgBufferLoad": ${score.averageBufferLoad},
              "interpretation": "${score.interpretation}"
            }
        """.trimIndent()
        prefs.edit().putString("latest_score", json).apply()
        Log.d(TAG, "IDS score stored")
    }

    private fun loadHistoricalScores(): List<IDSScore> {
        // TODO: Load from Room database in Phase 3
        return emptyList()
    }
}
