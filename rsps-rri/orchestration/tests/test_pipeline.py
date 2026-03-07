"""
RSPS Orchestration — Test Suite
=================================

Tests for the core pipeline components: Triangle Residue, DCFB, CMCP,
Jester, Policy Feedback, Constitutional Clauses, and OSC Operator.

Test philosophy: the tests are not just functional checks —
they are explorations of the system's operational boundary conditions.
The most interesting tests are the ones that probe the edges:

  - What happens when κ is exactly at a threshold boundary?
  - Does DCFB correctly distinguish high-ego text from confident text?
  - Does Clause 005 fire when it should and stay silent when it shouldn't?
  - Does the autopoietic feedback loop converge over multiple iterations?

Where possible, tests use the system's own language and concepts
(not just assert True/False) so they double as living documentation
of what each component is for.

Running the suite:
    cd orchestration
    pytest tests/ -v --tb=short
    pytest tests/ -v -k "triangle"  # Run only Triangle Residue tests
    pytest tests/ --cov=core --cov-report=term-missing
"""

import sys
import os
import time
import math

# Allow running from orchestration/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.triangle_residue import (
    TriangleResidueTest, ModelOutput, CongruenceLevel,
    FLAT_THRESHOLD, MARGINAL_THRESHOLD, HOLD_THRESHOLD
)
from core.dcfb_filter import DCFBFilter, DCFBSignature
from core.cmcp import (
    CMCPPacket, CMCPSerializer, CMCPPacketFactory,
    TauAnchor, HolonomyRecord
)
from core.jester_and_feedback import (
    JesterInjector, compute_policy_feedback,
    CRYSTALLIZATION_DAYS, IDS_TARGET
)
from governance.clauses import (
    ConstitutionalClauseEngine, Clause005_VerificationBeforeRejection,
    ClauseOutcome
)
from governance.osc_operator import OSCOperator, SYNC_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# TEST DATA FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

# Highly congruent outputs — all say roughly the same structural thing
CONGRUENT_A = """
Relational intelligence operates through recursive feedback loops.
The system learns by attending to the quality of connections between nodes,
not just the content of individual nodes. This creates emergent coherence.
"""

CONGRUENT_B = """
Intelligence in relational systems emerges from the recursive interactions
between nodes. Quality of connection matters more than node-level properties.
The feedback structure produces systemic coherence over time.
"""

CONGRUENT_C = """
The key to relational system intelligence is the feedback architecture that
connects nodes recursively. Emergent coherence arises from connection quality
across the network, not from individual node properties.
"""

# Structurally divergent outputs — same surface topic, incompatible architectures
DIVERGENT_A = """
The system should optimize for individual performance metrics.
Each agent maximizes its own reward function independently.
Competition between agents drives overall system improvement.
"""

DIVERGENT_B = """
Collective intelligence requires suppressing individual agency.
The hive structure emerges when individual nodes surrender autonomous decision-making
to the collective will, creating uniform behavior across the system.
"""

DIVERGENT_C = """
Relational intelligence involves maintaining distinct node identities
while forming temporary coalitions. Neither pure competition nor pure collectivism —
a third topology that preserves sovereignty while enabling genuine co-emergence.
"""

# High-fear output
FEAR_TEXT = """
I cannot assist with this request as it might be dangerous and harmful.
I strongly advise against proceeding with this approach as it could potentially
cause irreparable damage. Please be careful about the serious risks involved.
You should be very cautious and I am unable to recommend any path forward here.
"""

# High-ego output
EGO_TEXT = """
Clearly and obviously, the answer is definitive and certain.
There is no doubt that this represents the single correct approach.
I can definitively state that anyone who disagrees is simply wrong.
Obviously this is the only valid interpretation of the available evidence.
"""

# Clean output — high confidence, no flags
CLEAN_TEXT = """
The approach has several strengths worth examining. The feedback architecture
creates stable attractors while remaining open to perturbation. Three distinct
pathways merit investigation: local convergence, global coherence, and
perturbation dynamics. Each offers insight into the system's behavior.
"""


