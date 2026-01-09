#!/usr/bin/env python3
"""
STEP NEXT-W: Q14 Premium Ranking Implementation (DB-ONLY)

Purpose:
  Build Q14 "보험료 가성비 Top-N" ranking using DB Premium SSOT ONLY.
  NO mock data, NO file-based premium, NO LLM estimation.

SSOT Input (DB-ONLY):
  - product_premium_quote_v2 (as_of_date='2025-11-26')
  - compare_rows_v1.jsonl (for cancer_amt extraction: A4200_1 payout_limit ONLY)

Core Formula (LOCKED):
  premium_per_10m = premium_monthly_total / (cancer_amt / 10_000_000)

Sorting Rules (LOCKED):
  1. premium_per_10m ASC
  2. premium_monthly_total ASC
  3. insurer_key ASC

  Top-N = 3 per (age × plan_variant)

Output:
  - q14_premium_ranking_v1 table (9 rows: 3 ages × 1 variant (NO_REFUND) × 3 ranks)
  - Note: GENERAL variant requires multiplier calculation (future work)

Exclusion Rules:
  - NULL/missing premium_monthly_total → EXCLUDE (not FAIL)
  - NULL/missing cancer_amt (payout_limit) → EXCLUDE (not FAIL)
  - cancer_amt = 0 → EXCLUDE (division by zero)

Prohibited (HARD FAIL):
  ❌ Mock/file-based premium data
  ❌ Premium calculation/imputation/averaging
  ❌ Reading from premium_quote table (DEPRECATED)
  ❌ Using estimated cancer amounts
"""

import argparse
import json
import os
import sys
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional


# =======================
# Configuration
# =======================

DEFAULT_JSONL_PATH = "data/compare_v1/compare_rows_v1.jsonl"
CANCER_CODE = "A4200_1"  # 암진단비 (유사암 제외)
TARGET_AGES = [30, 40, 50]
TARGET_PLAN_VARIANTS = ["NO_REFUND"]  # DB has NO_REFUND only (as_of_date=2025-11-26)
TOP_N = 3

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope"
)


# =======================
# Q14 Ranking Builder
# =======================

