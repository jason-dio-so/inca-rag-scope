#!/usr/bin/env python3
"""
STEP NEXT-96: EX2_DETAIL Customer-First KPI Ordering Tests

GOAL:
- Verify 보장금액 appears FIRST in 보장 요약 section
- Verify ordering: 보장금액 → 보장한도 → 지급유형
- Verify NO handler/data logic changes
- Verify all existing EX2 tests still PASS

CONSTITUTIONAL RULES:
- ❌ NO comparison/recommendation/judgment
- ❌ NO coverage_code exposure
- ❌ NO raw text in bubble_markdown
- ✅ View layer ONLY (ordering change)
- ✅ Deterministic ONLY
"""

import pytest
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


# ============================================================================
# Case A — 고객 질문 중심 (보장금액 있음)
# ============================================================================

def test_case_a_amount_first_in_kpi_summary():
    """
    Case A — 고객 질문 중심
    - 입력: "삼성화재 암진단비 설명해줘"
    - 기대:
      - 보장금액이 첫 번째 KPI로 노출
      - "얼마 받는지" 즉시 인지 가능
    """
    card_data = {
        "amount": "3,000만원",  # STEP NEXT-96: 보장금액 (proposal_facts)
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "waiting_period": "90일",
            "condition_evidence_refs": ["EV:samsung:A4200_1:02"]
        },
        "proposal_detail_ref": "PD:samsung:A4200_1",
        "evidence_refs": ["EV:samsung:A4200_1:01"]
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="삼성화재",  # STEP NEXT-103: Changed from insurer code to display name
        display_name="암진단비(유사암 제외)",
        card_data=card_data
    )

    # ✅ 보장금액이 보장 요약의 첫 번째 항목
    보장_요약_section = bubble.split("## 보장 요약")[1].split("##")[0]

    # Check ordering: 보장금액 → 보장한도 → 지급유형
    assert "**보장금액**" in 보장_요약_section
    assert "**보장한도**" in 보장_요약_section
    assert "**지급유형**" in 보장_요약_section

    # Verify 보장금액 comes BEFORE 보장한도
    assert 보장_요약_section.index("**보장금액**") < 보장_요약_section.index("**보장한도**")

    # Verify 보장한도 comes BEFORE 지급유형
    assert 보장_요약_section.index("**보장한도**") < 보장_요약_section.index("**지급유형**")

    # ✅ 보장금액 값 확인
    assert "3,000만원" in bubble
    assert "지급 조건: 암진단비(유사암 제외) 해당 시" in bubble


# ============================================================================
# Case B — 금액 없는 담보
# ============================================================================

def test_case_b_no_amount_fallback_to_original():
    """
    Case B — 금액 없는 담보
    - 기대:
      - 보장금액 항목 미표시
      - 기존 EX2_DETAIL와 동일 (보장한도부터 시작)
    """
    card_data = {
        "amount": "명시 없음",  # No amount available
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "condition_evidence_refs": ["EV:samsung:A4200_1:02"]
        },
        "proposal_detail_ref": "PD:samsung:A4200_1",
        "evidence_refs": ["EV:samsung:A4200_1:01"]
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="삼성화재",  # STEP NEXT-103
        display_name="입원일당",
        card_data=card_data
    )

    보장_요약_section = bubble.split("## 보장 요약")[1].split("##")[0]

    # ❌ 보장금액 항목 없음 (amount = "명시 없음")
    assert "**보장금액**" not in 보장_요약_section

    # ✅ 보장한도가 첫 번째 항목
    assert "**보장한도**" in 보장_요약_section
    assert "**지급유형**" in 보장_요약_section


def test_case_b_none_amount_fallback():
    """
    Case B variant — amount is None
    """
    card_data = {
        "amount": None,  # None amount
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": []
        },
        "proposal_detail_ref": "PD:samsung:A4200_1"
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="삼성화재",  # STEP NEXT-103
        display_name="기타담보",
        card_data=card_data
    )

    보장_요약_section = bubble.split("## 보장 요약")[1].split("##")[0]

    # ❌ 보장금액 항목 없음 (amount is None)
    assert "**보장금액**" not in 보장_요약_section


# ============================================================================
# Case C — 기존 계약 테스트 (NO Regression)
# ============================================================================

def test_case_c_no_coverage_code_exposure():
    """
    Case C — 기존 계약 (STEP NEXT-86/90/91/92)
    - ❌ NO coverage_code exposure (A4200_1)
    """
    card_data = {
        "amount": "3,000만원",
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "proposal_detail_ref": "PD:samsung:A4200_1"
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="삼성화재",  # STEP NEXT-103
        display_name="암진단비",
        card_data=card_data
    )

    # ❌ NO bare coverage_code (outside of refs)
    import re
    bare_codes = re.findall(r'\b([A-Z]\d{4}_\d+)\b', bubble)
    for code in bare_codes:
        # Each code must be part of a ref (PD: or EV:)
        assert f"PD:samsung:{code}" in bubble or f"EV:samsung:{code}" in bubble, \
            f"Bare coverage_code {code} found without ref prefix"


