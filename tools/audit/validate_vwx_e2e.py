#!/usr/bin/env python3
"""
STEP NEXT-VWX: E2E Validation Script (DoD V/W/X)

Validates all VWX requirements in a single command.

Usage:
    python3 tools/audit/validate_vwx_e2e.py --baseDt 20260109

DoD Coverage:
    V1: Q12 premium_monthly slot exists + source_kind="PREMIUM_SSOT"
    V2: Q12 모든 insurer premium 존재 (G10)
    V3: Q1 Top-N deterministic
    V4: Premium 출력에 조건(age/sex/plan_variant) + as_of_date/baseDt 포함
    V5: G5~G9 회귀 테스트 (기존 결과 불변)

    W1: Q14 동일 입력 → 동일 Top-3
    W2: Premium 누락 상품 제외 (추정 금지)
    W3: Rounding 정책 고정 (소수점 2자리)

    X1: 54 API calls 성공/실패 집계 PASS
    X2: Premium SSOT sum match PASS
    X3: Q12 + Q1 + Q14 E2E 회귀 테스트
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any


class VWXValidator:
    """
    E2E Validator for STEP NEXT-VWX

    Runs all DoD checks (V1-V5, W1-W3, X1-X3) in sequence.
    """

    def __init__(self, base_dt: str):
        self.base_dt = base_dt
        self.validation_results = {
            "base_dt": base_dt,
            "phase_v": {"status": "PENDING", "checks": {}},
            "phase_w": {"status": "PENDING", "checks": {}},
            "phase_x": {"status": "PENDING", "checks": {}},
            "overall_status": "PENDING"
        }

    def validate_all(self):
        """Run all validation phases"""
        print("=" * 80)
        print(f"STEP NEXT-VWX E2E Validation (baseDt={self.base_dt})")
        print("=" * 80)
        print()

        # Phase V: Customer API Integration
        self._validate_phase_v()

        # Phase W: Q14 Enhancement
        self._validate_phase_w()

        # Phase X: Operational Stability
        self._validate_phase_x()

        # Overall status
        self._calculate_overall_status()

        # Print report
        self._print_report()

    def _validate_phase_v(self):
        """
        Validate Phase V (Customer API Integration)

        V1: Q12 premium_monthly slot exists + source_kind="PREMIUM_SSOT"
        V2: Q12 모든 insurer premium 존재 (G10)
        V3: Q1 Top-N deterministic
        V4: Premium 출력에 조건 + as_of_date + baseDt 포함
        V5: G5~G9 회귀 테스트
        """
        print("\n[Phase V] Customer API Integration")
        print("-" * 80)

        # V1: Q12 premium slot validation (use existing validate_q12_premium_gate.py)
        v1_status = self._run_subprocess(
            "python3 tools/audit/validate_q12_premium_gate.py "
            "--input data/compare_v1/compare_rows_v1.jsonl"
        )
        self.validation_results["phase_v"]["checks"]["V1_premium_slot"] = v1_status

        # V2: G10 gate enforcement (included in V1)
        self.validation_results["phase_v"]["checks"]["V2_g10_gate"] = v1_status

        # V3: Q1 Top-N deterministic (TODO: implement validate_q1_ranking.py)
        # self.validation_results["phase_v"]["checks"]["V3_q1_deterministic"] = "NOT_IMPLEMENTED"

        # V4: Premium metadata (included in V1)
        self.validation_results["phase_v"]["checks"]["V4_premium_metadata"] = v1_status

        # V5: G5~G9 regression (use existing validate_universe_gate.py)
        v5_status = self._run_subprocess(
            "python3 tools/audit/validate_universe_gate.py --data-dir data"
        )
        self.validation_results["phase_v"]["checks"]["V5_regression"] = v5_status

        # Phase V status
        all_passed = all(
            v == "PASS" for v in self.validation_results["phase_v"]["checks"].values()
            if v != "NOT_IMPLEMENTED"
        )
        self.validation_results["phase_v"]["status"] = "PASS" if all_passed else "FAIL"

    def _validate_phase_w(self):
        """
        Validate Phase W (Q14 Enhancement)

        W1: Q14 동일 입력 → 동일 Top-3
        W2: Premium 누락 상품 제외
        W3: Rounding 정책 고정
        """
        print("\n[Phase W] Q14 Premium Ranking")
        print("-" * 80)

        # TODO: Implement validate_q14_ranking.py
        print("  ⚠️  Phase W validation NOT IMPLEMENTED (Q14 ranking not built yet)")
        self.validation_results["phase_w"]["status"] = "NOT_IMPLEMENTED"
        self.validation_results["phase_w"]["checks"]["W1_deterministic"] = "NOT_IMPLEMENTED"
        self.validation_results["phase_w"]["checks"]["W2_no_estimation"] = "NOT_IMPLEMENTED"
        self.validation_results["phase_w"]["checks"]["W3_rounding"] = "NOT_IMPLEMENTED"

    def _validate_phase_x(self):
        """
        Validate Phase X (Operational Stability)

        X1: 54 API calls 성공/실패 집계
        X2: Premium SSOT sum match
        X3: E2E 회귀 테스트
        """
        print("\n[Phase X] Operational Stability")
        print("-" * 80)

        # X1: API call success/failure tracking (use validate_prdetail_pull.py)
        # (TODO: This script needs baseDt parameter support)
        # x1_status = self._run_subprocess(
        #     f"python3 tools/audit/validate_prdetail_pull.py --baseDt {self.base_dt}"
        # )
        # self.validation_results["phase_x"]["checks"]["X1_api_tracking"] = x1_status
        print("  ⚠️  X1 (API tracking) NOT IMPLEMENTED")
        self.validation_results["phase_x"]["checks"]["X1_api_tracking"] = "NOT_IMPLEMENTED"

        # X2: Premium SSOT validation (use existing validate_premium_ssot.py)
        x2_status = self._run_subprocess(
            f"python3 tools/audit/validate_premium_ssot.py --baseDt {self.base_dt}"
        )
        self.validation_results["phase_x"]["checks"]["X2_premium_ssot"] = x2_status

        # X3: E2E regression (combines Q12 + Q1 + Q14)
        # (Placeholder for now - will combine all checks)
        self.validation_results["phase_x"]["checks"]["X3_e2e_regression"] = "NOT_IMPLEMENTED"

        # Phase X status
        all_passed = all(
            v == "PASS" for v in self.validation_results["phase_x"]["checks"].values()
            if v != "NOT_IMPLEMENTED"
        )
        self.validation_results["phase_x"]["status"] = "PASS" if all_passed else "FAIL"

    def _run_subprocess(self, command: str) -> str:
        """
        Run subprocess command and return status

        Returns:
            "PASS" if exit code 0, "FAIL" otherwise
        """
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=60
            )
            return "PASS" if result.returncode == 0 else "FAIL"
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            print(f"  ❌ Error running: {command}")
            print(f"     {e}")
            return "ERROR"

    def _calculate_overall_status(self):
        """Calculate overall validation status"""
        phase_statuses = [
            self.validation_results["phase_v"]["status"],
            self.validation_results["phase_w"]["status"],
            self.validation_results["phase_x"]["status"]
        ]

        if all(s == "PASS" for s in phase_statuses):
            self.validation_results["overall_status"] = "PASS"
        elif any(s == "FAIL" for s in phase_statuses):
            self.validation_results["overall_status"] = "FAIL"
        else:
            self.validation_results["overall_status"] = "PARTIAL"

    def _print_report(self):
        """Print validation report"""
        print("\n" + "=" * 80)
        print("VWX Validation Report")
        print("=" * 80)
        print(f"baseDt: {self.base_dt}")
        print()

        # Phase V
        print("[Phase V] Customer API Integration:")
        for check, status in self.validation_results["phase_v"]["checks"].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"  {status_icon} {check}: {status}")
        print(f"  Status: {self.validation_results['phase_v']['status']}")
        print()

        # Phase W
        print("[Phase W] Q14 Premium Ranking:")
        for check, status in self.validation_results["phase_w"]["checks"].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"  {status_icon} {check}: {status}")
        print(f"  Status: {self.validation_results['phase_w']['status']}")
        print()

        # Phase X
        print("[Phase X] Operational Stability:")
        for check, status in self.validation_results["phase_x"]["checks"].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"  {status_icon} {check}: {status}")
        print(f"  Status: {self.validation_results['phase_x']['status']}")
        print()

        # Overall
        print("=" * 80)
        overall_icon = "✅" if self.validation_results["overall_status"] == "PASS" else "❌"
        print(f"{overall_icon} Overall Status: {self.validation_results['overall_status']}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-VWX E2E Validation (DoD V/W/X)"
    )
    parser.add_argument(
        "--baseDt",
        required=True,
        help="Base date (YYYYMMDD), e.g., 20260109"
    )

    args = parser.parse_args()

    validator = VWXValidator(args.baseDt)
    validator.validate_all()

    # Exit with status
    if validator.validation_results["overall_status"] == "PASS":
        sys.exit(0)
    elif validator.validation_results["overall_status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(2)  # PARTIAL (some not implemented)


if __name__ == "__main__":
    main()
