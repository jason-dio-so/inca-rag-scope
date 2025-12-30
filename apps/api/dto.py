#!/usr/bin/env python3
"""
Data Transfer Objects (DTOs) for Amount API
STEP NEXT-11: Amount API Integration & Presentation Lock

IMMUTABLE RULES:
1. amount_fact is READ-ONLY (no writes from API)
2. Status values are LOCKED: CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
3. NO inference, NO recommendations, NO comparisons
4. Audit lineage REQUIRED for all responses
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


# ============================================================================
# Amount Status (LOCKED Enum)
# ============================================================================

AmountStatus = Literal["CONFIRMED", "UNCONFIRMED", "NOT_AVAILABLE"]

# Status semantics:
# - CONFIRMED: Amount explicitly stated in proposal document + evidence exists
# - UNCONFIRMED: Coverage exists but amount not stated in documents
# - NOT_AVAILABLE: Coverage itself does not exist for this insurer/product


# ============================================================================
# Amount Evidence DTO
# ============================================================================

class AmountEvidenceDTO(BaseModel):
    """
    Evidence reference for amount value

    IMMUTABLE: This DTO structure is LOCKED as of STEP NEXT-11
    """
    status: Literal["found", "not_found"]
    source: Optional[str] = None  # e.g., "가입설계서 p.4"
    snippet: Optional[str] = None  # Max 400 chars, normalized

    class Config:
        frozen = True  # Immutable


# ============================================================================
# Amount Audit Metadata DTO
# ============================================================================

class AmountAuditDTO(BaseModel):
    """
    Audit lineage metadata for amount pipeline

    Links response to frozen audit run for compliance tracking
    """
    audit_run_id: Optional[uuid.UUID] = None  # From audit_runs table
    freeze_tag: Optional[str] = None  # e.g., "freeze/pre-10b2g2-20251229-024400"
    git_commit: Optional[str] = None  # Frozen commit hash

    class Config:
        frozen = True


# ============================================================================
# Amount Value DTO (Core)
# ============================================================================

class AmountDTO(BaseModel):
    """
    Amount value with status and evidence

    CRITICAL RULES:
    1. status determines presentation:
       - CONFIRMED → show value_text (unified format via presentation layer)
       - UNCONFIRMED → presentation varies by insurer type (see presentation_utils)
       - NOT_AVAILABLE → show "해당 담보 없음"

    2. value_text is ALWAYS from amount_fact.value_text (NEVER from snippet)

    3. evidence_ref is OPTIONAL but REQUIRED for CONFIRMED status

    4. NO comparisons, NO recommendations, NO inference

    IMMUTABLE: This DTO structure is LOCKED as of STEP NEXT-11
    """
    status: AmountStatus
    value_text: Optional[str] = None  # e.g., "1천만원" (from amount_fact ONLY)
    source_doc_type: Optional[str] = None  # e.g., "가입설계서"
    source_priority: Optional[str] = None  # e.g., "PRIMARY"
    evidence: Optional[AmountEvidenceDTO] = None
    notes: List[str] = Field(default_factory=list)

    class Config:
        frozen = True


# ============================================================================
# Coverage with Amount DTO
# ============================================================================

class CoverageWithAmountDTO(BaseModel):
    """
    Coverage instance with associated amount

    Used for compare API responses
    """
    coverage_code: str  # Canonical code (e.g., "A1300")
    coverage_name: str  # Canonical name (e.g., "상해사망")
    amount: AmountDTO
    audit: Optional[AmountAuditDTO] = None

    class Config:
        frozen = True


# ============================================================================
# Insurer Comparison Row DTO
# ============================================================================

class InsurerAmountDTO(BaseModel):
    """
    Single insurer's amount data in comparison table

    Presentation rules (UI/Frontend):
    - CONFIRMED: Display value_text (unified format via presentation_utils)
    - UNCONFIRMED: Type-aware display (see apps.api.presentation_utils)
    - NOT_AVAILABLE: Display "해당 담보 없음" (strikethrough/disabled)

    FORBIDDEN presentations:
    - Color coding for "better/worse"
    - Sorting by amount value
    - Highlighting max/min
    - Average calculation
    - Recommendations
    """
    insurer: str  # e.g., "SAMSUNG"
    product_name: str
    amount: AmountDTO

    class Config:
        frozen = True


# ============================================================================
# Compare Response with Amount DTO
# ============================================================================

class CompareWithAmountResponseDTO(BaseModel):
    """
    Comparison response including amount data

    PRESENTATION LOCK:
    - Comparison is FACT-BASED ONLY
    - NO ranking, NO recommendations
    - Status-based presentation (see InsurerAmountDTO)
    """
    coverage_code: str
    coverage_name: str
    insurers: List[InsurerAmountDTO]
    audit: Optional[AmountAuditDTO] = None

    class Config:
        frozen = True


# ============================================================================
# Amount Query Request DTO
# ============================================================================

class AmountQueryRequest(BaseModel):
    """
    Request for amount query API

    READ-ONLY: This endpoint ONLY reads from amount_fact table
    NO writes, NO updates, NO inference
    """
    insurer: str  # Insurer key (e.g., "SAMSUNG")
    coverage_code: Optional[str] = None  # Canonical code
    coverage_name_raw: Optional[str] = None  # Raw name from proposal
    include_audit: bool = Field(default=True, description="Include audit metadata")
    include_evidence: bool = Field(default=True, description="Include evidence snippet")


# ============================================================================
# Amount Query Response DTO
# ============================================================================

class AmountQueryResponseDTO(BaseModel):
    """
    Response for amount query API

    Single coverage amount lookup result
    """
    query_id: uuid.UUID
    timestamp: datetime
    coverage: CoverageWithAmountDTO
    audit: Optional[AmountAuditDTO] = None

    class Config:
        frozen = True


# ============================================================================
# Status Presentation Rules (LOCKED)
# ============================================================================

class AmountPresentationRules:
    """
    Presentation rules for amount status

    LOCKED: These rules are IMMUTABLE as of STEP NEXT-11
    Any UI changes must respect these rules
    """

    CONFIRMED = {
        "display": "value_text",  # Show actual amount value
        "style": "normal",  # Default text style
        "color": "inherit",  # No special coloring
        "note": None
    }

    UNCONFIRMED = {
        "display": "(Type-aware, see presentation_utils)",  # Varies by insurer type
        "style": "muted",  # Gray/subdued
        "color": "#666666",  # Gray
        "note": "표기 방식은 보험사/상품 구조에 따라 다릅니다"
    }

    NOT_AVAILABLE = {
        "display": "해당 담보 없음",  # Fixed text
        "style": "disabled",  # Strikethrough or disabled
        "color": "#999999",  # Light gray
        "note": "해당 보험사/상품에 이 담보가 없습니다"
    }

    @staticmethod
    def get_display_text(status: AmountStatus, value_text: Optional[str] = None) -> str:
        """
        Get display text for amount based on status

        DEPRECATED: Use apps.api.presentation_utils.format_amount_for_display() instead
        This provides type-aware display logic for UNCONFIRMED status

        Args:
            status: Amount status (CONFIRMED | UNCONFIRMED | NOT_AVAILABLE)
            value_text: Actual amount value (required for CONFIRMED)

        Returns:
            Display text for UI
        """
        if status == "CONFIRMED":
            return value_text if value_text else "확인 불가"
        elif status == "UNCONFIRMED":
            return "(Type-aware)"  # Use presentation_utils instead
        elif status == "NOT_AVAILABLE":
            return AmountPresentationRules.NOT_AVAILABLE["display"]
        else:
            return "확인 불가"

    @staticmethod
    def get_style(status: AmountStatus) -> dict:
        """Get CSS style rules for status"""
        rules_map = {
            "CONFIRMED": AmountPresentationRules.CONFIRMED,
            "UNCONFIRMED": AmountPresentationRules.UNCONFIRMED,
            "NOT_AVAILABLE": AmountPresentationRules.NOT_AVAILABLE
        }
        return rules_map.get(status, {"style": "normal", "color": "inherit"})


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_amount_dto(amount: AmountDTO) -> None:
    """
    Validate AmountDTO against presentation rules

    Raises:
        ValueError: If DTO violates rules
    """
    # Rule 1: CONFIRMED requires value_text
    if amount.status == "CONFIRMED":
        if not amount.value_text:
            raise ValueError("CONFIRMED status requires value_text")
        if amount.value_text in ["확인 불가", "해당 담보 없음"]:
            raise ValueError(f"CONFIRMED status cannot have fixed text: {amount.value_text}")

    # Rule 2: UNCONFIRMED/NOT_AVAILABLE should not have value_text
    if amount.status in ["UNCONFIRMED", "NOT_AVAILABLE"]:
        if amount.value_text and amount.value_text not in ["해당 담보 없음"]:
            raise ValueError(f"{amount.status} status should not have actual value_text")

    # Rule 3: Evidence required for CONFIRMED
    if amount.status == "CONFIRMED":
        if not amount.evidence or amount.evidence.status != "found":
            # Warning only (not fatal)
            import logging
            logging.warning(f"CONFIRMED amount without evidence: {amount.value_text}")
