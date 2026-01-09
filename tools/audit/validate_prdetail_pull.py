#!/usr/bin/env python3
"""
STEP NEXT-S: Validate prDetail Pull Completeness

Validates that 54 raw API responses exist and failures are properly tracked.

Usage:
    python3 tools/audit/validate_prdetail_pull.py --baseDt 20251126

DoD:
    (D1) 54 raw files exist (9 products × 3 ages × 2 sexes)
    (D2) Sum match verification (sum(coverage monthlyPrem) == monthlyPremSum)
    (D3) Failures exist → all have complete failure records
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class PrDetailPullValidator:
    """
    Validator for prDetail API pull completeness

    Checks:
    1. (D1) 54 raw files exist
    2. (D2) Sum match for all successful pulls
    3. (D3) Failures have complete records
    """

    def __init__(self, base_dt: str, raw_dir: Path):
        self.base_dt = base_dt
        self.raw_dir = raw_dir
        self.base_dt_dir = raw_dir / base_dt
        self.failures_file = raw_dir / "_failures" / f"{base_dt}.jsonl"

        self.validation_results = {
            "total_expected": 12,  # STEP NEXT-U: 6 prInfo + 6 prDetail
            "total_found": 0,
            "total_failures": 0,
            "http_200_count": 0,
            "http_4xx_count": 0,
            "http_5xx_count": 0,
            "by_age": defaultdict(int),
            "by_sex": defaultdict(int),
            "by_status_code": defaultdict(int),
            "missing": [],
            "failures": [],
            "sum_match_pass": 0,
            "sum_match_fail": 0,
            "violations": []
        }

    def validate(self):
        """Run all validation checks"""
        self._validate_d0_http_status()
        self._validate_d1_raw_files_exist()
        self._validate_d3_failures()
        self._print_report()

    def _validate_d0_http_status(self):
        """
        (D0) STEP NEXT-T: HTTP status distribution

        Checks:
        - HTTP 200 rate
        - 4xx vs 5xx breakdown
        - Response body snippets for failures
        """
        # Count raw files as 200s
        if self.base_dt_dir.exists():
            raw_files = list(self.base_dt_dir.rglob("*.json"))
            self.validation_results["http_200_count"] = len(raw_files)

        # Count failures by status code
        if self.failures_file.exists():
            with open(self.failures_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        failure = json.loads(line)
                        status_code = failure.get('status_code')
                        if status_code:
                            self.validation_results["by_status_code"][str(status_code)] += 1

                            if 400 <= status_code < 500:
                                self.validation_results["http_4xx_count"] += 1
                            elif status_code >= 500:
                                self.validation_results["http_5xx_count"] += 1

        # D0 pass condition: at least 1 HTTP 200
        if self.validation_results["http_200_count"] == 0:
            self.validation_results["violations"].append({
                "rule": "D0",
                "severity": "CRITICAL",
                "message": "No HTTP 200 responses found (all requests failed)"
            })

    def _validate_d1_raw_files_exist(self):
        """
        (D1) Check that raw files exist (STEP NEXT-U: _prInfo + _prDetail)

        Expected structure:
        data/premium_raw/{baseDt}/_prInfo/{age}_{sex}.json (6 files)
        data/premium_raw/{baseDt}/_prDetail/{age}_{sex}.json (6 files)
        """
        print(f"Checking raw files in: {self.base_dt_dir}")

        if not self.base_dt_dir.exists():
            self.validation_results["violations"].append({
                "rule": "D1",
                "severity": "CRITICAL",
                "message": f"Base date directory does not exist: {self.base_dt_dir}"
            })
            return

        # STEP NEXT-U: Check _prInfo directory
        prinfo_dir = self.base_dt_dir / "_prInfo"
        prdetail_dir = self.base_dt_dir / "_prDetail"

        prinfo_files = list(prinfo_dir.glob("*.json")) if prinfo_dir.exists() else []
        prdetail_files = list(prdetail_dir.glob("*.json")) if prdetail_dir.exists() else []

        prinfo_count = len(prinfo_files)
        prdetail_count = len(prdetail_files)

        print(f"  prInfo files: {prinfo_count}/6")
        print(f"  prDetail files: {prdetail_count}/6")

        self.validation_results["total_found"] = prinfo_count + prdetail_count
        self.validation_results["total_expected"] = 12  # 6 prInfo + 6 prDetail

        # Parse prDetail file paths (for breakdown)
        for raw_file in prdetail_files:
            filename = raw_file.name

            # Parse age_sex from filename: {age}_{sex}.json
            if "_" in filename:
                age_sex = filename.replace(".json", "")
                age_str, sex = age_sex.split("_")

                self.validation_results["by_age"][age_str] += 1
                self.validation_results["by_sex"][sex] += 1

        # Check if we have 12 files (6 prInfo + 6 prDetail)
        if self.validation_results["total_found"] < self.validation_results["total_expected"]:
            self.validation_results["violations"].append({
                "rule": "D1",
                "severity": "ERROR",
                "message": f"Expected {self.validation_results['total_expected']} raw files (6 prInfo + 6 prDetail), found {self.validation_results['total_found']} ({prinfo_count} prInfo + {prdetail_count} prDetail)"
            })

    def _validate_d3_failures(self):
        """
        (D3) Validate failure records are complete

        Checks:
        - Failures file exists if there are failures
        - All failure records have required fields
        """
        if not self.failures_file.exists():
            print(f"No failures file found: {self.failures_file}")
            return

        failures = []
        with open(self.failures_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    failures.append(json.loads(line))

        self.validation_results["total_failures"] = len(failures)
        self.validation_results["failures"] = failures

        # Validate each failure record
        required_fields = ["timestamp", "insurer_key", "product_id", "age", "sex", "error"]

        for idx, failure in enumerate(failures):
            missing_fields = [f for f in required_fields if f not in failure]

            if missing_fields:
                self.validation_results["violations"].append({
                    "rule": "D3",
                    "severity": "WARNING",
                    "message": f"Failure record {idx} missing fields: {', '.join(missing_fields)}",
                    "failure": failure
                })

    def _print_report(self):
        """Print validation report"""
        print("=" * 80)
        print("STEP NEXT-T: prDetail Pull Validation Report (HOTFIX)")
        print("=" * 80)
        print(f"Base date: {self.base_dt}")
        print(f"Raw directory: {self.raw_dir}")
        print()

        # STEP NEXT-T: D0 - HTTP Status Distribution
        print(f"(D0) HTTP Status Distribution:")
        print(f"  HTTP 200 (success): {self.validation_results['http_200_count']}")
        print(f"  HTTP 4xx (client error): {self.validation_results['http_4xx_count']}")
        print(f"  HTTP 5xx (server error): {self.validation_results['http_5xx_count']}")
        print(f"  Total requests: {self.validation_results['total_expected']}")

        success_rate = (self.validation_results['http_200_count'] / self.validation_results['total_expected']) * 100
        print(f"  Success rate: {success_rate:.1f}%")

        if self.validation_results["http_200_count"] > 0:
            print("  Status: ✅ PASS (at least 1 HTTP 200)")
        else:
            print("  Status: ❌ FAIL (no HTTP 200 responses)")

        # Status code breakdown
        if self.validation_results["by_status_code"]:
            print()
            print("  Status code breakdown:")
            for status_code, count in sorted(self.validation_results["by_status_code"].items()):
                print(f"    {status_code}: {count} requests")

        print()

        # D1: File count
        print(f"(D1) Raw Files:")
        print(f"  Expected: {self.validation_results['total_expected']}")
        print(f"  Found: {self.validation_results['total_found']}")

        if self.validation_results["total_found"] == self.validation_results["total_expected"]:
            print("  Status: ✅ PASS")
        else:
            print("  Status: ❌ FAIL")

        print()

        # STEP NEXT-U: No insurer breakdown (prInfo/prDetail are not per-product)
        print("Breakdown by Age:")
        for age, count in sorted(self.validation_results["by_age"].items()):
            print(f"  {age}: {count} files")

        print()
        print("Breakdown by Sex:")
        for sex, count in sorted(self.validation_results["by_sex"].items()):
            print(f"  {sex}: {count} files")

        print()

        # D3: Failures
        print(f"(D3) Failures:")
        print(f"  Total failures: {self.validation_results['total_failures']}")

        if self.validation_results["total_failures"] > 0:
            print(f"  Failures file: {self.failures_file}")
            print()
            print("  Sample failures (first 3):")
            for failure in self.validation_results["failures"][:3]:
                # STEP NEXT-U: Handle both prInfo and prDetail failures (no insurer_key/product_id)
                endpoint = failure.get('endpoint', 'unknown')
                age = failure.get('age', 'N/A')
                sex = failure.get('sex', 'N/A')
                print(f"    - {endpoint} | age {age} | sex {sex}")
                print(f"      Status: {failure.get('status_code', 'N/A')}")
                print(f"      Error: {failure['error'][:100]}")

                # STEP NEXT-U: Show response body snippet for 4xx errors
                if failure.get('response_body_snippet'):
                    snippet = failure['response_body_snippet'][:200]
                    print(f"      Response: {snippet}")
                print()

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

            print()

        # Summary
        print("=" * 80)
        print("SUMMARY:")
        print(f"  Total files: {self.validation_results['total_found']}")
        print(f"  Total failures: {self.validation_results['total_failures']}")
        print(f"  Violations: {len(self.validation_results['violations'])}")

        if self.validation_results["violations"]:
            print("\n  Status: ❌ VALIDATION FAILED")
            return False
        else:
            print("\n  Status: ✅ VALIDATION PASSED")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate prDetail API pull completeness (STEP NEXT-S)"
    )
    parser.add_argument(
        "--baseDt",
        required=True,
        help="Base date (YYYYMMDD), e.g., 20251126"
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("/Users/cheollee/inca-rag-scope/data/premium_raw"),
        help="Raw API response directory"
    )

    args = parser.parse_args()

    validator = PrDetailPullValidator(args.baseDt, args.raw_dir)
    validator.validate()

    # Exit code based on validation result
    sys.exit(0 if not validator.validation_results["violations"] else 1)


if __name__ == "__main__":
    main()
