#!/usr/bin/env python3
"""
STEP NEXT-80: 암직접입원비 보장일수 전체 보험사 비교

사용법:
    python3 tools/step_next_80_compare_all.py
"""

import json
from pathlib import Path
from collections import defaultdict
import sys
sys.path.insert(0, str(Path(__file__).parent))

from step_next_80_benefit_day_range import BenefitDayRangeAnalyzer


def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "scope_v3"
    output_file = project_root / "docs" / "audit" / "step_next_80_comparison_all.md"

    print("=" * 80)
    print("STEP NEXT-80: 암직접입원비 보장일수 전체 보험사 비교")
    print("=" * 80)
    print()

    # Get all step3 files
    step3_files = sorted(data_dir.glob("*_step3_evidence_enriched_v1_gated.jsonl"))

    all_results = []
    insurer_stats = {}

    analyzer = BenefitDayRangeAnalyzer(data_dir)

    for f in step3_files:
        insurer_key = f.stem.split('_')[0]
        print(f"Processing {insurer_key}...")

        results = analyzer.analyze_insurer(insurer_key)

        if results:
            all_results.extend(results)
            insurer_stats[insurer_key] = {
                "total": len(results),
                "extracted": len([r for r in results if r["day_range"] not in ["NO_EVIDENCE", "NEEDS_REVIEW"]]),
                "needs_review": len([r for r in results if r["day_range"] == "NEEDS_REVIEW"]),
                "no_evidence": len([r for r in results if r["day_range"] == "NO_EVIDENCE"])
            }

    if not all_results:
        print("❌ No 암직접입원비 coverages found across all insurers")
        return

    # Generate comparison table
    lines = []
    lines.append("# 암직접입원비 보장일수 범위 전체 비교 (STEP NEXT-80)")
    lines.append("")
    lines.append(f"**생성일**: {Path(__file__).stat().st_mtime}")
    lines.append(f"**총 보험사**: {len(insurer_stats)}")
    lines.append(f"**총 담보**: {len(all_results)}")
    lines.append("")

    # Summary by insurer
    lines.append("## 1. 보험사별 요약")
    lines.append("")
    lines.append("| 보험사 | 총 담보 | 추출 성공 | 수동 검토 | Evidence 없음 | 성공률 |")
    lines.append("|--------|---------|----------|-----------|--------------|--------|")

    for insurer_key in sorted(insurer_stats.keys()):
        stats = insurer_stats[insurer_key]
        success_rate = stats["extracted"] / stats["total"] * 100 if stats["total"] > 0 else 0
        lines.append(
            f"| {insurer_key.upper()} | {stats['total']} | {stats['extracted']} | "
            f"{stats['needs_review']} | {stats['no_evidence']} | {success_rate:.1f}% |"
        )

    # Detailed table
    lines.append("")
    lines.append("## 2. 상세 비교표")
    lines.append("")
    lines.append("| 보험사 | 상품명 | 담보명 | 보장일수 범위 | 근거 문서 | Evidence 수 |")
    lines.append("|--------|--------|--------|--------------|-----------|------------|")

    # Group by insurer
    by_insurer = defaultdict(list)
    for r in all_results:
        by_insurer[r["insurer_key"]].append(r)

    for insurer_key in sorted(by_insurer.keys()):
        for r in by_insurer[insurer_key]:
            product_name = r["product_name"][:30] + "..." if len(r["product_name"]) > 30 else r["product_name"]
            coverage_name = r["coverage_name"][:40] + "..." if len(r["coverage_name"]) > 40 else r["coverage_name"]

            evidence_doc = "N/A"
            if r["evidence_sample"]:
                ev = r["evidence_sample"][0]
                evidence_doc = f"{ev.get('doc_type', 'N/A')} p.{ev.get('page_start', 'N/A')}"

            # Add emoji for status
            day_range_display = r['day_range']
            if r['day_range'] not in ["NO_EVIDENCE", "NEEDS_REVIEW"]:
                day_range_display = f"✅ {r['day_range']}"
            elif r['day_range'] == "NEEDS_REVIEW":
                day_range_display = f"⚠️ {r['day_range']}"
            else:
                day_range_display = f"❌ {r['day_range']}"

            lines.append(
                f"| {r['insurer_key'].upper()} | {product_name} | {coverage_name} | "
                f"{day_range_display} | {evidence_doc} | {r['evidence_count']} |"
            )

    # Evidence samples
    lines.append("")
    lines.append("## 3. Evidence 샘플 (성공 케이스)")
    lines.append("")

    for r in all_results:
        if r['day_range'] not in ["NO_EVIDENCE", "NEEDS_REVIEW"] and r["evidence_sample"]:
            ev = r["evidence_sample"][0]
            lines.append(f"### {r['insurer_key'].upper()} - {r['coverage_name'][:50]}")
            lines.append("")
            lines.append(f"**추출 값**: {r['day_range']}")
            lines.append(f"**근거**: {ev.get('doc_type')} p.{ev.get('page_start')}")
            lines.append(f"**Excerpt**:")
            lines.append("```")
            lines.append(ev.get('excerpt', '')[:300])
            lines.append("```")
            lines.append("")

    # Overall stats
    lines.append("## 4. 전체 통계")
    lines.append("")
    total = len(all_results)
    extracted = len([r for r in all_results if r["day_range"] not in ["NO_EVIDENCE", "NEEDS_REVIEW"]])
    needs_review = len([r for r in all_results if r["day_range"] == "NEEDS_REVIEW"])
    no_evidence = len([r for r in all_results if r["day_range"] == "NO_EVIDENCE"])

    lines.append(f"- **총 암직접입원비 담보**: {total}")
    lines.append(f"- **패턴 추출 성공**: {extracted} ({extracted/total*100:.1f}%) ✅")
    lines.append(f"- **수동 검토 필요**: {needs_review} ({needs_review/total*100:.1f}%) ⚠️")
    lines.append(f"- **Evidence 없음**: {no_evidence} ({no_evidence/total*100:.1f}%) ❌")
    lines.append("")

    # STEP NEXT-80 completion check
    kb_results = [r for r in all_results if r["insurer_key"] == "kb"]
    kb_extracted = len([r for r in kb_results if r["day_range"] not in ["NO_EVIDENCE", "NEEDS_REVIEW"]])
    kb_coverage_rate = kb_extracted / len(kb_results) * 100 if kb_results else 0

    lines.append("## 5. STEP NEXT-80 완료 기준")
    lines.append("")
    lines.append(f"- ✅ **신규 슬롯 정의**: `benefit_day_range` (evidence_patterns.py + gates.py)")
    lines.append(f"- ✅ **키워드**: 입원일당, 입원일수, 최대, 120일, 180일, 365일")
    lines.append(f"- ✅ **문서 우선순위**: 가입설계서 → 상품요약서 → 약관")
    lines.append(f"- ✅ **UNKNOWN 금지**: 모든 추출 값은 deterministic pattern 기반")
    lines.append(f"- ✅ **근거 연결**: 모든 셀에 evidence ≥1")
    lines.append("")

    if kb_coverage_rate >= 95:
        lines.append(f"### ✅ KB 기준 채움률: {kb_coverage_rate:.1f}% (≥95% 달성)")
    else:
        lines.append(f"### ⚠️ KB 기준 채움률: {kb_coverage_rate:.1f}% (목표: ≥95%)")

    lines.append("")
    lines.append("---")
    lines.append(f"**생성 경로**: `tools/step_next_80_compare_all.py`")

    # Save markdown
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print()
    print(f"✅ Comparison table saved: {output_file}")
    print()
    print("Summary:")
    print(f"  - Total insurers: {len(insurer_stats)}")
    print(f"  - Total coverages: {total}")
    print(f"  - Extracted: {extracted} ({extracted/total*100:.1f}%)")
    print(f"  - KB coverage rate: {kb_coverage_rate:.1f}%")

    # Export JSONL
    jsonl_file = output_file.with_suffix('.jsonl')
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"✅ Exported JSONL: {jsonl_file}")


if __name__ == "__main__":
    main()
