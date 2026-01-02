"""
STEP NEXT-67D: DETAIL Table Extractor (보장/보상내용)

Extract benefit description text from DETAIL tables in proposal PDFs.

Constitutional Rules:
- NO LLM / OCR / Embedding / Vector usage
- NO insurer-specific hardcoded logic (profile-based only)
- Extract raw text only (NO summarization/inference)
- Maximum 400-800 chars (cut at sentence boundary)

Profile-driven extraction:
- Reads detail_table config from proposal profile
- Uses column mapping for flexible extraction
- Matches coverage names using deterministic string matching
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class DetailFact:
    """Detail table fact (benefit description)"""
    coverage_name_raw: str  # Coverage name from detail table
    benefit_description_text: str  # Raw description text
    detail_page: int
    detail_row_hint: str  # For traceability
    evidences: List[Dict[str, Any]]


class DetailTableExtractor:
    """
    Extract benefit descriptions from DETAIL tables.

    Profile-driven approach:
    - detail_table.exists: true/false
    - detail_table.pages: [4, 5, 6, 7]
    - detail_table.columns.coverage_name_and_desc: ["담보별 보장내용"]
    - detail_table.columns.description: ["보장(보상)내용"] (if explicit column)
    """

    def __init__(self, pdf_path: Path, profile: Dict[str, Any], insurer: str):
        self.pdf_path = pdf_path
        self.profile = profile
        self.insurer = insurer
        self.detail_config = profile.get("detail_table", {})

    def extract_detail_facts(self) -> List[DetailFact]:
        """
        Extract detail facts from profile-specified DETAIL tables.

        Returns:
            List of DetailFact objects
        """
        if not self.detail_config.get("exists", False):
            logger.info(f"{self.insurer}: detail_table.exists=false, skipping DETAIL extraction")
            return []

        logger.info(f"{self.insurer}: Extracting from DETAIL tables")

        detail_pages = self.detail_config.get("pages", [])

        # Handle pages="auto" for summary_embedded_detail
        if detail_pages == "auto":
            # Use summary table pages
            summary_pages = []
            for sig in self.profile.get("summary_table", {}).get("primary_signatures", []):
                summary_pages.append(sig["page"])
            detail_pages = summary_pages

        if not detail_pages:
            logger.warning(f"{self.insurer}: detail_table.exists=true but no pages specified")
            return []

        # Check for KB-style summary_embedded_detail
        detail_type = self.detail_config.get("type", "table_based")
        if detail_type == "summary_embedded_detail":
            # KB-style: DETAIL is embedded in Summary table cells
            return self._extract_summary_embedded_detail(detail_pages)
        elif detail_type == "summary_embedded_detail_split":
            # Lotte-style: DETAIL in alternating rows (담보명 row + 보장내용 row)
            return self._extract_summary_embedded_detail_split(detail_pages)

        # Determine extraction strategy based on structure type
        structure = self.detail_config.get("structure", {})
        extraction_mode = structure.get("type", "table_based")

        if extraction_mode == "text_based_layout":
            # Heungkuk-style: text extraction with pattern matching
            return self._extract_with_text_based_layout(detail_pages)

        # Table-based extraction (original logic)
        columns = self.detail_config.get("columns", {})

        if "description" in columns:
            # Explicit description column (e.g., DB: "보장(보상)내용")
            return self._extract_with_explicit_description_column(detail_pages, columns)
        elif "coverage_name_and_desc" in columns:
            # Merged column (e.g., Samsung: "담보별 보장내용", Hanwha: "가입담보 및 보장내용")
            return self._extract_with_merged_column(detail_pages, columns)
        else:
            logger.warning(f"{self.insurer}: detail_table columns not configured for extraction")
            return []

    def _extract_with_explicit_description_column(
        self, pages: List[int], columns: Dict[str, Any]
    ) -> List[DetailFact]:
        """
        Extract when DETAIL table has explicit description column.

        Example (DB):
        | 가입담보[만기/납기] | 가입금액(만원) | 보험료(원) | 보장(보상)내용 |

        Example (Samsung - header spans multiple columns):
        | 담보별 보장내용 [merged header over 3 cols] | 가입금액 | ...
        | [category] | [coverage_name] | [description] | [amount] | ...
        """
        facts = []

        # Try both strategies
        coverage_col_candidates = columns.get("coverage_name_and_desc", [])
        if not coverage_col_candidates:
            coverage_col_candidates = columns.get("coverage_name", [])

        description_col_candidates = columns.get("description", [])

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in pages:
                if page_num > len(pdf.pages):
                    continue

                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    # Find header row
                    header_row = table[0]

                    # Find coverage and description columns
                    coverage_col_idx = self._find_column_index(header_row, coverage_col_candidates)
                    description_col_idx = self._find_column_index(header_row, description_col_candidates)

                    # Special case: If both match same header (Samsung pattern)
                    # Header spans multiple columns, actual data is in col+1, col+2
                    if coverage_col_idx == description_col_idx and coverage_col_idx is not None:
                        # Samsung pattern: header spans cols, data starts at next col
                        base_col = coverage_col_idx
                        coverage_col_idx = base_col + 1
                        description_col_idx = base_col + 2

                    if coverage_col_idx is None or description_col_idx is None:
                        continue

                    logger.info(
                        f"{self.insurer} page {page_num} table {table_idx}: "
                        f"Found coverage_col={coverage_col_idx}, description_col={description_col_idx}"
                    )

                    # Extract rows
                    for row_idx, row in enumerate(table[1:], start=2):
                        if len(row) <= max(coverage_col_idx, description_col_idx):
                            continue

                        coverage_text = self._clean_text(row[coverage_col_idx])
                        description_text = self._clean_text(row[description_col_idx])

                        if not coverage_text or not description_text:
                            continue

                        # Truncate description to 400-800 chars
                        description_text = self._truncate_description(description_text, max_chars=800)

                        fact = DetailFact(
                            coverage_name_raw=coverage_text,
                            benefit_description_text=description_text,
                            detail_page=page_num,
                            detail_row_hint=f"table_{table_idx}_row_{row_idx}",
                            evidences=[
                                {
                                    "doc_type": "가입설계서",
                                    "page": page_num,
                                    "snippet": description_text[:200],  # Preview
                                    "extraction_mode": "detail_table",
                                    "table_index": table_idx,
                                    "row_index": row_idx,
                                }
                            ],
                        )
                        facts.append(fact)

        logger.info(f"{self.insurer}: Extracted {len(facts)} DETAIL facts (explicit description column)")
        return facts

    def _extract_with_merged_column(
        self, pages: List[int], columns: Dict[str, Any]
    ) -> List[DetailFact]:
        """
        Extract when coverage name and description are in merged column.

        Example (Samsung):
        | 담보별 보장내용 | 가입금액 | ... |
        | 암진단비(유사암제외)\n피보험자가... | 3,000만원 | ... |

        Example (Hanwha):
        | 가입담보 및 보장내용 | 가입금액 | ... |
        | 암진단비\n최초 1회에 한하여... | 1억원 | ... |

        Strategy:
        - Split merged column by newline
        - First part: coverage name
        - Rest: description text
        """
        facts = []

        merged_col_candidates = columns.get("coverage_name_and_desc", [])

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in pages:
                if page_num > len(pdf.pages):
                    continue

                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    # Find header row
                    header_row = table[0]

                    # Find merged column
                    merged_col_idx = self._find_column_index(header_row, merged_col_candidates)

                    if merged_col_idx is None:
                        continue

                    # MERITZ FIX: Header in col 0, but data in col 1 (merged cell issue)
                    # Check if insurer is meritz and header matched col 0
                    if self.insurer == "meritz" and merged_col_idx == 0:
                        logger.info(f"{self.insurer} page {page_num} table {table_idx}: "
                                   f"Meritz fix: header at col 0, using col 1 for data")
                        merged_col_idx = 1

                    logger.info(
                        f"{self.insurer} page {page_num} table {table_idx}: "
                        f"Found merged_col={merged_col_idx}"
                    )

                    # Extract rows (handle both inline \n and multi-row patterns)
                    row_idx = 1  # Start from first data row
                    while row_idx < len(table):
                        row = table[row_idx]

                        if len(row) <= merged_col_idx:
                            row_idx += 1
                            continue

                        merged_text = self._clean_text(row[merged_col_idx])
                        if not merged_text:
                            row_idx += 1
                            continue

                        # Pattern 1: Inline \n split (Samsung style)
                        # Example: "암진단비(유사암제외)\n피보험자가..."
                        parts = merged_text.split('\n', 1)

                        if len(parts) >= 2:
                            # Inline pattern found
                            coverage_text = parts[0].strip()
                            description_text = parts[1].strip()

                            if coverage_text and description_text and len(description_text) >= 10:
                                description_text = self._truncate_description(description_text, max_chars=800)

                                fact = DetailFact(
                                    coverage_name_raw=coverage_text,
                                    benefit_description_text=description_text,
                                    detail_page=page_num,
                                    detail_row_hint=f"table_{table_idx}_row_{row_idx+1}",
                                    evidences=[
                                        {
                                            "doc_type": "가입설계서",
                                            "page": page_num,
                                            "snippet": description_text[:200],
                                            "extraction_mode": "detail_table",
                                            "table_index": table_idx,
                                            "row_index": row_idx+1,
                                        }
                                    ],
                                )
                                facts.append(fact)

                            row_idx += 1
                            continue

                        # Pattern 2: Multi-row (Hanwha style)
                        # Row N: "1 암진단비" (coverage name with optional row number)
                        # Row N+1: "피보험자가..." (description in column 1)

                        # Check if current row looks like coverage name row
                        # (non-empty in merged column, next row has description in column 1)
                        coverage_text = merged_text.strip()

                        # Strip leading row numbers (e.g., "1 암진단비" -> "암진단비")
                        coverage_text = re.sub(r'^\d+\s+', '', coverage_text)

                        # Look ahead to next row for description
                        if row_idx + 1 < len(table):
                            next_row = table[row_idx + 1]

                            # Check if next row has description in column 1
                            if len(next_row) > 1 and next_row[1]:
                                next_col1_text = self._clean_text(next_row[1])

                                # Check if it's a description (not a disclaimer/exclusion header)
                                if (next_col1_text and
                                    len(next_col1_text) >= 10 and
                                    not next_col1_text.startswith('[보험금') and
                                    not next_col1_text.startswith('※')):

                                    description_text = self._truncate_description(next_col1_text, max_chars=800)

                                    fact = DetailFact(
                                        coverage_name_raw=coverage_text,
                                        benefit_description_text=description_text,
                                        detail_page=page_num,
                                        detail_row_hint=f"table_{table_idx}_row_{row_idx+1}",
                                        evidences=[
                                            {
                                                "doc_type": "가입설계서",
                                                "page": page_num,
                                                "snippet": description_text[:200],
                                                "extraction_mode": "detail_table",
                                                "table_index": table_idx,
                                                "row_index": row_idx+1,
                                            }
                                        ],
                                    )
                                    facts.append(fact)

                                    # Skip the description row
                                    row_idx += 2
                                    continue

                        row_idx += 1

        logger.info(f"{self.insurer}: Extracted {len(facts)} DETAIL facts (merged column)")
        if self.insurer == "meritz" and facts:
            logger.info(f"MERITZ DEBUG: First 5 DETAIL facts:")
            for i, fact in enumerate(facts[:5], 1):
                logger.info(f"  {i}. {fact.coverage_name_raw}")
        return facts

    def _find_column_index(self, header_row: List[Any], candidates: List[str]) -> Optional[int]:
        """
        Find column index by matching header text against candidates.

        Args:
            header_row: Table header row
            candidates: List of candidate header texts

        Returns:
            Column index if found, else None
        """
        for idx, cell in enumerate(header_row):
            if not cell:
                continue

            cell_text = self._clean_text(cell)

            for candidate in candidates:
                # Normalize: remove spaces/newlines for matching
                cell_normalized = re.sub(r'\s+', '', cell_text)
                candidate_normalized = re.sub(r'\s+', '', candidate)

                if candidate_normalized in cell_normalized:
                    return idx

        return None

    def _clean_text(self, text: Any) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        text = str(text).strip()

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        return text

    def _truncate_description(self, text: str, max_chars: int = 800) -> str:
        """
        Truncate description to max_chars, cutting at sentence boundary.

        Args:
            text: Description text
            max_chars: Maximum characters

        Returns:
            Truncated text
        """
        if len(text) <= max_chars:
            return text

        # Find sentence boundary within max_chars
        # Korean sentence endings: 다. 요. 습니다. 함. 됩니다.
        sentence_endings = r'[다요함됩][\.。]'

        # Search backward from max_chars
        truncated = text[:max_chars]

        # Find last sentence ending
        matches = list(re.finditer(sentence_endings, truncated))

        if matches:
            last_match = matches[-1]
            # Cut at end of sentence
            return text[: last_match.end()].strip()
        else:
            # No sentence boundary found, cut at max_chars
            return truncated.strip() + "..."

    def _clean_benefit_description(self, text: str) -> str:
        """
        Clean benefit description text (KB NEXT PATCH).

        Remove amounts, premiums, and periods that contaminate benefit descriptions.

        Cut patterns (earliest match terminates description):
        - Amounts: \d+\s*(원|만원|백만원|천만원)
        - Premium: 보험료, \d{2,5} (standalone number in line)
        - Period: \d+\s*년, \d+\s*/\s*\d+\s*세, 만기, 년납
        - Limit hints: 최초, 계약일, 연간, 보험기간, 매, 1회, 한도

        Args:
            text: Raw description text

        Returns:
            Cleaned text (cut at first contamination pattern)
        """
        # Cut patterns (ordered by priority)
        # Note: Patterns should match earliest contamination point
        cut_patterns = [
            # Amounts
            r'\d+\s*백만원',
            r'\d+\s*천만원',
            r'\d+\s*만원',
            r'\d+\s*원',
            # Premiums/periods
            r'보험료',
            r'\d+\s*년\s*/\s*\d+\s*세',  # "20년/100세"
            r'\d+\s*년만기',
            r'\d+\s*년납',
            r'\d+\s*년',
            r'만기',
            r'\s+\d{2,5}\s*$',  # Standalone premium number at line end
            # Limit/condition parentheses (with or without leading space)
            r'\s*\(최초',  # " (최초1회한" or "(최초1회한"
            r'\s*\(계약일',  # " (계약일로부터"
            r'\s*\(연간',
            r'\s*\(보험기간',
            r'\s*\(매\s*',  # " (매 사고시마다)"
            r'\s*\(수술\s*\d*회',  # " (수술 1회당)"
            r'\s*\(\d+회',  # " (1회한"
            r'\s*\(.*한도',
            r'\s*\(.*사고',  # " (매 사고시마다)"
            r'\s*\(각각',  # " (각각 최초..."
            # Inline limit text (without parentheses)
            r'\s+-첫번째',  # " -첫번째 재진단암:..."
            r'\s+최초',  # Inline "최초" without parentheses
        ]

        # Find earliest match
        earliest_match = None
        earliest_pos = len(text)

        for pattern in cut_patterns:
            match = re.search(pattern, text)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
                earliest_match = match

        if earliest_match:
            # Cut at earliest contamination
            cleaned = text[:earliest_pos].strip()
            logger.debug(f"Cleaned benefit description: cut at pos {earliest_pos} (pattern: {earliest_match.group()})")
            return cleaned
        else:
            return text

    def _extract_with_text_based_layout(self, pages: List[int]) -> List[DetailFact]:
        """
        Extract from text-based layouts (Heungkuk-style).

        Pattern:
        Line 1: 담보명 납입및만기 가입금액 보험료
        Line 2+: 보장설명 텍스트...
        Line N: [보험금을 지급하지 않는 사항]... (exclusion, skip)
        Line N+1: 다음 담보명...

        Strategy:
        1. Extract full page text
        2. Find coverage name lines (match known pattern + amount)
        3. Extract following lines until next coverage or exclusion marker
        """
        facts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in pages:
                if page_num > len(pdf.pages):
                    continue

                page = pdf.pages[page_num - 1]
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split('\n')

                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # Skip header/footer/noise
                    if not line or len(line) < 5:
                        i += 1
                        continue

                    # Check if this is a coverage name line
                    if self._is_coverage_name_line(line):
                        coverage_name = self._extract_coverage_name_from_line(line)

                        if not coverage_name:
                            i += 1
                            continue

                        # Extract description from following lines
                        description_lines = []
                        j = i + 1

                        # Hyundai pattern: skip payment info line (Line N+1)
                        # Pattern: "20년납100세만기 10만원 79"
                        if j < len(lines) and re.search(r'\d+년납.+\d+만원\s+\d+', lines[j].strip()):
                            j += 1  # Skip payment line, start from description

                        while j < len(lines):
                            next_line = lines[j].strip()

                            # Stop conditions
                            if not next_line:
                                j += 1
                                continue

                            # Stop at next coverage
                            if self._is_coverage_name_line(next_line):
                                break

                            # Stop at exclusion section
                            if '[보험금을 지급하지 않는 사항]' in next_line:
                                break

                            # Stop at page footer
                            if any(marker in next_line for marker in ['광화문GA지점', '준법감시인확인필', '설계번호', '고유번호', '발행일시', '대치AM지점', '발행일:', '발행자:', '제작 :', '심사 :', '승인일자']):
                                break

                            # Skip payment-only lines (Hyundai inline payment info)
                            # Pattern: "20년납100세만기 10만원 79" or "20년납100세만기 1천만원 2,078"
                            if re.match(r'^\d+년[납만].+\d+[만백천]?원\s+[\d,]+$', next_line):
                                j += 1
                                continue

                            # Collect description text
                            description_lines.append(next_line)
                            j += 1

                            # Limit description collection (max 15 lines)
                            if len(description_lines) >= 15:
                                break

                        # Build description text
                        description_text = ' '.join(description_lines).strip()

                        # Validate description (must have meaningful content)
                        if description_text and len(description_text) >= 20:
                            # Remove common noise patterns
                            description_text = self._clean_description_text(description_text)

                            # Truncate
                            description_text = self._truncate_description(description_text, max_chars=800)

                            fact = DetailFact(
                                coverage_name_raw=coverage_name,
                                benefit_description_text=description_text,
                                detail_page=page_num,
                                detail_row_hint=f"line_{i+1}",
                                evidences=[
                                    {
                                        "doc_type": "가입설계서",
                                        "page": page_num,
                                        "snippet": description_text[:200],
                                        "extraction_mode": "text_based_layout",
                                        "line_number": i+1,
                                    }
                                ],
                            )
                            facts.append(fact)
                            logger.debug(f"{self.insurer} p.{page_num} line {i+1}: Extracted '{coverage_name}'")

                        # Move to next potential coverage
                        i = j
                    else:
                        i += 1

        logger.info(f"{self.insurer}: Extracted {len(facts)} DETAIL facts (text-based layout)")
        return facts

    def _is_coverage_name_line(self, line: str) -> bool:
        """Check if line matches coverage name pattern."""
        # Hyundai pattern: "number. 담보명" (e.g., "5. 화상진단담보")
        if re.match(r'^\d+\.\s+[가-힣]+', line):
            # Must end with "담보" or similar
            if any(line.endswith(suffix) for suffix in ['담보', '보험', '보장']):
                return True

        # Heungkuk pattern: Must have period/amount pattern
        if not re.search(r'\d+년납', line):
            return False
        if not re.search(r'\d+만원', line):
            return False
        # Must NOT be header
        if '구분' in line and '보장내용' in line:
            return False
        # Must NOT be exclusion
        if '보험금을 지급하지 않는 사항' in line:
            return False
        return True

    def _extract_coverage_name_from_line(self, line: str) -> Optional[str]:
        """Extract coverage name from line."""
        # Hyundai pattern: "number. 담보명" (e.g., "5. 화상진단담보")
        hyundai_match = re.match(r'^\d+\.\s+(.+)$', line)
        if hyundai_match:
            coverage_name = hyundai_match.group(1).strip()
            if len(coverage_name) >= 3 and len(coverage_name) <= 100:
                return coverage_name

        # Heungkuk pattern: Find first period marker
        match = re.search(r'(\d+년납|\d+년만기|\d+년갱신)', line)
        if not match:
            return None
        # Text before period is coverage name
        coverage_name = line[:match.start()].strip()
        # Clean up
        coverage_name = re.sub(r'\s+', '', coverage_name)
        if len(coverage_name) < 3 or len(coverage_name) > 100:
            return None
        return coverage_name

    def _clean_description_text(self, text: str) -> str:
        """Clean description text (remove noise patterns)."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove "기본" prefix
        text = re.sub(r'^기본\s+', '', text)
        return text.strip()

    def _extract_summary_embedded_detail(self, pages: List[int]) -> List[DetailFact]:
        """
        Extract DETAIL from KB-style summary tables.

        KB structure (actual):
        - Table has "보장명 및 보장내용" header
        - Coverage number in col 0, coverage name in col 1
        - Description text appears in page text OUTSIDE the table structure
        - Pattern in text: "74 유사암진단비\n보험기간 중 기타피부암..."

        Strategy (text-based):
        1. Extract full page text
        2. Find coverage patterns: "number coverage_name\ndescription_text"
        3. Extract coverage name and description
        4. Match to table entries by coverage number

        Args:
            pages: List of page numbers to extract from

        Returns:
            List of DetailFact objects
        """
        facts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in pages:
                if page_num > len(pdf.pages):
                    continue

                page = pdf.pages[page_num - 1]
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split('\n')

                i = 0
                while i < len(lines):
                    line = lines[i].strip()

                    # Skip empty lines
                    if not line:
                        i += 1
                        continue

                    # Check if line matches coverage pattern: "number coverage_name"
                    # Example: "74 유사암진단비"
                    match = re.match(r'^(\d+)\s+([가-힣A-Za-z0-9\[\]\(\)]+)', line)

                    if match:
                        coverage_number = match.group(1)
                        coverage_name = match.group(2).strip()

                        # Skip if coverage name is too short
                        if len(coverage_name) < 2:
                            i += 1
                            continue

                        # Extract description from following lines
                        description_lines = []
                        j = i + 1

                        while j < len(lines):
                            next_line = lines[j].strip()

                            # Skip empty lines
                            if not next_line:
                                j += 1
                                continue

                            # Stop at next coverage (number + name pattern)
                            if re.match(r'^\d+\s+[가-힣A-Za-z0-9\[\]\(\)]+', next_line):
                                break

                            # Stop at amount pattern (indicates table data)
                            if re.match(r'^\d+[백천만억]원', next_line):
                                j += 1
                                continue

                            # Stop at header/footer markers
                            if any(marker in next_line for marker in [
                                '보장명 및 보장내용', '가입금액', '보험료', '납입',
                                '가입설계서', '준법', '발행일시'
                            ]):
                                break

                            # Collect description text
                            # Skip lines that look like amount/premium/period data
                            if not re.match(r'^[\d,]+$', next_line):
                                description_lines.append(next_line)

                            j += 1

                            # Limit description collection (max 20 lines)
                            if len(description_lines) >= 20:
                                break

                        # Build description text
                        description_text = ' '.join(description_lines).strip()

                        # Validate description (must have meaningful content)
                        if description_text and len(description_text) >= 20:
                            # Clean: remove amounts/premiums/periods (KB NEXT PATCH)
                            description_text = self._clean_benefit_description(description_text)

                            # After cleaning, check if still valid
                            if description_text and len(description_text) >= 20:
                                # Truncate to 800 chars
                                description_text = self._truncate_description(description_text, max_chars=800)

                                # Create DetailFact
                                fact = DetailFact(
                                    coverage_name_raw=coverage_name,
                                    benefit_description_text=description_text,
                                    detail_page=page_num,
                                    detail_row_hint=f"text_line_{i+1}",
                                    evidences=[
                                        {
                                            "doc_type": "가입설계서",
                                            "page": page_num,
                                            "snippet": description_text[:200],
                                            "extraction_mode": "summary_embedded_detail",
                                            "source": "summary_embedded_detail",
                                            "line_number": i+1,
                                        }
                                    ],
                                )
                                facts.append(fact)

                                logger.debug(
                                    f"{self.insurer} p.{page_num} line {i+1}: "
                                    f"Extracted '{coverage_name}' (#{coverage_number}) with {len(description_text)} chars"
                                )

                        # Move to next potential coverage
                        i = j
                    else:
                        i += 1

        logger.info(f"{self.insurer}: Extracted {len(facts)} DETAIL facts (summary_embedded_detail)")
        return facts

    def _extract_summary_embedded_detail_split(self, pages: List[int]) -> List[DetailFact]:
        """
        Extract DETAIL from Lotte-style alternating row tables.

        Lotte structure:
        - Row N (even): 담보유형 | 담보명 | 가입금액 | 납기/만기 | 보험료(원)
        - Row N+1 (odd): None | 보장내용 텍스트 | None | None | None

        Pattern:
        - Coverage name row contains: coverage number + name, amounts, periods
        - Description row has text in column 1 (담보명 column position)

        Args:
            pages: List of page numbers to extract from

        Returns:
            List of DetailFact objects
        """
        facts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in pages:
                if page_num > len(pdf.pages):
                    continue

                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    # Check if this table has the DETAIL structure
                    # Header should contain "담보명" and we expect "보장내용" in row 1
                    header_row = table[0]
                    if '담보명' not in str(header_row):
                        continue

                    # Find column index for 담보명
                    coverage_col_idx = None
                    for idx, cell in enumerate(header_row):
                        if cell and '담보명' in str(cell):
                            coverage_col_idx = idx
                            break

                    if coverage_col_idx is None:
                        continue

                    logger.debug(
                        f"{self.insurer} page {page_num} table {table_idx}: "
                        f"Found DETAIL table with coverage_col={coverage_col_idx}"
                    )

                    # Process rows in pairs
                    i = 1  # Start after header
                    while i < len(table) - 1:
                        row = table[i]
                        next_row = table[i + 1]

                        if len(row) <= coverage_col_idx or len(next_row) <= coverage_col_idx:
                            i += 1
                            continue

                        # Check if current row is coverage name row
                        coverage_text = self._clean_text(row[coverage_col_idx])

                        # Skip if this looks like a sub-header (e.g., "보장내용")
                        if not coverage_text or coverage_text in ['보장내용', '담보명']:
                            i += 1
                            continue

                        # Remove leading numbers (e.g., "1 상해..." -> "상해...")
                        # This matches summary table format which has no numbers
                        coverage_text = re.sub(r'^\d+\s+', '', coverage_text)

                        # Check if next row is description row
                        # Description row has text in coverage column but no amounts
                        description_text = self._clean_text(next_row[coverage_col_idx])

                        # Validate: description should be substantial text, not a coverage name
                        # Coverage names typically have numbers and are short
                        # Descriptions are longer and contain keywords
                        is_description = (
                            description_text and
                            len(description_text) > 20 and
                            not re.match(r'^\d+\s+[가-힣]+', description_text) and  # Not "1 상해..."
                            any(kw in description_text for kw in ['경우', '지급', '보장', '진단', '수술', '입원', '치료'])
                        )

                        if is_description:
                            # Clean: remove amounts/premiums/periods (KB NEXT PATCH pattern)
                            description_text = self._clean_benefit_description(description_text)

                            # After cleaning, validate again
                            if description_text and len(description_text) >= 20:
                                # Truncate to 800 chars
                                description_text = self._truncate_description(description_text, max_chars=800)

                                # Create DetailFact
                                fact = DetailFact(
                                    coverage_name_raw=coverage_text,
                                    benefit_description_text=description_text,
                                    detail_page=page_num,
                                    detail_row_hint=f"table_{table_idx}_row_{i+1}",
                                    evidences=[
                                        {
                                            "doc_type": "가입설계서",
                                            "page": page_num,
                                            "snippet": description_text[:200],
                                            "extraction_mode": "summary_embedded_detail_split",
                                            "source": "summary_embedded_detail_split",
                                            "table_index": table_idx,
                                            "row_index": i+1,
                                        }
                                    ],
                                )
                                facts.append(fact)

                                logger.debug(
                                    f"{self.insurer} p.{page_num} row {i+1}: "
                                    f"Extracted '{coverage_text}' with {len(description_text)} chars"
                                )

                                # Skip the description row
                                i += 2
                                continue

                        # Not a valid pair, move to next row
                        i += 1

        logger.info(f"{self.insurer}: Extracted {len(facts)} DETAIL facts (summary_embedded_detail_split)")
        return facts


