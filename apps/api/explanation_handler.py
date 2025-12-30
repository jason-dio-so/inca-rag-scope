#!/usr/bin/env python3
"""
Comparison Explanation Handler
STEP NEXT-12: Comparison Explanation Layer (Fact-First, Non-Recommendation)

CRITICAL RULES:
1. Input: AmountDTO (READ-ONLY, from STEP NEXT-11)
2. Output: ExplanationDTO (rule-based sentences)
3. NO direct access to amount_fact (use AmountDTO only)
4. NO amount inference/calculation
5. Templates are LOCKED (see ExplanationTemplateRegistry)

This handler converts AmountDTO status → fact-based explanation sentences.
"""

from typing import List, Optional
from datetime import datetime
import uuid
import logging

from apps.api.dto import (
    AmountDTO,
    AmountStatus,
    AmountAuditDTO
)
from apps.api.explanation_dto import (
    InsurerExplanationDTO,
    CoverageComparisonExplanationDTO,
    ExplanationResponseDTO,
    ExplanationTemplateRegistry
)

logger = logging.getLogger(__name__)


# ============================================================================
# Explanation Builder (Rule-Based)
# ============================================================================

class ExplanationBuilder:
    """
    Build explanation sentences from AmountDTO

    DESIGN:
    - Input: AmountDTO (from STEP NEXT-11 API)
    - Processing: Template-based sentence generation
    - Output: InsurerExplanationDTO

    FORBIDDEN:
    - Direct amount_fact access
    - Amount calculation/inference
    - LLM-based free-form generation
    - Comparative sentence generation
    """

    def build_insurer_explanation(
        self,
        insurer: str,
        coverage_name: str,
        amount_dto: AmountDTO
    ) -> InsurerExplanationDTO:
        """
        Build explanation for single insurer

        Args:
            insurer: Insurer name (e.g., "삼성화재")
            coverage_name: Coverage canonical name (e.g., "암진단비")
            amount_dto: Amount DTO (from STEP NEXT-11)

        Returns:
            InsurerExplanationDTO with rule-based explanation

        Raises:
            ValueError: If status/value_text contract violated
        """
        # Validate contract: CONFIRMED requires value_text
        if amount_dto.status == "CONFIRMED":
            if not amount_dto.value_text:
                raise ValueError(
                    f"Contract violation: CONFIRMED status without value_text "
                    f"(insurer={insurer}, coverage={coverage_name})"
                )

        # Validate contract: UNCONFIRMED/NOT_AVAILABLE should not have value_text
        if amount_dto.status in ["UNCONFIRMED", "NOT_AVAILABLE"]:
            if amount_dto.value_text:
                logger.warning(
                    f"Unexpected value_text for {amount_dto.status} status: "
                    f"insurer={insurer}, coverage={coverage_name}, "
                    f"value_text={amount_dto.value_text}"
                )

        # Generate explanation from template (RULE-BASED)
        explanation_text = ExplanationTemplateRegistry.generate_explanation(
            insurer=insurer,
            coverage_name=coverage_name,
            status=amount_dto.status,
            value_text=amount_dto.value_text
        )

        # Build DTO
        return InsurerExplanationDTO(
            insurer=insurer,
            status=amount_dto.status,
            explanation=explanation_text,
            value_text=amount_dto.value_text
        )


# ============================================================================
# Comparison Explanation Handler
# ============================================================================

