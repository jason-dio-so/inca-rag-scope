"""
Mock API Server for Insurance Comparison
STEP NEXT-9: API Contract Implementation

IMMUTABLE RULES:
1. NO DB connections
2. NO retrieval/search
3. NO LLM calls
4. Fixture-based responses only
5. CORS enabled for localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path
import uuid

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Comparison Mock API",
    version="mock-0.1.0",
    description="Mock API for testing UI integration (fixture-based)"
)

# CORS middleware - allow localhost:8000 (web-prototype)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProductInfo(BaseModel):
    insurer: str
    product_name: str

class TargetCoverage(BaseModel):
    coverage_code: Optional[str] = None
    coverage_name_raw: Optional[str] = None

class RequestOptions(BaseModel):
    include_notes: bool = True
    include_evidence: bool = True
    premium_reference_only: bool = False

class DebugOptions(BaseModel):
    force_example: Optional[str] = None
    compiler_version: Optional[str] = "v1.0.0"

class CompareRequest(BaseModel):
    intent: str = Field(..., pattern="^(PRODUCT_SUMMARY|COVERAGE_CONDITION_DIFF|COVERAGE_AVAILABILITY|PREMIUM_REFERENCE)$")
    insurers: List[str] = Field(..., min_items=1)
    products: List[ProductInfo] = Field(..., min_items=1)
    target_coverages: List[TargetCoverage] = []
    options: Optional[RequestOptions] = RequestOptions()
    debug: Optional[DebugOptions] = DebugOptions()

# Fixture loader
FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_fixture(example_name: str) -> Dict[str, Any]:
    """Load fixture JSON file"""
    fixture_path = FIXTURES_DIR / f"{example_name}.json"
    if not fixture_path.exists():
        raise HTTPException(status_code=404, detail=f"Fixture not found: {example_name}")

    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

def route_intent_to_fixture(intent: str, force_example: Optional[str] = None) -> str:
    """
    Route intent to fixture file (deterministic)

    Rules:
    1. If force_example is set, use it (dev override)
    2. Otherwise route by intent:
       - PRODUCT_SUMMARY -> example3
       - COVERAGE_CONDITION_DIFF -> example2
       - COVERAGE_AVAILABILITY -> example4
       - PREMIUM_REFERENCE -> example1
    """
    if force_example:
        return force_example

    intent_to_fixture = {
        "PRODUCT_SUMMARY": "example3_product_summary",
        "COVERAGE_CONDITION_DIFF": "example2_coverage_compare",
        "COVERAGE_AVAILABILITY": "example4_ox",
        "PREMIUM_REFERENCE": "example1_premium"
    }

    return intent_to_fixture.get(intent, "example3_product_summary")

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "mock-0.1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/compare")
async def compare(request: CompareRequest):
    """
    Main comparison endpoint

    Mock behavior:
    1. Validate request schema (Pydantic)
    2. Route intent -> fixture
    3. Load fixture
    4. Return Response View Model

    NO DB, NO retrieval, NO LLM
    """
    try:
        # Route to fixture
        force_example = request.debug.force_example if request.debug else None
        fixture_name = route_intent_to_fixture(request.intent, force_example)

        # Load fixture
        response = load_fixture(fixture_name)

        # Update meta with request info (minimal)
        if "meta" in response:
            response["meta"]["query_id"] = str(uuid.uuid4())
            response["meta"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
            response["meta"]["intent"] = request.intent
            if request.debug and request.debug.compiler_version:
                response["meta"]["compiler_version"] = request.debug.compiler_version

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Insurance Comparison Mock API",
        "version": "mock-0.1.0",
        "endpoints": {
            "health": "GET /health",
            "compare": "POST /compare"
        },
        "note": "This is a mock API for testing. No real data processing."
    }

# Run with: uvicorn server:app --host 0.0.0.0 --port 8001 --reload
