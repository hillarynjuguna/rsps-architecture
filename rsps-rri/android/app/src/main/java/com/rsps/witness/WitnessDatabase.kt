package com.rsps.witness

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * RSPS Witness — Room Database
 *
 * Persistent store for behavioral signal. Every pause event logged here
 * is a raw datum of attention — the phenomenological record of what
 * captured cognitive engagement during the observation window.
 *
 * The cross-reference query between this database and the Observatory's
 * buffered_notifications table is the integration key of Phase 1.5:
 * it joins what was held at the membrane with what actually captured
 * attention, producing the buffer_load_at_pause metric that contextualises
 * every IDS computation.
 *
 * Cross-database queries (accessing buffered_notifications from here)
 * require both databases to be in the same Room process context.
 * The EpistemicMembrane coordinator handles this correctly by holding
 * references to both database instances and executing the JOIN query
 * via a raw SQLite connection. See CrossReferenceQuery.kt.
 */
@Database(
    entities = [PauseEvent::class],
    version = 1,
    exportSchema = true
)
abstract class WitnessDatabase : RoomDatabase() {

    abstract fun witnessDao(): WitnessDao

    companion object {
        private const val DB_NAME = "witness.db"

        @Volatile private var INSTANCE: WitnessDatabase? = null

        fun getInstance(context: Context): WitnessDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    WitnessDatabase::class.java,
                    DB_NAME
                )
                    .fallbackToDestructiveMigration()
                    .build()
                    .also { INSTANCE = it }
            }
    }
}
