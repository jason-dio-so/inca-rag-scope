"""
STEP NEXT-H-3: Table-Anchored Evidence Extraction (Diagnosis-Only)

핵심 아이디어:
Step1에서 이미 가입설계서 표에서 coverage row를 추출했음.
그 row를 Evidence Anchor로 사용하여 Step3 evidence를 생성.

변경 사항:
1. 가입설계서 표의 동일 row = Evidence Anchor
2. 한 excerpt = 정확히 한 coverage row
3. G5 유지, Contamination = 0

목표:
- SEARCH_FAIL: 64.5% → < 30%
- FOUND: 17.3% → 개선
- Contamination: 0 유지
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.step3_evidence_resolver.document_reader import load_document_set
from pipeline.step3_evidence_resolver.evidence_patterns import EVIDENCE_PATTERNS


def load_diagnosis_registry() -> Dict:
    """Load diagnosis coverage registry"""
    registry_path = Path(__file__).parent.parent / "data" / "registry" / "diagnosis_coverage_registry.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["coverage_entries"]


@dataclass
class TableRowAnchor:
    """Table row anchor from Step1/Step2"""
    coverage_code: str
    coverage_name: str
    row_text: str  # Original table row text from 가입설계서
    normalized_name: str


class TableAnchoredExtractor:
    """
    Extract evidence using Step1 table row as anchor.

    Key principle:
    - Step1 already identified coverage rows in 가입설계서
    - Use those rows as Evidence Anchor
    - Search for slot keywords WITHIN the same table row
    """

    def __init__(self, document_set):
        self.document_set = document_set

    def find_table_row_in_proposal(
        self,
        coverage_name: str,
        coverage_code: str
    ) -> Optional[TableRowAnchor]:
        """
        Find the table row in 가입설계서 that matches the coverage.

        This row was originally extracted by Step1.
        We search for it again to use as Evidence Anchor.

        Args:
            coverage_name: Target coverage name
            coverage_code: Target coverage code

        Returns:
            TableRowAnchor or None
        """
        # Get 가입설계서 document
        proposal_docs = [
            doc for doc in self.document_set.documents.values()
            if doc.doc_type == "가입설계서"
        ]

        if not proposal_docs:
            return None

        proposal_doc = proposal_docs[0]
        doc_text = proposal_doc.get_all_text()
        lines = doc_text.split("\n")

        # Normalize target name for matching
        normalized_target = self._normalize_name(coverage_name)

        # Find best matching line (table row)
        best_match = None
        best_score = 0.0

        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue

            # Check if line is a table row (has separators or multiple columns)
            if not self._is_table_row(line):
                continue

            # Check if line contains coverage name
            normalized_line = self._normalize_name(line)

            # Score based on similarity
            score = self._compute_match_score(normalized_target, normalized_line)

            if score > best_score and score >= 0.6:  # Threshold
                best_score = score
                best_match = line

        if best_match:
            return TableRowAnchor(
                coverage_code=coverage_code,
                coverage_name=coverage_name,
                row_text=best_match.strip(),
                normalized_name=normalized_target
            )

        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize coverage name for matching"""
        # Remove number prefixes
        name = re.sub(r"^\d+\.\s*", "", name)
        # Remove spaces, parentheses
        name = re.sub(r"[() \t│|]", "", name)
        # Lowercase
        return name.lower()

    def _is_table_row(self, line: str) -> bool:
        """Check if line is a table row"""
        # Has table separators
        if "│" in line or "|" in line:
            return True
        # Has multiple whitespace gaps (columns)
        if len(re.findall(r"\s{3,}", line)) >= 2:
            return True
        # Contains typical table keywords
        if any(kw in line for kw in ["진단비", "가입금액", "보험료", "면책"]):
            return True
        return False

    def _compute_match_score(self, target: str, candidate: str) -> float:
        """Compute match score between target and candidate"""
        # Substring match
        if target in candidate:
            return 1.0

        # Token overlap
        target_tokens = set(re.findall(r"[가-힣a-z0-9]+", target))
        candidate_tokens = set(re.findall(r"[가-힣a-z0-9]+", candidate))

        if not target_tokens:
            return 0.0

        overlap = len(target_tokens & candidate_tokens)
        return overlap / len(target_tokens)

    def extract_evidence_from_anchor(
        self,
        anchor: TableRowAnchor,
        slot_key: str
    ) -> List[Dict]:
        """
        Extract evidence for slot using table row anchor.

        Process:
        1. Use anchor row_text as base excerpt
        2. Check if slot keyword present in row
        3. Build evidence with COVERAGE_ANCHOR + TABLE_ROW_EXCERPT format
        4. Return candidates

        Args:
            anchor: Table row anchor
            slot_key: Slot to extract

        Returns:
            List of evidence candidates
        """
        pattern = EVIDENCE_PATTERNS.get(slot_key)
        if not pattern:
            return []

        # Check if slot keyword present in anchor row
        has_keyword = any(kw in anchor.row_text for kw in pattern.keywords)

        if not has_keyword:
            # Check auxiliary documents for this slot
            # But ONLY if anchor exists
            return self._search_auxiliary_docs(anchor, slot_key)

        # Build evidence with structured format
        evidence = self._build_evidence_excerpt(
            anchor=anchor,
            slot_key=slot_key,
            source_text=anchor.row_text,
            doc_type="가입설계서"
        )

        return [evidence] if evidence else []

    def _search_auxiliary_docs(
        self,
        anchor: TableRowAnchor,
        slot_key: str
    ) -> List[Dict]:
        """
        Search auxiliary documents (요약서, 사업방법서, 약관) for slot evidence.

        ONLY allowed AFTER anchor is established.
        Must mention target coverage.

        Args:
            anchor: Table row anchor (must exist)
            slot_key: Slot to search

        Returns:
            List of evidence candidates
        """
        pattern = EVIDENCE_PATTERNS.get(slot_key)
        if not pattern:
            return []

        candidates = []

        # Search order: 상품요약서 → 사업방법서 → 약관
        search_order = ["상품요약서", "사업방법서", "약관"]

        for doc_type in search_order:
            docs = [
                doc for doc in self.document_set.documents.values()
                if doc.doc_type == doc_type
            ]

            if not docs:
                continue

            doc = docs[0]
            doc_text = doc.get_all_text()
            lines = doc_text.split("\n")

            # Search for slot keyword
            for i, line in enumerate(lines):
                if not any(kw in line for kw in pattern.keywords):
                    continue

                # Extract context
                start = max(0, i - pattern.context_lines)
                end = min(len(lines), i + pattern.context_lines + 1)
                context = "\n".join(lines[start:end])

                # Check if context mentions target coverage
                if not self._mentions_coverage(context, anchor.normalized_name):
                    continue

                # Build evidence
                evidence = self._build_evidence_excerpt(
                    anchor=anchor,
                    slot_key=slot_key,
                    source_text=context,
                    doc_type=doc_type
                )

                if evidence:
                    candidates.append(evidence)

                # Take first match per doc type
                break

        return candidates

    def _mentions_coverage(self, text: str, normalized_name: str) -> bool:
        """Check if text mentions target coverage"""
        normalized_text = self._normalize_name(text)
        return normalized_name in normalized_text

    def _build_evidence_excerpt(
        self,
        anchor: TableRowAnchor,
        slot_key: str,
        source_text: str,
        doc_type: str
    ) -> Optional[Dict]:
        """
        Build evidence excerpt with structured format:

        [COVERAGE_ANCHOR]
        coverage_code: A4200_1
        coverage_name: 암진단비(유사암 제외)

        [TABLE_ROW_EXCERPT]
        {source_text}

        Args:
            anchor: Table row anchor
            slot_key: Slot key
            source_text: Source text containing slot value
            doc_type: Document type

        Returns:
            Evidence dict or None
        """
        # Build structured excerpt
        anchor_block = f"""[COVERAGE_ANCHOR]
coverage_code: {anchor.coverage_code}
coverage_name: {anchor.coverage_name}"""

        excerpt_block = f"""[TABLE_ROW_EXCERPT]
{source_text}"""

        full_excerpt = f"{anchor_block}\n\n{excerpt_block}"

        return {
            "coverage_code": anchor.coverage_code,
            "coverage_name": anchor.coverage_name,
            "slot_key": slot_key,
            "doc_type": doc_type,
            "context": full_excerpt,
            "source_text_original": source_text,
            "extraction_method": "table_anchored_v1"
        }


