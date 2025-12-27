"""
Step 10: Multi-Insurer Single Coverage Comparison (A4200_1)

전체 보험사의 A4200_1(암진단비) 비교 (fact-only)

입력:
- data/single/*_A4200_1_profile.json

출력:
- data/single/a4200_1_all_compare.json
- reports/a4200_1_all_insurers.md
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_all_a4200_1_profiles(base_dir: Path) -> Dict[str, Dict]:
    """
    모든 A4200_1 profile 로드

    Args:
        base_dir: 프로젝트 루트

    Returns:
        Dict[insurer, profile]
    """
    profiles = {}
    single_dir = base_dir / 'data' / 'single'

    if not single_dir.exists():
        return profiles

    for profile_file in single_dir.glob('*_A4200_1_profile.json'):
        insurer = profile_file.stem.replace('_A4200_1_profile', '')
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            # Validate coverage_code
            if profile.get('coverage_code') == 'A4200_1':
                profiles[insurer] = profile

    return profiles


def generate_comparison_json(profiles: Dict[str, Dict]) -> Dict:
    """
    비교 JSON 생성

    Args:
        profiles: insurer별 profile

    Returns:
        Dict: 비교 결과
    """
    insurers = sorted(profiles.keys())

    comparison = {
        'coverage_code': 'A4200_1',
        'canonical_name': '암진단비(유사암제외)',
        'insurers': insurers,
        'count': len(insurers),
        'doc_type_coverage': {},
        'slot_status': {}
    }

    # Doc type coverage
    for insurer in insurers:
        comparison['doc_type_coverage'][insurer] = profiles[insurer].get('doc_type_coverage', {})

    # Slot status
    slot_keys = ['payout_amount', 'waiting_period', 'reduction_period', 'excluded_cancer', 'definition_excerpt', 'payment_condition_excerpt']

    for slot_key in slot_keys:
        comparison['slot_status'][slot_key] = {}
        for insurer in insurers:
            profile = profiles[insurer]
            slot_data = profile.get(slot_key, {})
            comparison['slot_status'][slot_key][insurer] = {
                'status': slot_data.get('status', 'unknown'),
                'refs': slot_data.get('refs', []),
                'has_text': slot_data.get('text') is not None
            }

    return comparison


def generate_markdown_report(comparison: Dict, profiles: Dict[str, Dict]) -> str:
    """
    마크다운 리포트 생성 (fact-only)

    Args:
        comparison: 비교 결과
        profiles: insurer별 profile

    Returns:
        str: 마크다운 텍스트
    """
    lines = []

    # Title
    lines.append(f"# Multi-Insurer A4200_1 (암진단비) Comparison")
    lines.append("")
    lines.append(f"**Coverage Code**: A4200_1")
    lines.append(f"**Canonical Name**: 암진단비(유사암제외)")
    lines.append(f"**Insurers**: {', '.join([i.upper() for i in comparison['insurers']])}")
    lines.append(f"**Count**: {comparison['count']}")
    lines.append("")

    # Document Type Coverage
    lines.append("## Document Type Coverage")
    lines.append("")
    lines.append(f"| Insurer | 약관 | 사업방법서 | 상품요약서 |")
    lines.append("|---|---|---|---|")

    for insurer in comparison['insurers']:
        doc_cov = comparison['doc_type_coverage'][insurer]
        policy = doc_cov.get('약관', 0)
        method = doc_cov.get('사업방법서', 0)
        summary = doc_cov.get('상품요약서', 0)
        lines.append(f"| {insurer.upper()} | {policy} | {method} | {summary} |")

    lines.append("")

    # Slot Status Summary
    lines.append("## Slot Status Summary")
    lines.append("")

    slot_names = {
        'payout_amount': 'Payout Amount',
        'waiting_period': 'Waiting Period',
        'reduction_period': 'Reduction Period',
        'excluded_cancer': 'Excluded Cancer',
        'definition_excerpt': 'Definition Excerpt',
        'payment_condition_excerpt': 'Payment Condition'
    }

    for slot_key, slot_name in slot_names.items():
        lines.append(f"### {slot_name}")
        lines.append("")
        lines.append(f"| Insurer | Status | Evidence Refs |")
        lines.append("|---|---|---|")

        slot_data = comparison['slot_status'][slot_key]
        for insurer in comparison['insurers']:
            data = slot_data[insurer]
            status = data['status']
            refs = ', '.join(data['refs']) if data['refs'] else '-'
            lines.append(f"| {insurer.upper()} | {status} | {refs} |")

        lines.append("")

    return '\n'.join(lines)


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Compare A4200_1 across all insurers')
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent.parent

    print(f"[Step 10] Multi-Insurer A4200_1 Comparison")

    # Load profiles
    profiles = load_all_a4200_1_profiles(base_dir)

    if not profiles:
        print("[Step 10] No A4200_1 profiles found")
        return

    print(f"[Step 10] Found {len(profiles)} insurers with A4200_1 profile")
    print(f"[Step 10] Insurers: {', '.join(sorted(profiles.keys()))}")

    # Generate comparison
    comparison = generate_comparison_json(profiles)

    # Save comparison JSON
    output_dir = base_dir / 'data' / 'single'
    output_dir.mkdir(parents=True, exist_ok=True)
    compare_file = output_dir / 'a4200_1_all_compare.json'

    with open(compare_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    # Generate and save report
    report_text = generate_markdown_report(comparison, profiles)
    report_dir = base_dir / 'reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / 'a4200_1_all_insurers.md'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n[Step 10] Comparison completed:")
    print(f"  - Total insurers: {comparison['count']}")

    # Doc type coverage stats
    method_zero_count = sum(1 for i in comparison['insurers'] if comparison['doc_type_coverage'][i].get('사업방법서', 0) == 0)
    print(f"  - Insurers with 사업방법서 = 0: {method_zero_count}")

    # Unknown slots stats
    waiting_unknown = sum(1 for i in comparison['insurers'] if comparison['slot_status']['waiting_period'][i]['status'] == 'unknown')
    payment_unknown = sum(1 for i in comparison['insurers'] if comparison['slot_status']['payment_condition_excerpt'][i]['status'] == 'unknown')
    print(f"  - Waiting period unknown: {waiting_unknown}")
    print(f"  - Payment condition unknown: {payment_unknown}")

    print(f"\n✓ Compare JSON: {compare_file}")
    print(f"✓ Report MD: {report_file}")


if __name__ == '__main__':
    main()
