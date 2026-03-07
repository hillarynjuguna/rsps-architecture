package com.rsps.observatory

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * RSPS Observatory — Room Database
 *
 * Single source of truth for the epistemic membrane's persistent state.
 * The buffer is the materialisation of the ρ-archive at the notification layer —
 * every row is a moment where the membrane *held* rather than *passed*,
 * and the accumulated weights across those rows are what the IDS cross-reference
 * query reads to contextualise Witness pause events.
 *
 * Migration strategy: additive only. Never drop columns. If a field must be
 * removed, null it; if a field must be renamed, add the new column and
 * migrate data in a Migration block. The ledger model means deletion is
 * almost always the wrong move — even stale data is potentially meaningful
 * residue for Paper 3's empirical record.
 */
@Database(
    entities = [BufferedNotificationEntity::class],
    version = 1,
    exportSchema = true
)
abstract class ObservatoryDatabase : RoomDatabase() {

    abstract fun bufferedNotificationDao(): BufferedNotificationDao

    companion object {
        private const val DB_NAME = "rsps_observatory.db"

        @Volatile private var INSTANCE: ObservatoryDatabase? = null

        fun getInstance(context: Context): ObservatoryDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    ObservatoryDatabase::class.java,
                    DB_NAME
                )
                    .fallbackToDestructiveMigration() // Phase 1 only; replace with Migrations in Phase 3
                    .build()
                    .also { INSTANCE = it }
            }
    }
}