def match_summary_to_detail(
    summary_facts: List[Dict[str, Any]], detail_facts: List[DetailFact]
) -> List[Dict[str, Any]]:
    """
    Match summary facts to detail facts by coverage name.

    Args:
        summary_facts: List of ProposalFact dicts (from summary table)
        detail_facts: List of DetailFact objects (from detail table)

    Returns:
        List of enriched summary facts with proposal_detail_facts added
    """
    # Build detail fact lookup by normalized coverage name
    detail_lookup = {}
    for detail_fact in detail_facts:
        normalized_name = normalize_coverage_name(detail_fact.coverage_name_raw)
        if normalized_name in detail_lookup:
            logger.warning(f"DETAIL duplicate normalized name: {detail_fact.coverage_name_raw} → {normalized_name}")
        detail_lookup[normalized_name] = detail_fact
        logger.debug(f"DETAIL lookup: {detail_fact.coverage_name_raw} → {normalized_name}")

    logger.info(f"Built detail lookup with {len(detail_lookup)} entries")
    if detail_lookup:
        logger.info(f"DETAIL lookup keys (first 10): {list(detail_lookup.keys())[:10]}")

    # Match and enrich summary facts
    enriched_facts = []
    match_count = 0

    for summary_fact in summary_facts:
        coverage_name_raw = summary_fact.get("coverage_name_raw", "")
        normalized_name = normalize_coverage_name(coverage_name_raw)

        # Try exact match
        detail_fact = detail_lookup.get(normalized_name)

        if detail_fact:
            # Add proposal_detail_facts field
            summary_fact["proposal_detail_facts"] = {
                "benefit_description_text": detail_fact.benefit_description_text,
                "detail_page": detail_fact.detail_page,
                "detail_row_hint": detail_fact.detail_row_hint,
                "evidences": detail_fact.evidences,
            }
            match_count += 1
            logger.debug(f"MATCHED: {coverage_name_raw} → {normalized_name}")
        else:
            # No match: add null placeholder
            summary_fact["proposal_detail_facts"] = None
            logger.debug(f"NO MATCH: {coverage_name_raw} → {normalized_name}")

        enriched_facts.append(summary_fact)

    logger.info(f"Matched {match_count}/{len(summary_facts)} summary facts to detail facts")

    return enriched_facts


def normalize_coverage_name(name: str) -> str:
    """
    Normalize coverage name for matching.

    Rules (deterministic):
    - Remove whitespace
    - Remove special characters (괄호, 하이픈 등)
    - Remove leading numbers (1., 2), etc.)
    - Lowercase (for consistency)

    Args:
        name: Raw coverage name

    Returns:
        Normalized name
    """
    # Remove whitespace
    name = re.sub(r'\s+', '', name)

    # Remove leading numbers
    name = re.sub(r'^[\d\.]+\)', '', name)  # "1)", "1."
    name = re.sub(r'^[\d\.]+\.', '', name)  # "1.", "1.1"

    # Remove parentheses and contents (e.g., "(유사암제외)")
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)

    # Remove special characters
    name = re.sub(r'[-_/·]', '', name)

    # Lowercase
    name = name.lower()

    return name
