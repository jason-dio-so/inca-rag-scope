"""
STEP NEXT-71 + STEP NEXT-72-OPS: Universe Gate Validation

HARD GATE: U == E == C (exact row count match)

Where:
- U = Universe rows (Step2-b canonical SSOT)
- E = Evidence rows (Step3 gated output)
- C = Compare rows (Step4 compare_rows)

Absolute rule: U == E == C for total AND per-insurer
Exit code 2 if ANY mismatch detected.

STEP NEXT-72-OPS Safety:
- REQUIRES --data-dir parameter (no default)
- Displays source directories
- Exit 2 on missing directories
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List


class UniverseGateValidator:
    """Validates U/E/C row counts"""

    INSURERS = [
        "samsung", "hanwha", "heungkuk", "hyundai", "kb", "meritz",
        "db_over41", "db_under40", "lotte_female", "lotte_male"
    ]

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.scope_dir = data_dir / "scope_v3"
        self.compare_dir = data_dir / "compare_v1"

    def count_universe_rows_by_insurer(self) -> Dict[str, int]:
        """Count U: Step2-b canonical (Universe SSOT) by actual insurer_key"""
        counts = {}

        for insurer_file in self.INSURERS:
            u_file = self.scope_dir / f"{insurer_file}_step2_canonical_scope_v1.jsonl"
            if not u_file.exists():
                continue

            with open(u_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    insurer_key = row.get('insurer_key', insurer_file)
                    counts[insurer_key] = counts.get(insurer_key, 0) + 1

        return counts

    def count_evidence_rows_by_insurer(self) -> Dict[str, int]:
        """Count E: Step3 gated output by actual insurer_key"""
        counts = {}

        for insurer_file in self.INSURERS:
            e_file = self.scope_dir / f"{insurer_file}_step3_evidence_enriched_v1_gated.jsonl"
            if not e_file.exists():
                continue

            with open(e_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    insurer_key = row.get('insurer_key', insurer_file)
                    counts[insurer_key] = counts.get(insurer_key, 0) + 1

        return counts

    def count_compare_rows_by_insurer(self) -> Dict[str, int]:
        """Count C: Step4 compare_rows by insurer"""
        c_file = self.compare_dir / "compare_rows_v1.jsonl"
        if not c_file.exists():
            return {}

        counts = {}

        with open(c_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                insurer = row['identity']['insurer_key']
                counts[insurer] = counts.get(insurer, 0) + 1

        return counts

    def validate(self) -> bool:
        """
        Validate U == E == C for all insurers.

        Returns:
            True if all gates pass, False otherwise
        """
        print("[Universe Gate Validation]")
        print("=" * 80)
        print(f"  Universe source: {self.scope_dir}")
        print(f"  Evidence source: {self.scope_dir}")
        print(f"  Compare source:  {self.compare_dir}")
        print("=" * 80)
        print()

        # Count by actual insurer_key (not file name)
        universe_counts = self.count_universe_rows_by_insurer()
        evidence_counts = self.count_evidence_rows_by_insurer()
        compare_counts = self.count_compare_rows_by_insurer()

        # Get all unique insurers
        all_insurers = sorted(set(list(universe_counts.keys()) +
                                  list(evidence_counts.keys()) +
                                  list(compare_counts.keys())))

        # Collect per-insurer stats
        insurer_stats = []
        total_u = 0
        total_e = 0
        total_c = 0
        all_match = True

        for insurer in all_insurers:
            u_count = universe_counts.get(insurer, 0)
            e_count = evidence_counts.get(insurer, 0)
            c_count = compare_counts.get(insurer, 0)

            total_u += u_count
            total_e += e_count
            total_c += c_count

            match = (u_count == e_count == c_count)
            if not match:
                all_match = False

            insurer_stats.append({
                "insurer": insurer,
                "u": u_count,
                "e": e_count,
                "c": c_count,
                "match": match
            })

        # Print per-insurer breakdown
        print(f"Per-Insurer Breakdown:")
        print(f"{'Insurer':<15} {'U':>6} {'E':>6} {'C':>6} {'U==E':>6} {'E==C':>6} {'Status':>8}")
        print("-" * 80)

        for stat in insurer_stats:
            u_e_match = "✓" if stat['u'] == stat['e'] else "✗"
            e_c_match = "✓" if stat['e'] == stat['c'] else "✗"
            status = "✅ PASS" if stat['match'] else "❌ FAIL"

            print(f"{stat['insurer']:<15} {stat['u']:>6} {stat['e']:>6} {stat['c']:>6} "
                  f"{u_e_match:>6} {e_c_match:>6} {status:>8}")

        print()
        print("-" * 80)
        print(f"{'TOTAL':<15} {total_u:>6} {total_e:>6} {total_c:>6}")
        print()

        # Check totals
        total_match = (total_u == total_e == total_c)

        print(f"Total Match:")
        print(f"  U (Universe):  {total_u}")
        print(f"  E (Evidence):  {total_e}")
        print(f"  C (Compare):   {total_c}")
        print(f"  U == E == C:   {total_match}")
        print()

        # Final verdict
        if all_match and total_match:
            print("✅ UNIVERSE GATE PASSED")
            print(f"   All insurers: U == E == C ({total_u} rows)")
            return True
        else:
            print("❌ UNIVERSE GATE FAILED")
            if not all_match:
                failed = [s['insurer'] for s in insurer_stats if not s['match']]
                print(f"   Failed insurers: {', '.join(failed)}")
            if not total_match:
                print(f"   Total mismatch: U={total_u}, E={total_e}, C={total_c}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-72-OPS: Validate Universe GATE (Zero-Tolerance Safety)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to data directory containing scope_v3/ and compare_v1/ (REQUIRED)"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"❌ ERROR: Data directory not found: {data_dir}")
        print(f"   STEP NEXT-72-OPS: --data-dir parameter is REQUIRED")
        print(f"   This prevents accidental validation of wrong directories")
        sys.exit(2)

    scope_v3 = data_dir / "scope_v3"
    compare_v1 = data_dir / "compare_v1"

    if not scope_v3.exists():
        print(f"❌ ERROR: scope_v3 directory not found: {scope_v3}")
        sys.exit(2)

    if not compare_v1.exists():
        print(f"⚠️  WARNING: compare_v1 directory not found: {compare_v1}")
        print(f"   Universe gate will check U == E only")

    validator = UniverseGateValidator(data_dir)

    passed = validator.validate()

    # HARD GATE: exit 2 on failure
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
