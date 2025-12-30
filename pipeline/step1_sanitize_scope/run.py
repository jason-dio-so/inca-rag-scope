#!/usr/bin/env python3
"""
STEP NEXT-18D: Global Scope Sanitization
=========================================

Purpose:
    Remove condition sentences and non-coverage entries from scope_mapped.csv files.

    Root cause fix: UNCONFIRMED proliferation is due to scope contamination,
    NOT amount extraction failure.

Rules (ANY match → DROP):
    - ~으로 진단확정된 경우
    - ~인 경우, ~일 때, ~시
    - 지급 조건, 지급 사유, 보장 내용
    - Sentence endings (문장형 종결)
    - coverage_code IS NULL AND sentence pattern
    - Parentheses-only explanations

Usage:
    python -m pipeline.step1_sanitize_scope.run --all
    python -m pipeline.step1_sanitize_scope.run --insurer kb
"""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple


# DROP patterns (ANY match → DROP row)
DROP_PATTERNS = [
    # Condition sentences (highest priority)
    (r'(으로|로)\s*진단확정된\s*경우', 'CONDITION_DIAGNOSIS'),
    (r'(인|한)\s*경우$', 'CONDITION_CASE'),
    (r'일\s*때$', 'CONDITION_WHEN'),
    (r'시$', 'CONDITION_TIME'),

    # Payment/benefit explanation sentences
    (r'지급\s*(조건|사유|내용)', 'PAYMENT_EXPLANATION'),
    (r'보장\s*(개시일|내용)', 'COVERAGE_EXPLANATION'),

    # Sentence markers
    (r'이후에$', 'SENTENCE_MARKER'),
    (r'경우$', 'SENTENCE_ENDING'),

    # Non-coverage administrative items
    (r'납입면제.*대상', 'PREMIUM_WAIVER'),
    (r'대상\s*(담보|보장)', 'TARGET_NON_COVERAGE'),

    # Parentheses-only content
    (r'^\([^)]+\)$', 'PARENTHESES_ONLY'),
]


def should_drop_row(coverage_name_raw: str, coverage_code: str, mapping_status: str) -> Tuple[bool, str]:
    """
    Determine if row should be dropped from scope.

    Args:
        coverage_name_raw: Coverage name from proposal
        coverage_code: Canonical coverage code (may be empty)
        mapping_status: Mapping status (matched/unmatched)

    Returns:
        (should_drop, reason)
    """
    # Rule 1: Check DROP patterns
    for pattern, reason in DROP_PATTERNS:
        if re.search(pattern, coverage_name_raw):
            return True, reason

    # Rule 2: If unmatched AND looks like sentence (has sentence markers)
    if mapping_status == 'unmatched' or not coverage_code:
        # Check for sentence-like patterns
        sentence_markers = ['~', '으로', '는', '는지', '된', '인']
        if any(marker in coverage_name_raw for marker in sentence_markers):
            # Additional check: long text (>20 chars) + no typical coverage keywords
            if len(coverage_name_raw) > 20:
                coverage_keywords = ['진단비', '수술비', '입원비', '사망', '후유장해', '치료비']
                if not any(kw in coverage_name_raw for kw in coverage_keywords):
                    return True, 'SENTENCE_LIKE_UNMATCHED'

    return False, ''


def sanitize_scope_mapped(
    input_csv: Path,
    output_csv: Path,
    filtered_out_jsonl: Path
) -> Dict:
    """
    Sanitize scope_mapped.csv by removing non-coverage entries.

    Args:
        input_csv: Input scope_mapped.csv
        output_csv: Output sanitized CSV
        filtered_out_jsonl: Filtered-out entries (audit trail)

    Returns:
        Statistics dict
    """
    if not input_csv.exists():
        return {'error': 'FILE_NOT_FOUND'}

    # Read input
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Sanitize
    kept_rows = []
    dropped_rows = []

    for row in rows:
        coverage_name = row.get('coverage_name_raw', '')
        coverage_code = row.get('coverage_code', '')
        mapping_status = row.get('mapping_status', '')

        should_drop, reason = should_drop_row(coverage_name, coverage_code, mapping_status)

        if should_drop:
            dropped_rows.append({
                'coverage_name_raw': coverage_name,
                'coverage_code': coverage_code or 'NONE',
                'mapping_status': mapping_status,
                'drop_reason': reason
            })
        else:
            # STEP NEXT-18X: Normalize mapping_status (strip + lowercase)
            if mapping_status:
                row['mapping_status'] = mapping_status.strip().lower()
            kept_rows.append(row)

    # Write sanitized output with CSV integrity hardening
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        if kept_rows:
            # STEP NEXT-18X-FIX: Enable quoting to prevent line breaks/commas breaking columns
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_MINIMAL,
                escapechar='\\'
            )
            writer.writeheader()

            # STEP NEXT-18X-FIX: Validate each row before writing
            for idx, row in enumerate(kept_rows):
                # Check column integrity
                if set(row.keys()) != set(fieldnames):
                    missing = set(fieldnames) - set(row.keys())
                    extra = set(row.keys()) - set(fieldnames)
                    error_msg = f"Row {idx+1} column mismatch: missing={missing}, extra={extra}"
                    raise ValueError(error_msg)

                # Validate mapping_status is normalized
                mapping_status = row.get('mapping_status', '')
                if mapping_status and mapping_status != mapping_status.strip().lower():
                    error_msg = f"Row {idx+1} has non-normalized mapping_status: '{mapping_status}'"
                    raise ValueError(error_msg)

                writer.writerow(row)

    # Write filtered-out audit trail
    filtered_out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(filtered_out_jsonl, 'w', encoding='utf-8') as f:
        for entry in dropped_rows:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return {
        'input_total': len(rows),
        'kept': len(kept_rows),
        'dropped': len(dropped_rows),
        'dropped_rows': dropped_rows
    }


