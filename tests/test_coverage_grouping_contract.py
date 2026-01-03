#!/usr/bin/env python3
"""
STEP NEXT-94: Coverage Grouping Contract Tests

CONSTITUTIONAL RULES:
- ❌ Group label MUST NOT affect judgment/comparison results
- ❌ Group label MUST NOT affect decision (RECOMMEND/NOT_RECOMMEND/NEUTRAL)
- ❌ Group label MUST NOT affect status (O/X/△/Unknown)
- ✅ Group label is VIEW-ONLY (display text for UI sections)
- ✅ Same input → same output (regardless of grouping on/off)

TEST STRATEGY:
1. Test assign_coverage_group utility (deterministic)
2. Test EX4_ELIGIBILITY bubble_markdown grouping (no judgment change)
3. Test grouping with single/multiple groups
"""

import pytest
from apps.api.response_composers.utils import assign_coverage_group
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


# ============================================================================
# Test 1: assign_coverage_group (Deterministic)
# ============================================================================

def test_assign_coverage_group_diagnosis():
    """진단 관련 담보: DIAGNOSIS trigger"""
    assert assign_coverage_group("암진단비", "DIAGNOSIS") == "진단 관련 담보"
    assert assign_coverage_group("제자리암진단비", "DIAGNOSIS") == "진단 관련 담보"


def test_assign_coverage_group_diagnosis_by_name():
    """진단 관련 담보: Inferred from name (no trigger)"""
    assert assign_coverage_group("암진단비", None) == "진단 관련 담보"
    assert assign_coverage_group("제자리암진단비", None) == "진단 관련 담보"
    assert assign_coverage_group("유사암진단급여금", None) == "진단 관련 담보"


def test_assign_coverage_group_surgery():
    """치료/수술 관련 담보: SURGERY trigger"""
    assert assign_coverage_group("유사암수술비", "SURGERY") == "치료/수술 관련 담보"
    assert assign_coverage_group("암수술비", "SURGERY") == "치료/수술 관련 담보"


def test_assign_coverage_group_treatment():
    """치료/수술 관련 담보: TREATMENT trigger"""
    assert assign_coverage_group("암치료비", "TREATMENT") == "치료/수술 관련 담보"
    assert assign_coverage_group("항암치료비", "TREATMENT") == "치료/수술 관련 담보"


def test_assign_coverage_group_treatment_by_name():
    """치료/수술 관련 담보: Inferred from name (no trigger)"""
    assert assign_coverage_group("유사암수술비", None) == "치료/수술 관련 담보"
    assert assign_coverage_group("암입원비", None) == "치료/수술 관련 담보"
    assert assign_coverage_group("항암방사선치료비", None) == "치료/수술 관련 담보"


def test_assign_coverage_group_fallback():
    """기타 담보: Fallback for unrecognized patterns"""
    assert assign_coverage_group("상해사망급여금", None) == "기타 담보"
    assert assign_coverage_group("장해급여금", None) == "기타 담보"
    assert assign_coverage_group("알수없는담보", None) == "기타 담보"


def test_assign_coverage_group_name_priority():
    """Name keyword takes priority over trigger when name is explicit"""
    # Even if trigger is SURGERY, if name contains "진단비", it's 진단 group
    assert assign_coverage_group("암진단비", "SURGERY") == "진단 관련 담보"
    # Even if trigger is DIAGNOSIS, if name contains "수술비", it's 치료/수술 group
    assert assign_coverage_group("암수술비", "DIAGNOSIS") == "치료/수술 관련 담보"


def test_assign_coverage_group_edge_cases():
    """Edge cases: empty name, MIXED trigger"""
    assert assign_coverage_group("", None) == "기타 담보"
    assert assign_coverage_group("암진단비", "MIXED") == "진단 관련 담보"  # Name takes priority


# ============================================================================
# Test 2: EX4_ELIGIBILITY Grouping Contract (NO JUDGMENT CHANGE)
# ============================================================================

def test_ex4_bubble_markdown_grouping_single_group():
    """Single group: No group header should appear"""
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
            "evidence_snippet": "1년 미만 50% 감액",
            "evidence_ref": "PD:meritz:A5298_001",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "제자리암진단비",
            "proposal_detail_ref": "PD:meritz:A5298_001"
        }
    ]

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section={
            "overall_evaluation": {
                "decision": "RECOMMEND",
                "summary": "보장 가능(O) 항목이 다수입니다"
            }
        }
    )

    # Single group (모두 진단 관련 담보) → group header 없음
    assert "**[진단 관련 담보]**" not in bubble
    assert "**samsung**: ○" in bubble
    assert "**meritz**: △" in bubble


def test_ex4_bubble_markdown_grouping_multiple_groups():
    """Multiple groups: Group headers should appear"""
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
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "유사암 수술 시 지급",
            "evidence_ref": "PD:meritz:A5299",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "유사암수술비",
            "proposal_detail_ref": "PD:meritz:A5299"
        }
    ]

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section={
            "overall_evaluation": {
                "decision": "RECOMMEND",
                "summary": "보장 가능(O) 항목이 다수입니다"
            }
        }
    )

    # Multiple groups (진단 + 치료/수술) → group headers 표시
    assert "**[진단 관련 담보]**" in bubble
    assert "**[치료/수술 관련 담보]**" in bubble
    assert "**samsung**: ○" in bubble
    assert "**meritz**: ○" in bubble


