#!/usr/bin/env python3
"""
STEP NEXT-95: Coverage Grouping Runtime Proof Tests

GOAL:
- Verify EX4_ELIGIBILITY grouping works correctly at runtime
- Verify EX3_COMPARE exclusion is intentional (single coverage only)
- Verify NO coverage_code/Unknown/raw_text exposure
- Verify judgment results unchanged (before/after diff = 0)

CONSTITUTIONAL RULES:
- ❌ NO judgment/comparison logic changes
- ❌ NO coverage_code exposure in UI
- ❌ NO "Unknown" string exposure (use "표현 없음"/"근거 없음")
- ✅ View layer only (bubble_markdown)
- ✅ Grouping is deterministic
"""

import pytest
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer
from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


# ============================================================================
# EX4_ELIGIBILITY Runtime Proof Tests
# ============================================================================

def test_ex4_case_a_single_group_no_header():
    """
    Case A — 단일 그룹
    - 조건: 모든 보험사가 동일 trigger (전부 진단비)
    - 기대:
      - ❌ 그룹 헤더 미표시
      - 판단 결과 기존과 100% 동일
    """
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "암 진단 시 3,000만원 지급",
            "evidence_ref": "PD:samsung:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4200_1"
        },
        {
            "insurer": "meritz",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "1년 미만 가입 시 50% 감액",
            "evidence_ref": "PD:meritz:A5298_001",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:meritz:A5298_001"
        },
        {
            "insurer": "kb",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "유사암은 면책",
            "evidence_ref": "PD:kb:B1100_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:kb:B1100_1"
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "NEUTRAL",
            "summary": "장단점 혼재로 우열 판단이 어렵습니다"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section
    )

    # ❌ 단일 그룹 → 그룹 헤더 미표시
    assert "**[진단 관련 담보]**" not in bubble
    assert "**[치료/수술 관련 담보]**" not in bubble
    assert "**[기타 담보]**" not in bubble

    # ✅ 판단 결과 보존 (O/△/X 모두 표시)
    assert "**samsung**: ○" in bubble
    assert "**meritz**: △" in bubble
    assert "**kb**: ✕" in bubble

    # ✅ decision/summary 보존
    assert "보험사별 보장 여부가 갈립니다" in bubble  # NEUTRAL decision
    assert "장단점 혼재로 우열 판단이 어렵습니다" in bubble

    # ❌ NO coverage_code exposure
    assert "A4200_1" not in bubble or "PD:samsung:A4200_1" in bubble
    assert "A5298_001" not in bubble or "PD:meritz:A5298_001" in bubble

    # ❌ NO "Unknown" string exposure
    assert "Unknown" not in bubble


def test_ex4_case_b_multiple_groups_with_headers():
    """
    Case B — 복수 그룹
    - 조건: trigger가 보험사별로 분리됨 (진단 + 수술)
    - 기대:
      - ✅ [진단 관련 담보], [치료/수술 관련 담보] 헤더 표시
      - 그룹 내 정렬: O → △ → X
      - 판단 결과 before/after diff = 0
    """
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "암 진단 시 지급",
            "evidence_ref": "PD:samsung:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4200_1"
        },
        {
            "insurer": "meritz",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "1년 미만 50% 감액",
            "evidence_ref": "PD:meritz:A5298_001",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:meritz:A5298_001"
        },
        {
            "insurer": "kb",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "유사암 수술 시 지급",
            "evidence_ref": "PD:kb:B1100_2",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "유사암수술비",
            "proposal_detail_ref": "PD:kb:B1100_2"
        },
        {
            "insurer": "hanwha",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "수술비는 면책",
            "evidence_ref": "PD:hanwha:C3200_1",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "유사암수술비",
            "proposal_detail_ref": "PD:hanwha:C3200_1"
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "RECOMMEND",
            "summary": "보장 가능(O) 항목이 다수입니다"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section
    )

    # ✅ 복수 그룹 → 그룹 헤더 표시
    assert "**[진단 관련 담보]**" in bubble
    assert "**[치료/수술 관련 담보]**" in bubble

    # ✅ 그룹 내 정렬 검증 (진단 그룹: O → △)
    diagnosis_section = bubble.split("**[진단 관련 담보]**")[1].split("**[치료/수술 관련 담보]**")[0]
    assert diagnosis_section.index("**samsung**: ○") < diagnosis_section.index("**meritz**: △")

    # ✅ 그룹 내 정렬 검증 (수술 그룹: O → X)
    surgery_section = bubble.split("**[치료/수술 관련 담보]**")[1].split("##")[0]  # Next section boundary
    assert surgery_section.index("**kb**: ○") < surgery_section.index("**hanwha**: ✕")

    # ✅ 판단 결과 보존
    assert "**samsung**: ○" in bubble
    assert "**meritz**: △" in bubble
    assert "**kb**: ○" in bubble
    assert "**hanwha**: ✕" in bubble

    # ✅ decision/summary 보존
    assert "보장 가능한 보험사가 다수입니다" in bubble  # RECOMMEND decision
    assert "보장 가능(O) 항목이 다수입니다" in bubble


