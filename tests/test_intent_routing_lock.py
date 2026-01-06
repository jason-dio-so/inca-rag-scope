"""
Intent Routing + need_more_info Contract Tests (STEP NEXT-OPS-CYCLE-03B/C)

Purpose: Lock intent routing rules to prevent regression
- EX3_COMPARE: insurers >= 2 + comparison keywords
- EX2_LIMIT_FIND: coverage auto-extract, insurers required
- EX2_DETAIL: insurers == 1
- EX4_ELIGIBILITY: disease subtype detection

Constitutional Rules (ABSOLUTE):
- NO code changes in apps/api/**
- Tests ONLY verify current behavior
- Test failure = routing regression detected
"""

import pytest
from apps.api.chat_intent import IntentRouter, IntentDispatcher
from apps.api.chat_vm import ChatRequest


# ============================================================================
# Test 1: EX3_COMPARE (insurers >= 2 + comparison keywords)
# ============================================================================

def test_ex3_compare_routing():
    """
    EX3_COMPARE: insurers >= 2 + "비교" keyword → EX3_COMPARE, no clarification

    STEP NEXT-OPS-CYCLE-03B: EX3 routing restored
    """
    request = ChatRequest(
        message="삼성화재와 메리츠화재 암진단비 비교해줢",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"],
        llm_mode="OFF"
    )

    # Route to kind
    kind = IntentRouter.route(request)
    assert kind == "EX3_COMPARE", f"Expected EX3_COMPARE, got {kind}"

    # Dispatch (should NOT require clarification)
    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is False, "EX3_COMPARE should not need clarification when all slots filled"
    assert response.message is not None, "EX3_COMPARE should return message"
    assert response.message.kind == "EX3_COMPARE"


