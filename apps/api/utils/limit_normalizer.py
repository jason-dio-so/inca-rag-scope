#!/usr/bin/env python3
"""
STEP NEXT-137: Coverage Limit Normalization Schema

PURPOSE:
Normalize coverage limit/amount data into structured schema for consistent comparison.

CONSTITUTIONAL RULES:
- ❌ NO insurer-specific hardcoding (must work for ALL insurers)
- ❌ NO string-based status decision (use normalized fields only)
- ❌ NO LLM usage (deterministic regex/parsing only)
- ✅ Generic schema applicable to all insurers/coverages
- ✅ Status decision based on normalized fields (scope, max_days, max_count, value)
"""

import re
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from enum import Enum


class LimitScope(str, Enum):
    """Limit scope classification"""
    PER_HOSPITALIZATION = "PER_HOSPITALIZATION"  # 1회 입원당
    PER_POLICY_TERM = "PER_POLICY_TERM"  # 보험기간 중
    PER_YEAR = "PER_YEAR"  # 연간
    PER_CLAIM = "PER_CLAIM"  # 1회당 (일반)
    UNKNOWN = "UNKNOWN"


class AmountUnit(str, Enum):
    """Amount payment unit"""
    PER_DAY = "PER_DAY"  # 일당
    LUMP_SUM = "LUMP_SUM"  # 정액 (일시금)
    PER_CLAIM = "PER_CLAIM"  # 1회당
    UNKNOWN = "UNKNOWN"


@dataclass
class LimitNormalized:
    """Normalized limit information"""
    scope: LimitScope
    max_days: Optional[int] = None  # e.g., 180 days
    max_count: Optional[int] = None  # e.g., 1 time
    period: Optional[str] = None  # e.g., "보험기간 중", "연간"
    raw_text: str = ""
    evidence_refs: List[str] = None

    def __post_init__(self):
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class AmountNormalized:
    """Normalized amount information"""
    unit: AmountUnit
    value: Optional[int] = None  # in KRW (smallest unit: 원)
    currency: str = "KRW"
    raw_text: str = ""
    evidence_refs: List[str] = None

    def __post_init__(self):
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class CoverageLimitNormalized:
    """Combined limit + amount normalized structure"""
    limit: Optional[LimitNormalized] = None
    amount: Optional[AmountNormalized] = None


def normalize_limit_text(limit_summary: Optional[str]) -> LimitNormalized:
    """
    Normalize limit_summary text into structured LimitNormalized.

    Args:
        limit_summary: Text like "1회 입원당 180일 한도", "보험기간 중 1회"

    Returns:
        LimitNormalized with extracted scope, max_days, max_count

    Rules:
        - Deterministic regex pattern matching only
        - NO insurer-specific logic
        - If pattern not recognized → scope=UNKNOWN, preserve raw_text
    """
    if not limit_summary:
        return LimitNormalized(scope=LimitScope.UNKNOWN, raw_text="")

    raw_text = limit_summary.strip()

    # Pattern 1: "N회 입원당 M일 한도" → PER_HOSPITALIZATION + max_days
    pattern_hosp_days = r"(\d+)\s*회\s*입원(?:당)?\s*(\d+)\s*일"
    match = re.search(pattern_hosp_days, raw_text)
    if match:
        count = int(match.group(1))
        days = int(match.group(2))
        return LimitNormalized(
            scope=LimitScope.PER_HOSPITALIZATION,
            max_count=count if count > 1 else None,  # 1회면 생략
            max_days=days,
            raw_text=raw_text
        )

    # Pattern 2: "보험기간 중 N회" → PER_POLICY_TERM + max_count
    pattern_policy_term = r"보험기간\s*중\s*(\d+)\s*회"
    match = re.search(pattern_policy_term, raw_text)
    if match:
        count = int(match.group(1))
        return LimitNormalized(
            scope=LimitScope.PER_POLICY_TERM,
            max_count=count,
            period="보험기간 중",
            raw_text=raw_text
        )

    # Pattern 3: "연간 N회" → PER_YEAR + max_count
    pattern_year = r"연간\s*(\d+)\s*회"
    match = re.search(pattern_year, raw_text)
    if match:
        count = int(match.group(1))
        return LimitNormalized(
            scope=LimitScope.PER_YEAR,
            max_count=count,
            period="연간",
            raw_text=raw_text
        )

    # Pattern 4: Just "N일 한도" → UNKNOWN scope + max_days
    pattern_days_only = r"(\d+)\s*일\s*한도"
    match = re.search(pattern_days_only, raw_text)
    if match:
        days = int(match.group(1))
        return LimitNormalized(
            scope=LimitScope.UNKNOWN,
            max_days=days,
            raw_text=raw_text
        )

    # No pattern matched → UNKNOWN
    return LimitNormalized(
        scope=LimitScope.UNKNOWN,
        raw_text=raw_text
    )


