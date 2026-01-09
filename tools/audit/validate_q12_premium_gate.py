#!/usr/bin/env python3
"""
STEP NEXT-R: Q12 Premium Gate Validator (G10)

Validates that Q12 comparison tables include premium_monthly slot
and that premium values come from PREMIUM_SSOT only.

Usage:
    python3 tools/audit/validate_q12_premium_gate.py --input data/compare_v1/compare_rows_v1.jsonl

DoD:
    (D1) Q12 실행 시 premium_monthly row가 항상 존재
    (D2) premium_monthly는 source_kind="PREMIUM_SSOT"만 허용 (DOC_EVIDENCE 금지)
    (D3) Q12에서 premium row가 하나라도 누락되면 G10 FAIL → 고객용 출력 FAIL
    (D4) premium 출력에 조건(age/sex/plan_variant) + as_of_date/baseDt가 포함
    (D5) 기존 G5/G6/G7/G8/G9 결과 불변
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class Q12PremiumGateValidator:
    """
    G10 Premium Gate Validator for Q12

    Checks:
    1. premium_monthly slot exists for ALL insurers in Q12
    2. source_kind == "PREMIUM_SSOT" (not "DOC_EVIDENCE")
    3. Premium value structure is valid
    4. Premium source + conditions are present
    """

    def __init__(self, input_file: Path):
        self.input_file = input_file
        self.rows = []
        self.validation_results = {
            "total_rows": 0,
            "insurers": set(),
            "premium_rows_count": 0,
            "premium_by_insurer": {},
            "violations": [],
            "warnings": []
        }

    def load_rows(self):
        """Load CompareRow instances from JSONL"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                self.rows.append(row)

        self.validation_results["total_rows"] = len(self.rows)

    def validate(self):
        """Run all validation checks"""
        self._validate_d1_premium_exists()
        self._validate_d2_source_kind()
        self._validate_d4_conditions_and_source()

        # D3 check: If ANY insurer is missing premium, Q12 should FAIL
        self._validate_d3_all_insurers_have_premium()

    def _validate_d1_premium_exists(self):
        """
        (D1) Q12 실행 시 premium_monthly row가 항상 존재

        Checks if premium_monthly slot exists in compare rows.
        """
        insurers_with_premium = set()
        insurers_without_premium = set()

        for row in self.rows:
            insurer_key = row.get("identity", {}).get("insurer_key")
            slots = row.get("slots", {})
            premium_slot = slots.get("premium_monthly")

            if insurer_key:
                self.validation_results["insurers"].add(insurer_key)

                if premium_slot:
                    insurers_with_premium.add(insurer_key)
                    self.validation_results["premium_rows_count"] += 1

                    # Track premium value per insurer
                    if insurer_key not in self.validation_results["premium_by_insurer"]:
                        self.validation_results["premium_by_insurer"][insurer_key] = []

                    self.validation_results["premium_by_insurer"][insurer_key].append({
                        "coverage_code": row.get("identity", {}).get("coverage_code"),
                        "coverage_title": row.get("identity", {}).get("coverage_title"),
                        "premium_value": premium_slot.get("value")
                    })
                else:
                    insurers_without_premium.add(insurer_key)

        # Check if any insurer is completely missing premium
        for insurer_key in self.validation_results["insurers"]:
            if insurer_key not in insurers_with_premium:
                self.validation_results["violations"].append({
                    "rule": "D1",
                    "severity": "ERROR",
                    "message": f"Insurer '{insurer_key}' has NO premium_monthly slot in any row",
                    "insurer": insurer_key
                })

    def _validate_d2_source_kind(self):
        """
        (D2) premium_monthly는 source_kind="PREMIUM_SSOT"만 허용

        Checks that premium_monthly slots have source_kind="PREMIUM_SSOT"
        (not "DOC_EVIDENCE").
        """
        for row in self.rows:
            insurer_key = row.get("identity", {}).get("insurer_key")
            coverage_code = row.get("identity", {}).get("coverage_code")
            slots = row.get("slots", {})
            premium_slot = slots.get("premium_monthly")

            if premium_slot:
                source_kind = premium_slot.get("source_kind")

                if source_kind != "PREMIUM_SSOT":
                    self.validation_results["violations"].append({
                        "rule": "D2",
                        "severity": "ERROR",
                        "message": f"premium_monthly has invalid source_kind: '{source_kind}' (expected 'PREMIUM_SSOT')",
                        "insurer": insurer_key,
                        "coverage_code": coverage_code,
                        "source_kind": source_kind
                    })

    def _validate_d3_all_insurers_have_premium(self):
        """
        (D3) Q12에서 premium row가 하나라도 누락되면 G10 FAIL

        For Q12, ALL insurers MUST have premium_monthly.
        If any insurer is missing premium, Q12 output should FAIL.
        """
        insurers_with_premium = set(self.validation_results["premium_by_insurer"].keys())
        all_insurers = self.validation_results["insurers"]

        missing_insurers = all_insurers - insurers_with_premium

        if missing_insurers:
            self.validation_results["violations"].append({
                "rule": "D3",
                "severity": "CRITICAL",
                "message": f"G10 FAIL: Q12 requires premium for ALL insurers. Missing: {', '.join(missing_insurers)}",
                "missing_insurers": list(missing_insurers),
                "action": "Q12 customer output BLOCKED"
            })

    def _validate_d4_conditions_and_source(self):
        """
        (D4) premium 출력에 조건 + as_of_date + baseDt 포함

        Checks that premium_monthly slots include:
        - confidence (with basis)
        - (Future: premium_source + premium_conditions in separate metadata)
        """
        for row in self.rows:
            insurer_key = row.get("identity", {}).get("insurer_key")
            coverage_code = row.get("identity", {}).get("coverage_code")
            slots = row.get("slots", {})
            premium_slot = slots.get("premium_monthly")

            if premium_slot:
                # Check confidence
                confidence = premium_slot.get("confidence")
                if not confidence:
                    self.validation_results["warnings"].append({
                        "rule": "D4",
                        "severity": "WARNING",
                        "message": f"premium_monthly missing confidence field",
                        "insurer": insurer_key,
                        "coverage_code": coverage_code
                    })
                else:
                    level = confidence.get("level")
                    basis = confidence.get("basis")

                    if level != "HIGH":
                        self.validation_results["warnings"].append({
                            "rule": "D4",
                            "severity": "WARNING",
                            "message": f"premium_monthly confidence level is not HIGH: '{level}'",
                            "insurer": insurer_key,
                            "coverage_code": coverage_code,
                            "confidence_level": level
                        })

                    if not basis or "Premium SSOT" not in basis:
                        self.validation_results["warnings"].append({
                            "rule": "D4",
                            "severity": "WARNING",
                            "message": f"premium_monthly confidence basis does not reference Premium SSOT",
                            "insurer": insurer_key,
                            "coverage_code": coverage_code,
                            "confidence_basis": basis
                        })

                # Check value structure
                value = premium_slot.get("value")
                if not value:
                    self.validation_results["violations"].append({
                        "rule": "D4",
                        "severity": "ERROR",
                        "message": f"premium_monthly has no value",
                        "insurer": insurer_key,
                        "coverage_code": coverage_code
                    })
                elif isinstance(value, dict):
                    # Check for amount, plan_variant, currency
                    if "amount" not in value:
                        self.validation_results["violations"].append({
                            "rule": "D4",
                            "severity": "ERROR",
                            "message": f"premium_monthly value missing 'amount'",
                            "insurer": insurer_key,
                            "coverage_code": coverage_code
                        })

                    if "plan_variant" not in value:
                        self.validation_results["warnings"].append({
                            "rule": "D4",
                            "severity": "WARNING",
                            "message": f"premium_monthly value missing 'plan_variant'",
                            "insurer": insurer_key,
                            "coverage_code": coverage_code
                        })

    def print_report(self):
        """Print validation report"""
        print("=" * 80)
        print("Q12 Premium Gate Validation Report (G10)")
        print("=" * 80)
        print(f"Input: {self.input_file}")
        print(f"Total rows: {self.validation_results['total_rows']}")
        print(f"Insurers: {', '.join(sorted(self.validation_results['insurers']))}")
        print(f"Rows with premium_monthly: {self.validation_results['premium_rows_count']}")
        print()

        # Premium by insurer
        print("Premium Coverage by Insurer:")
        print("-" * 80)
        for insurer_key in sorted(self.validation_results["premium_by_insurer"].keys()):
            premium_entries = self.validation_results["premium_by_insurer"][insurer_key]
            print(f"  {insurer_key}: {len(premium_entries)} row(s) with premium")

            # Show first entry as example
            if premium_entries:
                example = premium_entries[0]
                amount = example["premium_value"].get("amount") if isinstance(example["premium_value"], dict) else example["premium_value"]
                print(f"    Example: {example['coverage_title'][:40]} → ₩{amount:,}")

        print()

        # Violations
        if self.validation_results["violations"]:
            print("VIOLATIONS:")
            print("-" * 80)
            for violation in self.validation_results["violations"]:
                severity = violation.get("severity", "ERROR")
                rule = violation.get("rule", "UNKNOWN")
                message = violation.get("message", "")
                print(f"  [{severity}] {rule}: {message}")

                if "missing_insurers" in violation:
                    print(f"    Missing insurers: {', '.join(violation['missing_insurers'])}")
                    print(f"    Action: {violation.get('action', 'N/A')}")

            print()

        # Warnings
        if self.validation_results["warnings"]:
            print("WARNINGS:")
            print("-" * 80)
            for warning in self.validation_results["warnings"]:
                severity = warning.get("severity", "WARNING")
                rule = warning.get("rule", "UNKNOWN")
                message = warning.get("message", "")
                print(f"  [{severity}] {rule}: {message}")

            print()

        # Summary
        print("=" * 80)
        print("SUMMARY:")
        print(f"  Violations: {len(self.validation_results['violations'])}")
        print(f"  Warnings: {len(self.validation_results['warnings'])}")

        if self.validation_results["violations"]:
            print("\n  Status: ❌ VALIDATION FAILED")
            return False
        else:
            print("\n  Status: ✅ VALIDATION PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate Q12 Premium Gate (G10) compliance"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to compare_rows_v1.jsonl"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(2)

    validator = Q12PremiumGateValidator(args.input)
    validator.load_rows()
    validator.validate()
    passed = validator.print_report()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
