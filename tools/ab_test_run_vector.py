"""
STEP NEXT-V-01: A/B Test - Vector (B) Runner

Run vector-enriched customer_view_builder on coverage_cards.

Constitutional Rules:
- NO LLM usage
- Vector search for candidate retrieval
- Deterministic pattern matching
- Evidence traceability
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from core.customer_view_builder_v2 import build_customer_view_v2


def run_vector(axis: str, output_path: Path, index_dir: str = "data/vector_index/v1") -> Dict[str, Any]:
    """
    Run vector-enriched customer_view builder.

    Args:
        axis: Insurance axis (e.g., "samsung", "meritz")
        output_path: Output JSONL path
        index_dir: Vector index directory

    Returns:
        Summary stats
    """
    # Load coverage_cards
    cards_path = Path(f"data/compare/{axis}_coverage_cards.jsonl")

    if not cards_path.exists():
        raise FileNotFoundError(f"Coverage cards not found: {cards_path}")

    cards = []
    with open(cards_path, 'r', encoding='utf-8') as f:
        for line in f:
            cards.append(json.loads(line))

    print(f"Loaded {len(cards)} coverage cards from {cards_path}")

    # Check if vector index exists
    index_path = Path(index_dir) / f"{axis}__chunks.jsonl"
    if not index_path.exists():
        raise FileNotFoundError(f"Vector index not found: {index_path}")

    # Process each card
    results = []
    stats = {
        'total': 0,
        'benefit_description_nonempty': 0,
        'payment_type_detected': 0,
        'limit_conditions_nonempty': 0,
        'exclusion_notes_nonempty': 0,
        'vector_search_failed': 0
    }

    for card in cards:
        coverage_code = card.get('coverage_code', '')
        canonical_name = card.get('canonical_name', '')

        # Build customer_view using vector method
        customer_view = build_customer_view_v2(
            axis=axis,
            coverage_code=coverage_code,
            coverage_name=canonical_name,
            index_dir=index_dir
        )

        # Aggregate stats
        stats['total'] += 1
        if customer_view['benefit_description'] and customer_view['benefit_description'] != '명시 없음':
            stats['benefit_description_nonempty'] += 1
        if customer_view['payment_type']:
            stats['payment_type_detected'] += 1
        if customer_view['limit_conditions']:
            stats['limit_conditions_nonempty'] += 1
        if customer_view['exclusion_notes']:
            stats['exclusion_notes_nonempty'] += 1
        if 'failed' in customer_view.get('extraction_notes', '').lower():
            stats['vector_search_failed'] += 1

        # Store result
        result = {
            'axis': axis,
            'coverage_code': coverage_code,
            'canonical_name': canonical_name,
            'customer_view': customer_view,
            'method': 'vector_enhanced'
        }
        results.append(result)

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"Wrote {len(results)} results to {output_path}")
    print(f"Stats: {stats}")

    return stats


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tools.ab_test_run_vector <axis>")
        print("Example: python -m tools.ab_test_run_vector samsung")
        sys.exit(1)

    axis = sys.argv[1]
    output_path = Path(f"output/ab_test/B_{axis}_customer_view.jsonl")

    stats = run_vector(axis, output_path)

    print("\n=== Vector (B) Summary ===")
    print(f"Total: {stats['total']}")
    print(f"Benefit Description Nonempty: {stats['benefit_description_nonempty']} ({stats['benefit_description_nonempty']/stats['total']*100:.1f}%)")
    print(f"Payment Type Detected: {stats['payment_type_detected']} ({stats['payment_type_detected']/stats['total']*100:.1f}%)")
    print(f"Limit Conditions Nonempty: {stats['limit_conditions_nonempty']} ({stats['limit_conditions_nonempty']/stats['total']*100:.1f}%)")
    print(f"Exclusion Notes Nonempty: {stats['exclusion_notes_nonempty']} ({stats['exclusion_notes_nonempty']/stats['total']*100:.1f}%)")
    print(f"Vector Search Failed: {stats['vector_search_failed']}")