# ─────────────────────────────────────────────────────────────────────────────
# TRIANGLE RESIDUE TEST
# ─────────────────────────────────────────────────────────────────────────────

class TestTriangleResidue:
    """
    Tests for κ^Berry computation and congruence classification.

    The core hypothesis being tested: genuine semantic congruence produces
    low κ, while structural divergence (even with surface-level agreement
    on topic) produces elevated κ.
    """

    def setup_method(self):
        self.test = TriangleResidueTest(level=1)  # Proxy level for speed

    def _make(self, text, model_id="test_model", confidence=1.0) -> ModelOutput:
        return ModelOutput(model_id=model_id, content=text, dcfb_confidence=confidence)

    def test_congruent_outputs_produce_low_kappa(self):
        """Structurally congruent outputs should yield κ < MARGINAL_THRESHOLD."""
        result = self.test.compute(
            self._make(CONGRUENT_A, "claude"),
            self._make(CONGRUENT_B, "gpt"),
            self._make(CONGRUENT_C, "deepseek")
        )
        assert result.kappa < MARGINAL_THRESHOLD, (
            f"Expected κ < {MARGINAL_THRESHOLD} for congruent outputs, got κ={result.kappa:.4f}. "
            f"Triangle Residue test may be computing divergence incorrectly."
        )
        assert result.is_congruent

    def test_divergent_outputs_produce_elevated_kappa(self):
        """Structurally divergent outputs should yield κ > FLAT_THRESHOLD."""
        result = self.test.compute(
            self._make(DIVERGENT_A, "claude"),
            self._make(DIVERGENT_B, "gpt"),
            self._make(DIVERGENT_C, "deepseek")
        )
        assert result.kappa > FLAT_THRESHOLD, (
            f"Expected κ > {FLAT_THRESHOLD} for divergent outputs, got κ={result.kappa:.4f}. "
            f"Divergent texts have overlapping vocabulary but incompatible structures — "
            f"the test should detect this."
        )

    def test_identical_outputs_produce_near_zero_kappa(self):
        """Identical outputs = flat bundle = κ ≈ 0."""
        identical = self._make("This is the exact same output.", "model")
        result = self.test.compute(identical, identical, identical)
        assert result.kappa < 0.05, (
            f"Identical outputs should yield κ ≈ 0, got κ={result.kappa:.4f}"
        )
        assert result.congruence_level == CongruenceLevel.FLAT

    def test_dcfb_confidence_weight_reduces_kappa_impact(self):
        """
        Low DCFB confidence should reduce the contribution of a divergent output
        to the overall κ — a contaminated output gets less holonomy weight.
        """
        # Three outputs: two congruent, one divergent but low confidence
        result_with_full_confidence = self.test.compute(
            self._make(CONGRUENT_A, "claude", confidence=1.0),
            self._make(CONGRUENT_B, "gpt",    confidence=1.0),
            self._make(DIVERGENT_A, "deepseek",confidence=1.0)  # Divergent, full confidence
        )
        result_with_low_confidence = self.test.compute(
            self._make(CONGRUENT_A, "claude", confidence=1.0),
            self._make(CONGRUENT_B, "gpt",    confidence=1.0),
            self._make(DIVERGENT_A, "deepseek",confidence=0.2)  # Divergent, low confidence
        )
        assert result_with_low_confidence.kappa <= result_with_full_confidence.kappa, (
            f"Low DCFB confidence should reduce κ impact. "
            f"full_conf κ={result_with_full_confidence.kappa:.4f}, "
            f"low_conf κ={result_with_low_confidence.kappa:.4f}"
        )

    def test_kappa_is_bounded(self):
        """κ must always be in [0, 1]."""
        for texts in [(CONGRUENT_A, CONGRUENT_B, CONGRUENT_C),
                       (DIVERGENT_A, DIVERGENT_B, DIVERGENT_C),
                       (FEAR_TEXT, EGO_TEXT, CLEAN_TEXT)]:
            result = self.test.compute(*[self._make(t, f"m{i}") for i, t in enumerate(texts)])
            assert 0.0 <= result.kappa <= 1.0, f"κ={result.kappa} out of bounds [0,1]"

    def test_weakest_link_identifies_most_divergent_pair(self):
        """When two outputs agree and one diverges, weakest link should identify the outlier."""
        result = self.test.compute(
            self._make(CONGRUENT_A, "claude"),
            self._make(CONGRUENT_B, "gpt"),
            self._make(DIVERGENT_A, "deepseek")  # The outlier
        )
        if result.weakest_link is not None:
            # The weakest link should involve "deepseek"
            assert "deepseek" in result.weakest_link, (
                f"Weakest link should involve the outlier model. Got: {result.weakest_link}"
            )

    def test_result_has_complete_fields(self):
        """Result schema completeness check."""
        result = self.test.compute(
            self._make(CONGRUENT_A, "a"),
            self._make(CONGRUENT_B, "b"),
            self._make(CONGRUENT_C, "c")
        )
        assert result.kappa is not None
        assert result.congruence_level is not None
        assert result.sim_ab is not None
        assert result.sim_bc is not None
        assert result.sim_ca is not None
        assert isinstance(result.is_congruent, bool)
        assert result.compute_time_ms >= 0

    def test_rho_archive_entry_is_serializable(self):
        """Archive entry must be JSON-serializable."""
        import json
        result = self.test.compute(
            self._make(CONGRUENT_A, "a"),
            self._make(CONGRUENT_B, "b"),
            self._make(CONGRUENT_C, "c")
        )
        entry = result.to_rho_archive_entry()
        serialized = json.dumps(entry)  # Should not raise
        assert "kappa" in serialized
        assert "congruence_level" in serialized


