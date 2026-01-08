"""
STEP NEXT-70-ANCHOR-FIX + STEP NEXT-72-OPS: Validate Anchor GATE

GATE: pct_code == pct_anchor (100% match required)

Where:
- pct_code = % of rows where coverage_code != None
- pct_anchor = % of rows where anchored == true

Absolute rule: anchored := bool(coverage_code)

STEP NEXT-72-OPS Safety:
- REQUIRES --input parameter (no default)
- Displays target file and stage
- Exit 2 on missing input
"""

import json
import sys
import argparse
from pathlib import Path


def validate_anchor_gate(compare_rows_file: Path) -> bool:
    """
    Validate that anchored logic matches coverage_code existence.

    Returns:
        True if GATE passes, False otherwise
    """
    with open(compare_rows_file, 'r', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f]

    if not rows:
        print("ERROR: No rows found")
        return False

    total = len(rows)
    has_code = sum(1 for r in rows if r['identity'].get('coverage_code'))
    anchored = sum(1 for r in rows if not r['meta']['unanchored'])

    pct_code = (has_code / total) * 100
    pct_anchor = (anchored / total) * 100

    print(f"[Anchor GATE Validation]")
    print(f"  Target: {compare_rows_file}")
    print(f"  Stage: Step4 (Compare Model Output)")
    print(f"  Total rows: {total}")
    print(f"  Has coverage_code: {has_code} ({pct_code:.1f}%)")
    print(f"  Anchored (unanchored=false): {anchored} ({pct_anchor:.1f}%)")
    print()

    # GATE: Must be 100% match
    if has_code != anchored:
        print(f"❌ GATE FAILED: pct_code ({pct_code:.1f}%) != pct_anchor ({pct_anchor:.1f}%)")
        print(f"   Mismatch: {abs(has_code - anchored)} rows")

        # Find mismatches
        mismatches = []
        for r in rows:
            has_c = bool(r['identity'].get('coverage_code'))
            is_anch = not r['meta']['unanchored']
            if has_c != is_anch:
                mismatches.append({
                    'insurer': r['identity']['insurer_key'],
                    'coverage_name_raw': r['identity']['coverage_name_raw'][:60],
                    'coverage_code': r['identity'].get('coverage_code'),
                    'anchored': is_anch
                })

        print(f"\n  First 10 mismatches:")
        for m in mismatches[:10]:
            print(f"    {m}")

        return False
    else:
        print(f"✅ GATE PASSED: pct_code == pct_anchor ({pct_code:.1f}%)")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-72-OPS: Validate Anchor GATE (Zero-Tolerance Safety)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to compare_rows_v1.jsonl file (REQUIRED)"
    )

    args = parser.parse_args()

    compare_rows_file = Path(args.input)

    if not compare_rows_file.exists():
        print(f"❌ ERROR: File not found: {compare_rows_file}")
        print(f"   STEP NEXT-72-OPS: --input parameter is REQUIRED")
        print(f"   This prevents accidental validation of wrong pipeline stage")
        sys.exit(2)

    if not compare_rows_file.name.endswith("_rows_v1.jsonl"):
        print(f"⚠️  WARNING: Unexpected filename: {compare_rows_file.name}")
        print(f"   Expected: *_rows_v1.jsonl (Step4 compare output)")

    passed = validate_anchor_gate(compare_rows_file)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
