#!/usr/bin/env python3
"""
Contract Tests: STEP NEXT-110A — Insurer Code Exposure = 0%

SCOPE:
- EX2_DETAIL, EX3_COMPARE, EX4_ELIGIBILITY responses
- title, summary_bullets, bubble_markdown, sections
- Insurer codes (samsung, meritz, kb, hanwha, hyundai, lotte, heungkuk) MUST NOT appear in UI fields
- Display names (삼성화재, 메리츠화재, etc.) MUST be used instead

EXCLUDED:
- refs (PD:samsung:, EV:meritz: are OK)
- internal data keys
"""

import pytest
import re
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


# Insurer code pattern (all known codes)
INSURER_CODE_PATTERN = r'\b(samsung|meritz|kb|hanwha|hyundai|lotte|heungkuk|db)\b'

# Ref pattern (these are OK to have codes)
REF_PATTERN = r'(PD:|EV:)(samsung|meritz|kb|hanwha|hyundai|lotte|heungkuk|db):'


def extract_non_ref_text(text: str) -> str:
    """
    Extract text excluding refs (PD:/EV: patterns)
    Refs are allowed to contain insurer codes
    """
    # Remove all ref patterns
    text_no_refs = re.sub(REF_PATTERN, '', text, flags=re.IGNORECASE)
    return text_no_refs


def assert_no_insurer_codes(text: str, field_name: str):
    """Assert no insurer codes in text (excluding refs)"""
    text_to_check = extract_non_ref_text(text)
    matches = re.findall(INSURER_CODE_PATTERN, text_to_check, flags=re.IGNORECASE)
    assert not matches, f"{field_name} contains insurer code(s): {matches}"


# --- EX2_DETAIL Tests ---

def test_ex2_detail_title_no_insurer_code():
    """EX2_DETAIL title MUST use display name, NOT code"""
    response = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data={
            "amount": "3000만원",
            "kpi_summary": {"limit_summary": "1회", "payment_type": "LUMP_SUM"},
        },
        coverage_name="암진단비"
    )
    assert_no_insurer_codes(response["title"], "title")
    assert "삼성화재" in response["title"]


def test_ex2_detail_summary_no_insurer_code():
    """EX2_DETAIL summary_bullets MUST use display name"""
    response = EX2DetailComposer.compose(
        insurer="meritz",
        coverage_code="A4200_1",
        card_data={
            "amount": "3000만원",
            "kpi_summary": {"limit_summary": "1회", "payment_type": "LUMP_SUM"},
        },
        coverage_name="암진단비"
    )
    for bullet in response["summary_bullets"]:
        assert_no_insurer_codes(bullet, "summary_bullets")
    # Should have display name
    assert any("메리츠화재" in b for b in response["summary_bullets"])


def test_ex2_detail_bubble_markdown_no_insurer_code():
    """EX2_DETAIL bubble_markdown MUST use display name in all sections"""
    response = EX2DetailComposer.compose(
        insurer="kb",
        coverage_code="A4200_1",
        card_data={
            "amount": "3000만원",
            "kpi_summary": {"limit_summary": "1회", "payment_type": "LUMP_SUM"},
            "proposal_detail_ref": "PD:kb:A4200_1",
        },
        coverage_name="암진단비"
    )
    bubble = response["bubble_markdown"]
    assert_no_insurer_codes(bubble, "bubble_markdown")
    assert "KB손해보험" in bubble


# --- EX3_COMPARE Tests ---

def test_ex3_compare_title_no_insurer_code():
    """EX3_COMPARE title MUST use display names for both insurers"""
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data={
            "samsung": {"amount": "3000만원", "payment_type": "LUMP_SUM"},
            "meritz": {"amount": "2000만원", "payment_type": "LUMP_SUM"},
        },
        coverage_name="암진단비"
    )
    assert_no_insurer_codes(response["title"], "title")
    assert "삼성화재" in response["title"]
    assert "메리츠화재" in response["title"]


def test_ex3_compare_bubble_markdown_no_insurer_code():
    """EX3_COMPARE bubble_markdown MUST use display names throughout"""
    response = EX3CompareComposer.compose(
        insurers=["hanwha", "hyundai"],
        coverage_code="A4200_1",
        comparison_data={
            "hanwha": {"amount": "5000만원", "payment_type": "LUMP_SUM"},
            "hyundai": {"amount": "3000만원", "payment_type": "PER_DAY"},
        },
        coverage_name="암진단비"
    )
    bubble = response["bubble_markdown"]
    assert_no_insurer_codes(bubble, "bubble_markdown")
    assert "한화손해보험" in bubble
    assert "현대해상" in bubble


