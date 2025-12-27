"""
Step 6: Build Markdown Report

입력:
- data/compare/{INSURER}_coverage_cards.jsonl
- data/scope/{INSURER}_unmatched_review.csv

출력:
- reports/{INSURER}_scope_report.md
"""

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.compare_types import CoverageCard, CompareStats


def build_markdown_report(
    cards_jsonl: str,
    unmatched_review_csv: str,
    insurer: str,
    output_md: str
) -> CompareStats:
    """
    마크다운 리포트 생성

    Args:
        cards_jsonl: coverage cards JSONL 경로
        unmatched_review_csv: unmatched review CSV 경로
        insurer: 보험사명
        output_md: 출력 마크다운 경로

    Returns:
        CompareStats: 통계
    """
    # Cards 로드
    cards: List[CoverageCard] = []
    with open(cards_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                card_data = json.loads(line)
                card = CoverageCard.from_dict(card_data)
                cards.append(card)

    # 통계 계산
    stats = CompareStats(
        total_coverages=len(cards),
        matched=sum(1 for c in cards if c.mapping_status == 'matched'),
        unmatched=sum(1 for c in cards if c.mapping_status == 'unmatched'),
        evidence_found=sum(1 for c in cards if c.evidence_status == 'found'),
        evidence_not_found=sum(1 for c in cards if c.evidence_status == 'not_found')
    )

    # Unmatched review 로드
    unmatched_rows = []
    if Path(unmatched_review_csv).exists():
        with open(unmatched_review_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            unmatched_rows = list(reader)

    # 마크다운 생성
    md_lines = []

    # Title
    md_lines.append(f"# {insurer.upper()} Scope Report")
    md_lines.append("")
    md_lines.append(f"**보험사**: {insurer}")
    md_lines.append("")

    # Summary
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append(f"- **Total Coverages**: {stats.total_coverages}")
    md_lines.append(f"- **Matched**: {stats.matched}")
    md_lines.append(f"- **Unmatched**: {stats.unmatched}")
    md_lines.append(f"- **Evidence Found**: {stats.evidence_found}")
    md_lines.append(f"- **Evidence Not Found**: {stats.evidence_not_found}")
    md_lines.append("")

    # Evidence Source Breakdown (NEW)
    md_lines.append("## Evidence Source Breakdown")
    md_lines.append("")
    md_lines.append("| Coverage | 약관 | 사업방법서 | 상품요약서 | Bias |")
    md_lines.append("|---|---|---|---|---|")

    for card in cards:
        if card.evidence_status == 'found':
            coverage_name = card.coverage_name_canonical or card.coverage_name_raw
            hits = card.hits_by_doc_type
            policy_hits = hits.get('약관', 0)
            method_hits = hits.get('사업방법서', 0)
            summary_hits = hits.get('상품요약서', 0)
            bias = ', '.join(card.flags) if card.flags else ''

            md_lines.append(f"| {coverage_name} | {policy_hits} | {method_hits} | {summary_hits} | {bias} |")

    md_lines.append("")

    # Coverage List
    md_lines.append("## Coverage List")
    md_lines.append("")
    md_lines.append("| Coverage Code | Canonical Name | Raw Name | Evidence | Evidence Sources |")
    md_lines.append("|---|---|---|---|---|")

    for card in cards:
        code = card.coverage_code if card.coverage_code else "-"
        canonical = card.coverage_name_canonical if card.coverage_name_canonical else "-"
        raw = card.coverage_name_raw
        evidence_status = "✓" if card.evidence_status == "found" else "✗"
        evidence_sources = card.get_evidence_source_summary()

        md_lines.append(f"| {code} | {canonical} | {raw} | {evidence_status} | {evidence_sources} |")

    md_lines.append("")

    # Unmatched Review Section
    md_lines.append("## Unmatched Review")
    md_lines.append("")

    if unmatched_rows:
        md_lines.append("| Coverage Name (Raw) | Top Hits | Suggested Canonical Code |")
        md_lines.append("|---|---|---|")

        for row in unmatched_rows:
            coverage_name_raw = row['coverage_name_raw']
            top_hits = row['top_hits'][:100] + "..." if len(row['top_hits']) > 100 else row['top_hits']
            suggested_code = row.get('suggested_canonical_code', '')

            md_lines.append(f"| {coverage_name_raw} | {top_hits} | {suggested_code} |")

        md_lines.append("")
    else:
        md_lines.append("*No unmatched coverages*")
        md_lines.append("")

    # Evidence Not Found Section
    md_lines.append("## Evidence Not Found")
    md_lines.append("")

    not_found_cards = [c for c in cards if c.evidence_status == 'not_found']

    if not_found_cards:
        md_lines.append("| Coverage Name (Raw) | Reason |")
        md_lines.append("|---|---|")

        for card in not_found_cards:
            reason = "검색 결과 0건"
            md_lines.append(f"| {card.coverage_name_raw} | {reason} |")

        md_lines.append("")
    else:
        md_lines.append("*All coverages have evidence*")
        md_lines.append("")

    # 파일 저장
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    return stats


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Build markdown report')
    parser.add_argument('--insurer', type=str, default='samsung', help='보험사명')
    args = parser.parse_args()

    insurer = args.insurer
    base_dir = Path(__file__).parent.parent.parent

    # 입력 파일
    cards_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards.jsonl"
    unmatched_review_csv = base_dir / "data" / "scope" / f"{insurer}_unmatched_review.csv"

    # 출력 파일
    output_md = base_dir / "reports" / f"{insurer}_scope_report.md"

    print(f"[Step 6] Build Markdown Report")
    print(f"[Step 6] Insurer: {insurer}")
    print(f"[Step 6] Input cards: {cards_jsonl}")
    print(f"[Step 6] Input unmatched: {unmatched_review_csv}")

    # 리포트 생성
    stats = build_markdown_report(
        str(cards_jsonl),
        str(unmatched_review_csv),
        insurer,
        str(output_md)
    )

    print(f"\n[Step 6] Report created:")
    print(f"  - Total coverages: {stats.total_coverages}")
    print(f"  - Matched: {stats.matched}")
    print(f"  - Unmatched: {stats.unmatched}")
    print(f"  - Evidence found: {stats.evidence_found}")
    print(f"  - Evidence not found: {stats.evidence_not_found}")
    print(f"\n✓ Report: {output_md}")


if __name__ == "__main__":
    main()
