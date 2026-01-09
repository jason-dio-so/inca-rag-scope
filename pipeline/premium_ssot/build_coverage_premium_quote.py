"""
STEP NEXT-Q: Build coverage_premium_quote from API responses
Generate per-coverage premium SSOT

Rules (LOCKED):
1. NO_REFUND: premium from API cvrAmtArrLst[].monthlyPrem
2. GENERAL: NO_REFUND × multiplier (only if multiplier exists)
3. NO LLM/estimation/heuristic allocation
4. Sum verification: sum(coverage_premium) == monthlyPremSum (0 error tolerance)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from decimal import Decimal

# Add parent to path
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


def parse_api_response_coverage_premium(
    api_response: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Parse API response to extract per-coverage premiums

    Expected API structure (SSOT):
    {
      "insurer_key": "kb",
      "product_id": "kb__ci_insurance_2024",
      "quotes": [
        {
          "age": 30,
          "sex": "M",
          "smoke": "N",
          "pay_term_years": 20,
          "ins_term_years": 80,
          "monthly_prem_sum": 50000,
          "total_prem_sum": 12000000,
          "as_of_date": "2025-01-09",
          "coverages": [
            {
              "coverage_code": "A4200_1",
              "coverage_title_raw": "암진단비(유사암제외)",
              "coverage_amount_raw": "1000만원",
              "coverage_amount_value": 10000000,
              "monthly_prem": 20000
            },
            ...
          ]
        }
      ]
    }

    Args:
        api_response: API response dict

    Returns:
        List[Dict]: coverage_premium_quote records (NO_REFUND only)
    """
    insurer_key = api_response['insurer_key']
    product_id = api_response['product_id']
    quotes = api_response['quotes']

    records = []

    for quote in quotes:
        age = quote['age']
        sex = quote['sex']
        smoke = quote.get('smoke', 'NA')
        pay_term_years = quote['pay_term_years']
        ins_term_years = quote['ins_term_years']
        as_of_date = quote['as_of_date']
        monthly_prem_sum = quote['monthly_prem_sum']

        coverages = quote.get('coverages', [])

        for idx, coverage in enumerate(coverages):
            coverage_code = coverage.get('coverage_code')
            coverage_title_raw = coverage.get('coverage_title_raw')
            coverage_amount_raw = coverage.get('coverage_amount_raw')
            coverage_amount_value = coverage.get('coverage_amount_value')
            monthly_prem = coverage.get('monthly_prem')

            if monthly_prem is None or monthly_prem <= 0:
                # Skip coverages without premium
                continue

            records.append({
                'insurer_key': insurer_key,
                'product_id': product_id,
                'plan_variant': 'NO_REFUND',
                'age': age,
                'sex': sex,
                'smoke': smoke,
                'pay_term_years': pay_term_years,
                'ins_term_years': ins_term_years,
                'as_of_date': as_of_date,
                'coverage_code': coverage_code,
                'coverage_title_raw': coverage_title_raw,
                'coverage_name_normalized': coverage_title_raw,  # TODO: Apply normalization
                'coverage_amount_raw': coverage_amount_raw,
                'coverage_amount_value': coverage_amount_value,
                'premium_monthly_coverage': monthly_prem,
                'source_table_id': 'api_response',
                'source_row_id': f"coverage_{idx}",
                'multiplier_percent': None
            })

    return records


