#!/usr/bin/env python3
"""
inca-rag-scope: Premium Multiplier Excel Loader
STEP NEXT-GENERAL-SSOT: Load multiplier data from Excel into premium_multiplier table

Purpose:
- Read "4. 일반보험요율예시.xlsx"
- Normalize insurer keys and coverage names
- Insert/update premium_multiplier with as_of_date snapshot

ZERO TOLERANCE:
- NO estimation or default values
- NO fallback for missing multipliers
- Skip NaN values (do not insert)
- Exact coverage name from Excel (trim only, no mapping)
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Insurer name normalization map (Excel header → insurer_key)
INSURER_MAP = {
    "한화손해보험": "hanwha",
    "삼성화재": "samsung",
    "롯데손해보험": "lotte",
    "현대해상화재": "hyundai",
    "메리츠화재": "meritz",
    "DB손해보험": "db",
    "KB손해보험": "kb",
    "흥국화재": "heungkuk",
}


def normalize_coverage_name(raw_name: str) -> str:
    """Normalize coverage name (trim only, NO mapping)"""
    if pd.isna(raw_name):
        return None
    return str(raw_name).strip()


def load_excel(file_path: str) -> pd.DataFrame:
    """Load Excel file and return DataFrame"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    df = pd.read_excel(file_path, sheet_name="sheet1")
    print(f"[INFO] Loaded Excel: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def extract_multipliers(df: pd.DataFrame, as_of_date: str) -> list:
    """
    Extract (insurer_key, coverage_name, multiplier_percent, as_of_date) tuples

    Returns:
        List of tuples ready for DB insertion
    """
    # First row contains insurer names (headers)
    # First column contains coverage names
    # Data starts from row 1, col 1

    headers = df.iloc[0, 1:].tolist()  # Skip first column (담보명)
    coverage_col = df.iloc[1:, 0].tolist()  # Coverage names from row 1 onwards

    records = []
    skipped = 0

    for i, coverage_name_raw in enumerate(coverage_col):
        coverage_name = normalize_coverage_name(coverage_name_raw)
        if not coverage_name:
            skipped += 1
            continue

        for j, insurer_name_raw in enumerate(headers):
            insurer_name = str(insurer_name_raw).strip()
            insurer_key = INSURER_MAP.get(insurer_name)

            if not insurer_key:
                print(f"[WARN] Unknown insurer: '{insurer_name}' - SKIP")
                continue

            # Get multiplier value (row i+1, col j+1 in original df)
            multiplier_value = df.iloc[i + 1, j + 1]

            # Skip NaN values (ZERO TOLERANCE: no estimation)
            if pd.isna(multiplier_value):
                continue

            try:
                multiplier_percent = float(multiplier_value)
                if multiplier_percent <= 0:
                    print(f"[WARN] Invalid multiplier ({multiplier_percent}) for {insurer_key}/{coverage_name} - SKIP")
                    continue

                records.append((
                    insurer_key,
                    coverage_name,
                    multiplier_percent,
                    "4. 일반보험요율예시.xlsx",
                    i + 1,  # source_row_id (1-indexed)
                    as_of_date
                ))
            except (ValueError, TypeError) as e:
                print(f"[WARN] Cannot convert multiplier for {insurer_key}/{coverage_name}: {multiplier_value} - SKIP")
                continue

    print(f"[INFO] Extracted {len(records)} valid multiplier records")
    print(f"[INFO] Skipped {skipped} rows with null coverage names")
    return records


def insert_multipliers(db_url: str, records: list):
    """
    Insert multipliers into database using ON CONFLICT DO UPDATE

    Args:
        db_url: PostgreSQL connection string
        records: List of (insurer_key, coverage_name, multiplier_percent,
                         source_file, source_row_id, as_of_date) tuples
    """
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # Use ON CONFLICT to handle duplicates
        insert_query = """
        INSERT INTO premium_multiplier
            (insurer_key, coverage_name, multiplier_percent, source_file, source_row_id, as_of_date)
        VALUES %s
        ON CONFLICT (insurer_key, coverage_name, as_of_date)
        DO UPDATE SET
            multiplier_percent = EXCLUDED.multiplier_percent,
            source_file = EXCLUDED.source_file,
            source_row_id = EXCLUDED.source_row_id,
            created_at = CURRENT_TIMESTAMP
        """

        execute_values(cur, insert_query, records)
        conn.commit()

        print(f"[SUCCESS] Inserted/updated {len(records)} multiplier records")

        # Verify by counting
        cur.execute("""
            SELECT as_of_date, COUNT(*) as cnt
            FROM premium_multiplier
            WHERE as_of_date = %s
            GROUP BY as_of_date
        """, (records[0][5],))  # as_of_date is 6th element

        result = cur.fetchone()
        if result:
            print(f"[VERIFY] as_of_date={result[0]}, total_rows={result[1]}")

        # Show insurer breakdown
        cur.execute("""
            SELECT insurer_key, COUNT(*) as cnt
            FROM premium_multiplier
            WHERE as_of_date = %s
            GROUP BY insurer_key
            ORDER BY insurer_key
        """, (records[0][5],))

        print("[VERIFY] Insurer breakdown:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} rows")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to insert: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Load premium multiplier from Excel to DB")
    parser.add_argument(
        "--asOfDate",
        required=True,
        help="Snapshot date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--excelPath",
        default="data/sources/insurers/4. 일반보험요율예시.xlsx",
        help="Path to Excel file"
    )
    parser.add_argument(
        "--dbUrl",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL (default: $DATABASE_URL)"
    )

    args = parser.parse_args()

    if not args.dbUrl:
        print("[ERROR] DATABASE_URL not set")
        sys.exit(1)

    # Validate as_of_date format
    try:
        datetime.strptime(args.asOfDate, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] Invalid as_of_date format: {args.asOfDate} (expected: YYYY-MM-DD)")
        sys.exit(1)

    print(f"[START] Loading multipliers from Excel")
    print(f"  Excel: {args.excelPath}")
    print(f"  as_of_date: {args.asOfDate}")
    print(f"  DB: {args.dbUrl.split('@')[-1]}")  # Hide credentials
    print()

    # Load Excel
    df = load_excel(args.excelPath)

    # Extract multipliers
    records = extract_multipliers(df, args.asOfDate)

    if not records:
        print("[ERROR] No valid records extracted")
        sys.exit(1)

    # Insert to DB
    insert_multipliers(args.dbUrl, records)

    print()
    print("[COMPLETE] Multiplier load finished successfully")


if __name__ == "__main__":
    main()
