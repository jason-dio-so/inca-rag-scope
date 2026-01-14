#!/usr/bin/env python3
"""
STEP PIPELINE-V2-BLOCK-STEP2B-01: Step3 Evidence Resolver (Updated for Step1 V2)

Processes all Step1 V2 targeted extraction files and enriches with evidence.

IMPORTANT:
- Step2-b is DISABLED (constitutional violation)
- Step3 now reads Step1 V2 output directly
- Input: data/scope_v3/{INS_CD}_step1_targeted_v2.jsonl
- Output: data/scope_v3/{INS_CD}_step3_evidence_enriched_v1.jsonl
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.step3_evidence_resolver.resolver import BatchEvidenceResolver


def main():
    """Run Step3 evidence resolver for all insurers"""
    project_root = Path(__file__).parent.parent.parent
    ssot_dir = project_root / "data" / "scope_v3"

    # STEP PIPELINE-V2-BLOCK-STEP2B-01: Read Step1 V2 output instead of Step2-b
    input_files = sorted(ssot_dir.glob("*_step1_targeted_v2.jsonl"))

    if not input_files:
        print("❌ No Step1 V2 targeted extraction files found")
        print(f"   Expected: {ssot_dir}/*_step1_targeted_v2.jsonl")
        print()
        print("ACTION REQUIRED:")
        print("  Run Step1 V2 first: python -m pipeline.step1_targeted_v2.extractor")
        print("  Step2-b is DISABLED (constitutional violation)")
        sys.exit(2)

    print(f"[Step3 Evidence Resolver P2-FIX]")
    print(f"[Found {len(input_files)} input file(s)]")
    print()

    total_stats = {
        "total_coverages": 0,
        "processed": 0,
        "slots_found": 0,
        "slots_found_global": 0,
        "slots_unknown": 0,
        "slots_conflict": 0
    }

    for input_file in input_files:
        # STEP PIPELINE-V2-BLOCK-STEP2B-01: Extract ins_cd from Step1 V2 filename
        # e.g., "N01_step1_targeted_v2.jsonl" -> "N01"
        ins_cd = input_file.name.replace("_step1_targeted_v2.jsonl", "")

        # Map ins_cd to insurer_key for resolver compatibility
        # (Step3 resolver expects lowercase insurer names)
        INS_CD_TO_INSURER = {
            'N01': 'meritz',
            'N02': 'hanwha',
            'N03': 'lotte',
            'N05': 'heungkuk',
            'N08': 'samsung',
            'N09': 'hyundai',
            'N10': 'kb',
            'N13': 'db'
        }

        insurer_key = INS_CD_TO_INSURER.get(ins_cd)
        if not insurer_key:
            print(f"⚠️  Unknown ins_cd: {ins_cd}, skipping...")
            continue

        output_file = ssot_dir / f"{ins_cd}_step3_evidence_enriched_v1.jsonl"

        print(f"[Processing {ins_cd} ({insurer_key})]")
        print(f"  Input:  {input_file.name}")
        print(f"  Output: {output_file.name}")
        print(f"  Step1 V2 → Step3 (Step2-b bypassed)")

        # Create resolver
        try:
            resolver = BatchEvidenceResolver(insurer_key, enable_gates=True)
        except RuntimeError as e:
            print(f"  ⚠️  Warning: {e}")
            print(f"  Skipping {insurer_key}")
            print()
            continue

        # Process file
        stats = resolver.process_step2_file(
            input_file,
            output_file
        )

        # Accumulate stats
        for key in total_stats:
            total_stats[key] += stats[key]

        # Print stats
        total_slots = sum([
            stats['slots_found'],
            stats['slots_found_global'],
            stats['slots_conflict'],
            stats['slots_unknown']
        ])
        if total_slots > 0:
            coverage_specific_rate = stats['slots_found'] / total_slots * 100
            print(f"  Coverages: {stats['processed']}")
            print(f"  Slots FOUND: {stats['slots_found']} ({coverage_specific_rate:.1f}%)")
            print(f"  Slots UNKNOWN: {stats['slots_unknown']}")
        print()

    # Print summary
    print("=" * 80)
    print("[Step3 Summary]")
    print(f"  Total coverages processed: {total_stats['processed']}")
    print(f"  Total slots:")
    print(f"    FOUND: {total_stats['slots_found']}")
    print(f"    FOUND_GLOBAL: {total_stats['slots_found_global']}")
    print(f"    CONFLICT: {total_stats['slots_conflict']}")
    print(f"    UNKNOWN: {total_stats['slots_unknown']}")

    total_slots = sum([
        total_stats['slots_found'],
        total_stats['slots_found_global'],
        total_stats['slots_conflict'],
        total_stats['slots_unknown']
    ])
    if total_slots > 0:
        coverage_specific_rate = total_stats['slots_found'] / total_slots * 100
        print(f"  Coverage-specific rate: {coverage_specific_rate:.1f}%")

    print()
    print("✅ Step3 completed")


if __name__ == "__main__":
    main()
