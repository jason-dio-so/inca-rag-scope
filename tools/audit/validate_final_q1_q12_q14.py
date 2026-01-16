#!/usr/bin/env python3
"""
FINAL SMOKE GATE - Q1/Q12/Q14 Validation

Validates the complete Q1/Q12/Q14 data integrity for as_of_date=2025-11-26.

Exit Codes:
  0 - PASS (all checks passed)
  2 - FAIL (one or more checks failed)

Usage:
  export SSOT_DB_URL="postgresql://postgres:postgres@localhost:5433/inca_ssot"
  python3 tools/audit/validate_final_q1_q12_q14.py --as-of-date 2025-11-26
"""

import argparse
import os
import sys
import psycopg2
from typing import Dict, List, Tuple


class FinalSmokeGate:
    """Final validation gate for Q1/Q12/Q14 data integrity."""

    def __init__(self, as_of_date: str):
        self.as_of_date = as_of_date
        self.conn = None
        self.failed_checks = []

    def connect(self):
        """Connect to database using SSOT_DB_URL environment variable."""
        database_url = os.getenv("SSOT_DB_URL", "postgresql://postgres:postgres@localhost:5433/inca_ssot")

        if not database_url:
            print("❌ ERROR: SSOT_DB_URL environment variable not set")
            print("   Please set: export SSOT_DB_URL='postgresql://postgres:postgres@localhost:5433/inca_ssot'")
            sys.exit(2)

        try:
            self.conn = psycopg2.connect(database_url)
            print(f"✅ Connected to database")
        except Exception as e:
            print(f"❌ ERROR: Failed to connect to database: {e}")
            sys.exit(2)

    def log_db_metadata(self):
        """Log database metadata for audit trail."""
        print("\n" + "="*80)
        print("DATABASE METADATA")
        print("="*80)

        cursor = self.conn.cursor()

        # Database info
        cursor.execute("""
            SELECT current_database(), current_user, version()
        """)
        db_name, db_user, db_version = cursor.fetchone()
        print(f"Database: {db_name}")
        print(f"User: {db_user}")
        print(f"Version: {db_version[:50]}...")

        # Check required tables
        required_tables = [
            'product_premium_quote_v2',
            'coverage_premium_quote',
            'q14_premium_ranking_v1',
            'q14_premium_top4_v1'
        ]

        print(f"\nRequired Tables:")
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (table,))
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")

            if not exists:
                self.failed_checks.append(f"Missing table: {table}")

        cursor.close()

    def validate_q14(self):
        """Validate Q14 (Premium Top4) data integrity."""
        print("\n" + "="*80)
        print("Q14 VALIDATION: Premium Top4")
        print("="*80)

        cursor = self.conn.cursor()

        # Check 1: Row counts by variant
        print("\n[CHECK] Row counts by plan_variant")
        cursor.execute("""
            SELECT plan_variant, COUNT(*) as n
            FROM q14_premium_top4_v1
            WHERE as_of_date = %s
            GROUP BY plan_variant
            ORDER BY plan_variant
        """, (self.as_of_date,))

        expected = {'GENERAL': 24, 'NO_REFUND': 24}
        actual = {}

        for variant, count in cursor.fetchall():
            actual[variant] = count
            status = "✅" if count == expected.get(variant, 0) else "❌"
            print(f"  {status} {variant}: {count} rows (expected: {expected.get(variant, 0)})")

            if count != expected.get(variant, 0):
                self.failed_checks.append(f"Q14: {variant} has {count} rows, expected {expected.get(variant, 0)}")

        # Check 2: Segment breakdown (each segment should have exactly 4 rows)
        print("\n[CHECK] Segment breakdown (age × sex × variant)")
        cursor.execute("""
            SELECT age, sex, plan_variant, COUNT(*) as n
            FROM q14_premium_top4_v1
            WHERE as_of_date = %s
            GROUP BY age, sex, plan_variant
            HAVING COUNT(*) != 4
        """, (self.as_of_date,))

        bad_segments = cursor.fetchall()
        if bad_segments:
            print(f"  ❌ Found {len(bad_segments)} segments with incorrect row count:")
            for age, sex, variant, count in bad_segments:
                print(f"     - age={age}, sex={sex}, variant={variant}: {count} rows (expected 4)")
                self.failed_checks.append(f"Q14: Segment ({age},{sex},{variant}) has {count} rows, expected 4")
        else:
            print(f"  ✅ All segments have exactly 4 rows")

        # Check 3: Sorting verification (premium_monthly ASC, insurer_key ASC)
        print("\n[CHECK] Sorting order within segments")
        cursor.execute("""
            SELECT age, sex, plan_variant, COUNT(*) as violations
            FROM (
                SELECT
                    age, sex, plan_variant, rank,
                    premium_monthly,
                    LAG(premium_monthly) OVER (PARTITION BY age, sex, plan_variant ORDER BY rank) as prev_premium,
                    insurer_key,
                    LAG(insurer_key) OVER (PARTITION BY age, sex, plan_variant ORDER BY rank) as prev_insurer
                FROM q14_premium_top4_v1
                WHERE as_of_date = %s
            ) t
            WHERE
                (prev_premium IS NOT NULL AND premium_monthly < prev_premium)
                OR (prev_premium = premium_monthly AND prev_insurer IS NOT NULL AND insurer_key < prev_insurer)
            GROUP BY age, sex, plan_variant
        """, (self.as_of_date,))

        sort_violations = cursor.fetchall()
        if sort_violations:
            print(f"  ❌ Found {len(sort_violations)} segments with sorting violations:")
            for age, sex, variant, count in sort_violations:
                print(f"     - age={age}, sex={sex}, variant={variant}: {count} violations")
                self.failed_checks.append(f"Q14: Sorting violation in segment ({age},{sex},{variant})")
        else:
            print(f"  ✅ All segments sorted correctly")

        cursor.close()

    def validate_q1(self):
        """Validate Q1 (Cost-Efficiency) data integrity."""
        print("\n" + "="*80)
        print("Q1 VALIDATION: Cost-Efficiency Ranking")
        print("="*80)

        cursor = self.conn.cursor()

        # Check 1: Row counts by variant
        print("\n[CHECK] Row counts by plan_variant")
        cursor.execute("""
            SELECT plan_variant, COUNT(*) as n
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            GROUP BY plan_variant
            ORDER BY plan_variant
        """, (self.as_of_date,))

        expected = {'GENERAL': 18, 'NO_REFUND': 18}
        actual = {}

        for variant, count in cursor.fetchall():
            actual[variant] = count
            status = "✅" if count == expected.get(variant, 0) else "❌"
            print(f"  {status} {variant}: {count} rows (expected: {expected.get(variant, 0)})")

            if count != expected.get(variant, 0):
                self.failed_checks.append(f"Q1: {variant} has {count} rows, expected {expected.get(variant, 0)}")

        # Check 2: Formula integrity (premium_per_10m calculation)
        print("\n[CHECK] Formula integrity: premium_per_10m = premium_monthly / (cancer_amt / 10M)")
        cursor.execute("""
            SELECT COUNT(*) as mismatch_cnt
            FROM (
                SELECT r.*,
                       ROUND(r.premium_monthly / (r.cancer_amt / 10000000.0), 2) as recomputed
                FROM q14_premium_ranking_v1 r
                WHERE r.as_of_date = %s
            ) t
            WHERE ABS(t.premium_per_10m - t.recomputed) > 0.01
        """, (self.as_of_date,))

        mismatch_count = cursor.fetchone()[0]
        status = "✅" if mismatch_count == 0 else "❌"
        print(f"  {status} Formula mismatches: {mismatch_count} (expected: 0)")

        if mismatch_count > 0:
            self.failed_checks.append(f"Q1: {mismatch_count} rows with formula mismatch")

        # Check 3: Orphan check (all rankings must have matching product in product_premium_quote_v2)
        print("\n[CHECK] Orphan detection (rankings without matching product)")
        cursor.execute("""
            SELECT COUNT(*) as orphan_cnt
            FROM q14_premium_ranking_v1 r
            LEFT JOIN product_premium_quote_v2 p
                ON p.insurer_key = r.insurer_key
               AND p.product_id = r.product_id
               AND p.age = r.age
               AND p.sex = r.sex
               AND p.plan_variant = r.plan_variant
               AND p.as_of_date = r.as_of_date
            WHERE r.as_of_date = %s
              AND p.insurer_key IS NULL
        """, (self.as_of_date,))

        orphan_count = cursor.fetchone()[0]
        status = "✅" if orphan_count == 0 else "❌"
        print(f"  {status} Orphan rows: {orphan_count} (expected: 0)")

        if orphan_count > 0:
            self.failed_checks.append(f"Q1: {orphan_count} orphan rows (no matching product)")

        # Check 4: Segment breakdown (each segment should have exactly 3 rows)
        print("\n[CHECK] Segment breakdown (age × sex × variant)")
        cursor.execute("""
            SELECT age, sex, plan_variant, COUNT(*) as n
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            GROUP BY age, sex, plan_variant
            HAVING COUNT(*) != 3
        """, (self.as_of_date,))

        bad_segments = cursor.fetchall()
        if bad_segments:
            print(f"  ❌ Found {len(bad_segments)} segments with incorrect row count:")
            for age, sex, variant, count in bad_segments:
                print(f"     - age={age}, sex={sex}, variant={variant}: {count} rows (expected 3)")
                self.failed_checks.append(f"Q1: Segment ({age},{sex},{variant}) has {count} rows, expected 3")
        else:
            print(f"  ✅ All segments have exactly 3 rows")

        cursor.close()

    def validate_q12(self):
        """Validate Q12 (Samsung vs Meritz comparison) data availability."""
        print("\n" + "="*80)
        print("Q12 VALIDATION: Samsung vs Meritz Comparison")
        print("="*80)

        cursor = self.conn.cursor()

        # Check: Both insurers present for all segments
        print("\n[CHECK] Samsung and Meritz data availability")

        insurers = ['samsung', 'meritz']
        ages = [30, 40, 50]
        sexes = ['M', 'F']
        variants = ['NO_REFUND', 'GENERAL']

        missing_segments = []

        for insurer in insurers:
            for age in ages:
                for sex in sexes:
                    for variant in variants:
                        cursor.execute("""
                            SELECT COUNT(*) as n
                            FROM product_premium_quote_v2
                            WHERE as_of_date = %s
                              AND insurer_key = %s
                              AND age = %s
                              AND sex = %s
                              AND plan_variant = %s
                        """, (self.as_of_date, insurer, age, sex, variant))

                        count = cursor.fetchone()[0]

                        if count == 0:
                            missing_segments.append((insurer, age, sex, variant))

        if missing_segments:
            print(f"  ❌ Found {len(missing_segments)} missing segments:")
            for insurer, age, sex, variant in missing_segments[:5]:  # Show first 5
                print(f"     - {insurer}, age={age}, sex={sex}, variant={variant}")
                self.failed_checks.append(f"Q12: Missing data for {insurer} ({age},{sex},{variant})")
            if len(missing_segments) > 5:
                print(f"     ... and {len(missing_segments) - 5} more")
        else:
            print(f"  ✅ All segments present for both insurers")

        # Sample comparison (30M NO_REFUND)
        print("\n[CHECK] Sample comparison (age=30, sex=M, variant=NO_REFUND)")
        cursor.execute("""
            SELECT insurer_key, product_id, premium_monthly_total
            FROM product_premium_quote_v2
            WHERE as_of_date = %s
              AND insurer_key IN ('samsung', 'meritz')
              AND age = 30
              AND sex = 'M'
              AND plan_variant = 'NO_REFUND'
            ORDER BY insurer_key
        """, (self.as_of_date,))

        results = cursor.fetchall()
        if len(results) == 2:
            for insurer, product_id, premium in results:
                print(f"  ✅ {insurer}: product_id={product_id}, premium={premium:,}원")

            # Calculate difference
            samsung_premium = next((p for i, _, p in results if i == 'samsung'), None)
            meritz_premium = next((p for i, _, p in results if i == 'meritz'), None)

            if samsung_premium and meritz_premium:
                diff = abs(samsung_premium - meritz_premium)
                cheaper = 'meritz' if meritz_premium < samsung_premium else 'samsung'
                pct = (diff / max(samsung_premium, meritz_premium)) * 100
                print(f"  ✅ Cheaper: {cheaper}, Difference: {diff:,}원 ({pct:.2f}%)")
        else:
            print(f"  ❌ Expected 2 results, got {len(results)}")
            self.failed_checks.append(f"Q12: Sample comparison failed (expected 2 insurers, got {len(results)})")

        cursor.close()

    def print_summary(self):
        """Print final summary and return exit code."""
        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)

        if self.failed_checks:
            print(f"\n❌ FAIL: {len(self.failed_checks)} check(s) failed\n")
            for i, check in enumerate(self.failed_checks, 1):
                print(f"  {i}. {check}")
            print()
            return 2
        else:
            print("\n✅ FINAL LOCK PASS\n")
            print("All validation checks passed:")
            print("  ✅ Q14: 48 rows (24 NO_REFUND + 24 GENERAL)")
            print("  ✅ Q14: All segments have 4 rows")
            print("  ✅ Q14: Sorting verified")
            print("  ✅ Q1: 36 rows (18 NO_REFUND + 18 GENERAL)")
            print("  ✅ Q1: Formula integrity verified")
            print("  ✅ Q1: No orphan rows")
            print("  ✅ Q1: All segments have 3 rows")
            print("  ✅ Q12: Samsung and Meritz data available")
            print()
            return 0

    def run(self):
        """Execute all validation checks."""
        self.connect()
        self.log_db_metadata()
        self.validate_q14()
        self.validate_q1()
        self.validate_q12()
        exit_code = self.print_summary()

        if self.conn:
            self.conn.close()

        return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="FINAL SMOKE GATE - Q1/Q12/Q14 Validation"
    )
    parser.add_argument(
        '--as-of-date',
        default='2025-11-26',
        help='as_of_date to validate (default: 2025-11-26)'
    )

    args = parser.parse_args()

    print("="*80)
    print("FINAL SMOKE GATE - Q1/Q12/Q14 VALIDATION")
    print("="*80)
    print(f"as_of_date: {args.as_of_date}")
    print()

    gate = FinalSmokeGate(as_of_date=args.as_of_date)
    exit_code = gate.run()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
