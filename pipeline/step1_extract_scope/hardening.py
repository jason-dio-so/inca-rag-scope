"""
STEP 1-β: Scope Extraction Hardening
30 미만 담보 추출 시 보정 루프 강제 실행
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pdfplumber


def detect_declared_count(pdf_path: str) -> Optional[int]:
    """
    PDF에서 선언된 담보 총 개수 탐지 (검증용)

    패턴:
    - 총 N개
    - 기본계약 N개 + 특약 M개
    - 가입담보 총 N개
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:10]:  # 앞 10페이지만 탐색
            text = page.extract_text() or ""

            # 패턴1: "총 37개"
            match = re.search(r'총\s*(\d+)\s*개', text)
            if match:
                return int(match.group(1))

            # 패턴2: "기본계약 3개 + 특약 34개"
            match = re.search(r'기본계약\s*(\d+)\s*개.*?특약\s*(\d+)\s*개', text, re.DOTALL)
            if match:
                return int(match.group(1)) + int(match.group(2))

            # 패턴3: "대상계약 3개 34개" (흥국 스타일)
            match = re.search(r'대상계약\s*(\d+)\s*개\s*(\d+)\s*개', text)
            if match:
                return int(match.group(1)) + int(match.group(2))

    return None


def enhanced_table_extraction(pdf_path: str, insurer: str) -> List[Dict[str, str]]:
    """
    강화된 담보 추출 로직

    - 헤더 패턴 확장
    - 특약 표 별도 탐색
    - 종료 조건 강화
    """
    coverages = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = text.split('\n')

            # 텍스트 라인 기반 추출 (확장 패턴)
            for i, line in enumerate(lines):
                # 확장된 헤더 패턴
                triggers = ['순번', '담보명', '보장명', '가입담보', '보장내용', '특약명']
                indicators = ['보험료', '가입금액', '납기', '만기']

                if any(t in line for t in triggers) and any(ind in line for ind in indicators):
                    # 특약 섹션 체크
                    is_special = '특약' in line or '선택특약' in line

                    for j in range(i+1, min(i+80, len(lines))):
                        row = lines[j].strip()

                        # 강화된 종료 조건
                        if not row or any(x in row for x in ['보장보험료', '합계', '총액', '계', '주계약', '※', '▶', '☞']):
                            break

                        coverage_name = None

                        # 숫자 패턴
                        match = re.match(r'^(\d+)\s+(.+)', row)
                        if match:
                            coverage_name = match.group(2).split()[0]

                        # 점 패턴
                        match = re.match(r'^(\d+)\.\s*(.+)', row)
                        if match:
                            full = match.group(2)
                            parts = re.split(r'\s+\d+[만천백억,원]+', full)
                            coverage_name = parts[0].strip() if parts else None

                        if coverage_name:
                            if len(coverage_name) < 3 or re.match(r'^[\d,]+', coverage_name):
                                continue
                            if coverage_name in ['(기본)', '기본계약', '주계약']:
                                continue

                            if coverage_name not in seen:
                                seen.add(coverage_name)
                                coverages.append({
                                    "coverage_name_raw": coverage_name,
                                    "insurer": insurer,
                                    "source_page": page_num
                                })

            # 테이블 기반 추출 (강화 + 헤더 없는 테이블 지원)
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 3:
                    continue

                # 헤더 검증 (띄어쓰기 정규화)
                header_text = ' '.join(str(cell) for row in table[:2] for cell in row if cell)
                header_normalized = header_text.replace(' ', '')

                has_header = (('담보' in header_normalized or '보장' in header_normalized or '특약' in header_normalized)
                             and '보험료' in header_text)

                # 헤더 없는 담보 테이블 탐지 (첫 컬럼이 담보명 스타일)
                # 조건: 4개 컬럼, 첫 컬럼이 한글+특수문자, 2번째가 "납", 4번째가 숫자
                headerless_table = False
                if not has_header and len(table) > 3 and len(table[0]) >= 4:
                    first_row = table[0]
                    if (first_row[0] and len(str(first_row[0])) > 5
                        and '납' in str(first_row[1] or '')
                        and re.match(r'^\d+', str(first_row[3] or ''))):
                        headerless_table = True

                if not (has_header or headerless_table):
                    continue

                # 담보명 컬럼 찾기
                coverage_col_idx = None

                if has_header:
                    for row_idx in range(min(3, len(table))):
                        for col_idx, cell in enumerate(table[row_idx]):
                            cell_text = str(cell).replace(' ', '') if cell else ''
                            if '담보명' in cell_text or '보장명' in cell_text or '특약명' in cell_text or '보장내용' in cell_text:
                                coverage_col_idx = col_idx
                                break
                        if coverage_col_idx is not None:
                            break
                    start_row = 2 if len(table) > 2 else 1
                else:
                    # 헤더 없는 테이블: 첫 컬럼이 담보명
                    coverage_col_idx = 0
                    start_row = 0

                if coverage_col_idx is not None:
                    for row in table[start_row:]:
                        if len(row) > coverage_col_idx and row[coverage_col_idx]:
                            coverage_name = str(row[coverage_col_idx]).strip()

                            if len(coverage_name) < 3 or re.match(r'^[\d,]+', coverage_name):
                                continue

                            exclude_keywords = ['합계', '보험료', '광화문', '준법감시', '설계번호',
                                              '피보험자', '구분', '담 보', '담보 명', '가입금액',
                                              '☞', '※', '▶', '계약자', '납입', '발행일']
                            if any(x in coverage_name for x in exclude_keywords):
                                continue

                            if coverage_name not in seen:
                                seen.add(coverage_name)
                                coverages.append({
                                    "coverage_name_raw": coverage_name,
                                    "insurer": insurer,
                                    "source_page": page_num
                                })

    return coverages


def hardening_correction(insurer: str, pdf_files: List[Path]) -> Tuple[List[Dict[str, str]], int, List[int]]:
    """
    보정 루프 실행

    Returns:
        (coverages, declared_count, pages)
    """
    all_coverages = []
    seen = set()
    pages_found = []
    declared_total = None

    print(f"\n[Hardening] Starting correction loop for {insurer}")

    for pdf_path in pdf_files:
        print(f"\n[Hardening] Processing: {pdf_path.name}")

        # 선언값 탐지
        declared = detect_declared_count(str(pdf_path))
        if declared:
            declared_total = declared
            print(f"  - Declared count: {declared}")

        # 강화 추출
        coverages = enhanced_table_extraction(str(pdf_path), insurer)
        print(f"  - Enhanced extraction: {len(coverages)} coverages")

        # 병합
        for cov in coverages:
            cov_name = cov['coverage_name_raw']
            page = cov['source_page']

            if cov_name not in seen:
                seen.add(cov_name)
                all_coverages.append(cov)
                if page not in pages_found:
                    pages_found.append(page)

    print(f"\n[Hardening] Correction result:")
    print(f"  - Total unique coverages: {len(all_coverages)}")
    print(f"  - Pages: {sorted(pages_found)}")

    return all_coverages, declared_total or 0, sorted(pages_found)
