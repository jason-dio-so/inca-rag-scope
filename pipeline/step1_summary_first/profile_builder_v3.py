"""
STEP NEXT-45-D: Profile Builder V3 (Manifest-driven, Fingerprinted)

Constitutional upgrades (45-D):
- Manifest-driven execution (--manifest flag)
- PDF fingerprint provenance (file_size, page_count, sha256_first_2mb)
- Profile = generated artifact (not manual config)
- Variant support (db: under40/over41, lotte: male/female)

Previous enhancements (45-C-β-3):
1. KB row-number column detection (column 0 = row numbers)
2. Evidence-backed column mapping with offset detection
3. Improved summary table detection rules
4. Known anomalies documentation per insurer
5. Relaxed disqualify rule for "보장내용" header (summary-variant detection)
6. Two-tier signature storage: primary + variant
7. Expanded page scanning range (full document)
8. Profile completeness metrics with baseline page coverage
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timezone, timedelta

import pdfplumber
import fitz

from pipeline.step1_summary_first.pdf_fingerprint import compute_pdf_fingerprint

logger = logging.getLogger(__name__)


class ProfileBuilderV3:
    """Profile builder with KB column-offset detection + fingerprint provenance (45-D)"""

    # Summary table detection keywords
    COVERAGE_KEYWORDS = ['담보', '가입담보', '보장', '보장명']
    AMOUNT_KEYWORDS = ['가입금액']
    PREMIUM_KEYWORDS = ['보험료']
    PERIOD_KEYWORDS = ['납입', '만기', '납기', '보험기간']

    # Disqualifying keywords (detail table markers)
    DISQUALIFY_KEYWORDS = ['보장내용', '지급사유', '면책', '지급하지']

    # Builder version (STEP NEXT-45-D)
    BUILDER_VERSION = "step-next-45d"
    PROFILE_VERSION = "v3"

    def __init__(self, insurer: str, pdf_path: Path, variant: str = "default", manifest_path: str = None):
        self.insurer = insurer
        self.pdf_path = pdf_path
        self.variant = variant
        self.manifest_path = manifest_path

    def build_profile(self) -> Dict[str, Any]:
        """Build profile v3 with improved column detection (STEP NEXT-45-C-β-4: Two-pass detection)"""
        # Use pdfplumber for initial scan
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # STEP NEXT-45-C-β-4: Two-pass detection
            # Pass A: Keyword-based detection (existing logic)
            # Pass B: Pattern-based fallback detection (new)

            primary_candidates = []
            variant_candidates = []
            passA_pages = set()
            passB_pages = set()

            for page_num in range(1, total_pages + 1):
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 5:
                        continue

                    # Pass A: Keyword-based detection
                    is_summary, is_variant, evidence = self._is_summary_table(table, page_num, table_idx)

                    if is_summary:
                        candidate = {
                            'page': page_num,
                            'table_index': table_idx,
                            'table_data': table,
                            'evidence': evidence
                        }

                        if is_variant:
                            variant_candidates.append(candidate)
                        else:
                            primary_candidates.append(candidate)

                        passA_pages.add(page_num)

            # Pass B: Pattern-based fallback detection for pages NOT found in Pass A
            logger.info(f"{self.insurer}: Pass A found pages: {sorted(passA_pages)}")

            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num in range(1, total_pages + 1):
                    if page_num in passA_pages:
                        continue  # Skip pages already detected in Pass A

                    page = pdf.pages[page_num - 1]
                    tables = page.extract_tables()

                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 8:  # Pass B requires ≥8 rows
                            continue

                        # Pass B: Pattern-based detection
                        is_summary_like, evidence = self._is_summary_like_pattern_based(table, page_num, table_idx)

                        if is_summary_like:
                            candidate = {
                                'page': page_num,
                                'table_index': table_idx,
                                'table_data': table,
                                'evidence': evidence
                            }
                            variant_candidates.append(candidate)
                            passB_pages.add(page_num)

            logger.info(f"{self.insurer}: Pass B found pages: {sorted(passB_pages)}")

        # Build profile schema with two-tier signatures
        profile = self._build_profile_schema(primary_candidates, variant_candidates, total_pages)

        # Add detection metadata
        profile['detection_metadata'] = {
            'passA_pages': sorted(passA_pages),
            'passB_pages': sorted(passB_pages)
        }

        # STEP NEXT-45-D: Add provenance fields (MANDATORY)
        fingerprint = compute_pdf_fingerprint(str(self.pdf_path))
        kst = timezone(timedelta(hours=9))
        generated_at = datetime.now(kst).isoformat()

        profile_with_provenance = {
            # Provenance fields (MANDATORY for 45-D)
            "profile_version": self.PROFILE_VERSION,
            "builder_version": self.BUILDER_VERSION,
            "generated_at": generated_at,
            "source_manifest": self.manifest_path if self.manifest_path else None,
            "insurer": self.insurer,
            "variant": self.variant,
            "source_pdf_path": str(self.pdf_path),
            "pdf_fingerprint": fingerprint,
            # Original profile content
            **profile
        }

        # STEP NEXT-55A: Profile Lock - prevent column_map regression
        self._verify_profile_lock(profile_with_provenance)

        return profile_with_provenance

    def _verify_profile_lock(self, new_profile: Dict[str, Any]) -> None:
        """
        STEP NEXT-55A: Profile Lock - Change Control Gate

        Verify that column_map doesn't change for the same PDF fingerprint.
        If an existing profile has the same fingerprint but different column_map, exit with error.

        This prevents silent regression in column detection logic.
        """
        # Determine output path for this insurer/variant
        output_dir = Path(__file__).parent.parent.parent / "data" / "profile"
        if self.variant == "default":
            output_filename = f"{self.insurer}_proposal_profile_v3.json"
        else:
            output_filename = f"{self.insurer}_{self.variant}_proposal_profile_v3.json"
        output_path = output_dir / output_filename

        # Check if profile already exists
        if not output_path.exists():
            return  # New profile, no lock to verify

        # Load existing profile
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_profile = json.load(f)
        except Exception as e:
            logger.warning(f"{self.insurer}: Failed to load existing profile for lock verification: {e}")
            return

        # Compare fingerprints
        existing_fp = existing_profile.get('pdf_fingerprint', {})
        new_fp = new_profile.get('pdf_fingerprint', {})

        # If fingerprints don't match, this is a new PDF (allow changes)
        if existing_fp.get('sha256_first_2mb') != new_fp.get('sha256_first_2mb'):
            logger.info(f"{self.insurer}: PDF fingerprint changed (new PDF detected), allowing profile regeneration")
            return

        # Same fingerprint - verify column_map hasn't changed
        existing_column_maps = []
        new_column_maps = []

        for sig in existing_profile.get('summary_table', {}).get('primary_signatures', []):
            cm = sig.get('column_map', {})
            existing_column_maps.append((sig['page'], sig['table_index'], cm.get('coverage_name')))

        for sig in new_profile.get('summary_table', {}).get('primary_signatures', []):
            cm = sig.get('column_map', {})
            new_column_maps.append((sig['page'], sig['table_index'], cm.get('coverage_name')))

        # Compare column_maps
        if existing_column_maps != new_column_maps:
            logger.error(f"{self.insurer}: PROFILE LOCK VIOLATION!")
            logger.error(f"  Same PDF fingerprint ({new_fp.get('sha256_first_2mb', '')[:16]}...)")
            logger.error(f"  But column_map changed:")
            logger.error(f"    Existing: {existing_column_maps}")
            logger.error(f"    New:      {new_column_maps}")
            logger.error(f"  This indicates column detection logic regression.")
            logger.error(f"  Fix: Restore column detection logic or update lock if intentional.")
            import sys
            sys.exit(2)

        logger.info(f"{self.insurer}: Profile lock verified (column_map stable)")

    def _is_summary_table(self, table: List[List[Any]], page: int, table_idx: int) -> tuple[bool, bool, Optional[Dict]]:
        """
        Check if table is a summary table (primary or variant)

        Returns: (is_summary, is_variant, evidence_dict)
        - is_summary: True if table is summary (primary or variant)
        - is_variant: True if table is summary-variant (has disqualify keywords but meets relaxed criteria)
        - evidence_dict: Evidence data
        """
        # Extract header rows (first 3 rows)
        header_rows = table[:min(3, len(table))]
        header_text = ' '.join(
            str(cell) for row in header_rows for cell in row if cell
        )
        header_normalized = header_text.replace(' ', '').replace('\n', '')

        # Rule 1: Must have coverage keyword
        has_coverage = any(kw in header_normalized for kw in self.COVERAGE_KEYWORDS)
        if not has_coverage:
            return False, False, None

        # Rule 2: Must have amount keyword
        has_amount = any(kw in header_text for kw in self.AMOUNT_KEYWORDS)
        if not has_amount:
            return False, False, None

        # Rule 3: Must have premium OR period keyword
        has_premium = any(kw in header_text for kw in self.PREMIUM_KEYWORDS)
        has_period = any(kw in header_text for kw in self.PERIOD_KEYWORDS)
        if not (has_premium or has_period):
            return False, False, None

        # Rule 4: Check disqualifying keywords (STEP NEXT-45-C-β-3 relaxed)
        has_disqualify = any(kw in header_text for kw in self.DISQUALIFY_KEYWORDS)

        is_variant = False

        if has_disqualify:
            # STEP NEXT-45-C-β-3: Summary-variant detection
            # Allow if table has repetitive coverage pattern with valid data
            is_valid_variant = self._is_valid_summary_variant(table, header_text)

            if is_valid_variant:
                is_variant = True
            else:
                # Disqualify keywords without valid variant pattern
                return False, False, None

        # Rule 5: Minimum row count (relaxed for variants)
        min_rows = 5 if is_variant else 10
        if len(table) < min_rows:
            return False, False, None

        # Summary table detected
        evidence = {
            'page': page,
            'table_index': table_idx,
            'row_count': len(table),
            'col_count': len(table[0]) if table else 0,
            'header_snippet': header_text[:200],
            'sample_rows': [
                ' | '.join(str(cell) if cell else '' for cell in row)
                for row in table[2:5]  # Rows 3-5 as samples
            ],
            'is_variant': is_variant
        }

        return True, is_variant, evidence

    def _is_valid_summary_variant(self, table: List[List[Any]], header_text: str) -> bool:
        """
        Check if table with disqualify keywords is a valid summary-variant

        Criteria:
        1. Has coverage + amount + (premium OR period) keywords (already checked)
        2. Data rows have repetitive coverage pattern (≥10 rows)
        3. Amount/premium/period columns are mostly filled (>50% non-empty)
        4. REJECT if >30% of first column cells contain clause-like text (>100 chars or multi-line)
        """
        # Criterion 1: Already checked in _is_summary_table

        # Criterion 2: Minimum row count for variant pattern
        data_rows = table[3:]  # Skip header rows
        if len(data_rows) < 10:
            return False

        # Criterion 4: STEP NEXT-45-C-β-3: Reject detail tables with long clause descriptions
        # Check ENTIRE ROW (not just first column) for clause patterns
        # This handles both layouts: coverage in col 0 vs coverage in col 1 + clause in col 2
        clause_count = 0
        sample_data_rows = data_rows[:min(15, len(data_rows))]

        for row in sample_data_rows:
            # Join all cells in the row
            row_text = ' | '.join(str(cell).strip() if cell else '' for cell in row if cell)

            # Clause patterns (entire row check):
            # - Row contains very long clause text (>200 chars)
            # - Row contains multi-line text with newlines
            # - Row contains clause keywords: "진단 확정된 경우", "보장개시일 이후", "지급사유가 발생"
            has_long_text = len(row_text) > 200
            has_multiline = '\n' in row_text
            has_clause_keywords = any(kw in row_text for kw in ['진단 확정된 경우', '보장개시일 이후', '지급사유가 발생', '경우 가입금액 지급'])

            if has_long_text or has_multiline or has_clause_keywords:
                clause_count += 1

        clause_ratio = clause_count / len(sample_data_rows) if sample_data_rows else 0

        # If >30% of rows have clause-like text, this is a detail table, not summary-variant
        if clause_ratio > 0.30:
            return False

        # Criterion 3: Check data quality (amount/premium/period columns filled)
        # Detect amount pattern in cells
        amount_pattern = r'\d+[천백만억]*원'
        premium_pattern = r'\d+[,\d]*'
        period_pattern = r'\d+년|갱신|\d+세'

        # Sample data rows (rows 3-20)
        sample_rows = data_rows[:min(17, len(data_rows))]

        # Count rows with valid data patterns
        valid_data_count = 0
        for row in sample_rows:
            row_text = ' '.join(str(cell) for cell in row if cell)

            has_amount = bool(re.search(amount_pattern, row_text))
            has_premium = bool(re.search(premium_pattern, row_text))
            has_period = bool(re.search(period_pattern, row_text))

            # Row is valid if it has amount AND (premium OR period)
            if has_amount and (has_premium or has_period):
                valid_data_count += 1

        # Require >50% of sampled rows to have valid data
        validity_ratio = valid_data_count / len(sample_rows) if sample_rows else 0

        return validity_ratio > 0.5

    def _is_summary_like_pattern_based(self, table: List[List[Any]], page: int, table_idx: int) -> tuple[bool, Optional[Dict]]:
        """
        STEP NEXT-45-C-β-4: Pass B - Pattern-based fallback detection

        Detect summary-like tables based on data patterns (not keywords)

        Criteria (STEP NEXT-45-C-β-4 P0-3 adjusted):
        1. Data rows ≥ 7 (lowered from 8 for Hanwha/Lotte)
        2. Amount pattern presence ≥25% (lowered from 40%)
        3. Premium/Period pattern presence ≥20% (lowered from 30%)
        4. Korean text ratio ≥20% (lowered from 50% for Heungkuk/Hanwha/Lotte)
        5. NOT clause-heavy (서술문 비율 <35%, raised from 30%)
        """
        # Skip header rows (first 3)
        data_rows = table[3:] if len(table) > 3 else table

        if len(data_rows) < 7:  # STEP NEXT-45-C-β-4 P0-3: Lowered from 8 to 7
            return False, None

        # Pattern definitions
        amount_pattern = re.compile(r'\d{1,3}(,\d{3})*\s*원|\d+\s*만원|\d+\s*천만원|\d+\s*억원')
        premium_period_pattern = re.compile(r'\d+\s*년|세\s*만기|갱신|납입|보험료|\d{1,3}(,\d{3})+')
        korean_text_pattern = re.compile(r'[가-힣]{2,}')

        # Count pattern matches
        amount_matches = 0
        premium_period_matches = 0
        korean_text_matches = 0
        clause_matches = 0

        sample_rows = data_rows[:min(20, len(data_rows))]

        for row in sample_rows:
            row_text = ' '.join(str(cell).strip() if cell else '' for cell in row if cell)

            # Check amount pattern
            if amount_pattern.search(row_text):
                amount_matches += 1

            # Check premium/period pattern
            if premium_period_pattern.search(row_text):
                premium_period_matches += 1

            # Check Korean text in first 2 columns (coverage name candidates)
            first_cols_text = ' '.join(str(row[i]).strip() if i < len(row) and row[i] else '' for i in range(min(2, len(row))))
            if korean_text_pattern.search(first_cols_text):
                korean_text_matches += 1

            # Check clause patterns (서술문)
            clause_keywords = ['경우', '시', '합니다', '됩니다', '진단 확정된', '보장개시일 이후']
            if any(kw in row_text for kw in clause_keywords):
                clause_matches += 1

        # Calculate ratios
        amount_ratio = amount_matches / len(sample_rows) if sample_rows else 0
        premium_period_ratio = premium_period_matches / len(sample_rows) if sample_rows else 0
        korean_ratio = korean_text_matches / len(sample_rows) if sample_rows else 0
        clause_ratio = clause_matches / len(sample_rows) if sample_rows else 0

        # Decision criteria (STEP NEXT-45-C-β-4 P0-3 adjusted thresholds)
        is_summary_like = (
            amount_ratio >= 0.25 and  # Lowered from 0.40
            premium_period_ratio >= 0.20 and  # Lowered from 0.30
            korean_ratio >= 0.20 and  # Lowered from 0.50 (for Heungkuk/Hanwha/Lotte)
            clause_ratio < 0.35  # Raised from 0.30 (more lenient)
        )

        if not is_summary_like:
            return False, None

        # Generate evidence
        evidence = {
            'page': page,
            'table_index': table_idx,
            'row_count': len(table),
            'col_count': len(table[0]) if table else 0,
            'detection_method': 'pattern_based_passB',
            'pattern_scores': {
                'amount_ratio': round(amount_ratio, 2),
                'premium_period_ratio': round(premium_period_ratio, 2),
                'korean_ratio': round(korean_ratio, 2),
                'clause_ratio': round(clause_ratio, 2)
            },
            'header_snippet': ' '.join(str(cell) if cell else '' for row in table[:3] for cell in row)[:200],
            'sample_rows': [
                ' | '.join(str(cell) if cell else '' for cell in row)
                for row in table[3:6]  # Rows 4-6 as samples
            ],
            'is_variant': True  # Pass B results are always variant
        }

        return True, evidence

    def _build_profile_schema(self, primary_candidates: List[Dict], variant_candidates: List[Dict], total_pages: int) -> Dict[str, Any]:
        """Build profile JSON schema with two-tier signatures (STEP NEXT-45-C-β-3)"""
        all_candidates = primary_candidates + variant_candidates

        profile = {
            'insurer': self.insurer,
            'pdf_path': str(self.pdf_path),
            'total_pages': total_pages,
            'summary_table': {
                'exists': len(all_candidates) > 0,
                'pages': sorted(set(c['page'] for c in all_candidates)),
                'table_signatures': [],  # Combined: primary + variant (for backward compatibility)
                'primary_signatures': [],  # STEP NEXT-45-C-β-3: Primary summary tables
                'variant_signatures': []   # STEP NEXT-45-C-β-3: Summary-variant tables
            },
            'detail_table': {
                'exists': False,  # TBD
                'pages': []
            },
            'known_anomalies': [],
            'evidences': []
        }

        # Build primary signatures
        for candidate in primary_candidates:
            signature = self._build_table_signature(candidate)
            profile['summary_table']['primary_signatures'].append(signature)
            profile['summary_table']['table_signatures'].append(signature)  # Backward compatibility
            profile['evidences'].append(candidate['evidence'])

        # Build variant signatures
        for candidate in variant_candidates:
            signature = self._build_table_signature(candidate)
            profile['summary_table']['variant_signatures'].append(signature)
            profile['summary_table']['table_signatures'].append(signature)  # Backward compatibility
            profile['evidences'].append(candidate['evidence'])

        # Identify known anomalies
        profile['known_anomalies'] = self._identify_anomalies(all_candidates)

        return profile

    def _build_table_signature(self, candidate: Dict) -> Dict[str, Any]:
        """Build table signature with column mapping"""
        table = candidate['table_data']
        page = candidate['page']
        table_idx = candidate['table_index']

        # Detect header row (first row with keywords)
        header_row_idx = self._detect_header_row(table)
        header_row = table[header_row_idx] if header_row_idx < len(table) else []

        # Detect column map with offset awareness
        column_map = self._detect_column_map(header_row, table)

        # STEP NEXT-45-C-β-4 P0-1: For Pass B signatures, use content-based column_map
        is_passB = candidate.get('evidence', {}).get('detection_method') == 'pattern_based_passB'
        detection_pass = "B" if is_passB else "A"

        if is_passB:
            # Override column_map with content-pattern-based detection
            column_map = self._detect_column_map_passB(table, header_row_idx)

        # Detect row rules (totals, disclaimers, etc.)
        row_rules = self._detect_row_rules(table)

        signature = {
            'page': page,
            'table_index': table_idx,
            'row_count': len(table),
            'col_count': len(table[0]) if table else 0,
            'header_row_index': header_row_idx,
            'header_row': [str(cell) if cell else '' for cell in header_row],
            'column_map': column_map,
            'row_rules': row_rules,
            'evidence': candidate['evidence'],
            'detection_pass': detection_pass  # STEP NEXT-45-C-β-4: Track detection method
        }

        return signature

    def _detect_header_row(self, table: List[List[Any]]) -> int:
        """Detect which row is the header row"""
        for idx, row in enumerate(table[:5]):
            row_text = ' '.join(str(cell) for cell in row if cell)

            # Header row should have keyword
            has_keyword = any(
                kw in row_text
                for kw in self.COVERAGE_KEYWORDS + self.AMOUNT_KEYWORDS + self.PREMIUM_KEYWORDS
            )

            if has_keyword:
                return idx

        return 0  # Default to first row

    def _detect_category_columns(self, table: List[List[Any]], header_row: List[Any]) -> List[int]:
        """
        STEP NEXT-55A: Detect category columns (Samsung case)

        Category columns have:
        1. Low diversity: unique values < 30% of total rows
        2. Short text: avg length < 5 chars
        3. Category keywords: "진단", "입원", "수술", "사망", "후유장해", "기본계약", "납입"
        4. High sparsity: empty values > 50%

        Returns: List of column indices that are category columns
        """
        # Sample data rows (skip header, sample first 30 rows)
        data_rows = table[1:min(31, len(table))]
        if len(data_rows) < 5:
            return []

        # Determine column count
        col_counts = [len(row) for row in data_rows if row]
        if not col_counts:
            return []
        col_count = max(set(col_counts), key=col_counts.count)

        category_keywords = ['진단', '입원', '수술', '사망', '후유장해', '기본계약', '납입', '배상', '장해']
        category_columns = []

        for col_idx in range(min(3, col_count)):  # Only check first 3 columns
            # Extract column values
            col_values = []
            for row in data_rows:
                if col_idx < len(row):
                    val = str(row[col_idx]).strip() if row[col_idx] else ''
                    col_values.append(val)

            if not col_values:
                continue

            # Criterion 1: Empty ratio (sparsity)
            empty_count = sum(1 for val in col_values if not val)
            empty_ratio = empty_count / len(col_values)

            # Criterion 2: Unique diversity (measured against total rows, not just non-empty)
            # Category columns have few unique values spread across many rows
            non_empty_values = [val for val in col_values if val]
            if not non_empty_values:
                continue
            unique_values = set(non_empty_values)
            # Diversity = unique values / total rows (not non-empty rows)
            # This captures sparsity: 4 unique values across 30 rows = 13.3% diversity
            diversity_ratio = len(unique_values) / len(col_values)

            # Criterion 3: Average text length
            avg_length = sum(len(val) for val in non_empty_values) / len(non_empty_values) if non_empty_values else 0

            # Criterion 4: Category keyword presence
            keyword_match_count = sum(1 for val in non_empty_values if any(kw in val for kw in category_keywords))
            keyword_ratio = keyword_match_count / len(non_empty_values) if non_empty_values else 0

            # Decision: Is this a category column?
            is_category = (
                empty_ratio > 0.50 and  # Sparse (>50% empty)
                diversity_ratio < 0.30 and  # Low diversity (<30% unique)
                avg_length < 6 and  # Short text (<6 chars on average)
                keyword_ratio > 0.30  # Category keywords present (>30% of values)
            )

            if is_category:
                category_columns.append(col_idx)
                logger.info(f"{self.insurer}: Column {col_idx} identified as category column "
                           f"(empty: {empty_ratio:.1%}, diversity: {diversity_ratio:.1%}, "
                           f"avg_len: {avg_length:.1f}, keyword: {keyword_ratio:.1%})")

        return category_columns

    def _detect_coverage_name_column_by_content(
        self,
        table: List[List[Any]],
        category_column_indices: List[int],
        row_number_column_index: Optional[int]
    ) -> Optional[int]:
        """
        STEP NEXT-55A: Content-based coverage_name detection (Samsung fallback)

        When header is empty/missing, detect coverage_name column by analyzing cell content:
        - Korean text presence (>50% of rows)
        - Longer text (avg > 5 chars)
        - Not a category column, not a row-number column
        - Not an amount/premium/period column (no numeric patterns)

        Returns: Column index or None
        """
        # Sample data rows (skip header)
        data_rows = table[1:min(31, len(table))]
        if len(data_rows) < 5:
            return None

        # Determine column count
        col_counts = [len(row) for row in data_rows if row]
        if not col_counts:
            return None
        col_count = max(set(col_counts), key=col_counts.count)

        korean_pattern = re.compile(r'[가-힣]{3,}')  # Korean text (3+ chars)
        numeric_pattern = re.compile(r'\d+[,\d]*원?|^\d+$')  # Numbers/amounts

        candidate_scores = []

        for col_idx in range(min(5, col_count)):  # Check first 5 columns
            # Skip category/row-number columns
            if col_idx in category_column_indices:
                continue
            if col_idx == row_number_column_index:
                continue

            # Extract column values
            col_values = []
            for row in data_rows:
                if col_idx < len(row):
                    val = str(row[col_idx]).strip() if row[col_idx] else ''
                    col_values.append(val)

            if not col_values:
                continue

            # Score criteria
            non_empty = [v for v in col_values if v]
            if not non_empty:
                continue

            korean_count = sum(1 for v in non_empty if korean_pattern.search(v))
            korean_ratio = korean_count / len(non_empty)

            avg_length = sum(len(v) for v in non_empty) / len(non_empty)

            numeric_count = sum(1 for v in non_empty if numeric_pattern.search(v))
            numeric_ratio = numeric_count / len(non_empty)

            # Coverage name column should have:
            # - High Korean ratio (>50%)
            # - Long text (>5 chars avg)
            # - Low numeric ratio (<30%)
            score = 0.0
            if korean_ratio > 0.5:
                score += korean_ratio
            if avg_length > 5:
                score += (avg_length / 20.0)  # Normalize (max ~1.0)
            if numeric_ratio < 0.3:
                score += (1.0 - numeric_ratio)

            candidate_scores.append((col_idx, score, korean_ratio, avg_length, numeric_ratio))

        if not candidate_scores:
            return None

        # Sort by score (descending), then by leftmost column (ascending)
        candidate_scores.sort(key=lambda x: (-x[1], x[0]))
        best = candidate_scores[0]

        # Require minimum score threshold
        if best[1] < 1.0:
            return None

        logger.info(f"{self.insurer}: Content-based coverage_name candidate: col {best[0]} "
                   f"(score: {best[1]:.2f}, korean: {best[2]:.1%}, avg_len: {best[3]:.1f}, numeric: {best[4]:.1%})")

        return best[0]

    def _detect_column_map(self, header_row: List[Any], table: List[List[Any]]) -> Dict[str, Any]:
        """
        Detect column mapping with KB row-number offset detection

        Returns column_map with:
        - Column indices for each field
        - has_row_number_column flag
        - row_number_column_index
        """
        column_map = {
            'has_row_number_column': False,
            'row_number_column_index': None,
            'coverage_name': None,
            'coverage_amount': None,
            'premium': None,
            'period': None
        }

        # Check first column for row numbers (KB case)
        first_col_values = [
            str(row[0]).strip() if row and len(row) > 0 else ''
            for row in table[2:min(10, len(table))]  # Sample data rows
        ]

        # If >50% of first column values are pure numbers, it's a row-number column
        number_count = sum(1 for val in first_col_values if re.match(r'^\d+$', val))
        if number_count > len(first_col_values) * 0.5:
            column_map['has_row_number_column'] = True
            column_map['row_number_column_index'] = 0
            logger.info(f"{self.insurer}: Row-number column detected at index 0 (KB pattern)")

        # STEP NEXT-55A: Detect category columns (Samsung case)
        # Category columns have low diversity, short text, repeating category keywords, high sparsity
        category_column_indices = self._detect_category_columns(table, header_row)
        if category_column_indices:
            logger.info(f"{self.insurer}: Category columns detected at indices: {category_column_indices}")

        # Detect field columns (with offset if row-number column exists)
        col_offset = 1 if column_map['has_row_number_column'] else 0

        for idx, cell in enumerate(header_row):
            cell_text = str(cell).strip() if cell else ''
            cell_normalized = cell_text.replace(' ', '').replace('\n', '')

            # Coverage name column
            if any(kw in cell_normalized for kw in self.COVERAGE_KEYWORDS):
                # Apply offset for KB case
                if column_map['has_row_number_column'] and idx == 0:
                    # This is the row-number column header, skip
                    continue
                # STEP NEXT-55A: Skip category columns
                if idx in category_column_indices:
                    logger.info(f"{self.insurer}: Skipping category column {idx} for coverage_name mapping")
                    continue
                column_map['coverage_name'] = idx

            # Amount column
            if '가입금액' in cell_text:
                column_map['coverage_amount'] = idx

            # Premium column
            if '보험료' in cell_text:
                column_map['premium'] = idx

            # Period column
            if any(kw in cell_text for kw in self.PERIOD_KEYWORDS):
                column_map['period'] = idx

        # STEP NEXT-55A: Fallback - if coverage_name not found via header keywords,
        # use content-based detection (Samsung case: column 1 has empty header but actual coverage names)
        if column_map['coverage_name'] is None:
            logger.info(f"{self.insurer}: coverage_name not found via header keywords, using content-based fallback")
            coverage_name_col = self._detect_coverage_name_column_by_content(
                table,
                category_column_indices,
                column_map.get('row_number_column_index')
            )
            if coverage_name_col is not None:
                column_map['coverage_name'] = coverage_name_col
                logger.info(f"{self.insurer}: coverage_name detected at column {coverage_name_col} (content-based)")

        return column_map

    def _detect_column_map_passB(self, table: List[List[Any]], header_row_idx: int) -> Dict[str, Any]:
        """
        STEP NEXT-45-C-β-4 P0-1: Content-pattern-based column_map for Pass B

        Pass B has weak/missing headers, so we detect columns by analyzing cell content patterns.

        Returns column_map with:
        - Column indices for each field (based on content analysis)
        - mapping_method: "content_pattern"
        - mapping_confidence: 0-1 score
        """
        # Skip header rows and sample data rows (max 30 rows)
        data_rows = table[header_row_idx + 1:]
        sample_rows = data_rows[:min(30, len(data_rows))]

        if not sample_rows:
            return {
                'has_row_number_column': False,
                'row_number_column_index': None,
                'coverage_name': None,
                'coverage_amount_text': None,
                'premium_text': None,
                'period_text': None,
                'mapping_method': 'content_pattern',
                'mapping_confidence': 0.0
            }

        # Determine column count (use the mode of row lengths)
        col_counts = [len(row) for row in sample_rows if row]
        col_count = max(set(col_counts), key=col_counts.count) if col_counts else 0

        if col_count == 0:
            return {
                'has_row_number_column': False,
                'row_number_column_index': None,
                'coverage_name': None,
                'coverage_amount_text': None,
                'premium_text': None,
                'period_text': None,
                'mapping_method': 'content_pattern',
                'mapping_confidence': 0.0
            }

        # Initialize column scores
        amt_score = [0.0] * col_count
        prem_score = [0.0] * col_count
        period_score = [0.0] * col_count
        korean_score = [0.0] * col_count
        clause_score = [0.0] * col_count

        # Pattern definitions
        amt_pattern = re.compile(r'\d{1,3}(,\d{3})*\s*원|\d+\s*만원|\d+\s*천만원|\d+\s*억원|만원|천만원')
        prem_pattern = re.compile(r'\d{1,3}(,\d{3})+|보험료|월|납입')
        period_pattern = re.compile(r'\d+\s*년|세\s*만기|갱신|납입|만기|보험기간|납입기간')
        korean_pattern = re.compile(r'[가-힣]{2,}')
        clause_pattern = re.compile(r'경우|시|합니다|됩니다|진단 확정|보장개시일|면책|지급사유')

        # Analyze each column
        for row in sample_rows:
            for j in range(min(len(row), col_count)):
                cell = str(row[j]).strip() if row[j] else ''

                if not cell:
                    continue

                # Amount score
                if amt_pattern.search(cell):
                    amt_score[j] += 1

                # Premium score
                if prem_pattern.search(cell):
                    prem_score[j] += 1

                # Period score
                if period_pattern.search(cell):
                    period_score[j] += 1

                # Korean text score (coverage name candidate)
                korean_chars = len(korean_pattern.findall(cell))
                if korean_chars > 0:
                    korean_score[j] += korean_chars / 10.0  # Normalize

                # Clause score (negative signal for coverage_name)
                if clause_pattern.search(cell):
                    clause_score[j] += 1

        # Normalize scores
        num_rows = len(sample_rows)
        amt_score = [s / num_rows for s in amt_score]
        prem_score = [s / num_rows for s in prem_score]
        period_score = [s / num_rows for s in period_score]
        korean_score = [s / num_rows for s in korean_score]
        clause_score = [s / num_rows for s in clause_score]

        # Determine column assignments (deterministic with tie-breakers)
        column_map = {
            'has_row_number_column': False,
            'row_number_column_index': None,
            'coverage_name': None,
            'coverage_amount_text': None,
            'premium_text': None,
            'period_text': None,
            'mapping_method': 'content_pattern',
            'mapping_confidence': 0.0
        }

        # Coverage name = argmax(korean_score - clause_score), prefer leftmost
        coverage_name_scores = [korean_score[j] - clause_score[j] for j in range(col_count)]
        if max(coverage_name_scores) > 0.1:  # Minimum threshold
            # Find leftmost column with max score (tie-breaker)
            max_score = max(coverage_name_scores)
            for j in range(col_count):
                if coverage_name_scores[j] == max_score:
                    column_map['coverage_name'] = j
                    break

        # Amount column = argmax(amt_score)
        if max(amt_score) >= 0.25:  # Minimum 25% of rows
            column_map['coverage_amount_text'] = amt_score.index(max(amt_score))

        # Premium column = argmax(prem_score), must be different from amount
        if max(prem_score) >= 0.20:  # Minimum 20% of rows
            prem_idx = prem_score.index(max(prem_score))
            if prem_idx != column_map.get('coverage_amount_text'):
                column_map['premium_text'] = prem_idx
            else:
                # Use 2nd best if available
                prem_sorted = sorted(enumerate(prem_score), key=lambda x: x[1], reverse=True)
                if len(prem_sorted) > 1 and prem_sorted[1][1] >= 0.20:
                    column_map['premium_text'] = prem_sorted[1][0]

        # Period column = argmax(period_score), must be different from amount/premium
        if max(period_score) >= 0.20:  # Minimum 20% of rows
            period_idx = period_score.index(max(period_score))
            if period_idx not in [column_map.get('coverage_amount_text'), column_map.get('premium_text')]:
                column_map['period_text'] = period_idx
            else:
                # Use 2nd best if available
                period_sorted = sorted(enumerate(period_score), key=lambda x: x[1], reverse=True)
                for idx, score in period_sorted:
                    if score >= 0.20 and idx not in [column_map.get('coverage_amount_text'), column_map.get('premium_text')]:
                        column_map['period_text'] = idx
                        break

        # Calculate mapping confidence (fraction of fields successfully mapped)
        mapped_fields = sum([
            1 if column_map['coverage_name'] is not None else 0,
            1 if column_map['coverage_amount_text'] is not None else 0,
            1 if column_map['premium_text'] is not None else 0,
            1 if column_map['period_text'] is not None else 0
        ])
        column_map['mapping_confidence'] = mapped_fields / 4.0

        logger.info(f"{self.insurer} Pass B column_map: {column_map}")

        return column_map

    def _detect_row_rules(self, table: List[List[Any]]) -> Dict[str, Any]:
        """Detect row filtering rules (totals, disclaimers, etc.)"""
        rules = {
            'skip_totals': True,
            'skip_disclaimers': True,
            'total_keywords': ['합계', '총계', '보험료 합계', '보장보험료 합계'],
            'disclaimer_keywords': ['◆', '※', '가입한 담보', '반드시', '확인'],
            'min_coverage_name_length': 2,
            'max_coverage_name_length': 100
        }

        return rules

    def _identify_anomalies(self, summary_candidates: List[Dict]) -> List[str]:
        """Identify known structural anomalies"""
        anomalies = []

        # KB: Row-number column
        if self.insurer == 'kb':
            for candidate in summary_candidates:
                table = candidate['table_data']
                # Check if first column has numbers
                first_col_sample = [
                    str(row[0]).strip() if row and len(row) > 0 else ''
                    for row in table[2:7]
                ]
                if any(re.match(r'^\d+$', val) for val in first_col_sample):
                    anomalies.append(
                        "KB: Row-number column detected at index 0 "
                        "(coverage name in column 1, not 0)"
                    )
                    break

        # Hanwha: Merged header
        if self.insurer == 'hanwha':
            for candidate in summary_candidates:
                header_text = candidate['evidence']['header_snippet']
                if '가입담보 및 보장내용' in header_text:
                    anomalies.append(
                        "Hanwha: Merged header '가입담보 및 보장내용' detected "
                        "(requires Hanwha-specific filters from 44-γ)"
                    )
                    break

        # High table fragmentation
        if summary_candidates:
            avg_tables_per_page = len(summary_candidates) / len(set(c['page'] for c in summary_candidates))
            if avg_tables_per_page > 2.0:
                anomalies.append(
                    f"High table fragmentation: {avg_tables_per_page:.1f} summary tables/page "
                    f"(may require table merging logic)"
                )

        return anomalies


def main():
    """
    Generate profile v3 from manifest (STEP NEXT-45-D)

    Usage:
        python -m pipeline.step1_summary_first.profile_builder_v3 --manifest data/manifests/proposal_pdfs_v1.json
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Profile Builder V3 (manifest-based)")
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/proposal_pdfs_v1.json",
        help="Path to manifest JSON file"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load manifest
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return 1

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    print("\n" + "="*80)
    print("STEP NEXT-45-D: Profile Builder V3 (Manifest-driven, Fingerprinted)")
    print("="*80 + "\n")
    print(f"Manifest: {manifest_path}")
    print(f"Version: {manifest['version']}")
    print(f"Items: {len(manifest['items'])}\n")

    output_dir = Path(__file__).parent.parent.parent / "data" / "profile"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for item in manifest["items"]:
        insurer = item["insurer"]
        variant = item["variant"]
        pdf_path = Path(item["pdf_path"])

        if not pdf_path.exists():
            print(f"⚠️  {insurer} ({variant}): PDF not found - {pdf_path}")
            continue

        print(f"📄 {insurer} ({variant}): Building profile v3...")
        builder = ProfileBuilderV3(insurer, pdf_path, variant, str(manifest_path))
        profile = builder.build_profile()

        # Save profile (with variant in filename)
        if variant == "default":
            output_filename = f"{insurer}_proposal_profile_v3.json"
        else:
            output_filename = f"{insurer}_{variant}_proposal_profile_v3.json"

        output_path = output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        summary_exists = profile["summary_table"]["exists"]
        summary_pages = profile["summary_table"]["pages"]
        summary_count = len(profile["summary_table"]["table_signatures"])
        primary_count = len(profile["summary_table"]["primary_signatures"])
        variant_count = len(profile["summary_table"]["variant_signatures"])
        anomalies = len(profile["known_anomalies"])

        # Check for KB-specific success
        kb_success = ""
        if insurer == 'kb' and summary_exists:
            kb_success = " ✅ KB SUMMARY TABLE DETECTED!"

        # STEP NEXT-45-C-β-4: Show Pass A/B detection results
        passA_pages = profile.get('detection_metadata', {}).get('passA_pages', [])
        passB_pages = profile.get('detection_metadata', {}).get('passB_pages', [])
        fingerprint_short = profile["pdf_fingerprint"]["sha256_first_2mb"][:16]

        print(f"   ✓ Summary table: {summary_exists} (pages: {summary_pages}){kb_success}")
        print(f"   ✓ Summary signatures: {summary_count} (primary: {primary_count}, variant: {variant_count})")
        print(f"   ✓ Detection: Pass A pages {passA_pages}, Pass B pages {passB_pages}")
        print(f"   ✓ Fingerprint: {fingerprint_short}...")
        print(f"   ✓ Known anomalies: {anomalies}")
        if profile.get("known_anomalies"):
            for anomaly in profile["known_anomalies"]:
                print(f"      - {anomaly}")
        print(f"   ✓ Output: {output_path}\n")

        results.append({
            'insurer': insurer,
            'summary_exists': summary_exists,
            'summary_pages': summary_pages,
            'summary_count': summary_count,
            'primary_count': primary_count,
            'variant_count': variant_count
        })

    print("="*80)
    print("✅ Profile V3 generation complete (MANIFEST-DRIVEN, FINGERPRINTED)")
    print("="*80 + "\n")

    # Summary table
    print("Summary Table Detection Results:")
    print("-" * 80)
    print(f"{'Insurer':<12} {'Total':<8} {'Primary':<10} {'Variant':<10} {'Pages'}")
    print("-" * 80)
    for r in results:
        status = "✅" if r['summary_exists'] else "❌"
        pages_str = str(r['summary_pages'])
        print(f"{status} {r['insurer']:<10} {r['summary_count']:<8} {r['primary_count']:<10} {r['variant_count']:<10} {pages_str}")

    # KB gate check
    kb_result = next((r for r in results if r['insurer'] == 'kb'), None)
    if kb_result and kb_result['summary_exists']:
        print("\n🎯 HARD GATE PASSED: KB summary table detected (column-offset fix successful)")
    elif kb_result:
        print("\n❌ HARD GATE FAILED: KB summary table NOT detected")

    print()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
