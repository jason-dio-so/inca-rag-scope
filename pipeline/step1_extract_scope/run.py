"""
Step 1: Extract Scope from 가입설계서 (Subscription Proposal)

입력: 가입설계서 PDF
출력: data/scope/{INSURER}_scope.csv
    - coverage_name_raw: 가입설계서에서 추출한 원본 담보명
    - insurer: 보험사명
    - source_page: PDF 페이지 번호
"""

import csv
import argparse
from pathlib import Path
from typing import List, Dict
import pdfplumber
import re
from .hardening import hardening_correction, calculate_header_pollution_rate


class ScopeExtractor:
    """가입설계서에서 scope 담보 목록 추출"""

    def __init__(self, pdf_path: str, insurer: str):
        self.pdf_path = pdf_path
        self.insurer = insurer
        self.output_dir = Path(__file__).parent.parent.parent / "data" / "scope"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_coverages(self) -> List[Dict[str, str]]:
        """
        PDF에서 담보 목록 추출 (텍스트 + 테이블 혼합)

        Returns:
            List[Dict]: [{"coverage_name_raw": str, "insurer": str, "source_page": int}]
        """
        coverages = []
        seen = set()

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Method 1: 텍스트 라인 기반 (KB, 현대, 롯데)
                text = page.extract_text() or ""
                lines = text.split('\n')

                for i, line in enumerate(lines):
                    triggers = ['순번', '담보명', '보장명', '가입담보']
                    if any(t in line for t in triggers) and ('보험료' in line or '가입금액' in line or '납기' in line):
                        for j in range(i+1, min(i+60, len(lines))):
                            row = lines[j].strip()
                            if not row or '보장보험료' in row or '합계' in row or '※' in row:
                                break

                            coverage_name = None
                            match = re.match(r'^(\d+)\s+(.+)', row)
                            if match:
                                coverage_name = match.group(2).split()[0]

                            match = re.match(r'^(\d+)\.\s*(.+)', row)
                            if match:
                                full = match.group(2)
                                parts = re.split(r'\s+\d+[만천백억,원]+', full)
                                coverage_name = parts[0].strip() if parts else None

                            if coverage_name:
                                if len(coverage_name) < 3 or re.match(r'^[\d,]+', coverage_name):
                                    continue
                                if coverage_name in ['(기본)', '기본계약']:
                                    continue
                                if coverage_name not in seen:
                                    seen.add(coverage_name)
                                    coverages.append({
                                        "coverage_name_raw": coverage_name,
                                        "insurer": self.insurer,
                                        "source_page": page_num
                                    })

                # Method 2: 테이블 기반 (흥국)
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 3:
                        continue

                    # 담보명+보험료 컬럼이 모두 있는 테이블만 (실제 보장 테이블)
                    header_text = ' '.join(str(cell) for row in table[:2] for cell in row if cell)
                    header_normalized = header_text.replace(' ', '')  # 띄어쓰기 제거
                    if not (('담보' in header_normalized or '보장' in header_normalized) and '보험료' in header_text):
                        continue

                    # 담보명 컬럼 찾기 (띄어쓰기 무시)
                    coverage_col_idx = None
                    for row_idx in range(min(2, len(table))):
                        for col_idx, cell in enumerate(table[row_idx]):
                            cell_text = str(cell).replace(' ', '') if cell else ''
                            if '담보명' in cell_text or '보장명' in cell_text:
                                coverage_col_idx = col_idx
                                break
                        if coverage_col_idx is not None:
                            break

                    if coverage_col_idx is not None:
                        start_row = 2 if len(table) > 2 else 1  # 헤더 스킵
                        for row in table[start_row:]:
                            if len(row) > coverage_col_idx and row[coverage_col_idx]:
                                coverage_name = str(row[coverage_col_idx]).strip()

                                # 필터링
                                if len(coverage_name) < 3 or re.match(r'^[\d,]+', coverage_name):
                                    continue
                                if any(x in coverage_name for x in ['합계', '보험료', '광화문', '준법감시', '설계번호', '피보험자', '구분', '담 보', '담보 명', '가입금액', '☞', '※', '▶']):
                                    continue

                                if coverage_name not in seen:
                                    seen.add(coverage_name)
                                    coverages.append({
                                        "coverage_name_raw": coverage_name,
                                        "insurer": self.insurer,
                                        "source_page": page_num
                                    })

        return coverages

    def save_to_csv(self, coverages: List[Dict[str, str]]) -> str:
        """
        추출된 담보 목록을 CSV로 저장

        Args:
            coverages: 추출된 담보 목록

        Returns:
            str: 저장된 CSV 파일 경로
        """
        output_path = self.output_dir / f"{self.insurer}_scope.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["coverage_name_raw", "insurer", "source_page"])
            writer.writeheader()
            writer.writerows(coverages)

        return str(output_path)

    def run(self) -> str:
        """
        전체 추출 프로세스 실행

        Returns:
            str: 저장된 CSV 파일 경로
        """
        print(f"[Step 1] Extracting scope from: {self.pdf_path}")
        print(f"[Step 1] Insurer: {self.insurer}")

        # 1. PDF에서 담보 추출
        coverages = self.extract_coverages()
        print(f"[Step 1] Extracted {len(coverages)} coverages")

        # 2. CSV 저장
        output_path = self.save_to_csv(coverages)
        print(f"[Step 1] Saved to: {output_path}")

        return output_path


