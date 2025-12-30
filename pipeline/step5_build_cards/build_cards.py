"""
Step 5: Build Coverage Cards

입력:
- data/scope/{INSURER}_scope_mapped.csv
- data/evidence_pack/{INSURER}_evidence_pack.jsonl

출력:
- data/compare/{INSURER}_coverage_cards.jsonl
"""

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.scope_gate import load_scope_gate, resolve_scope_csv
from core.compare_types import CoverageCard, Evidence, CompareStats


def _select_diverse_evidences(evidences: List[Evidence], max_count: int = 3) -> List[Evidence]:
    """
    STEP 6-ε.2: Doc-Type Diversity Evidence Selection with Dedup + Real-Fallback Priority LOCK

    Args:
        evidences: 전체 evidence 목록
        max_count: 최대 선택 개수 (기본 3)

    Returns:
        List[Evidence]: 선택된 evidence (최대 max_count개, 중복 제거됨)

    규칙:
        Rule 6-ε.2.1: Evidence Dedup (LOCK)
            - (doc_type, file_path, page, snippet) 기준 중복 제거
        Rule 6-ε.2.2: Fallback 판정 보정 (LOCK)
            - 'fallback_' 포함 OR 'token_and(' 시작 → fallback
        Rule 6-ε.2.3: Evidence Selection Priority (최종 LOCK)
            1. Non-fallback 우선
            2. doc_type priority: 약관 > 사업방법서 > 상품요약서
            3. page 오름차순
            4. file_path 오름차순
            5. snippet 오름차순 (동률 방지)
        Rule 6-ε.2.4: Fill-up 유지 (LOCK)
            - 중복 제거 후에도 max_count까지 보충
    """
    if not evidences:
        return []

    # Helper: dedup key (Rule 6-ε.2.1)
    def dedup_key(ev: Evidence) -> tuple:
        return (ev.doc_type, ev.file_path, ev.page, ev.snippet)

    # Helper: fallback 판정 (Rule 6-ε.2.2 — 보정)
    def is_fallback(ev: Evidence) -> bool:
        if not ev.match_keyword:
            return False
        mk_lower = ev.match_keyword.lower()
        # 'fallback_' 포함 OR 'token_and(' 시작
        return 'fallback_' in mk_lower or ev.match_keyword.startswith('token_and(')

    # Helper: doc_type priority index
    doc_type_priority_map = {
        '약관': 0,
        '사업방법서': 1,
        '상품요약서': 2
    }

    def doc_type_priority_index(ev: Evidence) -> int:
        return doc_type_priority_map.get(ev.doc_type, 999)

    # Helper: sort key (Rule 6-ε.2.3)
    def sort_key(ev: Evidence):
        return (
            is_fallback(ev),           # 1. Non-fallback 우선
            doc_type_priority_index(ev),  # 2. doc_type priority
            ev.page,                   # 3. page 오름차순
            ev.file_path,              # 4. file_path 오름차순
            ev.snippet                 # 5. snippet 오름차순 (동률 방지)
        )

    # 중복 제거 (Rule 6-ε.2.1)
    seen_keys = set()
    unique_evidences = []
    for ev in evidences:
        key = dedup_key(ev)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_evidences.append(ev)

    # 1차 선택 (Diversity pass): 약관/사업방법서/상품요약서 각 1개씩
    by_doc_type = {}
    for ev in unique_evidences:
        doc_type = ev.doc_type
        if doc_type not in by_doc_type:
            by_doc_type[doc_type] = []
        by_doc_type[doc_type].append(ev)

    # 각 doc_type 내에서 정렬
    for doc_type in by_doc_type:
        by_doc_type[doc_type].sort(key=sort_key)

    selected = []
    doc_type_priority = ['약관', '사업방법서', '상품요약서']

    # 1차 선택: 각 doc_type에서 1개씩
    for doc_type in doc_type_priority:
        if doc_type in by_doc_type and len(selected) < max_count:
            selected.append(by_doc_type[doc_type][0])

    # 2차 보충 (Fill-up pass): max_count까지 채우기 (Rule 6-ε.2.4)
    if len(selected) < max_count:
        # 선택되지 않은 evidence pool 구축 (이미 중복 제거된 unique_evidences 사용)
        selected_set = set(id(ev) for ev in selected)
        remaining = [ev for ev in unique_evidences if id(ev) not in selected_set]

        # 정렬 후 부족분 채우기
        remaining.sort(key=sort_key)
        for ev in remaining:
            if len(selected) >= max_count:
                break
            selected.append(ev)

    return selected[:max_count]


