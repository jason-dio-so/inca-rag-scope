"""
STEP NEXT-V-01: A/B Test Metrics Calculation

Compare baseline (A) vs vector (B) customer_view outputs.

Metrics:
1. Coverage Rate (채움율): benefit_description, payment_type, limit_conditions, exclusion_notes
2. Evidence Quality: TOC/헛근거 vs 설명문 ratio
3. Performance: (TBD - latency measurements)

Constitutional Rules:
- NO LLM usage
- Deterministic pattern matching only
- Evidence snippet classification only
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict


class EvidenceQualityClassifier:
    """
    Classify evidence snippets as TOC/헛근거 or 설명문.

    Deterministic pattern matching.
    """

    # TOC/structural patterns (헛근거)
    TOC_PATTERNS = [
        r'특별약관',
        r'보통약관',
        r'제\d+조',
        r'\d+-\d+-\d+',  # 4-1-3
        r'^\d+\.\d+',    # 1.2
        r'목차',
        r'페이지\s*\d+',
        r'담보명',
        r'특약명',
    ]

    # Explanatory sentence patterns (설명문)
    EXPLANATORY_PATTERNS = [
        r'보험금을\s*지급',
        r'보장합니다',
        r'다음의\s*경우',
        r'해당하는\s*경우',
        r'지급사유',
        r'진단확정.*때',
        r'수술.*받은',
        r'입원.*때',
    ]

    @classmethod
    def classify(cls, snippet: str) -> Tuple[str, str]:
        """
        Classify snippet as 'toc' or 'explanatory'.

        Args:
            snippet: Evidence snippet text

        Returns:
            (category, matched_pattern)
        """
        # Check TOC patterns first (priority)
        for pattern in cls.TOC_PATTERNS:
            if re.search(pattern, snippet):
                return 'toc', pattern

        # Check explanatory patterns
        for pattern in cls.EXPLANATORY_PATTERNS:
            if re.search(pattern, snippet):
                return 'explanatory', pattern

        # Default: unknown (treat as TOC for conservative scoring)
        return 'toc', 'unknown'


def calculate_coverage_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate coverage rate metrics.

    Args:
        results: List of customer_view results

    Returns:
        Metrics dict
    """
    total = len(results)
    if total == 0:
        return {}

    benefit_desc_count = 0
    payment_type_count = 0
    limit_cond_count = 0
    exclusion_count = 0

    for result in results:
        cv = result.get('customer_view', {})

        if cv.get('benefit_description') and cv['benefit_description'] != '명시 없음':
            benefit_desc_count += 1
        if cv.get('payment_type'):
            payment_type_count += 1
        if cv.get('limit_conditions'):
            limit_cond_count += 1
        if cv.get('exclusion_notes'):
            exclusion_count += 1

    return {
        'total': total,
        'benefit_description_nonempty': benefit_desc_count,
        'benefit_description_rate': benefit_desc_count / total,
        'payment_type_detected': payment_type_count,
        'payment_type_rate': payment_type_count / total,
        'limit_conditions_nonempty': limit_cond_count,
        'limit_conditions_rate': limit_cond_count / total,
        'exclusion_notes_nonempty': exclusion_count,
        'exclusion_notes_rate': exclusion_count / total,
    }


