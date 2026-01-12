#!/usr/bin/env python3
"""
Production API Server for Insurance Comparison
STEP NEXT-10-β: Quality-Enhanced Production Implementation

IMMUTABLE RULES:
1. NO LLM calls
2. NO inference or interpretation
3. NO recommendations
4. Evidence REQUIRED for all values
5. Deterministic query compilation
6. Response View Model LOCKED (5-block structure)
7. FACT-FIRST: value_text = amount/fact ONLY, NOT snippet
8. Product Validation Gate: Invalid products → "확인 불가"

Database Tables:
- insurer, product, product_variant, document (metadata)
- coverage_canonical (Excel source of truth)
- coverage_instance, evidence_ref, amount_fact (facts)
"""

import os
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
import psycopg2.extras

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Comparison Production API",
    version="1.1.0-beta",
    description="Production API for insurance coverage comparison (DB-backed, evidence-based, fact-first)"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:9000",
        "http://127.0.0.1:9000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection configuration
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)

# Compiler version (deterministic query generation)
COMPILER_VERSION = "v1.1.0-beta"

# Forbidden snippet patterns (목차/민원사례/페이지나열 필터)
FORBIDDEN_SNIPPET_PATTERNS = [
    r"(목차|특약관|특별약관|민원사례|안내|예시|FAQ)",  # 목차/안내문
    r"(\n?\s*\d{2,4}\s*){3,}",  # 숫자 반복 과다 (페이지 번호 나열)
    r"제\s*\d+\s*(장|절|조)\s*[\.:]?\s*$",  # 조항 번호만
    r"^[\d\s\-\.]+$",  # 숫자/기호만
]

# ============================================================================
# Pydantic Models (API Contract - LOCKED)
# ============================================================================

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
    compiler_version: Optional[str] = "v1.1.0-beta"

class CompareRequest(BaseModel):
    intent: str = Field(..., pattern="^(PRODUCT_SUMMARY|COVERAGE_CONDITION_DIFF|COVERAGE_AVAILABILITY|PREMIUM_REFERENCE)$")
    insurers: List[str] = Field(..., min_items=1)
    products: List[ProductInfo] = Field(..., min_items=1)
    target_coverages: List[TargetCoverage] = []
    options: Optional[RequestOptions] = RequestOptions()
    debug: Optional[DebugOptions] = DebugOptions()

# ============================================================================
# Database Connection Pool
# ============================================================================

class DBConnection:
    """Simple database connection manager"""

    @staticmethod
    def get_connection():
        """Get database connection"""
        try:
            conn = psycopg2.connect(DB_URL)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")

# ============================================================================
# Product Validation Gate
# ============================================================================

