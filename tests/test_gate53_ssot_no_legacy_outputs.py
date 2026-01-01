"""
GATE-53-1: SSOT Violation Gate

Constitutional Rule (STEP NEXT-53):
- data/scope_v3/ is the ONLY authorized output directory for Step1+ outputs
- data/scope/ and data/scope_v2/ are ARCHIVED (should not exist or be empty)
- ANY Step2 outputs in data/scope/ → FAIL

This test enforces:
1. data/scope/ does not contain Step2 outputs (*.jsonl with 'step2' in name)
2. data/scope_v2/ does not exist or contains no Step2 outputs
3. All Step2 outputs reside in data/scope_v3/
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_no_step2_outputs_in_legacy_data_scope():
    """GATE-53-1a: data/scope/ must NOT contain any Step2 outputs."""
    legacy_scope = PROJECT_ROOT / "data" / "scope"

    # If data/scope doesn't exist, PASS (fully archived)
    if not legacy_scope.exists():
        return

    # If exists, check for Step2 outputs
    step2_files = list(legacy_scope.glob("*step2*.jsonl"))

    assert len(step2_files) == 0, (
        f"GATE-53-1a VIOLATION: Found {len(step2_files)} Step2 outputs in legacy data/scope/:\n"
        + "\n".join(f"  - {f.name}" for f in step2_files)
        + "\n\nThese files should be archived. Run STEP NEXT-53 cleanup."
    )


def test_no_step2_outputs_in_legacy_data_scope_v2():
    """GATE-53-1b: data/scope_v2/ must NOT contain any Step2 outputs."""
    legacy_scope_v2 = PROJECT_ROOT / "data" / "scope_v2"

    # If data/scope_v2 doesn't exist, PASS (fully archived)
    if not legacy_scope_v2.exists():
        return

    # If exists, check for Step2 outputs
    step2_files = list(legacy_scope_v2.glob("*step2*.jsonl"))

    assert len(step2_files) == 0, (
        f"GATE-53-1b VIOLATION: Found {len(step2_files)} Step2 outputs in legacy data/scope_v2/:\n"
        + "\n".join(f"  - {f.name}" for f in step2_files)
        + "\n\nThese files should be archived. Run STEP NEXT-53 cleanup."
    )


def test_scope_v3_is_ssot_for_step2():
    """GATE-53-1c: All Step2 outputs MUST reside in data/scope_v3/."""
    scope_v3 = PROJECT_ROOT / "data" / "scope_v3"

    # scope_v3 must exist
    assert scope_v3.exists(), "GATE-53-1c VIOLATION: data/scope_v3/ does not exist (SSOT missing)"

    # Must contain at least some Step2 outputs
    step2_sanitized = list(scope_v3.glob("*_step2_sanitized_scope_v1.jsonl"))
    step2_canonical = list(scope_v3.glob("*_step2_canonical_scope_v1.jsonl"))

    assert len(step2_sanitized) > 0 or len(step2_canonical) > 0, (
        "GATE-53-1c VIOLATION: data/scope_v3/ contains NO Step2 outputs. "
        "SSOT is empty or corrupted."
    )


def test_legacy_directories_archived():
    """GATE-53-1d: Legacy directories should be archived or contain warning README."""
    legacy_scope = PROJECT_ROOT / "data" / "scope"

    # If data/scope exists, it should contain ONLY a README warning
    if legacy_scope.exists():
        readme = legacy_scope / "README.md"
        assert readme.exists(), (
            "GATE-53-1d VIOLATION: data/scope/ exists but has no README.md warning. "
            "Run STEP NEXT-53 cleanup to add warning."
        )

        # Check README contains "ARCHIVED" keyword
        content = readme.read_text()
        assert "ARCHIVED" in content or "DO NOT USE" in content, (
            "GATE-53-1d VIOLATION: data/scope/README.md does not contain ARCHIVED warning."
        )
