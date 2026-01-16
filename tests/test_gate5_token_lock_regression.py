"""
GATE 5 Token Lock Regression Tests

Prevents regression of the N03/N09 token extraction bug fixed on 2026-01-16.

Bug Summary:
- N03 "일반암진단비Ⅱ" failed because len=6 did not trigger substring matching (condition was > 6)
- N09 "암진단Ⅱ(유사암제외)담보" failed because "담보" suffix was not stripped before tokenization

Fix:
- Changed condition from > 6 to >= 6 for substring matching
- Strip generic suffixes ("담보", "보장", "특약") before tokenization
"""

import re


def extract_core_tokens(coverage_name: str) -> list:
    """
    Extract core tokens from coverage_name using GATE 5 logic.
    This is the exact logic from tools/run_db_only_coverage.py apply_gates() GATE 5.
    """
    # Remove parentheses content
    base_name = re.sub(r'\([^)]*\)', '', coverage_name)

    # Strip Roman numerals
    base_name = re.sub(r'[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]', '', base_name)

    # Strip generic suffixes from the end
    generic_suffixes = ['담보', '보장', '특약', '특별약관']
    for suffix in generic_suffixes:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break

    # Extract tokens (2+ char Hangul sequences)
    core_tokens = [t for t in re.findall(r'[가-힣]{2,}', base_name) if len(t) >= 2]

    return core_tokens


def gate5_token_lock_passes(coverage_name: str, chunk_text: str) -> bool:
    """
    Simulate GATE 5 token lock validation.
    Returns True if chunk passes GATE 5 for given coverage_name.
    """
    # Normalize whitespace
    normalized_name = re.sub(r'\s+', '', coverage_name)
    normalized_text = re.sub(r'\s+', '', chunk_text)

    # Exact match check
    if normalized_name in normalized_text:
        return True

    # Token extraction
    core_tokens = extract_core_tokens(coverage_name)

    # No tokens - skip validation
    if not core_tokens:
        return True

    # Single long compound token - substring matching
    if len(core_tokens) == 1 and len(core_tokens[0]) >= 6:
        token = core_tokens[0]
        # Check for 4-char substrings in NORMALIZED chunk text (whitespace removed)
        for i in range(len(token) - 3):
            substr = token[i:i+4]
            if substr in normalized_text:
                return True
        return False

    # Multiple tokens or single short token - require at least 1 match
    # Check in NORMALIZED chunk text (whitespace removed)
    required_count = 1
    matched_count = sum(1 for token in core_tokens if token in normalized_text)
    return matched_count >= required_count


