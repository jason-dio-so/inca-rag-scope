#!/usr/bin/env python3
"""
STEP NEXT-O: Premium SSOT Validation Script
보험료 SSOT 검증 (무해지/일반 계산, 배수 누락 케이스)

Usage:
    python3 tools/audit/validate_premium_ssot.py --input data/premium_quotes.jsonl

Rules:
1. NO_REFUND 값은 API 원본과 일치
2. GENERAL = round(NO_REFUND × (multiplier_percent / 100))
3. 배수 없으면 GENERAL 레코드 없음
4. 계산 오차 = ZERO (100% 재현 가능)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.premium_ssot.multiplier_loader import (
    load_multiplier_excel,
    get_multiplier,
    calculate_general_premium
)


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def validate_premium_quotes(
    quotes: List[Dict[str, Any]],
    multipliers: List[Dict[str, Any]],
    coverage_name: str = "전체"
) -> Dict[str, Any]:
    """
    Validate premium_quote records

    Args:
        quotes: premium_quote 레코드
        multipliers: 배수 데이터
        coverage_name: 배수 조회용 담보명

    Returns:
        Dict: 검증 결과
            {
                "total_records": int,
                "no_refund_count": int,
                "general_count": int,
                "validation_errors": List[str],
                "calculation_mismatches": List[Dict],
                "missing_multiplier_cases": List[Dict],
                "summary": str
            }
    """
    total_records = len(quotes)
    no_refund_records = [q for q in quotes if q["plan_variant"] == "NO_REFUND"]
    general_records = [q for q in quotes if q["plan_variant"] == "GENERAL"]

    validation_errors = []
    calculation_mismatches = []
    missing_multiplier_cases = []

    # Group by (insurer_key, product_id, age, sex, smoke, pay_term, ins_term)
    grouped = defaultdict(lambda: {"NO_REFUND": None, "GENERAL": None})

    for quote in quotes:
        key = (
            quote["insurer_key"],
            quote["product_id"],
            quote["age"],
            quote["sex"],
            quote["smoke"],
            quote["pay_term_years"],
            quote["ins_term_years"]
        )
        variant = quote["plan_variant"]
        grouped[key][variant] = quote

    # Validate each group
    for key, variants in grouped.items():
        insurer_key, product_id, age, sex, smoke, pay_term, ins_term = key

        no_refund = variants["NO_REFUND"]
        general = variants["GENERAL"]

        if no_refund is None:
            validation_errors.append(
                f"Missing NO_REFUND record: insurer={insurer_key}, "
                f"product={product_id}, age={age}, sex={sex}"
            )
            continue

        # Check constraints
        if no_refund["premium_monthly"] <= 0:
            validation_errors.append(
                f"Invalid NO_REFUND monthly premium: {no_refund['premium_monthly']}"
            )

        if no_refund["premium_total"] <= 0:
            validation_errors.append(
                f"Invalid NO_REFUND total premium: {no_refund['premium_total']}"
            )

        # Get multiplier
        multiplier_percent = get_multiplier(insurer_key, coverage_name, multipliers)

        if multiplier_percent is None:
            # 배수 없음 → GENERAL 없어야 함
            if general is not None:
                validation_errors.append(
                    f"GENERAL record exists but no multiplier: insurer={insurer_key}, "
                    f"coverage={coverage_name}"
                )
            else:
                missing_multiplier_cases.append({
                    "insurer_key": insurer_key,
                    "coverage_name": coverage_name,
                    "note": "No multiplier → GENERAL not created (CORRECT)"
                })
        else:
            # 배수 있음 → GENERAL 계산 검증
            expected_monthly = calculate_general_premium(
                no_refund["premium_monthly"], multiplier_percent
            )
            expected_total = calculate_general_premium(
                no_refund["premium_total"], multiplier_percent
            )

            if general is None:
                validation_errors.append(
                    f"Missing GENERAL record: insurer={insurer_key}, "
                    f"product={product_id}, age={age}, sex={sex}, "
                    f"multiplier={multiplier_percent}"
                )
            else:
                # Validate calculation
                if general["premium_monthly"] != expected_monthly:
                    calculation_mismatches.append({
                        "insurer_key": insurer_key,
                        "product_id": product_id,
                        "age": age,
                        "sex": sex,
                        "field": "premium_monthly",
                        "actual": general["premium_monthly"],
                        "expected": expected_monthly,
                        "no_refund": no_refund["premium_monthly"],
                        "multiplier": multiplier_percent
                    })

                if general["premium_total"] != expected_total:
                    calculation_mismatches.append({
                        "insurer_key": insurer_key,
                        "product_id": product_id,
                        "age": age,
                        "sex": sex,
                        "field": "premium_total",
                        "actual": general["premium_total"],
                        "expected": expected_total,
                        "no_refund": no_refund["premium_total"],
                        "multiplier": multiplier_percent
                    })

    # Summary
    success = len(validation_errors) == 0 and len(calculation_mismatches) == 0

    summary = f"""
