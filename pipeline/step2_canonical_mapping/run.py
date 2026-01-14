#!/usr/bin/env python3
"""
⚠️⚠️⚠️ STEP2-B DISABLED ⚠️⚠️⚠️

This module is DISABLED as of STEP PIPELINE-V2-BLOCK-STEP2B-01.

REASON:
- coverage_code must come from SSOT input (Step1 V2), not from string-based assignment
- Contaminated path (data/sources/mapping/) is FORBIDDEN
- String matching for coverage_code generation is a CONSTITUTIONAL VIOLATION

Use Step1 V2 (pipeline.step1_targeted_v2) instead.

⚠️⚠️⚠️ STEP2-B DISABLED ⚠️⚠️⚠️

---

HISTORICAL DOCUMENTATION (DO NOT USE):

STEP NEXT-73: Step2-b Canonical Mapping Runner (SSOT Gate Enforcement)
========================================================================

CLI runner for canonical coverage mapping.
Processes ALL Step2-a sanitized files using glob, preserving variant axis.

Usage:
    python -m pipeline.step2_canonical_mapping.run [--mapping-source {approved|local}]

Options:
    --mapping-source approved  Use SSOT Excel only (default, PRODUCTION MODE)
    --mapping-source local     Use SSOT Excel + local_alias_overrides.csv (TESTING ONLY)

Input:
    data/scope_v3/*_step2_sanitized_scope_v1.jsonl

Output:
    data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl           (no variant)
    data/scope_v3/{insurer}_{variant}_step2_canonical_scope_v1.jsonl (with variant)
    data/scope_v3/{insurer}_step2_mapping_report.jsonl
    data/scope_v3/{insurer}_{variant}_step2_mapping_report.jsonl

Constitutional Rules (STEP NEXT-73):
- ZERO-TOLERANCE GATE: Default mode MUST use approved SSOT only
- Variant axis MUST be preserved from Step2-a → Step2-b
- NO LLM, NO PDF, NO Step1 module imports
- Input contract: Step2-a sanitized ONLY (hard fail if raw Step1)
- SSOT: data/scope_v3/ only
"""

import argparse
import re
import sys
from pathlib import Path

from pipeline.step2_canonical_mapping.canonical_mapper import (
    map_sanitized_scope,
    verify_no_reduction
)


def parse_step2a_filename(filename: str) -> tuple[str, str | None]:
    """
    Parse Step2-a sanitized filename to extract insurer and variant.

    Patterns:
    - {insurer}_step2_sanitized_scope_v1.jsonl → (insurer, None)
    - {insurer}_{variant}_step2_sanitized_scope_v1.jsonl → (insurer, variant)

    Returns:
        (insurer, variant) where variant is None if no variant present
    """
    # Pattern: {insurer}_{variant}_step2_sanitized_scope_v1.jsonl
    match = re.match(r'^(\w+)_(\w+)_step2_sanitized_scope_v1\.jsonl$', filename)
    if match:
        insurer, variant = match.groups()
        # Exclude common non-variant suffixes
        if variant in ['step2', 'sanitized', 'scope']:
            return (insurer, None)
        return (insurer, variant)

    # Pattern: {insurer}_step2_sanitized_scope_v1.jsonl
    match = re.match(r'^(\w+)_step2_sanitized_scope_v1\.jsonl$', filename)
    if match:
        insurer = match.group(1)
        return (insurer, None)

    return (None, None)


