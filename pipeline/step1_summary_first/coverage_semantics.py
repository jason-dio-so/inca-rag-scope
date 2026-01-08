"""
STEP NEXT-66-A: Coverage Semantics Extractor

Constitutional rules:
- ❌ LLM inference prohibited (rule-based only)
- ❌ Semantic deletion prohibited (conditions/limits/frequency/renewal)
- ✅ Coverage name = "display name" only, semantics are structured
- ✅ Same input → Same output (reproducibility required)
- ✅ No inference without evidence

Purpose:
Extract semantic components from coverage name to preserve metadata
that is critical for evidence pipeline downstream.

Example:
Input:  "다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
Output: {
    "coverage_title": "다빈치로봇 암수술비",
    "exclusions": ["갑상선암", "전립선암"],
    "payout_limit_type": "per_policy",
    "payout_limit_count": 1,
    "renewal_type": null,
    "renewal_flag": true
}
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class CoverageSemantics:
    """Structured semantic components extracted from coverage name"""
    coverage_title: str                     # Core coverage name (without metadata)
    exclusions: List[str]                   # Exclusion conditions
    payout_limit_type: Optional[str]        # annual, per_policy, per_accident, etc.
    payout_limit_count: Optional[int]       # Number of payouts allowed
    renewal_type: Optional[str]             # Renewal period (e.g., "10년", "1년")
    renewal_flag: bool                      # True if (갱신형) present
    coverage_modifiers: List[str]           # Other modifiers (감액없음, 요양병원제외, etc.)
    fragment_detected: bool                 # True if input looks like fragment
    parent_coverage_hint: Optional[str]     # Hint for fragment parent coverage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (for JSON serialization)"""
        return asdict(self)


