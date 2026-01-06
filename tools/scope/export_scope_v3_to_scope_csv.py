#!/usr/bin/env python3
"""
STEP NEXT-18X-B: scope_v3 → canonical scope CSV exporter

Purpose:
    Convert data/scope_v3/*_step2_sanitized_scope_v1.jsonl (intermediate)
    → data/scope/*_scope_mapped.sanitized.csv (SSOT)

Input:
    - data/scope_v3/*_step2_sanitized_scope_v1.jsonl
    - JSONL rows with: insurer, coverage_name_raw, sanitized, drop_reason

Output:
    - data/scope/{insurer}_scope_mapped.sanitized.csv
    - Single column: coverage_name_raw
    - Rows where sanitized == true ONLY

Rules:
    - NO additional columns (ScopeGate expects coverage_name_raw ONLY)
    - Deterministic output (sorted, deduplicated)
    - NO modifications to existing code (ScopeGate, tests)

Usage:
    python tools/scope/export_scope_v3_to_scope_csv.py \
      --input_dir data/scope_v3 \
      --output_dir data/scope
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Set


def extract_insurer_from_filename(filename: str) -> str:
    """
    Extract insurer code from filename.

    Examples:
        samsung_step2_sanitized_scope_v1.jsonl → samsung
        db_over41_step2_sanitized_scope_v1.jsonl → db_over41
        lotte_female_step2_sanitized_scope_v1.jsonl → lotte_female
    """
    # Remove _step2_sanitized_scope_v1.jsonl suffix
    insurer = filename.replace("_step2_sanitized_scope_v1.jsonl", "")
    return insurer


def load_sanitized_coverage_names(jsonl_path: Path) -> Set[str]:
    """
    Load coverage_name_raw from JSONL where sanitized == true.

    Returns:
        Set of coverage_name_raw (deduplicated)
    """
    coverage_names = set()

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            # Filter: sanitized == true ONLY
            if row.get("sanitized") is True:
                coverage_name_raw = row.get("coverage_name_raw")
                if coverage_name_raw:
                    coverage_names.add(coverage_name_raw)

    return coverage_names


def export_to_csv(coverage_names: Set[str], output_path: Path) -> None:
    """
    Write coverage_names to CSV (single column: coverage_name_raw).

    Rules:
        - Sorted (deterministic output)
        - Deduplicated (set already ensures this)
        - CSV header: coverage_name_raw
    """
    sorted_names = sorted(coverage_names)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["coverage_name_raw"])
        for name in sorted_names:
            writer.writerow([name])


def main():
    parser = argparse.ArgumentParser(
        description="Export scope_v3 JSONL to canonical scope CSV (SSOT)"
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=Path("data/scope_v3"),
        help="Input directory (default: data/scope_v3)",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("data/scope"),
        help="Output directory (default: data/scope)",
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all *_step2_sanitized_scope_v1.jsonl files
    jsonl_files = list(input_dir.glob("*_step2_sanitized_scope_v1.jsonl"))

    if not jsonl_files:
        print(f"⚠️  No *_step2_sanitized_scope_v1.jsonl files found in {input_dir}")
        return

    print(f"Found {len(jsonl_files)} JSONL files in {input_dir}")

    # Process each file
    for jsonl_path in jsonl_files:
        insurer = extract_insurer_from_filename(jsonl_path.name)

        # Load sanitized coverage names
        coverage_names = load_sanitized_coverage_names(jsonl_path)

        if not coverage_names:
            print(f"⚠️  {insurer}: No sanitized coverage names found, skipping")
            continue

        # Output CSV path (SSOT naming convention)
        csv_filename = f"{insurer}_scope_mapped.sanitized.csv"
        csv_path = output_dir / csv_filename

        # Export to CSV
        export_to_csv(coverage_names, csv_path)

        print(f"✅ {insurer}: {len(coverage_names)} coverage names → {csv_path}")

    print(f"\n✅ Export complete. Outputs in {output_dir}")


if __name__ == "__main__":
    main()
