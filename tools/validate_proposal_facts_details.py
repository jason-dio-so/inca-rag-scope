#!/usr/bin/env python3
"""
Validate proposal_facts details in coverage_cards.jsonl files.

Usage:
    python tools/validate_proposal_facts_details.py
"""
import json
from pathlib import Path
from collections import defaultdict

AXES = [
    "samsung", "meritz", "hanwha", "heungkuk", "hyundai",
    "kb", "lotte_male", "lotte_female", "db_under40", "db_over41"
]

def validate_axis(axis: str) -> dict:
    """Validate proposal_facts details for an axis."""
    cards_path = Path(f"data/compare/{axis}_coverage_cards.jsonl")

    result = {
        "axis": axis,
        "total_rows": 0,
        "with_proposal_facts": 0,
        "with_amount": 0,
        "with_premium": 0,
        "with_period": 0
    }

    if not cards_path.exists():
        return result

    with open(cards_path, "r", encoding="utf-8") as f:
        for line in f:
            card = json.loads(line)
            result["total_rows"] += 1

            if "proposal_facts" in card:
                result["with_proposal_facts"] += 1
                pf = card["proposal_facts"]

                if pf.get("coverage_amount_text"):
                    result["with_amount"] += 1
                if pf.get("premium_text"):
                    result["with_premium"] += 1
                if pf.get("period_text"):
                    result["with_period"] += 1

    return result

def main():
    print("=" * 100)
    print("Validating proposal_facts details in coverage_cards.jsonl")
    print("=" * 100)
    print()
    print(f"{'Axis':<15} {'Total':<8} {'Has PF':<8} {'Amount':<8} {'Premium':<8} {'Period':<8} {'%PF':<8} {'%Amt':<8}")
    print("-" * 100)

    all_results = []

    for axis in AXES:
        result = validate_axis(axis)
        all_results.append(result)

        pf_pct = (result["with_proposal_facts"] / result["total_rows"] * 100) if result["total_rows"] > 0 else 0
        amt_pct = (result["with_amount"] / result["with_proposal_facts"] * 100) if result["with_proposal_facts"] > 0 else 0

        print(f"{axis:<15} {result['total_rows']:<8} {result['with_proposal_facts']:<8} "
              f"{result['with_amount']:<8} {result['with_premium']:<8} {result['with_period']:<8} "
              f"{pf_pct:>6.1f}% {amt_pct:>6.1f}%")

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    total_rows = sum(r["total_rows"] for r in all_results)
    total_pf = sum(r["with_proposal_facts"] for r in all_results)
    total_amt = sum(r["with_amount"] for r in all_results)
    total_prem = sum(r["with_premium"] for r in all_results)
    total_per = sum(r["with_period"] for r in all_results)

    print(f"Total coverage cards:           {total_rows:4}")
    print(f"With proposal_facts:            {total_pf:4} ({total_pf/total_rows*100:>5.1f}%)")
    print(f"With coverage_amount_text:      {total_amt:4} ({total_amt/total_pf*100:>5.1f}% of rows with PF)")
    print(f"With premium_text:              {total_prem:4} ({total_prem/total_pf*100:>5.1f}% of rows with PF)")
    print(f"With period_text:               {total_per:4} ({total_per/total_pf*100:>5.1f}% of rows with PF)")
    print()

    return 0

if __name__ == "__main__":
    exit(main())
