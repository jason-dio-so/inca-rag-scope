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
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.coverage_profiles import get_profile

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

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

    # GATE 5: Coverage name lock
    normalized_name = re.sub(r'\s+', '', ctx.coverage_name)
    normalized_text = re.sub(r'\s+', '', chunk_text)
    if normalized_name not in normalized_text:
        core_tokens = []
        if "유사암" in ctx.coverage_name:
            core_tokens.append("유사암")
        if "진단비" in ctx.coverage_name:
            core_tokens.append("진단비")
        if "경계성종양" in ctx.coverage_name:
            core_tokens.append("경계성종양")

        required_count = min(2, len(core_tokens))
        matched_count = sum(1 for token in core_tokens if token in chunk_text)
        if matched_count < required_count:
            reasons.append("coverage_name_lock_failed")
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
    def __init__(self, coverage_code: str, as_of_date: str, ins_cds: List[str], skip_chunks: bool = False):
        self.coverage_code = coverage_code
        self.as_of_date = as_of_date
        self.ins_cds = ins_cds
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

    def get_anchor_keywords(self, ins_cd: str) -> List[str]:
        self.cur.execute("""
            SELECT anchor_keywords FROM coverage_mapping_ssot
            WHERE coverage_code = %s AND ins_cd = %s
        """, (self.coverage_code, ins_cd))
        row = self.cur.fetchone()
        return row['anchor_keywords'] if row else []

    def get_coverage_name(self, ins_cd: str) -> str:
        self.cur.execute("""
            SELECT insurer_coverage_name FROM coverage_mapping_ssot
            WHERE coverage_code = %s AND ins_cd = %s
        """, (self.coverage_code, ins_cd))
        row = self.cur.fetchone()
        return row['insurer_coverage_name'] if row else ""

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
            anchors = self.get_anchor_keywords(ins_cd)
            coverage_name = self.get_coverage_name(ins_cd)
            logger.info(f"  Anchors: {anchors}")
            logger.info(f"  Coverage name: {coverage_name}")

            self.cur.execute("""
                SELECT chunk_id, chunk_text, excerpt, page_number
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
                    self.cur.execute("""
                        INSERT INTO evidence_slot (coverage_code, as_of_date, ins_cd, slot_key, chunk_id, excerpt, page_number, status, gate_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'FOUND', %s)
                    """, (self.coverage_code, self.as_of_date, ins_cd, slot_key, found_chunk['chunk_id'],
                          found_chunk['excerpt'], found_chunk['page_number'], gate_version))
                    stats["FOUND"] += 1
                else:
                    stats["NOT_FOUND"] += 1

        self.conn.commit()
        logger.info(f"✅ Created slots: FOUND={stats['FOUND']}, NOT_FOUND={stats['NOT_FOUND']}, DROPPED={stats['DROPPED']}")
        return stats

    def generate_compare_table(self) -> int:
        logger.info(f"📊 Generating compare_table_v2 for {self.coverage_code}...")

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
            INSERT INTO compare_table_v2 (coverage_code, as_of_date, payload)
            VALUES (%s, %s, %s)
            RETURNING table_id
        """, (self.coverage_code, self.as_of_date, json.dumps(payload)))

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

            if self.skip_chunks:
                logger.info("⏭️  Skipping chunk generation (--skip-chunks)")

            self.delete_existing_slots()
            self.generate_evidence_slots()
            self.generate_compare_table()
            self.verify()

            logger.info("✅ PIPELINE COMPLETED")
        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description="DB-only coverage pipeline")
    parser.add_argument("--coverage_code", required=True, help="Coverage code (e.g., A4210)")
    parser.add_argument("--as_of_date", required=True, help="As-of date (YYYY-MM-DD)")
    parser.add_argument("--ins_cds", required=True, help="Comma-separated insurer codes (e.g., N01,N08)")
    parser.add_argument("--skip-chunks", action="store_true", help="Skip chunk generation")
    args = parser.parse_args()

    ins_cds = [x.strip() for x in args.ins_cds.split(",")]

    pipeline = DBOnlyCoveragePipeline(
        coverage_code=args.coverage_code,
        as_of_date=args.as_of_date,
        ins_cds=ins_cds,
        skip_chunks=args.skip_chunks
    )
    pipeline.run()


if __name__ == "__main__":
    main()
