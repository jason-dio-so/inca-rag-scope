"""
STEP NEXT-63: Example 2 - Coverage Limit Comparison

LLM OFF: Extract coverage limits from evidence snippets (deterministic)

Input:
- coverage_code (canonical)

Output:
- Insurer-by-insurer table
- Amount / Payment Type / Limit / Conditions
- Evidence references

Gates:
- coverage_code alignment 100%
- If amount parsing fails: null + reason
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from pipeline.step8_render_deterministic.templates import DeterministicTemplates
except ModuleNotFoundError:
    from templates import DeterministicTemplates


class CoverageLimitComparer:
    """Deterministic coverage limit extraction (NO LLM)"""

    def __init__(self, cards_dir: Path = Path("data/compare")):
        self.cards_dir = cards_dir
        self.templates = DeterministicTemplates()

    def load_coverage_cards(self, insurer: str) -> List[Dict[str, Any]]:
        """Load coverage cards (SSOT)"""
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

    def extract_amount(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """Extract amount from evidence snippets (deterministic pattern)"""
        # Pattern: "3,000만원", "5천만원", "1억원" etc.
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
                    return match.group(0)  # Return matched text as-is
        return None

    def extract_payment_type(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract payment type from evidence snippets

        STEP NEXT-UI-FIX-05: Look for payment type keywords in definition sentences
        """
        # Payment type patterns (in priority order)
        payment_patterns = [
            (r'일시금.*지급', '일시금'),
            (r'보험가입금액.*지급', '일시금'),
            (r'정액.*지급', '정액'),
            (r'실손.*보상', '실손'),
            (r'비례.*보상', '비례보상'),
            (r'최초\s*1\s*회\s*한', '최초 1회'),
        ]

        for ev in evidences:
            snippet = ev.get("snippet", "")

            for pattern, label in payment_patterns:
                if re.search(pattern, snippet):
                    return label

        return None

    def extract_limit(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract limit conditions from evidence snippets

        STEP NEXT-UI-FIX-05: Look for frequency/limit keywords
        """
        # Limit patterns (in priority order)
        limit_patterns = [
            r'최초\s*1\s*회',
            r'최초\s*\d+\s*회',
            r'연\s*1\s*회',
            r'연\s*\d+\s*회',
            r'연간\s*\d+\s*회',
            r'평생\s*\d+\s*회',
            r'1\s*회\s*한',
        ]

        for ev in evidences:
            snippet = ev.get("snippet", "")
            for pattern in limit_patterns:
                match = re.search(pattern, snippet)
                if match:
                    return match.group(0)

        return None

    def extract_conditions(self, evidences: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract conditions from evidence snippets (deterministic)

        STEP NEXT-UI-FIX-05: Filter out section numbers and invalid patterns
        """
        # Forbidden patterns (section numbers, article numbers, etc.)
        forbidden_patterns = [
            r'^\d+[-\.]\d+$',  # e.g., "4-1", "3.2"
            r'^제\d+조',       # e.g., "제5조"
            r'^약관\s*\d+',    # e.g., "약관 10"
            r'^\d+$',          # Standalone numbers
            r'^[A-Z]\d+',      # e.g., "A4200"
        ]

        # Condition keywords to look for
        condition_keywords = [
            "면책", "감액", "대기기간", "최초", "경과", "진단확정",
            "90일", "1년", "50%", "회한", "계약일", "책임개시일"
        ]

        for ev in evidences:
            snippet = ev.get("snippet", "").strip()
            if not snippet:
                continue

            # Split into sentences
            sentences = re.split(r'[.\n]', snippet)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check if sentence matches forbidden patterns
                is_forbidden = False
                for pattern in forbidden_patterns:
                    if re.match(pattern, sentence):
                        is_forbidden = True
                        break

                if is_forbidden:
                    continue

                # Check if sentence contains condition keywords
                has_condition_keyword = any(kw in sentence for kw in condition_keywords)

                if has_condition_keyword:
                    return sentence[:100]  # Truncate if too long

        # No valid condition found
        return None

    def compare_coverage_limits(self, insurers: List[str], coverage_code: str) -> Dict[str, Any]:
        """
        Compare coverage limits across insurers

        Returns:
        {
            "coverage_code": "...",
            "rows": [...]
        }
        """
        rows = []

        for insurer in insurers:
            cards = self.load_coverage_cards(insurer)
            card = self.find_coverage(cards, coverage_code)

            if not card:
                # Coverage not found for this insurer
                rows.append(self.templates.coverage_limit_row(
                    insurer=insurer,
                    amount=None,
                    payment_type=None,
                    limit=None,
                    conditions="담보 미존재",
                    evidence_refs=[]
                ))
                continue

            evidences = card.get("evidences", [])

            # STEP NEXT-UI-FIX-04: Use proposal_facts first, fallback to evidence extraction
            proposal_facts = card.get("proposal_facts", {}) or {}

            # Extract fields deterministically (proposal_facts priority)
            amount = proposal_facts.get("coverage_amount_text") or self.extract_amount(evidences)
            payment_type = self.extract_payment_type(evidences)
            limit = self.extract_limit(evidences)
            conditions = self.extract_conditions(evidences)

            # Build evidence references
            evidence_refs = []
            for ev in evidences[:3]:  # Top 3 evidences
                doc_type = ev.get("doc_type", "")
                page = ev.get("page", "")
                ref = f"{doc_type} p.{page}" if page else doc_type
                evidence_refs.append(ref)

            rows.append(self.templates.coverage_limit_row(
                insurer=insurer,
                amount=amount,
                payment_type=payment_type,
                limit=limit,
                conditions=conditions,
                evidence_refs=evidence_refs
            ))

        return {
            "coverage_code": coverage_code,
            "rows": rows
        }


def main():
    parser = argparse.ArgumentParser(description="Example 2: Coverage Limit Comparison (LLM OFF)")
    parser.add_argument("--insurers", nargs="+", required=True,
                       help="List of insurers to compare")
    parser.add_argument("--coverage-code", required=True,
                       help="Canonical coverage code")
    parser.add_argument("--output", type=Path, default=Path("output/example2_coverage_limit.json"),
                       help="Output JSON file")
    args = parser.parse_args()

    comparer = CoverageLimitComparer()
    result = comparer.compare_coverage_limits(args.insurers, args.coverage_code)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Example 2 output: {args.output}")
    print(f"Coverage code: {result['coverage_code']}")
    print(f"Insurers compared: {len(result['rows'])}")


if __name__ == "__main__":
    main()