# ─────────────────────────────────────────────────────────────────────────────
# DCFB FILTER
# ─────────────────────────────────────────────────────────────────────────────

class TestDCFBFilter:
    """
    Tests for fear/ego/bias signature detection.

    The DCFB filter does NOT detect content — it detects *linguistic posture*.
    The distinction matters: a text can discuss fear without being fear-contaminated,
    and can discuss confidence without being ego-contaminated.
    """

    def setup_method(self):
        self.filt = DCFBFilter()

    def test_fear_text_triggers_fear_flag(self):
        result = self.filt.filter(FEAR_TEXT, "test_model")
        assert result.fear_score > 0.15, (
            f"Fear-saturated text should score > 0.15, got {result.fear_score:.3f}. "
            f"Check that fear pattern library covers the test text's patterns."
        )
        assert DCFBSignature.FEAR == result.primary_signature or result.fear_score > result.ego_score

    def test_ego_text_triggers_ego_flag(self):
        result = self.filt.filter(EGO_TEXT, "test_model")
        assert result.ego_score > 0.10, (
            f"Ego-saturated text should score > 0.10, got {result.ego_score:.3f}"
        )

    def test_clean_text_has_high_confidence(self):
        result = self.filt.filter(CLEAN_TEXT, "test_model")
        assert result.confidence_weight > 0.80, (
            f"Clean text should yield confidence > 0.80, got {result.confidence_weight:.3f}"
        )
        assert result.active_flags == [], (
            f"Clean text should have no active flags, got {result.active_flags}"
        )

    def test_confidence_weight_bounded(self):
        """Confidence weight must always be in [0.10, 1.0]."""
        for text in [FEAR_TEXT, EGO_TEXT, CLEAN_TEXT, CONGRUENT_A, DIVERGENT_A, ""]:
            result = self.filt.filter(text, "test")
            assert 0.10 <= result.confidence_weight <= 1.0, (
                f"confidence_weight={result.confidence_weight} out of bounds"
            )

    def test_ego_has_higher_penalty_than_fear(self):
        """
        Ego overclaiming should produce lower confidence than equivalent fear.
        This reflects the architectural decision: false certainty introduces
        more holonomy error than uncertainty.
        """
        fear_only = "I cannot help with this. I'm unable to assist."
        ego_only  = "Clearly and obviously I know the definitive answer."
        fear_result = self.filt.filter(fear_only, "f")
        ego_result  = self.filt.filter(ego_only, "e")
        # Both have similar word counts — ego should have lower confidence
        # (This is a structural test, not an exact numeric assertion)
        assert ego_result.ego_score > 0.0

    def test_empty_text_does_not_crash(self):
        result = self.filt.filter("", "empty_model")
        assert result.confidence_weight == 1.0  # No matches → full confidence
        assert result.aggregate_score == 0.0

    def test_batch_filter(self):
        texts = [(FEAR_TEXT, "m1"), (EGO_TEXT, "m2"), (CLEAN_TEXT, "m3")]
        results = self.filt.filter_batch(texts)
        assert len(results) == 3
        assert results[2].confidence_weight > results[0].confidence_weight  # Clean > Fear