def main():
    print("=" * 80)
    print("⚠️⚠️⚠️ STEP2-B DISABLED ⚠️⚠️⚠️")
    print("=" * 80)
    print()
    print("REASON:")
    print("  - coverage_code must come from SSOT input (Step1 V2)")
    print("  - String-based coverage_code generation is a CONSTITUTIONAL VIOLATION")
    print("  - Contaminated path (data/sources/mapping/) is FORBIDDEN")
    print()
    print("ACTION REQUIRED:")
    print("  Use Step1 V2 (pipeline.step1_targeted_v2) instead")
    print("  Step1 V2 provides coverage_code from SSOT as INPUT")
    print()
    print("[STEP PIPELINE-V2-BLOCK-STEP2B-01]")
    print("=" * 80)
    sys.exit(2)

    # DEAD CODE BELOW (never executed)
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Step2-b Canonical Mapping with SSOT Gate Enforcement'
    )
    parser.add_argument(
        '--mapping-source',
        choices=['approved', 'local'],
        default='approved',
        help='Mapping source selection (default: approved = SSOT Excel only)'
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    mapping_excel = project_root / 'data' / 'sources' / 'mapping' / '담보명mapping자료.xlsx'
    local_overrides = project_root / 'data' / 'sources' / 'mapping' / 'local_alias_overrides.csv'

    if not mapping_excel.exists():
        print(f"[ERROR] Canonical mapping file not found: {mapping_excel}")
        return 1

    # STEP NEXT-73: ZERO-TOLERANCE GATE
    if args.mapping_source == 'approved':
        if local_overrides.exists():
            print(f"[GATE ENFORCEMENT] Mode: APPROVED (SSOT Excel only)")
            print(f"  ✅ Mapping source: {mapping_excel.name}")
            print(f"  🔒 Local overrides: BLOCKED (file exists but not loaded)")
            print()
        else:
            print(f"[GATE ENFORCEMENT] Mode: APPROVED (SSOT Excel only)")
            print(f"  ✅ Mapping source: {mapping_excel.name}")
            print()
    elif args.mapping_source == 'local':
        print(f"[GATE ENFORCEMENT] Mode: LOCAL (TESTING ONLY)")
        print(f"  ⚠️  WARNING: This mode uses unapproved mapping candidates!")
        print(f"  ⚠️  DO NOT use for production or final deliverables!")
        print(f"  ✅ Primary source: {mapping_excel.name}")
        if local_overrides.exists():
            print(f"  ⚠️  Override layer: {local_overrides.name} (loaded)")
            # FUTURE: Load and merge local_overrides.csv here
            print(f"  ❌ ERROR: Local override integration not yet implemented")
            return 1
        else:
            print(f"  ❌ ERROR: Local override file not found: {local_overrides}")
            return 1
        print()

    # STEP NEXT-52-HK: Enforce scope_v3 SSOT
    SSOT_DIR = project_root / 'data' / 'scope_v3'
    if not SSOT_DIR.exists():
        print(f"[ERROR] SSOT directory not found: {SSOT_DIR}")
        print(f"All outputs must be in data/scope_v3/ (STEP NEXT-52-HK)")
        return 2

    print(f"[STEP 2-b: Canonical Mapping (Variant-Aware)]")
    print(f"Canonical source: 신정원_v2024.12")
    print(f"SSOT: {SSOT_DIR}")
    print()

    # Glob all Step2-a sanitized files
    step2a_files = sorted(SSOT_DIR.glob('*_step2_sanitized_scope_v1.jsonl'))

    if not step2a_files:
        print("[ERROR] No Step2-a sanitized files found in SSOT directory")
        print(f"Expected: {SSOT_DIR}/*_step2_sanitized_scope_v1.jsonl")
        print(f"Run Step2-a first: python -m pipeline.step2_sanitize_scope.run")
        return 1

    print(f"Found {len(step2a_files)} Step2-a sanitized file(s):")
    for f in step2a_files:
        print(f"  - {f.name}")
    print()

    all_stats = {}
    failed_gates = []
    processed_count = 0

    for input_jsonl in step2a_files:
        insurer, variant = parse_step2a_filename(input_jsonl.name)

        if insurer is None:
            print(f"[SKIP] Cannot parse filename: {input_jsonl.name}")
            continue

        # Construct output filenames (variant-aware)
        if variant:
            output_jsonl = SSOT_DIR / f'{insurer}_{variant}_step2_canonical_scope_v1.jsonl'
            report_jsonl = SSOT_DIR / f'{insurer}_{variant}_step2_mapping_report.jsonl'
            display_name = f"{insurer.upper()} ({variant})"
        else:
            output_jsonl = SSOT_DIR / f'{insurer}_step2_canonical_scope_v1.jsonl'
            report_jsonl = SSOT_DIR / f'{insurer}_step2_mapping_report.jsonl'
            display_name = insurer.upper()

        # Validate SSOT path enforcement
        if not str(output_jsonl).startswith(str(SSOT_DIR)):
            print(f"[ERROR] Output path violation: {output_jsonl}")
            print(f"SSOT enforcement: All outputs must be in {SSOT_DIR}")
            return 2

        print(f"[{display_name}]")
        print(f"  Input: {input_jsonl.name}")

        # GATE 52-1: Input contract validation (HARD FAIL)
        if not input_jsonl.name.endswith('_step2_sanitized_scope_v1.jsonl'):
            print(f"  ❌ GATE 52-1 FAILED: Input contract violation!")
            print(f"     Expected: *_step2_sanitized_scope_v1.jsonl")
            print(f"     Got: {input_jsonl.name}")
            print(f"  ")
            print(f"  Step2-b MUST read Step2-a sanitized output only.")
            print(f"  This is a constitutional violation (NO raw Step1 input).")
            sys.exit(2)

        print(f"  ✅ GATE 52-1 PASSED: Input contract validated")

        # Map
        stats = map_sanitized_scope(input_jsonl, output_jsonl, report_jsonl, mapping_excel)

        if 'error' in stats:
            print(f"  ❌ ERROR: {stats['error']}")
            continue

        # Display statistics
        print(f"  Entries: {stats['input_total']} → {stats['mapped']} mapped ({stats['mapping_rate']*100:.1f}%), {stats['unmapped']} unmapped")

        print(f"  Mapping methods:")
        for method, count in sorted(stats['mapping_stats'].items(), key=lambda x: -x[1]):
            print(f"    - {method}: {count} ({count/stats['input_total']*100:.1f}%)")

        # Gate: Verify no reduction
        is_valid, error = verify_no_reduction(input_jsonl, output_jsonl)
        if not is_valid:
            print(f"  ❌ GATE FAILED (anti-reduction): {error}")
            failed_gates.append((display_name, error))
        else:
            print(f"  ✅ GATE PASSED: No row reduction")

        # Store stats with variant key
        stats_key = f"{insurer}_{variant}" if variant else insurer
        all_stats[stats_key] = stats
        processed_count += 1
        print()

    # Summary
    if not all_stats:
        print("\n[SUMMARY] No files processed")
        return 0

    print("\n" + "="*70)
    print("STEP 2-b CANONICAL MAPPING SUMMARY")
    print("="*70)

    total_input = sum(s['input_total'] for s in all_stats.values() if 'input_total' in s)
    total_mapped = sum(s['mapped'] for s in all_stats.values() if 'mapped' in s)
    total_unmapped = sum(s['unmapped'] for s in all_stats.values() if 'unmapped' in s)

    print(f"Processed: {processed_count} file(s)")
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

    # Per-file summary
    print(f"\nPer-file mapping rates:")
    for key, stats in sorted(all_stats.items()):
        if 'mapping_rate' in stats:
            rate = stats['mapping_rate'] * 100
            unmapped = stats.get('unmapped', 0)
            print(f"  - {key:15s}: {rate:5.1f}% mapped ({unmapped} unmapped)")

    print(f"\n✅ Canonical outputs: data/scope_v3/*_step2_canonical_scope_v1.jsonl")
    print(f"📎 Mapping reports: data/scope_v3/*_step2_mapping_report.jsonl")
    print(f"🔒 SSOT path: {SSOT_DIR} (enforced in STEP NEXT-52-HK)")
    print(f"🎯 Variant preservation: ENABLED (STEP NEXT-54)")
    print(f"🚦 Mapping source: {args.mapping_source.upper()} (STEP NEXT-73)")

    # Check for gate failures
    if failed_gates:
        print(f"\n❌ GATE FAILURES:")
        for name, error in failed_gates:
            print(f"  - {name}: {error}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
