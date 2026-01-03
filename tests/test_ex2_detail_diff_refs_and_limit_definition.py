#!/usr/bin/env python3
"""
Contract Test: EX2_DETAIL_DIFF Refs Enforcement + Limit Definition (STEP NEXT-90)

CONSTITUTIONAL RULES:
- ❌ NEVER return evidence_refs = [] (empty array)
- ❌ NEVER expose coverage_code in title/summary/sections.title
- ✅ "보장한도" MUST use kpi_summary.limit_summary, fallback to amount
- ✅ ALL values MUST have minimum 1 ref (PD: or EV:)

Policy A: "보장한도" = limit_summary (priority 1) OR coverage_amount_text (priority 2)
"""

import re
import pytest
from apps.api.chat_vm import ChatRequest
from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic


# Coverage code pattern (MUST NOT appear in view fields)
COVERAGE_CODE_PATTERN = re.compile(r"[A-Z]\d{4}_\d+")


def test_limit_uses_kpi_summary_when_available():
    """
    STEP NEXT-90: When kpi_summary.limit_summary exists, use it (not amount)

    Samsung A4200_1 has:
    - kpi_summary.limit_summary = "보험기간 중 1회"
    - proposal_facts.coverage_amount_text = "3,000만원"

    Expected: Use "보험기간 중 1회" (limit takes priority over amount)
    """
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        insurers=["samsung"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check groups
    assert len(response.sections) > 0, "Must have at least 1 section"
    diff_section = response.sections[0]

    # Find Samsung group
    samsung_group = None
    for group in diff_section.groups:
        if "samsung" in group.insurers:
            samsung_group = group
            break

    assert samsung_group is not None, "Samsung group not found"

    # Value should be limit_summary, not amount
    assert "1회" in samsung_group.value_display or "보험기간" in samsung_group.value_display, (
        f"Expected limit_summary (e.g., '보험기간 중 1회'), got: {samsung_group.value_display}"
    )
    assert "3,000만원" not in samsung_group.value_display, (
        "Should NOT use amount when limit_summary is available"
    )

    # Must have refs
    assert len(samsung_group.insurer_details) > 0, "Must have insurer_details"
    samsung_detail = samsung_group.insurer_details[0]
    assert len(samsung_detail.evidence_refs) > 0, "Must have at least 1 ref"


def test_limit_fallback_to_amount_when_no_limit_summary():
    """
    STEP NEXT-90: When kpi_summary.limit_summary is null, fallback to amount

    Meritz A4200_1 has:
    - kpi_summary.limit_summary = null
    - proposal_facts.coverage_amount_text = "3천만원"

    Expected: Use "3천만원" (amount fallback)
    """
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        message="보장한도가 다른 상품은?",
        insurers=["meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check groups
    diff_section = response.sections[0]

    # Find Meritz group
    meritz_group = None
    for group in diff_section.groups:
        if "meritz" in group.insurers:
            meritz_group = group
            break

    assert meritz_group is not None, "Meritz group not found"

    # Value should be amount (fallback)
    assert "만원" in meritz_group.value_display or "천만원" in meritz_group.value_display, (
        f"Expected amount fallback (e.g., '3천만원'), got: {meritz_group.value_display}"
    )

    # Must have refs (PD:meritz:A4200_1)
    meritz_detail = meritz_group.insurer_details[0]
    assert len(meritz_detail.evidence_refs) > 0, "Must have at least 1 ref (amount fallback)"

    # Must have note explaining fallback
    assert meritz_detail.notes is not None, "Must have note for amount fallback"
    assert any("보장금액" in note for note in meritz_detail.notes), (
        f"Note should explain amount fallback, got: {meritz_detail.notes}"
    )


def test_samsung_vs_meritz_shows_diff():
    """
    STEP NEXT-91: Samsung (limit) vs Meritz (amount) should show MIXED_DIMENSION status

    Samsung: "보험기간 중 1회" (from limit_summary) → LIMIT dimension
    Meritz: "3천만원" (from amount fallback) → AMOUNT dimension

    Expected: status=MIXED_DIMENSION, 2 groups (different dimension types)

    Update: STEP NEXT-90 → STEP NEXT-91
    - When one insurer has LIMIT and another has AMOUNT, status is MIXED_DIMENSION (not DIFF)
    - This is correct behavior introduced in STEP NEXT-91
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
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check diff status (STEP NEXT-91: MIXED_DIMENSION is correct)
    diff_section = response.sections[0]
    assert diff_section.status == "MIXED_DIMENSION", (
        f"Samsung (limit) vs Meritz (amount) should be MIXED_DIMENSION, got: {diff_section.status}"
    )

    # Should have 2 groups
    assert len(diff_section.groups) == 2, (
        f"Expected 2 groups (samsung, meritz), got: {len(diff_section.groups)}"
    )


def test_all_groups_have_minimum_one_ref():
    """
    STEP NEXT-90: ALL groups MUST have at least 1 ref (PD: or EV:)

    Even "명시 없음" cases must have PD: ref
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
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Check ALL groups
    diff_section = response.sections[0]
    for group_idx, group in enumerate(diff_section.groups):
        for detail_idx, detail in enumerate(group.insurer_details):
            assert len(detail.evidence_refs) > 0, (
                f"Group[{group_idx}].insurer_details[{detail_idx}] ({detail.insurer}) "
                f"has NO refs. MUST have minimum 1 ref (PD: or EV:)"
            )

            # Check ref format (must have PD: or EV:)
            for ref_idx, ref in enumerate(detail.evidence_refs):
                assert isinstance(ref, dict), (
                    f"Ref must be dict, got: {type(ref)} ({ref})"
                )
                ref_str = ref.get("ref", "")
                assert ref_str, f"Ref dict must have 'ref' key, got: {ref}"
                assert "PD:" in ref_str or "EV:" in ref_str, (
                    f"Ref must contain PD: or EV:, got: {ref_str}"
                )


def test_no_coverage_code_in_view_fields():
    """
    STEP NEXT-90: Regression test for STEP NEXT-89

    View fields (title/summary/sections.title) MUST have 0% coverage_code
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
        insurers=["samsung", "meritz"],
        coverage_names=["암진단비"]
    )

    response = handler.execute(compiled_query, request)

    # Collect view fields
    view_fields = []
    view_fields.append(("title", response.title))
    for idx, bullet in enumerate(response.summary_bullets):
        view_fields.append((f"summary_bullets[{idx}]", bullet))
    for idx, section in enumerate(response.sections):
        view_fields.append((f"sections[{idx}].title", section.title))

    # Check for coverage_code exposure
    violations = []
    for field_name, text in view_fields:
        matches = COVERAGE_CODE_PATTERN.findall(text)
        if matches:
            violations.append(f"{field_name}: {text} (codes: {matches})")

    assert len(violations) == 0, (
        f"❌ CODE LEAK in {len(violations)} view fields:\n" +
        "\n".join(violations)
    )
