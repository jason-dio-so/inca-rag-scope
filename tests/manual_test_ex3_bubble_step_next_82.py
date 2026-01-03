#!/usr/bin/env python3
"""
Manual test for EX3_COMPARE bubble_markdown enhancement (STEP NEXT-82)

Usage:
    python tests/manual_test_ex3_bubble_step_next_82.py
"""

from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer


def test_realistic_scenario():
    """Test with realistic comparison data"""
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"

    comparison_data = {
        "samsung": {
            "amount": "3000만원",
            "premium": "월 15,000원",
            "period": "20년납/80세만기",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:samsung:A4200_1:03"],
                "extraction_notes": ""
            }
        },
        "meritz": {
            "amount": "5000만원",
            "premium": "월 25,000원",
            "period": "20년납/80세만기",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:meritz:A4200_1",
            "evidence_refs": ["EV:meritz:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:meritz:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "1년 50%",
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:meritz:A4200_1:02"],
                "extraction_notes": ""
            }
        }
    }

    response = EX3CompareComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )

    print("=" * 80)
    print("EX3_COMPARE bubble_markdown (STEP NEXT-82)")
    print("=" * 80)
    print()
    print(response["bubble_markdown"])
    print()
    print("=" * 80)

    # Verify constitutional rules
    bubble = response["bubble_markdown"]

    print("\n검증 결과:")
    print(f"✓ 4개 섹션 존재: {'## 핵심 요약' in bubble and '## 한눈에 보는 결론' in bubble and '## 세부 비교 포인트' in bubble and '## 유의사항' in bubble}")
    print(f"✓ coverage_code 노출 없음: {'A4200' not in bubble}")
    print(f"✓ raw_text 없음: {'raw_text' not in bubble.lower()}")
    print(f"✓ UNKNOWN 노출 없음: {'UNKNOWN' not in bubble}")
    print(f"✓ Deterministic: {response['lineage']['deterministic']}")
    print(f"✓ NO LLM: {not response['lineage']['llm_used']}")


if __name__ == "__main__":
    test_realistic_scenario()