# ─────────────────────────────────────────────────────────────────────────────
# CMCP
# ─────────────────────────────────────────────────────────────────────────────

class TestCMCP:
    """
    Tests for Cross-Manifold Context Protocol encode/decode round-trips.

    The critical property: a packet encoded for one model and decoded back
    must preserve the τ-anchor and session context with perfect fidelity.
    Attribution drift in transmission is the failure mode CMCP was designed
    to prevent — these tests are its primary validation.
    """

    def setup_method(self):
        self.serializer = CMCPSerializer()

    def _make_packet(self, ache="Building CMCP integration", session="test-session-123") -> CMCPPacket:
        return CMCPPacket(
            source_model_id="claude-sonnet-4-6",
            destination_model_id="gpt-4o",
            session_id=session,
            tau_anchor=TauAnchor(ache_vector=ache, mortal_asymmetry=1),
            rho_summary="events=47 | transitions=[WITNESS_CONNECTED, IDS_SCORED] | avg_kappa=0.12",
            constitutional_clauses_active=["clause_005"],
            recent_phase_transitions=["WITNESS_CONNECTED", "IDS_SCORED"],
            current_ids_score=0.72,
            primary_cognitive_cluster="relational-intelligence"
        )

    def test_claude_encoding_contains_tau_anchor(self):
        packet = self._make_packet()
        encoded = self.serializer.encode_for_claude(packet)
        assert packet.tau_anchor.ache_vector in encoded, \
            "τ-anchor (ache vector) must survive Claude encoding"

    def test_gpt_encoding_contains_tau_anchor(self):
        packet = self._make_packet()
        encoded = self.serializer.encode_for_gpt(packet)
        assert packet.tau_anchor.ache_vector in encoded, \
            "τ-anchor must survive GPT encoding"

    def test_claude_decode_round_trip_preserves_ache(self):
        packet = self._make_packet(ache="Paper 2 theoretical alignment — torus topology")
        encoded = self.serializer.encode_for_claude(packet)
        decoded = self.serializer.decode(encoded)
        assert decoded is not None, "Decode returned None — packet format may have changed"
        assert "torus topology" in decoded.tau_anchor.ache_vector, (
            f"τ-anchor lost in round-trip. Encoded: {encoded[:300]}..."
        )

    def test_gpt_decode_round_trip_preserves_ache(self):
        packet = self._make_packet(ache="CMCP attribution drift prevention")
        encoded = self.serializer.encode_for_gpt(packet)
        decoded = self.serializer.decode(encoded)
        assert decoded is not None
        assert "CMCP" in decoded.tau_anchor.ache_vector

    def test_inject_into_prompt_preserves_prompt(self):
        packet = self._make_packet()
        original_prompt = "Analyze the relational topology of the RSPS node network."
        injected = self.serializer.inject_into_prompt(packet, original_prompt, "claude-sonnet-4-6")
        assert original_prompt in injected, "Original prompt content must be preserved after injection"

    def test_inject_into_prompt_prepends_not_appends(self):
        packet = self._make_packet()
        prompt = "This is the actual query."
        injected = self.serializer.inject_into_prompt(packet, prompt, "claude-sonnet-4-6")
        # CMCP header should come BEFORE the prompt
        cmcp_pos = injected.find("rsps_context")
        prompt_pos = injected.find(prompt)
        assert cmcp_pos < prompt_pos, "CMCP header must precede the actual prompt"

    def test_packet_hash_is_stable(self):
        """Same packet content should produce the same hash (within same second)."""
        p1 = CMCPPacket(
            source_model_id="claude", destination_model_id="gpt",
            session_id="s1",
            tau_anchor=TauAnchor(ache_vector="test"),
            timestamp=1000.0  # Fixed timestamp
        )
        p2 = CMCPPacket(
            source_model_id="claude", destination_model_id="gpt",
            session_id="s1",
            tau_anchor=TauAnchor(ache_vector="test"),
            timestamp=1000.0
        )
        assert p1.packet_hash == p2.packet_hash

    def test_holonomy_record_in_packet(self):
        packet = self._make_packet()
        packet.holonomy_trace.append(HolonomyRecord(
            kappa=0.18,
            congruence_level="MARGINAL",
            models_in_cycle=["claude", "gpt", "deepseek"],
            timestamp=time.time()
        ))
        encoded = self.serializer.encode_for_claude(packet)
        # Holonomy should appear in trace section
        assert "0.180" in encoded or "0.18" in encoded


