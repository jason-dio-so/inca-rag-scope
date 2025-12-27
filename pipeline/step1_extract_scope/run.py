"""
Step 1: Extract Scope from 가입설계서 (Subscription Proposal)

입력: 가입설계서 PDF
출력: data/scope/{INSURER}_scope.csv
    - coverage_name_raw: 가입설계서에서 추출한 원본 담보명
    - insurer: 보험사명
    - source_page: PDF 페이지 번호
"""

import csv
from pathlib import Path
from typing import List, Dict


class ScopeExtractor:
    """가입설계서에서 scope 담보 목록 추출"""

    def __init__(self, pdf_path: str, insurer: str):
        self.pdf_path = pdf_path
        self.insurer = insurer
        self.output_dir = Path(__file__).parent.parent.parent / "data" / "scope"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_coverages(self) -> List[Dict[str, str]]:
        """
        PDF에서 담보 목록 추출

        Returns:
            List[Dict]: [{"coverage_name_raw": str, "insurer": str, "source_page": int}]

        NOTE: 실제 PDF 파싱은 추후 구현
        현재는 placeholder로 구조만 정의
        """
        # TODO: PDF 파싱 로직
        # - PyPDF2, pdfplumber 등 사용
        # - 요약 장표 테이블 탐지
        # - 담보명 컬럼 추출

        coverages = []

        # Placeholder: 실제 파싱 결과로 대체 예정
        # coverages.append({
        #     "coverage_name_raw": "일반암진단비",
        #     "insurer": self.insurer,
        #     "source_page": 3
        # })

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
    CLI 실행 예시

    Usage:
        python run.py
    """
    # Placeholder: 실제 경로로 대체 필요
    PDF_PATH = "path/to/가입설계서.pdf"  # TODO: 실제 PDF 경로
    INSURER = "삼성생명"  # TODO: 실제 보험사명

    extractor = ScopeExtractor(pdf_path=PDF_PATH, insurer=INSURER)
    output_path = extractor.run()

    print(f"\n✓ Scope extraction completed: {output_path}")


if __name__ == "__main__":
    main()
