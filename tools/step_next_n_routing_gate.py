#!/usr/bin/env python3
"""
STEP NEXT-N: G9 Question Routing Gate
Enforce question → card type mapping to prevent misuse

CONSTITUTION:
- One question → One allowed card type
- Customer-facing = BALANCED_EXPLAIN only
- G9 gate enforces routing policy
- No numeric direct comparison
- No arbitrary card combinations
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional


class GateViolationError(Exception):
    """Raised when G9 gate check fails"""
    pass


class G9QuestionRoutingGate:
    """Enforce question → card type routing policy"""

    def __init__(self, routing_registry_path: Path):
        with open(routing_registry_path) as f:
            self.registry = json.load(f)
        self.routing_rules = self.registry["routing_rules"]

    def validate(self, question_id: str, cards: List[dict]) -> None:
        """
        Validate cards against routing policy for question

        Raises:
            GateViolationError if validation fails
        """
        # Check 1: Question ID exists
        if question_id not in self.routing_rules:
            raise GateViolationError(
                f"G9 FAIL: Unknown question_id '{question_id}'"
            )

        policy = self.routing_rules[question_id]

        # Check each card
        for card in cards:
            self._validate_card(card, policy, question_id)

    def _validate_card(self, card: dict, policy: dict, question_id: str) -> None:
        """Validate single card against policy"""

        # Infer card type from structure
        bullets = card.get("bullets", [])
        card_type = self._infer_card_type(bullets)

        # Check 2: Card type is allowed
        allowed_types = policy["allowed_card_types"]
        if card_type not in allowed_types:
            raise GateViolationError(
                f"G9 FAIL: Card type '{card_type}' not allowed for {question_id}. "
                f"Allowed: {allowed_types}"
            )

        # Check 3: Forbidden card types
        forbidden_types = policy.get("forbidden_card_types", [])
        if card_type in forbidden_types:
            raise GateViolationError(
                f"G9 FAIL: Card type '{card_type}' is forbidden for {question_id}"
            )

        # Check 4: WHY count minimum
        why_count = sum(1 for b in bullets if b.get("direction") == "WHY")
        min_why = policy.get("min_why", 1)
        if why_count < min_why:
            raise GateViolationError(
                f"G9 FAIL: WHY count {why_count} < minimum {min_why} for {question_id}"
            )

        # Check 5: WHY-NOT count minimum
        why_not_count = sum(1 for b in bullets if b.get("direction") == "WHY_NOT")
        min_why_not = policy.get("min_why_not", 1)
        if why_not_count < min_why_not:
            raise GateViolationError(
                f"G9 FAIL: WHY-NOT count {why_not_count} < minimum {min_why_not} for {question_id}"
            )

        # Check 6: Evidence required (if specified)
        special_rules = policy.get("special_rules", {})
        if special_rules.get("evidence_required", True):
            for bullet in bullets:
                refs = bullet.get("evidence_refs", [])
                if not refs or len(refs) == 0:
                    claim = bullet.get("claim", "unknown")
                    raise GateViolationError(
                        f"G9 FAIL: Missing evidence_refs for bullet: {claim}"
                    )

        # Check 7: No numeric output (if specified)
        if not special_rules.get("numeric_output", False):
            self._check_no_numeric_output(bullets)

    def _infer_card_type(self, bullets: List[dict]) -> str:
        """Infer card type from bullet structure"""
        if not bullets:
            return "UNKNOWN"

        why_count = sum(1 for b in bullets if b.get("direction") == "WHY")
        why_not_count = sum(1 for b in bullets if b.get("direction") == "WHY_NOT")

        if why_count >= 1 and why_not_count >= 1:
            return "BALANCED_EXPLAIN"
        elif why_count > 0 and why_not_count == 0:
            return "WHY_ONLY"
        else:
            return "UNKNOWN"

    def _check_no_numeric_output(self, bullets: List[dict]) -> None:
        """Check that claims don't contain numeric values"""
        import re

        forbidden_patterns = [
            r'\d+\s*만원',
            r'\d+\s*원',
            r'\d+\s*일',
            r'\d+\s*%',
            r'\d+\s*년',
            r'\d+\s*개월'
        ]

        for bullet in bullets:
            claim = bullet.get("claim", "")
            for pattern in forbidden_patterns:
                if re.search(pattern, claim):
                    raise GateViolationError(
                        f"G9 FAIL: Numeric output forbidden: '{claim}'"
                    )

    def get_policy(self, question_id: str) -> Optional[dict]:
        """Get routing policy for question"""
        return self.routing_rules.get(question_id)


def main():
    """
    CLI for G9 gate validation

    Usage:
        python3 step_next_n_routing_gate.py <question_id> <cards_jsonl>
    """
    if len(sys.argv) < 3:
        print("Usage: step_next_n_routing_gate.py <question_id> <cards_jsonl>")
        sys.exit(1)

    question_id = sys.argv[1]
    cards_path = Path(sys.argv[2])

    # Load routing registry
    registry_path = Path(__file__).parent.parent / "data" / "policy" / "question_card_routing.json"
    gate = G9QuestionRoutingGate(registry_path)

    # Load cards
    cards = []
    with open(cards_path) as f:
        for line in f:
            if line.strip():
                cards.append(json.loads(line))

    print(f"Loaded {len(cards)} cards from {cards_path}")
    print(f"Validating for question: {question_id}")

    # Validate
    try:
        gate.validate(question_id, cards)
        print(f"\n✅ G9 GATE PASS: All cards valid for {question_id}")

        # Show policy
        policy = gate.get_policy(question_id)
        print(f"\nApplied Policy:")
        print(f"  Allowed types: {policy['allowed_card_types']}")
        print(f"  Min WHY: {policy['min_why']}")
        print(f"  Min WHY-NOT: {policy['min_why_not']}")
        print(f"  Forbidden types: {policy.get('forbidden_card_types', [])}")

        sys.exit(0)

    except GateViolationError as e:
        print(f"\n❌ {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