def test_ex3_compare_missing_coverage():
    """
    EX3_COMPARE: insurers >= 2 + "비교" but NO coverage → need_more_info
    """
    request = ChatRequest(
        message="삼성화재와 메리츠화재 비교해줘",
        insurers=["samsung", "meritz"],
        coverage_names=[],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX3_COMPARE"

    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is True, "EX3_COMPARE with missing coverage should need clarification"
    assert "coverage_names" in response.missing_slots


# ============================================================================
# Test 2: EX2_LIMIT_FIND (coverage auto-extract, insurers required)
# ============================================================================

def test_ex2_limit_find_coverage_auto_extract():
    """
    EX2_LIMIT_FIND: coverage auto-extracted from message, ONLY insurers required

    STEP NEXT-OPS-CYCLE-03C: Coverage auto-extract restored (NO insurers auto-expand)
    """
    request = ChatRequest(
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=[],
        coverage_names=[],
        llm_mode="OFF"
    )

    # Route to EX2_LIMIT_FIND (via "찾아줘" pattern)
    kind = IntentRouter.route(request)
    assert kind == "EX2_LIMIT_FIND", f"Expected EX2_LIMIT_FIND, got {kind}"

    # Dispatch (should auto-extract coverage, require insurers)
    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is True, "EX2_LIMIT_FIND with missing insurers should need clarification"
    assert response.missing_slots == ["insurers"], f"Expected ['insurers'], got {response.missing_slots}"
    # Coverage should be auto-extracted (NOT in missing_slots)


def test_ex2_limit_find_no_insurers_auto_expand():
    """
    EX2_LIMIT_FIND: insurers MUST be selected (NO auto-expand to 8 insurers)

    Constitutional rule: insurers auto-expand FORBIDDEN (ABSOLUTE)
    """
    request = ChatRequest(
        message="암진단비 보장한도가 다른 상품 찾아줘",
        insurers=[],
        coverage_names=["암진단비"],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX2_LIMIT_FIND"

    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is True, "EX2_LIMIT_FIND MUST require insurers (NO auto-expand)"
    assert "insurers" in response.missing_slots


# ============================================================================
# Test 3: EX2_DETAIL (insurers == 1)
# ============================================================================

def test_ex2_detail_single_insurer():
    """
    EX2_DETAIL: insurers == 1 → EX2_DETAIL, no clarification

    STEP NEXT-86: Single insurer = explanation mode
    """
    request = ChatRequest(
        message="삼성화재 암진단비 설명해줘",
        insurers=["samsung"],
        coverage_names=["암진단비"],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX2_DETAIL", f"Expected EX2_DETAIL for single insurer, got {kind}"

    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is False, "EX2_DETAIL should not need clarification when all slots filled"
    assert response.message is not None
    assert response.message.kind == "EX2_DETAIL"


def test_ex2_detail_missing_coverage():
    """
    EX2_DETAIL: insurers == 1 but NO coverage → need_more_info
    """
    request = ChatRequest(
        message="삼성화재 설명해줘",
        insurers=["samsung"],
        coverage_names=[],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX2_DETAIL"

    response = IntentDispatcher.dispatch(request)
    assert response.need_more_info is True, "EX2_DETAIL with missing coverage should need clarification"
    assert "coverage_names" in response.missing_slots


# ============================================================================
# Test 4: EX4_ELIGIBILITY (disease subtype detection)
# ============================================================================

def test_ex4_eligibility_disease_subtype():
    """
    EX4_ELIGIBILITY: disease subtype keyword → EX4_ELIGIBILITY

    STEP NEXT-78: Anti-confusion gate for disease subtypes
    """
    request = ChatRequest(
        message="경계성종양 보장돼?",
        insurers=["samsung", "meritz"],
        coverage_names=[],
        llm_mode="OFF"
    )

    # Route should detect "경계성종양" (disease subtype)
    kind = IntentRouter.route(request)
    assert kind == "EX4_ELIGIBILITY", f"Expected EX4_ELIGIBILITY for disease subtype, got {kind}"

    # Note: EX4 requires insurers + disease_name, may need clarification if disease not detected
    # This test verifies routing only (dispatch may require disease_name slot)


def test_ex4_eligibility_missing_insurers():
    """
    EX4_ELIGIBILITY: disease subtype detected but NO insurers → need_more_info
    """
    request = ChatRequest(
        message="제자리암 보장돼?",
        insurers=[],
        coverage_names=[],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX4_ELIGIBILITY"

    response = IntentDispatcher.dispatch(request)
    # EX4 requires insurers + disease_name
    assert response.need_more_info is True, "EX4_ELIGIBILITY with missing insurers should need clarification"
    assert "insurers" in response.missing_slots


# ============================================================================
# Regression Tests (STEP NEXT-OPS-CYCLE-03B/C preservation)
# ============================================================================

def test_ex3_routing_not_dead():
    """
    Regression: EX3 routing should NOT fall back to EX2_LIMIT_FIND

    STEP NEXT-OPS-CYCLE-03B: EX3 was dead (0% routing), now restored
    """
    request = ChatRequest(
        message="한화생명과 DB손해보험 수술비 비교",
        insurers=["hanwha", "db"],
        coverage_names=["수술비"],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    assert kind == "EX3_COMPARE", "EX3 routing MUST NOT be dead (should not fall to EX2_LIMIT_FIND)"


def test_ex2_no_auto_expand_insurers():
    """
    Regression: EX2_LIMIT_FIND MUST NOT auto-expand insurers to 8

    STEP NEXT-OPS-CYCLE-03B: Removed auto-expand logic (42 lines deleted)
    """
    request = ChatRequest(
        message="암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
        insurers=[],
        coverage_names=[],
        llm_mode="OFF"
    )

    kind = IntentRouter.route(request)
    response = IntentDispatcher.dispatch(request)

    # Check that insurers were NOT auto-expanded
    assert response.need_more_info is True, "Should require user to select insurers"
    assert "insurers" in response.missing_slots, "Insurers MUST be in missing_slots (NO auto-expand)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
