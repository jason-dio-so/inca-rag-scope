#!/usr/bin/env python3
"""
STEP NEXT-FINAL: Q14 Premium Top4 Builder (DB-ONLY)

Purpose:
  Build Q14 "보험료 Top4" ranking using DB Premium SSOT ONLY.
  NO calculation columns (premium_per_10m), NO mock data.

SSOT Input:
  - product_premium_quote_v2 (as_of_date='2025-11-26')

Sorting Rules (LOCKED):
  ORDER BY premium_monthly_total ASC, insurer_key ASC
  LIMIT 4 per segment (age × sex × plan_variant)

Output:
  - q14_premium_top4_v1 table (24 rows: 3 ages × 2 sexes × 1 variant × 4 ranks)

Prohibited (HARD FAIL):
  ❌ premium_per_10m calculation
  ❌ GENERAL variant estimation (환급형 환산 금지)
  ❌ Fallback/mock data
"""

import argparse
import json
import os
import sys
import psycopg2
from typing import Dict, List

# =======================
# Configuration
# =======================

TARGET_AGES = [30, 40, 50]
TARGET_SEXES = ["M", "F"]
TARGET_PLAN_VARIANTS = ["NO_REFUND"]  # NO GENERAL until SSOT ready
TOP_N = 4

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)