def run_step3_table_anchored(
    insurers: List[str] = ["samsung", "kb"],
    output_dir: str = "data/scope_v3"
):
    """
    Run Step3 table-anchored evidence extraction for diagnosis coverages.
    """
    print("=" * 80)
    print("STEP NEXT-H-3: Table-Anchored Evidence Extraction")
    print("=" * 80)

    # Load diagnosis registry
    registry = load_diagnosis_registry()
    diagnosis_codes = list(registry.keys())

    print(f"\n✅ Diagnosis Registry Loaded: {len(diagnosis_codes)} coverage codes")
    print(f"   Coverage codes: {', '.join(diagnosis_codes)}")
    print(f"\n✅ Target insurers: {', '.join(insurers)}")

    # Process each insurer
    for insurer_key in insurers:
        print(f"\n{'=' * 80}")
        print(f"Processing: {insurer_key.upper()}")
        print(f"{'=' * 80}")

        # Load Step2-b canonical output
        step2_file = Path(output_dir) / f"{insurer_key}_step2_canonical_scope_v1.jsonl"
        if not step2_file.exists():
            print(f"⚠️  SKIP: {step2_file} not found")
            continue

        # Filter diagnosis coverage rows
        diagnosis_rows = []
        with open(step2_file, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                coverage_code = row.get("coverage_code")
                if coverage_code in diagnosis_codes:
                    diagnosis_rows.append(row)

        print(f"   Diagnosis rows found: {len(diagnosis_rows)}")

        if not diagnosis_rows:
            print(f"   ⚠️  No diagnosis rows found for {insurer_key}")
            continue

        # Load document set
        try:
            document_set = load_document_set(insurer_key)
        except Exception as e:
            print(f"   ❌ Failed to load documents for {insurer_key}: {e}")
            continue

        # Initialize table-anchored extractor
        extractor = TableAnchoredExtractor(document_set)

        # Process each diagnosis coverage row
        results = []
        for row in diagnosis_rows:
            coverage_code = row["coverage_code"]
            coverage_name = row.get("coverage_name_raw", row.get("coverage_name", ""))

            print(f"\n   Processing: {coverage_code} | {coverage_name}")

            # Find table row anchor in 가입설계서
            anchor = extractor.find_table_row_in_proposal(
                coverage_name=coverage_name,
                coverage_code=coverage_code
            )

            if not anchor:
                print(f"      ⚠️  No table row anchor found")
                # Create empty evidence pack
                evidence_pack = {slot_key: [] for slot_key in EVIDENCE_PATTERNS.keys()}
            else:
                print(f"      ✅ Table row anchor found: {anchor.row_text[:60]}...")

                # Extract evidence for all slots using anchor
                evidence_pack = {}
                for slot_key in EVIDENCE_PATTERNS.keys():
                    candidates = extractor.extract_evidence_from_anchor(
                        anchor=anchor,
                        slot_key=slot_key
                    )

                    if candidates:
                        print(f"         {slot_key}: {len(candidates)} candidates")
                        evidence_pack[slot_key] = candidates
                    else:
                        evidence_pack[slot_key] = []

            # Build result row
            result_row = {
                "insurer_key": insurer_key,
                "coverage_code": coverage_code,
                "coverage_name": coverage_name,
                "product": row.get("product", {}),
                "variant": row.get("variant", {}),
                "evidence_pack": evidence_pack,
                "partial_run": "STEP_NEXT_H3_TABLE_ANCHORED",
                "extraction_method": "table_anchored_v1",
                "anchor_found": anchor is not None
            }

            results.append(result_row)

        # Write table-anchored output
        output_file = Path(output_dir) / f"{insurer_key}_step3_diagnosis_tableanchored_v1.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✅ Table-anchored output written: {output_file}")
        print(f"   Total rows: {len(results)}")
        print(f"   Anchors found: {sum(1 for r in results if r['anchor_found'])}")

    print(f"\n{'=' * 80}")
    print("STEP NEXT-H-3 완료")
    print("- Evidence Anchor: Table-Row Strict")
    print("- Diagnosis Coverage Only")
    print("- G5 preserved")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP NEXT-H-3: Table-Anchored Evidence Extraction")
    parser.add_argument(
        "--insurers",
        nargs="+",
        default=["samsung", "kb"],
        help="Insurers to process (default: samsung kb)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/scope_v3",
        help="Output directory (default: data/scope_v3)"
    )

    args = parser.parse_args()

    run_step3_table_anchored(
        insurers=args.insurers,
        output_dir=args.output_dir
    )