def build_coverage_cards(
    scope_mapped_csv: str,
    evidence_pack_jsonl: str,
    insurer: str,
    output_cards_jsonl: str
) -> CompareStats:
    """
    Coverage cards 생성

    Args:
        scope_mapped_csv: scope mapped CSV 경로
        evidence_pack_jsonl: evidence pack JSONL 경로
        insurer: 보험사명
        output_cards_jsonl: 출력 cards JSONL 경로

    Returns:
        CompareStats: 통계
    """
    # Scope gate 로드
    scope_gate = load_scope_gate(insurer)

    # Scope mapped CSV 읽기
    scope_data = {}
    with open(scope_mapped_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coverage_name_raw = row['coverage_name_raw']

            # Scope gate 검증
            if not scope_gate.is_in_scope(coverage_name_raw):
                continue

            scope_data[coverage_name_raw] = {
                'coverage_code': row.get('coverage_code', ''),
                'coverage_name_canonical': row.get('coverage_name_canonical', ''),
                'mapping_status': row['mapping_status']
            }

    # Evidence pack JSONL 읽기
    evidence_data = {}
    with open(evidence_pack_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                coverage_name_raw = item['coverage_name_raw']

                # Scope gate 검증
                if not scope_gate.is_in_scope(coverage_name_raw):
                    continue

                evidences = [Evidence.from_dict(e) for e in item.get('evidences', [])]
                hits_by_doc_type = item.get('hits_by_doc_type', {})
                flags = item.get('flags', [])
                evidence_data[coverage_name_raw] = {
                    'evidences': evidences,
                    'hits_by_doc_type': hits_by_doc_type,
                    'flags': flags
                }

    # Coverage cards 생성
    cards: List[CoverageCard] = []
    stats = {
        'total': 0,
        'matched': 0,
        'unmatched': 0,
        'evidence_found': 0,
        'evidence_not_found': 0
    }

    for coverage_name_raw, scope_info in scope_data.items():
        stats['total'] += 1

        # Mapping status
        mapping_status = scope_info['mapping_status']
        if mapping_status == 'matched':
            stats['matched'] += 1
        else:
            stats['unmatched'] += 1

        # Evidence status
        ev_data = evidence_data.get(coverage_name_raw, {'evidences': [], 'hits_by_doc_type': {}, 'flags': []})
        evidences = ev_data['evidences']
        hits_by_doc_type = ev_data['hits_by_doc_type']
        flags = ev_data['flags']
        evidence_status = 'found' if evidences else 'not_found'

        if evidence_status == 'found':
            stats['evidence_found'] += 1
        else:
            stats['evidence_not_found'] += 1

        # Coverage code/canonical (없으면 None)
        coverage_code = scope_info['coverage_code'] if scope_info['coverage_code'] else None
        coverage_name_canonical = scope_info['coverage_name_canonical'] if scope_info['coverage_name_canonical'] else None

        # STEP 6-ε: Doc-Type Diversity Evidence Selection (최대 3개)
        selected_evidences = _select_diverse_evidences(evidences, max_count=3)

        # Card 생성
        card = CoverageCard(
            insurer=insurer,
            coverage_name_raw=coverage_name_raw,
            coverage_code=coverage_code,
            coverage_name_canonical=coverage_name_canonical,
            mapping_status=mapping_status,
            evidence_status=evidence_status,
            evidences=selected_evidences,
            hits_by_doc_type=hits_by_doc_type,
            flags=flags
        )
        cards.append(card)

    # 정렬
    cards.sort(key=lambda c: c.sort_key())

    # JSONL 저장
    with open(output_cards_jsonl, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + '\n')

    # 통계 반환
    return CompareStats(
        total_coverages=stats['total'],
        matched=stats['matched'],
        unmatched=stats['unmatched'],
        evidence_found=stats['evidence_found'],
        evidence_not_found=stats['evidence_not_found']
    )


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Build coverage cards')
    parser.add_argument('--insurer', type=str, default='samsung', help='보험사명')
    args = parser.parse_args()

    insurer = args.insurer
    base_dir = Path(__file__).parent.parent.parent

    # STEP NEXT-18X: Use canonical resolver
    scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
    evidence_pack_jsonl = base_dir / "data" / "evidence_pack" / f"{insurer}_evidence_pack.jsonl"

    # 출력 파일
    output_cards_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards.jsonl"
    output_cards_jsonl.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Step 5] Build Coverage Cards")
    print(f"[Step 5] Insurer: {insurer}")
    print(f"[Step 5] Input scope: {scope_mapped_csv}")
    print(f"[Step 5] Input evidence: {evidence_pack_jsonl}")

    # Cards 생성
    stats = build_coverage_cards(
        str(scope_mapped_csv),
        str(evidence_pack_jsonl),
        insurer,
        str(output_cards_jsonl)
    )

    print(f"\n[Step 5] Coverage cards created:")
    print(f"  - Total coverages: {stats.total_coverages}")
    print(f"  - Matched: {stats.matched}")
    print(f"  - Unmatched: {stats.unmatched}")
    print(f"  - Evidence found: {stats.evidence_found}")
    print(f"  - Evidence not found: {stats.evidence_not_found}")
    print(f"\n✓ Cards: {output_cards_jsonl}")


if __name__ == "__main__":
    main()
