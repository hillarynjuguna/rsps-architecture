package com.rsps.observatory

import androidx.room.*
import kotlinx.coroutines.flow.Flow

/**
 * RSPS Observatory — Buffered Notification DAO
 *
 * Provides atomic access to the Residue Ledger (Holding Cell).
 *
 * Five atomic operations constitute the full interface of the epistemic membrane:
 *
 *   1. bufferNotification  — HOLD: Capture and hold an intercepted notification
 *   2. getAllBufferedFlow   — OBSERVE: Reactive stream for Missed Summary UI
 *   3. getAllBufferedSync   — SNAPSHOT: Point-in-time capture for release/replay
 *   4. clearBuffer         — PURGE: Reset after release cycle
 *   5. deleteByKey         — DISMISS: Selective rejection of one item
 *
 * The distinction between PURGE and DISMISS is architectural:
 *   - PURGE happens after a conscious "I've reviewed and processed all of this"
 *   - DISMISS is a selective rejection without full engagement
 *
 * Both are valid epistemic operations. The ρ-node logs which was used.
 *
 * Additional queries support the Observatory–Witness cross-reference
 * and the cognitive load weight computations for IDS integration.
 */
@Dao
interface BufferedNotificationDao {

    // ─────────────────────────────────────────────────────────────────────
    // OPERATION 1: HOLD
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Buffer an intercepted notification.
     *
     * Upsert strategy: REPLACE handles the Update Problem — if the same
     * notification key is re-posted with updated content, the buffer stays
     * current rather than accumulating stale entries.
     *
     * Suspending: called from KineticService coroutine scope.
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun bufferNotification(notification: BufferedNotificationEntity)

    // ─────────────────────────────────────────────────────────────────────
    // OPERATION 2: OBSERVE
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Live reactive stream of all held notifications, newest first.
     *
     * Returns a Kotlin Flow: the UI subscribes and every buffer change
     * automatically emits an updated list. The ResidueViewModel collects
     * this flow and exposes it to the Missed Summary UI.
     *
     * This is the system monitoring its own membrane state — not polling,
     * but listening to its own state changes.
     */
    @Query("SELECT * FROM buffered_notifications ORDER BY interceptedAtTimestamp DESC")
    fun getAllBufferedFlow(): Flow<List<BufferedNotificationEntity>>

    /**
     * Flow filtered to unreviewed items only — primary UI state.
     */
    @Query("""
        SELECT * FROM buffered_notifications 
        WHERE isReviewed = 0 
        ORDER BY interceptedAtTimestamp DESC
    """)
    fun getUnreviewedFlow(): Flow<List<BufferedNotificationEntity>>

    // ─────────────────────────────────────────────────────────────────────
    // OPERATION 3: SNAPSHOT
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Atomic point-in-time snapshot of the entire buffer.
     *
     * Used by the Release/Replay mechanism — captures all held items
     * at a single consistent moment before acting on them.
     *
     * Suspending: one-shot query, not a stream.
     */
    @Query("SELECT * FROM buffered_notifications")
    suspend fun getAllBufferedSync(): List<BufferedNotificationEntity>

    /**
     * Snapshot of buffer within a time window — used for cross-reference
     * with Witness pause events.
     *
     * @param windowStart epoch millis — start of window
     * @param windowEnd   epoch millis — end of window (e.g., windowStart + 60_000)
     */
    @Query("""
        SELECT * FROM buffered_notifications 
        WHERE interceptedAtTimestamp BETWEEN :windowStart AND :windowEnd
    """)
    suspend fun getBufferedInWindow(windowStart: Long, windowEnd: Long): List<BufferedNotificationEntity>

    // ─────────────────────────────────────────────────────────────────────
    // OPERATION 4: PURGE
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Full buffer clear — post-release reset.
     *
     * Called after the user has consciously engaged with the Missed Summary
     * and chosen to release all held notifications. This is the membrane
     * completing one epistemic cycle.
     */
    @Query("DELETE FROM buffered_notifications")
    suspend fun clearBuffer()

    /**
     * Clear only reviewed items — partial release preserving unreviewed.
     */
    @Query("DELETE FROM buffered_notifications WHERE isReviewed = 1")
    suspend fun clearReviewed()

    // ─────────────────────────────────────────────────────────────────────
    // OPERATION 5: DISMISS
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Selective dismissal — remove one notification by its StatusBarNotification key.
     * Used when the user swipes away a specific item in the Missed Summary.
     */
    @Query("DELETE FROM buffered_notifications WHERE sbnKey = :key")
    suspend fun deleteByKey(key: String)

    // ─────────────────────────────────────────────────────────────────────
    // ANALYTICS / IDS INTEGRATION
    // ─────────────────────────────────────────────────────────────────────

    /**
     * Total buffer weight at a given moment — the cognitive load score
     * of all currently held notifications.
     *
     * Used by IDS scoring to contextualize pause events:
     * a pause with bufferWeight=12.5 has different IDS significance
     * than a pause with bufferWeight=0.2.
     */
    @Query("SELECT COALESCE(SUM(bufferWeight), 0.0) FROM buffered_notifications WHERE isReviewed = 0")
    suspend fun getTotalBufferWeight(): Float

    /**
     * Count of unreviewed notifications — simple membrane load indicator.
     */
    @Query("SELECT COUNT(*) FROM buffered_notifications WHERE isReviewed = 0")
    fun getUnreviewedCountFlow(): Flow<Int>

    /**
     * Mark a notification as reviewed (user saw it in Missed Summary).
     */
    @Query("UPDATE buffered_notifications SET isReviewed = 1 WHERE sbnKey = :key")
    suspend fun markReviewed(key: String)

    /**
     * Package-level aggregation — which apps are contributing most
     * to the cognitive load? Used in ResidueViewModel analytics.
     */
    @Query("""
        SELECT packageName, COUNT(*) as count, SUM(bufferWeight) as totalWeight
        FROM buffered_notifications
        WHERE isReviewed = 0
        GROUP BY packageName
        ORDER BY totalWeight DESC
    """)
    fun getPackageWeightFlow(): Flow<List<PackageWeight>>
}

/** Result type for package-level weight aggregation */
data class PackageWeight(
    val packageName: String,
    val count: Int,
    val totalWeight: Float
)
