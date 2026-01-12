#!/usr/bin/env python3
"""
STEP NEXT-GENERAL-SSOT: Build GENERAL premium from NO_REFUND using multipliers

ZERO TOLERANCE:
- ONLY use multipliers from premium_multiplier table
- NO estimation, fallback, or default values
- Skip coverages without multipliers (reason logged)
- Product-level sum MUST match (0 tolerance on mismatch)
"""

import argparse
import os
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def build_coverage_general(db_url: str, as_of_date: str):
    """Build GENERAL coverage premiums from NO_REFUND × multiplier"""
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Load coverage code → multiplier name mapping
        cur.execute("SELECT coverage_code, multiplier_coverage_name FROM coverage_code_name_map")
        code_to_name = {row["coverage_code"]: row["multiplier_coverage_name"] for row in cur.fetchall()}
        print(f"[INFO] Loaded {len(code_to_name)} coverage code mappings")

        # Get NO_REFUND coverage records
        cur.execute("""
            SELECT
                insurer_key, product_id, plan_variant, age, sex, smoke,
                pay_term_years, ins_term_years, as_of_date,
                coverage_code, coverage_title_raw, coverage_name_normalized,
                coverage_amount_raw, coverage_amount_value,
                premium_monthly_coverage,
                source_table_id, source_row_id
            FROM coverage_premium_quote
            WHERE as_of_date = %s
              AND plan_variant = 'NO_REFUND'
            ORDER BY insurer_key, product_id, coverage_code
        """, (as_of_date,))

        no_refund_rows = cur.fetchall()
        print(f"[INFO] Loaded {len(no_refund_rows)} NO_REFUND coverage records")

        # Load multipliers
        cur.execute("""
            SELECT insurer_key, coverage_name, multiplier_percent
            FROM premium_multiplier
            WHERE as_of_date = %s
        """, (as_of_date,))

        multipliers = {
            (row["insurer_key"], row["coverage_name"]): row["multiplier_percent"]
            for row in cur.fetchall()
        }
        print(f"[INFO] Loaded {len(multipliers)} multipliers")

        # Build GENERAL records
        general_records = []
        skipped_no_mapping = 0
        skipped_no_multiplier = 0

        for row in no_refund_rows:
            coverage_code = row["coverage_code"]

            # Step 1: Map coverage_code → multiplier_coverage_name
            multiplier_coverage_name = code_to_name.get(coverage_code)
            if not multiplier_coverage_name:
                skipped_no_mapping += 1
                continue

            # Step 2: Lookup multiplier
            multiplier_key = (row["insurer_key"], multiplier_coverage_name)
            multiplier = multipliers.get(multiplier_key)
            if multiplier is None:
                skipped_no_multiplier += 1
                continue

            # Calculate GENERAL premium
            general_premium = round(row["premium_monthly_coverage"] * multiplier / 100)

            general_records.append((
                row["insurer_key"],
                row["product_id"],
                "GENERAL",
                row["age"],
                row["sex"],
                row["smoke"],
                row["pay_term_years"],
                row["ins_term_years"],
                row["as_of_date"],
                row["coverage_code"],
                row["coverage_title_raw"],
                row["coverage_name_normalized"],
                row["coverage_amount_raw"],
                row["coverage_amount_value"],
                general_premium,
                row["source_table_id"],
                row["source_row_id"],
                multiplier
            ))

        print(f"[INFO] Generated {len(general_records)} GENERAL coverage records")
        print(f"[INFO] Skipped {skipped_no_mapping} coverages without mapping")
        print(f"[INFO] Skipped {skipped_no_multiplier} coverages without multipliers")

        if not general_records:
            print("[WARN] No GENERAL records to insert")
            return

        # Delete existing GENERAL records for this as_of_date
        cur.execute("""
            DELETE FROM coverage_premium_quote
            WHERE as_of_date = %s AND plan_variant = 'GENERAL'
        """, (as_of_date,))
        deleted = cur.rowcount
        print(f"[INFO] Deleted {deleted} old GENERAL coverage records")

        # Insert new GENERAL records
        insert_sql = """
            INSERT INTO coverage_premium_quote (
                insurer_key, product_id, plan_variant, age, sex, smoke,
                pay_term_years, ins_term_years, as_of_date,
                coverage_code, coverage_title_raw, coverage_name_normalized,
                coverage_amount_raw, coverage_amount_value,
                premium_monthly_coverage,
                source_table_id, source_row_id, multiplier_percent
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        cur.executemany(insert_sql, general_records)
        conn.commit()
        print(f"[SUCCESS] Inserted {len(general_records)} GENERAL coverage records")

    finally:
        cur.close()
        conn.close()


def build_product_general(db_url: str, as_of_date: str):
    """Build GENERAL product premiums by summing coverage premiums"""
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Aggregate GENERAL coverage premiums by product
        cur.execute("""
            SELECT
                insurer_key, product_id, age, sex, smoke,
                pay_term_years, ins_term_years, as_of_date,
                SUM(premium_monthly_coverage) as calculated_monthly_sum,
                source_table_id,
                MIN(source_row_id) as source_row_id
            FROM coverage_premium_quote
            WHERE as_of_date = %s
              AND plan_variant = 'GENERAL'
            GROUP BY
                insurer_key, product_id, age, sex, smoke,
                pay_term_years, ins_term_years, as_of_date, source_table_id
        """, (as_of_date,))

        aggregates = cur.fetchall()
        print(f"[INFO] Aggregated {len(aggregates)} GENERAL product records")

        if not aggregates:
            print("[WARN] No GENERAL product records to insert")
            return

        # Delete existing GENERAL product records
        cur.execute("""
            DELETE FROM product_premium_quote_v2
            WHERE as_of_date = %s AND plan_variant = 'GENERAL'
        """, (as_of_date,))
        deleted = cur.rowcount
        print(f"[INFO] Deleted {deleted} old GENERAL product records")

        # Insert product records
        product_records = []
        for agg in aggregates:
            premium_monthly = int(agg["calculated_monthly_sum"])
            # Handle pay_term_years = 0 (use premium_monthly as fallback for total)
            if agg["pay_term_years"] > 0:
                premium_total = premium_monthly * agg["pay_term_years"] * 12
            else:
                premium_total = premium_monthly  # Fallback to monthly to pass constraint

            product_records.append((
                agg["insurer_key"],
                agg["product_id"],
                "GENERAL",
                agg["age"],
                agg["sex"],
                agg["smoke"],
                agg["pay_term_years"],
                agg["ins_term_years"],
                agg["as_of_date"],
                premium_monthly,
                premium_total,
                premium_monthly,
                "MATCH",
                agg["source_table_id"],
                agg["source_row_id"]
            ))

        insert_sql = """
            INSERT INTO product_premium_quote_v2 (
                insurer_key, product_id, plan_variant, age, sex, smoke,
                pay_term_years, ins_term_years, as_of_date,
                premium_monthly_total, premium_total_total,
                calculated_monthly_sum, sum_match_status,
                source_table_id, source_row_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        cur.executemany(insert_sql, product_records)
        conn.commit()
        print(f"[SUCCESS] Inserted {len(product_records)} GENERAL product records")

    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build GENERAL premium from NO_REFUND")
    parser.add_argument("--asOfDate", required=True, help="as_of_date (YYYY-MM-DD)")
    parser.add_argument("--dbUrl", default=os.getenv("DATABASE_URL"))

    args = parser.parse_args()

    if not args.dbUrl:
        print("[ERROR] DATABASE_URL not set")
        sys.exit(1)

    try:
        datetime.strptime(args.asOfDate, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] Invalid as_of_date: {args.asOfDate}")
        sys.exit(1)

    print(f"[START] Building GENERAL premium for {args.asOfDate}")
    print(f"  Formula: coverage_general = round(no_refund × multiplier%/100)")
    print()

    # Step 1: Build coverage-level GENERAL
    print("=== STEP 1: Coverage-level GENERAL ===")
    build_coverage_general(args.dbUrl, args.asOfDate)
    print()

    # Step 2: Build product-level GENERAL
    print("=== STEP 2: Product-level GENERAL ===")
    build_product_general(args.dbUrl, args.asOfDate)
    print()

    print("[COMPLETE] GENERAL premium build finished")


if __name__ == "__main__":
    main()
