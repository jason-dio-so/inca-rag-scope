"""
STEP NEXT-V-01: A/B Test - Baseline (A) Runner

Run baseline customer_view_builder (string matching) on coverage_cards.

Constitutional Rules:
- NO LLM usage
- NO Step1/Step2 modification
- Read-only access to coverage_cards.jsonl
- Deterministic only
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from core.customer_view_builder import build_customer_view


def run_baseline(axis: str, output_path: Path) -> Dict[str, Any]:
    """
    Run baseline customer_view builder.

    Args:
        axis: Insurance axis (e.g., "samsung", "meritz")
        output_path: Output JSONL path

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

    # Process each card
    results = []
    stats = {
        'total': 0,
        'benefit_description_nonempty': 0,
        'payment_type_detected': 0,
        'limit_conditions_nonempty': 0,
        'exclusion_notes_nonempty': 0
    }

    for card in cards:
        coverage_code = card.get('coverage_code', '')
        canonical_name = card.get('canonical_name', '')
        evidences = card.get('evidences', [])

        # Build customer_view using baseline method (KB NEXT PATCH: add insurer/coverage_name_raw)
        customer_view = build_customer_view(
            evidences,
            insurer=card.get('insurer'),
            coverage_name_raw=card.get('coverage_name_raw')
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

        # Store result
        result = {
            'axis': axis,
            'coverage_code': coverage_code,
            'canonical_name': canonical_name,
            'customer_view': customer_view,
            'method': 'baseline_string_match'
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
        print("Usage: python -m tools.ab_test_run_baseline <axis>")
        print("Example: python -m tools.ab_test_run_baseline samsung")
        sys.exit(1)

    axis = sys.argv[1]
    output_path = Path(f"output/ab_test/A_{axis}_customer_view.jsonl")

    stats = run_baseline(axis, output_path)

    print("\n=== Baseline (A) Summary ===")
    print(f"Total: {stats['total']}")
    print(f"Benefit Description Nonempty: {stats['benefit_description_nonempty']} ({stats['benefit_description_nonempty']/stats['total']*100:.1f}%)")
    print(f"Payment Type Detected: {stats['payment_type_detected']} ({stats['payment_type_detected']/stats['total']*100:.1f}%)")
    print(f"Limit Conditions Nonempty: {stats['limit_conditions_nonempty']} ({stats['limit_conditions_nonempty']/stats['total']*100:.1f}%)")
    print(f"Exclusion Notes Nonempty: {stats['exclusion_notes_nonempty']} ({stats['exclusion_notes_nonempty']/stats['total']*100:.1f}%)")