def main():
    """
    CLI 실행

    Usage:
        python -m pipeline.step1_extract_scope.run --insurer lotte
    """
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

    # STEP 1: 기본 추출
    all_coverages = []
    seen = set()

    for pdf_path in pdf_files:
        print(f"\n[Step 1] Processing: {pdf_path.name}")
        extractor = ScopeExtractor(pdf_path=str(pdf_path), insurer=insurer)
        coverages = extractor.extract_coverages()

        # 중복 제거하며 병합
        for cov in coverages:
            cov_name = cov['coverage_name_raw']
            if cov_name not in seen:
                seen.add(cov_name)
                all_coverages.append(cov)

        print(f"  - Extracted {len(coverages)} coverages (unique: {len(seen)})")

    extracted_total = len(all_coverages)
    print(f"\n[Step 1] Initial extraction: {extracted_total} coverages")

    # STEP 2: 보정 루프 (extracted_total < 30 무조건 실행)
    declared_count = 0
    pages_found = []

    if extracted_total < 30:
        print(f"\n[Step 1] ⚠️  Extracted count ({extracted_total}) < 30, starting hardening correction...")
        all_coverages, declared_count, pages_found = hardening_correction(insurer, pdf_files)
        final_total = len(all_coverages)
        print(f"\n[Step 1] After correction: {final_total} coverages")
    else:
        final_total = extracted_total
        pages_found = sorted(set(cov['source_page'] for cov in all_coverages))

    # STEP 3: 최종 저장 및 판정
    output_path = extractor.save_to_csv(all_coverages)

    print(f"\n[Step 1] Final result:")
    print(f"  - Total PDFs processed: {len(pdf_files)}")
    print(f"  - Unique coverages: {final_total}")
    print(f"  - Pages: {pages_found}")
    print(f"  - Output: {output_path}")

    # STEP NEXT-32: Quality Gates Enforcement
    print(f"\n{'='*60}")
    print(f"[STEP NEXT-32 Quality Gates]")
    print(f"{'='*60}")

    # Gate 1: Count Gate (≥30)
    count_gate_pass = final_total >= 30
    print(f"\n[Gate 1] Count Gate (≥30)")
    print(f"  - Extracted: {final_total}")
    print(f"  - Threshold: 30")
    print(f"  - Status: {'✓ PASS' if count_gate_pass else '✗ FAIL'}")

    # Gate 2: Header Pollution Gate (<5%)
    # STEP NEXT-32-γ: Use with_samples=True for run.py only
    pollution_count, pollution_rate, pollution_samples = calculate_header_pollution_rate(all_coverages, with_samples=True)
    pollution_gate_pass = pollution_rate < 5.0
    print(f"\n[Gate 2] Header Pollution Gate (<5%)")
    print(f"  - Pollution count: {pollution_count}/{final_total}")
    print(f"  - Pollution rate: {pollution_rate:.2f}%")
    print(f"  - Threshold: <5%")
    print(f"  - Status: {'✓ PASS' if pollution_gate_pass else '✗ FAIL'}")

    # STEP NEXT-32-γ: Log pollution samples for verification
    if pollution_samples:
        print(f"  - Pollution samples (max 5):")
        for sample in pollution_samples:
            print(f"    • {sample}")
    else:
        print(f"  - Pollution samples: none")

    # Gate 3: Declared vs Extracted Gap (Warning only)
    if declared_count and declared_count > 0:
        gap_abs = abs(declared_count - final_total)
        gap_rate = gap_abs / declared_count
        print(f"\n[Gate 3] Declared vs Extracted Gap (Warning)")
        print(f"  - Declared: {declared_count}")
        print(f"  - Extracted: {final_total}")
        print(f"  - Gap: {gap_abs} ({gap_rate*100:.1f}%)")
        if gap_rate > 0.5:
            print(f"  - Status: ⚠️  WARN (gap > 50%)")
        else:
            print(f"  - Status: ✓ OK")
    else:
        print(f"\n[Gate 3] Declared vs Extracted Gap (Warning)")
        print(f"  - Declared count: N/A")
        print(f"  - Status: SKIP")

    # Final verdict
    print(f"\n{'='*60}")
    all_gates_pass = count_gate_pass and pollution_gate_pass
    if all_gates_pass:
        print(f"✓ ALL GATES PASSED")
        print(f"  insurer={insurer} extracted={final_total} pollution={pollution_rate:.2f}%")
    else:
        print(f"✗ GATE FAILURE")
        print(f"  insurer={insurer} extracted={final_total} pollution={pollution_rate:.2f}%")
        if not count_gate_pass:
            print(f"  - Count Gate FAILED (extracted {final_total} < 30)")
        if not pollution_gate_pass:
            print(f"  - Pollution Gate FAILED (rate {pollution_rate:.2f}% ≥ 5%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