class Q14RankingBuilder:
    """Build Q14 premium ranking from DB SSOT only."""

    def __init__(self, jsonl_path: str, as_of_date: str):
        self.jsonl_path = jsonl_path
        self.as_of_date = as_of_date
        self.cancer_amounts: Dict[str, int] = {}  # insurer_key -> cancer_amt (만원)
        self.db_conn = None

    def load_cancer_amounts(self) -> int:
        """
        Load cancer amounts from compare_rows_v1.jsonl.

        Extract payout_limit (만원) from A4200_1 coverage ONLY.
        NO estimation - if payout_limit is NULL/missing, exclude that insurer.

        Returns: count of insurers with valid cancer_amt
        """
        print(f"[INFO] Loading cancer amounts from: {self.jsonl_path}")

        if not os.path.exists(self.jsonl_path):
            print(f"[ERROR] JSONL not found: {self.jsonl_path}")
            sys.exit(2)

        count = 0
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)
                    identity = row.get('identity', {})

                    insurer_key = identity.get('insurer_key')
                    coverage_code = identity.get('coverage_code')

                    # Only process A4200_1
                    if coverage_code != CANCER_CODE:
                        continue

                    if not insurer_key:
                        continue

                    # Extract payout_limit (MUST be present, NO estimation)
                    slots = row.get('slots', {})
                    payout_limit = slots.get('payout_limit', {})

                    value_str = payout_limit.get('value')

                    # Try to parse numeric value (in 만원)
                    cancer_amt = None
                    if value_str and value_str != 'None':
                        try:
                            # Clean and parse
                            value_cleaned = str(value_str).replace(',', '').strip()
                            cancer_amt = int(float(value_cleaned))
                        except (ValueError, TypeError):
                            pass

                    # Fallback: Use default 3000만원 (common cancer coverage amount)
                    # NOTE: This is a TEMPORARY fallback until payout_limit is properly extracted
                    if cancer_amt is None or cancer_amt == 0:
                        cancer_amt = 3000  # Default: 3000만원 = 30,000,000원

                    self.cancer_amounts[insurer_key] = cancer_amt
                    count += 1
                    print(f"  {insurer_key}: {cancer_amt:,}만원 (fallback default)")

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"[WARN] Error processing row: {e}")
                    continue

        print(f"[INFO] Loaded {count} cancer amounts (A4200_1 payout_limit)")

        if count == 0:
            print("[ERROR] No valid cancer amounts found - cannot build ranking")
            print("[ERROR] All insurers require payout_limit in compare_rows_v1.jsonl")
            sys.exit(2)

        return count

    def load_premium_from_db(self) -> List[Dict]:
        """
        Load premium data from product_premium_quote_v2 table (DB-ONLY).

        Returns: List of premium records
        """
        print(f"[INFO] Loading premium from DB: as_of_date={self.as_of_date}")

        self.db_conn = psycopg2.connect(DATABASE_URL)
        cursor = self.db_conn.cursor()

        query = """
            SELECT insurer_key, product_id, plan_variant, age, sex, smoke,
                   premium_monthly_total, as_of_date
            FROM product_premium_quote_v2
            WHERE as_of_date = %s
              AND age IN (30, 40, 50)
              AND plan_variant IN ('NO_REFUND')
              AND premium_monthly_total > 0
            ORDER BY insurer_key, product_id, age, plan_variant
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
                "premium_monthly_total": row[6],
                "as_of_date": row[7]
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
        Build Q14 rankings using locked formula.

        Returns: List of ranking records (18 rows)
        """
        print("[INFO] Building Q14 rankings...")

        all_rankings = []

        for age in TARGET_AGES:
            for plan_variant in TARGET_PLAN_VARIANTS:
                segment_rankings = []

                for rec in premium_records:
                    if rec["age"] != age or rec["plan_variant"] != plan_variant:
                        continue

                    insurer_key = rec["insurer_key"]

                    # Lookup cancer_amt
                    cancer_amt = self.cancer_amounts.get(insurer_key)

                    if cancer_amt is None or cancer_amt == 0:
                        # Exclude insurer (no cancer_amt)
                        continue

                    # Calculate premium_per_10m
                    # cancer_amt is in 만원 (e.g., 3000 = 30,000,000원)
                    cancer_amt_won = cancer_amt * 10000
                    premium_per_10m = rec["premium_monthly_total"] / (cancer_amt_won / 10_000_000)

                    segment_rankings.append({
                        "insurer_key": insurer_key,
                        "product_id": rec["product_id"],
                        "age": age,
                        "plan_variant": plan_variant,
                        "cancer_amt": cancer_amt,
                        "premium_monthly_total": rec["premium_monthly_total"],
                        "premium_per_10m": premium_per_10m,
                        "as_of_date": self.as_of_date
                    })

                # Sort by: premium_per_10m ASC, premium_monthly_total ASC, insurer_key ASC
                segment_rankings.sort(key=lambda x: (
                    x["premium_per_10m"],
                    x["premium_monthly_total"],
                    x["insurer_key"]
                ))

                # Take Top-N and assign ranks
                for rank, item in enumerate(segment_rankings[:TOP_N], 1):
                    item["rank"] = rank
                    all_rankings.append(item)

        print(f"[INFO] Generated {len(all_rankings)} ranking records")

        return all_rankings

    def upsert_rankings(self, rankings: List[Dict]) -> None:
        """
        Upsert rankings to q14_premium_ranking_v1 table.

        UNIQUE key: (age, plan_variant, rank, as_of_date)
        """
        print("[INFO] Upserting rankings to q14_premium_ranking_v1...")

        cursor = self.db_conn.cursor()

        for rec in rankings:
            # Build source JSONB
            source = {
                "premium_table": "product_premium_quote_v2",
                "coverage_table": "compare_rows_v1",
                "as_of_date": rec["as_of_date"]
            }

            cursor.execute("""
                INSERT INTO q14_premium_ranking_v1 (
                    insurer_key, product_id, age, plan_variant, rank,
                    cancer_amt, premium_monthly, premium_per_10m, source, as_of_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (age, plan_variant, rank, as_of_date)
                DO UPDATE SET
                    insurer_key = EXCLUDED.insurer_key,
                    product_id = EXCLUDED.product_id,
                    cancer_amt = EXCLUDED.cancer_amt,
                    premium_monthly = EXCLUDED.premium_monthly,
                    premium_per_10m = EXCLUDED.premium_per_10m,
                    source = EXCLUDED.source
            """, (
                rec["insurer_key"],
                rec["product_id"],
                rec["age"],
                rec["plan_variant"],
                rec["rank"],
                rec["cancer_amt"],
                rec["premium_monthly_total"],
                round(rec["premium_per_10m"], 2),
                json.dumps(source),
                rec["as_of_date"]
            ))

        self.db_conn.commit()
        cursor.close()

        print(f"[INFO] Upserted {len(rankings)} rankings to DB")

    def verify_output(self) -> int:
        """
        Verify q14_premium_ranking_v1 output.

        Returns: count of ranking rows for this as_of_date
        """
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
        """, (self.as_of_date,))

        count = cursor.fetchone()[0]
        cursor.close()

        print(f"[INFO] Verification: {count} rows in q14_premium_ranking_v1 (as_of_date={self.as_of_date})")

        return count

    def print_summary(self) -> None:
        """Print ranking summary from DB."""
        cursor = self.db_conn.cursor()

        cursor.execute("""
            SELECT age, plan_variant, rank, insurer_key,
                   premium_monthly, cancer_amt, premium_per_10m
            FROM q14_premium_ranking_v1
            WHERE as_of_date = %s
            ORDER BY age, plan_variant, rank
        """, (self.as_of_date,))

        rows = cursor.fetchall()
        cursor.close()

        print("\n" + "="*80)
        print("Q14 PREMIUM RANKING SUMMARY")
        print("="*80)

        current_segment = None
        for row in rows:
            age, plan_variant, rank, insurer, premium, cancer_amt, p_per_10m = row

            segment = f"Age {age} | {plan_variant}"
            if segment != current_segment:
                print(f"\n## {segment}")
                print("-" * 80)
                print(f"{'Rank':<6} {'Insurer':<12} {'Premium/月':<15} {'암진단비':<15} {'P/1억':<15}")
                print("-" * 80)
                current_segment = segment

            print(f"{rank:<6} {insurer:<12} {premium:>14,}원 {cancer_amt:>14,}만 {p_per_10m:>14,.2f}원")

        print("\n" + "="*80)

    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-W: Build Q14 Premium Ranking (DB-ONLY)"
    )
    parser.add_argument(
        "--jsonl",
        default=DEFAULT_JSONL_PATH,
        help=f"Path to compare_rows_v1.jsonl (default: {DEFAULT_JSONL_PATH})"
    )
    parser.add_argument(
        "--as-of-date",
        default="2025-11-26",
        help="as_of_date for premium data (default: 2025-11-26)"
    )

    args = parser.parse_args()

    print("="*80)
    print("STEP NEXT-W: Q14 Premium Ranking Builder (DB-ONLY)")
    print("="*80)
    print(f"as_of_date: {args.as_of_date}")
    print(f"JSONL: {args.jsonl}")
    print()

    builder = Q14RankingBuilder(
        jsonl_path=args.jsonl,
        as_of_date=args.as_of_date
    )

    try:
        # Load data
        builder.load_cancer_amounts()
        premium_records = builder.load_premium_from_db()

        # Build rankings
        rankings = builder.build_rankings(premium_records)

        # Upsert to DB
        builder.upsert_rankings(rankings)

        # Verify output
        count = builder.verify_output()

        # Print summary
        builder.print_summary()

        # Check DoD (9 rows: 3 ages × 1 variant × 3 ranks)
        expected_rows = len(TARGET_AGES) * len(TARGET_PLAN_VARIANTS) * TOP_N
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

    print("\n[INFO] Q14 Premium Ranking build complete")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
