#!/usr/bin/env python3
"""
STEP NEXT-75: Recommendation Cards Generation CLI
==================================================

Generate customer-facing recommendation cards from recommend_results.jsonl.

Usage:
    python -m pipeline.step5_recommendation.run_cards

Input:
    - data/recommend_v1/recommend_results.jsonl
    - data/compare_v1/compare_rows_v1.jsonl
    - rules/rule_catalog.yaml

Output:
    - data/recommend_v1/recommend_cards_v1.jsonl
    - data/recommend_v1/recommend_cards_summary_v1.json
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
from .card_builder import build_all_cards
from .card_model import CardSummary, SLOT_PRIORITY


def save_jsonl(filepath: str, data: List[Dict]):
    """Save JSONL file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def save_json(filepath: str, data: Dict):
    """Save JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_summary(cards: List[Dict]) -> CardSummary:
    """
    Generate summary statistics from cards.

    Returns:
        CardSummary
    """
    total_cards = len(cards)

    # Count by rule
    cards_by_rule: Dict[str, int] = {}
    for card in cards:
        rule_id = card.get("rule_id", "unknown")
        cards_by_rule[rule_id] = cards_by_rule.get(rule_id, 0) + 1

    # Count conflicts and unknowns
    conflict_count = 0
    unknown_count = 0
    anchored_count = 0
    unanchored_count = 0

    slot_status_distribution: Dict[str, int] = {
        "FOUND": 0,
        "FOUND_GLOBAL": 0,
        "CONFLICT": 0,
        "UNKNOWN": 0
    }

    for card in cards:
        gates = card.get("gates", {})

        if gates.get("has_conflict", False):
            conflict_count += 1
        if gates.get("has_unknown", False):
            unknown_count += 1
        if gates.get("anchored", False):
            anchored_count += 1
        else:
            unanchored_count += 1

        # Count slot statuses
        explanations = card.get("explanations", [])
        for exp in explanations:
            status = exp.get("status", "UNKNOWN")
            if status in slot_status_distribution:
                slot_status_distribution[status] += 1

    # Generate summary
    summary: CardSummary = {
        "total_cards": total_cards,
        "cards_by_rule": cards_by_rule,
        "conflict_count": conflict_count,
        "unknown_count": unknown_count,
        "anchored_count": anchored_count,
        "unanchored_count": unanchored_count,
        "slot_status_distribution": slot_status_distribution,
        "gate_failures": []  # Populated by validate_cards_gates.py
    }

    return summary


def validate_dod(cards: List[Dict], summary: CardSummary) -> bool:
    """
    Validate DoD (Definition of Done) for STEP NEXT-75.

    DoD:
    1. All cards have evidences >= 1
    2. At least 3 slots are FOUND/FOUND_GLOBAL per card (no UNKNOWN-only cards)
    3. CONFLICT cards follow handling rules
    4. Fingerprint stability (checked separately)

    Returns:
        True if DoD pass, False otherwise
    """
    dod_pass = True
    errors = []

    # Check 1: All cards have evidences >= 1
    for card in cards:
        evidences = card.get("evidences", [])
        if len(evidences) < 1:
            errors.append(f"DoD FAIL: Card {card['card_id']} has no evidences")
            dod_pass = False

    # Check 2: At least 3 slots are FOUND/FOUND_GLOBAL per card
    for card in cards:
        explanations = card.get("explanations", [])
        found_count = sum(1 for exp in explanations if exp.get("status") in ["FOUND", "FOUND_GLOBAL"])

        if found_count < 3:
            errors.append(f"DoD FAIL: Card {card['card_id']} has only {found_count} FOUND/FOUND_GLOBAL slots (need >= 3)")
            dod_pass = False

    # Check 3: CONFLICT cards follow handling rules
    for card in cards:
        gates = card.get("gates", {})
        if gates.get("has_conflict", False):
            subject = card.get("subject", "")
            if "(문서 상충)" not in subject:
                errors.append(f"DoD FAIL: CONFLICT card {card['card_id']} missing '(문서 상충)' suffix")
                dod_pass = False

    # Print results
    if dod_pass:
        print("✅ DoD PASSED")
    else:
        print("❌ DoD FAILED")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    return dod_pass


def main():
    """CLI entry point"""
    print("=" * 80)
    print("STEP NEXT-75: Recommendation Cards Generation")
    print("=" * 80)

    # Input paths
    recommend_results_path = "data/recommend_v1/recommend_results.jsonl"
    compare_rows_path = "data/compare_v1/compare_rows_v1.jsonl"
    rule_catalog_path = "rules/rule_catalog.yaml"

    # Output paths
    cards_output_path = "data/recommend_v1/recommend_cards_v1.jsonl"
    summary_output_path = "data/recommend_v1/recommend_cards_summary_v1.json"

    # Validate inputs exist
    for path in [recommend_results_path, compare_rows_path, rule_catalog_path]:
        if not Path(path).exists():
            print(f"ERROR: Input file not found: {path}")
            sys.exit(2)

    print(f"\nInputs:")
    print(f"  - {recommend_results_path}")
    print(f"  - {compare_rows_path}")
    print(f"  - {rule_catalog_path}")

    # Build cards
    print("\nBuilding recommendation cards...")
    try:
        cards = build_all_cards(
            recommend_results_path=recommend_results_path,
            compare_rows_path=compare_rows_path,
            rule_catalog_path=rule_catalog_path
        )
    except Exception as e:
        print(f"ERROR building cards: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

    print(f"✅ Built {len(cards)} cards")

    # Generate summary
    print("\nGenerating summary...")
    summary = generate_summary(cards)

    print(f"\nSummary:")
    print(f"  Total cards: {summary['total_cards']}")
    print(f"  Cards by rule: {summary['cards_by_rule']}")
    print(f"  Conflicts: {summary['conflict_count']}")
    print(f"  Unknowns: {summary['unknown_count']}")
    print(f"  Anchored: {summary['anchored_count']}")
    print(f"  Unanchored: {summary['unanchored_count']}")
    print(f"  Slot status: {summary['slot_status_distribution']}")

    # Validate DoD
    print("\nValidating DoD...")
    dod_pass = validate_dod(cards, summary)

    if not dod_pass:
        print("\n⚠️ DoD validation failed, but continuing to save output...")

    # Save outputs
    print(f"\nSaving outputs...")
    save_jsonl(cards_output_path, cards)  # type: ignore
    save_json(summary_output_path, summary)

    print(f"✅ Saved {cards_output_path}")
    print(f"✅ Saved {summary_output_path}")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("  1. Run gate validation:")
    print(f"     python -m pipeline.step5_recommendation.validate_cards_gates {cards_output_path}")
    print("=" * 80)

    sys.exit(0)


if __name__ == "__main__":
    main()
