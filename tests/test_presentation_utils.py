#!/usr/bin/env python3
"""
Tests for Presentation Utils
STEP NEXT-17: Amount Display Unification & Type C Structure Communication
"""

import pytest
from apps.api.dto import AmountDTO, AmountStatus
from apps.api.presentation_utils import (
    format_amount_for_display,
    get_type_c_explanation_note,
    is_type_c_insurer,
    should_show_type_c_note,
    _unify_amount_format
)


class TestAmountFormatUnification:
    """Test unified amount format: 3,000만원"""

    def test_unify_cheon_to_comma_format(self):
        """3천만원 → 3,000만원"""
        assert _unify_amount_format("3천만원") == "3,000만원"
        assert _unify_amount_format("5천만원") == "5,000만원"

    def test_unify_baek_to_zero_format(self):
        """6백만원 → 600만원"""
        assert _unify_amount_format("6백만원") == "600만원"
        assert _unify_amount_format("8백만원") == "800만원"

    def test_add_comma_to_numeric_format(self):
        """3000만원 → 3,000만원"""
        assert _unify_amount_format("3000만원") == "3,000만원"
        assert _unify_amount_format("5000만원") == "5,000만원"

    def test_preserve_already_unified_format(self):
        """3,000만원 → 3,000만원 (no change)"""
        assert _unify_amount_format("3,000만원") == "3,000만원"
        assert _unify_amount_format("1,000만원") == "1,000만원"

    def test_preserve_eok_format(self):
        """1억원 → 1억원 (no change)"""
        assert _unify_amount_format("1억원") == "1억원"
        assert _unify_amount_format("2억원") == "2억원"


class TestTypeCInsurerDetection:
    """Test Type C insurer detection (Hanwha ONLY after STEP 17C correction)"""

    def test_type_c_korean_names(self):
        """Korean names should be detected - ONLY Hanwha after Type correction"""
        assert is_type_c_insurer("한화손해보험") is True
        # STEP 17C: hyundai/kb changed from C to A
        assert is_type_c_insurer("현대해상") is False
        assert is_type_c_insurer("KB손해보험") is False

    def test_type_c_english_codes(self):
        """English codes should be detected (case-insensitive) - ONLY Hanwha after Type correction"""
        assert is_type_c_insurer("hanwha") is True
        # STEP 17C: hyundai/kb changed from C to A
        assert is_type_c_insurer("hyundai") is False
        assert is_type_c_insurer("kb") is False
        assert is_type_c_insurer("HANWHA") is True

    def test_type_ab_insurers_not_detected(self):
        """Type A/B insurers should NOT be Type C"""
        assert is_type_c_insurer("삼성화재") is False
        assert is_type_c_insurer("samsung") is False
        assert is_type_c_insurer("메리츠화재") is False
        assert is_type_c_insurer("meritz") is False
        assert is_type_c_insurer("DB손해보험") is False


class TestFormatAmountForDisplay:
    """Test format_amount_for_display() main function"""

    def test_confirmed_type_ab_shows_unified_amount(self):
        """CONFIRMED + Type A/B → Unified amount format"""
        dto = AmountDTO(
            status="CONFIRMED",
            value_text="3천만원",
            evidence=None
        )
        result = format_amount_for_display(dto, "삼성화재")
        assert result == "3,000만원"

    def test_confirmed_type_c_shows_unified_amount(self):
        """CONFIRMED + Type C → Unified amount format (same as Type A/B)"""
        dto = AmountDTO(
            status="CONFIRMED",
            value_text="5천만원",
            evidence=None
        )
        result = format_amount_for_display(dto, "한화손해보험")
        assert result == "5,000만원"

    def test_unconfirmed_type_ab_shows_standard_text(self):
        """UNCONFIRMED + Type A/B → "금액 미표기" """
        dto = AmountDTO(
            status="UNCONFIRMED",
            value_text=None,
            evidence=None
        )
        result = format_amount_for_display(dto, "삼성화재")
        assert result == "금액 미표기"

    def test_unconfirmed_type_c_shows_structure_explanation(self):
        """UNCONFIRMED + Type C → "보험가입금액 기준" (CRITICAL) - ONLY Hanwha after STEP 17C"""
        dto = AmountDTO(
            status="UNCONFIRMED",
            value_text=None,
            evidence=None
        )

        # Test Type C insurers - ONLY Hanwha after STEP 17C correction
        assert format_amount_for_display(dto, "한화손해보험") == "보험가입금액 기준"
        assert format_amount_for_display(dto, "hanwha") == "보험가입금액 기준"

        # STEP 17C: hyundai/kb changed from C to A - should show standard "금액 미표기"
        assert format_amount_for_display(dto, "현대해상") == "금액 미표기"
        assert format_amount_for_display(dto, "KB손해보험") == "금액 미표기"
        assert format_amount_for_display(dto, "hyundai") == "금액 미표기"
        assert format_amount_for_display(dto, "kb") == "금액 미표기"

    def test_not_available_shows_fixed_text(self):
        """NOT_AVAILABLE → "해당 담보 없음" """
        dto = AmountDTO(
            status="NOT_AVAILABLE",
            value_text=None,
            evidence=None
        )
        result = format_amount_for_display(dto, "삼성화재")
        assert result == "해당 담보 없음"


