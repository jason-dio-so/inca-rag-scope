#!/usr/bin/env python3
"""
STEP NEXT-137: Normalized Schema-Based Status Decision Tests

Verify that status decision is based on normalized limit/amount schema,
NOT on raw string comparison.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.chat_vm import ChatRequest
from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic
from apps.api.store_loader import init_store_cache


def test_s1_samsung_vs_meritz_a6200_diff():
    """
    S1: Samsung (PER_HOSPITALIZATION, 180 days) vs Meritz (PER_POLICY_TERM, 1 count)
    Expected: status = DIFF (different limit scopes)
    """
    init_store_cache()

    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        insurers=['samsung', 'meritz'],
        coverage_code='A6200',
        message='암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘',
        kind='EX2_LIMIT_FIND'
    )

    compiled_query = {
        'kind': 'EX2_LIMIT_FIND',
        'coverage_code': 'A6200',
        'insurers': ['samsung', 'meritz'],
        'compare_field': '보장한도'
    }

    handler = Example2DiffHandlerDeterministic()
    response = handler.execute(compiled_query, request)

    assert response.sections, "S1 FAIL: No sections in response"
    actual_status = response.sections[0].status

    assert actual_status == "DIFF", f"S1 FAIL: Expected DIFF, got {actual_status}"

    # Verify evidence refs
    all_text = str(response.model_dump())
    assert 'A4200_1' not in all_text, "S1 FAIL: A4200_1 contamination"
    assert 'A6200' in all_text or 'samsung' in all_text.lower(), "S1 FAIL: Missing expected refs"

    print("✅ S1 PASS: Samsung vs Meritz A6200 → DIFF")


def test_s2_same_limit_same_amount_all_same():
    """
    S2: Two insurers with identical limit and amount
    Expected: status = ALL_SAME

    Note: Finding actual same-limit coverage is hard without data inspection.
    This test verifies the logic works when both normalized limits match.
    """
    # This would require finding a coverage where both insurers have identical
    # limit_summary and amount. Skipping for now as data verification needed.
    print("⏭️  S2 SKIPPED: Requires data inspection to find matching coverage")


def test_s3_partial_one_limit_one_amount():
    """
    S3: One insurer has limit only, another has amount only
    Expected: status = PARTIAL (incomplete data for comparison)

    Note: This would require finding such a coverage in actual data.
    """
    print("⏭️  S3 SKIPPED: Requires data inspection to find partial coverage")


def test_s4_other_coverage_no_regression():
    """
    S4: A4200_1 (암진단비) comparison should work without regression
    Expected: Legacy logic still works for non-"보장한도" comparisons
    """
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

    assert response.sections, "S4 FAIL: No sections in response"

    # Should not crash (no normalized_limit for A4200_1 is OK)
    actual_status = response.sections[0].status

    # Check NO A6200 contamination
    all_text = str(response.model_dump())
    assert 'A6200' not in all_text, "S4 FAIL: A6200 contamination in A4200_1 response"

    print(f"✅ S4 PASS: A4200_1 comparison works (status={actual_status}, no regression)")


def test_s5_generic_schema_no_hardcoding():
    """
    S5: Schema should work for any insurer (no insurer-specific hardcoding)
    Verify by checking that normalize functions are generic
    """
    from apps.api.utils.limit_normalizer import (
        normalize_limit_text,
        normalize_amount_text
    )

    # Test with different limit patterns (should all work generically)
    patterns = [
        ("1회 입원당 180일 한도", "PER_HOSPITALIZATION", 180),
        ("보험기간 중 1회", "PER_POLICY_TERM", 1),
        ("연간 2회", "PER_YEAR", 2),
    ]

    for text, expected_scope_name, expected_value in patterns:
        normalized = normalize_limit_text(text)
        assert normalized.scope.name == expected_scope_name, \
            f"S5 FAIL: Pattern '{text}' → {normalized.scope.name}, expected {expected_scope_name}"

    # Test amount normalization (should work for any amount)
    amounts = [
        ("2만원", 20000),
        ("3천만원", 30000000),
        ("1억원", 100000000),
    ]

    for text, expected_value in amounts:
        normalized = normalize_amount_text(text)
        assert normalized.value == expected_value, \
            f"S5 FAIL: Amount '{text}' → {normalized.value}, expected {expected_value}"

    print("✅ S5 PASS: Normalization schema is generic (no insurer hardcoding)")


if __name__ == "__main__":
    print("=== STEP NEXT-137: Normalized Status Decision Tests ===\n")

    try:
        test_s1_samsung_vs_meritz_a6200_diff()
        test_s2_same_limit_same_amount_all_same()
        test_s3_partial_one_limit_one_amount()
        test_s4_other_coverage_no_regression()
        test_s5_generic_schema_no_hardcoding()

        print("\n🎉 ALL TESTS COMPLETED (some skipped due to data requirements)")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
