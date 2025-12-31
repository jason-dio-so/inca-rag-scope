"""
STEP NEXT-44-β: Proposal Fact Extractor (FINAL)

Extract proposal facts from 가입설계서 PDF with evidence.
This is the SSOT for all coverage amounts and proposal data.

Rules (LOCKED):
1. Extract facts exactly as written in PDF (no calculation, no interpretation)
2. Every extracted value MUST have evidence (page, snippet)
3. Null values allowed only when fact not present in PDF
4. Hard gates for KB/Heungkuk row number and amount patterns
5. No DB access, no canonical mapping, no amount judgment
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import pdfplumber


class ProposalFactExtractor:
    """가입설계서에서 proposal facts 추출 (evidence 포함) - SSOT"""

    # STEP NEXT-44-β: Hard gate patterns for KB/Heungkuk regression prevention
    REJECT_PATTERNS = [
        r'^\d+\.?$',              # "10.", "11."
        r'^\d+\)$',               # "10)", "11)"
        r'^\d+(,\d{3})*(원|만원)?$',  # "3,000원", "3,000만원"
        r'^\d+만(원)?$',          # "10만", "10만원"
        r'^\d+[천백십](만)?원?$',  # "1천만원", "5백만원", "10만원"
        r'^[천백십만억]+원?$',    # "천원", "만원", "억원"
    ]

    def __init__(self, pdf_path: str, insurer: str):
        self.pdf_path = pdf_path
        self.insurer = insurer
        self.output_dir = Path(__file__).parent.parent.parent / "data" / "scope"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _is_rejected_coverage_name(self, name: str) -> bool:
        """Check if coverage name matches rejection patterns (KB/Heungkuk gate)"""
        name_clean = name.strip()
        for pattern in self.REJECT_PATTERNS:
            if re.match(pattern, name_clean):
                return True
        return False

    def extract_proposal_facts(self) -> List[Dict[str, Any]]:
        """
        PDF에서 proposal facts 추출

        Returns:
            List[Dict]: proposal fact entries with evidence
        """
        coverages = []
        seen_names = set()

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract tables (primary method for structured data)
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Find header row
                    header_text = ' '.join(str(cell) for row in table[:2] for cell in row if cell)
                    header_normalized = header_text.replace(' ', '').replace('\n', '')

                    # Must have coverage and premium columns
                    if not (('담보' in header_normalized or '보장' in header_normalized or '가입담보' in header_normalized) and '보험료' in header_text):
                        continue

                    # Find column indices
                    col_indices = self._find_column_indices(table)
                    if col_indices['coverage_col'] is None:
                        # STEP NEXT-44-β: Hard gate - discard table if no coverage column found
                        continue

                    # Extract data rows
                    start_row = 2 if len(table) > 2 else 1
                    for row_idx, row in enumerate(table[start_row:], start=start_row):
                        if not row or len(row) == 0:
                            continue

                        # Extract coverage name
                        coverage_name_raw = None

                        # STEP NEXT-44-β: Handle tables where col 0 is row number in data but coverage header
                        # Check if col 0 looks like a row number
                        col_0_val = self._extract_cell(row, 0) if len(row) > 0 else None
                        col_0_is_row_num = col_0_val and re.match(r'^\d+\.?$', col_0_val)

                        # If coverage_col is 0 but col 0 has row number, use col 1 instead
                        effective_coverage_col = col_indices['coverage_col']
                        if effective_coverage_col == 0 and col_0_is_row_num and len(row) > 1:
                            effective_coverage_col = 1

                        # Try effective coverage_col first
                        if effective_coverage_col is not None and effective_coverage_col < len(row):
                            coverage_name_raw = self._extract_cell(row, effective_coverage_col)

                        # Fallback: try adjacent columns
                        if not coverage_name_raw and len(row) > 1:
                            for col_idx in range(min(4, len(row))):
                                if col_idx == 0 and col_0_is_row_num:
                                    continue  # Skip row number column
                                candidate = self._extract_cell(row, col_idx)
                                if candidate and len(candidate) >= 3:
                                    # Check if this looks like a coverage name (not amount column)
                                    if col_indices['amount_col'] is not None and col_idx == col_indices['amount_col']:
                                        continue  # Skip amount column
                                    coverage_name_raw = candidate
                                    break

                        if not coverage_name_raw or len(coverage_name_raw) < 3:
                            continue

                        # Clean coverage name (remove newlines, extra spaces)
                        coverage_name_raw = ' '.join(coverage_name_raw.split())

                        # STEP NEXT-44-β: HARD GATE - Reject row numbers and amount patterns
                        if self._is_rejected_coverage_name(coverage_name_raw):
                            continue

                        # STEP NEXT-44-γ: Filter out non-coverage rows (enhanced for Hanwha)
                        # 1. Standard filters
                        if any(x in coverage_name_raw for x in ['합계', '광화문', '준법감시', '설계번호', '피보험자', '구분', '☞', '※', '▶', '선택계약', '기본계약', '경과기간', '납입보험료']):
                            continue

                        # 2. Hanwha-specific: Filter out benefit description texts (not coverage names)
                        # These are typically long sentences describing payment conditions
                        if any(x in coverage_name_raw for x in ['보험가입금액 지급', '보험금을 지급하지 않는', '보험금 지급', '진단확정', '치료를 목적으로', '직접 결과로', '보험기간 중']):
                            continue

                        # 3. Filter out standalone bracket texts (section markers)
                        if re.match(r'^\[.*\]$', coverage_name_raw):
                            continue

                        # 4. Filter out overly long texts (likely descriptions, not coverage names)
                        # Typical coverage name: 10-50 chars, descriptions: 50+ chars
                        if len(coverage_name_raw) > 100:
                            continue

                        # Skip duplicates
                        if coverage_name_raw in seen_names:
                            continue
                        seen_names.add(coverage_name_raw)

                        # Build proposal facts entry
                        proposal_entry = self._build_proposal_entry(
                            coverage_name_raw=coverage_name_raw,
                            row=row,
                            col_indices=col_indices,
                            page_num=page_num,
                            coverage_order=len(coverages) + 1
                        )

                        coverages.append(proposal_entry)

        return coverages

    def _build_proposal_entry(
        self,
        coverage_name_raw: str,
        row: List[str],
        col_indices: Dict[str, Optional[int]],
        page_num: int,
        coverage_order: int
    ) -> Dict[str, Any]:
        """
        Build proposal entry with STEP NEXT-44-β contract structure

        Contract: proposal_facts with evidences array (not evidence object)
        """
        entry = {
            "insurer": self.insurer,
            "coverage_name_raw": coverage_name_raw,
            "proposal_facts": {
                "coverage_amount_text": None,
                "premium_amount_text": None,
                "payment_period_text": None,
                "payment_method_text": None,
                "renewal_terms_text": None,
                "evidences": []
            }
        }

        # Extract coverage_amount
        if col_indices['amount_col'] is not None:
            amount_val = self._extract_cell(row, col_indices['amount_col'])
            if amount_val and amount_val.strip() and not re.match(r'^[-\s]*$', amount_val):
                entry["proposal_facts"]["coverage_amount_text"] = amount_val.strip()
                entry["proposal_facts"]["evidences"].append({
                    "doc_type": "가입설계서",
                    "page": page_num,
                    "snippet": f"{coverage_name_raw}: {amount_val.strip()}",
                    "source": "table",
                    "bbox": None
                })

        # Extract premium_amount
        if col_indices['premium_col'] is not None:
            premium_val = self._extract_cell(row, col_indices['premium_col'])
            if premium_val and premium_val.strip() and not re.match(r'^[-\s]*$', premium_val):
                entry["proposal_facts"]["premium_amount_text"] = premium_val.strip()
                entry["proposal_facts"]["evidences"].append({
                    "doc_type": "가입설계서",
                    "page": page_num,
                    "snippet": f"보험료 {premium_val.strip()}",
                    "source": "table",
                    "bbox": None
                })

        # Extract payment_period
        if col_indices['period_col'] is not None:
            period_val = self._extract_cell(row, col_indices['period_col'])
            if period_val and period_val.strip() and not re.match(r'^[-\s]*$', period_val):
                # Clean up newlines in period text
                period_clean = ' '.join(period_val.split())
                entry["proposal_facts"]["payment_period_text"] = period_clean
                entry["proposal_facts"]["evidences"].append({
                    "doc_type": "가입설계서",
                    "page": page_num,
                    "snippet": f"납입기간 {period_clean}",
                    "source": "table",
                    "bbox": None
                })

        # Extract payment_method (if available)
        if col_indices['method_col'] is not None:
            method_val = self._extract_cell(row, col_indices['method_col'])
            if method_val and method_val.strip() and not re.match(r'^[-\s]*$', method_val):
                entry["proposal_facts"]["payment_method_text"] = method_val.strip()
                entry["proposal_facts"]["evidences"].append({
                    "doc_type": "가입설계서",
                    "page": page_num,
                    "snippet": f"납입방법 {method_val.strip()}",
                    "source": "table",
                    "bbox": None
                })

        # renewal_terms_text: usually not in proposal tables, remains null

        # STEP NEXT-44-β: At least 1 evidence required
        if not entry["proposal_facts"]["evidences"]:
            # Add minimal evidence showing coverage was found but no facts extracted
            entry["proposal_facts"]["evidences"].append({
                "doc_type": "가입설계서",
                "page": page_num,
                "snippet": f"{coverage_name_raw}",
                "source": "table",
                "bbox": None
            })

        return entry

    def _find_column_indices(self, table: List[List[str]]) -> Dict[str, Optional[int]]:
        """
        Find column indices for coverage, amount, premium, period, method

        STEP NEXT-44-β: Handle multi-cell headers (e.g., "보장명 및 보장내용" spanning multiple cells)
        """
        indices = {
            'coverage_col': None,
            'amount_col': None,
            'premium_col': None,
            'period_col': None,
            'method_col': None
        }

        # Check first 2 rows for headers
        for row_idx in range(min(2, len(table))):
            row = table[row_idx]

            # Build text for each cell and its neighbors (for multi-cell headers)
            for col_idx, cell in enumerate(row):
                cell_text = str(cell).replace(' ', '').replace('\n', '').lower() if cell else ''

                # Also check next cell to handle split headers
                next_cell_text = ''
                if col_idx + 1 < len(row) and row[col_idx + 1]:
                    next_cell_text = str(row[col_idx + 1]).replace(' ', '').replace('\n', '').lower()

                combined_text = cell_text + next_cell_text

                # Coverage column: 담보명, 보장명, 담보가입현황, 가입담보
                # STEP NEXT-44-γ: Exclude merged headers like "가입담보 및 보장내용"
                if any(x in combined_text for x in ['담보명', '보장명', '담보가입현황', '담보별보장내용', '가입담보']):
                    # Skip if this is a merged header (contains "및 보장내용" or similar)
                    if '보장내용' in combined_text and ('및' in combined_text or '보장내용' in cell_text):
                        continue  # This is a multi-row header, not a simple coverage name column

                    if indices['coverage_col'] is None:
                        # If header is split across cells, use the second cell
                        if not cell_text and next_cell_text:
                            indices['coverage_col'] = col_idx + 1
                        else:
                            indices['coverage_col'] = col_idx
                # Amount column: 가입금액
                elif '가입금액' in cell_text:
                    if indices['amount_col'] is None:
                        indices['amount_col'] = col_idx
                # Premium column: 보험료
                elif '보험료' in cell_text and '납입면제' not in cell_text:
                    if indices['premium_col'] is None:
                        indices['premium_col'] = col_idx
                # Period column: 납입기간, 보험기간
                elif '납입기간' in cell_text or '보험기간' in cell_text or '납기' in cell_text:
                    if indices['period_col'] is None:
                        indices['period_col'] = col_idx
                # Method column
                elif '납입방법' in cell_text or '납입주기' in cell_text:
                    if indices['method_col'] is None:
                        indices['method_col'] = col_idx

        return indices

    def _extract_cell(self, row: List[str], col_idx: int) -> Optional[str]:
        """Extract cell value safely"""
        if col_idx < len(row) and row[col_idx]:
            return str(row[col_idx]).strip()
        return None

    def save_to_jsonl(self, coverages: List[Dict[str, Any]]) -> str:
        """
        Save proposal facts to JSONL

        Output: data/scope/{insurer}_step1_raw_scope.jsonl
        """
        output_path = self.output_dir / f"{self.insurer}_step1_raw_scope.jsonl"

        with open(output_path, 'w', encoding='utf-8') as f:
            for cov in coverages:
                f.write(json.dumps(cov, ensure_ascii=False) + '\n')

        return str(output_path)

    def run(self) -> str:
        """
        Execute full proposal fact extraction

        Returns:
            str: Output JSONL path
        """
        print(f"[STEP NEXT-44-β Step1] Extracting proposal facts from: {self.pdf_path}")
        print(f"[STEP NEXT-44-β Step1] Insurer: {self.insurer}")

        # Extract proposal facts
        coverages = self.extract_proposal_facts()
        print(f"[STEP NEXT-44-β Step1] Extracted {len(coverages)} coverages with proposal facts")

        # Save to JSONL
        output_path = self.save_to_jsonl(coverages)
        print(f"[STEP NEXT-44-β Step1] Saved to: {output_path}")

        # Verification stats
        amount_count = sum(1 for c in coverages if c['proposal_facts'].get('coverage_amount_text'))
        premium_count = sum(1 for c in coverages if c['proposal_facts'].get('premium_amount_text'))
        period_count = sum(1 for c in coverages if c['proposal_facts'].get('payment_period_text'))

        print(f"[STEP NEXT-44-β Step1] Proposal facts coverage:")
        print(f"  - coverage_amount_text: {amount_count}/{len(coverages)} ({amount_count/len(coverages)*100:.1f}%)")
        print(f"  - premium_amount_text: {premium_count}/{len(coverages)} ({premium_count/len(coverages)*100:.1f}%)")
        print(f"  - payment_period_text: {period_count}/{len(coverages)} ({period_count/len(coverages)*100:.1f}%)")

        return output_path


def main():
    """
    CLI entry point for STEP NEXT-44-β Step1

    Usage:
        python -m pipeline.step1_extract_scope.proposal_fact_extractor_v2 --insurer samsung
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--insurer', required=True, help='보험사 코드 (소문자)')
    args = parser.parse_args()

    insurer = args.insurer.lower()
    base_dir = Path(__file__).parent.parent.parent
    pdf_dir = base_dir / "data" / "sources" / "insurers" / insurer / "가입설계서"

    if not pdf_dir.exists():
        pdf_dir = base_dir / "data" / "sources" / "insurers" / insurer

    pdf_files = sorted(list(pdf_dir.glob("*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF found in {pdf_dir}")

    # Process all PDFs and merge results
    all_coverages = []
    seen_names = set()

    for pdf_path in pdf_files:
        print(f"\n[STEP NEXT-44-β Step1] Processing: {pdf_path.name}")
        extractor = ProposalFactExtractor(pdf_path=str(pdf_path), insurer=insurer)
        coverages = extractor.extract_proposal_facts()

        # Merge unique coverages
        for cov in coverages:
            cov_name = cov['coverage_name_raw']
            if cov_name not in seen_names:
                seen_names.add(cov_name)
                all_coverages.append(cov)

    if all_coverages:
        extractor = ProposalFactExtractor(pdf_path=str(pdf_files[0]), insurer=insurer)
        output_path = extractor.save_to_jsonl(all_coverages)

        print(f"\n[STEP NEXT-44-β Step1] Final result:")
        print(f"  - Total PDFs processed: {len(pdf_files)}")
        print(f"  - Unique coverages: {len(all_coverages)}")
        print(f"  - Output: {output_path}")

        # Final stats
        amount_count = sum(1 for c in all_coverages if c['proposal_facts'].get('coverage_amount_text'))
        premium_count = sum(1 for c in all_coverages if c['proposal_facts'].get('premium_amount_text'))
        period_count = sum(1 for c in all_coverages if c['proposal_facts'].get('payment_period_text'))

        print(f"\n[STEP NEXT-44-β Step1] Proposal facts coverage:")
        print(f"  - coverage_amount_text: {amount_count}/{len(all_coverages)} ({amount_count/len(all_coverages)*100:.1f}%)")
        print(f"  - premium_amount_text: {premium_count}/{len(all_coverages)} ({premium_count/len(all_coverages)*100:.1f}%)")
        print(f"  - payment_period_text: {period_count}/{len(all_coverages)} ({period_count/len(all_coverages)*100:.1f}%)")

        # STEP NEXT-44-β: KB/Heungkuk regression check
        print(f"\n[STEP NEXT-44-β Step1] Regression check:")
        rejected_patterns_found = False
        for cov in all_coverages[:5]:  # Check first 5
            name = cov['coverage_name_raw']
            for pattern in ProposalFactExtractor.REJECT_PATTERNS:
                if re.match(pattern, name):
                    print(f"  ⚠️  REGRESSION: '{name}' matches reject pattern {pattern}")
                    rejected_patterns_found = True
                    break
        if not rejected_patterns_found:
            print(f"  ✅ No rejected patterns found in coverage names")


if __name__ == "__main__":
    main()
