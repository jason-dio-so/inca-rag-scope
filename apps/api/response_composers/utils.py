#!/usr/bin/env python3
"""
Response Composer Utilities

STEP NEXT-81B: Coverage Code Exposure Prevention
STEP NEXT-88: View Layer Expression Rules
STEP NEXT-93: Coverage Name Display Normalization
"""

import re
from typing import Optional, List


# ============================================================================
# STEP NEXT-93: Coverage Name Display Normalization
# ============================================================================

def normalize_coverage_name_for_display(name: str) -> str:
    """
    Normalize coverage name for consistent UI display (STEP NEXT-93)

    RULES:
    - Remove all internal spaces between Korean characters ("암 진단비" → "암진단비")
    - Remove/normalize separators: [-_/·•] → ""
    - Keep only: 가-힣, 0-9, (), %, ·
    - Reject coverage_code patterns (A4200_1, etc.)
    - Return empty string if normalization fails

    Args:
        name: Coverage name with potential spacing/separator issues

    Returns:
        Normalized coverage name (or "" if invalid/rejected)

    Examples:
        >>> normalize_coverage_name_for_display("암 진단비")
        "암진단비"
        >>> normalize_coverage_name_for_display("  암   진단비  ")
        "암진단비"
        >>> normalize_coverage_name_for_display("뇌 출혈-진단비")
        "뇌출혈진단비"
        >>> normalize_coverage_name_for_display("A4200_1")
        ""  # Rejected (coverage_code pattern)
        >>> normalize_coverage_name_for_display("암진단비(유사암 제외)")
        "암진단비(유사암제외)"
    """
    if not name:
        return ""

    # Step 1: Trim whitespace
    name = name.strip()

    # Step 2: Reject coverage_code patterns immediately
    if re.match(r"^[A-Z]\d{4}_\d+$", name):
        return ""

    # Step 3: Remove/normalize separators (keep spaces for now)
    # Replace separators with spaces, then we'll remove spaces between Korean
    name = re.sub(r"[-_/·•]", " ", name)

    # Step 4: Keep only allowed characters: 가-힣, 0-9, (), %, ·, spaces
    # Remove everything else
    name = re.sub(r"[^가-힣0-9()%·\s]", "", name)

    # Step 5: Remove spaces between Korean characters
    # Pattern: Korean + space(s) + Korean → Korean + Korean
    while re.search(r"([가-힣])\s+([가-힣])", name):
        name = re.sub(r"([가-힣])\s+([가-힣])", r"\1\2", name)

    # Step 6: Collapse multiple spaces to single space
    name = re.sub(r"\s+", " ", name)

    # Step 7: Final trim
    name = name.strip()

    # Step 8: Reject if too short or empty
    if len(name) <= 1:
        return ""

    return name


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

    STEP NEXT-93: ALWAYS normalize coverage_name for consistent display
    - "암 진단비" → "암진단비"
    - "뇌 출혈-진단비" → "뇌출혈진단비"
    - Reject coverage_code patterns

    Args:
        coverage_name: Coverage name (e.g., "암진단비(유사암 제외)")
        coverage_code: Coverage code (e.g., "A4200_1") - NEVER displayed

    Returns:
        Display-safe, normalized coverage name (NO coverage_code exposure)

    Examples:
        >>> display_coverage_name(coverage_name="암진단비", coverage_code="A4200_1")
        "암진단비"
        >>> display_coverage_name(coverage_name="암 진단비", coverage_code="A4200_1")
        "암진단비"  # Normalized
        >>> display_coverage_name(coverage_name=None, coverage_code="A4200_1")
        "해당 담보"
        >>> display_coverage_name(coverage_name="A4200_1", coverage_code="A4200_1")
        "해당 담보"  # Reject coverage_code-like string
    """
    # If coverage_name is missing, use fallback
    if not coverage_name:
        return "해당 담보"

    # STEP NEXT-93: Normalize coverage_name for consistent display
    normalized = normalize_coverage_name_for_display(coverage_name)

    # If normalization failed (empty string) or resulted in invalid name, use fallback
    if not normalized:
        return "해당 담보"

    # Otherwise, use normalized coverage_name
    return normalized


def sanitize_no_coverage_code(text: str) -> str:
    r"""
    Sanitize text to remove coverage code patterns (STEP NEXT-86)

    CONSTITUTIONAL RULE:
    - ❌ NEVER allow bare coverage_code (A\d{4}_\d) in user-facing text
    - ✅ Keep coverage_code in refs (PD:insurer:CODE, EV:insurer:CODE:idx)
    - ✅ Replace bare codes with "해당 담보"

    Args:
        text: Text to sanitize (may contain coverage codes)

    Returns:
        Sanitized text (NO bare coverage codes, refs preserved)

    Examples:
        >>> sanitize_no_coverage_code("A4200_1 비교")
        "해당 담보 비교"
        >>> sanitize_no_coverage_code("PD:samsung:A4200_1")
        "PD:samsung:A4200_1"  # Ref preserved
        >>> sanitize_no_coverage_code("삼성의 A4200_1 (PD:samsung:A4200_1)")
        "삼성의 해당 담보 (PD:samsung:A4200_1)"  # Bare code replaced, ref preserved
    """
    # STEP NEXT-86: Preserve refs while removing bare coverage codes
    # Strategy:
    # 1. Find all coverage codes
    # 2. Check if they are in refs (PD:xxx:CODE or EV:xxx:CODE:idx)
    # 3. Replace only bare codes (not in refs)

    # Pattern: Coverage code (A4200_1, B1100_2, etc.)
    code_pattern = r"[A-Z]\d{4}_\d+"

    def replace_bare_code(match):
        """Replace bare code, but preserve refs"""
        code = match.group(0)
        start_pos = match.start()

        # Check if this code is part of a ref
        # Look back to see if there's "PD:xxx:" or "EV:xxx:" before this code
        prefix_pd = text[max(0, start_pos-15):start_pos]  # Look back up to 15 chars
        prefix_ev = text[max(0, start_pos-25):start_pos]  # Look back up to 25 chars for EV

        # If preceded by PD:insurer: or EV:insurer:, it's a ref - keep it
        if re.search(r"PD:[a-z]+:$", prefix_pd) or re.search(r"EV:[a-z]+:$", prefix_ev):
            return code  # Preserve ref

        # Otherwise, it's a bare code - replace it
        return "해당 담보"

    sanitized = re.sub(code_pattern, replace_bare_code, text)
    return sanitized


# ============================================================================
# STEP NEXT-88: View Layer Expression Rules
# ============================================================================

# Insurer display name mapping
INSURER_DISPLAY_NAMES = {
    "samsung": "삼성화재",
    "meritz": "메리츠화재",
    "db": "DB손해보험",
    "kb": "KB손해보험",
    "hanwha": "한화손해보험",
    "hyundai": "현대해상",
    "lotte": "롯데손해보험",
    "heungkuk": "흥국화재"
}


def format_insurer_name(insurer_code: str) -> str:
    """
    Format insurer code to display name

    Args:
        insurer_code: Insurer code (e.g., "samsung", "meritz")

    Returns:
        Display name (e.g., "삼성화재", "메리츠화재")
    """
    return INSURER_DISPLAY_NAMES.get(insurer_code, insurer_code)


def _get_korean_particle_wa_gwa(text: str) -> str:
    """
    Get correct Korean particle (와/과) based on final character

    Rules:
    - 와: after vowel (받침 없음)
    - 과: after consonant (받침 있음)

    Args:
        text: Korean text to check

    Returns:
        "와" or "과"
    """
    if not text:
        return "와"

    # Get last character
    last_char = text[-1]

    # Check if it's a Korean character
    if ord('가') <= ord(last_char) <= ord('힣'):
        # Calculate 받침 (final consonant)
        # Korean Unicode: 0xAC00 (가) + (initial * 588) + (medial * 28) + (final)
        # final = 0 means no 받침
        final = (ord(last_char) - ord('가')) % 28
        return "과" if final > 0 else "와"

    # Default: 와
    return "와"


def format_insurer_list(insurers: List[str]) -> str:
    """
    Format list of insurers to display string

    Args:
        insurers: List of insurer codes (e.g., ["samsung", "meritz"])

    Returns:
        Formatted string (e.g., "삼성화재와 메리츠화재")

    Examples:
        >>> format_insurer_list(["samsung"])
        "삼성화재"
        >>> format_insurer_list(["samsung", "meritz"])
        "삼성화재와 메리츠화재"
        >>> format_insurer_list(["hanwha", "lotte"])
        "한화손해보험과 롯데손해보험"  # 과 (받침 있음)
        >>> format_insurer_list(["samsung", "meritz", "kb"])
        "삼성화재, 메리츠화재, KB손해보험"
    """
    if not insurers:
        return "선택한 보험사"

    display_names = [format_insurer_name(code) for code in insurers]

    if len(display_names) == 1:
        return display_names[0]
    elif len(display_names) == 2:
        # Use correct Korean particle (와/과)
        particle = _get_korean_particle_wa_gwa(display_names[0])
        return f"{display_names[0]}{particle} {display_names[1]}"
    else:
        # 3+ insurers: "A, B, C"
        return ", ".join(display_names)


def get_insurer_subject(insurers: List[str]) -> str:
    """
    Get grammatically correct subject for insurer list (STEP NEXT-88)

    Rules:
    - 1 insurer: "선택한 보험사의"
    - 2+ insurers: "선택한 보험사들의"

    Args:
        insurers: List of insurer codes

    Returns:
        Subject with possessive particle (e.g., "선택한 보험사의" or "선택한 보험사들의")

    Examples:
        >>> get_insurer_subject(["samsung"])
        "선택한 보험사의"
        >>> get_insurer_subject(["samsung", "meritz"])
        "선택한 보험사들의"
    """
    if len(insurers) == 1:
        return "선택한 보험사의"
    else:
        return "선택한 보험사들의"


# ============================================================================
# STEP NEXT-94: Coverage Grouping UX
# ============================================================================

def assign_coverage_group(
    coverage_name: str,
    coverage_trigger: Optional[str] = None
) -> str:
    """
    Assign coverage group label for UX grouping (STEP NEXT-94)

    CONSTITUTIONAL RULES:
    - ❌ NO business logic change (view-only)
    - ❌ NO LLM usage (deterministic keyword matching only)
    - ❌ NO judgment/scoring/weighting
    - ✅ View layer only (display label for UI sections)
    - ✅ Max 3 groups: 진단, 치료/수술, 기타

    GROUPING RULES (deterministic keyword matching):
    1. "진단 관련 담보" (Group 1):
       - coverage_trigger == "DIAGNOSIS"
       - OR coverage_name contains: "진단비", "진단급여금"
    2. "치료/수술 관련 담보" (Group 2):
       - coverage_trigger in ["SURGERY", "TREATMENT"]
       - OR coverage_name contains: "수술비", "치료비", "입원", "통원", "항암", "방사선"
    3. "기타 담보" (Group 3):
       - Fallback for all other coverages

    Args:
        coverage_name: Normalized coverage name (e.g., "암진단비", "유사암수술비")
        coverage_trigger: Optional trigger type (DIAGNOSIS/SURGERY/TREATMENT/MIXED)

    Returns:
        Group label ("진단 관련 담보", "치료/수술 관련 담보", "기타 담보")

    Examples:
        >>> assign_coverage_group("암진단비", "DIAGNOSIS")
        "진단 관련 담보"
        >>> assign_coverage_group("유사암수술비", "SURGERY")
        "치료/수술 관련 담보"
        >>> assign_coverage_group("제자리암진단비", None)
        "진단 관련 담보"  # Inferred from name
        >>> assign_coverage_group("뇌출혈진단비", "MIXED")
        "진단 관련 담보"  # Inferred from name
        >>> assign_coverage_group("상해사망급여금", None)
        "기타 담보"
    """
    # Normalize coverage_name for keyword matching
    name_lower = coverage_name.lower() if coverage_name else ""

    # PRIORITY: Name-based keywords take precedence over trigger
    # (Name is more explicit than inferred trigger)

    # Group 1: 진단 관련 담보 (check name first)
    if any(keyword in name_lower for keyword in ["진단비", "진단급여"]):
        return "진단 관련 담보"

    # Group 2: 치료/수술 관련 담보 (check name first)
    if any(keyword in name_lower for keyword in [
        "수술비", "치료비", "입원", "통원", "항암", "방사선"
    ]):
        return "치료/수술 관련 담보"

    # If name doesn't match, use trigger as fallback
    if coverage_trigger == "DIAGNOSIS":
        return "진단 관련 담보"
    if coverage_trigger in ["SURGERY", "TREATMENT"]:
        return "치료/수술 관련 담보"

    # Group 3: 기타 담보 (fallback)
    return "기타 담보"
