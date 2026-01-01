"""
Amount Comparator — 보험사 간 금액 구조 비교

CONSTITUTIONAL RULES:
- NO recommendations / NO superiority judgment
- Structural diff only
- Evidence-traceable
"""

from typing import Dict, List, Any
from collections import defaultdict
import json


class AmountComparator:
    """
    보험사 간 금액 구조 비교기

    GATE-7-1: Coverage Alignment (동일 coverage_code 기준)
    GATE-7-2: Evidence Traceability (모든 amount는 evidence_refs ≥ 1)
    """

    def compare_by_coverage(
        self,
        parsed_amounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Coverage code별로 보험사 간 비교

        Args:
            parsed_amounts: [
                {
                    "coverage_code": "A4103",
                    "insurer": "samsung",
                    "amount_structure": {...},
                    "evidence_refs": [...]
                },
                ...
            ]

        Returns:
            [
                {
                    "coverage_code": "A4103",
                    "coverage_name_canonical": "뇌졸중진단비",
                    "insurers": {
                        "samsung": {...},
                        "meritz": {...},
                        ...
                    },
                    "comparison_metrics": {...}
                },
                ...
            ]
        """
        # Group by coverage_code
        by_coverage = defaultdict(list)
        for item in parsed_amounts:
            code = item.get("coverage_code")
            if code:  # Ignore unmapped (coverage_code == null)
                by_coverage[code].append(item)

        comparisons = []

        for coverage_code, items in by_coverage.items():
            # GATE-7-1: Coverage Alignment
            if len(items) == 0:
                continue

            # 보험사별로 정리
            insurers_data = {}
            canonical_name = None

            for item in items:
                insurer = item.get("insurer")
                canonical_name = item.get("coverage_name_canonical") or canonical_name

                insurers_data[insurer] = {
                    "amount_structure": item.get("amount_structure"),
                    "evidence_refs": item.get("evidence_refs"),
                    "mapping_status": item.get("mapping_status"),
                }

                # GATE-7-2: Evidence Traceability
                evidence_refs = item.get("evidence_refs", [])
                if len(evidence_refs) == 0:
                    print(f"⚠️  GATE-7-2 WARNING: {insurer}/{coverage_code} has no evidence_refs")

            # 비교 메트릭 (구조적 차이만)
            comparison_metrics = self._compute_metrics(insurers_data)

            comparisons.append({
                "coverage_code": coverage_code,
                "coverage_name_canonical": canonical_name,
                "insurers": insurers_data,
                "comparison_metrics": comparison_metrics,
            })

        return sorted(comparisons, key=lambda x: x["coverage_code"])

    def _compute_metrics(self, insurers_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        보험사 간 구조적 차이 메트릭

        NO JUDGMENT — 숫자 차이만 기록
        """
        amounts = []
        percentages = []
        payment_types = set()
        conditions_all = set()

        for insurer, data in insurers_data.items():
            structure = data.get("amount_structure", {})

            if structure.get("amount"):
                amounts.append(structure["amount"])
            if structure.get("percentage"):
                percentages.append(structure["percentage"])
            if structure.get("payment_type"):
                payment_types.add(structure["payment_type"])

            for cond in structure.get("conditions", []):
                conditions_all.add(cond)

        metrics = {
            "insurer_count": len(insurers_data),
            "amount_range": {
                "min": min(amounts) if amounts else None,
                "max": max(amounts) if amounts else None,
                "variance": max(amounts) - min(amounts) if len(amounts) > 1 else 0,
            },
            "percentage_range": {
                "min": min(percentages) if percentages else None,
                "max": max(percentages) if percentages else None,
            },
            "payment_types": sorted(payment_types),
            "conditions_union": sorted(conditions_all),
        }

        return metrics


def compare_all_axes(
    coverage_cards_files: List[str]
) -> List[Dict[str, Any]]:
    """
    전체 보험사 coverage_cards를 읽어서 비교

    Args:
        coverage_cards_files: [
            "data/compare/samsung_coverage_cards.jsonl",
            "data/compare/meritz_coverage_cards.jsonl",
            ...
        ]

    Returns:
        Comparison results (by coverage_code)
    """
    from .parse_amount import parse_coverage_amount

    all_parsed = []

    for file_path in coverage_cards_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    card = json.loads(line.strip())
                    parsed = parse_coverage_amount(card)
                    all_parsed.append(parsed)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            continue

    print(f"📊 Parsed {len(all_parsed)} coverage cards from {len(coverage_cards_files)} files")

    comparator = AmountComparator()
    comparisons = comparator.compare_by_coverage(all_parsed)

    print(f"✅ Generated {len(comparisons)} coverage comparisons")

    return comparisons
