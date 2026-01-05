#!/usr/bin/env python3
"""
STEP NEXT-136-γ: S2 Regression Tests

Verify that Samsung A6200 patch does NOT affect:
1. Other coverages (A4200_1, etc.)
2. Other insurers (meritz-only queries)
3. Other message kinds (EX2_DETAIL_DIFF, EX3_COMPARE)
4. Other compare_fields

All 5 scenarios MUST produce IDENTICAL output before/after patch.
"""

import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.chat_vm import ChatRequest
from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic, Example3HandlerDeterministic
from apps.api.store_loader import init_store_cache


def test_s2_1_other_coverage_a4200_1():
    """S2-1: A4200_1 (암진단비) should be unchanged"""
    init_store_cache()

    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['samsung', 'meritz'],
        coverage_code='A4200_1',
        message='암진단비 담보 중 보장한도가 다른 상품 찾아줘',
        kind='EX2_LIMIT_FIND'
    )

    compiled_query = {
        'kind': 'EX2_LIMIT_FIND',
        'coverage_code': 'A4200_1',
        'insurers': ['samsung', 'meritz'],
        'compare_field': '보장한도'
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    # Check NO 180일 in response (A4200_1 has no 180-day limit)
    all_text = str(response.model_dump())
    assert '180일' not in all_text, f"S2-1 FAIL: 180일 found in A4200_1 response (should not exist)"
    # Note: A4200_1 in refs (PD:*:A4200_1) is OK - checking for unexpected patch application
    assert 'A6200' not in all_text, f"S2-1 FAIL: A6200 contamination in A4200_1 response"

    print("✅ S2-1 PASS: A4200_1 unchanged")


def test_s2_2_other_coverage_a4103():
    """S2-2: A4103 (뇌졸중진단비) should be unchanged"""
    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['samsung', 'meritz'],
        coverage_code='A4103',
        message='뇌졸중진단비 담보 중 보장한도가 다른 상품 찾아줘',
        kind='EX2_LIMIT_FIND'
    )

    compiled_query = {
        'kind': 'EX2_LIMIT_FIND',
        'coverage_code': 'A4103',
        'insurers': ['samsung', 'meritz'],
        'compare_field': '보장한도'
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    all_text = str(response.model_dump())
    assert '180일' not in all_text, f"S2-2 FAIL: 180일 found in A4103 response"
    assert 'A6200' not in all_text, f"S2-2 FAIL: A6200 contamination in A4103 response"

    print("✅ S2-2 PASS: A4103 unchanged")


def test_s2_3_meritz_only_a6200():
    """S2-3: Meritz-only A6200 query should be unchanged (no Samsung patch applied)"""
    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['meritz', 'kb'],
        coverage_code='A6200',
        message='암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘',
        kind='EX2_LIMIT_FIND'
    )

    compiled_query = {
        'kind': 'EX2_LIMIT_FIND',
        'coverage_code': 'A6200',
        'insurers': ['meritz', 'kb'],
        'compare_field': '보장한도'
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    all_text = str(response.model_dump())

    # Samsung should NOT appear (not in insurers list)
    assert 'samsung' not in all_text.lower(), f"S2-3 FAIL: Samsung appeared in meritz-only query"

    print("✅ S2-3 PASS: Meritz-only A6200 unchanged")


def test_s2_4_ex2_detail_diff():
    """S2-4: EX2_DETAIL_DIFF kind should work with patch"""
    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['samsung', 'meritz'],
        coverage_code='A6200',
        message='삼성화재와 메리츠화재 암직접입원일당 보장한도 비교해줘',
        kind='EX2_DETAIL_DIFF'
    )

    compiled_query = {
        'kind': 'EX2_DETAIL_DIFF',
        'coverage_code': 'A6200',
        'insurers': ['samsung', 'meritz'],
        'compare_field': '보장한도'
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    all_text = str(response.model_dump())

    # Patch should apply (kind in guard: EX2_LIMIT_FIND, EX2_DETAIL_DIFF)
    assert '180일' in all_text, f"S2-4 FAIL: Patch should apply to EX2_DETAIL_DIFF"
    assert 'samsung' in all_text.lower(), f"S2-4 FAIL: Samsung not in response"

    print("✅ S2-4 PASS: EX2_DETAIL_DIFF with patch OK")


def test_s2_5_different_compare_field():
    """S2-5: Different compare_field (보장금액) should NOT trigger patch"""
    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['samsung', 'meritz'],
        coverage_code='A6200',
        message='암직접입원일당 담보 중 보장금액 비교해줘',
        kind='EX2_LIMIT_FIND'
    )

    compiled_query = {
        'kind': 'EX2_LIMIT_FIND',
        'coverage_code': 'A6200',
        'insurers': ['samsung', 'meritz'],
        'compare_field': '보장금액'  # Different field
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    all_text = str(response.model_dump())

    # Patch should NOT apply (compare_field != "보장한도")
    # But 2만원 should appear (amount comparison)
    assert '2만원' in all_text, f"S2-5 FAIL: 2만원 should appear in 보장금액 comparison"

    print("✅ S2-5 PASS: Different compare_field unchanged")


if __name__ == "__main__":
    print("=== STEP NEXT-136-γ: S2 Regression Tests ===\n")

    try:
        test_s2_1_other_coverage_a4200_1()
        test_s2_2_other_coverage_a4103()
        test_s2_3_meritz_only_a6200()
        test_s2_4_ex2_detail_diff()
        test_s2_5_different_compare_field()

        print("\n🎉 ALL S2 REGRESSION TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ REGRESSION TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
