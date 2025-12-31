#!/usr/bin/env python3
"""
SSOT Lock Guard Test (STEP NEXT-18X-SSOT-LOCK + STEP NEXT-31-P2)

Ensures that:
1. step10_audit has been moved to _deprecated/ (STEP NEXT-31-P2)
2. No executable code references reports/ paths
3. Only SSOT files exist for coverage/audit data

This test is the final technical safeguard for the SSOT contract.
"""

import re
import subprocess
from pathlib import Path

import pytest


def test_step10_audit_moved_to_deprecated():
    """
    Verify that step10_audit has been moved to _deprecated/ (STEP NEXT-31-P2).
    This prevents accidental reuse of deprecated audit workflow.
    """
    project_root = Path(__file__).resolve().parents[1]

    # step10_audit should NOT exist in pipeline/
    assert not (project_root / "pipeline" / "step10_audit").exists(), \
        "step10_audit should be moved to _deprecated/"

    # step10_audit SHOULD exist in _deprecated/pipeline/
    assert (project_root / "_deprecated" / "pipeline" / "step10_audit").exists(), \
        "step10_audit should exist in _deprecated/pipeline/"


def test_no_reports_path_in_executable_code():
    """
    Verify that no executable Python code references 'reports/' paths.

    Allowed:
    - .gitignore (for cleanup)
    - Historical docs (with ~~strikethrough~~)
    - Comments explaining removal

    Prohibited:
    - Active code paths that read/write reports/
    - Examples that suggest using reports/
    """
    project_root = Path(__file__).resolve().parents[1]

    # Search all Python files in pipeline/ and tools/
    code_dirs = [
        project_root / "pipeline",
        project_root / "tools",
    ]

    violations = []

    for code_dir in code_dirs:
        if not code_dir.exists():
            continue

        for py_file in code_dir.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for reports/ references
            # Allow: comments with "no reports/", "REMOVED", strikethrough
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'reports/' in line:
                    # Allow in comments that explicitly mark removal
                    if any(marker in line for marker in [
                        'NO reports/',
                        'no reports/',
                        '(REMOVED)',
                        '~~reports/',
                        '# reports/',  # Commented out
                        'DEPRECATED',
                        'moved to docs/audit/'
                    ]):
                        continue

                    # This is a violation
                    violations.append(f"{py_file.relative_to(project_root)}:{i}: {line.strip()}")

    assert len(violations) == 0, (
        f"Found {len(violations)} reports/ references in executable code:\n" +
        "\n".join(violations)
    )


def test_ssot_files_exist():
    """
    Verify that SSOT files exist for all expected insurers.

    Coverage SSOT: data/compare/*_coverage_cards.jsonl
    Audit SSOT: docs/audit/AMOUNT_STATUS_DASHBOARD.md
    """
    project_root = Path(__file__).resolve().parents[1]

    # Check audit SSOT
    audit_ssot = project_root / "docs/audit/AMOUNT_STATUS_DASHBOARD.md"
    assert audit_ssot.exists(), f"Audit SSOT not found: {audit_ssot}"

    # Check coverage SSOT for all insurers
    expected_insurers = [
        'samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk'
    ]

    missing = []
    for insurer in expected_insurers:
        cards_path = project_root / f"data/compare/{insurer}_coverage_cards.jsonl"
        if not cards_path.exists():
            missing.append(insurer)

    assert len(missing) == 0, (
        f"Missing coverage_cards.jsonl for insurers: {', '.join(missing)}"
    )


def test_no_reports_directory_in_output():
    """
    Verify that 'reports/' directory is not used for pipeline outputs.

    STEP NEXT-18X-SSOT-LOCK-2: Enhanced to detect behavior patterns, not just strings.

    Prohibited behaviors:
    - mkdir/makedirs for 'reports' directory
    - Path construction with 'reports'
    - open() targeting 'reports/' paths
    - Any file write operations to reports/

    Allowed:
    - .gitignore references (for cleanup)
    - Deprecated/removed markers in comments
    """
    project_root = Path(__file__).resolve().parents[1]

    # Check for mkdir reports/, Path("reports/"), etc. in code
    code_dirs = [
        project_root / "pipeline",
        project_root / "tools",
    ]

    violations = []

    for code_dir in code_dirs:
        if not code_dir.exists():
            continue

        for py_file in code_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Enhanced patterns to detect behavior
            # Check for directory creation patterns
            patterns = [
                # Directory creation
                (r'\.mkdir\s*\([^)]*\brepor', 'mkdir() with reports'),
                (r'makedirs\s*\([^)]*["\'].*report', 'makedirs() with reports'),
                (r'os\.mkdir.*["\'].*report', 'os.mkdir() with reports'),

                # Path construction
                (r'Path\s*\(\s*["\']reports[/\']', 'Path("reports/...") construction'),
                (r'Path\s*\([^)]*,\s*["\']reports["\']', 'Path(..., "reports", ...) construction'),
                (r'/\s*["\']reports["\']', '/ "reports" path joining'),

                # File operations
                (r'open\s*\(\s*["\']reports/', 'open("reports/...") write'),
                (r'open\s*\([^)]*["\']reports/', 'open() with reports/ path'),
                (r'\.write_text\s*\([^)]*reports', 'write_text() to reports'),
                (r'\.write\s*\([^)]*reports', 'write() to reports'),

                # String formatting that builds reports paths
                (r'f["\'][^"\']*reports/[^"\']*["\']', 'f-string with reports/'),
                (r'\.format\s*\([^)]*reports', 'format() with reports'),
                (r'%.*reports.*%', 'old-style format with reports'),
            ]

            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Skip _deprecated/ (already moved out of active pipeline)
                if '_deprecated' in str(py_file):
                    continue

                for pattern, description in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Allow if explicitly marked as deprecated/removed
                        if any(marker in line for marker in [
                            'DEPRECATED',
                            'REMOVED',
                            '~~',
                            'no reports/',
                            'NO reports/',
                            'Historical',
                        ]):
                            continue

                        violations.append(
                            f"{py_file.relative_to(project_root)}:{i}: {description} - {line.strip()}"
                        )
                        break  # Only report once per line

    assert len(violations) == 0, (
        f"Found {len(violations)} code paths creating/writing to reports/:\n" +
        "\n".join(violations[:10]) +  # Show first 10
        (f"\n... and {len(violations) - 10} more" if len(violations) > 10 else "")
    )


def test_gitignore_reports_present():
    """
    Verify that .gitignore contains reports/ for cleanup purposes.
    This is the ONLY allowed reference to reports/ in repo config.
    """
    project_root = Path(__file__).resolve().parents[1]
    gitignore = project_root / ".gitignore"

    assert gitignore.exists(), ".gitignore not found"

    with open(gitignore, 'r', encoding='utf-8') as f:
        content = f.read()

    # reports/ should be in .gitignore (for cleanup)
    assert 'reports/' in content, (
        ".gitignore should contain 'reports/' for cleanup"
    )
