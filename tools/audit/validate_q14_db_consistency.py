#!/usr/bin/env python3
"""
STEP NEXT-Q14-DB-CLEAN: Q14 DB Consistency Validator

Purpose:
  Validate q14_premium_ranking_v1 table 100% matches product_premium_quote_v2 SSOT.
  Detect duplicates, orphan rows, and verify expected row counts.

Validation Checks:
  V1: No duplicate keys (age, sex, plan_variant, rank, as_of_date)
  V2: All Q14 rows exist in product_premium_quote_v2 (LEFT JOIN null=0)
  V3: Expected row count (18 rows = 3 ages × 2 sexes × 1 variant × 3 ranks)

Exit Codes:
  0: All checks passed
  1: Validation failure detected
  2: Critical error (DB connection, missing table, etc.)
"""

import argparse
import os
import sys
import psycopg2
from typing import List, Dict, Any

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)

DEFAULT_AS_OF_DATE = "2025-11-26"
EXPECTED_ROWS = 18  # 3 ages × 2 sexes × 1 variant × 3 ranks


class Q14ConsistencyValidator:
    """Validates Q14 premium ranking DB consistency."""

    def __init__(self, as_of_date: str):
        self.as_of_date = as_of_date
        self.db_conn = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def connect(self):
        """Connect to database."""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print(f"[INFO] Connected to database: {DATABASE_URL.split('@')[1]}")
        except Exception as e:
            print(f"[ERROR] DB connection failed: {e}")
            sys.exit(2)

    def v1_check_duplicates(self) -> bool:
        """
        V1: Check for duplicate keys (age, sex, plan_variant, rank, as_of_date).

        Returns: True if no duplicates, False if duplicates found
        """
        print("\n" + "="*80)
        print("V1: Duplicate Key Check")
        print("="*80)

        cursor = self.db_conn.cursor()

        query = """
            SELECT age, sex, plan_variant, rank, as_of_date, COUNT(*) as cnt
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            GROUP BY age, sex, plan_variant, rank, as_of_date
            HAVING COUNT(*) > 1
        """

        cursor.execute(query, (self.as_of_date,))
        duplicates = cursor.fetchall()
        cursor.close()

        if duplicates:
            self.errors.append(f"V1 FAIL: {len(duplicates)} duplicate key(s) found")
            print(f"❌ FAIL: Found {len(duplicates)} duplicate keys:")
            for dup in duplicates:
                age, sex, plan_variant, rank, as_of_date, cnt = dup
                print(f"  - age={age}, sex={sex}, plan_variant={plan_variant}, rank={rank}: {cnt} rows")
            return False
        else:
            print("✅ PASS: No duplicate keys found")
            return True

    def v2_check_orphan_rows(self) -> bool:
        """
        V2: Check if all Q14 rows exist in product_premium_quote_v2.

        Orphan row = Q14 ranking references (insurer_key, product_id, age, sex, plan_variant)
        that doesn't exist in premium SSOT table.

        Returns: True if no orphans, False if orphans found
        """
        print("\n" + "="*80)
        print("V2: Orphan Row Check (LEFT JOIN product_premium_quote_v2)")
        print("="*80)

        cursor = self.db_conn.cursor()

        query = """
            SELECT q14.insurer_key, q14.product_id, q14.age, q14.sex, q14.plan_variant, q14.rank
            FROM q14_premium_ranking_v1 q14
            LEFT JOIN product_premium_quote_v2 pq
                ON q14.insurer_key = pq.insurer_key
                AND q14.product_id = pq.product_id
                AND q14.age = pq.age
                AND q14.sex = pq.sex
                AND q14.plan_variant = pq.plan_variant
                AND q14.as_of_date = pq.as_of_date
            WHERE q14.as_of_date = %s
              AND pq.insurer_key IS NULL
        """

        cursor.execute(query, (self.as_of_date,))
        orphans = cursor.fetchall()
        cursor.close()

        if orphans:
            self.errors.append(f"V2 FAIL: {len(orphans)} orphan row(s) found")
            print(f"❌ FAIL: Found {len(orphans)} orphan rows:")
            for orphan in orphans:
                insurer_key, product_id, age, sex, plan_variant, rank = orphan
                print(f"  - rank {rank}: {insurer_key}/{product_id} (age={age}, sex={sex}, {plan_variant})")
            return False
        else:
            print("✅ PASS: All Q14 rows exist in product_premium_quote_v2")
            return True

    def v3_check_row_count(self) -> bool:
        """
        V3: Check expected row count (18 rows = 3 ages × 2 sexes × 1 variant × 3 ranks).

        Returns: True if row count matches, False otherwise
        """
        print("\n" + "="*80)
        print("V3: Expected Row Count Check")
        print("="*80)

        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
        """, (self.as_of_date,))

        actual_count = cursor.fetchone()[0]
        cursor.close()

        print(f"Expected: {EXPECTED_ROWS} rows (3 ages × 2 sexes × 1 variant × 3 ranks)")
        print(f"Actual:   {actual_count} rows")

        if actual_count == EXPECTED_ROWS:
            print("✅ PASS: Row count matches expected")
            return True
        else:
            self.errors.append(f"V3 FAIL: Expected {EXPECTED_ROWS}, got {actual_count}")
            print(f"❌ FAIL: Row count mismatch")
            return False

    def print_db_summary(self):
        """Print current DB state summary."""
        print("\n" + "="*80)
        print("Q14 DB State Summary")
        print("="*80)

        cursor = self.db_conn.cursor()

        # Total rows
        cursor.execute("SELECT COUNT(*) FROM q14_premium_ranking_v1 WHERE as_of_date = %s", (self.as_of_date,))
        total_rows = cursor.fetchone()[0]
        print(f"Total rows (as_of_date={self.as_of_date}): {total_rows}")

        # Breakdown by age/sex
        cursor.execute("""
            SELECT age, sex, COUNT(*) as cnt
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            GROUP BY age, sex
            ORDER BY age, sex
        """, (self.as_of_date,))

        breakdown = cursor.fetchall()
        print("\nBreakdown by age/sex:")
        for age, sex, cnt in breakdown:
            print(f"  Age {age} | Sex {sex}: {cnt} rows")

        # Top 3 insurers per segment
        cursor.execute("""
            SELECT age, sex, rank, insurer_key, premium_monthly, premium_per_10m
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            ORDER BY age, sex, rank
        """, (self.as_of_date,))

        rankings = cursor.fetchall()
        cursor.close()

        print("\nRankings:")
        current_segment = None
        for age, sex, rank, insurer, premium, p_per_10m in rankings:
            segment = f"Age {age} | Sex {sex}"
            if segment != current_segment:
                print(f"\n  {segment}:")
                current_segment = segment
            print(f"    #{rank}: {insurer} (₩{premium:,}/월, {p_per_10m:.2f}원/1억)")

    def run_all_checks(self) -> bool:
        """
        Run all validation checks.

        Returns: True if all checks passed, False if any check failed
        """
        print("="*80)
        print("STEP NEXT-Q14-DB-CLEAN: Q14 DB Consistency Validation")
        print("="*80)
        print(f"Target as_of_date: {self.as_of_date}")
        print()

        # Connect to DB
        self.connect()

        # Print current state
        self.print_db_summary()

        # Run checks
        v1_pass = self.v1_check_duplicates()
        v2_pass = self.v2_check_orphan_rows()
        v3_pass = self.v3_check_row_count()

        # Print summary
        print("\n" + "="*80)
        print("Validation Summary")
        print("="*80)

        checks = [
            ("V1: No duplicate keys", v1_pass),
            ("V2: No orphan rows", v2_pass),
            ("V3: Expected row count (18)", v3_pass),
        ]

        all_passed = all(passed for _, passed in checks)

        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {check_name}")

        if all_passed:
            print("\n✅ All validation checks passed")
            print("Q14 DB is consistent with product_premium_quote_v2 SSOT")
        else:
            print("\n❌ Validation failed")
            print(f"Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")

        return all_passed

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-Q14-DB-CLEAN: Validate Q14 DB Consistency"
    )
    parser.add_argument(
        "--as-of-date",
        default=DEFAULT_AS_OF_DATE,
        help=f"Target as_of_date (default: {DEFAULT_AS_OF_DATE})"
    )

    args = parser.parse_args()

    validator = Q14ConsistencyValidator(as_of_date=args.as_of_date)

    try:
        all_passed = validator.run_all_checks()
        exit_code = 0 if all_passed else 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 2
    finally:
        validator.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
