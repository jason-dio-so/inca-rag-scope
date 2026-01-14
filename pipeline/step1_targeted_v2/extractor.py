"""
Step1 V2: SSOT-Based Targeted Extraction

CONSTITUTIONAL PREMISE (IMMUTABLE):
1. coverage_code is INPUT from SSOT (not discovered from PDF)
2. NO coverage discovery (extract SSOT-defined coverages ONLY)
3. String matching is for PDF → SSOT lookup ONLY (not for coverage_code assignment)
4. ins_cd is the ONLY insurer identifier (from SSOT)
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class CoverageTarget:
    """SSOT coverage target"""
    coverage_code: str
    canonical_name: str
    insurer_coverage_name: str
    ins_cd: str


@dataclass
class ProposalFacts:
    """Proposal facts extracted from PDF"""
    coverage_amount_text: Optional[str] = None
    coverage_amount: Optional[int] = None
    premium_text: Optional[str] = None
    premium: Optional[int] = None
    period_text: Optional[str] = None
    period: Optional[Dict] = None
    evidences: Optional[List[Dict]] = None


@dataclass
class MatchedFact:
    """Matched coverage fact (SSOT + PDF)"""
    coverage_code: str  # FROM SSOT (input)
    canonical_name: str  # FROM SSOT
    ins_cd: str  # FROM SSOT
    coverage_name_raw: Optional[str]  # FROM PDF (audit only, NOT identifier)
    proposal_facts: ProposalFacts
    ssot_match_status: str  # FOUND | NOT_FOUND
    match_method: Optional[str] = None  # exact | normalized


class Step1V2Extractor:
    """
    Step1 V2: SSOT-Based Targeted Extraction

    This extractor does NOT discover coverages from PDF.
    It extracts facts for SSOT-defined (ins_cd, coverage_code) pairs ONLY.
    """

    SSOT_PATH = "data/sources/insurers/담보명mapping자료.xlsx"

    def __init__(self, ins_cd: str):
        """
        Initialize extractor for specific insurer.

        Args:
            ins_cd: Insurer code from SSOT (N01, N02, ...)
        """
        self.ins_cd = ins_cd
        self.targets: List[CoverageTarget] = []

    def load_ssot_targets(self) -> List[CoverageTarget]:
        """
        Load SSOT coverage targets for this insurer.

        Returns:
            List of CoverageTarget
        """
        # Read SSOT Excel
        df = pd.read_excel(self.SSOT_PATH)

        # Filter by ins_cd
        insurer_rows = df[df['ins_cd'] == self.ins_cd]

        if len(insurer_rows) == 0:
            raise ValueError(f"No SSOT targets found for ins_cd={self.ins_cd}")

        # Convert to CoverageTarget list
        targets = []
        for _, row in insurer_rows.iterrows():
            targets.append(CoverageTarget(
                coverage_code=row['cre_cvr_cd'],
                canonical_name=row['신정원코드명'],
                insurer_coverage_name=row['담보명(가입설계서)'],
                ins_cd=row['ins_cd']
            ))

        self.targets = targets
        print(f"[Step1 V2] Loaded {len(targets)} SSOT targets for ins_cd={self.ins_cd}")
        return targets

    def normalize(self, text: str) -> str:
        """
        Normalize text for matching.

        Rules:
        - Remove whitespace
        - Remove special chars: (), [], -, Ⅱ, 담보, etc.

        Args:
            text: Original text

        Returns:
            Normalized text
        """
        text = text.replace(" ", "")
        text = text.replace("(", "").replace(")", "")
        text = text.replace("[", "").replace("]", "")
        text = text.replace("-", "")
        text = text.replace("Ⅱ", "2")
        text = text.replace("Ⅲ", "3")
        text = text.replace("담보", "")
        return text

    def find_best_match(
        self,
        coverage_name_raw: str,
        targets: List[CoverageTarget]
    ) -> Optional[CoverageTarget]:
        """
        Find best matching SSOT target for PDF row.

        Matching rules:
        1. Exact match: coverage_name_raw == target.insurer_coverage_name
        2. Normalized match: normalize(coverage_name_raw) == normalize(target.insurer_coverage_name)
        3. No match: return None

        CRITICAL: This is NOT coverage_code assignment.
        This is PDF text → SSOT target lookup ONLY.

        Args:
            coverage_name_raw: Coverage name from PDF
            targets: List of SSOT coverage targets

        Returns:
            Matching CoverageTarget or None
        """
        # Try exact match first
        for target in targets:
            if coverage_name_raw == target.insurer_coverage_name:
                return target

        # Try normalized match
        normalized_input = self.normalize(coverage_name_raw)
        for target in targets:
            normalized_target = self.normalize(target.insurer_coverage_name)
            if normalized_input == normalized_target:
                return target

        # No match
        return None

    def parse_amount(self, text: str) -> Optional[int]:
        """
        Parse coverage amount text to integer.

        Examples:
            "3천만원" → 30000000
            "3,000만원" → 30000000
            "1억원" → 100000000

        Args:
            text: Amount text from PDF

        Returns:
            Parsed amount as integer, or None if parsing fails
        """
        if not text:
            return None

        try:
            text = text.replace(",", "").replace(" ", "")

            if "억" in text:
                amount = int(text.replace("억원", "").replace("억", "")) * 100000000
            elif "천만" in text:
                amount = int(text.replace("천만원", "").replace("천만", "")) * 10000000
            elif "만" in text:
                amount = int(text.replace("만원", "").replace("만", "")) * 10000
            else:
                amount = int(text.replace("원", ""))

            return amount
        except Exception as e:
            print(f"[Step1 V2] Failed to parse amount '{text}': {e}")
            return None

    def parse_premium(self, text: str) -> Optional[int]:
        """
        Parse premium text to integer.

        Examples:
            "30,480" → 30480
            "34,230원" → 34230

        Args:
            text: Premium text from PDF

        Returns:
            Parsed premium as integer, or None if parsing fails
        """
        if not text:
            return None

        try:
            text = text.replace(",", "").replace("원", "").replace(" ", "")
            return int(text)
        except Exception as e:
            print(f"[Step1 V2] Failed to parse premium '{text}': {e}")
            return None

    def parse_period(self, text: str) -> Optional[Dict]:
        """
        Parse period text to structured dict.

        Examples:
            "20년 / 100세" → {"payment_years": 20, "maturity_age": 100}
            "100세만기 / 20년납" → {"payment_years": 20, "maturity_age": 100}

        Args:
            text: Period text from PDF

        Returns:
            Parsed period as dict, or None if parsing fails
        """
        if not text:
            return None

        try:
            parts = text.split("/")

            payment = None
            maturity = None

            for part in parts:
                if "년" in part:
                    payment = int(part.replace("년", "").replace("납", "").strip())
                if "세" in part:
                    maturity = int(part.replace("세", "").replace("만기", "").strip())

            return {
                "payment_years": payment,
                "maturity_age": maturity
            }
        except Exception as e:
            print(f"[Step1 V2] Failed to parse period '{text}': {e}")
            return None

    def extract_from_step1_v1_output(
        self,
        step1_v1_path: str,
        filter_coverage_code: Optional[str] = None
    ) -> List[MatchedFact]:
        """
        Extract targeted facts from Step1 V1 output (temporary bridge).

        This function uses existing Step1 V1 output as a data source,
        but filters and transforms it according to Step1 V2 principles:
        - coverage_code comes from SSOT (not Step1 V1)
        - Only SSOT-defined coverages are included

        Args:
            step1_v1_path: Path to Step1 V1 output JSONL
            filter_coverage_code: If specified, only extract this coverage_code

        Returns:
            List of MatchedFact
        """
        matched_facts = []

        # Read Step1 V1 output
        with open(step1_v1_path, 'r', encoding='utf-8') as f:
            for line in f:
                row = json.loads(line)

                # Get coverage_name_raw from Step1 V1
                coverage_name_raw = row.get('coverage_name_raw')
                if not coverage_name_raw:
                    continue

                # Try to match to SSOT target
                target = self.find_best_match(coverage_name_raw, self.targets)

                if not target:
                    # No SSOT target found → skip
                    continue

                # If filter specified, only include matching coverage_code
                if filter_coverage_code and target.coverage_code != filter_coverage_code:
                    continue

                # Extract proposal_facts from Step1 V1
                proposal_facts_raw = row.get('proposal_facts', {})

                # Parse and clean facts
                amount_text = proposal_facts_raw.get('coverage_amount_text')
                premium_text = proposal_facts_raw.get('premium_text')
                period_text = proposal_facts_raw.get('period_text')

                proposal_facts = ProposalFacts(
                    coverage_amount_text=amount_text,
                    coverage_amount=self.parse_amount(amount_text) if amount_text else None,
                    premium_text=premium_text,
                    premium=self.parse_premium(premium_text) if premium_text else None,
                    period_text=period_text,
                    period=self.parse_period(period_text) if period_text else None,
                    evidences=proposal_facts_raw.get('evidences', [])
                )

                # Determine match method
                match_method = "exact" if coverage_name_raw == target.insurer_coverage_name else "normalized"

                # Create MatchedFact
                matched_fact = MatchedFact(
                    coverage_code=target.coverage_code,  # ← FROM SSOT (input)
                    canonical_name=target.canonical_name,  # ← FROM SSOT
                    ins_cd=target.ins_cd,  # ← FROM SSOT
                    coverage_name_raw=coverage_name_raw,  # ← FROM PDF (audit)
                    proposal_facts=proposal_facts,
                    ssot_match_status="FOUND",
                    match_method=match_method
                )

                matched_facts.append(matched_fact)

        print(f"[Step1 V2] Extracted {len(matched_facts)} matched facts from Step1 V1 output")
        if filter_coverage_code:
            print(f"[Step1 V2] Filtered for coverage_code={filter_coverage_code}")

        return matched_facts

    def to_jsonl(self, matched_facts: List[MatchedFact], output_path: str):
        """
        Write matched facts to JSONL file.

        Args:
            matched_facts: List of MatchedFact
            output_path: Output JSONL file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for fact in matched_facts:
                # Convert to dict
                output = {
                    "ins_cd": fact.ins_cd,
                    "coverage_code": fact.coverage_code,
                    "canonical_name": fact.canonical_name,
                    "coverage_name_raw": fact.coverage_name_raw,
                    "proposal_facts": {
                        "coverage_amount_text": fact.proposal_facts.coverage_amount_text,
                        "coverage_amount": fact.proposal_facts.coverage_amount,
                        "premium_text": fact.proposal_facts.premium_text,
                        "premium": fact.proposal_facts.premium,
                        "period_text": fact.proposal_facts.period_text,
                        "period": fact.proposal_facts.period,
                        "evidences": fact.proposal_facts.evidences
                    },
                    "ssot_match_status": fact.ssot_match_status,
                    "match_method": fact.match_method
                }

                f.write(json.dumps(output, ensure_ascii=False) + '\n')

        print(f"[Step1 V2] Wrote {len(matched_facts)} facts to {output_path}")


