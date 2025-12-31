"""
STEP NEXT-44-γ-2: Global Over-Filtering Verification

Verify that Hanwha-specific filters (44-γ) do not over-filter other insurers.
Hard gates: 7 insurers (non-Hanwha) must maintain coverage_count within tolerance.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_jsonl_count(path: Path) -> int:
    """Load JSONL and count coverages"""
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)


def check_evidence_completeness(path: Path) -> Tuple[int, int]:
    """Check evidences array completeness"""
    total = 0
    missing = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            total += 1
            evidences = entry.get('proposal_facts', {}).get('evidences', [])
            if not evidences or len(evidences) == 0:
                missing += 1
    return total, missing


def verify_global_overfiltering() -> Dict[str, any]:
    """
    Verify global over-filtering gates

    Hard Gates:
    1. Non-Hanwha insurers (7): coverage_count drop <= 10% (or max 10 items)
    2. Hanwha: 30-40 range (existing test)
    3. All 8: evidences.length >= 1 for all records

    Returns:
        {
            'gates_passed': bool,
            'insurers': {insurer: {before, after, delta, status, ...}},
            'failed_gates': [...]
        }
    """
    baseline_dir = Path(__file__).parent.parent.parent / "backups" / "step1_44g2_baseline"
    current_dir = Path(__file__).parent.parent.parent / "data" / "scope"

    insurers = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "heungkuk", "db"]

    results = {
        'gates_passed': True,
        'insurers': {},
        'failed_gates': []
    }

    for insurer in insurers:
        baseline_path = baseline_dir / f"{insurer}_step1_raw_scope.jsonl"
        current_path = current_dir / f"{insurer}_step1_raw_scope.jsonl"

        before_count = load_jsonl_count(baseline_path)
        after_count = load_jsonl_count(current_path)
        delta = after_count - before_count
        delta_pct = (delta / before_count * 100) if before_count > 0 else 0

        # Evidence completeness check
        total, missing = check_evidence_completeness(current_path)
        evidence_status = "PASS" if missing == 0 else "FAIL"

        # Gate 1: Coverage count drop gate
        if insurer == "hanwha":
            # Hanwha: 30-40 range (existing test handles this)
            count_gate = "PASS" if 30 <= after_count <= 40 else "FAIL"
            tolerance = "30-40 range"
        else:
            # Non-Hanwha: delta <= 10% or max 10 items (whichever is larger)
            max_allowed_drop = max(10, round(before_count * 0.10))
            count_gate = "PASS" if delta >= -max_allowed_drop else "FAIL"
            tolerance = f"max drop {max_allowed_drop}"

        # Gate 2: Evidence completeness
        if evidence_status == "FAIL":
            count_gate = "FAIL"
            results['failed_gates'].append(f"{insurer}: {missing}/{total} records missing evidences")

        if count_gate == "FAIL":
            results['gates_passed'] = False
            results['failed_gates'].append(f"{insurer}: count_gate failed (before={before_count}, after={after_count}, delta={delta}, tolerance={tolerance})")

        results['insurers'][insurer] = {
            'before': before_count,
            'after': after_count,
            'delta': delta,
            'delta_pct': round(delta_pct, 2),
            'tolerance': tolerance,
            'count_gate': count_gate,
            'evidence_status': evidence_status,
            'evidence_missing': missing,
            'evidence_total': total
        }

    return results


def main():
    print("\n" + "="*80)
    print("STEP NEXT-44-γ-2: Global Over-Filtering Verification")
    print("="*80 + "\n")

    results = verify_global_overfiltering()

    # Print per-insurer results
    print(f"{'Insurer':<12} {'Before':<8} {'After':<8} {'Delta':<8} {'Δ%':<8} {'Tolerance':<20} {'Gate':<8} {'Evidence':<10}")
    print("-" * 100)

    for insurer, data in results['insurers'].items():
        print(f"{insurer:<12} {data['before']:<8} {data['after']:<8} {data['delta']:<8} {data['delta_pct']:<8.2f} {data['tolerance']:<20} {data['count_gate']:<8} {data['evidence_status']:<10}")

    print("\n" + "="*80)

    if results['gates_passed']:
        print("✅ ALL GATES PASSED - No over-filtering detected")
    else:
        print("❌ GATES FAILED")
        print("\nFailed gates:")
        for failure in results['failed_gates']:
            print(f"  - {failure}")

    print("="*80 + "\n")

    return 0 if results['gates_passed'] else 1


if __name__ == '__main__':
    exit(main())
