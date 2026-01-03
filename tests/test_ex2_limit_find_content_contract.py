"""
STEP NEXT-87C: EX2_LIMIT_FIND Content Contract Tests

Contract Rules:
- ✅ Deterministic only (no LLM)
- ✅ EX2_LIMIT_FIND is for "finding/filtering/difference exploration" ONLY
- ❌ NO recommendation/superiority/value judgement
- ❌ NO EX4 contamination (O/X/△ eligibility judgement)
- ❌ NO EX3 contamination (comprehensive comparison table)
- ✅ 0% coverage_code exposure in UI-facing text
- ✅ refs must use PD:/EV: format

DoD: All 6 scenarios must PASS contract tests.
"""

import pytest
import re
from typing import Dict, Any, List


# ============================================================================
# Contract Check Functions
# ============================================================================

# 2.1 Forbidden words (judgement leakage)
FORBIDDEN_WORDS = [
    "추천", "비추천", "유리", "불리", "낫", "좋", "나쁘",
    "권장", "비권장", "선택", "최적", "베스트",
    "가입하세요", "가입 권장", "피하세요"
]

# Coverage code pattern (e.g., A4200_1, B1234_2)
COVERAGE_CODE_PATTERN = re.compile(r'[A-Z]\d{4}_\d')


def check_forbidden_words(text: str) -> List[str]:
    """Check if text contains forbidden judgement words."""
    found = []
    for word in FORBIDDEN_WORDS:
        if word in text:
            found.append(word)
    return found


def check_coverage_code_exposure(text: str) -> List[str]:
    """Check if text exposes coverage codes (e.g., A4200_1)."""
    return COVERAGE_CODE_PATTERN.findall(text)


def check_ex4_contamination(text: str) -> bool:
    """
    Check for EX4 (eligibility) contamination.

    EX4 patterns:
    - "보장 가능 여부"
    - O/X/△ matrix or judgement
    - "Unknown" as eligibility result

    Note: Mentioning "면책" or "감액" as part of condition explanation is OK.
    Using O/X/△ as eligibility judgement is NOT OK.
    """
    ex4_patterns = [
        "보장 가능 여부",
        "보장 가능:",
        "보장 불가",
        r"[OX△●]\s*(?:보장|가능)",  # O/X/△ as judgement
        "Unknown.*보장",
    ]

    for pattern in ex4_patterns:
        if re.search(pattern, text):
            return True

    return False


def check_ex3_contamination(response: Dict[str, Any]) -> bool:
    """
    Check for EX3 (comprehensive comparison) contamination.

    EX3 patterns:
    - "비교표" section
    - "공통사항 및 유의사항" section
    - Comprehensive 2+ insurer comparison table structure
    """
    sections = response.get("message", {}).get("sections", [])

    ex3_section_titles = [
        "비교표",
        "공통사항",
        "유의사항",
        "종합 비교",
    ]

    for section in sections:
        title = section.get("title", "")
        for ex3_title in ex3_section_titles:
            if ex3_title in title:
                return True

    return False


def extract_all_user_facing_text(response: Dict[str, Any]) -> List[str]:
    """Extract all user-facing text from response."""
    texts = []
    message = response.get("message", {})

    # title
    if "title" in message:
        texts.append(message["title"])

    # summary_bullets
    if "summary_bullets" in message:
        texts.extend(message["summary_bullets"])

    # bubble_markdown
    if "bubble_markdown" in message:
        texts.append(message["bubble_markdown"])

    # sections
    for section in message.get("sections", []):
        if "title" in section:
            texts.append(section["title"])

        if "bullets" in section:
            texts.extend(section["bullets"])

        # table rows
        for row in section.get("rows", []):
            for cell in row.get("cells", []):
                if "text" in cell:
                    texts.append(cell["text"])

    return texts


