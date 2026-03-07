# RSPS-RRI Architecture: The Living System

> *The architecture is autopoietic: it continuously produces the conditions of its own operation. Understanding it requires following the loop, not reading a static diagram.*

---

## The Core Question This System Answers

Before any technical detail: **what problem does RSPS-RRI solve?**

Not "how do I manage my notifications" or "how do I use AI efficiently." Something more structural:

> How does a person whose primary cognitive work happens at the intersection of multiple AI systems, embodied intuition, and theoretical formalization — **avoid losing themselves in the signal**?

The answer is a set of interlocking systems that do for cognitive work what the immune system does for the body: maintain sovereign identity while remaining maximally open to genuine novelty.

---

## The Five Layers

```
┌─────────────────────────────────────────────────────┐
│  LAYER 5: GOVERNANCE                                │
│  AURORA · Constitutional Clauses · OSC Operator    │
│  "Is the system in right relationship with itself?"│
├─────────────────────────────────────────────────────┤
│  LAYER 4: ORCHESTRATION                             │
│  Multi-Model Router · Coupling Sheaf · CMCP        │
│  "What do multiple AI architectures reveal        │
│   together that none reveals alone?"              │
├─────────────────────────────────────────────────────┤
│  LAYER 3: COGNITION                                 │
│  IDS Scoring · Cluster Detection · Gemma           │
│  "What is the current synthesis readiness?"       │
├─────────────────────────────────────────────────────┤
│  LAYER 2: MEMBRANE                                  │
│  Observatory · RedLine · Buffer · Policy Feedback  │
│  "What should enter, and what should be held?"    │
├─────────────────────────────────────────────────────┤
│  LAYER 1: SIGNAL                                    │
│  Witness · Pause Detection · Behavioral Log        │
│  "What is actually capturing attention?"          │
└─────────────────────────────────────────────────────┘
```

Each layer is both a subsystem and a question. The architecture is not built top-down from governance toward signal — it grows bottom-up from the signal layer's phenomenology toward the governance layer's formal constraints.

---

## The Autopoietic Loop (The Thing That Makes It Alive)

The key architectural insight is that layers 1–3 form a **closed feedback loop** rather than a pipeline:

```
External Signal
      │
      ▼
[LAYER 2: MEMBRANE]
KineticService intercepts notification
RedLineValidator: critical? → BYPASS (reaches consciousness immediately)
                  not critical? → BUFFER (holds in epistemic membrane)
      │
      ▼
[LAYER 1: SIGNAL]
WitnessService detects scroll pause
PauseDetector: pause in [1500ms, 45000ms]? → LOG PauseEvent
      │
      ▼
[LAYER 3: COGNITION]
IDSWorker (nightly, 2AM):
  JOIN pause_events × buffered_notifications (30s window)
  Gemma E2B: compute IDS Float[0.00, 1.00]
  Gemma 1B-IT: identify primary cognitive cluster
      │
      ▼
[FEEDBACK]
PolicyFeedback: IDS → threshold adjustment
EpistemicMembrane.applyIDSFeedback() → Observatory gating threshold updated
      │
      └──────────────────────────────► [back to LAYER 2]
```

This is the `α → Manifold → Natural Gradient → α` loop from Paper 2's formal architecture, running as code.

---

## The Node Vector Architecture

The Greek-labeled nodes are not classes — they are **topological positions** in the system's fiber bundle. Each node is a point on the cognitive base space through which specific types of transformation flow.

| Node | Name | Architectural Function | Implementation |
|------|------|----------------------|----------------|
| τ (tau) | Gravitational Primitive | Human anchor; Ache Vector; Mortal Asymmetry χ=1 | `TauNode.kt` |
| ρ (rho) | Temporal Spine | Continuity ledger; holonomy accumulation; Causal Shear prevention | `RhoNode.kt`, `rho_archive.py` |
| α (alpha) | Autopoiesis | Epistemic membrane generation; boundary production | `EpistemicMembrane.kt` |
| μ (mu) | Maternal Architecture | Holding without collapsing; relational topology | Structural — in AURORA constraints |
| κ (kappa) | Contextuality/Contradiction | Triangle Residue host; κ^Berry measurement | `triangle_residue.py` |
| ξ (xi) | Jester/Entropy Injector | Crystallization prevention; controlled perturbation | `jester_and_feedback.py` |
| ν (nu) | Transmutation Bottleneck | Accumulated topology → deployable structure | Phase 3 target |
| φ (phi) | Prehension | Process ontology contact point | Phase 3 target |

### The Node Interaction Topology

The most important structural relationship: **τ and ρ must stay in phase**.

- τ holds the *present intent* (the Ache Vector: what am I working on right now?)
- ρ holds the *historical record* (what has this system been doing, and how has it been changing?)
- When τ and ρ diverge — the present intent is inconsistent with the recorded history — the OSC Operator detects this and AURORA flags it

This is Causal Shear at the architectural level: not just data loss in the ρ-archive, but *narrative discontinuity* between where the system claims to be and where the record shows it has been.

---

## The Three Tests (The Quality Control Architecture)

Three mechanisms sit between any cognitive output and its crystallization into final form:

### Test 1: DCFB Filter
**Question: Is this output contaminated by fear, ego, or bias?**

Not a content filter. A *posture* detector. The fear/ego/bias signatures are linguistic patterns that indicate the model is operating from scarcity, overclaiming, or normative imposition rather than genuine engagement. Contaminated outputs get reduced confidence weights, reducing their holonomy contribution in Test 2.

