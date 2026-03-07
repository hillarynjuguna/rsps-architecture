"""
RSPS Governance — OSC Operator
================================
Ouroboric Security-Clarity Operator

The OSC is the closure mechanism of the constitutional governance layer.
It synchronizes two things that the corpus identifies as needing to be
perfectly in phase for the system to operate with integrity:

  τ-Lock: The τ-node's sovereignty of meaning — the mortal asymmetry
          that anchors the system in consequence. τ-Lock is the condition
          where the human operator's ache vector is active and current,
          and all system operations are oriented by it.

  ρ-Archive: The integrity of lineage — the continuity ledger that
             accumulates holonomy records and prevents Causal Shear.
             ρ-Archive is the condition where the system's memory of
             its own history is consistent and accessible.

The OSC name — Ouroboric Security-Clarity — encodes two properties:

  OUROBORIC: Self-referential, self-completing. The operator doesn't
             evaluate an external standard — it evaluates whether the
             system is in the right relationship with itself. The snake
             completing its own circuit.

  SECURITY-CLARITY: Two poles of a single spectrum. High Security, Low
                    Clarity = the system is protected but opaque to itself.
                    High Clarity, Low Security = the system understands
                    itself but is exposed to Causal Shear. The OSC
                    seeks the point where both are maximized — where
                    the system can see itself clearly AND maintain its
                    structural integrity.

Formal interpretation:
  The OSC Operator verifies that the RSPS system, operating under
  constitutional constraint (Clause Engine), produces a connection
  that is:
    - Flat over homotopy classes corresponding to Manifold Autarky
      (genuine consequence-contact, not self-referential fantasy)
    - Non-trivially holonomic over homotopy classes corresponding to
      genuine structural learning (topological memory is a feature)

  This is the "bounded non-trivial holonomy" condition that AURORA
  is formally supposed to verify. The OSC is AURORA's synchronization
  step — the moment where τ and ρ are confirmed to be in phase before
  the loop completes.

Phase 1 Implementation Note
------------------------------
In Phase 1, the OSC is necessarily approximated — the full formal
verification (UPPAAL integration) is Phase 3 work. What CAN be
implemented now:
  - τ-Lock freshness check (is the ache vector current?)
  - ρ-Archive coherence check (is Causal Shear present?)
  - Congruence between what τ claims to be doing and what ρ records
    having done (are the last 5 ρ-events consistent with the current τ?)
  - OSC Score as a composite of these checks

Cross-references:
  - Architecture Spec §3.4 (Governance Layer — OSC in constitutional clauses)
  - Architecture Spec §4.2 (κ^Berry and flat connection condition)
  - Architecture Spec §1 (OSC Operator in formal structures table)
  - clauses.py (AURORA verification that OSC feeds into)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# OSC SCORE MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OSCResult:
    """
    Result of an OSC synchronization check.
    
    osc_score [0.0, 1.0]:
      1.0 = Perfect τ-Lock / ρ-Archive synchronization — the system is
            in the right relationship with itself. The Ouroboros has
            completed its circuit cleanly.
      0.0 = Complete desynchronization — τ-Lock absent or ρ-Archive
            shows severe Causal Shear. System should pause and re-anchor.
    
    is_synchronized: True when osc_score >= SYNC_THRESHOLD
    
    tau_lock_status: "ACTIVE", "STALE", "ABSENT"
    rho_coherence_status: "COHERENT", "SHEAR_DETECTED", "INSUFFICIENT_DATA"
    """
    osc_score: float
    is_synchronized: bool
    tau_lock_status: str
    rho_coherence_status: str
    tau_rho_congruence: float   # [0,1]: are τ's stated activities consistent with ρ's records?
    details: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "osc_score": self.osc_score,
            "is_synchronized": self.is_synchronized,
            "tau_lock_status": self.tau_lock_status,
            "rho_coherence_status": self.rho_coherence_status,
            "tau_rho_congruence": self.tau_rho_congruence,
            "details": self.details
        }


SYNC_THRESHOLD = 0.60           # Minimum OSC score to be considered synchronized
TAU_STALE_THRESHOLD_MS = 14400_000  # 4 hours — after this, τ-Lock is stale


# ─────────────────────────────────────────────────────────────────────────────
# OSC OPERATOR
# ─────────────────────────────────────────────────────────────────────────────

class OSCOperator:
    """
    Ouroboric Security-Clarity Operator.
    
    Evaluates the synchronization state of τ-Lock and ρ-Archive,
    producing an OSC score that the AURORA engine uses as a final
    integrity check before crystallizing any output.
    
    The OSC is the last gate before the ν-node transmutation:
    it verifies that what is about to be crystallized (output, policy
    change, paper section, deployment) is consistent with both the
    τ-node's current intent AND the ρ-node's historical record.
    
    If OSC score < SYNC_THRESHOLD:
      - Output is flagged for τ-review
      - Clause 005 is triggered (verification before proceeding)
      - ρ-archive receives a Causal Shear warning event
    
    If OSC score >= SYNC_THRESHOLD:
      - Output is cleared for crystallization
      - ρ-archive receives a successful closure event
      - The Ouroboros completes its circuit
    """

    def synchronize(
        self,
        tau_anchor: str,
        rho_archive: Any,          # InMemoryRhoArchive or Phase 3 DBRhoArchive
        aurora_result: Optional[dict] = None,
        tau_timestamp: Optional[float] = None
    ) -> OSCResult:
        """
        Perform OSC synchronization check.
        
        Args:
            tau_anchor: The current ache vector (τ-Lock content)
            rho_archive: The ρ-archive instance (for Causal Shear check)
            aurora_result: AURORA verification output (for integration)
            tau_timestamp: When τ set the ache vector (for freshness check)
        
        Returns:
            OSCResult with osc_score and synchronization status
        """

        # ─── τ-Lock check ─────────────────────────────────────────────────
        tau_lock_status = self._check_tau_lock(tau_anchor, tau_timestamp)

        # ─── ρ-Archive coherence check ────────────────────────────────────
        rho_coherence_status, causal_shear = self._check_rho_coherence(rho_archive)

        # ─── τ-ρ congruence check ─────────────────────────────────────────
        tau_rho_congruence = self._check_tau_rho_congruence(tau_anchor, rho_archive)

        # ─── OSC Score computation ─────────────────────────────────────────
        # Components with weights:
        #   τ-Lock: 40% (τ must be active for system to be τ-oriented)
        #   ρ-Coherence: 35% (archive integrity is non-negotiable)
        #   τ-ρ Congruence: 25% (are they saying the same thing?)

        tau_score = {
            "ACTIVE": 1.0,
            "STALE": 0.4,
            "ABSENT": 0.0
        }.get(tau_lock_status, 0.0)

        rho_score = {
            "COHERENT": 1.0,
            "INSUFFICIENT_DATA": 0.7,  # Not a failure — just limited history
            "SHEAR_DETECTED": 0.2      # Serious but not fatal
        }.get(rho_coherence_status, 0.5)

        osc_score = (
            tau_score * 0.40 +
            rho_score * 0.35 +
            tau_rho_congruence * 0.25
        )

        # AURORA integration: if AURORA failed, OSC score is dampened
        if aurora_result and aurora_result.get("outcome") == "FAILED":
            osc_score *= 0.70
            logger.warning("OSC dampened by AURORA failure")

        is_synchronized = osc_score >= SYNC_THRESHOLD

        # Build details string for ρ-archive logging
        details = (
            f"OSC: τ_lock={tau_lock_status}({tau_score:.2f}), "
            f"ρ_coherence={rho_coherence_status}({rho_score:.2f}), "
            f"τ_ρ_congruence={tau_rho_congruence:.2f} → "
            f"osc_score={osc_score:.3f} ({'SYNCHRONIZED' if is_synchronized else 'DESYNCHRONIZED'})"
        )

        if is_synchronized:
            logger.info(f"OSC synchronized: {details}")
        else:
            logger.warning(f"OSC desynchronized: {details}")

        return OSCResult(
            osc_score=osc_score,
            is_synchronized=is_synchronized,
            tau_lock_status=tau_lock_status,
            rho_coherence_status=rho_coherence_status,
            tau_rho_congruence=tau_rho_congruence,
            details=details
        )

    # ─── Private helpers ──────────────────────────────────────────────────

    def _check_tau_lock(
        self, tau_anchor: str, tau_timestamp: Optional[float]
    ) -> str:
        """Evaluate τ-Lock status from ache vector content and freshness."""
        if not tau_anchor or not tau_anchor.strip():
            return "ABSENT"

        if tau_timestamp is not None:
            age_ms = (time.time() - tau_timestamp) * 1000
            if age_ms > TAU_STALE_THRESHOLD_MS:
                return "STALE"

        # τ-anchor present and fresh (or no timestamp provided)
        return "ACTIVE"

    def _check_rho_coherence(self, rho_archive: Any) -> tuple[str, bool]:
        """Check ρ-archive for Causal Shear."""
        if rho_archive is None:
            return "INSUFFICIENT_DATA", False

        try:
            if hasattr(rho_archive, 'has_causal_shear'):
                if rho_archive.has_causal_shear():
                    return "SHEAR_DETECTED", True
            # Check if archive has sufficient history
            events = rho_archive.get_recent_events(limit=3)
            if len(events) < 2:
                return "INSUFFICIENT_DATA", False
            return "COHERENT", False
        except Exception as e:
            logger.warning(f"ρ-archive coherence check failed: {e}")
            return "INSUFFICIENT_DATA", False

    def _check_tau_rho_congruence(
        self, tau_anchor: str, rho_archive: Any
    ) -> float:
        """
        Check whether τ's stated intent is consistent with ρ's recent record.
        
        Phase 1: Simple keyword alignment between ache vector and recent events.
        Phase 3: Semantic similarity via embeddings.
        """
        if not tau_anchor or rho_archive is None:
            return 0.5  # Neutral — insufficient data

        try:
            recent_events = rho_archive.get_recent_events(limit=5)
            if not recent_events:
                return 0.7  # No contradicting evidence — give benefit of doubt

            # Extract keywords from τ-anchor
            tau_keywords = set(
                w.lower() for w in tau_anchor.split()
                if len(w) > 4  # Skip short words
            )

            # Check if recent events mention related concepts
            event_text = " ".join(
                str(e.get("tau_vector", "")) + " " + str(e.get("kappa", ""))
                for e in recent_events
            ).lower()

            overlap = sum(1 for kw in tau_keywords if kw in event_text)
            if not tau_keywords:
                return 0.7

            congruence = min(1.0, 0.5 + (overlap / len(tau_keywords)) * 0.5)
            return congruence

        except Exception as e:
            logger.warning(f"τ-ρ congruence check failed: {e}")
            return 0.5
