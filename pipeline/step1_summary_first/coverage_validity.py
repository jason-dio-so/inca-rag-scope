#!/usr/bin/env python3
"""
STEP NEXT-45-C-β-3: Coverage Validity Filter (Deterministic)

Purpose: Distinguish "coverage" from "clause/condition" to prevent baseline over-extraction
from polluting parity calculations.

Rules:
1. Length >= 2 characters (filter single-char noise)
2. Reject if starts with clause keywords: ~시, 경우, 조건, 보장개시일, etc.
3. Reject if contains sentence-ending patterns: ...된 경우, ...시, ...합니다
4. Allow short but valid coverage names: 질병사망, 화상진단비, etc.
"""

import re
from typing import List


# Clause keywords (leading or sentence-form)
CLAUSE_KEYWORDS = [
    "경우",
    "조건",
    "보장개시일",
    "진단확정",
    "지급",
    "면책",
    "미지급",
    "보험금",
    "알림",
    "유의사항",
    "안내",
    "주의",
    "계약일",
    "개시일",
    "이후",
]

# Sentence-ending patterns (indicates clause, not coverage)
SENTENCE_PATTERNS = [
    r"된\s*경우$",
    r"으로\s*경우$",
    r"시$",
    r"합니다$",
    r"입니다$",
    r"됩니다$",
    r"받습니다$",
    r"해당$",
    r"이상$",
    r"미만$",
]


def is_valid_coverage_name(text: str) -> bool:
    """
    Determine if a text is a valid coverage name (not a clause/condition).

    Args:
        text: Coverage name text

    Returns:
        True if valid coverage, False if clause/condition
    """
    if not text or not isinstance(text, str):
        return False

    # Normalize whitespace
    text = text.strip()

    # Rule 1: Length >= 2
    if len(text) < 2:
        return False

    # Rule 2: Leading clause keywords
    # Check if text starts with clause keyword (within first 10 chars)
    text_lower = text.lower()
    for keyword in CLAUSE_KEYWORDS:
        # Leading position (within first 10 chars)
        if text_lower[:10].find(keyword) != -1:
            return False

    # Rule 3: Sentence-ending patterns
    for pattern in SENTENCE_PATTERNS:
        if re.search(pattern, text):
            return False

    # Rule 4: Specific clause patterns (full-text match)
    # These are common clause formats that should be rejected
    clause_full_patterns = [
        r"^\d+%?이상",  # "80%이상", "일반상해80%이상후유장해시"
        r"이상후유장해시$",  # Specific clause format
        r"^암보장개시일",  # Policy start date clause
        r"으로\s+진단확정",  # Diagnosis confirmation clause
    ]

    for pattern in clause_full_patterns:
        if re.search(pattern, text):
            return False

    # If none of the rejection rules matched, it's a valid coverage
    return True


def filter_valid_coverages(coverage_names: List[str]) -> List[str]:
    """
    Filter a list of coverage names to include only valid coverages.

    Args:
        coverage_names: List of coverage name texts

    Returns:
        List of valid coverage names
    """
    return [name for name in coverage_names if is_valid_coverage_name(name)]


def get_validity_report(coverage_names: List[str]) -> dict:
    """
    Generate a validity report for a list of coverage names.

    Args:
        coverage_names: List of coverage name texts

    Returns:
        Dict with:
            - total: total count
            - valid: valid coverage count
            - invalid: invalid (clause) count
            - invalid_names: list of invalid coverage names
    """
    valid = []
    invalid = []

    for name in coverage_names:
        if is_valid_coverage_name(name):
            valid.append(name)
        else:
            invalid.append(name)

    return {
        "total": len(coverage_names),
        "valid": len(valid),
        "invalid": len(invalid),
        "invalid_names": invalid,
    }


if __name__ == "__main__":
    # Test with KB baseline examples
    test_cases = [
        # Valid coverages (should return True)
        ("질병사망", True),
        ("화상진단비", True),
        ("암진단비(유사암제외)", True),
        ("일반상해사망(기본)", True),
        ("뇌혈관질환진단비", True),
        ("10대고액치료비암진단비", True),

        # Invalid clauses (should return False)
        ("일반상해80%이상후유장해시", False),
        ("질병80%이상후유장해시", False),
        ("암보장개시일(계약일로부터 그날을 포함하여 90일이 지난날의 다음날) 이후에", False),
        ("뇌졸중으로 진단확정된 경우", False),
        ("급성심근경색증으로 진단확정된 경우", False),
        ("말기폐질환으로 진단확정된 경우", False),
        ("말기간경화로 진단확정된 경우", False),
        ("말기신부전증으로 진단확정된 경우", False),
    ]

    print("Coverage Validity Filter Test:\n")
    print(f"{'Coverage Name':<60} {'Expected':<10} {'Result':<10} {'Status':<10}")
    print("-" * 90)

    all_passed = True
    for name, expected in test_cases:
        result = is_valid_coverage_name(name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result != expected:
            all_passed = False

        print(f"{name:<60} {str(expected):<10} {str(result):<10} {status:<10}")

    print("-" * 90)
    if all_passed:
        print("✅ All tests PASSED")
    else:
        print("❌ Some tests FAILED")
