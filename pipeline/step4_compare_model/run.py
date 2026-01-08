"""
CLI Runner for Comparison Table Builder - STEP NEXT-68

Usage:
    python -m pipeline.step4_compare_model.run --insurers kb
    python -m pipeline.step4_compare_model.run --insurers kb meritz
"""

import argparse
from pathlib import Path
from .builder import CompareBuilder


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-68: Build coverage comparison tables"
    )
    parser.add_argument(
        "--insurers",
        type=str,
        nargs="+",
        required=True,
        help="Insurer keys to include (e.g., kb meritz)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Input directory (default: data/scope_v3)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/compare_v1)"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    input_dir = Path(args.input_dir) if args.input_dir else (project_root / "data" / "scope_v3")
    output_dir = Path(args.output_dir) if args.output_dir else (project_root / "data" / "compare_v1")

    print(f"[STEP NEXT-68] Coverage Comparison Model Builder")
    print(f"[Insurers] {', '.join(args.insurers)}")
    print(f"[Input Dir] {input_dir}")
    print(f"[Output Dir] {output_dir}")
    print()

    # Find Step3 gated files
    step3_files = []
    for insurer in args.insurers:
        step3_file = input_dir / f"{insurer}_step3_evidence_enriched_v1_gated.jsonl"
        if not step3_file.exists():
            print(f"Warning: Step3 file not found for {insurer}: {step3_file}")
            print(f"Skipping {insurer}...")
            continue
        step3_files.append(step3_file)
        print(f"Found: {step3_file.name}")

    if not step3_files:
        print("Error: No Step3 files found.")
        return 1

    print()

    # Build comparison tables
    builder = CompareBuilder()
    output_files = builder.build_from_step3_files(step3_files, output_dir)

    print(f"[Results]")
    print(f"  Rows file: {output_files['rows']}")
    print(f"  Tables file: {output_files['tables']}")

    # Load and display stats
    import json

    # Count rows
    with open(output_files['rows'], 'r') as f:
        row_count = sum(1 for _ in f)

    # Load table
    with open(output_files['tables'], 'r') as f:
        table = json.loads(f.readline())

    print(f"\n[Stats]")
    print(f"  Total rows: {row_count}")
    print(f"  Insurers: {', '.join(table['insurers'])}")
    print(f"  Total coverages in table: {table['meta']['total_rows']}")
    print(f"  Conflicts: {table['meta']['conflict_count']}")
    print(f"  Unknown rate: {table['meta']['unknown_rate']:.1f}%")

    if table.get('table_warnings'):
        print(f"\n[Warnings]")
        for warning in table['table_warnings']:
            print(f"  - {warning}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