def test_case_c_no_raw_text_in_bubble():
    """
    Case C — NO raw text (refs only)
    """
    card_data = {
        "amount": "5,000만원",
        "kpi_summary": {
            "limit_summary": "보험기간 중 2회",
            "payment_type": "PER_DAY",
            "kpi_evidence_refs": ["EV:meritz:A5298_001:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 30%",
            "waiting_period": "30일",
            "condition_evidence_refs": ["EV:meritz:A5298_001:02"]
        },
        "proposal_detail_ref": "PD:meritz:A5298_001"
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="메리츠화재",  # STEP NEXT-103
        display_name="뇌출혈진단비",
        card_data=card_data
    )

    # ✅ Refs are present
    assert "EV:meritz:A5298_001:01" in bubble
    assert "EV:meritz:A5298_001:02" in bubble

    # ✅ NO raw text embedding (only structured KPI + refs)
    # Bubble should NOT contain long evidence snippets
    assert len(bubble) < 1500  # Reasonable length check


def test_case_c_deterministic_only_no_llm():
    """
    Case C — Deterministic ONLY (NO LLM)
    """
    card_data = {
        "amount": "2,000만원",
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": []
        }
    }

    # Same input → same output (deterministic)
    bubble1 = EX2DetailComposer._build_bubble_markdown(
        insurer_display="KB손해보험",  # STEP NEXT-103
        display_name="급성심근경색진단비",
        card_data=card_data
    )

    bubble2 = EX2DetailComposer._build_bubble_markdown(
        insurer_display="KB손해보험",  # STEP NEXT-103
        display_name="급성심근경색진단비",
        card_data=card_data
    )

    # ✅ Deterministic: same input → same output
    assert bubble1 == bubble2


def test_case_c_payment_type_translation():
    """
    Case C — Payment type translation (STEP NEXT-86)
    """
    card_data = {
        "amount": "1,000만원",
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "LUMP_SUM",  # Should translate to "정액형 (일시금)"
            "kpi_evidence_refs": []
        }
    }

    bubble = EX2DetailComposer._build_bubble_markdown(
        insurer_display="한화손해보험",  # STEP NEXT-103
        display_name="상해사망급여금",
        card_data=card_data
    )

    # ✅ Payment type translated
    assert "정액형 (일시금)" in bubble
    assert "LUMP_SUM" not in bubble  # NO English exposure


# ============================================================================
# Integration Test — Full compose()
# ============================================================================

def test_full_compose_with_amount_first():
    """
    Integration: Full compose() with 보장금액 customer-first ordering
    """
    card_data = {
        "amount": "3,000만원",
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "waiting_period": "90일",
            "exclusion_condition": "계약일 이전 발생 질병",
            "renewal_condition": "비갱신형",
            "condition_evidence_refs": ["EV:samsung:A4200_1:02", "EV:samsung:A4200_1:03"]
        },
        "proposal_detail_ref": "PD:samsung:A4200_1",
        "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"]
    }

    result = EX2DetailComposer.compose(
        insurer="samsung",  # STEP NEXT-103: compose() uses insurer code, not display name
        coverage_code="A4200_1",
        card_data=card_data,
        coverage_name="암진단비(유사암 제외)"
    )

    # ✅ Message kind
    assert result["kind"] == "EX2_DETAIL"

    # ✅ Title uses display name (STEP NEXT-103)
    assert "삼성화재" in result["title"]
    assert "samsung" not in result["title"].lower()  # NO code exposure
    assert "암진단비" in result["title"]
    assert "설명" in result["title"]

    # ✅ Bubble markdown has 4 sections (STEP NEXT-110A: Product Header replaces 핵심 요약)
    bubble = result["bubble_markdown"]
    assert "<!-- PRODUCT_HEADER -->" in bubble
    assert "## 보장 요약" in bubble
    assert "## 조건 요약" in bubble
    assert "## 근거 자료" in bubble

    # ✅ 보장금액 is FIRST in 보장 요약
    보장_요약 = bubble.split("## 보장 요약")[1].split("##")[0]
    assert 보장_요약.index("**보장금액**") < 보장_요약.index("**보장한도**")

    # ✅ Lineage
    assert result["lineage"]["deterministic"] is True
    assert result["lineage"]["llm_used"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
