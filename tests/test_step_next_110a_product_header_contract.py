#!/usr/bin/env python3
"""
STEP NEXT-110A Contract Tests — Product Header SSOT Lock

Tests that EX2_DETAIL (and future EX3/EX4) responses include:
- Insurer display name
- Coverage name
- Data source reference
- NO coverage_code exposure

SSOT: docs/ui/STEP_NEXT_110A_HEADER_SSOT_LOCK.md
"""

import pytest
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


def test_ex2_detail_has_product_header():
    """
    EX2_DETAIL bubble_markdown must include product header at top
    """
    # Arrange
    insurer = "samsung"
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암제외)"

    card_data = {
        "amount": "3000만원",
        "kpi_summary": {
            "limit_summary": "1회 한도",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "waiting_period": "90일",
            "reduction_condition": "1년 미만 50%"
        }
    }

    # Act
    result = EX2DetailComposer.compose(
        insurer=insurer,
        coverage_code=coverage_code,
        card_data=card_data,
        coverage_name=coverage_name
    )

    # Assert
    bubble = result["bubble_markdown"]

    # Product header must be at top
    assert bubble.startswith("**[삼성화재]**"), "Header must start with insurer display name"
    assert "**암진단비(유사암제외)**" in bubble, "Header must include coverage name"
    assert "_기준: 가입설계서_" in bubble, "Header must include data source"
    assert "---" in bubble, "Header must have separator (---)"

    # Header must come BEFORE sections
    header_end = bubble.index("---")
    assert header_end < bubble.index("## 보장 요약"), "Header must come before sections"


def test_ex2_detail_no_coverage_code_in_header():
    """
    Product header must NOT expose coverage_code
    """
    # Arrange
    insurer = "meritz"
    coverage_code = "A4200_1"  # This should NOT appear in output
    coverage_name = "뇌출혈진단비"

    card_data = {
        "amount": "2000만원",
        "kpi_summary": {
            "limit_summary": "1회 한도",
            "payment_type": "lump_sum"
        }
    }

    # Act
    result = EX2DetailComposer.compose(
        insurer=insurer,
        coverage_code=coverage_code,
        card_data=card_data,
        coverage_name=coverage_name
    )

    # Assert
    bubble = result["bubble_markdown"]
    header_section = bubble.split("---")[0]  # Get header only

    # coverage_code pattern must NOT appear in header
    import re
    coverage_code_pattern = r"[A-Z][0-9]{4}_[0-9]+"
    assert not re.search(coverage_code_pattern, header_section), \
        f"Coverage code pattern must NOT appear in header. Found in: {header_section}"


def test_ex2_detail_header_uses_display_names():
    """
    Product header must use display names (NOT codes)
    """
    # Arrange
    insurer = "kb"
    coverage_code = "A1234_5"
    coverage_name = "급성심근경색진단비"

    card_data = {
        "kpi_summary": {
            "limit_summary": "1회",
            "payment_type": "LUMP_SUM"
        }
    }

    # Act
    result = EX2DetailComposer.compose(
        insurer=insurer,
        coverage_code=coverage_code,
        card_data=card_data,
        coverage_name=coverage_name
    )

    # Assert
    bubble = result["bubble_markdown"]
    header = bubble.split("---")[0]

    # Must use display names
    assert "**[KB손해보험]**" in header, "Must use insurer display name"
    assert "**급성심근경색진단비**" in header, "Must use coverage display name"

    # Must NOT use codes
    assert "kb" not in header.lower() or "[KB" in header, "Insurer code should only appear as part of display name"
    assert "A1234_5" not in header, "Coverage code must NOT appear"


def test_ex2_detail_header_structure_locked():
    """
    Product header structure must be locked (order and format)

    Structure:
    1. **[보험사]**
    2. **담보명**
    3. _기준: 가입설계서_
    4. ---
    """
    # Arrange
    insurer = "hanwha"
    coverage_code = "TEST_1"
    coverage_name = "테스트담보"

    card_data = {
        "kpi_summary": {
            "limit_summary": "unlimited"
        }
    }

    # Act
    result = EX2DetailComposer.compose(
        insurer=insurer,
        coverage_code=coverage_code,
        card_data=card_data,
        coverage_name=coverage_name
    )

    # Assert
    bubble = result["bubble_markdown"]
    lines = bubble.split("\n")

    # Line 1: **[보험사]**
    assert lines[0].startswith("**["), "Line 1 must be **[insurer]**"
    assert lines[0].endswith("]**"), "Line 1 must end with ]**"

    # Line 2: **담보명**
    assert lines[1].startswith("**"), "Line 2 must be **coverage_name**"
    assert lines[1].endswith("**"), "Line 2 must end with **"

    # Line 3: _기준: ..._
    assert lines[2].startswith("_기준:"), "Line 3 must be _기준: source_"
    assert lines[2].endswith("_"), "Line 3 must end with _"

    # Line 4: empty
    assert lines[3] == "", "Line 4 must be empty"

    # Line 5: ---
    assert lines[4] == "---", "Line 5 must be horizontal rule (---)"


def test_ex2_detail_regression_sections_preserved():
    """
    Adding product header must NOT break existing sections
    """
    # Arrange
    insurer = "samsung"
    coverage_code = "A4200_1"
    coverage_name = "암진단비"

    card_data = {
        "amount": "5000만원",
        "kpi_summary": {
            "limit_summary": "1회",
            "payment_type": "정액형",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "waiting_period": "90일",
            "reduction_condition": "1년 미만 50%",
            "exclusion_condition": "계약일 이전 발생",
            "renewal_condition": "비갱신형"
        }
    }

    # Act
    result = EX2DetailComposer.compose(
        insurer=insurer,
        coverage_code=coverage_code,
        card_data=card_data,
        coverage_name=coverage_name
    )

    # Assert
    bubble = result["bubble_markdown"]

    # All sections must still exist
    assert "## 보장 요약" in bubble, "보장 요약 section must exist"
    assert "## 조건 요약" in bubble, "조건 요약 section must exist"
    assert "## 근거 자료" in bubble, "근거 자료 section must exist"

    # Sections must come AFTER header
    header_end = bubble.index("---")
    assert header_end < bubble.index("## 보장 요약"), "Sections must come after header"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
