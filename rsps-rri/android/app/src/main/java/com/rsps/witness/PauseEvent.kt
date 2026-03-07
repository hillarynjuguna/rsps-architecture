package com.rsps.witness

import androidx.room.*
import kotlinx.coroutines.flow.Flow

// ─────────────────────────────────────────────────────────────────────────────
// DATA MODEL
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RSPS Witness — Pause Event
 *
 * The atomic unit of behavioral signal. Each row represents one moment
 * where attention was captured — where the scroll stopped because something
 * held the gaze long enough to register as meaningful engagement.
 *
 * The bufferLoadAtPause field is the cross-reference bridge to the Observatory:
 * it records the total cognitive load weight of all held notifications at the
 * moment this pause occurred. This is the integration key.
 *
 * A pause with bufferLoad=0.0 occurred in a clear membrane state.
 * A pause with bufferLoad=12.5 occurred while 8+ notifications were being held.
 * The IDS scorer weights these differently — attention quality degrades under
 * high buffer load regardless of pause duration.
 */
@Entity(
    tableName = "pause_events",
    indices = [
        Index(value = ["sessionId"]),
        Index(value = ["timestampMs"]),
        Index(value = ["platformPackage"])
    ]
)
data class PauseEvent(

    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    /** Session identifier — groups pauses from the same usage session */
    val sessionId: String,

    /** Package name of the platform where the pause occurred */
    val platformPackage: String,

    /** How long the pause lasted in milliseconds */
    val pauseDurationMs: Long,

    /** When the pause occurred (epoch millis) */
    val timestampMs: Long,

    /**
     * Total buffer weight from Observatory at moment of this pause.
     * Null if Observatory data was unavailable (e.g., service not running).
     * This is the cross-reference field that enables the integrated IDS computation.
     */
    val bufferLoadAtPause: Float? = null,

    /**
     * IDS weight assigned during scoring phase.
     * Null until Gemma scoring has processed this event.
     * Set by IDSWorker.
     */
    val idsWeight: Float? = null,

    /**
     * Cluster label assigned by Gemma 1B-IT.
     * E.g., "relational-intelligence", "technical-architecture", "social-signal"
     * Null until cluster detection has processed this event.
     */
    val clusterLabel: String? = null
)

// ─────────────────────────────────────────────────────────────────────────────
// DAO
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RSPS Witness — Witness DAO
 *
 * Data access for the behavioral signal layer.
 * The queries here are the analytical foundation for IDS scoring.
 */
@Dao
interface WitnessDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPauseEvent(event: PauseEvent): Long

    @Query("SELECT * FROM pause_events ORDER BY timestampMs DESC LIMIT 100")
    fun getRecentPausesFlow(): Flow<List<PauseEvent>>

    @Query("SELECT * FROM pause_events ORDER BY timestampMs DESC LIMIT :limit")
    suspend fun getRecentPausesSync(limit: Int = 500): List<PauseEvent>

    /** All pauses in the last N hours — IDS worker input */
    @Query("""
        SELECT * FROM pause_events 
        WHERE timestampMs > :sinceMs
        ORDER BY timestampMs DESC
    """)
    suspend fun getPausesSince(sinceMs: Long): List<PauseEvent>

    /** CDP window query — 90-day lookback for Cognitive Development Profile */
    @Query("""
        SELECT * FROM pause_events 
        WHERE timestampMs > :startMs AND timestampMs < :endMs
        ORDER BY timestampMs ASC
    """)
    suspend fun getPausesInWindow(startMs: Long, endMs: Long): List<PauseEvent>

    /**
     * The integration query — cross-references with Observatory buffer.
     *
     * For each pause event, computes the average buffer weight of all
     * Observatory notifications intercepted within a 60-second window
     * centered on the pause timestamp.
     *
     * This is the key analytical operation of the integrated system:
     * it connects what was held at the membrane with what captured attention.
     */
    @Query("""
        SELECT p.*, 
               COALESCE(AVG(n.bufferWeight), 0.0) as computedBufferLoad,
               COUNT(n.sbnKey) as notificationCountInWindow
        FROM pause_events p
        LEFT JOIN buffered_notifications n
          ON n.interceptedAtTimestamp BETWEEN (p.timestampMs - 30000) AND (p.timestampMs + 30000)
        WHERE p.timestampMs > :sinceMs
        GROUP BY p.id
        ORDER BY p.timestampMs DESC
    """)
    suspend fun getPausesWithBufferContext(sinceMs: Long): List<PauseWithBufferContext>

    /** Update cluster label after Gemma 1B-IT processing */
    @Query("UPDATE pause_events SET clusterLabel = :label WHERE id = :id")
    suspend fun updateClusterLabel(id: Long, label: String)

    /** Update IDS weight after scoring */
    @Query("UPDATE pause_events SET idsWeight = :weight WHERE id = :id")
    suspend fun updateIDSWeight(id: Long, weight: Float)

    /** Aggregate stats for dashboard display */
    @Query("""
        SELECT platformPackage,
               COUNT(*) as pauseCount,
               AVG(pauseDurationMs) as avgDurationMs,
               SUM(pauseDurationMs) as totalDurationMs
        FROM pause_events
        WHERE timestampMs > :sinceMs
        GROUP BY platformPackage
        ORDER BY totalDurationMs DESC
    """)
    suspend fun getPlatformStats(sinceMs: Long): List<PlatformStats>
}

// ─────────────────────────────────────────────────────────────────────────────
// QUERY RESULT TYPES
// ─────────────────────────────────────────────────────────────────────────────

data class PauseWithBufferContext(
    val id: Long,
    val sessionId: String,
    val platformPackage: String,
    val pauseDurationMs: Long,
    val timestampMs: Long,
    val bufferLoadAtPause: Float?,
    val computedBufferLoad: Float,
    val notificationCountInWindow: Int
)

data class PlatformStats(
    val platformPackage: String,
    val pauseCount: Int,
    val avgDurationMs: Float,
    val totalDurationMs: Long
)