def verify_sanitized_scope(csv_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify sanitized scope has no condition sentences.

    Args:
        csv_path: Path to sanitized CSV

    Returns:
        (is_clean, violations)
    """
    if not csv_path.exists():
        return False, ['FILE_NOT_FOUND']

    violations = []

    # Hard-coded failure patterns
    FAILURE_PATTERNS = [
        '진단확정된 경우',
        '인 경우',
        '일 때',
        '시$'
    ]

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coverage_name = row.get('coverage_name_raw', '')

            for pattern in FAILURE_PATTERNS:
                if re.search(pattern, coverage_name):
                    violations.append(coverage_name)
                    break

    return len(violations) == 0, violations


def main():
    parser = argparse.ArgumentParser(description='Sanitize scope_mapped.csv files')
    parser.add_argument('--insurer', type=str, help='Insurer name')
    parser.add_argument('--all', action='store_true', help='Process all insurers')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]

    if args.all:
        insurers = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']
    elif args.insurer:
        insurers = [args.insurer]
    else:
        print("[ERROR] Specify --insurer or --all")
        return 1

    print(f"[Step1 Scope Sanitization]")
    print(f"Processing {len(insurers)} insurer(s)\n")

    all_stats = {}

    for insurer in insurers:
        input_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped.csv'
        output_csv = project_root / 'data' / 'scope' / f'{insurer}_scope_mapped.sanitized.csv'
        filtered_out_jsonl = project_root / 'data' / 'scope' / f'{insurer}_scope_filtered_out.jsonl'

        print(f"[{insurer.upper()}]")

        stats = sanitize_scope_mapped(input_csv, output_csv, filtered_out_jsonl)

        if 'error' in stats:
            print(f"  ERROR: {stats['error']}")
            continue

        print(f"  Input: {stats['input_total']} rows")
        print(f"  Kept: {stats['kept']} rows ({stats['kept']/stats['input_total']*100:.1f}%)")
        print(f"  Dropped: {stats['dropped']} rows ({stats['dropped']/stats['input_total']*100:.1f}%)")

        if stats['dropped'] > 0:
            print(f"  Dropped examples:")
            for row in stats['dropped_rows'][:3]:
                print(f"    - [{row['drop_reason']}] {row['coverage_name_raw']}")

        # Verify
        is_clean, violations = verify_sanitized_scope(output_csv)

        if not is_clean:
            print(f"  ❌ VERIFICATION FAILED: {len(violations)} condition sentences remain!")
            for v in violations[:3]:
                print(f"    - {v}")
        else:
            print(f"  ✅ VERIFIED: No condition sentences")

        all_stats[insurer] = stats
        print()

    # Summary
    print("\n" + "="*70)
    print("GLOBAL SCOPE SANITIZATION SUMMARY")
    print("="*70)

    total_input = sum(s['input_total'] for s in all_stats.values() if 'input_total' in s)
    total_kept = sum(s['kept'] for s in all_stats.values() if 'kept' in s)
    total_dropped = sum(s['dropped'] for s in all_stats.values() if 'dropped' in s)

    print(f"Total input rows: {total_input}")
    print(f"Total kept: {total_kept} ({total_kept/total_input*100:.1f}%)")
    print(f"Total dropped: {total_dropped} ({total_dropped/total_input*100:.1f}%)")

    print(f"\n✅ Sanitized scope files: data/scope/*_scope_mapped.sanitized.csv")
    print(f"📎 Audit trail: data/scope/*_scope_filtered_out.jsonl")

    return 0


if __name__ == '__main__':
    exit(main())
