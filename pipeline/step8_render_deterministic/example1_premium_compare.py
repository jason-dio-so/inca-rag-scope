"""
STEP NEXT-63: Example 1 - Premium Comparison (Top 4)

LLM OFF: 100% deterministic premium ranking from proposal_facts

Input:
- Insurance type, gender, age, plan
- Sort by: premium (ascending)

Output:
- Top-4 insurers table
- Monthly premium / Total premium
- Evidence references (proposal PDF page)

Gates:
- premium >= 4 rows OR NotAvailable with reason
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from templates import DeterministicTemplates


class PremiumComparer:
    """Deterministic premium comparison (NO LLM)"""

    def __init__(self, scope_dir: Path = Path("data/scope_v3")):
        self.scope_dir = scope_dir
        self.templates = DeterministicTemplates()

    def load_canonical_scope(self, insurer: str) -> List[Dict[str, Any]]:
        """Load canonical scope with proposal_facts"""
        scope_file = self.scope_dir / f"{insurer}_step2_canonical_scope_v1.jsonl"
        if not scope_file.exists():
            return []

        items = []
        with open(scope_file, 'r', encoding='utf-8') as f:
            for line in f:
                items.append(json.loads(line))
        return items

    def extract_premium_data(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract premium from proposal_facts (deterministic)"""
        for item in items:
            proposal_facts = item.get("proposal_facts", {})
            premium_text = proposal_facts.get("premium_text")

            if premium_text:
                # Extract evidence reference
                evidences = proposal_facts.get("evidences", [])
                evidence_ref = ""
                if evidences:
                    ev = evidences[0]
                    doc_type = ev.get("doc_type", "")
                    page = ev.get("page", "")
                    evidence_ref = f"{doc_type} p.{page}" if page else doc_type

                # Parse monthly premium
                try:
                    monthly = int(premium_text.replace(",", ""))
                except:
                    monthly = None

                # Calculate total (assume from period_text if available)
                period_text = proposal_facts.get("period_text", "")
                total = self._calculate_total_premium(monthly, period_text)

                return {
                    "monthly": premium_text,
                    "monthly_int": monthly,
                    "total": f"{total:,}" if total else "계산 불가",
                    "evidence_ref": evidence_ref
                }
        return None

    def _calculate_total_premium(self, monthly: Optional[int], period_text: str) -> Optional[int]:
        """Calculate total premium from period text (deterministic pattern)"""
        if not monthly or not period_text:
            return None

        # Pattern: "20년납" → 20 * 12 months
        import re
        match = re.search(r'(\d+)년납', period_text)
        if match:
            years = int(match.group(1))
            return monthly * years * 12
        return None

    def compare_top4(self, insurers: List[str]) -> Dict[str, Any]:
        """
        Compare premiums across insurers and return Top-4

        Returns:
        {
            "status": "success" | "not_available",
            "rows": [...],
            "reason": "..." (if not_available)
        }
        """
        premium_data = []

        for insurer in insurers:
            items = self.load_canonical_scope(insurer)
            prem = self.extract_premium_data(items)

            if prem:
                premium_data.append({
                    "insurer": insurer,
                    **prem
                })

        # Gate: At least 4 insurers with premium data
        if len(premium_data) < 4:
            return self.templates.premium_not_available(
                "가입설계서 보험료 데이터 미제공 (4개 미만)"
            )

        # Sort by monthly_int (ascending), handle None values
        premium_data.sort(key=lambda x: x.get("monthly_int") if x.get("monthly_int") is not None else float('inf'))

        # Top-4
        top4 = premium_data[:4]

        rows = []
        for item in top4:
            rows.append(self.templates.premium_table_row(
                insurer=item["insurer"],
                monthly=item["monthly"],
                total=item["total"],
                monthly_ref=item["evidence_ref"],
                total_ref=item["evidence_ref"]
            ))

        return {
            "status": "success",
            "rows": rows
        }


def main():
    parser = argparse.ArgumentParser(description="Example 1: Premium Comparison (LLM OFF)")
    parser.add_argument("--insurers", nargs="+", required=True,
                       help="List of insurers to compare")
    parser.add_argument("--output", type=Path, default=Path("output/example1_premium_compare.json"),
                       help="Output JSON file")
    args = parser.parse_args()

    comparer = PremiumComparer()
    result = comparer.compare_top4(args.insurers)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Example 1 output: {args.output}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Top-4 insurers: {[r['insurer'] for r in result['rows']]}")


if __name__ == "__main__":
    main()
