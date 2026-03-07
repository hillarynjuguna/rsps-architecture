"""
RSPS Orchestration — FastAPI Application
==========================================

The orchestration API is the Python-layer bridge between:
  - The Android cognitive infrastructure (Witness + Observatory)
  - The multi-model AI network (via OpenRouter)
  - The governance layer (AURORA, constitutional clauses, OSC)
  - The n8n workflow automation layer

It exposes three primary endpoint groups:

  /orchestrate  — Multi-model routing with full RSPS pipeline
                  (DCFB filtering + Triangle Residue Test + AURORA)

  /cmcp         — Cross-Manifold Context Protocol operations
                  (encode, decode, inject into prompts)

  /membrane     — Policy feedback and IDS context relay
                  (IDS score ingestion, threshold computation)

Architecture Philosophy
-----------------------
This API is intentionally stateless at the HTTP layer — state lives in:
  - The Android ρ-archive (device-local SQLite)
  - The RhoArchive Python object (in-memory, session-scoped)
  - The CMCP packets (context-carrying across requests)

This matches the local-first sovereignty principle: the server never
*owns* the user's cognitive state. It processes and routes it, then
the result returns to the device.

The tension between local-first and API-dependent orchestration is
a live architectural constraint — see Architecture Spec §7.3.
The current resolution: orchestration metadata flows through the API,
but raw behavioral signal (pause events, notification data) never leaves
the device. The CMCP packet carries a ρ-archive *digest*, not the archive.

Starting the server:
  uvicorn api.main:app --reload --port 8000

Environment:
  OPENROUTER_API_KEY=sk-or-...
  DEFAULT_MODELS=claude-sonnet-4-6,gpt-4o,deepseek-chat
  TRIANGLE_RESIDUE_LEVEL=1  (1=proxy, 2=geometric)
  LOG_LEVEL=INFO
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.triangle_residue import TriangleResidueTest, ModelOutput, TriangleResidueResult
from core.dcfb_filter import DCFBFilter, DCFBResult
from core.cmcp import CMCPPacket, CMCPSerializer, CMCPPacketFactory, TauAnchor, HolonomyRecord
from core.jester_and_feedback import (
    JesterInjector, compute_policy_feedback,
    PolicyFeedbackResult, JesterPerturbation
)
from governance.clauses import ConstitutionalClauseEngine
from governance.osc_operator import OSCOperator

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("rsps.api")


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION LIFECYCLE
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy resources on startup."""
    logger.info("RSPS Orchestration API starting — initializing pipeline components")
    
    # Pre-load embedding model (avoids cold start on first request)
    app.state.triangle_test = TriangleResidueTest(
        level=int(os.getenv("TRIANGLE_RESIDUE_LEVEL", "1"))
    )
    app.state.dcfb_filter = DCFBFilter()
    app.state.cmcp_serializer = CMCPSerializer()
    app.state.clause_engine = ConstitutionalClauseEngine()
    app.state.osc_operator = OSCOperator()
    
    # RhoArchive in-memory (Phase 1: in-process state)
    # Phase 3: replace with SQLAlchemy-backed persistent archive
    app.state.rho_archive = InMemoryRhoArchive()
    
    logger.info("All pipeline components initialized — API ready")
    yield
    
    logger.info("RSPS Orchestration API shutting down")


