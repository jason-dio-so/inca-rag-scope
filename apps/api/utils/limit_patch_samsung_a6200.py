#!/usr/bin/env python3
"""
STEP NEXT-136-γ: Samsung A6200 Limit Summary Patch

PURPOSE:
Extract "180일 한도" from Samsung A6200 proposal detail text when kpi_summary.limit_summary is missing.

CONSTITUTIONAL RULES:
- ❌ NO LLM usage (deterministic regex only)
- ❌ NO coverage_code fallback (A4200_1 contamination forbidden)
- ❌ NO application to other insurers/coverages (guard required)
- ✅ Samsung + A6200 + EX2_LIMIT_FIND + compare_field=보장한도 ONLY
- ✅ Deterministic regex pattern matching
"""

import re
from typing import Optional


def patch_limit_summary_samsung_A6200(benefit_text: Optional[str]) -> Optional[str]:
    """
    Extract "180일 한도" from Samsung A6200 benefit description text.

    Args:
        benefit_text: benefit_description_text from proposal_detail_store

    Returns:
        "1회 입원당 180일 한도" if pattern matches, else None

    Rules:
        - Only applies when benefit_text contains "180일" + "한도" + "입원일당" patterns
        - Returns standardized format for consistency
        - NO LLM, NO inference, NO guessing
    """
    if not benefit_text:
        return None

    # STEP NEXT-136-γ: Regex patterns for 180-day limit extraction
    # Pattern 1: "180일을 한도로 ... 입원 1일당"
    pattern1 = r"(?:180\s*일)\s*(?:을\s*한도로|한도).*?(?:입원\s*1\s*일당|1\s*일당)"
    # Pattern 2: "입원 1일당 ... 180일을 한도로"
    pattern2 = r"(?:입원\s*1\s*일당).*?(?:180\s*일)\s*(?:을\s*한도로|한도)"
    # Pattern 3: "1회 입원당 180일 한도"
    pattern3 = r"1\s*회\s*입원(?:당)?\s*(?:180\s*일)\s*(?:을\s*한도로|한도)"

    for pattern in [pattern1, pattern2, pattern3]:
        if re.search(pattern, benefit_text, re.IGNORECASE):
            # Standardized output format
            return "1회 입원당 180일 한도"

    # No match found
    return None


# STEP NEXT-136-γ: Constitutional guard function
def should_apply_samsung_a6200_patch(
    insurer: str,
    coverage_code: str,
    compare_field: str,
    kind: str
) -> bool:
    """
    Guard function: Only apply patch when ALL conditions match.

    Args:
        insurer: Insurer code (e.g., "samsung")
        coverage_code: Coverage code (e.g., "A6200")
        compare_field: Field being compared (e.g., "보장한도")
        kind: Message kind (e.g., "EX2_LIMIT_FIND")

    Returns:
        True if ALL conditions match, else False

    Constitutional Rule:
        This patch MUST NOT affect:
        - Other insurers (meritz, kb, etc.)
        - Other coverages (A4200_1, A5200, etc.)
        - Other compare_fields (보장금액, 지급유형, etc.)
        - Other message kinds (EX2_DETAIL, EX3_COMPARE, etc.)
    """
    return (
        insurer == "samsung" and
        coverage_code == "A6200" and
        compare_field == "보장한도" and
        kind in ["EX2_LIMIT_FIND", "EX2_DETAIL_DIFF"]  # Both use same diff logic
    )
