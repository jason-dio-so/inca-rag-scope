#!/usr/bin/env python3
"""
STEP NEXT-124: CHECK-1 UX Verification Test

Purpose: Verify EX3_COMPARE bubble is LOCKED to structural interpretation format

DoD:
- ✅ Bubble is exactly 6 lines
- ✅ Contains structural comparison keywords
- ✅ NO forbidden phrases ("일부 보험사는...", "보장 기준 차이", "제공됩니다")
- ✅ Uses explicit insurer names
- ✅ User can understand structural difference immediately
"""
import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


def test_bubble_format_locked_to_6_lines():
    """
    STEP NEXT-124: Bubble MUST be exactly 6 lines

    No conditional variation based on data
    """
    # Arrange: Minimal comparison data
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": ["EV:meritz:A4200_1:01"]
        }
    }
    coverage_name = "암진단비"

    # Act
    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )

    # Assert: Exactly 6 lines
    bubble = response["bubble_markdown"]
    lines = bubble.split("\n")
    assert len(lines) == 6, f"Bubble MUST be exactly 6 lines, got {len(lines)}"


def test_bubble_contains_required_structural_keywords():
    """
    STEP NEXT-124: Bubble MUST contain structural interpretation keywords

    Required keywords:
    - "정해진 금액을 지급하는 구조"
    - "보험기간 중 지급 횟수 기준으로 보장이 정의"
    - "즉,"
    - "지급 금액이 명확한 정액 구조"
    - "지급 조건 해석이 중요한 한도 구조"
    """
    # Arrange
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": []
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": []
        }
    }

    # Act
    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name="암진단비"
    )

    bubble = response["bubble_markdown"]

    # Assert: Required keywords present
    required_keywords = [
        "정해진 금액을 지급하는 구조",
        "보험기간 중 지급 횟수 기준으로 보장이 정의",
        "즉,",
        "지급 금액이 명확한 정액 구조",
        "지급 조건 해석이 중요한 한도 구조"
    ]

    for keyword in required_keywords:
        assert keyword in bubble, f"Required keyword '{keyword}' not found in bubble"


def test_bubble_no_forbidden_phrases():
    """
    STEP NEXT-124: Bubble MUST NOT contain forbidden phrases

    Forbidden:
    - "일부 보험사는..."
    - "보장 기준 차이"
    - "제공됩니다" (standalone usage)
    """
    # Arrange
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": []
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": []
        }
    }

    # Act
    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name="암진단비"
    )

    bubble = response["bubble_markdown"]

    # Assert: Forbidden phrases NOT present
    forbidden_phrases = [
        "일부 보험사는",
        "보장 기준 차이",
        "제공됩니다"
    ]

    for phrase in forbidden_phrases:
        assert phrase not in bubble, f"Forbidden phrase '{phrase}' found in bubble (STEP NEXT-124 violation)"


def test_bubble_uses_explicit_insurer_names():
    """
    STEP NEXT-124: Bubble MUST use explicit insurer names (display names)

    Required:
    - Display names (삼성화재, 메리츠화재)
    - NOT insurer codes (samsung, meritz)
    """
    # Arrange
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": []
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": []
        }
    }

    # Act
    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name="암진단비"
    )

    bubble = response["bubble_markdown"]

    # Assert: Display names present, codes absent
    assert "삼성화재" in bubble, "Display name '삼성화재' must be in bubble"
    assert "메리츠화재" in bubble, "Display name '메리츠화재' must be in bubble"
    assert "samsung" not in bubble.lower(), "Insurer code 'samsung' must NOT be in bubble"
    assert "meritz" not in bubble.lower(), "Insurer code 'meritz' must NOT be in bubble"


def test_bubble_format_is_data_independent():
    """
    STEP NEXT-124: Bubble format MUST NOT vary based on comparison data

    Same format regardless of:
    - Amount values
    - Payment types
    - KPI data
    """
    # Arrange: Two different comparison scenarios
    scenarios = [
        # Scenario 1: Same amounts
        {
            "samsung": {"amount": "3000만원", "payment_type": "정액형"},
            "meritz": {"amount": "3000만원", "payment_type": "정액형"}
        },
        # Scenario 2: Different amounts
        {
            "samsung": {"amount": "명시 없음", "payment_type": "UNKNOWN"},
            "meritz": {"amount": "5000만원", "payment_type": "정액형"}
        }
    ]

    bubbles = []
    for comparison_data in scenarios:
        # Add required fields
        for insurer in comparison_data:
            comparison_data[insurer]["proposal_detail_ref"] = f"PD:{insurer}:A4200_1"
            comparison_data[insurer]["evidence_refs"] = []

        response = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data=comparison_data,
            coverage_name="암진단비"
        )
        bubbles.append(response["bubble_markdown"])

    # Assert: All bubbles have identical structure (6 lines, same keywords)
    # They differ only in insurer names, which are the same in both scenarios
    for bubble in bubbles:
        lines = bubble.split("\n")
        assert len(lines) == 6, "All bubbles must have 6 lines"
        assert "정해진 금액을 지급하는 구조" in bubble
        assert "지급 횟수 기준으로 보장이 정의" in bubble
        assert "즉," in bubble


def test_check1_dod_immediate_recognition():
    """
    STEP NEXT-124: CHECK-1 DoD - User can recognize structural difference immediately

    Verification:
    - Bubble contains both "정액 구조" and "한도 구조" labels
    - Structural comparison is explicit (insurer1는... insurer2는...)
    - NO need to read right panel to understand difference
    """
    # Arrange
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": []
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": []
        }
    }

    # Act
    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name="암진단비"
    )

    bubble = response["bubble_markdown"]

    # Assert: Immediate recognition criteria
    # 1. Both structural labels present
    assert "정액 구조" in bubble, "정액 구조 label must be present"
    assert "한도 구조" in bubble, "한도 구조 label must be present"

    # 2. Explicit comparison (insurer names + 는)
    assert "삼성화재는" in bubble or "메리츠화재는" in bubble, \
        "Explicit comparison pattern (insurer는...) must be present"

    # 3. Structural interpretation keywords
    assert "지급 금액이 명확한" in bubble, "Structural interpretation must be explicit"
    assert "지급 조건 해석이 중요한" in bubble, "Structural interpretation must be explicit"
