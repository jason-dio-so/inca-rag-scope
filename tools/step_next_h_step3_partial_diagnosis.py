"""
STEP NEXT-H-1: Step3 Partial Re-run (Diagnosis Coverage Only)

목표: SEARCH_FAIL 64.5% → < 30% by improving evidence quality

핵심 변경:
1. Coverage-row granularity: 한 excerpt = 정확히 한 담보 row만
2. COVERAGE_ANCHOR 강제 삽입: 모든 excerpt 최상단에 추가
3. 문서 우선순위 유지: 가입설계서 → 상품요약서 → 사업방법서 → 약관

금지:
- ❌ LLM 사용
- ❌ G5 완화
- ❌ 전체 파이프라인 재실행
- ❌ Registry 외 담보 처리

입력: Step2-b canonical rows (Diagnosis Registry 담보만)
출력: data/scope_v3/{insurer}_step3_diagnosis_partial_gated.jsonl
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.step3_evidence_resolver.document_reader import load_document_set
from pipeline.step3_evidence_resolver.evidence_patterns import EVIDENCE_PATTERNS, PatternMatcher
from pipeline.step3_evidence_resolver.gates import EvidenceGates
from pipeline.step4_compare_model.gates import CoverageAttributionValidator


# Load diagnosis registry
def load_diagnosis_registry() -> Dict:
    """Load diagnosis coverage registry"""
    registry_path = Path(__file__).parent.parent / "data" / "registry" / "diagnosis_coverage_registry.json"
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["coverage_entries"]


# Coverage-anchored evidence extraction
class CoverageAnchoredExtractor:
    """Extract evidence with mandatory coverage anchoring"""

    def __init__(self, document_set, enable_gates: bool = True):
        self.document_set = document_set
        self.pattern_matcher = PatternMatcher()
        self.gates = EvidenceGates() if enable_gates else None
        self.enable_gates = enable_gates

    def extract_anchored_evidence(
        self,
        coverage_code: str,
        coverage_name: str,
        slot_key: str
    ) -> List[Dict]:
        """
        Extract evidence with COVERAGE_ANCHOR mandatory insertion.

        핵심 원칙:
        1. 한 excerpt = 정확히 한 담보 row만
        2. excerpt 최상단에 COVERAGE_ANCHOR 추가
        3. 다른 담보 row/헤더/금액 포함 시 폐기

        Returns:
            List of evidence candidates with anchor
        """
        pattern = EVIDENCE_PATTERNS.get(slot_key)
        if not pattern:
            return []

        # Search documents in priority order
        search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]
        documents = self.document_set.search_all_documents(search_order)

        candidates = []

        for doc in documents:
            # Extract candidates using pattern matcher
            matches = self._find_matches_in_document(
                doc=doc,
                pattern=pattern
            )

            for match in matches:
                # Check if coverage name present (for tracking only)
                has_coverage_name = self._contains_coverage_name(match["context"], coverage_name)

                # Filter: Reject if multiple coverage rows detected
                # (This prevents cross-coverage contamination)
                if self._contains_multiple_coverages(match["context"], coverage_name):
                    continue

                # ALWAYS insert COVERAGE_ANCHOR (핵심 변경)
                # This is the key innovation of STEP NEXT-H
                anchored_context = self._insert_coverage_anchor(
                    coverage_code,
                    coverage_name,
                    match["context"]
                )

                candidate = {
                    "coverage_code": coverage_code,
                    "coverage_name": coverage_name,
                    "slot_key": slot_key,
                    "doc_type": doc.doc_type,
                    "page": match.get("page", 0),
                    "line_text": match["line_text"],
                    "context": anchored_context,
                    "context_original": match["context"],  # Keep original for debugging
                    "anchor_inserted": True,
                    "had_original_coverage_mention": has_coverage_name  # Track for analysis
                }

                candidates.append(candidate)

        return candidates

    def _contains_coverage_name(self, text: str, coverage_name: str) -> bool:
        """Check if text contains target coverage name (fuzzy match)"""
        # Remove number prefixes (e.g., "70. 암진단비" → "암진단비")
        cleaned_coverage_name = re.sub(r"^\d+\.\s*", "", coverage_name).strip()

        # Normalize for fuzzy matching
        normalized_name = re.sub(r"[() ]", "", cleaned_coverage_name)
        normalized_text = re.sub(r"[() ]", "", text)

        # Check for normalized match
        if re.search(normalized_name, normalized_text, re.IGNORECASE):
            return True

        # Check for common coverage name variations
        # e.g., "암진단비(유사암제외)" → "암진단비", "유사암제외진단비"
        if "진단비" in cleaned_coverage_name:
            base = cleaned_coverage_name.split("(")[0].strip()
            # Remove parentheses and normalize
            base_normalized = re.sub(r"[() ]", "", base)
            if base_normalized in normalized_text:
                return True

        return False

    def _contains_multiple_coverages(self, text: str, target_coverage: str) -> bool:
        """
        Detect if excerpt contains multiple coverage rows.

        Indicators of multiple coverages:
        - Multiple lines with "진단비" (excluding target coverage)
        - Table headers repeated
        - Multiple "보험금" or "지급금" lines with different coverage names
        """
        lines = text.split("\n")

        # Count coverage mentions
        coverage_mentions = []
        for line in lines:
            # Look for diagnosis benefit patterns
            if re.search(r"(암|뇌졸중|허혈성심장질환|급성심근경색|고액암|유사암|재진단암).*진단비", line):
                coverage_mentions.append(line)

        # If more than 1 coverage mentioned (excluding target), reject
        non_target_mentions = [m for m in coverage_mentions if target_coverage not in m]
        if len(non_target_mentions) >= 1:
            return True

        # Reject if table header appears multiple times (indicating multi-row table)
        header_count = text.count("보장명") + text.count("담보명") + text.count("보험금종류")
        if header_count > 1:
            return True

        return False

    def _find_matches_in_document(self, doc, pattern) -> List[Dict]:
        """Find pattern matches in document"""
        # Load document text
        doc_text = doc.get_all_text()
        lines = doc_text.split('\n')
        matches = []

        for i, line in enumerate(lines):
            # Check if any keyword matches
            for keyword in pattern.keywords:
                if keyword in line:
                    # Extract context window
                    start_idx = max(0, i - pattern.context_lines)
                    end_idx = min(len(lines), i + pattern.context_lines + 1)
                    context = '\n'.join(lines[start_idx:end_idx])

                    matches.append({
                        "line_text": line.strip(),
                        "context": context.strip(),
                        "page": 0,  # Will be updated if page info available
                        "line_num": i + 1
                    })
                    break  # One match per line

        return matches

    def _insert_coverage_anchor(
        self,
        coverage_code: str,
        coverage_name: str,
        original_context: str
    ) -> str:
        """
        Insert COVERAGE_ANCHOR at top of excerpt.

        Format:
        COVERAGE_ANCHOR: <coverage_code> | <coverage_name>

        ---
        <original context>
        """
        anchor_line = f"COVERAGE_ANCHOR: {coverage_code} | {coverage_name}"
        separator = "---"

        return f"{anchor_line}\n{separator}\n{original_context}"


def run_step3_partial_diagnosis(
    insurers: List[str] = ["samsung", "kb"],
    output_dir: str = "data/scope_v3"
):
    """
    Run Step3 partial re-run for diagnosis coverages only.

    Args:
        insurers: List of insurer keys (default: Samsung + KB pilot)
        output_dir: Output directory for partial results
    """
    print("=" * 80)
    print("STEP NEXT-H-1: Step3 Partial Re-run (Diagnosis Coverage Only)")
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

        # Load document set for this insurer
        try:
            document_set = load_document_set(insurer_key)
        except Exception as e:
            print(f"   ❌ Failed to load documents for {insurer_key}: {e}")
            continue

        # Initialize extractor
        extractor = CoverageAnchoredExtractor(document_set, enable_gates=True)

        # Process each diagnosis coverage row
        results = []
        for row in diagnosis_rows:
            coverage_code = row["coverage_code"]
            coverage_name = row.get("coverage_name_raw", row.get("coverage_name", ""))

            print(f"\n   Processing: {coverage_code} | {coverage_name}")

            # Extract evidence for all slots
            evidence_pack = {}
            for slot_key in EVIDENCE_PATTERNS.keys():
                candidates = extractor.extract_anchored_evidence(
                    coverage_code=coverage_code,
                    coverage_name=coverage_name,
                    slot_key=slot_key
                )

                if candidates:
                    print(f"      {slot_key}: {len(candidates)} candidates (anchored)")
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
                "partial_run": "STEP_NEXT_H",
                "anchor_method": "COVERAGE_ANCHOR_MANDATORY"
            }

            results.append(result_row)

        # Write partial output
        output_file = Path(output_dir) / f"{insurer_key}_step3_diagnosis_partial_v1.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✅ Partial Step3 output written: {output_file}")
        print(f"   Total rows: {len(results)}")

    print(f"\n{'=' * 80}")
    print("✅ STEP NEXT-H-1 완료")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP NEXT-H-1: Step3 Partial Diagnosis Re-run")
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

    run_step3_partial_diagnosis(
        insurers=args.insurers,
        output_dir=args.output_dir
    )