=== Premium SSOT Validation ===
Total records: {total_records}
NO_REFUND records: {len(no_refund_records)}
GENERAL records: {len(general_records)}

Validation errors: {len(validation_errors)}
Calculation mismatches: {len(calculation_mismatches)}
Missing multiplier cases: {len(missing_multiplier_cases)}

Status: {'✅ PASS' if success else '❌ FAIL'}
"""

    return {
        "total_records": total_records,
        "no_refund_count": len(no_refund_records),
        "general_count": len(general_records),
        "validation_errors": validation_errors,
        "calculation_mismatches": calculation_mismatches,
        "missing_multiplier_cases": missing_multiplier_cases,
        "summary": summary,
        "success": success
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate premium_quote SSOT records"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to premium_quote JSONL file"
    )
    parser.add_argument(
        "--multiplier-excel",
        default="/Users/cheollee/inca-rag-scope/data/sources/insurers/4. 일반보험요율예시.xlsx",
        help="Path to multiplier Excel file"
    )
    parser.add_argument(
        "--coverage-name",
        default="전체",
        help="Coverage name for multiplier lookup"
    )
    parser.add_argument(
        "--output",
        help="Path to output validation report (JSON)"
    )

    args = parser.parse_args()

    # Validate inputs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    multiplier_path = Path(args.multiplier_excel)
    if not multiplier_path.exists():
        print(f"❌ Multiplier Excel not found: {args.multiplier_excel}", file=sys.stderr)
        sys.exit(2)

    print(f"Loading premium quotes: {args.input}")
    quotes = load_jsonl(args.input)
    print(f"Loaded {len(quotes)} records")

    print(f"Loading multipliers: {args.multiplier_excel}")
    multipliers = load_multiplier_excel(args.multiplier_excel)
    print(f"Loaded {len(multipliers)} multiplier records")

    print(f"Validating with coverage_name='{args.coverage_name}'...")
    result = validate_premium_quotes(quotes, multipliers, args.coverage_name)

    # Print summary
    print(result["summary"])

    # Print errors
    if result["validation_errors"]:
        print("\n=== Validation Errors ===")
        for error in result["validation_errors"]:
            print(f"  ❌ {error}")

    if result["calculation_mismatches"]:
        print("\n=== Calculation Mismatches ===")
        for mismatch in result["calculation_mismatches"]:
            print(f"  ❌ {mismatch}")

    if result["missing_multiplier_cases"]:
        print(f"\n=== Missing Multiplier Cases ({len(result['missing_multiplier_cases'])}) ===")
        for case in result["missing_multiplier_cases"][:5]:
            print(f"  ℹ️  {case}")
        if len(result["missing_multiplier_cases"]) > 5:
            print(f"  ... and {len(result['missing_multiplier_cases']) - 5} more")

    # Save output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nValidation report saved: {args.output}")

    # Exit code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