def test_ex4_case_c_mixed_trigger_with_reduction():
    """
    Case C — trigger 혼합 + 감액 포함
    - 조건: △(감액) + O 혼합, trigger 다양
    - 기대:
      - grouping은 표시만 변경
      - 감액/면책 의미 왜곡 없음
    """
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "제자리암 진단 시 지급",
            "evidence_ref": "PD:samsung:A4210",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "제자리암진단비",
            "proposal_detail_ref": "PD:samsung:A4210"
        },
        {
            "insurer": "meritz",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "1년 미만 가입 시 50% 감액",
            "evidence_ref": "PD:meritz:A5298_003",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "제자리암진단비",
            "proposal_detail_ref": "PD:meritz:A5298_003"
        },
        {
            "insurer": "kb",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "유사암 치료 시 지급",
            "evidence_ref": "PD:kb:B1100_3",
            "coverage_trigger": "TREATMENT",
            "coverage_name_raw": "유사암치료비",
            "proposal_detail_ref": "PD:kb:B1100_3"
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "NEUTRAL",
            "summary": "장단점 혼재로 우열 판단이 어렵습니다"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section
    )

    # ✅ 복수 그룹 → 헤더 표시
    assert "**[진단 관련 담보]**" in bubble
    assert "**[치료/수술 관련 담보]**" in bubble

    # ✅ 감액 의미 보존 (△ with detail)
    assert "**meritz**: △" in bubble
    assert "진단비 지급 (1년 미만 50% 감액)" in bubble

    # ✅ 판단 결과 보존
    assert "**samsung**: ○" in bubble
    assert "**kb**: ○" in bubble

    # ✅ decision 보존
    assert "보험사별 보장 여부가 갈립니다" in bubble  # NEUTRAL


def test_ex4_no_unknown_string_exposure():
    """
    Constitutional Rule: NO "Unknown" string in UI
    - Must use "표현 없음" or "근거 없음"
    """
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "Unknown",
            "evidence_type": None,
            "evidence_snippet": None,
            "evidence_ref": None,
            "coverage_trigger": None,
            "coverage_name_raw": "기타담보",
            "proposal_detail_ref": None
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "NEUTRAL",
            "summary": "장단점 혼재로 우열 판단이 어렵습니다"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section
    )

    # ❌ NO "Unknown" string
    assert "Unknown" not in bubble
    # ✅ Must use "판단 근거 없음" or "?"
    assert "?" in bubble or "판단 근거 없음" in bubble


def test_ex4_no_coverage_code_exposure():
    """
    Constitutional Rule: NO coverage_code (A4200_1) in UI
    - OK in refs (PD:samsung:A4200_1)
    - NOT OK as bare string
    """
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "암 진단 시 지급",
            "evidence_ref": "PD:samsung:A4200_1",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4200_1"
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "RECOMMEND",
            "summary": "보장 가능(O) 항목이 다수입니다"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section,
        coverage_display_name="암진단비(유사암 제외)"
    )

    # Refs are OK (PD:samsung:A4200_1)
    # But bare codes are NOT OK
    import re
    # Find all coverage codes
    bare_codes = re.findall(r'\b([A-Z]\d{4}_\d+)\b', bubble)
    for code in bare_codes:
        # Each code must be part of a ref (PD: or EV:)
        assert f"PD:samsung:{code}" in bubble or f"EV:samsung:{code}" in bubble, \
            f"Bare coverage_code {code} found without ref prefix"


# ============================================================================
# EX3_COMPARE Runtime Proof Tests (Exclusion Verification)
# ============================================================================

def test_ex3_exclusion_intentional_single_coverage_only():
    """
    STEP NEXT-95: EX3_COMPARE exclusion is intentional
    - EX3 compares a SINGLE coverage across insurers
    - Grouping is NOT applicable (no multiple coverages to group)
    - This test verifies the exclusion is documented and intentional
    """
    # EX3 compose() signature confirms single coverage design
    # Args: coverage_code (singular), comparison_data (dict by insurer)
    # NOT: coverage_codes (plural) or multi-coverage comparison

    # Verify compose() takes single coverage_code
    import inspect
    sig = inspect.signature(EX3CompareComposer.compose)
    params = list(sig.parameters.keys())

    assert "coverage_code" in params  # Singular
    assert "coverage_codes" not in params  # NOT plural

    # Verify no grouping logic in EX3 bubble_markdown
    import inspect
    source = inspect.getsource(EX3CompareComposer._build_bubble_markdown)

    # Check for assign_coverage_group calls (simple string search)
    has_grouping = "assign_coverage_group" in source

    # ✅ EX3 should NOT have grouping logic
    assert not has_grouping, "EX3_COMPARE should NOT use assign_coverage_group (single coverage only)"


def test_ex3_single_coverage_design_verified():
    """
    Verify EX3 design: single coverage comparison only
    - Input: 1 coverage_code, N insurers
    - Output: comparison of SAME coverage across insurers
    - Grouping is meaningless (nothing to group)
    """
    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "premium": "10,000원",
            "period": "20년납/80세만기",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "meritz": {
            "amount": "3000만원",
            "premium": "9,500원",
            "period": "20년납/80세만기",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A5298_001",
            "evidence_refs": ["EV:meritz:A5298_001:01"]
        }
    }

    result = EX3CompareComposer.compose(
        insurers=["samsung", "meritz"],
        coverage_code="A4200_1",
        comparison_data=comparison_data,
        coverage_name="암진단비(유사암 제외)"
    )

    # ✅ Single coverage design verified
    assert result["kind"] == "EX3_COMPARE"
    assert "암진단비" in result["title"]
    assert "비교" in result["title"]

    # ✅ NO grouping in bubble_markdown (single coverage)
    bubble = result.get("bubble_markdown", "")
    assert "**[진단 관련 담보]**" not in bubble
    assert "**[치료/수술 관련 담보]**" not in bubble


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
