#!/usr/bin/env python3
"""
Tests for Comparison Explanation Layer
STEP NEXT-12: Comparison Explanation Layer (Fact-First, Non-Recommendation)

TEST STRATEGY:
1. Template-based generation (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
2. Forbidden word detection
3. Contract validation (status vs value_text)
4. Parallel explanations (no cross-comparison)
5. Order preservation
6. Audit metadata inclusion
"""

import pytest
from apps.api.dto import AmountDTO, AmountEvidenceDTO, AmountAuditDTO
from apps.api.explanation_dto import (
    InsurerExplanationDTO,
    CoverageComparisonExplanationDTO,
    ExplanationResponseDTO,
    ExplanationTemplateRegistry
)
from apps.api.explanation_handler import (
    ExplanationBuilder,
    ComparisonExplanationHandler,
    ExplanationValidator
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def confirmed_amount_dto():
    """CONFIRMED status with value_text"""
    return AmountDTO(
        status="CONFIRMED",
        value_text="3천만원",
        source_doc_type="가입설계서",
        evidence=AmountEvidenceDTO(
            status="found",
            source="가입설계서 p.4",
            snippet="암진단비: 3천만원"
        )
    )


@pytest.fixture
def unconfirmed_amount_dto():
    """UNCONFIRMED status without value_text"""
    return AmountDTO(
        status="UNCONFIRMED",
        value_text=None,
        source_doc_type=None,
        evidence=None
    )


@pytest.fixture
def not_available_amount_dto():
    """NOT_AVAILABLE status"""
    return AmountDTO(
        status="NOT_AVAILABLE",
        value_text=None,
        source_doc_type=None,
        evidence=None
    )


@pytest.fixture
def audit_metadata():
    """Sample audit metadata"""
    return AmountAuditDTO(
        audit_run_id="f2e58b52-f22d-4d66-8850-df464954c9b8",
        freeze_tag="freeze/pre-10b2g2-20251229-024400",
        git_commit="c6fad903c4782c9b78c44563f0f47bf13f9f3417"
    )


# ============================================================================
# Test Suite 1: Template-Based Generation
# ============================================================================

class TestTemplateBasedGeneration:
    """Test explanation template generation"""

    def test_confirmed_template(self):
        """CONFIRMED status generates correct template"""
        explanation = ExplanationTemplateRegistry.generate_explanation(
            insurer="삼성화재",
            coverage_name="암진단비",
            status="CONFIRMED",
            value_text="3천만원"
        )

        assert "삼성화재" in explanation
        assert "암진단비" in explanation
        assert "3천만원" in explanation
        assert "가입설계서에" in explanation
        assert "명시되어 있습니다" in explanation

    def test_unconfirmed_template(self):
        """UNCONFIRMED status generates correct template"""
        explanation = ExplanationTemplateRegistry.generate_explanation(
            insurer="KB손해보험",
            coverage_name="암진단비",
            status="UNCONFIRMED",
            value_text=None
        )

        assert "KB손해보험" in explanation
        assert "암진단비" in explanation
        assert "금액이 명시되어 있지 않습니다" in explanation

    def test_not_available_template(self):
        """NOT_AVAILABLE status generates correct template"""
        explanation = ExplanationTemplateRegistry.generate_explanation(
            insurer="현대해상",
            coverage_name="특수담보",
            status="NOT_AVAILABLE",
            value_text=None
        )

        assert "현대해상" in explanation
        assert "해당 담보가 존재하지 않습니다" in explanation

    def test_confirmed_without_value_text_raises(self):
        """CONFIRMED status without value_text raises ValueError"""
        with pytest.raises(ValueError, match="CONFIRMED status requires value_text"):
            ExplanationTemplateRegistry.generate_explanation(
                insurer="삼성화재",
                coverage_name="암진단비",
                status="CONFIRMED",
                value_text=None  # ❌ WRONG
            )


# ============================================================================
# Test Suite 2: Forbidden Word Detection
# ============================================================================

class TestForbiddenWordDetection:
    """Test forbidden word validation in explanations"""

    @pytest.mark.parametrize("forbidden_pattern,explanation_text", [
        # Evaluative comparisons (FORBIDDEN)
        ("유리", "삼성화재가 유리합니다"),
        ("불리", "메리츠는 불리한 조건입니다"),
        ("더 높", "삼성은 더 높습니다"),
        ("보다 낮", "메리츠가 보다 낮습니다"),
        ("A가 B보다", "삼성화재가 메리츠보다 좋습니다"),
        # Contrastive conjunctions (FORBIDDEN)
        ("반면", "삼성은 높지만 반면 메리츠는 낮습니다"),
        ("그러나", "삼성은 높습니다. 그러나 메리츠는 낮습니다"),
        ("하지만", "삼성은 높습니다. 하지만 메리츠는 낮습니다"),
        # Extremes/Rankings (FORBIDDEN)
        ("가장", "삼성이 가장 높습니다"),
        ("최고", "최고입니다"),
        ("최저", "최저입니다"),
        # Recommendations (FORBIDDEN)
        ("추천", "삼성을 추천합니다"),
        ("제안", "메리츠를 제안합니다"),
        ("권장", "KB를 권장합니다"),
        # Calculations (FORBIDDEN)
        ("평균", "평균은 2천만원입니다"),
        ("합계", "합계는 5천만원입니다"),
    ])
    def test_forbidden_word_raises(self, forbidden_pattern, explanation_text):
        """Forbidden patterns in evaluative context raise ValueError"""
        with pytest.raises((ValueError, Exception)):  # Can be ValueError or ValidationError
            InsurerExplanationDTO(
                insurer="삼성화재",
                status="CONFIRMED",
                explanation=explanation_text,
                value_text="3천만원"
            )

    def test_valid_explanation_passes(self):
        """Valid explanation (no forbidden words) passes"""
        # Should NOT raise
        explanation = InsurerExplanationDTO(
            insurer="삼성화재",
            status="CONFIRMED",
            explanation="삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.",
            value_text="3천만원"
        )

        assert explanation.insurer == "삼성화재"
        assert explanation.status == "CONFIRMED"


# ============================================================================
# Test Suite 3: Contract Validation (Status vs value_text)
# ============================================================================

class TestContractValidation:
    """Test status vs value_text contract rules"""

    def test_confirmed_requires_value_text(self, confirmed_amount_dto):
        """CONFIRMED explanation must have value_text"""
        builder = ExplanationBuilder()

        explanation = builder.build_insurer_explanation(
            insurer="삼성화재",
            coverage_name="암진단비",
            amount_dto=confirmed_amount_dto
        )

        assert explanation.status == "CONFIRMED"
        assert explanation.value_text == "3천만원"
        assert "3천만원" in explanation.explanation

    def test_unconfirmed_no_value_text(self, unconfirmed_amount_dto):
        """UNCONFIRMED explanation should not have value_text"""
        builder = ExplanationBuilder()

        explanation = builder.build_insurer_explanation(
            insurer="KB손해보험",
            coverage_name="암진단비",
            amount_dto=unconfirmed_amount_dto
        )

        assert explanation.status == "UNCONFIRMED"
        assert explanation.value_text is None
        assert "금액이 명시되어 있지 않습니다" in explanation.explanation

    def test_not_available_no_value_text(self, not_available_amount_dto):
        """NOT_AVAILABLE explanation should not have value_text"""
        builder = ExplanationBuilder()

        explanation = builder.build_insurer_explanation(
            insurer="현대해상",
            coverage_name="특수담보",
            amount_dto=not_available_amount_dto
        )

        assert explanation.status == "NOT_AVAILABLE"
        assert explanation.value_text is None
        assert "해당 담보가 존재하지 않습니다" in explanation.explanation

    def test_confirmed_contract_violation_raises(self):
        """CONFIRMED AmountDTO without value_text raises ValueError"""
        builder = ExplanationBuilder()

        # Create invalid AmountDTO (CONFIRMED without value_text)
        # NOTE: This violates AmountDTO contract, but we test handler resilience
        invalid_dto = AmountDTO(
            status="CONFIRMED",
            value_text=None,  # ❌ Contract violation
            source_doc_type="가입설계서",
            evidence=None
        )

        with pytest.raises(ValueError, match="Contract violation"):
            builder.build_insurer_explanation(
                insurer="삼성화재",
                coverage_name="암진단비",
                amount_dto=invalid_dto
            )


# ============================================================================
# Test Suite 4: Parallel Explanations (No Cross-Comparison)
# ============================================================================

class TestParallelExplanations:
    """Test parallel explanation generation (no cross-comparison)"""

    def test_two_confirmed_no_comparison(self, confirmed_amount_dto):
        """Two CONFIRMED insurers → no comparative words"""
        handler = ComparisonExplanationHandler()

        # Create two different CONFIRMED amounts
        samsung_dto = AmountDTO(
            status="CONFIRMED",
            value_text="3천만원",
            source_doc_type="가입설계서",
            evidence=None
        )

        kb_dto = AmountDTO(
            status="CONFIRMED",
            value_text="2천만원",
            source_doc_type="가입설계서",
            evidence=None
        )

        comparison = handler.generate_coverage_explanation(
            coverage_code="A4200_1",
            coverage_name="암진단비",
            insurer_amounts=[
                ("삼성화재", samsung_dto),
                ("KB손해보험", kb_dto)
            ]
        )

        # Validate no cross-comparison
        for explanation in comparison.comparison_explanation:
            # Check no forbidden comparative patterns (context-aware)
            from apps.api.policy.forbidden_language import validate_text
            try:
                validate_text(explanation.explanation)
            except ValueError:
                pytest.fail(f"Forbidden language detected in: {explanation.explanation}")

            # Check no cross-insurer reference
            if explanation.insurer == "삼성화재":
                assert "KB손해보험" not in explanation.explanation
            elif explanation.insurer == "KB손해보험":
                assert "삼성화재" not in explanation.explanation

    def test_mixed_status_no_comparison(
        self,
        confirmed_amount_dto,
        unconfirmed_amount_dto
    ):
        """CONFIRMED + UNCONFIRMED → no comparative language"""
        handler = ComparisonExplanationHandler()

        comparison = handler.generate_coverage_explanation(
            coverage_code="A4200_1",
            coverage_name="암진단비",
            insurer_amounts=[
                ("삼성화재", confirmed_amount_dto),
                ("KB손해보험", unconfirmed_amount_dto)
            ]
        )

        # Each explanation is independent
        samsung_exp = comparison.comparison_explanation[0]
        kb_exp = comparison.comparison_explanation[1]

        # Samsung explanation only references Samsung
        assert "삼성화재" in samsung_exp.explanation
        assert "KB손해보험" not in samsung_exp.explanation

        # KB explanation only references KB
        assert "KB손해보험" in kb_exp.explanation
        assert "삼성화재" not in kb_exp.explanation


# ============================================================================
# Test Suite 5: Order Preservation
# ============================================================================

class TestOrderPreservation:
    """Test that input order is preserved in output"""

    def test_order_preserved(self, confirmed_amount_dto, unconfirmed_amount_dto):
        """Input order is preserved in comparison explanation"""
        handler = ComparisonExplanationHandler()

        # Input order: 삼성 → KB → 현대
        insurer_amounts = [
            ("삼성화재", confirmed_amount_dto),
            ("KB손해보험", unconfirmed_amount_dto),
            ("현대해상", confirmed_amount_dto)
        ]

        comparison = handler.generate_coverage_explanation(
            coverage_code="A4200_1",
            coverage_name="암진단비",
            insurer_amounts=insurer_amounts
        )

        # Check order is preserved
        assert len(comparison.comparison_explanation) == 3
        assert comparison.comparison_explanation[0].insurer == "삼성화재"
        assert comparison.comparison_explanation[1].insurer == "KB손해보험"
        assert comparison.comparison_explanation[2].insurer == "현대해상"

    def test_no_sorting_by_amount(self, confirmed_amount_dto):
        """Explanations are NOT sorted by amount value"""
        handler = ComparisonExplanationHandler()

        # Input: 3천 → 5천 → 1천 (NOT sorted by amount)
        insurer_amounts = [
            ("삼성화재", AmountDTO(status="CONFIRMED", value_text="3천만원", evidence=None)),
            ("KB손해보험", AmountDTO(status="CONFIRMED", value_text="5천만원", evidence=None)),
            ("현대해상", AmountDTO(status="CONFIRMED", value_text="1천만원", evidence=None))
        ]

        comparison = handler.generate_coverage_explanation(
            coverage_code="A4200_1",
            coverage_name="암진단비",
            insurer_amounts=insurer_amounts
        )

        # Order should remain: 삼성(3천) → KB(5천) → 현대(1천)
        # NOT sorted as: 현대(1천) → 삼성(3천) → KB(5천)
        assert comparison.comparison_explanation[0].value_text == "3천만원"
        assert comparison.comparison_explanation[1].value_text == "5천만원"
        assert comparison.comparison_explanation[2].value_text == "1천만원"


# ============================================================================
# Test Suite 6: Audit Metadata Inclusion
# ============================================================================

class TestAuditMetadata:
    """Test audit metadata is included in responses"""

    def test_audit_metadata_in_coverage_explanation(
        self,
        confirmed_amount_dto,
        audit_metadata
    ):
        """Coverage explanation includes audit metadata"""
        handler = ComparisonExplanationHandler()

        comparison = handler.generate_coverage_explanation(
            coverage_code="A4200_1",
            coverage_name="암진단비",
            insurer_amounts=[("삼성화재", confirmed_amount_dto)],
            audit=audit_metadata
        )

        assert comparison.audit is not None
        assert str(comparison.audit.audit_run_id) == "f2e58b52-f22d-4d66-8850-df464954c9b8"
        assert comparison.audit.freeze_tag == "freeze/pre-10b2g2-20251229-024400"

    def test_audit_metadata_in_multi_coverage(
        self,
        confirmed_amount_dto,
        audit_metadata
    ):
        """Multi-coverage response includes global audit metadata"""
        handler = ComparisonExplanationHandler()

        coverage_data = [
            {
                "coverage_code": "A4200_1",
                "coverage_name": "암진단비",
                "insurer_amounts": [("삼성화재", confirmed_amount_dto)]
            }
        ]

        response = handler.generate_multi_coverage_explanation(
            coverage_data=coverage_data,
            audit=audit_metadata
        )

        assert response.audit is not None
        assert response.audit.audit_run_id == audit_metadata.audit_run_id


# ============================================================================
# Test Suite 7: Explanation Validation
# ============================================================================

class TestExplanationValidation:
    """Test ExplanationValidator enforcement"""

    def test_validate_confirmed_explanation(self):
        """CONFIRMED explanation passes validation"""
        explanation = InsurerExplanationDTO(
            insurer="삼성화재",
            status="CONFIRMED",
            explanation="삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다.",
            value_text="3천만원"
        )

        # Should pass
        assert ExplanationValidator.validate_explanation(explanation) is True

    def test_validate_unconfirmed_explanation(self):
        """UNCONFIRMED explanation passes validation"""
        explanation = InsurerExplanationDTO(
            insurer="KB손해보험",
            status="UNCONFIRMED",
            explanation="KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.",
            value_text=None
        )

        assert ExplanationValidator.validate_explanation(explanation) is True

    def test_validate_not_available_explanation(self):
        """NOT_AVAILABLE explanation passes validation"""
        explanation = InsurerExplanationDTO(
            insurer="현대해상",
            status="NOT_AVAILABLE",
            explanation="현대해상에는 해당 담보가 존재하지 않습니다.",
            value_text=None
        )

        assert ExplanationValidator.validate_explanation(explanation) is True

    def test_validate_confirmed_without_value_text_fails(self):
        """CONFIRMED explanation without value_text fails validation"""
        explanation = InsurerExplanationDTO(
            insurer="삼성화재",
            status="CONFIRMED",
            explanation="삼성화재의 암진단비는 가입설계서에 명시되어 있습니다.",
            value_text=None  # ❌ Missing
        )

        with pytest.raises(ValueError, match="CONFIRMED explanation without value_text"):
            ExplanationValidator.validate_explanation(explanation)

    def test_validate_unconfirmed_with_value_text_fails(self):
        """UNCONFIRMED explanation with value_text fails validation"""
        explanation = InsurerExplanationDTO(
            insurer="KB손해보험",
            status="UNCONFIRMED",
            explanation="KB손해보험의 암진단비는 가입설계서에 금액이 명시되어 있지 않습니다.",
            value_text="3천만원"  # ❌ Should not have
        )

        with pytest.raises(ValueError, match="UNCONFIRMED explanation with value_text"):
            ExplanationValidator.validate_explanation(explanation)

    def test_validate_cross_insurer_reference_fails(self):
        """Cross-insurer reference in explanation fails validation"""
        # Forbidden pattern "보다 높" should fail DTO creation
        with pytest.raises((ValueError, Exception)):  # Can be ValueError or ValidationError
            InsurerExplanationDTO(
                insurer="삼성화재",
                status="CONFIRMED",
                explanation="삼성화재의 암진단비는 3천만원으로 KB손해보험보다 높습니다.",
                value_text="3천만원"
            )


# ============================================================================
# Test Suite 8: Integration Test (Full Flow)
# ============================================================================

class TestIntegrationFlow:
    """Test full explanation generation flow"""

    def test_full_explanation_flow(
        self,
        confirmed_amount_dto,
        unconfirmed_amount_dto,
        not_available_amount_dto,
        audit_metadata
    ):
        """End-to-end test: AmountDTO → ExplanationResponseDTO"""
        handler = ComparisonExplanationHandler()

        # Multi-coverage, multi-insurer scenario
        coverage_data = [
            {
                "coverage_code": "A4200_1",
                "coverage_name": "암진단비",
                "insurer_amounts": [
                    ("삼성화재", confirmed_amount_dto),
                    ("KB손해보험", unconfirmed_amount_dto)
                ]
            },
            {
                "coverage_code": "A1300",
                "coverage_name": "상해사망",
                "insurer_amounts": [
                    ("삼성화재", confirmed_amount_dto),
                    ("현대해상", not_available_amount_dto)
                ]
            }
        ]

        response = handler.generate_multi_coverage_explanation(
            coverage_data=coverage_data,
            audit=audit_metadata
        )

        # Validate response structure
        assert len(response.coverages) == 2
        assert response.audit == audit_metadata

        # Validate first coverage (암진단비)
        cancer_coverage = response.coverages[0]
        assert cancer_coverage.coverage_code == "A4200_1"
        assert len(cancer_coverage.comparison_explanation) == 2

        samsung_exp = cancer_coverage.comparison_explanation[0]
        assert samsung_exp.insurer == "삼성화재"
        assert samsung_exp.status == "CONFIRMED"
        assert "3천만원" in samsung_exp.explanation

        kb_exp = cancer_coverage.comparison_explanation[1]
        assert kb_exp.insurer == "KB손해보험"
        assert kb_exp.status == "UNCONFIRMED"
        assert "금액이 명시되어 있지 않습니다" in kb_exp.explanation

        # Validate second coverage (상해사망)
        accident_coverage = response.coverages[1]
        assert accident_coverage.coverage_code == "A1300"
        assert len(accident_coverage.comparison_explanation) == 2

        hyundai_exp = accident_coverage.comparison_explanation[1]
        assert hyundai_exp.insurer == "현대해상"
        assert hyundai_exp.status == "NOT_AVAILABLE"
        assert "해당 담보가 존재하지 않습니다" in hyundai_exp.explanation

        # Validate all explanations
        ExplanationValidator.validate_response(response)
