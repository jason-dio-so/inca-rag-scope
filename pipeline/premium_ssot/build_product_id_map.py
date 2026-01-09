"""
STEP NEXT-Q: Build product_id_map from compare_rows_v1
Generate product ID mapping (compare_product_id ↔ premium_product_id)

Rules:
1. compare_product_id = compare_rows_v1.product_key
2. premium_product_id = DERIVED or MANUAL mapping
3. NO estimation - missing mappings are excluded
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
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


def extract_unique_products(compare_rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract unique (insurer_key, product_key) from compare_rows_v1

    Args:
        compare_rows: compare_rows_v1 records

    Returns:
        List[Dict]: Unique products [{insurer_key, compare_product_id}]
    """
    products = {}

    for row in compare_rows:
        identity = row['identity']
        insurer_key = identity['insurer_key']
        product_key = identity['product_key']

        key = (insurer_key, product_key)
        if key not in products:
            products[key] = {
                'insurer_key': insurer_key,
                'compare_product_id': product_key
            }

    return list(products.values())


def build_product_id_map(
    products: List[Dict[str, str]],
    mapping_rules: Dict[str, str] | None = None,
    as_of_date: str = None
) -> List[Dict[str, Any]]:
    """
    Build product_id_map records

    Args:
        products: Unique products from compare_rows_v1
        mapping_rules: Optional manual mapping {compare_product_id: premium_product_id}
        as_of_date: Mapping date (defaults to today)

    Returns:
        List[Dict]: product_id_map records
    """
    if as_of_date is None:
        as_of_date = datetime.now().strftime('%Y-%m-%d')

    mapping_rules = mapping_rules or {}

    records = []

    for product in products:
        insurer_key = product['insurer_key']
        compare_product_id = product['compare_product_id']

        # Check manual mapping
        if compare_product_id in mapping_rules:
            premium_product_id = mapping_rules[compare_product_id]
            source = 'MANUAL'
            evidence_ref = 'mapping_rules parameter'
        else:
            # DERIVED: Use compare_product_id as-is (simplest case)
            # TODO: Add more sophisticated derivation logic if needed
            premium_product_id = compare_product_id
            source = 'DERIVED'
            evidence_ref = 'identity mapping (compare_product_id == premium_product_id)'

        records.append({
            'insurer_key': insurer_key,
            'compare_product_id': compare_product_id,
            'premium_product_id': premium_product_id,
            'as_of_date': as_of_date,
            'source': source,
            'evidence_ref': evidence_ref
        })

    return records


def write_product_id_map_jsonl(records: List[Dict[str, Any]], output_path: str) -> None:
    """Write product_id_map records to JSONL"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"Written {len(records)} product_id_map records to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build product_id_map from compare_rows_v1")
    parser.add_argument(
        "--compare-rows",
        default="/Users/cheollee/inca-rag-scope/data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows_v1 JSONL file"
    )
    parser.add_argument(
        "--output",
        default="/tmp/product_id_map.jsonl",
        help="Path to output product_id_map JSONL file"
    )
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Mapping as-of date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    print(f"Loading compare_rows_v1: {args.compare_rows}")
    compare_rows = load_jsonl(args.compare_rows)
    print(f"Loaded {len(compare_rows)} compare_rows_v1 records")

    print("Extracting unique products...")
    products = extract_unique_products(compare_rows)
    print(f"Found {len(products)} unique products")

    print("Building product_id_map...")
    # TODO: Load manual mapping rules from external file if needed
    mapping_rules = {
        # Example manual mappings:
        # "samsung__삼성화재건강보험": "samsung__ci_insurance_2024",
    }

    product_id_map = build_product_id_map(products, mapping_rules, args.as_of_date)

    write_product_id_map_jsonl(product_id_map, args.output)

    # Print sample
    print("\nSample product_id_map records:")
    for record in product_id_map[:5]:
        print(f"  {record['insurer_key']}: {record['compare_product_id']} → {record['premium_product_id']} ({record['source']})")