def generate_general_coverage_premiums(
    no_refund_records: List[Dict[str, Any]],
    multipliers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate GENERAL coverage premiums from NO_REFUND + multipliers

    Rules:
    - GENERAL = NO_REFUND × multiplier (only if multiplier exists)
    - NO multiplier = NO GENERAL record

    Args:
        no_refund_records: NO_REFUND coverage_premium_quote records
        multipliers: Multiplier data from 일반보험요율예시.xlsx

    Returns:
        List[Dict]: GENERAL coverage_premium_quote records
    """
    general_records = []

    for record in no_refund_records:
        insurer_key = record['insurer_key']
        coverage_title_raw = record['coverage_title_raw']

        # Get multiplier
        multiplier_percent = get_multiplier(insurer_key, coverage_title_raw, multipliers)

        if multiplier_percent is None:
            # No multiplier → Skip GENERAL
            continue

        # Calculate GENERAL premium
        no_refund_premium = record['premium_monthly_coverage']
        general_premium = calculate_general_premium(no_refund_premium, multiplier_percent)

        if general_premium is None:
            continue

        # Create GENERAL record
        general_record = record.copy()
        general_record['plan_variant'] = 'GENERAL'
        general_record['premium_monthly_coverage'] = general_premium
        general_record['multiplier_percent'] = multiplier_percent
        general_record['source_table_id'] = f"calculated_from_no_refund_multiplier_{multiplier_percent}"

        general_records.append(general_record)

    return general_records


def verify_sum_match(
    coverage_premiums: List[Dict[str, Any]],
    expected_sum: int,
    tolerance: int = 0
) -> Dict[str, Any]:
    """
    Verify that sum(coverage_premium) == expected_sum

    Args:
        coverage_premiums: Coverage premium records
        expected_sum: Expected monthly premium sum
        tolerance: Allowed error (default: 0)

    Returns:
        Dict: {match: bool, actual_sum: int, expected_sum: int, error: int}
    """
    actual_sum = sum(c['premium_monthly_coverage'] for c in coverage_premiums)
    error = abs(actual_sum - expected_sum)
    match = error <= tolerance

    return {
        'match': match,
        'actual_sum': actual_sum,
        'expected_sum': expected_sum,
        'error': error,
        'status': 'MATCH' if match else 'MISMATCH'
    }


def write_coverage_premium_jsonl(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write coverage_premium_quote records to JSONL"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')

    print(f"Written {len(records)} coverage_premium_quote records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build coverage_premium_quote from API responses")
    parser.add_argument(
        "--api-response",
        required=True,
        help="Path to API response JSON file"
    )
    parser.add_argument(
        "--multiplier-excel",
        default="/Users/cheollee/inca-rag-scope/data/sources/insurers/4. 일반보험요율예시.xlsx",
        help="Path to multiplier Excel file"
    )
    parser.add_argument(
        "--output",
        default="/tmp/coverage_premium_quote.jsonl",
        help="Path to output coverage_premium_quote JSONL file"
    )

    args = parser.parse_args()

    print(f"Loading API response: {args.api_response}")
    with open(args.api_response, 'r', encoding='utf-8') as f:
        api_response = json.load(f)

    print(f"Loading multipliers: {args.multiplier_excel}")
    multipliers = load_multiplier_excel(args.multiplier_excel)
    print(f"Loaded {len(multipliers)} multiplier records")

    print("Parsing NO_REFUND coverage premiums...")
    no_refund_records = parse_api_response_coverage_premium(api_response)
    print(f"Parsed {len(no_refund_records)} NO_REFUND coverage premiums")

    # Verify sum
    if no_refund_records and 'quotes' in api_response and len(api_response['quotes']) > 0:
        quote = api_response['quotes'][0]
        expected_sum = quote['monthly_prem_sum']
        verification = verify_sum_match(no_refund_records, expected_sum)
        print(f"\nSum verification: {verification['status']}")
        print(f"  Expected: {verification['expected_sum']}")
        print(f"  Actual: {verification['actual_sum']}")
        print(f"  Error: {verification['error']}")

    print("\nGenerating GENERAL coverage premiums...")
    general_records = generate_general_coverage_premiums(no_refund_records, multipliers)
    print(f"Generated {len(general_records)} GENERAL coverage premiums")

    # Combine
    all_records = no_refund_records + general_records

    write_coverage_premium_jsonl(all_records, args.output)

    # Sample output
    print("\nSample coverage_premium_quote records:")
    for record in all_records[:4]:
        print(f"  {record['plan_variant']} | {record['coverage_code']} | {record['premium_monthly_coverage']}원")