class CoverageSemanticExtractor:
    """
    Rule-based extractor for coverage semantics

    STEP NEXT-66-A: Extract metadata from coverage names
    STEP NEXT-66-B: Detect fragments
    """

    # Patterns for semantic extraction
    EXCLUSION_PATTERN = re.compile(r'\((.*?제외)\)')
    PAYOUT_LIMIT_PATTERN = re.compile(r'\((최초|연간|매)(\d+)회한\)')
    RENEWAL_PATTERN = re.compile(r'\(갱신형(?:_(\d+)년)?\)')
    MODIFIER_PATTERN = re.compile(r'\((감액없음|요양병원제외|요양제외|기타피부암\s*및\s*갑상선암\s*포함)\)')

    # Fragment detection patterns
    FRAGMENT_PATTERNS = [
        re.compile(r'^최초\d*회$'),                          # 최초1회
        re.compile(r'^연간\d*회$'),                          # 연간1회
        re.compile(r'^매\d*회$'),                            # 매1회
        re.compile(r'\($'),                                  # Unclosed parenthesis at end
        re.compile(r'^\($'),                                 # Starts with unclosed paren
    ]

    def extract(self, coverage_name_raw: str) -> CoverageSemantics:
        """
        Extract semantic components from coverage name

        Args:
            coverage_name_raw: Raw coverage name from PDF

        Returns:
            CoverageSemantics object with extracted components
        """
        # STEP NEXT-66-B: Fragment detection
        fragment_detected, parent_hint = self._detect_fragment(coverage_name_raw)

        if fragment_detected:
            return CoverageSemantics(
                coverage_title=coverage_name_raw,  # Keep as-is for fragment
                exclusions=[],
                payout_limit_type=None,
                payout_limit_count=None,
                renewal_type=None,
                renewal_flag=False,
                coverage_modifiers=[],
                fragment_detected=True,
                parent_coverage_hint=parent_hint
            )

        # Extract semantic components
        exclusions = self._extract_exclusions(coverage_name_raw)
        payout_limit_type, payout_limit_count = self._extract_payout_limits(coverage_name_raw)
        renewal_type, renewal_flag = self._extract_renewal_info(coverage_name_raw)
        modifiers = self._extract_modifiers(coverage_name_raw)

        # Build coverage title (strip all parenthetical metadata)
        coverage_title = self._build_coverage_title(coverage_name_raw)

        return CoverageSemantics(
            coverage_title=coverage_title,
            exclusions=exclusions,
            payout_limit_type=payout_limit_type,
            payout_limit_count=payout_limit_count,
            renewal_type=renewal_type,
            renewal_flag=renewal_flag,
            coverage_modifiers=modifiers,
            fragment_detected=False,
            parent_coverage_hint=None
        )

    def _detect_fragment(self, text: str) -> tuple[bool, Optional[str]]:
        """
        STEP NEXT-66-B: Detect if input is a parsing fragment

        Returns:
            (is_fragment, parent_hint)
        """
        text_stripped = text.strip()

        # Check fragment patterns
        for pattern in self.FRAGMENT_PATTERNS:
            if pattern.search(text_stripped):
                # Provide parent hint if possible
                if '로봇' in text_stripped or '다빈치' in text_stripped:
                    return True, "다빈치로봇 수술"
                elif '표적항암' in text_stripped:
                    return True, "표적항암약물허가치료비"
                else:
                    return True, None

        return False, None

    def _extract_exclusions(self, text: str) -> List[str]:
        """
        Extract exclusion clauses

        Example: "(갑상선암 및 전립선암 제외)" → ["갑상선암", "전립선암"]
        """
        exclusions = []

        for match in self.EXCLUSION_PATTERN.finditer(text):
            exclusion_text = match.group(1)  # e.g., "갑상선암 및 전립선암 제외"

            # Remove "제외" suffix
            exclusion_text = exclusion_text.replace('제외', '').strip()

            # Split by common delimiters
            for delimiter in [' 및 ', ',', '·', '/', ' 또는 ']:
                if delimiter in exclusion_text:
                    parts = exclusion_text.split(delimiter)
                    exclusions.extend([p.strip() for p in parts if p.strip()])
                    break
            else:
                # No delimiter found, single exclusion
                if exclusion_text:
                    exclusions.append(exclusion_text.strip())

        return exclusions

    def _extract_payout_limits(self, text: str) -> tuple[Optional[str], Optional[int]]:
        """
        Extract payout limit information

        Examples:
        - "(최초1회한)" → ("per_policy", 1)
        - "(연간1회한)" → ("annual", 1)
        - "(매1회한)"   → ("per_accident", 1)
        """
        match = self.PAYOUT_LIMIT_PATTERN.search(text)
        if not match:
            return None, None

        limit_type_kr = match.group(1)  # 최초, 연간, 매
        limit_count_str = match.group(2)
        limit_count = int(limit_count_str)

        # Map Korean to canonical type
        type_map = {
            "최초": "per_policy",
            "연간": "annual",
            "매": "per_accident"
        }

        limit_type = type_map.get(limit_type_kr)

        return limit_type, limit_count

    def _extract_renewal_info(self, text: str) -> tuple[Optional[str], bool]:
        """
        Extract renewal information

        Examples:
        - "(갱신형)"        → (None, True)
        - "(갱신형_10년)"   → ("10년", True)
        """
        match = self.RENEWAL_PATTERN.search(text)
        if not match:
            return None, False

        renewal_period = match.group(1)  # e.g., "10" or None
        renewal_type = f"{renewal_period}년" if renewal_period else None

        return renewal_type, True

    def _extract_modifiers(self, text: str) -> List[str]:
        """
        Extract other modifiers

        Examples:
        - "(감액없음)"
        - "(요양병원제외)"
        - "(기타피부암 및 갑상선암 포함)"
        """
        modifiers = []

        for match in self.MODIFIER_PATTERN.finditer(text):
            modifier = match.group(1).strip()
            if modifier:
                modifiers.append(modifier)

        return modifiers

    def _build_coverage_title(self, text: str) -> str:
        """
        Build coverage title by removing all parenthetical metadata

        Example:
        "206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
        → "다빈치로봇 암수술비"

        STEP NEXT-66-FIX: Remove leading numbering
        """
        # Remove all parenthetical expressions
        title = re.sub(r'\([^)]*\)', '', text)

        # STEP NEXT-66-FIX: Remove leading numbering (e.g., "206.", "1)", "3. ")
        title = re.sub(r'^\s*\d+[.)]?\s*', '', title)

        # Normalize whitespace
        title = ' '.join(title.split())

        return title.strip()


def extract_coverage_semantics(coverage_name_raw: str) -> Dict[str, Any]:
    """
    Convenience function to extract coverage semantics

    Args:
        coverage_name_raw: Raw coverage name from PDF

    Returns:
        Dict with semantic components
    """
    extractor = CoverageSemanticExtractor()
    semantics = extractor.extract(coverage_name_raw)
    return semantics.to_dict()


# STEP NEXT-66-C: Evidence requirements mapping
EVIDENCE_REQUIREMENTS_MAP = {
    # Payout limits require evidence
    "payout_limit": ["최초", "연간", "매"],

    # Exclusions require evidence
    "exclusion_clause": ["제외"],

    # Renewal requires evidence
    "renewal_condition": ["갱신형"],

    # Modifiers require evidence
    "reduction_clause": ["감액"],
    "facility_restriction": ["요양병원제외", "요양제외"],
}


def get_evidence_requirements(coverage_name_raw: str) -> List[str]:
    """
    STEP NEXT-66-C: Determine what evidence is needed for this coverage

    Args:
        coverage_name_raw: Raw coverage name

    Returns:
        List of evidence requirement types
    """
    requirements = []

    for req_type, keywords in EVIDENCE_REQUIREMENTS_MAP.items():
        if any(kw in coverage_name_raw for kw in keywords):
            requirements.append(req_type)

    return requirements
