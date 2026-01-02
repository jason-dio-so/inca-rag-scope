#!/usr/bin/env python3
"""
STEP NEXT-74: KPI Report - 지급유형 / 한도 추출률

보험사별 KPI 추출 통계:
- 지급유형 추출률 (by payment_type)
- 한도 추출률
- UNKNOWN 비율
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def load_slim_cards(jsonl_path: Path) -> List[dict]:
    """Load slim cards from JSONL"""
    cards = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            cards.append(json.loads(line))
    return cards


def analyze_kpi_stats(cards: List[dict]) -> dict:
    """
    Analyze KPI extraction statistics

    Returns:
        {
            'total_count': int,
            'payment_type_stats': {type: count},
            'payment_type_extracted': int,  # non-UNKNOWN
            'limit_extracted': int,
            'kpi_ref_stats': {ref_count: count}
        }
    """
    total = len(cards)
    payment_type_stats = defaultdict(int)
    limit_extracted = 0
    kpi_ref_stats = defaultdict(int)

    for card in cards:
        kpi = card.get('kpi_summary')
        if not kpi:
            payment_type_stats['MISSING'] += 1
            continue

        # Payment type
        payment_type = kpi.get('payment_type', 'UNKNOWN')
        payment_type_stats[payment_type] += 1

        # Limit summary
        if kpi.get('limit_summary'):
            limit_extracted += 1

        # KPI refs
        kpi_refs = kpi.get('kpi_evidence_refs', [])
        kpi_ref_stats[len(kpi_refs)] += 1

    # Count non-UNKNOWN payment types
    payment_type_extracted = sum(
        count for ptype, count in payment_type_stats.items()
        if ptype not in ('UNKNOWN', 'MISSING')
    )

    return {
        'total_count': total,
        'payment_type_stats': dict(payment_type_stats),
        'payment_type_extracted': payment_type_extracted,
        'limit_extracted': limit_extracted,
        'kpi_ref_stats': dict(kpi_ref_stats)
    }


def print_report(insurer: str, stats: dict):
    """Print formatted KPI report"""
    total = stats['total_count']

    print(f"\n{'='*60}")
    print(f"KPI Extraction Report: {insurer.upper()}")
    print(f"{'='*60}\n")

    print(f"Total Coverages: {total}")
    print()

    # Payment Type Stats
    print("지급유형 (Payment Type):")
    print("-" * 40)
    payment_type_stats = stats['payment_type_stats']
    payment_type_extracted = stats['payment_type_extracted']

    # Sort by count (desc)
    for ptype in sorted(payment_type_stats.keys(), key=lambda k: payment_type_stats[k], reverse=True):
        count = payment_type_stats[ptype]
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {ptype:20s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n  Extracted (non-UNKNOWN): {payment_type_extracted}/{total} ({payment_type_extracted/total*100:.1f}%)")
    print()

    # Limit Summary Stats
    limit_extracted = stats['limit_extracted']
    limit_pct = (limit_extracted / total * 100) if total > 0 else 0
    print(f"한도 (Limit Summary):")
    print("-" * 40)
    print(f"  Extracted: {limit_extracted}/{total} ({limit_pct:.1f}%)")
    print(f"  Missing:   {total - limit_extracted}/{total} ({100 - limit_pct:.1f}%)")
    print()

    # KPI Ref Stats
    print("KPI Evidence Refs:")
    print("-" * 40)
    kpi_ref_stats = stats['kpi_ref_stats']
    for ref_count in sorted(kpi_ref_stats.keys()):
        count = kpi_ref_stats[ref_count]
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {ref_count} refs: {count:3d} ({pct:5.1f}%)")
    print()

    # Quality Gates
    print("Quality Gates:")
    print("-" * 40)
    unknown_count = payment_type_stats.get('UNKNOWN', 0)
    unknown_pct = (unknown_count / total * 100) if total > 0 else 0

    print(f"  ✓ All coverages have kpi_summary: {payment_type_stats.get('MISSING', 0) == 0}")
    print(f"  ✓ Payment type UNKNOWN ≤ 30%: {unknown_pct:.1f}% {'✓' if unknown_pct <= 30 else '✗'}")
    print(f"  ✓ Limit extraction ≥ 50%: {limit_pct:.1f}% {'✓' if limit_pct >= 50 else '✗'}")
    print(f"  ✓ All KPI traceable (refs > 0): {kpi_ref_stats.get(0, 0) == 0 or unknown_count == kpi_ref_stats.get(0, 0)}")
    print()


def main():
    parser = argparse.ArgumentParser(description="KPI Extraction Report")
    parser.add_argument('--insurer', required=True, help='Insurer name')
    parser.add_argument('--cards-path', help='Custom path to slim cards JSONL')

    args = parser.parse_args()

    # Default path
    if args.cards_path:
        cards_path = Path(args.cards_path)
    else:
        cards_path = Path(__file__).parent.parent / 'data' / 'compare' / f'{args.insurer}_coverage_cards_slim.jsonl'

    if not cards_path.exists():
        print(f"Error: Slim cards not found at {cards_path}")
        return 1

    # Load cards
    cards = load_slim_cards(cards_path)

    # Analyze
    stats = analyze_kpi_stats(cards)

    # Print report
    print_report(args.insurer, stats)

    return 0


if __name__ == '__main__':
    exit(main())
