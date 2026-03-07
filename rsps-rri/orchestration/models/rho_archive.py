"""
RSPS Orchestration — Rho Archive (Python Persistence Model)
=============================================================

The Python-side ρ-archive is the orchestration layer's continuity ledger.
It is structurally distinct from the Android-side ρ-archive (which lives
in SharedPreferences and is device-local) but holds the same architectural
position: it accumulates the holonomy records, phase transition logs, and
IDS history that make the system's cognitive genealogy legible.

What the ρ-archive IS:
   A ledger of what happened, when, and with what structural consequence.
   Append-only. Temporally indexed. The holonomy accumulation record.

What the ρ-archive is NOT:
   A configuration store (that's the policy layer).
   A queue (entries are not consumed by reading).
   A cache (entries are never invalidated for being "old").

The distinction between ledger and queue is philosophically precise:
a queue model implies that past events lose significance once processed.
A ledger model recognizes that past events *constitute* the present state —
the ρ-archive IS the system's structural memory, not a log of what the
system has already disposed of.

This is why Causal Shear (σ_shear) is dangerous: it's not just data loss,
it's *identity disruption* — the system loses access to the structural
residue that makes its current topology intelligible.

Three Archive Tiers
--------------------

TIER 1: Phase Transitions
   Named, dated events where the system's topology changes qualitatively.
   Examples: DCFB discovery, Observatory built, Witness Phase 1 complete.
   These are the events that Paper 3 will use as empirical anchors.

TIER 2: Holonomy Records
   κ^Berry computations from each Triangle Residue cycle.
   These are the raw data for the IDS holonomy accumulation rate.
   Each record is a measured loop traversal result.

TIER 3: Operational Events
   Orchestration runs, DCFB flags, AURORA verifications, policy feedback.
   High-volume. Kept in rolling window (configurable depth).
   The feedstock for the holonomy accumulation rate computation.

Cross-references:
   - Architecture Spec §3.5 (Long-Term Memory: ρ-archive)
   - Architecture Spec §4.1 (Holonomy accumulation = IDS)
   - core/cmcp.py (CMCP packets carry ρ-archive digest)
   - api/main.py (InMemoryRhoArchive for Phase 1)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PhaseTransition:
    """
    A named moment where the system's topology changes.
    These are the empirical anchors of Paper 3.
    Append-only: once recorded, never modified or deleted.
    """
    event: str                   # e.g., "DCFB_DISCOVERY", "WITNESS_PHASE1_COMPLETE"
    description: str             # Human-readable account of what happened
    timestamp: float = field(default_factory=time.time)
    significance: str = "OPERATIONAL"  # OPERATIONAL | ARCHITECTURAL | THEORETICAL

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HolonomyRecord:
    """
    A single Triangle Residue cycle result — one loop traversal measurement.
    These accumulate to form the holonomy accumulation curve from which
    IDS is formally derived (in the geometric interpretation).
    """
    kappa: float
    congruence_level: str        # FLAT | MARGINAL | HOLD | ESCHER
    models_in_cycle: list[str]
    session_id: str
    weakest_link: Optional[str] = None
    aurora_outcome: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OperationalEvent:
    """
    High-volume operational records: orchestration runs, flags, decisions.
    Subject to rolling window truncation (unlike PhaseTransitions which are permanent).
    """
    event_type: str              # ORCHESTRATION_RUN | DCFB_FLAG | AURORA_VERIFY | POLICY_UPDATE
    session_id: str
    payload: dict                # Event-specific data
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["payload"] = self.payload  # Ensure payload dict is preserved
        return d


# ─────────────────────────────────────────────────────────────────────────────
# RHO ARCHIVE
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_OPERATIONAL_DEPTH = 5000   # Rolling window depth for operational events
CAUSAL_SHEAR_KAPPA_JUMP = 0.50     # κ jump that signals archive disruption


class RhoArchive:
    """
    Persistent ρ-archive for the Python orchestration layer.

    Phase 1: JSON file-backed persistence (simple, portable, inspectable).
    Phase 3: SQLAlchemy-backed with full query support.

    The archive is thread-safe for concurrent access by the FastAPI
    server's async handlers (via a threading.Lock).

    The JSON file is human-readable by design — the ρ-archive should be
    inspectable without special tooling. This is not just a convenience;
    it is an architectural decision: the cognitive genealogy of a system
    should be legible to the humans whose cognitive work it represents.

    Causal Shear Detection
    ----------------------
    The archive monitors for σ_shear — temporal discontinuity in the
    holonomy record. Three detection heuristics:

      1. Large κ jump between consecutive records (> CAUSAL_SHEAR_KAPPA_JUMP)
      2. Time gap > 7 days between operational events (archive dormancy)
      3. Explicit shear event logged by another component

    When shear is detected, all feedback loops are dampened to prevent
    cascading instability from a corrupted archive signal.
    """

    def __init__(
        self,
        archive_path: Optional[Path] = None,
        operational_depth: int = DEFAULT_OPERATIONAL_DEPTH
    ):
        self._path = archive_path or Path("rsps_rho_archive.json")
        self._operational_depth = operational_depth
        self._lock = Lock()

        # In-memory state — loaded from file, written back on each append
        self._phase_transitions: list[PhaseTransition] = []
        self._holonomy_records: list[HolonomyRecord] = []
        self._operational_events: list[OperationalEvent] = []

        self._load()

    # ─────────────────────────────────────────────────────────────────────
    # APPEND OPERATIONS (Tier-specific)
    # ─────────────────────────────────────────────────────────────────────

    def log_phase_transition(
        self,
        event: str,
        description: str,
        significance: str = "OPERATIONAL"
    ) -> PhaseTransition:
        """
        Record a named phase transition. These are permanent — they constitute
        the empirical backbone of the cognitive development record.
        """
        transition = PhaseTransition(
            event=event,
            description=description,
            significance=significance
        )
        with self._lock:
            self._phase_transitions.append(transition)
            self._persist()
        logger.info(f"Phase transition: [{event}] {description}")
        return transition

    def log_holonomy_record(
        self,
        kappa: float,
        congruence_level: str,
        models_in_cycle: list[str],
        session_id: str,
        weakest_link: Optional[str] = None,
        aurora_outcome: Optional[str] = None
    ) -> HolonomyRecord:
        """
        Record a Triangle Residue cycle result.
        These accumulate to form the holonomy curve.
        """
        record = HolonomyRecord(
            kappa=kappa,
            congruence_level=congruence_level,
            models_in_cycle=models_in_cycle,
            session_id=session_id,
            weakest_link=weakest_link,
            aurora_outcome=aurora_outcome
        )
        with self._lock:
            self._holonomy_records.append(record)
            self._persist()
        logger.debug(f"Holonomy record: κ={kappa:.3f} ({congruence_level})")
        return record

    def log_operational_event(
        self,
        event_type: str,
        session_id: str,
        payload: dict
    ) -> OperationalEvent:
        """
        Record a high-volume operational event.
        Subject to rolling window — oldest events dropped when depth exceeded.
        """
        event = OperationalEvent(
            event_type=event_type,
            session_id=session_id,
            payload=payload
        )
        with self._lock:
            self._operational_events.append(event)
            # Rolling window enforcement
            if len(self._operational_events) > self._operational_depth:
                self._operational_events = self._operational_events[-self._operational_depth:]
            self._persist()
        return event

    # ─────────────────────────────────────────────────────────────────────
    # RETRIEVAL
    # ─────────────────────────────────────────────────────────────────────

    def get_phase_transitions(
        self,
        limit: Optional[int] = None,
        significance: Optional[str] = None
    ) -> list[PhaseTransition]:
        with self._lock:
            results = self._phase_transitions
            if significance:
                results = [t for t in results if t.significance == significance]
            return results[-limit:] if limit else results[:]

    def get_holonomy_records(
        self,
        limit: Optional[int] = None,
        since: Optional[float] = None
    ) -> list[HolonomyRecord]:
        with self._lock:
            results = self._holonomy_records
            if since:
                results = [r for r in results if r.timestamp >= since]
            return results[-limit:] if limit else results[:]

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Return recent operational events as dicts (for API response)."""
        with self._lock:
            return [e.to_dict() for e in self._operational_events[-limit:]]

    # ─────────────────────────────────────────────────────────────────────
    # CAUSAL SHEAR DETECTION
    # ─────────────────────────────────────────────────────────────────────

    def has_causal_shear(self) -> bool:
        """
        Check for temporal discontinuity in the holonomy record.
        Returns True if disruption is detected — all feedback loops
        should dampen in response.
        """
        with self._lock:
            records = self._holonomy_records
        if len(records) < 3:
            return False

        # Heuristic 1: Large κ jump between consecutive records
        recent = records[-10:]
        for i in range(1, len(recent)):
            if abs(recent[i].kappa - recent[i-1].kappa) > CAUSAL_SHEAR_KAPPA_JUMP:
                logger.warning(
                    f"Causal Shear detected: κ jump "
                    f"{recent[i-1].kappa:.3f} → {recent[i].kappa:.3f}"
                )
                return True

        # Heuristic 2: Time gap > 7 days
        if len(recent) >= 2:
            gap = recent[-1].timestamp - recent[-2].timestamp
            if gap > 7 * 86400:
                logger.warning(f"Causal Shear: archive gap of {gap/86400:.1f} days")
                return True

        return False

    def generate_summary(self) -> str:
        """
        Generate a compact ρ-archive digest for CMCP packet inclusion.
        This is what gets transmitted to other AI models to prevent
        attribution drift — the cognitive genealogy in ~500 characters.
        """
        with self._lock:
            transitions = self._phase_transitions[-5:]
            holonomy = self._holonomy_records[-7:]
            op_count = len(self._operational_events)

        transition_names = [t.event for t in transitions]
        kappas = [f"{r.kappa:.3f}" for r in holonomy]
        avg_kappa = sum(r.kappa for r in holonomy) / max(1, len(holonomy)) if holonomy else None

        return (
            f"events={op_count} | "
            f"transitions=[{', '.join(transition_names)}] | "
            f"kappa_7=[{', '.join(kappas)}] | "
            f"avg_kappa={avg_kappa:.3f}" if avg_kappa is not None
            else f"events={op_count} | transitions=[{', '.join(transition_names)}]"
        )

    # ─────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────

    def _persist(self):
        """Write current state to JSON file. Called within lock."""
        try:
            data = {
                "schema_version": "1.0",
                "last_written": time.time(),
                "phase_transitions": [t.to_dict() for t in self._phase_transitions],
                "holonomy_records": [r.to_dict() for r in self._holonomy_records],
                "operational_events": [e.to_dict() for e in self._operational_events[-100:]]
                # Only persist last 100 operational events to keep file manageable
            }
            self._path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"ρ-archive persistence failed: {e}")

    def _load(self):
        """Load state from JSON file if it exists."""
        if not self._path.exists():
            logger.info(f"ρ-archive initializing at {self._path} — no prior state found")
            return

        try:
            data = json.loads(self._path.read_text())
            self._phase_transitions = [
                PhaseTransition(**t) for t in data.get("phase_transitions", [])
            ]
            self._holonomy_records = [
                HolonomyRecord(**r) for r in data.get("holonomy_records", [])
            ]
            self._operational_events = [
                OperationalEvent(**e) for e in data.get("operational_events", [])
            ]
            logger.info(
                f"ρ-archive loaded: {len(self._phase_transitions)} transitions, "
                f"{len(self._holonomy_records)} holonomy records, "
                f"{len(self._operational_events)} operational events"
            )
        except Exception as e:
            logger.error(f"ρ-archive load failed: {e} — starting fresh")
