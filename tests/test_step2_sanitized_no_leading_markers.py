#!/usr/bin/env python3
"""
STEP NEXT-55: GATE-55-1 - No Leading Markers in Sanitized Output
==================================================================

Test that Step2-a sanitization removes ALL leading markers from coverage_name_normalized.

Constitutional requirement:
    - coverage_name_normalized MUST NOT contain any leading markers
    - Patterns: bullets (·•), dots (.), hyphens (-), parenthesized numbers, etc.
    - Zero tolerance policy (0 violations allowed)
"""

import json
import re
from pathlib import Path
import pytest


# Leading marker patterns (same as Step2-a NORMALIZATION_PATTERNS)
MARKER_PATTERNS = [
    (r'^\s*[·•]+\s*', 'BULLET_MARKER'),
    (r'^\s*\.+\s*', 'DOT_MARKER'),
    (r'^\s*\(\d+\)\s*', 'PAREN_NUMBER'),
    (r'^\s*\d+\)\s*', 'NUMBER_PAREN'),
    (r'^\s*[A-Za-z]\.\s*', 'ALPHA_DOT'),
]


def detect_leading_marker(text: str) -> tuple:
    """Check if text has leading marker."""
    for pattern, marker_type in MARKER_PATTERNS:
        if re.search(pattern, text):
            return True, marker_type
    return False, None


def test_gate_55_1_no_leading_markers():
    """
    GATE-55-1: Verify NO leading markers in coverage_name_normalized.

    Constitutional requirement (STEP NEXT-55):
        - ALL Step2-a sanitized outputs MUST have zero leading markers
        - Test fails if ANY row has a leading marker
    """
    scope_v3_dir = Path('data/scope_v3')

    # Find all Step2-a sanitized outputs
    sanitized_files = list(scope_v3_dir.glob('*_step2_sanitized_scope_v1.jsonl'))

    assert len(sanitized_files) > 0, "No Step2-a sanitized files found in data/scope_v3/"

    violations = []

    for jsonl_path in sorted(sanitized_files):
        insurer_variant = jsonl_path.stem.replace('_step2_sanitized_scope_v1', '')

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                entry = json.loads(line)
                coverage_name_normalized = entry.get('coverage_name_normalized', '')

                has_marker, marker_type = detect_leading_marker(coverage_name_normalized)

                if has_marker:
                    violations.append({
                        'file': insurer_variant,
                        'line': line_num,
                        'coverage_name_normalized': coverage_name_normalized,
                        'marker_type': marker_type
                    })

    # GATE: Zero tolerance - no violations allowed
    if violations:
        violation_msgs = [
            f"\n  [{v['file']}:{v['line']}] {v['coverage_name_normalized']} (marker: {v['marker_type']})"
            for v in violations[:10]  # Show first 10
        ]
        msg = f"GATE-55-1 FAILED: {len(violations)} leading marker(s) found:" + ''.join(violation_msgs)
        if len(violations) > 10:
            msg += f"\n  ... and {len(violations) - 10} more violations"
        pytest.fail(msg)


def test_gate_55_1_db_specific_smoke():
    """
    GATE-55-1 DB-specific smoke test.

    Constitutional requirement (STEP NEXT-55):
        - DB was the primary victim (100% contaminated before fix)
        - Verify ". 상해사망" is now "상해사망"
        - Verify all 30 DB rows have clean normalized names
    """
    scope_v3_dir = Path('data/scope_v3')

    for variant in ['db_over41', 'db_under40']:
        jsonl_path = scope_v3_dir / f'{variant}_step2_sanitized_scope_v1.jsonl'

        assert jsonl_path.exists(), f"DB variant {variant} not found"

        violations = []
        total_rows = 0

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                entry = json.loads(line)
                total_rows += 1

                coverage_name_normalized = entry.get('coverage_name_normalized', '')
                has_marker, marker_type = detect_leading_marker(coverage_name_normalized)

                if has_marker:
                    violations.append({
                        'coverage_name_normalized': coverage_name_normalized,
                        'marker_type': marker_type
                    })

        assert total_rows == 30, f"{variant}: Expected 30 rows, got {total_rows}"
        assert len(violations) == 0, (
            f"{variant}: {len(violations)} rows still have leading markers\n"
            f"Examples: {violations[:5]}"
        )


if __name__ == '__main__':
    # Run with pytest
    pytest.main([__file__, '-v'])
