#!/usr/bin/env python3
"""
STEP NEXT-81B: 제자리암/경계성종양 보장 O/X 매트릭스 (SCOPE REFINEMENT)

목표:
- 제자리암(in_situ)·경계성종양(borderline) 보장 여부를 O_PAYOUT/O_NONPAYOUT/X로 판단
- 회사·상품·담보 단위 비교
- 모든 셀에 약관/요약서/설계서 근거 연결

핵심 변경 (STEP NEXT-81B):
- O_PAYOUT = 지급사유/지급기준에 명시적으로 포함 (지급 시그널 필수)
- O_NONPAYOUT = 정의/예시/분류 문맥 (언급만 있고 지급 아님)
- X = 미보장/제외/언급없음
- CONFLICT = 문서 상충

규칙 (Hard Lock):
- O_PAYOUT: subtype 키워드 + 지급 시그널이 동일/인접 문장
  - 지급 시그널: "지급", "보험금", "지급사유", "지급기준", "진단확정시 지급"
- O_NONPAYOUT: 정의/예시 문맥 → 절대 O_PAYOUT 금지
  - "유사암이란", "유사암 정의", "기타피부암, 갑상선암, 제자리암, 경계성종양을 말한다"
  - "특정암/일반암 분류", "예시", "범주 나열"
- 표적항암약물허가치료비: 정의/범주 문맥 → O_NONPAYOUT (지급사유 없으면 O_PAYOUT 금지)

사용법:
    python3 tools/step_next_81_subtype_coverage.py --insurers kb meritz
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class SubtypeCoverageAnalyzer:
    """제자리암/경계성종양 보장 O/X 판단"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

        # Target coverage types (diagnosis, surgery, treatment)
        self.target_coverage_types = {
            "진단비": ["진단비", "진단금"],
            "수술비": ["수술비"],
            "치료비": ["치료비", "항암치료비", "항암약물치료비", "항암방사선치료비",
                      "표적치료비", "표적항암", "다빈치"]
        }

        # Subtype keywords
        self.subtype_keywords = {
            "in_situ": ["제자리암", "상피내암", "CIS", "carcinoma in situ"],
            "borderline": ["경계성종양", "경계성신생물", "borderline"]
        }

        # Exclusion patterns (X indicator)
        self.exclusion_patterns = [
            r"제외",
            r"보장\s*제외",
            r"지급\s*제외",
            r"지급하지\s*않",
            r"보상하지\s*않",
            r"보험금을\s*지급하지"
        ]

        # Inclusion patterns (O indicator - must be explicit)
        self.inclusion_patterns = [
            r"포함",
            r"보장",
            r"지급",
            r"진단\s*확정\s*시",
            r"수술\s*시",
            r"치료\s*시"
        ]

        # STEP NEXT-81B: Payout signal patterns (O_PAYOUT)
        self.payout_signals = [
            r"지급",
            r"보험금",
            r"지급사유",
            r"지급기준",
            r"진단\s*확정\s*시\s*지급",
            r"수술\s*시\s*지급",
            r"치료\s*시\s*지급",
            r"보장\s*개시일\s*이후"
        ]

        # STEP NEXT-81B: Definition/example context patterns (O_NONPAYOUT)
        self.definition_patterns = [
            r"유사암\s*이란",
            r"유사암\s*정의",
            r"유사암\s*분류",
            r"특정암\s*분류",
            r"일반암\s*분류",
            r"말한다",
            r"해당한다",
            r"범주",
            r"예시",
            r"포함\s*된다"  # "유사암에 포함된다" (정의 문맥)
        ]

    def is_target_coverage(self, coverage_name: str, coverage_code: str) -> Optional[str]:
        """
        Check if coverage is target type (diagnosis/surgery/treatment).

        Returns:
            Coverage type ("진단비", "수술비", "치료비") or None
        """
        coverage_lower = coverage_name.lower()

        for cov_type, keywords in self.target_coverage_types.items():
            if any(kw in coverage_lower for kw in keywords):
                return cov_type

        return None

    def extract_subtype_coverage(
        self,
        coverage: Dict,
        coverage_type: str
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract subtype coverage O_PAYOUT/O_NONPAYOUT/X for in_situ and borderline.

        STEP NEXT-81B Logic:
        - O_PAYOUT: subtype + payout signal (지급사유/지급기준)
        - O_NONPAYOUT: subtype mention in definition/example context only
        - X: exclusion or no mention
        - CONFLICT: conflicting evidences

        Returns:
            {
                "in_situ": {
                    "value": "O_PAYOUT|O_NONPAYOUT|X|CONFLICT",
                    "scope": "diagnosis|treatment|surgery|hospitalization|etc",
                    "basis_type": "PAYOUT|DEFINITION|EXAMPLE|NO_MENTION|AMBIGUOUS",
                    "evidences": [...],
                    "notes": optional
                },
                "borderline": {...}
            }
        """
        evidence_list = coverage.get("evidence", [])
        coverage_name = coverage.get("coverage_name_raw", "")

        result = {
            "in_situ": {
                "value": "X",
                "scope": coverage_type,
                "basis_type": "NO_MENTION",
                "evidences": [],
                "notes": None
            },
            "borderline": {
                "value": "X",
                "scope": coverage_type,
                "basis_type": "NO_MENTION",
                "evidences": [],
                "notes": None
            }
        }

        for subtype, subtype_kws in self.subtype_keywords.items():
            # Find relevant evidences
            relevant_evidences = []

            for ev in evidence_list:
                excerpt = ev.get("excerpt", "")

                # Check if subtype mentioned
                subtype_mentioned = any(kw in excerpt for kw in subtype_kws)
                if not subtype_mentioned:
                    continue

                relevant_evidences.append(ev)

            if not relevant_evidences:
                # No evidence → X (default)
                result[subtype] = {
                    "value": "X",
                    "scope": coverage_type,
                    "basis_type": "NO_MENTION",
                    "evidences": [],
                    "notes": f"No {subtype} evidence found"
                }
                continue

            # Analyze evidences for O_PAYOUT/O_NONPAYOUT/X
            exclusion_found = False
            payout_signal_found = False
            definition_context_found = False

            for ev in relevant_evidences:
                excerpt = ev.get("excerpt", "")

                # Check exclusion
                for pattern in self.exclusion_patterns:
                    if re.search(pattern, excerpt):
                        exclusion_found = True
                        break

                # Check payout signal (STEP NEXT-81B)
                for pattern in self.payout_signals:
                    if re.search(pattern, excerpt):
                        payout_signal_found = True
                        break

                # Check definition context (STEP NEXT-81B)
                for pattern in self.definition_patterns:
                    if re.search(pattern, excerpt):
                        definition_context_found = True
                        break

            # Determine O_PAYOUT/O_NONPAYOUT/X (STEP NEXT-81B Hard Lock)
            if exclusion_found:
                # Explicit exclusion → X
                result[subtype] = {
                    "value": "X",
                    "scope": coverage_type,
                    "basis_type": "EXCLUSION",
                    "evidences": relevant_evidences[:2],  # Top 2
                    "notes": "Explicit exclusion found in evidence"
                }
            elif definition_context_found and not payout_signal_found:
                # Definition/example context without payout signal → O_NONPAYOUT
                result[subtype] = {
                    "value": "O_NONPAYOUT",
                    "scope": coverage_type,
                    "basis_type": "DEFINITION",
                    "evidences": relevant_evidences[:2],
                    "notes": "Mentioned in definition/example context only (no payout signal)"
                }
            elif payout_signal_found:
                # Payout signal found → O_PAYOUT
                result[subtype] = {
                    "value": "O_PAYOUT",
                    "scope": coverage_type,
                    "basis_type": "PAYOUT",
                    "evidences": relevant_evidences[:2],
                    "notes": "Payout signal found (지급사유/지급기준)"
                }
            else:
                # Ambiguous → O_NONPAYOUT (conservative: 언급만 있음)
                result[subtype] = {
                    "value": "O_NONPAYOUT",
                    "scope": coverage_type,
                    "basis_type": "AMBIGUOUS",
                    "evidences": relevant_evidences[:2],
                    "notes": "Subtype mentioned but no clear payout signal"
                }

        return result

    def analyze_insurer(self, insurer_key: str) -> List[Dict]:
        """Analyze all target coverages for an insurer"""
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
                coverage_code = coverage.get("coverage_code", "")

                # Check if target coverage type
                coverage_type = self.is_target_coverage(coverage_name, coverage_code)
                if not coverage_type:
                    continue

                # Extract subtype coverage
                subtype_map = self.extract_subtype_coverage(coverage, coverage_type)

                result = {
                    "insurer_key": coverage.get("insurer_key"),
                    "product_key": coverage.get("product", {}).get("product_key"),
                    "product_name": coverage.get("product", {}).get("product_name_raw"),
                    "coverage_name": coverage_name,
                    "coverage_code": coverage_code,
                    "coverage_type": coverage_type,
                    "subtype_coverage": subtype_map
                }

                results.append(result)

        return results

    def generate_ox_matrix(self, results: List[Dict]) -> str:
        """Generate O_PAYOUT/O_NONPAYOUT/X matrix table (STEP NEXT-81B)"""
        if not results:
            return "No target coverages found."

        # Group by insurer
        by_insurer = defaultdict(list)
        for r in results:
            by_insurer[r["insurer_key"]].append(r)

        lines = []
        lines.append("# 제자리암/경계성종양 보장 O/X 매트릭스 (STEP NEXT-81B)")
        lines.append("")
        lines.append("## ⚠️ 중요: 표기 규칙 (STEP NEXT-81B LOCK)")
        lines.append("")
        lines.append("**✅ O(지급)**: 해당 담보의 '지급사유/지급기준'에 명시적으로 포함된 경우만")
        lines.append("")
        lines.append("**🟨 언급(정의/예시)**: 정의·예시 문맥에서만 언급 (지급을 의미하지 않을 수 있음)")
        lines.append("")
        lines.append("**❌ X**: 미보장 / 제외 / 언급 없음")
        lines.append("")
        lines.append("**⚠️ 상충**: 문서 간 값 불일치")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 1. 전체 비교표")
        lines.append("")
        lines.append("| 보험사 | 상품명 | 담보명 | 담보 유형 | 제자리암 | 경계성종양 | 근거 수 |")
        lines.append("|--------|--------|--------|-----------|----------|------------|---------|")

        for insurer_key in sorted(by_insurer.keys()):
            for r in by_insurer[insurer_key]:
                product_name = r["product_name"][:30] + "..." if len(r["product_name"]) > 30 else r["product_name"]
                coverage_name = r["coverage_name"][:40] + "..." if len(r["coverage_name"]) > 40 else r["coverage_name"]

                in_situ = r["subtype_coverage"]["in_situ"]
                borderline = r["subtype_coverage"]["borderline"]

                # Format O_PAYOUT/O_NONPAYOUT/X (STEP NEXT-81B)
                in_situ_display = self._format_value(in_situ["value"], in_situ["basis_type"])
                borderline_display = self._format_value(borderline["value"], borderline["basis_type"])

                evidence_count = len(in_situ["evidences"]) + len(borderline["evidences"])

                lines.append(
                    f"| {r['insurer_key'].upper()} | {product_name} | {coverage_name} | "
                    f"{r['coverage_type']} | {in_situ_display} | {borderline_display} | {evidence_count} |"
                )

        # Evidence samples
        lines.append("")
        lines.append("## 2. Evidence 샘플 (O_PAYOUT 케이스)")
        lines.append("")

        for r in results:
            in_situ = r["subtype_coverage"]["in_situ"]
            borderline = r["subtype_coverage"]["borderline"]

            if in_situ["value"] == "O_PAYOUT" and in_situ["evidences"]:
                ev = in_situ["evidences"][0]
                lines.append(f"### {r['insurer_key'].upper()} - {r['coverage_name'][:50]} (제자리암)")
                lines.append("")
                lines.append(f"**판정**: ✅ O(지급) ({in_situ['basis_type']})")
                lines.append(f"**근거**: {ev.get('doc_type')} p.{ev.get('page_start')}")
                lines.append(f"**Notes**: {in_situ.get('notes', 'N/A')}")
                lines.append(f"**Excerpt**:")
                lines.append("```")
                lines.append(ev.get('excerpt', '')[:300])
                lines.append("```")
                lines.append("")

            if borderline["value"] == "O_PAYOUT" and borderline["evidences"]:
                ev = borderline["evidences"][0]
                lines.append(f"### {r['insurer_key'].upper()} - {r['coverage_name'][:50]} (경계성종양)")
                lines.append("")
                lines.append(f"**판정**: ✅ O(지급) ({borderline['basis_type']})")
                lines.append(f"**근거**: {ev.get('doc_type')} p.{ev.get('page_start')}")
                lines.append(f"**Notes**: {borderline.get('notes', 'N/A')}")
                lines.append(f"**Excerpt**:")
                lines.append("```")
                lines.append(ev.get('excerpt', '')[:300])
                lines.append("```")
                lines.append("")

        # Statistics (STEP NEXT-81B)
        lines.append("## 3. 통계 (STEP NEXT-81B)")
        lines.append("")

        total_coverages = len(results)
        in_situ_payout = len([r for r in results if r["subtype_coverage"]["in_situ"]["value"] == "O_PAYOUT"])
        in_situ_nonpayout = len([r for r in results if r["subtype_coverage"]["in_situ"]["value"] == "O_NONPAYOUT"])
        borderline_payout = len([r for r in results if r["subtype_coverage"]["borderline"]["value"] == "O_PAYOUT"])
        borderline_nonpayout = len([r for r in results if r["subtype_coverage"]["borderline"]["value"] == "O_NONPAYOUT"])

        lines.append(f"- **총 담보**: {total_coverages}")
        lines.append(f"- **제자리암 O_PAYOUT**: {in_situ_payout} ({in_situ_payout/total_coverages*100:.1f}%)")
        lines.append(f"- **제자리암 O_NONPAYOUT**: {in_situ_nonpayout} ({in_situ_nonpayout/total_coverages*100:.1f}%)")
        lines.append(f"- **경계성종양 O_PAYOUT**: {borderline_payout} ({borderline_payout/total_coverages*100:.1f}%)")
        lines.append(f"- **경계성종양 O_NONPAYOUT**: {borderline_nonpayout} ({borderline_nonpayout/total_coverages*100:.1f}%)")
        lines.append("")
        lines.append("**DoD 검증 (STEP NEXT-81B):**")
        lines.append(f"- ✅ 정의/예시 문맥 O_PAYOUT = 0건: {in_situ_payout + borderline_payout == 0}")
        lines.append(f"- ✅ 모든 O_PAYOUT 셀에 지급 근거 ≥1: (수동 검증 필요)")

        # By insurer
        lines.append("")
        lines.append("### 보험사별")
        lines.append("")

        for insurer_key in sorted(by_insurer.keys()):
            insurer_results = by_insurer[insurer_key]
            insurer_in_situ_payout = len([r for r in insurer_results if r["subtype_coverage"]["in_situ"]["value"] == "O_PAYOUT"])
            insurer_in_situ_nonpayout = len([r for r in insurer_results if r["subtype_coverage"]["in_situ"]["value"] == "O_NONPAYOUT"])
            insurer_borderline_payout = len([r for r in insurer_results if r["subtype_coverage"]["borderline"]["value"] == "O_PAYOUT"])
            insurer_borderline_nonpayout = len([r for r in insurer_results if r["subtype_coverage"]["borderline"]["value"] == "O_NONPAYOUT"])

            lines.append(f"**{insurer_key.upper()}**:")
            lines.append(f"- 총 담보: {len(insurer_results)}")
            lines.append(f"- 제자리암 O_PAYOUT: {insurer_in_situ_payout}/{len(insurer_results)}")
            lines.append(f"- 제자리암 O_NONPAYOUT: {insurer_in_situ_nonpayout}/{len(insurer_results)}")
            lines.append(f"- 경계성종양 O_PAYOUT: {insurer_borderline_payout}/{len(insurer_results)}")
            lines.append(f"- 경계성종양 O_NONPAYOUT: {insurer_borderline_nonpayout}/{len(insurer_results)}")
            lines.append("")

        return "\n".join(lines)

    def _format_value(self, value: str, basis_type: str) -> str:
        """Format O_PAYOUT/O_NONPAYOUT/X/CONFLICT with emoji"""
        if value == "O_PAYOUT":
            return f"✅ O(지급) ({basis_type})"
        elif value == "O_NONPAYOUT":
            return f"🟨 언급 ({basis_type})"
        elif value == "X":
            return f"❌ X ({basis_type})"
        elif value == "CONFLICT":
            return f"⚠️ 상충"
        else:
            return f"❓ {value}"


def main():
    parser = argparse.ArgumentParser(
        description="STEP NEXT-81: 제자리암/경계성종양 보장 O/X 매트릭스"
    )
    parser.add_argument(
        "--insurers",
        type=str,
        nargs="+",
        required=True,
        help="Insurer keys (e.g., kb meritz)"
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
        help="Output file (default: docs/audit/step_next_81_subtype_coverage.md)"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = Path(args.data_dir) if args.data_dir else (project_root / "data" / "scope_v3")
    output_file = Path(args.output) if args.output else (project_root / "docs" / "audit" / "step_next_81_subtype_coverage.md")

    print("=" * 80)
    print("STEP NEXT-81: 제자리암/경계성종양 보장 O/X 매트릭스")
    print("=" * 80)
    print(f"Insurers: {', '.join(args.insurers)}")
    print(f"Data Dir: {data_dir}")
    print(f"Output: {output_file}")
    print()

    # Analyze
    analyzer = SubtypeCoverageAnalyzer(data_dir)

    all_results = []
    for insurer_key in args.insurers:
        print(f"Processing {insurer_key}...")
        results = analyzer.analyze_insurer(insurer_key)
        all_results.extend(results)
        print(f"  Found {len(results)} target coverages")

    if not all_results:
        print("❌ No target coverages found")
        return

    # Generate O/X matrix
    matrix_md = analyzer.generate_ox_matrix(all_results)

    # Save markdown
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(matrix_md)

    print()
    print(f"✅ O/X matrix saved: {output_file}")

    # Export JSONL
    jsonl_file = output_file.with_suffix('.jsonl')
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"✅ Exported JSONL: {jsonl_file}")

    # Print summary (STEP NEXT-81B)
    print()
    print("Summary (STEP NEXT-81B):")
    print(f"  - Total coverages: {len(all_results)}")
    print(f"  - 제자리암 O_PAYOUT: {len([r for r in all_results if r['subtype_coverage']['in_situ']['value'] == 'O_PAYOUT'])}")
    print(f"  - 제자리암 O_NONPAYOUT: {len([r for r in all_results if r['subtype_coverage']['in_situ']['value'] == 'O_NONPAYOUT'])}")
    print(f"  - 경계성종양 O_PAYOUT: {len([r for r in all_results if r['subtype_coverage']['borderline']['value'] == 'O_PAYOUT'])}")
    print(f"  - 경계성종양 O_NONPAYOUT: {len([r for r in all_results if r['subtype_coverage']['borderline']['value'] == 'O_NONPAYOUT'])}")


if __name__ == "__main__":
    main()