class TestTypeCExplanationNote:
    """Test Type C explanation note generation"""

    def test_explanation_note_text(self):
        """Note should explain structure difference"""
        note = get_type_c_explanation_note()
        assert "보험가입금액" in note
        assert "일부 보험사" in note
        assert "담보별 금액" in note

    def test_should_show_note_with_type_c_insurers(self):
        """Note should show when Type C insurers present"""
        insurers = ["삼성화재", "한화손해보험", "메리츠화재"]
        assert should_show_type_c_note(insurers) is True

        insurers = ["samsung", "hanwha"]
        assert should_show_type_c_note(insurers) is True

    def test_should_not_show_note_without_type_c_insurers(self):
        """Note should NOT show when only Type A/B insurers"""
        insurers = ["삼성화재", "메리츠화재", "DB손해보험"]
        assert should_show_type_c_note(insurers) is False

        insurers = ["samsung", "meritz", "db"]
        assert should_show_type_c_note(insurers) is False


class TestNoAmountInference:
    """Verify NO amount inference for Type C (CRITICAL)"""

    def test_unconfirmed_type_c_never_shows_numeric_amount(self):
        """
        CRITICAL: Type C UNCONFIRMED should NEVER show numeric amounts

        Even if "보험가입금액: 5,000만원" exists in data,
        presentation layer should NOT show it
        """
        dto = AmountDTO(
            status="UNCONFIRMED",
            value_text=None,  # MUST be None for UNCONFIRMED
            evidence=None
        )

        result = format_amount_for_display(dto, "한화손해보험")

        # Verify NO numeric amount
        assert "5,000만원" not in result
        assert "만원" not in result
        assert "보험가입금액 기준" == result


class TestContractCompliance:
    """Verify compliance with API contract"""

    def test_confirmed_requires_value_text(self):
        """CONFIRMED status MUST have value_text"""
        dto = AmountDTO(
            status="CONFIRMED",
            value_text="3천만원",
            evidence=None
        )
        result = format_amount_for_display(dto, "삼성화재")
        assert result is not None
        assert result != "확인 불가"

    def test_confirmed_without_value_text_handled_gracefully(self):
        """CONFIRMED without value_text should handle gracefully"""
        dto = AmountDTO(
            status="CONFIRMED",
            value_text=None,  # Contract violation
            evidence=None
        )
        result = format_amount_for_display(dto, "삼성화재")
        assert result == "확인 불가"

    def test_unconfirmed_never_shows_value_text(self):
        """UNCONFIRMED should ignore value_text if present"""
        dto = AmountDTO(
            status="UNCONFIRMED",
            value_text="3천만원",  # Unexpected, but handle it
            evidence=None
        )

        # Type A/B
        result_ab = format_amount_for_display(dto, "삼성화재")
        assert result_ab == "금액 미표기"

        # Type C
        result_c = format_amount_for_display(dto, "한화손해보험")
        assert result_c == "보험가입금액 기준"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
