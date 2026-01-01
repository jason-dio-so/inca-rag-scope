#!/usr/bin/env python3
"""
STEP NEXT-55: Leading Marker Contamination Scan
================================================

Scan all Step2-a sanitized outputs for leading markers that should have been removed.

Target patterns (problem markers):
    - ^\s*[·•\.\-]+\s+     (bullet/dot/hyphen)
    - ^\s*\(\d+\)\s+       (parenthesized number)
    - ^\s*\d+\)\s+         (number with closing paren)
    - ^\s*[A-Za-z]\.\s+    (alphabetic section marker)

Output:
    - docs/audit/STEP_NEXT_55_LEADING_MARKER_SCAN.md
    - Per-insurer statistics + top 20 examples
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


# Problem marker patterns
MARKER_PATTERNS = [
    (r'^\s*[·•]+\s+', 'BULLET_MARKER'),
    (r'^\s*\.+\s+', 'DOT_MARKER'),
    (r'^\s*-+\s+', 'HYPHEN_MARKER'),
    (r'^\s*\(\d+\)\s+', 'PAREN_NUMBER'),
    (r'^\s*\d+\)\s+', 'NUMBER_PAREN'),
    (r'^\s*[A-Za-z]\.\s+', 'ALPHA_DOT'),
]


def detect_leading_marker(text: str) -> Tuple[bool, str]:
    """
    Check if text starts with a problem marker.

    Returns:
        (has_marker, marker_type)
    """
    for pattern, marker_type in MARKER_PATTERNS:
        if re.search(pattern, text):
            return True, marker_type
    return False, ''


def scan_file(jsonl_path: Path) -> Dict:
    """
    Scan single sanitized JSONL for leading markers.

    Returns:
        {
            'total_rows': int,
            'marker_hits': int,
            'marker_type_counts': {marker_type: count},
            'examples': [(coverage_name_normalized, page, y0, y1, extraction_mode), ...]
        }
    """
    if not jsonl_path.exists():
        return {
            'error': 'FILE_NOT_FOUND',
            'total_rows': 0,
            'marker_hits': 0,
            'marker_type_counts': {},
            'examples': []
        }

    total_rows = 0
    marker_hits = 0
    marker_type_counts = defaultdict(int)
    examples = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)
            total_rows += 1

            # Check normalized name (this is what Step2-b sees)
            coverage_name_normalized = entry.get('coverage_name_normalized', '')
            has_marker, marker_type = detect_leading_marker(coverage_name_normalized)

            if has_marker:
                marker_hits += 1
                marker_type_counts[marker_type] += 1

                # Collect example with metadata
                examples.append({
                    'coverage_name_raw': entry.get('coverage_name_raw', ''),
                    'coverage_name_normalized': coverage_name_normalized,
                    'marker_type': marker_type,
                    'page': entry.get('page', -1),
                    'y0': entry.get('y0', -1),
                    'y1': entry.get('y1', -1),
                    'extraction_mode': entry.get('extraction_mode', 'UNKNOWN'),
                })

    return {
        'total_rows': total_rows,
        'marker_hits': marker_hits,
        'marker_type_counts': dict(marker_type_counts),
        'examples': examples[:20]  # Top 20 examples
    }


def scan_all_insurers() -> Dict[str, Dict]:
    """
    Scan all Step2-a sanitized outputs in data/scope_v3/.

    Returns:
        {insurer_variant: scan_result, ...}
    """
    scope_v3_dir = Path('data/scope_v3')

    if not scope_v3_dir.exists():
        raise RuntimeError(f"SSOT directory not found: {scope_v3_dir}")

    results = {}

    # Scan all *_step2_sanitized_scope_v1.jsonl files
    for jsonl_path in sorted(scope_v3_dir.glob('*_step2_sanitized_scope_v1.jsonl')):
        insurer_variant = jsonl_path.stem.replace('_step2_sanitized_scope_v1', '')
        results[insurer_variant] = scan_file(jsonl_path)

    return results


def generate_report(results: Dict[str, Dict], output_path: Path) -> None:
    """
    Generate markdown report.

    Args:
        results: {insurer_variant: scan_result}
        output_path: Output markdown file path
    """
    total_insurers = len(results)
    total_rows_all = sum(r['total_rows'] for r in results.values())
    total_marker_hits_all = sum(r['marker_hits'] for r in results.values())

    contamination_rate = (total_marker_hits_all / total_rows_all * 100) if total_rows_all > 0 else 0

    lines = [
        "# STEP NEXT-55: Leading Marker Contamination Scan",
        "",
        f"**Scan Date**: {Path(__file__).stat().st_mtime}",
        f"**Total Insurers/Variants**: {total_insurers}",
        f"**Total Rows**: {total_rows_all:,}",
        f"**Marker Hits**: {total_marker_hits_all:,}",
        f"**Contamination Rate**: {contamination_rate:.2f}%",
        "",
        "---",
        "",
        "## Summary by Insurer/Variant",
        "",
        "| Insurer/Variant | Total Rows | Marker Hits | Contamination % |",
        "|-----------------|------------|-------------|-----------------|",
    ]

    for insurer_variant, result in sorted(results.items()):
        if result.get('error'):
            lines.append(f"| {insurer_variant} | ERROR | {result['error']} | - |")
            continue

        total_rows = result['total_rows']
        marker_hits = result['marker_hits']
        contamination = (marker_hits / total_rows * 100) if total_rows > 0 else 0

        lines.append(f"| {insurer_variant} | {total_rows:,} | {marker_hits:,} | {contamination:.2f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## Marker Type Distribution (All Insurers)",
        "",
    ])

    # Aggregate marker type counts
    marker_type_totals = defaultdict(int)
    for result in results.values():
        if not result.get('error'):
            for marker_type, count in result.get('marker_type_counts', {}).items():
                marker_type_totals[marker_type] += count

    lines.extend([
        "| Marker Type | Total Count |",
        "|-------------|-------------|",
    ])

    for marker_type, count in sorted(marker_type_totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {marker_type} | {count:,} |")

    lines.extend([
        "",
        "---",
        "",
        "## Examples by Insurer/Variant (Top 20 per insurer)",
        "",
    ])

    for insurer_variant, result in sorted(results.items()):
        if result.get('error') or result['marker_hits'] == 0:
            continue

        lines.extend([
            f"### {insurer_variant}",
            "",
            f"**Marker Hits**: {result['marker_hits']:,} / {result['total_rows']:,}",
            "",
            "| Raw | Normalized | Marker Type | Page | Y0-Y1 | Mode |",
            "|-----|------------|-------------|------|-------|------|",
        ])

        for example in result['examples']:
            raw = example['coverage_name_raw'][:40]
            normalized = example['coverage_name_normalized'][:40]
            marker_type = example['marker_type']
            page = example['page']
            y0 = example['y0']
            y1 = example['y1']
            mode = example['extraction_mode']

            lines.append(f"| {raw} | {normalized} | {marker_type} | {page} | {y0:.0f}-{y1:.0f} | {mode} |")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Root Cause Verdict",
        "",
        "**Observation**:",
        f"- {total_marker_hits_all:,} rows ({contamination_rate:.2f}%) have leading markers in `coverage_name_normalized`",
        "- This confirms Step2-a normalization is missing marker removal patterns",
        "",
        "**Action Required**:",
        "- Add LEADING_BULLET_MARKER, LEADING_DOT_MARKER patterns to NORMALIZATION_PATTERNS",
        "- Re-run Step2-a to clean coverage_name_normalized",
        "- Verify GATE-55-1 (zero marker contamination)",
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
    print("STEP NEXT-55: Scanning leading marker contamination...")

    # Scan all insurers
    results = scan_all_insurers()

    # Generate report
    output_path = Path('docs/audit/STEP_NEXT_55_LEADING_MARKER_SCAN.md')
    generate_report(results, output_path)

    print(f"✅ Report generated: {output_path}")

    # Print summary
    total_rows_all = sum(r['total_rows'] for r in results.values())
    total_marker_hits_all = sum(r['marker_hits'] for r in results.values())
    contamination_rate = (total_marker_hits_all / total_rows_all * 100) if total_rows_all > 0 else 0

    print(f"\n📊 Summary:")
    print(f"   Total rows: {total_rows_all:,}")
    print(f"   Marker hits: {total_marker_hits_all:,}")
    print(f"   Contamination rate: {contamination_rate:.2f}%")

    if total_marker_hits_all > 0:
        print("\n⚠️  CONTAMINATION DETECTED: Step2-a normalization needs update")
    else:
        print("\n✅ CLEAN: No leading markers found")


if __name__ == '__main__':
    main()