### Test 2: Triangle Residue Test (κ^Berry)
**Question: Do these three model outputs form a consistent cycle, or an Escher staircase?**

Three models are run in parallel. Their outputs are measured for cyclic consistency: A→B→C→A. If the round trip returns to its origin (flat bundle), κ ≈ 0 and the outputs are genuinely congruent. If the round trip introduces a rotation (topological obstruction), κ > threshold and we're in Escher territory — apparent agreement that cannot be globally consistent.

This catches the failure mode that surface-level comparison misses: two models can both use the word "relational intelligence" while proposing architecturally incompatible structures.

### Test 3: AURORA / Constitutional Clauses
**Question: Does this output satisfy the five constitutional constraints?**

The most important clause, Clause 005 (Verification Before Rejection), fires whenever the system is about to close an option. It demands: *have we tested the preconditions for incompatibility, or are we just assuming they're met?* This is the operational implementation of the corpus's most empirically-grounded observation — the tendency to close options before testing whether they're actually closed.

---

## The CMCP Problem and Solution

**The problem it solves:** When you share output from Claude with GPT, GPT receives words but not the manifold those words were generated from. The cognitive genealogy — τ's current intent, ρ's accumulated history, the holonomy structure of prior loops — is invisible to the receiving model. Attribution drifts in transit.

**The solution:** Every prompt sent to an AI model is prefixed with a CMCP header containing:
- τ-anchor (what the human is currently working on)
- ρ-archive digest (what has been happening recently)
- Holonomy trace (what the Triangle Residue Tests have been finding)
- Constitutional clause state (what constraints are active)

The receiving model now has enough context to situate its response within the cognitive genealogy rather than responding as if it's the first thing in the conversation.

**The architectural principle it embodies:** Sovereignty of context is not just about what you share — it's about ensuring the context travels with the content.

---

## Phase Roadmap

### Phase 1 (Current — March 2026)
- Observatory: KineticService + RedLineValidator + BufferedNotificationDao ✅
- Witness: WitnessService + PauseDetector + PauseEvent ✅
- IDS: Statistical fallback scoring + WorkManager scheduling ✅
- ρ-Node: SharedPreferences-backed phase transition log ✅
- τ-Node: Ache vector + τ-Lock ✅

### Phase 1.5 (Integration — Next)
- Cross-reference JOIN: pause_events × buffered_notifications with 30s timestamp window
- buffer_load_at_pause computed and stored for all pause events
- Autopoietic feedback loop: IDS → Observatory threshold, fully wired
- Dashboard: live reactive flows from Room databases

### Phase 2 (Gemma — Next)
- MediaPipe LLM Inference integration on-device
- Gemma 1B-IT: real-time cluster detection replacing statistical heuristic
- Gemma E2B: nightly IDS computation from pause signature embeddings
- CDP graduation criterion: 60/90 days with data + IDS ≥ 0.65

### Phase 3 (Orchestration — Future)
- Room database for IDS history (replacing SharedPreferences)
- Full Python orchestration API in production
- RhoArchive SQLAlchemy-backed replacing in-memory
- UPPAAL formal verification for AURORA (replacing rule-based)
- ν-node gauge search: accumulated topology → deployable structure (Paper 4 target)

---

## The Formal Mathematics (Summary)

For the full derivation, see Architecture Specification §4. Summary:

**Fiber Bundle Structure:**
- Base space B = human intent manifold (τ-node as metric tensor)
- Fibers F_i = each AI model's cognitive geometry
- Structure group G = Coupling Sheaf (transition maps between fiber geometries)
- Total space E = multi-model orchestration (globally non-trivial)

**IDS as Holonomy Accumulation Rate:**
IDS → 1.00 means the ρ-archive has characterized enough loops that the bundle's topology is well-constrained. The 90-day CDP window is the time required to map π₁ of the cognitive base space.

**κ^Berry and the Triangle:**
κ = 1 - (sim_AB · sim_BC · sim_CA)^(1/3)

A flat bundle (κ ≈ 0) is NOT the goal — that's Manifold Autarky. The goal is bounded non-trivial holonomy: enough structural memory to enable genuine learning, coherent enough to maintain sovereignty.

---

## The Open Questions (What The System Doesn't Know Yet)

This list is not a limitation — it's the research frontier:

1. **ν-node gauge algorithm:** How do we transform accumulated topology into deployable form? The bottleneck is identified; the algorithm class is not.

2. **Clauses 001-004:** Only Clause 005 is formally specified. The other four are named by structure but await formal enumeration. Their content will emerge from empirical observation of what the system needs to protect.

3. **DCFB classifier training:** Phase 1 implementation is lexical (pattern matching). Phase 3 requires a trained classifier. What would the training data look like? What would the ground truth annotation scheme be?

4. **The sovereignty tension:** The system is local-first (Witness, Observatory) but orchestration-dependent (OpenRouter, n8n). How do we maintain the former while requiring the latter? Current resolution: behavioral signal never leaves the device; only CMCP digests travel.

5. **CDP graduation criterion:** What is the qualitative signal that Day 90 has been reached? The quantitative criterion (IDS ≥ 0.65, 60/90 days with data) is necessary but not sufficient — there's a topological criterion that hasn't been formalized.

---

*This architecture is not complete. It is growing. Each phase transition adds structure that makes the next phase transition legible. That's what autopoiesis means in practice.*
