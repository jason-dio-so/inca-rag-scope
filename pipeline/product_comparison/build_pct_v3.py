"""
STEP NEXT-R: Build Product Comparison Table v3
Q1/Q14 activation with real premium data

Updates from v2:
- Q1/Q14 Top3/Top4 calculation
- Base contract from policy JSON (not hardcoded)
- Premium mandatory for customer output
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_base_contract_policy(policy_path: str) -> Dict[str, Any]:
    """
    Load base contract policy from JSON

    Args:
        policy_path: Path to base_contract_codes.json

    Returns:
        Dict: Policy definition
    """
    with open(policy_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_pct_v3(
    product_premiums: List[Dict[str, Any]],
    coverage_premiums: List[Dict[str, Any]],
    compare_rows: List[Dict[str, Any]],
    base_contract_policy: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build PCT v3 with Q1/Q14 support

    Args:
        product_premiums: product_premium_quote_v2 records
        coverage_premiums: coverage_premium_quote records
        compare_rows: compare_rows_v1 records
        base_contract_policy: Base contract policy

    Returns:
        List[Dict]: PCT v3 records
    """
    base_contract_codes = set(base_contract_policy['base_contract_codes'])

    # Group coverage premiums by key
    coverage_map = defaultdict(list)
    for cp in coverage_premiums:
        key = (
            cp['insurer_key'],
            cp['product_id'],
            cp['plan_variant'],
            cp['age'],
            cp['sex']
        )
        coverage_map[key].append(cp)

    # Group compare_rows by product
    compare_map = defaultdict(list)
    for row in compare_rows:
        identity = row['identity']
        key = (identity['insurer_key'], identity['product_key'])
        compare_map[key].append(row)

    pct_records = []

    for pp in product_premiums:
        insurer_key = pp['insurer_key']
        product_id = pp['product_id']
        plan_variant = pp['plan_variant']
        age = pp['age']
        sex = pp['sex']
        smoke = pp.get('smoke', 'NA')
        pay_term_years = pp['pay_term_years']
        ins_term_years = pp['ins_term_years']
        as_of_date = pp['as_of_date']
        premium_monthly = pp['premium_monthly_total']
        premium_total = pp['premium_total_total']

        # Get coverage premiums
        coverage_key = (insurer_key, product_id, plan_variant, age, sex)
        coverages = coverage_map.get(coverage_key, [])

        # Get compare_rows for payout limits
        compare_key = (insurer_key, product_id)
        compare_rows_for_product = compare_map.get(compare_key, [])

        # Build coverage list with amounts
        coverage_list = []
        for cp in coverages:
            coverage_code = cp['coverage_code']

            # Find payout limit from compare_rows
            payout_limit = None
            payout_limit_status = None
            for row in compare_rows_for_product:
                if row['identity'].get('coverage_code') == coverage_code:
                    payout_limit_slot = row['slots'].get('payout_limit', {})
                    payout_limit = payout_limit_slot.get('value')
                    payout_limit_status = payout_limit_slot.get('status')
                    break

            coverage_list.append({
                'coverage_code': coverage_code,
                'coverage_title': cp['coverage_title_raw'],
                'payout_limit': payout_limit,
                'payout_limit_status': payout_limit_status,
                'coverage_amount_value': cp.get('coverage_amount_value'),
                'monthly_premium': cp['premium_monthly_coverage']
            })

        # Calculate base_contract_monthly_sum
        base_contract_monthly_sum = sum(
            c['monthly_premium'] for c in coverage_list
            if c['coverage_code'] in base_contract_codes and c['monthly_premium'] > 0
        )
        base_contract_monthly_sum = base_contract_monthly_sum if base_contract_monthly_sum > 0 else None

        # Calculate optional_contract_monthly_sum
        optional_contract_monthly_sum = sum(
            c['monthly_premium'] for c in coverage_list
            if c['coverage_code'] not in base_contract_codes and c['monthly_premium'] > 0
        )
        optional_contract_monthly_sum = optional_contract_monthly_sum if optional_contract_monthly_sum > 0 else None

        # Base contract flags
        base_contract_min_flags = {
            'has_death': any(c['coverage_code'] in {'A1100', 'A1300'} for c in coverage_list),
            'has_disability': any(c['coverage_code'] == 'A3300_1' for c in coverage_list),
            'min_level': len([c for c in coverage_list if c['coverage_code'] in base_contract_codes])
        }

        # Q1 derived: Cancer diagnosis amount (A4200_1)
        cancer_diagnosis_amount = None
        for c in coverage_list:
            if c['coverage_code'] == 'A4200_1':
                cancer_diagnosis_amount = c.get('coverage_amount_value') or c.get('payout_limit')
                break

        # Q2 derived: Cerebrovascular (A4101) + Ischemic (A4105)
        cerebrovascular_amount = None
        ischemic_amount = None
        for c in coverage_list:
            if c['coverage_code'] == 'A4101':
                cerebrovascular_amount = c.get('coverage_amount_value') or c.get('payout_limit')
            elif c['coverage_code'] == 'A4105':
                ischemic_amount = c.get('coverage_amount_value') or c.get('payout_limit')

        # Build PCT record
        pct_record = {
            'insurer_key': insurer_key,
            'product_key': product_id,
            'plan_variant': plan_variant,
            'age': age,
            'sex': sex,
            'smoke': smoke,
            'pay_term_years': pay_term_years,
            'ins_term_years': ins_term_years,
            'as_of_date': as_of_date,
            'premium_monthly': premium_monthly,
            'premium_total': premium_total,
            'coverage_list': coverage_list,
            'base_contract_monthly_sum': base_contract_monthly_sum,
            'optional_contract_monthly_sum': optional_contract_monthly_sum,
            'base_contract_min_flags': base_contract_min_flags,
            'underwriting_tags': {},
            'cancer_diagnosis_amount': cancer_diagnosis_amount,
            'cerebrovascular_amount': cerebrovascular_amount,
            'ischemic_amount': ischemic_amount
        }

        pct_records.append(pct_record)

    return pct_records


