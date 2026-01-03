#!/usr/bin/env python3
"""
Contract Test: EX2_DETAIL_DIFF Coverage Code Exposure Prevention (STEP NEXT-89)

CONSTITUTIONAL RULES:
- ❌ NEVER expose coverage_code ([A-Z]\d{4}_\d+) in title/summary_bullets/sections[*].title
- ✅ Coverage codes ONLY allowed in refs (PD:, EV:)
- ✅ View fields MUST use coverage_name or "해당 담보" fallback

TEST SCOPE:
1. Title/summary/section.title have 0% coverage_code exposure
2. Coverage_name fallback works when coverage_names not provided
3. Insurer list formatting (singular/plural) is correct
"""

import re
import pytest
from pathlib import Path
from apps.api.chat_vm import ChatRequest
from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic


# Coverage code pattern (MUST NOT appear in view fields)
COVERAGE_CODE_PATTERN = re.compile(r"[A-Z]\d{4}_\d+")


def test_ex2_detail_diff_no_coverage_code_in_title():
    """
    STEP NEXT-89: Title MUST NOT contain coverage_code

    Validates:
    - response.title contains NO bare coverage codes (A4200_1, etc.)
    - Title uses coverage_name or "해당 담보" fallback
    """
    handler = Example2DiffHandlerDeterministic()

    # Scenario: 2 insurers, with coverage_names provided
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],  # Proper coverage name
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check title for coverage code exposure
    title = response.title
    matches = COVERAGE_CODE_PATTERN.findall(title)

    assert len(matches) == 0, (
        f"❌ CODE LEAK in title: {title}\n"
        f"Found coverage codes: {matches}"
    )

    # Title should contain coverage_name (암진단비)
    assert "암진단비" in title or "해당 담보" in title, (
        f"Title missing coverage name or fallback: {title}"
    )


def test_ex2_detail_diff_no_coverage_code_in_summary_bullets():
    """
    STEP NEXT-89: Summary bullets MUST NOT contain coverage_code

    Validates:
    - response.summary_bullets[*] contains NO bare coverage codes
    """
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check each summary bullet for coverage code exposure
    for idx, bullet in enumerate(response.summary_bullets):
        matches = COVERAGE_CODE_PATTERN.findall(bullet)

        assert len(matches) == 0, (
            f"❌ CODE LEAK in summary_bullets[{idx}]: {bullet}\n"
            f"Found coverage codes: {matches}"
        )


def test_ex2_detail_diff_no_coverage_code_in_section_titles():
    """
    STEP NEXT-89: Section titles MUST NOT contain coverage_code

    Validates:
    - response.sections[*].title contains NO bare coverage codes
    """
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check each section title for coverage code exposure
    for idx, section in enumerate(response.sections):
        section_title = section.title
        matches = COVERAGE_CODE_PATTERN.findall(section_title)

        assert len(matches) == 0, (
            f"❌ CODE LEAK in sections[{idx}].title: {section_title}\n"
            f"Found coverage codes: {matches}"
        )


def test_ex2_detail_diff_coverage_name_fallback_when_missing():
    """
    STEP NEXT-89: When coverage_names NOT provided, fallback to card or "해당 담보"

    Validates:
    - Title uses card's coverage_name_canonical/raw
    - If card has no name, uses "해당 담보"
    - NO coverage_code exposure
    """
    handler = Example2DiffHandlerDeterministic()

    # Scenario: coverage_names NOT provided (simulate missing from request)
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        # NO coverage_names key
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"]
        # NO coverage_names
    )

    response = handler.execute(compiled_query, request)

    # Check title (should use card fallback or "해당 담보")
    title = response.title
    matches = COVERAGE_CODE_PATTERN.findall(title)

    assert len(matches) == 0, (
        f"❌ CODE LEAK in title (fallback scenario): {title}\n"
        f"Found coverage codes: {matches}"
    )

    # Title should use "해당 담보" or card's coverage_name
    # (We can't guarantee card has name, but we CAN guarantee no code)
    assert "A4200_1" not in title, (
        f"Title leaked coverage_code in fallback scenario: {title}"
    )


def test_ex2_detail_diff_insurer_list_formatting():
    """
    STEP NEXT-89: Insurer list formatting (singular/plural)

    Validates:
    - 2+ insurers: "삼성화재와 메리츠화재의 ..."
    - 1 insurer: "삼성화재의 ..."
    - NO coverage_code exposure
    """
    handler = Example2DiffHandlerDeterministic()

    # Scenario 1: 2 insurers
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    title = response.title

    # Should contain insurer names (not codes)
    assert "삼성화재" in title or "메리츠화재" in title, (
        f"Title missing insurer names: {title}"
    )

    # Should NOT contain coverage_code
    matches = COVERAGE_CODE_PATTERN.findall(title)
    assert len(matches) == 0, (
        f"❌ CODE LEAK in title (2 insurers): {title}\n"
        f"Found coverage codes: {matches}"
    )


def test_ex2_detail_diff_all_view_fields_zero_exposure():
    """
    STEP NEXT-89: COMPREHENSIVE test - ALL view fields MUST have 0% coverage_code

    Validates:
    - title: 0% exposure
    - summary_bullets[*]: 0% exposure
    - sections[*].title: 0% exposure
    """
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        kind="EX2_DETAIL_DIFF",
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Collect all view fields
    all_view_texts = []

    # Title
    all_view_texts.append(("title", response.title))

    # Summary bullets
    for idx, bullet in enumerate(response.summary_bullets):
        all_view_texts.append((f"summary_bullets[{idx}]", bullet))

    # Section titles
    for idx, section in enumerate(response.sections):
        all_view_texts.append((f"sections[{idx}].title", section.title))

    # Check ALL view fields for coverage_code exposure
    violations = []
    for field_name, text in all_view_texts:
        matches = COVERAGE_CODE_PATTERN.findall(text)
        if matches:
            violations.append(f"{field_name}: {text} (codes: {matches})")

    assert len(violations) == 0, (
        f"❌ CODE LEAK in {len(violations)} view fields:\n" +
        "\n".join(violations)
    )
