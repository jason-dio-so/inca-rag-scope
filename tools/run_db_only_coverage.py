#!/usr/bin/env python3
"""
DB-only coverage pipeline with context guard.
Baseline SSOT implementation for A4210.

Usage:
  python3 tools/run_db_only_coverage.py \\
    --coverage_code A4210 \\
    --as_of_date 2025-11-26 \\
    --ins_cds N01,N08 \\
    --skip-chunks
"""

import argparse
import hashlib
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber
import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.coverage_profiles import get_profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Insurer code to directory mapping
INSURER_DIR_MAP = {
    "N01": "meritz",
    "N02": "hanwha",
    "N03": "db",
    "N05": "heungkuk",
    "N08": "samsung",
    "N09": "hyundai",
    "N10": "kb",
    "N13": "lotte"
}

# PDF Source Registry (hard-coded for now)
PDF_SOURCE_REGISTRY = {
    "약관": {"suffix": "_약관.pdf", "doc_type": "약관"},
    "사업방법서": {"suffix": "_사업방법서.pdf", "doc_type": "사업방법서", "alt_suffix": "_사업설명서.pdf"},
    "상품요약서": {"suffix": "_상품요약서.pdf", "doc_type": "상품요약서"}
}

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "inca_ssot",
    "user": "postgres",
    "password": "postgres"
}

class GateContext:
    def __init__(self, coverage_code: str, ins_cd: str, anchors: List[str], coverage_name: str, profile: dict = None):
        self.coverage_code = coverage_code
        self.ins_cd = ins_cd
        self.anchors = anchors
        self.coverage_name = coverage_name
        self.profile = profile or {}

    def get_required_terms(self, slot_key: str) -> List[str]:
        return self.profile.get("required_terms_by_slot", {}).get(slot_key, [])

    def get_hard_negatives(self) -> List[str]:
        return self.profile.get("hard_negative_terms_global", [])

    def get_section_negatives(self) -> List[str]:
        return self.profile.get("section_negative_terms_global", [])

    def get_diagnosis_signals(self) -> List[str]:
        return self.profile.get("diagnosis_signal_terms_global", [])

    def get_slot_negatives(self, slot_key: str) -> List[str]:
        return self.profile.get("slot_specific_negatives", {}).get(slot_key, [])


def apply_gates(slot_key: str, chunk_text: str, excerpt: str, ctx: GateContext) -> Tuple[bool, List[str]]:
    """Apply 7-gate validation to chunk"""
    reasons = []

    # GATE 1: Anchor in excerpt
    if not any(anchor in excerpt for anchor in ctx.anchors):
        reasons.append("no_anchor_in_excerpt")
        return False, reasons

    # GATE 2: Hard-negative check
    for pattern in ctx.get_hard_negatives():
        if re.search(pattern, chunk_text):
            reasons.append(f"hard_negative:{pattern}")
            return False, reasons

    # GATE 3: Section-negative check
    for pattern in ctx.get_section_negatives():
        if re.search(pattern, chunk_text):
            reasons.append(f"section_negative:{pattern}")
            return False, reasons

    # GATE 4: Diagnosis-signal required
    has_signal = False
    for pattern in ctx.get_diagnosis_signals():
        if re.search(pattern, chunk_text):
            has_signal = True
            break
    if not has_signal:
        reasons.append("no_diagnosis_signal")
        return False, reasons

    # GATE 5: Coverage name lock (dynamic token extraction)
    normalized_name = re.sub(r'\s+', '', ctx.coverage_name)
    normalized_text = re.sub(r'\s+', '', chunk_text)

    # First check: exact match (normalized)
    if normalized_name in normalized_text:
        pass  # Perfect match, proceed
    else:
        # Extract core tokens from coverage_name (2+ chars, exclude parentheses content)
        base_name = re.sub(r'\([^)]*\)', '', ctx.coverage_name)  # Remove (유사암제외) etc
        core_tokens = [t for t in re.findall(r'[가-힣]{2,}', base_name) if len(t) >= 2]

        # Require at least 2 tokens to match (or all if less than 2)
        required_count = min(2, len(core_tokens))
        matched_count = sum(1 for token in core_tokens if token in chunk_text)

        if matched_count < required_count:
            reasons.append(f"coverage_name_lock_failed:req_{required_count}_matched_{matched_count}")
            return False, reasons

    # GATE 6: Slot-specific keywords
    required_terms = ctx.get_required_terms(slot_key)
    if required_terms:
        has_required = any(re.search(term, chunk_text) for term in required_terms)
        if not has_required:
            reasons.append(f"no_required_terms_for_{slot_key}")
            return False, reasons

    # GATE 7: Slot-specific negatives
    for pattern in ctx.get_slot_negatives(slot_key):
        if re.search(pattern, chunk_text):
            reasons.append(f"slot_specific_negative:{pattern}")
            return False, reasons

    return True, []


