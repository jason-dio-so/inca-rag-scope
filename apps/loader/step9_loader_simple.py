#!/usr/bin/env python3
"""
STEP NEXT-DB-2C: STEP 9 Loader (SIMPLIFIED VERSION - facts only)
================================================================

⚠️  DEPRECATED: This version contains extraction logic violations.
    Use apps/loader/step9_loader.py instead.

Simplified implementation focusing on core functionality.
"""

import sys
import warnings

warnings.warn(
    "step9_loader_simple.py is DEPRECATED due to lineage violations. "
    "Use step9_loader.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import argparse
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import psycopg2
import psycopg2.extras
import openpyxl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class SimpleLoader:
    def __init__(self, db_url: str, project_root: Path):
        self.db_url = db_url
        self.project_root = project_root
        self.conn = None
        self.cur = None

    def connect(self):
        logger.info("Connecting to database...")
        self.conn = psycopg2.connect(self.db_url)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        logger.info("Connected")

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Closed")

    def truncate_facts(self):
        logger.info("Truncating fact tables...")
        for table in ['amount_fact', 'evidence_ref', 'coverage_instance', 'coverage_canonical']:
            self.cur.execute(f"TRUNCATE TABLE {table} CASCADE")
        self.conn.commit()
        logger.info("Truncated")

    def load_coverage_canonical(self):
        """Load coverage_canonical from Excel - the ONLY source of truth"""
        logger.info("Loading coverage_canonical from Excel...")

        # STEP PIPELINE-V2-BLOCK-STEP2B-01: Use correct SSOT path
        excel_path = self.project_root / 'data/sources/insurers/담보명mapping자료.xlsx'
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = wb.active

        # Build coverage_code -> canonical_name mapping
        coverage_map = {}
        for idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if idx == 0:  # Skip header
                continue
            if not row or len(row) < 4:
                continue

            # Columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)
            coverage_code = row[2]  # cre_cvr_cd
            canonical_name = row[3]  # 신정원코드명

            if coverage_code and canonical_name:
                coverage_map[coverage_code] = canonical_name

        wb.close()

        logger.info(f"Found {len(coverage_map)} unique coverage codes")

        # Insert unique coverage_codes
        inserted = 0
        for code, name in coverage_map.items():
            self.cur.execute(
                """
                INSERT INTO coverage_canonical
                (coverage_code, coverage_name_canonical, coverage_category, payment_event, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (code, name, None, None, datetime.now())
            )
            inserted += 1

        # Insert placeholder for unmatched rows
        self.cur.execute(
            """
            INSERT INTO coverage_canonical
            (coverage_code, coverage_name_canonical, coverage_category, payment_event, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ('UNKNOWN', '미매핑', None, None, datetime.now())
        )
        inserted += 1

        self.conn.commit()
        logger.info(f"Inserted {inserted} rows into coverage_canonical (including UNKNOWN placeholder)")

    def load_coverage_instance(self):
        """Load coverage_instance from scope_mapped.csv files"""
        logger.info("Loading coverage_instance from scope_mapped.csv...")

        # Get insurer/product/coverage_canonical ID maps
        self.cur.execute("SELECT insurer_id, insurer_name_kr FROM insurer")
        insurer_map = {r['insurer_name_kr']: r['insurer_id'] for r in self.cur.fetchall()}

        self.cur.execute("""
            SELECT p.product_id, i.insurer_name_kr
            FROM product p
            JOIN insurer i ON p.insurer_id = i.insurer_id
        """)
        product_map = {r['insurer_name_kr']: r['product_id'] for r in self.cur.fetchall()}

        # coverage_canonical uses coverage_code as PK (no coverage_id)
        self.cur.execute("SELECT coverage_code FROM coverage_canonical")
        coverage_codes = set(r['coverage_code'] for r in self.cur.fetchall())

        insurer_key_to_kr = {
            'samsung': '삼성생명',
            'hyundai': '현대해상',
            'lotte': '롯데손해보험',
            'db': 'DB손해보험',
            'kb': 'KB손해보험',
            'meritz': '메리츠화재',
            'hanwha': '한화생명',
            'heungkuk': '흥국생명'
        }

        total_inserted = 0

        for insurer_key, insurer_kr in insurer_key_to_kr.items():
            scope_path = self.project_root / f'data/scope/{insurer_key}_scope_mapped.csv'
            if not scope_path.exists():
                logger.warning(f"Skipping {insurer_key}: file not found")
                continue

            insurer_id = insurer_map.get(insurer_kr)
            product_id = product_map.get(insurer_kr)

            if not insurer_id or not product_id:
                logger.warning(f"Skipping {insurer_key}: missing insurer/product")
                continue

            with open(scope_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            for row in rows:
                coverage_name_raw = row.get('coverage_name_raw', '').strip()
                coverage_code = row.get('coverage_code', '').strip()
                mapping_status = row.get('mapping_status', 'unknown')
                match_type = row.get('match_type', 'none')
                source_page = row.get('source_page', '')

                if not coverage_name_raw:
                    continue

                # coverage_code must exist in coverage_canonical for matched rows
                if mapping_status == 'matched' and coverage_code not in coverage_codes:
                    logger.warning(f"Skipping matched row with invalid coverage_code: {coverage_code}")
                    continue

                # For unmatched rows, use a placeholder coverage_code
                final_coverage_code = coverage_code if coverage_code else 'UNKNOWN'

                self.cur.execute(
                    """
                    INSERT INTO coverage_instance
                    (insurer_id, product_id, variant_id, coverage_code,
                     coverage_name_raw, source_page, mapping_status, match_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (insurer_id, product_id, None, final_coverage_code,
                     coverage_name_raw, source_page, mapping_status, match_type, datetime.now())
                )
                total_inserted += 1

        self.conn.commit()
        logger.info(f"Inserted {total_inserted} rows into coverage_instance")

    def load_evidence_ref(self):
        """Load evidence_ref from evidence_pack.jsonl files"""
        logger.info("Loading evidence_ref from evidence_pack.jsonl...")

        # Get document map
        self.cur.execute("SELECT document_id, file_path FROM document")
        doc_map = {r['file_path']: r['document_id'] for r in self.cur.fetchall()}

        insurer_keys = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']
        total_inserted = 0

        for insurer_key in insurer_keys:
            pack_path = self.project_root / f'data/evidence_pack/{insurer_key}_evidence_pack.jsonl'
            if not pack_path.exists():
                logger.warning(f"Skipping {insurer_key}: evidence pack not found")
                continue

            with open(pack_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                entry = json.loads(line)
                coverage_name_raw = entry.get('coverage_name_raw', '')
                evidences = entry.get('evidences', [])

                # Find coverage_instance_id
                self.cur.execute(
                    """
                    SELECT ci.coverage_instance_id
                    FROM coverage_instance ci
                    JOIN insurer i ON ci.insurer_id = i.insurer_id
                    WHERE ci.coverage_name_raw = %s
                    AND i.insurer_name_kr = %s
                    LIMIT 1
                    """,
                    (coverage_name_raw, self._insurer_key_to_kr(insurer_key))
                )
                result = self.cur.fetchone()
                if not result:
                    continue

                coverage_instance_id = result['coverage_instance_id']

                for ev in evidences:
                    doc_type = ev.get('doc_type', '')
                    page_num = ev.get('page', 0)
                    snippet = ev.get('snippet', '')
                    match_keyword = ev.get('match_keyword', '')
                    file_path = ev.get('file_path', '')

                    document_id = doc_map.get(file_path)

                    self.cur.execute(
                        """
                        INSERT INTO evidence_ref
                        (coverage_instance_id, document_id, doc_type, page_num,
                         snippet_text, match_keyword, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (coverage_instance_id, document_id, doc_type, page_num,
                         snippet, match_keyword, datetime.now())
                    )
                    total_inserted += 1

        self.conn.commit()
        logger.info(f"Inserted {total_inserted} rows into evidence_ref")

    def load_amount_fact(self):
        """Load amount_fact from coverage_cards.jsonl files"""
        logger.info("Loading amount_fact from coverage_cards.jsonl...")

        insurer_keys = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']
        total_inserted = 0

        for insurer_key in insurer_keys:
            cards_path = self.project_root / f'data/compare/{insurer_key}_coverage_cards.jsonl'
            if not cards_path.exists():
                logger.warning(f"Skipping {insurer_key}: coverage cards not found")
                continue

            with open(cards_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                card = json.loads(line)
                coverage_name_raw = card.get('coverage_name_raw', '')
                evidences = card.get('evidences', [])

                # Find coverage_instance_id
                self.cur.execute(
                    """
                    SELECT ci.coverage_instance_id
                    FROM coverage_instance ci
                    JOIN insurer i ON ci.insurer_id = i.insurer_id
                    WHERE ci.coverage_name_raw = %s
                    AND i.insurer_name_kr = %s
                    LIMIT 1
                    """,
                    (coverage_name_raw, self._insurer_key_to_kr(insurer_key))
                )
                result = self.cur.fetchone()
                if not result:
                    continue

                coverage_instance_id = result['coverage_instance_id']

                # Extract amount_text from evidence snippets
                amount_text = None
                source_doc_type = None

                for ev in evidences:
                    snippet = ev.get('snippet', '')
                    if '만원' in snippet or '원' in snippet:
                        amount_text = snippet[:500]
                        source_doc_type = ev.get('doc_type', '')
                        break

                if not amount_text:
                    continue

                self.cur.execute(
                    """
                    INSERT INTO amount_fact
                    (coverage_instance_id, evidence_ref_id, amount_text,
                     source_doc_type, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (coverage_instance_id, None, amount_text, source_doc_type, datetime.now())
                )
                total_inserted += 1

        self.conn.commit()
        logger.info(f"Inserted {total_inserted} rows into amount_fact")

    def _insurer_key_to_kr(self, insurer_key: str) -> str:
        mapping = {
            'samsung': '삼성생명',
            'hyundai': '현대해상',
            'lotte': '롯데손해보험',
            'db': 'DB손해보험',
            'kb': 'KB손해보험',
            'meritz': '메리츠화재',
            'hanwha': '한화생명',
            'heungkuk': '흥국생명'
        }
        return mapping.get(insurer_key, insurer_key)

    def run(self):
        logger.info("=== STEP 9 Loader Started (Simplified) ===")
        self.connect()

        try:
            self.truncate_facts()
            self.load_coverage_canonical()
            self.load_coverage_instance()
            self.load_evidence_ref()
            self.load_amount_fact()

            logger.info("=== STEP 9 Loader Completed ===")

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            self.conn.rollback()
            raise

        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--db-url',
        default='postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).resolve().parents[2]
    )

    args = parser.parse_args()

    loader = SimpleLoader(db_url=args.db_url, project_root=args.project_root)
    loader.run()


if __name__ == '__main__':
    main()
