package com.rsps.membrane

import android.content.Context
import android.util.Log
import com.rsps.nodes.RhoNode
import com.rsps.nodes.TauNode
import com.rsps.observatory.ObservatoryDatabase
import com.rsps.witness.WitnessDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * RSPS Membrane — Epistemic Membrane Integration Coordinator
 *
 * This is the architectural linchpin of Phase 1.5: the component that
 * recognises the Observatory and Witness as two halves of one system.
 *
 * The Observatory is the gate — it decides what enters.
 * The Witness is the record — it logs what actually captured attention.
 *
 * The EpistemicMembrane holds both, runs the cross-reference JOIN that
 * produces buffer_load_at_pause, and applies the autopoietic feedback
 * loop that adjusts Observatory policy from IDS scores.
 *
 * Architecturally this class implements the closed loop:
 *
 *   α → Manifold → Natural Gradient → α
 *
 * — the autopoiesis node (α) continuously producing the epistemic
 * membrane's boundary conditions by consuming its own output (IDS)
 * to reconfigure the membrane's permeability.
 *
 * The EpistemicMembrane is NOT a service. It does not run in the
 * background. It is a coordinator that is called by services and by
 * the IDSWorker when they need to consult or update the integrated state.
 */
class EpistemicMembrane private constructor(
    private val context: Context,
    private val rhoNode: RhoNode,
    private val tauNode: TauNode
) {
    companion object {
        private const val TAG = "EpistemicMembrane"
        private const val PREFS = "rsps_membrane_policy"
        private const val KEY_THRESHOLD = "gating_threshold"
        private const val DEFAULT_THRESHOLD = 0.5f

        @Volatile private var INSTANCE: EpistemicMembrane? = null

        fun getInstance(
            context: Context,
            rhoNode: RhoNode,
            tauNode: TauNode
        ): EpistemicMembrane =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: EpistemicMembrane(context.applicationContext, rhoNode, tauNode)
                    .also { INSTANCE = it }
            }
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private val observatoryDb by lazy { ObservatoryDatabase.getInstance(context) }
    private val witnessDb by lazy { WitnessDatabase.getInstance(context) }

    /** Current gating threshold — higher value = tighter membrane */
    var gatingThreshold: Float
        get() = prefs.getFloat(KEY_THRESHOLD, DEFAULT_THRESHOLD)
        private set(value) = prefs.edit().putFloat(KEY_THRESHOLD, value).apply()

    // ─────────────────────────────────────────────────────────────────────
    // AUTOPOIETIC FEEDBACK
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Apply IDS score to adjust the gating threshold.
     *
     * Called by IDSWorker after each nightly scoring run. This is the
     * closure of the autopoietic loop — the system using the output of
     * its own cognitive measurement to reconfigure the conditions of
     * its own cognition.
     *
     * Asymmetric gain:
     *   - IDS above target → small threshold loosening (policy working)
     *   - IDS below target → stronger threshold tightening (too noisy)
     *
     * The Causal Shear damping factor halves any adjustment when the
     * ρ-archive shows temporal discontinuity — archive integrity takes
     * priority over membrane optimisation in unstable conditions.
     */
    fun applyIDSFeedback(idsScore: Float) {
        val target = 0.65f
        val gain = 0.15f
        val shearDamping = if (rhoNode.hasCausalShear()) 0.5f else 1.0f

        val deviation = idsScore - target
        val rawDelta = if (deviation >= 0) deviation * gain * 0.7f
                       else deviation * gain * 1.3f

        val clampedDelta = (rawDelta * shearDamping).coerceIn(-0.20f, 0.20f)
        val newThreshold = (gatingThreshold + clampedDelta).coerceIn(0.10f, 2.50f)

        val oldThreshold = gatingThreshold
        gatingThreshold = newThreshold

        val direction = if (clampedDelta > 0.001f) "LOOSENED" else
                        if (clampedDelta < -0.001f) "TIGHTENED" else "STABLE"

        Log.i(TAG, "Policy feedback: $direction by ${clampedDelta} | IDS=$idsScore | threshold $oldThreshold → $newThreshold")

        rhoNode.logPhaseTransition(
            event = "MEMBRANE_POLICY_UPDATE",
            description = "IDS=$idsScore → threshold $oldThreshold → $newThreshold ($direction)"
        )
    }

    // ─────────────────────────────────────────────────────────────────────
    // CROSS-REFERENCE
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Run the integration cross-reference query for recent pause events.
     *
     * This is the architectural bridge: for each Witness pause event,
     * it computes the average Observatory buffer weight within the
     * 60-second window centred on that pause, producing the
     * buffer_load_at_pause value that contextualises IDS scoring.
     *
     * High buffer load at pause → attention was fragmented at that moment.
     * Low buffer load at pause → attention was relatively clear.
     *
     * The IDS scorer weights these differently, producing a more accurate
     * picture of genuine cognitive engagement vs distracted consumption.
     */
    suspend fun updatePauseEventsWithBufferContext(sinceMs: Long) {
        val pauseEvents = witnessDb.witnessDao().getPausesSince(sinceMs)

        for (pause in pauseEvents) {
            if (pause.bufferLoadAtPause != null) continue // Already enriched

            val windowStart = pause.timestampMs - 30_000L
            val windowEnd = pause.timestampMs + 30_000L
            val notificationsInWindow = observatoryDb.bufferedNotificationDao()
                .getBufferedInWindow(windowStart, windowEnd)

            val avgWeight = if (notificationsInWindow.isEmpty()) 0f
                            else notificationsInWindow.map { it.bufferWeight }.average().toFloat()

            // Update the pause event with the computed buffer context
            // (requires WitnessDao.updateBufferLoad — add to Phase 1.5)
            Log.v(TAG, "Pause ${pause.id}: buffer_load=$avgWeight (${notificationsInWindow.size} notifications)")
        }
    }

    /**
     * Current membrane status snapshot for the dashboard UI.
     */
    suspend fun getMembranStatus(): MembraneStatus {
        val bufferCount = observatoryDb.bufferedNotificationDao()
            .getUnreviewedCountFlow().let {
                // Collect once — simplified for non-reactive call sites
                0 // placeholder; UI should collect the Flow directly
            }
        val bufferWeight = observatoryDb.bufferedNotificationDao().getTotalBufferWeight()

        return MembraneStatus(
            gatingThreshold = gatingThreshold,
            totalBufferWeight = bufferWeight,
            isShearDetected = rhoNode.hasCausalShear(),
            tauLockActive = tauNode.acheVector.isNotEmpty()
        )
    }
}

data class MembraneStatus(
    val gatingThreshold: Float,
    val totalBufferWeight: Float,
    val isShearDetected: Boolean,
    val tauLockActive: Boolean
)

/**
 * PolicyFeedback — Android-side wrapper called by IDSWorker.
 * Delegates to EpistemicMembrane.
 */
class PolicyFeedback(private val context: Context) {
    fun applyIDSFeedback(idsScore: com.rsps.ids.IDSScore) {
        val app = context.applicationContext as? com.rsps.RSPSApplication ?: return
        app.epistemicMembrane.applyIDSFeedback(idsScore.score)
    }
}
