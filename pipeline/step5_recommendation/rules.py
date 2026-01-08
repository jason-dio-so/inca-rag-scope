#!/usr/bin/env python3
"""
STEP NEXT-74: Deterministic Recommendation Rules
==================================================

Evidence-based decision logic with NO LLM, NO inference.

Core principles:
1. NO evidence → NO_EVIDENCE (hard rule)
2. Core slot CONFLICTs → downgrade decision
3. UNKNOWN in core slots → NOT_RECOMMENDED
4. All FOUND/FOUND_GLOBAL in core → RECOMMENDED (if no conflicts)
5. Mixed evidence strength → CONDITIONAL

Constitutional compliance:
- NO arbitrary scoring
- NO LLM calls
- All decisions traceable to slot status
"""

from typing import Dict, List, Tuple
from .model import DecisionType, SlotStatus, SlotSnapshot


# Core slots that heavily impact recommendation
CORE_SLOTS = ["start_date", "exclusions", "payout_limit", "reduction"]

# Secondary slots (informational but less critical)
SECONDARY_SLOTS = ["entry_age", "waiting_period"]


def count_slot_statuses(slot_snapshot: SlotSnapshot) -> Dict[SlotStatus, int]:
    """Count occurrences of each slot status"""
    counts: Dict[SlotStatus, int] = {
        "FOUND": 0,
        "FOUND_GLOBAL": 0,
        "CONFLICT": 0,
        "UNKNOWN": 0
    }

    for slot_name, status in slot_snapshot.items():
        if status in counts:
            counts[status] += 1

    return counts


def count_core_slot_statuses(slot_snapshot: SlotSnapshot) -> Dict[SlotStatus, int]:
    """Count statuses only in core slots"""
    counts: Dict[SlotStatus, int] = {
        "FOUND": 0,
        "FOUND_GLOBAL": 0,
        "CONFLICT": 0,
        "UNKNOWN": 0
    }

    for slot_name in CORE_SLOTS:
        status = slot_snapshot.get(slot_name)  # type: ignore
        if status and status in counts:
            counts[status] += 1

    return counts


def determine_decision(
    slot_snapshot: SlotSnapshot,
    total_evidence_count: int
) -> DecisionType:
    """
    Deterministic decision based on slot status and evidence count.

    Rules (in priority order):
    1. NO evidence → NO_EVIDENCE
    2. Core UNKNOWN ≥ 1 → NOT_RECOMMENDED
    3. Core CONFLICT ≥ 2 → NOT_RECOMMENDED
    4. Core CONFLICT = 1 → CONDITIONAL
    5. All core are FOUND/FOUND_GLOBAL, no conflicts → RECOMMENDED
    6. Mixed evidence (FOUND_GLOBAL majority) → CONDITIONAL

    Args:
        slot_snapshot: Status of all 6 slots
        total_evidence_count: Total number of evidence refs

    Returns:
        DecisionType
    """
    # Rule 1: NO evidence → NO_EVIDENCE (HARD)
    if total_evidence_count == 0:
        return "NO_EVIDENCE"

    # Count statuses in core slots only
    core_counts = count_core_slot_statuses(slot_snapshot)

    # Rule 2: Core UNKNOWN ≥ 1 → NOT_RECOMMENDED
    if core_counts["UNKNOWN"] >= 1:
        return "NOT_RECOMMENDED"

    # Rule 3: Core CONFLICT ≥ 2 → NOT_RECOMMENDED
    if core_counts["CONFLICT"] >= 2:
        return "NOT_RECOMMENDED"

    # Rule 4: Core CONFLICT = 1 → CONDITIONAL
    if core_counts["CONFLICT"] == 1:
        return "CONDITIONAL"

    # Rule 5: All core are FOUND/FOUND_GLOBAL, no conflicts
    if core_counts["CONFLICT"] == 0 and core_counts["UNKNOWN"] == 0:
        # Strong evidence (mostly FOUND)
        if core_counts["FOUND"] >= 3:
            return "RECOMMENDED"
        # Weaker evidence (mostly FOUND_GLOBAL)
        elif core_counts["FOUND_GLOBAL"] >= 2:
            return "CONDITIONAL"
        # Mixed
        else:
            return "RECOMMENDED"  # Default to RECOMMENDED if core has any FOUND

    # Rule 6: Default to CONDITIONAL for edge cases
    return "CONDITIONAL"


