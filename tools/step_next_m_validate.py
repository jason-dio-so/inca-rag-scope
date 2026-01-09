#!/usr/bin/env python3
"""
STEP NEXT-M: Balanced Card Validation
Enforce G7 (Balance) and G8 (No-Promotion) gates

Checks:
1. G7: WHY ≥ 1 AND WHY-NOT ≥ 1 (mandatory)
2. G8: No emotion/comparison/numbers
3. All STEP NEXT-L checks (no numbers, Tier-A, evidence, confidence)
4. WHY-NOT is fact-based (no comparative language)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import re


def check_g7_balanced_card(cards: List[dict]) -> Dict[str, List[str]]:
    """G7 GATE: Enforce WHY ≥ 1 AND WHY-NOT ≥ 1"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        bullets = card.get("bullets", [])

        why_count = sum(1 for b in bullets if b.get("direction") == "WHY")
        why_not_count = sum(1 for b in bullets if b.get("direction") == "WHY_NOT")

        if why_count == 0:
            violations.append(f"{insurer}: No WHY bullets (FAIL)")
        if why_not_count == 0:
            violations.append(f"{insurer}: No WHY_NOT bullets (FAIL)")

    return {"g7_balanced_card": violations}


def check_g8_no_promotion(cards: List[dict]) -> Dict[str, List[str]]:
    """G8 GATE: No emotional/promotional language"""
    violations = []

    # Forbidden emotional words
    forbidden_emotional = [
        r'매우', r'아주', r'정말', r'굉장히',
        r'최고', r'최상', r'베스트',
        r'추천', r'권장', r'강력'
    ]

    # Numbers (already checked, but re-verify)
    number_patterns = [
        r'\d+\s*일',
        r'\d+\s*만원',
        r'\d+\s*원',
        r'\d+\s*%',
        r'\d+\s*년',
        r'\d+\s*개월'
    ]

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            claim = bullet.get("claim", "")

            # Check emotional expressions
            for pattern in forbidden_emotional:
                if re.search(pattern, claim):
                    violations.append(f"{insurer}: Emotional word in '{claim}'")
                    break

            # Check numbers
            for pattern in number_patterns:
                if re.search(pattern, claim):
                    violations.append(f"{insurer}: Number in '{claim}'")
                    break

    return {"g8_no_promotion": violations}


def check_why_not_fact_based(cards: List[dict]) -> Dict[str, List[str]]:
    """WHY-NOT must be factual (existence), not comparative"""
    violations = []

    # Forbidden comparative words in WHY-NOT
    # (These are allowed in WHY, but not WHY-NOT)
    forbidden_in_why_not = [
        r'더\s+\w+',  # "더 많다", "더 적다"
        r'보다',      # "~보다"
        r'최고', r'최저', r'최대', r'최소',
    ]

    # Required factual patterns in WHY-NOT
    factual_keywords = [
        "존재함", "제외됨", "제한", "조건", "명시됨", "제약"
    ]

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            if bullet.get("direction") != "WHY_NOT":
                continue

            claim = bullet.get("claim", "")

            # Check for forbidden comparatives
            for pattern in forbidden_in_why_not:
                if re.search(pattern, claim):
                    violations.append(f"{insurer}: Comparative in WHY-NOT: '{claim}'")
                    break

            # Check for factual keywords (at least one should exist)
            has_factual = any(kw in claim for kw in factual_keywords)
            if not has_factual:
                violations.append(f"{insurer}: WHY-NOT not fact-based: '{claim}'")

    return {"why_not_fact_based": violations}


def check_confidence_high_only(cards: List[dict]) -> Dict[str, List[str]]:
    """STEP NEXT-M requires HIGH confidence only"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            confidence = bullet.get("confidence")
            if confidence != "HIGH":
                claim = bullet.get("claim", "unknown")
                violations.append(f"{insurer}: Not HIGH confidence in '{claim}' (got: {confidence})")

    return {"confidence_high_only": violations}


def check_evidence_refs(cards: List[dict]) -> Dict[str, List[str]]:
    """All bullets must have evidence refs"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            refs = bullet.get("evidence_refs", [])
            if not refs or len(refs) == 0:
                claim = bullet.get("claim", "unknown")
                violations.append(f"{insurer}: No evidence_refs for '{claim}'")

    return {"evidence_refs_required": violations}


def check_max_bullets(cards: List[dict]) -> Dict[str, List[str]]:
    """Max 3 bullets per card"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        bullets = card.get("bullets", [])
        if len(bullets) > 3:
            violations.append(f"{insurer}: {len(bullets)} bullets (max 3)")

    return {"max_bullets": violations}


def check_deterministic(cards: List[dict]) -> Dict[str, List[str]]:
    """Each insurer appears once"""
    violations = []

    insurer_counts = {}
    for card in cards:
        insurer = card["insurer_key"]
        insurer_counts[insurer] = insurer_counts.get(insurer, 0) + 1

    for insurer, count in insurer_counts.items():
        if count > 1:
            violations.append(f"{insurer}: appears {count} times")

    return {"deterministic": violations}


def main():
    if len(sys.argv) < 2:
        print("Usage: step_next_m_validate.py <cards_jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # Read cards
    cards = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    print(f"Loaded {len(cards)} cards from {input_path}")

    # Run all checks
    results = {}
    results.update(check_g7_balanced_card(cards))
    results.update(check_g8_no_promotion(cards))
    results.update(check_why_not_fact_based(cards))
    results.update(check_confidence_high_only(cards))
    results.update(check_evidence_refs(cards))
    results.update(check_max_bullets(cards))
    results.update(check_deterministic(cards))

    # Summary
    total_violations = sum(len(v) for v in results.values())

    print("\n" + "="*60)
    print("VALIDATION RESULTS (STEP NEXT-M)")
    print("="*60)

    all_pass = True
    for check_name, violations in results.items():
        status = "✅ PASS" if not violations else "❌ FAIL"
        print(f"{check_name:30s}: {status} ({len(violations)} violations)")
        if violations:
            all_pass = False
            for v in violations[:5]:
                print(f"  - {v}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")

    print("="*60)

    # Statistics
    total_bullets = sum(len(c.get("bullets", [])) for c in cards)
    why_count = sum(1 for c in cards for b in c.get("bullets", []) if b.get("direction") == "WHY")
    why_not_count = sum(1 for c in cards for b in c.get("bullets", []) if b.get("direction") == "WHY_NOT")

    print(f"\nBalance Statistics:")
    print(f"  Total cards: {len(cards)}")
    print(f"  Total bullets: {total_bullets}")
    print(f"  WHY: {why_count} ({why_count/total_bullets*100:.1f}%)")
    print(f"  WHY-NOT: {why_not_count} ({why_not_count/total_bullets*100:.1f}%)")

    # Write validation report
    output_path = input_path.parent.parent / "docs" / "audit" / "step_next_m_validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "input_file": str(input_path),
        "total_cards": len(cards),
        "total_bullets": total_bullets,
        "why_count": why_count,
        "why_not_count": why_not_count,
        "checks": {
            k: {
                "pass": len(v) == 0,
                "violation_count": len(v),
                "violations": v[:10]
            }
            for k, v in results.items()
        },
        "overall_pass": all_pass
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📋 Validation report: {output_path}")

    if all_pass:
        print("\n✅ ALL CHECKS PASSED (G7 + G8 + L-checks)")
        sys.exit(0)
    else:
        print(f"\n❌ {total_violations} VIOLATIONS FOUND")
        sys.exit(2)


if __name__ == "__main__":
    main()
