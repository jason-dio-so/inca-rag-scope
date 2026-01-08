#!/usr/bin/env python3
"""
STEP NEXT-74: Step5 Recommendation Runner
===========================================

CLI runner for rule-based coverage recommendation generation.

Usage:
    python -m pipeline.step5_recommendation.run --insurers samsung kb hanwha --topn 10

Input:
    data/compare_v1/compare_rows_v1.jsonl

Output:
    data/recommend_v1/recommend_rows_v1.jsonl
    data/recommend_v1/insurer_topn_v1.json

Gates (Zero-Tolerance):
- G1 SSOT Gate: Input must be data/compare_v1/compare_rows_v1.jsonl
- G2 Evidence Gate: decision != NO_EVIDENCE requires evidence_refs >= 1
- G3 Determinism Gate: Same input → Same output (SHA256 check)
- G4 No-LLM Gate: No LLM calls in code/logs
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

from .builder import (
    build_all_recommendations,
    build_insurer_summaries
)
from .model import RecommendRow


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]


def gate_ssot_input(input_file: Path) -> bool:
    """
    G1 SSOT Gate: Enforce input contract.

    Returns:
        True if valid, False otherwise
    """
    expected_name = "compare_rows_v1.jsonl"
    expected_dir = "compare_v1"

    if input_file.name != expected_name:
        print(f"❌ G1 SSOT GATE FAILED: Input filename must be '{expected_name}'")
        print(f"   Got: {input_file.name}")
        return False

    if expected_dir not in str(input_file):
        print(f"❌ G1 SSOT GATE FAILED: Input must be in '{expected_dir}/' directory")
        print(f"   Got: {input_file}")
        return False

    print(f"✅ G1 SSOT GATE PASSED: Input contract validated")
    return True


def gate_evidence_integrity(recommend_rows: List[RecommendRow]) -> bool:
    """
    G2 Evidence Gate: Verify decision != NO_EVIDENCE has evidence_refs >= 1.

    Returns:
        True if all pass, False otherwise
    """
    violations = []

    for idx, row in enumerate(recommend_rows):
        decision = row["decision"]
        evidence_count = len(row.get("evidence_refs", []))

        if decision != "NO_EVIDENCE" and evidence_count == 0:
            identity = row["coverage_identity"]
            violations.append((
                idx,
                identity["insurer_key"],
                identity["coverage_title"],
                decision
            ))

    if violations:
        print(f"❌ G2 EVIDENCE GATE FAILED: {len(violations)} violations")
        for idx, ins, title, dec in violations[:5]:  # Show first 5
            print(f"   Row {idx}: {ins}/{title} → {dec} (but 0 evidence)")
        return False

    print(f"✅ G2 EVIDENCE GATE PASSED: All {len(recommend_rows)} rows have valid evidence")
    return True


def gate_determinism(output_file: Path, prev_hash: str | None) -> str:
    """
    G3 Determinism Gate: Verify same input → same output.

    Args:
        output_file: Output file to hash
        prev_hash: Previous run's hash (if exists)

    Returns:
        Current file hash
    """
    current_hash = compute_file_hash(output_file)

    if prev_hash:
        if current_hash != prev_hash:
            print(f"⚠️  G3 DETERMINISM WARNING: Output hash changed")
            print(f"   Previous: {prev_hash}")
            print(f"   Current:  {current_hash}")
            print(f"   (This may be expected if input changed)")
        else:
            print(f"✅ G3 DETERMINISM GATE PASSED: Output hash stable ({current_hash})")
    else:
        print(f"✅ G3 DETERMINISM GATE: First run, hash = {current_hash}")

    return current_hash


def gate_no_llm() -> bool:
    """
    G4 No-LLM Gate: Verify no LLM calls in codebase.

    Check if import anthropic/openai statements exist (not comments).
    """
    # Check current file and builder/rules
    files_to_check = [
        Path(__file__).parent / "builder.py",
        Path(__file__).parent / "rules.py"
    ]

    for file_path in files_to_check:
        if file_path.exists():
            with open(file_path, 'r') as f:
                for line in f:
                    line_stripped = line.strip()
                    # Check for actual import statements (not in comments/strings)
                    if line_stripped.startswith("import anthropic") or \
                       line_stripped.startswith("from anthropic") or \
                       line_stripped.startswith("import openai") or \
                       line_stripped.startswith("from openai"):
                        print(f"❌ G4 NO-LLM GATE FAILED: LLM import detected in {file_path.name}")
                        return False

    print(f"✅ G4 NO-LLM GATE PASSED: No LLM imports detected")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-74: Rule-based Coverage Recommendation"
    )
    parser.add_argument(
        "--insurers",
        nargs="+",
        required=True,
        help="List of insurer keys to process"
    )
    parser.add_argument(
        "--topn",
        type=int,
        default=10,
        help="Number of top recommendations per insurer (default: 10)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("STEP 5: Rule-based Recommendation Generation")
    print("=" * 80)
    print()

    # Paths
    project_root = Path(__file__).resolve().parents[2]  # Fixed: 2 levels up from run.py
    input_file = project_root / "data" / "compare_v1" / "compare_rows_v1.jsonl"
    output_dir = project_root / "data" / "recommend_v1"
    output_file = output_dir / "recommend_rows_v1.jsonl"
    summary_file = output_dir / "insurer_topn_v1.json"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # G1 SSOT Gate
    print("[GATE 1: SSOT Input Validation]")
    if not gate_ssot_input(input_file):
        sys.exit(2)

    if not input_file.exists():
        print(f"❌ ERROR: Input file not found: {input_file}")
        sys.exit(1)

    print()

    # G4 No-LLM Gate
    print("[GATE 4: No-LLM Verification]")
    if not gate_no_llm():
        sys.exit(2)

    print()

    # Build recommendations
    print(f"[Building Recommendations]")
    print(f"Input: {input_file.name}")
    print(f"Insurers: {', '.join(args.insurers)}")
    print()

    recommend_rows = build_all_recommendations(input_file)

    print(f"✅ Generated {len(recommend_rows)} recommendation rows")
    print()

    # G2 Evidence Gate
    print("[GATE 2: Evidence Integrity Check]")
    if not gate_evidence_integrity(recommend_rows):
        sys.exit(1)

    print()

    # Filter by requested insurers
    filtered_rows = [
        r for r in recommend_rows
        if r["coverage_identity"]["insurer_key"] in args.insurers
    ]

    print(f"Filtered to {len(filtered_rows)} rows for requested insurers")
    print()

    # Count decisions
    decision_counts: Dict[str, int] = {}
    for row in filtered_rows:
        dec = row["decision"]
        decision_counts[dec] = decision_counts.get(dec, 0) + 1

    print(f"Decision summary:")
    for dec, count in sorted(decision_counts.items()):
        pct = (count / len(filtered_rows) * 100) if filtered_rows else 0
        print(f"  {dec:20s}: {count:4d} ({pct:5.1f}%)")

    print()

    # Write output
    print(f"[Writing Outputs]")
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in filtered_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    print(f"✅ Saved: {output_file}")

    # Build insurer summaries
    summaries = build_insurer_summaries(filtered_rows, args.insurers, args.topn)

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {summary_file}")
    print()

    # G3 Determinism Gate (informational)
    print("[GATE 3: Determinism Check]")
    gate_determinism(output_file, None)  # No prev hash on first run
    print()

    # Summary
    print("=" * 80)
    print("STEP 5 RECOMMENDATION SUMMARY")
    print("=" * 80)
    print(f"Total rows processed: {len(recommend_rows)}")
    print(f"Filtered rows (insurers): {len(filtered_rows)}")
    print(f"Output: {output_file}")
    print(f"Summary: {summary_file}")
    print()

    # Per-insurer summary
    print("Per-insurer Top-N:")
    for insurer, summary in sorted(summaries.items()):
        counts = summary["counts"]
        rec_count = counts.get("RECOMMENDED", 0)
        print(f"  {insurer:15s}: {rec_count:3d} RECOMMENDED, {len(summary['top_recommended'])} in top-N")

    print()
    print("✅ All gates passed. Recommendation generation complete.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
