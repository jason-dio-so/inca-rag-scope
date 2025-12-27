"""
Step 3: PDF Text Extraction

입력: data/evidence_sources/{INSURER}_manifest.csv
출력: data/evidence_text/{INSURER}/{doc_type}/{basename}.page.jsonl

페이지별 텍스트 추출 (no OCR, no embedding, no LLM)
"""

import csv
import json
from pathlib import Path
from typing import List, Dict
import pymupdf  # PyMuPDF (fitz)


class PDFTextExtractor:
    """PDF 페이지별 텍스트 추출"""

    def __init__(self, output_base_dir: str):
        self.output_base_dir = Path(output_base_dir)

    def extract_pdf_to_jsonl(self, pdf_path: str, doc_type: str, insurer: str) -> str:
        """
        PDF를 페이지별 JSONL로 추출

        Args:
            pdf_path: PDF 파일 경로
            doc_type: 문서 타입 (약관, 사업방법서, 상품요약서)
            insurer: 보험사명

        Returns:
            str: 생성된 JSONL 파일 경로
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # 출력 디렉토리 생성
        output_dir = self.output_base_dir / insurer / doc_type
        output_dir.mkdir(parents=True, exist_ok=True)

        # 출력 파일명
        basename = pdf_path.stem
        output_file = output_dir / f"{basename}.page.jsonl"

        # PDF 열기
        doc = pymupdf.open(str(pdf_path))

        pages_data = []

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")  # 텍스트 추출

                page_data = {
                    "page": page_num + 1,  # 1-based page number
                    "text": text.strip()
                }
                pages_data.append(page_data)

        finally:
            doc.close()

        # JSONL 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            for page_data in pages_data:
                f.write(json.dumps(page_data, ensure_ascii=False) + '\n')

        return str(output_file)

    def extract_from_manifest(self, manifest_csv: str, insurer: str) -> List[Dict]:
        """
        Manifest CSV에서 모든 PDF 추출

        Args:
            manifest_csv: manifest CSV 경로
            insurer: 보험사명

        Returns:
            List[Dict]: 추출 결과 목록
        """
        results = []

        with open(manifest_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                doc_type = row['doc_type']
                file_path = row['file_path']

                print(f"[Extract] {doc_type}: {file_path}")

                try:
                    output_file = self.extract_pdf_to_jsonl(file_path, doc_type, insurer)
                    results.append({
                        'doc_type': doc_type,
                        'file_path': file_path,
                        'output_file': output_file,
                        'status': 'success'
                    })
                    print(f"  → {output_file}")

                except Exception as e:
                    results.append({
                        'doc_type': doc_type,
                        'file_path': file_path,
                        'output_file': None,
                        'status': 'failed',
                        'error': str(e)
                    })
                    print(f"  ✗ Error: {e}")

        return results


def main():
    """CLI 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='PDF text extraction')
    parser.add_argument('--insurer', type=str, default='samsung', help='보험사명')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    insurer = args.insurer

    manifest_csv = base_dir / "data" / "evidence_sources" / f"{insurer}_manifest.csv"
    output_base_dir = base_dir / "data" / "evidence_text"

    print(f"[Step 3] PDF Text Extraction")
    print(f"[Step 3] Manifest: {manifest_csv}")
    print(f"[Step 3] Output: {output_base_dir}/{insurer}/")

    extractor = PDFTextExtractor(str(output_base_dir))
    results = extractor.extract_from_manifest(str(manifest_csv), insurer)

    # 통계
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')

    print(f"\n[Step 3] Extraction completed:")
    print(f"  - Success: {success_count}")
    print(f"  - Failed: {failed_count}")
    print(f"  - Total: {len(results)}")


if __name__ == "__main__":
    main()
