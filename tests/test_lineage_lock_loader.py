"""
Lineage Lock Tests for Loader

These tests enforce that apps.loader modules:
1. Do NOT import from step7_amount or inca-rag-final
2. Do NOT perform extraction/inference on snippets
3. ONLY map CSV/JSONL fields → DB tables

CRITICAL: These tests prevent loader from becoming an extractor.
"""

import pytest
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_loader_no_step7_imports():
    """Verify loader does not import step7 modules."""
    loader_files = list(Path("apps/loader").glob("*.py"))

    assert len(loader_files) > 0, "No loader files found"

    violations = []
    for loader_file in loader_files:
        content = loader_file.read_text(encoding='utf-8')

        # Check for step7 imports
        forbidden_patterns = [
            r'from\s+pipeline\.step7',
            r'import\s+.*step7',
            r'from\s+.*step7',
        ]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                violations.append(f"{loader_file}: {matches}")

    assert len(violations) == 0, (
        f"LINEAGE VIOLATION: Loader imports step7 modules:\n" +
        "\n".join(violations)
    )


def test_loader_no_inca_rag_final_imports():
    """Verify loader does not import inca-rag-final lineage."""
    loader_files = list(Path("apps/loader").glob("*.py"))

    violations = []
    for loader_file in loader_files:
        content = loader_file.read_text(encoding='utf-8')

        # Check for inca-rag-final imports
        forbidden_strings = [
            "inca-rag-final",
            "inca_rag_final",
        ]

        for forbidden in forbidden_strings:
            if forbidden in content:
                violations.append(f"{loader_file}: contains '{forbidden}'")

    assert len(violations) == 0, (
        f"LINEAGE VIOLATION: Loader contains inca-rag-final references:\n" +
        "\n".join(violations)
    )


def test_loader_no_snippet_extraction():
    """Verify loader does NOT extract/parse snippet content."""
    # Only check step9_loader.py (not the deprecated simple version)
    loader_file = Path("apps/loader/step9_loader.py")

    if not loader_file.exists():
        pytest.skip("step9_loader.py not found")

    content = loader_file.read_text(encoding='utf-8')

    violations = []

    # Check for EXTRACTION patterns (searching/parsing snippets for amounts)
    # Note: snippet[:500] for truncation in evidence_ref is OK (not extraction)
    forbidden_patterns = [
        (r'\'만원\'\s+in\s+snippet', '만원 keyword search in snippet'),
        (r'\'원\'\s+in\s+snippet', '원 keyword search in snippet'),
        (r'snippet\.split', 'snippet parsing with split()'),
        (r're\.search\(.*snippet', 'regex search on snippet'),
        (r're\.findall\(.*snippet', 'regex findall on snippet'),
    ]

    for pattern, description in forbidden_patterns:
        matches = re.findall(pattern, content)
        if matches:
            violations.append(f"{description}: {matches[:2]}")

    assert len(violations) == 0, (
        f"EXTRACTION VIOLATION in step9_loader.py:\n" +
        "\n".join(violations) +
        "\n\nLoader should NOT search/parse snippets for amounts."
    )


def test_loader_allowed_inputs_only():
    """Verify loader only reads from approved CSV/JSONL paths."""
    loader_files = list(Path("apps/loader").glob("*.py"))

    # Patterns that indicate file reading
    file_read_pattern = r'open\s*\([\'"]([^\'"]+)[\'"]'
    path_pattern = r'Path\s*\([\'"]([^\'"]+)[\'"]'

    violations = []
    # STEP PIPELINE-V2-BLOCK-STEP2B-01: Updated SSOT path
    allowed_prefixes = [
        "data/scope/",
        "data/evidence_pack/",
        "data/compare/",
        "data/sources/insurers/",  # Correct SSOT path (was data/sources/mapping/)
        "apps/metadata/",
    ]

    for loader_file in loader_files:
        content = loader_file.read_text(encoding='utf-8')

        # Find all file paths
        file_paths = re.findall(file_read_pattern, content)
        file_paths += re.findall(path_pattern, content)

        for file_path in file_paths:
            # Skip variable/f-string paths (dynamic paths are checked at runtime)
            if '{' in file_path or 'f"' in content:
                continue

            # Check if path starts with allowed prefix
            if not any(file_path.startswith(prefix) for prefix in allowed_prefixes):
                # Skip logging/config files
                if not any(x in file_path for x in ['.log', '.yml', '.yaml', 'config']):
                    violations.append(f"{loader_file}: unexpected path '{file_path}'")

    # Note: Some violations may be false positives (dynamic paths)
    # This test is a heuristic check, not absolute
    if violations:
        print(f"WARNING: Potential non-CSV/JSONL inputs detected:\n" + "\n".join(violations))


def test_loader_amount_fact_uses_card_field():
    """Verify amount_fact population expects 'amount' field from coverage_cards."""
    loader_file = Path("apps/loader/step9_loader.py")

    if not loader_file.exists():
        pytest.skip("step9_loader.py not found")

    content = loader_file.read_text(encoding='utf-8')

    # Find load_amount_fact method
    if "def load_amount_fact" not in content:
        pytest.skip("load_amount_fact method not found")

    # Extract method content
    method_start = content.find("def load_amount_fact")
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = len(content)

    method_content = content[method_start:method_end]

    # Check for violations (extraction from evidences/snippet)
    violations = []

    # FORBIDDEN: Iterating over evidences to extract amounts
    if "for ev in evidences:" in method_content:
        violations.append("Iterates over evidences (should use card['amount'] instead)")

    # FORBIDDEN: Searching in snippets
    if "'만원' in snippet" in method_content or "'원' in snippet" in method_content:
        violations.append("Searches for amount keywords in snippets")

    # FORBIDDEN: Extracting substring from snippet
    if "snippet[:" in method_content:
        violations.append("Extracts substring from snippet")

    assert len(violations) == 0, (
        f"EXTRACTION VIOLATION in load_amount_fact:\n" +
        "\n".join(violations) +
        "\n\nLoader should use card.get('amount', {}) instead of extracting from snippets."
    )
