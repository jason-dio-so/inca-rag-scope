"""
STEP 1-β: Scope Extraction Hardening
30 미만 담보 추출 시 보정 루프 강제 실행

STEP NEXT-32: Quality Gates Implementation
- Count Gate (≥30)
- Header Pollution Gate (<5%)
- Declared vs Extracted Gap Warning (>50%)
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pdfplumber


def normalize_newline_only(s: str) -> str:
    """
    STEP NEXT-34-ε: Newline-only removal for search key stability

    Deterministic + idempotent.
    Allowed: remove '\n' and '\r\n' only.
    Forbidden: strip(), collapse spaces, regex \s+, other normalization.

    Args:
        s: Input string (coverage_name_raw)

    Returns:
        String with newlines removed (for search key only, NOT for raw SSOT)
    """
    if s is None:
        return s
    return s.replace("\r\n", "").replace("\n", "")


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


def samsung_table_extraction(pdf_path: str, insurer: str) -> List[Dict[str, str]]:
    """
    STEP NEXT-32: Samsung-specific table extraction

    Samsung 가입설계서의 table 구조:
    - Page 2-3: "담보가입현황" 테이블 (담보명이 2~3번째 열)
    - Page 4+: "담보별 보장내용" 테이블 (기본계약/선택계약 섹션)

    Args:
        pdf_path: PDF file path
        insurer: "samsung"

    Returns:
        List of coverage dicts
    """
    coverages = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Samsung pattern detection
                # 패턴 1: "담보가입현황" 또는 "담보별 보장내용"이 헤더에 있는 테이블
                header_text = ' '.join(str(cell) for row in table[:2] for cell in row if cell)
                is_coverage_table = ('담보' in header_text or '보장' in header_text) and \
                                   ('가입금액' in header_text or '보험료' in header_text)

                if not is_coverage_table:
                    continue

                # 담보명 컬럼 찾기 (Samsung 특화)
                # Samsung 표준 패턴:
                # - "담보가입현황" 테이블: 담보명이 3번째 열(index 2)
                # - "담보별 보장내용" 테이블: 담보명이 2번째 열(index 1)
                coverage_col_idx = None

                # Detect table type
                is_status_table = '담보가입현황' in header_text  # 담보가입현황 테이블
                is_detail_table = '담보별 보장내용' in header_text or '담보별보장내용' in header_text.replace(' ', '')

                if is_status_table:
                    # 담보가입현황: 담보명이 3번째 열(index 2)
                    coverage_col_idx = 2
                elif is_detail_table:
                    # 담보별 보장내용: 담보명이 2번째 열(index 1)
                    coverage_col_idx = 1
                else:
                    # Fallback: find column with longest text cells (likely coverage names)
                    col_lengths = []
                    for col_idx in range(len(table[0])):
                        avg_length = sum(len(str(row[col_idx] or '')) for row in table[2:min(len(table), 10)]) / min(8, len(table) - 2)
                        col_lengths.append((col_idx, avg_length))
                    if col_lengths:
                        coverage_col_idx = max(col_lengths, key=lambda x: x[1])[0]

                if coverage_col_idx is None or coverage_col_idx >= len(table[0]):
                    continue

                # Extract coverages from table rows
                start_row = 2 if len(table) > 2 else 1

                for row in table[start_row:]:
                    if len(row) <= coverage_col_idx:
                        continue

                    cell_value = row[coverage_col_idx]
                    if not cell_value:
                        continue

                    coverage_name = str(cell_value).strip()

                    # Filter out section headers and non-coverage text
                    # Samsung-specific: "기본계약", "선택계약" are section markers
                    if coverage_name in ['기본계약', '선택계약', '담보가입현황', '담보별 보장내용']:
                        continue

                    # General filters
                    if len(coverage_name) < 3:
                        continue

                    # 금액값 제거 (숫자+만원/천원/억원 패턴)
                    # 예: "10만원", "3,000만원", "500만원" 등
                    if re.match(r'^[\d,]+[만천억]*원?$', coverage_name):
                        continue
                    # "1,000만원" 같은 패턴 (쉼표 포함)
                    if re.match(r'^[\d,]+(만|천|억|조)?원$', coverage_name):
                        continue

                    if any(x in coverage_name for x in ['합계', '총액', '보험료', '계약자', '피보험자',
                                                        '가입금액', '납입기간', '보험기간', '설계번호']):
                        continue

                    # Samsung 특화: "보장개시일 이후..." 같은 긴 설명문 제외
                    if len(coverage_name) > 100:
                        continue

                    # 주석/설명문 제외
                    if coverage_name.startswith('※') or coverage_name.startswith('◆'):
                        continue

                    if coverage_name not in seen:
                        seen.add(coverage_name)
                        coverages.append({
                            "coverage_name_raw": coverage_name,
                            "insurer": insurer,
                            "source_page": page_num
                        })

    return coverages


def meritz_table_extraction(pdf_path: str, insurer: str) -> List[Dict[str, str]]:
    """
    STEP NEXT-32: Meritz-specific table extraction

    Meritz 가입설계서의 table 구조:
    - "가입담보" 테이블: 담보명이 3번째 열(index 2)
    - Col 0: 카테고리 ("수술", "골절/화상" 등) - 헤더 오염 원인
    - Col 1: 담보 코드
    - Col 2: 담보명 (실제 coverage)

    Args:
        pdf_path: PDF file path
        insurer: "meritz"

    Returns:
        List of coverage dicts
    """
    coverages = []
    seen = set()

    # Meritz-specific category headers to exclude
    category_headers = [
        '수술', '골절/화상', '기타', '할증/제도성', '사망후유', '입원일당',
        '암/3대질병/장해', '진단', '수술/치료', '통원', '간병', '치과',
        '기본계약', '선택계약', '가입담보', '담보사항'
    ]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Meritz pattern: "가입담보" header with "가입금액" column
                header_text = ' '.join(str(cell) for row in table[:2] for cell in row if cell)
                is_coverage_table = '가입담보' in header_text and '가입금액' in header_text

                if not is_coverage_table:
                    continue

                # Meritz: 담보명은 3번째 열(index 2)
                coverage_col_idx = 2

                # Extract coverages from table rows (skip header row 0)
                for row in table[1:]:
                    if len(row) <= coverage_col_idx:
                        continue

                    cell_value = row[coverage_col_idx]
                    if not cell_value:
                        continue

                    coverage_name = str(cell_value).strip()

                    # Meritz-specific: Remove leading code numbers (e.g., "180 담보명" -> "담보명")
                    coverage_name = re.sub(r'^\d+\s+', '', coverage_name)

                    # Filter out category headers (from Col 0)
                    if coverage_name in category_headers:
                        continue

                    # General filters
                    if len(coverage_name) < 3:
                        continue

                    # 금액값 제거
                    if re.match(r'^[\d,]+(만|천|억|조)?원$', coverage_name):
                        continue

                    # 코드만 있는 경우 제외
                    if re.match(r'^\d+$', coverage_name):
                        continue

                    if any(x in coverage_name for x in ['합계', '총액', '계약자', '피보험자',
                                                        '설계번호', '발행정보', '영업담당자']):
                        continue

                    # Meritz-specific: "자동갱신특약" 같은 제도성 특약 제외
                    if '자동갱신' in coverage_name or '특약' == coverage_name:
                        continue

                    # 긴 설명문 제외 (보장내용 설명)
                    if len(coverage_name) > 100:
                        continue

                    # 주석/설명문 제외
                    if coverage_name.startswith('※') or coverage_name.startswith('◆') or coverage_name.startswith('-'):
                        continue

                    if coverage_name not in seen:
                        seen.add(coverage_name)
                        coverages.append({
                            "coverage_name_raw": coverage_name,
                            "insurer": insurer,
                            "source_page": page_num
                        })

    return coverages


def enhanced_table_extraction(pdf_path: str, insurer: str) -> List[Dict[str, str]]:
    """
    강화된 담보 추출 로직

    - 헤더 패턴 확장
    - 특약 표 별도 탐색
    - 종료 조건 강화
    - STEP NEXT-32: Samsung/Meritz table-first extraction
    """
    # STEP NEXT-32: Insurer-specific table extraction
    if insurer == 'samsung':
        return samsung_table_extraction(pdf_path, insurer)
    elif insurer == 'meritz':
        return meritz_table_extraction(pdf_path, insurer)

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


def is_header_pollution(coverage_name: str) -> bool:
    """
    STEP NEXT-32-γ: Header pollution detection (exact match only)

    Detects if a coverage name is likely a header/section/metadata text.
    Uses ONLY explicit keyword matching - no heuristics.

    Args:
        coverage_name: Coverage name to check

    Returns:
        True if likely pollution, False otherwise
    """
    # STEP NEXT-32-γ: Exact match pollution keywords only
    POLLUTION_EXACT_KEYWORDS = {
        '갱신형', '무해지', '표준형', '선택', '기본',
        '제도성', '할증', '가입담보', '담보사항', '계약', '특약',
        '기본계약', '보장내용', '가입안내', '유의사항', '알려드립니다',
        '보험료', '납입', '계약자', '피보험자', '기본정보', '용어설명', '예시',
        '합계', '총액', '광화문', '준법감시', '설계번호', '발행일', '표', '계',
        '보장명', '담보명', '가입금액', '보장', '보험', '주의', '안내'
    }

    # Exact match only
    if coverage_name in POLLUTION_EXACT_KEYWORDS:
        return True

    # List markers at start
    if re.match(r'^[0-9]+\)|^※|^-\s|^▶|^☞|^\*', coverage_name):
        return True

    return False


def calculate_header_pollution_rate(
    coverages: List[Dict[str, str]],
    with_samples: bool = False
) -> Tuple:
    """
    STEP NEXT-32-γ: Calculate header pollution rate (backward compatible)

    Args:
        coverages: List of coverage dicts
        with_samples: If True, return (count, rate, samples). If False, return (count, rate).

    Returns:
        (pollution_count, pollution_rate_percent) if with_samples=False
        (pollution_count, pollution_rate_percent, pollution_samples) if with_samples=True
    """
    if not coverages:
        if with_samples:
            return 0, 0.0, []
        return 0, 0.0

    # Identify polluted coverage names
    polluted = [cov['coverage_name_raw'] for cov in coverages if is_header_pollution(cov['coverage_name_raw'])]

    pollution_count = len(polluted)
    pollution_rate = (pollution_count / len(coverages)) * 100

    if with_samples:
        # Return top 5 samples for debugging/verification
        pollution_samples = polluted[:5]
        return pollution_count, pollution_rate, pollution_samples
    else:
        return pollution_count, pollution_rate


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
