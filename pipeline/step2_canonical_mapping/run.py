#!/usr/bin/env python3
"""
STEP NEXT-47: Step2-b Canonical Mapping Runner
================================================

CLI runner for canonical coverage mapping.

Usage:
    python -m pipeline.step2_canonical_mapping.run --insurer samsung
    python -m pipeline.step2_canonical_mapping.run --all

Input:
    data/scope/{insurer}_step2_sanitized_scope_v1.jsonl

Output:
    data/scope/{insurer}_step2_canonical_scope_v1.jsonl
    data/scope/{insurer}_step2_mapping_report.jsonl
"""

import argparse
import sys
from pathlib import Path

from pipeline.step2_canonical_mapping.canonical_mapper import (
    map_sanitized_scope,
    verify_no_reduction
)


def main():
    parser = argparse.ArgumentParser(
        description='Step2-b: Map sanitized scope to canonical coverage codes'
    )
    parser.add_argument('--insurer', type=str, help='Insurer name')
    parser.add_argument('--all', action='store_true', help='Process all insurers')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    mapping_excel = project_root / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'

    if not mapping_excel.exists():
        print(f"[ERROR] Canonical mapping file not found: {mapping_excel}")
        return 1

    if args.all:
        insurers = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']
    elif args.insurer:
        insurers = [args.insurer]
    else:
        print("[ERROR] Specify --insurer or --all")
        return 1

    print(f"[STEP 2-b: Canonical Mapping]")
    print(f"Canonical source: 신정원_v2024.12")
    print(f"Processing {len(insurers)} insurer(s)\n")

    all_stats = {}
    failed_gates = []

    # STEP NEXT-52-HK: Enforce scope_v3 SSOT
    SSOT_DIR = project_root / 'data' / 'scope_v3'
    if not SSOT_DIR.exists():
        print(f"[ERROR] SSOT directory not found: {SSOT_DIR}")
        print(f"All outputs must be in data/scope_v3/ (STEP NEXT-52-HK)")
        return 2

    for insurer in insurers:
        # Input: Step2-a sanitized scope
        input_jsonl = SSOT_DIR / f'{insurer}_step2_sanitized_scope_v1.jsonl'

        # Output: Step2-b canonical scope
        output_jsonl = SSOT_DIR / f'{insurer}_step2_canonical_scope_v1.jsonl'
        report_jsonl = SSOT_DIR / f'{insurer}_step2_mapping_report.jsonl'

        # Validate SSOT path enforcement
        if not str(output_jsonl).startswith(str(SSOT_DIR)):
            print(f"[ERROR] Output path violation: {output_jsonl}")
            print(f"SSOT enforcement: All outputs must be in {SSOT_DIR}")
            return 2

        print(f"[{insurer.upper()}]")

        # GATE 52-1: Input contract validation (HARD FAIL)
        if not input_jsonl.exists():
            print(f"  ⚠️  Input not found: {input_jsonl.name}")
            print(f"  Run Step2-a first: python -m pipeline.step2_sanitize_scope.run --insurer {insurer}")
            print()
            continue

        # Verify input is from Step2-a (sanitized), not raw Step1
        if not input_jsonl.name.endswith('_step2_sanitized_scope_v1.jsonl'):
            print(f"  ❌ GATE 52-1 FAILED: Input contract violation!")
            print(f"     Expected: *_step2_sanitized_scope_v1.jsonl")
            print(f"     Got: {input_jsonl.name}")
            print(f"  ")
            print(f"  Step2-b MUST read Step2-a sanitized output only.")
            print(f"  This is a constitutional violation (NO raw Step1 input).")
            sys.exit(2)

        print(f"  Input: {input_jsonl.name}")
        print(f"  ✅ GATE 52-1 PASSED: Input contract validated")

        # Map
        stats = map_sanitized_scope(input_jsonl, output_jsonl, report_jsonl, mapping_excel)

        if 'error' in stats:
            print(f"  ❌ ERROR: {stats['error']}")
            continue

        # Display statistics
        print(f"  Input: {stats['input_total']} entries")
        print(f"  Mapped: {stats['mapped']} entries ({stats['mapping_rate']*100:.1f}%)")
        print(f"  Unmapped: {stats['unmapped']} entries ({stats['unmapped']/stats['input_total']*100:.1f}%)")

        print(f"\n  Mapping methods:")
        for method, count in sorted(stats['mapping_stats'].items(), key=lambda x: -x[1]):
            print(f"    - {method}: {count} ({count/stats['input_total']*100:.1f}%)")

        # Gate: Verify no reduction
        is_valid, error = verify_no_reduction(input_jsonl, output_jsonl)
        if not is_valid:
            print(f"\n  ❌ GATE FAILED (anti-reduction): {error}")
            failed_gates.append((insurer, error))
        else:
            print(f"\n  ✅ GATE PASSED: No row reduction")

        all_stats[insurer] = stats
        print()

    # Summary
    if not all_stats:
        print("\n[SUMMARY] No insurers processed")
        return 0

    print("\n" + "="*70)
    print("STEP 2-b CANONICAL MAPPING SUMMARY")
    print("="*70)

    total_input = sum(s['input_total'] for s in all_stats.values() if 'input_total' in s)
    total_mapped = sum(s['mapped'] for s in all_stats.values() if 'mapped' in s)
    total_unmapped = sum(s['unmapped'] for s in all_stats.values() if 'unmapped' in s)

    print(f"Total input: {total_input} entries")
    print(f"Total mapped: {total_mapped} entries ({total_mapped/total_input*100:.1f}%)")
    print(f"Total unmapped: {total_unmapped} entries ({total_unmapped/total_input*100:.1f}%)")

    # Global mapping stats
    global_mapping_stats = {}
    for stats in all_stats.values():
        if 'mapping_stats' in stats:
            for method, count in stats['mapping_stats'].items():
                global_mapping_stats[method] = global_mapping_stats.get(method, 0) + count

    if global_mapping_stats:
        print(f"\nGlobal mapping methods:")
        for method, count in sorted(global_mapping_stats.items(), key=lambda x: -x[1]):
            print(f"  - {method}: {count} ({count/total_input*100:.1f}%)")

    # Per-insurer summary
    print(f"\nPer-insurer mapping rates:")
    for insurer, stats in sorted(all_stats.items()):
        if 'mapping_rate' in stats:
            rate = stats['mapping_rate'] * 100
            unmapped = stats.get('unmapped', 0)
            print(f"  - {insurer:10s}: {rate:5.1f}% mapped ({unmapped} unmapped)")

    print(f"\n✅ Canonical outputs: data/scope_v3/*_step2_canonical_scope_v1.jsonl")
    print(f"📎 Mapping reports: data/scope_v3/*_step2_mapping_report.jsonl")
    print(f"🔒 SSOT path: {SSOT_DIR} (enforced in STEP NEXT-52-HK)")

    # Check for gate failures
    if failed_gates:
        print(f"\n❌ GATE FAILURES:")
        for insurer, error in failed_gates:
            print(f"  - {insurer}: {error}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
