#!/usr/bin/env python3
"""
STEP NEXT-103: EX2_DETAIL Display Name Contract Test

DESIGN:
Test that EX2_DETAIL responses NEVER expose insurer codes (samsung, meritz, etc.)
in title, summary_bullets, or bubble_markdown. Only display names allowed.

RULES:
- ❌ NO insurer code in title/summary/bubble_markdown (samsung, meritz, kb, etc.)
- ❌ NO coverage_code patterns (A4200_1, etc.)
- ✅ Display names ONLY (삼성화재, 메리츠화재, KB손해보험, etc.)
- ✅ Insurer codes OK in internal fields (not user-facing)

SSOT: docs/audit/STEP_NEXT_103_EX2_SWITCH_PAYLOAD_PROOF.md
"""

import re
import pytest

from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_card_samsung():
    """Sample card data for Samsung insurer"""
    return {
        "amount": "3000만원",
        "premium": "명시 없음",
        "period": "20년납/80세만기",
        "payment_type": "정액형",
        "proposal_detail_ref": "PD:samsung:A4200_1",
        "evidence_refs": ["EV:samsung:A4200_1:01"],
        "kpi_summary": {
            "limit_summary": "3,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "waiting_period": "90일",
            "exclusion_condition": "계약일 이전 발생 질병",
            "renewal_condition": "비갱신형",
            "condition_evidence_refs": ["EV:samsung:A4200_1:02"]
        }
    }


@pytest.fixture
def sample_card_meritz():
    """Sample card data for Meritz insurer"""
    return {
        "amount": "2000만원",
        "premium": "명시 없음",
        "period": "20년납/80세만기",
        "payment_type": "정액형",
        "proposal_detail_ref": "PD:meritz:A4200_1",
        "evidence_refs": ["EV:meritz:A4200_1:01"],
        "kpi_summary": {
            "limit_summary": "2,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:meritz:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "근거 없음",
            "waiting_period": "90일",
            "exclusion_condition": "근거 없음",
            "renewal_condition": "비갱신형",
            "condition_evidence_refs": ["EV:meritz:A4200_1:02"]
        }
    }


# ============================================================================
# Test Cases
# ============================================================================

def test_ex2_detail_no_insurer_code_in_title(sample_card_samsung):
    """
    Test that title uses display name (삼성화재), NOT code (samsung)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    title = result["title"]

    # ✅ Should contain display name
    assert "삼성화재" in title

    # ❌ Should NOT contain insurer code
    assert "samsung" not in title.lower()
    assert re.search(r"\bsamsung\b", title, re.IGNORECASE) is None


def test_ex2_detail_no_insurer_code_in_summary(sample_card_samsung):
    """
    Test that summary_bullets use display name (삼성화재), NOT code (samsung)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    summary_bullets = result["summary_bullets"]
    summary_text = "\n".join(summary_bullets)

    # ✅ Should contain display name
    assert "삼성화재" in summary_text

    # ❌ Should NOT contain insurer code
    assert "samsung" not in summary_text.lower()
    assert re.search(r"\bsamsung\b", summary_text, re.IGNORECASE) is None


