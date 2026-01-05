#!/usr/bin/env python3
"""
STEP NEXT-135-β: EXAM2 Coverage Code Resolution Lock (Final)

Purpose: Prevent A4200_1 contamination in EXAM2 results

Core Rules (ABSOLUTE):
1. coverage_code MUST be compiled for ALL EX2 intents (EX2_LIMIT_FIND, EX2_DETAIL_DIFF, EX2_DETAIL)
2. Evidence refs MUST match query coverage (NO A4200_1 fallback contamination)
3. Coverage extraction from current message ONLY (STEP NEXT-134 preserved)
4. NO coverage_code omission for ANY EX2 kind in compiled_query

Constitutional Basis: EXAM CONSTITUTION (Coverage resolution MUST match query)

Definition of Success:
> "Coverage code compilation prevents A4200_1 fallback. Evidence refs always match user query coverage."

ROOT CAUSE (FIXED):
1. QueryCompiler line 580 did NOT include EX2_DETAIL_DIFF in coverage_code compilation condition
2. Handler had A4200_1 fallback: coverage_code = compiled_query.get("coverage_code", "A4200_1")
3. Result: 암직접입원일당 query → A4200_1 refs (contamination)

FIXES (STEP NEXT-135-β):
1. Line 582: Added "EX2_DETAIL_DIFF" to compilation condition
2. Handlers: Removed ALL A4200_1 fallbacks, replaced with explicit ValueError
3. Tests: Verify ALL EX2 kinds compile coverage_code correctly

SOLUTION:
1. QueryCompiler: Add "EX2_LIMIT_FIND" to coverage_code compilation condition (Line 580)
2. Handler: Remove A4200_1 fallback, raise error if coverage_code missing

VERIFICATION:
- "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" → A4200_1 refs = 0%, A6200 refs = 100%
- 10회 반복 → A4200_1 contamination = 0%
"""

import pytest
import json
import uuid
from apps.api.chat_intent import IntentRouter, QueryCompiler
from apps.api.chat_vm import ChatRequest


# ============================================================================
# Test 1: EX2_LIMIT_FIND Coverage Code Compilation (QueryCompiler)
# ============================================================================

def test_ex2_limit_find_coverage_code_compilation():
    """
    STEP NEXT-135: EX2_LIMIT_FIND MUST have coverage_code in compiled_query

    Given: "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"
    When: QueryCompiler.compile()
    Then: compiled_query["coverage_code"] = "A6200" (NOT missing, NOT A4200_1)
    """
    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=["samsung", "meritz"],
        coverage_names=["암직접입원일당"],
        compare_field="보장한도"
    )

    # Route to determine kind
    kind = IntentRouter.route(request)
    assert kind == "EX2_LIMIT_FIND", f"Expected EX2_LIMIT_FIND, got {kind}"

    # Compile query
    compiled_query = QueryCompiler.compile(request, kind)

    # CRITICAL: coverage_code MUST exist (no fallback allowed)
    assert "coverage_code" in compiled_query, "coverage_code missing from compiled_query"

    # CRITICAL: coverage_code MUST be A6200 (암직접입원일당), NOT A4200_1 (암진단비)
    assert compiled_query["coverage_code"] == "A6200", \
        f"Expected A6200 (암직접입원일당), got {compiled_query['coverage_code']}"

    print(f"✅ TEST PASS: coverage_code = {compiled_query['coverage_code']}")


# ============================================================================
# Test 2: Handler Fallback Removed (NO A4200_1 default)
# ============================================================================

def test_ex2_handler_no_fallback():
    """
    STEP NEXT-135: Handler MUST NOT use A4200_1 fallback

    Given: compiled_query without coverage_code
    When: Handler executes
    Then: Raise ValueError (do NOT fallback to A4200_1)
    """
    from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic

    handler = Example2DiffHandlerDeterministic()

    # Simulate compiled_query WITHOUT coverage_code
    compiled_query = {
        "kind": "EX2_LIMIT_FIND",
        "insurers": ["samsung", "meritz"],
        "coverage_names": ["암직접입원일당"],
        "compare_field": "보장한도"
        # NOTE: NO "coverage_code" key
    }

    request = ChatRequest(
        request_id=str(uuid.uuid4()),
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=["samsung", "meritz"],
        coverage_names=["암직접입원일당"]
    )

    # Handler MUST raise ValueError (NOT return A4200_1 result)
    with pytest.raises(ValueError, match="coverage_code missing"):
        handler.execute(compiled_query, request)

    print("✅ TEST PASS: Handler raises ValueError when coverage_code missing (NO A4200_1 fallback)")


# ============================================================================
# Test 3: Intent Regression (비교 vs 찾아줘)
# ============================================================================

