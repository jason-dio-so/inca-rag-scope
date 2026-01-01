"""
STEP NEXT-57B: Pipeline Entrypoint Singleton Test
==================================================

Constitutional Rule: Single Execution Path
- ONLY canonical entrypoint allowed: tools/run_pipeline_v3.sh
- NO legacy entrypoints (rebuild_insurer.sh, etc.)
- NO legacy path writes (data/scope/)

Gates:
- GATE-57B-1: Multiple Entrypoint Confusion
- GATE-57B-2: SSOT Violation
"""

import pytest
from pathlib import Path


def test_rebuild_insurer_archived():
    """
    GATE-57B-1: rebuild_insurer.sh must be archived (SSOT violation)

    Constitutional Rule: Single entrypoint only
    - rebuild_insurer.sh uses data/scope/ (violates SSOT)
    - rebuild_insurer.sh calls legacy map_to_canonical.py (deprecated)

    Expected: tools/rebuild_insurer.sh does NOT exist
    """
    legacy_path = Path("tools/rebuild_insurer.sh")

    assert not legacy_path.exists(), \
        f"rebuild_insurer.sh must be archived (found at {legacy_path})\n" \
        f"SSOT violation: writes to data/scope/ instead of data/scope_v3/\n" \
        f"Migration: Use tools/run_pipeline_v3.sh instead"


def test_no_legacy_scope_writes_in_tools():
    """
    GATE-57B-2: No active tools write to data/scope/ (legacy path)

    SSOT Rule: ALL outputs → data/scope_v3/

    Violation: Any shell script in tools/ containing "data/scope/" writes

    Exceptions:
    - Lines starting with # (comments)
    - Lines containing "data/scope_v3/" (SSOT path)
    - Lines in GATE checks (validation only, not writes)
    """
    tools_dir = Path("tools")
    violations = []

    for script in tools_dir.glob("*.sh"):
        # Skip archived scripts
        if script.name.startswith("_archived"):
            continue

        content = script.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue

            # Skip SSOT paths (data/scope_v3 is OK)
            if 'data/scope_v3' in line:
                continue

            # Skip GATE validation lines (read-only checks)
            if 'GATE' in line or 'find data/scope' in line:
                continue

            # Detect legacy path usage
            if 'data/scope/' in line and 'data/scope_v3' not in line:
                violations.append(f"{script.name}:{i} → {line.strip()}")

    assert not violations, \
        f"Found {len(violations)} legacy data/scope/ reference(s) in tools:\n" + \
        "\n".join(f"  - {v}" for v in violations) + \
        "\n\nSSOT Rule: Use data/scope_v3/ only"


def test_canonical_entrypoint_exists():
    """
    GATE-57B-1: Canonical entrypoint must exist

    Expected: tools/run_pipeline_v3.sh exists
    """
    canonical_path = Path("tools/run_pipeline_v3.sh")

    assert canonical_path.exists(), \
        "Canonical entrypoint missing: tools/run_pipeline_v3.sh"

    assert canonical_path.is_file(), \
        "tools/run_pipeline_v3.sh is not a file"


def test_canonical_entrypoint_uses_ssot():
    """
    GATE-57B-2: Canonical entrypoint must use SSOT paths only

    Expected: run_pipeline_v3.sh uses data/scope_v3/ only
    """
    canonical_path = Path("tools/run_pipeline_v3.sh")
    content = canonical_path.read_text()

    # Must contain SSOT path
    assert 'data/scope_v3' in content, \
        "run_pipeline_v3.sh must use data/scope_v3/ (SSOT)"

    # Must NOT write to legacy path
    lines = content.split('\n')
    legacy_writes = []

    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        # Skip GATE validation (read-only)
        if 'GATE' in line or 'find data/scope' in line:
            continue

        # Detect writes to legacy path
        if 'data/scope/' in line and 'data/scope_v3' not in line:
            # Check if it's a write operation
            if any(op in line for op in ['>', 'rm ', 'mv ', 'cp ', 'mkdir']):
                legacy_writes.append(f"Line {i}: {line.strip()}")

    assert not legacy_writes, \
        f"run_pipeline_v3.sh contains legacy path writes:\n" + \
        "\n".join(f"  - {w}" for w in legacy_writes)


def test_step2_modules_use_ssot():
    """
    GATE-57B-2: Step2 modules must use SSOT paths only

    Expected: Step2 runners (run.py) use data/scope_v3/ only
    """
    step2_modules = [
        Path("pipeline/step2_sanitize_scope/run.py"),
        Path("pipeline/step2_canonical_mapping/run.py"),
    ]

    violations = []

    for module in step2_modules:
        if not module.exists():
            continue

        content = module.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                continue

            # Detect legacy path usage (NOT in scope_v3)
            if "'data/scope/" in line or '"data/scope/' in line:
                if 'scope_v3' not in line:
                    violations.append(f"{module.name}:{i} → {line.strip()}")

    assert not violations, \
        f"Found {len(violations)} legacy path reference(s) in Step2:\n" + \
        "\n".join(f"  - {v}" for v in violations) + \
        "\n\nSSOT Rule: Use data/scope_v3/ only"


def test_no_variant_merged_files():
    """
    GATE-57B-3: DB/LOTTE must NOT have single merged files

    Forbidden:
    - data/scope_v3/db_step2_*.jsonl (must be db_under40_*, db_over41_*)
    - data/scope_v3/lotte_step2_*.jsonl (must be lotte_male_*, lotte_female_*)
    """
    scope_v3 = Path("data/scope_v3")

    if not scope_v3.exists():
        pytest.skip("data/scope_v3/ does not exist yet")

    forbidden_patterns = [
        "db_step2_*.jsonl",
        "lotte_step2_*.jsonl",
    ]

    violations = []

    for pattern in forbidden_patterns:
        matches = list(scope_v3.glob(pattern))
        if matches:
            violations.extend(matches)

    assert not violations, \
        f"Found {len(violations)} forbidden single-variant file(s):\n" + \
        "\n".join(f"  - {v.name}" for v in violations) + \
        "\n\nVariant Rule: DB/LOTTE must produce under40/over41 or male/female pairs"


def test_variant_pairs_exist():
    """
    GATE-57B-3: DB/LOTTE variant pairs must exist

    Required:
    - DB: db_under40_step2_*.jsonl + db_over41_step2_*.jsonl
    - LOTTE: lotte_male_step2_*.jsonl + lotte_female_step2_*.jsonl
    """
    scope_v3 = Path("data/scope_v3")

    if not scope_v3.exists():
        pytest.skip("data/scope_v3/ does not exist yet")

    # Check if ANY Step2 files exist
    step2_files = list(scope_v3.glob("*_step2_*.jsonl"))
    if not step2_files:
        pytest.skip("No Step2 outputs exist yet")

    required_pairs = {
        "DB": ["db_under40_step2_canonical_scope_v1.jsonl", "db_over41_step2_canonical_scope_v1.jsonl"],
        "LOTTE": ["lotte_male_step2_canonical_scope_v1.jsonl", "lotte_female_step2_canonical_scope_v1.jsonl"],
    }

    missing = []

    for insurer, files in required_pairs.items():
        for filename in files:
            filepath = scope_v3 / filename
            if not filepath.exists():
                missing.append(f"{insurer}: {filename}")

    assert not missing, \
        f"Missing {len(missing)} variant pair file(s):\n" + \
        "\n".join(f"  - {m}" for m in missing) + \
        "\n\nVariant Rule: DB/LOTTE must maintain variant axis through Step2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
