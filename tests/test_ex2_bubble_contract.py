#!/usr/bin/env python3
"""
Contract Tests for EX2_DETAIL Bubble Markdown

STEP NEXT-86: Validate EX2_DETAIL output contract

VALIDATION RULES:
1. ❌ NO coverage_code exposure (e.g., "A4200_1")
2. ❌ NO raw_text in bubble_markdown
3. ✅ 4-section bubble_markdown structure
4. ✅ refs use PD:/EV: prefix
5. ✅ "표현 없음" / "근거 없음" when missing data
"""

import re
import pytest
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer
from apps.api.response_composers.utils import sanitize_no_coverage_code


class TestEX2BubbleContract:
    """Contract tests for EX2_DETAIL bubble markdown"""

    def test_no_coverage_code_exposure_in_bubble(self):
        """
        STEP NEXT-86: coverage_code MUST NOT appear in bubble_markdown

        Pattern: A4200_1, B1100_2, etc.
        """
        # Mock card data
        card_data = {
            "amount": "3000만원",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "limit_summary": "3,000만원",
                "payment_type": "정액형",
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

        # Compose response
        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Pattern: Coverage code (e.g., A4200_1)
        # NOTE: refs like "EV:samsung:A4200_1:01" are allowed (refs only)
        # But raw "A4200_1" without "EV:" or "PD:" prefix is FORBIDDEN

        # Check for raw coverage_code exposure (NOT in refs)
        # Strategy: Find all A\d{4}_\d patterns, then check if they are in valid refs

        # Find all coverage code patterns
        all_coverage_codes = re.findall(r"[A-Z]\d{4}_\d+", bubble_markdown)

        # Filter out valid refs (PD:xxx:CODE or EV:xxx:CODE:idx)
        invalid_codes = []
        for code in all_coverage_codes:
            # Check if this code appears in a valid ref context
            pd_ref_pattern = rf"PD:[a-z]+:{code}"
            ev_ref_pattern = rf"EV:[a-z]+:{code}:\d+"

            if not (re.search(pd_ref_pattern, bubble_markdown) or
                    re.search(ev_ref_pattern, bubble_markdown)):
                # Code appears but not in valid ref
                invalid_codes.append(code)

        assert len(invalid_codes) == 0, (
            f"VIOLATION: coverage_code exposed in bubble_markdown (not in valid refs): {invalid_codes}\n"
            f"Bubble content:\n{bubble_markdown}"
        )

    def test_bubble_has_4_sections(self):
        """
        STEP NEXT-86: bubble_markdown MUST have 4 sections

        Sections:
        1. 핵심 요약
        2. 보장 요약
        3. 조건 요약
        4. 근거 자료
        """
        card_data = {
            "amount": "3000만원",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "limit_summary": "3,000만원",
                "payment_type": "정액형",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
            },
            "kpi_condition": {
                "reduction_condition": "1년 미만 50%",
                "waiting_period": "90일",
                "exclusion_condition": "계약일 이전 발생 질병",
                "renewal_condition": "비갱신형",
                "condition_evidence_refs": []
            }
        }

        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Check for section headers
        assert "## 핵심 요약" in bubble_markdown, "Missing section: 핵심 요약"
        assert "## 보장 요약" in bubble_markdown, "Missing section: 보장 요약"
        assert "## 조건 요약" in bubble_markdown, "Missing section: 조건 요약"
        assert "## 근거 자료" in bubble_markdown, "Missing section: 근거 자료"

    def test_refs_use_pd_ev_prefix(self):
        """
        STEP NEXT-86: All refs MUST use PD:/EV: prefix

        Valid: PD:samsung:A4200_1, EV:samsung:A4200_1:01
        Invalid: A4200_1 (bare code)
        """
        card_data = {
            "amount": "3000만원",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"],
            "kpi_summary": {
                "limit_summary": "3,000만원",
                "payment_type": "정액형",
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

        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Find all refs in markdown links: [근거 보기](REF)
        ref_pattern = r"\[근거 보기\]\(([^)]+)\)"
        refs = re.findall(ref_pattern, bubble_markdown)

        for ref in refs:
            assert ref.startswith("PD:") or ref.startswith("EV:"), (
                f"Invalid ref (must use PD:/EV: prefix): {ref}"
            )

    def test_표현_없음_when_missing_kpi_summary(self):
        """
        STEP NEXT-86: Use "표현 없음" when KPI Summary is missing

        NOT "Unknown" or other variants
        """
        card_data = {
            "amount": "표현 없음",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": [],
            "kpi_summary": {
                "limit_summary": None,  # Missing
                "payment_type": None,   # Missing
                "kpi_evidence_refs": []
            },
            "kpi_condition": {
                "reduction_condition": "근거 없음",
                "waiting_period": "근거 없음",
                "exclusion_condition": "근거 없음",
                "renewal_condition": "근거 없음",
                "condition_evidence_refs": []
            }
        }

        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Check for "표현 없음" in 보장 요약 section
        assert "보장한도**: 표현 없음" in bubble_markdown, "Missing '표현 없음' for limit_summary"
        assert "지급유형**: 표현 없음" in bubble_markdown, "Missing '표현 없음' for payment_type"

    def test_근거_없음_when_missing_kpi_condition(self):
        """
        STEP NEXT-86: Use "근거 없음" when KPI Condition is missing

        NOT "Unknown" or other variants
        """
        card_data = {
            "amount": "3000만원",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": [],
            "kpi_summary": {
                "limit_summary": "3,000만원",
                "payment_type": "정액형",
                "kpi_evidence_refs": []
            },
            "kpi_condition": {
                "reduction_condition": None,  # Missing
                "waiting_period": None,       # Missing
                "exclusion_condition": None,  # Missing
                "renewal_condition": None,    # Missing
                "condition_evidence_refs": []
            }
        }

        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Check for "근거 없음" in 조건 요약 section
        assert "감액**: 근거 없음" in bubble_markdown, "Missing '근거 없음' for reduction_condition"
        assert "대기기간**: 근거 없음" in bubble_markdown, "Missing '근거 없음' for waiting_period"
        assert "면책**: 근거 없음" in bubble_markdown, "Missing '근거 없음' for exclusion_condition"
        assert "갱신**: 근거 없음" in bubble_markdown, "Missing '근거 없음' for renewal_condition"

    def test_no_raw_text_in_bubble(self):
        """
        STEP NEXT-86: bubble_markdown MUST NOT contain raw text snippets

        Only refs are allowed (PD:/EV:)
        """
        card_data = {
            "amount": "3000만원",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "limit_summary": "3,000만원",
                "payment_type": "정액형",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
            },
            "kpi_condition": {
                "reduction_condition": "1년 미만 50%",
                "waiting_period": "90일",
                "exclusion_condition": "계약일 이전 발생 질병",
                "renewal_condition": "비갱신형",
                "condition_evidence_refs": []
            }
        }

        response = EX2DetailComposer.compose(
            insurer="samsung",
            coverage_code="A4200_1",
            card_data=card_data,
            coverage_name="암진단비(유사암 제외)"
        )

        bubble_markdown = response.get("bubble_markdown", "")

        # Raw text snippets are usually long (> 50 chars) and contain detailed clauses
        # Check for patterns like "제1조", "제2항", "다만", "단서" (common in raw text)
        raw_text_indicators = ["제1조", "제2항", "제3항", "다만,", "단서"]

        for indicator in raw_text_indicators:
            assert indicator not in bubble_markdown, (
                f"VIOLATION: Raw text indicator found in bubble_markdown: {indicator}\n"
                f"Bubble should only contain refs, not raw text snippets."
            )

    def test_sanitize_no_coverage_code_util(self):
        """
        Test sanitize_no_coverage_code utility function

        STEP NEXT-86: Ensure coverage codes are replaced with "해당 담보"
        """
        # Test cases
        test_cases = [
            ("A4200_1 비교", "해당 담보 비교"),
            ("삼성화재의 A4200_1를 설명", "삼성화재의 해당 담보를 설명"),
            ("B1100_2와 C3300_1 비교", "해당 담보와 해당 담보 비교"),
            ("정상 텍스트", "정상 텍스트"),  # No coverage code
        ]

        for input_text, expected_output in test_cases:
            result = sanitize_no_coverage_code(input_text)
            assert result == expected_output, (
                f"Sanitization failed:\n"
                f"Input: {input_text}\n"
                f"Expected: {expected_output}\n"
                f"Got: {result}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
