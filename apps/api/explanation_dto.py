#!/usr/bin/env python3
"""
Comparison Explanation View Model DTOs
STEP NEXT-12: Comparison Explanation Layer (Fact-First, Non-Recommendation)

CONSTITUTIONAL RULES:
1. NO recommendations (better/worse/유리/불리)
2. NO evaluations (높다/낮다/많다/적다)
3. NO calculations (합계/평균/차이/비율)
4. NO sorting by amount
5. NO visual comparisons (색상/아이콘/그래프)
6. NO amount inference (snippet 재검색 금지)
7. NO treating UNCONFIRMED as CONFIRMED

This layer provides FACT-ONLY explanations based on AmountDTO status.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid

from apps.api.dto import AmountStatus, AmountAuditDTO


# ============================================================================
# Explanation Sentence DTO (Rule-Based)
# ============================================================================

class InsurerExplanationDTO(BaseModel):
    """
    Single insurer's explanation sentence (rule-based, fact-only)

    CRITICAL RULES:
    1. Sentence is generated from TEMPLATE (NOT LLM)
    2. Templates are status-based (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
    3. NO comparative language (더/보다/반면/그러나)
    4. NO evaluative language (유리/불리/높다/낮다)
    5. Sentences are INDEPENDENT (no cross-reference)

    FORBIDDEN WORDS:
    - 더 높습니다, 더 낮습니다
    - 유리합니다, 불리합니다
    - 차이가 있습니다
    - 삼성은 KB보다
    - 가장 큰 금액
    - 보다, 반면, 그러나, 하지만
    """
    insurer: str  # e.g., "삼성화재"
    status: AmountStatus  # CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
    explanation: str  # Rule-based sentence (NEVER free-form LLM)
    value_text: Optional[str] = None  # For CONFIRMED only (from AmountDTO)

    class Config:
        frozen = True  # Immutable

    @field_validator('explanation')
    @classmethod
    def validate_no_forbidden_words(cls, v: str) -> str:
        """
        Enforce forbidden language policy

        DELEGATES to: apps.api.policy.forbidden_language (SINGLE SOURCE)

        NOTE: Step12 templates are LOCKED and not modified.
        This validator is called AFTER template generation to ensure compliance.
        """
        from apps.api.policy.forbidden_language import validate_text

        try:
            validate_text(v)
        except ValueError as e:
            raise ValueError(
                f"FORBIDDEN language in explanation: {e}\n"
                f"Explanation sentences must be FACT-ONLY (no comparisons/evaluations)"
            )

        return v


# ============================================================================
# Coverage Comparison Explanation View Model
# ============================================================================

class CoverageComparisonExplanationDTO(BaseModel):
    """
    Comparison explanation for a single coverage across multiple insurers

    DESIGN PRINCIPLES:
    1. Explanations are PARALLEL (NOT comparative)
    2. Each insurer explanation is INDEPENDENT
    3. NO sorting by amount
    4. NO highlighting max/min
    5. Order is preserved from input

    USAGE:
    - Frontend displays explanations as independent blocks
    - NO sentence recombination in UI
    - NO emphasis/abbreviation/summarization
    """
    coverage_code: str  # e.g., "A4200_1"
    coverage_name: str  # e.g., "암진단비"
    comparison_explanation: List[InsurerExplanationDTO]  # Parallel explanations
    audit: Optional[AmountAuditDTO] = None  # Shared audit metadata

    class Config:
        frozen = True

    @field_validator('comparison_explanation')
    @classmethod
    def validate_no_sorting_by_amount(cls, v: List[InsurerExplanationDTO]) -> List[InsurerExplanationDTO]:
        """
        Prevent sorting by amount value

        Order MUST be preserved from input (e.g., insurer input order)
        """
        # NOTE: We cannot check actual sorting here, but this validator
        # documents the contract requirement
        return v


# ============================================================================
# Explanation Response (Multi-Coverage)
# ============================================================================

class ExplanationResponseDTO(BaseModel):
    """
    Multi-coverage explanation response

    Used for batch comparison queries
    """
    query_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    coverages: List[CoverageComparisonExplanationDTO]
    audit: Optional[AmountAuditDTO] = None  # Global audit metadata

    class Config:
        frozen = True


# ============================================================================
# Explanation Template (Rule-Based, Frozen)
# ============================================================================

class ExplanationTemplateRegistry:
    """
    LOCKED template registry for explanation sentence generation

    CRITICAL RULES:
    1. Templates are STATIC (no parameterized comparisons)
    2. Templates use ONLY {insurer}, {coverage_name}, {value_text}
    3. NO templates with comparative clauses
    4. Templates are FACT-ONLY statements

    MODIFICATION POLICY:
    - Template changes require code review + test update
    - New templates must pass forbidden-word validation
    - Templates are version-locked with STEP NEXT-12
    """

    # CONFIRMED template
    CONFIRMED_TEMPLATE = "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."

    # UNCONFIRMED template
    UNCONFIRMED_TEMPLATE = "{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."

    # NOT_AVAILABLE template
    NOT_AVAILABLE_TEMPLATE = "{insurer}에는 해당 담보가 존재하지 않습니다."

    @staticmethod
    def generate_explanation(
        insurer: str,
        coverage_name: str,
        status: AmountStatus,
        value_text: Optional[str] = None
    ) -> str:
        """
        Generate explanation sentence from template

        RULE-BASED (NOT LLM):
        - Status determines template
        - Template parameters are substituted
        - NO free-form generation

        Args:
            insurer: Insurer name (e.g., "삼성화재")
            coverage_name: Coverage canonical name (e.g., "암진단비")
            status: Amount status (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
            value_text: Amount text (REQUIRED for CONFIRMED)

        Returns:
            Fact-only explanation sentence

        Raises:
            ValueError: If CONFIRMED without value_text
        """
        if status == "CONFIRMED":
            if not value_text:
                raise ValueError("CONFIRMED status requires value_text")
            return ExplanationTemplateRegistry.CONFIRMED_TEMPLATE.format(
                insurer=insurer,
                coverage_name=coverage_name,
                value_text=value_text
            )

        elif status == "UNCONFIRMED":
            return ExplanationTemplateRegistry.UNCONFIRMED_TEMPLATE.format(
                insurer=insurer,
                coverage_name=coverage_name
            )

        elif status == "NOT_AVAILABLE":
            return ExplanationTemplateRegistry.NOT_AVAILABLE_TEMPLATE.format(
                insurer=insurer
            )

        else:
            raise ValueError(f"Unknown status: {status}")