class Q14Top4Builder:
    """Build Q14 premium Top4 ranking from DB SSOT only."""

    def __init__(self, as_of_date: str):
        self.as_of_date = as_of_date
        self.db_conn = None

    def connect(self):
        """Connect to database."""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            print(f"[INFO] Connected to database")
        except Exception as e:
            print(f"[ERROR] DB connection failed: {e}")
            sys.exit(2)

    def load_premium_from_db(self) -> List[Dict]:
        """
        Load premium data from product_premium_quote_v2 table (DB-ONLY).

        Returns: List of premium records
        """
        print(f"[INFO] Loading premium from DB: as_of_date={self.as_of_date}")

        cursor = self.db_conn.cursor()

        query = """
            SELECT insurer_key, product_id, plan_variant, age, sex, smoke,
                   pay_term_years, ins_term_years,
                   premium_monthly_total, as_of_date
            FROM product_premium_quote_v2
            WHERE as_of_date = %s
              AND age IN (30, 40, 50)
              AND plan_variant IN ('NO_REFUND')
              AND premium_monthly_total > 0
            ORDER BY insurer_key, product_id, age, sex, plan_variant
        """

        cursor.execute(query, (self.as_of_date,))
        rows = cursor.fetchall()

        records = []
        for row in rows:
            records.append({
                "insurer_key": row[0],
                "product_id": row[1],
                "plan_variant": row[2],
                "age": row[3],
                "sex": row[4],
                "smoke": row[5],
                "pay_term_years": row[6],
                "ins_term_years": row[7],
                "premium_monthly_total": row[8],
                "as_of_date": row[9]
            })

        cursor.close()

        print(f"[INFO] Loaded {len(records)} premium records from DB")

        if len(records) == 0:
            print("[ERROR] No premium data found in product_premium_quote_v2")
            print(f"[ERROR] Check as_of_date={self.as_of_date}")
            sys.exit(2)

        return records

    def build_rankings(self, premium_records: List[Dict]) -> List[Dict]:
        """
        Build Q14 Top4 rankings (pure premium sorting, NO calculation).

        Sorting: premium_monthly_total ASC, insurer_key ASC
        Top: 4 per segment

        Returns: List of ranking records (24 rows = 3 ages × 2 sexes × 1 variant × 4 ranks)
        """
        print("[INFO] Building Q14 Premium Top4 rankings...")

        all_rankings = []

        for age in TARGET_AGES:
            for sex in TARGET_SEXES:
                for plan_variant in TARGET_PLAN_VARIANTS:
                    segment_rankings = []

                    for rec in premium_records:
                        if rec["age"] != age or rec["sex"] != sex or rec["plan_variant"] != plan_variant:
                            continue

                        # Calculate total premium (monthly * term)
                        # Note: pay_term_years=0 means full-life, use ins_term_years
                        pay_term = rec["pay_term_years"] if rec["pay_term_years"] > 0 else rec["ins_term_years"]
                        premium_total = rec["premium_monthly_total"] * 12 * pay_term

                        segment_rankings.append({
                            "insurer_key": rec["insurer_key"],
                            "product_id": rec["product_id"],
                            "age": age,
                            "sex": sex,
                            "plan_variant": plan_variant,
                            "premium_monthly": rec["premium_monthly_total"],
                            "premium_total": premium_total,
                            "as_of_date": self.as_of_date
                        })

                    # Sort by: premium_monthly ASC, insurer_key ASC (LOCKED)
                    segment_rankings.sort(key=lambda x: (
                        x["premium_monthly"],
                        x["insurer_key"]
                    ))

                    # Take Top-4 and assign ranks
                    for rank, item in enumerate(segment_rankings[:TOP_N], 1):
                        item["rank"] = rank
                        all_rankings.append(item)

        print(f"[INFO] Generated {len(all_rankings)} ranking records")

        return all_rankings

    def upsert_rankings(self, rankings: List[Dict]) -> None:
        """
        DELETE+INSERT pattern (snapshot regeneration).

        Policy:
        1. DELETE all rows for target as_of_date
        2. INSERT new rankings (Top4 per age×sex×variant)

        UNIQUE key: (as_of_date, age, sex, plan_variant, rank)
        """
        print("[INFO] Regenerating Q14 Premium Top4 (DELETE+INSERT)...")

        cursor = self.db_conn.cursor()

        # Step 1: DELETE all rows for this as_of_date
        cursor.execute("""
            DELETE FROM q14_premium_top4_v1
            WHERE as_of_date = %s
        """, (self.as_of_date,))
        deleted_count = cursor.rowcount
        print(f"[INFO] Deleted {deleted_count} existing rows for as_of_date={self.as_of_date}")

        # Step 2: INSERT new rankings
        for rec in rankings:
            # Build source JSONB
            source = {
                "table": "product_premium_quote_v2",
                "as_of_date": rec["as_of_date"]
            }

            cursor.execute("""
                INSERT INTO q14_premium_top4_v1 (
                    as_of_date, age, sex, plan_variant, rank,
                    insurer_key, product_id, premium_monthly, premium_total, source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                rec["as_of_date"],
                rec["age"],
                rec["sex"],
                rec["plan_variant"],
                rec["rank"],
                rec["insurer_key"],
                rec["product_id"],
                rec["premium_monthly"],
                rec["premium_total"],
                json.dumps(source)
            ))

        self.db_conn.commit()
        cursor.close()

        print(f"[INFO] Inserted {len(rankings)} new rankings to DB")

    def verify_output(self) -> int:
        """
        Verify q14_premium_top4_v1 output.

        Returns: count of ranking rows for this as_of_date
        """
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM q14_premium_top4_v1
            WHERE as_of_date = %s
        """, (self.as_of_date,))

        count = cursor.fetchone()[0]
        cursor.close()

        print(f"[INFO] Verification: {count} rows in q14_premium_top4_v1 (as_of_date={self.as_of_date})")

        return count

    def print_summary(self) -> None:
        """Print ranking summary from DB."""
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT age, sex, plan_variant, rank, insurer_key, product_id,
                   premium_monthly, premium_total
            FROM q14_premium_top4_v1
            WHERE as_of_date = %s
            ORDER BY age, sex, plan_variant, rank
        """, (self.as_of_date,))

        rows = cursor.fetchall()
        cursor.close()

        print("\n" + "="*80)
        print("Q14 PREMIUM TOP4 SUMMARY")
        print("="*80)

        current_segment = None
        for row in rows:
            age, sex, plan_variant, rank, insurer, product_id, premium_monthly, premium_total = row

            segment = f"Age {age} | Sex {sex} | {plan_variant}"
            if segment != current_segment:
                print(f"\n## {segment}")
                print("-" * 80)
                print(f"{'Rank':<6} {'Insurer':<12} {'Product':<15} {'월보험료':<15} {'총납입':<15}")
                print("-" * 80)
                current_segment = segment

            print(f"{rank:<6} {insurer:<12} {product_id:<15} {premium_monthly:>14,}원 {premium_total:>14,.0f}원")

        print("\n" + "="*80)

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-FINAL: Build Q14 Premium Top4 (DB-ONLY)"
    )
    parser.add_argument(
        "--as-of-date",
        default="2025-11-26",
        help="as_of_date for premium data (default: 2025-11-26)"
    )

    args = parser.parse_args()

    print("="*80)
    print("STEP NEXT-FINAL: Q14 Premium Top4 Builder (DB-ONLY)")
    print("="*80)
    print(f"as_of_date: {args.as_of_date}")
    print()

    builder = Q14Top4Builder(as_of_date=args.as_of_date)

    try:
        # Connect to DB
        builder.connect()

        # Load premium data
        premium_records = builder.load_premium_from_db()

        # Build rankings
        rankings = builder.build_rankings(premium_records)

        # Upsert to DB
        builder.upsert_rankings(rankings)

        # Verify output
        count = builder.verify_output()

        # Print summary
        builder.print_summary()

        # Check DoD (24 rows: 3 ages × 2 sexes × 1 variant × 4 ranks)
        expected_rows = len(TARGET_AGES) * len(TARGET_SEXES) * len(TARGET_PLAN_VARIANTS) * TOP_N
        if count == expected_rows:
            print(f"\n✅ DoD PASS: {expected_rows} ranking rows generated")
            exit_code = 0
        else:
            print(f"\n❌ DoD FAIL: Expected {expected_rows} rows, got {count}")
            exit_code = 2

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 2

    finally:
        builder.close()

    print("\n[INFO] Q14 Premium Top4 build complete")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
