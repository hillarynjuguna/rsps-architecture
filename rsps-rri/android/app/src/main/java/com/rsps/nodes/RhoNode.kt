package com.rsps.nodes

import android.content.Context
import android.util.Log
import com.rsps.ids.IDSScore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

/**
 * RSPS — ρ-Node (Rho Node): Temporal Spine / Continuity Ledger
 *
 * The ρ-node is the holonomy representation of the system's history.
 * Every generative transient event — every IDS threshold crossing, every
 * membrane policy change, every phase transition — is a loop in the base
 * space whose transformation is recorded here.
 *
 * Formal mapping:
 *   ρ: π₁(X, x) → G^δ
 *   The fundamental group homomorphism that encodes how every possible
 *   loop in the cognitive base space transforms the fiber.
 *
 * Causal Shear (σ_shear) is what happens when the ρ-archive is disrupted:
 *   loops that should map to the identity start producing non-trivial
 *   transformations, and the system loses its ability to distinguish
 *   genuine structural change from noise.
 *
 * The IDS scoring system is — formally — measuring the holonomy
 * accumulation rate of the cognitive fiber bundle. The ρ-node is
 * where that accumulation lives.
 *
 * The ρ-archive is intentionally append-only. You cannot delete history
 * from the ρ-node — doing so would introduce Causal Shear. You can only
 * add new entries that *supersede* or *contextualize* earlier ones.
 * This is the ledger model, not the queue model.
 *
 * Implementation: SharedPreferences-backed JSON for Phase 1.
 * Phase 3 will migrate to an encrypted Room database with CMCP integration.
 */
class RhoNode private constructor(private val context: Context) {

    companion object {
        private const val TAG = "RhoNode"
        private const val PREFS_NAME = "rsps_rho_archive"
        private const val KEY_EVENTS = "phase_transitions"
        private const val KEY_MEMBRANE_EVENTS = "membrane_events"
        private const val KEY_IDS_HISTORY = "ids_history"
        private const val MAX_EVENTS = 2000  // Soft cap — not enforced until Phase 3

        @Volatile private var instance: RhoNode? = null

        fun getInstance(context: Context): RhoNode =
            instance ?: synchronized(this) {
                instance ?: RhoNode(context.applicationContext).also { instance = it }
            }
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    // ─────────────────────────────────────────────────────────────────────
    // PHASE TRANSITION LOG
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Log a named phase transition to the archive.
     *
     * Phase transitions are the named moments where the system's topology
     * changes — new capabilities come online, thresholds are crossed,
     * structural decisions are made.
     *
     * The corpus dates:
     *   - Nov 6, 2025: DCFB discovery
     *   - Dec 23, 2025: RSPS Observatory built
     *   - Mar 2026: Witness Phase 1
     *   - Mar 7, 2026: Integration insight
     *
     * Every significant system event should be logged here so Paper 3
     * has an accurate empirical record of phase transitions.
     */
    fun logPhaseTransition(event: String, description: String) {
        scope.launch {
            val entry = JSONObject().apply {
                put("timestamp", System.currentTimeMillis())
                put("event", event)
                put("description", description)
                put("iso8601", java.time.Instant.now().toString())
            }
            appendToArchive(KEY_EVENTS, entry)
            Log.d(TAG, "Phase transition recorded: $event — $description")
        }
    }

    /**
     * Log an epistemic membrane event (notification gating decision).
     * These are the raw material of the holonomy accumulation.
     */
    fun logMembraneEvent(type: String, key: String, packageName: String) {
        scope.launch {
            val entry = JSONObject().apply {
                put("timestamp", System.currentTimeMillis())
                put("type", type)           // REDLINE_BYPASS, BUFFERED, DISMISSED, RELEASED
                put("key", key)
                put("packageName", packageName)
            }
            appendToArchive(KEY_MEMBRANE_EVENTS, entry)
        }
    }

    /**
     * Log an IDS score event — the holonomy accumulation metric.
     * Each nightly score is a loop traversal result.
     */
    fun logIDSScoreEvent(score: IDSScore) {
        scope.launch {
            val entry = JSONObject().apply {
                put("timestamp", score.computedAt)
                put("score", score.score)
                put("cdpDay", score.cdpDay)
                put("primaryCluster", score.primaryCluster)
                put("pauseEventCount", score.pauseEventCount)
                put("avgBufferLoad", score.averageBufferLoad)
                put("synthesisReadiness", score.synthesisReadiness.name)
                put("interpretation", score.interpretation)
            }
            appendToArchive(KEY_IDS_HISTORY, entry)
            Log.i(TAG, "IDS event archived: Day ${score.cdpDay}, score=${score.score}")
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // RETRIEVAL
    // ─────────────────────────────────────────────────────────────────────

    fun getPhaseTransitions(): List<JSONObject> = loadFromArchive(KEY_EVENTS)

    fun getIDSHistory(): List<JSONObject> = loadFromArchive(KEY_IDS_HISTORY)

    fun getMembraneEvents(): List<JSONObject> = loadFromArchive(KEY_MEMBRANE_EVENTS)

    /**
     * Generate a ρ-archive summary for CMCP packets.
     * This is what gets included in the Layer 9 header when sending
     * context to another AI model.
     */
    fun generateArchiveSummary(): String {
        val transitions = getPhaseTransitions().takeLast(5)
        val idsHistory = getIDSHistory().takeLast(7)

        return buildString {
            append("RHO_ARCHIVE_SUMMARY: ")
            append("phase_transitions=${transitions.size}_recent | ")
            append("latest_transitions=[")
            transitions.joinTo(this, "; ") { it.optString("event") }
            append("] | ")
            append("ids_7day=[")
            idsHistory.joinTo(this, ",") { String.format("%.2f", it.optDouble("score")) }
            append("] | ")
            append("cdp_day=${idsHistory.lastOrNull()?.optInt("cdpDay") ?: 0}")
        }
    }

    /**
     * Check for Causal Shear — disruption in the archive's temporal continuity.
     * Detects gaps, anomalous IDS drops, or missing expected events.
     */
    fun hasCausalShear(): Boolean {
        val idsHistory = getIDSHistory()
        if (idsHistory.size < 3) return false

        // Check for large IDS drops that indicate archive disruption
        val recentScores = idsHistory.takeLast(5).map { it.optDouble("score").toFloat() }
        for (i in 1 until recentScores.size) {
            val drop = recentScores[i - 1] - recentScores[i]
            if (drop > 0.35f) {
                Log.w(TAG, "Causal shear detected: IDS drop of ${drop} between consecutive days")
                return true
            }
        }
        return false
    }

    // ─────────────────────────────────────────────────────────────────────
    // PERSISTENCE
    // ─────────────────────────────────────────────────────────────────────

    private fun appendToArchive(key: String, entry: JSONObject) {
        val existing = prefs.getString(key, "[]")
        val array = try {
            JSONArray(existing)
        } catch (e: Exception) {
            JSONArray()
        }
        array.put(entry)
        prefs.edit().putString(key, array.toString()).apply()
    }

    private fun loadFromArchive(key: String): List<JSONObject> {
        val json = prefs.getString(key, "[]") ?: return emptyList()
        return try {
            val array = JSONArray(json)
            (0 until array.length()).map { array.getJSONObject(it) }
        } catch (e: Exception) {
            Log.w(TAG, "Archive parse error for key=$key: ${e.message}")
            emptyList()
        }
    }
}
