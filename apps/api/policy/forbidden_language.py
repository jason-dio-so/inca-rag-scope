#!/usr/bin/env python3
"""
Single Source of Truth for Forbidden Language Policy
STEP NEXT-14-β: Production Hardening

DESIGN PRINCIPLES:
1. Allowlist-first: Factual statements are explicitly allowed
2. Evaluative-only blocking: Block superiority/recommendations/evaluations
3. Single source: All validators use this module
4. NO blocking of descriptive language (e.g., "비교합니다" is ALLOWED)

FORBIDDEN CATEGORIES:
- Superiority: "더 좋다", "유리하다", "우수하다"
- Comparative evaluation: "A가 B보다", "높다/낮다"
- Recommendations: "추천", "권장", "선택하세요"
- Judgments: "판단", "결론"
- Calculations: "평균", "합계", "차이 계산"

ALLOWED PHRASES:
- Factual descriptions: "비교합니다", "확인합니다", "표시합니다"
- Information presentation: "정리했습니다", "안내합니다"
- Neutral observations: "명시되어 있습니다", "존재합니다"
"""

import re
from typing import List, Set


# ============================================================================
# Allowlist (Explicitly Allowed Factual Phrases)
# ============================================================================

ALLOWLIST_PHRASES: Set[str] = {
    # Factual statements (always allowed)
    "비교합니다",
    "비교를",
    "비교한",
    "비교 결과",
    "확인합니다",
    "확인할",
    "표시합니다",
    "표시한",
    "정리했습니다",
    "정리한",
    "안내합니다",
    "안내한",
    "명시되어 있습니다",
    "명시된",
    "존재합니다",
    "존재하지 않습니다",
    "포함합니다",
    "포함된",
    "제공합니다",
    "제공된",
    "기준으로",
    "기반으로",
    "차이를 확인",  # "Difference checking" is allowed
    "보다 자세",  # "More detailed" is allowed
    "더 확인",  # "Further checking" is allowed
}


# ============================================================================
# Forbidden Patterns (Evaluative/Comparative Language ONLY)
# ============================================================================

EVALUATIVE_FORBIDDEN_PATTERNS: List[str] = [
    # Superiority/Inferiority (evaluative comparisons)
    r'(?:유리|불리)(?:합니다|한|하다)',  # "유리합니다", "불리한"
    r'(?:우수|열등)(?:합니다|한|하다)',  # "우수합니다", "열등한"
    r'(?:좋|나쁜|나쁘)(?:습니다|은|다)',  # "좋습니다", "나쁜"

    # Comparative evaluation (A vs B)
    r'(?:더|덜)\s+(?:높|낮|많|적|크|작)',  # "더 높다", "덜 많다"
    r'(?:높|낮|많|적)(?:습니다|은|다)(?!\s*(?:명시|표시|확인))',  # "높습니다" (but allow "높다고 명시")
    r'보다\s+(?:높|낮|많|적|크|작|좋|나쁘)',  # "보다 높다", "보다 좋다"
    r'[가-힣]+(?:가|은|는)\s+[가-힣]+보다',  # "A가 B보다", "삼성은 메리츠보다"

    # Contrastive conjunctions (but/however/whereas)
    r'반면(?:에)?',  # "반면", "반면에"
    r'그러나',  # "그러나"
    r'하지만',  # "하지만"

    # Extremes/Rankings
    r'가장\s+(?:높|낮|많|적|크|작|좋|나쁘)',  # "가장 높다", "가장 좋다"
    r'(?:최고|최저|최대|최소)(?:입니다|의|인)',  # "최고입니다", "최대의"

    # Recommendations/Judgments
    r'(?:추천|권장|제안)(?:합니다|한|하다)',  # "추천합니다", "권장한"
    r'(?:선택|판단|결론)(?:하세요|합니다|하다)',  # "선택하세요", "판단합니다"

    # Calculations/Aggregations (evaluative context)
    r'(?:평균|합계|총합)(?:은|는|입니다)',  # "평균은", "합계는", "합계입니다"
    r'차이(?:는|가)\s+[0-9]',  # "차이는 100만원" (calculation)
]


# ============================================================================
# Validation Function (Single Source)
# ============================================================================

