"""
STEP NEXT-66: Enrich Coverage Cards with Vector Search

Read existing coverage_cards.jsonl and enrich customer_view using vector search.

Usage:
    python -m scripts.enrich_cards_with_vector --axis samsung
"""

import json
import argparse
from pathlib import Path
from tqdm import tqdm

from core.customer_view_builder_v2 import build_customer_view_v2


def enrich_coverage_cards(axis: str, cards_path: Path, output_path: Path, index_dir: str):
    """
    Enrich coverage cards with vector-based customer_view.

    Args:
        axis: Insurance axis
        cards_path: Input coverage_cards.jsonl path
        output_path: Output path (enriched cards)
        index_dir: Vector index directory
    """
    print(f"=== Enriching {axis} coverage cards ===")
    print(f"Input: {cards_path}")
    print(f"Output: {output_path}")

    # Check if vector index exists
    index_path = Path(index_dir) / f"{axis}__chunks.jsonl"
    if not index_path.exists():
        print(f"⚠️  Vector index not found: {index_path}")
        print(f"   Skipping enrichment (will keep existing customer_view)")
        # Just copy the file
        import shutil
        shutil.copy(cards_path, output_path)
        return

    # Read cards
    cards = []
    with open(cards_path, 'r', encoding='utf-8') as f:
        for line in f:
            cards.append(json.loads(line))

    print(f"Loaded {len(cards)} cards")

    # Enrich each card
    enriched_cards = []
    enriched_count = 0

    for card in tqdm(cards, desc="Enriching"):
        coverage_code = card.get('coverage_code', '')
        coverage_name = card.get('coverage_name_canonical', '')

        if not coverage_name:
            # Skip if no canonical name
            enriched_cards.append(card)
            continue

        # Build customer_view with vector search
        new_customer_view = build_customer_view_v2(
            axis=axis,
            coverage_code=coverage_code,
            coverage_name=coverage_name,
            index_dir=index_dir
        )

        # Replace customer_view
        card['customer_view'] = new_customer_view
        enriched_cards.append(card)

        # Count enrichment (check if we got non-trivial data)
        if (new_customer_view.get('benefit_description') != '명시 없음' or
            new_customer_view.get('payment_type') is not None or
            len(new_customer_view.get('limit_conditions', [])) > 0):
            enriched_count += 1

    # Write enriched cards
    with open(output_path, 'w', encoding='utf-8') as f:
        for card in enriched_cards:
            f.write(json.dumps(card, ensure_ascii=False) + '\n')

    print(f"\n✅ Enrichment complete:")
    print(f"   Total cards: {len(enriched_cards)}")
    print(f"   Enriched: {enriched_count} ({enriched_count/len(enriched_cards)*100:.1f}%)")
    print(f"   Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Enrich coverage cards with vector search")
    parser.add_argument(
        "--axis", type=str, required=True,
        help="Insurance axis (e.g., samsung, meritz)"
    )
    parser.add_argument(
        "--cards-dir", type=str, default="data/compare",
        help="Coverage cards directory"
    )
    parser.add_argument(
        "--output-dir", type=str, default="data/compare",
        help="Output directory (same as input by default)"
    )
    parser.add_argument(
        "--index-dir", type=str, default="data/vector_index/v1",
        help="Vector index directory"
    )

    args = parser.parse_args()

    # Determine axis name for file paths
    if args.axis in ["lotte_male", "lotte_female"]:
        axis_file = args.axis
    else:
        axis_file = args.axis

    cards_path = Path(args.cards_dir) / f"{axis_file}_coverage_cards.jsonl"
    output_path = Path(args.output_dir) / f"{axis_file}_coverage_cards.jsonl"

    if not cards_path.exists():
        print(f"❌ Cards file not found: {cards_path}")
        return

    enrich_coverage_cards(args.axis, cards_path, output_path, args.index_dir)


if __name__ == "__main__":
    main()
