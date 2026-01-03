#!/usr/bin/env python3
"""
STEP NEXT-87B: EX2_LIMIT_FIND Routing Validation Test

PURPOSE:
- Validate that EX2_LIMIT_FIND intent routing works correctly
- NO code changes, only validation
- Check anti-confusion gates work as expected

USAGE:
    python tests/test_ex2_filter_routing.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.chat_vm import ChatRequest, MessageKind
from apps.api.chat_intent import IntentRouter
import uuid


def test_routing(message: str, insurers: list, coverage_names: list) -> tuple[MessageKind, str]:
    """Test routing for a given message"""
    request = ChatRequest(
        request_id=uuid.uuid4(),
        message=message,
        insurers=insurers,
        coverage_names=coverage_names,
        llm_mode="OFF"
    )

    routed_kind = IntentRouter.route(request)

    # Also show what detect_intent would return (for debugging)
    detected_kind, confidence = IntentRouter.detect_intent(request)

    return routed_kind, detected_kind, confidence


def main():
    """Run all routing tests"""

    print("=" * 80)
    print("STEP NEXT-87B: EX2_LIMIT_FIND Routing Validation")
    print("=" * 80)
    print()

    # Test cases
    test_cases = [
        {
            "name": "테스트 1: 보장한도가 다른 상품",
            "message": "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘",
            "insurers": ["samsung", "meritz", "hanwha"],
            "coverage_names": ["암직접입원비"],
            "expected": "EX2_LIMIT_FIND"
        },
        {
            "name": "테스트 2: 대기기간이 다른 보험사",
            "message": "암직접입원비 중 대기기간이 다른 보험사",
            "insurers": ["samsung", "meritz", "hanwha"],
            "coverage_names": ["암직접입원비"],
            "expected": "EX2_LIMIT_FIND"
        },
        {
            "name": "테스트 3: 조건이 다른 회사",
            "message": "암입원비 담보에서 조건이 다른 회사",
            "insurers": ["samsung", "meritz", "hanwha"],
            "coverage_names": ["암입원비"],
            "expected": "EX2_LIMIT_FIND"
        },
        {
            "name": "테스트 4: 보장한도 차이",
            "message": "암직접입원비 보장한도 차이 알려줘",
            "insurers": ["samsung", "meritz", "hanwha"],
            "coverage_names": ["암직접입원비"],
            "expected": "EX2_LIMIT_FIND"
        },
        # Anti-confusion tests
        {
            "name": "테스트 5: EX2_DETAIL (insurers=1)",
            "message": "삼성화재 암진단비 설명해주세요",
            "insurers": ["samsung"],
            "coverage_names": ["암진단비(유사암제외)"],
            "expected": "EX2_DETAIL"
        },
        {
            "name": "테스트 6: EX3_COMPARE (비교 without 다른)",
            "message": "삼성화재와 메리츠화재 암진단비 비교",
            "insurers": ["samsung", "meritz"],
            "coverage_names": ["암진단비(유사암제외)"],
            "expected": "EX3_COMPARE"  # Or EX2_LIMIT_FIND depending on patterns
        },
        {
            "name": "테스트 7: EX4_ELIGIBILITY (subtype)",
            "message": "제자리암 보장 가능 여부",
            "insurers": ["samsung", "meritz"],
            "coverage_names": [],
            "expected": "EX4_ELIGIBILITY"
        }
    ]

    results = []

    for idx, test in enumerate(test_cases, 1):
        print(f"[{idx}/{len(test_cases)}] {test['name']}")
        print(f"  Message: \"{test['message']}\"")
        print(f"  Insurers: {test['insurers']} (count: {len(test['insurers'])})")

        routed_kind, detected_kind, confidence = test_routing(
            test["message"],
            test["insurers"],
            test["coverage_names"]
        )

        print(f"  Expected: {test['expected']}")
        print(f"  Routed:   {routed_kind}")
        print(f"  Detected: {detected_kind} (confidence: {confidence:.2f})")

        # Check result
        is_correct = routed_kind == test['expected']
        status = "✅ PASS" if is_correct else "❌ FAIL"
        print(f"  Status:   {status}")

        results.append({
            "test": test['name'],
            "message": test['message'],
            "expected": test['expected'],
            "routed": routed_kind,
            "detected": detected_kind,
            "confidence": confidence,
            "pass": is_correct
        })

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    total = len(results)
    passed = sum(1 for r in results if r['pass'])
    failed = total - passed

    print(f"Total:  {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print()

    if failed > 0:
        print("Failed Tests:")
        for r in results:
            if not r['pass']:
                print(f"  ❌ {r['test']}")
                print(f"     Expected: {r['expected']}, Got: {r['routed']}")
        print()

    # Results table (Markdown)
    print("=" * 80)
    print("RESULTS TABLE (for STEP_NEXT_87B_EX2_FILTER_VALIDATION.md)")
    print("=" * 80)
    print()
    print("| 프롬프트 | 실제 kind | 기대 kind | 문제점 |")
    print("|----------|-----------|-----------|--------|")
    for r in results[:4]:  # Only EX2_LIMIT_FIND tests
        problem = "-" if r['pass'] else f"Expected {r['expected']}, got {r['routed']}"
        # Truncate message for table
        msg_short = r['message'][:30] + "..." if len(r['message']) > 30 else r['message']
        print(f"| {msg_short} | {r['routed']} | {r['expected']} | {problem} |")
    print()

    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
