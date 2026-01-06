"""
SSOT vNext: Amount Extraction Logic

Deterministic amount status determination based on:
- proposal_facts.coverage_amount_text
- evidence patterns
- structural coverage characteristics
"""

import re
from typing import Optional, List
from core.compare_types import Amount


def determine_amount(
    coverage_name_raw: str,
    proposal_facts: Optional[dict],
    evidences: List[dict],
    insurer: str,
    coverage_code: Optional[str]
) -> Amount:
    """
    Determine amount status and value for a coverage.

    Args:
        coverage_name_raw: Raw coverage name
        proposal_facts: Step1 proposal facts (may contain coverage_amount_text)
        evidences: List of evidence dicts
        insurer: Insurer code
        coverage_code: Coverage code (if mapped)

    Returns:
        Amount object with status, value_text, evidence_refs

    Decision tree:
        1. CONFIRMED: coverage_amount_text exists OR amount found in evidence
        2. UNCONFIRMED: amount keywords exist but value unclear
        3. NOT_AVAILABLE: structurally no amount concept
    """

    # Extract coverage_amount_text from proposal_facts
    coverage_amount_text = None
    if proposal_facts and isinstance(proposal_facts, dict):
        coverage_amount_text = proposal_facts.get('coverage_amount_text')

    # Evidence refs for amount (PD:insurer:coverage_code format)
    evidence_refs = []
    if coverage_code:
        evidence_refs.append(f"PD:{insurer}:{coverage_code}")

    # Rule 1: CONFIRMED - coverage_amount_text exists
    if coverage_amount_text and coverage_amount_text.strip():
        # Clean value_text (remove numeric parentheticals)
        value_text = _clean_amount_text(coverage_amount_text)
        return Amount(
            status="CONFIRMED",
            value_text=value_text,
            evidence_refs=evidence_refs
        )

    # Rule 2: CONFIRMED - amount pattern in evidence
    amount_from_evidence = _extract_amount_from_evidences(evidences)
    if amount_from_evidence:
        return Amount(
            status="CONFIRMED",
            value_text=amount_from_evidence,
            evidence_refs=evidence_refs
        )

    # Rule 3: NOT_AVAILABLE - structurally no amount (deterministic patterns)
    if _is_not_available_coverage(coverage_name_raw):
        return Amount(
            status="NOT_AVAILABLE",
            value_text=None,
            evidence_refs=[]
        )

    # Rule 4: UNCONFIRMED - has amount keywords but unclear
    if _has_amount_keywords(coverage_name_raw, evidences):
        return Amount(
            status="UNCONFIRMED",
            value_text="명시 없음",
            evidence_refs=evidence_refs
        )

    # Default: NOT_AVAILABLE
    return Amount(
        status="NOT_AVAILABLE",
        value_text=None,
        evidence_refs=[]
    )


def _clean_amount_text(text: str) -> str:
    """
    Clean amount text by removing numeric parentheticals.

    Example:
        "3,000만원 (30,000,000원)" → "3,000만원"
    """
    # Remove parenthetical numeric amount (e.g., "(30,000,000원)")
    text = re.sub(r'\s*\([0-9,]+원\)', '', text)
    return text.strip()


def _extract_amount_from_evidences(evidences: List[dict]) -> Optional[str]:
    """
    Extract amount from evidence snippets using pattern matching.

    Returns:
        Extracted amount text (e.g., "3,000만원") or None
    """
    # Amount patterns (Korean format)
    amount_patterns = [
        r'(\d{1,3}(?:,\d{3})*만원)',  # e.g., "3,000만원"
        r'(\d+천만원)',  # e.g., "3천만원"
        r'(\d+억원)',  # e.g., "1억원"
    ]

    for ev in evidences:
        snippet = ev.get('snippet', '')
        for pattern in amount_patterns:
            match = re.search(pattern, snippet)
            if match:
                return match.group(1)

    return None


def _is_not_available_coverage(coverage_name_raw: str) -> bool:
    """
    Check if coverage structurally has no amount concept.

    Examples: 사망, 후유장해 (percentage-based), 면책 (waiver)
    """
    not_available_patterns = [
        r'사망$',  # Death benefit (often 100% of sum assured)
        r'후유장해',  # Disability (percentage-based)
        r'면책',  # Premium waiver
        r'보험료\s*납입\s*면제',  # Premium waiver
    ]

    for pattern in not_available_patterns:
        if re.search(pattern, coverage_name_raw):
            return True

    return False


def _has_amount_keywords(coverage_name_raw: str, evidences: List[dict]) -> bool:
    """
    Check if amount-related keywords exist (but value unclear).

    Returns:
        True if amount keywords found but value not extractable
    """
    amount_keywords = ['가입금액', '보장금액', '지급금액', '금액']

    # Check coverage name
    for keyword in amount_keywords:
        if keyword in coverage_name_raw:
            return True

    # Check evidence snippets
    for ev in evidences:
        snippet = ev.get('snippet', '')
        for keyword in amount_keywords:
            if keyword in snippet:
                return True

    return False
