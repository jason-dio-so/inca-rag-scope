#!/usr/bin/env python3
"""
Manual test for EX4_ELIGIBILITY bubble_markdown enhancement (STEP NEXT-83)

Usage:
    PYTHONPATH=. python tests/manual_test_ex4_bubble_step_next_83.py
"""

from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer


def test_realistic_scenario():
    """Test with realistic eligibility data"""
    insurers = ["samsung", "meritz", "hanwha"]
    subtype_keyword = "제자리암"
    coverage_name = "암진단비(유사암 제외)"
    coverage_code = "A4200_1"

    eligibility_data = [
        {
            "insurer": "samsung",
            "status": "O",
            "evidence_type": "정의",
            "evidence_snippet": "제자리암: 암세포가 발생한 조직 또는 장기에 국한되어 있는 경우",
            "evidence_ref": "약관 p.12"
        },
        {
            "insurer": "meritz",
            "status": "X",
            "evidence_type": "면책",
            "evidence_snippet": "제자리암은 보장하지 않습니다",
            "evidence_ref": "약관 p.15"
        },
        {
            "insurer": "hanwha",
            "status": "△",
            "evidence_type": "감액",
            "evidence_snippet": "제자리암 진단 시 보장금액의 50% 지급",
            "evidence_ref": "약관 p.18"
        }
    ]

    response = EX4EligibilityComposer.compose(
        insurers=insurers,
        subtype_keyword=subtype_keyword,
        eligibility_data=eligibility_data,
        coverage_name=coverage_name,
        coverage_code=coverage_code
    )

    print("=" * 80)
    print("EX4_ELIGIBILITY bubble_markdown (STEP NEXT-83)")
    print("=" * 80)
    print()
    print(response["bubble_markdown"])
    print()
    print("=" * 80)

    # Verify constitutional rules
    bubble = response["bubble_markdown"]

    print("\n검증 결과:")
    print(f"✓ 4개 섹션 존재: {'## 핵심 요약' in bubble and '## 한눈에 보는 결론' in bubble and '## 보험사별 판단 요약' in bubble and '## 유의사항' in bubble}")
    print(f"✓ coverage_code 노출 없음: {'A4200' not in bubble}")
    print(f"✓ raw_text 없음: {'raw_text' not in bubble.lower()}")
    print(f"✓ evidence_snippet 없음: {'evidence_snippet' not in bubble.lower()}")
    print(f"✓ Deterministic: {response['lineage']['deterministic']}")
    print(f"✓ NO LLM: {not response['lineage']['llm_used']}")
    print(f"✓ NO emojis in conclusion: {bubble[bubble.find('## 한눈에 보는 결론'):bubble.find('## 보험사별 판단 요약')].count('✅') == 0}")


if __name__ == "__main__":
    test_realistic_scenario()
