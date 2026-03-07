package com.rsps

import android.app.Application
import android.util.Log
import androidx.work.Configuration
import androidx.work.WorkManager
import com.rsps.ids.IDSWorker
import com.rsps.membrane.EpistemicMembrane
import com.rsps.nodes.RhoNode
import com.rsps.nodes.TauNode

/**
 * RSPS Application — Root of the autopoietic cognitive system.
 *
 * Initializes the three core layers in dependency order:
 *   1. ρ-node (Rho): Temporal spine — must exist before anything can be recorded
 *   2. τ-node (Tau): Human anchor — establishes mortal asymmetry χ=1
 *   3. Epistemic Membrane: Integration coordinator
 *
 * WorkManager is configured here for IDS nightly scoring jobs.
 */
class RSPSApplication : Application(), Configuration.Provider {

    companion object {
        private const val TAG = "RSPSApplication"
        lateinit var instance: RSPSApplication
            private set
    }

    // Core node singletons — the system's persistent state holders
    lateinit var rhoNode: RhoNode
        private set
    lateinit var tauNode: TauNode
        private set
    lateinit var epistemicMembrane: EpistemicMembrane
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.i(TAG, "RSPS system initializing — Phase transition: APPLICATION_START")

        // Order matters: rho before tau before membrane
        initializeRhoNode()
        initializeTauNode()
        initializeEpistemicMembrane()

        // Schedule nightly IDS scoring (2AM by default)
        IDSWorker.scheduleNightlyScoring(this)

        Log.i(TAG, "RSPS system online. Autopoietic loop active.")
    }

    private fun initializeRhoNode() {
        rhoNode = RhoNode.getInstance(this)
        rhoNode.logPhaseTransition(
            event = "SYSTEM_BOOT",
            description = "Application process started — ρ-archive online"
        )
    }

    private fun initializeTauNode() {
        tauNode = TauNode.getInstance(this)
        Log.d(TAG, "τ-node online — Mortal Asymmetry χ=1 engaged")
    }

    private fun initializeEpistemicMembrane() {
        epistemicMembrane = EpistemicMembrane.getInstance(this, rhoNode, tauNode)
        Log.d(TAG, "Epistemic Membrane online — Observatory ↔ Witness integration active")
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(Log.INFO)
            .build()
}
