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

from core.scope_gate import load_scope_gate
from core.compare_types import CoverageCard, Evidence, CompareStats


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

        # Card 생성
        card = CoverageCard(
            insurer=insurer,
            coverage_name_raw=coverage_name_raw,
            coverage_code=coverage_code,
            coverage_name_canonical=coverage_name_canonical,
            mapping_status=mapping_status,
            evidence_status=evidence_status,
            evidences=evidences[:3],  # 최대 3개
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

    # 입력 파일
    scope_mapped_csv = base_dir / "data" / "scope" / f"{insurer}_scope_mapped.csv"
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