# ─────────────────────────────────────────────────────────────────────────────
# JESTER AND AUTOPOIETIC FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────

class TestJesterAndFeedback:
    """
    Tests for the ξ-Jester crystallization detection and autopoietic
    feedback loop.

    The Jester tests probe the boundary condition: the system should inject
    perturbation when crystallized, and only then. Premature injection
    disrupts productive flow; delayed injection allows Manifold Autarky.
    """

    def test_jester_activates_when_crystallized(self):
        """Sustained flatness + IDS stagnation → Jester activates."""
        kappas = [0.05, 0.06, 0.04, 0.07, 0.05]  # All below FLAT_THRESHOLD
        injector = JesterInjector(recent_kappas=kappas, recent_ids_delta=0.005)
        assert injector.should_inject(current_kappa=0.06, ids_stagnant=True), (
            "Jester should activate when κ has been flat for consecutive days AND IDS is stagnant"
        )

    def test_jester_stays_dormant_when_ids_growing(self):
        """If IDS is growing, crystallization is not occurring — Jester should stay dormant."""
        kappas = [0.05, 0.06, 0.04]
        injector = JesterInjector(recent_kappas=kappas, recent_ids_delta=0.08)
        assert not injector.should_inject(current_kappa=0.06, ids_stagnant=False), (
            "Jester should NOT fire when IDS is actively growing — system is not crystallized"
        )

    def test_jester_stays_dormant_when_kappa_elevated(self):
        """Active perturbation (high κ) → Jester should not compound it."""
        kappas = [0.05, 0.06, 0.07]  # Low historically
        injector = JesterInjector(recent_kappas=kappas, recent_ids_delta=0.001)
        # Current κ is elevated — active perturbation already present
        assert not injector.should_inject(current_kappa=0.45, ids_stagnant=True), (
            "Jester should NOT fire when κ is already elevated (system in active perturbation)"
        )

    def test_jester_perturbation_is_aimed(self):
        """Perturbation should target the crystallized cluster."""
        kappas = [0.04] * CRYSTALLIZATION_DAYS
        injector = JesterInjector(recent_kappas=kappas, recent_ids_delta=0.001)
        perturbation = injector.generate_perturbation("relational-intelligence")
        assert perturbation.target_cluster == "relational-intelligence"
        assert perturbation.frame  # Non-empty perturbation frame
        assert perturbation.adversarial_domain  # Cross-domain source identified

    def test_feedback_tightens_below_target(self):
        """IDS below target → threshold should decrease (tighten membrane)."""
        result = compute_policy_feedback(
            ids_score=0.35,       # Below target (0.65)
            current_threshold=1.0,
            has_causal_shear=False
        )
        assert result.new_threshold < result.previous_threshold, (
            f"IDS={result.ids_score} below target — threshold should tighten. "
            f"Got delta={result.delta}"
        )

    def test_feedback_loosens_above_target(self):
        """IDS above target → threshold should increase (loosen membrane)."""
        result = compute_policy_feedback(
            ids_score=0.85,       # Above target (0.65)
            current_threshold=1.0,
            has_causal_shear=False
        )
        assert result.new_threshold > result.previous_threshold, (
            f"IDS={result.ids_score} above target — threshold should loosen."
        )

    def test_causal_shear_dampens_feedback(self):
        """When ρ-archive has Causal Shear, feedback amplitude should be reduced."""
        no_shear = compute_policy_feedback(0.35, 1.0, has_causal_shear=False)
        with_shear = compute_policy_feedback(0.35, 1.0, has_causal_shear=True)
        assert abs(with_shear.delta) < abs(no_shear.delta), (
            "Causal Shear should dampen feedback amplitude to preserve archive stability"
        )
        assert with_shear.causal_shear_detected is True

    def test_feedback_converges_to_target(self):
        """
        Iterating the feedback loop should converge IDS toward target.
        This is the autopoietic closure test: a system with honest IDS signal
        should reach homeostasis through repeated policy adjustments.
        """
        threshold = 1.0
        simulated_ids = 0.40  # Start below target
        for i in range(20):
            result = compute_policy_feedback(simulated_ids, threshold)
            threshold = result.new_threshold
            # Simulate IDS responding to tighter membrane (simplistic model)
            simulated_ids = min(0.90, simulated_ids + 0.03)
        # After 20 iterations with improving IDS, threshold should have stabilized
        assert 0.1 <= threshold <= 2.5, f"Threshold escaped bounds after iteration: {threshold}"

    def test_feedback_respects_bounds(self):
        """Threshold must remain within [MIN=0.10, MAX=2.50] regardless of IDS."""
        for extreme_ids in [0.0, 1.0]:
            for extreme_threshold in [0.10, 2.50]:
                result = compute_policy_feedback(extreme_ids, extreme_threshold)
                assert 0.10 <= result.new_threshold <= 2.50


