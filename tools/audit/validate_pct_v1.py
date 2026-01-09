#!/usr/bin/env python3
"""
STEP NEXT-P: PCT v1 Validation Script
Validate Product Comparison Table v1 for Q1/Q2/Q3

Usage:
    python3 tools/audit/validate_pct_v1.py --input /tmp/pct_v1.jsonl

Validation Rules:
1. Q1: premium_per_10m calculation is deterministic
2. Q2: underwriting_tags are evidence-based ONLY
3. Q3: base_contract_monthly_sum calculation is reproducible
4. NO LLM/estimation/interpolation
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


def validate_q1_premium_per_cancer(pct_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate Q1: Premium per 10M cancer diagnosis

    Rules:
    - cancer_diagnosis_amount from A4200_1 coverage
    - premium_per_10m = premium_monthly / (cancer_amt / 10,000,000)
    - Exclude records with NULL cancer_diagnosis_amount

    Returns:
        Dict: Validation results
    """
    results = {
        'total_records': len(pct_records),
        'q1_eligible_records': 0,
        'q1_excluded_records': 0,
        'q1_top3_by_age_variant': {},
        'errors': []
    }

    # Filter Q1-eligible records
    q1_eligible = []
    for record in pct_records:
        cancer_amt = record.get('cancer_diagnosis_amount')
        if cancer_amt is None or cancer_amt <= 0:
            results['q1_excluded_records'] += 1
            continue

        premium_monthly = record['premium_monthly']

        # Calculate premium_per_10m
        try:
            premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
        except (ZeroDivisionError, TypeError):
            results['errors'].append(
                f"Q1 calculation error: insurer={record['insurer_key']}, "
                f"product={record['product_key']}, cancer_amt={cancer_amt}"
            )
            continue

        q1_eligible.append({
            'insurer_key': record['insurer_key'],
            'product_key': record['product_key'],
            'plan_variant': record['plan_variant'],
            'age': record['age'],
            'sex': record['sex'],
            'premium_monthly': premium_monthly,
            'cancer_diagnosis_amount': cancer_amt,
            'premium_per_10m': premium_per_10m
        })

    results['q1_eligible_records'] = len(q1_eligible)

    # Group by (age, plan_variant) and get Top3
    for age in [30, 40, 50]:
        for plan_variant in ['NO_REFUND', 'GENERAL']:
            group = [r for r in q1_eligible
                     if r['age'] == age and r['plan_variant'] == plan_variant]

            # Sort by premium_per_10m ASC
            group_sorted = sorted(group, key=lambda x: x['premium_per_10m'])

            top3 = group_sorted[:3]
            key = f"age_{age}_{plan_variant}"
            results['q1_top3_by_age_variant'][key] = top3

    return results