def main():
    """
    Step1 V2 entry point (for testing).
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.step1_targeted_v2.extractor <ins_cd> [coverage_code]")
        print("Example: python -m pipeline.step1_targeted_v2.extractor N01 A4200_1")
        sys.exit(1)

    ins_cd = sys.argv[1]
    filter_coverage_code = sys.argv[2] if len(sys.argv) > 2 else None

    # Initialize extractor
    extractor = Step1V2Extractor(ins_cd)

    # Load SSOT targets
    extractor.load_ssot_targets()

    # Extract from Step1 V1 output (temporary bridge)
    step1_v1_path = f"data/scope_v3/{ins_cd.lower()}_step1_raw_scope_v3.jsonl"

    # Map ins_cd to insurer_key (temporary)
    insurer_key_map = {
        "N01": "meritz",
        "N02": "hanwha",
        "N03": "lotte",
        "N05": "heungkuk",
        "N08": "samsung",
        "N09": "hyundai",
        "N10": "kb",
        "N13": "db_over41"
    }
    insurer_key = insurer_key_map.get(ins_cd)
    if insurer_key:
        step1_v1_path = f"data/scope_v3/{insurer_key}_step1_raw_scope_v3.jsonl"

    matched_facts = extractor.extract_from_step1_v1_output(
        step1_v1_path=step1_v1_path,
        filter_coverage_code=filter_coverage_code
    )

    # Write to output
    output_path = f"data/scope_v3/{ins_cd}_step1_targeted_v2.jsonl"
    extractor.to_jsonl(matched_facts, output_path)

    print(f"\n[Step1 V2] SUCCESS")
    print(f"[Step1 V2] Extracted {len(matched_facts)} coverages for ins_cd={ins_cd}")
    if filter_coverage_code:
        print(f"[Step1 V2] Filtered for coverage_code={filter_coverage_code}")


if __name__ == "__main__":
    main()
