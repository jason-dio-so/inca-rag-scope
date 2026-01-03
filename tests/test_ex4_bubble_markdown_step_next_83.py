#!/usr/bin/env python3
"""
Test EX4_ELIGIBILITY bubble_markdown enhancement (STEP NEXT-83)

Constitutional Rules:
- ❌ NO coverage_code exposure
- ❌ NO raw_text in bubble
- ❌ NO LLM usage
- ❌ NO scoring/weighting/inference
- ✅ MUST have 4 sections (핵심 요약, 한눈에 보는 결론, 보험사별 판단 요약, 유의사항)
- ✅ Deterministic only
- ✅ Natural language decision summary (NO emojis in conclusion)
"""

import pytest
from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


def test_bubble_markdown_has_four_sections():
    """Verify bubble_markdown has exactly 4 required sections"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "...", "evidence_ref": "약관 p.12"},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "...", "evidence_ref": "약관 p.15"},
        {"insurer": "hanwha", "status": "△", "evidence_type": "감액", "evidence_snippet": "...", "evidence_ref": "약관 p.18"}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]

    # Must have 4 sections
    assert "## 핵심 요약" in bubble
    assert "## 한눈에 보는 결론" in bubble
    assert "## 보험사별 판단 요약" in bubble
    assert "## 유의사항" in bubble


def test_bubble_markdown_no_coverage_code():
    """Verify NO coverage_code exposure in bubble_markdown"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "제자리암"
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data,
        coverage_name=coverage_name,
        coverage_code=coverage_code
    )

    bubble = response["bubble_markdown"]

    # NO coverage_code patterns
    assert "A4200_1" not in bubble
    assert "A4200" not in bubble
    import re
    code_pattern = r"A\d{4}_\d"
    assert not re.search(code_pattern, bubble), "coverage_code detected in bubble_markdown"


def test_bubble_markdown_section1_summary():
    """Verify Section 1: 핵심 요약 contains required context"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "hanwha", "status": "△", "evidence_type": "감액", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section1_start = bubble.find("## 핵심 요약")
    section1_end = bubble.find("## 한눈에 보는 결론")
    section1 = bubble[section1_start:section1_end]

    # Must contain
    assert "3개 보험사" in section1
    assert "제자리암" in section1
    assert "가입설계서 및 약관 기준" in section1


def test_bubble_markdown_section2_conclusion_recommend():
    """Verify Section 2: 한눈에 보는 결론 for RECOMMEND decision"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": "약관 p.1"},
        {"insurer": "meritz", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": "약관 p.2"},
        {"insurer": "hanwha", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": "약관 p.3"}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 보험사별 판단 요약")
    section2 = bubble[section2_start:section2_end]

    # Should show RECOMMEND conclusion
    assert "보장 가능한 보험사가 다수입니다" in section2


def test_bubble_markdown_section2_conclusion_not_recommend():
    """Verify Section 2: 한눈에 보는 결론 for NOT_RECOMMEND decision"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "유사암"

    eligibility_data = [
        {"insurer": "samsung", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": "약관 p.1"},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": "약관 p.2"},
        {"insurer": "hanwha", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": "약관 p.3"}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 보험사별 판단 요약")
    section2 = bubble[section2_start:section2_end]

    # Should show NOT_RECOMMEND conclusion
    assert "보장되지 않는 보험사가 다수입니다" in section2


def test_bubble_markdown_section2_conclusion_neutral():
    """Verify Section 2: 한눈에 보는 결론 for NEUTRAL decision"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "경계성종양"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": "약관 p.1"},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": "약관 p.2"}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 보험사별 판단 요약")
    section2 = bubble[section2_start:section2_end]

    # Should show NEUTRAL conclusion
    assert "보험사별 보장 여부가 갈립니다" in section2


def test_bubble_markdown_section3_insurer_grouping():
    """Verify Section 3: 보험사별 판단 요약 groups insurers by status"""
    insurers = ["samsung", "meritz", "hanwha", "kb"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "hanwha", "status": "△", "evidence_type": "감액", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "kb", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section3_start = bubble.find("## 보험사별 판단 요약")
    section3_end = bubble.find("## 유의사항")
    section3 = bubble[section3_start:section3_end]

    # Must group by status
    assert "보장 가능" in section3
    assert "samsung, meritz" in section3 or ("samsung" in section3 and "meritz" in section3)
    assert "감액 조건 존재" in section3
    assert "hanwha" in section3
    assert "보장 제외" in section3
    assert "kb" in section3


def test_bubble_markdown_section4_caution():
    """Verify Section 4: 유의사항 has required disclaimers"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section4_start = bubble.find("## 유의사항")
    section4 = bubble[section4_start:]

    # Must contain
    assert "본 결과는 가입설계서 기준 요약" in section4
    assert "세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다" in section4


def test_bubble_markdown_no_emojis_in_conclusion():
    """Verify NO emojis in conclusion section (customer-friendly text only)"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section2_start = bubble.find("## 한눈에 보는 결론")
    section2_end = bubble.find("## 보험사별 판단 요약")
    section2 = bubble[section2_start:section2_end]

    # NO emojis in conclusion text (✅, ❌, ⚠️)
    # Note: Emojis may appear in Section 3 (insurer grouping) as labels, but NOT in conclusion
    assert "✅" not in section2 or section2.count("✅") == 0
    assert "❌" not in section2 or section2.count("❌") == 0


def test_bubble_markdown_no_llm_no_raw_text():
    """Verify bubble_markdown uses deterministic logic only (NO LLM, NO raw_text)"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "제자리암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]

    # NO raw_text patterns
    assert "raw_text" not in bubble.lower()
    assert "evidence_snippet" not in bubble.lower()

    # NO inference traces
    assert "추정" not in bubble
    assert "좋아 보임" not in bubble
    assert "합리적" not in bubble

    # Lineage should confirm deterministic
    assert response["lineage"]["deterministic"] is True
    assert response["lineage"]["llm_used"] is False


def test_bubble_markdown_with_coverage_name():
    """Verify bubble_markdown includes coverage_name context when provided"""
    insurers = ["samsung", "meritz"]
    subtype_keyword = "제자리암"
    coverage_name = "암진단비(유사암 제외)"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "X", "evidence_type": "면책", "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data,
        coverage_name=coverage_name
    )

    bubble = response["bubble_markdown"]
    section1_start = bubble.find("## 핵심 요약")
    section1_end = bubble.find("## 한눈에 보는 결론")
    section1 = bubble[section1_start:section1_end]

    # Should include coverage name
    assert "암진단비(유사암 제외)" in section1 or "암진단비" in section1


def test_bubble_markdown_unknown_status_handling():
    """Verify bubble_markdown handles Unknown status correctly"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "갑상선암"

    eligibility_data = [
        {"insurer": "samsung", "status": "O", "evidence_type": "정의", "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "meritz", "status": "Unknown", "evidence_type": None, "evidence_snippet": "", "evidence_ref": ""},
        {"insurer": "hanwha", "status": "Unknown", "evidence_type": None, "evidence_snippet": "", "evidence_ref": ""}
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data
    )

    bubble = response["bubble_markdown"]
    section3_start = bubble.find("## 보험사별 판단 요약")
    section3_end = bubble.find("## 유의사항")
    section3 = bubble[section3_start:section3_end]

    # Should show Unknown insurers
    assert "판단 근거 없음" in section3
    assert "meritz" in section3
    assert "hanwha" in section3
