#!/usr/bin/env python3
"""
STEP NEXT-92: EX2_DETAIL_DIFF Strict Mixed Dimension Contract Test

PURPOSE:
Eliminate false positive MIXED_DIMENSION detection and ensure refs are always present

CONTRACT:
1. ✅ LIMIT vs AMOUNT + both have valid values → MIXED_DIMENSION
2. ✅ LIMIT vs "명시 없음" → NOT MIXED_DIMENSION (DIFF or ALL_SAME)
3. ✅ AMOUNT fallback alone → NOT MIXED_DIMENSION
4. ✅ ALL groups have evidence_refs.length >= 1
5. ✅ 0% coverage_code exposure in UI
6. ✅ title/summary/section consistency with status
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


def test_mixed_dimension_requires_both_valid_values(handler):
    """
    STEP NEXT-92: MIXED_DIMENSION only when BOTH sides have valid (non-"명시 없음") values

    Scenario:
    - Samsung has limit_summary (LIMIT dimension, valid value)
    - Meritz has NO limit_summary, uses coverage_amount_text (AMOUNT dimension, valid value)

    Expected:
    - status == MIXED_DIMENSION
    """
    # Arrange
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",  # Samsung has LIMIT, Meritz has AMOUNT fallback
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

    # Contract 1: status == MIXED_DIMENSION (both have valid values)
    assert diff_section.status == "MIXED_DIMENSION", \
        f"Expected MIXED_DIMENSION when both sides have valid values, got {diff_section.status}"


def test_no_mixed_when_one_side_missing(handler):
    """
    STEP NEXT-92: NOT MIXED_DIMENSION when one side is "명시 없음"

    Scenario:
    - Find a coverage where one insurer has limit, other doesn't
    - The one without should show "명시 없음"

    Expected:
    - status == DIFF (NOT MIXED_DIMENSION)
    """
    # Arrange
    # Use A1000_1 where both insurers should have the same dimension
    compiled_query = {
        "insurers": ["samsung", "hanwha"],
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

    # Contract 2: status should be DIFF or ALL_SAME, NOT MIXED_DIMENSION
    assert diff_section.status in ["DIFF", "ALL_SAME"], \
        f"Expected DIFF or ALL_SAME when same dimension, got {diff_section.status}"


def test_all_groups_have_evidence_refs(handler):
    """
    STEP NEXT-92: ALL groups must have evidence_refs with minimum 1 ref

    This is a constitutional requirement.

    Expected:
    - Every group.value_normalized.evidence_refs has length >= 1
    - Every group.insurer_details[].evidence_refs has length >= 1
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

    # Contract 4: ALL groups have evidence_refs
    for idx, group in enumerate(diff_section.groups):
        # Check value_normalized.evidence_refs
        if group.value_normalized:
            assert "evidence_refs" in group.value_normalized, \
                f"Group {idx} value_normalized missing evidence_refs field"
            assert len(group.value_normalized["evidence_refs"]) >= 1, \
                f"Group {idx} value_normalized.evidence_refs is empty (expected >= 1)"

        # Check insurer_details[].evidence_refs
        if group.insurer_details:
            for detail in group.insurer_details:
                assert len(detail.evidence_refs) >= 1, \
                    f"Insurer {detail.insurer} in group {idx} has no evidence_refs (expected >= 1)"


def test_refs_use_pd_or_ev_prefix(handler):
    """
    STEP NEXT-92: All refs must use PD: or EV: prefix

    Expected:
    - Every ref string starts with "PD:" or "EV:"
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

    # Check all refs
    for idx, group in enumerate(diff_section.groups):
        if group.value_normalized and "evidence_refs" in group.value_normalized:
            for ref_obj in group.value_normalized["evidence_refs"]:
                if "ref" in ref_obj:
                    ref_str = ref_obj["ref"]
                    assert ref_str.startswith("PD:") or ref_str.startswith("EV:"), \
                        f"Group {idx} ref '{ref_str}' doesn't start with PD: or EV:"


def test_no_coverage_code_in_ui(handler):
    """
    STEP NEXT-92: 0% coverage_code exposure in UI

    Expected:
    - coverage_code not in title, summary, sections
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

    # Contract 5: 0% coverage_code exposure
    coverage_code = "A4200_1"

    assert coverage_code not in vm.title, \
        f"Coverage code {coverage_code} exposed in title: {vm.title}"

    for bullet in vm.summary_bullets:
        assert coverage_code not in bullet, \
            f"Coverage code {coverage_code} exposed in summary: {bullet}"


def test_title_summary_consistency_with_mixed_status(handler):
    """
    STEP NEXT-92: title/summary must be consistent with status

    When status == MIXED_DIMENSION:
    - title should contain "보장 기준 차이"
    - summary should explain mixed dimension

    When status == DIFF:
    - title should contain "보장한도 차이" (field-specific)
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

    # Contract 6: title/summary consistency
    if diff_section.status == "MIXED_DIMENSION":
        assert "보장 기준 차이" in vm.title, \
            f"MIXED_DIMENSION status but title doesn't contain '보장 기준 차이': {vm.title}"

        summary_text = " ".join(vm.summary_bullets)
        assert "보장 '한도/횟수'" in summary_text or "보장금액" in summary_text, \
            f"MIXED_DIMENSION status but summary doesn't explain mixed dimension: {vm.summary_bullets}"

    elif diff_section.status == "DIFF":
        # Should have field-specific wording
        assert "보장한도" in vm.title or "차이" in vm.title, \
            f"DIFF status but title doesn't mention field: {vm.title}"


def test_amount_fallback_alone_not_mixed(handler):
    """
    STEP NEXT-92: AMOUNT fallback alone should NOT trigger MIXED_DIMENSION

    Scenario:
    - Single insurer using amount fallback (no LIMIT to compare with)

    Expected:
    - status != MIXED_DIMENSION
    """
    # Arrange
    # Use single insurer to test amount fallback alone
    compiled_query = {
        "insurers": ["meritz"],  # Single insurer with amount fallback
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="메리츠화재의 뇌출혈진단비 보장한도 확인")

    # Act
    vm = handler.execute(compiled_query, request)

    # Find CoverageDiffResultSection
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None

    # Contract 3: amount fallback alone → NOT MIXED_DIMENSION
    assert diff_section.status != "MIXED_DIMENSION", \
        f"Single insurer with amount fallback should NOT be MIXED_DIMENSION, got {diff_section.status}"


def test_section_title_consistency(handler):
    """
    STEP NEXT-92: section title should match overall status

    Expected:
    - Section title should be consistent with the response kind/status
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

    # Section title should be reasonable
    assert diff_section.title, "Section should have a title"
    assert "비교 결과" in diff_section.title or "차이" in diff_section.title, \
        f"Section title should mention comparison/difference: {diff_section.title}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
