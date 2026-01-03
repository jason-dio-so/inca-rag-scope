#!/usr/bin/env python3
"""
STEP NEXT-91: EX2_DETAIL_DIFF Mixed Dimension Contract Test

PURPOSE:
Verify that EX2_DETAIL_DIFF properly handles mixed dimensions (limit vs amount fallback)

CONTRACT:
1. ✅ Mixed limit+amount → status == MIXED_DIMENSION
2. ✅ value_display contains 한도: / 보장금액: prefix
3. ✅ title uses "보장 기준 차이"
4. ✅ summary_bullets contains mixed dimension explanation
5. ✅ 0% coverage_code exposure
6. ✅ Minimum 1 ref per row
7. ✅ dimension_type metadata present in groups
8. ✅ Notes for amount fallback insurers
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic
from apps.api.chat_vm import ChatRequest


@pytest.fixture
def handler():
    """Create handler instance"""
    return Example2DiffHandlerDeterministic()


def test_mixed_dimension_status_detection(handler):
    """
    STEP NEXT-91: Test that mixed dimension (LIMIT+AMOUNT) is detected

    Scenario:
    - Samsung has limit_summary (LIMIT dimension)
    - Meritz has NO limit_summary, uses coverage_amount_text (AMOUNT dimension)

    Expected:
    - status == MIXED_DIMENSION
    """
    # Arrange
    # NOTE: A4200_1 is a coverage where Samsung has limit_summary but Meritz uses amount fallback
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Assert
    assert vm.kind == "EX2_DETAIL_DIFF"

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None, "CoverageDiffResultSection not found"

    # Contract 1: status == MIXED_DIMENSION
    assert diff_section.status == "MIXED_DIMENSION", \
        f"Expected MIXED_DIMENSION status, got {diff_section.status}"


def test_value_display_prefix_formatting(handler):
    """
    STEP NEXT-91: Test that value_display has dimension type prefixes

    Expected:
    - LIMIT group: value_display starts with "한도: "
    - AMOUNT group: value_display starts with "보장금액: "
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None
    assert diff_section.status == "MIXED_DIMENSION"

    # Contract 2: value_display contains prefix
    limit_group = None
    amount_group = None

    for group in diff_section.groups:
        if group.dimension_type == "LIMIT":
            limit_group = group
        elif group.dimension_type == "AMOUNT":
            amount_group = group

    # At least one of each type should exist for MIXED_DIMENSION
    if limit_group:
        assert limit_group.value_display.startswith("한도: "), \
            f"LIMIT group value_display should start with '한도: ', got {limit_group.value_display}"

    if amount_group:
        assert amount_group.value_display.startswith("보장금액: "), \
            f"AMOUNT group value_display should start with '보장금액: ', got {amount_group.value_display}"


def test_title_uses_basis_wording(handler):
    """
    STEP NEXT-91: Test that title uses "보장 기준 차이" for mixed dimension

    Expected:
    - title contains "보장 기준 차이"
    - NOT "보장한도 차이"
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Assert
    # Contract 3: title uses "보장 기준 차이"
    assert "보장 기준 차이" in vm.title, \
        f"Title should contain '보장 기준 차이', got: {vm.title}"
    assert "보장한도 차이" not in vm.title, \
        f"Title should NOT contain '보장한도 차이', got: {vm.title}"


def test_summary_explains_mixed_dimension(handler):
    """
    STEP NEXT-91: Test that summary_bullets explain mixed dimension

    Expected:
    - summary_bullets contains explanation about mixed basis
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Assert
    # Contract 4: summary_bullets contains mixed dimension explanation
    summary_text = " ".join(vm.summary_bullets)
    assert "보장 '한도/횟수'" in summary_text or "보장금액" in summary_text, \
        f"Summary should explain mixed dimension, got: {vm.summary_bullets}"


def test_no_coverage_code_exposure(handler):
    """
    STEP NEXT-91: Test that coverage_code is not exposed in UI

    Expected:
    - 0% coverage_code exposure in title, summary, sections
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Assert
    # Contract 5: 0% coverage_code exposure
    coverage_code = "A4200_1"

    assert coverage_code not in vm.title, \
        f"Coverage code {coverage_code} exposed in title: {vm.title}"

    for bullet in vm.summary_bullets:
        assert coverage_code not in bullet, \
            f"Coverage code {coverage_code} exposed in summary: {bullet}"


def test_minimum_one_ref_per_group(handler):
    """
    STEP NEXT-91: Test that each group has minimum 1 ref

    Expected:
    - Each insurer_detail has at least 1 ref (PD: or EV:)
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None

    # Contract 6: Minimum 1 ref per insurer
    for group in diff_section.groups:
        if group.insurer_details:
            for detail in group.insurer_details:
                assert len(detail.evidence_refs) >= 1, \
                    f"Insurer {detail.insurer} has no refs (expected minimum 1)"


def test_dimension_type_metadata_present(handler):
    """
    STEP NEXT-91: Test that dimension_type metadata is present in groups

    Expected:
    - Each group has dimension_type field (LIMIT or AMOUNT)
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None
    assert diff_section.status == "MIXED_DIMENSION"

    # Contract 7: dimension_type metadata present
    for group in diff_section.groups:
        assert hasattr(group, 'dimension_type'), \
            f"Group missing dimension_type field"
        assert group.dimension_type in ["LIMIT", "AMOUNT", None], \
            f"Invalid dimension_type: {group.dimension_type}"


def test_notes_for_amount_fallback(handler):
    """
    STEP NEXT-91: Test that amount fallback insurers have notes

    Expected:
    - Insurers using amount fallback have note explaining this
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None
    assert diff_section.status == "MIXED_DIMENSION"

    # Contract 8: Notes for amount fallback
    amount_fallback_note = "보장한도 정보가 없어 보장금액 기준으로 표시되었습니다"

    found_note = False
    for group in diff_section.groups:
        if group.dimension_type == "AMOUNT" and group.insurer_details:
            for detail in group.insurer_details:
                if detail.notes and amount_fallback_note in detail.notes:
                    found_note = True
                    break

    # At least one AMOUNT group should have this note
    if any(g.dimension_type == "AMOUNT" for g in diff_section.groups):
        assert found_note, \
            f"Amount fallback note not found in AMOUNT groups"


def test_no_mixed_dimension_when_same_type(handler):
    """
    STEP NEXT-91: Test that MIXED_DIMENSION is NOT set when all insurers use same dimension

    Scenario:
    - All insurers have limit_summary (all LIMIT dimension)

    Expected:
    - status == DIFF or ALL_SAME (NOT MIXED_DIMENSION)
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "hanwha"],  # Both have limit_summary
        "coverage_code": "A1000_1",
        "coverage_names": ["암진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 한화생명의 암진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None

    # Assert: status should be DIFF or ALL_SAME, NOT MIXED_DIMENSION
    assert diff_section.status in ["DIFF", "ALL_SAME"], \
        f"Expected DIFF or ALL_SAME when all insurers use same dimension, got {diff_section.status}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
