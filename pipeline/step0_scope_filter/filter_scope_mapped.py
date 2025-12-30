#!/usr/bin/env python3
"""
STEP NEXT-18D: Filter Existing scope_mapped.csv Files
======================================================

Purpose:
    Remove condition sentences and non-coverage entries from
    EXISTING scope_mapped.csv files.

    This is simpler and more reliable than re-parsing PDFs.

Usage:
    python -m pipeline.step0_scope_filter.filter_scope_mapped --insurer kb
    python -m pipeline.step0_scope_filter.filter_scope_mapped --all
"""

import argparse
import csv
import re
from pathlib import Path
from typing import List, Dict, Tuple


# Exclusion patterns (ANY match → DROP)
EXCLUSION_PATTERNS = [
    # Condition sentences
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_SENTENCE'),
    (r'(인|한)\s*경우$', 'CONDITION_SENTENCE'),
    (r'시$', 'CONDITION_SENTENCE'),
    (r'때$', 'CONDITION_SENTENCE'),
    (r'한하여$', 'CONDITION_SENTENCE'),

    # Sentence ending
    (r'다\.$', 'SENTENCE_ENDING'),
    (r'습니다\.$', 'SENTENCE_ENDING'),

    # Explanation phrases (from analysis)
    (r'보장개시일\s*이후', 'EXPLANATION_PHRASE'),
    (r'계약일로부터', 'EXPLANATION_PHRASE'),

    # Non-coverage markers
    (r'납입면제대상', 'PREMIUM_WAIVER'),
    (r'대상보장', 'NON_COVERAGE'),
    (r'대상담보', 'NON_COVERAGE'),
]


def should_exclude_row(coverage_name_raw: str) -> Tuple[bool, str]:
    """
    Check if coverage name should be excluded.

    Returns:
        (should_exclude, reason)
    """
    for pattern, reason in EXCLUSION_PATTERNS:
        if re.search(pattern, coverage_name_raw):
            return True, reason

    return False, ''


def filter_scope_mapped(input_csv: Path, output_csv: Path) -> Dict:
    """
    Filter scope_mapped.csv to remove non-coverage entries.

    Args:
        input_csv: Input scope_mapped.csv path
        output_csv: Output (filtered) scope_mapped.csv path

    Returns:
        Statistics dict
    """
    if not input_csv.exists():
        print(f"[ERROR] Input file not found: {input_csv}")
        return {}

    # Read input
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter
    kept_rows = []
    filtered_rows = []

    for row in rows:
        coverage_name = row['coverage_name_raw']
        should_exclude, reason = should_exclude_row(coverage_name)

        if should_exclude:
            filtered_rows.append({
                'coverage_name_raw': coverage_name,
                'reason': reason
            })
        else:
            kept_rows.append(row)

    # Write filtered output
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        if kept_rows:
            writer = csv.DictWriter(f, fieldnames=kept_rows[0].keys())
            writer.writeheader()
            writer.writerows(kept_rows)

    stats = {
        'input_total': len(rows),
        'kept': len(kept_rows),
        'filtered': len(filtered_rows),
        'filtered_rows': filtered_rows
    }

    return stats


def main():
    parser = argparse.ArgumentParser(description='Filter scope_mapped.csv files')
    parser.add_argument('--insurer', type=str, help='Insurer name (or use --all)')
    parser.add_argument('--all', action='store_true', help='Process all insurers')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]

    if args.all:
        insurers = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']
    elif args.insurer:
        insurers = [args.insurer]
    else:
        print("[ERROR] Specify --insurer or --all")
        return

    print(f"[Step0 Scope Filter]")
    print(f"Filtering scope_mapped.csv for {len(insurers)} insurer(s)\n")

    all_stats = {}

    for insurer in insurers:
        input_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped.csv'
        output_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped_filtered.csv'

        print(f"[{insurer}]")

        stats = filter_scope_mapped(input_csv, output_csv)

        if stats:
            print(f"  Input: {stats['input_total']} rows")
            print(f"  Kept: {stats['kept']} rows")
            print(f"  Filtered: {stats['filtered']} rows")

            if stats['filtered'] > 0:
                print(f"  Filtered examples:")
                for row in stats['filtered_rows'][:3]:
                    print(f"    - [{row['reason']}] {row['coverage_name_raw']}")

            all_stats[insurer] = stats
            print()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_input = sum(s['input_total'] for s in all_stats.values())
    total_kept = sum(s['kept'] for s in all_stats.values())
    total_filtered = sum(s['filtered'] for s in all_stats.values())

    print(f"Total input: {total_input}")
    print(f"Total kept: {total_kept} ({total_kept/total_input*100:.1f}%)")
    print(f"Total filtered: {total_filtered} ({total_filtered/total_input*100:.1f}%)")

    print(f"\n✓ Filtered scope_mapped.csv files saved to *_scope_mapped_filtered.csv")
    print(f"  Next step: Rename filtered files to replace originals")


if __name__ == '__main__':
    main()
