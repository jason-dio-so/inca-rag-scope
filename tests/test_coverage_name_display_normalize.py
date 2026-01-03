#!/usr/bin/env python3
"""
STEP NEXT-93: Coverage Name Display Normalization Unit Tests

PURPOSE:
Verify that coverage names are consistently normalized for UI display

CONTRACT:
1. ✅ "암 진단비" → "암진단비" (space removal)
2. ✅ "  암   진단비  " → "암진단비" (trim + multiple spaces)
3. ✅ "뇌 출혈-진단비" → "뇌출혈진단비" (separator removal)
4. ✅ "A4200_1" → "" (coverage_code rejection)
5. ✅ "암진단비(유사암 제외)" → "암진단비(유사암제외)" (parentheses preserved, inner space removed)
6. ✅ display_coverage_name() always uses normalization
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.response_composers.utils import (
    normalize_coverage_name_for_display,
    display_coverage_name
)


class TestNormalizeCoverageNameForDisplay:
    """Test normalize_coverage_name_for_display function"""

    def test_basic_space_removal(self):
        """Test basic Korean space removal"""
        assert normalize_coverage_name_for_display("암 진단비") == "암진단비"
        assert normalize_coverage_name_for_display("뇌 출혈 진단비") == "뇌출혈진단비"
        assert normalize_coverage_name_for_display("급성 심근경색 진단비") == "급성심근경색진단비"

    def test_trim_and_multiple_spaces(self):
        """Test trimming and multiple space handling"""
        assert normalize_coverage_name_for_display("  암진단비  ") == "암진단비"
        assert normalize_coverage_name_for_display("  암   진단비  ") == "암진단비"
        assert normalize_coverage_name_for_display("\t암\t진단비\t") == "암진단비"

    def test_separator_removal(self):
        """Test separator removal/normalization"""
        assert normalize_coverage_name_for_display("암-진단비") == "암진단비"
        assert normalize_coverage_name_for_display("암_진단비") == "암진단비"
        assert normalize_coverage_name_for_display("암/진단비") == "암진단비"
        assert normalize_coverage_name_for_display("뇌 출혈-진단비") == "뇌출혈진단비"

    def test_coverage_code_rejection(self):
        """Test coverage_code pattern rejection"""
        assert normalize_coverage_name_for_display("A4200_1") == ""
        assert normalize_coverage_name_for_display("B1100_2") == ""
        assert normalize_coverage_name_for_display("C3000_10") == ""

    def test_parentheses_preservation(self):
        """Test that parentheses are preserved"""
        result = normalize_coverage_name_for_display("암진단비(유사암 제외)")
        assert "(" in result and ")" in result
        assert result == "암진단비(유사암제외)"

        result2 = normalize_coverage_name_for_display("뇌출혈진단비(뇌졸중 포함)")
        assert result2 == "뇌출혈진단비(뇌졸중포함)"

    def test_percentage_preservation(self):
        """Test that percentage signs are preserved"""
        result = normalize_coverage_name_for_display("80% 보장")
        assert "%" in result
        # % preserved, space between % and Korean may remain
        # (our normalization only removes spaces between Korean characters)
        assert result == "80% 보장"

    def test_empty_and_too_short(self):
        """Test empty string and too-short rejection"""
        assert normalize_coverage_name_for_display("") == ""
        assert normalize_coverage_name_for_display("  ") == ""
        assert normalize_coverage_name_for_display("a") == ""  # Too short

    def test_invalid_characters_removal(self):
        """Test that invalid characters are removed"""
        # English letters should be removed (except in coverage_code pattern)
        result = normalize_coverage_name_for_display("암진단비abc")
        assert "abc" not in result or result == ""

    def test_mixed_separators(self):
        """Test multiple types of separators"""
        assert normalize_coverage_name_for_display("암-진단 비") == "암진단비"
        assert normalize_coverage_name_for_display("암_진단-비") == "암진단비"


class TestDisplayCoverageName:
    """Test display_coverage_name function with normalization"""

    def test_basic_normalization_applied(self):
        """Test that display_coverage_name applies normalization"""
        result = display_coverage_name(
            coverage_name="암 진단비",
            coverage_code="A4200_1"
        )
        assert result == "암진단비"

    def test_no_spaces_in_output(self):
        """Test that output never has spaces between Korean"""
        test_cases = [
            "암 진단비",
            "뇌 출혈 진단비",
            "급성 심근경색 진단비",
            "  암   진단비  "
        ]

        for test_case in test_cases:
            result = display_coverage_name(
                coverage_name=test_case,
                coverage_code="A1000_1"
            )
            # Should not have space between Korean characters
            assert not any(result[i:i+3].count(" ") > 0 and
                          ord('가') <= ord(result[i]) <= ord('힣') and
                          ord('가') <= ord(result[i+2]) <= ord('힣')
                          for i in range(len(result)-2))

    def test_coverage_code_rejection(self):
        """Test that coverage_code is rejected"""
        result = display_coverage_name(
            coverage_name="A4200_1",
            coverage_code="A4200_1"
        )
        assert result == "해당 담보"

    def test_none_coverage_name_fallback(self):
        """Test fallback when coverage_name is None"""
        result = display_coverage_name(
            coverage_name=None,
            coverage_code="A4200_1"
        )
        assert result == "해당 담보"

    def test_empty_coverage_name_fallback(self):
        """Test fallback when coverage_name is empty"""
        result = display_coverage_name(
            coverage_name="",
            coverage_code="A4200_1"
        )
        assert result == "해당 담보"

    def test_normalized_with_parentheses(self):
        """Test normalization with parentheses"""
        result = display_coverage_name(
            coverage_name="암진단비(유사암 제외)",
            coverage_code="A1000_1"
        )
        assert "(" in result and ")" in result
        assert result == "암진단비(유사암제외)"

    def test_multiple_cases_consistency(self):
        """Test that same coverage (different spacing) produces same output"""
        coverage_code = "A1000_1"

        result1 = display_coverage_name(coverage_name="암진단비", coverage_code=coverage_code)
        result2 = display_coverage_name(coverage_name="암 진단비", coverage_code=coverage_code)
        result3 = display_coverage_name(coverage_name="  암   진단비  ", coverage_code=coverage_code)

        # All should produce the same normalized result
        assert result1 == result2 == result3 == "암진단비"


class TestRegressionNoCoverageCodeExposure:
    """Regression tests for coverage_code exposure prevention"""

    def test_coverage_code_never_returned(self):
        """Test that coverage_code is NEVER returned in display name"""
        test_cases = [
            ("A4200_1", "A4200_1"),
            ("B1100_2", "B1100_2"),
            ("C3000_10", "C3000_10"),
        ]

        for coverage_name, coverage_code in test_cases:
            result = display_coverage_name(
                coverage_name=coverage_name,
                coverage_code=coverage_code
            )
            # Result should be fallback, NOT the coverage_code
            assert result == "해당 담보"
            assert result != coverage_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
