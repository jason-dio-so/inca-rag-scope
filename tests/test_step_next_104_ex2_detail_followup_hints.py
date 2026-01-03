#!/usr/bin/env python3
"""
STEP NEXT-104: EX2_DETAIL Followup Hints Demo Flow Lock Contract Test

DESIGN:
Test that EX2_DETAIL bubble_markdown ALWAYS contains the fixed demo flow hints:
1. "메리츠는?" (insurer switch)
2. "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" (LIMIT_FIND)

RULES:
- ❌ NO dynamic text in hints (LOCKED for demo)
- ❌ NO insurer code exposure (samsung, meritz, etc.)
- ❌ NO coverage_code patterns (A4200_1, etc.)
- ✅ Always show exact 2 hints
- ✅ Hints must be copy-paste ready (no placeholders like {담보명})

SSOT: This is the contract test for STEP NEXT-104
"""

import pytest
import re

from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_card_samsung():
    """Sample card data for Samsung insurer"""
    return {
        "amount": "3000만원",
        "kpi_summary": {
            "limit_summary": "3,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "waiting_period": "90일",
            "exclusion_condition": "계약일 이전 발생 질병",
            "renewal_condition": "비갱신형"
        }
    }


@pytest.fixture
def sample_card_meritz():
    """Sample card data for Meritz insurer"""
    return {
        "amount": "2000만원",
        "kpi_summary": {
            "limit_summary": "2,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:meritz:A4200_1:01"]
        },
        "kpi_condition": {
            "renewal_condition": "비갱신형"
        }
    }


# ============================================================================
# Test Cases
# ============================================================================

def test_ex2_detail_has_followup_hints_section(sample_card_samsung):
    """
    Test that EX2_DETAIL bubble_markdown contains followup hints section
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Should have hints section header
    assert "🔎 **다음으로 이런 질문도 해볼 수 있어요**" in bubble_markdown


def test_ex2_detail_hint_1_meritz_switch(sample_card_samsung):
    """
    Test that first hint is ALWAYS "메리츠는?" (insurer switch to Meritz)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Should contain exact hint text
    assert "- 메리츠는?" in bubble_markdown

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # ✅ First hint should be "메리츠는?"
        lines = [line.strip() for line in hints_section.split("\n") if line.strip().startswith("- ")]
        assert len(lines) >= 1
        assert lines[0] == "- 메리츠는?"


def test_ex2_detail_hint_2_limit_find(sample_card_samsung):
    """
    Test that second hint is ALWAYS "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Should contain exact hint text
    assert "- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" in bubble_markdown

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # ✅ Second hint should be LIMIT_FIND pattern
        lines = [line.strip() for line in hints_section.split("\n") if line.strip().startswith("- ")]
        assert len(lines) >= 2
        assert lines[1] == "- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"


def test_ex2_detail_hints_are_fixed_not_dynamic(sample_card_meritz):
    """
    Test that hints are FIXED (not dependent on insurer/coverage_name)

    Even when insurer=meritz and coverage_name is different,
    hints should still be the same demo flow.
    """
    result = EX2DetailComposer.compose(
        insurer="meritz",
        coverage_code="B1100_1",
        card_data=sample_card_meritz,
        coverage_name="뇌출혈진단비"
    )

    bubble_markdown = result["bubble_markdown"]

    # ✅ Hints should be IDENTICAL regardless of insurer/coverage
    assert "- 메리츠는?" in bubble_markdown
    assert "- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" in bubble_markdown


def test_ex2_detail_hints_no_insurer_code(sample_card_samsung):
    """
    Test that hints section contains NO insurer codes (samsung, meritz, etc.)

    "메리츠는?" is OK (Korean display name),
    but "meritz는?" would be WRONG.
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # Remove refs (PD:, EV:)
        text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", hints_section)

        # ❌ Should NOT contain insurer codes as standalone words
        # "메리츠" is OK (Korean), "meritz" is NOT OK
        insurer_codes = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "db", "heungkuk"]
        for code in insurer_codes:
            # Use word boundary to avoid false positives
            pattern = rf"\b{code}\b(?![가-힣])"
            assert re.search(pattern, text_without_refs, re.IGNORECASE) is None, \
                f"Insurer code '{code}' found in hints section"


def test_ex2_detail_hints_no_coverage_code(sample_card_samsung):
    """
    Test that hints section contains NO coverage codes (A4200_1, etc.)

    "암직접입원비" is OK (Korean coverage name),
    but "A1100_1" would be WRONG.
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # Remove refs (PD:, EV:)
        text_without_refs = re.sub(r"(PD|EV):[a-z]+:[A-Z]\d{4}_\d+(:\d+)?", "", hints_section)

        # ❌ Should NOT contain bare coverage codes
        coverage_code_pattern = r"\b[A-Z]\d{4}_\d+\b"
        assert not re.search(coverage_code_pattern, text_without_refs), \
            "Coverage code pattern found in hints section"


def test_ex2_detail_hints_are_copy_paste_ready(sample_card_samsung):
    """
    Test that hints are copy-paste ready (no placeholders like {담보명})

    User should be able to copy "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
    directly without editing.
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # ❌ Should NOT contain placeholders
        assert "{" not in hints_section
        assert "}" not in hints_section
        assert "{{" not in hints_section
        assert "}}" not in hints_section


def test_ex2_detail_exactly_2_hints(sample_card_samsung):
    """
    Test that there are EXACTLY 2 hints (no more, no less)
    """
    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_samsung,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble_markdown = result["bubble_markdown"]

    # Extract hints section
    if "다음으로 이런 질문도" in bubble_markdown:
        hints_section = bubble_markdown.split("다음으로 이런 질문도")[-1]

        # Count bullet points (lines starting with "- ")
        lines = [line.strip() for line in hints_section.split("\n") if line.strip().startswith("- ")]

        # ✅ Should have EXACTLY 2 hints
        assert len(lines) == 2, f"Expected 2 hints, found {len(lines)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
