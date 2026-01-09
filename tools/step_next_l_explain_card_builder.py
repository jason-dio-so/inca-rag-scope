#!/usr/bin/env python3
"""
STEP NEXT-L: Customer Explanation Card Builder
Generates "Why/Why-Not" cards from Step4 output
Evidence-based, no-number reasoning

CONSTITUTION:
- No numbers in output (금액/일수/비율 금지)
- Tier-A slots only (payout_limit, waiting_period, reduction, exclusions)
- G5 PASS required (unattributed values rejected)
- Confidence required (HIGH/MEDIUM only, no NONE)
- Template-based (NO LLM, NO inference)
- Deterministic deduplication
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Bullet:
    """Single explanation bullet"""
    direction: str  # "WHY" | "WHY_NOT"
    claim: str
    evidence_refs: List[str]  # ["doc_id:page", ...]
    confidence: str  # "HIGH" | "MEDIUM"
    source_doc_type: str

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "claim": self.claim,
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
            "source_doc_type": self.source_doc_type
        }


@dataclass
class ExplanationCard:
    """One card per company"""
    insurer_key: str
    product_key: str
    bullets: List[Bullet]

    def to_dict(self) -> dict:
        return {
            "insurer_key": self.insurer_key,
            "product_key": self.product_key,
            "bullets": [b.to_dict() for b in self.bullets]
        }


# TIER-A SLOTS (from SLOT_TIER_POLICY.md)
TIER_A_SLOTS = {
    "payout_limit",
    "waiting_period",
    "reduction",
    "exclusions"
}

# Template mapping: slot → (WHY claim, WHY_NOT claim)
TEMPLATES = {
    "waiting_period": (
        "면책기간이 상대적으로 짧음",
        "면책 조건이 불리함"
    ),
    "reduction": (
        "감액 조건이 덜 불리함",
        "감액 조건이 불리함"
    ),
    "exclusions": (
        "지급 제외 범위가 좁음",
        "제외 범위가 넓음"
    ),
    "payout_limit": (
        "지급 한도가 상대적으로 유리함",
        "지급 한도가 상대적으로 불리함"
    )
}


class ExplanationCardBuilder:
    """Build explanation cards from Step4 output"""

    def __init__(self, step4_rows: List[dict]):
        self.step4_rows = step4_rows

    def build(self) -> List[ExplanationCard]:
        """Generate cards grouped by company"""
        # Group rows by insurer
        by_insurer = defaultdict(list)
        for row in self.step4_rows:
            insurer = row["identity"]["insurer_key"]
            by_insurer[insurer].append(row)

        cards = []
        for insurer, rows in by_insurer.items():
            card = self._build_card_for_insurer(insurer, rows)
            if card.bullets:  # Only emit if bullets exist
                cards.append(card)

        return cards

    def _build_card_for_insurer(self, insurer_key: str, rows: List[dict]) -> ExplanationCard:
        """Build single card for one insurer"""
        # Collect all bullets from all coverages
        all_bullets = []
        product_key = None

        for row in rows:
            if not product_key:
                product_key = row["identity"]["product_key"]

            bullets = self._extract_bullets_from_row(row)
            all_bullets.extend(bullets)

        # Deduplicate and rank
        bullets = self._deduplicate_and_rank(all_bullets)

        # Limit to 3
        bullets = bullets[:3]

        return ExplanationCard(
            insurer_key=insurer_key,
            product_key=product_key or f"{insurer_key}__unknown",
            bullets=bullets
        )

    def _extract_bullets_from_row(self, row: dict) -> List[Bullet]:
        """Extract bullets from one coverage row"""
        bullets = []
        slots = row.get("slots", {})

        for slot_name in TIER_A_SLOTS:
            if slot_name not in slots:
                continue

            slot_data = slots[slot_name]

            # GATE: G5 enforcement (must have status=FOUND or FOUND_GLOBAL)
            status = slot_data.get("status")
            if status not in ["FOUND", "FOUND_GLOBAL"]:
                continue

            # GATE: Confidence required (HIGH/MEDIUM only)
            confidence_obj = slot_data.get("confidence")
            if not confidence_obj or confidence_obj.get("level") not in ["HIGH", "MEDIUM"]:
                continue

            # GATE: Evidence must exist
            evidences = slot_data.get("evidences", [])
            if not evidences:
                continue

            # Determine direction (simple heuristic: if value exists = WHY, else = WHY_NOT)
            # For this implementation, we default to WHY if slot is FOUND
            direction = "WHY"  # Default for now

            # Get template
            if slot_name not in TEMPLATES:
                continue

            why_claim, why_not_claim = TEMPLATES[slot_name]
            claim = why_claim if direction == "WHY" else why_not_claim

            # Extract evidence refs
            evidence_refs = []
            doc_type = None
            for ev in evidences:
                doc_type = ev.get("doc_type", "unknown")
                page = ev.get("page", 0)
                evidence_refs.append(f"{doc_type}:p{page}")

            # Use highest confidence doc type
            confidence_level = confidence_obj.get("level", "MEDIUM")

            bullet = Bullet(
                direction=direction,
                claim=claim,
                evidence_refs=evidence_refs[:3],  # Limit to 3 refs
                confidence=confidence_level,
                source_doc_type=doc_type or "unknown"
            )
            bullets.append(bullet)

        return bullets

    def _deduplicate_and_rank(self, bullets: List[Bullet]) -> List[Bullet]:
        """Remove duplicates and rank by priority"""
        # Deduplicate by claim text
        seen_claims = set()
        unique_bullets = []

        for bullet in bullets:
            if bullet.claim not in seen_claims:
                seen_claims.add(bullet.claim)
                unique_bullets.append(bullet)

        # Sort: WHY first, then by confidence (HIGH > MEDIUM)
        def sort_key(b: Bullet) -> tuple:
            direction_priority = 0 if b.direction == "WHY" else 1
            confidence_priority = 0 if b.confidence == "HIGH" else 1
            return (direction_priority, confidence_priority)

        unique_bullets.sort(key=sort_key)

        return unique_bullets


def validate_no_numbers(card: ExplanationCard) -> List[str]:
    """Check for forbidden numeric values"""
    violations = []
    for bullet in card.bullets:
        # Simple regex: any digit followed by common units
        import re
        claim = bullet.claim
        # Forbidden patterns: 90일, 3000만원, 50%, etc.
        if re.search(r'\d+\s*(일|만원|원|%|년|개월)', claim):
            violations.append(f"Number found in claim: {claim}")
    return violations


def validate_tier_a_only(bullets: List[Bullet]) -> List[str]:
    """Ensure only Tier-A slots were used"""
    # This is structural: builder only uses TIER_A_SLOTS
    # No runtime check needed (enforced by code)
    return []


def validate_g5_pass(bullets: List[Bullet]) -> List[str]:
    """All bullets must come from G5-passing values"""
    # Enforced in _extract_bullets_from_row (status check)
    return []


def validate_confidence_required(bullets: List[Bullet]) -> List[str]:
    """All bullets must have HIGH or MEDIUM confidence"""
    violations = []
    for bullet in bullets:
        if bullet.confidence not in ["HIGH", "MEDIUM"]:
            violations.append(f"Invalid confidence: {bullet.confidence} in claim: {bullet.claim}")
    return violations


def main():
    if len(sys.argv) < 3:
        print("Usage: step_next_l_explain_card_builder.py <input_jsonl> <output_jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    # Read Step4 output
    rows = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    print(f"Loaded {len(rows)} rows from {input_path}")

    # Build cards
    builder = ExplanationCardBuilder(rows)
    cards = builder.build()

    print(f"Generated {len(cards)} explanation cards")

    # Validate
    all_violations = []
    for card in cards:
        violations = validate_no_numbers(card)
        violations += validate_confidence_required(card.bullets)
        if violations:
            all_violations.extend(violations)

    if all_violations:
        print("VALIDATION FAILED:")
        for v in all_violations[:10]:
            print(f"  - {v}")
        sys.exit(2)

    # Write output
    with open(output_path, "w") as f:
        for card in cards:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + "\n")

    print(f"✅ Wrote {len(cards)} cards to {output_path}")

    # Summary stats
    total_bullets = sum(len(card.bullets) for card in cards)
    print(f"Total bullets: {total_bullets}")
    print(f"Avg bullets per card: {total_bullets / len(cards):.2f}")

    # Confidence breakdown
    high_count = sum(1 for c in cards for b in c.bullets if b.confidence == "HIGH")
    medium_count = sum(1 for c in cards for b in c.bullets if b.confidence == "MEDIUM")
    print(f"HIGH confidence: {high_count}")
    print(f"MEDIUM confidence: {medium_count}")


if __name__ == "__main__":
    main()
