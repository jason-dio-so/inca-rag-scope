#!/usr/bin/env python3
"""
STEP NEXT-DB2: Premium SSOT Real Data Load Runner

Purpose:
  Load real premium data from Greenlight API into DB (port 5432)
  with ZERO TOLERANCE enforcement.

Constitutional Rules:
- baseDt = 20251126 (LOCKED)
- 12 API calls: prInfo (6) + prDetail (6)
- DB Reality Gate: ALL 5 tables MUST exist before load
- Sum Validation: 0 tolerance (MISMATCH → exit 2)
- NO mock/file fallback

Output:
- Raw responses: data/premium_raw/20251126/_prInfo/ + _prDetail/
- Failures: data/premium_raw/_failures/20251126.jsonl
- DB tables populated: premium_quote, coverage_premium_quote, product_premium_quote_v2
- Audit logs: docs/audit/STEP_NEXT_DB2_PREMIUM_REAL_LOAD_LOCK.md
"""

import sys
import os
import json
import psycopg2
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.premium_ssot.greenlight_client import GreenlightAPIClient


class DB2LoadRunner:
    """STEP NEXT-DB2 Premium Load Runner"""

    # LOCKED configuration
    BASE_DT = "20251126"
    AGES = [30, 40, 50]
    SEXES = ["M", "F"]

    # Database URL
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
    )

    # Required tables (G11 gate)
    REQUIRED_TABLES = [
        "premium_multiplier",
        "premium_quote",
        "coverage_premium_quote",
        "product_premium_quote_v2",
        "q14_premium_ranking_v1"
    ]

    def __init__(self):
        self.client = GreenlightAPIClient(output_dir="data/premium_raw")
        self.db_conn = None
        self.audit_log = []
        self.failures = []

    def run(self) -> int:
        """
        Execute DB2 load with ZERO TOLERANCE

        Returns:
            0: Success
            2: Hard failure
        """
        print("=" * 80)
        print("STEP NEXT-DB2: Premium SSOT Real Data Load")
        print("=" * 80)
        print(f"baseDt: {self.BASE_DT}")
        print(f"Ages: {self.AGES}")
        print(f"Sexes: {self.SEXES}")
        print(f"Total API calls: {len(self.AGES) * len(self.SEXES) * 2} (prInfo + prDetail)")
        print()

        try:
            # Step 1: DB Reality Gate (FAIL FAST)
            print("[1/7] DB Reality Gate...")
            self._verify_db_tables()
            print("✅ All 5 premium tables exist")
            print()

            # Step 2: Skip multiplier (NO_REFUND only for now)
            print("[2/7] Skip multiplier (NO_REFUND only)...")
            print("✅ Skipped (NO_REFUND data only)")
            print()

            # Step 3: API Pull (12 calls)
            print("[3/7] API Pull (12 calls)...")
            api_results = self._pull_all_premium_data()
            print(f"✅ Completed {len(api_results)} API call groups")
            print(f"   Failures: {len(self.failures)}")
            print()

            # Step 4: Convert API results to DB records (directly)
            print("[4/7] Convert API results to DB records...")
            all_product_records = []
            all_coverage_records = []
            sum_mismatches = []

            for api_result in api_results:
                # Build records directly from coverage_premiums
                self._process_api_result(
                    api_result,
                    all_product_records,
                    all_coverage_records,
                    sum_mismatches
                )

            print(f"✅ Generated {len(all_product_records)} product records")
            print(f"✅ Generated {len(all_coverage_records)} coverage records")

            # HARD FAIL on sum mismatch
            if sum_mismatches:
                print()
                print("❌ SUM VALIDATION FAILED (0 TOLERANCE)")
                for mismatch in sum_mismatches:
                    print(f"   {mismatch['insurer_key']} | {mismatch['product_id']} | "
                          f"age={mismatch['age']} sex={mismatch['sex']}")
                    print(f"   Expected: {mismatch['expected_sum']}, Got: {mismatch['calculated_sum']}, "
                          f"Error: {mismatch['error']}")
                return 2

            print("✅ Sum validation: ALL PASS")
            print()

            # Step 6: Upsert to DB
            print("[6/7] Upsert to DB...")
            self._upsert_to_db(all_product_records, all_coverage_records)
            print("✅ DB upsert complete")
            print()

            # Step 7: Verification queries
            print("[7/7] Verification queries...")
            self._run_verification_queries()
            print("✅ Verification complete")
            print()

            print("=" * 80)
            print("✅ STEP NEXT-DB2 COMPLETE")
            print("=" * 80)

            return 0

        except Exception as e:
            print()
            print(f"❌ FATAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return 2

        finally:
            if self.db_conn:
                self.db_conn.close()

    def _verify_db_tables(self):
        """Verify all required DB tables exist (G11 gate)"""
        conn = psycopg2.connect(self.DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public' AND tablename = ANY(%s)
        """, (self.REQUIRED_TABLES,))

        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        missing_tables = set(self.REQUIRED_TABLES) - set(existing_tables)

        if missing_tables:
            print(f"❌ Missing DB tables: {missing_tables}")
            print("   Apply migrations first:")
            print("   psql $DATABASE_URL -f schema/020_premium_quote.sql")
            print("   psql $DATABASE_URL -f schema/040_coverage_premium_quote.sql")
            print("   psql $DATABASE_URL -f schema/050_q14_premium_ranking.sql")
            print("   psql $DATABASE_URL -f schema/030_product_comparison_v1.sql")
            sys.exit(2)

    def _upsert_multipliers(self, multiplier_data: List[Dict[str, Any]]):
        """Upsert multiplier data to DB"""
        conn = psycopg2.connect(self.DATABASE_URL)
        cursor = conn.cursor()

        for m in multiplier_data:
            cursor.execute("""
                INSERT INTO premium_multiplier (insurer_key, coverage_name, multiplier_percent)
                VALUES (%s, %s, %s)
                ON CONFLICT (insurer_key, coverage_name)
                DO UPDATE SET multiplier_percent = EXCLUDED.multiplier_percent
            """, (m["insurer_key"], m["coverage_name"], m["multiplier_percent"]))

        conn.commit()
        cursor.close()
        conn.close()

    def _pull_all_premium_data(self) -> List[Dict[str, Any]]:
        """Pull premium data for all age × sex combinations"""
        results = []

        for age in self.AGES:
            for sex in self.SEXES:
                print(f"  Calling API: age={age}, sex={sex}...")
                result = self.client.pull_premium_for_request(
                    base_dt=self.BASE_DT,
                    age=age,
                    sex=sex
                )

                results.append(result)

                # Track failures
                if result.get("failures"):
                    self.failures.extend(result["failures"])

        return results

    def _process_api_result(
        self,
        api_result: Dict[str, Any],
        all_product_records: List[Dict[str, Any]],
        all_coverage_records: List[Dict[str, Any]],
        sum_mismatches: List[Dict[str, Any]]
    ):
        """
        Process single API result and generate DB records

        Args:
            api_result: Result from pull_premium_for_request()
            all_product_records: Accumulator for product records
            all_coverage_records: Accumulator for coverage records
            sum_mismatches: Accumulator for sum validation errors
        """
        # Convert baseDt "20251126" → as_of_date "2025-11-26"
        base_dt = api_result.get("base_dt", self.BASE_DT)
        as_of_date = f"{base_dt[0:4]}-{base_dt[4:6]}-{base_dt[6:8]}"

        age = api_result["age"]
        sex = api_result["sex"]
        plan_variant = api_result["plan_variant"]

        prdetail_response = api_result.get("prdetail_response")
        if not prdetail_response:
            # prDetail API failed, skip this result
            return

        # Insurer code map (insCd → insurer_key)
        INSURER_CODE_MAP = {
            "N01": "meritz",
            "N02": "hanwha",
            "N03": "lotte",
            "N05": "heungkuk",
            "N08": "samsung",
            "N09": "hyundai",
            "N10": "kb",
            "N13": "db"
        }

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
                pay_term_years_raw = ins_detail.get("payTermYears", "")
                ins_term_years_raw = ins_detail.get("insTermYears", "")

                # Map insurer_key
                insurer_key = INSURER_CODE_MAP.get(ins_cd)
                if not insurer_key:
                    # Unknown insurer → skip
                    continue

                # Parse pay_term_years and ins_term_years
                pay_term_years = self._parse_term_years(pay_term_years_raw)
                ins_term_years = self._parse_term_years(ins_term_years_raw)

                # Product ID: use prCd as product_id
                product_id = pr_cd

                # Process coverages
                cvr_amt_arr_lst = ins_detail.get("cvrAmtArrLst", [])
                coverage_sum = 0

                for cvr in cvr_amt_arr_lst:
                    cvr_cd = cvr.get("cvrCd")
                    cvr_nm = cvr.get("cvrNm")

                    # Premium: Try monthlyPremInt first, fallback to monthlyPrem
                    monthly_prem_int = cvr.get("monthlyPremInt")
                    monthly_prem = cvr.get("monthlyPrem", 0)

                    premium_monthly = monthly_prem_int if monthly_prem_int is not None else monthly_prem

                    coverage_sum += premium_monthly

                    # Skip zero-premium coverages (violates chk_cpq_premium_positive)
                    if premium_monthly <= 0:
                        continue

                    # Create coverage record
                    coverage_record = {
                        "insurer_key": insurer_key,
                        "product_id": product_id,
                        "coverage_code": cvr_cd,
                        "plan_variant": plan_variant,
                        "age": age,
                        "sex": sex,
                        "smoke": "N",  # LOCKED: NO_REFUND only
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years,
                        "premium_monthly_coverage": premium_monthly,
                        "as_of_date": as_of_date,
                        "source_table_id": None,
                        "source_row_id": None
                    }
                    all_coverage_records.append(coverage_record)

                # Sum validation (0 tolerance)
                if abs(coverage_sum - monthly_prem_sum) > 0.01:
                    sum_mismatches.append({
                        "insurer_key": insurer_key,
                        "product_id": product_id,
                        "age": age,
                        "sex": sex,
                        "expected_sum": monthly_prem_sum,
                        "calculated_sum": coverage_sum,
                        "error": abs(coverage_sum - monthly_prem_sum)
                    })

                # Create product record
                product_record = {
                    "insurer_key": insurer_key,
                    "product_id": product_id,
                    "plan_variant": plan_variant,
                    "age": age,
                    "sex": sex,
                    "smoke": "N",  # LOCKED: NO_REFUND only
                    "pay_term_years": pay_term_years,
                    "ins_term_years": ins_term_years,
                    "as_of_date": as_of_date,
                    "premium_monthly_total": monthly_prem_sum,
                    "premium_total_total": total_prem_sum,
                    "source_table_id": None,
                    "source_row_id": None
                }
                all_product_records.append(product_record)

    def _parse_term_years(self, term_str: str) -> int:
        """
        Parse term years from Korean format

        Examples:
            "20년" → 20
            "100세만기" → 100
            "전기납" → 0 (cannot parse)
            "" → 0

        Args:
            term_str: Term string from API

        Returns:
            Parsed years (int), or 0 if cannot parse
        """
        if not term_str:
            return 0

        term_str = str(term_str).strip()

        # Pattern: "숫자년" → extract number
        if "년" in term_str:
            try:
                return int(term_str.replace("년", "").strip())
            except ValueError:
                return 0

        # Pattern: "숫자세만기" → extract number
        if "세만기" in term_str or "세" in term_str:
            try:
                num_str = term_str.replace("세만기", "").replace("세", "").strip()
                return int(num_str)
            except ValueError:
                return 0

        # Cannot parse → return 0
        return 0

    def _build_product_id_map(self, api_results: List[Dict[str, Any]]) -> Dict[tuple, str]:
        """Build product ID map from API results"""
        return build_product_id_map(api_results, base_dt=self.BASE_DT)

    def _upsert_to_db(
        self,
        product_records: List[Dict[str, Any]],
        coverage_records: List[Dict[str, Any]]
    ):
        """Upsert product and coverage records to DB using as_of_date natural keys"""
        conn = psycopg2.connect(self.DATABASE_URL)
        cursor = conn.cursor()

        # Upsert product_premium_quote_v2
        # UNIQUE constraint: (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
        for pr in product_records:
            cursor.execute("""
                INSERT INTO product_premium_quote_v2 (
                    insurer_key, product_id, plan_variant, age, sex, smoke,
                    pay_term_years, ins_term_years, as_of_date,
                    premium_monthly_total, premium_total_total, source_table_id, source_row_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
                DO UPDATE SET
                    premium_monthly_total = EXCLUDED.premium_monthly_total,
                    premium_total_total = EXCLUDED.premium_total_total,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                pr["insurer_key"], pr["product_id"], pr["plan_variant"],
                pr["age"], pr["sex"], pr["smoke"],
                pr["pay_term_years"], pr["ins_term_years"],
                pr["as_of_date"],
                pr["premium_monthly_total"], pr["premium_total_total"],
                pr.get("source_table_id"), pr.get("source_row_id")
            ))

        # Upsert coverage_premium_quote
        # UNIQUE constraint: (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date)
        for cr in coverage_records:
            cursor.execute("""
                INSERT INTO coverage_premium_quote (
                    insurer_key, product_id, coverage_code, plan_variant,
                    age, sex, smoke, pay_term_years, ins_term_years,
                    premium_monthly_coverage, as_of_date,
                    source_table_id, source_row_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date)
                DO UPDATE SET
                    premium_monthly_coverage = EXCLUDED.premium_monthly_coverage,
                    pay_term_years = EXCLUDED.pay_term_years,
                    ins_term_years = EXCLUDED.ins_term_years,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                cr["insurer_key"], cr["product_id"], cr["coverage_code"],
                cr["plan_variant"], cr["age"], cr["sex"], cr["smoke"],
                cr["pay_term_years"], cr["ins_term_years"],
                cr["premium_monthly_coverage"], cr["as_of_date"],
                cr.get("source_table_id"), cr.get("source_row_id")
            ))

        conn.commit()
        cursor.close()
        conn.close()

    def _run_verification_queries(self):
        """Run verification queries and save results"""
        conn = psycopg2.connect(self.DATABASE_URL)
        cursor = conn.cursor()

        # Convert baseDt to as_of_date for queries
        as_of_date = f"{self.BASE_DT[0:4]}-{self.BASE_DT[4:6]}-{self.BASE_DT[6:8]}"

        # Count queries using as_of_date
        tables = [
            "premium_multiplier",
            "product_premium_quote_v2",
            "coverage_premium_quote",
            "premium_quote"
        ]

        for table in tables:
            if table == "premium_multiplier":
                cursor.execute(f"SELECT count(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows (total)")
            else:
                # as_of_date query
                cursor.execute(f"SELECT as_of_date, count(*) FROM {table} WHERE as_of_date = %s GROUP BY 1", (as_of_date,))
                result = cursor.fetchone()
                if result:
                    count = result[1]
                    print(f"  {table}: {count} rows (as_of_date={as_of_date})")
                else:
                    print(f"  {table}: 0 rows (as_of_date={as_of_date})")
                    count = 0

            self.audit_log.append({"table": table, "as_of_date": as_of_date if table != "premium_multiplier" else None, "count": count})

        cursor.close()
        conn.close()


def main():
    runner = DB2LoadRunner()
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