def calculate_q1_rankings(
    pct_records: List[Dict[str, Any]],
    top_n: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate Q1 rankings: Premium per 10M cancer diagnosis

    Args:
        pct_records: PCT v3 records
        top_n: Number of top products to return (default: 3)

    Returns:
        Dict: {age_planvariant: [top products]}
    """
    rankings = {}

    # Group by (age, plan_variant)
    for age in [30, 40, 50]:
        for plan_variant in ['NO_REFUND', 'GENERAL']:
            # Filter eligible records
            eligible = [
                r for r in pct_records
                if (r['age'] == age and
                    r['plan_variant'] == plan_variant and
                    r['cancer_diagnosis_amount'] is not None and
                    r['cancer_diagnosis_amount'] > 0 and
                    r['premium_monthly'] > 0)
            ]

            # Calculate premium_per_10m
            for record in eligible:
                cancer_amt = record['cancer_diagnosis_amount']
                premium_monthly = record['premium_monthly']
                record['premium_per_10m'] = premium_monthly / (cancer_amt / 10_000_000)

            # Sort and take top N
            sorted_records = sorted(eligible, key=lambda x: x['premium_per_10m'])
            top_records = sorted_records[:top_n]

            key = f"age_{age}_{plan_variant}"
            rankings[key] = top_records

    return rankings


def calculate_q14_rankings(
    pct_records: List[Dict[str, Any]],
    top_n: int = 4
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate Q14 rankings: Top4 가성비 비교

    Args:
        pct_records: PCT v3 records
        top_n: Number of top products to return (default: 4)

    Returns:
        Dict: {age_planvariant: [top products]}
    """
    # Q14 uses same logic as Q1 but top_n = 4
    return calculate_q1_rankings(pct_records, top_n=top_n)


def write_jsonl(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write records to JSONL"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')

    print(f"Written {len(records)} records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build PCT v3 with Q1/Q14 support")
    parser.add_argument(
        "--product-premiums",
        required=True,
        help="Path to product_premium_quote_v2 JSONL"
    )
    parser.add_argument(
        "--coverage-premiums",
        required=True,
        help="Path to coverage_premium_quote JSONL"
    )
    parser.add_argument(
        "--compare-rows",
        default="/Users/cheollee/inca-rag-scope/data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows_v1 JSONL"
    )
    parser.add_argument(
        "--base-contract-policy",
        default="/Users/cheollee/inca-rag-scope/data/policy/base_contract_codes.json",
        help="Path to base contract policy JSON"
    )
    parser.add_argument(
        "--output",
        default="/tmp/pct_v3.jsonl",
        help="Path to output PCT v3 JSONL"
    )

    args = parser.parse_args()

    print("=== STEP NEXT-R: PCT v3 Builder ===\n")

    print(f"Loading product premiums: {args.product_premiums}")
    product_premiums = load_jsonl(args.product_premiums)
    print(f"Loaded {len(product_premiums)} product premium records")

    print(f"Loading coverage premiums: {args.coverage_premiums}")
    coverage_premiums = load_jsonl(args.coverage_premiums)
    print(f"Loaded {len(coverage_premiums)} coverage premium records")

    print(f"Loading compare rows: {args.compare_rows}")
    compare_rows = load_jsonl(args.compare_rows)
    print(f"Loaded {len(compare_rows)} compare_rows_v1 records")

    print(f"Loading base contract policy: {args.base_contract_policy}")
    base_contract_policy = load_base_contract_policy(args.base_contract_policy)
    print(f"Base contract codes: {base_contract_policy['base_contract_codes']}\n")

    print("Building PCT v3...")
    pct_records = build_pct_v3(
        product_premiums,
        coverage_premiums,
        compare_rows,
        base_contract_policy
    )
    print(f"Built {len(pct_records)} PCT v3 records")

    write_jsonl(pct_records, args.output)

    # Calculate Q1 rankings
    print("\n=== Q1 Rankings (Top3 per age × plan_variant) ===")
    q1_rankings = calculate_q1_rankings(pct_records, top_n=3)
    for key, top_products in q1_rankings.items():
        print(f"\n{key}:")
        for idx, product in enumerate(top_products, 1):
            print(f"  {idx}. {product['insurer_key']} | {product['product_key'][:30]}")
            print(f"     Premium/10M: {product.get('premium_per_10m', 'N/A')}원")

    # Calculate Q14 rankings
    print("\n=== Q14 Rankings (Top4 per age × plan_variant) ===")
    q14_rankings = calculate_q14_rankings(pct_records, top_n=4)
    eligible_count = sum(len(v) for v in q14_rankings.values())
    print(f"Total Q14 eligible products: {eligible_count}")

    # Sample output
    print("\n=== Sample PCT v3 Record ===")
    if pct_records:
        sample = pct_records[0]
        print(json.dumps({
            'insurer_key': sample['insurer_key'],
            'product_key': sample['product_key'][:50],
            'plan_variant': sample['plan_variant'],
            'age': sample['age'],
            'premium_monthly': sample['premium_monthly'],
            'base_contract_monthly_sum': sample['base_contract_monthly_sum'],
            'cancer_diagnosis_amount': sample['cancer_diagnosis_amount'],
            'coverage_count': len(sample['coverage_list'])
        }, ensure_ascii=False, indent=2))