def test_ex4_bubble_markdown_grouping_no_decision_change():
    """Grouping MUST NOT change decision/summary"""
    # Test data with multiple groups
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "...",
            "evidence_ref": "PD:samsung:A4210",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4210"
        },
        {
            "insurer": "meritz",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "...",
            "evidence_ref": "PD:meritz:A5298",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:meritz:A5298"
        }
    ]

    evaluation_section = {
        "overall_evaluation": {
            "decision": "NEUTRAL",
            "summary": "보장 상태가 혼재되어 우열 판단 불가"
        }
    }

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section=evaluation_section
    )

    # Decision/summary MUST be preserved (from evaluation_section)
    assert "보험사별 보장 여부가 갈립니다" in bubble  # Translated decision
    assert "보장 상태가 혼재되어 우열 판단 불가" in bubble  # Original summary


def test_ex4_bubble_markdown_grouping_status_preserved():
    """Grouping MUST preserve status icons (O/△/X/?)"""
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "...",
            "evidence_ref": "PD:samsung:A4210",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4210"
        },
        {
            "insurer": "meritz",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "...",
            "evidence_ref": "PD:meritz:A5298",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "암수술비",
            "proposal_detail_ref": "PD:meritz:A5298"
        },
        {
            "insurer": "kb",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "...",
            "evidence_ref": "PD:kb:B1100",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:kb:B1100"
        },
        {
            "insurer": "hanwha",
            "status": "Unknown",
            "evidence_type": None,
            "evidence_snippet": None,
            "evidence_ref": None,
            "coverage_trigger": None,
            "coverage_name_raw": "기타담보",
            "proposal_detail_ref": None
        }
    ]

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section={
            "overall_evaluation": {
                "decision": "NEUTRAL",
                "summary": "장단점 혼재로 우열 판단이 어렵습니다"
            }
        }
    )

    # All status icons MUST be preserved
    assert "**samsung**: ○" in bubble
    assert "**meritz**: △" in bubble
    assert "**kb**: ✕" in bubble
    assert "**hanwha**: ?" in bubble


def test_ex4_bubble_markdown_no_coverage_code_exposure():
    """Grouping MUST NOT expose coverage_code (constitutional rule)"""
    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "...",
            "evidence_ref": "PD:samsung:A4200_1",  # Code in ref (OK)
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4200_1"
        }
    ]

    bubble = EX4EligibilityComposer._build_bubble_markdown(
        subtype_keyword="제자리암",
        eligibility_data=eligibility_data,
        evaluation_section={
            "overall_evaluation": {
                "decision": "RECOMMEND",
                "summary": "보장 가능(O) 항목이 다수입니다"
            }
        },
        coverage_display_name="암진단비(유사암 제외)"
    )

    # ❌ NO bare coverage_code (A4200_1) outside of refs
    assert "A4200_1" not in bubble or "PD:samsung:A4200_1" in bubble
    # ✅ Coverage name is safe
    assert "암진단비" in bubble or "제자리암" in bubble


# ============================================================================
# Test 3: Grouping Does NOT Affect Comparison Logic
# ============================================================================

def test_grouping_does_not_affect_evaluation():
    """Coverage group label MUST NOT affect overall_evaluation decision"""
    # Same eligibility data, different coverage groups → same decision
    eligibility_data_diagnosis = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "...",
            "evidence_ref": "PD:samsung:A4210",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:samsung:A4210"
        },
        {
            "insurer": "meritz",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "...",
            "evidence_ref": "PD:meritz:A5298",
            "coverage_trigger": "DIAGNOSIS",
            "coverage_name_raw": "암진단비",
            "proposal_detail_ref": "PD:meritz:A5298"
        }
    ]

    eligibility_data_surgery = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "...",
            "evidence_ref": "PD:samsung:A4211",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "암수술비",
            "proposal_detail_ref": "PD:samsung:A4211"
        },
        {
            "insurer": "meritz",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "...",
            "evidence_ref": "PD:meritz:A5299",
            "coverage_trigger": "SURGERY",
            "coverage_name_raw": "암수술비",
            "proposal_detail_ref": "PD:meritz:A5299"
        }
    ]

    # Both should have NEUTRAL decision (O vs X)
    eval1 = EX4EligibilityComposer._build_overall_evaluation(
        eligibility_data_diagnosis, ["제자리암"]
    )
    eval2 = EX4EligibilityComposer._build_overall_evaluation(
        eligibility_data_surgery, ["제자리암"]
    )

    # Decision MUST be same (coverage group is view-only)
    assert eval1["overall_evaluation"]["decision"] == eval2["overall_evaluation"]["decision"]
    # Both should be NEUTRAL (O=1, X=1)
    assert eval1["overall_evaluation"]["decision"] == "NEUTRAL"
    assert eval2["overall_evaluation"]["decision"] == "NEUTRAL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
