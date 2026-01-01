#!/usr/bin/env python3
"""
Step7 Amount Comparison — Entrypoint

Usage:
    python -m pipeline.step7_amount_compare.run

Constitutional Enforcement:
- Reads from data/compare/*_coverage_cards.jsonl (SSOT)
- Writes to data/scope_v3/*_amount_comparison.jsonl
- NO Step1-5 modifications
- Deterministic (GATE-7-3)
"""

import json
import argparse
import hashlib
from pathlib import Path
from typing import List
from datetime import datetime

from .compare_amounts import compare_all_axes


def main():
    parser = argparse.ArgumentParser(description="Step7 Amount Comparison Engine")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/scope_v3",
        help="Output directory for amount comparisons"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/compare",
        help="Input directory for coverage cards"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Step7 Amount Comparison Engine (STEP NEXT-62)")
    print("=" * 80)
    print(f"Input:  {args.input_dir}/*_coverage_cards.jsonl")
    print(f"Output: {args.output_dir}/*_amount_comparison.jsonl")
    print()

    # 1. Find all coverage_cards.jsonl files
    input_path = Path(args.input_dir)
    coverage_cards_files = sorted(input_path.glob("*_coverage_cards.jsonl"))

    if not coverage_cards_files:
        print(f"❌ No coverage_cards.jsonl files found in {args.input_dir}")
        return 1

    print(f"📂 Found {len(coverage_cards_files)} coverage_cards files:")
    for f in coverage_cards_files:
        print(f"   - {f.name}")
    print()

    # 2. Compare all axes
    print("[Step 7-1] Parsing amount structures...")
    comparisons = compare_all_axes([str(f) for f in coverage_cards_files])

    if not comparisons:
        print("❌ No comparisons generated")
        return 1

    # 3. Write output (one file per coverage_code)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Aggregate output: all comparisons in one file
    output_file = output_path / "amount_comparisons_all.jsonl"

    print(f"\n[Step 7-2] Writing {len(comparisons)} comparisons to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        for comp in comparisons:
            f.write(json.dumps(comp, ensure_ascii=False) + '\n')

    print(f"✅ Written to {output_file}")

    # 4. GATE-7-3: Determinism check (SHA256)
    print(f"\n[GATE-7-3] Determinism validation...")
    sha256_hash = hashlib.sha256()
    with open(output_file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    sha256 = sha256_hash.hexdigest()
    print(f"  SHA256: {sha256}")

    # Record hash
    hash_file = output_path / "amount_comparisons_all.sha256"
    with open(hash_file, 'w') as f:
        f.write(f"{sha256}  amount_comparisons_all.jsonl\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")

    print(f"  Hash recorded: {hash_file}")

    # 5. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total comparisons: {len(comparisons)}")
    print(f"Output file: {output_file}")
    print(f"SHA256: {sha256[:16]}...")
    print()

    # Coverage code distribution
    insurer_counts = {}
    for comp in comparisons:
        count = comp["comparison_metrics"]["insurer_count"]
        insurer_counts[count] = insurer_counts.get(count, 0) + 1

    print("Coverage distribution by insurer count:")
    for count in sorted(insurer_counts.keys(), reverse=True):
        print(f"  {count} insurers: {insurer_counts[count]} coverages")

    print("\n✅ Step7 Amount Comparison complete")
    return 0


if __name__ == "__main__":
    exit(main())
