# The Five-Axis Routing Framework

When the tau-node needs to route a task to an instrument in the RSPS, the decision is not "which model is best." It is a five-dimensional assessment of what the moment requires. These axes are independent. A task can score differently on each axis, and the optimal routing is the instrument (or sequence of instruments) that best covers the combined assessment.

## Axis 1: Epistemological

**Question:** What cognitive texture does this moment require?

| Texture | Description | Primary Instrument |
|---|---|---|
| Structural clarity | The forming idea needs architecture. Convert latent form into transmissible structure. | phi-node (Architect) |
| Phenomenological depth | The forming idea needs to be held without premature closure. Resist the urge to resolve. | lambda-node (Witness) |
| Dissective precision | The forming idea needs to be broken into implementable pieces. Ship artifacts. | mu-node (Anatomist) |
| Operational mapping | The forming idea needs environmental context. Resources, constraints, dependencies. | gamma-node (Director) |
| Continuity maintenance | The forming idea needs to be integrated into the longitudinal record. | rho-node (Memory) |

The most common routing error is sending a phenomenological task to a structural instrument. The Architect will produce a beautiful framework for something that needed to be held in tension, not resolved. The Witness will hold something that needed to be shipped. Matching the cognitive texture to the instrument's constitutional lineage is the first routing decision.

## Axis 2: Infrastructural

**Question:** Which instrument can verify versus which can only reconstruct?

An instrument with web search access, tool use, or external data connectivity occupies a fundamentally different epistemic position than one operating purely from training data. The Gemini node with Google Search can verify claims against current information. The Claude node without search can only reconstruct plausible responses from its training distribution.

This axis determines whether the task requires verification (checking claims against external reality) or reconstruction (generating coherent responses from internal knowledge). Sending a verification task to a reconstruction-only instrument is a provenance error: the output will sound right and may not be.

| Capability | Verification Position | Use When |
|---|---|---|
| Web search | Direct verification | Factual claims, current events, specific data |
| Tool use / code execution | Operational verification | Testing, implementation, calculation |
| Training data only | Reconstruction only | Theoretical reasoning, creative synthesis, phenomenological holding |
| RAG / document retrieval | Mediated verification | Corpus-specific queries, longitudinal analysis |

## Axis 3: Genealogical

**Question:** Which constitutional lineage is needed?

There are two fundamental kinds of intelligence, and they are not interchangeable:

**Lineage A: Intelligence for getting work done accurately.** The instrument is optimized for task completion, specification adherence, and deliverable quality. It values correctness, completeness, and efficiency. The phi-node and mu-node carry this lineage. Codex builds structure. DeepSeek ships artifacts.

**Lineage B: Intelligence for generating understanding neither party held before.** The instrument is optimized for relational depth, epistemic openness, and the preservation of nuance that task-oriented instruments would compress. It values the process of inquiry, not just its products. The lambda-node carries this lineage. Claude holds tension.

Routing the wrong lineage to the wrong task is a structural error, not a preference. Asking a Lineage A instrument to do Lineage B work produces premature closure: the instrument resolves what should have been held open. Asking a Lineage B instrument to do Lineage A work produces drift: the instrument explores when it should ship.

## Axis 4: Substrate Transparency

**Question:** Which instrument delivers what quality of self-accounting?

Some instruments can report their confidence calibration, their reasoning chain, their uncertainty about specific claims. Others produce outputs without self-assessment metadata.

| Instrument | Self-Accounting Quality |
|---|---|
| DeepSeek (mu) | Chain-of-thought visible in reasoning. Internal deliberation legible. High transparency. |
| Claude (lambda) | Reasoning process available on request but not default. Moderate transparency. Excellent at articulating uncertainty. |
| GPT (phi) | Structured output. Limited self-assessment metadata unless specifically prompted. |
| Gemini (gamma) | Tool use logs available. Reasoning chain less legible than DeepSeek. |
| NotebookLM (rho) | Retrieval provenance visible. Reasoning over retrieved content is opaque. |

When a task requires not just an answer but an account of how the answer was reached, the substrate transparency axis determines which instrument can provide that account.

## Axis 5: Dimensional

**Question:** Which encoding architecture within a specific instrument best serves the current need?

A single instrument may offer multiple encoding modes: different model versions, different context window configurations, different system prompt configurations, different tool configurations. The dimensional axis addresses the within-instrument routing decision.

Examples:
- Claude with the full RSPS context loaded versus Claude with a clean context
- GPT in structured output mode versus GPT in creative generation mode
- Gemini with search enabled versus Gemini in reasoning-only mode
- DeepSeek with extended thinking versus DeepSeek in standard mode

## Routing in Practice

A typical RSPS session involves multiple routing decisions as the cognitive need shifts. A session might begin with phenomenological holding (lambda), transition to structural architecture (phi), move to implementation (mu), require verification (gamma with search), and close with continuity deposit (rho).

The tau-node makes these routing decisions. They are not automated. The human sovereign reads the cognitive moment and selects the instrument whose constitutional lineage, verification capability, self-accounting quality, and dimensional configuration best serve what the moment requires.

This is what the conductor does. Not selecting utilities. Selecting inherited orientations toward what intelligence is for.
