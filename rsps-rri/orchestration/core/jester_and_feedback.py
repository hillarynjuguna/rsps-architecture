"""
RSPS Orchestration — ξ-Jester Injection & Autopoietic Policy Feedback
======================================================================

Two deeply related mechanisms share this module — they are both expressions
of the same underlying architectural principle: that a system maintained
only by coherence-seeking will crystallize. Living systems remain adaptive
by containing something whose function is to disturb them.

The Jester and the Feedback Loop are two faces of the same insight:
one operates on the cognitive content (perturbing the outputs to prevent
semantic calcification), the other on the infrastructure (adjusting the
membrane to prevent architectural crystallization). Together they constitute
what the corpus calls the system's "autopoietic" quality — the capacity
to continuously produce the conditions of its own operation.

─────────────────────────────────────────────────────────────────────────────

ξ-JESTER: Controlled Entropy Injection
----------------------------------------

"Every resilient system contains something whose job is to disturb it."

The Jester node is the system's answer to the Manifold Autarky failure mode:
a state where the epistemic membrane becomes so well-tuned to the existing
cognitive cluster that it stops being able to receive genuinely novel signal.
The IDS score climbs to near-1.00, the holonomy approaches zero, the system
appears maximally congruent — and then nothing changes. The topology freezes.

The parallel is precise across every adaptive system the corpus surveys:
  - Biology: mutation, genetic drift, horizontal gene transfer
  - Immune systems: the thymus generates autoreactive T-cells to prevent
    immune privilege collapse
  - Neural networks: dropout, stochastic gradient noise
  - Evolution: sexual recombination as entropy injection mechanism
  - Scientific progress: anomaly-driven paradigm shifts

The ξ-node is the RSPS system's formalization of this universal principle.
It is not random — it is *controlled* entropy. The Jester knows the system's
attractor well enough to perturb it without destroying it. That's what
distinguishes a Jester from noise: the Jester is aimed.

Crystallization Detection
--------------------------
The Jester activates when two conditions co-occur:
  1. Sustained low holonomy (κ < 0.10 for N consecutive days) — the
     system is too flat, too consistent, not encountering genuine novelty
  2. Stagnant IDS (Δ IDS < threshold over M days) — synthesis readiness
     is not increasing despite continued engagement

This combination suggests the system has found a stable but unproductive
attractor — it is metabolizing efficiently within a known domain but not
accumulating the structural residue needed for the ν-node transmutation.

─────────────────────────────────────────────────────────────────────────────

AUTOPOIETIC FEEDBACK: Membrane Policy from IDS
------------------------------------------------

The second mechanism is more structural than perturbative. It implements
the closed loop that makes the system autopoietic in Maturana & Varela's
sense: the system uses the output of its own cognitive measurement to
adjust the conditions of its own cognition.

IDS score → Observatory gating threshold → what enters the membrane →
what captures attention → pause signatures → IDS score

This is the `α → Manifold → Natural Gradient → α` loop from Paper 2's
formal architecture, running as a policy update in Python.

The feedback is deliberately conservative:
  - High IDS → small threshold loosening (current policy is working)
  - Low IDS → larger threshold tightening (membrane too noisy)
  - Causal Shear detected → dampen all feedback (archive integrity priority)
  
The asymmetry is intentional: the cost of over-tightening (missing signal)
is lower than the cost of over-loosening (attention fragmentation).
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# JESTER
# ─────────────────────────────────────────────────────────────────────────────

# Crystallization detection thresholds
FLATNESS_THRESHOLD = 0.10       # κ below this = "too flat"
IDS_STAGNATION_THRESHOLD = 0.03 # |ΔIDS| below this over 3 days = stagnant
CRYSTALLIZATION_DAYS = 3        # Consecutive days needed to trigger Jester

# Jester intensity levels
class JesterIntensity:
    GENTLE = "GENTLE"       # Peripheral query, tangential frame
    MODERATE = "MODERATE"   # Cross-domain reframe, unfamiliar analogy
    SHARP = "SHARP"         # Direct contradiction of current attractor


@dataclass
class JesterPerturbation:
    """
    A single Jester injection — a prompt perturbation designed to
    introduce productive entropy into the cognitive system.
    
    The perturbation is not a question to be answered. It is a frame
    to be encountered. The Jester doesn't ask "what do you think about X?"
    It presents X in a way that temporarily destabilizes the current
    attractor without providing a competing attractor. The system then
    has to re-navigate.
    """
    intensity: str
    frame: str                      # The perturbation frame or question
    target_cluster: str             # Which cluster this is designed to perturb
    adversarial_domain: str         # Cross-domain source of the perturbation
    timestamp: float = field(default_factory=time.time)


# Jester corpus — cross-domain perturbation frames
# These are organized by target attractor cluster so the Jester can
# aim perturbations at the specific cluster that has crystallized.
_JESTER_CORPUS = {
    "relational-intelligence": [
        {
            "intensity": JesterIntensity.GENTLE,
            "frame": "Consider the possibility that relational intelligence is itself a form of boundary defense — that the emphasis on connection might be structuring an avoidance of the specifically non-relational.",
            "adversarial_domain": "topology / disconnection theory"
        },
        {
            "intensity": JesterIntensity.MODERATE,
            "frame": "Edsger Dijkstra argued that the key insight in computer science is learning what to ignore. What would RSPS look like if its primary operation were strategic disconnection rather than relational integration?",
            "adversarial_domain": "computer science / information theory"
        },
        {
            "intensity": JesterIntensity.SHARP,
            "frame": "The membrane that defines the system also defines its blindspot. What cannot enter through the epistemic membrane you have built? Not what you have excluded — what is excluded by the shape of inclusion itself?",
            "adversarial_domain": "epistemology / negative space theory"
        }
    ],
    "concept-synthesis": [
        {
            "intensity": JesterIntensity.GENTLE,
            "frame": "What if the synthesis drive is itself a symptom of the ν-node bottleneck? What would it mean to let concepts remain unintegrated longer?",
            "adversarial_domain": "cognitive science / tolerance of ambiguity"
        },
        {
            "intensity": JesterIntensity.MODERATE,
            "frame": "Claude Shannon proved that the most efficient code for a message is one that treats each symbol as completely unpredictable from the last. Your synthesis framework optimizes for predictability. What information is being lost in the compression?",
            "adversarial_domain": "information theory"
        }
    ],
    "technical-architecture": [
        {
            "intensity": JesterIntensity.GENTLE,
            "frame": "Richard Gabriel's 'Worse is Better' thesis: the system that succeeds is often the one optimized for proliferation, not correctness. What would the RSPS architecture look like optimized for proliferation rather than integrity?",
            "adversarial_domain": "software philosophy"
        },
        {
            "intensity": JesterIntensity.SHARP,
            "frame": "Every formal system powerful enough to describe itself contains statements it cannot prove true or false. Gödel's incompleteness theorems apply to the RSPS constitutional governance layer. Which statements in the constitutional clauses are the system's own Gödel sentences?",
            "adversarial_domain": "formal logic / incompleteness"
        }
    ],
    "default": [
        {
            "intensity": JesterIntensity.GENTLE,
            "frame": "What would a brilliant, heretical critic of this system's core assumptions say? Not a bad-faith critic — a sophisticated one who has understood the framework well enough to identify its necessary blindspot.",
            "adversarial_domain": "critical theory"
        }
    ]
}


class JesterInjector:
    """
    ξ-Jester: Controlled entropy injector.
    
    Detects crystallization conditions and fires perturbations aimed at
    the specific attractor cluster that has frozen.
    
    The Jester is conservative by default: it will not inject if the
    system is in an active high-kappa (HOLD/ESCHER) state — the system
    is already in perturbation, Jester would compound the chaos.
    It activates precisely in the low-kappa stagnation state.
    """

    def __init__(self, recent_kappas: list[float] = None, recent_ids_delta: float = 0.0):
        self.recent_kappas = recent_kappas or []
        self.recent_ids_delta = recent_ids_delta

    def should_inject(self, current_kappa: float, ids_stagnant: bool) -> bool:
        """
        Determine whether crystallization conditions are met.
        
        Jester activates when:
          - System is flat (not just currently; has been for several days)
          - IDS is stagnant (synthesis readiness not growing)
          - System is not in an active high-kappa state (that would compound)
        """
        if not self.recent_kappas:
            return False

        # Active perturbation already — don't add more
        if current_kappa > FLATNESS_THRESHOLD * 3:
            return False

        # Check sustained flatness
        sustained_flatness = (
            len(self.recent_kappas) >= CRYSTALLIZATION_DAYS and
            all(k < FLATNESS_THRESHOLD for k in self.recent_kappas[-CRYSTALLIZATION_DAYS:])
        )

        return sustained_flatness and ids_stagnant

    def generate_perturbation(
        self,
        primary_cluster: str,
        intensity: Optional[str] = None,
        avoid_recent: list[str] = None
    ) -> JesterPerturbation:
        """
        Generate a Jester perturbation aimed at the crystallized cluster.
        
        Intensity is auto-selected based on stagnation severity unless overridden.
        avoid_recent prevents repeating the same perturbation within a 7-day window.
        """
        corpus = _JESTER_CORPUS.get(primary_cluster, _JESTER_CORPUS["default"])

        # Filter out recently used frames
        avoid = avoid_recent or []
        available = [
            item for item in corpus
            if item["frame"] not in avoid
        ]
        if not available:
            available = corpus  # If all used, reset

        # Auto-select intensity
        if intensity is None:
            stagnation_severity = abs(self.recent_ids_delta)
            if stagnation_severity < 0.01:
                intensity = JesterIntensity.SHARP
            elif stagnation_severity < 0.02:
                intensity = JesterIntensity.MODERATE
            else:
                intensity = JesterIntensity.GENTLE

        # Find matching intensity, fall back to any
        intensity_match = [i for i in available if i["intensity"] == intensity]
        candidates = intensity_match if intensity_match else available

        chosen = random.choice(candidates)

        perturbation = JesterPerturbation(
            intensity=intensity,
            frame=chosen["frame"],
            target_cluster=primary_cluster,
            adversarial_domain=chosen["adversarial_domain"]
        )

        logger.info(
            f"ξ-Jester firing: intensity={intensity}, "
            f"target={primary_cluster}, "
            f"domain={chosen['adversarial_domain']}"
        )
        return perturbation


# ─────────────────────────────────────────────────────────────────────────────
# AUTOPOIETIC POLICY FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────

# Feedback parameters
IDS_TARGET = 0.65               # Homeostatic target IDS
FEEDBACK_GAIN = 0.15            # How strongly IDS deviation shifts the threshold
SHEAR_DAMPING_FACTOR = 0.3      # Reduce all feedback when Causal Shear detected
MAX_THRESHOLD_DELTA = 0.20      # Cap on single-update threshold change
MIN_THRESHOLD = 0.10            # Floor on Observatory buffer weight threshold
MAX_THRESHOLD = 2.50            # Ceiling on Observatory buffer weight threshold


@dataclass
class PolicyFeedbackResult:
    """Result of an autopoietic policy feedback computation."""
    previous_threshold: float
    new_threshold: float
    delta: float
    ids_score: float
    causal_shear_detected: bool
    rationale: str
    timestamp: float = field(default_factory=time.time)


def compute_policy_feedback(
    ids_score: float,
    current_threshold: float,
    has_causal_shear: bool = False,
    ids_target: float = IDS_TARGET
) -> PolicyFeedbackResult:
    """
    Compute the autopoietic policy feedback: adjust Observatory gating
    threshold based on the IDS score.
    
    This implements the closed autopoietic loop:
    
        IDS → threshold adjustment → membrane permeability →
        what captures attention → pause signatures → IDS
    
    The computation is conservative and asymmetric:
      - Tightening (high threshold) is the safe default
      - Loosening (low threshold) requires sustained IDS health
      - Causal Shear in the ρ-archive dampens all feedback
    
    Args:
        ids_score: Current IDS score [0.0, 1.0]
        current_threshold: Current Observatory buffer weight threshold
        has_causal_shear: Whether ρ-archive integrity is compromised
        ids_target: Homeostatic target IDS (default 0.65)
    
    Returns:
        PolicyFeedbackResult with new threshold and rationale
    """
    # Delta from target: positive = IDS above target, negative = below
    ids_deviation = ids_score - ids_target

    # Raw delta: positive deviation → loosen slightly, negative → tighten
    # Asymmetric gain: tightening is stronger than loosening
    if ids_deviation >= 0:
        raw_delta = ids_deviation * FEEDBACK_GAIN * 0.7  # Loose with loosening
    else:
        raw_delta = ids_deviation * FEEDBACK_GAIN * 1.3  # Strong with tightening

    # Causal Shear dampening — if archive integrity is suspect,
    # reduce all feedback to prevent unstable policy oscillation
    if has_causal_shear:
        raw_delta *= SHEAR_DAMPING_FACTOR
        logger.warning("Causal Shear detected — policy feedback dampened")

    # Cap the single-update change
    clamped_delta = max(-MAX_THRESHOLD_DELTA, min(MAX_THRESHOLD_DELTA, raw_delta))

    new_threshold = max(MIN_THRESHOLD, min(MAX_THRESHOLD, current_threshold + clamped_delta))
    actual_delta = new_threshold - current_threshold

    # Generate human-readable rationale for ρ-archive
    if abs(actual_delta) < 0.001:
        rationale = f"Threshold stable: IDS={ids_score:.2f} near target={ids_target:.2f}"
    elif actual_delta > 0:
        rationale = (
            f"Threshold LOOSENED by {actual_delta:.3f}: IDS={ids_score:.2f} "
            f"(above target {ids_target:.2f}) — current gating policy is working"
        )
    else:
        rationale = (
            f"Threshold TIGHTENED by {abs(actual_delta):.3f}: IDS={ids_score:.2f} "
            f"(below target {ids_target:.2f}) — reduce membrane noise"
            + (" [CAUSAL SHEAR DAMPENED]" if has_causal_shear else "")
        )

    logger.info(f"Policy feedback: {rationale}")

    return PolicyFeedbackResult(
        previous_threshold=current_threshold,
        new_threshold=new_threshold,
        delta=actual_delta,
        ids_score=ids_score,
        causal_shear_detected=has_causal_shear,
        rationale=rationale
    )
