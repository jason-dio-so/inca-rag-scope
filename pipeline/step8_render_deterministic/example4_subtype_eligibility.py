"""
STEP NEXT-63: Example 4 - Subtype Eligibility (제자리암 / 경계성종양)

LLM OFF: Determine O/X/Unknown from evidence keywords (deterministic)

Input:
- subtype keyword (e.g., "제자리암", "경계성종양")

Output:
- O/X/Unknown table
- Judgment basis:
  - Definition
  - Exclusion (면책)
  - Reduction (감액)
  - Payment rate
- Evidence reference required

Gates:
- If no evidence → Unknown + reason
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from templates import DeterministicTemplates


class SubtypeEligibilityChecker:
    """Deterministic subtype eligibility checker (NO LLM)"""

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

    def find_subtype_evidence(self, cards: List[Dict[str, Any]],
                             subtype_keyword: str) -> Optional[Dict[str, Any]]:
        """
        Find evidence containing subtype keyword

        Returns: {
            "has_evidence": bool,
            "evidence_type": "정의" | "면책" | "감액" | "지급률",
            "snippet": "...",
            "evidence_ref": "..."
        }
        """
        # Search across all cancer-related coverages
        cancer_codes = ["A4200", "A4200_1", "A4201"]  # 암진단비 variations

        for card in cards:
            coverage_code = card.get("coverage_code", "") or ""
            if not any(code in coverage_code for code in cancer_codes):
                continue

            evidences = card.get("evidences", [])

            for ev in evidences:
                snippet = ev.get("snippet", "")

                # Check if subtype keyword exists
                if subtype_keyword not in snippet:
                    continue

                # Determine evidence type
                evidence_type = self._classify_evidence_type(snippet, subtype_keyword)

                # Build reference
                doc_type = ev.get("doc_type", "")
                page = ev.get("page", "")
                evidence_ref = f"{doc_type} p.{page}" if page else doc_type

                return {
                    "has_evidence": True,
                    "evidence_type": evidence_type,
                    "snippet": snippet[:200],  # Truncate
                    "evidence_ref": evidence_ref
                }

        return {
            "has_evidence": False,
            "evidence_type": None,
            "snippet": None,
            "evidence_ref": None
        }

    def _classify_evidence_type(self, snippet: str, subtype_keyword: str) -> str:
        """Classify evidence type based on surrounding context"""
        # Pattern 1: 면책 (exclusion)
        exclusion_keywords = ["제외", "보장하지 않", "면책", "해당하지 않"]
        for keyword in exclusion_keywords:
            if keyword in snippet:
                return "면책"

        # Pattern 2: 감액 (reduction)
        reduction_keywords = ["감액", "%", "50%", "20%", "일부 지급"]
        for keyword in reduction_keywords:
            if keyword in snippet:
                return "감액"

        # Pattern 3: 지급률 (payment rate)
        if "지급" in snippet or "보상" in snippet:
            return "지급률"

        # Default: 정의 (definition)
        return "정의"

    def determine_eligibility_status(self, evidence: Dict[str, Any]) -> str:
        """
        Determine O/X/Unknown status

        Rules:
        - Unknown: no evidence
        - X: 면책 (excluded)
        - △: 감액 (reduced payment)
        - O: 정의 or 지급률 (covered)
        """
        if not evidence["has_evidence"]:
            return "Unknown"

        evidence_type = evidence["evidence_type"]

        if evidence_type == "면책":
            return "X"
        elif evidence_type == "감액":
            return "△"
        else:  # 정의, 지급률
            return "O"

    def check_subtype_eligibility(self, insurers: List[str],
                                  subtype_keyword: str) -> Dict[str, Any]:
        """
        Check subtype eligibility across insurers

        Returns:
        {
            "subtype_keyword": "...",
            "rows": [...]
        }
        """
        rows = []

        for insurer in insurers:
            cards = self.load_coverage_cards(insurer)
            evidence = self.find_subtype_evidence(cards, subtype_keyword)
            status = self.determine_eligibility_status(evidence)

            rows.append(self.templates.eligibility_row(
                insurer=insurer,
                status=status,
                evidence_type=evidence["evidence_type"],
                evidence_snippet=evidence["snippet"],
                evidence_ref=evidence["evidence_ref"]
            ))

        return {
            "subtype_keyword": subtype_keyword,
            "rows": rows
        }


def main():
    parser = argparse.ArgumentParser(description="Example 4: Subtype Eligibility (LLM OFF)")
    parser.add_argument("--insurers", nargs="+", required=True,
                       help="List of insurers to check")
    parser.add_argument("--subtype", required=True,
                       help="Subtype keyword (e.g., 제자리암, 경계성종양)")
    parser.add_argument("--output", type=Path, default=Path("output/example4_subtype_eligibility.json"),
                       help="Output JSON file")
    args = parser.parse_args()

    checker = SubtypeEligibilityChecker()
    result = checker.check_subtype_eligibility(args.insurers, args.subtype)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Example 4 output: {args.output}")
    print(f"Subtype: {result['subtype_keyword']}")
    print(f"Insurers checked: {len(result['rows'])}")

    # Show status summary
    statuses = [row['status'] for row in result['rows']]
    print(f"Status distribution: O={statuses.count('O')}, "
          f"X={statuses.count('X')}, △={statuses.count('△')}, "
          f"Unknown={statuses.count('Unknown')}")


if __name__ == "__main__":
    main()