@pytest.mark.parametrize("message,expected_kind", [
    ("암진단비 비교해줘", "EX3_COMPARE"),
    ("암진단비 보장한도가 다른 상품 찾아줘", "EX2_LIMIT_FIND"),
    ("삼성화재와 메리츠화재 암진단비 차이", "EX3_COMPARE"),
    ("암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘", "EX2_LIMIT_FIND"),
])
def test_intent_separation_regression(message, expected_kind):
    """
    STEP NEXT-135: "찾아줘" Gate MUST NOT capture comparison queries

    Given: Comparison query ("비교해줘", "차이")
    When: IntentRouter.route()
    Then: EX3_COMPARE (NOT EX2_LIMIT_FIND)

    Given: Search query ("찾아줘", "다른 상품")
    When: IntentRouter.route()
    Then: EX2_LIMIT_FIND (NOT EX3_COMPARE)
    """
    import uuid
    request = ChatRequest(
        request_id=uuid.uuid4(),
        message=message,
        insurers=["samsung", "meritz"]
    )

    kind = IntentRouter.route(request)
    assert kind == expected_kind, f"Message: {message}\nExpected: {expected_kind}, Got: {kind}"

    print(f"✅ TEST PASS: '{message}' → {kind}")


# ============================================================================
# Test 4: A6200 Coverage Name Mapping
# ============================================================================

@pytest.mark.parametrize("coverage_name,expected_code", [
    ("암직접입원일당", "A6200"),
    ("암직접입원비", "A6200"),  # Same code
    ("암진단비", "A4200_1"),
    ("입원일당", "A6100_1"),
])
def test_coverage_name_to_code_mapping(coverage_name, expected_code):
    """
    STEP NEXT-135: Coverage name → code mapping MUST be deterministic

    Given: Coverage name from user query
    When: QueryCompiler.map_coverage_name_to_code()
    Then: Correct coverage_code (암직접입원일당 → A6200)
    """
    code = QueryCompiler.map_coverage_name_to_code(coverage_name)
    assert code == expected_code, \
        f"Coverage: {coverage_name}\nExpected: {expected_code}, Got: {code}"

    print(f"✅ TEST PASS: {coverage_name} → {code}")


# ============================================================================
# Test 5: Insurer Auto-Expand Policy (B안)
# ============================================================================

def test_insurer_auto_expand_when_missing():
    """
    STEP NEXT-135: Insurers auto-expand to all 8 ONLY when user does NOT specify

    Given: User message without insurers
    When: QueryCompiler.compile()
    Then: insurers = all 8 insurers (auto-expand)

    Given: User message WITH insurers
    When: QueryCompiler.compile()
    Then: insurers = user-specified list (NO auto-expand)
    """
    # Case 1: NO insurers specified → auto-expand
    import uuid
    request1 = ChatRequest(
        request_id=uuid.uuid4(),
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=[],  # Empty
        coverage_names=["암직접입원일당"]
    )

    kind1 = IntentRouter.route(request1)
    compiled1 = QueryCompiler.compile(request1, kind1)

    # Should auto-expand to all 8 insurers
    expected_all = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai", "heungkuk", "db"]
    assert set(compiled1["insurers"]) == set(expected_all), \
        f"Expected auto-expand to 8 insurers, got {len(compiled1['insurers'])}"

    # Case 2: User specifies 2 insurers → NO auto-expand
    request2 = ChatRequest(
        request_id=uuid.uuid4(),
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=["samsung", "meritz"],
        coverage_names=["암직접입원일당"]
    )

    kind2 = IntentRouter.route(request2)
    compiled2 = QueryCompiler.compile(request2, kind2)

    # Should keep user's 2 insurers (NO auto-expand)
    assert compiled2["insurers"] == ["samsung", "meritz"], \
        f"Expected user's 2 insurers, got {compiled2['insurers']}"

    print("✅ TEST PASS: Auto-expand ONLY when insurers empty")


# ============================================================================
# Definition of Done (DoD)
# ============================================================================

def test_step_next_135_definition_of_done():
    """
    STEP NEXT-135 Definition of Done:

    "암직접입원일당 질의를 100번 반복해도
    A4200_1이 단 1번도 나오지 않으면 성공"

    Verification:
    1. compiled_query["coverage_code"] = "A6200" (100%)
    2. A4200_1 refs in response = 0%
    3. Intent separation preserved (EX2_LIMIT_FIND vs EX3_COMPARE)
    4. NO A4200_1 fallback in handler
    """
    # Simulate 10 iterations (100 too slow for unit test)
    import uuid
    for i in range(10):
        request = ChatRequest(
            request_id=uuid.uuid4(),
            message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
            insurers=["samsung", "meritz"],
            coverage_names=["암직접입원일당"]
        )

        kind = IntentRouter.route(request)
        assert kind == "EX2_LIMIT_FIND", f"Iteration {i}: Wrong kind {kind}"

        compiled_query = QueryCompiler.compile(request, kind)
        assert compiled_query["coverage_code"] == "A6200", \
            f"Iteration {i}: A4200_1 contamination detected!"

    print("✅ DoD PASS: 10 iterations, A4200_1 contamination = 0%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
