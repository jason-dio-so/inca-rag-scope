#!/usr/bin/env python3
"""
Test EX3_COMPARE bubble_markdown enhancement (STEP NEXT-82)

Constitutional Rules:
- ❌ NO coverage_code exposure (e.g., A4200_1)
- ❌ NO raw_text in bubble
- ✅ MUST have 4 sections (핵심 요약, 한눈에 보는 결론, 세부 비교 포인트, 유의사항)
- ✅ Customer-facing language only
- ✅ Deterministic only (NO LLM)
"""

import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


def test_bubble_markdown_has_four_sections():
    """Verify bubble_markdown has exactly 4 required sections"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "exclusion_condition": "유사암 제외"
            }
        },
        "meritz": {
            "amount": "5000만원",
            "payment_type": "정액형",
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:meritz:A4200_1:01"]
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "exclusion_condition": "유사암 제외"
            }
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )

    bubble = response["bubble_markdown"]

    # Must have 4 sections
    assert "## 핵심 요약" in bubble
    assert "## 한눈에 보는 결론" in bubble
    assert "## 세부 비교 포인트" in bubble
    assert "## 유의사항" in bubble


def test_bubble_markdown_no_coverage_code():
    """Verify NO coverage_code exposure in bubble_markdown"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"

    comparison_data = {
        "samsung": {"amount": "3000만원", "payment_type": "정액형"},
        "meritz": {"amount": "5000만원", "payment_type": "정액형"}
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )

    bubble = response["bubble_markdown"]

    # NO coverage_code patterns (A4200_1, A1234_0, etc.)
    assert "A4200_1" not in bubble
    assert "A4200" not in bubble
    # Generic pattern check
    import re
    code_pattern = r"A\d{4}_\d"
    assert not re.search(code_pattern, bubble), "coverage_code detected in bubble_markdown"


def test_bubble_markdown_section1_summary():
    """Verify Section 1: 핵심 요약 contains required items"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"

    comparison_data = {
        "samsung": {"amount": "3000만원"},
        "meritz": {"amount": "5000만원"}
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )

    bubble = response["bubble_markdown"]

    # Extract Section 1
    section1_start = bubble.find("## 핵심 요약")
    section1_end = bubble.find("## 한눈에 보는 결론")
    section1 = bubble[section1_start:section1_end]

    # Must contain
    assert "선택한 보험사: samsung, meritz" in section1
    # STEP NEXT-93: Coverage name is normalized (space removed inside parentheses)
    assert "비교 대상 담보: 암진단비(유사암제외)" in section1
    assert "기준 문서: 가입설계서" in section1


def test_bubble_markdown_section2_conclusion():
    """Verify Section 2: 한눈에 보는 결론 summarizes correctly"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "kpi_summary": {"payment_type": "정액형"},
            "kpi_condition": {"waiting_period": "90일"}
        },
        "meritz": {
            "amount": "5000만원",
            "payment_type": "정액형",
            "kpi_summary": {"payment_type": "정액형"},
            "kpi_condition": {"waiting_period": "90일"}
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 세부 비교 포인트")
    section2 = bubble[section2_start:section2_end]

    # Amount should show difference
    assert "보장금액: 상이" in section2
    assert "samsung 3000만원" in section2
    assert "meritz 5000만원" in section2

    # Payment type should show same
    assert "지급유형: 정액형" in section2

    # Difference should show none (waiting period is same)
    assert "주요 차이: 없음" in section2


def test_bubble_markdown_section3_detail():
    """Verify Section 3: 세부 비교 포인트 lists insurer features"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "kpi_summary": {"limit_summary": "1회한 지급"}
        },
        "meritz": {
            "amount": "5000만원",
            "payment_type": "일당형",
            "kpi_summary": {"limit_summary": "연간 5회 한도"}
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]
    section3_start = bubble.find("## 세부 비교 포인트")
    section3_end = bubble.find("## 유의사항")
    section3 = bubble[section3_start:section3_end]

    # Must list both insurers
    assert "- samsung:" in section3
    assert "- meritz:" in section3

    # Should contain features
    assert "보장금액 3000만원" in section3 or "3000만원" in section3
    assert "보장금액 5000만원" in section3 or "5000만원" in section3


def test_bubble_markdown_section4_caution():
    """Verify Section 4: 유의사항 has required disclaimers"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {"amount": "3000만원"},
        "meritz": {"amount": "5000만원"}
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]
    section4_start = bubble.find("## 유의사항")
    section4 = bubble[section4_start:]

    # Must contain
    assert "실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다" in section4
    assert "아래 표에서 상세 비교 및 근거 문서를 확인하세요" in section4


def test_bubble_markdown_different_conditions():
    """Verify bubble correctly identifies condition differences"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "1년 50%"
            }
        },
        "meritz": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "2년 50%"
            }
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 세부 비교 포인트")
    section2 = bubble[section2_start:section2_end]

    # Should detect reduction_condition difference
    assert "주요 차이: 있음" in section2
    assert "감액조건" in section2


def test_bubble_markdown_unknown_payment_type():
    """Verify UNKNOWN payment_type displays as '표현 없음'"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "UNKNOWN"
        },
        "meritz": {
            "amount": "5000만원",
            "payment_type": "정액형"
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]

    # UNKNOWN should show as 표현 없음
    assert "표현 없음" in bubble
    assert "UNKNOWN" not in bubble


def test_bubble_markdown_no_llm_no_raw_text():
    """Verify bubble_markdown uses deterministic logic only (NO LLM, NO raw_text)"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {"amount": "3000만원"},
        "meritz": {"amount": "5000만원"}
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]

    # NO raw_text patterns
    assert "raw_text" not in bubble.lower()
    assert "benefit_description" not in bubble.lower()

    # NO LLM traces (heuristic check)
    assert "추정" not in bubble
    assert "판단" not in bubble
    assert "좋아 보임" not in bubble
    assert "합리적" not in bubble

    # Lineage should confirm deterministic
    assert response["lineage"]["deterministic"] is True
    assert response["lineage"]["llm_used"] is False


def test_bubble_markdown_fallback_when_no_kpi():
    """Verify bubble_markdown handles missing KPI gracefully"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"

    comparison_data = {
        "samsung": {"amount": "3000만원"},
        "meritz": {"amount": "5000만원"}
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data
    )

    bubble = response["bubble_markdown"]

    # Should still have 4 sections
    assert "## 핵심 요약" in bubble
    assert "## 한눈에 보는 결론" in bubble
    assert "## 세부 비교 포인트" in bubble
    assert "## 유의사항" in bubble

    # Should fall back to "가입설계서 기준 보장"
    assert "가입설계서 기준 보장" in bubble or "보장금액" in bubble