def normalize_amount_text(
    amount_text: Optional[str],
    payment_type: Optional[str] = None
) -> AmountNormalized:
    """
    Normalize amount text into structured AmountNormalized.

    Args:
        amount_text: Text like "2만원", "3천만원"
        payment_type: Optional hint from kpi_summary.payment_type (e.g., "PER_DAY")

    Returns:
        AmountNormalized with value (in 원) and unit

    Rules:
        - Parse Korean number format: "만원", "천만원", "억원"
        - Unit determined by payment_type or coverage context
        - If parsing fails → unit=UNKNOWN, preserve raw_text
    """
    if not amount_text:
        return AmountNormalized(unit=AmountUnit.UNKNOWN, raw_text="")

    raw_text = amount_text.strip()

    # Parse Korean currency format
    value_krw = _parse_korean_currency(raw_text)

    # Determine unit from payment_type hint
    unit = AmountUnit.UNKNOWN
    if payment_type:
        if payment_type == "PER_DAY" or "일당" in payment_type:
            unit = AmountUnit.PER_DAY
        elif payment_type in ["LUMP_SUM", "정액형"]:
            unit = AmountUnit.LUMP_SUM
        elif "per_claim" in payment_type.lower():
            unit = AmountUnit.PER_CLAIM

    # Fallback: check raw_text for unit hints
    if unit == AmountUnit.UNKNOWN:
        if "일당" in raw_text:
            unit = AmountUnit.PER_DAY
        elif "정액" in raw_text or "일시금" in raw_text:
            unit = AmountUnit.LUMP_SUM

    return AmountNormalized(
        unit=unit,
        value=value_krw,
        currency="KRW",
        raw_text=raw_text
    )


def _parse_korean_currency(text: str) -> Optional[int]:
    """
    Parse Korean currency format to integer (in 원).

    Examples:
        "2만원" → 20000
        "3천만원" → 30000000
        "1억원" → 100000000

    Returns:
        Integer value in 원, or None if parsing fails
    """
    # Remove whitespace
    text = text.replace(" ", "").replace(",", "")

    # Pattern: N억 M천만원, N천만원, N만원
    pattern_eok = r"(\d+)\s*억"
    pattern_chunman = r"(\d+)\s*천만"
    pattern_man = r"(\d+)\s*만"

    value = 0

    # 억 (100,000,000)
    match = re.search(pattern_eok, text)
    if match:
        value += int(match.group(1)) * 100_000_000

    # 천만 (10,000,000)
    match = re.search(pattern_chunman, text)
    if match:
        value += int(match.group(1)) * 10_000_000

    # 만 (10,000)
    match = re.search(pattern_man, text)
    if match:
        value += int(match.group(1)) * 10_000

    if value == 0:
        # Try direct number (e.g., "20000원")
        pattern_direct = r"(\d+)\s*원?"
        match = re.search(pattern_direct, text)
        if match:
            value = int(match.group(1))

    return value if value > 0 else None


def compare_limits(
    limit1: Optional[LimitNormalized],
    limit2: Optional[LimitNormalized]
) -> Literal["SAME", "DIFF", "PARTIAL", "UNKNOWN"]:
    """
    Compare two LimitNormalized structures.

    Args:
        limit1, limit2: Normalized limits to compare

    Returns:
        "SAME": Both limits have same scope + max_days/max_count
        "DIFF": Limits differ in scope or values
        "PARTIAL": One or both limits have UNKNOWN scope (incomplete data)
        "UNKNOWN": Both limits are None or missing

    Rules:
        - Compare scope first (must match)
        - Then compare max_days (if applicable)
        - Then compare max_count (if applicable)
        - NO raw_text string comparison
    """
    if limit1 is None and limit2 is None:
        return "UNKNOWN"

    if limit1 is None or limit2 is None:
        return "PARTIAL"

    # If either scope is UNKNOWN → PARTIAL
    if limit1.scope == LimitScope.UNKNOWN or limit2.scope == LimitScope.UNKNOWN:
        return "PARTIAL"

    # Scope must match
    if limit1.scope != limit2.scope:
        return "DIFF"

    # Compare max_days
    if limit1.max_days != limit2.max_days:
        return "DIFF"

    # Compare max_count
    if limit1.max_count != limit2.max_count:
        return "DIFF"

    return "SAME"


def compare_amounts(
    amount1: Optional[AmountNormalized],
    amount2: Optional[AmountNormalized]
) -> Literal["SAME", "DIFF", "PARTIAL", "UNKNOWN"]:
    """
    Compare two AmountNormalized structures.

    Args:
        amount1, amount2: Normalized amounts to compare

    Returns:
        "SAME": Both amounts have same value
        "DIFF": Amounts differ in value
        "PARTIAL": One or both amounts missing
        "UNKNOWN": Both amounts are None

    Rules:
        - Compare value (in KRW)
        - Unit difference is OK if values match (unit is secondary)
        - NO raw_text string comparison
    """
    if amount1 is None and amount2 is None:
        return "UNKNOWN"

    if amount1 is None or amount2 is None:
        return "PARTIAL"

    # If either value is None → PARTIAL
    if amount1.value is None or amount2.value is None:
        return "PARTIAL"

    # Compare values
    if amount1.value != amount2.value:
        return "DIFF"

    return "SAME"


def decide_overall_status(
    limit_comparison: str,
    amount_comparison: str
) -> Literal["ALL_SAME", "DIFF", "PARTIAL", "UNKNOWN"]:
    """
    Decide overall status based on limit + amount comparisons.

    Args:
        limit_comparison: Result from compare_limits()
        amount_comparison: Result from compare_amounts()

    Returns:
        "ALL_SAME": Both limit and amount are SAME
        "DIFF": At least one is DIFF
        "PARTIAL": At least one is PARTIAL (but none DIFF)
        "UNKNOWN": Both are UNKNOWN

    Rules:
        - DIFF takes priority (any difference → DIFF)
        - Then PARTIAL (incomplete data)
        - Then ALL_SAME (both SAME)
        - Fallback → UNKNOWN
    """
    if limit_comparison == "DIFF" or amount_comparison == "DIFF":
        return "DIFF"

    if limit_comparison == "PARTIAL" or amount_comparison == "PARTIAL":
        return "PARTIAL"

    if limit_comparison == "SAME" and amount_comparison == "SAME":
        return "ALL_SAME"

    return "UNKNOWN"
