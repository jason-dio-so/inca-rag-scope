#!/usr/bin/env python3
"""
STEP NEXT-87C: Generate EX2_LIMIT_FIND Response Samples for Contract Testing

Usage:
    python tests/manual_test_ex2_limit_find_samples.py
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.response_composers.ex2_limit_find_composer import EX2LimitFindComposer
from tests.test_ex2_limit_find_content_contract import validate_ex2_limit_find_contract


def scenario_1_limit_difference():
    """
    Scenario 1: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
    """
    insurers = ["samsung", "meritz"]
    coverage_code = "A4200_2"
    coverage_name = "암직접입원비"
    compare_field = "보장한도"

    comparison_data = {
        "samsung": {
            "limit_summary": "1일 1회, 최대 120일",
            "payment_type": "일당형",
            "proposal_detail_ref": "PD:samsung:A4200_2",
            "evidence_refs": ["EV:samsung:A4200_2:01", "EV:samsung:A4200_2:02"],
            "kpi_summary": {
                "payment_type": "일당형",
                "limit_summary": "1일 1회, 최대 120일",
                "kpi_evidence_refs": ["EV:samsung:A4200_2:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": ["EV:samsung:A4200_2:03"],
                "extraction_notes": ""
            }
        },
        "meritz": {
            "limit_summary": "1일 1회, 최대 60일",
            "payment_type": "일당형",
            "proposal_detail_ref": "PD:meritz:A4200_2",
            "evidence_refs": ["EV:meritz:A4200_2:01"],
            "kpi_summary": {
                "payment_type": "일당형",
                "limit_summary": "1일 1회, 최대 60일",
                "kpi_evidence_refs": ["EV:meritz:A4200_2:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": ["EV:meritz:A4200_2:02"],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def scenario_2_waiting_period_difference():
    """
    Scenario 2: "암진단비 담보 중 대기기간이 다른 보험사 찾아줘"
    """
    insurers = ["hanwha", "samsung", "kb"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"
    compare_field = "조건"

    comparison_data = {
        "hanwha": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hanwha:A4200_1",
            "evidence_refs": ["EV:hanwha:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:hanwha:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:hanwha:A4200_1:03"],
                "extraction_notes": ""
            }
        },
        "samsung": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "2년",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:samsung:A4200_1:02"],
                "extraction_notes": ""
            }
        },
        "kb": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:kb:A4200_1",
            "evidence_refs": ["EV:kb:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:kb:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:kb:A4200_1:02"],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def scenario_3_condition_difference():
    """
    Scenario 3: "암진단비 담보 조건이 다른 회사 찾아줘"
    """
    insurers = ["hanwha", "heungkuk"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"
    compare_field = "조건"

    comparison_data = {
        "hanwha": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hanwha:A4200_1",
            "evidence_refs": ["EV:hanwha:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:hanwha:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:hanwha:A4200_1:03"],
                "extraction_notes": ""
            }
        },
        "heungkuk": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:heungkuk:A4200_1",
            "evidence_refs": ["EV:heungkuk:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:heungkuk:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "1년 50%",
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:heungkuk:A4200_1:02"],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def scenario_4_limit_difference_multi():
    """
    Scenario 4: "보장한도 차이 알려줘" (3+ insurers)
    """
    insurers = ["hanwha", "samsung", "kb"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"
    compare_field = "보장한도"

    comparison_data = {
        "hanwha": {
            "limit_summary": "1회한 3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hanwha:A4200_1",
            "evidence_refs": ["EV:hanwha:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 3000만원",
                "kpi_evidence_refs": ["EV:hanwha:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": [],
                "extraction_notes": ""
            }
        },
        "samsung": {
            "limit_summary": "1회한 5000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 5000만원",
                "kpi_evidence_refs": ["EV:samsung:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": [],
                "extraction_notes": ""
            }
        },
        "kb": {
            "limit_summary": "1회한 3000만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:kb:A4200_1",
            "evidence_refs": ["EV:kb:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 3000만원",
                "kpi_evidence_refs": ["EV:kb:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": [],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def scenario_5_reduction_condition_filter():
    """
    Scenario 5: "유사암진단비에서 감액 조건이 있는 회사만"
    """
    insurers = ["hanwha", "samsung", "hyundai"]
    coverage_code = "A4210_1"
    coverage_name = "유사암진단비"
    compare_field = "조건"

    comparison_data = {
        "hanwha": {
            "limit_summary": "1회한 300만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hanwha:A4210_1",
            "evidence_refs": ["EV:hanwha:A4210_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 300만원",
                "kpi_evidence_refs": ["EV:hanwha:A4210_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "1년 50%",
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": ["EV:hanwha:A4210_1:02"],
                "extraction_notes": ""
            }
        },
        "samsung": {
            "limit_summary": "1회한 300만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:samsung:A4210_1",
            "evidence_refs": ["EV:samsung:A4210_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 300만원",
                "kpi_evidence_refs": ["EV:samsung:A4210_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": ["EV:samsung:A4210_1:02"],
                "extraction_notes": ""
            }
        },
        "hyundai": {
            "limit_summary": "1회한 300만원",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hyundai:A4210_1",
            "evidence_refs": ["EV:hyundai:A4210_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 300만원",
                "kpi_evidence_refs": ["EV:hyundai:A4210_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": "2년 50%",
                "exclusion_condition": None,
                "renewal_type": None,
                "condition_evidence_refs": ["EV:hyundai:A4210_1:02"],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def scenario_6_waiver_condition_difference():
    """
    Scenario 6: "납입면제 조건이 다른 회사 찾아줘"

    Note: This is hypothetical as we don't have waiver coverage in our current scope.
    Using a general "조건" comparison for demonstration.
    """
    insurers = ["hanwha", "lotte"]
    coverage_code = "A4200_1"
    coverage_name = "암진단비(유사암 제외)"
    compare_field = "조건"

    comparison_data = {
        "hanwha": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:hanwha:A4200_1",
            "evidence_refs": ["EV:hanwha:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:hanwha:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "90일",
                "reduction_condition": None,
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:hanwha:A4200_1:03"],
                "extraction_notes": ""
            }
        },
        "lotte": {
            "limit_summary": "1회한 지급",
            "payment_type": "정액형",
            "proposal_detail_ref": "PD:lotte:A4200_1",
            "evidence_refs": ["EV:lotte:A4200_1:01"],
            "kpi_summary": {
                "payment_type": "정액형",
                "limit_summary": "1회한 지급",
                "kpi_evidence_refs": ["EV:lotte:A4200_1:01"],
                "extraction_notes": ""
            },
            "kpi_condition": {
                "waiting_period": "2년",
                "reduction_condition": "1년 20%",
                "exclusion_condition": "유사암 제외",
                "renewal_type": None,
                "condition_evidence_refs": ["EV:lotte:A4200_1:02"],
                "extraction_notes": ""
            }
        }
    }

    return EX2LimitFindComposer.compose(
        insurers=insurers,
        coverage_code=coverage_code,
        compare_field=compare_field,
        comparison_data=comparison_data,
        coverage_name=coverage_name
    )


def main():
    """Generate all 6 scenario responses and validate contracts"""

    print("=" * 80)
    print("STEP NEXT-87C: EX2_LIMIT_FIND Contract Validation")
    print("=" * 80)
    print()

    scenarios = [
        ("scenario_1", "보장한도가 다른 상품", scenario_1_limit_difference),
        ("scenario_2", "대기기간이 다른 보험사", scenario_2_waiting_period_difference),
        ("scenario_3", "조건이 다른 회사", scenario_3_condition_difference),
        ("scenario_4", "보장한도 차이 (3사)", scenario_4_limit_difference_multi),
        ("scenario_5", "감액 조건 필터", scenario_5_reduction_condition_filter),
        ("scenario_6", "납입면제 조건 차이", scenario_6_waiver_condition_difference),
    ]

    results = {}
    all_passed = True

    for scenario_id, description, scenario_func in scenarios:
        print(f"\n[{scenario_id}] {description}")
        print("-" * 80)

        # Generate response
        response = scenario_func()

        # Validate contract
        validation_result = validate_ex2_limit_find_contract(response)

        # Store result
        results[scenario_id] = {
            "description": description,
            "response": response,
            "validation": validation_result
        }

        # Print validation result
        if validation_result["passed"]:
            print("✅ PASS: Contract validation succeeded")
        else:
            print("❌ FAIL: Contract violations detected")
            all_passed = False

            violations = validation_result["violations"]
            if violations["forbidden_words"]:
                print(f"   - Forbidden words: {violations['forbidden_words'][:3]}")
            if violations["coverage_code_exposure"]:
                print(f"   - Coverage code exposure: {violations['coverage_code_exposure'][:3]}")
            if violations["ex4_contamination"]:
                print(f"   - EX4 contamination detected")
            if violations["ex3_contamination"]:
                print(f"   - EX3 contamination detected")

        # Print sample output
        print(f"\nTitle: {response['title']}")
        print(f"Summary: {response['summary_bullets']}")

    # Save samples to file
    output_path = Path(__file__).parent / "ex2_limit_find_samples.json"
    with open(output_path, "w", encoding="utf-8") as f:
        # Convert for JSON serialization (remove validation function results)
        serializable_results = {}
        for scenario_id, data in results.items():
            serializable_results[scenario_id] = {
                "description": data["description"],
                "response": data["response"],
                "validation_passed": data["validation"]["passed"],
                "violations": data["validation"]["violations"]
            }
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Samples saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for scenario_id, data in results.items():
        status = "✅ PASS" if data["validation"]["passed"] else "❌ FAIL"
        print(f"{status} {scenario_id}: {data['description']}")

    print()
    if all_passed:
        print("🎉 All scenarios PASSED contract validation")
    else:
        print("⚠️  Some scenarios FAILED - review violations above")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
