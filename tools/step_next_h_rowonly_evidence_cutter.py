"""
STEP NEXT-H-REWORK: Row-Only Evidence Cutter (Diagnosis Coverage)

목표: SEARCH_FAIL 64.5% → < 30%

핵심 원칙 (ABSOLUTE):
1. Coverage Row Locator: 대상 담보의 row anchor를 찾아야 excerpt 생성 가능
2. Row excerpt 규칙: excerpt는 정확히 1개 담보 row만 포함
3. ❌ COVERAGE_ANCHOR 삽입 금지 (문서에 없는 텍스트 추가 = 근거 위조)
4. ❌ G5 완화 금지
5. ❌ LLM/추론 금지

입력: Step2-b canonical output (Diagnosis Registry 담보만)
출력: data/scope_v3/{insurer}_step3_diagnosis_rowonly_v1.jsonl
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.step3_evidence_resolver.document_reader import load_document_set
from pipeline.step3_evidence_resolver.evidence_patterns import EVIDENCE_PATTERNS


# Load diagnosis registry
def load_diagnosis_registry() -> Dict:
    """Load diagnosis coverage registry"""
    registry_path = Path(__file__).parent.parent / "data" / "registry" / "diagnosis_coverage_registry.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["coverage_entries"]


@dataclass
class RowAnchor:
    """Row anchor location for a coverage"""
    coverage_code: str
    coverage_name: str
    doc_type: str
    line_idx: int
    line_text: str
    page: int = 0


class CoverageRowLocator:
    """Locate coverage row anchors in documents"""

    def __init__(self):
        pass

    def find_row_anchors(
        self,
        doc,
        coverage_code: str,
        coverage_name: str
    ) -> List[RowAnchor]:
        """
        Find row anchors for target coverage in document.

        Row anchor criteria:
        - Line must contain coverage_name (with fuzzy matching)
        - Line must be part of a coverage table/list (structural signal)

        Returns:
            List of RowAnchor objects
        """
        # Clean coverage name (remove number prefixes)
        cleaned_name = re.sub(r"^\d+\.\s*", "", coverage_name).strip()

        # Load document text
        doc_text = doc.get_all_text()
        lines = doc_text.split("\n")

        anchors = []

        for i, line in enumerate(lines):
            # Check if line contains coverage name
            if not self._line_contains_coverage(line, cleaned_name):
                continue

            # Check if line is in table/list structure
            if not self._is_coverage_row_line(line):
                continue

            # Found row anchor
            anchor = RowAnchor(
                coverage_code=coverage_code,
                coverage_name=coverage_name,
                doc_type=doc.doc_type,
                line_idx=i,
                line_text=line.strip(),
                page=0  # TODO: extract page number if needed
            )
            anchors.append(anchor)

        return anchors

    def _line_contains_coverage(self, line: str, coverage_name: str) -> bool:
        """Check if line contains target coverage name (fuzzy)"""
        # Normalize
        norm_line = re.sub(r"[() \t]", "", line)
        norm_name = re.sub(r"[() \t]", "", coverage_name)

        # Check full name match
        if norm_name in norm_line:
            return True

        # Check base name (before parentheses)
        if "진단비" in coverage_name:
            base = coverage_name.split("(")[0].strip()
            norm_base = re.sub(r"[() \t]", "", base)
            if norm_base in norm_line:
                return True

        return False

    def _is_coverage_row_line(self, line: str) -> bool:
        """
        Check if line is likely a coverage row in a table/list.

        Heuristics:
        - Contains table separators (│, |)
        - Has multiple whitespace gaps (columns)
        - Contains typical table column keywords (보장명, 가입금액, 보험료)
        """
        # Table separator check
        if line.count("│") >= 1 or line.count("|") >= 1:
            return True

        # Multiple column gaps
        if len(re.findall(r"\s{3,}", line)) >= 2:
            return True

        # Table column keywords
        table_keywords = ["보장명", "담보명", "가입금액", "보험료", "지급사유"]
        if any(kw in line for kw in table_keywords):
            return True

        return False


class RowOnlyEvidenceExtractor:
    """Extract evidence from coverage-specific rows only"""

    def __init__(self, document_set):
        self.document_set = document_set
        self.row_locator = CoverageRowLocator()

    def extract_row_evidence(
        self,
        coverage_code: str,
        coverage_name: str,
        slot_key: str
    ) -> List[Dict]:
        """
        Extract evidence for slot from coverage-specific rows only.

        Process:
        1. Find row anchors for coverage in all documents
        2. For each row anchor, extract row excerpt (single coverage only)
        3. Search for slot keywords within row excerpt
        4. Return candidates (NO ANCHOR INSERTION)

        Returns:
            List of evidence candidates
        """
        pattern = EVIDENCE_PATTERNS.get(slot_key)
        if not pattern:
            return []

        candidates = []

        # Search documents in priority order
        search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]
        documents = self.document_set.search_all_documents(search_order)

        for doc in documents:
            # Find row anchors for this coverage
            row_anchors = self.row_locator.find_row_anchors(
                doc=doc,
                coverage_code=coverage_code,
                coverage_name=coverage_name
            )

            if not row_anchors:
                continue

            # Load full document text
            doc_text = doc.get_all_text()
            lines = doc_text.split("\n")

            # Extract evidence from each row
            for anchor in row_anchors:
                # Extract row excerpt (single coverage only)
                row_excerpt = self._extract_row_excerpt(
                    lines=lines,
                    anchor_line_idx=anchor.line_idx,
                    max_lines=8  # Row boundary limit
                )

                # Check if slot keyword present in this row
                has_slot_keyword = any(
                    kw in row_excerpt for kw in pattern.keywords
                )

                if not has_slot_keyword:
                    continue

                # Extract context around slot keyword
                context = self._extract_slot_context(
                    row_excerpt=row_excerpt,
                    slot_keywords=pattern.keywords,
                    context_lines=pattern.context_lines
                )

                if not context:
                    continue

                # Build candidate (NO ANCHOR INSERTION)
                candidate = {
                    "coverage_code": coverage_code,
                    "coverage_name": coverage_name,
                    "slot_key": slot_key,
                    "doc_type": doc.doc_type,
                    "page": anchor.page,
                    "line_text": anchor.line_text,  # Row anchor line
                    "context": context,  # Original text only
                    "row_excerpt": row_excerpt,  # Full row for debugging
                    "extraction_method": "row_only_v1"
                }

                candidates.append(candidate)

        return candidates

    def _extract_row_excerpt(
        self,
        lines: List[str],
        anchor_line_idx: int,
        max_lines: int = 8
    ) -> str:
        """
        Extract row excerpt starting from anchor line.

        Termination conditions:
        1. Next coverage row anchor detected
        2. Table header/separator detected
        3. max_lines reached

        Returns:
            Row excerpt string (original text only, NO INSERTION)
        """
        excerpt_lines = []
        start_idx = anchor_line_idx

        for i in range(start_idx, min(start_idx + max_lines, len(lines))):
            line = lines[i]

            # Termination check: next coverage row
            if i > start_idx and self._is_next_coverage_row(line):
                break

            # Termination check: table separator/header
            if i > start_idx and self._is_table_boundary(line):
                break

            excerpt_lines.append(line)

        return "\n".join(excerpt_lines)

    def _is_next_coverage_row(self, line: str) -> bool:
        """Check if line is start of next coverage row"""
        # Look for diagnosis coverage patterns
        diagnosis_patterns = [
            r"(암|뇌졸중|허혈성심장질환|급성심근경색|고액암|유사암|재진단암).*진단비",
            r"\d+\.\s*(암|뇌졸중|허혈성심장질환)",  # Numbered coverage lines
        ]

        for pattern in diagnosis_patterns:
            if re.search(pattern, line):
                return True

        return False

    def _is_table_boundary(self, line: str) -> bool:
        """Check if line is table separator/header"""
        # Empty line
        if not line.strip():
            return True

        # Table separator (horizontal lines)
        if re.match(r"^[─│┼├┤┬┴┌┐└┘\-|=_\s]+$", line):
            return True

        # Section headers
        header_keywords = ["보장내용", "지급사유", "보장개시일", "■", "※"]
        if any(kw in line for kw in header_keywords):
            # Check if this is a standalone header (not part of data row)
            if len(line.strip()) < 30:  # Short line = likely header
                return True

        return False

    def _extract_slot_context(
        self,
        row_excerpt: str,
        slot_keywords: List[str],
        context_lines: int
    ) -> str:
        """
        Extract context around slot keyword within row excerpt.

        Returns original text only (NO ANCHOR INSERTION).
        """
        lines = row_excerpt.split("\n")

        # Find line with slot keyword
        match_idx = None
        for i, line in enumerate(lines):
            if any(kw in line for kw in slot_keywords):
                match_idx = i
                break

        if match_idx is None:
            return ""

        # Extract context window
        start = max(0, match_idx - context_lines)
        end = min(len(lines), match_idx + context_lines + 1)

        context_lines_list = lines[start:end]
        return "\n".join(context_lines_list)


def run_step3_rowonly_diagnosis(
    insurers: List[str] = ["samsung", "kb"],
    output_dir: str = "data/scope_v3"
):
    """
    Run Step3 row-only re-run for diagnosis coverages.

    Args:
        insurers: List of insurer keys (default: Samsung + KB pilot)
        output_dir: Output directory
    """
    print("=" * 80)
    print("STEP NEXT-H-REWORK: Row-Only Evidence Cutter (Diagnosis Coverage)")
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

        # Initialize row-only extractor
        extractor = RowOnlyEvidenceExtractor(document_set)

        # Process each diagnosis coverage row
        results = []
        for row in diagnosis_rows:
            coverage_code = row["coverage_code"]
            coverage_name = row.get("coverage_name_raw", row.get("coverage_name", ""))

            print(f"\n   Processing: {coverage_code} | {coverage_name}")

            # Extract row-only evidence for all slots
            evidence_pack = {}
            for slot_key in EVIDENCE_PATTERNS.keys():
                candidates = extractor.extract_row_evidence(
                    coverage_code=coverage_code,
                    coverage_name=coverage_name,
                    slot_key=slot_key
                )

                if candidates:
                    print(f"      {slot_key}: {len(candidates)} row-only candidates")
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
                "partial_run": "STEP_NEXT_H_ROWONLY",
                "extraction_method": "row_only_v1"
            }

            results.append(result_row)

        # Write row-only output
        output_file = Path(output_dir) / f"{insurer_key}_step3_diagnosis_rowonly_v1.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✅ Row-only Step3 output written: {output_file}")
        print(f"   Total rows: {len(results)}")

    print(f"\n{'=' * 80}")
    print("✅ STEP NEXT-H-ROWONLY 완료")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP NEXT-H-REWORK: Row-Only Evidence Cutter")
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

    run_step3_rowonly_diagnosis(
        insurers=args.insurers,
        output_dir=args.output_dir
    )