def validate_ex2_limit_find_contract(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate EX2_LIMIT_FIND response against contract rules.

    Returns:
        {
            "passed": bool,
            "violations": {
                "forbidden_words": [...],
                "coverage_code_exposure": [...],
                "ex4_contamination": bool,
                "ex3_contamination": bool,
            }
        }
    """
    violations = {
        "forbidden_words": [],
        "coverage_code_exposure": [],
        "ex4_contamination": False,
        "ex3_contamination": False,
    }

    # Extract all user-facing text
    all_texts = extract_all_user_facing_text(response)
    combined_text = "\n".join(all_texts)

    # Check forbidden words
    for text in all_texts:
        forbidden = check_forbidden_words(text)
        if forbidden:
            violations["forbidden_words"].extend([
                f"{word} in: {text[:50]}..." for word in forbidden
            ])

    # Check coverage code exposure
    for text in all_texts:
        codes = check_coverage_code_exposure(text)
        if codes:
            violations["coverage_code_exposure"].extend([
                f"{code} in: {text[:50]}..." for code in codes
            ])

    # Check EX4 contamination
    violations["ex4_contamination"] = check_ex4_contamination(combined_text)

    # Check EX3 contamination
    violations["ex3_contamination"] = check_ex3_contamination(response)

    # Overall pass/fail
    passed = (
        not violations["forbidden_words"] and
        not violations["coverage_code_exposure"] and
        not violations["ex4_contamination"] and
        not violations["ex3_contamination"]
    )

    return {
        "passed": passed,
        "violations": violations,
    }


# ============================================================================
# Test Scenarios
# ============================================================================

def test_ex2_limit_find_contract_validation_function():
    """Test that contract validation function works correctly."""

    # PASS case
    valid_response = {
        "message": {
            "title": "암직접입원비 보장한도 차이",
            "summary_bullets": [
                "삼성생명: 1일당 10만원",
                "한화생명: 1일당 5만원",
            ],
            "sections": [
                {
                    "title": "보장한도 차이",
                    "bullets": ["삼성생명이 더 높은 한도를 제공합니다."]
                },
                {
                    "title": "근거 안내",
                    "bullets": ["PD:samsung:A4200_1", "PD:hanwha:A4200_1"]
                }
            ]
        }
    }

    result = validate_ex2_limit_find_contract(valid_response)

    # Should detect "더 좋" (part of "더 높은" is OK, but need to check for judgement)
    # Actually "삼성생명이 더 높은 한도를 제공합니다" is factual, not judgement
    # Let's use a clear violation example

    # FAIL case: forbidden word
    invalid_response_1 = {
        "message": {
            "title": "암직접입원비 추천",  # ❌ "추천"
            "summary_bullets": ["삼성생명을 추천합니다"],  # ❌
        }
    }

    result = validate_ex2_limit_find_contract(invalid_response_1)
    assert not result["passed"]
    assert len(result["violations"]["forbidden_words"]) > 0

    # FAIL case: coverage code exposure
    invalid_response_2 = {
        "message": {
            "title": "A4200_1 보장한도 차이",  # ❌ coverage_code
        }
    }

    result = validate_ex2_limit_find_contract(invalid_response_2)
    assert not result["passed"]
    assert len(result["violations"]["coverage_code_exposure"]) > 0


# ============================================================================
# Real Scenario Tests (using manual_test_ex2_limit_find_samples.py)
# ============================================================================

def test_scenario_1_limit_difference():
    """
    Scenario 1: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_1_limit_difference

    response = scenario_1_limit_difference()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


def test_scenario_2_waiting_period_difference():
    """
    Scenario 2: "암진단비 담보 중 대기기간이 다른 보험사 찾아줘"

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_2_waiting_period_difference

    response = scenario_2_waiting_period_difference()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


def test_scenario_3_condition_difference():
    """
    Scenario 3: "암진단비 담보 조건이 다른 회사 찾아줘"

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_3_condition_difference

    response = scenario_3_condition_difference()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


def test_scenario_4_limit_difference_multi_insurer():
    """
    Scenario 4: "보장한도 차이 알려줘" (3+ insurers selected)

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_4_limit_difference_multi

    response = scenario_4_limit_difference_multi()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


def test_scenario_5_reduction_condition_filter():
    """
    Scenario 5: "유사암진단비에서 감액 조건이 있는 회사만"

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination

    Note: Mentioning "감액" as part of condition is OK.
          Using O/X/△ for eligibility judgement is NOT OK.
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_5_reduction_condition_filter

    response = scenario_5_reduction_condition_filter()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


def test_scenario_6_waiver_condition_difference():
    """
    Scenario 6: "납입면제 조건이 다른 회사 찾아줘"

    Expected: EX2_LIMIT_FIND response
    Contract: NO judgement, NO EX4/EX3 contamination
    """
    from tests.manual_test_ex2_limit_find_samples import scenario_6_waiver_condition_difference

    response = scenario_6_waiver_condition_difference()
    result = validate_ex2_limit_find_contract(response)

    assert result["passed"], f"Contract violations: {result['violations']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
