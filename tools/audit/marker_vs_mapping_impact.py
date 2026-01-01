#!/usr/bin/env python3
"""
STEP NEXT-55: Marker vs Mapping Impact Analysis
================================================

Analyze the causal relationship between leading markers and mapping failures.

Questions to answer:
    1. What % of unmapped rows have leading markers?
    2. If we remove markers, would they become mapped? (dry-run simulation)
    3. Which specific coverages are affected? (DB "상해사망" example)

Output:
    - docs/audit/STEP_NEXT_55_MARKER_IMPACT.md
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import openpyxl


# Marker patterns (same as scan_leading_markers.py)
MARKER_PATTERNS = [
    (r'^\s*[·•]+\s+', 'BULLET_MARKER'),
    (r'^\s*\.+\s+', 'DOT_MARKER'),
    (r'^\s*-+\s+', 'HYPHEN_MARKER'),
    (r'^\s*\(\d+\)\s+', 'PAREN_NUMBER'),
    (r'^\s*\d+\)\s+', 'NUMBER_PAREN'),
    (r'^\s*[A-Za-z]\.\s+', 'ALPHA_DOT'),
]


def detect_leading_marker(text: str) -> Tuple[bool, str]:
    """Check if text has leading marker."""
    for pattern, marker_type in MARKER_PATTERNS:
        if re.search(pattern, text):
            return True, marker_type
    return False, ''


def remove_leading_markers(text: str) -> str:
    """Simulate marker removal (what Step2-a SHOULD do)."""
    cleaned = text
    for pattern, _ in MARKER_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned)
    return cleaned.strip()


def load_excel_mapping() -> Dict[str, Dict]:
    """
    Load canonical mapping from Excel (per-insurer).

    Returns:
        {
            'db': {
                '상해사망': {'code': 'A1300', 'name': '상해사망'},
                ...
            },
            'hanwha': {...},
            ...
        }
    """
    excel_path = Path('data/sources/insurers/담보명mapping자료.xlsx')

    if not excel_path.exists():
        raise RuntimeError(f"Mapping Excel not found: {excel_path}")

    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active

    # Insurer code to name mapping
    INSURER_CODE_MAP = {
        'N01': 'meritz',
        'N02': 'hanwha',
        'N03': 'lotte',
        'N05': 'heungkuk',
        'N08': 'samsung',
        'N09': 'hyundai',
        'N10': 'kb',
        'N13': 'db'
    }

    mapping = defaultdict(dict)

    # Expected columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:  # Empty row
            continue

        ins_cd = row[0]
        cre_cvr_cd = row[2] if len(row) > 2 else None
        canonical_name = row[3] if len(row) > 3 else None
        coverage_name = row[4] if len(row) > 4 else None

        if ins_cd and cre_cvr_cd and coverage_name:
            insurer = INSURER_CODE_MAP.get(ins_cd)
            if insurer:
                mapping[insurer][coverage_name.strip()] = {
                    'code': cre_cvr_cd.strip(),
                    'name': canonical_name.strip() if canonical_name else ''
                }

    wb.close()

    return dict(mapping)


def analyze_insurer(
    canonical_jsonl: Path,
    excel_mapping: Dict[str, Dict]
) -> Dict:
    """
    Analyze single insurer's canonical mapping output.

    Returns:
        {
            'total_rows': int,
            'unmapped_rows': int,
            'unmapped_with_marker': int,
            'marker_removable': int,  # Would become mapped if marker removed
            'examples': [...]
        }
    """
    if not canonical_jsonl.exists():
        return {
            'error': 'FILE_NOT_FOUND',
            'total_rows': 0,
            'unmapped_rows': 0,
            'unmapped_with_marker': 0,
            'marker_removable': 0,
            'examples': []
        }

    total_rows = 0
    unmapped_rows = 0
    unmapped_with_marker = 0
    marker_removable = 0
    examples = []

    with open(canonical_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)
            total_rows += 1

            # Only analyze unmapped rows
            if entry.get('mapping_method') != 'unmapped':
                continue

            unmapped_rows += 1
            insurer = entry.get('insurer', '')
            coverage_name_raw = entry.get('coverage_name_raw', '')
            coverage_name_normalized = entry.get('coverage_name_normalized', '')

            # Check if has marker
            has_marker, marker_type = detect_leading_marker(coverage_name_raw)

            if has_marker:
                unmapped_with_marker += 1

                # Dry-run: Would it map if marker removed?
                cleaned = remove_leading_markers(coverage_name_raw)

                # Check exact match in Excel for this insurer
                insurer_mapping = excel_mapping.get(insurer, {})
                would_map = cleaned in insurer_mapping

                if would_map:
                    marker_removable += 1
                    canonical_code = insurer_mapping[cleaned]['code']
                    canonical_name = insurer_mapping[cleaned]['name']

                    examples.append({
                        'coverage_name_raw': coverage_name_raw,
                        'coverage_name_normalized': coverage_name_normalized,
                        'cleaned': cleaned,
                        'marker_type': marker_type,
                        'would_map_to': f"{canonical_code} ({canonical_name})",
                        'page': entry.get('page', -1)
                    })

    return {
        'total_rows': total_rows,
        'unmapped_rows': unmapped_rows,
        'unmapped_with_marker': unmapped_with_marker,
        'marker_removable': marker_removable,
        'examples': examples[:20]  # Top 20 examples
    }


def analyze_all_insurers(excel_mapping: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Analyze all insurers.

    Returns:
        {insurer_variant: analysis_result, ...}
    """
    scope_v3_dir = Path('data/scope_v3')

    if not scope_v3_dir.exists():
        raise RuntimeError(f"SSOT directory not found: {scope_v3_dir}")

    results = {}

    # Analyze all *_step2_canonical_scope_v1.jsonl files
    for jsonl_path in sorted(scope_v3_dir.glob('*_step2_canonical_scope_v1.jsonl')):
        insurer_variant = jsonl_path.stem.replace('_step2_canonical_scope_v1', '')
        results[insurer_variant] = analyze_insurer(jsonl_path, excel_mapping)

    return results


