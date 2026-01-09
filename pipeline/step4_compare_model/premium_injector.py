#!/usr/bin/env python3
"""
STEP NEXT-V: Premium Injector (Runtime Q12/Q1/Q14 Integration)

Constitutional Rules (ABSOLUTE):
- Premium = SSOT ONLY (NO LLM/estimation/inference)
- Q12: ALL insurers MUST have premium (G10 gate)
- SSOT miss → Option A (sync_pull) OR Option B (fail_on_miss)
- source_kind = "PREMIUM_SSOT" (LOCKED)
- NO birthday calculation (templates only)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class PremiumInjector:
    """
    Runtime Premium Injector for Q12/Q1/Q14

    Injects premium_monthly slot into CompareRow instances.
    """

    def __init__(
        self,
        ssot_dir: str = "data/premium_raw",
        multiplier_excel: str = "data/sources/insurers/4. 일반보험요율예시.xlsx",
        runtime_policy: str = None
    ):
        """
        Initialize Premium Injector

        Args:
            ssot_dir: Directory for premium SSOT raw files
            multiplier_excel: Path to multiplier Excel
            runtime_policy: "sync_pull" | "fail_on_miss" (defaults to env PREMIUM_RUNTIME_POLICY)
        """
        self.ssot_dir = Path(ssot_dir)
        self.multiplier_excel = multiplier_excel

        # Runtime policy: sync_pull (Option A) or fail_on_miss (Option B)
        self.runtime_policy = runtime_policy or os.getenv("PREMIUM_RUNTIME_POLICY", "sync_pull")

        if self.runtime_policy not in ["sync_pull", "fail_on_miss"]:
            raise ValueError(
                f"Invalid PREMIUM_RUNTIME_POLICY: {self.runtime_policy}. "
                f"Must be 'sync_pull' or 'fail_on_miss'"
            )

    def inject_premium_for_q12(
        self,
        compare_rows: List[Dict[str, Any]],
        base_dt: str,
        age: int,
        sex: str,
        plan_variant: str = "NO_REFUND"
    ) -> Dict[str, Any]:
        """
        Inject premium_monthly slot for Q12 comparison

        G10 Gate: ALL insurers MUST have premium (if ANY missing → FAIL)

        Args:
            compare_rows: List of CompareRow dicts
            base_dt: YYYYMMDD
            age: 30 | 40 | 50
            sex: "M" | "F"
            plan_variant: "NO_REFUND" | "GENERAL"

        Returns:
            Dict with:
                - compare_rows: List[Dict] with premium_monthly injected
                - status: "SUCCESS" | "FAIL"
                - missing_insurers: List[str] (if any)
                - errors: List[str]
        """
        result = {
            "compare_rows": [],
            "status": "PENDING",
            "missing_insurers": [],
            "errors": []
        }

        # Extract unique insurers/products
        insurer_product_set = set()
        for row in compare_rows:
            identity = row.get("identity", {})
            insurer_key = identity.get("insurer_key")
            product_id = identity.get("product_key")

            if insurer_key and product_id:
                insurer_product_set.add((insurer_key, product_id))

        # Load SSOT premium data
        ssot_data = self._load_ssot_premium(base_dt, age, sex, plan_variant)

        if ssot_data["status"] == "MISS":
            # SSOT miss → Apply runtime policy
            if self.runtime_policy == "sync_pull":
                # Option A: Synchronous Pull
                print(f"  ⚠️  SSOT miss for baseDt={base_dt}, age={age}, sex={sex}")
                print(f"     Triggering synchronous Pull (PREMIUM_RUNTIME_POLICY=sync_pull)...")

                pull_result = self._sync_pull_and_upsert(base_dt, age, sex, plan_variant)

                if pull_result["status"] == "SUCCESS":
                    # Reload SSOT after Pull
                    ssot_data = self._load_ssot_premium(base_dt, age, sex, plan_variant)
                else:
                    result["errors"].extend(pull_result["errors"])
                    result["status"] = "FAIL"
                    return result

            elif self.runtime_policy == "fail_on_miss":
                # Option B: Fail immediately
                result["errors"].append(
                    f"SSOT miss for baseDt={base_dt}, age={age}, sex={sex}. "
                    f"PREMIUM_RUNTIME_POLICY=fail_on_miss → FAIL"
                )
                result["status"] = "FAIL"
                return result

        # Check premium coverage for ALL insurers (G10 gate)
        premium_map = ssot_data.get("premium_map", {})
        insurers_with_premium = set()
        insurers_without_premium = set()

        for (insurer_key, product_id) in insurer_product_set:
            if (insurer_key, product_id) in premium_map:
                insurers_with_premium.add(insurer_key)
            else:
                insurers_without_premium.add(insurer_key)

        # G10 GATE: Q12 requires ALL insurers to have premium
        if insurers_without_premium:
            result["missing_insurers"] = list(insurers_without_premium)
            result["errors"].append(
                f"G10 FAIL: Q12 requires premium for ALL insurers. "
                f"Missing: {', '.join(insurers_without_premium)}"
            )
            result["status"] = "FAIL"
            return result

        # Inject premium_monthly slot
        injected_rows = []

        for row in compare_rows:
            identity = row.get("identity", {})
            insurer_key = identity.get("insurer_key")
            product_id = identity.get("product_key")

            # Get premium from map
            premium_data = premium_map.get((insurer_key, product_id))

            if premium_data:
                # Inject premium_monthly slot
                row_with_premium = row.copy()

                # Build SlotValue for premium_monthly
                premium_slot = {
                    "status": "FOUND",
                    "value": {
                        "amount": premium_data["premium_monthly_total"],
                        "currency": "KRW",
                        "plan_variant": plan_variant,
                        "age": age,
                        "sex": sex,
                        "as_of_date": premium_data["as_of_date"],
                        "baseDt": base_dt
                    },
                    "source_kind": "PREMIUM_SSOT",
                    "confidence": {
                        "level": "HIGH",
                        "basis": f"Premium SSOT (API: prDetail_api, baseDt={base_dt})"
                    },
                    "evidences": [
                        {
                            "table_id": "prDetail_api",
                            "as_of_date": premium_data["as_of_date"],
                            "response_hash": premium_data.get("api_response_hash", "")
                        }
                    ]
                }

                # Add to slots (or create slots if missing)
                if "slots" not in row_with_premium:
                    row_with_premium["slots"] = {}

                row_with_premium["slots"]["premium_monthly"] = premium_slot

                injected_rows.append(row_with_premium)
            else:
                # Should not happen (already checked in G10 gate)
                injected_rows.append(row)

        result["compare_rows"] = injected_rows
        result["status"] = "SUCCESS"

        return result

    def _load_ssot_premium(
        self,
        base_dt: str,
        age: int,
        sex: str,
        plan_variant: str
    ) -> Dict[str, Any]:
        """
        Load premium from SSOT (raw JSON files)

        Args:
            base_dt: YYYYMMDD
            age: 30 | 40 | 50
            sex: "M" | "F"
            plan_variant: "NO_REFUND" | "GENERAL"

        Returns:
            Dict with:
                - status: "HIT" | "MISS"
                - premium_map: {(insurer_key, product_id): premium_data}
        """
        # Check if prDetail exists for this (baseDt, age, sex)
        prdetail_path = self.ssot_dir / base_dt / "_prDetail" / f"{age}_{sex}.json"

        if not prdetail_path.exists():
            return {
                "status": "MISS",
                "premium_map": {}
            }

        # Load prDetail
        with open(prdetail_path, 'r', encoding='utf-8') as f:
            prdetail_response = json.load(f)

        # Load prInfo for product mapping
        prinfo_path = self.ssot_dir / base_dt / "_prInfo" / f"{age}_{sex}.json"

        if not prinfo_path.exists():
            return {
                "status": "MISS",
                "premium_map": {}
            }

        with open(prinfo_path, 'r', encoding='utf-8') as f:
            prinfo_response = json.load(f)

        # Build product_id_map from prInfo
        # (This is a simplified version - in production, use compare_rows products)
        from pipeline.premium_ssot.runtime_upsert import RuntimeSSOTUpserter

        upserter = RuntimeSSOTUpserter()
        prinfo_products = prinfo_response.get("outPrList", [])

        # For now, build a simple map (insurer_key, pr_cd) → product_id
        # In production, this should use compare_rows to get actual product_ids
        product_id_map = {}

        INSURER_CODE_MAP = {
            'meritz': 'N01',
            'hanwha': 'N02',
            'lotte': 'N03',
            'heungkuk': 'N05',
            'samsung': 'N08',
            'hyundai': 'N09',
            'kb': 'N10',
            'db': 'N13'
        }

        ins_cd_to_key = {v: k for k, v in INSURER_CODE_MAP.items()}

        for product in prinfo_products:
            ins_cd = product.get("insCd")
            pr_cd = product.get("prCd")
            pr_nm = product.get("prNm", "")

            insurer_key = ins_cd_to_key.get(ins_cd)

            if insurer_key and pr_cd:
                # Build product_id (simplified - use prNm hint)
                product_id = f"{insurer_key}__{pr_nm.split()[0] if pr_nm else pr_cd}"
                product_id_map[(insurer_key, pr_cd)] = product_id

        # Parse prDetail to build premium_map
        premium_map = {}

        search_divs = prdetail_response.get("prProdLineCondOutSearchDiv", [])

        for search_div in search_divs:
            ins_list = search_div.get("prProdLineCondOutIns", [])

            for ins_detail in ins_list:
                ins_cd = ins_detail.get("insCd")
                pr_cd = ins_detail.get("prCd")
                monthly_prem_sum = ins_detail.get("monthlyPremSum", 0)
                total_prem_sum = ins_detail.get("totalPremSum", 0)
                pay_term_years = ins_detail.get("payTermYears", 0)
                ins_term_years = ins_detail.get("insTermYears", 0)

                insurer_key = ins_cd_to_key.get(ins_cd)
                product_id = product_id_map.get((insurer_key, pr_cd))

                if insurer_key and product_id:
                    premium_map[(insurer_key, product_id)] = {
                        "premium_monthly_total": monthly_prem_sum,
                        "premium_total_total": total_prem_sum,
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years,
                        "as_of_date": f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:]}",
                        "api_response_hash": "runtime_loaded"
                    }

        return {
            "status": "HIT",
            "premium_map": premium_map
        }

    def _sync_pull_and_upsert(
        self,
        base_dt: str,
        age: int,
        sex: str,
        plan_variant: str
    ) -> Dict[str, Any]:
        """
        Synchronous Pull + SSOT Upsert

        Calls Greenlight API → Saves raw → Upserts SSOT

        Args:
            base_dt: YYYYMMDD
            age: 30 | 40 | 50
            sex: "M" | "F"
            plan_variant: "NO_REFUND" | "GENERAL"

        Returns:
            Dict with status ("SUCCESS" | "FAIL"), errors
        """
        from pipeline.premium_ssot.greenlight_client import GreenlightAPIClient
        from pipeline.premium_ssot.runtime_upsert import RuntimeSSOTUpserter, load_multiplier_data

        result = {
            "status": "PENDING",
            "errors": []
        }

        # Initialize client
        client = GreenlightAPIClient(output_dir=str(self.ssot_dir))

        # Pull premium
        print(f"  → Calling Greenlight API (baseDt={base_dt}, age={age}, sex={sex})...")

        api_result = client.pull_premium_for_request(base_dt, age, sex, plan_variant)

        # Check failures
        if api_result["failures"]:
            result["errors"].extend([f["error"] for f in api_result["failures"]])
            result["status"] = "FAIL"
            return result

        # Load multipliers
        multipliers = load_multiplier_data(self.multiplier_excel)

        # Initialize upserter
        upserter = RuntimeSSOTUpserter(multiplier_data=multipliers)

        # Build product_id_map from prInfo
        prinfo_products = api_result.get("product_list", [])

        # For now, use simplified product_id_map
        # In production, this should use compare_rows products
        product_id_map = {}

        INSURER_CODE_MAP = {
            'meritz': 'N01',
            'hanwha': 'N02',
            'lotte': 'N03',
            'heungkuk': 'N05',
            'samsung': 'N08',
            'hyundai': 'N09',
            'kb': 'N10',
            'db': 'N13'
        }

        ins_cd_to_key = {v: k for k, v in INSURER_CODE_MAP.items()}

        for product in prinfo_products:
            ins_cd = product.get("insCd")
            pr_cd = product.get("prCd")
            pr_nm = product.get("prNm", "")

            insurer_key = ins_cd_to_key.get(ins_cd)

            if insurer_key and pr_cd:
                product_id = f"{insurer_key}__{pr_nm.split()[0] if pr_nm else pr_cd}"
                product_id_map[(insurer_key, pr_cd)] = product_id

        # Convert to SSOT records
        ssot_result = upserter.convert_api_to_ssot(api_result, base_dt, product_id_map)

        if ssot_result["errors"]:
            result["errors"].extend(ssot_result["errors"])
            result["status"] = "FAIL"
            return result

        # SSOT records are now in memory (ssot_result)
        # In production, these would be written to DB
        # For now, raw files are already saved by GreenlightAPIClient

        print(f"  ✅ SSOT populated: {len(ssot_result['product_premium_records'])} products")

        result["status"] = "SUCCESS"

        return result


if __name__ == "__main__":
    # Test injector
    import argparse

    parser = argparse.ArgumentParser(description="Test Premium Injector")
    parser.add_argument("--baseDt", required=True, help="Base date YYYYMMDD")
    parser.add_argument("--age", type=int, default=30, help="Age (30/40/50)")
    parser.add_argument("--sex", default="M", help="Sex (M/F)")
    parser.add_argument("--plan-variant", default="NO_REFUND", help="Plan variant")
    parser.add_argument(
        "--compare-rows",
        default="data/compare_v1/compare_rows_v1.jsonl",
        help="Path to compare_rows JSONL"
    )

    args = parser.parse_args()

    # Load compare_rows
    compare_rows = []
    with open(args.compare_rows, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                compare_rows.append(json.loads(line))

    # Initialize injector
    injector = PremiumInjector()

    # Inject premium
    result = injector.inject_premium_for_q12(
        compare_rows=compare_rows,
        base_dt=args.baseDt,
        age=args.age,
        sex=args.sex,
        plan_variant=args.plan_variant
    )

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
