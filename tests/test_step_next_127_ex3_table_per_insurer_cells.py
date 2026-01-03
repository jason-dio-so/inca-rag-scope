#!/usr/bin/env python3
"""
STEP NEXT-127: EX3_COMPARE Table Per-Insurer Cells + Meta Contract Tests

SSOT: docs/audit/STEP_NEXT_127_EX3_TABLE_PER_INSURER_LOCK.md

Tests verify:
1. Per-insurer cells: limit vs amount shown correctly per insurer
2. Per-insurer meta: Each cell has its own insurer's refs (NOT shared)
3. Structural basis: "보장 정의 기준" reflects limit vs amount difference
4. NO samsung refs in meritz cells (cross-contamination = 0%)
"""

import pytest
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


@pytest.fixture
def samsung_meritz_comparison_data():
    """
    Fixture: Samsung (limit-based) vs Meritz (amount-based) comparison

    Samsung: Has limit_summary ("보험기간 중 1회"), amount = "3000만원"
    Meritz: Has amount ("3천만원"), NO limit_summary
    """
    return {
        "samsung": {
            "amount": "3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "보험기간 중 1회",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:kpi"]
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "condition_evidence_refs": ["EV:samsung:A4200_1:cond"]
            }
        },
        "meritz": {
            "amount": "3천만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": ["EV:meritz:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": None,  # NO limit
                "kpi_evidence_refs": []
            },
            "kpi_condition": None
        }
    }


def test_ex3_table_samsung_limit_shown_in_cells(samsung_meritz_comparison_data):
    """
    TEST 1: Samsung's limit ("보험기간 중 1회") MUST appear in cells.text

    EVIDENCE (current bug):
    - Samsung limit exists in meta.kpi_summary.limit_summary
    - BUT NOT in cells.text (only amount "3000만원" shown)

    EXPECTED (STEP NEXT-127):
    - cells.text contains "보험기간 중 1회" (핵심 보장 내용 row)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None, "comparison_table section must exist"

    # Extract all cell texts (flatten)
    all_cell_texts = []
    for row in table_section["rows"]:
        for cell in row["cells"]:
            if cell.get("text"):
                all_cell_texts.append(cell["text"])

    # CRITICAL: Samsung's limit MUST appear in cells
    assert "보험기간 중 1회" in all_cell_texts, (
        "Samsung limit '보험기간 중 1회' must appear in cells.text, not just in meta"
    )


def test_ex3_table_meritz_amount_shown_in_cells(samsung_meritz_comparison_data):
    """
    TEST 2: Meritz's amount ("3천만원") MUST appear in cells.text

    EXPECTED (STEP NEXT-127):
    - cells.text contains "3천만원" (핵심 보장 내용 row)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Extract all cell texts
    all_cell_texts = []
    for row in table_section["rows"]:
        for cell in row["cells"]:
            if cell.get("text"):
                all_cell_texts.append(cell["text"])

    # Meritz amount MUST appear
    assert "3천만원" in all_cell_texts, (
        "Meritz amount '3천만원' must appear in cells.text"
    )


def test_ex3_table_structural_basis_different_per_insurer(samsung_meritz_comparison_data):
    """
    TEST 3: "보장 정의 기준" row MUST show DIFFERENT basis per insurer

    EVIDENCE (current bug):
    - Both samsung and meritz show "정액 지급 방식" (SAME)

    EXPECTED (STEP NEXT-127):
    - Samsung: "지급 한도/횟수 기준" (limit exists)
    - Meritz: "보장금액(정액) 기준" (amount only)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Find "보장 정의 기준" row
    basis_row = next(
        (row for row in table_section["rows"]
         if row["cells"][0]["text"] == "보장 정의 기준"),
        None
    )
    assert basis_row is not None, "보장 정의 기준 row must exist"

    # Extract basis texts (skip label cell)
    samsung_basis = basis_row["cells"][1]["text"]
    meritz_basis = basis_row["cells"][2]["text"]

    # Samsung: limit-based
    assert samsung_basis == "지급 한도/횟수 기준", (
        f"Samsung basis must be '지급 한도/횟수 기준', got '{samsung_basis}'"
    )

    # Meritz: amount-based
    assert meritz_basis == "보장금액(정액) 기준", (
        f"Meritz basis must be '보장금액(정액) 기준', got '{meritz_basis}'"
    )

    # MUST be different
    assert samsung_basis != meritz_basis, (
        "Samsung and Meritz must have DIFFERENT structural basis"
    )


def test_ex3_table_no_samsung_refs_in_meritz_cells(samsung_meritz_comparison_data):
    """
    TEST 4 (CRITICAL): NO samsung refs in meritz cells (cross-contamination = 0%)

    EVIDENCE (current bug):
    - ALL row.meta contains PD:samsung:*, EV:samsung:* (even for meritz column)

    EXPECTED (STEP NEXT-127):
    - Meritz cells MUST have PD:meritz:*, EV:meritz:* ONLY
    - Samsung refs in meritz cells = ABSOLUTE ZERO
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Check all rows
    for row_idx, row in enumerate(table_section["rows"]):
        # Check meritz cell (column index 2)
        if len(row["cells"]) >= 3:
            meritz_cell = row["cells"][2]
            meritz_meta = meritz_cell.get("meta")

            if meritz_meta:
                # Extract all refs from meritz cell meta
                all_refs = []

                if meritz_meta.get("proposal_detail_ref"):
                    all_refs.append(meritz_meta["proposal_detail_ref"])

                if meritz_meta.get("evidence_refs"):
                    all_refs.extend(meritz_meta["evidence_refs"])

                if meritz_meta.get("kpi_summary", {}).get("kpi_evidence_refs"):
                    all_refs.extend(meritz_meta["kpi_summary"]["kpi_evidence_refs"])

                if meritz_meta.get("kpi_condition", {}).get("condition_evidence_refs"):
                    all_refs.extend(meritz_meta["kpi_condition"]["condition_evidence_refs"])

                # CRITICAL: NO samsung refs allowed
                for ref in all_refs:
                    assert not ref.startswith("PD:samsung:"), (
                        f"Row {row_idx} meritz cell contains samsung proposal_detail_ref: {ref}"
                    )
                    assert not ref.startswith("EV:samsung:"), (
                        f"Row {row_idx} meritz cell contains samsung evidence_ref: {ref}"
                    )


