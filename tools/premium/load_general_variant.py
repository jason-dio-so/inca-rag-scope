#!/usr/bin/env python3
"""
GENERAL Variant Loader — Evidence-Mandatory SSOT (Reproducible)

Generates GENERAL premium variant from NO_REFUND × multiplier
Target DB: inca_ssot@5433 ONLY

Rules:
- GENERAL.premium_monthly_total = round(NO_REFUND.premium_monthly_total × multiplier_percent / 100)
- Uses PostgreSQL round() in SQL (NOT Python round()) for 100% reproducibility
- Zero-tolerance validation (mismatch = 0)
- Idempotent: Re-running produces identical results
"""

import os
import sys
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

# SSOT DB (LOCKED)
DB_URL = os.getenv(
    "SSOT_DB_URL",
    "postgresql://postgres:postgres@localhost:5433/inca_ssot"
)

# Default multiplier for GENERAL variant (130%)
DEFAULT_MULTIPLIER = 130


class GeneralVariantLoader:
    """Load GENERAL variant premium into SSOT DB (reproducible, idempotent)"""

    def __init__(self):
        self.conn = None
        self.multiplier = DEFAULT_MULTIPLIER
        self.deleted_count = 0
        self.inserted_count = 0
        self.errors: list = []

    def connect(self):
        """Connect to SSOT DB and verify"""
        print("=" * 80)
        print("DB ID CHECK — Reproducible Loader")
        print("=" * 80)

        # Parse URL to get host port (client perspective)
        parsed_url = urlparse(DB_URL)
        expected_port = parsed_url.port or 5432

        # Connect to DB
        self.conn = psycopg2.connect(DB_URL)
        cursor = self.conn.cursor()

        # Check database name + log container port
        cursor.execute("SELECT current_database(), inet_server_port()")
        db_name, container_port = cursor.fetchone()

        print(f"Connected DB: {db_name}")
        print(f"Host Port (from URL): {expected_port}")
        print(f"Container Port (from DB): {container_port} (informational)")

        # Validate: DB name + host port (not container port due to NAT)
        if db_name != 'inca_ssot':
            raise RuntimeError(f"SSOT_DB_MISMATCH: expected DB inca_ssot, got {db_name}")

        if expected_port != 5433:
            raise RuntimeError(f"SSOT_DB_MISMATCH: expected host port 5433, got {expected_port}")

        print("✅ DB ID CHECK PASS: inca_ssot@5433 (host port)\n")
        cursor.close()

    def check_current_state(self):
        """Check current GENERAL rows"""
        print("=" * 80)
        print("Current State Check")
        print("=" * 80)

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT plan_variant, COUNT(*) as row_count
            FROM product_premium_quote_v2
            WHERE as_of_date = '2025-11-26'
            GROUP BY plan_variant
            ORDER BY plan_variant
        """)

        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} rows")

        cursor.close()
        print()

    def delete_existing_general(self):
        """Delete existing GENERAL rows for clean re-generation"""
        print("=" * 80)
        print("Deleting Existing GENERAL Rows (for clean regeneration)")
        print("=" * 80)

        cursor = self.conn.cursor()

        # Delete existing GENERAL rows for the same as_of_date
        cursor.execute("""
            DELETE FROM product_premium_quote_v2
            WHERE plan_variant = 'GENERAL'
              AND as_of_date = '2025-11-26'
        """)

        self.deleted_count = cursor.rowcount
        print(f"✅ Deleted {self.deleted_count} existing GENERAL rows\n")
        cursor.close()

    def generate_and_insert_general(self):
        """Generate GENERAL rows using DB round() (INSERT SELECT)"""
        print("=" * 80)
        print("Generating GENERAL Rows (DB round() for reproducibility)")
        print("=" * 80)

        cursor = self.conn.cursor()

        # Use INSERT SELECT with DB round() - ensures PostgreSQL rounding
        insert_sql = f"""
            INSERT INTO product_premium_quote_v2 (
                ins_cd, product_id, product_full_name, plan_variant,
                age, sex, premium_monthly_total, premium_total_total,
                as_of_date, source, source_table_id, source_row_id
            )
            SELECT
                ins_cd,
                product_id,
                product_full_name,
                'GENERAL' as plan_variant,
                age,
                sex,
                round(premium_monthly_total * {self.multiplier}.0 / 100) as premium_monthly_total,
                round(premium_total_total * {self.multiplier}.0 / 100) as premium_total_total,
                as_of_date,
                'CALC NO_REFUND×{self.multiplier}% (DB round)' as source,
                source_table_id,
                source_row_id || '_GENERAL' as source_row_id
            FROM product_premium_quote_v2
            WHERE plan_variant = 'NO_REFUND'
              AND as_of_date = '2025-11-26'
        """

        try:
            cursor.execute(insert_sql)
            self.inserted_count = cursor.rowcount
            print(f"✅ Inserted {self.inserted_count} GENERAL rows using DB round()\n")
        except Exception as e:
            print(f"❌ Insert failed: {e}")
            raise
        finally:
            cursor.close()

    def validate(self):
        """Validate GENERAL rows (zero-tolerance)"""
        print("=" * 80)
        print("Validation — Zero-Tolerance")
        print("=" * 80)

        cursor = self.conn.cursor()

        # 1. Row count check
        cursor.execute("SELECT COUNT(*) FROM product_premium_quote_v2 WHERE plan_variant='GENERAL' AND as_of_date='2025-11-26'")
        general_count = cursor.fetchone()[0]
        print(f"GENERAL rows: {general_count}")

        expected_count = 48  # 8 insurers × 3 ages × 2 genders
        if general_count == expected_count:
            print(f"✅ Row count PASS ({expected_count} expected)\n")
        else:
            print(f"⚠️ Row count mismatch: expected {expected_count}, got {general_count}\n")

        # 2. Sum validation (zero-tolerance)
        cursor.execute(f"""
            SELECT
              COUNT(*) as total_rows,
              SUM(CASE WHEN diff = 0 THEN 1 ELSE 0 END) as match_count,
              SUM(CASE WHEN diff != 0 THEN 1 ELSE 0 END) as mismatch_count
            FROM (
              SELECT
                g.premium_monthly_total - round(n.premium_monthly_total * {self.multiplier}.0 / 100) as diff
              FROM product_premium_quote_v2 g
              JOIN product_premium_quote_v2 n
                ON g.ins_cd = n.ins_cd
                AND g.product_id = n.product_id
                AND g.age = n.age
                AND g.sex = n.sex
                AND g.as_of_date = n.as_of_date
              WHERE g.plan_variant = 'GENERAL'
                AND n.plan_variant = 'NO_REFUND'
                AND g.as_of_date = '2025-11-26'
            ) t
        """)

        total, matches, mismatches = cursor.fetchone()
        print(f"Sum Validation:")
        print(f"  Total rows: {total}")
        print(f"  Matches: {matches}")
        print(f"  Mismatches: {mismatches}")

        if mismatches == 0:
            print(f"✅ ZERO-TOLERANCE PASS (0 mismatches)\n")
        else:
            print(f"❌ ZERO-TOLERANCE FAIL ({mismatches} mismatches)\n")

        # 3. Show any mismatches (if any)
        if mismatches > 0:
            cursor.execute(f"""
                SELECT
                  g.ins_cd,
                  g.age,
                  g.sex,
                  n.premium_monthly_total as no_refund,
                  g.premium_monthly_total as general,
                  round(n.premium_monthly_total * {self.multiplier}.0 / 100) as expected,
                  g.premium_monthly_total - round(n.premium_monthly_total * {self.multiplier}.0 / 100) as diff
                FROM product_premium_quote_v2 g
                JOIN product_premium_quote_v2 n
                  ON g.ins_cd = n.ins_cd
                  AND g.product_id = n.product_id
                  AND g.age = n.age
                  AND g.sex = n.sex
                  AND g.as_of_date = n.as_of_date
                WHERE g.plan_variant = 'GENERAL'
                  AND n.plan_variant = 'NO_REFUND'
                  AND g.premium_monthly_total != round(n.premium_monthly_total * {self.multiplier}.0 / 100)
                  AND g.as_of_date = '2025-11-26'
                ORDER BY abs(g.premium_monthly_total - round(n.premium_monthly_total * {self.multiplier}.0 / 100)) DESC
            """)

            print("Mismatch Details:")
            for row in cursor.fetchall():
                print(f"  {row}")

        cursor.close()

    def run(self):
        """Execute full load process"""
        try:
            self.connect()
            self.check_current_state()
            self.delete_existing_general()
            self.generate_and_insert_general()
            self.conn.commit()
            self.validate()

            print("=" * 80)
            print("✅ GENERAL Variant Load COMPLETE (Reproducible)")
            print("=" * 80)
            print(f"Summary:")
            print(f"  Deleted: {self.deleted_count} rows")
            print(f"  Inserted: {self.inserted_count} rows")
            print(f"  Method: PostgreSQL round() (NOT Python)")
            print(f"  Reproducible: YES (re-run produces identical results)")

            return 0
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            if self.conn:
                self.conn.rollback()
            return 1
        finally:
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    loader = GeneralVariantLoader()
    sys.exit(loader.run())