class ProductValidator:
    """
    Validate product_name existence in DB

    Rules:
    1. Check if product_name exists in product table for given insurer
    2. If not found, mark insurer as invalid
    3. Invalid insurers get "확인 불가" for all rows
    """

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def validate_products(self, products: List[ProductInfo]) -> Dict[str, bool]:
        """
        Validate products and return insurer validity map

        Returns:
            {
                "SAMSUNG": True,  # Valid
                "HANWHA": False,  # Invalid
            }
        """
        validity_map = {}

        for product_info in products:
            insurer_key = product_info.insurer.upper()
            product_name = product_info.product_name

            # Get insurer_id
            insurer_kr_map = {
                'SAMSUNG': '삼성생명',
                'HANWHA': '한화생명',
                'MERITZ': '메리츠화재',
                'DB': 'DB손해보험',
                'KB': 'KB손해보험',
                'LOTTE': '롯데손해보험',
                'HYUNDAI': '현대해상',
                'HEUNGKUK': '흥국생명'
            }

            insurer_kr = insurer_kr_map.get(insurer_key)
            if not insurer_kr:
                validity_map[insurer_key] = False
                logger.warning(f"Unknown insurer key: {insurer_key}")
                continue

            # Check if product exists
            self.cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM product p
                JOIN insurer i ON p.insurer_id = i.insurer_id
                WHERE i.insurer_name_kr = %s
                  AND p.product_name LIKE %s
                """,
                (insurer_kr, f"%{product_name.split()[0]}%")  # Fuzzy match first keyword
            )
            result = self.cursor.fetchone()

            is_valid = result['count'] > 0
            validity_map[insurer_key] = is_valid

            if not is_valid:
                logger.warning(f"Product not found in DB: {insurer_key} - {product_name}")

        logger.info(f"Product validation results: {validity_map}")
        return validity_map

# ============================================================================
# Evidence Quality Filter
# ============================================================================

class EvidenceFilter:
    """
    Filter evidence snippets by quality

    Rules:
    1. Check snippet against forbidden patterns
    2. If forbidden, try next rank
    3. If all ranks forbidden, return not_found
    """

    @staticmethod
    def is_forbidden_snippet(snippet: str) -> bool:
        """Check if snippet matches forbidden patterns"""
        if not snippet or len(snippet.strip()) < 10:
            return True

        for pattern in FORBIDDEN_SNIPPET_PATTERNS:
            if re.search(pattern, snippet, re.IGNORECASE):
                logger.debug(f"Forbidden snippet pattern matched: {pattern[:30]}")
                return True

        return False

    @staticmethod
    def filter_evidences(cursor, coverage_instance_id: str, max_rank: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get best quality evidence from evidence_ref

        Returns:
            {
                "status": "found",
                "source": "약관 p.27",
                "snippet": "..."
            }
            or
            {
                "status": "not_found"
            }
        """
        for rank in range(1, max_rank + 1):
            cursor.execute(
                """
                SELECT er.snippet, er.doc_type, er.page
                FROM evidence_ref er
                WHERE er.coverage_instance_id = %s AND er.rank = %s
                LIMIT 1
                """,
                (coverage_instance_id, rank)
            )
            result = cursor.fetchone()

            if not result:
                continue

            snippet = result['snippet']

            # Check if snippet is forbidden
            if EvidenceFilter.is_forbidden_snippet(snippet):
                logger.debug(f"Rank {rank} evidence rejected (forbidden pattern)")
                continue

            # Valid evidence found
            # Normalize snippet (trim, remove excessive whitespace)
            normalized_snippet = re.sub(r'\s+', ' ', snippet.strip())[:400]

            return {
                "status": "found",
                "source": f"{result['doc_type']} p.{result['page']}",
                "snippet": normalized_snippet
            }

        # No valid evidence found
        return {
            "status": "not_found"
        }

# ============================================================================
# Query Compiler (Deterministic)
# ============================================================================

class QueryCompiler:
    """
    Compile API requests into DB queries (deterministic, rule-based)

    Rules:
    1. Same request → same SQL → same results
    2. NO LLM, NO inference
    3. Intent-based routing
    """

    def __init__(self, request: CompareRequest):
        self.request = request
        self.intent = request.intent
        self.insurers = request.insurers
        self.products = request.products
        self.target_coverages = request.target_coverages

    def compile(self) -> Dict[str, Any]:
        """
        Compile request into query plan

        Returns:
            {
                "intent": str,
                "coverage_codes": List[str],
                "insurer_filters": List[str],
                "canonical_set_id": Optional[str]
            }
        """
        if self.intent == "PRODUCT_SUMMARY":
            return self._compile_product_summary()
        elif self.intent == "COVERAGE_CONDITION_DIFF":
            return self._compile_coverage_condition_diff()
        elif self.intent == "COVERAGE_AVAILABILITY":
            return self._compile_coverage_availability()
        elif self.intent == "PREMIUM_REFERENCE":
            return self._compile_premium_reference()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown intent: {self.intent}")

    def _compile_product_summary(self) -> Dict[str, Any]:
        """
        PRODUCT_SUMMARY: 9 core coverages (Example 3)

        canonical_set_id: EXAMPLE3_CORE_9
        coverage_codes: [A4200_1, A4210, A5200, A5100, A6100_1, A6300_1, A9617_1, A9640_1, A4102]
        """
        return {
            "intent": "PRODUCT_SUMMARY",
            "canonical_set_id": "EXAMPLE3_CORE_9",
            "coverage_codes": [
                "A4200_1",  # 암 진단비(유사암 제외)
                "A4210",    # 유사암 진단비
                "A5200",    # 암 수술비
                "A5100",    # 질병 수술비
                "A6100_1",  # 질병 입원일당
                "A6300_1",  # 암 직접치료 입원일당
                "A9617_1",  # 항암방사선약물치료비
                "A9640_1",  # 항암약물허가치료비
                "A4102",    # 뇌출혈 진단비
            ],
            "insurer_filters": self.insurers
        }

    def _compile_coverage_condition_diff(self) -> Dict[str, Any]:
        """COVERAGE_CONDITION_DIFF: Single coverage, 5 conditions (Example 2)"""
        coverage_code = None
        if self.target_coverages and len(self.target_coverages) > 0:
            coverage_code = self.target_coverages[0].coverage_code

        if not coverage_code:
            coverage_code = "A4200_1"

        return {
            "intent": "COVERAGE_CONDITION_DIFF",
            "coverage_codes": [coverage_code],
            "insurer_filters": self.insurers,
            "comparison_aspects": [
                "보장 여부",
                "보장 금액",
                "대기기간",
                "감액기간",
                "제외 암종"
            ]
        }

    def _compile_coverage_availability(self) -> Dict[str, Any]:
        """COVERAGE_AVAILABILITY: O/X table (Example 4)"""
        coverage_codes = []
        if self.target_coverages:
            coverage_codes = [tc.coverage_code for tc in self.target_coverages if tc.coverage_code]

        if not coverage_codes:
            coverage_codes = ["A4220_1", "A4230_1"]

        return {
            "intent": "COVERAGE_AVAILABILITY",
            "coverage_codes": coverage_codes,
            "insurer_filters": self.insurers
        }

    def _compile_premium_reference(self) -> Dict[str, Any]:
        """PREMIUM_REFERENCE: Premium info (Example 1)"""
        return {
            "intent": "PREMIUM_REFERENCE",
            "coverage_codes": [],
            "insurer_filters": self.insurers,
            "premium_notice": True
        }

