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

    def search_coverage_evidence(
        self,
        coverage_name_raw: str,
        coverage_name_canonical: Optional[str] = None,
        mapping_status: str = "matched",
        max_evidences_per_type: int = 3
    ) -> Dict:
        """
        담보별 evidence 검색 (문서 타입별 독립 검색 강제)

        Args:
            coverage_name_raw: 원본 담보명
            coverage_name_canonical: 표준 담보명 (matched인 경우)
            mapping_status: matched | unmatched
            max_evidences_per_type: 문서 타입별 최대 evidence 수

        Returns:
            Dict: {
                'evidences': List[Dict],
                'hits_by_doc_type': Dict[str, int],
                'flags': List[str]
            }
        """
        # 검색 키워드 결정
        if mapping_status == "matched" and coverage_name_canonical:
            # Canonical 우선, raw도 함께 검색
            keywords = [coverage_name_canonical, coverage_name_raw]
        else:
            # Unmatched는 raw만
            keywords = [coverage_name_raw]

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

        # Flags 생성
        flags = []
        # policy_only flag: 약관만 있고 다른 문서는 0건
        if hits_by_doc_type['약관'] >= 1 and hits_by_doc_type['사업방법서'] == 0 and hits_by_doc_type['상품요약서'] == 0:
            flags.append('policy_only')

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
        search_result = searcher.search_coverage_evidence(
            coverage_name_raw=coverage_name_raw,
            coverage_name_canonical=coverage_name_canonical if coverage_name_canonical else None,
            mapping_status=mapping_status,
            max_evidences_per_type=3
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

    # Evidence pack JSONL 저장
    with open(output_pack_jsonl, 'w', encoding='utf-8') as f:
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

    scope_mapped_csv = base_dir / "data" / "scope" / f"{insurer}_scope_mapped.csv"
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
