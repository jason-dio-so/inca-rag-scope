#!/usr/bin/env python3
"""
STEP NEXT-55: GATE-55-2 - DB Marker Mapping Smoke Test
========================================================

Test that DB under40/over41 mapping recovery from leading marker contamination.

Constitutional requirement:
    - DB was 100% unmapped before STEP NEXT-55 (due to ". 상해사망" patterns)
    - After fix, DB mapping rate MUST be >= 95%
    - Core coverages (상해사망, 질병사망, etc.) MUST be mapped
"""

import json
from pathlib import Path
import pytest


# Core coverages that MUST be mapped for DB (신정원 codes exist)
CORE_DB_COVERAGES = {
    '상해사망': 'A1300',
    '질병사망': 'A1100',
    '상해후유장해(3-100%)': 'A3300_1',
    '뇌졸중진단비': 'A4103',
    '뇌출혈진단비': 'A4102',
    '뇌혈관질환진단비': 'A4101',
}


def test_gate_55_2_db_mapping_rate():
    """
    GATE-55-2: Verify DB mapping rate >= 95%.

    Constitutional requirement (STEP NEXT-55):
        - DB under40/over41 MUST have >= 95% mapping rate
        - Before fix: 0% (0/30 mapped)
        - After fix: >= 95% (>= 29/30 mapped)
    """
    scope_v3_dir = Path('data/scope_v3')

    for variant in ['db_over41', 'db_under40']:
        jsonl_path = scope_v3_dir / f'{variant}_step2_canonical_scope_v1.jsonl'

        assert jsonl_path.exists(), f"DB variant {variant} not found"

        total = 0
        mapped = 0
        unmapped_examples = []

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)
                total += 1

                if entry.get('mapping_method') == 'unmapped':
                    unmapped_examples.append({
                        'coverage_name_raw': entry.get('coverage_name_raw', ''),
                        'coverage_name_normalized': entry.get('coverage_name_normalized', '')
                    })
                else:
                    mapped += 1

        mapping_rate = mapped / total if total > 0 else 0.0

        # GATE: >= 95% mapping rate required
        assert mapping_rate >= 0.95, (
            f"{variant}: Mapping rate {mapping_rate:.1%} < 95%\n"
            f"Mapped: {mapped}/{total}\n"
            f"Unmapped examples: {unmapped_examples[:5]}"
        )


def test_gate_55_2_db_core_coverages():
    """
    GATE-55-2: Verify core DB coverages are mapped.

    Constitutional requirement (STEP NEXT-55):
        - Core coverages (상해사망, 질병사망, etc.) MUST be mapped
        - These were ALL unmapped before fix (due to ". " prefix)
        - Verify exact canonical codes
    """
    scope_v3_dir = Path('data/scope_v3')

    for variant in ['db_over41', 'db_under40']:
        jsonl_path = scope_v3_dir / f'{variant}_step2_canonical_scope_v1.jsonl'

        assert jsonl_path.exists(), f"DB variant {variant} not found"

        # Build index: coverage_name_normalized -> canonical_code
        coverage_index = {}

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)
                coverage_name_normalized = entry.get('coverage_name_normalized', '')
                coverage_code = entry.get('coverage_code')

                if coverage_code:
                    coverage_index[coverage_name_normalized] = coverage_code

        # Verify each core coverage is mapped with correct code
        missing = []
        wrong_code = []

        for coverage_name, expected_code in CORE_DB_COVERAGES.items():
            actual_code = coverage_index.get(coverage_name)

            if actual_code is None:
                missing.append(coverage_name)
            elif actual_code != expected_code:
                wrong_code.append({
                    'coverage': coverage_name,
                    'expected': expected_code,
                    'actual': actual_code
                })

        # GATE: All core coverages must be mapped with correct codes
        assert len(missing) == 0, (
            f"{variant}: {len(missing)} core coverage(s) not mapped: {missing}"
        )

        assert len(wrong_code) == 0, (
            f"{variant}: {len(wrong_code)} core coverage(s) have wrong code:\n"
            f"{wrong_code}"
        )


def test_gate_55_2_db_no_dot_markers():
    """
    GATE-55-2: Verify no dot markers in DB normalized names.

    Constitutional requirement (STEP NEXT-55):
        - DB rows should NOT have ". " prefix in coverage_name_normalized
        - This is the root cause that was fixed
    """
    scope_v3_dir = Path('data/scope_v3')

    for variant in ['db_over41', 'db_under40']:
        jsonl_path = scope_v3_dir / f'{variant}_step2_sanitized_scope_v1.jsonl'

        assert jsonl_path.exists(), f"DB variant {variant} not found"

        dot_marker_rows = []

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                entry = json.loads(line)
                coverage_name_normalized = entry.get('coverage_name_normalized', '')

                if coverage_name_normalized.startswith('.'):
                    dot_marker_rows.append({
                        'line': line_num,
                        'coverage_name_normalized': coverage_name_normalized
                    })

        # GATE: Zero dot markers allowed
        assert len(dot_marker_rows) == 0, (
            f"{variant}: {len(dot_marker_rows)} rows still have dot markers:\n"
            f"{dot_marker_rows[:5]}"
        )


if __name__ == '__main__':
    # Run with pytest
    pytest.main([__file__, '-v'])
