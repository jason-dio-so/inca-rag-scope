"""
Step 8: Multi-Insurer Comparison (All Insurers)

입력:
- data/compare/*_coverage_cards.jsonl (모든 보험사)

출력:
- data/compare/all_insurers_matrix.json
- data/compare/all_insurers_stats.json
- reports/all_insurers_overview.md
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.compare_types import CoverageCard


def load_all_cards(cards_dir: Path) -> Dict[str, List[CoverageCard]]:
    """
    모든 보험사의 coverage cards 로드

    Returns:
        Dict[insurer_name, List[CoverageCard]]
    """
    all_cards = {}

    for cards_file in cards_dir.glob("*_coverage_cards.jsonl"):
        insurer = cards_file.stem.replace("_coverage_cards", "")

        cards = []
        with open(cards_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    card_data = json.loads(line)
                    card = CoverageCard.from_dict(card_data)
                    cards.append(card)

        all_cards[insurer] = cards
        print(f"  Loaded {insurer}: {len(cards)} coverages")

    return all_cards


def build_canonical_matrix(all_cards: Dict[str, List[CoverageCard]]) -> List[Dict]:
    """
    Canonical coverage_code 기준으로 보험사 분포 매트릭스 생성

    Returns:
        List of matrix rows, sorted by coverage_code
    """
    # coverage_code별로 보험사 정보 수집
    code_to_insurers = defaultdict(lambda: {
        'canonical_name': '',
        'insurers': {}
    })

    for insurer, cards in all_cards.items():
        for card in cards:
            if card.coverage_code:  # matched only
                code = card.coverage_code

                # Set canonical name (should be same across insurers)
                if not code_to_insurers[code]['canonical_name']:
                    code_to_insurers[code]['canonical_name'] = card.coverage_name_canonical

                # Add insurer info
                code_to_insurers[code]['insurers'][insurer] = {
                    'present': True,
                    'raw_name': card.coverage_name_raw,
                    'matched': card.mapping_status == 'matched',
                    'evidence_found': card.evidence_status == 'found'
                }

    # Add present=False for insurers without this coverage
    all_insurer_names = set(all_cards.keys())
    for code, data in code_to_insurers.items():
        present_insurers = set(data['insurers'].keys())
        absent_insurers = all_insurer_names - present_insurers

        for insurer in absent_insurers:
            data['insurers'][insurer] = {
                'present': False
            }

    # Convert to list and sort by coverage_code
    matrix = []
    for code in sorted(code_to_insurers.keys()):
        data = code_to_insurers[code]
        matrix.append({
            'coverage_code': code,
            'canonical_name': data['canonical_name'],
            'insurers': data['insurers']
        })

    return matrix


def calculate_stats(all_cards: Dict[str, List[CoverageCard]], matrix: List[Dict]) -> Dict:
    """
    분포 통계 계산
    """
    all_codes = {row['coverage_code'] for row in matrix}

    # Insurer별 code 집합
    insurer_codes = {}
    for insurer, cards in all_cards.items():
        insurer_codes[insurer] = {card.coverage_code for card in cards if card.coverage_code}

    # 공통 codes (모든 보험사에 있음)
    if insurer_codes:
        codes_common_to_all = set.intersection(*insurer_codes.values())
    else:
        codes_common_to_all = set()

    # 각 보험사별 unique codes
    codes_unique_per_insurer = {}
    for insurer, codes in insurer_codes.items():
        other_codes = set()
        for other_insurer, other_codes_set in insurer_codes.items():
            if other_insurer != insurer:
                other_codes.update(other_codes_set)

        codes_unique_per_insurer[insurer] = list(codes - other_codes)

    # Insurer별 unmatched rate
    unmatched_rate_per_insurer = {}
    for insurer, cards in all_cards.items():
        total = len(cards)
        unmatched = sum(1 for card in cards if card.mapping_status == 'unmatched')
        unmatched_rate_per_insurer[insurer] = {
            'total': total,
            'unmatched': unmatched,
            'unmatched_rate': round(unmatched / total * 100, 1) if total > 0 else 0
        }

    # Coverage code별 insurer 수
    insurer_count_per_code = {}
    for row in matrix:
        code = row['coverage_code']
        count = sum(1 for ins_data in row['insurers'].values() if ins_data.get('present', False))
        insurer_count_per_code[code] = count

    stats = {
        'total_canonical_codes': len(all_codes),
        'total_insurers': len(all_cards),
        'insurer_count_per_code': insurer_count_per_code,
        'codes_common_to_all': list(sorted(codes_common_to_all)),
        'codes_unique_per_insurer': codes_unique_per_insurer,
        'unmatched_rate_per_insurer': unmatched_rate_per_insurer
    }

    return stats


def generate_markdown_report(
    all_cards: Dict[str, List[CoverageCard]],
    matrix: List[Dict],
    stats: Dict,
    output_md: str
):
    """
    Human-readable overview 리포트 생성 (fact-only)
    """
    md_lines = []

    # Title
    md_lines.append("# Multi-Insurer Coverage Overview")
    md_lines.append("")
    md_lines.append(f"**Total Insurers**: {stats['total_insurers']}")
    md_lines.append(f"**Total Canonical Codes**: {stats['total_canonical_codes']}")
    md_lines.append("")

    # Summary by Insurer
    md_lines.append("## Coverage Summary by Insurer")
    md_lines.append("")
    md_lines.append("| Insurer | Total | Matched | Unmatched | Unmatched % | Evidence Found |")
    md_lines.append("|---|---|---|---|---|---|")

    for insurer in sorted(all_cards.keys()):
        cards = all_cards[insurer]
        total = len(cards)
        matched = sum(1 for c in cards if c.mapping_status == 'matched')
        unmatched = sum(1 for c in cards if c.mapping_status == 'unmatched')
        evidence_found = sum(1 for c in cards if c.evidence_status == 'found')
        unmatched_pct = stats['unmatched_rate_per_insurer'][insurer]['unmatched_rate']

        md_lines.append(
            f"| {insurer} | {total} | {matched} | {unmatched} | {unmatched_pct}% | {evidence_found} |"
        )

    md_lines.append("")

    # Common Coverages
    md_lines.append("## Common Coverages (Present in All Insurers)")
    md_lines.append("")
    md_lines.append(f"**Count**: {len(stats['codes_common_to_all'])}")
    md_lines.append("")

    if stats['codes_common_to_all']:
        md_lines.append("| Code | Canonical Name |")
        md_lines.append("|---|---|")
        for code in stats['codes_common_to_all']:
            # Find canonical name from matrix
            canonical_name = next((row['canonical_name'] for row in matrix if row['coverage_code'] == code), '')
            md_lines.append(f"| {code} | {canonical_name} |")
        md_lines.append("")
    else:
        md_lines.append("*No coverages common to all insurers*")
        md_lines.append("")

    # Unique Coverages per Insurer
    md_lines.append("## Unique Coverages (Only in One Insurer)")
    md_lines.append("")

    for insurer in sorted(all_cards.keys()):
        unique_codes = stats['codes_unique_per_insurer'].get(insurer, [])
        md_lines.append(f"### {insurer.upper()}")
        md_lines.append("")
        md_lines.append(f"**Count**: {len(unique_codes)}")
        md_lines.append("")

        if unique_codes:
            md_lines.append("| Code | Canonical Name |")
            md_lines.append("|---|---|")
            for code in unique_codes:
                canonical_name = next((row['canonical_name'] for row in matrix if row['coverage_code'] == code), '')
                md_lines.append(f"| {code} | {canonical_name} |")
            md_lines.append("")
        else:
            md_lines.append("*No unique coverages*")
            md_lines.append("")

    # Coverage Distribution
    md_lines.append("## Coverage Code Distribution")
    md_lines.append("")
    md_lines.append("| Code | Canonical Name | Insurer Count | Insurers |")
    md_lines.append("|---|---|---|---|")

    for row in matrix:
        code = row['coverage_code']
        canonical = row['canonical_name']
        count = stats['insurer_count_per_code'][code]

        # List insurers with this coverage
        present_insurers = [
            ins for ins, data in row['insurers'].items()
            if data.get('present', False)
        ]
        insurers_str = ", ".join(sorted(present_insurers))

        md_lines.append(f"| {code} | {canonical} | {count} | {insurers_str} |")

    md_lines.append("")

    # Write report
    Path(output_md).parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Compare all insurers')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent

    # Input
    cards_dir = base_dir / "data" / "compare"

    # Output
    output_matrix = base_dir / "data" / "compare" / "all_insurers_matrix.json"
    output_stats = base_dir / "data" / "compare" / "all_insurers_stats.json"
    output_report = base_dir / "reports" / "all_insurers_overview.md"

    print(f"[Step 8] Multi-Insurer Comparison")
    print(f"[Step 8] Loading coverage cards from: {cards_dir}")

    # Load all cards
    all_cards = load_all_cards(cards_dir)

    if not all_cards:
        print("ERROR: No coverage cards found")
        return

    print(f"\n[Step 8] Building canonical matrix...")
    matrix = build_canonical_matrix(all_cards)

    print(f"[Step 8] Calculating statistics...")
    stats = calculate_stats(all_cards, matrix)

    print(f"[Step 8] Generating reports...")

    # Save matrix
    output_matrix.parent.mkdir(parents=True, exist_ok=True)
    with open(output_matrix, 'w', encoding='utf-8') as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)

    # Save stats
    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Generate markdown report
    generate_markdown_report(all_cards, matrix, stats, str(output_report))

    print(f"\n[Step 8] Multi-insurer comparison completed:")
    print(f"  - Total insurers: {stats['total_insurers']}")
    print(f"  - Total canonical codes: {stats['total_canonical_codes']}")
    print(f"  - Common to all: {len(stats['codes_common_to_all'])}")
    print(f"\n✓ Matrix: {output_matrix}")
    print(f"✓ Stats: {output_stats}")
    print(f"✓ Report: {output_report}")


if __name__ == "__main__":
    main()
