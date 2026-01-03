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
        """
        Load coverage cards (SSOT)

        STEP NEXT-84: Use slim cards (has coverage_name + evidences)
        """
        # STEP NEXT-84: Use slim cards for coverage_name field
        cards_file = self.cards_dir / f"{insurer}_coverage_cards_slim.jsonl"
        if not cards_file.exists():
            # Fallback to full cards (legacy)
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

        STEP NEXT-84: Expand search to ALL coverages (not just A4200)
        - Search all cards (no code filter)
        - Search customer_view.benefit_description (SSOT for STEP NEXT-79+)
        - Detect coverage_trigger (DIAGNOSIS/SURGERY/TREATMENT)

        Returns: {
            "has_evidence": bool,
            "evidence_type": "정의" | "면책" | "감액" | "지급률",
            "snippet": "...",
            "evidence_ref": "...",
            "coverage_trigger": "DIAGNOSIS" | "SURGERY" | "TREATMENT" | "MIXED" | None
        }
        """
        # STEP NEXT-84: Two-pass search (priority-based)
        # Pass 1: Find cards where coverage_name_raw contains subtype (direct coverage)
        direct_matches = []
        indirect_matches = []

        for card in cards:
            coverage_name_raw = card.get("coverage_name_raw", "") or ""
            customer_view = card.get("customer_view", {}) or {}
            benefit_desc = customer_view.get("benefit_description", "") or ""

            # Priority 1: coverage_name_raw contains subtype
            if subtype_keyword in coverage_name_raw:
                direct_matches.append((card, coverage_name_raw, benefit_desc))
            # Priority 2: benefit_desc contains subtype (fallback)
            elif subtype_keyword in benefit_desc:
                indirect_matches.append((card, coverage_name_raw, benefit_desc))

        # Process direct matches first (highest priority)
        if direct_matches:
            card, coverage_name_raw, benefit_desc = direct_matches[0]
            snippet = benefit_desc or coverage_name_raw

            # STEP NEXT-84: If found in coverage_name, it's COVERED (not excluded)
            evidence_type = self._classify_evidence_type_for_covered_subtype(snippet)
            coverage_trigger = self._detect_coverage_trigger(coverage_name_raw, snippet)

            # STEP NEXT-85: Use PD:/EV: refs
            insurer = card.get("insurer", "")
            coverage_code = card.get("coverage_code", "")
            proposal_detail_ref = f"PD:{insurer}:{coverage_code}" if insurer and coverage_code else None
            evidence_ref = proposal_detail_ref or "가입설계서 (보장내용)"

            return {
                "has_evidence": True,
                "evidence_type": evidence_type,
                "snippet": snippet[:200],
                "evidence_ref": evidence_ref,
                "coverage_trigger": coverage_trigger,
                "proposal_detail_ref": proposal_detail_ref  # STEP NEXT-85
            }

        # Fallback: Process indirect matches (benefit_desc only)
        # STEP NEXT-84: Prefer non-exclusion matches (정의/감액) over exclusion (면책)
        if indirect_matches:
            # Find first non-exclusion match
            non_exclusion_match = None
            for card, coverage_name_raw, benefit_desc in indirect_matches:
                evidence_type = self._classify_evidence_type(benefit_desc, subtype_keyword)
                if evidence_type != "면책":
                    non_exclusion_match = (card, coverage_name_raw, benefit_desc, evidence_type)
                    break

            # Use non-exclusion match if found, otherwise use first match
            if non_exclusion_match:
                card, coverage_name_raw, benefit_desc, evidence_type = non_exclusion_match
            else:
                card, coverage_name_raw, benefit_desc = indirect_matches[0]
                evidence_type = self._classify_evidence_type(benefit_desc, subtype_keyword)

            coverage_trigger = self._detect_coverage_trigger(coverage_name_raw, benefit_desc)

            # STEP NEXT-85: Use PD:/EV: refs
            insurer = card.get("insurer", "")
            coverage_code = card.get("coverage_code", "")
            proposal_detail_ref = f"PD:{insurer}:{coverage_code}" if insurer and coverage_code else None
            evidence_ref = proposal_detail_ref or "가입설계서 (보장내용)"

            return {
                "has_evidence": True,
                "evidence_type": evidence_type,
                "snippet": benefit_desc[:200],
                "evidence_ref": evidence_ref,
                "coverage_trigger": coverage_trigger,
                "proposal_detail_ref": proposal_detail_ref  # STEP NEXT-85
            }

        return {
            "has_evidence": False,
            "evidence_type": None,
            "snippet": None,
            "evidence_ref": None,
            "coverage_trigger": None
        }

    def _detect_coverage_trigger(self, coverage_name: str, snippet: str) -> str:
        """
        STEP NEXT-84: Detect coverage trigger type

        Returns: "DIAGNOSIS" | "SURGERY" | "TREATMENT" | "MIXED"
        """
        coverage_lower = coverage_name.lower()
        snippet_lower = snippet.lower()

        # Trigger detection rules (deterministic)
        is_diagnosis = any(keyword in coverage_lower for keyword in ["진단비", "진단급여금", "진단"])
        is_surgery = any(keyword in coverage_lower for keyword in ["수술비", "수술급여금", "수술"])
        is_treatment = any(keyword in coverage_lower for keyword in ["치료비", "입원", "통원", "방사선", "약물"])

        # Check snippet if coverage_name is ambiguous
        if not (is_diagnosis or is_surgery or is_treatment):
            is_diagnosis = "진단" in snippet_lower and "확정" in snippet_lower
            is_surgery = "수술" in snippet_lower
            is_treatment = "치료" in snippet_lower or "입원" in snippet_lower

        # Determine trigger
        trigger_count = sum([is_diagnosis, is_surgery, is_treatment])
        if trigger_count > 1:
            return "MIXED"
        elif is_diagnosis:
            return "DIAGNOSIS"
        elif is_surgery:
            return "SURGERY"
        elif is_treatment:
            return "TREATMENT"
        else:
            return "DIAGNOSIS"  # Default fallback

    def _classify_evidence_type_for_covered_subtype(self, snippet: str) -> str:
        """
        STEP NEXT-85: Classify evidence type when subtype is in coverage_name (already covered)

        Priority (high to low):
        1. 감액 (reduction with %)
        2. 대기기간 (waiting period)
        3. 수술 (surgery trigger)
        4. 정의 (definition/categorization)
        """
        # Pattern 1: 감액 (reduction with percentage)
        reduction_keywords = ["감액", "50%", "20%", "일부 지급"]
        for keyword in reduction_keywords:
            if keyword in snippet and "%" in snippet:
                return "감액"

        # Pattern 2: 대기기간 (waiting period)
        if "대기" in snippet or "보장개시일" in snippet:
            return "대기기간"

        # Pattern 3: 수술 (surgery trigger)
        surgery_keywords = ["수술", "수술 1회당", "직접적인 목적으로 수술"]
        for keyword in surgery_keywords:
            if keyword in snippet:
                return "수술"

        # Pattern 4: 정의 (definition/categorization)
        definition_keywords = ["유사암 :", "제자리암", "경계성종양", "갑상선암", "기타피부암", "진단 확정"]
        for keyword in definition_keywords:
            if keyword in snippet:
                return "정의"

        # Default: fallback to 정의
        return "정의"

    def _classify_evidence_type(self, snippet: str, subtype_keyword: str) -> str:
        """
        STEP NEXT-85: Classify evidence type (with exclusion detection)

        Priority (high to low):
        1. 면책 (exclusion - X)
        2. 감액 (reduction - △)
        3. 대기기간 (waiting period - △)
        4. 수술 (surgery trigger - O)
        5. 정의 (definition - O)
        """
        # Pattern 1: 면책 (exclusion)
        exclusion_keywords = ["제외", "보장하지 않", "면책", "해당하지 않"]
        for keyword in exclusion_keywords:
            if keyword in snippet:
                return "면책"

        # Pattern 2: 감액 (reduction with percentage)
        reduction_keywords = ["감액", "50%", "20%", "일부 지급"]
        for keyword in reduction_keywords:
            if keyword in snippet and "%" in snippet:
                return "감액"

        # Pattern 3: 대기기간 (waiting period)
        if "대기" in snippet or "보장개시일" in snippet:
            return "대기기간"

        # Pattern 4: 수술 (surgery trigger)
        surgery_keywords = ["수술 1회당", "직접적인 목적으로 수술", "수술을 받은 경우"]
        for keyword in surgery_keywords:
            if keyword in snippet:
                return "수술"

        # Pattern 5: 정의 (definition/categorization)
        definition_keywords = ["유사암 :", "제자리암", "경계성종양", "진단 확정"]
        for keyword in definition_keywords:
            if keyword in snippet:
                return "정의"

        # Default: 정의
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
                evidence_ref=evidence["evidence_ref"],
                coverage_trigger=evidence["coverage_trigger"],  # STEP NEXT-84
                proposal_detail_ref=evidence.get("proposal_detail_ref")  # STEP NEXT-85
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
