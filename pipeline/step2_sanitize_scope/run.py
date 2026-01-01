#!/usr/bin/env python3
"""
STEP NEXT-54: Step2 Sanitize Scope Runner (Variant-Aware)
===========================================================

CLI runner for Step2 sanitization pipeline.
Processes ALL Step1 raw files using glob, preserving variant axis.

Usage:
    python -m pipeline.step2_sanitize_scope.run

Input:
    data/scope_v3/*_step1_raw_scope_v3.jsonl

Output:
    data/scope_v3/{insurer}_step2_sanitized_scope_v1.jsonl           (no variant)
    data/scope_v3/{insurer}_{variant}_step2_sanitized_scope_v1.jsonl (with variant)
    data/scope_v3/{insurer}_step2_dropped.jsonl
    data/scope_v3/{insurer}_{variant}_step2_dropped.jsonl

Constitutional Rules (STEP NEXT-54):
- Variant axis MUST be preserved from Step1 → Step2
- NO LLM, NO PDF, NO Step1 module imports
- SSOT: data/scope_v3/ only
"""

import re
import sys
from pathlib import Path

from pipeline.step2_sanitize_scope.sanitize import (
    sanitize_step1_output,
    verify_sanitized_output
)


def parse_step1_filename(filename: str) -> tuple[str, str | None]:
    """
    Parse Step1 raw filename to extract insurer and variant.

    Patterns:
    - {insurer}_step1_raw_scope_v3.jsonl → (insurer, None)
    - {insurer}_{variant}_step1_raw_scope_v3.jsonl → (insurer, variant)

    Returns:
        (insurer, variant) where variant is None if no variant present
    """
    # Pattern: {insurer}_{variant}_step1_raw_scope_v3.jsonl
    match = re.match(r'^(\w+)_(\w+)_step1_raw_scope_v3\.jsonl$', filename)
    if match:
        insurer, variant = match.groups()
        # Exclude common non-variant suffixes
        if variant in ['step1', 'raw', 'scope']:
            return (insurer, None)
        return (insurer, variant)

    # Pattern: {insurer}_step1_raw_scope_v3.jsonl
    match = re.match(r'^(\w+)_step1_raw_scope_v3\.jsonl$', filename)
    if match:
        insurer = match.group(1)
        return (insurer, None)

    return (None, None)


def main():
    project_root = Path(__file__).resolve().parents[2]

    # STEP NEXT-52-HK: Enforce scope_v3 SSOT
    SSOT_DIR = project_root / 'data' / 'scope_v3'
    if not SSOT_DIR.exists():
        print(f"[ERROR] SSOT directory not found: {SSOT_DIR}")
        print(f"All outputs must be in data/scope_v3/ (STEP NEXT-52-HK)")
        return 2

    print(f"[STEP 2-a: Sanitize Scope (Variant-Aware)]")
    print(f"SSOT: {SSOT_DIR}")
    print()

    # Glob all Step1 raw files
    step1_files = sorted(SSOT_DIR.glob('*_step1_raw_scope_v3.jsonl'))

    if not step1_files:
        print("[ERROR] No Step1 raw files found in SSOT directory")
        print(f"Expected: {SSOT_DIR}/*_step1_raw_scope_v3.jsonl")
        return 1

    print(f"Found {len(step1_files)} Step1 raw file(s):")
    for f in step1_files:
        print(f"  - {f.name}")
    print()

    all_stats = {}
    processed_count = 0

    for input_jsonl in step1_files:
        insurer, variant = parse_step1_filename(input_jsonl.name)

        if insurer is None:
            print(f"[SKIP] Cannot parse filename: {input_jsonl.name}")
            continue

        # Construct output filenames (variant-aware)
        if variant:
            output_jsonl = SSOT_DIR / f'{insurer}_{variant}_step2_sanitized_scope_v1.jsonl'
            dropped_jsonl = SSOT_DIR / f'{insurer}_{variant}_step2_dropped.jsonl'
            display_name = f"{insurer.upper()} ({variant})"
        else:
            output_jsonl = SSOT_DIR / f'{insurer}_step2_sanitized_scope_v1.jsonl'
            dropped_jsonl = SSOT_DIR / f'{insurer}_step2_dropped.jsonl'
            display_name = insurer.upper()

        # Validate SSOT path enforcement
        if not str(output_jsonl).startswith(str(SSOT_DIR)):
            print(f"[ERROR] Output path violation: {output_jsonl}")
            print(f"SSOT enforcement: All outputs must be in {SSOT_DIR}")
            return 2

        print(f"[{display_name}]")
        print(f"  Input: {input_jsonl.name}")

        # Sanitize
        stats = sanitize_step1_output(input_jsonl, output_jsonl, dropped_jsonl)

        if 'error' in stats:
            print(f"  ❌ ERROR: {stats['error']}")
            continue

        # Display statistics
        print(f"  Entries: {stats['input_total']} → {stats['kept']} kept ({stats['kept']/stats['input_total']*100:.1f}%), {stats['dropped']} dropped")

        if stats['dropped'] > 0:
            print(f"  Drop reasons:")
            for reason, count in sorted(stats['drop_reason_counts'].items(), key=lambda x: -x[1]):
                print(f"    - {reason}: {count}")

            # Show examples
            if stats['dropped_entries']:
                print(f"  Dropped examples:")
                for entry in stats['dropped_entries'][:3]:
                    print(f"    - [{entry['drop_reason']}] {entry['coverage_name_raw']}")

        # Verify
        is_clean, violations = verify_sanitized_output(output_jsonl)

        if not is_clean:
            print(f"  ❌ VERIFICATION FAILED: {len(violations)} contamination(s) detected!")
            for v in violations[:3]:
                print(f"    - {v}")
            return 1
        else:
            print(f"  ✅ VERIFIED: No contamination")

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
    print("STEP 2-a SANITIZATION SUMMARY")
    print("="*70)

    total_input = sum(s['input_total'] for s in all_stats.values() if 'input_total' in s)
    total_kept = sum(s['kept'] for s in all_stats.values() if 'kept' in s)
    total_dropped = sum(s['dropped'] for s in all_stats.values() if 'dropped' in s)

    print(f"Processed: {processed_count} file(s)")
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
    print(f"🎯 Variant preservation: ENABLED (STEP NEXT-54)")

    return 0


if __name__ == '__main__':
    sys.exit(main())
