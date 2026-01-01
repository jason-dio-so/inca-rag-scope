"""
GATE-53-3: Entrypoint Documentation Gate

Constitutional Rule (STEP NEXT-53):
- CLAUDE.md must document the canonical entrypoint (Step1 → Step2-a → Step2-b)
- data/scope_v3/README.md must document the canonical entrypoint
- Documentation must specify:
  1. manifest SSOT usage
  2. scope_v3 SSOT enforcement
  3. Step execution order (Step1 → Step2-a → Step2-b)

This test enforces:
1. CLAUDE.md contains canonical entrypoint documentation
2. data/scope_v3/README.md contains canonical entrypoint documentation
3. Both docs reference manifest, scope_v3, and step order
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_claude_md_has_canonical_entrypoint():
    """GATE-53-3a: CLAUDE.md must document canonical entrypoint."""
    claude_md = PROJECT_ROOT / "CLAUDE.md"

    assert claude_md.exists(), "GATE-53-3a VIOLATION: CLAUDE.md does not exist"

    content = claude_md.read_text()

    # Check for key phrases
    required_phrases = [
        "step1_summary_first",
        "step2_sanitize_scope",
        "step2_canonical_mapping",
        "manifest",
        "scope_v3",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in content]

    assert len(missing) == 0, (
        f"GATE-53-3a VIOLATION: CLAUDE.md missing canonical entrypoint references:\n"
        + "\n".join(f"  - {phrase}" for phrase in missing)
        + "\n\nUpdate CLAUDE.md to include canonical pipeline documentation."
    )


def test_scope_v3_readme_has_canonical_entrypoint():
    """GATE-53-3b: data/scope_v3/README.md must document canonical entrypoint."""
    readme = PROJECT_ROOT / "data" / "scope_v3" / "README.md"

    assert readme.exists(), (
        "GATE-53-3b VIOLATION: data/scope_v3/README.md does not exist"
    )

    content = readme.read_text()

    # Check for key phrases
    required_phrases = [
        "step1_summary_first",
        "step2_sanitize_scope",
        "step2_canonical_mapping",
        "manifest",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in content]

    assert len(missing) == 0, (
        f"GATE-53-3b VIOLATION: data/scope_v3/README.md missing canonical entrypoint references:\n"
        + "\n".join(f"  - {phrase}" for phrase in missing)
        + "\n\nUpdate data/scope_v3/README.md to include canonical pipeline documentation."
    )


def test_docs_specify_step_order():
    """GATE-53-3c: Documentation must specify Step1 → Step2-a → Step2-b order."""
    docs_to_check = [
        PROJECT_ROOT / "CLAUDE.md",
        PROJECT_ROOT / "data" / "scope_v3" / "README.md",
    ]

    violations = []
    for doc in docs_to_check:
        if not doc.exists():
            continue

        content = doc.read_text()

        # Check for sequential mentions of Step1 → Step2
        has_step1 = "Step1" in content or "step1" in content
        has_step2a = "Step2-a" in content or "step2_sanitize" in content
        has_step2b = "Step2-b" in content or "step2_canonical" in content

        if not (has_step1 and has_step2a and has_step2b):
            violations.append((doc.name, has_step1, has_step2a, has_step2b))

    assert len(violations) == 0, (
        f"GATE-53-3c VIOLATION: Documentation missing step order references:\n"
        + "\n".join(
            f"  - {name}: Step1={s1}, Step2-a={s2a}, Step2-b={s2b}"
            for name, s1, s2a, s2b in violations
        )
        + "\n\nDocumentation must clearly specify Step1 → Step2-a → Step2-b order."
    )


def test_docs_specify_manifest_ssot():
    """GATE-53-3d: Documentation must reference manifest SSOT."""
    docs_to_check = [
        PROJECT_ROOT / "CLAUDE.md",
        PROJECT_ROOT / "data" / "scope_v3" / "README.md",
    ]

    violations = []
    for doc in docs_to_check:
        if not doc.exists():
            continue

        content = doc.read_text()

        # Check for manifest references
        has_manifest = "manifest" in content.lower() or "MANIFEST" in content

        if not has_manifest:
            violations.append(doc.name)

    assert len(violations) == 0, (
        f"GATE-53-3d VIOLATION: Documentation missing manifest SSOT references:\n"
        + "\n".join(f"  - {name}" for name in violations)
        + "\n\nDocumentation must specify manifest SSOT (data/manifests/proposal_pdfs_v1.json)."
    )


def test_docs_specify_scope_v3_ssot():
    """GATE-53-3e: Documentation must reference scope_v3 SSOT."""
    docs_to_check = [
        PROJECT_ROOT / "CLAUDE.md",
        PROJECT_ROOT / "data" / "scope_v3" / "README.md",
    ]

    violations = []
    for doc in docs_to_check:
        if not doc.exists():
            continue

        content = doc.read_text()

        # Check for scope_v3 references
        has_scope_v3 = "scope_v3" in content

        if not has_scope_v3:
            violations.append(doc.name)

    assert len(violations) == 0, (
        f"GATE-53-3e VIOLATION: Documentation missing scope_v3 SSOT references:\n"
        + "\n".join(f"  - {name}" for name in violations)
        + "\n\nDocumentation must specify scope_v3 SSOT (data/scope_v3/)."
    )
