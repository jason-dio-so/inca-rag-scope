"""
STEP NEXT-Q: Build Product Comparison Table v2
Generate PCT v2 with per-coverage premium integration

Updates from v1:
- Integrates coverage_premium_quote (per-coverage premiums)
- Calculates base_contract_monthly_sum from coverage premiums
- Uses product_id_map for product alignment
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


def build_product_id_map_dict(product_id_map: List[Dict[str, Any]]) -> Dict[tuple, str]:
    """
    Build product_id mapping dictionary

    Args:
        product_id_map: product_id_map records

    Returns:
        Dict: {(insurer_key, compare_product_id): premium_product_id}
    """
    mapping = {}
    for record in product_id_map:
        key = (record['insurer_key'], record['compare_product_id'])
        mapping[key] = record['premium_product_id']
    return mapping


def build_coverage_bundle_with_premiums(
    compare_rows: List[Dict[str, Any]],
    coverage_premiums: List[Dict[str, Any]],
    insurer_key: str,
    product_id: str,
    plan_variant: str,
    age: int,
    sex: str
) -> Dict[str, Any]:
    """
    Build coverage bundle with per-coverage premiums

    Args:
        compare_rows: compare_rows_v1 records
        coverage_premiums: coverage_premium_quote records
        insurer_key: Insurer key
        product_id: Product ID (premium_product_id)
        plan_variant: GENERAL | NO_REFUND
        age: Age
        sex: Sex

    Returns:
        Dict: Coverage bundle with premiums
    """
    # Filter compare_rows for this product
    product_rows = [
        row for row in compare_rows
        if (row['identity']['insurer_key'] == insurer_key and
            row['identity']['product_key'] == product_id)
    ]

    # Filter coverage_premiums for this product/variant/age/sex
    product_coverage_premiums = [
        cp for cp in coverage_premiums
        if (cp['insurer_key'] == insurer_key and
            cp['product_id'] == product_id and
            cp['plan_variant'] == plan_variant and
            cp['age'] == age and
            cp['sex'] == sex)
    ]

    # Build coverage list with premiums
    coverage_list = []
    coverage_premium_map = {
        cp['coverage_code']: cp for cp in product_coverage_premiums
    }

    for row in product_rows:
        identity = row['identity']
        slots = row['slots']

        coverage_code = identity.get('coverage_code')
        coverage_title = identity.get('coverage_title', identity.get('coverage_name_raw'))

        # Get payout_limit
        payout_limit_slot = slots.get('payout_limit', {})
        payout_limit_value = payout_limit_slot.get('value')
        payout_limit_status = payout_limit_slot.get('status')

        # Get coverage premium from coverage_premium_quote
        coverage_premium = coverage_premium_map.get(coverage_code)
        monthly_premium = coverage_premium['premium_monthly_coverage'] if coverage_premium else None

        coverage_list.append({
            'coverage_code': coverage_code,
            'coverage_title': coverage_title,
            'payout_limit': payout_limit_value,
            'payout_limit_status': payout_limit_status,
            'monthly_premium': monthly_premium
        })

    # Base contract classification (POLICY)
    BASE_CONTRACT_CODES = {
        'A4001',  # 질병사망
        'A4002',  # 상해사망
        'A4003',  # 후유장해
    }

    base_coverages = [c for c in coverage_list if c['coverage_code'] in BASE_CONTRACT_CODES]
    optional_coverages = [c for c in coverage_list if c['coverage_code'] not in BASE_CONTRACT_CODES]

    # Calculate base_contract_monthly_sum
    base_contract_monthly_sum = sum(
        c['monthly_premium'] for c in base_coverages
        if c['monthly_premium'] is not None
    )
    base_contract_monthly_sum = base_contract_monthly_sum if base_contract_monthly_sum > 0 else None

    # Calculate optional_contract_monthly_sum
    optional_contract_monthly_sum = sum(
        c['monthly_premium'] for c in optional_coverages
        if c['monthly_premium'] is not None
    )
    optional_contract_monthly_sum = optional_contract_monthly_sum if optional_contract_monthly_sum > 0 else None

    # Base contract min flags
    base_contract_min_flags = {
        'has_death': any(c['coverage_code'] in {'A4001', 'A4002'} for c in base_coverages),
        'has_disability': any(c['coverage_code'] == 'A4003' for c in base_coverages),
        'min_level': len(base_coverages)
    }

    # Underwriting tags (evidence-based ONLY)
    underwriting_tags = {
        'has_chronic_no_surcharge': False,  # TODO: Evidence-based detection
        'has_simplified': False
    }

    return {
        'coverage_list': coverage_list,
        'base_contract_monthly_sum': base_contract_monthly_sum,
        'optional_contract_monthly_sum': optional_contract_monthly_sum,
        'base_contract_min_flags': base_contract_min_flags,
        'underwriting_tags': underwriting_tags
    }


def build_pct_v2(
    premium_quotes: List[Dict[str, Any]],
    compare_rows: List[Dict[str, Any]],
    coverage_premiums: List[Dict[str, Any]],
    product_id_map: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build Product Comparison Table v2

    Args:
        premium_quotes: product_premium_quote_v2 records
        compare_rows: compare_rows_v1 records
        coverage_premiums: coverage_premium_quote records
        product_id_map: product_id_map records

    Returns:
        List[Dict]: PCT v2 records
    """
    pct_records = []

    # Build product_id mapping
    id_mapping = build_product_id_map_dict(product_id_map)

    for quote in premium_quotes:
        insurer_key = quote['insurer_key']
        premium_product_id = quote['product_id']
        plan_variant = quote['plan_variant']
        age = quote['age']
        sex = quote['sex']
        smoke = quote.get('smoke', 'NA')
        pay_term_years = quote['pay_term_years']
        ins_term_years = quote['ins_term_years']
        as_of_date = quote['as_of_date']
        premium_monthly = quote['premium_monthly']
        premium_total = quote['premium_total']

        # Build coverage bundle with premiums
        bundle = build_coverage_bundle_with_premiums(
            compare_rows,
            coverage_premiums,
            insurer_key,
            premium_product_id,
            plan_variant,
            age,
            sex
        )

        # Build PCT record
        pct_record = {
            # Key dimensions
            'insurer_key': insurer_key,
            'product_key': premium_product_id,
            'plan_variant': plan_variant,
            'age': age,
            'sex': sex,
            'smoke': smoke,
            'pay_term_years': pay_term_years,
            'ins_term_years': ins_term_years,
            'as_of_date': as_of_date,

            # Premium (from premium_quote SSOT)
            'premium_monthly': premium_monthly,
            'premium_total': premium_total,

            # Coverage bundle (with per-coverage premiums)
            'coverage_list': bundle['coverage_list'],
            'base_contract_monthly_sum': bundle['base_contract_monthly_sum'],
            'optional_contract_monthly_sum': bundle['optional_contract_monthly_sum'],
            'base_contract_min_flags': bundle['base_contract_min_flags'],
            'underwriting_tags': bundle['underwriting_tags'],

            # Q1 derived: Cancer diagnosis amount (A4200_1)
            'cancer_diagnosis_amount': next(
                (c['payout_limit'] for c in bundle['coverage_list']
                 if c['coverage_code'] == 'A4200_1' and c['payout_limit'] is not None),
                None
            ),

            # Q2 derived: Cerebrovascular (A4101) + Ischemic (A4105)
            'cerebrovascular_amount': next(
                (c['payout_limit'] for c in bundle['coverage_list']
                 if c['coverage_code'] == 'A4101' and c['payout_limit'] is not None),
                None
            ),

            'ischemic_amount': next(
                (c['payout_limit'] for c in bundle['coverage_list']
                 if c['coverage_code'] == 'A4105' and c['payout_limit'] is not None),
                None
            )
        }

        pct_records.append(pct_record)

    return pct_records


