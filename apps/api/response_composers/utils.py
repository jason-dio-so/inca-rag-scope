#!/usr/bin/env python3
"""
Response Composer Utilities

STEP NEXT-81B: Coverage Code Exposure Prevention
"""

import re
from typing import Optional


def display_coverage_name(
    *,
    coverage_name: Optional[str] = None,
    coverage_code: str
) -> str:
    """
    Get display-safe coverage name (NEVER expose coverage_code to user)

    CONSTITUTIONAL RULE (STEP NEXT-81B):
    - ❌ NEVER return coverage_code (e.g., "A4200_1") to user-facing text
    - ✅ Use coverage_name if available and safe
    - ✅ Fallback to "해당 담보" if coverage_name is missing or unsafe

    Args:
        coverage_name: Coverage name (e.g., "암진단비(유사암 제외)")
        coverage_code: Coverage code (e.g., "A4200_1") - NEVER displayed

    Returns:
        Display-safe coverage name (NO coverage_code exposure)

    Examples:
        >>> display_coverage_name(coverage_name="암진단비", coverage_code="A4200_1")
        "암진단비"
        >>> display_coverage_name(coverage_name=None, coverage_code="A4200_1")
        "해당 담보"
        >>> display_coverage_name(coverage_name="A4200_1", coverage_code="A4200_1")
        "해당 담보"  # Reject coverage_code-like string
    """
    # If coverage_name is missing, use fallback
    if not coverage_name:
        return "해당 담보"

    # If coverage_name looks like a coverage_code (e.g., "A4200_1"), reject it
    if re.match(r"^[A-Z]\d{4}_\d+$", coverage_name):
        return "해당 담보"

    # Otherwise, use coverage_name
    return coverage_name


def sanitize_no_coverage_code(text: str) -> str:
    r"""
    Sanitize text to remove all coverage code patterns (STEP NEXT-81B)

    CONSTITUTIONAL RULE:
    - ❌ NEVER allow coverage_code (A\d{4}_\d) to appear in user-facing text
    - ✅ Replace with "해당 담보" or remove token

    Args:
        text: Text to sanitize (may contain coverage codes)

    Returns:
        Sanitized text (NO coverage codes)

    Examples:
        >>> sanitize_no_coverage_code("A4200_1 비교")
        "해당 담보 비교"
        >>> sanitize_no_coverage_code("삼성화재와 메리츠화재의 A4200_1를 비교")
        "삼성화재와 메리츠화재의 해당 담보를 비교"
    """
    # Pattern: A4200_1, B1100_2, etc.
    # Note: Use lookahead/lookbehind to handle Korean characters properly
    pattern = r"[A-Z]\d{4}_\d+"

    # Replace with fallback
    sanitized = re.sub(pattern, "해당 담보", text)

    return sanitized
