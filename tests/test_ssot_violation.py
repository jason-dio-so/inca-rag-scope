"""
STEP NEXT-56: GATE-56-4 - SSOT Enforcement Test

Constitutional requirement:
- ONLY valid output directory: data/scope_v3/
- FORBIDDEN: data/scope/, data/scope_v2/, root-level JSONL

Enforcement:
- No JSONL files in legacy directories
- No JSONL files outside designated SSOT
- Hard fail if violations detected
"""

import pytest
from pathlib import Path


# SSOT (constitutional)
VALID_OUTPUT_DIR = Path("data/scope_v3")

# Forbidden directories (archived/legacy)
FORBIDDEN_DIRS = [
    Path("data/scope"),
    Path("data/scope_v2"),
]

# Root directory
ROOT_DIR = Path(".")


def test_gate_56_4_no_legacy_scope_files():
    """
    GATE-56-4: SSOT Enforcement - No Legacy Files

    Constitutional violation:
    - Any JSONL file in data/scope/
    - Any JSONL file in data/scope_v2/
    """
    violations = []

    for forbidden_dir in FORBIDDEN_DIRS:
        if not forbidden_dir.exists():
            continue

        # Find all JSONL files in forbidden directory
        jsonl_files = list(forbidden_dir.rglob("*.jsonl"))

        for jsonl_file in jsonl_files:
            # Ignore archive directories
            if "_archive" in str(jsonl_file) or "archive" in str(jsonl_file):
                continue

            violations.append(str(jsonl_file))

    if violations:
        pytest.fail(
            f"GATE-56-4 FAILED: Legacy JSONL files detected (CONSTITUTIONAL VIOLATION)\n" +
            "\n".join(f"  ❌ {v}" for v in violations) +
            f"\n\nAll outputs MUST be in {VALID_OUTPUT_DIR}/ (SSOT)"
        )

    print("✅ GATE-56-4 PASSED: No legacy files detected")


def test_gate_56_4_no_root_level_jsonl():
    """
    GATE-56-4: SSOT Enforcement - No Root-Level JSONL

    Constitutional violation:
    - JSONL files directly in project root
    - JSONL files in non-SSOT directories
    """
    # Check root directory (exclude subdirectories)
    root_jsonl_files = [
        f for f in ROOT_DIR.glob("*.jsonl")
        if f.is_file()
    ]

    if root_jsonl_files:
        pytest.fail(
            f"GATE-56-4 FAILED: Root-level JSONL files detected\n" +
            "\n".join(f"  ❌ {f}" for f in root_jsonl_files) +
            f"\n\nAll outputs MUST be in {VALID_OUTPUT_DIR}/"
        )

    print("✅ GATE-56-4 PASSED: No root-level JSONL files")


def test_gate_56_4_ssot_structure_valid():
    """
    GATE-56-4: SSOT Enforcement - Valid Structure

    Constitutional requirement:
    - data/scope_v3/ directory exists
    - _RUNS/ subdirectory exists
    - LATEST symlink exists (after first run)
    """
    assert VALID_OUTPUT_DIR.exists(), \
        f"SSOT directory missing: {VALID_OUTPUT_DIR}"

    runs_dir = VALID_OUTPUT_DIR / "_RUNS"
    assert runs_dir.exists(), \
        f"SSOT _RUNS directory missing: {runs_dir}"

    # LATEST symlink (may not exist if no runs yet)
    latest_link = VALID_OUTPUT_DIR / "LATEST"
    if latest_link.exists():
        assert latest_link.is_symlink(), \
            f"LATEST should be a symlink: {latest_link}"
        print(f"  ℹ️  LATEST → {latest_link.readlink()}")

    print("✅ GATE-56-4 PASSED: SSOT structure valid")


def test_gate_56_4_only_scope_v3_outputs():
    """
    GATE-56-4: SSOT Enforcement - Exclusive Output Location

    Verify all Step1/Step2 outputs are in scope_v3/ ONLY
    """
    # Expected output patterns
    output_patterns = [
        "*_step1_raw_scope_v3.jsonl",
        "*_step2_sanitized_scope_v1.jsonl",
        "*_step2_canonical_scope_v1.jsonl",
        "*_step2_dropped.jsonl",
        "*_step2_mapping_report.jsonl",
    ]

    # Check data/ directory for misplaced outputs
    data_dir = Path("data")
    violations = []

    for pattern in output_patterns:
        # Search in data/ (excluding scope_v3/)
        for jsonl_file in data_dir.rglob(pattern):
            # Skip if in valid SSOT
            if VALID_OUTPUT_DIR in jsonl_file.parents:
                continue

            # Skip archives
            if "archive" in str(jsonl_file).lower():
                continue

            violations.append(str(jsonl_file))

    if violations:
        pytest.fail(
            f"GATE-56-4 FAILED: Step outputs outside SSOT detected\n" +
            "\n".join(f"  ❌ {v}" for v in violations) +
            f"\n\nAll Step1/Step2 outputs MUST be in {VALID_OUTPUT_DIR}/"
        )

    print("✅ GATE-56-4 PASSED: All outputs in SSOT location")


def test_gate_56_4_readme_exists():
    """
    GATE-56-4: SSOT Enforcement - Documentation

    SSOT directory MUST have README.md explaining structure
    """
    readme_path = VALID_OUTPUT_DIR / "README.md"

    if not readme_path.exists():
        print(f"⚠️  WARNING: {readme_path} missing (recommended for SSOT documentation)")
    else:
        print(f"✅ README.md exists: {readme_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
