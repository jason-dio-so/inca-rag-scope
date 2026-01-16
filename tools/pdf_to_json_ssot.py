#!/usr/bin/env python3
"""
PDF → JSON SSOT: One-time conversion of all insurance PDFs
Coverage-agnostic, insurer × doc_type based processing

Usage:
  python3 tools/pdf_to_json_ssot.py

Principles:
  - Coverage-agnostic (NO coverage_code)
  - Insurer × doc_type unit processing
  - Each PDF read ONLY ONCE
  - raw_text: NO summarization/processing
  - Split by paragraph/table units
  - Store in document_page_ssot table
"""

import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

import pdfplumber
import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Insurer directory mapping
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

# Document type normalization
DOC_TYPE_NORMALIZE = {
    "약관": "약관",
    "사업방법서": "사업방법서",
    "사업설명서": "사업방법서",  # Alias
    "상품요약서": "요약서",
    "쉬운요약서": "요약서",  # Alias
    "가입설계서": "가입설계서"
}

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "inca_ssot",
    "user": "postgres",
    "password": "postgres"
}


def sanitize_text(text: str) -> str:
    """Remove NUL bytes and other problematic characters from text"""
    if not text:
        return ""

    # Remove NUL bytes (0x00) which cause PostgreSQL errors
    text = text.replace('\x00', '')

    return text.strip()


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of text"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs by double newlines"""
    if not text:
        return []

    # Split by double newlines (paragraph breaks)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Filter out very short paragraphs (likely noise)
    return [p for p in paragraphs if len(p) >= 20]


def detect_section_title(text: str) -> str:
    """Attempt to detect section title from first line"""
    lines = text.split('\n')
    if not lines:
        return None

    first_line = lines[0].strip()

    # If first line is short and ends with certain patterns, treat as section title
    if len(first_line) < 100 and any(keyword in first_line for keyword in ['보험금', '담보', '보장', '특약', '계약', '지급', '면책']):
        return first_line

    return None


