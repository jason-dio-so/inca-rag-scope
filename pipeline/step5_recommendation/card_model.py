#!/usr/bin/env python3
"""
STEP NEXT-75: Recommendation Card Output Schema (LOCKED)
=========================================================

Deterministic card output schema for customer-facing recommendation UI.

Constitutional rules:
- NO LLM calls
- NO inference or new value generation
- 100% evidence traceability
- Deterministic card generation
"""

from typing import TypedDict, Literal, List, Dict, Any
from dataclasses import dataclass
import hashlib
import json


# Slot status from Step4
SlotStatus = Literal["FOUND", "FOUND_GLOBAL", "CONFLICT", "UNKNOWN"]


class EvidenceRef(TypedDict, total=False):
    """Evidence reference for card"""
    doc_type: str
    page: int
    locator: Dict[str, Any]
    excerpt_hash: str  # SHA256 hash of excerpt for deduplication


class CoverageIdentity(TypedDict):
    """4D Coverage identity"""
    insurer_key: str
    product_key: str
    variant_key: str
    coverage_code: str  # Nullable (empty string if unanchored)
    coverage_title: str  # From Step1 semantics (title field)


class ExplanationBullet(TypedDict):
    """Deterministic explanation bullet from slot data"""
    label: str  # e.g., "면책기간", "감액", "가입나이", etc.
    value: str  # Direct from slots.*.value (NO reinterpretation)
    status: SlotStatus
    evidence_refs: List[EvidenceRef]  # Top K=2 evidences for this slot


class CardGates(TypedDict):
    """Gate results for this card"""
    has_conflict: bool  # Any slot has CONFLICT
    has_unknown: bool  # Any slot has UNKNOWN
    evidence_count: int  # Total evidences >= 1 required
    anchored: bool  # coverage_code is not empty


class RecommendationCard(TypedDict):
    """
    Recommendation Card Schema (customer-facing output).

    This is the LOCKED schema for Step5 output.
    """
    card_id: str  # Stable hash(rule_id + 4D identity + coverage_code + coverage_name_normalized)
    generated_at: str  # ISO8601

    # Rule context
    rule_id: str
    rule_title: str
    rank: int  # 1..N within rule

    # Customer-facing subject (template-based, NO free text)
    subject: str  # e.g., "[{rule_title}] {coverage_title} — {metric_key} {metric_value}"

    # Identity
    identity: CoverageIdentity

    # Metrics (from rule calculation, sourced from slots.*)
    metrics: Dict[str, Any]  # e.g., {"waiting_days": 1.0, "payout_amount": 90}

    # Explanations (deterministic bullets)
    explanations: List[ExplanationBullet]  # Ordered by slot priority

    # Top representative evidences (minimum 1)
    evidences: List[EvidenceRef]  # Top K=2 across all slots, sorted by doc_priority

    # Gates
    gates: CardGates


class CardSummary(TypedDict):
    """Summary statistics and gate report"""
    total_cards: int
    cards_by_rule: Dict[str, int]  # {rule_id: count}
    conflict_count: int
    unknown_count: int
    anchored_count: int
    unanchored_count: int
    slot_status_distribution: Dict[str, int]  # {FOUND: N, FOUND_GLOBAL: M, ...}
    gate_failures: List[str]  # List of gate failure messages


# Priority slots for explanation generation (fixed order)
SLOT_PRIORITY = [
    "waiting_period",
    "reduction",
    "payout_limit",
    "exclusions",
    "entry_age",
    "start_date"
]

# Slot label mapping (Korean)
SLOT_LABELS = {
    "waiting_period": "면책기간",
    "reduction": "감액",
    "payout_limit": "지급한도",
    "exclusions": "제외사항",
    "entry_age": "가입나이",
    "start_date": "보장개시일"
}

# Doc priority for evidence sorting (higher = more authoritative)
DOC_PRIORITY = {
    "가입설계서": 4,
    "상품요약서": 3,
    "사업방법서": 2,
    "약관": 1
}


@dataclass
class SubjectTemplate:
    """Subject line templates (NO free text generation)"""

    @staticmethod
    def default(rule_title: str, coverage_title: str, metric_key: str, metric_value: Any) -> str:
        """Default template"""
        return f"[{rule_title}] {coverage_title} — {metric_key} {metric_value}"

    @staticmethod
    def with_conflict(base_subject: str) -> str:
        """Add conflict suffix"""
        return f"{base_subject} (문서 상충)"

    @staticmethod
    def waiting_period(coverage_title: str, waiting_days: Any, reduction_summary: str = "") -> str:
        """Waiting period specific template"""
        if reduction_summary:
            return f"{coverage_title} — 면책 {waiting_days}일 / 감액 {reduction_summary}"
        return f"{coverage_title} — 면책 {waiting_days}일"


def generate_card_id(
    rule_id: str,
    insurer_key: str,
    product_key: str,
    variant_key: str,
    coverage_code: str,
    coverage_name_normalized: str
) -> str:
    """
    Generate stable card ID from identity components.

    Uses SHA256 hash for stability.
    """
    components = [
        rule_id,
        insurer_key,
        product_key,
        variant_key,
        coverage_code,
        coverage_name_normalized
    ]
    hash_input = "|".join(components)
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def generate_excerpt_hash(excerpt: str) -> str:
    """Generate hash for excerpt deduplication"""
    return hashlib.sha256(excerpt.encode()).hexdigest()[:16]


def sort_evidences_by_priority(evidences: List[Dict]) -> List[Dict]:
    """
    Sort evidences by:
    1. doc_priority (가입설계서 > 요약서 > 사업방법서 > 약관)
    2. page asc
    """
    def sort_key(ev: Dict) -> tuple:
        doc_type = ev.get("doc_type", "")
        page = ev.get("page", 9999)
        priority = DOC_PRIORITY.get(doc_type, 0)
        return (-priority, page)

    return sorted(evidences, key=sort_key)


def deduplicate_evidences(evidences: List[Dict]) -> List[EvidenceRef]:
    """
    Deduplicate evidences by excerpt hash.

    Returns top K=2 evidences after deduplication.
    """
    seen_hashes = set()
    unique_evidences = []

    for ev in evidences:
        excerpt = ev.get("excerpt", "")
        excerpt_hash = generate_excerpt_hash(excerpt)

        if excerpt_hash not in seen_hashes:
            seen_hashes.add(excerpt_hash)
            unique_evidences.append({
                "doc_type": ev.get("doc_type", ""),
                "page": ev.get("page", 0),
                "locator": ev.get("locator", {}),
                "excerpt_hash": excerpt_hash
            })

    # Return top K=2
    return unique_evidences[:2]  # type: ignore
