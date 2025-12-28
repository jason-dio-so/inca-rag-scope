#!/usr/bin/env python3
"""
STEP NEXT-DB-2C: STEP 9 Loader (facts only)
============================================

Purpose:
    Load canonical truth + STEP 1-7 artifacts into 4 fact tables:
    - coverage_canonical (from Excel)
    - coverage_instance (from scope_mapped.csv)
    - evidence_ref (from pack.jsonl)
    - amount_fact (from coverage_cards.jsonl)

Rules:
    - NO LLM / NO inference / NO computation
    - Excel is the ONLY source for coverage_canonical
    - products.yml is the ONLY source for insurer/product/variant/document FK
    - Clear+reload for idempotency
    - LOTTE/DB variants are DATA, not logic

Usage:
    python -m apps.loader.step9_loader --db-url "postgresql://..." --mode clear_reload
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

import psycopg2
import psycopg2.extras
import openpyxl
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class Step9Loader:
    """
    STEP 9 Loader: Load facts only (no inference, no logic)
    """

    def __init__(self, db_url: str, project_root: Path):
        self.db_url = db_url
        self.project_root = project_root
        self.conn = None
        self.cursor = None

        # Metadata caches (loaded from DB)
        self.insurer_map = {}  # insurer_key -> insurer_id
        self.product_map = {}  # product_key -> product_id
        self.variant_map = {}  # variant_key -> variant_id
        self.document_map = {}  # document_key -> document_id

        # Coverage canonical map (loaded from DB after insert)
        self.coverage_canonical_map = {}  # coverage_code -> exists(bool)

    def connect(self):
        """Connect to PostgreSQL database"""
        logger.info(f"Connecting to database...")
        self.conn = psycopg2.connect(self.db_url)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        logger.info("Database connection established")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

    def load_metadata_maps(self):
        """Load metadata ID mappings from DB (insurer, product, variant, document)"""
        logger.info("Loading metadata ID mappings from DB...")

        # Load insurers
        self.cursor.execute("SELECT insurer_id, insurer_name_kr FROM insurer")
        for row in self.cursor.fetchall():
            # Derive insurer_key from insurer_name_kr (삼성생명 -> samsung, etc.)
            insurer_key = self._derive_insurer_key(row['insurer_name_kr'])
            self.insurer_map[insurer_key] = row['insurer_id']

        # Load products
        self.cursor.execute("""
            SELECT p.product_id, p.product_name, i.insurer_name_kr
            FROM product p
            JOIN insurer i ON p.insurer_id = i.insurer_id
        """)
        for row in self.cursor.fetchall():
            # Derive product_key from insurer_name_kr
            insurer_key = self._derive_insurer_key(row['insurer_name_kr'])
            product_key = f"{insurer_key}_health_v1"
            self.product_map[product_key] = row['product_id']

        # Load variants
        self.cursor.execute("SELECT variant_id, variant_key FROM product_variant")
        for row in self.cursor.fetchall():
            self.variant_map[row['variant_key']] = row['variant_id']

        # Load documents
        self.cursor.execute("SELECT document_id, file_path FROM document")
        for row in self.cursor.fetchall():
            # Use file_path as key
            self.document_map[row['file_path']] = row['document_id']

        logger.info(f"Loaded metadata: {len(self.insurer_map)} insurers, "
                   f"{len(self.product_map)} products, {len(self.variant_map)} variants, "
                   f"{len(self.document_map)} documents")

    def _derive_insurer_key(self, insurer_name_kr: str) -> str:
        """Derive insurer_key from Korean name"""
        mapping = {
            '삼성생명': 'samsung',
            '현대해상': 'hyundai',
            '롯데손해보험': 'lotte',
            'DB손해보험': 'db',
            'KB손해보험': 'kb',
            '메리츠화재': 'meritz',
            '한화생명': 'hanwha',
            '흥국생명': 'heungkuk'
        }
        return mapping.get(insurer_name_kr, insurer_name_kr.lower())

    def _normalize_text(self, text: str) -> str:
        """Normalize text for instance_key/evidence_key (trim + collapse spaces only)"""
        import re
        if not text:
            return ""
        # Trim and collapse multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', text.strip())
        return normalized

    def _build_instance_key(self, insurer_key: str, product_key: str,
                           variant_key: str, coverage_code: str,
                           coverage_name_raw: str) -> str:
        """
        Build deterministic instance_key for coverage_instance.
        Format: {insurer_key}|{product_key}|{variant_key_or_}|{coverage_code_or_}|{coverage_name_raw}
        - variant_key: "_" if NULL
        - coverage_code: "_" if NULL (for unmatched)
        - coverage_name_raw: normalized text (trim + collapse spaces)
        """
        variant_part = variant_key if variant_key else "_"
        code_part = coverage_code if coverage_code else "_"
        name_part = self._normalize_text(coverage_name_raw)

        return f"{insurer_key}|{product_key}|{variant_part}|{code_part}|{name_part}"

    def _derive_product_key(self, product_name_raw: str) -> str:
        """Derive product_key from product_name_raw"""
        # Extract insurer prefix
        for kr_name, key in [
            ('삼성', 'samsung'),
            ('현대', 'hyundai'),
            ('롯데', 'lotte'),
            ('DB', 'db'),
            ('KB', 'kb'),
            ('메리츠', 'meritz'),
            ('한화', 'hanwha'),
            ('흥국', 'heungkuk')
        ]:
            if kr_name in product_name_raw:
                return f"{key}_health_v1"
        return product_name_raw.lower().replace(' ', '_')

    def _derive_variant_key(self, variant_attrs: Dict) -> str:
        """Derive variant_key from variant_attrs"""
        if 'sex' in variant_attrs:
            return f"LOTTE_{'MALE' if variant_attrs['sex'] == 'M' else 'FEMALE'}"
        elif 'age_band' in variant_attrs:
            return f"DB_AGE_{'U40' if variant_attrs['age_band'] == 'UNDER_41' else 'O40'}"
        return str(uuid.uuid4())

    def _derive_document_key(self, doc_title_raw: str) -> str:
        """Derive document_key from doc_title_raw"""
        # Simple derivation (exact match from products.yml)
        # This is a simplified version; production needs exact YAML lookup
        return doc_title_raw.lower().replace(' ', '_')

    def truncate_fact_tables(self):
        """Truncate 4 fact tables (reset_then_load mode ONLY - NOT for production upsert)"""
        logger.warning("⚠️  Truncating fact tables (reset_then_load mode) - metadata tables untouched")

        tables = ['amount_fact', 'evidence_ref', 'coverage_instance', 'coverage_canonical']
        for table in tables:
            self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            logger.info(f"  - Truncated {table}")

        self.conn.commit()
        logger.info("✅ Fact tables truncated (metadata preserved)")

    def load_coverage_canonical(self, excel_path: Path):
        """
        Load coverage_canonical from Excel (ONLY source of truth)
        Excel structure: ('ins_cd', '보험사명', 'cre_cvr_cd', '신정원코드명', '담보명(가입설계서)')
        - cre_cvr_cd = coverage_code (e.g., A1100)
        - 신정원코드명 = coverage_name_canonical (e.g., 질병사망)
        """
        logger.info(f"Loading coverage_canonical from {excel_path}...")

        if not excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        sheet = wb.active

        # Expected header: ('ins_cd', '보험사명', 'cre_cvr_cd', '신정원코드명', '담보명(가입설계서)')
        # cre_cvr_cd (idx=2) = coverage_code
        # 신정원코드명 (idx=3) = coverage_name_canonical

        rows_data = list(sheet.iter_rows(values_only=True))
        header = rows_data[0]

        logger.info(f"Excel header: {header}")

        # Build unique coverage set (by coverage_code)
        unique_coverages = {}

        for row in rows_data[1:]:
            if not row or len(row) < 4:
                continue

            coverage_code = str(row[2]).strip() if row[2] else None
            coverage_name = str(row[3]).strip() if row[3] else None

            if not coverage_code or not coverage_name:
                continue

            # Keep first occurrence (canonical name)
            if coverage_code not in unique_coverages:
                unique_coverages[coverage_code] = {
                    'coverage_code': coverage_code,
                    'coverage_name_canonical': coverage_name,
                    'alias_list': []
                }

        wb.close()

        logger.info(f"Extracted {len(unique_coverages)} unique canonical coverages from Excel")

        # UPSERT into DB
        # Schema: (coverage_code PK, coverage_name_canonical, coverage_category, payment_event, created_at)
        upsert_sql = """
            INSERT INTO coverage_canonical
            (coverage_code, coverage_name_canonical, coverage_category, payment_event, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (coverage_code) DO UPDATE SET
                coverage_name_canonical = EXCLUDED.coverage_name_canonical,
                updated_at = CURRENT_TIMESTAMP
        """

        upserted = 0
        for coverage_data in unique_coverages.values():
            self.cursor.execute(
                upsert_sql,
                (
                    coverage_data['coverage_code'],
                    coverage_data['coverage_name_canonical'],
                    None,  # coverage_category (not derived from Excel)
                    None,  # payment_event (not derived from Excel)
                    datetime.now()
                )
            )
            if self.cursor.rowcount > 0:
                self.coverage_canonical_map[coverage_data['coverage_code']] = True
                upserted += 1

        self.conn.commit()
        logger.info(f"✅ Upserted {upserted} rows into coverage_canonical")

    def load_coverage_instance(self, insurer_key: str, scope_mapped_path: Path):
        """
        Load coverage_instance from scope_mapped.csv
        Schema: (instance_id UUID PK, insurer_id, product_id, variant_id, coverage_code,
                 coverage_name_raw, source_page, mapping_status, match_type, instance_key, created_at)
        """
        logger.info(f"Loading coverage_instance for {insurer_key} from {scope_mapped_path}...")

        if not scope_mapped_path.exists():
            logger.warning(f"Scope file not found, skipping: {scope_mapped_path}")
            return

        insurer_id = self.insurer_map.get(insurer_key)
        if not insurer_id:
            logger.error(f"Insurer {insurer_key} not found in DB metadata")
            return

        with open(scope_mapped_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        logger.info(f"  Read {len(rows)} rows from {scope_mapped_path}")

        # UPSERT coverage_instance (idempotent via instance_key)
        # Natural key: instance_key (deterministic, loader-generated)
        upsert_sql = """
            INSERT INTO coverage_instance
            (insurer_id, product_id, variant_id, coverage_code,
             coverage_name_raw, source_page, mapping_status, match_type, instance_key, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (instance_key)
            DO UPDATE SET
                coverage_name_raw = EXCLUDED.coverage_name_raw,
                source_page = EXCLUDED.source_page,
                mapping_status = EXCLUDED.mapping_status,
                match_type = EXCLUDED.match_type,
                updated_at = CURRENT_TIMESTAMP
        """

        inserted = 0
        skipped = 0

        for row in rows:
            coverage_code = row.get('coverage_code', '').strip()
            coverage_name_raw = row.get('coverage_name_raw', '').strip()
            mapping_status = row.get('mapping_status', 'unknown').strip()
            match_type = row.get('match_type', 'none').strip()
            source_page = row.get('source_page', '')

            # Convert empty string to None for coverage_code
            if not coverage_code:
                coverage_code = None

            if not coverage_name_raw:
                skipped += 1
                continue

            # Validate mapping_status
            if mapping_status not in ['matched', 'unmatched']:
                mapping_status = 'unmatched'

            # ✅ ALLOW unmatched with coverage_code=NULL (schema now supports it)
            # ⛔ DO NOT SKIP unmatched rows (data loss prevention)
            if mapping_status == 'matched' and coverage_code is None:
                logger.warning(f"⚠️  Matched coverage without code: {coverage_name_raw}, forcing to unmatched")
                mapping_status = 'unmatched'

            # Get product_id (use insurer_key to derive product_key)
            product_key = f"{insurer_key}_health_v1"
            product_id = self.product_map.get(product_key)

            if not product_id:
                logger.warning(f"Product not found for {insurer_key}, skipping row")
                skipped += 1
                continue

            # variant_id: set to NULL for now (no variant info in scope_mapped.csv)
            variant_id = None
            variant_key = None

            # source_page: convert to int or NULL
            source_page_int = None
            if source_page:
                try:
                    source_page_int = int(source_page)
                except ValueError:
                    pass

            # Build instance_key (natural key for idempotent upsert)
            instance_key = self._build_instance_key(
                insurer_key, product_key, variant_key, coverage_code, coverage_name_raw
            )

            self.cursor.execute(
                upsert_sql,
                (
                    insurer_id,
                    product_id,
                    variant_id,
                    coverage_code,  # NULL allowed for unmatched
                    coverage_name_raw,
                    source_page_int,
                    mapping_status,
                    match_type if match_type else None,
                    instance_key,
                    datetime.now()
                )
            )
            if self.cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        self.conn.commit()
        logger.info(f"✅ Upserted {inserted} rows (skipped {skipped} due to conflicts) into coverage_instance for {insurer_key}")

    def load_evidence_ref(self, insurer_key: str, pack_path: Path):
        """
        Load evidence_ref from evidence_pack.jsonl
        Schema: (evidence_id UUID PK, coverage_instance_id, document_id, doc_type,
                 page INT, snippet TEXT, match_keyword, rank INT 1-3, evidence_key, created_at)
        """
        logger.info(f"Loading evidence_ref for {insurer_key} from {pack_path}...")

        if not pack_path.exists():
            logger.warning(f"Evidence pack not found, skipping: {pack_path}")
            return

        with open(pack_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        logger.info(f"  Read {len(lines)} evidence pack entries")

        # UPSERT evidence_ref (idempotent via evidence_key)
        # Natural key: evidence_key (deterministic, loader-generated)
        upsert_sql = """
            INSERT INTO evidence_ref
            (coverage_instance_id, document_id, doc_type, page,
             snippet, match_keyword, rank, evidence_key, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (evidence_key)
            DO UPDATE SET
                snippet = EXCLUDED.snippet,
                match_keyword = EXCLUDED.match_keyword,
                updated_at = CURRENT_TIMESTAMP
        """

        inserted = 0
        skipped = 0

        for line in lines:
            entry = json.loads(line.strip())

            evidences = entry.get('evidences', [])
            coverage_name_raw = entry.get('coverage_name_raw', '')

            # Find coverage_instance_id AND instance_key by matching coverage_name_raw + insurer
            self.cursor.execute(
                """
                SELECT ci.instance_id, ci.instance_key
                FROM coverage_instance ci
                JOIN insurer i ON ci.insurer_id = i.insurer_id
                WHERE i.insurer_name_kr = %s AND ci.coverage_name_raw = %s
                LIMIT 1
                """,
                (self._insurer_key_to_kr(insurer_key), coverage_name_raw)
            )
            result = self.cursor.fetchone()

            if not result:
                skipped += len(evidences)
                continue

            coverage_instance_id = result['instance_id']
            instance_key = result['instance_key']

            # Rank evidences by doc_type priority (가입설계서 > 약관 > 사업방법서 > 상품요약서)
            doc_type_priority = {'가입설계서': 1, '약관': 2, '사업방법서': 3, '상품요약서': 3}

            for idx, ev in enumerate(evidences[:3]):  # Max 3 evidences per coverage
                doc_type = ev.get('doc_type', '')
                page = ev.get('page', 0)
                snippet = ev.get('snippet', '')
                match_keyword = ev.get('match_keyword', '')
                file_path = ev.get('file_path', '')

                if not snippet or not doc_type or page <= 0:
                    skipped += 1
                    continue

                # Validate doc_type
                if doc_type not in ['약관', '사업방법서', '상품요약서', '가입설계서']:
                    skipped += 1
                    continue

                # Lookup document_id by file_path
                # Evidence pack has absolute paths, document table has relative paths
                # Normalize: remove project root prefix if present
                file_path_normalized = file_path
                if file_path.startswith('/'):
                    # Convert absolute to relative (remove /Users/cheollee/inca-rag-scope/ prefix)
                    parts = Path(file_path).parts
                    if 'data' in parts:
                        data_idx = parts.index('data')
                        file_path_normalized = str(Path(*parts[data_idx:]))

                document_id = self.document_map.get(file_path_normalized)
                if not document_id:
                    logger.debug(f"Document not found for path: {file_path_normalized}")
                    skipped += 1
                    continue

                # Assign rank (1-3)
                rank = idx + 1

                # Build evidence_key (natural key for idempotent upsert)
                # Format: {instance_key}|{file_path}|{doc_type}|{page}|{rank}
                evidence_key = f"{instance_key}|{file_path_normalized}|{doc_type}|{page}|{rank}"

                self.cursor.execute(
                    upsert_sql,
                    (
                        coverage_instance_id,
                        document_id,
                        doc_type,
                        page,
                        snippet[:500],  # Truncate snippet if needed
                        match_keyword,
                        rank,
                        evidence_key,
                        datetime.now()
                    )
                )
                inserted += 1

        self.conn.commit()
        logger.info(f"✅ Upserted {inserted} evidence refs (skipped {skipped}) for {insurer_key}")

    def load_amount_fact(self, insurer_key: str, cards_path: Path):
        """
        Load amount_fact from coverage_cards.jsonl
        Schema: (amount_id UUID PK, coverage_instance_id, evidence_id,
                 status ENUM, value_text TEXT, source_doc_type, source_priority, notes JSONB)
        """
        logger.info(f"Loading amount_fact for {insurer_key} from {cards_path}...")

        if not cards_path.exists():
            logger.warning(f"Coverage cards not found, skipping: {cards_path}")
            return

        with open(cards_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        logger.info(f"  Read {len(lines)} coverage card entries")

        inserted = 0
        skipped = 0

        for line in lines:
            card = json.loads(line.strip())

            coverage_name_raw = card.get('coverage_name_raw', '')
            evidences = card.get('evidences', [])

            # Find coverage_instance_id
            self.cursor.execute(
                """
                SELECT ci.instance_id
                FROM coverage_instance ci
                JOIN insurer i ON ci.insurer_id = i.insurer_id
                WHERE i.insurer_name_kr = %s AND ci.coverage_name_raw = %s
                LIMIT 1
                """,
                (self._insurer_key_to_kr(insurer_key), coverage_name_raw)
            )
            result = self.cursor.fetchone()

            if not result:
                skipped += 1
                continue

            coverage_instance_id = result['instance_id']

            # Extract amount_text from snippet (heuristic: look for "만원", "원" keywords)
            # Priority: 가입설계서 > others
            value_text = None
            source_doc_type = None
            evidence_id = None

            # Try 가입설계서 first
            for ev in evidences:
                if ev.get('doc_type') == '가입설계서':
                    snippet = ev.get('snippet', '')
                    if '만원' in snippet or '원' in snippet:
                        value_text = snippet[:200]
                        source_doc_type = '가입설계서'
                        break

            # Fallback to other doc types
            if not value_text:
                for ev in evidences:
                    snippet = ev.get('snippet', '')
                    if '만원' in snippet or '원' in snippet:
                        value_text = snippet[:200]
                        source_doc_type = ev.get('doc_type', '')
                        break

            # Determine status based on value_text AND evidence_id availability
            # Constraint: CONFIRMED requires evidence_id NOT NULL
            if not value_text:
                # No amount found, store as UNCONFIRMED
                status = 'UNCONFIRMED'
                value_text = None
                source_doc_type = None
                source_priority = None
            else:
                # Amount found, but need to verify evidence_id exists
                source_priority = 'PRIMARY' if source_doc_type == '가입설계서' else 'SECONDARY'

                # Lookup evidence_id (required for CONFIRMED status)
                if source_doc_type:
                    self.cursor.execute(
                        """
                        SELECT evidence_id FROM evidence_ref
                        WHERE coverage_instance_id = %s AND doc_type = %s
                        LIMIT 1
                        """,
                        (coverage_instance_id, source_doc_type)
                    )
                    ev_result = self.cursor.fetchone()
                    if ev_result:
                        evidence_id = ev_result['evidence_id']
                        status = 'CONFIRMED'
                    else:
                        # No evidence_id found, cannot use CONFIRMED
                        # Constraint: UNCONFIRMED requires value_text=NULL
                        status = 'UNCONFIRMED'
                        evidence_id = None
                        value_text = None  # MUST be NULL for UNCONFIRMED
                        source_doc_type = None
                        source_priority = None
                else:
                    status = 'UNCONFIRMED'
                    evidence_id = None
                    value_text = None
                    source_doc_type = None
                    source_priority = None

            # UPSERT amount_fact (idempotent by coverage_instance_id)
            upsert_sql = """
                INSERT INTO amount_fact
                (coverage_instance_id, evidence_id, status, value_text,
                 source_doc_type, source_priority, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coverage_instance_id) DO UPDATE SET
                    evidence_id = EXCLUDED.evidence_id,
                    status = EXCLUDED.status,
                    value_text = EXCLUDED.value_text,
                    source_doc_type = EXCLUDED.source_doc_type,
                    source_priority = EXCLUDED.source_priority,
                    updated_at = CURRENT_TIMESTAMP
            """

            self.cursor.execute(
                upsert_sql,
                (
                    coverage_instance_id,
                    evidence_id,
                    status,
                    value_text,
                    source_doc_type,
                    source_priority,
                    json.dumps([]),
                    datetime.now()
                )
            )
            if self.cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        self.conn.commit()
        logger.info(f"✅ Upserted {inserted} amount facts (skipped {skipped}) for {insurer_key}")

    def _insurer_key_to_kr(self, insurer_key: str) -> str:
        """Convert insurer_key to Korean name"""
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

    def run(self, mode: str = 'upsert'):
        """
        Main execution flow

        Modes:
        - upsert (DEFAULT, production): Idempotent upsert, no truncate
        - reset_then_load (explicit dev): Truncate facts then load
        """
        logger.info("=== STEP 9 Loader Started ===")
        logger.info(f"Mode: {mode}")

        if mode not in ['upsert', 'reset_then_load']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'upsert' or 'reset_then_load'")

        self.connect()

        try:
            # Step 1: Load metadata ID mappings
            self.load_metadata_maps()

            # Step 2: Truncate fact tables ONLY if reset_then_load
            if mode == 'reset_then_load':
                self.truncate_fact_tables()
            else:
                logger.info("✅ UPSERT mode: fact tables will be updated idempotently (no truncate)")

            # Step 3: Load coverage_canonical from Excel
            excel_path = self.project_root / 'data/sources/mapping/담보명mapping자료.xlsx'
            self.load_coverage_canonical(excel_path)

            # Step 4-7: Load facts for each insurer
            insurers = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']

            for insurer_key in insurers:
                logger.info(f"\n--- Processing {insurer_key} ---")

                # Load coverage_instance
                scope_path = self.project_root / f'data/scope/{insurer_key}_scope_mapped.csv'
                self.load_coverage_instance(insurer_key, scope_path)

                # Load evidence_ref
                pack_path = self.project_root / f'data/evidence_pack/{insurer_key}_evidence_pack.jsonl'
                self.load_evidence_ref(insurer_key, pack_path)

                # Load amount_fact
                cards_path = self.project_root / f'data/compare/{insurer_key}_coverage_cards.jsonl'
                self.load_amount_fact(insurer_key, cards_path)

            logger.info("\n=== STEP 9 Loader Completed ===")

        except Exception as e:
            logger.error(f"Error during loading: {e}", exc_info=True)
            self.conn.rollback()
            raise

        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description='STEP 9 Loader (facts only)')
    parser.add_argument(
        '--db-url',
        default='postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope',
        help='PostgreSQL connection URL'
    )
    parser.add_argument(
        '--mode',
        default='upsert',
        choices=['upsert', 'reset_then_load'],
        help='Load mode: upsert (default, idempotent) or reset_then_load (explicit truncate)'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help='Project root directory'
    )

    args = parser.parse_args()

    loader = Step9Loader(
        db_url=args.db_url,
        project_root=args.project_root
    )

    loader.run(mode=args.mode)


if __name__ == '__main__':
    main()
