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
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Literal
import uuid
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
import psycopg2
import psycopg2.extras

# Q1 endpoints
from apps.api.q1_endpoints import (
    Q1CoverageRankingRequest,
    Q1CoverageCandidatesRequest,
    execute_coverage_ranking,
    execute_coverage_candidates
)

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

# Database connection configuration (SSOT: port 5433 ONLY)
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/inca_ssot"
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

class CompareIntent(str, Enum):
    """
    Allowed intent values for CompareRequest.
    Q2_COVERAGE_LIMIT_COMPARE added for Q2 Chat flow (coverage limit comparison).
    """
    PRODUCT_SUMMARY = "PRODUCT_SUMMARY"
    COVERAGE_CONDITION_DIFF = "COVERAGE_CONDITION_DIFF"
    COVERAGE_AVAILABILITY = "COVERAGE_AVAILABILITY"
    PREMIUM_REFERENCE = "PREMIUM_REFERENCE"
    Q2_COVERAGE_LIMIT_COMPARE = "Q2_COVERAGE_LIMIT_COMPARE"

class CompareRequest(BaseModel):
    """
    CompareRequest with conditional validation:
    - intent: Must be one of CompareIntent enum values
    - products: Required (min_items=1) for all intents EXCEPT Q2_COVERAGE_LIMIT_COMPARE
    - For Q2_COVERAGE_LIMIT_COMPARE: products can be empty, coverage_codes required
    """
    intent: Literal[
        "PRODUCT_SUMMARY",
        "COVERAGE_CONDITION_DIFF",
        "COVERAGE_AVAILABILITY",
        "PREMIUM_REFERENCE",
        "Q2_COVERAGE_LIMIT_COMPARE"
    ]
    insurers: List[str] = Field(..., min_items=1)
    products: List[ProductInfo] = Field(default_factory=list)
    target_coverages: List[TargetCoverage] = []
    options: Optional[RequestOptions] = RequestOptions()
    debug: Optional[DebugOptions] = DebugOptions()

    # Q2-specific fields (optional for backward compatibility)
    age: Optional[int] = None
    gender: Optional[str] = None
    coverage_codes: Optional[List[str]] = None
    sort_by: Optional[str] = None
    plan_variant_scope: Optional[str] = None
    as_of_date: Optional[str] = None
    query: Optional[str] = None

    @model_validator(mode='after')
    def validate_intent_requirements(self):
        """
        Conditional validation based on intent:
        - For non-Q2 intents: products must have at least 1 item
        - For Q2_COVERAGE_LIMIT_COMPARE: coverage_codes required, products optional
        """
        intent = self.intent

        # Rule 1: Non-Q2 intents require products
        if intent in ["PRODUCT_SUMMARY", "COVERAGE_CONDITION_DIFF", "COVERAGE_AVAILABILITY", "PREMIUM_REFERENCE"]:
            if not self.products or len(self.products) < 1:
                raise ValueError(
                    f"Intent '{intent}' requires at least 1 product. "
                    f"Received {len(self.products)} products."
                )

        # Rule 2: Q2 intent requires coverage_codes
        if intent == "Q2_COVERAGE_LIMIT_COMPARE":
            if not self.coverage_codes or len(self.coverage_codes) < 1:
                raise ValueError(
                    "Intent 'Q2_COVERAGE_LIMIT_COMPARE' requires at least 1 coverage_code. "
                    f"Received: {self.coverage_codes}"
                )
            # Filter out null/empty coverage_codes
            valid_codes = [c for c in self.coverage_codes if c and str(c).strip()]
            if not valid_codes:
                raise ValueError(
                    "Intent 'Q2_COVERAGE_LIMIT_COMPARE' requires at least 1 non-empty coverage_code. "
                    f"All codes are null/empty: {self.coverage_codes}"
                )

        return self

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
        elif self.intent == "Q2_COVERAGE_LIMIT_COMPARE":
            return self._compile_q2_coverage_limit_compare()
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

    def _compile_q2_coverage_limit_compare(self) -> Dict[str, Any]:
        """
        Q2_COVERAGE_LIMIT_COMPARE: Coverage limit comparison (Q2 Chat flow)

        Uses coverage_codes from request (no products needed)
        Returns query plan for Q2 handler to process
        """
        # Get coverage_codes from request (validated in CompareRequest)
        coverage_codes = self.request.coverage_codes if hasattr(self.request, 'coverage_codes') else []

        return {
            "intent": "Q2_COVERAGE_LIMIT_COMPARE",
            "coverage_codes": coverage_codes,
            "insurer_filters": self.insurers
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

class Q2CoverageLimitCompareHandler(IntentHandler):
    """
    Handler for Q2_COVERAGE_LIMIT_COMPARE intent

    Reads pre-computed comparison data from compare_table_v2 table
    Uses coverage_codes from request (no products required)

    Subset Matching Policy:
    - Query by (coverage_code, as_of_date) only
    - Return intersection of requested insurers and available insurers
    - 404 only if no row exists or intersection is empty
    - Inject insurer_code into insurer_rows (using insurer_set order as SSOT)
    """
    def handle(self) -> Dict[str, Any]:
        """
        Fetch Q2 coverage limit comparison data from compare_table_v2

        Supports subset matching: returns available insurers even if requested set is larger

        Returns: Pre-computed comparison payload with:
            - insurer_rows: filtered to requested insurers ∩ available insurers
            - insurer_code: injected into each row
            - debug: requested_insurer_set, available_insurer_set, returned_insurer_set, missing_insurers
        """
        try:
            # Get coverage_code (first one from list)
            coverage_codes = self.query_plan.get("coverage_codes", [])
            if not coverage_codes:
                raise HTTPException(status_code=400, detail="Q2 requires at least one coverage_code")

            coverage_code = coverage_codes[0]

            # Get as_of_date from request (default: 2025-11-26)
            as_of_date = getattr(self.request, 'as_of_date', "2025-11-26")

            # Get insurers from request
            insurers = self.request.insurers

            # Map insurers back to insurer codes (reverse mapping)
            INSURER_ENUM_TO_CODE = {
                "MERITZ": "N01",
                "DB": "N02",
                "HANWHA": "N03",
                "LOTTE": "N05",
                "KB": "N08",
                "HYUNDAI": "N09",
                "SAMSUNG": "N10",
                "HEUNGKUK": "N13"
            }

            requested_insurer_codes = [INSURER_ENUM_TO_CODE.get(ins, ins) for ins in insurers]
            requested_insurer_set = sorted(requested_insurer_codes)

            # Query compare_table_v2 by (coverage_code, as_of_date) ONLY
            # Tie-breaker: largest insurer_set first, then most recent generated_at
            self.cursor.execute("""
                SELECT table_id, payload, insurer_set
                FROM compare_table_v2
                WHERE coverage_code = %s
                  AND as_of_date = %s
                ORDER BY jsonb_array_length(insurer_set) DESC,
                         (payload->'debug'->>'generated_at') DESC
                LIMIT 1
            """, (coverage_code, as_of_date))

            row = self.cursor.fetchone()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"No Q2 data found for coverage_code={coverage_code}, as_of_date={as_of_date}"
                )

            # Extract available insurers from DB row
            available_insurer_set = row['insurer_set']
            payload = dict(row['payload'])

            # Calculate intersection: requested ∩ available
            returned_insurer_set = sorted(list(set(requested_insurer_set) & set(available_insurer_set)))

            if not returned_insurer_set:
                raise HTTPException(
                    status_code=404,
                    detail=f"No matching insurers for coverage_code={coverage_code}. "
                           f"Requested: {requested_insurer_set}, Available: {available_insurer_set}"
                )

            # Calculate missing insurers
            missing_insurers = sorted(list(set(requested_insurer_set) - set(available_insurer_set)))

            # Filter insurer_rows to returned_insurer_set and inject insurer_code
            # SSOT: insurer_set order = insurer_rows order
            insurer_rows = payload.get('insurer_rows', [])
            filtered_rows = []

            for idx, ins_cd in enumerate(available_insurer_set):
                if ins_cd in returned_insurer_set:
                    row_data = insurer_rows[idx] if idx < len(insurer_rows) else {}
                    # Inject insurer_code
                    row_data['insurer_code'] = ins_cd
                    filtered_rows.append(row_data)

            payload['insurer_rows'] = filtered_rows

            # Add debug info
            if 'debug' not in payload:
                payload['debug'] = {}

            payload['debug']['requested_insurer_set'] = requested_insurer_set
            payload['debug']['available_insurer_set'] = available_insurer_set
            payload['debug']['returned_insurer_set'] = returned_insurer_set
            payload['debug']['missing_insurers'] = missing_insurers

            return payload

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in Q2CoverageLimitCompareHandler: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

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
                "PREMIUM_REFERENCE": PremiumReferenceHandler,
                "Q2_COVERAGE_LIMIT_COMPARE": Q2CoverageLimitCompareHandler
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

    # DB ID CHECK (MANDATORY) - Enforce SSOT: inca_ssot@5433
    logger.info("=" * 80)
    logger.info("DB ID CHECK — SSOT Enforcement")
    logger.info(f"  Database URL: {DB_URL}")
    try:
        # Parse URL to get host port (client perspective)
        from urllib.parse import urlparse
        parsed_url = urlparse(DB_URL)
        expected_port = parsed_url.port or 5432

        # Connect and check database name + container port (for logging only)
        test_conn = psycopg2.connect(DB_URL)
        test_cur = test_conn.cursor()
        test_cur.execute("SELECT current_database(), inet_server_port()")
        db_name, container_port = test_cur.fetchone()
        test_cur.close()
        test_conn.close()

        logger.info(f"  Connected DB: {db_name}")
        logger.info(f"  Host Port (from URL): {expected_port}")
        logger.info(f"  Container Port (from DB): {container_port} (informational only)")

        # Validate: DB name + host port only (not container port due to NAT)
        if db_name != 'inca_ssot':
            error_msg = f"SSOT_DB_MISMATCH: expected DB inca_ssot, got {db_name}"
            logger.error(f"❌ {error_msg}")
            logger.error("See: docs/policy/DB_SSOT_LOCK.md")
            raise RuntimeError(error_msg)

        if expected_port != 5433:
            error_msg = f"SSOT_DB_MISMATCH: expected host port 5433, got {expected_port}"
            logger.error(f"❌ {error_msg}")
            logger.error("See: docs/policy/DB_SSOT_LOCK.md")
            raise RuntimeError(error_msg)

        logger.info("✅ DB ID CHECK PASS: inca_ssot@5433 (host port)")
    except psycopg2.Error as e:
        logger.error(f"❌ DB connection failed: {e}")
        raise RuntimeError(f"DB connection failed: {e}")
    logger.info("=" * 80)

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


