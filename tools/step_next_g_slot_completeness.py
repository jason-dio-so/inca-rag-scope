#!/usr/bin/env python3
"""
STEP NEXT-G: Diagnosis Slot Completeness Validator

Validates slot completeness for ALL diagnosis benefits (Samsung + KB).

Classifies each UNKNOWN slot:
- UNKNOWN_MISSING: No evidence in source documents (doc gap)
- UNKNOWN_SEARCH_FAIL: Evidence exists but extraction/attribution failed

NO Step1-3 changes.
NO LLM.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


# Core slots to validate
CORE_SLOTS = [
    "start_date",
    "waiting_period",
    "reduction",
    "payout_limit",
    "entry_age",
    "exclusions"
]

# Extended slots (STEP NEXT-76-A)
EXTENDED_SLOTS = [
    "underwriting_condition",
    "mandatory_dependency",
    "payout_frequency",
    "industry_aggregate_limit"
]

ALL_SLOTS = CORE_SLOTS + EXTENDED_SLOTS


def load_registry():
    """Load diagnosis coverage registry"""
    registry_path = Path("data/registry/diagnosis_coverage_registry.json")
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_step3_coverage(insurer: str, coverage_code: str) -> Dict:
    """Load specific coverage from Step3 output"""
    step3_file = Path(f"data/scope_v3/{insurer}_step3_evidence_enriched_v1_gated.jsonl")

    if not step3_file.exists():
        # Try uppercase
        step3_file = Path(f"data/scope_v3/{insurer.upper()}_step3_evidence_enriched_v1_gated.jsonl")

    if not step3_file.exists():
        return None

    with open(step3_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get('coverage_code') == coverage_code:
                return row

    return None


def classify_unknown_reason(
    slot_key: str,
    compare_slot: Dict,
    step3_coverage: Dict
) -> str:
    """
    Classify UNKNOWN slot into:
    - UNKNOWN_MISSING: No evidence in source docs
    - UNKNOWN_SEARCH_FAIL: Evidence exists but extraction/attribution failed
    """
    # Check Step3 evidence_status
    if not step3_coverage:
        return "UNKNOWN_MISSING (Step3 file not found)"

    step3_status = step3_coverage.get('evidence_status', {}).get(slot_key, 'UNKNOWN')
    step3_evidences = [
        ev for ev in step3_coverage.get('evidence', [])
        if ev.get('slot_key') == slot_key
    ]

    # If Step3 status is FOUND/FOUND_GLOBAL/CONFLICT but Step4 is UNKNOWN
    # → Search succeeded but G5 gate or normalization failed
    if step3_status in ['FOUND', 'FOUND_GLOBAL', 'CONFLICT']:
        notes = compare_slot.get('notes', '')
        if 'G5 Gate:' in notes:
            # G5 attribution gate blocked it
            gate_reason = notes.split('G5 Gate:')[1].split('(')[0].strip()
            return f"UNKNOWN_SEARCH_FAIL (G5: {gate_reason})"
        else:
            # Other failure (normalization, schema, etc)
            return "UNKNOWN_SEARCH_FAIL (normalization/schema)"

    # If Step3 status is UNKNOWN and no evidences
    # → Search failed, no evidence found in docs
    if step3_status == 'UNKNOWN' and len(step3_evidences) == 0:
        return "UNKNOWN_MISSING (no evidence in docs)"

    # If Step3 status is UNKNOWN but evidences exist
    # → Evidence found but status determination failed
    if step3_status == 'UNKNOWN' and len(step3_evidences) > 0:
        return f"UNKNOWN_SEARCH_FAIL ({len(step3_evidences)} evidences but UNKNOWN)"

    # Default
    return "UNKNOWN (unclassified)"


def analyze_completeness(registry: Dict) -> Dict:
    """
    Analyze slot completeness for all diagnosis coverages.

    Returns:
        {
            "matrix": {coverage_code: {insurer: {slot: status}}},
            "summary": {...},
            "search_fail_backlog": [...]
        }
    """
    compare_rows_file = Path("data/compare_v1/compare_rows_v1.jsonl")

    # Load all diagnosis coverage rows from compare_rows
    diagnosis_rows = {}  # (coverage_code, insurer) -> row

    with open(compare_rows_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)
            code = row.get('identity', {}).get('coverage_code')
            insurer = row.get('identity', {}).get('insurer_key')

            # Filter to registry diagnosis coverages + Samsung/KB only
            if code not in registry.get('coverage_entries', {}):
                continue

            if insurer not in ['samsung', 'kb']:
                continue

            diagnosis_rows[(code, insurer)] = row

    # Build completeness matrix
    matrix = {}
    summary = {
        'total_slots_checked': 0,
        'found_count': 0,
        'unknown_missing_count': 0,
        'unknown_search_fail_count': 0,
        'by_coverage': {},
        'by_insurer': {},
        'by_slot': {}
    }

    search_fail_backlog = []

    for (coverage_code, insurer), row in diagnosis_rows.items():
        if coverage_code not in matrix:
            matrix[coverage_code] = {}

        if insurer not in matrix[coverage_code]:
            matrix[coverage_code][insurer] = {}

        slots = row.get('slots', {})

        # Load Step3 coverage for detailed analysis
        step3_coverage = load_step3_coverage(insurer, coverage_code)

        for slot_key in ALL_SLOTS:
            slot = slots.get(slot_key, {})
            status = slot.get('status', 'UNKNOWN')

            summary['total_slots_checked'] += 1

            # Classify slot
            if status in ['FOUND', 'FOUND_GLOBAL', 'CONFLICT']:
                classification = 'FOUND'
                summary['found_count'] += 1
            elif status == 'UNKNOWN':
                # Classify UNKNOWN reason
                reason = classify_unknown_reason(slot_key, slot, step3_coverage)

                if 'UNKNOWN_MISSING' in reason:
                    classification = 'UNKNOWN_MISSING'
                    summary['unknown_missing_count'] += 1
                elif 'UNKNOWN_SEARCH_FAIL' in reason:
                    classification = 'UNKNOWN_SEARCH_FAIL'
                    summary['unknown_search_fail_count'] += 1

                    # Add to search-fail backlog
                    search_fail_backlog.append({
                        'coverage_code': coverage_code,
                        'insurer': insurer,
                        'slot': slot_key,
                        'reason': reason,
                        'step3_status': step3_coverage.get('evidence_status', {}).get(slot_key) if step3_coverage else None,
                        'evidence_count': len([
                            ev for ev in step3_coverage.get('evidence', [])
                            if ev.get('slot_key') == slot_key
                        ]) if step3_coverage else 0
                    })
                else:
                    classification = reason
            else:
                classification = status

            matrix[coverage_code][insurer][slot_key] = {
                'status': status,
                'classification': classification
            }

            # Update summaries
            coverage_key = f"{coverage_code} ({registry['coverage_entries'][coverage_code]['canonical_name']})"
            if coverage_key not in summary['by_coverage']:
                summary['by_coverage'][coverage_key] = {'found': 0, 'missing': 0, 'search_fail': 0, 'total': 0}

            if insurer not in summary['by_insurer']:
                summary['by_insurer'][insurer] = {'found': 0, 'missing': 0, 'search_fail': 0, 'total': 0}

            if slot_key not in summary['by_slot']:
                summary['by_slot'][slot_key] = {'found': 0, 'missing': 0, 'search_fail': 0, 'total': 0}

            summary['by_coverage'][coverage_key]['total'] += 1
            summary['by_insurer'][insurer]['total'] += 1
            summary['by_slot'][slot_key]['total'] += 1

            if classification == 'FOUND':
                summary['by_coverage'][coverage_key]['found'] += 1
                summary['by_insurer'][insurer]['found'] += 1
                summary['by_slot'][slot_key]['found'] += 1
            elif classification == 'UNKNOWN_MISSING':
                summary['by_coverage'][coverage_key]['missing'] += 1
                summary['by_insurer'][insurer]['missing'] += 1
                summary['by_slot'][slot_key]['missing'] += 1
            elif classification == 'UNKNOWN_SEARCH_FAIL':
                summary['by_coverage'][coverage_key]['search_fail'] += 1
                summary['by_insurer'][insurer]['search_fail'] += 1
                summary['by_slot'][slot_key]['search_fail'] += 1

    return {
        'matrix': matrix,
        'summary': summary,
        'search_fail_backlog': search_fail_backlog
    }


def print_report(analysis: Dict, registry: Dict):
    """Print completeness report"""
    print("=" * 80)
    print("STEP NEXT-G: Diagnosis Slot Completeness Report (Samsung + KB)")
    print("=" * 80)
    print()

    summary = analysis['summary']

    # Overall stats
    print(f"📊 Overall Statistics")
    print(f"  Total slots checked: {summary['total_slots_checked']}")
    print(f"  ✅ FOUND: {summary['found_count']} ({summary['found_count']/summary['total_slots_checked']*100:.1f}%)")
    print(f"  ❓ UNKNOWN_MISSING: {summary['unknown_missing_count']} ({summary['unknown_missing_count']/summary['total_slots_checked']*100:.1f}%)")
    print(f"  🔍 UNKNOWN_SEARCH_FAIL: {summary['unknown_search_fail_count']} ({summary['unknown_search_fail_count']/summary['total_slots_checked']*100:.1f}%)")
    print()

    # By insurer
    print(f"📋 Completeness by Insurer")
    for insurer, stats in sorted(summary['by_insurer'].items()):
        total = stats['total']
        found_pct = stats['found'] / total * 100 if total > 0 else 0
        print(f"  {insurer.upper()}:")
        print(f"    ✅ FOUND: {stats['found']}/{total} ({found_pct:.1f}%)")
        print(f"    ❓ MISSING: {stats['missing']}/{total} ({stats['missing']/total*100:.1f}%)")
        print(f"    🔍 SEARCH_FAIL: {stats['search_fail']}/{total} ({stats['search_fail']/total*100:.1f}%)")
    print()

    # By coverage
    print(f"📋 Completeness by Coverage")
    for coverage, stats in sorted(summary['by_coverage'].items()):
        total = stats['total']
        found_pct = stats['found'] / total * 100 if total > 0 else 0
        print(f"  {coverage}:")
        print(f"    ✅ FOUND: {stats['found']}/{total} ({found_pct:.1f}%)")
        print(f"    ❓ MISSING: {stats['missing']}/{total}")
        print(f"    🔍 SEARCH_FAIL: {stats['search_fail']}/{total}")
    print()

    # By slot
    print(f"📋 Completeness by Slot")
    print(f"  Core Slots:")
    for slot in CORE_SLOTS:
        stats = summary['by_slot'].get(slot, {'found': 0, 'missing': 0, 'search_fail': 0, 'total': 0})
        total = stats['total']
        if total == 0:
            continue
        found_pct = stats['found'] / total * 100
        print(f"    {slot}: {stats['found']}/{total} ({found_pct:.1f}%) | MISSING:{stats['missing']} | SEARCH_FAIL:{stats['search_fail']}")

    print(f"  Extended Slots:")
    for slot in EXTENDED_SLOTS:
        stats = summary['by_slot'].get(slot, {'found': 0, 'missing': 0, 'search_fail': 0, 'total': 0})
        total = stats['total']
        if total == 0:
            continue
        found_pct = stats['found'] / total * 100
        print(f"    {slot}: {stats['found']}/{total} ({found_pct:.1f}%) | MISSING:{stats['missing']} | SEARCH_FAIL:{stats['search_fail']}")
    print()

    # Search-fail backlog
    backlog = analysis['search_fail_backlog']
    print(f"🔍 Search-Fail Backlog ({len(backlog)} items)")
    print()

    if backlog:
        # Group by reason
        by_reason = defaultdict(list)
        for item in backlog:
            reason_key = item['reason'].split('(')[1].split(')')[0] if '(' in item['reason'] else item['reason']
            by_reason[reason_key].append(item)

        for reason, items in sorted(by_reason.items(), key=lambda x: -len(x[1])):
            print(f"  {reason}: {len(items)} cases")
            for item in items[:5]:  # Show first 5
                entry = registry['coverage_entries'][item['coverage_code']]
                print(f"    - {item['insurer']} / {item['coverage_code']} ({entry['canonical_name']}) / {item['slot']}")
                if item['evidence_count'] > 0:
                    print(f"      Evidence count: {item['evidence_count']}, Step3 status: {item['step3_status']}")
            if len(items) > 5:
                print(f"    ... and {len(items)-5} more")
            print()
    else:
        print("  ✅ No search failures!")
    print()


def generate_matrix_table(analysis: Dict, registry: Dict):
    """Generate completeness matrix table (Markdown)"""
    matrix = analysis['matrix']

    lines = []
    lines.append("# Diagnosis Slot Completeness Matrix (Samsung + KB)")
    lines.append("")

    for coverage_code in sorted(matrix.keys()):
        entry = registry['coverage_entries'][coverage_code]
        lines.append(f"## {coverage_code}: {entry['canonical_name']}")
        lines.append("")

        # Build table header
        insurers = sorted(matrix[coverage_code].keys())
        header = "| Slot | " + " | ".join([ins.upper() for ins in insurers]) + " |"
        separator = "|------|" + "|".join(["------" for _ in insurers]) + "|"

        lines.append(header)
        lines.append(separator)

        # Build table rows
        for slot_key in ALL_SLOTS:
            row_cells = [slot_key]
            for insurer in insurers:
                slot_data = matrix[coverage_code][insurer].get(slot_key, {})
                classification = slot_data.get('classification', 'UNKNOWN')

                if classification == 'FOUND':
                    cell = "✅"
                elif classification == 'UNKNOWN_MISSING':
                    cell = "❓"
                elif 'UNKNOWN_SEARCH_FAIL' in classification:
                    cell = "🔍"
                else:
                    cell = "?"

                row_cells.append(cell)

            lines.append("| " + " | ".join(row_cells) + " |")

        lines.append("")

    lines.append("**Legend:**")
    lines.append("- ✅ FOUND (evidence extracted successfully)")
    lines.append("- ❓ UNKNOWN_MISSING (no evidence in source documents)")
    lines.append("- 🔍 UNKNOWN_SEARCH_FAIL (evidence exists but extraction/attribution failed)")
    lines.append("")

    return "\n".join(lines)


def main():
    print("Loading registry...")
    registry = load_registry()

    print("Analyzing slot completeness...")
    analysis = analyze_completeness(registry)

    print_report(analysis, registry)

    # Save detailed analysis
    output_dir = Path("docs/audit")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_file = output_dir / "step_next_g_slot_completeness.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"📝 Detailed analysis saved: {json_file}")

    # Save matrix table
    matrix_file = output_dir / "step_next_g_completeness_matrix.md"
    with open(matrix_file, 'w', encoding='utf-8') as f:
        f.write(generate_matrix_table(analysis, registry))
    print(f"📝 Completeness matrix saved: {matrix_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
