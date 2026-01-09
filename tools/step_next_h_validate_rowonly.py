"""
STEP NEXT-H: Validate Row-Only Evidence Quality

Compare before (current Step3) vs after (row-only Step3) for diagnosis coverages.

Metrics:
- FOUND rate
- UNKNOWN_SEARCH_FAIL rate
- Contamination (must remain 0)

DoD:
- SEARCH_FAIL: 64.5% → < 30%
- Contamination: 0 maintained
- Evidence contains only original document text (no anchor insertion)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.step4_compare_model.gates import CoverageAttributionValidator, DiagnosisCoverageRegistry


def load_diagnosis_registry():
    """Load diagnosis coverage registry"""
    return DiagnosisCoverageRegistry()


def load_step3_output(file_path: Path) -> List[Dict]:
    """Load Step3 output (row-only or original)"""
    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def apply_g5_gate_to_evidence(evidence_pack: Dict, coverage_code: str, coverage_name: str, registry) -> Dict:
    """
    Apply G5 Coverage Attribution Gate to evidence pack.

    Returns:
        Dict mapping slot_key → {status, reason}
    """
    validator = CoverageAttributionValidator(registry)

    slot_results = {}

    for slot_key, candidates in evidence_pack.items():
        if not candidates:
            slot_results[slot_key] = {
                "status": "UNKNOWN",
                "classification": "UNKNOWN_MISSING"
            }
            continue

        # Collect excerpts from candidates
        excerpts = [candidate.get("context", "") for candidate in candidates]

        # Apply G5 validation to all excerpts
        attribution = validator.validate_attribution(
            excerpts=excerpts,
            coverage_code=coverage_code,
            coverage_name=coverage_name
        )

        # Determine status based on validation result
        if attribution["valid"]:
            slot_results[slot_key] = {
                "status": "FOUND",
                "classification": "FOUND",
                "total_count": len(candidates)
            }
        else:
            # G5 gate rejected
            slot_results[slot_key] = {
                "status": "UNKNOWN",
                "classification": "UNKNOWN_SEARCH_FAIL",
                "reason": attribution.get("reason", "G5 gate rejected"),
                "matched_exclusion": attribution.get("matched_exclusion"),
                "total_count": len(candidates)
            }

    return slot_results


def compute_metrics(slot_results: Dict[str, Dict]) -> Dict:
    """Compute metrics from slot results"""
    total = len(slot_results)
    found = sum(1 for r in slot_results.values() if r["classification"] == "FOUND")
    search_fail = sum(1 for r in slot_results.values() if r["classification"] == "UNKNOWN_SEARCH_FAIL")
    missing = sum(1 for r in slot_results.values() if r["classification"] == "UNKNOWN_MISSING")

    return {
        "total_slots": total,
        "found_count": found,
        "search_fail_count": search_fail,
        "missing_count": missing,
        "found_pct": round(found / total * 100, 1) if total > 0 else 0,
        "search_fail_pct": round(search_fail / total * 100, 1) if total > 0 else 0,
        "missing_pct": round(missing / total * 100, 1) if total > 0 else 0
    }


def validate_rowonly_output(insurers: List[str] = ["samsung", "kb"], version: str = "v1"):
    """
    Validate row-only Step3 output by applying G5 gates.

    Args:
        insurers: List of insurer keys
        version: "v1" or "v2"
    """
    print("=" * 80)
    print(f"STEP NEXT-H: Row-Only Evidence Validation ({version.upper()})")
    print("=" * 80)

    # Load diagnosis registry
    registry = load_diagnosis_registry()

    # Core slots to check (matching STEP NEXT-G scope)
    core_slots = [
        "start_date",
        "waiting_period",
        "reduction",
        "payout_limit",
        "entry_age",
        "exclusions"
    ]

    extended_slots = [
        "underwriting_condition",
        "mandatory_dependency",
        "payout_frequency",
        "industry_aggregate_limit"
    ]

    all_slots = core_slots + extended_slots

    for insurer_key in insurers:
        print(f"\n{'=' * 80}")
        print(f"Insurer: {insurer_key.upper()}")
        print(f"{'=' * 80}")

        # Load row-only Step3 output
        if version == "tableanchored":
            rowonly_file = Path("data/scope_v3") / f"{insurer_key}_step3_diagnosis_tableanchored_v1.jsonl"
        else:
            rowonly_file = Path("data/scope_v3") / f"{insurer_key}_step3_diagnosis_rowonly_{version}.jsonl"

        if not rowonly_file.exists():
            print(f"⚠️  Output not found: {rowonly_file}")
            continue

        rowonly_rows = load_step3_output(rowonly_file)
        print(f"\n✅ Loaded row-only Step3 output: {len(rowonly_rows)} coverage rows")

        # Apply G5 to each coverage
        coverage_results = {}
        all_slot_results = {}

        for row in rowonly_rows:
            coverage_code = row["coverage_code"]
            coverage_name = row["coverage_name"]
            evidence_pack = row.get("evidence_pack", {})

            # Apply G5 gates
            slot_results = apply_g5_gate_to_evidence(
                evidence_pack=evidence_pack,
                coverage_code=coverage_code,
                coverage_name=coverage_name,
                registry=registry
            )

            coverage_results[coverage_code] = {
                "coverage_name": coverage_name,
                "slot_results": slot_results
            }

            # Aggregate slot results
            for slot_key in all_slots:
                if slot_key not in slot_results:
                    continue

                key = f"{coverage_code}_{slot_key}"
                all_slot_results[key] = slot_results[slot_key]

        # Compute metrics
        metrics = compute_metrics(all_slot_results)

        print(f"\n{'─' * 80}")
        print(f"METRICS (After G5 Gate)")
        print(f"{'─' * 80}")
        print(f"Total slots checked: {metrics['total_slots']}")
        print(f"FOUND: {metrics['found_count']} ({metrics['found_pct']}%)")
        print(f"UNKNOWN_SEARCH_FAIL: {metrics['search_fail_count']} ({metrics['search_fail_pct']}%)")
        print(f"UNKNOWN_MISSING: {metrics['missing_count']} ({metrics['missing_pct']}%)")

        # Breakdown by coverage
        print(f"\n{'─' * 80}")
        print(f"By Coverage")
        print(f"{'─' * 80}")
        for coverage_code, result in coverage_results.items():
            coverage_name = result["coverage_name"]
            slot_results = result["slot_results"]

            found = sum(1 for r in slot_results.values() if r["classification"] == "FOUND")
            total = len(slot_results)

            print(f"{coverage_code} ({coverage_name[:30]}...): {found}/{total} FOUND")

        # Save detailed results
        output_file = Path("docs/audit") / f"step_next_h_rowonly_validation_{insurer_key}_{version}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "insurer": insurer_key,
                "metrics": metrics,
                "coverage_results": coverage_results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Detailed results saved: {output_file}")

    print(f"\n{'=' * 80}")
    print("✅ Validation Complete")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP NEXT-H: Validate Row-Only Evidence")
    parser.add_argument(
        "--insurers",
        nargs="+",
        default=["samsung", "kb"],
        help="Insurers to validate (default: samsung kb)"
    )
    parser.add_argument(
        "--version",
        default="v2",
        choices=["v1", "v2", "tableanchored"],
        help="Version to validate (default: v2)"
    )

    args = parser.parse_args()

    validate_rowonly_output(insurers=args.insurers, version=args.version)
