"""
STEP NEXT-45-D: Extractor V3 with Fingerprint Gate

Constitutional upgrades (45-D):
- Manifest-driven execution (--manifest flag)
- PDF fingerprint gate (exit code 2 on mismatch)
- Reproducibility enforcement (Profile regeneration required on PDF change)
- Variant support (db: under40/over41, lotte: male/female)

Previous enhancements (45-C-β):
1. Profile-based column mapping (handles KB row-number column offset)
2. Improved row filtering (totals, disclaimers, noise)
3. Evidence-backed extraction
4. Full parity with baseline coverage counts (target: 95%+)
5. Hybrid layout extractor (PyMuPDF text blocks + regex parsing)
6. Auto-trigger: switches to hybrid mode if >30% coverage names are empty
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pdfplumber

from pipeline.step1_summary_first.hybrid_layout import (
    extract_summary_rows_hybrid,
    detect_summary_pages,
)
from pipeline.step1_summary_first.pdf_fingerprint import (
    compute_pdf_fingerprint,
    fingerprints_match
)
from pipeline.step1_summary_first.detail_extractor import (
    DetailTableExtractor,
    match_summary_to_detail
)
from pipeline.step1_summary_first.product_variant_extractor import (
    ProductVariantExtractor,
    extract_insurer_code
)
from pipeline.step1_summary_first.coverage_semantics import (
    extract_coverage_semantics,
    get_evidence_requirements
)

logger = logging.getLogger(__name__)


@dataclass
class ProposalFact:
    """Proposal fact (raw text only, no inference)"""
    coverage_name_raw: str
    proposal_facts: Dict[str, Any]


class ExtractorV3:
    """Profile-based summary-first extractor + fingerprint gate (45-D)"""

    def __init__(self, insurer: str, pdf_path: Path, profile_path: Path, variant: str = "default"):
        self.insurer = insurer
        self.pdf_path = pdf_path
        self.profile_path = profile_path
        self.variant = variant
        self.profile = self._load_profile()

        # STEP NEXT-45-D: Fingerprint gate (HARD GATE)
        self._verify_fingerprint()

        # STEP NEXT-61: Extract product and variant identity (GATE-1, GATE-2)
        self._extract_product_variant_identity()

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile JSON"""
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _verify_fingerprint(self):
        """
        STEP NEXT-45-D: Fingerprint gate (HARD GATE)

        Verify that the current PDF matches the profile's fingerprint.
        If mismatch, abort execution with exit code 2.

        Constitutional rule:
        - Profile must be regenerated when input PDF changes
        - This gate enforces reproducibility
        """
        # Check if profile has fingerprint field (backward compat)
        if "pdf_fingerprint" not in self.profile:
            logger.error(
                f"{self.insurer} ({self.variant}): Profile missing 'pdf_fingerprint' field. "
                f"This profile was generated with old builder (< 45-D). "
                f"Run profile_builder_v3 with manifest to regenerate."
            )
            sys.exit(2)

        # Compute fingerprint of current PDF
        current_fp = compute_pdf_fingerprint(str(self.pdf_path))
        profile_fp = self.profile["pdf_fingerprint"]

        # Check match
        if not fingerprints_match(current_fp, profile_fp):
            logger.error(
                f"{self.insurer} ({self.variant}): Profile fingerprint mismatch.\n"
                f"Current PDF fingerprint:\n"
                f"  - file_size_bytes: {current_fp['file_size_bytes']}\n"
                f"  - page_count: {current_fp['page_count']}\n"
                f"  - sha256_first_2mb: {current_fp['sha256_first_2mb']}\n"
                f"  - source_basename: {current_fp['source_basename']}\n"
                f"Profile fingerprint:\n"
                f"  - file_size_bytes: {profile_fp['file_size_bytes']}\n"
                f"  - page_count: {profile_fp['page_count']}\n"
                f"  - sha256_first_2mb: {profile_fp['sha256_first_2mb']}\n"
                f"  - source_basename: {profile_fp['source_basename']}\n\n"
                f"Profile fingerprint mismatch. Run profile_builder_v3 with the current manifest first."
            )
            sys.exit(2)

        logger.info(
            f"{self.insurer} ({self.variant}): Fingerprint verification passed "
            f"(sha256: {current_fp['sha256_first_2mb'][:16]}...)"
        )

    def _extract_product_variant_identity(self):
        """
        STEP NEXT-61: Extract product and variant identity (GATE-1, GATE-2)

        Constitutional rules:
        - Product name = ONLY from page 1 of proposal PDF
        - Variant context = ONLY from "상품명 바로 아래 블록"
        - NO inference from file names
        - Explicit "default" when variant not found

        Sets:
            self.product_identity: Dict with product/variant/context fields
            self.insurer_key: str
            self.ins_cd: str
        """
        try:
            extractor = ProductVariantExtractor(
                insurer=self.insurer,
                pdf_path=self.pdf_path,
                variant_hint=self.variant  # For validation only
            )
            identity = extractor.extract()

            # Store identity
            self.product_identity = identity

            # Set insurer identifiers
            self.insurer_key = self.insurer.lower()
            self.ins_cd = extract_insurer_code(self.insurer)

            # GATE-1: Product gate (HARD GATE)
            if not identity["product"]["product_name_raw"]:
                logger.error(
                    f"{self.insurer}: Product name not found in page 1 (GATE-1 FAIL)"
                )
                sys.exit(2)

            if not identity["product"]["product_key"]:
                logger.error(
                    f"{self.insurer}: Product key generation failed (GATE-1 FAIL)"
                )
                sys.exit(2)

            # GATE-2: Variant gate (WARNING ONLY if hint mismatch)
            extracted_variant = identity["variant"]["variant_key"]
            if self.variant != "default" and extracted_variant != self.variant:
                logger.warning(
                    f"{self.insurer}: Variant mismatch (GATE-2 WARNING) - "
                    f"Expected: {self.variant}, Extracted: {extracted_variant}. "
                    f"Using extracted value (file name hint is reference only)."
                )

            logger.info(
                f"{self.insurer}: Product identity extracted - "
                f"product_key: {identity['product']['product_key']}, "
                f"variant_key: {extracted_variant}"
            )

        except Exception as e:
            logger.error(
                f"{self.insurer}: Product/Variant extraction failed (GATE-1/2 FAIL): {e}"
            )
            sys.exit(2)

    def extract(self) -> List[ProposalFact]:
        """
        Extract proposal facts with summary-first SSOT

        STEP NEXT-67D: Also extract DETAIL table (보장/보상내용) if exists
        """
        summary_exists = self.profile["summary_table"]["exists"]

        if not summary_exists:
            logger.error(f"{self.insurer}: No summary table in profile")
            raise RuntimeError(f"{self.insurer}: Summary table required but not found in profile v3")

        logger.info(f"{self.insurer}: Extracting from summary table (SSOT)")
        summary_facts = self._extract_from_summary()

        # STEP NEXT-67D: Extract DETAIL table and match to summary
        detail_extractor = DetailTableExtractor(self.pdf_path, self.profile, self.insurer)
        detail_facts = detail_extractor.extract_detail_facts()

        if detail_facts:
            # Convert ProposalFact objects to dicts for matching
            summary_dicts = [
                {
                    "coverage_name_raw": fact.coverage_name_raw,
                    "proposal_facts": fact.proposal_facts
                }
                for fact in summary_facts
            ]

            # Match and enrich
            enriched_dicts = match_summary_to_detail(summary_dicts, detail_facts)

            # Convert back to ProposalFact objects
            # Note: ProposalFact is a simple dataclass, so we need to handle the new field
            # For now, we'll return dicts and update the dataclass later
            return enriched_dicts
        else:
            # No detail facts: add null placeholder to all summary facts
            summary_dicts = [
                {
                    "coverage_name_raw": fact.coverage_name_raw,
                    "proposal_facts": fact.proposal_facts,
                    "proposal_detail_facts": None
                }
                for fact in summary_facts
            ]
            return summary_dicts

    def _extract_from_summary(self) -> List[ProposalFact]:
        """
        Extract facts from summary tables using profile column map

        STEP NEXT-45-C-β-4 P0-2: Per-signature hybrid-first logic for Pass B
        """
        facts = []

        # STEP NEXT-45-C-β-4: Separate primary and variant signatures for targeted extraction
        primary_sigs = self.profile["summary_table"].get("primary_signatures", [])
        variant_sigs = self.profile["summary_table"].get("variant_signatures", [])

        # Fallback for backward compatibility
        if not primary_sigs and not variant_sigs:
            all_sigs = self.profile["summary_table"]["table_signatures"]
            primary_sigs = all_sigs
            variant_sigs = []

        logger.info(f"{self.insurer}: Extracting from {len(primary_sigs)} primary + {len(variant_sigs)} variant signatures")

        # Process primary signatures (Pass A) - use standard extraction first
        facts.extend(self._extract_signatures(primary_sigs, mode="standard_first"))

        # Process variant signatures (Pass B) - use hybrid-first extraction
        facts.extend(self._extract_signatures(variant_sigs, mode="hybrid_first"))

        logger.info(f"{self.insurer}: Extracted {len(facts)} facts from summary tables")
        return facts

    def _extract_signatures(self, signatures: List[Dict], mode: str) -> List[ProposalFact]:
        """
        Extract facts from signatures with specified mode

        mode: "standard_first" or "hybrid_first"
        """
        facts = []

        if not signatures:
            return facts

        logger.info(f"{self.insurer}: Processing {len(signatures)} signatures in mode={mode}")

        if mode == "hybrid_first":
            # STEP NEXT-45-C-β-4 P0-2: Hybrid-first for Pass B
            # Try hybrid extraction first, fallback to standard only if hybrid returns 0 rows
            hybrid_facts = self._extract_signatures_hybrid(signatures)

            if len(hybrid_facts) > 0:
                logger.info(f"{self.insurer}: Hybrid extraction succeeded with {len(hybrid_facts)} facts")
                facts = hybrid_facts
            else:
                logger.warning(f"{self.insurer}: Hybrid extraction returned 0 facts, falling back to standard")
                facts = self._extract_signatures_standard(signatures)

        elif mode == "standard_first":
            # Standard extraction with auto-trigger to hybrid if >30% empty coverage names
            standard_facts = self._extract_signatures_standard(signatures)

            # STEP NEXT-45-C-β-5: Check profile extraction_config for force_standard_extraction
            extraction_config = self.profile.get("extraction_config", {})
            force_standard = extraction_config.get("force_standard_extraction", False)

            if force_standard:
                logger.info(
                    f"{self.insurer}: force_standard_extraction=True, skipping hybrid trigger check. "
                    f"Reason: {extraction_config.get('reason', 'N/A')}"
                )
                facts = standard_facts
            else:
                # Check if we should trigger hybrid
                should_use_hybrid = self._should_trigger_hybrid(signatures)

                if should_use_hybrid:
                    logger.warning(f"{self.insurer}: Triggering hybrid extraction (empty coverage ratio > 30%)")
                    hybrid_facts = self._extract_signatures_hybrid(signatures)
                    facts = hybrid_facts
                else:
                    facts = standard_facts

        else:
            raise ValueError(f"Unknown extraction mode: {mode}")

        return facts

    def _should_trigger_hybrid(self, signatures: List[Dict]) -> bool:
        """Check if we should trigger hybrid extraction based on empty coverage ratio"""
        with pdfplumber.open(self.pdf_path) as pdf:
            total_data_rows = 0
            empty_coverage_rows = 0

            for sig in signatures:
                page = sig["page"]
                table_index = sig["table_index"]
                column_map = sig["column_map"]
                header_row_idx = sig["header_row_index"]

                # Extract table
                page_obj = pdf.pages[page - 1]
                tables = page_obj.extract_tables()

                if table_index >= len(tables):
                    continue

                table = tables[table_index]

                # Check raw table data (before filtering)
                coverage_col = column_map.get("coverage_name")
                if coverage_col is None:
                    continue

                data_rows = table[header_row_idx + 1:]
                for row in data_rows:
                    if coverage_col < len(row):
                        total_data_rows += 1
                        coverage_text = str(row[coverage_col]).strip() if row[coverage_col] else ""
                        if not coverage_text or coverage_text.lower() in ["none", "null", ""]:
                            empty_coverage_rows += 1

            # Auto-trigger: if >30% coverage names are empty in raw table data
            if total_data_rows > 0:
                empty_ratio = empty_coverage_rows / total_data_rows
                logger.info(
                    f"{self.insurer}: Raw table check: {total_data_rows} data rows, "
                    f"{empty_coverage_rows} empty coverage names ({empty_ratio * 100:.1f}%)"
                )

                return empty_ratio > 0.30

        return False

    def _extract_signatures_standard(self, signatures: List[Dict]) -> List[ProposalFact]:
        """Standard table extraction from signatures"""
        facts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for sig in signatures:
                page = sig["page"]
                table_index = sig["table_index"]
                column_map = sig["column_map"]
                row_rules = sig["row_rules"]
                header_row_idx = sig["header_row_index"]

                # STEP NEXT-45-C-β-4 P0-2: Skip standard extraction if column_map has no coverage_name
                if column_map.get("coverage_name") is None:
                    logger.warning(
                        f"{self.insurer} page {page} table {table_index}: "
                        f"column_map missing coverage_name, skipping standard extraction"
                    )
                    continue

                # Extract table
                page_obj = pdf.pages[page - 1]
                tables = page_obj.extract_tables()

                if table_index >= len(tables):
                    logger.warning(
                        f"{self.insurer} page {page}: Table index {table_index} out of range "
                        f"(total: {len(tables)})"
                    )
                    continue

                table = tables[table_index]

                # Extract facts from table
                page_facts = self._extract_facts_from_table(
                    table, column_map, row_rules, header_row_idx, page, table_index
                )
                facts.extend(page_facts)

        return facts

    def _extract_signatures_hybrid(self, signatures: List[Dict]) -> List[ProposalFact]:
        """Hybrid extraction from signatures"""
        facts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for sig in signatures:
                page = sig["page"]
                table_index = sig["table_index"]

                # Get table bbox
                page_obj = pdf.pages[page - 1]
                tables_info = page_obj.find_tables()

                if table_index >= len(tables_info):
                    logger.warning(
                        f"{self.insurer} page {page}: Table index {table_index} out of range "
                        f"for find_tables (total: {len(tables_info)})"
                    )
                    continue

                table_bbox = tables_info[table_index].bbox

                # Extract rows using hybrid approach
                rows = extract_summary_rows_hybrid(
                    self.pdf_path, page - 1, table_bbox
                )

                logger.info(
                    f"{self.insurer} page {page}: Hybrid extracted {len(rows)} rows from table {table_index}"
                )

                # Convert hybrid rows to ProposalFacts
                for row in rows:
                    # STEP NEXT-66-A: Extract coverage semantics
                    coverage_semantics = extract_coverage_semantics(row.coverage_name_raw)

                    # STEP NEXT-66-C: Determine evidence requirements
                    evidence_requirements = get_evidence_requirements(row.coverage_name_raw)

                    fact = ProposalFact(
                        coverage_name_raw=row.coverage_name_raw,
                        proposal_facts={
                            "coverage_amount_text": row.amount_text,
                            "premium_text": row.premium_text,
                            "period_text": row.period_text,
                            "payment_method_text": None,

                            # STEP NEXT-66-A: Include coverage semantics
                            "coverage_semantics": coverage_semantics,

                            # STEP NEXT-66-C: Include evidence requirements
                            "evidence_requirements": evidence_requirements,

                            "evidences": [
                                {
                                    "doc_type": "가입설계서",
                                    "page": row.page,
                                    "y0": row.y0,
                                    "y1": row.y1,
                                    "extraction_mode": "hybrid"
                                }
                            ]
                        }
                    )
                    facts.append(fact)

        return facts

    def _extract_facts_from_table(
        self,
        table: List[List[Any]],
        column_map: Dict[str, Any],
        row_rules: Dict[str, Any],
        header_row_idx: int,
        page: int,
        table_idx: int
    ) -> List[ProposalFact]:
        """Extract facts from table using column map and row rules"""
        facts = []

        # Skip header rows
        data_rows = table[header_row_idx + 1:]

        for row_idx, row in enumerate(data_rows, start=header_row_idx + 2):
            # Apply row filters
            if self._should_skip_row(row, row_rules, column_map):
                continue

            # Extract fact from row
            fact = self._extract_fact_from_row(
                row, column_map, page, row_idx
            )

            if fact:
                facts.append(fact)

        return facts

    def _should_skip_row(
        self,
        row: List[Any],
        row_rules: Dict[str, Any],
        column_map: Dict[str, Any]
    ) -> bool:
        """Check if row should be skipped based on row rules"""
        # Get coverage name (accounting for row-number column offset)
        coverage_col = column_map.get("coverage_name")
        if coverage_col is None or coverage_col >= len(row):
            return True

        coverage_text = str(row[coverage_col]).strip() if row[coverage_col] else ""

        # Empty coverage name
        if not coverage_text:
            return True

        # Min/max length check
        min_len = row_rules.get("min_coverage_name_length", 2)
        max_len = row_rules.get("max_coverage_name_length", 100)
        if not (min_len <= len(coverage_text) <= max_len):
            return True

        # Total keywords
        if row_rules.get("skip_totals", True):
            total_keywords = row_rules.get("total_keywords", [])
            if any(kw in coverage_text for kw in total_keywords):
                logger.debug(f"{self.insurer}: Skipping total row: {coverage_text}")
                return True

        # Disclaimer keywords
        if row_rules.get("skip_disclaimers", True):
            disclaimer_keywords = row_rules.get("disclaimer_keywords", [])
            if any(kw in coverage_text for kw in disclaimer_keywords):
                logger.debug(f"{self.insurer}: Skipping disclaimer row: {coverage_text}")
                return True

        # Row number pattern (legacy, should not happen with v3 profiles)
        if re.match(r'^\d+\.?$', coverage_text) or re.match(r'^\d+\)$', coverage_text):
            logger.debug(f"{self.insurer}: Skipping row-number: {coverage_text}")
            return True

        return False

    def _extract_fact_from_row(
        self,
        row: List[Any],
        column_map: Dict[str, Any],
        page: int,
        row_idx: int
    ) -> Optional[ProposalFact]:
        """
        Extract single fact from table row

        STEP NEXT-66-A: Now includes coverage semantics extraction
        """
        # Get coverage name (accounting for row-number column)
        coverage_col = column_map.get("coverage_name")
        if coverage_col is None or coverage_col >= len(row):
            return None

        coverage_name_raw = str(row[coverage_col]).strip() if row[coverage_col] else ""
        if not coverage_name_raw:
            return None

        # STEP NEXT-66-A: Extract coverage semantics
        coverage_semantics = extract_coverage_semantics(coverage_name_raw)

        # STEP NEXT-66-C: Determine evidence requirements
        evidence_requirements = get_evidence_requirements(coverage_name_raw)

        # Extract other fields
        coverage_amount_text = self._safe_get_cell(row, column_map.get("coverage_amount"))
        premium_text = self._safe_get_cell(row, column_map.get("premium"))
        period_text = self._safe_get_cell(row, column_map.get("period"))

        # Build proposal fact
        proposal_fact = ProposalFact(
            coverage_name_raw=coverage_name_raw,
            proposal_facts={
                "coverage_amount_text": coverage_amount_text,
                "premium_text": premium_text,
                "period_text": period_text,
                "payment_method_text": None,  # Not in summary tables

                # STEP NEXT-66-A: Include coverage semantics
                "coverage_semantics": coverage_semantics,

                # STEP NEXT-66-C: Include evidence requirements
                "evidence_requirements": evidence_requirements,

                "evidences": [
                    {
                        "doc_type": "가입설계서",
                        "page": page,
                        "row_index": row_idx,
                        "raw_row": [str(cell) if cell else "" for cell in row]
                    }
                ]
            }
        )

        return proposal_fact

    def _safe_get_cell(self, row: List[Any], col_idx: Optional[int]) -> Optional[str]:
        """Safely get cell value as text"""
        if col_idx is None or col_idx >= len(row):
            return None

        cell_value = row[col_idx]
        if not cell_value:
            return None

        return str(cell_value).strip()