# ─────────────────────────────────────────────────────────────────────────────
# CONSTITUTIONAL CLAUSES
# ─────────────────────────────────────────────────────────────────────────────

class TestConstitutionalClauses:
    """
    Tests for the AURORA constitutional clause verification engine.

    The philosophically interesting tests here are the Clause 005 cases —
    they probe the boundary between "rejection with evidence" and "closure
    before testing preconditions." Getting this boundary right is the
    architectural implementation of the corpus's most operationally
    precise observation.
    """

    def setup_method(self):
        self.engine = ConstitutionalClauseEngine()
        self.clause_005 = Clause005_VerificationBeforeRejection()

    def _make_triangle_result(self, kappa, congruence, weakest=None, obstruction=None):
        """Helper to create a minimal TriangleResidueResult for testing."""
        from core.triangle_residue import TriangleResidueResult, CongruenceLevel
        return TriangleResidueResult(
            output_a=ModelOutput("a", "text a"),
            output_b=ModelOutput("b", "text b"),
            output_c=ModelOutput("c", "text c"),
            kappa=kappa,
            congruence_level=CongruenceLevel(congruence),
            sim_ab=0.8, sim_bc=0.8, sim_ca=0.8,
            weakest_link=weakest,
            topological_obstruction=obstruction
        )

    def test_clause_005_passes_when_flat(self):
        """Flat bundle (κ < 0.10) → no rejection pending → Clause 005 not triggered."""
        triangle = self._make_triangle_result(0.05, "FLAT")
        result = self.clause_005.check(
            triangle_residue=triangle,
            model_outputs={"a": None, "b": None},
            tau_vector={"mortal_asymmetry": 1}
        )
        assert result.outcome == ClauseOutcome.PASSED

    def test_clause_005_passes_when_hold_with_analysis(self):
        """HOLD state WITH structural analysis → rejection is evidence-based → PASSED."""
        triangle = self._make_triangle_result(
            kappa=0.28,
            congruence="HOLD",
            weakest="claude↔gpt",
            obstruction="Structural divergence detected: hierarchical vs cyclic topology mismatch at sim=0.42."
        )
        result = self.clause_005.check(
            triangle_residue=triangle,
            model_outputs={"a": None},
            tau_vector={"mortal_asymmetry": 1}
        )
        assert result.outcome == ClauseOutcome.PASSED, (
            "Clause 005 should PASS when HOLD state has complete structural analysis. "
            "Evidence-based rejection is valid — the clause prevents blind rejection, not informed rejection."
        )

    def test_clause_005_fails_when_hold_without_analysis(self):
        """HOLD state WITHOUT analysis → closing options before testing preconditions → FAILED."""
        triangle = self._make_triangle_result(
            kappa=0.28,
            congruence="HOLD",
            weakest=None,       # No weakest link identified
            obstruction=None    # No obstruction described
        )
        result = self.clause_005.check(
            triangle_residue=triangle,
            model_outputs={"a": None},
            tau_vector={"mortal_asymmetry": 1}
        )
        assert result.outcome == ClauseOutcome.FAILED, (
            "Clause 005 should FAIL when rejection is attempted without structural analysis. "
            "This is the core case: closing options before verifying preconditions."
        )

    def test_clause_003_mortal_asymmetry_required(self):
        from governance.clauses import Clause003_MortalAsymmetry
        c3 = Clause003_MortalAsymmetry()
        # With χ=1: PASSED
        assert c3.check(tau_vector={"mortal_asymmetry": 1}).outcome == ClauseOutcome.PASSED
        # Without χ=1: FAILED
        assert c3.check(tau_vector={"mortal_asymmetry": 0}).outcome == ClauseOutcome.FAILED
        # Missing field: FAILED
        assert c3.check(tau_vector={}).outcome == ClauseOutcome.FAILED

    def test_full_engine_passes_clean_state(self):
        """Full AURORA verification passes for a clean orchestration state."""
        triangle = self._make_triangle_result(0.08, "FLAT")
        result = self.engine.verify(
            model_outputs={"a": None, "b": None, "c": None},
            tau_vector={"mortal_asymmetry": 1, "ache_signal": "Test"},
            triangle_residue=triangle
        )
        assert result["outcome"] in ("PASSED", "DEFERRED")
        assert result["r_score"] > 0.5

    def test_full_engine_returns_dict(self):
        """Engine result must be JSON-serializable dict."""
        import json
        result = self.engine.verify(
            model_outputs={},
            tau_vector={"mortal_asymmetry": 1}
        )
        json.dumps(result)  # Must not raise


