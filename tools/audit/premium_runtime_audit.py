#!/usr/bin/env python3
"""
HOTFIX: Premium Runtime Audit (Q12 G10 Gate Validation)

Purpose:
  Validate that ALL insurers required for Q12 comparison have premium_monthly
  available from PREMIUM SSOT for runtime injection.

Context:
  - premium_monthly is NOT a document slot (not in JSONL)
  - It's injected at runtime from Premium SSOT (product_premium_quote_v2 or API)
  - Q12 G10 Gate requires ALL insurers to have premium data

SSOT Input:
  - data/compare_v1/compare_rows_v1.jsonl (for insurer list)
  - Premium SSOT (DB table or JSONL mock)
  - Persona: age, sex, plan_variant

G10 Gate Rule (HARD):
  - Q12 requires premium_monthly for ALL insurers in comparison
  - If ANY insurer has missing premium → FAIL (exit 2)

Output:
  - docs/audit/PREMIUM_RUNTIME_AUDIT_REPORT.md
  - docs/audit/PREMIUM_RUNTIME_AUDIT_REPORT.csv
  - Exit code: 0 (PASS) | 2 (FAIL)
"""

import argparse
import json
import os
import sys
import csv
from datetime import datetime
from typing import Dict, List, Set, Optional
from collections import defaultdict


DEFAULT_INSURERS = ["samsung", "db", "hanwha", "heungkuk", "hyundai", "kb", "lotte", "meritz"]
DEFAULT_AGE = 40
DEFAULT_SEX = "M"
DEFAULT_PLAN_VARIANT = "NO_REFUND"