app = FastAPI(
    title="RSPS-RRI Orchestration API",
    description="""
    Multi-model cognitive orchestration layer for the Recursive Sovereign Project Space.
    Implements: DCFB filtering, Triangle Residue Test (κ^Berry), CMCP encoding/decoding,
    Constitutional clause governance, OSC operator, Autopoietic policy feedback.
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 3: restrict to specific origins
    allow_methods=["*"],
    allow_headers=["*"]
)


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class TauVectorInput(BaseModel):
    ache_signal: str = Field(..., description="τ-node's explicit current intent statement")
    mortal_asymmetry: int = Field(default=1, description="Always 1 — consequence anchor invariant")
    routing_destiny: Optional[str] = Field(None, description="Explicit routing constraint hint")
    ids_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Current device IDS score")
    primary_cluster: Optional[str] = Field(None, description="Current primary cognitive cluster")

class OrchestrationRequest(BaseModel):
    """
    Full multi-model orchestration request.
    
    The tau_vector is required — orchestration without τ-anchor is Manifold
    Autarky waiting to happen. The models list defaults to the configured
    three-model triangle. dcfb_enabled defaults to True.
    """
    tau_vector: TauVectorInput
    prompt: str = Field(..., description="The content to route through the model triangle")
    models: list[str] = Field(
        default_factory=lambda: os.getenv(
            "DEFAULT_MODELS", "claude-sonnet-4-6,gpt-4o,deepseek-chat"
        ).split(","),
        description="Model identifiers for the Triangle Residue cycle (exactly 3 recommended)"
    )
    session_id: Optional[str] = Field(None, description="Session ID; generated if not provided")
    dcfb_enabled: bool = Field(default=True)
    triangle_residue_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    inject_cmcp: bool = Field(default=True, description="Prepend CMCP header to model prompts")
    cmcp_prior_packet: Optional[dict] = Field(None, description="Prior CMCP packet to extend")

class ModelOutputSchema(BaseModel):
    model_id: str
    content: str
    dcfb_confidence: float
    dcfb_flags: list[str]

class TriangleResidueSchema(BaseModel):
    kappa: float
    congruence_level: str
    is_congruent: bool
    weakest_link: Optional[str]
    obstruction: Optional[str]
    computation_ms: float

class AURORAResultSchema(BaseModel):
    r_score: float
    clauses_checked: list[str]
    violations: list[str]
    outcome: str   # PASSED / FAILED / DEFERRED

class OrchestrationResponse(BaseModel):
    session_id: str
    outputs: dict[str, ModelOutputSchema]
    triangle_residue: TriangleResidueSchema
    aurora_result: AURORAResultSchema
    recommended_synthesis: Optional[str]   # Best output or synthesis suggestion
    rho_archive_delta: dict                 # What was logged to ρ-archive
    cmcp_packet_for_next: Optional[dict]   # CMCP packet for next model call
    total_ms: float

class PolicyFeedbackRequest(BaseModel):
    ids_score: float = Field(..., ge=0.0, le=1.0)
    current_threshold: float = Field(..., ge=0.1, le=2.5)
    has_causal_shear: bool = Field(default=False)

class JesterRequest(BaseModel):
    primary_cluster: str
    recent_kappas: list[float]
    ids_delta_3day: float
    avoid_recent_frames: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATION ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(request: OrchestrationRequest, background_tasks: BackgroundTasks):
    """
    Full RSPS multi-model orchestration pipeline.
    
    Pipeline steps:
      1. Validate τ-vector (Mortal Asymmetry check)
      2. Build CMCP packet from τ + ρ-archive
      3. Route to N models in parallel via OpenRouter
      4. Apply DCFB filter to each output
      5. Run Triangle Residue Test (κ^Berry computation)
      6. AURORA constitutional clause verification
      7. OSC Operator synchronization
      8. Log everything to ρ-archive
      9. Return results + CMCP packet for next call
    
    If Triangle Residue κ > threshold, the response is flagged but still
    returned — the system never silently suppresses. The τ-node decides.
    """
    start = time.perf_counter()
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"Orchestration request | session={session_id} | models={request.models}")

    # ─── Step 1: τ-vector validation ────────────────────────────────────
    if not request.tau_vector.ache_signal:
        raise HTTPException(
            status_code=422,
            detail="τ-anchor required: ache_signal cannot be empty. "
                   "Orchestration without τ-anchor risks Manifold Autarky."
        )

    # ─── Step 2: Build CMCP packet ────────────────────────────────────────
    cmcp_factory = CMCPPacketFactory(
        rho_archive=app.state.rho_archive,
        tau_state={
            "ache_vector": request.tau_vector.ache_signal,
            "current_ids_score": request.tau_vector.ids_score,
            "primary_cluster": request.tau_vector.primary_cluster
        }
    )

    models = request.models[:3] if len(request.models) >= 3 else request.models
    primary_model = models[0] if models else "claude-sonnet-4-6"

    # Build one CMCP packet per destination model
    cmcp_packets = {}
    if request.inject_cmcp:
        for dest_model in models:
            cmcp_packets[dest_model] = cmcp_factory.build(
                source_model_id="rsps-orchestrator",
                destination_model_id=dest_model,
                session_id=session_id,
                override_ache_vector=request.tau_vector.ache_signal
            )

    # ─── Step 3: Parallel model calls ─────────────────────────────────────
    serializer = app.state.cmcp_serializer

    async def call_model(model_id: str) -> tuple[str, str]:
        """Call a single model via OpenRouter, returning (model_id, response_text)."""
        prompt = request.prompt
        if request.inject_cmcp and model_id in cmcp_packets:
            prompt = serializer.inject_into_prompt(
                cmcp_packets[model_id], prompt, model_id
            )

        try:
            response_text = await _call_openrouter(model_id, prompt)
            return model_id, response_text
        except Exception as e:
            logger.error(f"Model call failed [{model_id}]: {e}")
            return model_id, f"[ERROR: {model_id} call failed — {str(e)}]"

    # Run all model calls concurrently
    model_results = dict(await asyncio.gather(*[call_model(m) for m in models]))

    # ─── Step 4: DCFB filtering ───────────────────────────────────────────
    dcfb_filter = app.state.dcfb_filter
    dcfb_results: dict[str, DCFBResult] = {}
    model_outputs: dict[str, ModelOutput] = {}

    for model_id, content in model_results.items():
        dcfb_result = dcfb_filter.filter(content, model_id)
        dcfb_results[model_id] = dcfb_result
        model_outputs[model_id] = ModelOutput(
            model_id=model_id,
            content=content,
            dcfb_confidence=dcfb_result.confidence_weight
        )

    # ─── Step 5: Triangle Residue Test ────────────────────────────────────
    triangle_result: Optional[TriangleResidueResult] = None
    if len(model_outputs) >= 3:
        outputs = list(model_outputs.values())
        triangle_result = app.state.triangle_test.compute(
            outputs[0], outputs[1], outputs[2]
        )
        logger.info(
            f"Triangle Residue: κ={triangle_result.kappa:.3f} "
            f"| {triangle_result.congruence_level.value}"
        )

    # ─── Step 6: AURORA verification ─────────────────────────────────────
    aurora_result = app.state.clause_engine.verify(
        model_outputs=model_outputs,
        tau_vector=request.tau_vector.dict(),
        triangle_residue=triangle_result
    )

    # ─── Step 7: OSC Operator ─────────────────────────────────────────────
    osc_result = app.state.osc_operator.synchronize(
        tau_anchor=request.tau_vector.ache_signal,
        rho_archive=app.state.rho_archive,
        aurora_result=aurora_result
    )

    # ─── Step 8: Log to ρ-archive (background) ───────────────────────────
    rho_delta = {
        "session_id": session_id,
        "timestamp": time.time(),
        "kappa": triangle_result.kappa if triangle_result else None,
        "congruence_level": triangle_result.congruence_level.value if triangle_result else None,
        "aurora_outcome": aurora_result.get("outcome"),
        "dcfb_flags": {m: r.active_flags for m, r in dcfb_results.items()},
        "tau_vector": request.tau_vector.ache_signal
    }
    background_tasks.add_task(
        app.state.rho_archive.log_orchestration_event, rho_delta
    )

    # ─── Step 9: Build response ───────────────────────────────────────────
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Recommend synthesis from the highest-confidence, lowest-fear output
    recommended = _select_synthesis_candidate(model_outputs, dcfb_results, triangle_result)

    # Build CMCP packet for the next call
    next_cmcp = None
    if triangle_result:
        holonomy_record = HolonomyRecord(
            kappa=triangle_result.kappa,
            congruence_level=triangle_result.congruence_level.value,
            models_in_cycle=[o.model_id for o in [
                triangle_result.output_a, triangle_result.output_b, triangle_result.output_c
            ]],
            timestamp=time.time()
        )
        next_packet = cmcp_factory.build(
            source_model_id="rsps-orchestrator",
            destination_model_id="next_model",
            session_id=session_id
        )
        next_packet.holonomy_trace.append(holonomy_record)
        next_cmcp = {
            "session_id": next_packet.session_id,
            "kappa": holonomy_record.kappa,
            "congruence_level": holonomy_record.congruence_level,
            "tau_anchor": next_packet.tau_anchor.ache_vector
        }

    return OrchestrationResponse(
        session_id=session_id,
        outputs={
            m: ModelOutputSchema(
                model_id=m,
                content=model_outputs[m].content,
                dcfb_confidence=dcfb_results[m].confidence_weight,
                dcfb_flags=dcfb_results[m].active_flags
            )
            for m in model_outputs
        },
        triangle_residue=TriangleResidueSchema(
            kappa=triangle_result.kappa if triangle_result else 0.0,
            congruence_level=triangle_result.congruence_level.value if triangle_result else "N/A",
            is_congruent=triangle_result.is_congruent if triangle_result else True,
            weakest_link=triangle_result.weakest_link if triangle_result else None,
            obstruction=triangle_result.topological_obstruction if triangle_result else None,
            computation_ms=triangle_result.compute_time_ms if triangle_result else 0.0
        ),
        aurora_result=AURORAResultSchema(
            r_score=aurora_result.get("r_score", 1.0),
            clauses_checked=aurora_result.get("clauses_checked", ["clause_005"]),
            violations=aurora_result.get("violations", []),
            outcome=aurora_result.get("outcome", "PASSED")
        ),
        recommended_synthesis=recommended,
        rho_archive_delta=rho_delta,
        cmcp_packet_for_next=next_cmcp,
        total_ms=elapsed_ms
    )


# ─────────────────────────────────────────────────────────────────────────────
# SUPPORTING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/membrane/feedback")
async def policy_feedback_endpoint(request: PolicyFeedbackRequest) -> PolicyFeedbackResult:
    """
    Compute autopoietic policy feedback for the Observatory gating threshold.
    Called by the Android layer after each nightly IDS computation.
    """
    result = compute_policy_feedback(
        ids_score=request.ids_score,
        current_threshold=request.current_threshold,
        has_causal_shear=request.has_causal_shear
    )
    return result


@app.post("/jester/evaluate")
async def jester_evaluation(request: JesterRequest):
    """
    Check if Jester injection conditions are met and return perturbation if so.
    """
    injector = JesterInjector(
        recent_kappas=request.recent_kappas,
        recent_ids_delta=request.ids_delta_3day
    )
    current_kappa = request.recent_kappas[-1] if request.recent_kappas else 0.0
    ids_stagnant = abs(request.ids_delta_3day) < 0.03

    if injector.should_inject(current_kappa, ids_stagnant):
        perturbation = injector.generate_perturbation(
            primary_cluster=request.primary_cluster,
            avoid_recent=request.avoid_recent_frames
        )
        return {"inject": True, "perturbation": perturbation}
    return {"inject": False, "perturbation": None}


@app.post("/cmcp/encode")
async def cmcp_encode(tau_anchor: str, session_id: str, source_model: str, dest_model: str):
    """Encode a CMCP packet from provided τ-anchor and session context."""
    factory = CMCPPacketFactory(
        rho_archive=app.state.rho_archive,
        tau_state={"ache_vector": tau_anchor}
    )
    packet = factory.build(source_model, dest_model, session_id, tau_anchor)
    serializer = app.state.cmcp_serializer
    return {
        "claude_encoding": serializer.encode_for_claude(packet),
        "gpt_encoding": serializer.encode_for_gpt(packet),
        "packet_hash": packet.packet_hash
    }


@app.get("/health")
async def health():
    return {
        "status": "online",
        "components": {
            "triangle_residue": "ready",
            "dcfb_filter": "ready",
            "cmcp_serializer": "ready",
            "clause_engine": "ready",
            "osc_operator": "ready"
        }
    }


@app.get("/rho/archive")
async def get_rho_archive():
    """Retrieve recent ρ-archive events."""
    return app.state.rho_archive.get_recent_events(limit=50)


# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _call_openrouter(model_id: str, prompt: str) -> str:
    """Call OpenRouter API (OpenAI-compatible endpoint)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Return mock response if no API key configured
        return f"[MOCK RESPONSE from {model_id}]: This is a placeholder response. Set OPENROUTER_API_KEY in .env to enable real model calls."

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://rsps-rri.local",
                "X-Title": "RSPS-RRI Orchestration"
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _select_synthesis_candidate(
    outputs: dict[str, ModelOutput],
    dcfb: dict[str, DCFBResult],
    triangle: Optional[TriangleResidueResult]
) -> Optional[str]:
    """Select the output most suitable as synthesis candidate."""
    if not outputs:
        return None

    # Score each output: higher confidence + lower DCFB = better candidate
    scores = {
        model_id: dcfb[model_id].confidence_weight if model_id in dcfb else 1.0
        for model_id in outputs
    }

    best_model = max(scores, key=scores.get)
    return f"[{best_model}]: {outputs[best_model].content}"


# ─────────────────────────────────────────────────────────────────────────────
# IN-MEMORY ρ-ARCHIVE (Phase 1 — replace with SQLAlchemy in Phase 3)
# ─────────────────────────────────────────────────────────────────────────────

class InMemoryRhoArchive:
    """Phase 1 in-memory ρ-archive. Thread-safe, append-only."""

    def __init__(self):
        self._events: list[dict] = []
        self._phase_transitions: list[dict] = []

    def log_orchestration_event(self, event: dict):
        self._events.append(event)
        if len(self._events) > 10000:
            self._events = self._events[-5000:]  # Rolling window

    def log_phase_transition(self, event: str, description: str):
        self._phase_transitions.append({
            "event": event,
            "description": description,
            "timestamp": time.time()
        })

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        return self._events[-limit:]

    def get_phase_transitions(self) -> list[dict]:
        return self._phase_transitions

    def generate_summary(self) -> str:
        recent = self._events[-10:]
        transitions = [t["event"] for t in self._phase_transitions[-5:]]
        kappas = [e.get("kappa") for e in recent if e.get("kappa") is not None]
        avg_kappa = sum(kappas) / len(kappas) if kappas else None
        return (
            f"events={len(self._events)} | "
            f"transitions=[{', '.join(transitions)}] | "
            f"avg_kappa={avg_kappa:.3f}" if avg_kappa else f"events={len(self._events)}"
        )

    def has_causal_shear(self) -> bool:
        recent_kappas = [
            e.get("kappa") for e in self._events[-5:]
            if e.get("kappa") is not None
        ]
        if len(recent_kappas) < 3:
            return False
        for i in range(1, len(recent_kappas)):
            if abs(recent_kappas[i] - recent_kappas[i-1]) > 0.5:
                return True
        return False
