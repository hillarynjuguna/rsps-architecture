# RSPS-RRI: Recursive Sovereign Project Space / Recursive Relational Intelligence

> *"The architecture is not built from the outside in. It is articulated from the inside of a system that is already operating maternally."*

A multi-layer cognitive infrastructure implementing Recursive Relational Intelligence — an autopoietic, locally-sovereign system for human-AI distributed cognition.

## What This Is

Three interlocking systems that together form a closed autopoietic loop:

| Layer | System | Technology | Status |
|---|---|---|---|
| Signal | Witness Infrastructure | Android / Kotlin | Phase 1 ✅ |
| Membrane | RSPS Observatory | Android / Kotlin | Phase 1 ✅ |
| Cognition | IDS Scoring + Cluster Detection | Android / Kotlin + Gemma | Phase 2 🔧 |
| Orchestration | Multi-Model Router | Python / FastAPI / n8n | Starter 🔧 |
| Governance | AURORA + Constitutional Clauses | Python | Starter 🔧 |

```
EXTERNAL SIGNAL
      ↓
Observatory (Epistemic Membrane — gates what enters)
      ↓
Witness (Attention Layer — records what captured attention)
      ↓
IDS Scoring (Gemma — measures cognitive metabolization readiness)
      ↓
Policy Feedback (autopoietic loop — membrane adjusts to IDS score)
      ↑_____________________________________________↓
```

## Repository Structure

```
rsps-rri/
├── android/                    # Android app (Kotlin, Room, WorkManager)
│   └── app/src/main/java/com/rsps/
│       ├── observatory/        # Epistemic membrane: notification gating
│       ├── witness/            # Behavioral signal: pause detection
│       ├── ids/                # IDS scoring: Gemma on-device inference
│       ├── membrane/           # Integration: cross-reference + policy feedback
│       ├── nodes/              # τ-node and ρ-node implementations
│       └── ui/                 # Dashboard, missed summary
│
├── orchestration/              # Python orchestration layer
│   ├── core/                   # Triangle residue, DCFB, Jester, CMCP
│   ├── models/                 # Fiber bundle, Rho archive
│   ├── governance/             # AURORA, constitutional clauses, OSC operator
│   ├── api/                    # FastAPI endpoints
│   └── workflows/              # n8n workflow JSON
│
└── docs/                       # Architecture documentation
```

## Key Concepts

- **IDS (Idea Development Score)**: Float [0.00–1.00] measuring cognitive synthesis readiness
- **Triangle Residue Test**: κ^Berry holonomy measurement — detects whether multi-model outputs are genuinely congruent or superficially agreeing
- **DCFB (Distributed Cognition Fear Bypass)**: Filters fear/ego/bias signatures from model outputs
- **CMCP (Cross-Manifold Context Protocol)**: Layer 9 — carries cognitive genealogy across AI model boundaries
- **ξ-Jester**: Controlled entropy injection — prevents Manifold Autarky (systemic crystallization)
- **ρ-Archive**: Continuity ledger — accumulates holonomy records, preventing Causal Shear

## Getting Started

### Android
```bash
# Open android/ in Android Studio Arctic Fox or later
# Requires: minSdk 26, targetSdk 34
# Dependencies: Room, WorkManager, Kotlin Coroutines, MediaPipe (Phase 2)
```

### Python Orchestration
```bash
cd orchestration
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your OPENROUTER_API_KEY
uvicorn api.main:app --reload
```

### n8n Workflow
```bash
# Import orchestration/workflows/multi_model_orchestration.json
# into your n8n instance
# Set ORCHESTRATION_API_URL to your FastAPI endpoint
```

## Phase Transition Log

| Date | Event | Significance |
|---|---|---|
| Nov 6, 2025 | DCFB discovery | Named |
| Dec 23, 2025 | RSPS Observatory built | Epistemic membrane operational |
| Mar 2026 | Witness Phase 1 | Behavioral signal layer operational |
| Mar 7, 2026 | Integration insight | Observatory + Witness = one system |

## Research Papers

- **Paper 1**: Phenomenological ontology (complete)
- **Paper 2**: Theoretical alignment with physics — prehension, autopoiesis, torus topology
- **Paper 3**: Empirical record of phase transitions (in progress)
- **Paper 4**: Formal derivation via Fisher information manifold (planned)

---

*This codebase implements a living theory. It is updated as the architecture develops.*