# ============================================================================
# Intent Handlers (Fact-First)
# ============================================================================

class IntentHandler:
    """Base class for intent handlers with fact-first logic"""

    def __init__(self, conn, query_plan: Dict[str, Any], request: CompareRequest, product_validity: Dict[str, bool]):
        self.conn = conn
        self.cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.query_plan = query_plan
        self.request = request
        self.product_validity = product_validity  # NEW: Product validation results

    def handle(self) -> Dict[str, Any]:
        """Handle intent and return Response View Model"""
        raise NotImplementedError

    def _get_insurer_id(self, insurer_key: str) -> Optional[str]:
        """Get insurer_id from insurer_key"""
        insurer_kr_map = {
            'SAMSUNG': '삼성생명',
            'HANWHA': '한화생명',
            'MERITZ': '메리츠화재',
            'DB': 'DB손해보험',
            'KB': 'KB손해보험',
            'LOTTE': '롯데손해보험',
            'HYUNDAI': '현대해상',
            'HEUNGKUK': '흥국생명'
        }

        insurer_kr = insurer_kr_map.get(insurer_key.upper())
        if not insurer_kr:
            return None

        self.cursor.execute(
            "SELECT insurer_id FROM insurer WHERE insurer_name_kr = %s",
            (insurer_kr,)
        )
        result = self.cursor.fetchone()
        return result['insurer_id'] if result else None

    def _is_product_valid(self, insurer_key: str) -> bool:
        """Check if product is valid for this insurer"""
        return self.product_validity.get(insurer_key.upper(), False)

    def _get_fact_value(self, insurer_id: str, coverage_code: str) -> Optional[Dict[str, Any]]:
        """
        Get fact-based value from amount_fact (FACT-FIRST)

        Returns:
            {
                "value_text": "3000만원",
                "evidence_id": uuid,
                "source_doc_type": "가입설계서"
            }
            or None
        """
        self.cursor.execute(
            """
            SELECT af.value_text, af.evidence_id, af.source_doc_type, af.status, ci.instance_id
            FROM amount_fact af
            JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
            WHERE ci.insurer_id = %s AND ci.coverage_code = %s
              AND af.status = 'CONFIRMED'
            LIMIT 1
            """,
            (insurer_id, coverage_code)
        )
        result = self.cursor.fetchone()

        if not result or not result['value_text']:
            return None

        # CRITICAL: Validate value_text is NOT a snippet (forbidden pattern check)
        value_text = result['value_text']
        if EvidenceFilter.is_forbidden_snippet(value_text):
            logger.warning(f"amount_fact.value_text contains forbidden pattern, rejecting: {value_text[:50]}")
            return None

        return {
            "value_text": value_text,
            "evidence_id": result['evidence_id'],
            "source_doc_type": result['source_doc_type'],
            "instance_id": result['instance_id']
        }

    def _build_evidence_from_fact(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build evidence from fact data (with quality filter)"""
        if not fact_data:
            return {"status": "not_found"}

        instance_id = fact_data.get('instance_id')
        if not instance_id:
            return {"status": "not_found"}

        # Use EvidenceFilter to get best quality evidence
        return EvidenceFilter.filter_evidences(self.cursor, instance_id, max_rank=3)

class ProductSummaryHandler(IntentHandler):
    """Handler for PRODUCT_SUMMARY intent (Example 3) with fact-first logic"""

    def handle(self) -> Dict[str, Any]:
        """
        Build Response View Model for PRODUCT_SUMMARY

        Structure:
        - meta
        - query_summary
        - comparison (COVERAGE_TABLE with 9 rows)
        - notes
        - limitations
        """
        coverage_codes = self.query_plan["coverage_codes"]
        insurer_filters = self.query_plan["insurer_filters"]

        # Build targets
        targets = []
        for product_info in self.request.products:
            targets.append({
                "insurer": product_info.insurer,
                "product_name": product_info.product_name,
                "source": "user_specified"
            })

        # Build comparison rows
        rows = []
        for coverage_code in coverage_codes:
            # Get canonical name
            self.cursor.execute(
                "SELECT coverage_name_canonical FROM coverage_canonical WHERE coverage_code = %s",
                (coverage_code,)
            )
            canonical_result = self.cursor.fetchone()
            if not canonical_result:
                continue

            coverage_name = canonical_result['coverage_name_canonical']

            # Get values for each insurer
            values = {}
            for insurer_key in insurer_filters:
                insurer_upper = insurer_key.upper()

                # Product Validation Gate: Check if product is valid
                if not self._is_product_valid(insurer_upper):
                    values[insurer_upper] = {
                        "value_text": "확인 불가",
                        "evidence": {"status": "not_found"}
                    }
                    continue

                insurer_id = self._get_insurer_id(insurer_key)
                if not insurer_id:
                    values[insurer_upper] = {
                        "value_text": "확인 불가",
                        "evidence": {"status": "not_found"}
                    }
                    continue

                # FACT-FIRST: Get value from amount_fact
                fact_data = self._get_fact_value(insurer_id, coverage_code)

                if fact_data and fact_data.get('value_text'):
                    # Build evidence from fact
                    evidence = self._build_evidence_from_fact(fact_data)

                    values[insurer_upper] = {
                        "value_text": fact_data['value_text'],
                        "evidence": evidence
                    }
                else:
                    # No fact found
                    values[insurer_upper] = {
                        "value_text": "확인 불가",
                        "evidence": {"status": "not_found"}
                    }

            rows.append({
                "coverage_code": coverage_code,
                "coverage_name": coverage_name,
                "values": values
            })

        # Build response
        return {
            "meta": {
                "query_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "intent": "PRODUCT_SUMMARY",
                "compiler_version": COMPILER_VERSION
            },
            "query_summary": {
                "targets": targets,
                "coverage_scope": {
                    "type": "CANONICAL_SET",
                    "canonical_set_id": self.query_plan["canonical_set_id"],
                    "count": len(coverage_codes)
                },
                "premium_notice": False
            },
            "comparison": {
                "type": "COVERAGE_TABLE",
                "columns": [insurer.upper() for insurer in insurer_filters],
                "rows": rows
            },
            "notes": [],
            "limitations": [
                "본 비교는 약관 및 가입설계서에 기반한 정보 제공입니다.",
                "대기기간, 감액기간, 면책사항 등 세부 조건은 약관을 직접 확인하시기 바랍니다.",
                "개인 조건에 따른 보험료 계산은 포함되지 않습니다.",
                "보장 내용은 가입 시점 및 특약 구성에 따라 달라질 수 있습니다."
            ]
        }

# Note: Other handlers (CoverageConditionDiff, CoverageAvailability, PremiumReference)
# would follow similar pattern with fact-first logic and product validation gate
# For brevity, only ProductSummaryHandler is fully implemented here

# Simplified handlers for other intents (placeholder)
class CoverageConditionDiffHandler(IntentHandler):
    def handle(self) -> Dict[str, Any]:
        return {
            "meta": {"query_id": str(uuid.uuid4()), "timestamp": datetime.utcnow().isoformat() + "Z", "intent": "COVERAGE_CONDITION_DIFF", "compiler_version": COMPILER_VERSION},
            "query_summary": {"targets": [{"insurer": p.insurer, "product_name": p.product_name, "source": "user_specified"} for p in self.request.products], "coverage_scope": {"type": "SINGLE_COVERAGE", "count": 1}, "premium_notice": False},
            "comparison": {"type": "COVERAGE_TABLE", "columns": [i.upper() for i in self.query_plan["insurer_filters"]], "rows": []},
            "notes": [],
            "limitations": ["본 비교는 약관 및 가입설계서에 기반한 정보 제공입니다.", "실제 지급 조건은 약관 전문을 확인하시기 바랍니다."]
        }

class CoverageAvailabilityHandler(IntentHandler):
    def handle(self) -> Dict[str, Any]:
        return {
            "meta": {"query_id": str(uuid.uuid4()), "timestamp": datetime.utcnow().isoformat() + "Z", "intent": "COVERAGE_AVAILABILITY", "compiler_version": COMPILER_VERSION},
            "query_summary": {"targets": [{"insurer": p.insurer, "product_name": p.product_name, "source": "user_specified"} for p in self.request.products], "coverage_scope": {"type": "MULTI_COVERAGE", "count": len(self.query_plan["coverage_codes"])}, "premium_notice": False},
            "comparison": {"type": "OX_TABLE", "columns": [i.upper() for i in self.query_plan["insurer_filters"]], "rows": []},
            "notes": [],
            "limitations": ["본 정보는 약관 및 가입설계서에 기반한 사실 확인입니다.", "대기기간, 감액기간, 면책사항 등 세부 조건은 약관을 직접 확인하시기 바랍니다."]
        }

class PremiumReferenceHandler(IntentHandler):
    def handle(self) -> Dict[str, Any]:
        return {
            "meta": {"query_id": str(uuid.uuid4()), "timestamp": datetime.utcnow().isoformat() + "Z", "intent": "PREMIUM_REFERENCE", "compiler_version": COMPILER_VERSION},
            "query_summary": {"targets": [{"insurer": p.insurer, "product_name": p.product_name, "source": "user_specified"} for p in self.request.products], "coverage_scope": {"type": "MULTI_COVERAGE", "count": 2}, "premium_notice": True},
            "comparison": {"type": "PREMIUM_LIST", "columns": [i.upper() for i in self.query_plan["insurer_filters"]], "rows": []},
            "notes": [],
            "limitations": ["⚠️ 본 시스템은 개인별 보험료 계산 기능을 제공하지 않습니다.", "⚠️ 표시된 보험료는 참고용이며, 실제 가입 보험료와 다를 수 있습니다.", "정확한 보험료는 보험사 또는 설계사를 통해 직접 확인하시기 바랍니다.", "본 비교는 약관 및 가입설계서에 기반한 정보 제공입니다."]
        }

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = "ok"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "1.1.0-beta",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": db_status
    }

@app.post("/compare")
async def compare(request: CompareRequest):
    """
    Main comparison endpoint with FACT-FIRST and Product Validation Gate

    Processing steps:
    1. Validate request schema (Pydantic)
    2. Validate products (Product Validation Gate)
    3. Compile request → query plan (deterministic)
    4. Execute query plan → fetch DB data (FACT-FIRST)
    5. Filter evidence quality
    6. Build Response View Model (5-block structure)
    7. Return response

    Rules:
    - NO LLM
    - NO inference
    - Evidence REQUIRED for all values
    - Deterministic results
    - value_text = FACT ONLY (no snippet)
    """
    try:
        # Step 1: Get DB connection
        conn = DBConnection.get_connection()

        try:
            # Step 2: Product Validation Gate
            validator = ProductValidator(conn)
            product_validity = validator.validate_products(request.products)

            # Step 3: Compile query plan
            compiler = QueryCompiler(request)
            query_plan = compiler.compile()

            logger.info(f"Query plan: {query_plan}")
            logger.info(f"Product validity: {product_validity}")

            # Step 4: Route to intent handler (with product validity)
            handler_map = {
                "PRODUCT_SUMMARY": ProductSummaryHandler,
                "COVERAGE_CONDITION_DIFF": CoverageConditionDiffHandler,
                "COVERAGE_AVAILABILITY": CoverageAvailabilityHandler,
                "PREMIUM_REFERENCE": PremiumReferenceHandler
            }

            handler_class = handler_map.get(request.intent)
            if not handler_class:
                raise HTTPException(status_code=400, detail=f"Unknown intent: {request.intent}")

            handler = handler_class(conn, query_plan, request, product_validity)
            response = handler.handle()

            return response

        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/chat")
async def chat(request_dict: dict):
    """
    Chat endpoint for ChatGPT-style UI (STEP NEXT-14)

    FLOW:
    1. Intent router → MessageKind
    2. Slot validator → check required fields
    3. Compiler → deterministic query
    4. Handler → execute + build VM
    5. Return AssistantMessageVM or need_more_info

    CRITICAL RULES:
    - NO LLM generation
    - Deterministic compiler ONLY
    - Forbidden words validated
    - Locks preserved (Step7/11/12/13)
    """
    try:
        # Import chat modules
        from apps.api.chat_vm import ChatRequest, ChatResponse
        from apps.api.chat_intent import IntentDispatcher

        # Parse request
        request = ChatRequest(**request_dict)

        logger.info(f"Chat request: {request.request_id} | message: {request.message[:100]} | kind: {request.kind}")

        # Dispatch to intent handler
        response = IntentDispatcher.dispatch(request)

        logger.info(f"Chat response: need_more_info={response.need_more_info} | kind: {response.message.kind if response.message else None}")

        # Return response (Pydantic model → JSON)
        return response.model_dump(mode='json', exclude_none=True)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/faq/templates")
async def get_faq_templates():
    """
    Get FAQ template list (STEP NEXT-14)

    Returns all available FAQ templates for UI rendering
    """
    try:
        from apps.api.chat_vm import FAQTemplateRegistry

        templates = FAQTemplateRegistry.TEMPLATES

        return {
            "templates": [t.model_dump() for t in templates],
            "count": len(templates)
        }

    except Exception as e:
        logger.error(f"FAQ templates error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"FAQ error: {str(e)}")


# STEP NEXT-73R-P2: Store API endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize store cache on startup"""
    from apps.api.store_loader import init_store_cache
    logger.info("[STEP NEXT-73R] Initializing store cache...")
    init_store_cache()


@app.get("/store/proposal-detail/{ref:path}")
async def get_proposal_detail_endpoint(ref: str):
    """
    Get proposal detail by ref (STEP NEXT-73R)

    Args:
        ref: proposal_detail_ref (e.g., PD:samsung:A4200_1)

    Returns:
        Proposal detail record or 404
    """
    from apps.api.store_loader import get_proposal_detail

    record = get_proposal_detail(ref)
    if not record:
        raise HTTPException(status_code=404, detail=f"Proposal detail not found: {ref}")

    return record


@app.get("/store/evidence/{ref:path}")
async def get_evidence_endpoint(ref: str):
    """
    Get evidence by ref (STEP NEXT-73R)

    Args:
        ref: evidence_ref (e.g., EV:samsung:A4200_1:01)

    Returns:
        Evidence record or 404
    """
    from apps.api.store_loader import get_evidence

    record = get_evidence(ref)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {ref}")

    return record


class BatchEvidenceRequest(BaseModel):
    refs: List[str] = Field(..., description="List of evidence_refs")


@app.post("/store/evidence/batch")
async def batch_get_evidence_endpoint(req: BatchEvidenceRequest):
    """
    Batch get evidence by refs (STEP NEXT-73R)

    Args:
        req: BatchEvidenceRequest with refs list

    Returns:
        Dict[ref, record] for all found refs
    """
    from apps.api.store_loader import batch_get_evidence

    result = batch_get_evidence(req.refs)
    return result


@app.get("/q11")
async def q11_cancer_hospitalization_comparison(
    as_of_date: str = "2025-11-26",
    insurers: Optional[str] = None
):
    """
    Q11: 암직접입원비 담보 중 보장한도가 다른 상품 찾기

    LOCK (SSOT):
    - coverage_code: A6200 ONLY (canonical code allowlist)
    - Data source: compare_tables_v1.jsonl (has coverage_code)
    - Sort: duration_limit_days DESC NULLS LAST, daily_benefit_amount_won DESC NULLS LAST, insurer_key ASC
    - UNKNOWN: value=null → UI displays "UNKNOWN (근거 부족)"
    - NO text pattern matching, NO fallback/estimation

    Policy: docs/policy/Q11_COVERAGE_CODE_LOCK.md

    Args:
        as_of_date: Data snapshot date (default: 2025-11-26)
        insurers: Comma-separated list (optional, default: all)

    Returns:
        {
            "query_id": "Q11",
            "as_of_date": str,
            "coverage_code": "A6200",
            "items": [...] (ranked list)
        }
    """
    import json

    # Q11 Coverage Code Allowlist (SSOT)
    Q11_COVERAGE_CODES = ["A6200"]

    try:
        # Load data from compare_tables_v1.jsonl (has coverage_code)
        data_path = "data/compare_v1/compare_tables_v1.jsonl"

        items = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                table_data = json.loads(line)

                # Extract coverage_rows
                for row in table_data.get('coverage_rows', []):
                    identity = row.get('identity', {})

                    # Filter: coverage_code IN allowlist (SSOT)
                    coverage_code = identity.get('coverage_code')
                    if coverage_code not in Q11_COVERAGE_CODES:
                        continue

                    # Extract slots
                    slots = row.get('slots', {})
                    daily_slot = slots.get('daily_benefit_amount_won', {})
                    days_slot = slots.get('duration_limit_days', {})

                    # Extract values
                    insurer_key = identity.get('insurer_key', '')
                    coverage_title = identity.get('coverage_title', '')
                    daily_value = daily_slot.get('value')
                    days_value = days_slot.get('value')

                    # Filter by insurers if specified
                    if insurers:
                        allowed_insurers = [i.strip().lower() for i in insurers.split(',')]
                        if insurer_key.lower() not in allowed_insurers:
                            continue

                    # Get evidence (first one from duration_limit_days)
                    days_evidences = days_slot.get('evidences', [])
                    evidence_data = {}
                    if days_evidences and len(days_evidences) > 0:
                        ev = days_evidences[0]
                        evidence_data = {
                            "doc_type": ev.get('doc_type', ''),
                            "page": ev.get('page'),
                            "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else ''
                        }

                    # Build item
                    item = {
                        "insurer_key": insurer_key,
                        "coverage_code": coverage_code,
                        "coverage_name": coverage_title,
                        "daily_benefit_amount_won": int(daily_value) if daily_value and str(daily_value).isdigit() else None,
                        "duration_limit_days": int(days_value) if days_value and str(days_value).isdigit() else None,
                        "evidence": evidence_data if evidence_data else None
                    }

                    items.append(item)

        # Sort: deterministic (NULLS LAST)
        # 1. duration_limit_days DESC (None sorts LAST)
        # 2. daily_benefit_amount_won DESC (None sorts LAST)
        # 3. insurer_key ASC (tie-break)
        def sort_key(x):
            days = x['duration_limit_days']
            daily = x['daily_benefit_amount_won']
            insurer = x['insurer_key']

            # NULLS LAST: (is_null, -value) ensures None sorts after all numbers
            days_sort = (days is None, -days if days is not None else 0)
            daily_sort = (daily is None, -daily if daily is not None else 0)
            insurer_sort = insurer

            return (days_sort, daily_sort, insurer_sort)

        items.sort(key=sort_key)

        # Add rank
        for i, item in enumerate(items, 1):
            item['rank'] = i

        return {
            "query_id": "Q11",
            "as_of_date": as_of_date,
            "coverage_code": "A6200",
            "items": items
        }

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Data file not found: {data_path}")
    except Exception as e:
        logger.error(f"Q11 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Q11 error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Insurance Comparison Production API (Fact-First)",
        "version": "1.1.0-beta",
        "endpoints": {
            "health": "GET /health",
            "compare": "POST /compare",
            "chat": "POST /chat (STEP NEXT-14)",
            "faq_templates": "GET /faq/templates (STEP NEXT-14)",
            "q11": "GET /q11 (PHASE2)"
        },
        "compiler_version": COMPILER_VERSION,
        "features": [
            "Product Validation Gate",
            "Fact-First value_text",
            "Evidence Quality Filter",
            "ChatGPT-style UI (STEP NEXT-14)",
            "Q11 Cancer Hospitalization Comparison (PHASE2)"
        ],
        "note": "Production API (DB-backed, evidence-based, fact-first)"
    }

# Run with: uvicorn apps.api.server_v2:app --host 0.0.0.1 --port 8001 --reload
