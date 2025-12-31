"""
Step 4: Evidence Search (Deterministic, No LLM, No Embedding)

입력:
- data/scope/{INSURER}_scope_mapped.csv
- data/evidence_text/{INSURER}/**/*.page.jsonl

출력:
- data/evidence_pack/{INSURER}_evidence_pack.jsonl
- data/scope/{INSURER}_unmatched_review.csv
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import sys

# scope_gate import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.scope_gate import load_scope_gate


class EvidenceSearcher:
    """담보별 evidence 검색 (deterministic)"""

    # 문서 타입 우선순위
    DOC_TYPE_PRIORITY = {
        '약관': 1,
        '사업방법서': 2,
        '상품요약서': 3,
        '상품설명서': 3
    }

    def __init__(self, evidence_text_dir: str, insurer: str):
        self.evidence_text_dir = Path(evidence_text_dir) / insurer
        self.insurer = insurer
        self.text_data = self._load_all_text_data()

    def _normalize(self, text: str) -> str:
        """
        텍스트 정규화 (검색용)

        Args:
            text: 원본 텍스트

        Returns:
            str: 정규화된 텍스트
        """
        # 공백 제거
        text = re.sub(r'\s+', '', text)
        # 특수문자 제거 (한글, 영문, 숫자, 괄호만 유지)
        text = re.sub(r'[^가-힣a-zA-Z0-9()]', '', text)
        return text.lower()

    def _generate_hyundai_query_variants(self, coverage_name: str) -> List[str]:
        """
        현대 전용: 담보명에서 query variants 생성 (suffix 제거)

        Args:
            coverage_name: 담보명 (raw 또는 canonical)

        Returns:
            List[str]: query variants (최대 4개)
        """
        variants = [coverage_name]  # 원본 포함

        # Rule (a): 끝 suffix 제거 - 담보, 특약, 보장, 보장특약
        suffixes = ['보장특약', '담보', '특약', '보장']  # 긴 것부터 매칭
        for suffix in suffixes:
            if coverage_name.endswith(suffix):
                variants.append(coverage_name[:-len(suffix)])
                break

        # Rule (b): 진단비 <-> 진단 변환
        if '진단비' in coverage_name:
            variants.append(coverage_name.replace('진단비', '진단'))
        elif '진단' in coverage_name and '진단비' not in coverage_name:
            variants.append(coverage_name.replace('진단', '진단비'))

        # Rule (c): 공백 정리 (연속 공백 → 1개, 양끝 trim)
        cleaned = re.sub(r'\s+', ' ', coverage_name).strip()
        if cleaned != coverage_name:
            variants.append(cleaned)

        # 중복 제거, 순서 유지
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique_variants.append(v)

        return unique_variants[:4]  # 최대 4개

    def _generate_hanwha_query_variants(self, coverage_name: str) -> List[str]:
        """
        한화 전용: 담보명에서 query variants 생성 (암 용어 브릿지)

        Args:
            coverage_name: 담보명 (raw 또는 canonical)

        Returns:
            List[str]: query variants (최대 6개)
        """
        variants = [coverage_name]  # 원본 포함

        # Rule (a): 끝 suffix 제거 - 담보, 특약, 보장, 보장특약
        suffixes = ['보장특약', '담보', '특약', '보장']  # 긴 것부터 매칭
        for suffix in suffixes:
            if coverage_name.endswith(suffix):
                variants.append(coverage_name[:-len(suffix)])
                break

        # Rule (b): 진단비 <-> 진단 변환
        if '진단비' in coverage_name:
            variants.append(coverage_name.replace('진단비', '진단'))
        elif '진단' in coverage_name and '진단비' not in coverage_name:
            variants.append(coverage_name.replace('진단', '진단비'))

        # Rule (c): 암 용어 브릿지 (hanwha-specific)
        # 4대유사암 ↔ 유사암(4대) ↔ 유사암
        if '유사암(4대)' in coverage_name or '유사암(8대)' in coverage_name:
            variants.append(coverage_name.replace('유사암(4대)', '4대유사암'))
            variants.append(coverage_name.replace('유사암(8대)', '8대유사암'))
            variants.append(coverage_name.replace('유사암(4대)', '유사암'))
            variants.append(coverage_name.replace('유사암(8대)', '유사암'))
        if '4대유사암' in coverage_name:
            variants.append(coverage_name.replace('4대유사암', '유사암(4대)'))
            variants.append(coverage_name.replace('4대유사암', '유사암'))
        if '8대유사암' in coverage_name:
            variants.append(coverage_name.replace('8대유사암', '유사암(8대)'))
            variants.append(coverage_name.replace('8대유사암', '유사암'))

        # 통합암(4대유사암제외) variants
        if '통합암(4대유사암제외)' in coverage_name:
            variants.append(coverage_name.replace('통합암(4대유사암제외)', '통합암'))
            variants.append(coverage_name.replace('통합암(4대유사암제외)', '4대유사암제외'))
            variants.append(coverage_name.replace('통합암(4대유사암제외)', '유사암제외'))

        # 4대유사암제외 variants
        if '4대유사암제외' in coverage_name:
            variants.append(coverage_name.replace('4대유사암제외', '유사암제외'))
            variants.append(coverage_name.replace('4대유사암제외', '유사암'))

        # 4대특정암 ↔ 특정암
        if '4대특정암' in coverage_name:
            variants.append(coverage_name.replace('4대특정암', '특정암'))

        # Rule (d): Top-6 suffix variants (θ)
        # 1. 치료비 ↔ 치료
        if '치료비' in coverage_name:
            variants.append(coverage_name.replace('치료비', '치료'))
        elif '치료' in coverage_name and '치료비' not in coverage_name:
            variants.append(coverage_name.replace('치료', '치료비'))

        # 2. 입원일당 ↔ 입원
        if '입원일당' in coverage_name:
            variants.append(coverage_name.replace('입원일당', '입원'))
        elif '입원' in coverage_name and '입원일당' not in coverage_name:
            variants.append(coverage_name.replace('입원', '입원일당'))

        # 3. 수술비 ↔ 수술
        if '수술비' in coverage_name:
            variants.append(coverage_name.replace('수술비', '수술'))
        elif '수술' in coverage_name and '수술비' not in coverage_name:
            variants.append(coverage_name.replace('수술', '수술비'))

        # 4. 항암치료 ↔ 항암
        if '항암치료' in coverage_name:
            variants.append(coverage_name.replace('항암치료', '항암'))
        elif '항암' in coverage_name and '항암치료' not in coverage_name:
            variants.append(coverage_name.replace('항암', '항암치료'))

        # 5. 표적항암 ↔ 표적
        if '표적항암' in coverage_name:
            variants.append(coverage_name.replace('표적항암', '표적'))
        elif '표적' in coverage_name and '표적항암' not in coverage_name:
            variants.append(coverage_name.replace('표적', '표적항암'))

        # 6. 재진단암 ↔ 재진단
        if '재진단암' in coverage_name:
            variants.append(coverage_name.replace('재진단암', '재진단'))
        elif '재진단' in coverage_name and '재진단암' not in coverage_name:
            variants.append(coverage_name.replace('재진단', '재진단암'))

        # STEP 4-λ Fallback #2: Bracket / Suffix Normalization (Hanwha)
        # 괄호 제거 버전 추가
        if '(' in coverage_name and ')' in coverage_name:
            # 괄호 전체 제거
            no_bracket = re.sub(r'\([^)]*\)', '', coverage_name)
            variants.append(no_bracket)

            # 괄호 내부만 제거 (외부 유지)
            inside_bracket = re.sub(r'[()]', '', coverage_name)
            variants.append(inside_bracket)

        # suffix 제거 (fallback용 - 더 공격적)
        fallback_suffixes = ['담보', '보장', '특약', '갱신형', '비갱신형']
        for suffix in fallback_suffixes:
            if coverage_name.endswith(suffix):
                variants.append(coverage_name[:-len(suffix)])

        # 중복 제거, 순서 유지
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique_variants.append(v)

        return unique_variants[:6]  # 최대 6개

    def _load_all_text_data(self) -> Dict[str, List[Dict]]:
        """
        모든 JSONL 파일 로드

        Returns:
            Dict[doc_type, List[page_data]]
        """
        text_data = {}

        if not self.evidence_text_dir.exists():
            return text_data

        for jsonl_file in self.evidence_text_dir.rglob('*.page.jsonl'):
            # doc_type은 parent directory
            doc_type = jsonl_file.parent.name

            pages = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        page_data = json.loads(line)
                        page_data['file_path'] = str(jsonl_file)
                        page_data['doc_type'] = doc_type
                        pages.append(page_data)

            if doc_type not in text_data:
                text_data[doc_type] = []
            text_data[doc_type].extend(pages)

        return text_data

    def _extract_snippet(self, text: str, keyword: str, context_lines: int = 2) -> List[str]:
        """
        키워드 포함 라인 + 전후 context 추출

        Args:
            text: 전체 텍스트
            keyword: 검색 키워드
            context_lines: 전후 라인 수

        Returns:
            List[str]: snippet 리스트
        """
        lines = text.split('\n')
        normalized_keyword = self._normalize(keyword)
        snippets = []

        for i, line in enumerate(lines):
            normalized_line = self._normalize(line)

            if normalized_keyword in normalized_line:
                # 전후 context_lines만큼 추출
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)

                snippet_lines = lines[start:end]
                snippet = '\n'.join(snippet_lines).strip()

                if snippet:
                    snippets.append(snippet)

        return snippets

    def _extract_core_tokens(self, coverage_name: str) -> List[str]:
        """
        STEP 4-λ Fallback #1: 담보명에서 핵심 토큰 추출

        Args:
            coverage_name: 담보명 (raw 또는 canonical)

        Returns:
            List[str]: 핵심 토큰 (한글 2자 이상만)
        """
        # 제외 토큰 리스트
        exclude_tokens = {'비', '형', '담보', '보장', '특약', '갱신', '무배당', '갱신형', '비갱신형'}

        # 괄호 제거
        no_bracket = re.sub(r'\([^)]*\)', '', coverage_name)

        # 한글 토큰만 추출 (연속된 한글 2자 이상)
        tokens = re.findall(r'[가-힣]{2,}', no_bracket)

        # 제외 토큰 필터링
        core_tokens = [t for t in tokens if t not in exclude_tokens]

        return core_tokens

    def _kb_bm_a4200_1_definition_hit(self, pages: List[Dict]) -> Dict:
        """
        STEP 6-δ.1: KB 사업방법서 A4200_1 정의 Hit 판정 (snippet 품질 개선)

        Args:
            pages: 사업방법서 페이지 데이터 목록

        Returns:
            Dict: {'hit': bool, 'snippet': str, 'page': int, 'file_path': str}
        """
        # STEP 6-δ.1: Snippet 후보 점수화
        best_candidate = None
        best_score = 0

        for page_data in pages:
            text = page_data['text']
            lines = text.split('\n')
            page = page_data['page']
            file_path = page_data['file_path']

            # 각 라인 점수화
            for i, line in enumerate(lines):
                # 필수 토큰 체크 (ALL REQUIRED)
                has_cancer_diagnosis = '암진단비' in line
                has_similar_cancer = '유사암' in line
                has_exclude = '제외' in line or '유사암제외' in line

                # 필수 토큰이 모두 없으면 skip
                if not (has_cancer_diagnosis and has_similar_cancer and has_exclude):
                    continue

                # 점수 계산
                score = 0
                if has_cancer_diagnosis:
                    score += 1
                if has_similar_cancer:
                    score += 1
                if has_exclude:
                    score += 1
                if '보험금' in line or '지급' in line:
                    score += 1

                # score < 3은 폐기
                if score < 3:
                    continue

                # 최고 점수 갱신
                if score > best_score:
                    best_score = score
                    # snippet: 선택된 라인 기준 위아래 4줄 (총 9줄)
                    start = max(0, i - 4)
                    end = min(len(lines), i + 5)
                    snippet_lines = lines[start:end]
                    snippet = '\n'.join(snippet_lines).strip()[:500]

                    best_candidate = {
                        'hit': True,
                        'snippet': snippet,
                        'page': page,
                        'file_path': file_path
                    }

        # 최고 점수 후보 반환
        if best_candidate:
            return best_candidate

        # No hit
        return {'hit': False, 'snippet': '', 'page': 0, 'file_path': ''}

    def _fallback_token_and_search(
        self,
        coverage_name: str,
        doc_type: str,
        pages: List[Dict],
        max_evidences: int = 3
    ) -> List[Dict]:
        """
        STEP 4-λ Fallback #1: Token-AND Search

        Args:
            coverage_name: 담보명
            doc_type: 문서 타입
            pages: 페이지 데이터 목록
            max_evidences: 최대 evidence 수

        Returns:
            List[Dict]: fallback evidences
        """
        core_tokens = self._extract_core_tokens(coverage_name)

        # 핵심 토큰이 2개 미만이면 fallback 불가
        if len(core_tokens) < 2:
            return []

        fallback_evidences = []

        for page_data in pages:
            if len(fallback_evidences) >= max_evidences:
                break

            text = page_data['text']
            page_lines = text.split('\n')

            for i, line in enumerate(page_lines):
                if len(fallback_evidences) >= max_evidences:
                    break

                # 동일 라인 내 핵심 토큰 >= 2개 동시 존재 검사
                token_count = sum(1 for token in core_tokens if token in line)

                if token_count >= 2:
                    # Context 추출
                    start = max(0, i - 2)
                    end = min(len(page_lines), i + 3)
                    snippet_lines = page_lines[start:end]
                    snippet = '\n'.join(snippet_lines).strip()

                    if snippet:
                        evidence = {
                            'doc_type': doc_type,
                            'file_path': page_data['file_path'],
                            'page': page_data['page'],
                            'snippet': snippet[:500],
                            'match_keyword': f"token_and({','.join(core_tokens[:2])})"
                        }
                        fallback_evidences.append(evidence)

        return fallback_evidences

    def search_coverage_evidence(
        self,
        coverage_name_raw: str,
        coverage_name_canonical: Optional[str] = None,
        mapping_status: str = "matched",
        coverage_code: Optional[str] = None,
        max_evidences_per_type: int = 3,
        coverage_name_search_key: Optional[str] = None
    ) -> Dict:
        """
        담보별 evidence 검색 (문서 타입별 독립 검색 강제)

        STEP NEXT-34-ε: Use search_key for exact match stability (newline-only removal)

        Args:
            coverage_name_raw: 원본 담보명 (SSOT, unchanged)
            coverage_name_canonical: 표준 담보명 (matched인 경우)
            mapping_status: matched | unmatched
            coverage_code: 담보 코드 (STEP 6-δ 전용)
            max_evidences_per_type: 문서 타입별 최대 evidence 수
            coverage_name_search_key: 검색용 키 (newline removed, fallback to raw if None)

        Returns:
            Dict: {
                'evidences': List[Dict],
                'hits_by_doc_type': Dict[str, int],
                'flags': List[str]
            }
        """
        # STEP NEXT-34-ε: Use search_key for exact match (fallback to raw if None)
        search_raw = coverage_name_search_key if coverage_name_search_key else coverage_name_raw

        # 검색 키워드 결정
        if mapping_status == "matched" and coverage_name_canonical:
            # Canonical 우선, search_raw도 함께 검색
            keywords = [coverage_name_canonical, search_raw]
        else:
            # Unmatched는 search_raw만
            keywords = [search_raw]

        # 현대 전용: query variants 생성
        if self.insurer == 'hyundai':
            expanded_keywords = []
            for kw in keywords:
                variants = self._generate_hyundai_query_variants(kw)
                expanded_keywords.extend(variants)
            # 중복 제거
            seen = set()
            keywords = []
            for kw in expanded_keywords:
                if kw not in seen:
                    seen.add(kw)
                    keywords.append(kw)

        # 한화 전용: query variants 생성
        if self.insurer == 'hanwha':
            expanded_keywords = []
            for kw in keywords:
                variants = self._generate_hanwha_query_variants(kw)
                expanded_keywords.extend(variants)
            # 중복 제거
            seen = set()
            keywords = []
            for kw in expanded_keywords:
                if kw not in seen:
                    seen.add(kw)
                    keywords.append(kw)

        # 문서 타입별 hit 카운트 초기화 (필수 3개 타입)
        hits_by_doc_type = {
            '약관': 0,
            '사업방법서': 0,
            '상품요약서': 0
        }

        # 문서 타입별로 우선순위 순서로 검색
        sorted_doc_types = sorted(
            self.text_data.keys(),
            key=lambda dt: self.DOC_TYPE_PRIORITY.get(dt, 999)
        )

        all_evidences = []

        # 각 문서 타입에 대해 독립적으로 검색 (필수)
        for doc_type in sorted_doc_types:
            pages = self.text_data[doc_type]
            doc_type_evidences = []

            for page_data in pages:
                if len(doc_type_evidences) >= max_evidences_per_type:
                    break

                text = page_data['text']

                for keyword in keywords:
                    snippets = self._extract_snippet(text, keyword)

                    for snippet in snippets:
                        if len(doc_type_evidences) >= max_evidences_per_type:
                            break

                        evidence = {
                            'doc_type': doc_type,
                            'file_path': page_data['file_path'],
                            'page': page_data['page'],
                            'snippet': snippet[:500],  # 최대 500자
                            'match_keyword': keyword
                        }
                        doc_type_evidences.append(evidence)

            # 문서 타입별 hit 수 기록
            # 상품설명서는 상품요약서로 통합
            normalized_doc_type = '상품요약서' if doc_type == '상품설명서' else doc_type
            if normalized_doc_type in hits_by_doc_type:
                hits_by_doc_type[normalized_doc_type] += len(doc_type_evidences)

            all_evidences.extend(doc_type_evidences)

        # STEP 4-λ Fallback #1: Token-AND Search (Hanwha only)
        # 조건: phrase/variant 검색 실패 시에만 발동
        fallback_flags = []
        if self.insurer == 'hanwha' and len(all_evidences) == 0:
            for doc_type in sorted_doc_types:
                pages = self.text_data[doc_type]
                fallback_evidences = self._fallback_token_and_search(
                    coverage_name_raw,
                    doc_type,
                    pages,
                    max_evidences=max_evidences_per_type
                )

                if fallback_evidences:
                    # 문서 타입별 hit 수 업데이트
                    normalized_doc_type = '상품요약서' if doc_type == '상품설명서' else doc_type
                    if normalized_doc_type in hits_by_doc_type:
                        hits_by_doc_type[normalized_doc_type] += len(fallback_evidences)

                    all_evidences.extend(fallback_evidences)
                    fallback_flags.append('fallback_token_and')

        # STEP 6-δ: KB 사업방법서 정의 Hit 보정 (A4200_1 ONLY)
        # 조건: kb/A4200_1/사업방법서 + 기존 검색 실패 시에만
        if (self.insurer == 'kb' and
            coverage_code == 'A4200_1' and
            '사업방법서' in self.text_data and
            hits_by_doc_type['사업방법서'] == 0):

            bm_pages = self.text_data['사업방법서']
            hit_result = self._kb_bm_a4200_1_definition_hit(bm_pages)

            if hit_result['hit']:
                # doc_type hit = 1
                hits_by_doc_type['사업방법서'] = 1

                # evidence 1개 추가
                evidence = {
                    'doc_type': '사업방법서',
                    'file_path': hit_result['file_path'],
                    'page': hit_result['page'],
                    'snippet': hit_result['snippet'],
                    'match_keyword': 'kb_bm_definition_hit'
                }
                all_evidences.append(evidence)
                fallback_flags.append('kb_bm_definition_hit')

        # Flags 생성
        flags = []
        # policy_only flag: 약관만 있고 다른 문서는 0건
        if hits_by_doc_type['약관'] >= 1 and hits_by_doc_type['사업방법서'] == 0 and hits_by_doc_type['상품요약서'] == 0:
            flags.append('policy_only')

        # fallback flags 추가
        flags.extend(fallback_flags)

        return {
            'evidences': all_evidences,
            'hits_by_doc_type': hits_by_doc_type,
            'flags': flags
        }


def create_evidence_pack(
    scope_mapped_csv: str,
    evidence_text_dir: str,
    insurer: str,
    output_pack_jsonl: str,
    output_unmatched_csv: str
) -> Dict:
    """
    Evidence pack 생성

    Args:
        scope_mapped_csv: scope mapped CSV 경로
        evidence_text_dir: evidence text 디렉토리
        insurer: 보험사명
        output_pack_jsonl: 출력 evidence pack JSONL
        output_unmatched_csv: 출력 unmatched review CSV

    Returns:
        dict: 통계
    """
    # Scope gate 로드
    scope_gate = load_scope_gate(insurer)

    # Evidence searcher 초기화
    searcher = EvidenceSearcher(evidence_text_dir, insurer)

    # Scope mapped CSV 읽기
    with open(scope_mapped_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        scope_rows = list(reader)

    # Evidence pack 생성
    evidence_pack = []
    unmatched_rows = []
    stats = {'total': 0, 'matched': 0, 'unmatched': 0, 'with_evidence': 0, 'without_evidence': 0}

    for row in scope_rows:
        coverage_name_raw = row['coverage_name_raw']
        # STEP NEXT-34-ε: Read search_key from Step1 output (fallback to raw if missing)
        coverage_name_search_key = row.get('coverage_name_search_key', coverage_name_raw)

        # Scope gate 검증
        if not scope_gate.is_in_scope(coverage_name_raw):
            print(f"[SKIP] Not in scope: {coverage_name_raw}")
            continue

        stats['total'] += 1
        mapping_status = row['mapping_status']
        coverage_code = row.get('coverage_code', '')
        coverage_name_canonical = row.get('coverage_name_canonical', '')

        if mapping_status == 'matched':
            stats['matched'] += 1
        else:
            stats['unmatched'] += 1

        # Evidence 검색 (문서 타입별 독립 검색)
        # STEP NEXT-34-ε: Pass search_key for exact match stability
        search_result = searcher.search_coverage_evidence(
            coverage_name_raw=coverage_name_raw,
            coverage_name_canonical=coverage_name_canonical if coverage_name_canonical else None,
            mapping_status=mapping_status,
            coverage_code=coverage_code if coverage_code else None,
            max_evidences_per_type=3,
            coverage_name_search_key=coverage_name_search_key
        )

        evidences = search_result['evidences']
        hits_by_doc_type = search_result['hits_by_doc_type']
        flags = search_result['flags']

        if evidences:
            stats['with_evidence'] += 1
        else:
            stats['without_evidence'] += 1

        # 로깅: 문서 타입별 hit 수 출력
        print(f"  [{coverage_name_raw}] 약관:{hits_by_doc_type['약관']} 사업방법서:{hits_by_doc_type['사업방법서']} 상품요약서:{hits_by_doc_type['상품요약서']}")

        # Evidence pack 항목
        pack_item = {
            'insurer': insurer,
            'coverage_name_raw': coverage_name_raw,
            'coverage_code': coverage_code if coverage_code else None,
            'mapping_status': mapping_status,
            'needs_alias_review': mapping_status == 'unmatched',
            'evidences': evidences,
            'hits_by_doc_type': hits_by_doc_type,
            'flags': flags
        }
        evidence_pack.append(pack_item)

        # Unmatched review 항목
        if mapping_status == 'unmatched':
            top_hits = ""
            if evidences:
                top_evidence = evidences[0]
                top_hits = f"{top_evidence['doc_type']}/p{top_evidence['page']}: {top_evidence['snippet'][:100]}..."

            unmatched_rows.append({
                'coverage_name_raw': coverage_name_raw,
                'top_hits': top_hits,
                'suggested_canonical_code': ''  # 비워둠
            })

    # STEP NEXT-31-P3: Evidence pack JSONL 저장 (meta record 첫 줄)
    from core.scope_gate import calculate_scope_content_hash
    from datetime import datetime

    # Calculate scope content hash (scope_mapped_csv is already Path or str)
    scope_path = Path(scope_mapped_csv) if not isinstance(scope_mapped_csv, Path) else scope_mapped_csv
    scope_content_hash = calculate_scope_content_hash(scope_path)

    # Write evidence pack with meta record as first line
    with open(output_pack_jsonl, 'w', encoding='utf-8') as f:
        # Write meta record (first line)
        meta_record = {
            'record_type': 'meta',
            'insurer': insurer,
            'scope_file': scope_path.name,
            'scope_content_hash': scope_content_hash,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'schema_version': 'v1'
        }
        f.write(json.dumps(meta_record, ensure_ascii=False) + '\n')

        # Write evidence records
        for item in evidence_pack:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # Unmatched review CSV 저장
    with open(output_unmatched_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['coverage_name_raw', 'top_hits', 'suggested_canonical_code']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unmatched_rows)

    return stats


def main():
    """CLI 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Evidence search')
    parser.add_argument('--insurer', type=str, default='samsung', help='보험사명')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent
    insurer = args.insurer

    # STEP NEXT-31-P1: Use sanitized scope ONLY (same as Step5)
    from core.scope_gate import resolve_scope_csv
    scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")

    # STEP NEXT-31-P1: Hard gate - MUST be sanitized CSV
    if not scope_mapped_csv.name.endswith('.sanitized.csv'):
        raise RuntimeError(
            f"[STEP NEXT-31-P1 GATE] Step4 MUST use sanitized scope CSV.\n"
            f"Found: {scope_mapped_csv.name}\n"
            f"Required: {insurer}_scope_mapped.sanitized.csv\n"
            f"Run step1_sanitize_scope first to generate sanitized CSV."
        )

    evidence_text_dir = base_dir / "data" / "evidence_text"
    output_pack_jsonl = base_dir / "data" / "evidence_pack" / f"{insurer}_evidence_pack.jsonl"
    output_unmatched_csv = base_dir / "data" / "scope" / f"{insurer}_unmatched_review.csv"

    # 출력 디렉토리 생성
    output_pack_jsonl.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Step 4] Evidence Search")
    print(f"[Step 4] Input: {scope_mapped_csv}")
    print(f"[Step 4] Evidence text: {evidence_text_dir}/{insurer}/")

    stats = create_evidence_pack(
        str(scope_mapped_csv),
        str(evidence_text_dir),
        insurer,
        str(output_pack_jsonl),
        str(output_unmatched_csv)
    )

    print(f"\n[Step 4] Evidence pack created:")
    print(f"  - Total coverages: {stats['total']}")
    print(f"  - Matched: {stats['matched']}")
    print(f"  - Unmatched: {stats['unmatched']}")
    print(f"  - With evidence: {stats['with_evidence']}")
    print(f"  - Without evidence: {stats['without_evidence']}")
    print(f"\n✓ Evidence pack: {output_pack_jsonl}")
    print(f"✓ Unmatched review: {output_unmatched_csv}")


if __name__ == "__main__":
    main()
