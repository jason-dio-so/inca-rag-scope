#!/usr/bin/env python3
"""
STEP NEXT-128: EX3_COMPARE Bubble ↔ Table Consistency Contract Tests

SSOT: docs/audit/STEP_NEXT_128_EX3_BUBBLE_TABLE_CONSISTENCY_LOCK.md

Tests verify:
1. Bubble ALWAYS matches table structure (NO hardcoded assumptions)
2. Samsung (limit) vs Meritz (amount) → bubble correctly identifies limit vs amount
3. Reverse order (Meritz vs Samsung) → bubble adapts correctly
4. Same input → same bubble (reproducibility)
"""

import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


@pytest.fixture
def samsung_limit_meritz_amount_data():
    """
    Samsung: LIMIT structure (보험기간 중 1회)
    Meritz: AMOUNT structure (3천만원)
    """
    return {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "보험기간 중 1회",  # LIMIT
                "kpi_evidence_refs": []
            },
            "kpi_condition": None
        },
        "meritz": {
            "amount": "3천만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": ["EV:meritz:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": None,  # NO LIMIT (amount only)
                "kpi_evidence_refs": []
            },
            "kpi_condition": None
        }
    }


def test_ex3_bubble_samsung_limit_meritz_amount(samsung_limit_meritz_amount_data):
    """
    TEST 1 (CRITICAL): Samsung (limit) vs Meritz (amount) → bubble MUST say Samsung = limit

    BEFORE (BUG):
    - Table: Samsung = "보험기간 중 1회" (limit), Meritz = "3천만원" (amount)
    - Bubble: Samsung = "정액" (WRONG), Meritz = "한도" (WRONG)

    AFTER (FIXED):
    - Table: Samsung = limit, Meritz = amount
    - Bubble: Samsung = limit, Meritz = amount (MATCH)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    bubble = response.get("bubble_markdown", "")

    # Samsung MUST be described as LIMIT structure
    assert "삼성화재는 보험기간 중 지급 횟수/한도 기준" in bubble, (
        "Samsung must be described as LIMIT structure (보험기간 중 지급 횟수/한도 기준)"
    )

    # Meritz MUST be described as AMOUNT structure
    assert "메리츠화재는 진단 시 정해진 금액(보장금액) 기준" in bubble, (
        "Meritz must be described as AMOUNT structure (진단 시 정해진 금액 기준)"
    )

    # MUST NOT say Samsung = 정액 (WRONG)
    assert "삼성화재는 진단 시 정해진 금액" not in bubble or "메리츠화재는 보험기간 중" in bubble, (
        "Samsung must NOT be described as AMOUNT if table shows LIMIT"
    )


def test_ex3_bubble_reversed_order(samsung_limit_meritz_amount_data):
    """
    TEST 2: Reversed order (meritz, samsung) → bubble adapts correctly

    EXPECTED:
    - Table: Meritz = amount, Samsung = limit
    - Bubble: Meritz = amount FIRST, Samsung = limit SECOND
    """
    response = EX3CompareComposer.compose(
        insurers=["meritz", "samsung"],  # REVERSED
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    bubble = response.get("bubble_markdown", "")

    # Meritz (insurer1) = AMOUNT
    assert "메리츠화재는 진단 시 정해진 금액(보장금액) 기준" in bubble

    # Samsung (insurer2) = LIMIT
    assert "삼성화재는 보험기간 중 지급 횟수/한도 기준" in bubble


def test_ex3_bubble_always_6_lines(samsung_limit_meritz_amount_data):
    """
    TEST 3 (REGRESSION): Bubble MUST be 6 lines EXACTLY (STEP NEXT-126 format)

    EXPECTED:
    Line 1: {insurer}는 ... 기준으로 보장이 정의되고,
    Line 2: {insurer}는 ... 기준으로 보장이 정의됩니다.
    Line 3: (blank)
    Line 4: **즉,**
    Line 5: - {insurer}: ...
    Line 6: - {insurer}: ...
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    bubble = response.get("bubble_markdown", "")
    lines = bubble.split("\n")

    assert len(lines) == 6, f"Bubble must be EXACTLY 6 lines, got {len(lines)}"

    # Line 3 must be blank
    assert lines[2] == "", "Line 3 must be blank"

    # Line 4 must be "**즉,**"
    assert lines[3] == "**즉,**", "Line 4 must be '**즉,**'"


def test_ex3_bubble_no_ilbu_phrase(samsung_limit_meritz_amount_data):
    """
    TEST 4 (REGRESSION): NO "일부 보험사는..." (STEP NEXT-123 absolute lock)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    bubble = response.get("bubble_markdown", "")

    assert "일부 보험사" not in bubble, (
        "Bubble must NOT contain '일부 보험사' (STEP NEXT-123 absolute forbidden)"
    )


def test_ex3_bubble_table_consistency_samsung_first(samsung_limit_meritz_amount_data):
    """
    TEST 5 (CRITICAL): Bubble ↔ Table consistency (Samsung first)

    VERIFICATION:
    - Extract structure from table
    - Verify bubble matches table structure
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    # Extract table structure
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Find "핵심 보장 내용" row
    detail_row = next(
        (row for row in table_section["rows"]
         if row["cells"][0]["text"] == "핵심 보장 내용"),
        None
    )
    assert detail_row is not None

    samsung_cell = detail_row["cells"][1]["text"]
    meritz_cell = detail_row["cells"][2]["text"]

    # Determine table structure
    samsung_is_limit = "보험기간 중" in samsung_cell or "회" in samsung_cell
    meritz_is_amount = "만원" in meritz_cell or "원" in meritz_cell

    assert samsung_is_limit, f"Table shows Samsung as LIMIT, got: {samsung_cell}"
    assert meritz_is_amount, f"Table shows Meritz as AMOUNT, got: {meritz_cell}"

    # Verify bubble matches table
    bubble = response.get("bubble_markdown", "")

    if samsung_is_limit:
        assert "삼성화재는 보험기간 중 지급 횟수/한도 기준" in bubble or "삼성화재: 지급 조건·횟수(한도) 기준" in bubble
    if meritz_is_amount:
        assert "메리츠화재는 진단 시 정해진 금액(보장금액) 기준" in bubble or "메리츠화재: 지급 금액이 명확한 정액(보장금액) 기준" in bubble


def test_ex3_table_unchanged(samsung_limit_meritz_amount_data):
    """
    TEST 6 (REGRESSION): Table structure MUST remain unchanged (STEP NEXT-127)

    EXPECTED:
    - Samsung column shows "보험기간 중 1회"
    - Meritz column shows "3천만원"
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Find "핵심 보장 내용" row
    detail_row = next(
        (row for row in table_section["rows"]
         if row["cells"][0]["text"] == "핵심 보장 내용"),
        None
    )
    assert detail_row is not None

    # Samsung cell MUST show limit
    samsung_cell = detail_row["cells"][1]["text"]
    assert "보험기간 중 1회" in samsung_cell, f"Samsung cell must show limit, got: {samsung_cell}"

    # Meritz cell MUST show amount
    meritz_cell = detail_row["cells"][2]["text"]
    assert "3천만원" in meritz_cell, f"Meritz cell must show amount, got: {meritz_cell}"


def test_ex3_bubble_reproducibility(samsung_limit_meritz_amount_data):
    """
    TEST 7 (REGRESSION): Same input → same bubble (STEP NEXT-126 reproducibility)
    """
    response1 = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    response2 = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_limit_meritz_amount_data,
        coverage_name="암진단비"
    )

    assert response1["bubble_markdown"] == response2["bubble_markdown"], (
        "Same input must produce same bubble (reproducibility)"
    )
