#!/usr/bin/env python3
"""
STEP NEXT-74: Recommendation Data Models
==========================================

TypedDict models for recommendation output schema.
"""

from typing import TypedDict, Literal, List, Dict, Any


# Decision types
DecisionType = Literal["RECOMMENDED", "CONDITIONAL", "NOT_RECOMMENDED", "NO_EVIDENCE"]

# Slot status types (from Step4)
SlotStatus = Literal["FOUND", "FOUND_GLOBAL", "CONFLICT", "UNKNOWN"]


class EvidenceRef(TypedDict, total=False):
    """Evidence reference with doc/page/excerpt"""
    doc_type: str
    page: int
    excerpt: str
    locator: Dict[str, Any]
    gate_status: str


class CoverageIdentity(TypedDict):
    """Coverage identity (from compare row)"""
    insurer_key: str
    product_key: str
    variant_key: str
    coverage_code: str  # May be empty for unanchored
    coverage_title: str


class SlotSnapshot(TypedDict):
    """Slot status summary for recommendation context"""
    start_date: SlotStatus
    exclusions: SlotStatus
    payout_limit: SlotStatus
    reduction: SlotStatus
    entry_age: SlotStatus
    waiting_period: SlotStatus


class RecommendRow(TypedDict):
    """
    Recommendation row output schema (1:1 with compare_rows_v1.jsonl).

    Constitutional rules:
    - decision != NO_EVIDENCE requires evidence_refs >= 1
    - reason_bullets must be evidence-anchored (no generic statements)
    - All decisions are deterministic based on slot status
    """
    coverage_identity: CoverageIdentity
    decision: DecisionType
    reason_bullets: List[str]  # Max 6, each must reference evidence
    risk_notes: List[str]  # Optional, evidence-anchored
    slot_snapshot: SlotSnapshot
    evidence_refs: List[EvidenceRef]  # Deduplicated evidence used in reasoning


class TopRecommendedCoverage(TypedDict):
    """Top-N recommended coverage for insurer summary"""
    coverage_title: str
    coverage_code: str
    reason_highlights: List[str]  # Top 2 reasons
    evidence_count: int


class InsurerSummary(TypedDict):
    """Per-insurer aggregation with decision counts and top recommendations"""
    insurer_key: str
    counts: Dict[DecisionType, int]  # {RECOMMENDED: N, CONDITIONAL: M, ...}
    total_coverages: int
    top_recommended: List[TopRecommendedCoverage]  # Top N by evidence quality
