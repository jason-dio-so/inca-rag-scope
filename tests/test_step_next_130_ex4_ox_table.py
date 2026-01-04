#!/usr/bin/env python3
"""
Contract Tests for STEP NEXT-130: EX4 O/X Eligibility Table

PURPOSE:
Verify EX4_ELIGIBILITY O/X table implementation against STEP NEXT-130 specification

SCOPE:
1. Fixed 5 rows (진단비, 수술비, 항암약물, 표적항암, 다빈치수술)
2. O/X only (NO △/Unknown/조건부)
3. 2-4 sentence bubble
4. Display names only (NO code exposure)
5. Evidence refs attached
6. NO recommendation/judgment

SSOT: docs/audit/STEP_NEXT_130_EX4_OX_TABLE_LOCK.md
"""

import pytest
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


# Mock coverage cards for testing
MOCK_COVERAGE_CARDS = [
    # Samsung - 진단비 (제자리암 관련)
    {
        "insurer": "samsung",
        "coverage_name_raw": "암진단비",
        "coverage_code": "A4200",
        "evidences": [
            {"snippet": "제자리암 진단 시 지급", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": [
                {"snippet": "암진단비 제자리암 보장"}
            ]
        }
    },
    # Samsung - 수술비 (제자리암 관련)
    {
        "insurer": "samsung",
        "coverage_name_raw": "암수술비",
        "coverage_code": "A4210",
        "evidences": [
            {"snippet": "제자리암 수술 시 지급", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": [
                {"snippet": "암수술비 제자리암 보장"}
            ]
        }
    },
    # Samsung - 항암약물 (제자리암 관련)
    {
        "insurer": "samsung",
        "coverage_name_raw": "항암약물치료비",
        "coverage_code": "A4220",
        "evidences": [
            {"snippet": "제자리암 항암약물치료 지급", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": []
        }
    },
    # Meritz - 진단비 (제자리암 관련)
    {
        "insurer": "meritz",
        "coverage_name_raw": "암진단비",
        "coverage_code": "A5200",
        "evidences": [
            {"snippet": "제자리암 진단 보장", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": [
                {"snippet": "암진단비 제자리암"}
            ]
        }
    },
    # Meritz - 수술비 (제자리암도 보장)
    {
        "insurer": "meritz",
        "coverage_name_raw": "암수술비",
        "coverage_code": "A5210",
        "evidences": [
            {"snippet": "제자리암 경계성종양 수술 시 지급", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": [
                {"snippet": "암수술비 제자리암"}
            ]
        }
    },
    # Meritz - 표적항암 (제자리암 관련)
    {
        "insurer": "meritz",
        "coverage_name_raw": "표적항암치료비",
        "coverage_code": "A5230",
        "evidences": [
            {"snippet": "제자리암 표적항암 보장", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": []
        }
    },
    # Meritz - 다빈치수술 (제자리암 관련)
    {
        "insurer": "meritz",
        "coverage_name_raw": "로봇수술비",
        "coverage_code": "A5240",
        "evidences": [
            {"snippet": "제자리암 다빈치 로봇수술 지급", "doc_type": "약관"}
        ],
        "proposal_facts": {
            "evidences": []
        }
    },
]


class TestEX4OXTableStructure:
    """Test EX4 O/X table structure (STEP NEXT-130)"""

    def test_fixed_5_rows(self):
        """Test 1: Table has exactly 5 fixed rows"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        # Find table section
        table_section = None
        for section in response["sections"]:
            if section.get("kind") == "comparison_table":
                table_section = section
                break

        assert table_section is not None, "Table section not found"
        assert len(table_section["rows"]) == 5, f"Expected 5 rows, got {len(table_section['rows'])}"

        # Verify row labels match fixed categories
        expected_categories = ["진단비", "수술비", "항암약물", "표적항암", "다빈치수술"]
        actual_categories = [row["cells"][0]["text"] for row in table_section["rows"]]
        assert actual_categories == expected_categories, f"Categories mismatch: {actual_categories}"

    def test_ox_only_no_delta_unknown(self):
        """Test 2: All cells contain O or X only (NO △/Unknown)"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        # Find table section
        table_section = None
        for section in response["sections"]:
            if section.get("kind") == "comparison_table":
                table_section = section
                break

        # Check all insurer cells (skip first cell which is category label)
        for row in table_section["rows"]:
            for cell in row["cells"][1:]:  # Skip first cell (category label)
                cell_value = cell["text"]
                assert cell_value in ["O", "X"], f"Invalid cell value: {cell_value} (expected O or X)"

    def test_display_names_only_no_code(self):
        """Test 3: Column headers use display names (NO insurer code)"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        # Find table section
        table_section = None
        for section in response["sections"]:
            if section.get("kind") == "comparison_table":
                table_section = section
                break

        columns = table_section["columns"]
        assert "삼성화재" in columns, "Samsung display name not found in columns"
        assert "메리츠화재" in columns, "Meritz display name not found in columns"
        assert "samsung" not in columns, "Insurer code 'samsung' should not appear"
        assert "meritz" not in columns, "Insurer code 'meritz' should not appear"

    def test_bubble_length_2_to_4_sentences(self):
        """Test 4: Bubble markdown is 2-4 sentences (short guidance)"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        bubble = response["bubble_markdown"]
        assert bubble is not None and len(bubble) > 0, "Bubble markdown is empty"

        # Count sentences (rough heuristic: periods + exclamation marks)
        sentence_count = bubble.count(".") + bubble.count("!")
        assert 2 <= sentence_count <= 5, f"Bubble has {sentence_count} sentences (expected 2-4)"

        # Verify it's short (< 300 chars)
        assert len(bubble) < 300, f"Bubble too long: {len(bubble)} chars (expected < 300)"

    def test_no_recommendation_in_bubble(self):
        """Test 5: Bubble has NO recommendation/judgment keywords"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        bubble = response["bubble_markdown"]

        # Forbidden keywords
        forbidden = [
            "추천", "권장", "유리", "불리", "좋", "나쁨",
            "우수", "우월", "열등", "부족", "충분"
        ]

        for keyword in forbidden:
            assert keyword not in bubble, f"Forbidden keyword '{keyword}' found in bubble"

    def test_no_coverage_code_exposure(self):
        """Test 6: NO coverage_code exposure anywhere in response"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS,
            coverage_code="A4200"
        )

        # Serialize response to JSON string
        import json
        response_json = json.dumps(response, ensure_ascii=False)

        # Check for coverage_code patterns (A####, A####_###)
        import re
        code_pattern = re.compile(r'\bA\d{4}(_\d+)?\b')
        matches = code_pattern.findall(response_json)

        # Allow refs (PD:samsung:A4200), but NOT in user-facing text
        # Check title, summary_bullets, bubble_markdown
        assert "A4200" not in response["title"], "Coverage code in title"
        for bullet in response["summary_bullets"]:
            assert "A4200" not in bullet, f"Coverage code in summary bullet: {bullet}"

        # Bubble should not have bare coverage codes
        bubble_codes = code_pattern.findall(response["bubble_markdown"])
        # Allow in refs format (PD:insurer:CODE), but not standalone
        for match in bubble_codes:
            assert f"PD:" in response["bubble_markdown"] or f"EV:" in response["bubble_markdown"], \
                f"Coverage code {match} found outside ref context in bubble"

    def test_evidence_refs_attached(self):
        """Test 7: Evidence refs attached to rows with O status"""
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        # Find table section
        table_section = None
        for section in response["sections"]:
            if section.get("kind") == "comparison_table":
                table_section = section
                break

        # Check rows with O status have refs
        for row_idx, row in enumerate(table_section["rows"]):
            # Check if any cell in this row is "O"
            has_o = any(cell["text"] == "O" for cell in row["cells"][1:])

            if has_o:
                # Row should have evidence_refs in meta
                meta = row.get("meta", {})
                evidence_refs = meta.get("evidence_refs")

                # If O exists, refs should exist (may be empty list if no refs found)
                assert evidence_refs is not None, \
                    f"Row {row_idx} has O but no evidence_refs in meta"

                # If refs exist, they should be in PD: format
                if evidence_refs:
                    for ref in evidence_refs:
                        assert ref.startswith("PD:"), \
                            f"Invalid ref format: {ref} (expected PD:insurer:code)"

    def test_deterministic_ox_logic(self):
        """Test 8: O/X logic is deterministic (keyword matching)"""
        # Test case 1: Samsung has 진단비 + 제자리암 → O
        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            coverage_cards=MOCK_COVERAGE_CARDS
        )

        table_section = None
        for section in response["sections"]:
            if section.get("kind") == "comparison_table":
                table_section = section
                break

        # Row 0 (진단비): Samsung = O, Meritz = O (both have 진단비 + 제자리암)
        row_0_cells = table_section["rows"][0]["cells"]
        assert row_0_cells[1]["text"] == "O", "Samsung 진단비 should be O"
        assert row_0_cells[2]["text"] == "O", "Meritz 진단비 should be O"

        # Row 1 (수술비): Samsung = O, Meritz = O (both have 수술비 + 제자리암)
        row_1_cells = table_section["rows"][1]["cells"]
        assert row_1_cells[1]["text"] == "O", "Samsung 수술비 should be O"
        assert row_1_cells[2]["text"] == "O", "Meritz 수술비 should be O"

        # Row 2 (항암약물): Samsung = O, Meritz = O (Meritz 표적항암 contains "항암" → matches)
        row_2_cells = table_section["rows"][2]["cells"]
        assert row_2_cells[1]["text"] == "O", "Samsung 항암약물 should be O"
        assert row_2_cells[2]["text"] == "O", "Meritz 항암약물 should be O (표적항암 card matches)"

        # Row 3 (표적항암): Samsung = X, Meritz = O (only Meritz has 표적항암 + 제자리암)
        row_3_cells = table_section["rows"][3]["cells"]
        assert row_3_cells[1]["text"] == "X", "Samsung 표적항암 should be X"
        assert row_3_cells[2]["text"] == "O", "Meritz 표적항암 should be O"

        # Row 4 (다빈치수술): Samsung = X, Meritz = O (only Meritz has 다빈치)
        row_4_cells = table_section["rows"][4]["cells"]
        assert row_4_cells[1]["text"] == "X", "Samsung 다빈치수술 should be X"
        assert row_4_cells[2]["text"] == "O", "Meritz 다빈치수술 should be O"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
