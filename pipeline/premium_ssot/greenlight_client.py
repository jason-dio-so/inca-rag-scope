#!/usr/bin/env python3
"""
STEP NEXT-V: Greenlight Customer API Client (2-Step Flow)

Constitutional Rules (ABSOLUTE):
- API Method: GET + JSON Body (NOT querystring)
- 2-Step Flow: prInfo → prDetail (LOCKED)
- Birthday: Templates ONLY (NO calculation)
  - 30→19960101, 40→19860101, 50→19760101
- Retry Policy: 5xx/timeout/connection max 2, 4xx NO retry
- Failures: ALL failures saved to _failures/{baseDt}.jsonl
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
from requests.exceptions import Timeout, ConnectionError


class GreenlightAPIClient:
    """
    Greenlight Customer API Client (2-Step Flow)

    STEP NEXT-V: Runtime Premium SSOT Population
    """

    BASE_URL = "https://new-prod.greenlight.direct/public/prdata"

    # Birthday Templates (LOCKED - NO CALCULATION)
    BIRTHDAY_TEMPLATES = {
        30: "19960101",
        40: "19860101",
        50: "19760101"
    }

    # Insurer Code Map (LOCKED)
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

    def __init__(self, output_dir: str = "data/premium_raw"):
        """
        Initialize Greenlight API Client

        Args:
            output_dir: Base directory for raw API responses and failures
        """
        self.output_dir = Path(output_dir)
        self.failures = []

    def pull_premium_for_request(
        self,
        base_dt: str,
        age: int,
        sex: str,
        plan_variant: str = "NO_REFUND"
    ) -> Dict[str, Any]:
        """
        Pull premium for single request context (age × sex × baseDt)

        2-Step Flow:
        1. prInfo → Get product list (prCd mapping)
        2. prDetail → Get coverage premiums

        Args:
            base_dt: YYYYMMDD (e.g., "20251126")
            age: 30 | 40 | 50
            sex: "M" | "F"
            plan_variant: "NO_REFUND" | "GENERAL"

        Returns:
            Dict with:
                - prinfo_response: prInfo API response
                - prdetail_response: prDetail API response
                - product_list: List of products from prInfo
                - coverage_premiums: List of coverage premium records
                - failures: List of failure records
        """
        result = {
            "base_dt": base_dt,
            "age": age,
            "sex": sex,
            "plan_variant": plan_variant,
            "prinfo_response": None,
            "prdetail_response": None,
            "product_list": [],
            "coverage_premiums": [],
            "failures": []
        }

        # Step 1: Pull prInfo
        prinfo_result = self._call_prinfo(base_dt, age, sex)

        if prinfo_result["status"] == "SUCCESS":
            result["prinfo_response"] = prinfo_result["response"]
            result["product_list"] = self._parse_prinfo_products(prinfo_result["response"])

            # Save raw prInfo
            self._save_raw_prinfo(base_dt, age, sex, prinfo_result["response"])
        else:
            # prInfo failed → save failure and return
            failure = self._build_failure_record(
                endpoint="prInfo",
                base_dt=base_dt,
                age=age,
                sex=sex,
                error=prinfo_result["error"],
                status_code=prinfo_result.get("status_code"),
                response_body=prinfo_result.get("response_body")
            )
            result["failures"].append(failure)
            self._save_failure(failure, base_dt)
            return result

        # Step 2: Pull prDetail
        prdetail_result = self._call_prdetail(base_dt, age, sex)

        if prdetail_result["status"] == "SUCCESS":
            result["prdetail_response"] = prdetail_result["response"]

            # Parse coverage premiums (NO_REFUND only from API)
            result["coverage_premiums"] = self._parse_prdetail_coverages(
                prdetail_result["response"],
                age,
                sex
            )

            # Save raw prDetail
            self._save_raw_prdetail(base_dt, age, sex, prdetail_result["response"])
        else:
            # prDetail failed → save failure
            failure = self._build_failure_record(
                endpoint="prDetail",
                base_dt=base_dt,
                age=age,
                sex=sex,
                error=prdetail_result["error"],
                status_code=prdetail_result.get("status_code"),
                response_body=prdetail_result.get("response_body")
            )
            result["failures"].append(failure)
            self._save_failure(failure, base_dt)

        return result

    def _call_prinfo(self, base_dt: str, age: int, sex: str) -> Dict[str, Any]:
        """
        Call prInfo API (GET + JSON Body)

        Returns:
            Dict with status ("SUCCESS" | "FAIL"), response, error, status_code
        """
        endpoint = f"{self.BASE_URL}/prInfo"

        # Get birthday template (NO CALCULATION)
        birthday = self.BIRTHDAY_TEMPLATES.get(age)
        if not birthday:
            return {
                "status": "FAIL",
                "error": f"No birthday template for age {age}",
                "status_code": None
            }

        # Convert sex (M→"1", F→"2")
        sex_code = "1" if sex == "M" else "2"

        # Build request body
        body = {
            "baseDt": base_dt,
            "birthday": birthday,
            "customerNm": "홍길동",  # LOCKED
            "sex": sex_code,
            "age": str(age)
        }

        # Call API with retry
        return self._call_api_with_retry(endpoint, body, max_retries=2)

    def _call_prdetail(self, base_dt: str, age: int, sex: str) -> Dict[str, Any]:
        """
        Call prDetail API (GET + JSON Body)

        Returns:
            Dict with status ("SUCCESS" | "FAIL"), response, error, status_code
        """
        endpoint = f"{self.BASE_URL}/prDetail"

        # Get birthday template (NO CALCULATION)
        birthday = self.BIRTHDAY_TEMPLATES.get(age)
        if not birthday:
            return {
                "status": "FAIL",
                "error": f"No birthday template for age {age}",
                "status_code": None
            }

        # Convert sex (M→"1", F→"2")
        sex_code = "1" if sex == "M" else "2"

        # Build request body (same as prInfo)
        body = {
            "baseDt": base_dt,
            "birthday": birthday,
            "customerNm": "홍길동",  # LOCKED
            "sex": sex_code,
            "age": str(age)
        }

        # Call API with retry
        return self._call_api_with_retry(endpoint, body, max_retries=2)

    def _call_api_with_retry(
        self,
        endpoint: str,
        body: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Call API with retry policy

        Retry Policy (LOCKED):
        - 5xx / Timeout / ConnectionError: Retry up to max_retries
        - 4xx (Client Error): NO retry (immediate fail)

        Args:
            endpoint: Full API URL
            body: JSON body
            max_retries: Max retry attempts (default: 2)

        Returns:
            Dict with status, response, error, status_code, response_body
        """
        timeout = 15  # seconds
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # GET + JSON Body (NOT querystring)
                response = requests.get(
                    endpoint,
                    json=body,
                    timeout=timeout,
                    headers={"Content-Type": "application/json"}
                )

                status_code = response.status_code

                # 2xx: Success
                if 200 <= status_code < 300:
                    try:
                        json_response = response.json()
                        return {
                            "status": "SUCCESS",
                            "response": json_response,
                            "status_code": status_code,
                            "retry_count": retry_count
                        }
                    except json.JSONDecodeError:
                        return {
                            "status": "FAIL",
                            "error": f"Invalid JSON response (status {status_code})",
                            "status_code": status_code,
                            "response_body": response.text[:1000]
                        }

                # 4xx: Client Error (NO RETRY)
                if 400 <= status_code < 500:
                    return {
                        "status": "FAIL",
                        "error": f"Client error {status_code}",
                        "status_code": status_code,
                        "response_body": response.text[:1000]
                    }

                # 5xx: Server Error (RETRY)
                if status_code >= 500:
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"  ⚠️  Server error {status_code}, retrying ({retry_count}/{max_retries})...")
                        continue
                    else:
                        return {
                            "status": "FAIL",
                            "error": f"Server error {status_code} after {max_retries} retries",
                            "status_code": status_code,
                            "response_body": response.text[:1000]
                        }

            except (Timeout, ConnectionError) as e:
                # Network errors: Retry
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"  ⚠️  Network error ({type(e).__name__}), retrying ({retry_count}/{max_retries})...")
                    continue
                else:
                    return {
                        "status": "FAIL",
                        "error": f"Network error after {max_retries} retries: {str(e)}",
                        "status_code": None,
                        "response_body": None
                    }

            except Exception as e:
                # Other errors: Immediate fail (no retry)
                return {
                    "status": "FAIL",
                    "error": f"Unexpected error: {str(e)}",
                    "status_code": None,
                    "response_body": None
                }

        # Should not reach here
        return {
            "status": "FAIL",
            "error": "Max retries exceeded",
            "status_code": None
        }

    def _parse_prinfo_products(self, prinfo_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse prInfo response to extract product list

        Args:
            prinfo_response: prInfo API response

        Returns:
            List of products: [{insCd, prCd, prNm, monthlyPrem, ...}]
        """
        out_pr_list = prinfo_response.get("outPrList", [])
        return out_pr_list

    def _parse_prdetail_coverages(
        self,
        prdetail_response: Dict[str, Any],
        age: int,
        sex: str
    ) -> List[Dict[str, Any]]:
        """
        Parse prDetail response to extract coverage premiums (NO_REFUND only)

        Args:
            prdetail_response: prDetail API response
            age: Age
            sex: Sex

        Returns:
            List of coverage premium records
        """
        coverage_premiums = []

        # Navigate structure: prProdLineCondOutSearchDiv[] → prProdLineCondOutIns[]
        search_divs = prdetail_response.get("prProdLineCondOutSearchDiv", [])

        for search_div in search_divs:
            ins_list = search_div.get("prProdLineCondOutIns", [])

            for ins_detail in ins_list:
                ins_cd = ins_detail.get("insCd")
                pr_cd = ins_detail.get("prCd")
                pr_nm = ins_detail.get("prNm")
                monthly_prem_sum = ins_detail.get("monthlyPremSum", 0)
                total_prem_sum = ins_detail.get("totalPremSum", 0)
                pay_term_years = ins_detail.get("payTermYears", 0)
                ins_term_years = ins_detail.get("insTermYears", 0)

                # Find insurer_key from ins_cd
                insurer_key = None
                for key, code in self.INSURER_CODE_MAP.items():
                    if code == ins_cd:
                        insurer_key = key
                        break

                if not insurer_key:
                    # Unknown insurer → skip
                    continue

                # Parse coverages
                cvr_amt_arr_lst = ins_detail.get("cvrAmtArrLst", [])

                for cvr in cvr_amt_arr_lst:
                    cvr_cd = cvr.get("cvrCd")
                    cvr_nm = cvr.get("cvrNm")
                    acc_amt = cvr.get("accAmt", 0)
                    monthly_prem = cvr.get("monthlyPrem", 0)

                    coverage_premiums.append({
                        "insurer_key": insurer_key,
                        "ins_cd": ins_cd,
                        "pr_cd": pr_cd,
                        "pr_nm": pr_nm,
                        "coverage_code": cvr_cd,
                        "coverage_name": cvr_nm,
                        "plan_variant": "NO_REFUND",
                        "age": age,
                        "sex": sex,
                        "premium_monthly_coverage": monthly_prem,
                        "coverage_amount": acc_amt,
                        "monthly_prem_sum": monthly_prem_sum,
                        "total_prem_sum": total_prem_sum,
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years,
                        "source_kind": "PREMIUM_SSOT"
                    })

        return coverage_premiums

    def _save_raw_prinfo(
        self,
        base_dt: str,
        age: int,
        sex: str,
        response: Dict[str, Any]
    ):
        """Save raw prInfo response"""
        dir_path = self.output_dir / base_dt / "_prInfo"
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{age}_{sex}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)

    def _save_raw_prdetail(
        self,
        base_dt: str,
        age: int,
        sex: str,
        response: Dict[str, Any]
    ):
        """Save raw prDetail response"""
        dir_path = self.output_dir / base_dt / "_prDetail"
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / f"{age}_{sex}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)

    def _build_failure_record(
        self,
        endpoint: str,
        base_dt: str,
        age: int,
        sex: str,
        error: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build failure record for _failures/ log

        Args:
            endpoint: "prInfo" | "prDetail"
            base_dt: YYYYMMDD
            age: Age
            sex: Sex
            error: Error message
            status_code: HTTP status code (if available)
            response_body: Response body snippet (if available)

        Returns:
            Failure record dict
        """
        birthday = self.BIRTHDAY_TEMPLATES.get(age, "UNKNOWN")
        sex_code = "1" if sex == "M" else "2"

        return {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "base_dt": base_dt,
            "age": age,
            "sex": sex,
            "request_params": {
                "baseDt": base_dt,
                "birthday": birthday,
                "customerNm": "홍길동",
                "sex": sex_code,
                "age": str(age)
            },
            "error": error,
            "status_code": status_code,
            "response_body_snippet": response_body[:1000] if response_body else None
        }

    def _save_failure(self, failure: Dict[str, Any], base_dt: str):
        """
        Save failure record to _failures/{baseDt}.jsonl

        Args:
            failure: Failure record
            base_dt: YYYYMMDD
        """
        failures_dir = self.output_dir / "_failures"
        failures_dir.mkdir(parents=True, exist_ok=True)

        failure_file = failures_dir / f"{base_dt}.jsonl"

        # Append to JSONL
        with open(failure_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(failure, ensure_ascii=False, default=str) + '\n')


if __name__ == "__main__":
    # Test client
    import argparse

    parser = argparse.ArgumentParser(description="Test Greenlight API Client")
    parser.add_argument("--baseDt", required=True, help="Base date YYYYMMDD")
    parser.add_argument("--age", type=int, default=30, help="Age (30/40/50)")
    parser.add_argument("--sex", default="M", help="Sex (M/F)")

    args = parser.parse_args()

    client = GreenlightAPIClient()
    result = client.pull_premium_for_request(
        base_dt=args.baseDt,
        age=args.age,
        sex=args.sex
    )

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