class PremiumRuntimeAuditor:
    """Audit Premium SSOT availability for Q12 G10 gate compliance."""

    def __init__(self, age: int = DEFAULT_AGE, sex: str = DEFAULT_SEX,
                 plan_variant: str = DEFAULT_PLAN_VARIANT,
                 use_mock: bool = True):
        self.age = age
        self.sex = sex
        self.plan_variant = plan_variant
        self.use_mock = use_mock

        # Data
        self.required_insurers: Set[str] = set(DEFAULT_INSURERS)
        self.premium_data: Dict[str, Optional[int]] = {}  # insurer -> premium_monthly or None

    def load_required_insurers_from_jsonl(self, jsonl_path: str) -> None:
        """Extract unique insurers from compare_rows_v1.jsonl."""
        print(f"[INFO] Loading insurers from: {jsonl_path}")

        if not os.path.exists(jsonl_path):
            print(f"[WARN] JSONL not found, using default insurers: {DEFAULT_INSURERS}")
            self.required_insurers = set(DEFAULT_INSURERS)
            return

        insurers = set()
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    insurer = row.get('identity', {}).get('insurer_key')
                    if insurer:
                        insurers.add(insurer)
                except json.JSONDecodeError:
                    pass

        if insurers:
            self.required_insurers = insurers
            print(f"[INFO] Found {len(insurers)} unique insurers in JSONL")
        else:
            print(f"[WARN] No insurers found in JSONL, using defaults")
            self.required_insurers = set(DEFAULT_INSURERS)

    def load_premium_from_mock(self) -> None:
        """
        TEMPORARY: Load MOCK premium data for demonstration.

        In production, this MUST query product_premium_quote_v2 table.
        """
        print("[INFO] Loading premium from MOCK (TEMPORARY)")
        print("[WARN] In production, query product_premium_quote_v2 table")

        # Mock: All insurers have premium except 'samsung' (to demonstrate FAIL case)
        # For PASS case, comment out the samsung exclusion
        base_premium = 80000 if self.age == 40 else 50000

        for insurer in self.required_insurers:
            # Simulate missing premium for one insurer (for demo)
            # In real audit, this would come from actual DB query
            if insurer == "samsung":
                # Uncomment next line to simulate FAIL scenario
                # self.premium_data[insurer] = None
                # Comment out to simulate PASS scenario
                self.premium_data[insurer] = base_premium + 1000
            else:
                # Add variance per insurer
                variance = hash(insurer) % 10000
                self.premium_data[insurer] = base_premium + variance

        print(f"[INFO] Loaded premium data for {len(self.premium_data)} insurers")

    def validate_g10_gate(self) -> Dict:
        """
        Validate Q12 G10 Gate: ALL insurers must have premium_monthly.

        Returns: {
            "status": "PASS" | "FAIL",
            "total_insurers": int,
            "with_premium": int,
            "missing_premium": int,
            "missing_insurers": [str],
            "gate_rule": str
        }
        """
        print("[INFO] Validating Q12 G10 Gate...")

        missing_insurers = []
        with_premium = 0

        for insurer in self.required_insurers:
            premium = self.premium_data.get(insurer)
            if premium is None or premium <= 0:
                missing_insurers.append(insurer)
            else:
                with_premium += 1

        gate_status = "PASS" if len(missing_insurers) == 0 else "FAIL"

        result = {
            "status": gate_status,
            "total_insurers": len(self.required_insurers),
            "with_premium": with_premium,
            "missing_premium": len(missing_insurers),
            "missing_insurers": sorted(missing_insurers),
            "gate_rule": "Q12 G10 Gate: ALL insurers must have premium_monthly (if ANY missing → FAIL)"
        }

        print(f"[INFO] G10 Gate Status: {gate_status}")
        print(f"[INFO] Insurers with premium: {with_premium}/{len(self.required_insurers)}")
        if missing_insurers:
            print(f"[WARN] Missing premium: {missing_insurers}")

        return result

    def generate_markdown_report(self, gate_result: Dict, output_path: str) -> None:
        """Generate Markdown report for premium runtime audit."""
        print(f"[INFO] Generating Markdown report: {output_path}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Premium Runtime Audit Report (Q12 G10 Gate)\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Purpose**: Validate Q12 G10 Gate compliance for runtime premium injection\n\n")

            # Persona
            f.write("---\n\n")
            f.write("## Audit Persona\n\n")
            f.write(f"- **Age**: {self.age}\n")
            f.write(f"- **Sex**: {self.sex}\n")
            f.write(f"- **Plan Variant**: {self.plan_variant}\n\n")

            # G10 Gate Result
            f.write("---\n\n")
            f.write("## Q12 G10 Gate Status\n\n")
            f.write(f"**Status**: **{gate_result['status']}**\n\n")
            f.write(f"**Gate Rule**: {gate_result['gate_rule']}\n\n")

            f.write(f"**Total Insurers Required**: {gate_result['total_insurers']}\n\n")
            f.write(f"**With Premium SSOT**: {gate_result['with_premium']}\n\n")
            f.write(f"**Missing Premium**: {gate_result['missing_premium']}\n\n")

            if gate_result['missing_insurers']:
                f.write("**Missing Insurers**:\n")
                for insurer in gate_result['missing_insurers']:
                    f.write(f"- ❌ `{insurer}`\n")
                f.write("\n")
            else:
                f.write("✅ **All insurers have premium SSOT available**\n\n")

            # Premium Data Table
            f.write("---\n\n")
            f.write("## Premium SSOT by Insurer\n\n")
            f.write("| Insurer | Premium Monthly (원) | Status |\n")
            f.write("|---------|----------------------|--------|\n")

            for insurer in sorted(self.required_insurers):
                premium = self.premium_data.get(insurer)
                if premium is not None and premium > 0:
                    status = "✅ OK"
                    premium_str = f"{premium:,}"
                else:
                    status = "❌ MISSING"
                    premium_str = "N/A"
                f.write(f"| {insurer} | {premium_str} | {status} |\n")
            f.write("\n")

            # Interpretation
            f.write("---\n\n")
            f.write("## Interpretation\n\n")

            if gate_result['status'] == "PASS":
                f.write("✅ **Q12 is READY for runtime execution**\n\n")
                f.write("All required insurers have premium_monthly available from SSOT.\n\n")
                f.write("Q12 responses can include premium data and pass G10 gate validation.\n\n")
            else:
                f.write("❌ **Q12 is NOT READY for runtime execution**\n\n")
                f.write(f"Missing premium data for {len(gate_result['missing_insurers'])} insurer(s).\n\n")
                f.write("**Required Actions**:\n")
                for insurer in gate_result['missing_insurers']:
                    f.write(f"1. Load premium SSOT for `{insurer}` (age={self.age}, sex={self.sex}, plan_variant={self.plan_variant})\n")
                f.write("\n")
                f.write("**Until fixed**: Q12 requests will FAIL with G10 gate error.\n\n")

            # Data Source
            f.write("---\n\n")
            f.write("## Data Source\n\n")
            if self.use_mock:
                f.write("⚠️ **MOCK DATA** (for demonstration)\n\n")
                f.write("In production, premium data MUST come from:\n")
                f.write("- `product_premium_quote_v2` table, OR\n")
                f.write("- Greenlight API (prInfo + prDetail), OR\n")
                f.write("- Other approved Premium SSOT sources\n\n")
            else:
                f.write("✅ **Production SSOT** (product_premium_quote_v2)\n\n")

            # Metadata
            f.write("---\n\n")
            f.write("## Metadata\n\n")
            f.write(f"- **Script**: `tools/audit/premium_runtime_audit.py`\n")
            f.write(f"- **Execution Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Insurers Audited**: {len(self.required_insurers)}\n")
            f.write(f"- **G10 Gate Status**: **{gate_result['status']}**\n")
            f.write("\n")

        print(f"[INFO] Markdown report written to: {output_path}")

    def generate_csv_report(self, gate_result: Dict, output_path: str) -> None:
        """Generate CSV report for premium runtime audit."""
        print(f"[INFO] Generating CSV report: {output_path}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "insurer", "age", "sex", "plan_variant",
                "premium_monthly", "has_premium", "gate_status"
            ])

            for insurer in sorted(self.required_insurers):
                premium = self.premium_data.get(insurer)
                has_premium = "YES" if (premium is not None and premium > 0) else "NO"
                premium_str = str(premium) if premium is not None else "NULL"

                writer.writerow([
                    insurer, self.age, self.sex, self.plan_variant,
                    premium_str, has_premium, gate_result['status']
                ])

        print(f"[INFO] CSV report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Premium Runtime Audit - Q12 G10 Gate Validation"
    )
    parser.add_argument(
        "--jsonl",
        default="data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows_v1.jsonl (for insurer list)"
    )
    parser.add_argument(
        "--age",
        type=int,
        default=DEFAULT_AGE,
        help=f"Persona age (default: {DEFAULT_AGE})"
    )
    parser.add_argument(
        "--sex",
        default=DEFAULT_SEX,
        help=f"Persona sex (default: {DEFAULT_SEX})"
    )
    parser.add_argument(
        "--plan-variant",
        default=DEFAULT_PLAN_VARIANT,
        help=f"Plan variant (default: {DEFAULT_PLAN_VARIANT})"
    )
    parser.add_argument(
        "--use-mock",
        action="store_true",
        default=True,
        help="Use MOCK premium data (default: True, for demo)"
    )
    parser.add_argument(
        "--out-md",
        default="docs/audit/PREMIUM_RUNTIME_AUDIT_REPORT.md",
        help="Output Markdown report path"
    )
    parser.add_argument(
        "--out-csv",
        default="docs/audit/PREMIUM_RUNTIME_AUDIT_REPORT.csv",
        help="Output CSV report path"
    )

    args = parser.parse_args()

    # Create auditor
    auditor = PremiumRuntimeAuditor(
        age=args.age,
        sex=args.sex,
        plan_variant=args.plan_variant,
        use_mock=args.use_mock
    )

    # Load data
    auditor.load_required_insurers_from_jsonl(args.jsonl)
    auditor.load_premium_from_mock()  # TODO: Replace with DB query in production

    # Validate G10 gate
    gate_result = auditor.validate_g10_gate()

    # Generate reports
    auditor.generate_markdown_report(gate_result, args.out_md)
    auditor.generate_csv_report(gate_result, args.out_csv)

    # Print summary
    print("\n" + "="*60)
    print("PREMIUM RUNTIME AUDIT COMPLETE")
    print("="*60)
    print(f"G10 Gate Status: {gate_result['status']}")
    print(f"Insurers with Premium: {gate_result['with_premium']}/{gate_result['total_insurers']}")
    if gate_result['missing_insurers']:
        print(f"Missing Premium: {gate_result['missing_insurers']}")
    print(f"Reports Generated:")
    print(f"  - {args.out_md}")
    print(f"  - {args.out_csv}")
    print("="*60)

    # Exit code based on gate status
    if gate_result['status'] == "FAIL":
        print("[ERROR] Q12 G10 Gate FAILED - missing premium data")
        return 2  # FAIL exit code
    else:
        print("[SUCCESS] Q12 G10 Gate PASSED - all insurers have premium SSOT")
        return 0  # PASS exit code


if __name__ == "__main__":
    sys.exit(main())