class ComparisonExplanationHandler:
    """
    Generate comparison explanations for multiple insurers

    DESIGN:
    - Input: List of (insurer, AmountDTO) pairs
    - Processing: Parallel explanation generation (NO cross-comparison)
    - Output: CoverageComparisonExplanationDTO

    CRITICAL RULES:
    1. Explanations are PARALLEL (not comparative)
    2. Order is PRESERVED from input
    3. NO sorting by amount
    4. NO highlighting max/min
    5. Each explanation is INDEPENDENT

    FORBIDDEN:
    - Sorting by amount value
    - Adding comparison clauses
    - Highlighting best/worst
    - Calculating statistics
    """

    def __init__(self):
        self.builder = ExplanationBuilder()

    def generate_coverage_explanation(
        self,
        coverage_code: str,
        coverage_name: str,
        insurer_amounts: List[tuple[str, AmountDTO]],
        audit: Optional[AmountAuditDTO] = None
    ) -> CoverageComparisonExplanationDTO:
        """
        Generate comparison explanation for single coverage

        Args:
            coverage_code: Canonical coverage code (e.g., "A4200_1")
            coverage_name: Canonical coverage name (e.g., "암진단비")
            insurer_amounts: List of (insurer_name, amount_dto) tuples
                             ORDER IS PRESERVED (do not sort!)
            audit: Optional audit metadata (from amount pipeline)

        Returns:
            CoverageComparisonExplanationDTO with parallel explanations

        Raises:
            ValueError: If contract violated
        """
        # Generate parallel explanations (INDEPENDENT, NOT COMPARATIVE)
        explanations: List[InsurerExplanationDTO] = []

        for insurer, amount_dto in insurer_amounts:
            try:
                explanation = self.builder.build_insurer_explanation(
                    insurer=insurer,
                    coverage_name=coverage_name,
                    amount_dto=amount_dto
                )
                explanations.append(explanation)

            except ValueError as e:
                logger.error(
                    f"Failed to build explanation: insurer={insurer}, "
                    f"coverage={coverage_name}, error={e}"
                )
                raise

        # Build comparison explanation DTO
        # CRITICAL: Order is PRESERVED from input (no sorting!)
        return CoverageComparisonExplanationDTO(
            coverage_code=coverage_code,
            coverage_name=coverage_name,
            comparison_explanation=explanations,
            audit=audit
        )

    def generate_multi_coverage_explanation(
        self,
        coverage_data: List[dict],
        audit: Optional[AmountAuditDTO] = None
    ) -> ExplanationResponseDTO:
        """
        Generate explanations for multiple coverages

        Args:
            coverage_data: List of coverage dictionaries:
                [
                    {
                        "coverage_code": "A4200_1",
                        "coverage_name": "암진단비",
                        "insurer_amounts": [
                            ("삼성화재", AmountDTO(...)),
                            ("KB손해보험", AmountDTO(...)),
                        ]
                    },
                    ...
                ]
            audit: Optional global audit metadata

        Returns:
            ExplanationResponseDTO with all coverage explanations

        Raises:
            ValueError: If contract violated
        """
        coverage_explanations: List[CoverageComparisonExplanationDTO] = []

        for coverage in coverage_data:
            try:
                explanation = self.generate_coverage_explanation(
                    coverage_code=coverage["coverage_code"],
                    coverage_name=coverage["coverage_name"],
                    insurer_amounts=coverage["insurer_amounts"],
                    audit=audit
                )
                coverage_explanations.append(explanation)

            except (KeyError, ValueError) as e:
                logger.error(
                    f"Failed to generate coverage explanation: "
                    f"coverage={coverage.get('coverage_code')}, error={e}"
                )
                raise

        # Build response
        return ExplanationResponseDTO(
            query_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            coverages=coverage_explanations,
            audit=audit
        )


# ============================================================================
# Explanation Validator (Contract Enforcement)
# ============================================================================

