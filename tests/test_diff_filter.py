#!/usr/bin/env python3
"""
Test STEP NEXT-COMPARE-FILTER-01: Diff Filter

Test coverage difference filtering feature
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.chat_vm import ChatRequest
from apps.api.chat_intent import IntentRouter, QueryCompiler
from apps.api.chat_handlers_deterministic import HandlerRegistryDeterministic


def test_diff_query_detection():
    """Test diff pattern detection"""
    print("=" * 60)
    print("TEST 1: Diff Pattern Detection")
    print("=" * 60)

    test_cases = [
        ("보장한도가 다른 상품 찾아줘", "EX2_DETAIL_DIFF"),
        ("보장한도 차이가 있는지 확인", "EX2_DETAIL_DIFF"),
        ("암진단비 보장한도 비교", "EX2_DETAIL"),  # No diff keyword
    ]

    for query, expected_kind in test_cases:
        request = ChatRequest(
            message=query,
            coverage_names=["암진단비"],
            insurers=["삼성화재", "메리츠화재"]
        )

        kind, confidence = IntentRouter.detect_intent(request)
        status = "✅" if kind == expected_kind else "❌"
        print(f"{status} '{query}' → {kind} (expected: {expected_kind})")


def test_diff_handler_execution():
    """Test diff handler with real data"""
    print("\n" + "=" * 60)
    print("TEST 2: Diff Handler Execution")
    print("=" * 60)

    # Create request with diff pattern
    request = ChatRequest(
        message="암직접입원비 보장한도가 다른 상품 찾아줘",
        kind="EX2_DETAIL_DIFF",  # Explicit kind
        coverage_names=["A4200_1"],
        insurers=["samsung", "meritz", "db", "hanwha"],
        compare_field="보장한도"
    )

    # Compile query
    compiled_query = QueryCompiler.compile(request, "EX2_DETAIL_DIFF")
    compiled_query["coverage_code"] = "A4200_1"  # Add coverage code

    print(f"\nCompiled Query:")
    print(json.dumps(compiled_query, ensure_ascii=False, indent=2))

    # Get handler
    handler = HandlerRegistryDeterministic.get_handler("EX2_DETAIL_DIFF")

    if not handler:
        print("❌ Handler not found")
        return

    # Execute
    try:
        vm = handler.execute(compiled_query, request)
        print(f"\n✅ Handler executed successfully")
        print(f"Title: {vm.title}")
        print(f"Summary:")
        for bullet in vm.summary_bullets:
            print(f"  - {bullet}")
        print(f"Sections: {len(vm.sections)}")
        print(f"Lineage: {vm.lineage}")
    except Exception as e:
        print(f"❌ Handler execution failed: {e}")
        import traceback
        traceback.print_exc()


def test_all_same_scenario():
    """Test scenario where all insurers have same value"""
    print("\n" + "=" * 60)
    print("TEST 3: All Same Scenario")
    print("=" * 60)

    # If all insurers have same limit value
    from pipeline.step8_render_deterministic.diff_filter import CoverageDiffFilter

    coverage_data = [
        {"insurer": "삼성화재", "value": "1~180일", "coverage_code": "A4200_1"},
        {"insurer": "메리츠화재", "value": "1~180일", "coverage_code": "A4200_1"},
        {"insurer": "DB손해보험", "value": "1~180일", "coverage_code": "A4200_1"},
    ]

    result = CoverageDiffFilter.filter_by_difference(coverage_data, "보장한도")
    print(f"Status: {result['status']}")
    print(f"Diff Insurers: {len(result['diff_insurers'])}")
    print(f"Same Insurers: {len(result['same_insurers'])}")

    if result['status'] == "ALL_SAME":
        print("✅ Correctly detected all same")
    else:
        print("❌ Should be ALL_SAME")


if __name__ == "__main__":
    test_diff_query_detection()
    test_diff_handler_execution()
    test_all_same_scenario()
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