def extract_pdf_to_ssot(pdf_path: Path, ins_cd: str, doc_type: str, conn) -> Dict[str, int]:
    """
    Extract PDF content and insert into document_page_ssot

    Returns:
        Dict with stats: pages_processed, paragraphs_inserted, duplicates_skipped
    """
    stats = {"pages_processed": 0, "paragraphs_inserted": 0, "duplicates_skipped": 0, "errors": 0}
    cursor = conn.cursor()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"    Total pages: {total_pages}")

            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # Extract text from page
                    text = page.extract_text()
                    if not text or len(text.strip()) < 10:
                        continue

                    # Sanitize text (remove NUL bytes)
                    text = sanitize_text(text)
                    if not text or len(text) < 10:
                        continue

                    stats["pages_processed"] += 1

                    # Split into paragraphs
                    paragraphs = split_into_paragraphs(text)

                    for para in paragraphs:
                        # Sanitize paragraph text
                        para = sanitize_text(para)
                        if not para or len(para) < 20:
                            continue

                        # Detect section title (optional)
                        section_title = detect_section_title(para)

                        # Compute content hash
                        content_hash = compute_hash(para)

                        # Insert to DB (with deduplication via content_hash)
                        try:
                            cursor.execute("""
                                INSERT INTO document_page_ssot
                                (ins_cd, doc_type, source_pdf, page_start, page_end,
                                 section_title, raw_text, content_hash, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (ins_cd, doc_type, pdf_path.name, page_num, page_num,
                                  section_title, para, content_hash, datetime.now()))
                            stats["paragraphs_inserted"] += 1
                        except psycopg2.IntegrityError:
                            # Duplicate content_hash, skip
                            conn.rollback()
                            stats["duplicates_skipped"] += 1
                            continue

                    # Progress logging
                    if page_num % 100 == 0 or page_num == total_pages:
                        logger.info(f"      Progress: {page_num}/{total_pages} pages, {stats['paragraphs_inserted']} paragraphs inserted")

                except Exception as e:
                    logger.warning(f"      ⚠️  Error processing page {page_num}: {e}")
                    stats["errors"] += 1
                    continue

            # Commit after processing all pages
            conn.commit()
            logger.info(f"    ✅ Processed: {stats['pages_processed']} pages, {stats['paragraphs_inserted']} paragraphs, {stats['duplicates_skipped']} duplicates")

    except Exception as e:
        logger.error(f"    ❌ Failed to process {pdf_path.name}: {e}")
        conn.rollback()
        stats["errors"] += 1

    finally:
        cursor.close()

    return stats


def process_insurer(ins_cd: str, insurer_dir: str, conn) -> Dict[str, int]:
    """
    Process all PDFs for a single insurer

    Returns:
        Dict with aggregated stats
    """
    logger.info(f"\n📂 Processing insurer: {ins_cd} ({insurer_dir})")

    insurer_path = PROJECT_ROOT / "data" / "sources" / "insurers" / insurer_dir
    if not insurer_path.exists():
        logger.warning(f"  ⚠️  Insurer directory not found: {insurer_path}")
        return {"total_pdfs": 0, "total_paragraphs": 0}

    total_stats = {"total_pdfs": 0, "total_paragraphs": 0, "total_pages": 0, "total_errors": 0}

    # Find all PDF files in insurer directory
    pdf_files = sorted(insurer_path.rglob("*.pdf"))

    if not pdf_files:
        logger.warning(f"  ⚠️  No PDF files found for {ins_cd}")
        return total_stats

    logger.info(f"  Found {len(pdf_files)} PDF files")

    for pdf_path in pdf_files:
        # Determine doc_type from parent directory name
        doc_type_raw = pdf_path.parent.name
        doc_type = DOC_TYPE_NORMALIZE.get(doc_type_raw, doc_type_raw)

        logger.info(f"  📄 Processing: {pdf_path.name} (doc_type: {doc_type})")

        # Extract PDF to SSOT
        stats = extract_pdf_to_ssot(pdf_path, ins_cd, doc_type, conn)

        total_stats["total_pdfs"] += 1
        total_stats["total_paragraphs"] += stats["paragraphs_inserted"]
        total_stats["total_pages"] += stats["pages_processed"]
        total_stats["total_errors"] += stats["errors"]

    logger.info(f"✅ {ins_cd} complete: {total_stats['total_pdfs']} PDFs, {total_stats['total_pages']} pages, {total_stats['total_paragraphs']} paragraphs")

    return total_stats


def verify_ssot(conn) -> bool:
    """
    Verify document_page_ssot table after conversion

    Checks:
      - All 8 insurers have data
      - Each insurer has ≥4 doc_types
      - Total row count > 0
    """
    logger.info("\n🔍 Verifying document_page_ssot...")

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Check 1: Total row count
    cursor.execute("SELECT COUNT(*) as total FROM document_page_ssot")
    total_rows = cursor.fetchone()['total']
    logger.info(f"  Total rows: {total_rows}")

    if total_rows == 0:
        logger.error("  ❌ FAIL: No data in document_page_ssot")
        return False

    # Check 2: Insurers coverage
    cursor.execute("""
        SELECT ins_cd, COUNT(DISTINCT doc_type) as doc_types, COUNT(*) as rows
        FROM document_page_ssot
        GROUP BY ins_cd
        ORDER BY ins_cd
    """)
    insurer_stats = cursor.fetchall()

    logger.info(f"  Insurers with data: {len(insurer_stats)}/8")

    all_passed = True
    for row in insurer_stats:
        status = "✅" if row['doc_types'] >= 4 else "⚠️"
        logger.info(f"    {status} {row['ins_cd']}: {row['doc_types']} doc_types, {row['rows']} rows")
        if row['doc_types'] < 4:
            all_passed = False

    # Check 3: Doc_type distribution
    cursor.execute("""
        SELECT doc_type, COUNT(*) as rows
        FROM document_page_ssot
        GROUP BY doc_type
        ORDER BY doc_type
    """)
    doc_type_stats = cursor.fetchall()

    logger.info(f"\n  Doc_type distribution:")
    for row in doc_type_stats:
        logger.info(f"    {row['doc_type']}: {row['rows']} rows")

    cursor.close()

    if all_passed and total_rows > 0:
        logger.info("\n✅ VERIFICATION PASSED")
        return True
    else:
        logger.warning("\n⚠️  VERIFICATION PARTIAL")
        return False


def main():
    logger.info("=" * 80)
    logger.info("PDF → JSON SSOT: Full Reset Phase")
    logger.info("=" * 80)
    logger.info("Purpose: Convert all insurance PDFs to coverage-agnostic SSOT")
    logger.info("Scope: 약관, 사업방법서, 요약서, 가입설계서")
    logger.info("Principle: Each PDF read ONCE, NO coverage_code")
    logger.info("=" * 80)

    # Connect to DB
    conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    logger.info(f"\n🔌 Connecting to DB: {conn_str}")

    conn = psycopg2.connect(**DB_CONFIG)
    logger.info(f"✅ Connected to: {DB_CONFIG['dbname']}")

    # Clear existing data in document_page_ssot (optional)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM document_page_ssot")
    existing_rows = cursor.fetchone()[0]

    if existing_rows > 0:
        logger.info(f"\n🗑️  Clearing existing {existing_rows} rows from document_page_ssot...")
        cursor.execute("DELETE FROM document_page_ssot")
        conn.commit()
        logger.info("✅ Table cleared")

    cursor.close()

    # Process all insurers
    global_stats = {"total_insurers": 0, "total_pdfs": 0, "total_pages": 0, "total_paragraphs": 0}

    for ins_cd, insurer_dir in sorted(INSURER_DIR_MAP.items()):
        insurer_stats = process_insurer(ins_cd, insurer_dir, conn)

        global_stats["total_insurers"] += 1
        global_stats["total_pdfs"] += insurer_stats.get("total_pdfs", 0)
        global_stats["total_pages"] += insurer_stats.get("total_pages", 0)
        global_stats["total_paragraphs"] += insurer_stats.get("total_paragraphs", 0)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CONVERSION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Insurers processed: {global_stats['total_insurers']}/8")
    logger.info(f"PDFs processed: {global_stats['total_pdfs']}")
    logger.info(f"Pages processed: {global_stats['total_pages']}")
    logger.info(f"Paragraphs inserted: {global_stats['total_paragraphs']}")
    logger.info("=" * 80)

    # Verify
    verify_passed = verify_ssot(conn)

    # Close connection
    conn.close()

    if verify_passed:
        logger.info("\n✅ PIPELINE COMPLETED")
        return 0
    else:
        logger.warning("\n⚠️  PIPELINE COMPLETED WITH WARNINGS")
        return 1


if __name__ == "__main__":
    sys.exit(main())