def calculate_evidence_quality_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate evidence quality metrics (TOC vs explanatory).

    Args:
        results: List of customer_view results

    Returns:
        Quality metrics dict
    """
    total_snippets = 0
    toc_count = 0
    explanatory_count = 0

    for result in results:
        cv = result.get('customer_view', {})

        # Get benefit_description (the primary field for quality check)
        desc = cv.get('benefit_description', '')
        if desc and desc != '명시 없음':
            # Classify
            category, _ = EvidenceQualityClassifier.classify(desc)
            total_snippets += 1
            if category == 'toc':
                toc_count += 1
            elif category == 'explanatory':
                explanatory_count += 1

    if total_snippets == 0:
        return {
            'total_snippets': 0,
            'toc_like_count': 0,
            'toc_like_ratio': 0.0,
            'explanatory_count': 0,
            'explanatory_ratio': 0.0
        }

    return {
        'total_snippets': total_snippets,
        'toc_like_count': toc_count,
        'toc_like_ratio': toc_count / total_snippets,
        'explanatory_count': explanatory_count,
        'explanatory_ratio': explanatory_count / total_snippets
    }


def compare_ab(a_results: List[Dict], b_results: List[Dict]) -> Dict[str, Any]:
    """
    Compare A (baseline) vs B (vector) results.

    Args:
        a_results: Baseline results
        b_results: Vector results

    Returns:
        Comparison metrics
    """
    # Coverage metrics
    a_coverage = calculate_coverage_metrics(a_results)
    b_coverage = calculate_coverage_metrics(b_results)

    # Evidence quality metrics
    a_quality = calculate_evidence_quality_metrics(a_results)
    b_quality = calculate_evidence_quality_metrics(b_results)

    # Delta calculations (B - A)
    coverage_delta = {
        'benefit_description_rate_delta': b_coverage['benefit_description_rate'] - a_coverage['benefit_description_rate'],
        'payment_type_rate_delta': b_coverage['payment_type_rate'] - a_coverage['payment_type_rate'],
        'limit_conditions_rate_delta': b_coverage['limit_conditions_rate'] - a_coverage['limit_conditions_rate'],
        'exclusion_notes_rate_delta': b_coverage['exclusion_notes_rate'] - a_coverage['exclusion_notes_rate'],
    }

    quality_delta = {
        'toc_like_ratio_delta': b_quality['toc_like_ratio'] - a_quality['toc_like_ratio'],
        'explanatory_ratio_delta': b_quality['explanatory_ratio'] - a_quality['explanatory_ratio'],
    }

    return {
        'a_coverage': a_coverage,
        'b_coverage': b_coverage,
        'coverage_delta': coverage_delta,
        'a_quality': a_quality,
        'b_quality': b_quality,
        'quality_delta': quality_delta
    }


def load_results(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load results from JSONL file"""
    results = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def main(axis: str):
    """
    Run A/B metrics comparison for an axis.

    Args:
        axis: Insurance axis (e.g., "samsung", "meritz")
    """
    a_path = Path(f"output/ab_test/A_{axis}_customer_view.jsonl")
    b_path = Path(f"output/ab_test/B_{axis}_customer_view.jsonl")

    if not a_path.exists():
        raise FileNotFoundError(f"Baseline results not found: {a_path}")
    if not b_path.exists():
        raise FileNotFoundError(f"Vector results not found: {b_path}")

    # Load results
    a_results = load_results(a_path)
    b_results = load_results(b_path)

    print(f"Loaded A: {len(a_results)}, B: {len(b_results)}")

    # Compare
    comparison = compare_ab(a_results, b_results)

    # Write summary
    summary_path = Path(f"output/ab_test/metrics_{axis}_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    print(f"Wrote metrics summary to {summary_path}")

    # Print summary
    print("\n=== Coverage Metrics ===")
    print(f"A (Baseline):")
    print(f"  benefit_description_rate: {comparison['a_coverage']['benefit_description_rate']:.1%}")
    print(f"  payment_type_rate: {comparison['a_coverage']['payment_type_rate']:.1%}")
    print(f"  limit_conditions_rate: {comparison['a_coverage']['limit_conditions_rate']:.1%}")
    print(f"  exclusion_notes_rate: {comparison['a_coverage']['exclusion_notes_rate']:.1%}")

    print(f"\nB (Vector):")
    print(f"  benefit_description_rate: {comparison['b_coverage']['benefit_description_rate']:.1%}")
    print(f"  payment_type_rate: {comparison['b_coverage']['payment_type_rate']:.1%}")
    print(f"  limit_conditions_rate: {comparison['b_coverage']['limit_conditions_rate']:.1%}")
    print(f"  exclusion_notes_rate: {comparison['b_coverage']['exclusion_notes_rate']:.1%}")

    print(f"\nDelta (B - A):")
    for key, value in comparison['coverage_delta'].items():
        print(f"  {key}: {value:+.1%}")

    print("\n=== Evidence Quality Metrics ===")
    print(f"A (Baseline):")
    print(f"  toc_like_ratio: {comparison['a_quality']['toc_like_ratio']:.1%}")
    print(f"  explanatory_ratio: {comparison['a_quality']['explanatory_ratio']:.1%}")

    print(f"\nB (Vector):")
    print(f"  toc_like_ratio: {comparison['b_quality']['toc_like_ratio']:.1%}")
    print(f"  explanatory_ratio: {comparison['b_quality']['explanatory_ratio']:.1%}")

    print(f"\nDelta (B - A):")
    print(f"  toc_like_ratio_delta: {comparison['quality_delta']['toc_like_ratio_delta']:+.1%}")
    print(f"  explanatory_ratio_delta: {comparison['quality_delta']['explanatory_ratio_delta']:+.1%}")

    # Decision criteria check
    print("\n=== Decision Criteria ===")
    benefit_delta = comparison['coverage_delta']['benefit_description_rate_delta']
    toc_delta = comparison['quality_delta']['toc_like_ratio_delta']
    expl_delta = comparison['quality_delta']['explanatory_ratio_delta']

    print(f"1. Coverage improvement (≥ +20%p): {benefit_delta:.1%} {'✓ PASS' if benefit_delta >= 0.20 else '✗ FAIL'}")
    print(f"2. TOC ratio reduction: {toc_delta:+.1%} {'✓ PASS' if toc_delta < 0 else '✗ FAIL'}")
    print(f"3. Explanatory ratio increase: {expl_delta:+.1%} {'✓ PASS' if expl_delta > 0 else '✗ FAIL'}")

    return comparison


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tools.ab_test_metrics <axis>")
        print("Example: python -m tools.ab_test_metrics samsung")
        sys.exit(1)

    axis = sys.argv[1]
    main(axis)
