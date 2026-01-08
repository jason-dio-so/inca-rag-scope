#!/usr/bin/env python3
"""
STEP NEXT-74: Recommendation Builder
======================================

Convert compare_rows_v1.jsonl → recommend_rows_v1.jsonl with evidence-based decisions.
"""

import json
from typing import Dict, List, Any
from pathlib import Path

from .model import (
    RecommendRow,
    CoverageIdentity,
    SlotSnapshot,
    EvidenceRef,
    InsurerSummary,
    TopRecommendedCoverage,
    DecisionType
)
from .rules import (
    determine_decision,
    generate_reason_bullets,
    rank_coverages_by_evidence
)


def extract_all_evidences(compare_row: Dict) -> List[EvidenceRef]:
    """
    Extract all evidence refs from compare row slots.
    Deduplicate by (doc_type, page, excerpt subset).
    """
    evidences: List[EvidenceRef] = []
    seen_keys = set()

    slots = compare_row.get("slots", {})
    for slot_name, slot_data in slots.items():
        if isinstance(slot_data, dict):
            slot_evidences = slot_data.get("evidences", [])
            for ev in slot_evidences:
                if isinstance(ev, dict):
                    # Dedup key: (doc_type, page, first 50 chars of excerpt)
                    doc_type = ev.get("doc_type", "")
                    page = ev.get("page", 0)
                    excerpt = ev.get("excerpt", "")
                    key = (doc_type, page, excerpt[:50])

                    if key not in seen_keys:
                        seen_keys.add(key)
                        evidences.append(ev)  # type: ignore

    return evidences


def build_slot_snapshot(compare_row: Dict) -> SlotSnapshot:
    """Extract slot status snapshot from compare row"""
    slots = compare_row.get("slots", {})

    snapshot: SlotSnapshot = {
        "start_date": slots.get("start_date", {}).get("status", "UNKNOWN"),  # type: ignore
        "exclusions": slots.get("exclusions", {}).get("status", "UNKNOWN"),  # type: ignore
        "payout_limit": slots.get("payout_limit", {}).get("status", "UNKNOWN"),  # type: ignore
        "reduction": slots.get("reduction", {}).get("status", "UNKNOWN"),  # type: ignore
        "entry_age": slots.get("entry_age", {}).get("status", "UNKNOWN"),  # type: ignore
        "waiting_period": slots.get("waiting_period", {}).get("status", "UNKNOWN"),  # type: ignore
    }

    return snapshot


def build_coverage_identity(compare_row: Dict) -> CoverageIdentity:
    """Extract coverage identity from compare row"""
    identity = compare_row.get("identity", {})

    return CoverageIdentity(
        insurer_key=identity.get("insurer_key", ""),
        product_key=identity.get("product_key", ""),
        variant_key=identity.get("variant_key", "default"),
        coverage_code=identity.get("coverage_code", ""),
        coverage_title=identity.get("coverage_title", "")
    )


def build_recommend_row(compare_row: Dict) -> RecommendRow:
    """
    Build recommendation row from compare row.

    Steps:
    1. Extract coverage identity
    2. Build slot snapshot
    3. Collect all evidences (dedup)
    4. Determine decision (deterministic rules)
    5. Generate reason bullets (evidence-anchored)

    Args:
        compare_row: Single row from compare_rows_v1.jsonl

    Returns:
        RecommendRow
    """
    # Extract components
    coverage_identity = build_coverage_identity(compare_row)
    slot_snapshot = build_slot_snapshot(compare_row)
    evidences = extract_all_evidences(compare_row)

    # Determine decision
    decision = determine_decision(slot_snapshot, len(evidences))

    # Generate reasons
    reason_bullets, risk_notes = generate_reason_bullets(
        slot_snapshot,
        decision,
        evidences,
        coverage_identity["coverage_title"]
    )

    # Build output
    recommend_row: RecommendRow = {
        "coverage_identity": coverage_identity,
        "decision": decision,
        "reason_bullets": reason_bullets,
        "risk_notes": risk_notes,
        "slot_snapshot": slot_snapshot,
        "evidence_refs": evidences
    }

    return recommend_row


def aggregate_insurer_summary(
    recommend_rows: List[RecommendRow],
    insurer_key: str,
    top_n: int = 10
) -> InsurerSummary:
    """
    Aggregate recommendation rows for a single insurer.

    Args:
        recommend_rows: All recommendation rows for this insurer
        insurer_key: Insurer key
        top_n: Number of top recommendations to include

    Returns:
        InsurerSummary with counts and top recommendations
    """
    # Count decisions
    counts: Dict[DecisionType, int] = {
        "RECOMMENDED": 0,
        "CONDITIONAL": 0,
        "NOT_RECOMMENDED": 0,
        "NO_EVIDENCE": 0
    }

    for row in recommend_rows:
        decision = row["decision"]
        if decision in counts:
            counts[decision] += 1

    # Rank and select top N recommended
    recommend_dicts = [dict(r) for r in recommend_rows]
    top_recommended_rows = rank_coverages_by_evidence(recommend_dicts)[:top_n]

    # Build top recommended summaries
    top_recommended: List[TopRecommendedCoverage] = []
    for row in top_recommended_rows:
        identity = row["coverage_identity"]
        reasons = row.get("reason_bullets", [])
        ev_count = len(row.get("evidence_refs", []))

        top_recommended.append(TopRecommendedCoverage(
            coverage_title=identity["coverage_title"],
            coverage_code=identity.get("coverage_code", ""),
            reason_highlights=reasons[:2],  # Top 2 reasons
            evidence_count=ev_count
        ))

    summary: InsurerSummary = {
        "insurer_key": insurer_key,
        "counts": counts,
        "total_coverages": len(recommend_rows),
        "top_recommended": top_recommended
    }

    return summary


def build_all_recommendations(
    compare_rows_file: Path
) -> List[RecommendRow]:
    """
    Build all recommendation rows from compare_rows_v1.jsonl.

    Args:
        compare_rows_file: Path to compare_rows_v1.jsonl

    Returns:
        List of RecommendRow (1:1 with input)
    """
    recommend_rows: List[RecommendRow] = []

    with open(compare_rows_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                compare_row = json.loads(line)
                recommend_row = build_recommend_row(compare_row)
                recommend_rows.append(recommend_row)
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: JSON decode error at line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"⚠️  Warning: Error processing line {line_num}: {e}")
                continue

    return recommend_rows


def build_insurer_summaries(
    recommend_rows: List[RecommendRow],
    insurers: List[str],
    top_n: int = 10
) -> Dict[str, InsurerSummary]:
    """
    Build per-insurer summaries with top-N recommendations.

    Args:
        recommend_rows: All recommendation rows
        insurers: List of insurer keys to summarize
        top_n: Number of top recommendations per insurer

    Returns:
        Dict[insurer_key, InsurerSummary]
    """
    # Group by insurer
    by_insurer: Dict[str, List[RecommendRow]] = {ins: [] for ins in insurers}

    for row in recommend_rows:
        insurer = row["coverage_identity"]["insurer_key"]
        if insurer in by_insurer:
            by_insurer[insurer].append(row)

    # Aggregate each insurer
    summaries: Dict[str, InsurerSummary] = {}
    for insurer, rows in by_insurer.items():
        if rows:  # Only include insurers with data
            summaries[insurer] = aggregate_insurer_summary(rows, insurer, top_n)

    return summaries
