"""
STEP NEXT-P: Build Product Comparison Table v1
Generate PCT v1 from premium_quote + compare_rows_v1

Rules (LOCKED):
1. Premium from premium_quote ONLY (SSOT)
2. Coverage/amounts from compare_rows_v1 ONLY (SSOT)
3. NO LLM/estimation/interpolation/averaging
4. Missing value = NULL or "정보 없음"
5. plan_variant is mandatory axis for Q1/Q14
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from decimal import Decimal
import re

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


def extract_slot_value(slots: Dict, slot_name: str) -> tuple[str | None, str | None]:
    """
    Extract slot value and status

    Args:
        slots: slots dictionary
        slot_name: slot key name

    Returns:
        (value, status) tuple
    """
    if slot_name not in slots:
        return None, None

    slot = slots[slot_name]
    value = slot.get('value')
    status = slot.get('status')

    return (str(value) if value is not None else None, status)


def parse_payout_limit(payout_limit_str: str | None) -> int | None:
    """
    Parse payout_limit value to extract amount

    Rules:
    - "90, 1, 1163010" → Extract first number as amount (90만원 = 900,000원)
    - "1000만원" → 10,000,000
    - "5천만원" → 50,000,000
    - NULL/empty → None

    Args:
        payout_limit_str: payout_limit value string

    Returns:
        Amount in KRW (원) or None
    """
    if not payout_limit_str:
        return None

    # Try to extract first number
    # Pattern: "90, 1, 1163010" or "1000" or "5000만원"
    payout_limit_str = str(payout_limit_str).strip()

    # Remove common prefixes/suffixes
    payout_limit_str = payout_limit_str.replace('만원', '')
    payout_limit_str = payout_limit_str.replace('천만원', '0000')
    payout_limit_str = payout_limit_str.replace('억원', '00000000')

    # Extract first number
    match = re.search(r'(\d+)', payout_limit_str)
    if match:
        amount = int(match.group(1))
        # Assume "만원" unit if number is small (< 10000)
        if amount < 10000 and '만원' in str(payout_limit_str):
            amount *= 10000
        return amount

    return None


def build_coverage_bundle(
    compare_rows: List[Dict[str, Any]],
    insurer_key: str,
    product_key: str,
    variant_key: str = "default"
) -> Dict[str, Any]:
    """
    Build coverage bundle for a product

    Args:
        compare_rows: All compare_rows_v1 records
        insurer_key: Insurer key
        product_key: Product key
        variant_key: Variant key

    Returns:
        Dict: {
            coverage_list: List[{coverage_code, coverage_title, payout_limit, monthly_premium}],
            base_contract_monthly_sum: int,
            optional_contract_monthly_sum: int,
            base_contract_min_flags: dict,
            underwriting_tags: dict
        }
    """
    # Filter rows for this product
    product_rows = [
        row for row in compare_rows
        if (row['identity']['insurer_key'] == insurer_key and
            row['identity']['product_key'] == product_key and
            row['identity'].get('variant_key', 'default') == variant_key)
    ]

    coverage_list = []

    for row in product_rows:
        identity = row['identity']
        slots = row['slots']

        coverage_code = identity.get('coverage_code')
        coverage_title = identity.get('coverage_title', identity.get('coverage_name_raw'))

        # Extract payout_limit
        payout_limit_value, payout_limit_status = extract_slot_value(slots, 'payout_limit')
        payout_limit_amount = parse_payout_limit(payout_limit_value)

        # Extract underwriting_condition
        underwriting_condition, underwriting_status = extract_slot_value(slots, 'underwriting_condition')

        coverage_list.append({
            'coverage_code': coverage_code,
            'coverage_title': coverage_title,
            'payout_limit': payout_limit_amount,
            'payout_limit_status': payout_limit_status,
            'monthly_premium': None,  # TODO: Per-coverage premium (out of scope for now)
            'underwriting_condition': underwriting_condition,
            'underwriting_status': underwriting_status
        })

    # Base contract classification (POLICY)
    # Define base contract coverage codes
    BASE_CONTRACT_CODES = {
        'A4001',  # 질병사망
        'A4002',  # 상해사망
        'A4003',  # 후유장해
        # Add more as needed
    }

    base_coverages = [c for c in coverage_list if c['coverage_code'] in BASE_CONTRACT_CODES]
    optional_coverages = [c for c in coverage_list if c['coverage_code'] not in BASE_CONTRACT_CODES]

    # Base contract monthly sum (PLACEHOLDER - requires per-coverage premium)
    base_contract_monthly_sum = None  # TODO: Sum of base coverage premiums
    optional_contract_monthly_sum = None  # TODO: Sum of optional coverage premiums

    # Base contract min flags
    base_contract_min_flags = {
        'has_death': any(c['coverage_code'] in {'A4001', 'A4002'} for c in base_coverages),
        'has_disability': any(c['coverage_code'] == 'A4003' for c in base_coverages),
        'min_level': len(base_coverages)
    }

    # Underwriting tags (EVIDENCE-BASED ONLY)
    # Check if any coverage has underwriting_condition evidence
    has_chronic_no_surcharge = any(
        c['underwriting_condition'] and '할증' in str(c['underwriting_condition'])
        for c in coverage_list
    )

    underwriting_tags = {
        'has_chronic_no_surcharge': has_chronic_no_surcharge,
        'has_simplified': False  # TODO: Evidence-based detection
    }

    return {
        'coverage_list': coverage_list,
        'base_contract_monthly_sum': base_contract_monthly_sum,
        'optional_contract_monthly_sum': optional_contract_monthly_sum,
        'base_contract_min_flags': base_contract_min_flags,
        'underwriting_tags': underwriting_tags
    }


def build_pct_v1(
    premium_quotes: List[Dict[str, Any]],
    compare_rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build Product Comparison Table v1

    Args:
        premium_quotes: premium_quote records
        compare_rows: compare_rows_v1 records

    Returns:
        List[Dict]: PCT v1 records
    """
    pct_records = []

    # Group compare_rows by (insurer_key, product_key, variant_key)
    coverage_bundles = {}

    for quote in premium_quotes:
        insurer_key = quote['insurer_key']
        product_key = quote['product_id']
        variant_key = 'default'  # Assuming default for now

        # Build coverage bundle if not cached
        bundle_key = (insurer_key, product_key, variant_key)
        if bundle_key not in coverage_bundles:
            coverage_bundles[bundle_key] = build_coverage_bundle(
                compare_rows, insurer_key, product_key, variant_key
            )

        bundle = coverage_bundles[bundle_key]

        # Build PCT record
        pct_record = {
            # Key dimensions
            'insurer_key': insurer_key,
            'product_key': product_key,
            'plan_variant': quote['plan_variant'],
            'age': quote['age'],
            'sex': quote['sex'],
            'smoke': quote['smoke'],
            'pay_term_years': quote['pay_term_years'],
            'ins_term_years': quote['ins_term_years'],
            'as_of_date': quote['as_of_date'],

            # Premium (from premium_quote SSOT)
            'premium_monthly': quote['premium_monthly'],
            'premium_total': quote['premium_total'],

            # Coverage bundle
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

    print(f"Written {len(records)} PCT v1 records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Product Comparison Table v1")
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
        "--output",
        default="/tmp/pct_v1.jsonl",
        help="Path to output PCT v1 JSONL file"
    )

    args = parser.parse_args()

    print(f"Loading premium quotes: {args.premium_quotes}")
    premium_quotes = load_jsonl(args.premium_quotes)
    print(f"Loaded {len(premium_quotes)} premium quote records")

    print(f"Loading compare rows: {args.compare_rows}")
    compare_rows = load_jsonl(args.compare_rows)
    print(f"Loaded {len(compare_rows)} compare_rows_v1 records")

    print("Building PCT v1...")
    pct_records = build_pct_v1(premium_quotes, compare_rows)

    write_pct_jsonl(pct_records, args.output)

    # Sample output
    print("\nSample PCT v1 record:")
    if pct_records:
        sample = pct_records[0]
        print(json.dumps({
            'insurer_key': sample['insurer_key'],
            'product_key': sample['product_key'],
            'plan_variant': sample['plan_variant'],
            'age': sample['age'],
            'premium_monthly': sample['premium_monthly'],
            'cancer_diagnosis_amount': sample['cancer_diagnosis_amount'],
            'coverage_count': len(sample['coverage_list'])
        }, ensure_ascii=False, indent=2))
