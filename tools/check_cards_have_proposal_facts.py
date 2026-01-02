#!/usr/bin/env python3
"""
Check which coverage_cards.jsonl files need proposal_facts backfill.

Usage:
    python tools/check_cards_have_proposal_facts.py
"""
import json
from pathlib import Path

AXES = [
    "samsung", "meritz", "hanwha", "heungkuk", "hyundai",
    "kb", "lotte_male", "lotte_female", "db_under40", "db_over41"
]

def check_axis(axis: str) -> dict:
    """Check if axis coverage_cards has proposal_facts."""
    cards_path = Path(f"data/compare/{axis}_coverage_cards.jsonl")

    result = {
        "axis": axis,
        "cards_exists": cards_path.exists(),
        "has_proposal_facts": False,
        "sample_count": 0,
        "with_facts_count": 0
    }

    if not cards_path.exists():
        return result

    # Sample first 10 rows to check
    with open(cards_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 10:
                break
            card = json.loads(line)
            result["sample_count"] += 1
            if "proposal_facts" in card:
                result["with_facts_count"] += 1

    result["has_proposal_facts"] = (
        result["with_facts_count"] > 0 and
        result["with_facts_count"] == result["sample_count"]
    )

    return result

def main():
    print("=" * 80)
    print("Checking coverage_cards.jsonl for proposal_facts presence")
    print("=" * 80)
    print()

    needs_backfill = []
    already_done = []
    missing = []

    for axis in AXES:
        result = check_axis(axis)

        if not result["cards_exists"]:
            missing.append(axis)
            status = "❌ MISSING"
        elif result["has_proposal_facts"]:
            already_done.append(axis)
            status = "✅ HAS FACTS"
        else:
            needs_backfill.append(axis)
            status = "⚠️  NEEDS BACKFILL"

        print(f"{status:20} {axis:15} (sampled: {result['sample_count']}, with_facts: {result['with_facts_count']})")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Already done:     {len(already_done):2} axes: {', '.join(already_done)}")
    print(f"Needs backfill:   {len(needs_backfill):2} axes: {', '.join(needs_backfill)}")
    print(f"Missing cards:    {len(missing):2} axes: {', '.join(missing)}")
    print()

    if needs_backfill:
        print("ACTIONS NEEDED:")
        print("Run Step5 for the following axes:")
        for axis in needs_backfill:
            print(f"  python -m pipeline.step5_build_cards.build_cards --insurer {axis}")
        print()

    return 0 if not needs_backfill else 1

if __name__ == "__main__":
    exit(main())
