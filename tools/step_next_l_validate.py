#!/usr/bin/env python3
"""
STEP NEXT-L: Validation Script
Verify explanation cards meet DoD criteria

Checks:
1. No numbers in claims (금액/일수/비율 = 0건)
2. Only Tier-A slots used (Tier-B/C = 0건)
3. All bullets have evidence_refs (누락 = 0건)
4. All bullets have confidence (HIGH or MEDIUM, 누락 = 0건)
5. Deterministic output (same input = same output)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import re


def check_no_numbers(cards: List[dict]) -> Dict[str, List[str]]:
    """Check for forbidden numeric values in claims"""
    violations = []

    # Patterns that indicate numbers with units
    patterns = [
        r'\d+\s*일',      # 90일
        r'\d+\s*만원',    # 3000만원
        r'\d+\s*원',      # 100원
        r'\d+\s*%',       # 50%
        r'\d+\s*년',      # 1년
        r'\d+\s*개월',    # 3개월
        r'\d+\s*회',      # 2회
    ]

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            claim = bullet.get("claim", "")
            for pattern in patterns:
                if re.search(pattern, claim):
                    violations.append(f"{insurer}: '{claim}' contains number")
                    break

    return {
        "no_numbers": violations
    }


def check_tier_a_only(cards: List[dict]) -> Dict[str, List[str]]:
    """Verify only Tier-A slots were used (structural check)"""
    # This is enforced by builder code structure
    # But we can check if any forbidden slot names appear in evidence
    violations = []

    tier_b_slots = {"entry_age", "start_date", "mandatory_dependency"}
    tier_c_slots = {"underwriting_condition", "payout_frequency", "industry_aggregate_limit"}
    forbidden_slots = tier_b_slots | tier_c_slots

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            claim = bullet.get("claim", "")
            # Simple heuristic: check for keywords
            if "가입 연령" in claim or "보장 개시일" in claim:
                violations.append(f"{insurer}: Tier-B slot detected in claim: {claim}")
            if "유병자" in claim or "지급 빈도" in claim or "누적 한도" in claim:
                violations.append(f"{insurer}: Tier-C slot detected in claim: {claim}")

    return {
        "tier_a_only": violations
    }


def check_evidence_refs(cards: List[dict]) -> Dict[str, List[str]]:
    """All bullets must have at least one evidence reference"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            refs = bullet.get("evidence_refs", [])
            if not refs or len(refs) == 0:
                claim = bullet.get("claim", "unknown")
                violations.append(f"{insurer}: No evidence_refs for claim: {claim}")

    return {
        "evidence_refs_required": violations
    }


def check_confidence_required(cards: List[dict]) -> Dict[str, List[str]]:
    """All bullets must have HIGH or MEDIUM confidence"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        for bullet in card.get("bullets", []):
            confidence = bullet.get("confidence")
            claim = bullet.get("claim", "unknown")

            if not confidence:
                violations.append(f"{insurer}: Missing confidence for claim: {claim}")
            elif confidence not in ["HIGH", "MEDIUM"]:
                violations.append(f"{insurer}: Invalid confidence '{confidence}' for claim: {claim}")

    return {
        "confidence_required": violations
    }


def check_max_bullets(cards: List[dict]) -> Dict[str, List[str]]:
    """Each card should have at most 3 bullets"""
    violations = []

    for card in cards:
        insurer = card["insurer_key"]
        bullets = card.get("bullets", [])
        if len(bullets) > 3:
            violations.append(f"{insurer}: {len(bullets)} bullets (max 3 allowed)")

    return {
        "max_bullets": violations
    }


def check_deterministic(cards: List[dict]) -> Dict[str, List[str]]:
    """Check for basic determinism (same insurer appears once)"""
    violations = []

    insurer_counts = {}
    for card in cards:
        insurer = card["insurer_key"]
        insurer_counts[insurer] = insurer_counts.get(insurer, 0) + 1

    for insurer, count in insurer_counts.items():
        if count > 1:
            violations.append(f"{insurer}: appears {count} times (should be 1)")

    return {
        "deterministic": violations
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: step_next_l_validate.py <cards_jsonl>")
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
    results.update(check_no_numbers(cards))
    results.update(check_tier_a_only(cards))
    results.update(check_evidence_refs(cards))
    results.update(check_confidence_required(cards))
    results.update(check_max_bullets(cards))
    results.update(check_deterministic(cards))

    # Output summary
    total_violations = sum(len(v) for v in results.values())

    print("\n" + "="*60)
    print("VALIDATION RESULTS")
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

    # Write validation report
    output_path = input_path.parent.parent / "docs" / "audit" / "step_next_l_validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "input_file": str(input_path),
        "total_cards": len(cards),
        "total_bullets": sum(len(c.get("bullets", [])) for c in cards),
        "checks": {
            k: {
                "pass": len(v) == 0,
                "violation_count": len(v),
                "violations": v[:10]  # First 10 only
            }
            for k, v in results.items()
        },
        "overall_pass": all_pass
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📋 Validation report written to {output_path}")

    if all_pass:
        print("\n✅ ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ {total_violations} VIOLATIONS FOUND")
        sys.exit(2)


if __name__ == "__main__":
    main()
