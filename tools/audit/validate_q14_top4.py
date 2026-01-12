#!/usr/bin/env python3
"""
STEP NEXT-FINAL: Q14 Premium Top4 Validator

Purpose:
  Validate q14_premium_top4_v1 table matches SSOT + sorting rules.

Validation Checks:
  V1: Segment row count ≤ 4 (no overflow)
  V2: No orphan rows (LEFT JOIN product_premium_quote_v2)
  V3: Sorting order correct (premium_monthly ASC, insurer_key ASC)

Exit Codes:
  0: All checks passed
  1: Validation failure detected
  2: Critical error
"""

import argparse
import os
import sys
import psycopg2
from typing import List

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)

DEFAULT_AS_OF_DATE = "2025-11-26"


class Q14Top4Validator:
    """Validates Q14 Premium Top4 DB consistency."""

    def __init__(self, as_of_date: str):
        self.as_of_date = as_of_date
        self.db_conn = None
        self.errors: List[str] = []

    def connect(self):
        """Connect to database."""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print(f"[INFO] Connected to database")
        except Exception as e:
            print(f"[ERROR] DB connection failed: {e}")
            sys.exit(2)

    def v1_check_row_counts(self) -> bool:
        """
        V1: Check segment row counts ≤ 4.

        Returns: True if all segments have ≤ 4 rows, False otherwise
        """
        print("\n" + "="*80)
        print("V1: Segment Row Count Check (≤ 4 per segment)")
        print("="*80)

        cursor = self.db_conn.cursor()

        query = """
            SELECT age, sex, plan_variant, COUNT(*) as cnt
            FROM q14_premium_top4_v1
            WHERE as_of_date = %s
            GROUP BY age, sex, plan_variant
            HAVING COUNT(*) > 4
        """

        cursor.execute(query, (self.as_of_date,))
        overflows = cursor.fetchall()
        cursor.close()

        if overflows:
            self.errors.append(f"V1 FAIL: {len(overflows)} segment(s) have > 4 rows")
            print(f"❌ FAIL: Found {len(overflows)} segments with overflow:")
            for overflow in overflows:
                age, sex, plan_variant, cnt = overflow
                print(f"  - age={age}, sex={sex}, plan_variant={plan_variant}: {cnt} rows (expected ≤ 4)")
            return False
        else:
            print("✅ PASS: All segments have ≤ 4 rows")
            return True

    def v2_check_orphan_rows(self) -> bool:
        """
        V2: Check if all Q14 rows exist in product_premium_quote_v2.

        Returns: True if no orphans, False if orphans found
        """
        print("\n" + "="*80)
        print("V2: Orphan Row Check (LEFT JOIN product_premium_quote_v2)")
        print("="*80)

        cursor = self.db_conn.cursor()

        query = """
            SELECT q14.insurer_key, q14.product_id, q14.age, q14.sex, q14.plan_variant, q14.rank
            FROM q14_premium_top4_v1 q14
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

    def v3_check_sorting(self) -> bool:
        """
        V3: Check sorting order (premium_monthly ASC, insurer_key ASC).

        Samples 3 segments and verifies ranking matches recomputed sort.

        Returns: True if sorting correct, False otherwise
        """
        print("\n" + "="*80)
        print("V3: Sorting Order Check (premium_monthly ASC, insurer_key ASC)")
        print("="*80)

        cursor = self.db_conn.cursor()

        # Sample 3 segments
        test_segments = [
            (30, "F", "NO_REFUND"),
            (40, "M", "NO_REFUND"),
            (50, "F", "NO_REFUND"),
        ]

        all_pass = True

        for age, sex, plan_variant in test_segments:
            # Get Q14 stored rankings
            cursor.execute("""
                SELECT rank, insurer_key, product_id, premium_monthly
                FROM q14_premium_top4_v1
                WHERE as_of_date = %s AND age = %s AND sex = %s AND plan_variant = %s
                ORDER BY rank
            """, (self.as_of_date, age, sex, plan_variant))

            stored_rankings = cursor.fetchall()

            # Get recomputed rankings from SSOT
            cursor.execute("""
                SELECT insurer_key, product_id, premium_monthly_total
                FROM product_premium_quote_v2
                WHERE as_of_date = %s AND age = %s AND sex = %s AND plan_variant = %s
                ORDER BY premium_monthly_total ASC, insurer_key ASC
                LIMIT 4
            """, (self.as_of_date, age, sex, plan_variant))

            recomputed_rankings = cursor.fetchall()

            # Compare
            match = True
            for i, (stored, recomputed) in enumerate(zip(stored_rankings, recomputed_rankings), 1):
                stored_rank, stored_insurer, stored_product, stored_premium = stored
                recomputed_insurer, recomputed_product, recomputed_premium = recomputed

                if (stored_insurer != recomputed_insurer or
                    stored_product != recomputed_product or
                    abs(float(stored_premium) - float(recomputed_premium)) > 0.01):
                    match = False
                    self.errors.append(
                        f"V3 FAIL: Segment (age={age}, sex={sex}) rank {i} mismatch"
                    )
                    print(f"❌ FAIL: Segment (age={age}, sex={sex}, {plan_variant}) rank {i} mismatch:")
                    print(f"  Stored:     {stored_insurer}/{stored_product} (₩{stored_premium:,})")
                    print(f"  Recomputed: {recomputed_insurer}/{recomputed_product} (₩{recomputed_premium:,})")

            if match:
                print(f"✅ PASS: Segment (age={age}, sex={sex}, {plan_variant}) - 4 ranks correct")
            else:
                all_pass = False

        cursor.close()
        return all_pass

    def print_db_summary(self):
        """Print current DB state summary."""
        print("\n" + "="*80)
        print("Q14 Premium Top4 DB State Summary")
        print("="*80)

        cursor = self.db_conn.cursor()

        # Total rows
        cursor.execute("SELECT COUNT(*) FROM q14_premium_top4_v1 WHERE as_of_date = %s", (self.as_of_date,))
        total_rows = cursor.fetchone()[0]
        print(f"Total rows (as_of_date={self.as_of_date}): {total_rows}")

        # Breakdown by age/sex
        cursor.execute("""
            SELECT age, sex, COUNT(*) as cnt
            FROM q14_premium_top4_v1
            WHERE as_of_date = %s
            GROUP BY age, sex
            ORDER BY age, sex
        """, (self.as_of_date,))

        breakdown = cursor.fetchall()
        print("\nBreakdown by age/sex:")
        for age, sex, cnt in breakdown:
            print(f"  Age {age} | Sex {sex}: {cnt} rows")

        cursor.close()

    def run_all_checks(self) -> bool:
        """
        Run all validation checks.

        Returns: True if all checks passed, False if any check failed
        """
        print("="*80)
        print("STEP NEXT-FINAL: Q14 Premium Top4 Validation")
        print("="*80)
        print(f"Target as_of_date: {self.as_of_date}")
        print()

        # Connect to DB
        self.connect()

        # Print current state
        self.print_db_summary()

        # Run checks
        v1_pass = self.v1_check_row_counts()
        v2_pass = self.v2_check_orphan_rows()
        v3_pass = self.v3_check_sorting()

        # Print summary
        print("\n" + "="*80)
        print("Validation Summary")
        print("="*80)

        checks = [
            ("V1: Segment row counts ≤ 4", v1_pass),
            ("V2: No orphan rows", v2_pass),
            ("V3: Sorting order correct (3 segments)", v3_pass),
        ]

        all_passed = all(passed for _, passed in checks)

        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {check_name}")

        if all_passed:
            print("\n✅ All validation checks passed")
            print("Q14 Premium Top4 is consistent with SSOT")
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
        description="STEP NEXT-FINAL: Validate Q14 Premium Top4"
    )
    parser.add_argument(
        "--as-of-date",
        default=DEFAULT_AS_OF_DATE,
        help=f"Target as_of_date (default: {DEFAULT_AS_OF_DATE})"
    )

    args = parser.parse_args()

    validator = Q14Top4Validator(as_of_date=args.as_of_date)

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
