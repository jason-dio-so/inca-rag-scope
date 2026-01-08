#!/usr/bin/env python3
"""
STEP NEXT-75: Recommendation Card Builder
==========================================

Deterministic card generation from recommend_results.jsonl.

Rules:
1. All values come from recommend_results OR compare_rows slots (NO new generation)
2. Explanation bullets follow SLOT_PRIORITY order
3. CONFLICT cards get "(문서 상충)" suffix
4. Evidence >= 1 per card (hard requirement)
"""

import json
from typing import Dict, List, Any
from datetime import datetime, timezone
from .card_model import (
    RecommendationCard,
    CoverageIdentity,
    ExplanationBullet,
    CardGates,
    EvidenceRef,
    SLOT_PRIORITY,
    SLOT_LABELS,
    SubjectTemplate,
    generate_card_id,
    sort_evidences_by_priority,
    deduplicate_evidences
)


def load_jsonl(filepath: str) -> List[Dict]:
    """Load JSONL file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def load_compare_rows(filepath: str) -> Dict[str, Dict]:
    """
    Load compare_rows_v1.jsonl and index by 4D identity.

    Returns: {identity_key: row}
    """
    rows = load_jsonl(filepath)
    indexed = {}

    for row in rows:
        identity = row.get("identity", {})
        key = (
            identity.get("insurer_key", ""),
            identity.get("product_key", ""),
            identity.get("variant_key", ""),
            identity.get("coverage_title", "")
        )
        indexed[key] = row

    return indexed


def build_identity(recommend_row: Dict, compare_row: Dict) -> CoverageIdentity:
    """Build coverage identity from recommend_row + compare_row"""
    rec_cov = recommend_row.get("coverage", {})
    comp_identity = compare_row.get("identity", {})

    return {
        "insurer_key": rec_cov.get("insurer", ""),
        "product_key": rec_cov.get("product", ""),
        "variant_key": rec_cov.get("variant", "default"),
        "coverage_code": comp_identity.get("coverage_code", ""),  # May be empty
        "coverage_title": rec_cov.get("coverage_title", "")
    }


def build_explanations(
    compare_row: Dict,
    recommend_row: Dict
) -> List[ExplanationBullet]:
    """
    Build explanation bullets from slots, following SLOT_PRIORITY.

    Rules:
    - Only include slots with status FOUND/FOUND_GLOBAL/CONFLICT
    - Skip UNKNOWN slots (or include with empty value)
    - Top K=2 evidences per slot
    """
    slots = compare_row.get("slots", {})
    explanations: List[ExplanationBullet] = []

    for slot_name in SLOT_PRIORITY:
        slot_data = slots.get(slot_name, {})
        status = slot_data.get("status", "UNKNOWN")

        # Skip UNKNOWN for explanations (per spec, UNKNOWN value should be empty)
        if status == "UNKNOWN":
            continue

        # Get value (may be None)
        value = slot_data.get("value", "")
        if value is None:
            value = ""

        # Get top K=2 evidences for this slot
        slot_evidences = slot_data.get("evidences", [])
        sorted_evidences = sort_evidences_by_priority(slot_evidences)
        top_evidences = deduplicate_evidences(sorted_evidences)

        # Build explanation bullet
        explanations.append({
            "label": SLOT_LABELS.get(slot_name, slot_name),
            "value": str(value),
            "status": status,  # type: ignore
            "evidence_refs": top_evidences
        })

    return explanations


def collect_all_evidences(compare_row: Dict) -> List[EvidenceRef]:
    """
    Collect all evidences from slots, deduplicate, and return top K=2.

    Sorted by doc_priority (가입설계서 > 요약서 > 사업방법서 > 약관) then page.
    """
    all_evidences = []
    slots = compare_row.get("slots", {})

    for slot_name in SLOT_PRIORITY:
        slot_data = slots.get(slot_name, {})
        evidences = slot_data.get("evidences", [])
        all_evidences.extend(evidences)

    # Sort and deduplicate
    sorted_evidences = sort_evidences_by_priority(all_evidences)
    return deduplicate_evidences(sorted_evidences)


def build_gates(compare_row: Dict, evidences: List[EvidenceRef]) -> CardGates:
    """Build gate results for this card"""
    slots = compare_row.get("slots", {})

    has_conflict = False
    has_unknown = False

    for slot_name in SLOT_PRIORITY:
        slot_data = slots.get(slot_name, {})
        status = slot_data.get("status", "UNKNOWN")

        if status == "CONFLICT":
            has_conflict = True
        if status == "UNKNOWN":
            has_unknown = True

    identity = compare_row.get("identity", {})
    coverage_code = identity.get("coverage_code", "")
    anchored = bool(coverage_code)

    return {
        "has_conflict": has_conflict,
        "has_unknown": has_unknown,
        "evidence_count": len(evidences),
        "anchored": anchored
    }


def build_subject(
    rule_title: str,
    coverage_title: str,
    metrics: Dict[str, Any],
    has_conflict: bool
) -> str:
    """
    Build subject line using fixed templates.

    NO free text generation.
    """
    # Extract primary metric (first in metrics dict)
    metric_items = list(metrics.items())
    if metric_items:
        metric_key, metric_value = metric_items[0]
    else:
        metric_key, metric_value = "N/A", ""

    # Default template
    base_subject = SubjectTemplate.default(
        rule_title=rule_title,
        coverage_title=coverage_title,
        metric_key=metric_key,
        metric_value=metric_value
    )

    # Add conflict suffix if needed
    if has_conflict:
        return SubjectTemplate.with_conflict(base_subject)

    return base_subject


def build_card(
    recommend_row: Dict,
    compare_rows_index: Dict[str, Dict],
    rule_catalog: Dict[str, Dict]
) -> RecommendationCard:
    """
    Build a single recommendation card from recommend_results row.

    Args:
        recommend_row: Single row from recommend_results.jsonl
        compare_rows_index: Indexed compare_rows by 4D identity
        rule_catalog: Rule metadata indexed by rule_id

    Returns:
        RecommendationCard
    """
    # Get rule info
    rule_id = recommend_row.get("rule_id", "")
    rule_info = rule_catalog.get(rule_id, {})
    rule_title = rule_info.get("intent", rule_id)

    # Get compare row
    rec_cov = recommend_row.get("coverage", {})
    compare_key = (
        rec_cov.get("insurer", ""),
        rec_cov.get("product", ""),
        rec_cov.get("variant", "default"),
        rec_cov.get("coverage_title", "")
    )
    compare_row = compare_rows_index.get(compare_key)

    if not compare_row:
        raise ValueError(f"Compare row not found for {compare_key}")

    # Build identity
    identity = build_identity(recommend_row, compare_row)

    # Build explanations (from slots)
    explanations = build_explanations(compare_row, recommend_row)

    # Collect all evidences (top K=2)
    evidences = collect_all_evidences(compare_row)

    # Build gates
    gates = build_gates(compare_row, evidences)

    # Build metrics (from recommend_row)
    metrics = recommend_row.get("metric", {})

    # Build subject
    subject = build_subject(
        rule_title=rule_title,
        coverage_title=identity["coverage_title"],
        metrics=metrics,
        has_conflict=gates["has_conflict"]
    )

    # Generate card_id
    card_id = generate_card_id(
        rule_id=rule_id,
        insurer_key=identity["insurer_key"],
        product_key=identity["product_key"],
        variant_key=identity["variant_key"],
        coverage_code=identity["coverage_code"],
        coverage_name_normalized=identity["coverage_title"]
    )

    # Build card
    card: RecommendationCard = {
        "card_id": card_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rule_id": rule_id,
        "rule_title": rule_title,
        "rank": recommend_row.get("rank", 1),
        "subject": subject,
        "identity": identity,
        "metrics": metrics,
        "explanations": explanations,
        "evidences": evidences,
        "gates": gates
    }

    return card


def build_all_cards(
    recommend_results_path: str,
    compare_rows_path: str,
    rule_catalog_path: str
) -> List[RecommendationCard]:
    """
    Build all recommendation cards.

    Args:
        recommend_results_path: data/recommend_v1/recommend_results.jsonl
        compare_rows_path: data/compare_v1/compare_rows_v1.jsonl
        rule_catalog_path: rules/rule_catalog.yaml

    Returns:
        List of RecommendationCard
    """
    # Load inputs
    recommend_rows = load_jsonl(recommend_results_path)
    compare_rows_index = load_compare_rows(compare_rows_path)

    # Load rule catalog
    import yaml
    with open(rule_catalog_path, 'r', encoding='utf-8') as f:
        rule_catalog_data = yaml.safe_load(f)

    rule_catalog = {}
    for rule in rule_catalog_data.get("rules", []):
        rule_id = rule.get("rule_id", "")
        rule_catalog[rule_id] = rule

    # Build cards
    cards = []
    for rec_row in recommend_rows:
        try:
            card = build_card(rec_row, compare_rows_index, rule_catalog)
            cards.append(card)
        except Exception as e:
            print(f"ERROR building card for {rec_row.get('rule_id', 'unknown')}: {e}")
            continue

    return cards