def main():
    """
    Extract Step1 v3 (STEP NEXT-56-R: --insurer support + lowercase enforcement)

    Usage:
        # Standard: single insurer without manifest
        python -m pipeline.step1_summary_first.extractor_v3 --insurer samsung

        # Legacy: manifest-based (still supported)
        python -m pipeline.step1_summary_first.extractor_v3 --manifest data/manifests/proposal_pdfs_v1.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Extractor V3 (STEP NEXT-56-R: --insurer support + lowercase)")
    parser.add_argument(
        "--manifest",
        type=str,
        help="Path to manifest JSON file (legacy mode)"
    )
    parser.add_argument(
        "--insurer",
        type=str,
        help="Insurer code (standard mode, e.g., samsung, kb)"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    profile_dir = Path(__file__).parent.parent.parent / "data" / "profile"
    output_dir = Path(__file__).parent.parent.parent / "data" / "scope_v3"
    output_dir.mkdir(parents=True, exist_ok=True)

    # STEP NEXT-56-R: Determine execution mode
    if args.insurer:
        # Standard mode: single insurer without manifest
        insurer_raw = args.insurer.strip().lower()  # Force lowercase
        variant = "default"

        # Auto-detect PDF path
        pdf_dir = Path(__file__).parent.parent.parent / "data" / "sources" / "insurers" / insurer_raw / "가입설계서"
        if not pdf_dir.exists():
            print(f"❌ PDF directory not found: {pdf_dir}")
            return 1

        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"❌ No PDF files found in: {pdf_dir}")
            return 1

        pdf_path = pdf_files[0]  # Use first PDF

        # Determine profile path
        profile_filename = f"{insurer_raw}_proposal_profile_v3.json"
        profile_path = profile_dir / profile_filename

        if not profile_path.exists():
            print(f"❌ Profile not found: {profile_path}")
            print(f"   Run profile_builder_v3 first: python -m pipeline.step1_summary_first.profile_builder_v3 --insurer {insurer_raw}")
            return 1

        # Create single-item manifest-like structure for processing
        items = [{
            "insurer": insurer_raw,
            "variant": variant,
            "pdf_path": str(pdf_path)
        }]

        print("\n" + "="*80)
        print("STEP NEXT-56-R: Extractor V3 (Standard --insurer mode)")
        print("="*80 + "\n")
        print(f"Insurer: {insurer_raw}")
        print(f"PDF: {pdf_path}")
        print(f"Profile: {profile_path}\n")

    elif args.manifest:
        # Legacy mode: manifest-based
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"❌ Manifest not found: {manifest_path}")
            return 1

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        print("\n" + "="*80)
        print("STEP NEXT-45-D: Extractor V3 (Legacy manifest mode)")
        print("="*80 + "\n")
        print(f"Manifest: {manifest_path}")
        print(f"Version: {manifest['version']}")
        print(f"Items: {len(manifest['items'])}\n")

        items = manifest["items"]
    else:
        print("❌ Either --insurer or --manifest must be specified")
        parser.print_help()
        return 1

    results = []

    for item in items:
        insurer = item["insurer"].strip().lower()  # STEP NEXT-56-R: Force lowercase
        variant = item.get("variant", "default")
        pdf_path = Path(item["pdf_path"])

        # Determine profile filename (lowercase)
        if variant == "default":
            profile_filename = f"{insurer}_proposal_profile_v3.json"
            output_filename = f"{insurer}_step1_raw_scope_v3.jsonl"
        else:
            profile_filename = f"{insurer}_{variant}_proposal_profile_v3.json"
            output_filename = f"{insurer}_{variant}_step1_raw_scope_v3.jsonl"

        profile_path = profile_dir / profile_filename

        if not pdf_path.exists():
            print(f"⚠️  {insurer} ({variant}): PDF not found - {pdf_path}")
            continue

        if not profile_path.exists():
            print(f"⚠️  {insurer} ({variant}): Profile not found - {profile_path}")
            continue

        print(f"📄 {insurer} ({variant}): Extracting proposal facts (fingerprint gate enabled)...")

        try:
            extractor = ExtractorV3(insurer, pdf_path, profile_path, variant)
            facts = extractor.extract()

            # STEP NEXT-66-FIX: Filter out standalone fragments
            fragments_output_path = output_dir / output_filename.replace("_step1_raw_scope_v3.jsonl", "_step1_fragments_v3.jsonl")

            # Separate fragments from valid facts
            valid_facts = []
            fragment_facts = []

            for fact in facts:
                semantics = fact.get("proposal_facts", {}).get("coverage_semantics", {})
                is_fragment = semantics.get("fragment_detected", False)

                # STEP NEXT-66-FIX: All fragments go to separate file
                if is_fragment:
                    fragment_facts.append(fact)
                else:
                    valid_facts.append(fact)

            # Save valid facts to main JSONL (STEP NEXT-61: with product/variant identity)
            output_path = output_dir / output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                for fact in valid_facts:
                    # STEP NEXT-61: Include product/variant identity in every row
                    fact_dict = {
                        # Identity fields (STEP NEXT-61)
                        "insurer_key": extractor.insurer_key,
                        "ins_cd": extractor.ins_cd,
                        "product": extractor.product_identity["product"],
                        "variant": extractor.product_identity["variant"],
                        "proposal_context": extractor.product_identity["proposal_context"],

                        # Coverage fields (existing)
                        "coverage_name_raw": fact["coverage_name_raw"],
                        "proposal_facts": fact["proposal_facts"],
                        "proposal_detail_facts": fact.get("proposal_detail_facts")
                    }
                    json.dump(fact_dict, f, ensure_ascii=False)
                    f.write('\n')

            # STEP NEXT-66-FIX: Save fragments to separate file
            if fragment_facts:
                with open(fragments_output_path, 'w', encoding='utf-8') as f:
                    for fact in fragment_facts:
                        fact_dict = {
                            "insurer_key": extractor.insurer_key,
                            "ins_cd": extractor.ins_cd,
                            "product": extractor.product_identity["product"],
                            "variant": extractor.product_identity["variant"],
                            "proposal_context": extractor.product_identity["proposal_context"],
                            "coverage_name_raw": fact["coverage_name_raw"],
                            "proposal_facts": fact["proposal_facts"],
                            "proposal_detail_facts": fact.get("proposal_detail_facts")
                        }
                        json.dump(fact_dict, f, ensure_ascii=False)
                        f.write('\n')

            # Read baseline for comparison
            baseline_path = Path(f"data/scope/{insurer}_scope.csv")
            baseline_count = 0
            if baseline_path.exists():
                with open(baseline_path, 'r') as f:
                    baseline_count = sum(1 for _ in f) - 1  # -1 for header

            delta = len(valid_facts) - baseline_count if baseline_count > 0 else 0
            delta_pct = (delta / baseline_count * 100) if baseline_count > 0 else 0

            status = "✅" if delta_pct >= -5 else ("⚠️" if delta_pct >= -15 else "❌")

            # STEP NEXT-66-FIX: Report fragment filtering
            if fragment_facts:
                print(f"   🔍 Fragment filtering: {len(fragment_facts)} fragments separated (standalone metadata)")
                print(f"      Fragment output: {fragments_output_path}")

            print(f"   {status} Extracted: {len(valid_facts)} valid facts (baseline: {baseline_count}, delta: {delta:+d} / {delta_pct:+.1f}%)")
            print(f"   ✓ Output: {output_path}\n")

            results.append({
                'insurer': insurer,
                'v3_count': len(valid_facts),  # STEP NEXT-66-FIX: Count only valid facts
                'baseline_count': baseline_count,
                'delta': delta,
                'delta_pct': delta_pct
            })

        except Exception as e:
            print(f"   ❌ {insurer}: Extraction failed - {e}\n")
            logger.exception(f"Extraction failed for {insurer} ({variant})")
            return 1

    print("="*80)
    print("✅ Step1 V3 extraction complete (FINGERPRINT-GATED)")
    print("="*80 + "\n")

    # Summary table
    print("Coverage Count Comparison (Baseline vs V3):")
    print("-" * 80)
    print(f"{'Insurer':<12} {'Baseline':>10} {'V3':>10} {'Delta':>10} {'Delta %':>10} {'Status':>8}")
    print("-" * 80)

    total_baseline = 0
    total_v3 = 0

    for r in results:
        status = "✅" if r['delta_pct'] >= -5 else ("⚠️" if r['delta_pct'] >= -15 else "❌")
        print(
            f"{r['insurer']:<12} {r['baseline_count']:>10} {r['v3_count']:>10} "
            f"{r['delta']:>+10} {r['delta_pct']:>+9.1f}% {status:>8}"
        )
        total_baseline += r['baseline_count']
        total_v3 += r['v3_count']

    print("-" * 80)
    total_delta = total_v3 - total_baseline
    total_delta_pct = (total_delta / total_baseline * 100) if total_baseline > 0 else 0
    total_status = "✅" if total_delta_pct >= -5 else ("⚠️" if total_delta_pct >= -15 else "❌")

    print(
        f"{'TOTAL':<12} {total_baseline:>10} {total_v3:>10} "
        f"{total_delta:>+10} {total_delta_pct:>+9.1f}% {total_status:>8}"
    )

    # Quality gate check
    print()
    if total_delta_pct >= -5:
        print("🎯 QUALITY GATE PASSED: Coverage count parity ≥95% (delta: {:.1f}%)".format(total_delta_pct))
    else:
        print("❌ QUALITY GATE FAILED: Coverage count parity <95% (delta: {:.1f}%)".format(total_delta_pct))

    # KB specific check
    kb_result = next((r for r in results if r['insurer'] == 'kb'), None)
    if kb_result and kb_result['v3_count'] > 0:
        print("🎯 KB GATE PASSED: KB extracted from summary table (count: {})".format(kb_result['v3_count']))
    elif kb_result:
        print("❌ KB GATE FAILED: KB extraction failed or returned 0 facts")

    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