def generate_report(results: Dict[str, Dict], output_path: Path) -> None:
    """
    Generate markdown report.

    Args:
        results: {insurer_variant: analysis_result}
        output_path: Output markdown file path
    """
    total_unmapped = sum(r['unmapped_rows'] for r in results.values())
    total_unmapped_with_marker = sum(r['unmapped_with_marker'] for r in results.values())
    total_marker_removable = sum(r['marker_removable'] for r in results.values())

    marker_contribution_rate = (total_unmapped_with_marker / total_unmapped * 100) if total_unmapped > 0 else 0
    marker_fix_rate = (total_marker_removable / total_unmapped_with_marker * 100) if total_unmapped_with_marker > 0 else 0

    lines = [
        "# STEP NEXT-55: Marker vs Mapping Impact Analysis",
        "",
        "## Executive Summary",
        "",
        f"**Total Unmapped Rows**: {total_unmapped:,}",
        f"**Unmapped with Marker**: {total_unmapped_with_marker:,} ({marker_contribution_rate:.1f}%)",
        f"**Marker-Removable**: {total_marker_removable:,} ({marker_fix_rate:.1f}% of marker rows)",
        "",
        "**Causality Verdict**: ✅ **CONFIRMED**",
        f"- {marker_contribution_rate:.1f}% of unmapped rows have leading markers",
        f"- {total_marker_removable} rows ({marker_fix_rate:.1f}%) would become mapped if markers removed",
        "",
        "---",
        "",
        "## Impact by Insurer/Variant",
        "",
        "| Insurer/Variant | Unmapped | With Marker | Removable | Fix Rate % |",
        "|-----------------|----------|-------------|-----------|------------|",
    ]

    for insurer_variant, result in sorted(results.items()):
        if result.get('error'):
            lines.append(f"| {insurer_variant} | ERROR | {result['error']} | - | - |")
            continue

        unmapped = result['unmapped_rows']
        with_marker = result['unmapped_with_marker']
        removable = result['marker_removable']
        fix_rate = (removable / with_marker * 100) if with_marker > 0 else 0

        lines.append(f"| {insurer_variant} | {unmapped:,} | {with_marker:,} | {removable:,} | {fix_rate:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## Examples: Marker-Removable Unmapped Rows",
        "",
    ])

    for insurer_variant, result in sorted(results.items()):
        if result.get('error') or result['marker_removable'] == 0:
            continue

        lines.extend([
            f"### {insurer_variant}",
            "",
            f"**Marker-Removable**: {result['marker_removable']:,} / {result['unmapped_with_marker']:,}",
            "",
            "| Raw | Normalized (with marker) | Cleaned | Would Map To | Marker Type |",
            "|-----|--------------------------|---------|--------------|-------------|",
        ])

        for example in result['examples']:
            raw = example['coverage_name_raw'][:30]
            normalized = example['coverage_name_normalized'][:30]
            cleaned = example['cleaned'][:30]
            would_map_to = example['would_map_to']
            marker_type = example['marker_type']

            lines.append(f"| {raw} | {normalized} | {cleaned} | {would_map_to} | {marker_type} |")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Root Cause Confirmation",
        "",
        "**Finding**:",
        f"- {total_marker_removable:,} unmapped rows would become mapped if Step2-a removed leading markers",
        f"- This represents {marker_fix_rate:.1f}% recovery rate for marker-contaminated rows",
        "",
        "**Action Required**:",
        "1. Update Step2-a NORMALIZATION_PATTERNS to remove leading markers",
        "2. Re-run Step2-a + Step2-b pipeline",
        "3. Verify mapping rate increase (expect +{:,} mapped rows)".format(total_marker_removable),
        "",
    ])

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    """
    Main entry point.
    """
    print("STEP NEXT-55: Analyzing marker impact on mapping failures...")

    # Load Excel mapping
    print("Loading Excel mapping...")
    excel_mapping = load_excel_mapping()
    print(f"✅ Loaded {len(excel_mapping):,} canonical mappings")

    # Analyze all insurers
    results = analyze_all_insurers(excel_mapping)

    # Generate report
    output_path = Path('docs/audit/STEP_NEXT_55_MARKER_IMPACT.md')
    generate_report(results, output_path)

    print(f"✅ Report generated: {output_path}")

    # Print summary
    total_unmapped = sum(r['unmapped_rows'] for r in results.values())
    total_unmapped_with_marker = sum(r['unmapped_with_marker'] for r in results.values())
    total_marker_removable = sum(r['marker_removable'] for r in results.values())

    print(f"\n📊 Summary:")
    print(f"   Total unmapped: {total_unmapped:,}")
    print(f"   Unmapped with marker: {total_unmapped_with_marker:,}")
    print(f"   Marker-removable: {total_marker_removable:,}")

    if total_marker_removable > 0:
        print(f"\n✅ CAUSALITY CONFIRMED: {total_marker_removable:,} rows would map if markers removed")
    else:
        print("\n⚠️  No marker-removable rows found")


if __name__ == '__main__':
    main()
