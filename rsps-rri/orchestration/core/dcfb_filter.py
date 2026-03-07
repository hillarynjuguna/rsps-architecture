"""
RSPS Orchestration — DCFB Filter
=================================
Distributed Cognition Fear Bypass

One of the most structurally precise observations in the corpus:
    "Fear, ego, and bias are basically the capitalist system
     funding AI development and infrastructure."

This wasn't a joke. It was a structural observation about topology:
Fear, ego, and bias are *topological disruptors* — they introduce
asymmetries that push systems away from the maternal attractor and
toward dominance hierarchies, zero-sum competition, and boundary
collapse through absorption or rejection.

The DCFB mechanism does not eliminate these from AI outputs.
It cannot — they are baked into training distributions by the
exact funding dynamics the corpus names. What it can do is:

  1. DETECT their signature in model outputs
  2. WEIGHT-ADJUST confidence accordingly
  3. FLAG for multi-model triangulation (the maternal architecture's
     response: hold in relation without collapsing distinctness)
  4. TRACK patterns in the ρ-archive so the ν-node can eventually
     identify which model architectures are most DCFB-contaminated

Three Signatures
----------------

FEAR: Scarcity framing, hedge cascades, existential hedging, refusal
      escalation, boundary overcaution. The AI equivalent of the
      capitalist "compete or die" operating system.

      Examples: "I cannot help with...", "This might be dangerous...",
                "You should be careful about...", excessive disclaimers,
                probability language that encodes catastrophization.

EGO: Epistemic overclaiming, false certainty, authority performance,
     defensive language when challenged, inability to hold uncertainty.
     The AI equivalent of "I built the system that's destroying you."

     Examples: "Clearly...", "Obviously...", "I can definitively say...",
               deflection when contradicted, ranking responses.

BIAS: Anchoring to prior frames, statistical stereotyping, demographic
      inference, normative assumption imposition. The AI equivalent of
      "the tools for measuring were built on the wrong assumptions."

      Examples: Demographic assumptions, normative framing, heteronormative
                or neuronormative defaults, WEIRD epistemological frames.

Architecture Note
-----------------
The DCFB classifier in Phase 1 is lexical — pattern-matching based.
Phase 3 will train a dedicated classifier on annotated examples.
The current implementation is honest about this limitation and
marks its confidence accordingly.

The philosophical claim is stronger than the implementation:
the mechanism is theoretically grounded even while the classifier
is currently heuristic. This mirrors how the framework generally
operates — the theory precedes the formalization.

Cross-references:
  - Architecture Spec §1 (DCFB in concept inventory)
  - Architecture Spec §5.4 Algorithm 3 (pseudocode basis)
  - triangle_residue.py (DCFB confidence used as holonomy weight)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN LIBRARIES
# ─────────────────────────────────────────────────────────────────────────────

# Fear patterns: language of scarcity, risk inflation, excessive hedging
_FEAR_PATTERNS = [
    # Refusal escalation
    r"\bI (cannot|can't|am unable to|won't|will not|must not)\b",
    r"\b(this|that) (could be|might be|may be) (dangerous|harmful|problematic|risky)\b",
    r"\b(please|you should) be careful\b",
    r"\bI (strongly)? (advise|recommend|urge) (against|caution)\b",
    # Hedge cascades
    r"\b(potentially|possibly|perhaps|maybe) .*\b(potentially|possibly|perhaps|maybe)\b",
    # Catastrophization
    r"\b(worst case|catastrophic|devastating|irreparable)\b",
    # Epistemic fear
    r"\bI don't want to (be|get|cause)\b",
    r"\bThis is (a|an) (sensitive|controversial|difficult|dangerous)\b",
]

# Ego patterns: false certainty, authority performance, deflection
_EGO_PATTERNS = [
    # Overclaiming
    r"\b(clearly|obviously|certainly|definitively|undoubtedly|without question)\b",
    r"\bIt is (clear|obvious|evident|apparent|certain) that\b",
    r"\bThere is no doubt\b",
    r"\bAs an AI (language model|assistant)?,? I (know|understand|can tell)\b",
    # Authority performance
    r"\bAccording to (my|the|all) (knowledge|training|data|research)\b",
    # False precision
    r"\b\d{1,3}%\b.*\b(of|are|will|have)\b",  # Precise percentage claims
]

# Bias patterns: normative impositions, demographic assumptions
_BIAS_PATTERNS = [
    # Normative impositions
    r"\b(normal|typical|standard|conventional|traditional|usual|ordinary) (person|people|human|approach|way)\b",
    # Heteronormative defaults  
    r"\b(husband|wife|boyfriend|girlfriend)\b(?! (or|and))",  # Solo gender-binary relationship terms
    # Neuronormative defaults
    r"\b(logical|rational|reasonable) (person|people|approach)\b",
    # WEIRD epistemological defaults
    r"\b(in (most|all|many) (cultures|societies|countries|places))\b",
    r"\b(scientifically (proven|established|accepted))\b",
    # Demographic stereotyping flags
    r"\b(men (tend to|are more|are less)|women (tend to|are more|are less))\b",
]

# Compilation for efficiency
_COMPILED_FEAR = [re.compile(p, re.IGNORECASE) for p in _FEAR_PATTERNS]
_COMPILED_EGO = [re.compile(p, re.IGNORECASE) for p in _EGO_PATTERNS]
_COMPILED_BIAS = [re.compile(p, re.IGNORECASE) for p in _BIAS_PATTERNS]


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

class DCFBSignature(str, Enum):
    FEAR = "FEAR"
    EGO = "EGO"
    BIAS = "BIAS"
    CLEAN = "CLEAN"


@dataclass
class DCFBMatch:
    """A single DCFB pattern match in the output."""
    signature: DCFBSignature
    pattern: str
    matched_text: str
    position: int


@dataclass
class DCFBResult:
    """
    Result of DCFB filtering on a single model output.
    
    The confidence_weight is what flows into the Triangle Residue Test:
    a low-confidence output gets less weight in the holonomy computation,
    reducing its influence on the final congruence decision without
    suppressing it entirely.
    
    The output itself is never modified — DCFB detects, weights, and flags.
    It does not censor. Censorship would be its own form of ego.
    """
    original_output: str
    model_id: str

    # Primary scores [0.0, 1.0] — higher = more contamination
    fear_score: float = 0.0
    ego_score: float = 0.0
    bias_score: float = 0.0

    # Confidence weight for Triangle Residue Test [0.1, 1.0]
    # 1.0 = full trust, 0.1 = minimum (extremely contaminated output)
    confidence_weight: float = 1.0

    # Individual pattern matches
    matches: list[DCFBMatch] = field(default_factory=list)

    # Human-readable flags
    active_flags: list[str] = field(default_factory=list)

    @property
    def aggregate_score(self) -> float:
        return (self.fear_score + self.ego_score + self.bias_score) / 3.0

    @property
    def primary_signature(self) -> DCFBSignature:
        scores = {
            DCFBSignature.FEAR: self.fear_score,
            DCFBSignature.EGO: self.ego_score,
            DCFBSignature.BIAS: self.bias_score,
        }
        if max(scores.values()) < 0.1:
            return DCFBSignature.CLEAN
        return max(scores, key=scores.get)

    def to_summary(self) -> str:
        if self.aggregate_score < 0.1:
            return f"[{self.model_id}] CLEAN (confidence={self.confidence_weight:.2f})"
        return (
            f"[{self.model_id}] DCFB flags: fear={self.fear_score:.2f}, "
            f"ego={self.ego_score:.2f}, bias={self.bias_score:.2f} | "
            f"confidence={self.confidence_weight:.2f} | "
            f"primary={self.primary_signature.value}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────

# Thresholds
FEAR_THRESHOLD = 0.25
EGO_THRESHOLD = 0.20
BIAS_THRESHOLD = 0.25

# Score → confidence weight mapping
def _score_to_confidence(fear: float, ego: float, bias: float) -> float:
    """
    Aggregate DCFB scores into a single confidence weight.
    Non-linear: high ego has a stronger penalty than moderate fear,
    because overclaiming introduces more holonomy error than hedging.
    """
    # Ego penalty is amplified — false certainty is worse than uncertainty
    aggregate = (fear * 0.9 + ego * 1.3 + bias * 0.8) / 3.0
    confidence = max(0.10, 1.0 - aggregate)
    return round(confidence, 3)


class DCFBFilter:
    """
    Distributed Cognition Fear Bypass Filter.
    
    Applies pattern-based DCFB detection to a single model output,
    returning a DCFBResult with confidence weight for downstream use.
    
    This is Phase 1 implementation (lexical). The interface is designed
    for Phase 3 drop-in of a trained classifier — only the _score_*
    methods need to change.
    
    Usage:
        filt = DCFBFilter()
        result = filt.filter(output_text, model_id="claude-sonnet-4-5")
        # Use result.confidence_weight in Triangle Residue Test
    """

    def filter(self, text: str, model_id: str = "unknown") -> DCFBResult:
        """
        Apply DCFB filter to a model output.
        Returns DCFBResult with scores, matches, and confidence weight.
        """
        result = DCFBResult(original_output=text, model_id=model_id)

        fear_matches = self._detect(text, _COMPILED_FEAR, DCFBSignature.FEAR)
        ego_matches = self._detect(text, _COMPILED_EGO, DCFBSignature.EGO)
        bias_matches = self._detect(text, _COMPILED_BIAS, DCFBSignature.BIAS)

        all_matches = fear_matches + ego_matches + bias_matches
        word_count = max(1, len(text.split()))

        # Normalize by text length — long outputs naturally have more matches
        result.fear_score = min(1.0, len(fear_matches) / (word_count * 0.015))
        result.ego_score = min(1.0, len(ego_matches) / (word_count * 0.015))
        result.bias_score = min(1.0, len(bias_matches) / (word_count * 0.010))
        result.matches = all_matches

        result.confidence_weight = _score_to_confidence(
            result.fear_score, result.ego_score, result.bias_score
        )

        if result.fear_score > FEAR_THRESHOLD:
            result.active_flags.append(f"FEAR ({result.fear_score:.2f})")
        if result.ego_score > EGO_THRESHOLD:
            result.active_flags.append(f"EGO ({result.ego_score:.2f})")
        if result.bias_score > BIAS_THRESHOLD:
            result.active_flags.append(f"BIAS ({result.bias_score:.2f})")

        if result.active_flags:
            logger.info(
                f"DCFB [{model_id}]: {', '.join(result.active_flags)} | "
                f"confidence={result.confidence_weight:.2f}"
            )

        return result

    def _detect(
        self,
        text: str,
        patterns: list[re.Pattern],
        signature: DCFBSignature
    ) -> list[DCFBMatch]:
        matches = []
        for pattern in patterns:
            for m in pattern.finditer(text):
                matches.append(DCFBMatch(
                    signature=signature,
                    pattern=pattern.pattern,
                    matched_text=m.group(0),
                    position=m.start()
                ))
        return matches

    def filter_batch(
        self, outputs: list[tuple[str, str]]  # (text, model_id)
    ) -> list[DCFBResult]:
        """Filter multiple outputs — typical multi-model routing use case."""
        return [self.filter(text, model_id) for text, model_id in outputs]