def test_ex3_table_meritz_refs_present(samsung_meritz_comparison_data):
    """
    TEST 5: Meritz cells MUST have meritz refs (not empty)

    EXPECTED (STEP NEXT-127):
    - Meritz cells contain PD:meritz:*, EV:meritz:*
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Check at least one row has meritz refs
    found_meritz_ref = False
    for row in table_section["rows"]:
        if len(row["cells"]) >= 3:
            meritz_cell = row["cells"][2]
            meritz_meta = meritz_cell.get("meta")

            if meritz_meta:
                # Check proposal_detail_ref
                pd_ref = meritz_meta.get("proposal_detail_ref")
                if pd_ref and pd_ref.startswith("PD:meritz:"):
                    found_meritz_ref = True
                    break

                # Check evidence_refs
                ev_refs = meritz_meta.get("evidence_refs", [])
                if any(ref.startswith("EV:meritz:") for ref in ev_refs):
                    found_meritz_ref = True
                    break

    assert found_meritz_ref, (
        "Meritz cells must contain at least one meritz ref (PD:meritz:* or EV:meritz:*)"
    )


def test_ex3_table_samsung_refs_present(samsung_meritz_comparison_data):
    """
    TEST 6: Samsung cells MUST have samsung refs (not empty)

    EXPECTED (STEP NEXT-127):
    - Samsung cells contain PD:samsung:*, EV:samsung:*
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Find comparison_table section
    table_section = next(
        (s for s in response["sections"] if s.get("kind") == "comparison_table"),
        None
    )
    assert table_section is not None

    # Check at least one row has samsung refs
    found_samsung_ref = False
    for row in table_section["rows"]:
        if len(row["cells"]) >= 2:
            samsung_cell = row["cells"][1]
            samsung_meta = samsung_cell.get("meta")

            if samsung_meta:
                # Check proposal_detail_ref
                pd_ref = samsung_meta.get("proposal_detail_ref")
                if pd_ref and pd_ref.startswith("PD:samsung:"):
                    found_samsung_ref = True
                    break

                # Check evidence_refs
                ev_refs = samsung_meta.get("evidence_refs", [])
                if any(ref.startswith("EV:samsung:") for ref in ev_refs):
                    found_samsung_ref = True
                    break

    assert found_samsung_ref, (
        "Samsung cells must contain at least one samsung ref (PD:samsung:* or EV:samsung:*)"
    )


def test_ex3_bubble_matches_table(samsung_meritz_comparison_data):
    """
    TEST 7 (REGRESSION): STEP NEXT-128 bubble MUST match table structure

    EXPECTED:
    - bubble_markdown uses fixed 6-line format (STEP NEXT-126 format preserved)
    - bubble content MATCHES table structure (STEP NEXT-128 fix)
    - Samsung = LIMIT, Meritz = AMOUNT (based on table data)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    bubble = response.get("bubble_markdown", "")

    # STEP NEXT-128: Bubble MUST match table structure
    # Samsung has limit → described as LIMIT structure
    # Meritz has amount only → described as AMOUNT structure
    assert "삼성화재는 보험기간 중 지급 횟수/한도 기준" in bubble or "삼성화재: 지급 조건·횟수(한도) 기준" in bubble
    assert "메리츠화재는 진단 시 정해진 금액(보장금액) 기준" in bubble or "메리츠화재: 지급 금액이 명확한 정액(보장금액) 기준" in bubble

    # NO "일부 보험사는..." (STEP NEXT-123 absolute lock)
    assert "일부 보험사" not in bubble

    # STEP NEXT-126: 6 lines format preserved
    lines = bubble.split("\n")
    assert len(lines) == 6, f"Bubble must be 6 lines, got {len(lines)}"


def test_ex3_no_coverage_code_exposure(samsung_meritz_comparison_data):
    """
    TEST 8 (REGRESSION): NO coverage_code exposure (A4200_1)

    EXPECTED:
    - Coverage code NEVER appears in user-facing text
    - Refs (PD:/EV:) are OK (not user-facing)
    """
    response = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=samsung_meritz_comparison_data,
        coverage_name="암진단비"
    )

    # Check title
    assert "A4200" not in response["title"], "Coverage code in title"

    # Check bubble_markdown
    assert "A4200" not in response.get("bubble_markdown", ""), "Coverage code in bubble"

    # Check summary_bullets
    for bullet in response.get("summary_bullets", []):
        assert "A4200" not in bullet, f"Coverage code in bullet: {bullet}"

    # Check section titles
    for section in response.get("sections", []):
        title = section.get("title", "")
        assert "A4200" not in title, f"Coverage code in section title: {title}"
