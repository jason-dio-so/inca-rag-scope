#!/usr/bin/env python3
"""
STEP NEXT-80: 암직접입원비 보장일수 범위 비교표 생성

목표:
- 암직접입원비 담보의 보장일수 범위(예: 1-120일)를 회사/상품/담보 단위로 표로 비교
- 모든 셀에 약관/요약서/설계서 근거를 연결

필수:
- 신규 슬롯: benefit_day_range
- 키워드: 입원일당, 입원일수, 최대, 120일, 180일
- 문서 우선순위: 가입설계서 → 상품요약서 → 약관
- UNKNOWN 금지
- evidence ≥1

사용법:
    python3 tools/step_next_80_benefit_day_range.py --insurer kb
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class BenefitDayRangeAnalyzer:
    """암직접입원비 보장일수 범위 추출 및 비교"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.target_coverage_keywords = [
            "암직접입원비", "암 직접입원비", "암입원일당", "암 입원일당",
            "암직접치료입원일당", "암 직접치료입원일당", "암치료입원일당"
        ]

    def is_target_coverage(self, coverage_name: str) -> bool:
        """Check if coverage is 암직접입원비 related"""
        coverage_lower = coverage_name.lower()
        return any(kw in coverage_lower for kw in self.target_coverage_keywords)

    def extract_day_range_from_text(self, text: str) -> Optional[str]:
        """
        Extract day range from text.

        Patterns:
        - "1일부터 120일까지"
        - "1~120일"
        - "최대 120일"
        - "120일 한도"
        """
        # Pattern 1: X일부터 Y일까지
        pattern1 = r'(\d+)\s*일\s*부터\s*(\d+)\s*일'
        match = re.search(pattern1, text)
        if match:
            return f"{match.group(1)}-{match.group(2)}일"

        # Pattern 2: X~Y일
        pattern2 = r'(\d+)\s*~\s*(\d+)\s*일'
        match = re.search(pattern2, text)
        if match:
            return f"{match.group(1)}-{match.group(2)}일"

        # Pattern 3: 최대 X일
        pattern3 = r'최대\s*(\d+)\s*일'
        match = re.search(pattern3, text)
        if match:
            return f"1-{match.group(1)}일"

        # Pattern 4: X일 한도
        pattern4 = r'(\d+)\s*일\s*한도'
        match = re.search(pattern4, text)
        if match:
            return f"1-{match.group(1)}일"

        return None

    def extract_from_coverage(self, coverage: Dict) -> Optional[Dict]:
        """
        Extract benefit_day_range from coverage evidence.

        Returns:
            {
                "day_range": "1-120일",
                "evidence": [...]
            }
        """
        evidence_list = coverage.get("evidence", [])

        # Keywords for day range
        day_keywords = ["입원일당", "입원일수", "일당", "보장일수", "지급일수", "최대", "120일", "180일"]

        relevant_evidences = []
        for ev in evidence_list:
            excerpt = ev.get("excerpt", "")
            if any(kw in excerpt for kw in day_keywords):
                relevant_evidences.append(ev)

        # Try to extract day range from evidences
        for ev in relevant_evidences:
            excerpt = ev.get("excerpt", "")
            day_range = self.extract_day_range_from_text(excerpt)
            if day_range:
                return {
                    "day_range": day_range,
                    "evidence": [ev],
                    "extraction_method": "deterministic_pattern"
                }

        # If no pattern match but have relevant evidence, mark as FOUND but needs manual review
        if relevant_evidences:
            return {
                "day_range": "NEEDS_REVIEW",
                "evidence": relevant_evidences[:3],  # Top 3
                "extraction_method": "keyword_match_only"
            }

        return None

    def analyze_insurer(self, insurer_key: str) -> List[Dict]:
        """Analyze all 암직접입원비 coverages for an insurer"""
        input_file = self.data_dir / f"{insurer_key}_step3_evidence_enriched_v1_gated.jsonl"

        if not input_file.exists():
            print(f"⚠️  File not found: {input_file}")
            return []

        results = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                coverage = json.loads(line)
                coverage_name = coverage.get("coverage_name_raw", "")

                # Check if target coverage
                if not self.is_target_coverage(coverage_name):
                    continue

                # Extract day range
                extraction = self.extract_from_coverage(coverage)

                result = {
                    "insurer_key": coverage.get("insurer_key"),
                    "product_key": coverage.get("product", {}).get("product_key"),
                    "product_name": coverage.get("product", {}).get("product_name_raw"),
                    "coverage_name": coverage_name,
                    "coverage_code": coverage.get("coverage_code"),
                    "day_range": extraction.get("day_range") if extraction else "NO_EVIDENCE",
                    "evidence_count": len(extraction.get("evidence", [])) if extraction else 0,
                    "extraction_method": extraction.get("extraction_method") if extraction else "none",
                    "evidence_sample": extraction.get("evidence", [])[:1] if extraction else []
                }

                results.append(result)

        return results

    def generate_comparison_table(self, results: List[Dict]) -> str:
        """Generate markdown comparison table"""
        if not results:
            return "No 암직접입원비 coverages found."

        # Group by insurer
        by_insurer = defaultdict(list)
        for r in results:
            by_insurer[r["insurer_key"]].append(r)

        # Build table
        lines = []
        lines.append("# 암직접입원비 보장일수 범위 비교 (STEP NEXT-80)")
        lines.append("")
        lines.append("| 보험사 | 상품명 | 담보명 | 보장일수 범위 | 근거 문서 | Evidence 수 | 추출 방법 |")
        lines.append("|--------|--------|--------|--------------|-----------|------------|----------|")

        for insurer_key in sorted(by_insurer.keys()):
            for r in by_insurer[insurer_key]:
                product_name = r["product_name"][:30] + "..." if len(r["product_name"]) > 30 else r["product_name"]
                coverage_name = r["coverage_name"][:30] + "..." if len(r["coverage_name"]) > 30 else r["coverage_name"]

                evidence_doc = "N/A"
                if r["evidence_sample"]:
                    ev = r["evidence_sample"][0]
                    evidence_doc = f"{ev.get('doc_type', 'N/A')} p.{ev.get('page_start', 'N/A')}"

                lines.append(
                    f"| {r['insurer_key'].upper()} | {product_name} | {coverage_name} | "
                    f"{r['day_range']} | {evidence_doc} | {r['evidence_count']} | {r['extraction_method']} |"
                )

        lines.append("")
        lines.append("## 범례")
        lines.append("- **보장일수 범위**: 1-120일 형식 (deterministic pattern extraction)")
        lines.append("- **NEEDS_REVIEW**: 키워드 매칭되었으나 패턴 추출 실패 (수동 검토 필요)")
        lines.append("- **NO_EVIDENCE**: 해당 문서에 관련 evidence 없음")
        lines.append("")
        lines.append("## Coverage 통계")

        total = len(results)
        extracted = len([r for r in results if r["day_range"] not in ["NO_EVIDENCE", "NEEDS_REVIEW"]])
        needs_review = len([r for r in results if r["day_range"] == "NEEDS_REVIEW"])
        no_evidence = len([r for r in results if r["day_range"] == "NO_EVIDENCE"])

        lines.append(f"- **총 암직접입원비 담보**: {total}")
        lines.append(f"- **패턴 추출 성공**: {extracted} ({extracted/total*100:.1f}%)")
        lines.append(f"- **수동 검토 필요**: {needs_review} ({needs_review/total*100:.1f}%)")
        lines.append(f"- **Evidence 없음**: {no_evidence} ({no_evidence/total*100:.1f}%)")

        return "\n".join(lines)

    def export_jsonl(self, results: List[Dict], output_file: Path):
        """Export results as JSONL"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"✅ Exported JSONL: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-80: 암직접입원비 보장일수 범위 비교"
    )
    parser.add_argument(
        "--insurer",
        type=str,
        required=True,
        help="Insurer key (e.g., kb, samsung)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Data directory (default: data/scope_v3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: docs/audit/step_next_80_benefit_day_range.md)"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = Path(args.data_dir) if args.data_dir else (project_root / "data" / "scope_v3")
    output_file = Path(args.output) if args.output else (project_root / "docs" / "audit" / "step_next_80_benefit_day_range.md")

    print("=" * 80)
    print("STEP NEXT-80: 암직접입원비 보장일수 범위 추출 및 비교")
    print("=" * 80)
    print(f"Insurer: {args.insurer}")
    print(f"Data Dir: {data_dir}")
    print(f"Output: {output_file}")
    print()

    # Analyze
    analyzer = BenefitDayRangeAnalyzer(data_dir)
    results = analyzer.analyze_insurer(args.insurer)

    if not results:
        print("❌ No 암직접입원비 coverages found for insurer:", args.insurer)
        return

    # Generate comparison table
    table_md = analyzer.generate_comparison_table(results)

    # Save markdown
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(table_md)

    print(f"✅ Comparison table saved: {output_file}")
    print()

    # Export JSONL
    jsonl_file = output_file.with_suffix('.jsonl')
    analyzer.export_jsonl(results, jsonl_file)

    # Print summary
    print()
    print("Summary:")
    print(f"  - Total coverages: {len(results)}")
    print(f"  - With day range: {len([r for r in results if r['day_range'] not in ['NO_EVIDENCE', 'NEEDS_REVIEW']])}")
    print(f"  - Needs review: {len([r for r in results if r['day_range'] == 'NEEDS_REVIEW'])}")
    print(f"  - No evidence: {len([r for r in results if r['day_range'] == 'NO_EVIDENCE'])}")

    # Print table preview
    print()
    print("Table Preview:")
    print("-" * 80)
    print(table_md)


if __name__ == "__main__":
    main()
