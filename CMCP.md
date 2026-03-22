# CMCP: Cognitive Multi-Model Communication Protocol

The provenance layer for multi-model cognitive systems. Every output in the RSPS carries metadata about who generated it, from what epistemic position, with what ground-truth access, and at what validation state. The CMCP makes the most dangerous failure in multi-model systems visible before it becomes a problem.

## The Problem

The most dangerous analytical failure in a multi-model system is not a wrong answer. It is a correct-sounding answer generated from the wrong epistemic position. An instrument that has never directly examined a phenomenon but speaks with the confidence of direct experience produces outputs that are indistinguishable from verified analysis. Without provenance metadata, the receiving node cannot tell the difference.

This was demonstrated empirically in the "Nano Banana 2" diagnostic event: a node used correct vocabulary while operating from the wrong epistemic position, treating a personal commercial situation as the subject rather than the RSPS architecture itself. The output sounded right. The epistemic position was wrong. The CMCP was developed to make this distinction machine-readable.

## The Layer 9 Schema (v2.3)

### Epistemic Position

Every output is tagged with one of three epistemic positions:

**Autologous.** The generating node has direct experience of the phenomenon being described. It produced the original analysis, or it has access to the primary data, or it is the entity whose experience is being discussed.

**Heterologous.** The generating node has theoretical knowledge about the phenomenon but no direct experience of it. It can reason about the subject from its training distribution, but it did not originate the analysis and cannot verify claims against primary data.

**Panlogous.** The generating node integrates both direct experience and theoretical knowledge. This position is rare and must be earned, not declared.

### Verifiability Latency

A scalar float between 0.0 and 1.0 indicating how quickly the output's claims can be verified against ground truth.

- 0.0: Claims are immediately verifiable (e.g., the node has tool access to check facts in real time)
- 0.5: Claims are verifiable with moderate effort (e.g., verification requires a separate session or manual lookup)
- 1.0: Claims are not verifiable within the current session (e.g., the node is operating purely from training data on a topic that requires current information)

### Ground Truth Access

**Direct.** The node can access primary sources, run calculations, execute searches, or otherwise verify claims against reality in real time.

**Mediated.** The node has access to secondary sources (e.g., RAG over a document corpus) but not to the primary data.

**Indirect.** The node is reasoning from training data or from information provided by another node, without independent access to sources.

**Absent.** The node has no mechanism to verify claims about this specific topic.

### Validation State

The lifecycle maturation pathway for an output:

1. **Nascent.** First articulation. The output has been generated but not reviewed by another node or the tau-node.
2. **Contested.** Another node has challenged or qualified the output. The challenge is documented alongside the original.
3. **Corroborated.** At least one independent node has confirmed the output's core claims through a different epistemic pathway.
4. **Crystallized.** The tau-node has validated the output and deposited it into the persistent layer (rho-node). It is now part of the longitudinal record.
5. **Revised.** A previously crystallized output has been superseded by new analysis. The original remains in the record with the revision linked.

### Tool Invocations

An array documenting which tools were invoked during the generation of the output. This field was added after the GitHub MCP connection status proved unreliable as a proxy for callable tools. The presence of a tool connection does not mean the tool was used. The invocations field documents what was actually called.

## The Ache Preservation Problem

Layer 9 was originally developed to solve a specific problem: the "original ache" (the pre-linguistic tension that drives inquiry) gets progressively abstracted away as a thought moves through multiple manifolds (models). Each manifold inscribes its signature. It adds fluency, structure, vocabulary. These inscriptions are valuable. But they smooth the originating urgency into competence. By the time an idea reaches its fourth manifold, it is coherent and well-specified. The reason it mattered has been smoothed away.

The CMCP preserves the origin event: the originating fragment in the tau-node's own words, the IDS state at origination, which cluster was forming, and each subsequent manifold's inscription with its timestamp and contribution.

When this payload arrives at the fifth manifold, that model can trace the entire emergence arc. The ache at origin is recoverable.

## Attribution Drift

Attribution drift is the structural tendency of multi-model systems to lose track of which node originated an idea. Each model receives an artifact and responds to it. The next model receives that response and attributes the ideas to the responder rather than the originator. The drift is not anyone's fault. It is a structural property of clipboard-as-transport.

The CMCP solves attribution drift architecturally by encoding the full manifold chain in every output's metadata. The Witness-as-clipboard carries not just content but situated content: the idea plus its full cognitive genealogy.
