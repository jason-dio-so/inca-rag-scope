#!/usr/bin/env python3
"""
STEP NEXT-52-HK: SSOT Guardrail Test
=====================================

Enforce that NO Step2 outputs exist in legacy data/scope/ directory.

ALL Step2 outputs MUST be in data/scope_v3/ (SSOT).

This test prevents accidental writes to the wrong directory.
"""

import pytest
from pathlib import Path


def test_no_legacy_step2_outputs_in_data_scope():
    """
    GATE: Enforce data/scope_v3/ as SSOT for Step2 outputs.

    FAIL if ANY of these exist in data/scope/:
    - *_step2_sanitized_scope_v1.jsonl
    - *_step2_dropped.jsonl
    - *_step2_canonical_scope_v1.jsonl
    - *_step2_mapping_report.jsonl
    """
    project_root = Path(__file__).resolve().parents[1]
    legacy_dir = project_root / 'data' / 'scope'

    # Forbidden patterns (Step2 outputs)
    forbidden_patterns = [
        '*_step2_sanitized_scope_v1.jsonl',
        '*_step2_dropped.jsonl',
        '*_step2_canonical_scope_v1.jsonl',
        '*_step2_mapping_report.jsonl',
    ]

    violations = []
    for pattern in forbidden_patterns:
        matches = list(legacy_dir.glob(pattern))
        if matches:
            violations.extend(matches)

    # Assert NO violations
    assert not violations, (
        f"SSOT VIOLATION: Found {len(violations)} Step2 output(s) in legacy data/scope/.\n"
        f"All Step2 outputs MUST be in data/scope_v3/ (STEP NEXT-52-HK).\n"
        f"Violations:\n" + "\n".join(f"  - {v.name}" for v in violations[:10])
    )


def test_ssot_directory_exists():
    """
    Verify that data/scope_v3/ SSOT directory exists.
    """
    project_root = Path(__file__).resolve().parents[1]
    ssot_dir = project_root / 'data' / 'scope_v3'

    assert ssot_dir.exists(), (
        f"SSOT directory not found: {ssot_dir}\n"
        f"All Step2 outputs must be in data/scope_v3/"
    )


def test_step2_outputs_exist_in_ssot():
    """
    Smoke test: Verify at least ONE Step2 output exists in data/scope_v3/.

    This ensures the SSOT directory is being used.
    """
    project_root = Path(__file__).resolve().parents[1]
    ssot_dir = project_root / 'data' / 'scope_v3'

    # Check for any Step2 output
    patterns = [
        '*_step2_sanitized_scope_v1.jsonl',
        '*_step2_canonical_scope_v1.jsonl',
    ]

    found = []
    for pattern in patterns:
        matches = list(ssot_dir.glob(pattern))
        found.extend(matches)

    assert found, (
        f"No Step2 outputs found in {ssot_dir}.\n"
        f"Run Step2 pipeline to generate outputs in SSOT directory."
    )
