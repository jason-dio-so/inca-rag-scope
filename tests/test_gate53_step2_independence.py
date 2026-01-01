"""
GATE-53-2: Step2 Independence Gate

Constitutional Rule (STEP NEXT-53):
- Step2-a and Step2-b must NOT import Step1 modules
- Step2 operates ONLY on JSONL inputs (no PDF, no LLM, no Step1 logic)
- Input contract: Step2-a takes *_step1_raw_scope_v3.jsonl ONLY
- Input contract: Step2-b takes *_step2_sanitized_scope_v1.jsonl ONLY

This test enforces:
1. No Step1 module imports in Step2 code
2. No PDF processing in Step2 code
3. No LLM calls in Step2 code
"""

import ast
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def get_imports_from_file(file_path: Path) -> list[str]:
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def test_step2_sanitize_no_step1_imports():
    """GATE-53-2a: pipeline/step2_sanitize_scope/ must NOT import Step1 modules."""
    step2_sanitize = PROJECT_ROOT / "pipeline" / "step2_sanitize_scope"

    if not step2_sanitize.exists():
        return  # If doesn't exist, PASS (archived or not yet created)

    violations = []
    for py_file in step2_sanitize.glob("*.py"):
        if py_file.name.startswith("test_"):
            continue

        imports = get_imports_from_file(py_file)
        step1_imports = [
            imp for imp in imports
            if "step1_extract_scope" in imp
            or "step1_sanitize_scope" in imp
            or "step1_summary_first" in imp
        ]

        if step1_imports:
            violations.append((py_file.name, step1_imports))

    assert len(violations) == 0, (
        f"GATE-53-2a VIOLATION: Found Step1 imports in Step2-a:\n"
        + "\n".join(
            f"  - {fname}: {', '.join(imports)}"
            for fname, imports in violations
        )
        + "\n\nStep2-a must operate ONLY on JSONL inputs, no Step1 logic."
    )


def test_step2_canonical_mapping_no_step1_imports():
    """GATE-53-2b: pipeline/step2_canonical_mapping/ must NOT import Step1 modules."""
    step2_mapping = PROJECT_ROOT / "pipeline" / "step2_canonical_mapping"

    if not step2_mapping.exists():
        return  # If doesn't exist, PASS

    violations = []
    for py_file in step2_mapping.glob("*.py"):
        if py_file.name.startswith("test_"):
            continue

        imports = get_imports_from_file(py_file)
        step1_imports = [
            imp for imp in imports
            if "step1_extract_scope" in imp
            or "step1_sanitize_scope" in imp
            or "step1_summary_first" in imp
        ]

        if step1_imports:
            violations.append((py_file.name, step1_imports))

    assert len(violations) == 0, (
        f"GATE-53-2b VIOLATION: Found Step1 imports in Step2-b:\n"
        + "\n".join(
            f"  - {fname}: {', '.join(imports)}"
            for fname, imports in violations
        )
        + "\n\nStep2-b must operate ONLY on JSONL inputs, no Step1 logic."
    )


def test_step2_no_pdf_processing():
    """GATE-53-2c: Step2 modules must NOT import PDF processing libraries."""
    forbidden_pdf_imports = [
        "pdfplumber",
        "PyPDF2",
        "pdfminer",
        "pypdf",
        "fitz",  # PyMuPDF
    ]

    step2_dirs = [
        PROJECT_ROOT / "pipeline" / "step2_sanitize_scope",
        PROJECT_ROOT / "pipeline" / "step2_canonical_mapping",
    ]

    violations = []
    for step2_dir in step2_dirs:
        if not step2_dir.exists():
            continue

        for py_file in step2_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue

            imports = get_imports_from_file(py_file)
            pdf_imports = [imp for imp in imports if any(pdf in imp for pdf in forbidden_pdf_imports)]

            if pdf_imports:
                violations.append((step2_dir.name, py_file.name, pdf_imports))

    assert len(violations) == 0, (
        f"GATE-53-2c VIOLATION: Found PDF processing imports in Step2:\n"
        + "\n".join(
            f"  - {dirname}/{fname}: {', '.join(imports)}"
            for dirname, fname, imports in violations
        )
        + "\n\nStep2 must operate ONLY on JSONL inputs (no PDF)."
    )


def test_step2_no_llm_calls():
    """GATE-53-2d: Step2 modules must NOT import LLM libraries."""
    forbidden_llm_imports = [
        "anthropic",
        "openai",
        "langchain",
        "llama_index",
    ]

    step2_dirs = [
        PROJECT_ROOT / "pipeline" / "step2_sanitize_scope",
        PROJECT_ROOT / "pipeline" / "step2_canonical_mapping",
    ]

    violations = []
    for step2_dir in step2_dirs:
        if not step2_dir.exists():
            continue

        for py_file in step2_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue

            imports = get_imports_from_file(py_file)
            llm_imports = [imp for imp in imports if any(llm in imp for llm in forbidden_llm_imports)]

            if llm_imports:
                violations.append((step2_dir.name, py_file.name, llm_imports))

    assert len(violations) == 0, (
        f"GATE-53-2d VIOLATION: Found LLM imports in Step2:\n"
        + "\n".join(
            f"  - {dirname}/{fname}: {', '.join(imports)}"
            for dirname, fname, imports in violations
        )
        + "\n\nStep2 must use deterministic logic only (no LLM)."
    )
