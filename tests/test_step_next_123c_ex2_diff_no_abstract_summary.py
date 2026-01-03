#!/usr/bin/env python3
"""
STEP NEXT-123C: Contract Test - EX2_DETAIL_DIFF Must NOT Use Abstract Summary

ABSOLUTE FORBIDDEN:
- "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
- ANY abstract/vague language like "일부 보험사는..."

REQUIRED (MIXED_DIMENSION case):
- Explicit insurer names in summary_bullets
- Structural comparison: "{Insurer1}는 ... 기준, {Insurer2}는 ... 기준"
- NO "일부 보험사는..." patterns

This is a CONSTITUTIONAL test: If it fails, STEP NEXT-123C is violated.
"""
import pytest
from apps.api.chat_handlers_deterministic import Example2DiffHandlerDeterministic
from apps.api.chat_vm import ChatRequest


@pytest.fixture
def handler():
    return Example2DiffHandlerDeterministic()


def test_no_abstract_summary_in_mixed_dimension(handler):
    """
    STEP NEXT-123C: Test that MIXED_DIMENSION summary uses explicit insurer names

    FORBIDDEN:
    - "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
    - "일부 보험사는..."

    REQUIRED:
    - Explicit insurer names (삼성화재, 메리츠화재, etc.)
    - Structural comparison format
    """
    # Arrange: Query that triggers MIXED_DIMENSION (samsung has LIMIT, meritz has AMOUNT)
    compiled_query = {
        "insurers": ["samsung", "meritz"],
        "coverage_code": "A4200_1",
        "coverage_names": ["뇌출혈진단비"],
        "compare_field": "보장한도"
    }
    request = ChatRequest(message="삼성화재와 메리츠화재의 뇌출혈진단비 보장한도가 달라요?")

    # Act
    vm = handler.execute(compiled_query, request)

    # Assert: Find diff section and verify MIXED_DIMENSION
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None, "CoverageDiffResultSection not found"
    assert diff_section.status == "MIXED_DIMENSION", \
        f"Expected MIXED_DIMENSION, got {diff_section.status}"

    # Contract 1: ABSOLUTE FORBIDDEN - No abstract summary
    summary_text = " ".join(vm.summary_bullets)
    assert "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다" not in summary_text, \
        "FORBIDDEN PHRASE detected in summary_bullets (STEP NEXT-123C violation)"

    # Contract 2: No "일부 보험사는..." pattern
    assert "일부 보험사는" not in summary_text, \
        "Abstract pattern '일부 보험사는...' detected (STEP NEXT-123C violation)"

    # Contract 3: Summary must contain explicit insurer names
    assert "삼성화재" in summary_text or "메리츠화재" in summary_text, \
        f"Summary must contain explicit insurer names, got: {summary_text}"

    # Contract 4: Summary must explain structural difference
    # Either "보장금액" or "한도" or "횟수" should be present
    assert any(keyword in summary_text for keyword in ["보장금액", "한도", "횟수", "정액"]), \
        f"Summary must explain structural basis, got: {summary_text}"


def test_explicit_insurer_names_in_summary(handler):
    """
    STEP NEXT-123C: Test that summary uses display names, NOT codes

    FORBIDDEN:
    - "samsung", "meritz" (insurer codes)

    REQUIRED:
    - "삼성화재", "메리츠화재" (display names)
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

    # Find diff section
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None
    assert diff_section.status == "MIXED_DIMENSION"

    # Assert: No insurer codes in summary
    summary_text = " ".join(vm.summary_bullets)
    assert "samsung" not in summary_text.lower(), \
        f"Insurer code 'samsung' found in summary: {summary_text}"
    assert "meritz" not in summary_text.lower(), \
        f"Insurer code 'meritz' found in summary: {summary_text}"

    # Assert: Display names present
    assert "삼성화재" in summary_text or "메리츠화재" in summary_text, \
        f"Display names missing from summary: {summary_text}"


def test_structural_comparison_format(handler):
    """
    STEP NEXT-123C: Test that summary follows structural comparison format

    REQUIRED:
    - "{Insurer1}는 ... 기준, {Insurer2}는 ... 기준" pattern
    - Describes HOW coverage is defined (structural basis)
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

    # Find diff section
    diff_section = None
    for section in vm.sections:
        if hasattr(section, 'status'):
            diff_section = section
            break

    assert diff_section is not None
    assert diff_section.status == "MIXED_DIMENSION"

    # Assert: Structural comparison pattern
    summary_text = " ".join(vm.summary_bullets)

    # Should contain structural explanation keywords
    structural_keywords = ["기준", "정의", "구조", "방식"]
    assert any(keyword in summary_text for keyword in structural_keywords), \
        f"Summary should contain structural comparison keywords, got: {summary_text}"

    # Should NOT contain vague/abstract terms
    forbidden_vague_terms = ["일부", "몇몇", "어떤"]
    for term in forbidden_vague_terms:
        assert term not in summary_text, \
            f"Vague term '{term}' found in summary: {summary_text}"


def test_no_coverage_code_exposure_in_summary(handler):
    """
    STEP NEXT-123C: Test that coverage_code is NOT exposed in summary

    FORBIDDEN:
    - "A4200_1" or any coverage code pattern
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

    # Assert: No coverage_code in summary
    summary_text = " ".join(vm.summary_bullets)
    assert "A4200_1" not in summary_text, \
        f"Coverage code exposed in summary: {summary_text}"

    # Check for common coverage code patterns (uppercase letter + digits)
    import re
    code_pattern = re.compile(r'\b[A-Z]\d{4}(_\d+)?\b')
    assert not code_pattern.search(summary_text), \
        f"Coverage code pattern found in summary: {summary_text}"
