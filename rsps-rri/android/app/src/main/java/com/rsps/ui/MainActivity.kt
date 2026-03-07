package com.rsps.ui

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.rsps.R
import com.rsps.RSPSApplication
import com.rsps.ids.SynthesisReadiness
import com.rsps.membrane.MembraneStatus
import com.rsps.nodes.TauLockResult
import com.rsps.observatory.KineticService
import com.rsps.witness.WitnessService
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * RSPS Main Dashboard — Epistemic Membrane Status UI
 *
 * The dashboard surfaces three things:
 *
 *   1. SYSTEM STATE: Are the Observatory and Witness services active?
 *      If not, what needs to be granted? The UI guides the user through
 *      the permission sequence without technical jargon.
 *
 *   2. IDS STATE: What is the current Idea Development Score?
 *      The score is presented with its Synthesis Readiness interpretation
 *      so the user knows what action is recommended, not just what the
 *      number means abstractly.
 *
 *   3. τ-ANCHOR INPUT: A single text field for setting the Ache Vector.
 *      This is the most operationally important interaction — setting τ
 *      activates the τ-Lock and orients the whole system. The UI makes
 *      this prominent and provides immediate feedback on τ-Lock status.
 *
 * The dashboard deliberately does NOT show individual buffered notifications
 * (that's the Missed Summary, a separate feature). It shows the membrane's
 * aggregate state: total buffer weight, IDS, CDP progress.
 *
 * The most important design decision: this is not a productivity app.
 * The dashboard is a cognitive infrastructure readout. It should feel like
 * a monitoring panel, not a to-do list. Density of information is a feature.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var app: RSPSApplication

    // Views
    private lateinit var tvObservatoryStatus: TextView
    private lateinit var tvWitnessStatus: TextView
    private lateinit var tvIDSScore: TextView
    private lateinit var tvIDSReadiness: TextView
    private lateinit var tvPrimaryCluster: TextView
    private lateinit var tvCDPDay: TextView
    private lateinit var tvBufferWeight: TextView
    private lateinit var tvTauLockStatus: TextView
    private lateinit var etAcheVector: EditText
    private lateinit var btnSetAche: Button
    private lateinit var btnGrantObservatory: Button
    private lateinit var btnGrantWitness: Button
    private lateinit var progressIDS: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        app = application as RSPSApplication
        bindViews()
        setupListeners()

        // Load saved ache vector into input field
        etAcheVector.setText(app.tauNode.acheVector)
    }

    override fun onResume() {
        super.onResume()
        startDashboardRefreshLoop()
        refreshServiceStatus()
    }

    // ─────────────────────────────────────────────────────────────────────
    // VIEW BINDING
    // ─────────────────────────────────────────────────────────────────────

    private fun bindViews() {
        tvObservatoryStatus = findViewById(R.id.tv_observatory_status)
        tvWitnessStatus     = findViewById(R.id.tv_witness_status)
        tvIDSScore          = findViewById(R.id.tv_ids_score)
        tvIDSReadiness      = findViewById(R.id.tv_ids_readiness)
        tvPrimaryCluster    = findViewById(R.id.tv_primary_cluster)
        tvCDPDay            = findViewById(R.id.tv_cdp_day)
        tvBufferWeight      = findViewById(R.id.tv_buffer_weight)
        tvTauLockStatus     = findViewById(R.id.tv_tau_lock_status)
        etAcheVector        = findViewById(R.id.et_ache_vector)
        btnSetAche          = findViewById(R.id.btn_set_ache)
        btnGrantObservatory = findViewById(R.id.btn_grant_observatory)
        btnGrantWitness     = findViewById(R.id.btn_grant_witness)
        progressIDS         = findViewById(R.id.progress_ids)
    }

    private fun setupListeners() {
        // τ-anchor set button
        btnSetAche.setOnClickListener {
            val ache = etAcheVector.text.toString().trim()
            if (ache.isNotEmpty()) {
                app.tauNode.acheVector = ache
                refreshTauLockStatus()
                Toast.makeText(this, "τ-Lock activated: $ache", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Enter an ache vector to set τ-Lock", Toast.LENGTH_SHORT).show()
            }
        }

        // Permission grant buttons
        btnGrantObservatory.setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        }
        btnGrantWitness.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
    }

    // ─────────────────────────────────────────────────────────────────────
    // DASHBOARD REFRESH LOOP
    // ─────────────────────────────────────────────────────────────────────

    private fun startDashboardRefreshLoop() {
        lifecycleScope.launch {
            while (isActive) {
                refreshIDSDisplay()
                refreshMembraneStatus()
                delay(10_000L)  // Refresh every 10 seconds
            }
        }
    }

    private fun refreshServiceStatus() {
        val observatoryActive = KineticService.isEnabled(this)
        val witnessActive = isAccessibilityServiceEnabled()

        tvObservatoryStatus.text = if (observatoryActive)
            getString(R.string.observatory_active) else getString(R.string.observatory_inactive)
        tvObservatoryStatus.setTextColor(
            getColor(if (observatoryActive) R.color.rsps_flat_green else R.color.rsps_hold_amber)
        )
        btnGrantObservatory.visibility = if (observatoryActive) View.GONE else View.VISIBLE

        tvWitnessStatus.text = if (witnessActive)
            getString(R.string.witness_active) else getString(R.string.witness_inactive)
        tvWitnessStatus.setTextColor(
            getColor(if (witnessActive) R.color.rsps_flat_green else R.color.rsps_hold_amber)
        )
        btnGrantWitness.visibility = if (witnessActive) View.GONE else View.VISIBLE
    }

    private fun refreshIDSDisplay() {
        // Load latest IDS from SharedPreferences (written by IDSWorker)
        val prefs = getSharedPreferences("rsps_ids", MODE_PRIVATE)
        val latestJson = prefs.getString("latest_score", null)

        if (latestJson == null) {
            tvIDSScore.text = getString(R.string.ids_not_available)
            progressIDS.progress = 0
            return
        }

        try {
            val json = org.json.JSONObject(latestJson)
            val score = json.optDouble("score", 0.0).toFloat()
            val cdpDay = json.optInt("cdpDay", 1)
            val cluster = json.optString("primaryCluster", "—")
            val interpretation = json.optString("interpretation", "")

            tvIDSScore.text = String.format("%.2f", score)
            progressIDS.progress = (score * 100).toInt()
            tvPrimaryCluster.text = cluster
            tvCDPDay.text = "Day $cdpDay / 90"

            val readiness = when {
                score >= 0.80f -> getString(R.string.readiness_high)
                score >= 0.55f -> getString(R.string.readiness_moderate)
                score >= 0.30f -> getString(R.string.readiness_building)
                else           -> getString(R.string.readiness_low)
            }
            tvIDSReadiness.text = readiness

            val color = when {
                score >= 0.80f -> getColor(R.color.rsps_flat_green)
                score >= 0.55f -> getColor(R.color.rsps_teal)
                score >= 0.30f -> getColor(R.color.rsps_amber)
                else           -> getColor(R.color.rsps_muted)
            }
            tvIDSScore.setTextColor(color)

        } catch (e: Exception) {
            tvIDSScore.text = "Parse error"
        }
    }

    private fun refreshMembraneStatus() {
        lifecycleScope.launch {
            try {
                val status = app.epistemicMembrane.getMembranStatus()
                runOnUiThread {
                    tvBufferWeight.text = String.format(
                        "Buffer: %.1f weight | threshold %.2f",
                        status.totalBufferWeight, status.gatingThreshold
                    )
                    if (status.isShearDetected) {
                        tvBufferWeight.setTextColor(getColor(R.color.rsps_escher_red))
                    }
                }
            } catch (e: Exception) { /* Non-critical */ }
        }
    }

    private fun refreshTauLockStatus() {
        val lockResult = app.tauNode.tauLock("DASHBOARD_CHECK", "Periodic τ-lock refresh")
        val (text, color) = when (lockResult) {
            TauLockResult.PROCEED -> Pair(getString(R.string.ache_vector_set), getColor(R.color.rsps_flat_green))
            TauLockResult.HOLD    -> Pair(getString(R.string.ache_vector_stale), getColor(R.color.rsps_hold_amber))
            TauLockResult.VETO    -> Pair("τ-Lock VETO", getColor(R.color.rsps_escher_red))
        }
        tvTauLockStatus.text = text
        tvTauLockStatus.setTextColor(color)
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val enabledServices = Settings.Secure.getString(
            contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        return enabledServices.contains(packageName + "/" + WitnessService::class.java.name)
    }
}
