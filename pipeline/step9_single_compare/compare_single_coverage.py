"""
Step 9: Single Coverage Comparison

두 보험사의 동일 coverage_code 비교 (fact-only, no interpretation)

입력:
- data/single/{INSURER_A}_{COVERAGE_CODE}_profile.json
- data/single/{INSURER_B}_{COVERAGE_CODE}_profile.json

출력:
- data/single/{INSURER_A}_vs_{INSURER_B}_{COVERAGE_CODE}_compare.json
- reports/single_{COVERAGE_CODE}_{INSURER_A}_vs_{INSURER_B}.md
"""

import argparse
import json
from pathlib import Path
from typing import Dict


def compare_single_coverage(
    insurer_a: str,
    insurer_b: str,
    coverage_code: str,
    base_dir: Path
) -> Dict:
    """
    단일 담보 비교

    Args:
        insurer_a: 보험사 A
        insurer_b: 보험사 B
        coverage_code: Coverage code
        base_dir: 프로젝트 루트

    Returns:
        Dict: 비교 결과
    """
    # Profile 로드
    profile_a_file = base_dir / 'data' / 'single' / f'{insurer_a}_{coverage_code}_profile.json'
    profile_b_file = base_dir / 'data' / 'single' / f'{insurer_b}_{coverage_code}_profile.json'

    with open(profile_a_file, 'r', encoding='utf-8') as f:
        profile_a = json.load(f)

    with open(profile_b_file, 'r', encoding='utf-8') as f:
        profile_b = json.load(f)

    # 비교 결과 생성
    comparison = {
        'coverage_code': coverage_code,
        'canonical_name': profile_a.get('canonical_name'),
        'insurers': [insurer_a, insurer_b],
        'doc_type_hits': {
            insurer_a: profile_a.get('doc_type_coverage', {}),
            insurer_b: profile_b.get('doc_type_coverage', {})
        },
        'slots': {
            'payout_amount': {
                insurer_a: {
                    'text': profile_a['payout_amount']['text'],
                    'refs': profile_a['payout_amount']['refs'],
                    'status': profile_a['payout_amount']['status']
                },
                insurer_b: {
                    'text': profile_b['payout_amount']['text'],
                    'refs': profile_b['payout_amount']['refs'],
                    'status': profile_b['payout_amount']['status']
                }
            },
            'waiting_period': {
                insurer_a: {
                    'text': profile_a['waiting_period']['text'],
                    'refs': profile_a['waiting_period']['refs'],
                    'status': profile_a['waiting_period']['status']
                },
                insurer_b: {
                    'text': profile_b['waiting_period']['text'],
                    'refs': profile_b['waiting_period']['refs'],
                    'status': profile_b['waiting_period']['status']
                }
            },
            'reduction_period': {
                insurer_a: {
                    'text': profile_a['reduction_period']['text'],
                    'refs': profile_a['reduction_period']['refs'],
                    'status': profile_a['reduction_period']['status']
                },
                insurer_b: {
                    'text': profile_b['reduction_period']['text'],
                    'refs': profile_b['reduction_period']['refs'],
                    'status': profile_b['reduction_period']['status']
                }
            },
            'excluded_cancer': {
                insurer_a: {
                    'text': profile_a['excluded_cancer']['text'],
                    'refs': profile_a['excluded_cancer']['refs'],
                    'status': profile_a['excluded_cancer']['status']
                },
                insurer_b: {
                    'text': profile_b['excluded_cancer']['text'],
                    'refs': profile_b['excluded_cancer']['refs'],
                    'status': profile_b['excluded_cancer']['status']
                }
            },
            'definition_excerpt': {
                insurer_a: {
                    'text': profile_a['definition_excerpt']['text'],
                    'refs': profile_a['definition_excerpt']['refs'],
                    'status': profile_a['definition_excerpt']['status']
                },
                insurer_b: {
                    'text': profile_b['definition_excerpt']['text'],
                    'refs': profile_b['definition_excerpt']['refs'],
                    'status': profile_b['definition_excerpt']['status']
                }
            },
            'payment_condition_excerpt': {
                insurer_a: {
                    'text': profile_a['payment_condition_excerpt']['text'],
                    'refs': profile_a['payment_condition_excerpt']['refs'],
                    'status': profile_a['payment_condition_excerpt']['status']
                },
                insurer_b: {
                    'text': profile_b['payment_condition_excerpt']['text'],
                    'refs': profile_b['payment_condition_excerpt']['refs'],
                    'status': profile_b['payment_condition_excerpt']['status']
                }
            }
        }
    }

    return comparison