def generate_reason_bullets(
    slot_snapshot: SlotSnapshot,
    decision: DecisionType,
    all_evidences: List[Dict],
    coverage_title: str
) -> Tuple[List[str], List[str]]:
    """
    Generate evidence-anchored reason bullets and risk notes.

    Args:
        slot_snapshot: Slot status summary
        decision: Decision type
        all_evidences: All evidence refs from compare row
        coverage_title: Coverage title for context

    Returns:
        (reason_bullets, risk_notes)
    """
    reason_bullets = []
    risk_notes = []

    # Count statuses
    core_counts = count_core_slot_statuses(slot_snapshot)
    all_counts = count_slot_statuses(slot_snapshot)

    # Evidence count per doc type
    evidence_by_doc: Dict[str, int] = {}
    for ev in all_evidences:
        doc_type = ev.get("doc_type", "unknown")
        evidence_by_doc[doc_type] = evidence_by_doc.get(doc_type, 0) + 1

    # Bullet 1: Decision summary with evidence count
    total_ev = len(all_evidences)
    if decision == "NO_EVIDENCE":
        reason_bullets.append(f"증거 부족: 약관/상품요약서에서 '{coverage_title}' 관련 근거를 발견하지 못함")
    elif decision == "RECOMMENDED":
        ev_summary = ", ".join([f"{doc}({cnt}건)" for doc, cnt in sorted(evidence_by_doc.items())])
        reason_bullets.append(f"핵심 항목 {core_counts['FOUND']}개 명확히 확인됨 (총 {total_ev}건 근거: {ev_summary})")
    elif decision == "CONDITIONAL":
        reason_bullets.append(f"조건부 추천: 핵심 항목 중 CONFLICT {core_counts['CONFLICT']}건 또는 FOUND_GLOBAL {all_counts['FOUND_GLOBAL']}건 존재")
    elif decision == "NOT_RECOMMENDED":
        reason_bullets.append(f"비추천: 핵심 항목 중 CONFLICT {core_counts['CONFLICT']}건 또는 UNKNOWN {core_counts['UNKNOWN']}건 검출")

    # Bullet 2: Core slots status breakdown
    core_status_parts = []
    for slot in CORE_SLOTS:
        status = slot_snapshot.get(slot)  # type: ignore
        if status == "FOUND":
            core_status_parts.append(f"{slot}(확인)")
        elif status == "FOUND_GLOBAL":
            core_status_parts.append(f"{slot}(전역)")
        elif status == "CONFLICT":
            core_status_parts.append(f"{slot}(충돌)")
        elif status == "UNKNOWN":
            core_status_parts.append(f"{slot}(미확인)")

    if core_status_parts:
        reason_bullets.append(f"핵심 항목 상태: {', '.join(core_status_parts)}")

    # Bullet 3: Evidence source breakdown
    if evidence_by_doc:
        doc_list = [f"{doc_type} {cnt}건" for doc_type, cnt in sorted(evidence_by_doc.items(), key=lambda x: -x[1])]
        reason_bullets.append(f"근거 출처: {', '.join(doc_list)}")

    # Risk notes for CONFLICT/UNKNOWN
    if core_counts["CONFLICT"] > 0:
        conflict_slots = [s for s in CORE_SLOTS if slot_snapshot.get(s) == "CONFLICT"]  # type: ignore
        risk_notes.append(f"⚠️ 충돌 항목({len(conflict_slots)}): {', '.join(conflict_slots)} - 문서 간 불일치 확인 필요")

    if core_counts["UNKNOWN"] > 0:
        unknown_slots = [s for s in CORE_SLOTS if slot_snapshot.get(s) == "UNKNOWN"]  # type: ignore
        risk_notes.append(f"⚠️ 미확인 항목({len(unknown_slots)}): {', '.join(unknown_slots)} - 추가 검토 필요")

    # Limit bullets to max 6
    reason_bullets = reason_bullets[:6]

    return reason_bullets, risk_notes


def rank_coverages_by_evidence(recommend_rows: List[Dict]) -> List[Dict]:
    """
    Rank RECOMMENDED coverages by evidence quality.

    Ranking criteria (in order):
    1. Decision = RECOMMENDED (exclude others)
    2. More FOUND in core slots (stronger evidence)
    3. More total evidence count
    4. Alphabetical by coverage_code

    Args:
        recommend_rows: List of recommendation rows

    Returns:
        Sorted list of RECOMMENDED rows
    """
    recommended = [r for r in recommend_rows if r["decision"] == "RECOMMENDED"]

    def rank_key(row: Dict) -> Tuple:
        snapshot = row["slot_snapshot"]
        core_found = sum(1 for slot in CORE_SLOTS if snapshot.get(slot) == "FOUND")
        total_ev = len(row.get("evidence_refs", []))
        code = row["coverage_identity"].get("coverage_code", "")

        return (-core_found, -total_ev, code)

    return sorted(recommended, key=rank_key)