def test_ex2_detail_no_insurer_code_in_bubble_markdown(sample_card_samsung):
    """
    Test that bubble_markdown uses display name (삼성화재), NOT code (samsung)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Should contain display name
    assert "삼성화재" in bubble_markdown

    # ❌ Should NOT contain insurer code (allow in refs PD:samsung:, EV:samsung:)
    # Extract non-ref text (remove refs)
    text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", bubble_markdown)

    # In non-ref text, should NOT have insurer codes
    assert "samsung" not in text_without_refs.lower()
    assert re.search(r"\bsamsung\b", text_without_refs, re.IGNORECASE) is None


def test_ex2_detail_meritz_display_name(sample_card_meritz):
    """
    Test that Meritz displays as "메리츠화재", NOT "meritz"
    """
    result = EX2DetailComposer.compose(
        insurer="meritz",
        coverage_code="A4200_1",
        card_data=sample_card_meritz,
        coverage_name="암직접입원비"
    )

    title = result["title"]
    bubble_markdown = result["bubble_markdown"]

    # ✅ Should contain display name
    assert "메리츠화재" in title
    assert "메리츠화재" in bubble_markdown

    # ❌ Should NOT contain insurer code
    text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", bubble_markdown)
    assert "meritz" not in text_without_refs.lower()
    assert re.search(r"\bmeritz\b", title, re.IGNORECASE) is None


def test_ex2_detail_no_coverage_code_in_user_facing_text(sample_card_samsung):
    """
    Test that coverage_code (A4200_1) is NEVER exposed in title/summary/bubble
    (except in refs like PD:samsung:A4200_1)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    title = result["title"]
    summary_bullets = "\n".join(result["summary_bullets"])
    bubble_markdown = result["bubble_markdown"]

    # Remove refs from bubble_markdown
    text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", bubble_markdown)

    # ❌ Should NOT contain bare coverage_code
    assert "A4200_1" not in title
    assert "A4200_1" not in summary_bullets
    assert "A4200_1" not in text_without_refs

    # Pattern check: NO bare coverage codes
    assert not re.search(r"\b[A-Z]\d{4}_\d+\b", title)
    assert not re.search(r"\b[A-Z]\d{4}_\d+\b", summary_bullets)
    assert not re.search(r"\b[A-Z]\d{4}_\d+\b", text_without_refs)


def test_ex2_detail_question_hints_use_display_name(sample_card_samsung):
    """
    Test that question continuity hints are FIXED for demo flow (STEP NEXT-104)

    STEP NEXT-104: Hints are now LOCKED to demo flow (not dynamic based on insurer)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Should contain FIXED demo flow hints (STEP NEXT-104)
    assert "- 메리츠는?" in bubble_markdown
    assert "- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" in bubble_markdown

    # ❌ Should NOT contain insurer code in hints
    # Extract hints section (after "다음으로 이런 질문도")
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]
        # Remove refs
        hints_text = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", hints_section)
        # "메리츠" is OK (Korean display name), but "meritz" is NOT OK
        assert "samsung" not in hints_text.lower()
        assert "meritz" not in hints_text.lower()  # Code exposure


def test_ex2_detail_all_insurers_display_names():
    """
    Test that ALL insurers use display names, not codes
    """
    test_cases = [
        ("samsung", "삼성화재"),
        ("meritz", "메리츠화재"),
        ("kb", "KB손해보험"),
        ("hanwha", "한화손해보험"),
        ("hyundai", "현대해상"),
        ("lotte", "롯데손해보험"),
        ("db", "DB손해보험"),
        ("heungkuk", "흥국화재"),
    ]

    card_data = {
        "amount": "1000만원",
        "kpi_summary": {"limit_summary": "1,000만원", "payment_type": "LUMP_SUM"},
        "kpi_condition": {"renewal_condition": "비갱신형"}
    }

    for insurer_code, expected_display in test_cases:
        result = EX2DetailComposer.compose(
            insurer=insurer_code,
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="테스트담보"
        )

        title = result["title"]
        bubble_markdown = result["bubble_markdown"]

        # ✅ Should contain display name
        assert expected_display in title, f"Expected {expected_display} in title for {insurer_code}"
        assert expected_display in bubble_markdown, f"Expected {expected_display} in bubble for {insurer_code}"

        # ❌ Should NOT contain insurer code (use word boundary to avoid false positives like "KB손해보험")
        text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", bubble_markdown)
        # Only check if insurer_code appears as standalone word (not part of display name like "KB손해보험")
        pattern = rf"\b{insurer_code}\b(?![가-힣])"  # Not followed by Korean (to exclude "kb손해보험")
        assert re.search(pattern, text_without_refs, re.IGNORECASE) is None, f"Insurer code {insurer_code} found as standalone word in bubble text"
        assert re.search(pattern, title, re.IGNORECASE) is None, f"Insurer code {insurer_code} found as standalone word in title"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