def generate_markdown_report(
    comparison: Dict,
    insurer_a: str,
    insurer_b: str,
    coverage_code: str
) -> str:
    """
    마크다운 리포트 생성 (fact-only, no interpretation)

    Args:
        comparison: 비교 결과
        insurer_a: 보험사 A
        insurer_b: 보험사 B
        coverage_code: Coverage code

    Returns:
        str: 마크다운 텍스트
    """
    lines = []

    # Title
    lines.append(f"# Single Coverage Deep Dive: {coverage_code}")
    lines.append("")
    lines.append(f"**Canonical Name**: {comparison['canonical_name']}")
    lines.append(f"**Insurers**: {insurer_a.upper()} vs {insurer_b.upper()}")
    lines.append("")

    # Document Type Hit Distribution
    lines.append("## Document Type Hit Distribution")
    lines.append("")
    lines.append("| Doc Type | Samsung | Meritz |")
    lines.append("|---|---|---|")

    hits_a = comparison['doc_type_hits'][insurer_a]
    hits_b = comparison['doc_type_hits'][insurer_b]

    for doc_type in ['약관', '사업방법서', '상품요약서']:
        a_hits = hits_a.get(doc_type, 0)
        b_hits = hits_b.get(doc_type, 0)
        lines.append(f"| {doc_type} | {a_hits} | {b_hits} |")

    lines.append("")

    # Slot Comparison
    lines.append("## Slot-by-Slot Comparison")
    lines.append("")

    slot_names = {
        'payout_amount': 'Payout Amount',
        'waiting_period': 'Waiting Period',
        'reduction_period': 'Reduction Period',
        'excluded_cancer': 'Excluded Cancer',
        'definition_excerpt': 'Definition Excerpt',
        'payment_condition_excerpt': 'Payment Condition Excerpt'
    }

    for slot_key, slot_name in slot_names.items():
        lines.append(f"### {slot_name}")
        lines.append("")
        lines.append(f"| Insurer | Text | Evidence Refs | Status |")
        lines.append("|---|---|---|---|")

        slot_data = comparison['slots'][slot_key]

        for insurer in [insurer_a, insurer_b]:
            data = slot_data[insurer]
            text = data['text'][:100] + "..." if data['text'] and len(data['text']) > 100 else (data['text'] or '-')
            refs = ', '.join(data['refs']) if data['refs'] else '-'
            status = data['status']

            lines.append(f"| {insurer.upper()} | {text} | {refs} | {status} |")

        lines.append("")

    return '\n'.join(lines)


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='Compare single coverage between two insurers')
    parser.add_argument('--insurer-a', type=str, required=True, help='보험사 A')
    parser.add_argument('--insurer-b', type=str, required=True, help='보험사 B')
    parser.add_argument('--coverage-code', type=str, required=True, help='Coverage code (e.g., A4200_1)')
    args = parser.parse_args()

    insurer_a = args.insurer_a
    insurer_b = args.insurer_b
    coverage_code = args.coverage_code
    base_dir = Path(__file__).parent.parent.parent

    print(f"[Step 9] Single Coverage Comparison")
    print(f"[Step 9] Coverage Code: {coverage_code}")
    print(f"[Step 9] {insurer_a.upper()} vs {insurer_b.upper()}")

    # Compare
    comparison = compare_single_coverage(insurer_a, insurer_b, coverage_code, base_dir)

    # Save comparison JSON
    output_dir = base_dir / 'data' / 'single'
    output_dir.mkdir(parents=True, exist_ok=True)
    compare_file = output_dir / f'{insurer_a}_vs_{insurer_b}_{coverage_code}_compare.json'

    with open(compare_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    # Generate and save report
    report_text = generate_markdown_report(comparison, insurer_a, insurer_b, coverage_code)
    report_dir = base_dir / 'reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f'single_{coverage_code}_{insurer_a}_vs_{insurer_b}.md'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n[Step 9] Comparison completed:")
    print(f"  - Coverage: {comparison['canonical_name']}")
    print(f"  - Doc type hits ({insurer_a}): {comparison['doc_type_hits'][insurer_a]}")
    print(f"  - Doc type hits ({insurer_b}): {comparison['doc_type_hits'][insurer_b]}")
    print(f"\n✓ Compare JSON: {compare_file}")
    print(f"✓ Report MD: {report_file}")


if __name__ == '__main__':
    main()
