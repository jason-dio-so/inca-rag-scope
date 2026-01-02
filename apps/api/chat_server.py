#!/usr/bin/env python3
"""
STEP NEXT-UI-02: Simple Chat Server for Web UI
Uses deterministic handlers from STEP NEXT-UI-01
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.api.chat_vm import ChatRequest, ChatResponse
from apps.api.chat_intent import IntentDispatcher

app = FastAPI(
    title="Insurance Chat UI API",
    version="1.0.0",
    description="Chat API for STEP NEXT-UI-02"
)

# CORS middleware - CRITICAL for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
