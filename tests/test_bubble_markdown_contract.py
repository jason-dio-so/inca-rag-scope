#!/usr/bin/env python3
r"""
STEP NEXT-81B: bubble_markdown Contract Tests + Coverage Code Exposure Prevention

Constitutional Rules:
- EX3/EX4 responses MUST include bubble_markdown
- NO coverage_code exposure (e.g., A4200_1) ANYWHERE in user-facing text
- NO raw text (full약관 content)
- Deterministic only (NO LLM artifacts)

STEP NEXT-81B: Coverage Code Exposure Prevention (Constitutional):
- ❌ NEVER allow coverage_code (A\d{4}_\d) in user-facing text
- ✅ message.title, summary_bullets, sections[*].title, bubble_markdown MUST be code-free
- ✅ Coverage codes ONLY allowed in internal refs (proposal_detail_ref, evidence_refs)
"""

import pytest
import re
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


def extract_all_text_fields(response_dict: dict) -> list:
    """
    Extract ALL user-facing text fields from /chat response

    Returns:
        List of all text strings that users will see
    """
    text_fields = []

    # Message-level fields
    if "title" in response_dict:
        text_fields.append(response_dict["title"])

    if "summary_bullets" in response_dict:
        text_fields.extend(response_dict["summary_bullets"])

    if "bubble_markdown" in response_dict:
        text_fields.append(response_dict["bubble_markdown"])

    # Section-level fields
    if "sections" in response_dict:
        for section in response_dict["sections"]:
            if "title" in section and section["title"]:
                text_fields.append(section["title"])

            # Check group titles/bullets in common_notes
            if section.get("kind") == "common_notes":
                if "groups" in section and section["groups"]:
                    for group in section["groups"]:
                        text_fields.append(group["title"])
                        text_fields.extend(group["bullets"])
                if "bullets" in section:
                    text_fields.extend(section["bullets"])

            # Check table cells (should not have coverage_code in text)
            if section.get("kind") == "comparison_table":
                if "rows" in section:
                    for row in section["rows"]:
                        for cell in row.get("cells", []):
                            text_fields.append(cell.get("text", ""))

    return text_fields


