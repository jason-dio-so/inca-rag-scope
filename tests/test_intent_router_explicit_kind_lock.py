#!/usr/bin/env python3
"""
Contract Test: Explicit kind Priority Lock (STEP NEXT-80)

CRITICAL RULES:
1. If request.kind is provided, it MUST be returned (100% priority)
2. Anti-confusion gates MUST NOT override explicit kind
3. Pattern matching MUST NOT override explicit kind
4. Category MUST NOT override explicit kind

This test ensures the UI contract is honored:
- Example 3 button sends kind="EX3_COMPARE"
- Backend MUST return kind="EX3_COMPARE" in response
- NO rerouting to EX2_LIMIT_FIND or EX2_DETAIL_DIFF allowed
"""

import pytest
from apps.api.chat_vm import ChatRequest, MessageKind
from apps.api.chat_intent import IntentRouter


def test_explicit_kind_ex3_compare_absolute_priority():
    """
    Test: Explicit kind=EX3_COMPARE MUST be honored (ABSOLUTE priority)

    Scenario: UI Example 3 button sends kind="EX3_COMPARE" with text containing
    limit-related keywords that would normally trigger EX2_LIMIT_FIND.

    Expected: kind="EX3_COMPARE" is returned (NO override)
    """
    request = ChatRequest(
        message="삼성화재와 메리츠화재의 암진단비 보장한도가 다른지 비교해주세요",
        kind="EX3_COMPARE",  # Explicit kind from UI
        coverage_names=["암진단비(유사암제외)"],
        insurers=["samsung", "meritz"],
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    # CRITICAL: Explicit kind MUST NOT be overridden
    assert result == "EX3_COMPARE", (
        f"Explicit kind=EX3_COMPARE was overridden to {result}. "
        "This violates STEP NEXT-80 contract (explicit kind = 100% priority)."
    )


def test_explicit_kind_ex3_compare_with_disease_subtype():
    """
    Test: Explicit kind=EX3_COMPARE MUST NOT be overridden by disease subtype gate

    Scenario: UI sends kind="EX3_COMPARE" but message contains "제자리암"
    which normally triggers EX4_ELIGIBILITY.

    Expected: kind="EX3_COMPARE" is returned (gate does NOT apply)
    """
    request = ChatRequest(
        message="삼성화재와 메리츠화재의 제자리암 보장을 비교해주세요",
        kind="EX3_COMPARE",  # Explicit kind from UI
        coverage_names=["제자리암진단비"],
        insurers=["samsung", "meritz"],
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    assert result == "EX3_COMPARE", (
        f"Explicit kind=EX3_COMPARE was overridden to {result} by disease subtype gate. "
        "Anti-confusion gates MUST NOT apply when explicit kind is provided."
    )


def test_explicit_kind_ex4_eligibility_absolute_priority():
    """
    Test: Explicit kind=EX4_ELIGIBILITY MUST be honored

    Scenario: UI Example 4 button sends kind="EX4_ELIGIBILITY"

    Expected: kind="EX4_ELIGIBILITY" is returned (NO override)
    """
    request = ChatRequest(
        message="제자리암 보장 가능한가요?",
        kind="EX4_ELIGIBILITY",  # Explicit kind from UI
        insurers=["samsung", "meritz"],
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    assert result == "EX4_ELIGIBILITY", (
        f"Explicit kind=EX4_ELIGIBILITY was overridden to {result}. "
        "This violates explicit kind contract."
    )


def test_no_explicit_kind_applies_gates():
    """
    Test: When kind is NOT provided, gates SHOULD apply

    Scenario: No explicit kind, message contains "보장한도.*다른"

    Expected: EX2_LIMIT_FIND (gate applies normally)
    """
    request = ChatRequest(
        message="암진단비 보장한도가 다른 상품을 찾아주세요",
        kind=None,  # No explicit kind
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    # When no explicit kind, gate should apply
    assert result == "EX2_LIMIT_FIND", (
        f"Expected EX2_LIMIT_FIND from gate, got {result}. "
        "Gates should apply when kind is not provided."
    )


def test_no_explicit_kind_applies_disease_subtype_gate():
    """
    Test: When kind is NOT provided, disease subtype gate SHOULD apply

    Scenario: No explicit kind, message contains "제자리암"

    Expected: EX4_ELIGIBILITY (gate applies normally)
    """
    request = ChatRequest(
        message="제자리암 보장 가능한가요?",
        kind=None,  # No explicit kind
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    # When no explicit kind, disease subtype gate should apply
    assert result == "EX4_ELIGIBILITY", (
        f"Expected EX4_ELIGIBILITY from disease subtype gate, got {result}. "
        "Disease subtype gate should apply when kind is not provided."
    )


def test_explicit_kind_ex2_limit_find_with_eligibility_keywords():
    """
    Test: Explicit kind=EX2_LIMIT_FIND MUST NOT be overridden by eligibility patterns

    Scenario: kind="EX2_LIMIT_FIND" but message contains "보장 가능"

    Expected: kind="EX2_LIMIT_FIND" is returned (NO override to EX4)
    """
    request = ChatRequest(
        message="암진단비 보장 가능한 한도가 다른 상품은?",
        kind="EX2_LIMIT_FIND",  # Explicit kind
        coverage_names=["암진단비(유사암제외)"],
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    assert result == "EX2_LIMIT_FIND", (
        f"Explicit kind=EX2_LIMIT_FIND was overridden to {result}. "
        "Explicit kind MUST have absolute priority over pattern matching."
    )


def test_explicit_kind_priority_over_category():
    """
    Test: Explicit kind MUST override category-based routing

    Scenario: kind="EX3_COMPARE" but selected_category would route to EX2_DETAIL_DIFF

    Expected: kind="EX3_COMPARE" is returned (explicit kind > category)
    """
    request = ChatRequest(
        message="암진단비 비교해주세요",
        kind="EX3_COMPARE",  # Explicit kind
        selected_category="② 상품/담보 설명",  # Would normally route to EX2_DETAIL_DIFF
        coverage_names=["암진단비(유사암제외)"],
        insurers=["samsung", "meritz"],
        llm_mode="OFF"
    )

    result = IntentRouter.route(request)

    # Explicit kind MUST override category
    assert result == "EX3_COMPARE", (
        f"Explicit kind=EX3_COMPARE was overridden to {result} by category. "
        "Explicit kind MUST have absolute priority over category."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
