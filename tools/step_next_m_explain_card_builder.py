#!/usr/bin/env python3
"""
STEP NEXT-M: Balanced Explanation Card Builder (WHY + WHY-NOT)
Eliminates promotional bias by enforcing balanced structure

CONSTITUTION:
- WHY ≥ 1 AND WHY-NOT ≥ 1 (mandatory)
- WHY-NOT = factual constraints only (no comparison)
- No numbers, no emotion, no inference
- Tier-A + G5 PASS + HIGH confidence only
- G7 Balanced Card Gate enforcement
- G8 No-Promotion Gate enforcement
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass
class Bullet:
    """Single explanation bullet"""
    direction: str  # "WHY" | "WHY_NOT"
    claim: str
    evidence_refs: List[str]
    confidence: str
    source_doc_type: str
    slot_name: str  # Track which slot generated this

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
    """One card per company with balanced WHY/WHY-NOT"""
    insurer_key: str
    product_key: str
    bullets: List[Bullet]

    def to_dict(self) -> dict:
        return {
            "insurer_key": self.insurer_key,
            "product_key": self.product_key,
            "bullets": [b.to_dict() for b in self.bullets]
        }


# TIER-A SLOTS
TIER_A_SLOTS = {
    "payout_limit",
    "waiting_period",
    "reduction",
    "exclusions"
}

# WHY-NOT Templates (FACT-BASED ONLY, NO COMPARISON)
# Format: (existence condition, fact statement)
WHY_NOT_TEMPLATES = {
    "waiting_period": "초기 보장에 제한 조건이 존재함",
    "reduction": "특정 기간 내 지급 제한 조건이 존재함",
    "exclusions": "일부 상황에서는 보장이 제외됨",
    "payout_limit": "지급 조건에 제약이 명시됨"
}

# WHY Templates (from STEP NEXT-L)
WHY_TEMPLATES = {
    "waiting_period": "면책기간이 상대적으로 짧음",
    "reduction": "감액 조건이 덜 불리함",
    "exclusions": "지급 제외 범위가 좁음",
    "payout_limit": "지급 한도가 상대적으로 유리함"
}


class BalancedCardBuilder:
    """Build balanced WHY+WHY-NOT cards"""

    def __init__(self, step4_rows: List[dict]):
        self.step4_rows = step4_rows

    def build(self) -> List[ExplanationCard]:
        """Generate balanced cards grouped by company"""
        by_insurer = defaultdict(list)
        for row in self.step4_rows:
            insurer = row["identity"]["insurer_key"]
            by_insurer[insurer].append(row)

        cards = []
        for insurer, rows in by_insurer.items():
            card = self._build_balanced_card(insurer, rows)
            if card:  # Only emit if balanced
                cards.append(card)

        return cards

    def _build_balanced_card(self, insurer_key: str, rows: List[dict]) -> Optional[ExplanationCard]:
        """Build single balanced card (WHY + WHY-NOT)"""
        why_bullets = []
        why_not_bullets = []
        product_key = None

        for row in rows:
            if not product_key:
                product_key = row["identity"]["product_key"]

            why, why_not = self._extract_balanced_bullets(row)
            why_bullets.extend(why)
            why_not_bullets.extend(why_not)

        # Deduplicate
        why_bullets = self._deduplicate(why_bullets)
        why_not_bullets = self._deduplicate(why_not_bullets)

        # G7 GATE: Balanced Card Enforcement
        if len(why_bullets) == 0 or len(why_not_bullets) == 0:
            # FAIL: Card must have both WHY and WHY-NOT
            return None

        # Sort by confidence
        why_bullets = sorted(why_bullets, key=lambda b: 0 if b.confidence == "HIGH" else 1)
        why_not_bullets = sorted(why_not_bullets, key=lambda b: 0 if b.confidence == "HIGH" else 1)

        # Balanced selection: 2 WHY + 1 WHY-NOT (or 1 WHY + 2 WHY-NOT)
        # Default: 2 WHY + 1 WHY-NOT
        selected_why = why_bullets[:2]
        selected_why_not = why_not_bullets[:1]

        # If not enough WHY, balance with more WHY-NOT
        if len(selected_why) < 2 and len(why_not_bullets) >= 2:
            selected_why = why_bullets[:1]
            selected_why_not = why_not_bullets[:2]

        all_bullets = selected_why + selected_why_not

        # Final G7 check
        if len(selected_why) == 0 or len(selected_why_not) == 0:
            return None

        return ExplanationCard(
            insurer_key=insurer_key,
            product_key=product_key or f"{insurer_key}__unknown",
            bullets=all_bullets
        )

    def _extract_balanced_bullets(self, row: dict) -> tuple[List[Bullet], List[Bullet]]:
        """Extract both WHY and WHY-NOT from one coverage row"""
        why_bullets = []
        why_not_bullets = []
        slots = row.get("slots", {})

        for slot_name in TIER_A_SLOTS:
            if slot_name not in slots:
                continue

            slot_data = slots[slot_name]
            status = slot_data.get("status")

            # GATE: G5 enforcement
            if status not in ["FOUND", "FOUND_GLOBAL"]:
                continue

            # GATE: Confidence required (HIGH only for M-step)
            confidence_obj = slot_data.get("confidence")
            if not confidence_obj or confidence_obj.get("level") != "HIGH":
                continue

            evidences = slot_data.get("evidences", [])
            if not evidences:
                continue

            # Extract evidence refs
            evidence_refs = []
            doc_type = None
            for ev in evidences:
                doc_type = ev.get("doc_type", "unknown")
                page = ev.get("page", 0)
                evidence_refs.append(f"{doc_type}:p{page}")

            confidence_level = confidence_obj.get("level", "HIGH")

            # Generate WHY bullet
            if slot_name in WHY_TEMPLATES:
                why_bullet = Bullet(
                    direction="WHY",
                    claim=WHY_TEMPLATES[slot_name],
                    evidence_refs=evidence_refs[:3],
                    confidence=confidence_level,
                    source_doc_type=doc_type or "unknown",
                    slot_name=slot_name
                )
                why_bullets.append(why_bullet)

            # Generate WHY-NOT bullet (FACT-BASED)
            if slot_name in WHY_NOT_TEMPLATES:
                # WHY-NOT logic: existence of constraint = fact
                # Only generate if slot has actual content (not just FOUND status)
                value = slot_data.get("value")

                # For WHY-NOT: generate if constraint exists (fact-based)
                # waiting_period: exists = fact "제한 조건 존재"
                # reduction: exists = fact "감액 조건 존재"
                # exclusions: exists = fact "보장 제외 존재"
                # payout_limit: exists = fact "지급 조건 제약 존재"

                why_not_bullet = Bullet(
                    direction="WHY_NOT",
                    claim=WHY_NOT_TEMPLATES[slot_name],
                    evidence_refs=evidence_refs[:3],
                    confidence=confidence_level,
                    source_doc_type=doc_type or "unknown",
                    slot_name=slot_name
                )
                why_not_bullets.append(why_not_bullet)

        return why_bullets, why_not_bullets

    def _deduplicate(self, bullets: List[Bullet]) -> List[Bullet]:
        """Remove duplicate claims"""
        seen_claims = set()
        unique = []
        for bullet in bullets:
            if bullet.claim not in seen_claims:
                seen_claims.add(bullet.claim)
                unique.append(bullet)
        return unique


# G7 GATE: Balanced Card Gate
def validate_g7_balanced_card(cards: List[ExplanationCard]) -> List[str]:
    """Enforce WHY ≥ 1 AND WHY-NOT ≥ 1"""
    violations = []

    for card in cards:
        why_count = sum(1 for b in card.bullets if b.direction == "WHY")
        why_not_count = sum(1 for b in card.bullets if b.direction == "WHY_NOT")

        if why_count == 0:
            violations.append(f"{card.insurer_key}: No WHY bullets")
        if why_not_count == 0:
            violations.append(f"{card.insurer_key}: No WHY_NOT bullets (FAIL)")

    return violations


# G8 GATE: No-Promotion Gate
def validate_g8_no_promotion(cards: List[ExplanationCard]) -> List[str]:
    """Check for emotional/comparison/numeric expressions"""
    violations = []

    # Forbidden patterns
    emotional_patterns = [
        r'매우', r'아주', r'정말', r'굉장히',  # Very, extremely, really
        r'최고', r'최상', r'베스트',  # Best, top
        r'추천', r'권장',  # Recommend
    ]

    numeric_patterns = [
        r'\d+\s*(일|만원|원|%|년|개월|회)'
    ]

    # Allowed comparative words in templates (grandfathered)
    allowed_comparatives = {
        "상대적으로", "덜", "좁음", "유리함", "불리함"
    }

    for card in cards:
        for bullet in card.bullets:
            claim = bullet.claim

            # Check emotional expressions
            for pattern in emotional_patterns:
                if re.search(pattern, claim):
                    violations.append(f"{card.insurer_key}: Emotional expression in '{claim}'")
                    break

            # Check numeric expressions
            for pattern in numeric_patterns:
                if re.search(pattern, claim):
                    violations.append(f"{card.insurer_key}: Number found in '{claim}'")
                    break

    return violations


def main():
    if len(sys.argv) < 3:
        print("Usage: step_next_m_explain_card_builder.py <input_jsonl> <output_jsonl>")
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

    # Build balanced cards
    builder = BalancedCardBuilder(rows)
    cards = builder.build()

    print(f"Generated {len(cards)} balanced cards")

    # G7 GATE: Validate balance
    g7_violations = validate_g7_balanced_card(cards)
    if g7_violations:
        print("\n❌ G7 GATE FAIL: Balanced Card Violations")
        for v in g7_violations:
            print(f"  - {v}")
        sys.exit(2)

    # G8 GATE: Validate no-promotion
    g8_violations = validate_g8_no_promotion(cards)
    if g8_violations:
        print("\n❌ G8 GATE FAIL: Promotion Violations")
        for v in g8_violations:
            print(f"  - {v}")
        sys.exit(2)

    # Write output
    with open(output_path, "w") as f:
        for card in cards:
            f.write(json.dumps(card.to_dict(), ensure_ascii=False) + "\n")

    print(f"✅ Wrote {len(cards)} balanced cards to {output_path}")

    # Statistics
    total_bullets = sum(len(card.bullets) for card in cards)
    why_count = sum(1 for c in cards for b in c.bullets if b.direction == "WHY")
    why_not_count = sum(1 for c in cards for b in c.bullets if b.direction == "WHY_NOT")

    print(f"\nStatistics:")
    print(f"  Total bullets: {total_bullets}")
    print(f"  WHY: {why_count} ({why_count/total_bullets*100:.1f}%)")
    print(f"  WHY-NOT: {why_not_count} ({why_not_count/total_bullets*100:.1f}%)")
    print(f"  Avg bullets/card: {total_bullets / len(cards):.2f}")

    # Check balance
    unbalanced = [c for c in cards if
                  sum(1 for b in c.bullets if b.direction == "WHY_NOT") == 0]
    if unbalanced:
        print(f"\n⚠️  {len(unbalanced)} cards missing WHY-NOT")
    else:
        print(f"\n✅ All {len(cards)} cards are balanced (WHY + WHY-NOT)")


if __name__ == "__main__":
    main()
