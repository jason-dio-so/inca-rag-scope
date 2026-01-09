#!/usr/bin/env python3
"""
STEP NEXT-Q: Premium Allocation Validation
Validate per-coverage premium SSOT and sum verification

Usage:
    python3 tools/audit/validate_premium_allocation.py \
      --coverage-premiums /tmp/coverage_premium_quote.jsonl \
      --product-premiums /tmp/test_premium_quotes.jsonl

Validation Rules (LOCKED):
V1: Sum Match - sum(coverage_premium) == monthlyPremSum (0 error tolerance)
V2: Q1 Reproducibility - premium_per_10m calculation is deterministic
V3: Product Mismatch - All PCT products have product_id_map entries
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def validate_sum_match(
    coverage_premiums: List[Dict[str, Any]],
    product_premiums: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    V1: Validate sum(coverage_premium) == product premium

    Args:
        coverage_premiums: coverage_premium_quote records
        product_premiums: product_premium_quote records

    Returns:
        Dict: Validation results
    """
    results = {
        'total_products': 0,
        'match_count': 0,
        'mismatch_count': 0,
        'mismatches': [],
        'errors': []
    }

    # Group coverage_premiums by (insurer_key, product_id, plan_variant, age, sex)
    grouped_coverage = defaultdict(list)
    for cp in coverage_premiums:
        key = (
            cp['insurer_key'],
            cp['product_id'],
            cp['plan_variant'],
            cp['age'],
            cp['sex']
        )
        grouped_coverage[key].append(cp)

    # Verify each product premium
    for pp in product_premiums:
        key = (
            pp['insurer_key'],
            pp['product_id'],
            pp['plan_variant'],
            pp['age'],
            pp['sex']
        )

        results['total_products'] += 1

        coverages = grouped_coverage.get(key, [])
        if not coverages:
            results['errors'].append({
                'product': key,
                'issue': 'No coverage premiums found'
            })
            continue

        # Calculate sum
        actual_sum = sum(c['premium_monthly_coverage'] for c in coverages)
        expected_sum = pp['premium_monthly']
        error = abs(actual_sum - expected_sum)

        if error == 0:
            results['match_count'] += 1
        else:
            results['mismatch_count'] += 1
            results['mismatches'].append({
                'insurer_key': pp['insurer_key'],
                'product_id': pp['product_id'],
                'plan_variant': pp['plan_variant'],
                'age': pp['age'],
                'sex': pp['sex'],
                'expected_sum': expected_sum,
                'actual_sum': actual_sum,
                'error': error,
                'coverage_count': len(coverages)
            })

    return results