class TestEX3BubbleMarkdownContract:
    """Contract tests for EX3_COMPARE bubble_markdown"""

    def test_ex3_bubble_markdown_exists(self):
        """bubble_markdown field MUST exist in EX3 response"""
        response = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data={
                "samsung": {
                    "amount": "3000만원",
                    "premium": "10만원",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:samsung:A4200_1",
                    "evidence_refs": ["EV:samsung:A4200_1:01"],
                    "kpi_summary": {
                        "payment_type": "LUMP_SUM",
                        "limit_summary": "보험기간 중 1회"
                    },
                    "kpi_condition": {
                        "waiting_period": "90일",
                        "reduction_condition": "1년 50%",
                        "exclusion_condition": "유사암 제외"
                    }
                },
                "meritz": {
                    "amount": "3천만원",
                    "premium": "10만원",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:meritz:A4200_1",
                    "evidence_refs": ["EV:meritz:A4200_1:01"],
                    "kpi_summary": {
                        "payment_type": "LUMP_SUM",
                        "limit_summary": "보험기간 중 1회"
                    },
                    "kpi_condition": {
                        "waiting_period": "90일",
                        "reduction_condition": "명시 없음",
                        "exclusion_condition": "유사암 제외"
                    }
                }
            },
            coverage_name="암진단비(유사암 제외)"
        )

        assert "bubble_markdown" in response, "EX3 response MUST have bubble_markdown"
        assert response["bubble_markdown"], "bubble_markdown MUST NOT be empty"
        assert isinstance(response["bubble_markdown"], str), "bubble_markdown MUST be string"

    def test_ex3_no_coverage_code_exposure_in_all_fields(self):
        """
        STEP NEXT-81B: CONSTITUTIONAL ENFORCEMENT
        NO coverage_code exposure in ANY user-facing text field

        Checks:
        - title
        - summary_bullets
        - bubble_markdown
        - sections[*].title
        - table cells
        """
        response = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data={
                "samsung": {
                    "amount": "3000만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:samsung:A4200_1",
                    "evidence_refs": []
                },
                "meritz": {
                    "amount": "3천만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:meritz:A4200_1",
                    "evidence_refs": []
                }
            },
            coverage_name="암진단비(유사암 제외)"
        )

        # Extract ALL text fields
        text_fields = extract_all_text_fields(response)

        # Forbidden pattern: A\d{4}_\d (coverage code)
        # Note: No word boundary (\b) as it doesn't work well with Korean text
        coverage_code_pattern = re.compile(r"[A-Z]\d{4}_\d+")

        violations = []
        for text in text_fields:
            if text and coverage_code_pattern.search(text):
                violations.append(text)

        # Assert NO violations (constitutional enforcement)
        assert len(violations) == 0, (
            f"Coverage code exposure detected in {len(violations)} text fields:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_ex3_no_coverage_code_when_coverage_name_missing(self):
        """
        STEP NEXT-81B: Fallback to "해당 담보" when coverage_name is None
        NEVER fallback to coverage_code
        """
        response = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data={
                "samsung": {
                    "amount": "3000만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:samsung:A4200_1",
                    "evidence_refs": []
                },
                "meritz": {
                    "amount": "2000만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:meritz:A4200_1",
                    "evidence_refs": []
                }
            },
            coverage_name=None  # Missing
        )

        # Extract all text fields
        text_fields = extract_all_text_fields(response)

        # Check for coverage_code pattern
        coverage_code_pattern = re.compile(r"[A-Z]\d{4}_\d+")

        violations = []
        for text in text_fields:
            if text and coverage_code_pattern.search(text):
                violations.append(text)

        assert len(violations) == 0, (
            f"Coverage code exposure detected even with coverage_name=None:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

        # Verify title uses fallback "해당 담보"
        assert "해당 담보" in response["title"], (
            f"Title should use fallback '해당 담보' when coverage_name is None, "
            f"got: {response['title']}"
        )

    def test_ex3_bubble_has_expected_sections(self):
        """bubble_markdown MUST have required sections"""
        response = EX3CompareComposer.compose(
            insurers=["samsung", "meritz"],
            coverage_code="A4200_1",
            comparison_data={
                "samsung": {
                    "amount": "3000만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:samsung:A4200_1",
                    "evidence_refs": []
                },
                "meritz": {
                    "amount": "3천만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "LUMP_SUM",
                    "proposal_detail_ref": "PD:meritz:A4200_1",
                    "evidence_refs": []
                }
            },
            coverage_name="암진단비(유사암 제외)"
        )

        bubble = response["bubble_markdown"]
        # Required sections
        assert "# samsung vs meritz" in bubble, "MUST have title section"
        assert "## 핵심 결론" in bubble, "MUST have core conclusion section"
        assert "## 주요 차이" in bubble, "MUST have differences section"
        assert "## 근거 확인" in bubble, "MUST have evidence guide section"
        assert "## 주의사항" in bubble, "MUST have caution section"


class TestEX4BubbleMarkdownContract:
    """Contract tests for EX4_ELIGIBILITY bubble_markdown"""

    def test_ex4_bubble_markdown_exists(self):
        """bubble_markdown field MUST exist in EX4 response"""
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장함",
                "evidence_ref": "EV:samsung:A4200_1:01"
            },
            {
                "insurer": "meritz",
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "EV:meritz:A4200_1:01"
            }
        ]

        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        assert "bubble_markdown" in response, "EX4 response MUST have bubble_markdown"
        assert response["bubble_markdown"], "bubble_markdown MUST NOT be empty"
        assert isinstance(response["bubble_markdown"], str), "bubble_markdown MUST be string"

    def test_ex4_bubble_has_expected_sections(self):
        """bubble_markdown MUST have required sections"""
        eligibility_data = [
            {
                "insurer": "samsung",
                "status": "O",
                "evidence_type": "정의",
                "evidence_snippet": "제자리암: 보장함",
                "evidence_ref": "EV:samsung:A4200_1:01"
            },
            {
                "insurer": "meritz",
                "status": "X",
                "evidence_type": "면책",
                "evidence_snippet": "제자리암: 면책",
                "evidence_ref": "EV:meritz:A4200_1:01"
            }
        ]

        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        bubble = response["bubble_markdown"]
        # Required sections
        assert "# 제자리암 보장 가능 여부 요약" in bubble, "MUST have title section"
        assert "## 종합 평가" in bubble, "MUST have evaluation section"
        assert "## 보험사별 분포" in bubble, "MUST have distribution section"
        assert "## 근거 확인" in bubble, "MUST have evidence guide section"
        assert "## 유의사항" in bubble, "MUST have caution section"

    def test_ex4_bubble_has_ox_distribution(self):
        """bubble_markdown MUST show O/X/△ distribution"""
        eligibility_data = [
            {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "...", "evidence_ref": "EV:samsung:A:01"},
            {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "...", "evidence_ref": "EV:meritz:A:01"},
            {"insurer": "db", "status": "△", "evidence_type": "감액", "evidence_snippet": "...", "evidence_ref": "EV:db:A:01"}
        ]

        response = EX4EligibilityComposer.compose(
            insurers=["samsung", "meritz", "db"],
            subtype_keyword="제자리암",
            eligibility_data=eligibility_data
        )

        bubble = response["bubble_markdown"]
        # Check distribution counts (use emoji markers for cross-platform compatibility)
        assert "1개 보험사" in bubble, "MUST show insurer counts"
        assert "✅" in bubble or "보장 가능" in bubble, "MUST show O status"
        assert "❌" in bubble or "면책" in bubble, "MUST show X status"
        assert "⚠️" in bubble or "감액" in bubble, "MUST show △ status"


