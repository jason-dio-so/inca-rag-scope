#!/usr/bin/env python3
"""
STEP NEXT-46: Step2 Sanitize Scope Runner
===========================================

CLI runner for Step2 sanitization pipeline.

Usage:
    python -m pipeline.step2_sanitize_scope.run --insurer hanwha
    python -m pipeline.step2_sanitize_scope.run --all

Input:
    data/scope/{insurer}_step1_raw_scope.jsonl

Output:
    data/scope/{insurer}_step2_sanitized_scope_v1.jsonl
    data/scope/{insurer}_step2_dropped.jsonl
"""

import argparse
import sys
from pathlib import Path

from pipeline.step2_sanitize_scope.sanitize import (
    sanitize_step1_output,
    verify_sanitized_output
)


def main():
    parser = argparse.ArgumentParser(
        description='Step2: Sanitize raw Step1 extraction outputs'
    )
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

    print(f"[STEP 2: Sanitize Scope]")
    print(f"Processing {len(insurers)} insurer(s)\n")

    all_stats = {}

    # STEP NEXT-52-HK: Enforce scope_v3 SSOT
    SSOT_DIR = project_root / 'data' / 'scope_v3'
    if not SSOT_DIR.exists():
        print(f"[ERROR] SSOT directory not found: {SSOT_DIR}")
        print(f"All outputs must be in data/scope_v3/ (STEP NEXT-52-HK)")
        return 2

    for insurer in insurers:
        # Input: Step1 raw scope
        input_jsonl = SSOT_DIR / f'{insurer}_step1_raw_scope_v3.jsonl'

        # Output: Step2 sanitized scope
        output_jsonl = SSOT_DIR / f'{insurer}_step2_sanitized_scope_v1.jsonl'
        dropped_jsonl = SSOT_DIR / f'{insurer}_step2_dropped.jsonl'

        # Validate SSOT path enforcement
        if not str(output_jsonl).startswith(str(SSOT_DIR)):
            print(f"[ERROR] Output path violation: {output_jsonl}")
            print(f"SSOT enforcement: All outputs must be in {SSOT_DIR}")
            return 2

        print(f"[{insurer.upper()}]")

        # Check if input exists
        if not input_jsonl.exists():
            print(f"  ⚠️  Input not found: {input_jsonl.name}")
            print(f"  Run Step1 first: python -m pipeline.step1_summary_first.extractor_v3 --insurer {insurer}")
            print()
            continue

        # Sanitize
        stats = sanitize_step1_output(input_jsonl, output_jsonl, dropped_jsonl)

        if 'error' in stats:
            print(f"  ❌ ERROR: {stats['error']}")
            continue

        # Display statistics
        print(f"  Input: {stats['input_total']} entries")
        print(f"  Kept: {stats['kept']} entries ({stats['kept']/stats['input_total']*100:.1f}%)")
        print(f"  Dropped: {stats['dropped']} entries ({stats['dropped']/stats['input_total']*100:.1f}%)")

        if stats['dropped'] > 0:
            print(f"\n  Drop reasons:")
            for reason, count in sorted(stats['drop_reason_counts'].items(), key=lambda x: -x[1]):
                print(f"    - {reason}: {count}")

            # Show examples
            print(f"\n  Dropped examples:")
            for entry in stats['dropped_entries'][:5]:
                print(f"    - [{entry['drop_reason']}] {entry['coverage_name_raw']}")

        # Verify
        is_clean, violations = verify_sanitized_output(output_jsonl)

        if not is_clean:
            print(f"\n  ❌ VERIFICATION FAILED: {len(violations)} contamination(s) detected!")
            for v in violations[:3]:
                print(f"    - {v}")
            return 1
        else:
            print(f"\n  ✅ VERIFIED: No contamination detected")

        all_stats[insurer] = stats
        print()

    # Summary
    if not all_stats:
        print("\n[SUMMARY] No insurers processed")
        return 0

    print("\n" + "="*70)
    print("STEP 2 SANITIZATION SUMMARY")
    print("="*70)

    total_input = sum(s['input_total'] for s in all_stats.values() if 'input_total' in s)
    total_kept = sum(s['kept'] for s in all_stats.values() if 'kept' in s)
    total_dropped = sum(s['dropped'] for s in all_stats.values() if 'dropped' in s)

    print(f"Total input: {total_input} entries")
    print(f"Total kept: {total_kept} entries ({total_kept/total_input*100:.1f}%)")
    print(f"Total dropped: {total_dropped} entries ({total_dropped/total_input*100:.1f}%)")

    # Aggregate drop reasons
    global_drop_reasons = {}
    for stats in all_stats.values():
        if 'drop_reason_counts' in stats:
            for reason, count in stats['drop_reason_counts'].items():
                global_drop_reasons[reason] = global_drop_reasons.get(reason, 0) + count

    if global_drop_reasons:
        print(f"\nGlobal drop reasons:")
        for reason, count in sorted(global_drop_reasons.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count} ({count/total_dropped*100:.1f}%)")

    print(f"\n✅ Sanitized outputs: data/scope_v3/*_step2_sanitized_scope_v1.jsonl")
    print(f"📎 Audit trail: data/scope_v3/*_step2_dropped.jsonl")
    print(f"🔒 SSOT path: {SSOT_DIR} (enforced in STEP NEXT-52-HK)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