def write_pct_jsonl(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write PCT records to JSONL"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')

    print(f"Written {len(records)} PCT v2 records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Product Comparison Table v2")
    parser.add_argument(
        "--premium-quotes",
        default="/tmp/test_premium_quotes.jsonl",
        help="Path to premium_quote JSONL file"
    )
    parser.add_argument(
        "--compare-rows",
        default="/Users/cheollee/inca-rag-scope/data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows_v1 JSONL file"
    )
    parser.add_argument(
        "--coverage-premiums",
        default="/tmp/coverage_premium_quote.jsonl",
        help="Path to coverage_premium_quote JSONL file"
    )
    parser.add_argument(
        "--product-id-map",
        default="/tmp/product_id_map.jsonl",
        help="Path to product_id_map JSONL file"
    )
    parser.add_argument(
        "--output",
        default="/tmp/pct_v2.jsonl",
        help="Path to output PCT v2 JSONL file"
    )

    args = parser.parse_args()

    print(f"Loading premium quotes: {args.premium_quotes}")
    premium_quotes = load_jsonl(args.premium_quotes)
    print(f"Loaded {len(premium_quotes)} premium quote records")

    print(f"Loading compare rows: {args.compare_rows}")
    compare_rows = load_jsonl(args.compare_rows)
    print(f"Loaded {len(compare_rows)} compare_rows_v1 records")

    print(f"Loading coverage premiums: {args.coverage_premiums}")
    coverage_premiums = load_jsonl(args.coverage_premiums)
    print(f"Loaded {len(coverage_premiums)} coverage_premium_quote records")

    print(f"Loading product_id_map: {args.product_id_map}")
    product_id_map = load_jsonl(args.product_id_map)
    print(f"Loaded {len(product_id_map)} product_id_map records")

    print("Building PCT v2...")
    pct_records = build_pct_v2(premium_quotes, compare_rows, coverage_premiums, product_id_map)

    write_pct_jsonl(pct_records, args.output)

    # Sample output
    print("\nSample PCT v2 record:")
    if pct_records:
        sample = pct_records[0]
        print(json.dumps({
            'insurer_key': sample['insurer_key'],
            'product_key': sample['product_key'],
            'plan_variant': sample['plan_variant'],
            'age': sample['age'],
            'premium_monthly': sample['premium_monthly'],
            'base_contract_monthly_sum': sample['base_contract_monthly_sum'],
            'cancer_diagnosis_amount': sample['cancer_diagnosis_amount'],
            'coverage_count': len(sample['coverage_list'])
        }, ensure_ascii=False, indent=2))
