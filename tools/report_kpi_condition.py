"""
STEP NEXT-76: KPI Condition Quality Report

KPI 조건 추출 품질 리포트 생성:
- 보험사별 조건 추출률
- 조건별 분포 (면책/감액/대기/갱신)
- UNKNOWN 비율
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# 프로젝트 루트
BASE_DIR = Path(__file__).parent.parent


def load_slim_cards(insurer: str) -> List[dict]:
    """Slim coverage cards 로드"""
    cards_path = BASE_DIR / "data" / "compare" / f"{insurer}_coverage_cards_slim.jsonl"

    if not cards_path.exists():
        print(f"[WARNING] Slim cards not found for {insurer}: {cards_path}")
        return []

    cards = []
    with open(cards_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    return cards


def analyze_kpi_conditions(cards: List[dict]) -> dict:
    """KPI 조건 분석"""
    total = len(cards)

    # 조건별 카운트
    waiting_period_count = 0
    reduction_count = 0
    exclusion_count = 0
    renewal_count = 0

    # 조건 값 분포
    waiting_periods = defaultdict(int)
    reductions = defaultdict(int)
    exclusions = defaultdict(int)
    renewals = defaultdict(int)

    # Evidence ref 없음 (추출 실패)
    no_condition_refs = 0

    for card in cards:
        kpi_condition = card.get('kpi_condition')
        if not kpi_condition:
            no_condition_refs += 1
            continue

        # 대기기간
        waiting = kpi_condition.get('waiting_period')
        if waiting:
            waiting_period_count += 1
            waiting_periods[waiting] += 1

        # 감액
        reduction = kpi_condition.get('reduction_condition')
        if reduction:
            reduction_count += 1
            reductions[reduction] += 1

        # 면책
        exclusion = kpi_condition.get('exclusion_condition')
        if exclusion:
            exclusion_count += 1
            exclusions[exclusion] += 1

        # 갱신
        renewal = kpi_condition.get('renewal_condition')
        if renewal:
            renewal_count += 1
            renewals[renewal] += 1

        # Evidence refs
        refs = kpi_condition.get('condition_evidence_refs', [])
        if not refs:
            no_condition_refs += 1

    # 통계 계산
    at_least_one_condition = sum([
        1 for card in cards
        if card.get('kpi_condition') and (
            card['kpi_condition'].get('waiting_period') or
            card['kpi_condition'].get('reduction_condition') or
            card['kpi_condition'].get('exclusion_condition') or
            card['kpi_condition'].get('renewal_condition')
        )
    ])

    return {
        'total': total,
        'at_least_one_condition': at_least_one_condition,
        'waiting_period_count': waiting_period_count,
        'reduction_count': reduction_count,
        'exclusion_count': exclusion_count,
        'renewal_count': renewal_count,
        'waiting_periods': dict(waiting_periods),
        'reductions': dict(reductions),
        'exclusions': dict(exclusions),
        'renewals': dict(renewals),
        'no_condition_refs': no_condition_refs
    }


def print_report(insurer: str, stats: dict):
    """리포트 출력"""
    total = stats['total']

    print(f"\n{'=' * 60}")
    print(f"KPI CONDITION QUALITY REPORT - {insurer.upper()}")
    print(f"{'=' * 60}\n")

    print(f"총 담보 수: {total}")
    print(f"조건 추출 담보 수: {stats['at_least_one_condition']} ({stats['at_least_one_condition']/total*100:.1f}%)\n")

    print(f"조건별 추출 현황:")
    print(f"  - 대기기간: {stats['waiting_period_count']} ({stats['waiting_period_count']/total*100:.1f}%)")
    print(f"  - 감액: {stats['reduction_count']} ({stats['reduction_count']/total*100:.1f}%)")
    print(f"  - 면책: {stats['exclusion_count']} ({stats['exclusion_count']/total*100:.1f}%)")
    print(f"  - 갱신: {stats['renewal_count']} ({stats['renewal_count']/total*100:.1f}%)\n")

    # 대기기간 분포
    if stats['waiting_periods']:
        print(f"대기기간 분포 (Top 5):")
        sorted_waiting = sorted(stats['waiting_periods'].items(), key=lambda x: x[1], reverse=True)[:5]
        for period, count in sorted_waiting:
            print(f"  - {period}: {count}")
        print()

    # 감액 분포
    if stats['reductions']:
        print(f"감액 분포 (Top 5):")
        sorted_reductions = sorted(stats['reductions'].items(), key=lambda x: x[1], reverse=True)[:5]
        for reduction, count in sorted_reductions:
            print(f"  - {reduction}: {count}")
        print()

    # 면책 분포
    if stats['exclusions']:
        print(f"면책 분포 (Top 5):")
        sorted_exclusions = sorted(stats['exclusions'].items(), key=lambda x: x[1], reverse=True)[:5]
        for exclusion, count in sorted_exclusions:
            print(f"  - {exclusion}: {count}")
        print()

    # 갱신 분포
    if stats['renewals']:
        print(f"갱신 분포:")
        sorted_renewals = sorted(stats['renewals'].items(), key=lambda x: x[1], reverse=True)
        for renewal, count in sorted_renewals:
            print(f"  - {renewal}: {count}")
        print()

    # UNKNOWN 비율
    no_condition_rate = stats['no_condition_refs'] / total * 100 if total > 0 else 0
    print(f"Evidence refs 없음: {stats['no_condition_refs']} ({no_condition_rate:.1f}%)")

    # 품질 게이트 체크
    print(f"\n{'=' * 60}")
    print(f"QUALITY GATE CHECK")
    print(f"{'=' * 60}\n")

    # 게이트 1: UNKNOWN 비율 ≤ 30%
    if no_condition_rate <= 30:
        print(f"✓ UNKNOWN 비율: {no_condition_rate:.1f}% (≤ 30%)")
    else:
        print(f"✗ UNKNOWN 비율: {no_condition_rate:.1f}% (> 30%)")

    print()


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python tools/report_kpi_condition.py <insurer1> [insurer2] ...")
        print("Example: python tools/report_kpi_condition.py samsung hanwha")
        sys.exit(1)

    insurers = sys.argv[1:]

    for insurer in insurers:
        cards = load_slim_cards(insurer)
        if not cards:
            continue

        stats = analyze_kpi_conditions(cards)
        print_report(insurer, stats)


if __name__ == "__main__":
    main()