def validate_text(text: str) -> None:
    """
    Validate text against forbidden language policy

    ALGORITHM:
    1. Check if text contains allowlist phrases → PASS
    2. Check against forbidden patterns → FAIL if matched
    3. Return None if valid, raise ValueError if forbidden

    Args:
        text: Text to validate

    Raises:
        ValueError: If text contains forbidden language

    Examples:
        >>> validate_text("2개 보험사의 암진단비를 비교합니다")  # PASS (allowlist)
        >>> validate_text("삼성이 메리츠보다 유리합니다")  # FAIL (forbidden)
        >>> validate_text("가입설계서에 1천만원으로 명시되어 있습니다")  # PASS
    """
    # Step 1: Check allowlist (priority)
    # If any allowlist phrase is present, skip forbidden check for those phrases
    text_lower = text.lower()

    # Create a sanitized version with allowlist phrases removed
    sanitized_text = text
    for allowed_phrase in ALLOWLIST_PHRASES:
        # Temporarily replace allowed phrases with safe placeholders
        sanitized_text = sanitized_text.replace(allowed_phrase, "___ALLOWED___")

    # Step 2: Check forbidden patterns on sanitized text
    for pattern in EVALUATIVE_FORBIDDEN_PATTERNS:
        match = re.search(pattern, sanitized_text)
        if match:
            raise ValueError(
                f"FORBIDDEN language detected: pattern '{pattern}' matches in '{text}'\n"
                f"Matched substring: '{match.group()}'\n"
                f"Policy: Evaluative/comparative language is prohibited. "
                f"Use factual statements instead."
            )

    # Step 3: Valid - return None
    return None


# ============================================================================
# Bulk Validation (for lists)
# ============================================================================

def validate_text_list(texts: List[str]) -> None:
    """
    Validate list of texts

    Args:
        texts: List of texts to validate

    Raises:
        ValueError: If any text contains forbidden language
    """
    for i, text in enumerate(texts):
        try:
            validate_text(text)
        except ValueError as e:
            raise ValueError(f"Validation failed at index {i}: {e}")


# ============================================================================
# Policy Documentation
# ============================================================================

POLICY_SUMMARY = """
Forbidden Language Policy (Single Source of Truth)

ALLOWED (Factual Statements):
- "비교합니다" - Describing comparison action
- "확인합니다" - Describing verification
- "표시합니다" - Describing display
- "명시되어 있습니다" - Stating what is specified
- "차이를 확인" - Checking differences (factual)

FORBIDDEN (Evaluative/Comparative):
- "A가 B보다 높다" - Comparative evaluation
- "유리합니다" - Superiority judgment
- "추천합니다" - Recommendation
- "가장 좋다" - Extremes/rankings
- "평균은 X입니다" - Calculations

USAGE:
```python
from apps.api.policy.forbidden_language import validate_text

# Validate single text
validate_text("2개 보험사를 비교합니다")  # OK

# Validate list
validate_text_list(["문장1", "문장2"])  # OK or raise ValueError
```

NOTE: This module is the SINGLE source for all forbidden language validation.
All validators in chat_vm.py, explanation_dto.py, etc. MUST delegate to this module.
"""


# ============================================================================
# Test Examples (for documentation)
# ============================================================================

if __name__ == "__main__":
    # Test cases
    print("Testing Forbidden Language Policy...\n")

    # SHOULD PASS
    test_cases_pass = [
        "2개 보험사의 암진단비를 비교합니다",
        "가입설계서에 명시되어 있습니다",
        "금액을 확인할 수 있습니다",
        "보장 내용을 표시합니다",
        "차이를 확인하세요",
        "보다 자세한 내용은 약관을 참조하세요",
    ]

    for text in test_cases_pass:
        try:
            validate_text(text)
            print(f"✅ PASS: {text}")
        except ValueError as e:
            print(f"❌ UNEXPECTED FAIL: {text}\n   {e}")

    print()

    # SHOULD FAIL
    test_cases_fail = [
        "삼성이 메리츠보다 유리합니다",
        "A 상품이 더 높습니다",
        "가장 좋은 선택입니다",
        "추천합니다",
        "반면 B는 낮습니다",
    ]

    for text in test_cases_fail:
        try:
            validate_text(text)
            print(f"❌ UNEXPECTED PASS: {text}")
        except ValueError as e:
            print(f"✅ CORRECTLY BLOCKED: {text}")

    print(f"\n{POLICY_SUMMARY}")