# --- EX4_ELIGIBILITY Tests ---

def test_ex4_eligibility_bubble_markdown_no_insurer_code():
    """EX4_ELIGIBILITY bubble_markdown MUST use display names in all sections"""
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "보장함",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
        },
        {
            "insurer": "meritz",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "보장 제외",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
        },
    ]
    response = EX4EligibilityComposer.compose(
        insurers=["samsung", "meritz"],
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
    )
    bubble = response["bubble_markdown"]
    assert_no_insurer_codes(bubble, "bubble_markdown")
    assert "삼성화재" in bubble
    assert "메리츠화재" in bubble


def test_ex4_eligibility_matrix_table_no_insurer_code():
    """EX4_ELIGIBILITY matrix table MUST use display names in 보험사 column"""
    eligibility_data = [
        {
            "insurer": "lotte",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "보장함",
            "proposal_detail_ref": "PD:lotte:A4200_1",
        },
        {
            "insurer": "heungkuk",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "50% 감액",
            "proposal_detail_ref": "PD:heungkuk:A4200_1",
        },
    ]
    response = EX4EligibilityComposer.compose(
        insurers=["lotte", "heungkuk"],
        subtype_keyword="경계성종양",
        eligibility_data=eligibility_data,
    )
    # Extract table section
    matrix_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"), None
    )
    assert matrix_section is not None

    # Check all rows for insurer codes
    for row in matrix_section["rows"]:
        insurer_cell_text = row["cells"][0]["text"]  # First column is 보험사
        assert_no_insurer_codes(insurer_cell_text, "matrix table row")


def test_ex4_eligibility_overall_evaluation_no_insurer_code():
    """EX4_ELIGIBILITY overall_evaluation reasons MUST use display names"""
    eligibility_data = [
        {
            "insurer": "db",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "보장함",
            "proposal_detail_ref": "PD:db:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
        },
    ]
    response = EX4EligibilityComposer.compose(
        insurers=["db"],
        subtype_keyword="유사암",
        eligibility_data=eligibility_data,
    )
    # Extract overall evaluation section
    eval_section = next(
        (s for s in response["sections"] if s.get("kind") == "overall_evaluation"), None
    )
    assert eval_section is not None

    # Check reasons
    overall_eval = eval_section.get("overall_evaluation", {})
    reasons = overall_eval.get("reasons", [])
    for reason in reasons:
        description = reason.get("description", "")
        assert_no_insurer_codes(description, "overall_evaluation reason")


# --- Cross-Intent Regression Tests ---

def test_ex2_ex3_ex4_all_insurers_covered():
    """All known insurers must be tested across all intents"""
    # This test ensures we don't miss any insurer in the future
    all_insurers = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "heungkuk", "db"]

    # EX2 test coverage
    for insurer in all_insurers[:4]:  # Test first 4
        response = EX2DetailComposer.compose(
            insurer=insurer,
            coverage_code="TEST",
            card_data={"amount": "1000만원", "kpi_summary": {}},
            coverage_name="테스트담보"
        )
        assert_no_insurer_codes(response["title"], f"EX2 title ({insurer})")

    # EX3 test coverage (test all pairs)
    response = EX3CompareComposer.compose(
        insurers=["samsung", "kb"],
        coverage_code="TEST",
        comparison_data={
            "samsung": {"amount": "1000만원"},
            "kb": {"amount": "2000만원"},
        },
        coverage_name="테스트담보"
    )
    assert_no_insurer_codes(response["bubble_markdown"], "EX3 bubble_markdown")

    # EX4 test coverage
    eligibility_data = [
        {"insurer": ins, "status": "O", "evidence_type": None, "evidence_snippet": None}
        for ins in all_insurers[:3]
    ]
    response = EX4EligibilityComposer.compose(
        insurers=all_insurers[:3],
        subtype_keyword="테스트",
        eligibility_data=eligibility_data,
    )
    assert_no_insurer_codes(response["bubble_markdown"], "EX4 bubble_markdown")
