"""
STEP NEXT-63: Example 3 - Two-Insurer Comparison (Samsung vs Meritz)

LLM OFF: Side-by-side comparison with deterministic summary

Input:
- Two insurers
- coverage_code

Output:
- Comparison table (side-by-side)
- 3-line summary (fixed template):
  1. Amount: same/different
  2. Payment type: same/different
  3. Conditions: same/different
- All fields linked to evidence

Gates:
- join_rate == 1.0 (both insurers must have the coverage)
- evidence_fill_rate >= 0.8
- Numeric fields must be numeric only
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from pipeline.step8_render_deterministic.templates import DeterministicTemplates


class TwoInsurerComparer:
    """Deterministic two-insurer comparison (NO LLM)"""

    def __init__(self, cards_dir: Path = Path("data/compare"), use_slim: bool = True):
        self.cards_dir = cards_dir
        self.templates = DeterministicTemplates()
        self.use_slim = use_slim  # STEP NEXT-73R: Prefer slim cards

    def load_coverage_cards(self, insurer: str) -> List[Dict[str, Any]]:
        """
        Load coverage cards (SSOT)

        STEP NEXT-73R: Try slim cards first, fallback to legacy
        """
        # Try slim cards first
        if self.use_slim:
            slim_file = self.cards_dir / f"{insurer}_coverage_cards_slim.jsonl"
            if slim_file.exists():
                cards = []
                with open(slim_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        cards.append(json.loads(line))
                return cards

        # Fallback to legacy cards
        cards_file = self.cards_dir / f"{insurer}_coverage_cards.jsonl"
        if not cards_file.exists():
            return []

        cards = []
        with open(cards_file, 'r', encoding='utf-8') as f:
            for line in f:
                cards.append(json.loads(line))
        return cards

    def find_coverage(self, cards: List[Dict[str, Any]], coverage_code: str) -> Optional[Dict[str, Any]]:
        """Find card by coverage_code"""
        for card in cards:
            if card.get("coverage_code") == coverage_code:
                return card
        return None

    def extract_amount_text(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """Extract amount from evidence snippets"""
        import re
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*만\s*원',
            r'(\d+)\s*천\s*만\s*원',
            r'(\d+)\s*억\s*원'
        ]

        for ev in evidences:
            snippet = ev.get("snippet", "")
            for pattern in patterns:
                match = re.search(pattern, snippet)
                if match:
                    return match.group(0)
        return None

    def extract_payment_type(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """Extract payment type"""
        keywords = ["정액", "실손", "비례보상", "최초1회한", "일시금"]

        for ev in evidences:
            snippet = ev.get("snippet", "")
            for keyword in keywords:
                if keyword in snippet:
                    return keyword
        return None

    def build_evidence_refs(self, evidences: List[Dict[str, Any]]) -> List[str]:
        """Build evidence reference list"""
        refs = []
        for ev in evidences[:3]:
            doc_type = ev.get("doc_type", "")
            page = ev.get("page", "")
            ref = f"{doc_type} p.{page}" if page else doc_type
            refs.append(ref)
        return refs

    def compare_two_insurers(self, insurer1: str, insurer2: str,
                            coverage_code: str) -> Dict[str, Any]:
        """
        Compare coverage between two insurers

        Returns:
        {
            "coverage_code": "...",
            "comparison_table": {...},
            "summary": [...],
            "gates": {...}
        }
        """
        # Load cards
        cards1 = self.load_coverage_cards(insurer1)
        cards2 = self.load_coverage_cards(insurer2)

        card1 = self.find_coverage(cards1, coverage_code)
        card2 = self.find_coverage(cards2, coverage_code)

        # Gate 1: join_rate == 1.0 (both must exist)
        if not card1 or not card2:
            return {
                "coverage_code": coverage_code,
                "status": "FAIL",
                "reason": f"join_rate != 1.0 (missing: {insurer1 if not card1 else insurer2})"
            }

        # Extract fields
        evidences1 = card1.get("evidences", [])
        evidences2 = card2.get("evidences", [])

        # STEP NEXT-UI-FIX-04: Use proposal_facts first, fallback to evidence extraction
        proposal_facts1 = card1.get("proposal_facts", {}) or {}
        proposal_facts2 = card2.get("proposal_facts", {}) or {}

        amount1 = proposal_facts1.get("coverage_amount_text") or self.extract_amount_text(evidences1)
        amount2 = proposal_facts2.get("coverage_amount_text") or self.extract_amount_text(evidences2)

        payment1 = self.extract_payment_type(evidences1)
        payment2 = self.extract_payment_type(evidences2)

        # STEP NEXT-73R: Get refs from slim cards (if available), otherwise build from evidences
        refs1_obj = card1.get("refs", {})
        refs2_obj = card2.get("refs", {})

        proposal_detail_ref1 = refs1_obj.get("proposal_detail_ref")
        proposal_detail_ref2 = refs2_obj.get("proposal_detail_ref")

        evidence_refs1 = refs1_obj.get("evidence_refs", [])
        evidence_refs2 = refs2_obj.get("evidence_refs", [])

        # Fallback to legacy evidence refs (for backward compat)
        if not evidence_refs1:
            evidence_refs1 = self.build_evidence_refs(evidences1)
        if not evidence_refs2:
            evidence_refs2 = self.build_evidence_refs(evidences2)

        # Gate 2: evidence_fill_rate >= 0.8
        total_fields = 4  # amount, payment, refs (2x)
        filled_fields = sum([
            1 if amount1 else 0,
            1 if amount2 else 0,
            1 if payment1 else 0,
            1 if payment2 else 0
        ])
        evidence_fill_rate = filled_fields / total_fields

        if evidence_fill_rate < 0.8:
            return {
                "coverage_code": coverage_code,
                "status": "FAIL",
                "reason": f"evidence_fill_rate {evidence_fill_rate:.1%} < 0.8"
            }

        # STEP NEXT-UI-FIX-04: Add premium and period from proposal_facts
        premium1 = proposal_facts1.get("premium_text") or "명시 없음"
        premium2 = proposal_facts2.get("premium_text") or "명시 없음"
        period1 = proposal_facts1.get("period_text") or "명시 없음"
        period2 = proposal_facts2.get("period_text") or "명시 없음"

        # Build comparison table (STEP NEXT-73R: Add proposal_detail_ref)
        comparison_table = {
            insurer1: {
                "amount": amount1 or "명시 없음",
                "premium": premium1,
                "period": period1,
                "payment_type": payment1 or "명시 없음",
                "evidence_refs": evidence_refs1,
                "proposal_detail_ref": proposal_detail_ref1  # STEP NEXT-73R
            },
            insurer2: {
                "amount": amount2 or "명시 없음",
                "premium": premium2,
                "period": period2,
                "payment_type": payment2 or "명시 없음",
                "evidence_refs": evidence_refs2,
                "proposal_detail_ref": proposal_detail_ref2  # STEP NEXT-73R
            }
        }

        # Build 3-line summary (deterministic templates)
        summary = []

        # 1. Amount comparison
        if amount1 and amount2:
            summary.append(self.templates.comparison_summary_amount([amount1, amount2]))
        else:
            summary.append("금액: 비교 불가 (일부 데이터 없음)")

        # 2. Payment type comparison
        if payment1 and payment2:
            summary.append(self.templates.comparison_summary_payment_type([payment1, payment2]))
        else:
            summary.append("지급유형: 비교 불가 (일부 데이터 없음)")

        # 3. Conditions comparison
        summary.append(self.templates.comparison_summary_conditions([
            str(evidences1), str(evidences2)
        ]))

        return {
            "coverage_code": coverage_code,
            "status": "success",
            "comparison_table": comparison_table,
            "summary": summary,
            "gates": {
                "join_rate": 1.0,
                "evidence_fill_rate": evidence_fill_rate
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Example 3: Two-Insurer Comparison (LLM OFF)")
    parser.add_argument("--insurer1", required=True, help="First insurer")
    parser.add_argument("--insurer2", required=True, help="Second insurer")
    parser.add_argument("--coverage-code", required=True, help="Coverage code")
    parser.add_argument("--output", type=Path, default=Path("output/example3_two_insurer_compare.json"),
                       help="Output JSON file")
    args = parser.parse_args()

    comparer = TwoInsurerComparer()
    result = comparer.compare_two_insurers(args.insurer1, args.insurer2, args.coverage_code)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Example 3 output: {args.output}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Gates: join_rate={result['gates']['join_rate']}, "
              f"evidence_fill_rate={result['gates']['evidence_fill_rate']:.1%}")


if __name__ == "__main__":
    main()