def validate_q2_underwriting(pct_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate Q2: Underwriting tags are evidence-based

    Rules:
    - underwriting_tags.has_chronic_no_surcharge must have evidence
    - Exclude records without evidence (NO estimation)

    Returns:
        Dict: Validation results
    """
    results = {
        'total_records': len(pct_records),
        'q2_eligible_records': 0,
        'q2_excluded_records': 0,
        'inference_violations': [],
        'errors': []
    }

    for record in pct_records:
        underwriting_tags = record.get('underwriting_tags', {})

        has_chronic_no_surcharge = underwriting_tags.get('has_chronic_no_surcharge', False)

        if has_chronic_no_surcharge:
            # Check if evidence exists
            coverage_list = record.get('coverage_list', [])
            has_evidence = any(
                c.get('underwriting_condition') is not None
                for c in coverage_list
            )

            if not has_evidence:
                results['inference_violations'].append({
                    'insurer_key': record['insurer_key'],
                    'product_key': record['product_key'],
                    'issue': 'has_chronic_no_surcharge=True but no underwriting_condition evidence'
                })

            results['q2_eligible_records'] += 1
        else:
            results['q2_excluded_records'] += 1

    return results


def validate_q3_base_contract(pct_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate Q3: Base contract minimization

    Rules:
    - base_contract_monthly_sum calculation is deterministic
    - base_contract_min_flags based on coverage_code presence

    Returns:
        Dict: Validation results
    """
    results = {
        'total_records': len(pct_records),
        'base_contract_defined': 0,
        'base_contract_null': 0,
        'min_flags_errors': [],
        'errors': []
    }

    BASE_CONTRACT_CODES = {'A4001', 'A4002', 'A4003'}

    for record in pct_records:
        base_contract_monthly_sum = record.get('base_contract_monthly_sum')
        base_contract_min_flags = record.get('base_contract_min_flags', {})

        if base_contract_monthly_sum is not None:
            results['base_contract_defined'] += 1
        else:
            results['base_contract_null'] += 1

        # Validate min_flags
        coverage_list = record.get('coverage_list', [])
        has_death = any(c['coverage_code'] in {'A4001', 'A4002'} for c in coverage_list)
        has_disability = any(c['coverage_code'] == 'A4003' for c in coverage_list)

        expected_has_death = base_contract_min_flags.get('has_death', False)
        expected_has_disability = base_contract_min_flags.get('has_disability', False)

        if has_death != expected_has_death:
            results['min_flags_errors'].append({
                'insurer_key': record['insurer_key'],
                'product_key': record['product_key'],
                'field': 'has_death',
                'expected': has_death,
                'actual': expected_has_death
            })

        if has_disability != expected_has_disability:
            results['min_flags_errors'].append({
                'insurer_key': record['insurer_key'],
                'product_key': record['product_key'],
                'field': 'has_disability',
                'expected': has_disability,
                'actual': expected_has_disability
            })

    return results


def validate_pct_v1(pct_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate PCT v1 records

    Returns:
        Dict: Comprehensive validation results
    """
    print("Validating Q1: Premium per cancer diagnosis...")
    q1_results = validate_q1_premium_per_cancer(pct_records)

    print("Validating Q2: Underwriting tags...")
    q2_results = validate_q2_underwriting(pct_records)

    print("Validating Q3: Base contract minimization...")
    q3_results = validate_q3_base_contract(pct_records)

    # Overall success
    success = (
        len(q1_results['errors']) == 0 and
        len(q2_results['inference_violations']) == 0 and
        len(q3_results['min_flags_errors']) == 0
    )

    return {
        'total_records': len(pct_records),
        'q1_results': q1_results,
        'q2_results': q2_results,
        'q3_results': q3_results,
        'success': success
    }


def main():
    parser = argparse.ArgumentParser(description="Validate PCT v1 records")
    parser.add_argument("--input", required=True, help="Path to PCT v1 JSONL file")
    parser.add_argument("--output", help="Path to validation report (JSON)")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)

    print(f"Loading PCT v1 records: {args.input}")
    pct_records = load_jsonl(args.input)
    print(f"Loaded {len(pct_records)} records\n")

    results = validate_pct_v1(pct_records)

    # Print summary
    print("\n=== PCT v1 Validation Summary ===")
    print(f"Total records: {results['total_records']}")
    print()

    print("Q1 (Premium per Cancer):")
    print(f"  Eligible: {results['q1_results']['q1_eligible_records']}")
    print(f"  Excluded: {results['q1_results']['q1_excluded_records']}")
    print(f"  Errors: {len(results['q1_results']['errors'])}")
    print()

    print("Q2 (Underwriting):")
    print(f"  Eligible: {results['q2_results']['q2_eligible_records']}")
    print(f"  Excluded: {results['q2_results']['q2_excluded_records']}")
    print(f"  Inference violations: {len(results['q2_results']['inference_violations'])}")
    print()

    print("Q3 (Base Contract):")
    print(f"  Defined: {results['q3_results']['base_contract_defined']}")
    print(f"  NULL: {results['q3_results']['base_contract_null']}")
    print(f"  Min flags errors: {len(results['q3_results']['min_flags_errors'])}")
    print()

    print(f"Status: {'✅ PASS' if results['success'] else '❌ FAIL'}")

    # Print Q1 Top3 sample
    if results['q1_results']['q1_top3_by_age_variant']:
        print("\n=== Q1 Top3 Sample (age_30_NO_REFUND) ===")
        top3 = results['q1_results']['q1_top3_by_age_variant'].get('age_30_NO_REFUND', [])
        for i, record in enumerate(top3, 1):
            print(f"{i}. {record['insurer_key']} - {record['product_key']}")
            print(f"   Premium/10M: {record['premium_per_10m']:.2f}원")

    # Print errors
    if results['q1_results']['errors']:
        print("\n=== Q1 Errors ===")
        for error in results['q1_results']['errors']:
            print(f"  ❌ {error}")

    if results['q2_results']['inference_violations']:
        print("\n=== Q2 Inference Violations ===")
        for violation in results['q2_results']['inference_violations']:
            print(f"  ❌ {violation}")

    if results['q3_results']['min_flags_errors']:
        print("\n=== Q3 Min Flags Errors ===")
        for error in results['q3_results']['min_flags_errors'][:5]:
            print(f"  ❌ {error}")

    # Save output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nValidation report saved: {args.output}")

    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()
