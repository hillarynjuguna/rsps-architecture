package com.rsps.observatory

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * RSPS Observatory — Buffered Notification Entity
 *
 * The fundamental unit of the epistemic membrane's holding layer.
 * When the KineticService intercepts a notification that does not
 * pass the RedLine check, it is crystallized into this entity and
 * held in the buffer until the user reviews the Missed Summary.
 *
 * The "bufferWeight" field represents the cognitive load contribution
 * of this notification — used in the cross-reference JOIN with the
 * Witness pause events to compute buffer_load_at_pause.
 *
 * This is the Residue Ledger: events are stored as data for later
 * interpretation (ledger model), not processed immediately (queue model).
 */
@Entity(
    tableName = "buffered_notifications",
    indices = [Index(value = ["sbnKey"], unique = true)]
)
data class BufferedNotificationEntity(

    /** Unique key from Android's StatusBarNotification — natural PK */
    @PrimaryKey
    val sbnKey: String,

    /** Package that generated the notification (e.g., com.whatsapp) */
    val packageName: String,

    /** Notification title text — may be null for media notifications */
    val title: String? = null,

    /** Notification body text — truncated at 512 chars for storage */
    val text: String? = null,

    /** Epoch millis when the KineticService intercepted this notification */
    val interceptedAtTimestamp: Long,

    /**
     * Whether this notification was routed through the RedLine bypass.
     * RedLine notifications are NOT stored here — they pass directly
     * to consciousness. isRedLine=true here would indicate a categorization
     * error and should be flagged.
     */
    val isRedLine: Boolean = false,

    /**
     * Cognitive load weight of this notification.
     * Used in buffer_load_at_pause calculations.
     * Default 1.0 — elevated for high-priority senders, reduced for
     * low-signal senders (e.g., marketing apps).
     *
     * Future: computed by DCFB classifier on notification content.
     */
    val bufferWeight: Float = 1.0f,

    /**
     * Notification category (CATEGORY_MESSAGE, CATEGORY_SOCIAL, etc.)
     * from Android's Notification.category field.
     */
    val category: String? = null,

    /**
     * True once the user has reviewed this item in the Missed Summary.
     * Reviewed items are eligible for clearBuffer() on next session end.
     */
    val isReviewed: Boolean = false
)
