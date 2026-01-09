#!/usr/bin/env python3
"""
STEP NEXT-V: Runtime SSOT Upsert

Constitutional Rules (ABSOLUTE):
- NO_REFUND: API values as-is (NO modification)
- GENERAL: round(NO_REFUND × multiplier/100) ONLY if multiplier exists
- Sum Validation: sum(coverage.monthlyPrem) == monthlyPremSum (0 tolerance)
- Product ID Map: prInfo-based ONLY (NO name similarity guessing)
- NO LLM / NO estimation / NO inference
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class RuntimeSSOTUpserter:
    """
    Runtime SSOT Upsert Handler

    Converts API responses to SSOT records and validates sums.
    """

    def __init__(self, multiplier_data: List[Dict[str, Any]] = None):
        """
        Initialize SSOT upserter

        Args:
            multiplier_data: Multiplier records from multiplier Excel
                [{insurer_key, coverage_name, multiplier_percent}]
        """
        self.multiplier_data = multiplier_data or []
        self.multiplier_map = self._build_multiplier_map()

    def _build_multiplier_map(self) -> Dict[tuple, float]:
        """
        Build multiplier lookup map

        Returns:
            Dict: {(insurer_key, coverage_name): multiplier_percent}
        """
        multiplier_map = {}
        for m in self.multiplier_data:
            key = (m["insurer_key"], m["coverage_name"])
            multiplier_map[key] = m["multiplier_percent"]

        return multiplier_map

    def convert_api_to_ssot(
        self,
        api_result: Dict[str, Any],
        base_dt: str,
        product_id_map: Dict[tuple, str]
    ) -> Dict[str, Any]:
        """
        Convert API result to SSOT records

        Args:
            api_result: Result from GreenlightAPIClient.pull_premium_for_request()
            base_dt: YYYYMMDD
            product_id_map: {(insurer_key, pr_cd): product_id}

        Returns:
            Dict with:
                - product_premium_records: List[Dict] for product_premium_quote_v2
                - coverage_premium_records: List[Dict] for coverage_premium_quote
                - validation_results: List[Dict] (sum match status)
                - errors: List[str]
        """
        result = {
            "product_premium_records": [],
            "coverage_premium_records": [],
            "validation_results": [],
            "errors": []
        }

        # Extract coverages from API result
        coverage_premiums = api_result.get("coverage_premiums", [])

        if not coverage_premiums:
            result["errors"].append("No coverage premiums in API result")
            return result

        # Group by (insurer_key, pr_cd)
        grouped = defaultdict(list)
        for cov in coverage_premiums:
            key = (cov["insurer_key"], cov["pr_cd"])
            grouped[key].append(cov)

        # Process each group
        for (insurer_key, pr_cd), coverages in grouped.items():
            # Get product_id from map
            product_id = product_id_map.get((insurer_key, pr_cd))

            if not product_id:
                result["errors"].append(
                    f"No product_id mapping for {insurer_key} | {pr_cd}"
                )
                continue

            # Extract metadata from first coverage
            first_cov = coverages[0]
            age = first_cov["age"]
            sex = first_cov["sex"]
            monthly_prem_sum = first_cov["monthly_prem_sum"]
            total_prem_sum = first_cov["total_prem_sum"]
            pay_term_years = first_cov["pay_term_years"]
            ins_term_years = first_cov["ins_term_years"]

            # Validate sum (NO_REFUND only)
            calculated_sum = sum(c["premium_monthly_coverage"] for c in coverages)
            sum_match = (calculated_sum == monthly_prem_sum)

            validation_result = {
                "insurer_key": insurer_key,
                "product_id": product_id,
                "age": age,
                "sex": sex,
                "expected_sum": monthly_prem_sum,
                "calculated_sum": calculated_sum,
                "match": sum_match,
                "error": abs(calculated_sum - monthly_prem_sum) if not sum_match else 0
            }
            result["validation_results"].append(validation_result)

            if not sum_match:
                result["errors"].append(
                    f"Sum mismatch: {insurer_key} | {product_id} | "
                    f"expected {monthly_prem_sum}, got {calculated_sum}"
                )

            # Build product_premium_quote_v2 record (NO_REFUND)
            product_record = {
                "insurer_key": insurer_key,
                "product_id": product_id,
                "plan_variant": "NO_REFUND",
                "age": age,
                "sex": sex,
                "smoke": "NA",
                "pay_term_years": pay_term_years,
                "ins_term_years": ins_term_years,
                "as_of_date": f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:]}",
                "premium_monthly_total": monthly_prem_sum,
                "premium_total_total": total_prem_sum,
                "calculated_monthly_sum": calculated_sum,
                "sum_match_status": "MATCH" if sum_match else "MISMATCH",
                "source_table_id": "prDetail_api",
                "api_response_hash": hashlib.sha256(
                    json.dumps(coverages, sort_keys=True).encode()
                ).hexdigest()[:16],
                "response_age": age
            }
            result["product_premium_records"].append(product_record)

            # Build coverage_premium_quote records (NO_REFUND)
            for cov in coverages:
                coverage_record = {
                    "insurer_key": insurer_key,
                    "product_id": product_id,
                    "coverage_code": cov["coverage_code"],
                    "coverage_name": cov["coverage_name"],
                    "plan_variant": "NO_REFUND",
                    "age": age,
                    "sex": sex,
                    "smoke": "NA",
                    "premium_monthly_coverage": cov["premium_monthly_coverage"],
                    "coverage_amount": cov["coverage_amount"],
                    "source_table_id": "prDetail_api",
                    "source_kind": "PREMIUM_SSOT"
                }
                result["coverage_premium_records"].append(coverage_record)

            # Generate GENERAL records (if multiplier exists)
            general_records = self._generate_general_records(
                coverages,
                insurer_key,
                product_id,
                age,
                sex,
                base_dt
            )

            result["coverage_premium_records"].extend(general_records)

            # Add GENERAL product record if any GENERAL coverages exist
            if general_records:
                # Calculate GENERAL sum
                general_sum = sum(r["premium_monthly_coverage"] for r in general_records)

                general_product_record = {
                    "insurer_key": insurer_key,
                    "product_id": product_id,
                    "plan_variant": "GENERAL",
                    "age": age,
                    "sex": sex,
                    "smoke": "NA",
                    "pay_term_years": pay_term_years,
                    "ins_term_years": ins_term_years,
                    "as_of_date": f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:]}",
                    "premium_monthly_total": general_sum,
                    "premium_total_total": 0,  # Not available from API
                    "calculated_monthly_sum": general_sum,
                    "sum_match_status": "CALCULATED",
                    "source_table_id": "prDetail_api_general_derived",
                    "api_response_hash": hashlib.sha256(
                        json.dumps(general_records, sort_keys=True).encode()
                    ).hexdigest()[:16],
                    "response_age": age
                }
                result["product_premium_records"].append(general_product_record)

        return result

    def _generate_general_records(
        self,
        no_refund_coverages: List[Dict[str, Any]],
        insurer_key: str,
        product_id: str,
        age: int,
        sex: str,
        base_dt: str
    ) -> List[Dict[str, Any]]:
        """
        Generate GENERAL coverage records from NO_REFUND

        Formula: GENERAL = round(NO_REFUND × multiplier / 100)

        Args:
            no_refund_coverages: NO_REFUND coverage records
            insurer_key: Insurer key
            product_id: Product ID
            age: Age
            sex: Sex
            base_dt: YYYYMMDD

        Returns:
            List of GENERAL coverage records
        """
        general_records = []

        for cov in no_refund_coverages:
            coverage_name = cov["coverage_name"]

            # Lookup multiplier
            multiplier_key = (insurer_key, coverage_name)
            multiplier = self.multiplier_map.get(multiplier_key)

            if not multiplier:
                # No multiplier → Skip GENERAL generation
                continue

            # Calculate GENERAL premium
            no_refund_premium = cov["premium_monthly_coverage"]
            general_premium = round(no_refund_premium * multiplier / 100)

            general_record = {
                "insurer_key": insurer_key,
                "product_id": product_id,
                "coverage_code": cov["coverage_code"],
                "coverage_name": coverage_name,
                "plan_variant": "GENERAL",
                "age": age,
                "sex": sex,
                "smoke": "NA",
                "premium_monthly_coverage": general_premium,
                "coverage_amount": cov["coverage_amount"],
                "source_table_id": "prDetail_api_general_derived",
                "source_kind": "PREMIUM_SSOT",
                "multiplier_percent": multiplier,
                "base_no_refund_premium": no_refund_premium
            }
            general_records.append(general_record)

        return general_records

    def build_product_id_map(
        self,
        prinfo_products: List[Dict[str, Any]],
        compare_products: List[Dict[str, str]]
    ) -> Dict[tuple, str]:
        """
        Build product_id map from prInfo products

        Mapping Strategy (LOCKED):
        - Match by insCd (EXACT)
        - If multiple products for same insurer → use first (NO guessing)

        Args:
            prinfo_products: Products from prInfo outPrList
            compare_products: Products from compare_rows
                [{insurer_key, product_id}]

        Returns:
            Dict: {(insurer_key, pr_cd): product_id}
        """
        # Insurer code map
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

        # Reverse map: ins_cd → insurer_key
        ins_cd_to_key = {v: k for k, v in INSURER_CODE_MAP.items()}

        # Build map: {(insurer_key, pr_cd): product_id}
        product_map = {}

        for compare_prod in compare_products:
            insurer_key = compare_prod["insurer_key"]
            product_id = compare_prod["product_id"]

            # Get expected ins_cd
            expected_ins_cd = INSURER_CODE_MAP.get(insurer_key)
            if not expected_ins_cd:
                continue

            # Find products with matching ins_cd
            matching_products = [
                p for p in prinfo_products
                if p.get("insCd") == expected_ins_cd
            ]

            if not matching_products:
                # No products for this insurer
                continue

            # Use first product (NO guessing)
            pr_cd = matching_products[0].get("prCd")

            if pr_cd:
                product_map[(insurer_key, pr_cd)] = product_id

        return product_map


def load_multiplier_data(multiplier_excel_path: str) -> List[Dict[str, Any]]:
    """
    Load multiplier data from Excel

    Args:
        multiplier_excel_path: Path to multiplier Excel file

    Returns:
        List of multiplier records
    """
    from pipeline.premium_ssot.multiplier_loader import load_multiplier_excel

    return load_multiplier_excel(multiplier_excel_path)


if __name__ == "__main__":
    # Test upserter
    import argparse

    parser = argparse.ArgumentParser(description="Test Runtime SSOT Upserter")
    parser.add_argument("--api-result", required=True, help="Path to API result JSON")
    parser.add_argument("--baseDt", required=True, help="Base date YYYYMMDD")
    parser.add_argument(
        "--multiplier-excel",
        default="data/sources/insurers/4. 일반보험요율예시.xlsx",
        help="Path to multiplier Excel"
    )

    args = parser.parse_args()

    # Load API result
    with open(args.api_result, 'r', encoding='utf-8') as f:
        api_result = json.load(f)

    # Load multipliers
    multipliers = load_multiplier_data(args.multiplier_excel)

    # Create upserter
    upserter = RuntimeSSOTUpserter(multiplier_data=multipliers)

    # Mock product_id_map (TODO: load from real map)
    product_id_map = {
        ("samsung", "some_pr_cd"): "samsung__삼성화재건강보험"
    }

    # Convert
    result = upserter.convert_api_to_ssot(api_result, args.baseDt, product_id_map)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
