"""
STEP NEXT-45-C-β-5 P0-1: Diagnose Profile Signature Yield

Analyzes why Samsung extracted only 17 facts when profile shows 49 rows.
Outputs detailed signature-level diagnostics for all insurers.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import pdfplumber

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def load_profile(insurer: str) -> Dict[str, Any]:
    """Load profile v3 JSON"""
    profile_path = Path(f"data/profile/{insurer}_proposal_profile_v3.json")
    if not profile_path.exists():
        return {}

    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_extracted_facts(insurer: str) -> List[Dict]:
    """Load extracted facts from scope_v3"""
    scope_path = Path(f"data/scope_v3/{insurer}_step1_raw_scope_v3.jsonl")
    if not scope_path.exists():
        return []

    facts = []
    with open(scope_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                facts.append(json.loads(line))
    return facts


def count_table_rows(pdf_path: Path, page: int, table_index: int) -> int:
    """Count actual data rows in table (excluding header)"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_obj = pdf.pages[page - 1]
            tables = page_obj.extract_tables()

            if table_index >= len(tables):
                return 0

            table = tables[table_index]
            # Assuming first row is header
            return len(table) - 1 if len(table) > 1 else 0
    except Exception as e:
        logger.error(f"Error counting rows: {e}")
        return 0


def analyze_empty_coverage_ratio(pdf_path: Path, page: int, table_index: int, coverage_col: int) -> tuple:
    """Analyze empty coverage ratio in raw table data"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_obj = pdf.pages[page - 1]
            tables = page_obj.extract_tables()

            if table_index >= len(tables):
                return 0, 0, 0.0

            table = tables[table_index]
            # Skip header row
            data_rows = table[1:] if len(table) > 1 else []

            total_rows = len(data_rows)
            empty_rows = 0

            for row in data_rows:
                if coverage_col < len(row):
                    coverage_text = str(row[coverage_col]).strip() if row[coverage_col] else ""
                    if not coverage_text or coverage_text.lower() in ["none", "null", ""]:
                        empty_rows += 1

            empty_ratio = empty_rows / total_rows if total_rows > 0 else 0.0
            return total_rows, empty_rows, empty_ratio
    except Exception as e:
        logger.error(f"Error analyzing empty ratio: {e}")
        return 0, 0, 0.0


def diagnose_insurer(insurer: str) -> None:
    """Diagnose signature yield for one insurer"""
    logger.info(f"\n{'='*80}")
    logger.info(f"INSURER: {insurer.upper()}")
    logger.info(f"{'='*80}")

    profile = load_profile(insurer)
    if not profile:
        logger.warning(f"No profile found for {insurer}")
        return

    facts = load_extracted_facts(insurer)

    summary_table = profile.get("summary_table", {})
    if not summary_table.get("exists"):
        logger.warning(f"No summary table in profile")
        return

    pdf_path = Path(profile["pdf_path"])
    if not pdf_path.exists():
        logger.warning(f"PDF not found: {pdf_path}")
        return

    # Get signatures
    primary_sigs = summary_table.get("primary_signatures", [])
    variant_sigs = summary_table.get("variant_signatures", [])
    all_sigs = summary_table.get("table_signatures", [])

    # Fallback for backward compatibility
    if not primary_sigs and not variant_sigs:
        primary_sigs = all_sigs
        variant_sigs = []

    logger.info(f"\nProfile Summary:")
    logger.info(f"  Total pages: {profile['total_pages']}")
    logger.info(f"  Summary pages: {summary_table.get('pages', [])}")
    logger.info(f"  Primary signatures: {len(primary_sigs)}")
    logger.info(f"  Variant signatures: {len(variant_sigs)}")
    logger.info(f"  Detection metadata: {profile.get('detection_metadata', {})}")

    logger.info(f"\nExtraction Results:")
    logger.info(f"  Total extracted facts: {len(facts)}")

    # Count facts by page
    facts_by_page = {}
    facts_by_mode = {"standard": 0, "hybrid": 0, "unknown": 0}

    for fact in facts:
        evidences = fact.get("proposal_facts", {}).get("evidences", [])
        if evidences:
            page = evidences[0].get("page", -1)
            mode = evidences[0].get("extraction_mode", "unknown")

            facts_by_page[page] = facts_by_page.get(page, 0) + 1
            facts_by_mode[mode] = facts_by_mode.get(mode, 0) + 1

    logger.info(f"  Facts by page: {dict(sorted(facts_by_page.items()))}")
    logger.info(f"  Facts by mode: {facts_by_mode}")

    # Signature-level analysis
    logger.info(f"\n{'─'*80}")
    logger.info("Signature-Level Diagnostics:")
    logger.info(f"{'─'*80}")

    total_expected_rows = 0

    for i, sig in enumerate(primary_sigs + variant_sigs):
        is_primary = i < len(primary_sigs)
        sig_type = "PRIMARY" if is_primary else "VARIANT"

        page = sig["page"]
        table_index = sig["table_index"]
        row_count = sig.get("row_count", 0)
        col_count = sig.get("col_count", 0)
        detection_pass = sig.get("detection_pass", "?")
        column_map = sig.get("column_map", {})

        logger.info(f"\n[{sig_type}] Signature #{i+1}:")
        logger.info(f"  Page: {page}, Table Index: {table_index}")
        logger.info(f"  Detection Pass: {detection_pass}")
        logger.info(f"  Profile row_count: {row_count}, col_count: {col_count}")
        logger.info(f"  Column map:")
        logger.info(f"    coverage_name: {column_map.get('coverage_name')}")
        logger.info(f"    coverage_amount: {column_map.get('coverage_amount')}")
        logger.info(f"    premium: {column_map.get('premium')}")
        logger.info(f"    period: {column_map.get('period')}")

        # Count actual table rows in PDF
        actual_rows = count_table_rows(pdf_path, page, table_index)
        logger.info(f"  Actual table rows (in PDF): {actual_rows}")

        # Analyze empty coverage ratio
        coverage_col = column_map.get("coverage_name")
        if coverage_col is not None:
            total, empty, ratio = analyze_empty_coverage_ratio(pdf_path, page, table_index, coverage_col)
            logger.info(f"  Empty coverage analysis:")
            logger.info(f"    Total data rows: {total}")
            logger.info(f"    Empty coverage rows: {empty}")
            logger.info(f"    Empty ratio: {ratio*100:.1f}%")

            # Check if hybrid should be triggered
            should_hybrid = ratio > 0.30
            logger.info(f"    Should trigger hybrid? {should_hybrid} (threshold: >30%)")

        # Count extracted facts from this page
        extracted_from_page = facts_by_page.get(page, 0)
        logger.info(f"  Extracted facts from page {page}: {extracted_from_page}")

        # Evidence snippet
        evidence = sig.get("evidence", {})
        header_snippet = evidence.get("header_snippet", "")[:100]
        logger.info(f"  Header snippet: {header_snippet}...")

        total_expected_rows += row_count

    logger.info(f"\n{'─'*80}")
    logger.info(f"SUMMARY:")
    logger.info(f"  Total expected rows (from profile): {total_expected_rows}")
    logger.info(f"  Total extracted facts: {len(facts)}")
    logger.info(f"  Extraction rate: {len(facts) / total_expected_rows * 100:.1f}%" if total_expected_rows > 0 else "  Extraction rate: N/A")
    logger.info(f"{'─'*80}")


def main():
    """Diagnose all insurers with focus on Samsung and Hyundai"""
    insurers = ["samsung", "hyundai", "kb", "meritz", "hanwha", "heungkuk", "lotte", "db"]

    # Focus on Samsung first
    logger.info("\n" + "="*80)
    logger.info("PRIORITY DIAGNOSIS: SAMSUNG")
    logger.info("="*80)
    diagnose_insurer("samsung")

    logger.info("\n" + "="*80)
    logger.info("PRIORITY DIAGNOSIS: HYUNDAI")
    logger.info("="*80)
    diagnose_insurer("hyundai")

    # Then other insurers
    logger.info("\n" + "="*80)
    logger.info("OTHER INSURERS")
    logger.info("="*80)

    for insurer in insurers:
        if insurer not in ["samsung", "hyundai"]:
            diagnose_insurer(insurer)


if __name__ == "__main__":
    main()
