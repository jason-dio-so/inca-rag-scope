"""
Step 7: Compare Insurers (STEP NEXT-18X-SSOT: NO reports/)

입력:
- data/compare/{INSURER_A}_coverage_cards.jsonl
- data/compare/{INSURER_B}_coverage_cards.jsonl

출력 (SSOT):
- data/compare/{INSURER_A}_vs_{INSURER_B}_compare.jsonl
- data/compare/compare_stats.json

Legacy *.md output removed (no reports/)
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.compare_types import CoverageCard


def compare_insurers(
    insurer_a: str,
    insurer_b: str,
    cards_a_jsonl: str,
    cards_b_jsonl: str,
    output_compare_jsonl: str,
    output_stats_json: str
):
    """
    두 보험사 비교 (SSOT: JSONL + JSON only)

    Args:
        insurer_a: 보험사 A
        insurer_b: 보험사 B
        cards_a_jsonl: 보험사 A coverage cards
        cards_b_jsonl: 보험사 B coverage cards
        output_compare_jsonl: 비교 결과 JSONL
        output_stats_json: 통계 JSON
    """
    # Cards 로드
    cards_a: List[CoverageCard] = []
    with open(cards_a_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                card_data = json.loads(line)
                card = CoverageCard.from_dict(card_data)
                cards_a.append(card)

    cards_b: List[CoverageCard] = []
    with open(cards_b_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                card_data = json.loads(line)
                card = CoverageCard.from_dict(card_data)
                cards_b.append(card)

    # coverage_code 기준으로 join
    cards_a_by_code: Dict[str, CoverageCard] = {}
    for card in cards_a:
        if card.coverage_code:
            cards_a_by_code[card.coverage_code] = card

    cards_b_by_code: Dict[str, CoverageCard] = {}
    for card in cards_b:
        if card.coverage_code:
            cards_b_by_code[card.coverage_code] = card

    # All unique coverage codes
    all_codes = sorted(set(cards_a_by_code.keys()) | set(cards_b_by_code.keys()))

    # 비교 결과 생성
    compare_rows = []
    stats = {
        'total_codes_compared': len(all_codes),
        'both_matched_count': 0,
        'either_unmatched_count': 0,
        'evidence_found_both': 0,
        'evidence_missing_any': 0,
        'only_in_a': 0,
        'only_in_b': 0
    }

    for code in all_codes:
        card_a = cards_a_by_code.get(code)
        card_b = cards_b_by_code.get(code)

        notes = []

        # 카드 정보 추출
        a_info = None
        b_info = None

        if card_a:
            a_info = {
                'raw_name': card_a.coverage_name_raw,
                'matched': card_a.mapping_status == 'matched',
                'evidence_found': card_a.evidence_status == 'found',
                'top_evidence_ref': card_a.get_top_evidence_ref()
            }
            if card_a.mapping_status == 'unmatched':
                notes.append(f"{insurer_a}_unmatched")
            if card_a.evidence_status == 'not_found':
                notes.append(f"{insurer_a}_no_evidence")
            # policy_only flag 추가
            if 'policy_only' in card_a.flags:
                notes.append(f"{insurer_a}_policy_only")
        else:
            notes.append(f"only_in_{insurer_b}")
            stats['only_in_b'] += 1

        if card_b:
            b_info = {
                'raw_name': card_b.coverage_name_raw,
                'matched': card_b.mapping_status == 'matched',
                'evidence_found': card_b.evidence_status == 'found',
                'top_evidence_ref': card_b.get_top_evidence_ref()
            }
            if card_b.mapping_status == 'unmatched':
                notes.append(f"{insurer_b}_unmatched")
            if card_b.evidence_status == 'not_found':
                notes.append(f"{insurer_b}_no_evidence")
            # policy_only flag 추가
            if 'policy_only' in card_b.flags:
                notes.append(f"{insurer_b}_policy_only")
        else:
            notes.append(f"only_in_{insurer_a}")
            stats['only_in_a'] += 1

        # both_policy_only flag
        if card_a and card_b and 'policy_only' in card_a.flags and 'policy_only' in card_b.flags:
            notes.append('both_policy_only')

        # 통계 업데이트
        if card_a and card_b:
            if card_a.mapping_status == 'matched' and card_b.mapping_status == 'matched':
                stats['both_matched_count'] += 1
            else:
                stats['either_unmatched_count'] += 1

            if card_a.evidence_status == 'found' and card_b.evidence_status == 'found':
                stats['evidence_found_both'] += 1
            else:
                stats['evidence_missing_any'] += 1

        # Get canonical name (from either card)
        canonical_name = ''
        if card_a and card_a.coverage_name_canonical:
            canonical_name = card_a.coverage_name_canonical
        elif card_b and card_b.coverage_name_canonical:
            canonical_name = card_b.coverage_name_canonical

        compare_row = {
            'coverage_code': code,
            'canonical_name': canonical_name,
            insurer_a: a_info,
            insurer_b: b_info,
            'notes': notes
        }
        compare_rows.append(compare_row)

    # JSONL 저장
    Path(output_compare_jsonl).parent.mkdir(parents=True, exist_ok=True)
    with open(output_compare_jsonl, 'w', encoding='utf-8') as f:
        for row in compare_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    # 통계 JSON 저장
    with open(output_stats_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # STEP NEXT-18X-SSOT: Legacy report generation removed
    # SSOT: compare_jsonl + stats_json only

    return stats


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Compare insurers')
    parser.add_argument('--insurer-a', type=str, required=True, help='보험사 A')
    parser.add_argument('--insurer-b', type=str, required=True, help='보험사 B')
    args = parser.parse_args()

    insurer_a = args.insurer_a
    insurer_b = args.insurer_b

    base_dir = Path(__file__).parent.parent.parent

    # 입력 파일
    cards_a_jsonl = base_dir / "data" / "compare" / f"{insurer_a}_coverage_cards.jsonl"
    cards_b_jsonl = base_dir / "data" / "compare" / f"{insurer_b}_coverage_cards.jsonl"

    # 출력 파일 (SSOT: no reports/)
    output_compare_jsonl = base_dir / "data" / "compare" / f"{insurer_a}_vs_{insurer_b}_compare.jsonl"
    output_stats_json = base_dir / "data" / "compare" / "compare_stats.json"

    print(f"[Step 7] Compare Insurers (SSOT: JSONL + JSON only)")
    print(f"[Step 7] {insurer_a.upper()} vs {insurer_b.upper()}")
    print(f"[Step 7] Input A: {cards_a_jsonl}")
    print(f"[Step 7] Input B: {cards_b_jsonl}")

    # 비교 실행
    stats = compare_insurers(
        insurer_a,
        insurer_b,
        str(cards_a_jsonl),
        str(cards_b_jsonl),
        str(output_compare_jsonl),
        str(output_stats_json)
    )

    print(f"\n[Step 7] Comparison completed:")
    print(f"  - Total codes compared: {stats['total_codes_compared']}")
    print(f"  - Both matched: {stats['both_matched_count']}")
    print(f"  - Either unmatched: {stats['either_unmatched_count']}")
    print(f"  - Evidence found both: {stats['evidence_found_both']}")
    print(f"  - Evidence missing any: {stats['evidence_missing_any']}")
    print(f"\n✓ Compare JSONL: {output_compare_jsonl}")
    print(f"✓ Stats JSON: {output_stats_json}")


if __name__ == "__main__":
    main()