@app.get("/q5")
async def q5_waiting_period_policy(
    insurers: Optional[str] = None
):
    """
    Q5: 면책/감액 기간 정책 (Contract-level Overlay)

    FROZEN (Q5 Pattern):
    - Data source: q5_waiting_policy_v1.jsonl (Overlay SSOT)
    - Policy values: IMMEDIATE_100 | REDUCTION_1Y | REDUCTION_2Y | UNKNOWN
    - NO Core Model dependency (pure overlay)
    - Evidence-based only (no inference)
    - UNKNOWN is acceptable (document limitations)

    Policy: docs/policy/Q5_WAITING_PERIOD_DECISION.md

    Args:
        insurers: Comma-separated list (optional, default: all)

    Returns:
        {
            "query_id": "Q5",
            "items": [...]
        }
    """
    from apps.api.overlays.q5.loader import load_q5_waiting_policy
    from apps.api.overlays.q5.model import POLICY_DISPLAY

    try:
        # Parse insurer filter
        insurers_filter = None
        if insurers:
            insurers_filter = [i.strip() for i in insurers.split(',')]

        # Load from overlay SSOT
        policies = load_q5_waiting_policy(insurers_filter=insurers_filter)

        # Build response items
        items = []
        for policy in policies:
            # Get first evidence (if available)
            evidence_data = None
            if policy.evidence_refs and len(policy.evidence_refs) > 0:
                ev = policy.evidence_refs[0]
                evidence_data = {
                    "doc_type": ev.get('doc_type', ''),
                    "page": ev.get('page'),
                    "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else '',
                    "pattern": ev.get('pattern', '')
                }

            item = {
                "insurer_key": policy.insurer_key,
                "waiting_period_policy": policy.waiting_period_policy,
                "policy_display": POLICY_DISPLAY.get(policy.waiting_period_policy, policy.waiting_period_policy),
                "evidence_count": len(policy.evidence_refs),
                "evidence": evidence_data
            }

            items.append(item)

        # Sort by policy (most restrictive first), then insurer_key
        # Order: REDUCTION_2Y > REDUCTION_1Y > IMMEDIATE_100 > UNKNOWN
        policy_rank = {
            "REDUCTION_2Y": 0,
            "REDUCTION_1Y": 1,
            "IMMEDIATE_100": 2,
            "UNKNOWN": 3
        }

        items.sort(key=lambda x: (policy_rank.get(x['waiting_period_policy'], 99), x['insurer_key']))

        return {
            "query_id": "Q5",
            "items": items
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Q5 SSOT not found: {str(e)}")
    except Exception as e:
        logger.error(f"Q5 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Q5 error: {str(e)}")


@app.get("/q7")
async def q7_waiver_policy(
    insurers: Optional[str] = None
):
    """
    Q7: 납입면제 사유 정책 (Contract-level Overlay)

    FROZEN (TYPE B Overlay):
    - Data source: q7_waiver_policy_v1.jsonl (Overlay SSOT)
    - waiver_triggers: List of conditions that trigger premium waiver
    - has_sanjeong_teukrye: YES | NO | UNKNOWN (산정특례가 납입면제 사유인지 여부)
    - NO Core Model dependency (pure overlay)
    - Evidence-based only (no inference)
    - UNKNOWN is acceptable (document limitations)

    Policy: docs/policy/Q7_WAIVER_POLICY_OVERLAY.md

    Args:
        insurers: Comma-separated list (optional, default: all)

    Returns:
        {
            "query_id": "Q7",
            "items": [...]
        }
    """
    from apps.api.overlays.q7.loader import load_q7_waiver_policy
    from apps.api.overlays.q7.model import SANJEONG_TEUKRYE_DISPLAY

    try:
        # Parse insurer filter
        insurers_filter = None
        if insurers:
            insurers_filter = [i.strip() for i in insurers.split(',')]

        # Load from overlay SSOT
        policies = load_q7_waiver_policy(insurers_filter=insurers_filter)

        # Build response items
        items = []
        for policy in policies:
            # Get first evidence (if available)
            evidence_data = None
            if policy.evidence_refs and len(policy.evidence_refs) > 0:
                ev = policy.evidence_refs[0]
                evidence_data = {
                    "doc_type": ev.get('doc_type', ''),
                    "page": ev.get('page'),
                    "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else '',
                    "locator": ev.get('locator', '')
                }

            item = {
                "insurer_key": policy.insurer_key,
                "waiver_triggers": policy.waiver_triggers,
                "has_sanjeong_teukrye": policy.has_sanjeong_teukrye,
                "sanjeong_teukrye_display": SANJEONG_TEUKRYE_DISPLAY.get(policy.has_sanjeong_teukrye, policy.has_sanjeong_teukrye),
                "evidence_count": len(policy.evidence_refs),
                "evidence": evidence_data
            }

            items.append(item)

        # Sort by insurer_key (alphabetical)
        items.sort(key=lambda x: x['insurer_key'])

        return {
            "query_id": "Q7",
            "items": items
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Q7 SSOT not found: {str(e)}")
    except Exception as e:
        logger.error(f"Q7 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Q7 error: {str(e)}")


@app.get("/q8")
async def q8_surgery_repeat_policy(
    insurers: Optional[str] = None
):
    """
    Q8: 질병수술비(1~5종) 반복 지급 조건 정책 (Contract-level Overlay)

    FROZEN (TYPE B Overlay):
    - Data source: q8_surgery_repeat_policy_v1.jsonl (Overlay SSOT)
    - repeat_payment_policy: PER_EVENT | ANNUAL_LIMIT | UNKNOWN
    - NO Core Model dependency (pure overlay)
    - Evidence-based only (no inference, no interpretation)
    - UNKNOWN is acceptable (document limitations)
    - Scope: 질병수술비(1~5종) payment frequency ONLY (no specific surgery interpretation)

    Policy: docs/policy/Q8_SURGERY_REPEAT_POLICY_OVERLAY.md

    Args:
        insurers: Comma-separated list (optional, default: all)

    Returns:
        {
            "query_id": "Q8",
            "items": [...]
        }
    """
    from apps.api.overlays.q8.loader import load_q8_surgery_repeat_policy
    from apps.api.overlays.q8.model import POLICY_DISPLAY

    try:
        # Parse insurer filter
        insurers_filter = None
        if insurers:
            insurers_filter = [i.strip() for i in insurers.split(',')]

        # Load from overlay SSOT
        policies = load_q8_surgery_repeat_policy(insurers_filter=insurers_filter)

        # Build response items
        items = []
        for policy in policies:
            # Get first evidence (if available)
            evidence_data = None
            if policy.evidence_refs and len(policy.evidence_refs) > 0:
                ev = policy.evidence_refs[0]
                evidence_data = {
                    "doc_type": ev.get('doc_type', ''),
                    "page": ev.get('page'),
                    "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else ''
                }

            item = {
                "insurer_key": policy.insurer_key,
                "repeat_payment_policy": policy.repeat_payment_policy,
                "display_text": policy.display_text,
                "evidence_count": len(policy.evidence_refs),
                "evidence": evidence_data
            }

            items.append(item)

        # Sort by insurer_key (alphabetical)
        items.sort(key=lambda x: x['insurer_key'])

        return {
            "query_id": "Q8",
            "items": items
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Q8 SSOT not found: {str(e)}")
    except Exception as e:
        logger.error(f"Q8 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Q8 error: {str(e)}")


def extract_duration_from_evidence_text(text: str) -> Optional[int]:
    """
    STEP DEMO-Q11-EVIDENCE-TRUST-02: Extract duration limit from evidence text

    Patterns supported:
    - "1일-180일" (hyphen range)
    - "1~180일" (tilde range)
    - "180일 한도"
    - "1일이상180일한도"

    Returns:
        Duration in days, or None if not found
    """
    import re

    if not text:
        return None

    patterns = [
        r'(\d+)\s*일\s*한도',  # "180일한도", "90일 한도"
        r'1\s*일?\s*-\s*(\d+)\s*일',  # "1일-180일", "1-180일" (hyphen)
        r'1\s*~\s*(\d+)\s*일',  # "1~180일" (tilde)
        r'1\s*일\s*이상\s*(\d+)\s*일\s*한도',  # "1일이상180일한도"
        r'최대\s*(\d+)\s*일',  # "최대180일"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None

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
    - STEP DEMO-Q11-EVIDENCE-TRUST-02: Evidence-based fallback extraction

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
        # HOTFIX-INSURER-PRODUCT-MISMATCH: Load product names from product table (SSOT)
        # Map insurer_key to ins_cd (CORRECTED from insurer table)
        INSURER_KEY_TO_INS_CD = {
            'meritz': 'N01',     # 메리츠
            'hanwha': 'N02',     # 한화
            'db': 'N03',         # DB
            'heungkuk': 'N05',   # 흥국
            'samsung': 'N08',    # 삼성
            'hyundai': 'N09',    # 현대
            'kb': 'N10',         # KB
            'lotte': 'N13'       # 롯데
        }

        # Connect to SSOT DB
        ssot_db_url = "postgresql://postgres:postgres@localhost:5433/inca_ssot"
        conn = psycopg2.connect(ssot_db_url)

        # Load product names from product table (SSOT)
        # RULE: product table is SSOT for product names, NOT product_premium_quote_v2
        product_name_map = {}
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT ins_cd, product_full_name
                FROM product
                WHERE as_of_date = %s
                ORDER BY ins_cd
            """, (as_of_date,))

            rows = cursor.fetchall()
            for row in rows:
                ins_cd = row['ins_cd']
                product_name = row['product_full_name']
                # Map back from ins_cd to insurer_key
                for key, code in INSURER_KEY_TO_INS_CD.items():
                    if code == ins_cd:
                        product_name_map[key] = product_name
                        break
        except Exception as e:
            logger.warning(f"Failed to load product names from product table: {e}")

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

                    # SSOT Normalization: FOUND + NULL → UNKNOWN
                    # Enforce semantic integrity (FOUND = value confirmed)
                    if days_slot.get('status') == 'FOUND' and days_slot.get('value') is None:
                        days_slot = {'status': 'UNKNOWN', 'evidences': []}

                    if daily_slot.get('status') == 'FOUND' and daily_slot.get('value') is None:
                        daily_slot = {'status': 'UNKNOWN', 'evidences': []}

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

                    # Get evidence (with fallback enhancement)
                    # Priority: duration_limit_days evidence → daily_benefit_amount_won evidence
                    days_evidences = days_slot.get('evidences', [])
                    daily_evidences = daily_slot.get('evidences', [])

                    evidence_data = {}
                    if days_evidences and len(days_evidences) > 0:
                        ev = days_evidences[0]
                        evidence_data = {
                            "doc_type": ev.get('doc_type', ''),
                            "page": ev.get('page'),
                            "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else ''
                        }
                    elif daily_evidences and len(daily_evidences) > 0 and daily_slot.get('status') == 'FOUND':
                        # Fallback: Use daily evidence if duration has no evidence but daily is FOUND
                        ev = daily_evidences[0]
                        evidence_data = {
                            "doc_type": ev.get('doc_type', ''),
                            "page": ev.get('page'),
                            "excerpt": ev.get('excerpt', '')[:200] if ev.get('excerpt') else '',
                            "source_slot": "daily_benefit_amount_won"  # Mark fallback source
                        }

                    # STEP Q11-PRODUCT-NAME-FIX-02: Get product name from DB SSOT
                    product_name_value = product_name_map.get(insurer_key, '상품명 정보 없음(DB 미등록)')
                    product_full_name = {
                        "value": product_name_value,
                        "evidence": {}  # No evidence tracking for product names from DB
                    }

                    # Build item with slot-level status (NEW: return status for UI)
                    item = {
                        "insurer_key": insurer_key,
                        "coverage_code": coverage_code,
                        "coverage_name": coverage_title,
                        "product_full_name": product_full_name,  # STEP Q11-PRODUCT-NAME-FIX-01
                        "duration_limit_days": {
                            "status": days_slot.get('status', 'UNKNOWN'),
                            "value": int(days_value) if days_value and str(days_value).isdigit() else None,
                            "evidences": days_evidences
                        },
                        "daily_benefit_amount_won": {
                            "status": daily_slot.get('status', 'UNKNOWN'),
                            "value": int(daily_value) if daily_value and str(daily_value).isdigit() else None,
                            "evidences": daily_evidences
                        },
                        "evidence": evidence_data if evidence_data else None
                    }

                    # STEP DEMO-Q11-EVIDENCE-TRUST-02: Evidence-based fallback for duration
                    if item['duration_limit_days']['value'] is None:
                        # Try extracting from multiple evidence sources (priority order)
                        duration_extracted = None
                        matched_evidence = None

                        # Source 1: duration_limit_days.evidences (highest priority)
                        for ev in days_evidences:
                            excerpt = ev.get('excerpt', '')
                            extracted = extract_duration_from_evidence_text(excerpt)
                            if extracted:
                                duration_extracted = extracted
                                matched_evidence = ev
                                break

                        # Source 2: item.evidence (global evidence)
                        if not duration_extracted and evidence_data:
                            excerpt = evidence_data.get('excerpt', '')
                            extracted = extract_duration_from_evidence_text(excerpt)
                            if extracted:
                                duration_extracted = extracted
                                matched_evidence = evidence_data

                        # Source 3: daily_benefit_amount_won.evidences (fallback)
                        if not duration_extracted:
                            for ev in daily_evidences:
                                excerpt = ev.get('excerpt', '')
                                extracted = extract_duration_from_evidence_text(excerpt)
                                if extracted:
                                    duration_extracted = extracted
                                    matched_evidence = ev
                                    break

                        # Apply extracted duration if found
                        if duration_extracted and matched_evidence:
                            item['duration_limit_days']['status'] = 'FOUND'
                            item['duration_limit_days']['value'] = duration_extracted
                            item['duration_limit_days']['evidences'] = [matched_evidence]

                    items.append(item)

        # Sort: deterministic (NULLS LAST)
        # 1. duration_limit_days.value DESC (None sorts LAST)
        # 2. daily_benefit_amount_won.value DESC (None sorts LAST)
        # 3. insurer_key ASC (tie-break)
        def sort_key(x):
            days = x['duration_limit_days']['value']
            daily = x['daily_benefit_amount_won']['value']
            insurer = x['insurer_key']

            # NULLS LAST: (is_null, -value) ensures None sorts after all numbers
            days_sort = (days is None, -days if days is not None else 0)
            daily_sort = (daily is None, -daily if daily is not None else 0)
            insurer_sort = insurer

            return (days_sort, daily_sort, insurer_sort)

        # STEP DEMO-Q11-EVIDENCE-TRUST-02: Deduplicate items by insurer_key
        # (e.g., db_over41 and db_under40 both map to "db")
        # Priority: FOUND status > evidence exists > higher benefit value
        items_by_insurer = {}
        for item in items:
            key = item['insurer_key']
            if key not in items_by_insurer:
                items_by_insurer[key] = item
            else:
                existing = items_by_insurer[key]
                # Compare priority: FOUND duration > FOUND benefit > higher benefit value
                item_dur_found = item['duration_limit_days']['status'] == 'FOUND'
                existing_dur_found = existing['duration_limit_days']['status'] == 'FOUND'
                item_ben_found = item['daily_benefit_amount_won']['status'] == 'FOUND'
                existing_ben_found = existing['daily_benefit_amount_won']['status'] == 'FOUND'

                if item_dur_found and not existing_dur_found:
                    items_by_insurer[key] = item
                elif item_dur_found == existing_dur_found and item_ben_found and not existing_ben_found:
                    items_by_insurer[key] = item
                elif item_dur_found == existing_dur_found and item_ben_found == existing_ben_found:
                    # Both have same status, compare values
                    item_ben_val = item['daily_benefit_amount_won']['value'] or 0
                    existing_ben_val = existing['daily_benefit_amount_won']['value'] or 0
                    if item_ben_val > existing_ben_val:
                        items_by_insurer[key] = item

        items = list(items_by_insurer.values())
        items.sort(key=sort_key)

        # STEP DEMO-Q11-EVIDENCE-TRUST-02: Ensure Phase-1 8 insurers always visible
        PHASE1_INSURERS = ['kb', 'samsung', 'hyundai', 'db', 'meritz', 'hanwha', 'heungkuk', 'lotte']

        # Check which insurers are missing from items
        present_insurers = {item['insurer_key'] for item in items}
        missing_insurers = [ins for ins in PHASE1_INSURERS if ins not in present_insurers]

        # Add placeholder items for missing insurers (only if no insurer filter specified)
        if not insurers and missing_insurers:
            for insurer_key in missing_insurers:
                # STEP Q11-PRODUCT-NAME-FIX-02: Get product name from DB SSOT
                product_name_value = product_name_map.get(insurer_key, '상품명 정보 없음(DB 미등록)')
                product_full_name = {
                    "value": product_name_value,
                    "evidence": {}
                }

                placeholder_item = {
                    "insurer_key": insurer_key,
                    "coverage_code": "A6200",
                    "coverage_name": "암직접치료입원비",
                    "product_full_name": product_full_name,
                    "duration_limit_days": {
                        "status": "UNKNOWN",
                        "value": None,
                        "evidences": []
                    },
                    "daily_benefit_amount_won": {
                        "status": "UNKNOWN",
                        "value": None,
                        "evidences": []
                    },
                    "evidence": None,
                    "badge": "NOT_IN_PROPOSAL",
                    "note": "가입설계서에 미포함"
                }
                items.append(placeholder_item)

            # Re-sort after adding placeholders
            items.sort(key=sort_key)

        # Add rank
        for i, item in enumerate(items, 1):
            item['rank'] = i

        # Load references from q11_references_v1.jsonl (SSOT: business method only)
        references = []
        references_path = "data/compare_v1/q11_references_v1.jsonl"
        try:
            with open(references_path, 'r', encoding='utf-8') as ref_file:
                for line in ref_file:
                    if not line.strip():
                        continue
                    ref_data = json.loads(line)

                    # Filter by insurers if specified
                    if insurers:
                        allowed_insurers = [i.strip().lower() for i in insurers.split(',')]
                        if ref_data.get('insurer_key', '').lower() not in allowed_insurers:
                            continue

                    references.append(ref_data)
        except FileNotFoundError:
            logger.warning(f"References file not found: {references_path}")
            references = []

        return {
            "query_id": "Q11",
            "as_of_date": as_of_date,
            "coverage_code": "A6200",
            "items": items,
            "references": references
        }

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Data file not found: {data_path}")
    except Exception as e:
        logger.error(f"Q11 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Q11 error: {str(e)}")
    finally:
        # Close DB connection
        if 'conn' in locals():
            try:
                conn.close()
            except Exception:
                pass


@app.get("/q13")
async def q13_subtype_coverage_matrix(
    insurers: Optional[str] = None
):
    """
    Q13: 제자리암/경계성종양 보장 O/X 매트릭스

    LOCK (SSOT):
    - Data source: docs/audit/step_next_81c_subtype_coverage_locked.jsonl
    - Subtypes: in_situ (제자리암), borderline (경계성종양)
    - Output rules:
      - diagnosis_benefit → "O" (✅, usable=true)
      - treatment_trigger → "⚠️" (usable=false, "진단비 아님(치료비 트리거)")
      - definition_only → "ℹ️"
      - excluded → "X" (❌)
      - NO_DATA → "—" (NO SSOT record, NOT excluded)
    - NO estimation, NO pattern matching
    - treatment_trigger MUST NOT be shown as "O"

    Policy: docs/audit/STEP_NEXT_82_Q13_OUTPUT_LOCK.md

    Args:
        insurers: Comma-separated list (optional, default: Phase1 8 insurers)

    Returns:
        {
            "query_id": "Q13",
            "ssot_source": str,
            "data_completeness": {"insurers_with_data": int, "n_total": int},
            "matrix": [
                {
                    "insurer_key": str,
                    "in_situ": {...},
                    "borderline": {...}
                }
            ]
        }
    """
    import json
    from pathlib import Path

    # Phase1 default insurers
    PHASE1_INSURERS = ["samsung", "meritz", "db", "kb", "hanwha", "hyundai", "lotte", "heungkuk"]

    try:
        # Determine target insurers
        if insurers:
            target_insurers = [i.strip().lower() for i in insurers.split(',')]
        else:
            target_insurers = PHASE1_INSURERS

        # Load SSOT
        ssot_path = Path("docs/audit/step_next_81c_subtype_coverage_locked.jsonl")

        # Load all records into dict
        ssot_data = {}  # {insurer_key: record}
        if ssot_path.exists():
            with open(ssot_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    insurer = record.get('insurer_key')
                    if insurer:
                        ssot_data[insurer] = record

        # Build matrix for target insurers
        matrix = []
        insurers_with_data = 0

        for insurer_key in target_insurers:
            record = ssot_data.get(insurer_key)

            if record:
                insurers_with_data += 1
                locked = record.get('subtype_coverage_locked', {})

                # Build cells for in_situ and borderline (unwrap from SSOT)
                cells = {}
                for subtype in ['in_situ', 'borderline']:
                    subtype_data = locked.get(subtype)

                    # If subtype not in SSOT, create NO_DATA cell
                    if not subtype_data:
                        cells[subtype] = {
                            "status_icon": "—",
                            "coverage_kind": None,
                            "usable_as_coverage": False,
                            "display": "NO_DATA",
                            "color": "gray",
                            "evidence_refs": [],
                            "reason": f"SSOT에 {subtype} 없음"
                        }
                        continue

                    coverage_kind = subtype_data.get('coverage_kind')
                    usable = subtype_data.get('usable_as_coverage', False)
                    evidence_refs = subtype_data.get('evidence_refs', [])

                    # Determine display per coverage_kind
                    if coverage_kind == 'diagnosis_benefit':
                        status_icon = "✅"
                        display = "O"
                        color = "green"
                    elif coverage_kind == 'treatment_trigger':
                        status_icon = "⚠️"
                        display = "진단비 아님(치료비 트리거)"
                        color = "orange"
                    elif coverage_kind == 'definition_only':
                        status_icon = "ℹ️"
                        display = "정의 문맥 언급"
                        color = "gray"
                    elif coverage_kind == 'excluded':
                        status_icon = "❌"
                        display = "X"
                        color = "red"
                    else:
                        # Unknown coverage_kind (should not happen with valid SSOT)
                        status_icon = "—"
                        display = "UNKNOWN"
                        color = "gray"

                    cells[subtype] = {
                        "status_icon": status_icon,
                        "coverage_kind": coverage_kind,
                        "usable_as_coverage": usable,
                        "display": display,
                        "color": color,
                        "evidence_refs": evidence_refs
                    }

                # Unwrap: ensure top-level in_situ and borderline
                matrix.append({
                    "insurer_key": insurer_key,
                    "in_situ": cells['in_situ'],
                    "borderline": cells['borderline']
                })

            else:
                # NO_DATA case
                matrix.append({
                    "insurer_key": insurer_key,
                    "in_situ": {
                        "status_icon": "—",
                        "coverage_kind": None,
                        "usable_as_coverage": False,
                        "display": "NO_DATA",
                        "color": "gray",
                        "evidence_refs": [],
                        "reason": "SSOT 레코드 없음"
                    },
                    "borderline": {
                        "status_icon": "—",
                        "coverage_kind": None,
                        "usable_as_coverage": False,
                        "display": "NO_DATA",
                        "color": "gray",
                        "evidence_refs": [],
                        "reason": "SSOT 레코드 없음"
                    }
                })

        return {
            "query_id": "Q13",
            "ssot_source": str(ssot_path),
            "data_completeness": {
                "insurers_with_data": insurers_with_data,
                "n_total": len(target_insurers)
            },
            "matrix": matrix
        }

    except Exception as e:
        logger.error(f"Q13 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
            "q5": "GET /q5 (OVERLAY)",
            "q7": "GET /q7 (OVERLAY)",
            "q8": "GET /q8 (OVERLAY)",
            "q11": "GET /q11 (PHASE2)",
            "q13": "GET /q13 (PHASE2-LIMITED)"
        },
        "compiler_version": COMPILER_VERSION,
        "features": [
            "Product Validation Gate",
            "Fact-First value_text",
            "Evidence Quality Filter",
            "ChatGPT-style UI (STEP NEXT-14)",
            "Q11 Cancer Hospitalization Comparison (PHASE2)",
            "Q13 Subtype Coverage Matrix (PHASE2-LIMITED)"
        ],
        "note": "Production API (DB-backed, evidence-based, fact-first)"
    }


@app.get("/coverage_status")
async def coverage_status(
    coverage_code: str,
    as_of_date: str = "2025-11-26"
):
    """
    GET /coverage_status - Get available insurers for a coverage

    Query params:
    - coverage_code: A4200_1, etc.
    - as_of_date: YYYY-MM-DD (default: 2025-11-26)

    Returns: {"coverage_code": str, "as_of_date": str, "available_insurers": [str]}
    """
    try:
        # Connect to SSOT DB (port 5433)
        ssot_db_url = "postgresql://postgres:postgres@localhost:5433/inca_ssot"
        conn = psycopg2.connect(ssot_db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Query coverage_mapping_ssot for ACTIVE insurers
        cursor.execute("""
            SELECT ins_cd
            FROM coverage_mapping_ssot
            WHERE coverage_code = %s
              AND as_of_date = %s
              AND status = 'ACTIVE'
            ORDER BY ins_cd
        """, (coverage_code, as_of_date))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No active insurers found for coverage_code={coverage_code}, as_of_date={as_of_date}"
            )

        available_insurers = [row['ins_cd'] for row in rows]

        return {
            "coverage_code": coverage_code,
            "as_of_date": as_of_date,
            "available_insurers": available_insurers
        }

    except psycopg2.Error as e:
        logger.error(f"Database error in /coverage_status: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in /coverage_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compare_v2")
async def compare_v2(
    coverage_code: str,
    as_of_date: str = "2025-11-26",
    ins_cds: Optional[str] = None
):
    """
    GET /compare_v2 - Read compare_table_v2 from SSOT DB

    Query params:
    - coverage_code: A4200_1, etc.
    - as_of_date: YYYY-MM-DD (default: 2025-11-26)
    - ins_cds: Comma-separated insurer codes (e.g., N01,N08)

    Returns: compare_table_v2.payload (includes q12_report if exists)
    """
    try:
        # Parse insurer codes
        if not ins_cds:
            raise HTTPException(status_code=400, detail="ins_cds parameter required")

        insurer_list = [code.strip() for code in ins_cds.split(",")]
        insurer_set = sorted(insurer_list)  # Normalize order for exact match

        # Connect to SSOT DB (port 5433)
        ssot_db_url = "postgresql://postgres:postgres@localhost:5433/inca_ssot"
        conn = psycopg2.connect(ssot_db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Query compare_table_v2 by exact insurer_set match
        cursor.execute("""
            SELECT table_id, payload
            FROM compare_table_v2
            WHERE coverage_code = %s
              AND as_of_date = %s
              AND insurer_set = %s::jsonb
        """, (coverage_code, as_of_date, json.dumps(insurer_set)))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No compare_table_v2 row found for coverage_code={coverage_code}, as_of_date={as_of_date}, insurer_set={insurer_set}"
            )

        # Return payload as-is (includes q12_report if it exists)
        payload = row['payload']
        return payload

    except psycopg2.Error as e:
        logger.error(f"Database error in /compare_v2: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in /compare_v2: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Q1 Premium Ranking Endpoint (STEP NEXT Chat UI v2)
# ============================================================================

@app.get("/premium/ranking")
async def premium_ranking(
    age: int,
    sex: str,
    plan_variant: str = "BOTH",
    sort_by: str = "monthly_total",
    top_n: int = 4,
    as_of_date: str = "2025-11-26"
):
    """
    GET /premium/ranking - Q1 Premium Ranking (DB2 SSOT Only)

    Query params:
    - age (required): int, 20-80
    - sex (required): M|F
    - plan_variant (optional): NO_REFUND | GENERAL | BOTH (default: BOTH)
    - sort_by (optional): monthly_total | total (default: monthly_total)
    - top_n (optional): int (default: 4)
    - as_of_date (optional): YYYY-MM-DD (default: 2025-11-26)

    Returns: Q1ViewModel with evidence payload (Evidence-Mandatory, Rail-Only)

    SSOT: product_premium_quote_v2 ONLY (premium_quote is DEPRECATED)
    """
    try:
        # Validate inputs
        if sex not in ["M", "F"]:
            raise HTTPException(status_code=400, detail="sex must be 'M' or 'F'")

        if plan_variant not in ["NO_REFUND", "GENERAL", "BOTH"]:
            raise HTTPException(status_code=400, detail="plan_variant must be 'NO_REFUND', 'GENERAL', or 'BOTH'")

        if sort_by not in ["monthly_total", "total"]:
            raise HTTPException(status_code=400, detail="sort_by must be 'monthly_total' or 'total'")

        if age < 20 or age > 80:
            raise HTTPException(status_code=400, detail="age must be between 20 and 80")

        if top_n < 1 or top_n > 20:
            raise HTTPException(status_code=400, detail="top_n must be between 1 and 20")

        # Premium DB URL (SSOT: product_premium_quote_v2 is in inca_ssot database)
        # Load from .env.ssot: SSOT_DB_URL
        premium_db_url = os.getenv(
            "SSOT_DB_URL",
            "postgresql://postgres:postgres@localhost:5433/inca_ssot"
        )

        conn = psycopg2.connect(premium_db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Determine which variants to query
        if plan_variant == "BOTH":
            variant_filter = ("NO_REFUND", "GENERAL")
        else:
            variant_filter = (plan_variant,)

        # Query product_premium_quote_v2 (DB2 SSOT)
        cursor.execute("""
            SELECT
                ins_cd,
                product_id,
                product_full_name,
                plan_variant,
                age,
                sex,
                premium_monthly_total,
                premium_total_total,
                as_of_date,
                source,
                source_table_id,
                source_row_id
            FROM product_premium_quote_v2
            WHERE age = %s
              AND sex = %s
              AND as_of_date = %s
              AND plan_variant IN %s
            ORDER BY
                CASE WHEN %s = 'monthly_total' THEN premium_monthly_total END ASC,
                CASE WHEN %s = 'total' THEN premium_total_total END ASC,
                ins_cd ASC
        """, (age, sex, as_of_date, variant_filter, sort_by, sort_by))

        rows = cursor.fetchall()

        # For GENERAL variant rows, fetch multiplier evidence from coverage_premium_quote
        multiplier_evidence_map = {}
        if "GENERAL" in variant_filter:
            for row in rows:
                if row['plan_variant'] == 'GENERAL':
                    ins_cd = row['ins_cd']
                    product_id = row['product_id']

                    # Query coverage_premium_quote for multiplier_percent (sample any coverage for this product)
                    cursor.execute("""
                        SELECT DISTINCT multiplier_percent, coverage_code
                        FROM coverage_premium_quote
                        WHERE ins_cd = %s
                          AND product_id = %s
                          AND plan_variant = 'GENERAL'
                          AND age = %s
                          AND sex = %s
                          AND as_of_date = %s
                        LIMIT 1
                    """, (ins_cd, product_id, age, sex, as_of_date))

                    mult_row = cursor.fetchone()
                    if mult_row:
                        key = f"{ins_cd}_{product_id}"
                        multiplier_evidence_map[key] = {
                            "multiplier_percent": mult_row['multiplier_percent'],
                            "coverage_code": mult_row['coverage_code']
                        }

        conn.close()

        # Build Q1 result rows
        insurer_map = {
            "N01": "DB손해보험",
            "N02": "롯데손해보험",
            "N03": "메리츠화재",
            "N05": "삼성화재",
            "N08": "현대해상",
            "N09": "흥국화재",
            "N10": "KB손해보험",
            "N13": "한화손해보험"
        }

        # Group by insurer+product (merge NO_REFUND and GENERAL into single row if BOTH)
        product_map = {}
        for row in rows:
            key = f"{row['ins_cd']}_{row['product_id']}"
            if key not in product_map:
                product_map[key] = {
                    "ins_cd": row['ins_cd'],
                    "insurer_name": insurer_map.get(row['ins_cd'], row['ins_cd']),
                    "product_id": row['product_id'],
                    "product_name": row['product_full_name'],
                    "no_refund": None,
                    "general": None
                }

            variant = row['plan_variant']
            premium_data = {
                "premium_monthly": row['premium_monthly_total'],
                "premium_total": row['premium_total_total'],
                "as_of_date": row['as_of_date'],
                "source": row['source'],
                "source_table_id": row['source_table_id'],
                "source_row_id": row['source_row_id']
            }

            if variant == "NO_REFUND":
                product_map[key]["no_refund"] = premium_data
            elif variant == "GENERAL":
                product_map[key]["general"] = premium_data

        # Convert to list and sort
        result_rows = []
        for key, data in product_map.items():
            # Determine sort key
            if sort_by == "monthly_total":
                # Use NO_REFUND monthly as primary sort key
                sort_key = data["no_refund"]["premium_monthly"] if data["no_refund"] else float('inf')
            else:
                sort_key = data["no_refund"]["premium_total"] if data["no_refund"] else float('inf')

            # Build evidence payload
            evidence = {
                "base_premium": {
                    "source_table": "product_premium_quote_v2",
                    "ins_cd": data["ins_cd"],
                    "product_id": data["product_id"],
                    "age": age,
                    "sex": sex,
                    "as_of_date": as_of_date,
                    "no_refund": data["no_refund"],
                    "general": data["general"]
                }
            }

            # Add rate_multiplier evidence if GENERAL variant exists
            if data["general"]:
                mult_key = f"{data['ins_cd']}_{data['product_id']}"
                if mult_key in multiplier_evidence_map:
                    # Use actual multiplier from coverage_premium_quote
                    evidence["rate_multiplier"] = {
                        "source_table": "coverage_premium_quote",
                        "ins_cd": data["ins_cd"],
                        "product_id": data["product_id"],
                        "multiplier_percent": multiplier_evidence_map[mult_key]["multiplier_percent"],
                        "coverage_code": multiplier_evidence_map[mult_key]["coverage_code"],
                        "as_of_date": as_of_date
                    }
                else:
                    # STEP NEXT: Fallback to 130% when coverage_premium_quote is empty
                    # This is the product-level multiplier used in GENERAL variant calculation
                    evidence["rate_multiplier"] = {
                        "source_table": "product_premium_quote_v2",
                        "ins_cd": data["ins_cd"],
                        "product_id": data["product_id"],
                        "multiplier_percent": 130,
                        "note": "Product-level GENERAL multiplier (hardcoded fallback)",
                        "formula": "GENERAL = NO_REFUND × 130%",
                        "as_of_date": as_of_date
                    }

            result_rows.append({
                "insurer_code": data["ins_cd"],  # ALIGNED WITH FRONTEND (not ins_cd)
                "insurer_name": data["insurer_name"],
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "premium_monthly": data["no_refund"]["premium_monthly"] if data["no_refund"] else None,  # ALIGNED (NO_REFUND baseline)
                "premium_total": data["no_refund"]["premium_total"] if data["no_refund"] else None,  # ALIGNED
                "premium_monthly_general": data["general"]["premium_monthly"] if data["general"] else None,
                "premium_total_general": data["general"]["premium_total"] if data["general"] else None,
                "sort_key": sort_key,
                "evidence": evidence
            })

        # Sort and take top_n
        result_rows.sort(key=lambda x: x["sort_key"])
        top_rows = result_rows[:top_n]

        # Add rank
        for i, row in enumerate(top_rows):
            row["rank"] = i + 1
            del row["sort_key"]  # Remove internal sort key

        # Build Q1ViewModel response
        response = {
            "kind": "Q1",
            "query_params": {
                "age": age,
                "sex": sex,
                "plan_variant": plan_variant,
                "sort_by": sort_by,
                "top_n": top_n,
                "as_of_date": as_of_date
            },
            "rows": top_rows
        }

        return response

    except psycopg2.Error as e:
        logger.error(f"Database error in /premium/ranking: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in /premium/ranking: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STEP-NEXT: Health Check & DB Debug Endpoints
# ============================================================================

@app.get("/healthz")
async def healthz():
    """
    Health check endpoint
    Returns 200 if API is running
    """
    return {"status": "ok", "service": "inca-rag-scope-api"}


@app.get("/debug/db")
async def debug_db():
    """
    Debug endpoint: Verify DB connection and SSOT enforcement

    Returns 500 if DB is not inca_ssot:5433
    Returns 200 with DB details if correct
    """
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT current_database(), inet_server_port()")
        db_name, db_port = cur.fetchone()
        cur.close()
        conn.close()

        # Enforce SSOT: must be inca_ssot on internal port 5432 (container)
        # (Host port 5433 maps to container port 5432)
        if db_name != 'inca_ssot':
            return {
                "status": "error",
                "message": f"❌ DB MISMATCH: Expected inca_ssot, got {db_name}",
                "db_name": db_name,
                "db_port": db_port,
                "db_url": DB_URL.replace('postgres:postgres', '***:***')
            }, 500

        return {
            "status": "ok",
            "message": "✅ SSOT DB connection verified",
            "db_name": db_name,
            "db_port": db_port,
            "db_url": DB_URL.replace('postgres:postgres', '***:***'),
            "note": "Host port 5433 → Container port 5432"
        }

    except Exception as e:
        logger.error(f"DB debug check failed: {e}")
        return {
            "status": "error",
            "message": f"❌ DB connection failed: {str(e)}",
            "db_url": DB_URL.replace('postgres:postgres', '***:***')
        }, 500


# ============================================================================
# Q1 Premium Ranking Endpoints
# ============================================================================

@app.post("/q1/coverage_ranking")
def q1_coverage_ranking(request: Q1CoverageRankingRequest):
    """
    Q1 BY_COVERAGE premium ranking endpoint

    Purpose: Rank products by coverage-specific premium sum
    Rules:
    - SSOT DB only (inca_ssot@5433)
    - Product-level aggregation: (insurer_code, product_code)
    - MANDATORY: insurer_name + product_name in all rows
    - EXCLUDE rows without insurer_name OR product_name
    - Top 4 results only
    """
    try:
        conn = psycopg2.connect(DB_URL)
        try:
            result = execute_coverage_ranking(request, conn)
            return result.dict()
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Q1 coverage_ranking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/q1/coverage_candidates")
def q1_coverage_candidates(request: Q1CoverageCandidatesRequest):
    """
    Q1 coverage candidates resolution endpoint

    Purpose: Resolve user's free-text coverage query to canonical coverage_code candidates
    Rules:
    - Deterministic matching only (NO LLM)
    - Uses 4 strategies: exact → contains → alias → token
    - Returns max 3 candidates sorted by score desc
    - coverage_code MUST be 신정원 canonical
    """
    try:
        # Note: execute_coverage_candidates creates its own DB connection via coverage_resolver
        result = execute_coverage_candidates(request, None)
        return result.dict()

    except Exception as e:
        logger.error(f"Q1 coverage_candidates error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn apps.api.server:app --host 0.0.0.0 --port 8000 --reload