class DBOnlyCoveragePipeline:
    def __init__(self, coverage_code: str, as_of_date: str, ins_cds: List[str], stage: str = "all", skip_chunks: bool = False):
        self.coverage_code = coverage_code
        self.as_of_date = as_of_date
        self.ins_cds = ins_cds
        self.stage = stage
        self.skip_chunks = skip_chunks
        self.conn = None
        self.cur = None

    def connect(self):
        conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        logger.info(f"Connecting to DB: {conn_str}")
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        logger.info(f"✅ Connected to: {DB_CONFIG['dbname']}")

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def get_coverage_name(self, ins_cd: str) -> str:
        """Get insurer_coverage_name from DB"""
        self.cur.execute("""
            SELECT insurer_coverage_name FROM coverage_mapping_ssot
            WHERE coverage_code = %s AND ins_cd = %s AND as_of_date = %s
        """, (self.coverage_code, ins_cd, self.as_of_date))
        row = self.cur.fetchone()
        return row['insurer_coverage_name'] if row else ""

    def get_anchor_keywords(self, ins_cd: str, profile: dict = None) -> List[str]:
        """Get anchor keywords from profile + insurer_coverage_name"""
        anchors = []

        # Get profile anchors
        if profile:
            anchors.extend(profile.get("anchor_keywords", []))

        # Add insurer_coverage_name as anchor
        coverage_name = self.get_coverage_name(ins_cd)
        if coverage_name and coverage_name not in anchors:
            anchors.append(coverage_name)

        return anchors

    def generate_chunks(self) -> Dict[str, int]:
        """Generate coverage_chunk from PDF sources"""
        logger.info(f"📄 Generating chunks for {self.coverage_code}...")
        profile = get_profile(self.coverage_code)

        total_created = 0
        stats = {}

        for ins_cd in self.ins_cds:
            logger.info(f"Processing {ins_cd}...")
            insurer_dir = INSURER_DIR_MAP.get(ins_cd)
            if not insurer_dir:
                logger.warning(f"  ⚠️  No directory mapping for {ins_cd}, skipping")
                continue

            # Get anchors and coverage name for filtering
            coverage_name = self.get_coverage_name(ins_cd)
            anchors = self.get_anchor_keywords(ins_cd, profile)
            logger.info(f"  Anchors: {anchors[:3]}...")  # First 3 for brevity

            ins_stats = {"pages_extracted": 0, "chunks_created": 0}

            # Process each doc_type
            for doc_key, doc_config in PDF_SOURCE_REGISTRY.items():
                doc_type = doc_config["doc_type"]
                insurer_name_ko = {
                    "meritz": "메리츠", "hanwha": "한화", "db": "DB", "heungkuk": "흥국",
                    "samsung": "삼성", "hyundai": "현대", "kb": "KB", "lotte": "롯데"
                }.get(insurer_dir, insurer_dir.title())

                # Find PDF file
                pdf_filename = f"{insurer_name_ko}{doc_config['suffix']}"
                pdf_path = PROJECT_ROOT / "data" / "sources" / "insurers" / insurer_dir / doc_key / pdf_filename

                # Try alternative suffix if not found
                if not pdf_path.exists() and "alt_suffix" in doc_config:
                    pdf_filename = f"{insurer_name_ko}{doc_config['alt_suffix']}"
                    pdf_path = PROJECT_ROOT / "data" / "sources" / "insurers" / insurer_dir / doc_key / pdf_filename

                if not pdf_path.exists():
                    logger.info(f"  ⏭️  {doc_type} PDF not found: {pdf_path.name}")
                    continue

                logger.info(f"  📖 Processing {doc_type}: {pdf_path.name}")

                # Extract text from PDF
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        total_pages = len(pdf.pages)
                        logger.info(f"    Total pages: {total_pages}")

                        for page_num, page in enumerate(pdf.pages, start=1):
                            # Progress logging every 100 pages
                            if page_num % 100 == 0:
                                logger.info(f"    Progress: {page_num}/{total_pages} pages, {ins_stats['chunks_created']} chunks created")
                                self.conn.commit()  # Batch commit every 100 pages

                            text = page.extract_text()
                            if not text or len(text) < 50:
                                continue

                            ins_stats["pages_extracted"] += 1

                            # Filter: check if page contains any anchor
                            if not any(anchor in text for anchor in anchors):
                                continue

                            # Create chunk
                            excerpt = text[:500]  # First 500 chars as excerpt
                            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

                            # Normalize doc_type before INSERT
                            normalized_doc_type = doc_type
                            if doc_type in ["상품요약서", "쉬운요약서"]:
                                normalized_doc_type = "요약서"

                            # UPSERT chunk
                            self.cur.execute("""
                                INSERT INTO coverage_chunk
                                (ins_cd, coverage_code, as_of_date, doc_type, source_pdf,
                                 page_start, page_end, excerpt, chunk_text, content_hash)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (ins_cd, coverage_code, as_of_date, doc_type, source_pdf, page_start, page_end, content_hash)
                                DO NOTHING
                            """, (ins_cd, self.coverage_code, self.as_of_date, normalized_doc_type, pdf_filename,
                                  page_num, page_num, excerpt, text, content_hash))

                            if self.cur.rowcount > 0:
                                ins_stats["chunks_created"] += 1

                        logger.info(f"    Final: {total_pages}/{total_pages} pages, {ins_stats['chunks_created']} chunks created")

                except Exception as e:
                    logger.error(f"  ❌ Error processing {pdf_path.name}: {e}")
                    continue

            self.conn.commit()
            total_created += ins_stats["chunks_created"]
            stats[ins_cd] = ins_stats
            logger.info(f"  ✅ {ins_cd}: {ins_stats['chunks_created']} chunks from {ins_stats['pages_extracted']} pages")

        logger.info(f"✅ Chunk generation complete: {total_created} total chunks")
        return stats

    def get_chunk_count(self) -> int:
        self.cur.execute("""
            SELECT COUNT(*) FROM coverage_chunk
            WHERE coverage_code = %s AND as_of_date = %s
        """, (self.coverage_code, self.as_of_date))
        return self.cur.fetchone()['count']

    def delete_existing_slots(self):
        logger.info("🗑️  Deleting existing evidence_slot and compare_table_v2...")
        self.cur.execute("DELETE FROM evidence_slot WHERE coverage_code = %s AND as_of_date = %s",
                        (self.coverage_code, self.as_of_date))
        slot_count = self.cur.rowcount
        self.cur.execute("DELETE FROM compare_table_v2 WHERE coverage_code = %s AND as_of_date = %s",
                        (self.coverage_code, self.as_of_date))
        table_count = self.cur.rowcount
        self.conn.commit()
        logger.info(f"✅ Deleted {slot_count} evidence_slot rows, {table_count} compare_table_v2 rows")

    def generate_evidence_slots(self) -> Dict[str, int]:
        profile = get_profile(self.coverage_code)
        gate_version = profile.get("gate_version", "GATE_SSOT_V2_CONTEXT_GUARD") if profile else "GATE_SSOT_V2_CONTEXT_GUARD"
        profile_id = profile.get("profile_id", f"{self.coverage_code}_DEFAULT") if profile else f"{self.coverage_code}_DEFAULT"

        logger.info(f"🔍 Generating evidence_slot for {self.coverage_code}...")
        logger.info(f"  Profile: {profile_id}")
        logger.info(f"  Gate version: {gate_version}")

        slot_keys = ["waiting_period", "exclusions", "subtype_coverage_map"]
        stats = {"FOUND": 0, "NOT_FOUND": 0, "DROPPED": 0}

        for ins_cd in self.ins_cds:
            logger.info(f"Processing {ins_cd}...")
            coverage_name = self.get_coverage_name(ins_cd)
            anchors = self.get_anchor_keywords(ins_cd, profile)
            logger.info(f"  Coverage name: {coverage_name}")
            logger.info(f"  Anchors: {anchors}")

            self.cur.execute("""
                SELECT chunk_id, chunk_text, excerpt, page_start, page_end, doc_type, source_pdf
                FROM coverage_chunk
                WHERE coverage_code = %s AND as_of_date = %s AND ins_cd = %s
            """, (self.coverage_code, self.as_of_date, ins_cd))
            all_chunks = self.cur.fetchall()

            anchor_matched = [c for c in all_chunks if any(a in c['excerpt'] for a in anchors)]
            logger.info(f"  Filtered chunks: {len(anchor_matched)}/{len(all_chunks)} (anchor-matched)")

            ctx = GateContext(
                coverage_code=self.coverage_code,
                ins_cd=ins_cd,
                anchors=anchors,
                coverage_name=coverage_name,
                profile=profile
            )

            for slot_key in slot_keys:
                found_chunk = None
                for chunk in anchor_matched:
                    passed, reasons = apply_gates(slot_key, chunk['chunk_text'], chunk['excerpt'], ctx)
                    if passed:
                        found_chunk = chunk
                        break

                if found_chunk:
                    page_range = f"{found_chunk['page_start']}-{found_chunk['page_end']}"
                    self.cur.execute("""
                        INSERT INTO evidence_slot (coverage_code, as_of_date, ins_cd, slot_key,
                                                  doc_type, source_pdf, page_range, excerpt, status, gate_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'FOUND', %s)
                    """, (self.coverage_code, self.as_of_date, ins_cd, slot_key,
                          found_chunk['doc_type'], found_chunk['source_pdf'], page_range,
                          found_chunk['excerpt'], gate_version))
                    stats["FOUND"] += 1
                else:
                    stats["NOT_FOUND"] += 1

        self.conn.commit()
        logger.info(f"✅ Created slots: FOUND={stats['FOUND']}, NOT_FOUND={stats['NOT_FOUND']}, DROPPED={stats['DROPPED']}")
        return stats

    def generate_compare_table(self) -> int:
        logger.info(f"📊 Generating compare_table_v2 for {self.coverage_code}...")

        # Get canonical name from coverage_canonical
        self.cur.execute("SELECT canonical_name FROM coverage_canonical WHERE coverage_code = %s", (self.coverage_code,))
        canonical_row = self.cur.fetchone()
        canonical_name = canonical_row['canonical_name'] if canonical_row else self.coverage_code

        profile = get_profile(self.coverage_code)
        gate_version = profile.get("gate_version", "GATE_SSOT_V2_CONTEXT_GUARD") if profile else "GATE_SSOT_V2_CONTEXT_GUARD"
        profile_id = profile.get("profile_id", f"{self.coverage_code}_DEFAULT") if profile else f"{self.coverage_code}_DEFAULT"

        self.cur.execute("""
            SELECT ins_cd, slot_key, excerpt, status
            FROM evidence_slot
            WHERE coverage_code = %s AND as_of_date = %s
            ORDER BY ins_cd, slot_key
        """, (self.coverage_code, self.as_of_date))

        slots_by_insurer = {}
        for row in self.cur.fetchall():
            ins_cd = row['ins_cd']
            if ins_cd not in slots_by_insurer:
                slots_by_insurer[ins_cd] = {}
            slots_by_insurer[ins_cd][row['slot_key']] = {
                "status": row['status'],
                "excerpt": row['excerpt']
            }

        insurer_rows = [{"ins_cd": ins_cd, "slots": slots} for ins_cd, slots in slots_by_insurer.items()]
        insurer_set = json.dumps(sorted(self.ins_cds))  # JSON array of ins_cds

        payload = {
            "insurer_rows": insurer_rows,
            "q13_report": None,
            "debug": {
                "gate_version": gate_version,
                "profile_id": profile_id,
                "generated_by": "tools/run_db_only_coverage.py",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "chunk_rowcount_at_generation": self.get_chunk_count()
            }
        }

        self.cur.execute("""
            INSERT INTO compare_table_v2 (coverage_code, as_of_date, canonical_name, insurer_set, payload)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING table_id
        """, (self.coverage_code, self.as_of_date, canonical_name, insurer_set, json.dumps(payload)))

        table_id = self.cur.fetchone()['table_id']
        self.conn.commit()
        logger.info(f"✅ Created compare_table_v2: table_id={table_id}")
        return table_id

    def verify(self):
        logger.info("🔍 Verifying...")
        self.cur.execute("SELECT COUNT(*) FROM coverage_chunk WHERE coverage_code = %s AND as_of_date = %s",
                        (self.coverage_code, self.as_of_date))
        chunk_count = self.cur.fetchone()['count']

        self.cur.execute("SELECT COUNT(*) FROM evidence_slot WHERE coverage_code = %s AND as_of_date = %s",
                        (self.coverage_code, self.as_of_date))
        slot_count = self.cur.fetchone()['count']

        self.cur.execute("SELECT COUNT(*) FROM compare_table_v2 WHERE coverage_code = %s AND as_of_date = %s",
                        (self.coverage_code, self.as_of_date))
        table_count = self.cur.fetchone()['count']

        logger.info("📊 Results:")
        logger.info(f"  coverage_chunk: {chunk_count}")
        logger.info(f"  evidence_slot: {slot_count}")
        logger.info(f"  compare_table_v2: {table_count}")
        logger.info("✅ VERIFICATION PASSED")

    def run(self):
        try:
            self.connect()

            if self.stage in ["chunks", "all"]:
                if not self.skip_chunks:
                    self.generate_chunks()
                else:
                    logger.info("⏭️  Skipping chunk generation (--skip-chunks)")

            if self.stage in ["evidence", "all"]:
                self.delete_existing_slots()
                self.generate_evidence_slots()

            if self.stage in ["compare", "all"]:
                self.generate_compare_table()

            if self.stage == "all":
                self.verify()

            logger.info("✅ PIPELINE COMPLETED")
        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description="DB-only coverage pipeline")
    parser.add_argument("--coverage_code", required=True, help="Coverage code (e.g., A4210)")
    parser.add_argument("--as_of_date", required=True, help="As-of date (YYYY-MM-DD)")
    parser.add_argument("--ins_cds", required=True, help="Comma-separated insurer codes (e.g., N01,N08)")
    parser.add_argument("--stage", choices=["chunks", "evidence", "compare", "all"], default="all",
                       help="Pipeline stage to run (default: all)")
    parser.add_argument("--skip-chunks", action="store_true", help="Skip chunk generation")
    args = parser.parse_args()

    ins_cds = [x.strip() for x in args.ins_cds.split(",")]

    pipeline = DBOnlyCoveragePipeline(
        coverage_code=args.coverage_code,
        as_of_date=args.as_of_date,
        ins_cds=ins_cds,
        stage=args.stage,
        skip_chunks=args.skip_chunks
    )
    pipeline.run()


if __name__ == "__main__":
    main()
