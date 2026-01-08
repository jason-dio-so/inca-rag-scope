"""
Comparison Model Schema - STEP NEXT-68

Dataclass definitions for coverage comparison tables.
Evidence-first, deterministic only.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import re


@dataclass
class EvidenceReference:
    """Single evidence reference from Step3 output"""
    doc_type: str  # 가입설계서, 약관, etc.
    page: int
    excerpt: str
    locator: Dict[str, Any]  # keyword, line_num, is_table
    gate_status: Optional[str] = None  # FOUND | FOUND_GLOBAL
    confidence: Optional[float] = None  # Reserved for future use

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SlotValue:
    """
    Evidence-based slot value.

    CONSTRAINT: value must be derived from evidences (no inference).
    """
    status: str  # FOUND | FOUND_GLOBAL | CONFLICT | UNKNOWN
    value: Optional[str] = None  # Normalized value if deterministic
    evidences: List[EvidenceReference] = field(default_factory=list)
    notes: Optional[str] = None  # Gate failure reason, conflict summary

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "value": self.value,
            "evidences": [ev.to_dict() for ev in self.evidences],
            "notes": self.notes
        }


@dataclass
class CoverageIdentity:
    """Coverage identity for comparison key"""
    insurer_key: str
    product_key: str
    variant_key: str
    coverage_code: Optional[str] = None  # e.g., "206"
    coverage_title: str = ""  # Normalized title (no modifiers)
    coverage_name_raw: Optional[str] = None  # Original full name

    def get_comparison_key(self) -> str:
        """
        Generate comparison key for cross-insurer matching.

        Priority: coverage_code > coverage_title
        """
        if self.coverage_code:
            return f"code:{self.coverage_code}"
        return f"title:{self.coverage_title}"

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CoverageSemantics:
    """Optional semantics from Step1 (preserved)"""
    exclusions: List[str] = field(default_factory=list)
    payout_limit_count: Optional[int] = None
    payout_limit_type: Optional[str] = None  # per_policy, per_diagnosis, etc.
    renewal_flag: bool = False
    renewal_type: Optional[str] = None
    coverage_modifiers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        result = {}
        if self.exclusions:
            result["exclusions"] = self.exclusions
        if self.payout_limit_count is not None:
            result["payout_limit_count"] = self.payout_limit_count
        if self.payout_limit_type:
            result["payout_limit_type"] = self.payout_limit_type
        if self.renewal_flag:
            result["renewal_flag"] = self.renewal_flag
            if self.renewal_type:
                result["renewal_type"] = self.renewal_type
        if self.coverage_modifiers:
            result["coverage_modifiers"] = self.coverage_modifiers
        return result


@dataclass
class CompareRow:
    """
    Single coverage comparison row.

    One row per (insurer, product, variant, coverage).
    """
    identity: CoverageIdentity
    semantics: Optional[CoverageSemantics] = None

    # Required comparison slots (customer-facing)
    start_date: Optional[SlotValue] = None
    exclusions: Optional[SlotValue] = None
    payout_limit: Optional[SlotValue] = None
    reduction: Optional[SlotValue] = None
    entry_age: Optional[SlotValue] = None
    waiting_period: Optional[SlotValue] = None

    # Optional renewal condition (from semantics)
    renewal_condition: Optional[str] = None

    # Metadata
    slot_status_summary: Dict[str, int] = field(default_factory=dict)
    has_conflict: bool = False
    unanchored: bool = False  # True if no coverage_code

    def to_dict(self) -> Dict:
        result = {
            "identity": self.identity.to_dict(),
        }

        if self.semantics:
            result["semantics"] = self.semantics.to_dict()

        # Slots
        slots = {}
        for slot_name in ["start_date", "exclusions", "payout_limit",
                          "reduction", "entry_age", "waiting_period"]:
            slot = getattr(self, slot_name)
            if slot:
                slots[slot_name] = slot.to_dict()
        result["slots"] = slots

        # Renewal condition
        if self.renewal_condition:
            result["renewal_condition"] = self.renewal_condition

        # Meta
        result["meta"] = {
            "slot_status_summary": self.slot_status_summary,
            "has_conflict": self.has_conflict,
            "unanchored": self.unanchored
        }

        return result


@dataclass
class CompareTable:
    """
    Multi-insurer comparison table.

    Groups coverage rows by comparison_key for cross-insurer comparison.
    """
    table_id: str
    insurers: List[str]
    product_keys: List[str]
    variant_keys: List[str]

    # Coverage rows grouped by comparison_key
    coverage_rows: List[CompareRow] = field(default_factory=list)

    # Warnings and metadata
    table_warnings: List[str] = field(default_factory=list)
    total_rows: int = 0
    conflict_count: int = 0
    unknown_rate: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "table_id": self.table_id,
            "insurers": self.insurers,
            "product_keys": self.product_keys,
            "variant_keys": self.variant_keys,
            "coverage_rows": [row.to_dict() for row in self.coverage_rows],
            "table_warnings": self.table_warnings,
            "meta": {
                "total_rows": self.total_rows,
                "conflict_count": self.conflict_count,
                "unknown_rate": self.unknown_rate
            }
        }


# Utility functions

def extract_coverage_code(coverage_name_raw: str) -> Optional[str]:
    """
    Extract coverage code from coverage_name_raw.

    Examples:
    - "206. 다빈치로봇 암수술비(...)" -> "206"
    - "1. 일반상해사망(기본)" -> "1"
    - "280  표적항암약물허가치료비(...)" -> "280"  (space separator)
    - "일반상해사망" -> None
    """
    # Match: number + (period OR 2+ spaces) at start
    match = re.match(r'^(\d+)(?:\.|[\s]{2,})', coverage_name_raw)
    return match.group(1) if match else None


def extract_coverage_title(coverage_name_raw: str) -> str:
    """
    Extract clean coverage title (no code, no modifiers).

    Examples:
    - "206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
      -> "다빈치로봇 암수술비"
    - "1. 일반상해사망(기본)" -> "일반상해사망"
    - "280  표적항암약물허가치료비(...)" -> "표적항암약물허가치료비"
    """
    # Remove leading code (number + period OR 2+ spaces)
    title = re.sub(r'^\d+(?:\.|[\s]{2,})\s*', '', coverage_name_raw)

    # Remove parenthetical modifiers
    title = re.split(r'\(', title)[0].strip()

    return title


def normalize_coverage_title(title: str) -> str:
    """
    Normalize coverage title for comparison.

    - Strip whitespace
    - Lowercase (for future case-insensitive matching)
    """
    return title.strip()