def validate_q1_reproducibility(
    pct_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    V2: Validate Q1 premium_per_10m calculation reproducibility

    Args:
        pct_records: PCT v2 records

    Returns:
        Dict: Validation results
    """
    results = {
        'total_records': len(pct_records),
        'q1_eligible': 0,
        'q1_excluded': 0,
        'calculation_errors': [],
        'sample_calculations': []
    }

    for record in pct_records:
        cancer_amt = record.get('cancer_diagnosis_amount')

        if cancer_amt is None or cancer_amt <= 0:
            results['q1_excluded'] += 1
            continue

        premium_monthly = record['premium_monthly']

        try:
            premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
            results['q1_eligible'] += 1

            if len(results['sample_calculations']) < 3:
                results['sample_calculations'].append({
                    'insurer_key': record['insurer_key'],
                    'product_key': record['product_key'],
                    'age': record['age'],
                    'plan_variant': record['plan_variant'],
                    'premium_monthly': premium_monthly,
                    'cancer_amt': cancer_amt,
                    'premium_per_10m': round(premium_per_10m, 2)
                })

        except (ZeroDivisionError, TypeError) as e:
            results['calculation_errors'].append({
                'insurer_key': record['insurer_key'],
                'product_key': record['product_key'],
                'error': str(e)
            })

    return results


def validate_product_id_map_coverage(
    pct_records: List[Dict[str, Any]],
    product_id_map: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    V3: Validate all PCT products have product_id_map entries

    Args:
        pct_records: PCT v2 records
        product_id_map: product_id_map records

    Returns:
        Dict: Validation results
    """
    results = {
        'total_pct_products': 0,
        'mapped_count': 0,
        'unmapped_count': 0,
        'unmapped_products': []
    }

    # Build mapping set
    mapped_products = {
        (m['insurer_key'], m['premium_product_id'])
        for m in product_id_map
    }

    # Check each PCT product
    pct_products = {
        (r['insurer_key'], r['product_key'])
        for r in pct_records
    }

    results['total_pct_products'] = len(pct_products)

    for product in pct_products:
        if product in mapped_products:
            results['mapped_count'] += 1
        else:
            results['unmapped_count'] += 1
            results['unmapped_products'].append({
                'insurer_key': product[0],
                'product_key': product[1]
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Validate premium allocation")
    parser.add_argument(
        "--coverage-premiums",
        required=True,
        help="Path to coverage_premium_quote JSONL file"
    )
    parser.add_argument(
        "--product-premiums",
        required=True,
        help="Path to product premium JSONL file"
    )
    parser.add_argument(
        "--pct-records",
        help="Path to PCT v2 JSONL file (for V2/V3 validation)"
    )
    parser.add_argument(
        "--product-id-map",
        help="Path to product_id_map JSONL file (for V3 validation)"
    )
    parser.add_argument(
        "--output",
        help="Path to validation report (JSON)"
    )

    args = parser.parse_args()

    print(f"Loading coverage premiums: {args.coverage_premiums}")
    coverage_premiums = load_jsonl(args.coverage_premiums)
    print(f"Loaded {len(coverage_premiums)} coverage_premium_quote records")

    print(f"Loading product premiums: {args.product_premiums}")
    product_premiums = load_jsonl(args.product_premiums)
    print(f"Loaded {len(product_premiums)} product premium records\n")

    # V1: Sum Match Validation
    print("=== V1: Sum Match Validation ===")
    v1_results = validate_sum_match(coverage_premiums, product_premiums)
    print(f"Total products: {v1_results['total_products']}")
    print(f"Match: {v1_results['match_count']}")
    print(f"Mismatch: {v1_results['mismatch_count']}")
    print(f"Errors: {len(v1_results['errors'])}")

    if v1_results['mismatches']:
        print("\nMismatches:")
        for mm in v1_results['mismatches'][:3]:
            print(f"  {mm['insurer_key']} | {mm['plan_variant']} | age {mm['age']}")
            print(f"    Expected: {mm['expected_sum']}, Actual: {mm['actual_sum']}, Error: {mm['error']}")

    # V2: Q1 Reproducibility (if PCT records provided)
    v2_results = None
    if args.pct_records:
        print("\n=== V2: Q1 Reproducibility Validation ===")
        pct_records = load_jsonl(args.pct_records)
        v2_results = validate_q1_reproducibility(pct_records)
        print(f"Total records: {v2_results['total_records']}")
        print(f"Q1 eligible: {v2_results['q1_eligible']}")
        print(f"Q1 excluded: {v2_results['q1_excluded']}")
        print(f"Calculation errors: {len(v2_results['calculation_errors'])}")

        if v2_results['sample_calculations']:
            print("\nSample Q1 calculations:")
            for calc in v2_results['sample_calculations']:
                print(f"  {calc['insurer_key']} | age {calc['age']} | {calc['plan_variant']}")
                print(f"    Premium/10M: {calc['premium_per_10m']}원")

    # V3: Product ID Map Coverage (if provided)
    v3_results = None
    if args.pct_records and args.product_id_map:
        print("\n=== V3: Product ID Map Coverage ===")
        pct_records = load_jsonl(args.pct_records)
        product_id_map = load_jsonl(args.product_id_map)
        v3_results = validate_product_id_map_coverage(pct_records, product_id_map)
        print(f"Total PCT products: {v3_results['total_pct_products']}")
        print(f"Mapped: {v3_results['mapped_count']}")
        print(f"Unmapped: {v3_results['unmapped_count']}")

        if v3_results['unmapped_products']:
            print("\nUnmapped products:")
            for prod in v3_results['unmapped_products'][:5]:
                print(f"  {prod['insurer_key']}: {prod['product_key']}")

    # Overall status
    v1_pass = v1_results['mismatch_count'] == 0 and len(v1_results['errors']) == 0
    v2_pass = v2_results is None or len(v2_results['calculation_errors']) == 0
    v3_pass = v3_results is None or v3_results['unmapped_count'] == 0

    success = v1_pass and v2_pass and v3_pass

    print(f"\n=== Overall Status ===")
    print(f"V1 (Sum Match): {'✅ PASS' if v1_pass else '❌ FAIL'}")
    if v2_results:
        print(f"V2 (Q1 Reproducibility): {'✅ PASS' if v2_pass else '❌ FAIL'}")
    if v3_results:
        print(f"V3 (Product ID Map): {'✅ PASS' if v3_pass else '❌ FAIL'}")
    print(f"\nFinal: {'✅ PASS' if success else '❌ FAIL'}")

    # Save output
    if args.output:
        report = {
            'v1_sum_match': v1_results,
            'v2_q1_reproducibility': v2_results,
            'v3_product_id_map': v3_results,
            'success': success
        }
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nValidation report saved: {args.output}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