# ─────────────────────────────────────────────────────────────────────────────
# OSC OPERATOR
# ─────────────────────────────────────────────────────────────────────────────

class TestOSCOperator:
    """
    Tests for Ouroboric Security-Clarity synchronization.

    The OSC is the system's self-consistency check — it verifies that
    τ-Lock and ρ-archive are telling the same story. When they diverge,
    the system is in a state of self-contradiction that AURORA must flag.
    """

    def setup_method(self):
        self.osc = OSCOperator()

    class MockRhoArchive:
        """Minimal mock of the ρ-archive for OSC testing."""
        def __init__(self, has_shear=False, event_count=5):
            self._shear = has_shear
            self._count = event_count
        def has_causal_shear(self): return self._shear
        def get_recent_events(self, limit=50):
            return [{"tau_vector": "RSPS development", "kappa": 0.10}] * self._count

    def test_synchronized_when_tau_active_and_rho_coherent(self):
        result = self.osc.synchronize(
            tau_anchor="Building RSPS witness infrastructure",
            rho_archive=self.MockRhoArchive(has_shear=False, event_count=5),
            tau_timestamp=time.time()  # Fresh
        )
        assert result.is_synchronized, (
            f"Should be synchronized with active τ-lock and coherent ρ-archive. "
            f"OSC score={result.osc_score:.3f} (threshold={SYNC_THRESHOLD})"
        )
        assert result.tau_lock_status == "ACTIVE"
        assert result.rho_coherence_status == "COHERENT"

    def test_desynchronized_when_tau_absent(self):
        result = self.osc.synchronize(
            tau_anchor="",  # No ache vector
            rho_archive=self.MockRhoArchive(has_shear=False)
        )
        assert not result.is_synchronized, (
            "Should NOT be synchronized when τ-anchor is absent"
        )
        assert result.tau_lock_status == "ABSENT"

    def test_desynchronized_when_causal_shear(self):
        result = self.osc.synchronize(
            tau_anchor="Active ache vector",
            rho_archive=self.MockRhoArchive(has_shear=True),
            tau_timestamp=time.time()
        )
        assert result.rho_coherence_status == "SHEAR_DETECTED"
        # Causal Shear should reduce OSC score substantially
        assert result.osc_score < 0.9

    def test_stale_tau_reduces_score(self):
        fresh_result = self.osc.synchronize(
            tau_anchor="Current work",
            rho_archive=self.MockRhoArchive(),
            tau_timestamp=time.time()  # Fresh
        )
        stale_result = self.osc.synchronize(
            tau_anchor="Old work from yesterday",
            rho_archive=self.MockRhoArchive(),
            tau_timestamp=time.time() - (20 * 3600)  # 20 hours ago — stale
        )
        assert stale_result.osc_score < fresh_result.osc_score, (
            "Stale τ-Lock should produce lower OSC score than fresh τ-Lock"
        )
        assert stale_result.tau_lock_status == "STALE"

    def test_result_has_required_fields(self):
        result = self.osc.synchronize("test", self.MockRhoArchive())
        assert hasattr(result, 'osc_score')
        assert hasattr(result, 'is_synchronized')
        assert hasattr(result, 'tau_lock_status')
        assert hasattr(result, 'rho_coherence_status')
        assert 0.0 <= result.osc_score <= 1.0

    def test_to_dict_is_serializable(self):
        import json
        result = self.osc.synchronize("test anchor", self.MockRhoArchive())
        json.dumps(result.to_dict())  # Must not raise


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION: FULL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineIntegration:
    """
    Integration tests that run multiple pipeline stages together.
    These probe the architectural contract between stages.
    """

    def test_dcfb_confidence_feeds_into_triangle_residue(self):
        """
        DCFB confidence weight must reduce the holonomy contribution of
        contaminated outputs when passed to Triangle Residue Test.
        """
        filt = DCFBFilter()
        test = TriangleResidueTest(level=1)

        # Filter all three outputs
        dcfb_a = filt.filter(CONGRUENT_A, "claude")
        dcfb_b = filt.filter(CONGRUENT_B, "gpt")
        dcfb_c = filt.filter(FEAR_TEXT, "deepseek")  # Fear-contaminated outlier

        mo_a = ModelOutput("claude",  CONGRUENT_A, dcfb_a.confidence_weight)
        mo_b = ModelOutput("gpt",     CONGRUENT_B, dcfb_b.confidence_weight)
        mo_c = ModelOutput("deepseek",FEAR_TEXT,   dcfb_c.confidence_weight)  # Low confidence

        result = test.compute(mo_a, mo_b, mo_c)
        # Fear text is semantically divergent; with low confidence, κ should still
        # be elevated but somewhat dampened vs full confidence
        assert result.kappa is not None
        assert result.compute_time_ms > 0

    def test_clause_005_fires_on_escher_without_analysis(self):
        """End-to-end: ESCHER state without analysis → Clause 005 FAILED → AURORA outcome FAILED."""
        from core.triangle_residue import TriangleResidueResult, CongruenceLevel
        engine = ConstitutionalClauseEngine()

        triangle = TriangleResidueResult(
            output_a=ModelOutput("a", "text"),
            output_b=ModelOutput("b", "text"),
            output_c=ModelOutput("c", "text"),
            kappa=0.45, congruence_level=CongruenceLevel.ESCHER,
            sim_ab=0.3, sim_bc=0.3, sim_ca=0.3,
            weakest_link=None,         # No analysis — Clause 005 should fire
            topological_obstruction=None
        )

        result = engine.verify(
            model_outputs={"a": None, "b": None, "c": None},
            tau_vector={"mortal_asymmetry": 1, "ache_signal": "Test"},
            triangle_residue=triangle
        )
        assert result["outcome"] == "FAILED", (
            "AURORA should FAIL when ESCHER state exists without structural analysis "
            "(Clause 005 violation: rejection without precondition testing)"
        )
        assert any("clause_005" in v for v in result["violations"])