class TestCoverageCodeUtilities:
    """STEP NEXT-81B: Test coverage code prevention utilities"""

    def test_display_coverage_name_normal(self):
        """display_coverage_name returns coverage_name when valid"""
        from apps.api.response_composers.utils import display_coverage_name

        result = display_coverage_name(
            coverage_name="암진단비(유사암 제외)",
            coverage_code="A4200_1"
        )
        assert result == "암진단비(유사암 제외)"

    def test_display_coverage_name_none(self):
        """display_coverage_name returns fallback when coverage_name is None"""
        from apps.api.response_composers.utils import display_coverage_name

        result = display_coverage_name(
            coverage_name=None,
            coverage_code="A4200_1"
        )
        assert result == "해당 담보"

    def test_display_coverage_name_rejects_code(self):
        """display_coverage_name rejects coverage_name that looks like coverage_code"""
        from apps.api.response_composers.utils import display_coverage_name

        # If coverage_name looks like coverage_code, reject it
        result = display_coverage_name(
            coverage_name="A4200_1",
            coverage_code="A4200_1"
        )
        assert result == "해당 담보"

    def test_sanitize_no_coverage_code(self):
        """sanitize_no_coverage_code removes all coverage_code patterns"""
        from apps.api.response_composers.utils import sanitize_no_coverage_code

        # Case 1: coverage_code at start
        text = "A4200_1 비교"
        result = sanitize_no_coverage_code(text)
        assert "A4200_1" not in result
        assert "해당 담보" in result

        # Case 2: coverage_code in middle
        text = "삼성화재와 메리츠화재의 A4200_1를 비교"
        result = sanitize_no_coverage_code(text)
        assert "A4200_1" not in result
        assert "해당 담보" in result

        # Case 3: no coverage_code
        text = "암진단비 비교"
        result = sanitize_no_coverage_code(text)
        assert result == text

        # Case 4: multiple coverage_codes
        text = "A4200_1과 B1100_2 비교"
        result = sanitize_no_coverage_code(text)
        assert "A4200_1" not in result
        assert "B1100_2" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