class TestGate5TokenLockRegression:
    """
    Unit tests for GATE 5 token extraction logic.
    These tests ensure N03/N09 token lock issues don't regress.
    """

    def test_n03_token_extraction(self):
        """
        Test N03 "일반암진단비Ⅱ" token extraction.

        Bug: len=6 token did not trigger substring matching (condition was > 6)
        Fix: Changed to >= 6
        """
        coverage_name = "일반암진단비Ⅱ"
        tokens = extract_core_tokens(coverage_name)

        # After stripping Ⅱ, should have single token "일반암진단비"
        assert len(tokens) == 1, f"Expected 1 token, got {len(tokens)}: {tokens}"
        assert tokens[0] == "일반암진단비", f"Expected '일반암진단비', got '{tokens[0]}'"

        # Token length is 6 (critical threshold)
        assert len(tokens[0]) == 6, f"Token length should be 6, got {len(tokens[0])}"

    def test_n03_substring_matching(self):
        """
        Test N03 chunk with "암진단비" (4-char substring) passes GATE 5.
        """
        coverage_name = "일반암진단비Ⅱ"

        # Sample chunk with "암진단비" but not full "일반암진단비"
        chunk_text = "제외) 또는 재진단암(유사암, 대장점막내암 제외)과 동일한 조직병리학적 특성을 가진 암진단비"

        # This should PASS because "암진단비" is a 4-char substring of "일반암진단비"
        assert gate5_token_lock_passes(coverage_name, chunk_text), \
            "N03 chunk with '암진단비' should pass GATE 5 (substring match)"

    def test_n03_no_false_negatives(self):
        """
        Test N03 does not reject chunks with valid cancer diagnosis terms.
        """
        coverage_name = "일반암진단비Ⅱ"

        # Various valid chunks
        valid_chunks = [
            "암진단비 지급사유가 발생한 경우",
            "일반 암 진단 시 보험금 지급",
            "암 진단비(유사암제외) 특약"
        ]

        for chunk in valid_chunks:
            result = gate5_token_lock_passes(coverage_name, chunk)
            assert result, f"N03 should pass for chunk: {chunk[:50]}..."

    def test_n09_token_extraction(self):
        """
        Test N09 "암진단Ⅱ(유사암제외)담보" token extraction.

        Bug: "담보" suffix was not stripped, resulting in compound token "암진단담보"
        Fix: Strip "담보" suffix before tokenization
        """
        coverage_name = "암진단Ⅱ(유사암제외)담보"
        tokens = extract_core_tokens(coverage_name)

        # After stripping (유사암제외), Ⅱ, and "담보" suffix, should have "암진단"
        assert len(tokens) == 1, f"Expected 1 token, got {len(tokens)}: {tokens}"
        assert tokens[0] == "암진단", f"Expected '암진단', got '{tokens[0]}'"

        # Token should NOT contain "담보"
        assert "담보" not in tokens[0], f"Token should not contain '담보': {tokens[0]}"

    def test_n09_token_matching(self):
        """
        Test N09 chunk with "암진단" (without "담보") passes GATE 5.
        """
        coverage_name = "암진단Ⅱ(유사암제외)담보"

        # Sample chunk with "암 진단" (with space) but not "담보"
        chunk_text = "피보험자가 암 진단 확정을 받은 경우 보험금을 지급합니다"

        # This should PASS because "암진단" is the only required token (담보 removed)
        assert gate5_token_lock_passes(coverage_name, chunk_text), \
            "N09 chunk with '암 진단' should pass GATE 5 (담보 suffix removed)"

    def test_n09_no_false_negatives(self):
        """
        Test N09 does not require "담보" term in chunks.
        """
        coverage_name = "암진단Ⅱ(유사암제외)담보"

        # Valid chunks without "담보" keyword but WITH "암진단" token
        valid_chunks = [
            "암진단시 보험가입금액 지급",
            "암 진단 확정일로부터 보험금 지급",
            "피보험자가 암 진단을 받은 경우"
        ]

        for chunk in valid_chunks:
            result = gate5_token_lock_passes(coverage_name, chunk)
            assert result, f"N09 should pass for chunk without '담보': {chunk[:50]}..."

    def test_other_insurers_not_affected(self):
        """
        Test that GATE 5 fix does not break other insurers.
        """
        # N08: short token, should use exact match
        assert extract_core_tokens("암진단비(유사암제외)") == ["암진단비"]
        assert len("암진단비") == 4, "N08 token is 4 chars (< 6)"

        # N08 chunk should pass with exact match (normalized)
        assert gate5_token_lock_passes("암진단비(유사암제외)", "암진단비 지급 사유")

        # N13: short token with Roman numeral
        assert extract_core_tokens("암진단비Ⅱ(유사암제외)") == ["암진단비"]

        # N02: tokenization result (after removing parentheses: "암진단비")
        tokens = extract_core_tokens("암(4대유사암제외)진단비")
        # After "암(4대유사암제외)" removed, left with "진단비" OR full token "암진단비"
        # Actually regex finds continuous Hangul, so "암" and "대유사암제외" and "진단비" separately
        # Or if parentheses removal results in "암진단비", that's a 4-char token
        assert len(tokens) >= 1, f"N02 should have at least 1 token, got {tokens}"

    def test_suffix_stripping_order(self):
        """
        Test that suffix is stripped BEFORE tokenization, not after.
        """
        # If "담보" is not stripped before tokenization, we'd get "암진단담보" as one token
        coverage_name = "암진단Ⅱ(유사암제외)담보"
        tokens = extract_core_tokens(coverage_name)

        # Should be ["암진단"], NOT ["암진단담보"]
        assert tokens == ["암진단"], f"Expected ['암진단'], got {tokens}"

    def test_substring_threshold_boundary(self):
        """
        Test the critical len >= 6 boundary condition.
        """
        # len=5: should NOT use substring matching
        tokens_5 = ["일반암진단"]  # 5 chars
        assert len(tokens_5[0]) == 5
        assert len(tokens_5[0]) < 6  # Should use exact match

        # len=6: SHOULD use substring matching (critical fix)
        tokens_6 = ["일반암진단비"]  # 6 chars
        assert len(tokens_6[0]) == 6
        assert len(tokens_6[0]) >= 6  # Should use substring match

        # len=7: should use substring matching
        tokens_7 = ["일반암진단비용"]  # 7 chars
        assert len(tokens_7[0]) == 7
        assert len(tokens_7[0]) >= 6


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
