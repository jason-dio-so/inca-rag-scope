"""
STEP NEXT-44: Proposal Fact Extractor

Extract proposal facts (coverage_amount, premium_amount, payment_period, etc.)
directly from 가입설계서 PDF with evidence.

Rules:
- Extract facts exactly as written in PDF (no calculation, no interpretation)
- Every extracted value MUST have evidence (doc_type, page, snippet)
- Null values allowed only when fact not present in PDF
- No DB access, no canonical mapping, no amount judgment
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import pdfplumber


class ProposalFactExtractor:
    """가입설계서에서 proposal facts 추출 (evidence 포함)"""

    def __init__(self, pdf_path: str, insurer: str):
        self.pdf_path = pdf_path
        self.insurer = insurer
        self.output_dir = Path(__file__).parent.parent.parent / "data" / "scope"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
                    header_normalized = header_text.replace(' ', '')

                    # Must have coverage and premium columns
                    # Accept tables with "가입담보" or "담보" or "보장" AND "보험료"
                    if not (('담보' in header_normalized or '보장' in header_normalized or '가입담보' in header_normalized) and '보험료' in header_text):
                        continue

                    # Find column indices
                    col_indices = self._find_column_indices(table)
                    if col_indices['coverage_col'] is None:
                        continue

                    # Extract data rows
                    start_row = 2 if len(table) > 2 else 1
                    for row_idx, row in enumerate(table[start_row:], start=start_row):
                        if not row or len(row) == 0:
                            continue

                        # Extract coverage name (may be in col 0 or col 1 depending on table structure)
                        coverage_name_raw = None

                        # Try coverage_col first
                        if col_indices['coverage_col'] is not None and col_indices['coverage_col'] < len(row):
                            coverage_name_raw = self._extract_cell(row, col_indices['coverage_col'])

                        # For Samsung-style tables, coverage name may be in second column
                        if not coverage_name_raw and len(row) > 1:
                            for col_idx in range(min(3, len(row))):
                                candidate = self._extract_cell(row, col_idx)
                                if candidate and len(candidate) >= 3 and not re.match(r'^[\d,\s]+$', candidate):
                                    coverage_name_raw = candidate
                                    break

                        if not coverage_name_raw or len(coverage_name_raw) < 3:
                            continue

                        # Clean coverage name (remove newlines, extra spaces)
                        coverage_name_raw = ' '.join(coverage_name_raw.split())

                        # Filter out non-coverage rows
                        if any(x in coverage_name_raw for x in ['합계', '광화문', '준법감시', '설계번호', '피보험자', '구분', '☞', '※', '▶', '선택계약', '기본계약', '경과기간', '납입보험료']):
                            continue
                        if re.match(r'^[\d,\s]+$', coverage_name_raw):
                            continue

                        # Skip duplicates
                        if coverage_name_raw in seen_names:
                            continue
                        seen_names.add(coverage_name_raw)

                        # Extract proposal facts
                        proposal_entry = {
                            "insurer": self.insurer,
                            "coverage_name_raw": coverage_name_raw,
                            "coverage_order": len(coverages) + 1,
                            "proposal": {}
                        }

                        # Extract coverage_amount
                        if col_indices['amount_col'] is not None:
                            amount_val = self._extract_cell(row, col_indices['amount_col'])
                            if amount_val and amount_val.strip() and not re.match(r'^[-\s]*$', amount_val):
                                # Create snippet from table row
                                snippet = self._create_table_snippet(table, row_idx, coverage_name_raw, amount_val)
                                proposal_entry["proposal"]["coverage_amount"] = {
                                    "value": amount_val.strip(),
                                    "evidence": {
                                        "doc_type": "proposal",
                                        "page": page_num,
                                        "snippet": snippet
                                    }
                                }

                        # Extract premium_amount
                        if col_indices['premium_col'] is not None:
                            premium_val = self._extract_cell(row, col_indices['premium_col'])
                            if premium_val and premium_val.strip() and not re.match(r'^[-\s]*$', premium_val):
                                snippet = self._create_table_snippet(table, row_idx, coverage_name_raw, premium_val)
                                proposal_entry["proposal"]["premium_amount"] = {
                                    "value": premium_val.strip(),
                                    "evidence": {
                                        "doc_type": "proposal",
                                        "page": page_num,
                                        "snippet": snippet
                                    }
                                }

                        # Extract payment_period
                        if col_indices['period_col'] is not None:
                            period_val = self._extract_cell(row, col_indices['period_col'])
                            if period_val and period_val.strip() and not re.match(r'^[-\s]*$', period_val):
                                snippet = self._create_table_snippet(table, row_idx, coverage_name_raw, period_val)
                                proposal_entry["proposal"]["payment_period"] = {
                                    "value": period_val.strip(),
                                    "evidence": {
                                        "doc_type": "proposal",
                                        "page": page_num,
                                        "snippet": snippet
                                    }
                                }

                        # Extract payment_method (if available)
                        if col_indices['method_col'] is not None:
                            method_val = self._extract_cell(row, col_indices['method_col'])
                            if method_val and method_val.strip() and not re.match(r'^[-\s]*$', method_val):
                                snippet = self._create_table_snippet(table, row_idx, coverage_name_raw, method_val)
                                proposal_entry["proposal"]["payment_method"] = {
                                    "value": method_val.strip(),
                                    "evidence": {
                                        "doc_type": "proposal",
                                        "page": page_num,
                                        "snippet": snippet
                                    }
                                }

                        # Extract renewal_condition (if available)
                        # Most proposals don't explicitly state this in table, so often null

                        coverages.append(proposal_entry)

        return coverages

    def _find_column_indices(self, table: List[List[str]]) -> Dict[str, Optional[int]]:
        """Find column indices for coverage, amount, premium, period, method"""
        indices = {
            'coverage_col': None,
            'amount_col': None,
            'premium_col': None,
            'period_col': None,
            'method_col': None
        }

        # Check first 2 rows for headers
        for row_idx in range(min(2, len(table))):
            for col_idx, cell in enumerate(table[row_idx]):
                cell_text = str(cell).replace(' ', '').replace('\n', '').lower() if cell else ''

                # Coverage column: 담보명, 보장명, 담보가입현황, 가입담보
                if any(x in cell_text for x in ['담보명', '보장명', '담보가입현황', '담보별보장내용', '가입담보']):
                    if indices['coverage_col'] is None:  # Take first match
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
                elif '납입기간' in cell_text or '보험기간' in cell_text:
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

    def _create_table_snippet(self, table: List[List[str]], row_idx: int, coverage_name: str, value: str) -> str:
        """Create evidence snippet from table row"""
        # Return simplified snippet showing coverage and value
        return f"{coverage_name}: {value}"

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
        print(f"[STEP NEXT-44 Step1] Extracting proposal facts from: {self.pdf_path}")
        print(f"[STEP NEXT-44 Step1] Insurer: {self.insurer}")

        # Extract proposal facts
        coverages = self.extract_proposal_facts()
        print(f"[STEP NEXT-44 Step1] Extracted {len(coverages)} coverages with proposal facts")

        # Save to JSONL
        output_path = self.save_to_jsonl(coverages)
        print(f"[STEP NEXT-44 Step1] Saved to: {output_path}")

        # Verification stats
        amount_count = sum(1 for c in coverages if 'coverage_amount' in c.get('proposal', {}))
        premium_count = sum(1 for c in coverages if 'premium_amount' in c.get('proposal', {}))
        period_count = sum(1 for c in coverages if 'payment_period' in c.get('proposal', {}))

        print(f"[STEP NEXT-44 Step1] Proposal facts coverage:")
        print(f"  - coverage_amount: {amount_count}/{len(coverages)} ({amount_count/len(coverages)*100:.1f}%)")
        print(f"  - premium_amount: {premium_count}/{len(coverages)} ({premium_count/len(coverages)*100:.1f}%)")
        print(f"  - payment_period: {period_count}/{len(coverages)} ({period_count/len(coverages)*100:.1f}%)")

        return output_path


def main():
    """
    CLI entry point for STEP NEXT-44 Step1

    Usage:
        python -m pipeline.step1_extract_scope.proposal_fact_extractor --insurer samsung
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
        print(f"\n[STEP NEXT-44 Step1] Processing: {pdf_path.name}")
        extractor = ProposalFactExtractor(pdf_path=str(pdf_path), insurer=insurer)
        coverages = extractor.extract_proposal_facts()

        # Merge unique coverages
        for cov in coverages:
            cov_name = cov['coverage_name_raw']
            if cov_name not in seen_names:
                seen_names.add(cov_name)
                all_coverages.append(cov)

    # Re-number coverage_order
    for idx, cov in enumerate(all_coverages, start=1):
        cov['coverage_order'] = idx

    # Save merged result
    if all_coverages:
        extractor = ProposalFactExtractor(pdf_path=str(pdf_files[0]), insurer=insurer)
        output_path = extractor.save_to_jsonl(all_coverages)

        print(f"\n[STEP NEXT-44 Step1] Final result:")
        print(f"  - Total PDFs processed: {len(pdf_files)}")
        print(f"  - Unique coverages: {len(all_coverages)}")
        print(f"  - Output: {output_path}")

        # Final stats
        amount_count = sum(1 for c in all_coverages if 'coverage_amount' in c.get('proposal', {}))
        premium_count = sum(1 for c in all_coverages if 'premium_amount' in c.get('proposal', {}))
        period_count = sum(1 for c in all_coverages if 'payment_period' in c.get('proposal', {}))

        print(f"\n[STEP NEXT-44 Step1] Proposal facts coverage:")
        print(f"  - coverage_amount: {amount_count}/{len(all_coverages)} ({amount_count/len(all_coverages)*100:.1f}%)")
        print(f"  - premium_amount: {premium_count}/{len(all_coverages)} ({premium_count/len(all_coverages)*100:.1f}%)")
        print(f"  - payment_period: {period_count}/{len(all_coverages)} ({period_count/len(all_coverages)*100:.1f}%)")


if __name__ == "__main__":
    main()
