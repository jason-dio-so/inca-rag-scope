#!/usr/bin/env python3
"""
STEP NEXT-59: Unmapped Status Report (SSOT Separated)

Generates company-by-company status report with proper separation:
- Group A: Step2-a dropped items (fragments/noise)
- Group B: Step2-b unmapped items (legitimate unmapped)

Constitutional Rules:
- NO LLM
- NO Step2-a/Step2-b logic modification
- SSOT paths: data/scope_v3/ only
- Reproducible (same input → same output)
- Overview numbers MUST match Step2-b mapping_report exactly
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional


def get_display_name(entry: Dict) -> Optional[str]:
    """
    Extract display name with field priority (STEP NEXT-59 Constitutional).

    Priority:
    1. coverage_name_normalized
    2. coverage_name_raw
    3. coverage_name
    4. None (invalid, exclude from report)
    """
    for field in ['coverage_name_normalized', 'coverage_name_raw', 'coverage_name']:
        if field in entry and entry[field] and entry[field].strip():
            return entry[field].strip()
    return None


def load_step2b_summary(mapping_report_path: Path) -> Dict:
    """
    Load Step2-b mapping summary (SSOT for overview numbers).
    """
    entries = []
    with open(mapping_report_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    total = len(entries)
    mapped = sum(1 for e in entries if e.get('mapping_method') != 'unmapped')
    unmapped = sum(1 for e in entries if e.get('mapping_method') == 'unmapped')

    return {
        'total': total,
        'mapped': mapped,
        'unmapped': unmapped,
        'mapping_rate': round(mapped / total * 100, 1) if total > 0 else 0.0
    }


def load_group_b_unmapped(mapping_report_path: Path) -> List[str]:
    """
    Load Group B: Step2-b unmapped items (legitimate unmapped).
    """
    unmapped_items = []
    invalid_count = 0

    with open(mapping_report_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry.get('mapping_method') == 'unmapped':
                    display_name = get_display_name(entry)
                    if display_name:
                        unmapped_items.append(display_name)
                    else:
                        invalid_count += 1

    # Return unique sorted items
    return sorted(set(unmapped_items))


def load_group_a_dropped(dropped_path: Path) -> Dict:
    """
    Load Group A: Step2-a dropped items (fragments/noise).
    Returns: {'items': [...], 'reasons': Counter, 'invalid_count': int}
    """
    if not dropped_path.exists():
        return {'items': [], 'reasons': Counter(), 'invalid_count': 0}

    dropped_items = []
    drop_reasons = []
    invalid_count = 0

    with open(dropped_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                display_name = get_display_name(entry)
                if display_name:
                    dropped_items.append(display_name)
                    drop_reasons.append(entry.get('drop_reason', 'UNKNOWN'))
                else:
                    invalid_count += 1

    return {
        'items': sorted(set(dropped_items)),
        'reasons': Counter(drop_reasons),
        'invalid_count': invalid_count
    }


def generate_report(scope_v3_dir: Path, output_path: Path):
    """
    Generate SSOT-separated unmapped status report.
    """
    mapping_reports = list(scope_v3_dir.glob('*_step2_mapping_report.jsonl'))
    mapping_reports = sorted(mapping_reports, key=lambda p: p.stem.split('_step2_')[0])

    if not mapping_reports:
        print("❌ No Step2-b mapping reports found")
        return

    # Collect data per insurer
    results = {}

    for report_path in mapping_reports:
        insurer = report_path.stem.split('_step2_')[0]
        print(f"Processing {insurer}...")

        # Step2-b summary (SSOT for overview)
        step2b_summary = load_step2b_summary(report_path)

        # Group B: Step2-b unmapped (legitimate unmapped)
        group_b_items = load_group_b_unmapped(report_path)

        # Group A: Step2-a dropped (fragments/noise)
        dropped_path = scope_v3_dir / f"{insurer}_step2_dropped.jsonl"
        group_a_data = load_group_a_dropped(dropped_path)

        results[insurer] = {
            'step2b_summary': step2b_summary,
            'group_b_unmapped': group_b_items,
            'group_a_dropped': group_a_data
        }

    # Generate markdown report
    lines = []
    lines.append("# Company-by-Company Unmapped Status Report")
    lines.append("")
    lines.append("**Generated**: STEP NEXT-59 (SSOT Separated: Step2-a dropped vs Step2-b unmapped)")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("| Company | Total | Mapped | Unmapped | Rate | Dropped (Step2-a) |")
    lines.append("|---------|-------|--------|----------|------|-------------------|")

    for insurer, data in results.items():
        summary = data['step2b_summary']
        dropped_count = len(data['group_a_dropped']['items'])
        lines.append(
            f"| {insurer} | {summary['total']} | {summary['mapped']} | "
            f"{summary['unmapped']} | {summary['mapping_rate']}% | {dropped_count} |"
        )

    lines.append("")
    lines.append("**SSOT Definition**:")
    lines.append("- **Total/Mapped/Unmapped/Rate**: From Step2-b `*_step2_mapping_report.jsonl` (canonical mapping results)")
    lines.append("- **Dropped**: From Step2-a `*_step2_dropped.jsonl` (sanitize phase noise/fragments)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed sections per company
    for insurer, data in results.items():
        summary = data['step2b_summary']
        group_b = data['group_b_unmapped']
        group_a = data['group_a_dropped']

        lines.append(f"## {insurer.upper()}")
        lines.append("")
        lines.append(f"**Total Coverage Items**: {summary['total']}")
        lines.append(f"**Mapped**: {summary['mapped']} ({summary['mapping_rate']}%)")
        lines.append(f"**Unmapped**: {summary['unmapped']}")
        lines.append(f"**Dropped (Step2-a)**: {len(group_a['items'])}")
        lines.append("")

        # Group B: Step2-b unmapped (legitimate unmapped)
        if group_b:
            lines.append("### Group B: Step2-b Unmapped (Legitimate Unmapped)")
            lines.append("")
            lines.append(f"**Count**: {len(group_b)}")
            lines.append("")
            lines.append("**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.")
            lines.append("")

            sample_limit = 30
            if len(group_b) <= sample_limit:
                lines.append("**All Items**:")
                for item in group_b:
                    lines.append(f"- `{item}`")
            else:
                lines.append(f"**Sample (first {sample_limit} of {len(group_b)})**:")
                for item in group_b[:sample_limit]:
                    lines.append(f"- `{item}`")
            lines.append("")

        # Group A: Step2-a dropped (fragments/noise)
        if group_a['items']:
            lines.append("### Group A: Step2-a Dropped (Fragments/Noise)")
            lines.append("")
            lines.append(f"**Count**: {len(group_a['items'])}")
            lines.append("")
            lines.append("**Description**: Items removed by Step2-a sanitization (deterministic pattern matching).")
            lines.append("")

            # Drop reasons breakdown
            if group_a['reasons']:
                lines.append("**Drop Reasons**:")
                for reason, count in group_a['reasons'].most_common():
                    lines.append(f"- `{reason}`: {count}")
                lines.append("")

            sample_limit = 30
            if len(group_a['items']) <= sample_limit:
                lines.append("**All Items**:")
                for item in group_a['items']:
                    lines.append(f"- `{item}`")
            else:
                lines.append(f"**Sample (first {sample_limit} of {len(group_a['items'])})**:")
                for item in group_a['items'][:sample_limit]:
                    lines.append(f"- `{item}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Summary statistics
    lines.append("## Summary Statistics")
    lines.append("")

    total_all = sum(data['step2b_summary']['total'] for data in results.values())
    mapped_all = sum(data['step2b_summary']['mapped'] for data in results.values())
    unmapped_all = sum(data['step2b_summary']['unmapped'] for data in results.values())
    dropped_all = sum(len(data['group_a_dropped']['items']) for data in results.values())

    lines.append(f"- **Total Coverage Items (Step2-b)**: {total_all}")
    lines.append(f"- **Mapped**: {mapped_all} ({round(mapped_all / total_all * 100, 1)}%)")
    lines.append(f"- **Unmapped (Group B)**: {unmapped_all}")
    lines.append(f"- **Dropped (Group A, Step2-a)**: {dropped_all}")
    lines.append("")

    lines.append("## Constitutional Rules (STEP NEXT-59)")
    lines.append("")
    lines.append("1. ✅ **SSOT Separation**: Group A (Step2-a dropped) ≠ Group B (Step2-b unmapped)")
    lines.append("2. ✅ **No Fragment Logic on Step2-b**: Step2-b unmapped items are NOT re-classified as fragments")
    lines.append("3. ✅ **Field Priority**: `coverage_name_normalized` > `coverage_name_raw` > `coverage_name`")
    lines.append("4. ✅ **Overview = Step2-b SSOT**: Total/Mapped/Unmapped from mapping_report.jsonl only")
    lines.append("5. ❌ **No LLM**: Deterministic only")
    lines.append("6. ❌ **No Logic Change**: Step2-a/Step2-b unchanged")
    lines.append("")

    lines.append("## Action Items")
    lines.append("")
    lines.append("1. **Group A (Dropped)**: Already handled by Step2-a (no action needed)")
    lines.append("2. **Group B (Unmapped)**: Require manual review and Excel mapping additions")
    lines.append("   - Add missing canonical names to `data/sources/mapping/담보명mapping자료.xlsx`")
    lines.append("   - Re-run Step2-b canonical mapping")
    lines.append("")

    # Write output
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Report generated: {output_path}")
    print(f"   Total companies: {len(results)}")
    print(f"   Total items (Step2-b): {total_all}")
    print(f"   Overall mapping rate: {round(mapped_all / total_all * 100, 1)}%")
    print(f"   Group B (unmapped): {unmapped_all}")
    print(f"   Group A (dropped): {dropped_all}")


if __name__ == '__main__':
    scope_v3_dir = Path(__file__).parent.parent.parent / 'data' / 'scope_v3'
    output_path = Path(__file__).parent.parent.parent / 'docs' / 'audit' / 'UNMAPPED_STATUS_BY_COMPANY.md'

    generate_report(scope_v3_dir, output_path)