class ExplanationValidator:
    """
    Validate explanation output against contract

    VALIDATION RULES:
    1. NO forbidden words in explanations
    2. NO cross-insurer comparisons
    3. CONFIRMED explanations contain value_text
    4. UNCONFIRMED explanations use fixed text
    5. NOT_AVAILABLE explanations use fixed text
    6. NO sorting by amount detected
    """

    FORBIDDEN_PATTERNS = [
        '더', '보다', '반면', '그러나', '하지만',
        '유리', '불리', '높다', '낮다', '많다', '적다',
        '차이', '비교', '우수', '열등', '좋', '나쁜',
        '가장', '최고', '최저', '평균', '합계',
        '추천', '제안', '권장', '선택', '판단'
    ]

    CONFIRMED_REQUIRED_PATTERNS = [
        '가입설계서에',
        '명시되어 있습니다'
    ]

    UNCONFIRMED_REQUIRED_PATTERNS = [
        '금액이 명시되어 있지 않습니다'
    ]

    NOT_AVAILABLE_REQUIRED_PATTERNS = [
        '해당 담보가 존재하지 않습니다'
    ]

    @staticmethod
    def validate_explanation(explanation: InsurerExplanationDTO) -> bool:
        """
        Validate single explanation DTO

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check forbidden words
        for pattern in ExplanationValidator.FORBIDDEN_PATTERNS:
            if pattern in explanation.explanation:
                raise ValueError(
                    f"FORBIDDEN pattern detected: '{pattern}' in "
                    f"'{explanation.explanation}'"
                )

        # Validate status-specific patterns
        if explanation.status == "CONFIRMED":
            # CONFIRMED must have value_text
            if not explanation.value_text:
                raise ValueError(
                    f"CONFIRMED explanation without value_text: "
                    f"{explanation.explanation}"
                )

            # CONFIRMED must contain required patterns
            for pattern in ExplanationValidator.CONFIRMED_REQUIRED_PATTERNS:
                if pattern not in explanation.explanation:
                    raise ValueError(
                        f"CONFIRMED explanation missing pattern '{pattern}': "
                        f"{explanation.explanation}"
                    )

        elif explanation.status == "UNCONFIRMED":
            # UNCONFIRMED must NOT have value_text
            if explanation.value_text:
                raise ValueError(
                    f"UNCONFIRMED explanation with value_text: "
                    f"{explanation.value_text}"
                )

            # UNCONFIRMED must contain required pattern
            for pattern in ExplanationValidator.UNCONFIRMED_REQUIRED_PATTERNS:
                if pattern not in explanation.explanation:
                    raise ValueError(
                        f"UNCONFIRMED explanation missing pattern '{pattern}': "
                        f"{explanation.explanation}"
                    )

        elif explanation.status == "NOT_AVAILABLE":
            # NOT_AVAILABLE must NOT have value_text
            if explanation.value_text:
                raise ValueError(
                    f"NOT_AVAILABLE explanation with value_text: "
                    f"{explanation.value_text}"
                )

            # NOT_AVAILABLE must contain required pattern
            for pattern in ExplanationValidator.NOT_AVAILABLE_REQUIRED_PATTERNS:
                if pattern not in explanation.explanation:
                    raise ValueError(
                        f"NOT_AVAILABLE explanation missing pattern '{pattern}': "
                        f"{explanation.explanation}"
                    )

        return True

    @staticmethod
    def validate_comparison(
        comparison: CoverageComparisonExplanationDTO
    ) -> bool:
        """
        Validate coverage comparison explanation

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Validate each explanation
        for explanation in comparison.comparison_explanation:
            ExplanationValidator.validate_explanation(explanation)

        # Check for cross-insurer references
        # (simplified heuristic: explanations should not reference other insurers)
        all_insurers = [e.insurer for e in comparison.comparison_explanation]

        for explanation in comparison.comparison_explanation:
            for other_insurer in all_insurers:
                if other_insurer != explanation.insurer:
                    if other_insurer in explanation.explanation:
                        raise ValueError(
                            f"Cross-insurer reference detected: "
                            f"{explanation.insurer} explanation mentions "
                            f"{other_insurer}"
                        )

        return True

    @staticmethod
    def validate_response(response: ExplanationResponseDTO) -> bool:
        """
        Validate full explanation response

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        for coverage in response.coverages:
            ExplanationValidator.validate_comparison(coverage)

        return True
