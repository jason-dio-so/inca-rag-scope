#!/usr/bin/env python3
"""
STEP NEXT-56-C: Unmapped Diagnostic Tool

Separates unmapped items into:
- GROUP-1: Fragment/Scrap (should be dropped/normalized in Step2-a)
- GROUP-2: Legit Variant (meaningful coverage with text variations)

NO insurer-specific branching, NO LLM, deterministic only.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def is_fragment(coverage_name: str) -> Tuple[bool, str]:
    """
    Detect if coverage name is a fragment/scrap.

    Fragment indicators:
    - Unclosed parentheses: "다빈치로봇 암수술비(...("
    - Standalone clause: "최초1회", "갱신형", "기본"
    - Broken sentence: newline breaks, isolated words
    - Malformed structure: )(갱신형)담보, 신형)담보

    Args:
        coverage_name: Coverage name to check

    Returns:
        (is_fragment, reason)
    """
    name = coverage_name.strip()

    # Empty or too short (< 3 chars)
    if len(name) < 3:
        return True, "TOO_SHORT"

    # Unclosed parentheses
    open_count = name.count('(')
    close_count = name.count(')')
    if open_count != close_count:
        return True, f"UNBALANCED_PARENS (open={open_count}, close={close_count})"

    # Ends with opening paren (incomplete)
    if name.endswith('('):
        return True, "ENDS_WITH_OPEN_PAREN"

    # Starts with closing paren (broken prefix)
    if name.startswith(')'):
        return True, "STARTS_WITH_CLOSE_PAREN"

    # Standalone clause words (common fragments)
    standalone_clauses = [
        '최초1회', '최초1회한', '갱신형', '기본',
        '1회한', '연간1회한', '1년50%', '1년감액'
    ]
    if name in standalone_clauses:
        return True, f"STANDALONE_CLAUSE ({name})"

    # Malformed structure patterns
    malformed_patterns = [
        (r'\)\s*\(갱신형\)\s*담보$', 'MALFORMED_SUFFIX_1'),  # )(갱신형)담보
        (r'신형\)\s*담보$', 'MALFORMED_SUFFIX_2'),  # 신형)담보
        (r'^\([^)]*$', 'OPEN_PAREN_ONLY'),  # (something (no close)
    ]

    for pattern, reason in malformed_patterns:
        if re.search(pattern, name):
            return True, reason

    # Newline breaks (indicates text extraction error)
    if '\n' in name and len(name.split('\n')) > 2:
        return True, "MULTI_LINE_BREAK"

    return False, "OK"


def categorize_unmapped(mapping_report_jsonl: Path) -> Dict:
    """
    Categorize unmapped items into GROUP-1 (fragment) and GROUP-2 (legit variant).

    Args:
        mapping_report_jsonl: Path to *_step2_mapping_report.jsonl

    Returns:
        {
            'insurer': str,
            'total_unmapped': int,
            'group1_fragment': [...],
            'group2_legit': [...],
            'stats': {...}
        }
    """
    if not mapping_report_jsonl.exists():
        return {'error': 'FILE_NOT_FOUND'}

    # Read report
    entries = []
    with open(mapping_report_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Filter unmapped
    unmapped = [e for e in entries if e['mapping_method'] == 'unmapped']

    # Categorize
    group1_fragment = []
    group2_legit = []

    for entry in unmapped:
        coverage_name = entry['coverage_name_raw']
        is_frag, reason = is_fragment(coverage_name)

        categorized_entry = {
            'coverage_name_raw': coverage_name,
            'insurer': entry['insurer']
        }

        if is_frag:
            categorized_entry['fragment_reason'] = reason
            group1_fragment.append(categorized_entry)
        else:
            group2_legit.append(categorized_entry)

    # Extract insurer from first entry
    insurer = entries[0]['insurer'] if entries else 'unknown'

    return {
        'insurer': insurer,
        'total_unmapped': len(unmapped),
        'group1_fragment': group1_fragment,
        'group2_legit': group2_legit,
        'stats': {
            'fragment_count': len(group1_fragment),
            'legit_count': len(group2_legit),
            'fragment_ratio': len(group1_fragment) / len(unmapped) if unmapped else 0.0
        }
    }


def print_diagnosis_report(diagnosis: Dict):
    """Print human-readable diagnosis report."""

    print(f"\n{'='*80}")
    print(f"STEP NEXT-56-C: Unmapped Diagnosis Report")
    print(f"{'='*80}")
    print(f"Insurer: {diagnosis['insurer'].upper()}")
    print(f"Total unmapped: {diagnosis['total_unmapped']}")
    print(f"\nGROUP-1 (Fragment/Scrap): {diagnosis['stats']['fragment_count']} ({diagnosis['stats']['fragment_ratio']:.1%})")
    print(f"GROUP-2 (Legit Variant):  {diagnosis['stats']['legit_count']} ({1 - diagnosis['stats']['fragment_ratio']:.1%})")
    print(f"{'='*80}\n")

    # GROUP-1 details
    print(f"GROUP-1 (Fragment/Scrap) - should be dropped/normalized in Step2-a:")
    print(f"{'-'*80}")

    # Group by reason
    fragments_by_reason = defaultdict(list)
    for item in diagnosis['group1_fragment']:
        fragments_by_reason[item['fragment_reason']].append(item['coverage_name_raw'])

    for reason, names in sorted(fragments_by_reason.items()):
        print(f"\n  Reason: {reason} ({len(names)} items)")
        for name in names[:5]:  # Show first 5 examples
            print(f"    - {repr(name)}")
        if len(names) > 5:
            print(f"    ... ({len(names) - 5} more)")

    # GROUP-2 details
    print(f"\n\nGROUP-2 (Legit Variant) - meaningful coverage, needs normalization:")
    print(f"{'-'*80}")

    for item in diagnosis['group2_legit'][:20]:  # Show first 20
        print(f"  - {item['coverage_name_raw']}")

    if len(diagnosis['group2_legit']) > 20:
        print(f"  ... ({len(diagnosis['group2_legit']) - 20} more)")

    print(f"\n{'='*80}")
    print(f"DoD: GROUP-1 items should NOT appear in unmapped after Step2-a/Step2-b improvements.")
    print(f"{'='*80}\n")


def main():
    """Run diagnosis for KB and HYUNDAI."""

    scope_v3_dir = Path(__file__).parent.parent.parent / 'data' / 'scope_v3'

    insurers = ['kb', 'hyundai']

    for insurer in insurers:
        report_path = scope_v3_dir / f'{insurer}_step2_mapping_report.jsonl'

        if not report_path.exists():
            print(f"⚠️  {insurer}: mapping report not found at {report_path}")
            continue

        diagnosis = categorize_unmapped(report_path)
        print_diagnosis_report(diagnosis)

        # Save JSON output
        output_path = scope_v3_dir / f'{insurer}_step2_unmapped_diagnosis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(diagnosis, f, ensure_ascii=False, indent=2)

        print(f"✅ Diagnosis saved to: {output_path}\n")


if __name__ == '__main__':
    main()
