#!/usr/bin/env python3
"""
STEP NEXT-UI-02: Simple Chat Server for Web UI
Uses deterministic handlers from STEP NEXT-UI-01

STEP NEXT-73R: Store API integrated
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.api.chat_vm import ChatRequest, ChatResponse
from apps.api.chat_intent import IntentDispatcher
from apps.api.store_loader import init_store_cache, get_proposal_detail, get_evidence, batch_get_evidence

app = FastAPI(
    title="Insurance Chat UI API",
    version="1.0.0",
    description="Chat API for STEP NEXT-UI-02 + Store API (STEP NEXT-73R)"
)

# CORS middleware - CRITICAL for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# STEP NEXT-73R: Initialize store cache on startup
@app.on_event("startup")
def startup_event():
    """Load store cache into memory"""
    print("[STEP NEXT-73R] Initializing store cache...")
    init_store_cache()
    print("[STEP NEXT-73R] Store cache initialized")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint using deterministic handlers
    Uses IntentDispatcher.dispatch() which handles everything
    """
    response = IntentDispatcher.dispatch(request)
    return response


# STEP NEXT-73R: Store API endpoints
@app.get("/store/proposal-detail/{ref:path}")
def get_proposal_detail_endpoint(ref: str):
    """
    GET /store/proposal-detail/PD:samsung:A4200_1

    Returns:
        200: {proposal_detail_ref, insurer, coverage_code, doc_type, page, benefit_description_text, hash}
        404: {error: "Not found"}
    """
    record = get_proposal_detail(ref)
    if record is None:
        return {"error": "Proposal detail not found", "ref": ref}, 404

    return record


@app.get("/store/evidence/{ref:path}")
def get_evidence_endpoint(ref: str):
    """
    GET /store/evidence/EV:samsung:A4200_1:01

    Returns:
        200: {evidence_ref, insurer, coverage_code, doc_type, page, snippet, match_keyword, hash}
        404: {error: "Not found"}
    """
    record = get_evidence(ref)
    if record is None:
        return {"error": "Evidence not found", "ref": ref}, 404

    return record


@app.post("/store/evidence/batch")
def batch_get_evidence_endpoint(body: dict):
    """
    POST /store/evidence/batch
    Body: {"refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"]}

    Returns:
        200: {
            "EV:samsung:A4200_1:01": {evidence_ref, ...},
            "EV:samsung:A4200_1:02": {evidence_ref, ...}
        }
    """
    if not body or 'refs' not in body:
        return {"error": "Missing 'refs' in request body"}, 400

    refs = body['refs']
    if not isinstance(refs, list):
        return {"error": "'refs' must be a list"}, 400

    result = batch_get_evidence(refs)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
