"""
STEP NEXT-H-2: Row Locator Fix (v2) - Similarity-Based Matching

목표: MISSING 84% → < 30% by improving row anchor detection

핵심 변경:
1. Row 후보 생성 (넓게): 진단비/치료비/수술비 등 패턴으로 후보 추출
2. 타겟 담보명 유사도 스코어링 (정확): Token overlap + substring matching
3. Cross-coverage 차단: 다른 담보 강 매칭 시 penalty
4. Top-1 row 선택: score >= threshold만 사용

HARD LOCK:
- ❌ Coverage anchor 삽입 금지
- ❌ G5 완화 금지
- ✅ Row-only 유지
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

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


def normalize_coverage_name(name: str) -> str:
    """
    Normalize coverage name for matching.

    Remove:
    - Number prefixes (70., 85., etc.)
    - Spaces
    - Parentheses
    - Roman numerals (Ⅱ, Ⅲ)
    - [갱신형] markers
    """
    # Remove number prefix
    name = re.sub(r"^\d+\.\s*", "", name)

    # Remove brackets and markers
    name = re.sub(r"\[갱신형\]|\[.*?\]", "", name)

    # Remove Roman numerals
    name = re.sub(r"[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹ]", "", name)

    # Remove spaces and parentheses
    name = re.sub(r"[() \t]", "", name)

    # Lowercase for case-insensitive matching
    name = name.lower()

    return name


def extract_tokens(text: str) -> List[str]:
    """Extract meaningful tokens from text"""
    # Split by common delimiters
    tokens = re.findall(r"[가-힣a-zA-Z0-9]+", text)
    return [t.lower() for t in tokens if len(t) >= 2]


@dataclass
class RowCandidate:
    """Row candidate with metadata"""
    line_idx: int
    row_text: str
    row_blob: str  # Row + following lines
    normalized: str
    tokens: List[str]
    page: int = 0


class ImprovedRowLocator:
    """Improved row locator with similarity-based matching"""

    # Row start patterns (broad)
    ROW_START_PATTERNS = [
        r"^\s*\d+\.\s*.{2,80}(진단비|치료비|수술비|입원일당|수술급|통원)",
        r"^\s*[가-힣\s]{2,80}(진단비|치료비|수술비|입원일당)",
        r"^.{2,80}(암|뇌졸중|허혈성심장질환|급성심근경색|고액암|유사암).{0,30}(진단비|치료비)",
    ]

    def __init__(self, registry: Dict):
        self.registry = registry

        # Build normalized coverage names for all registry entries
        self.registry_normalized = {}
        for code, entry in registry.items():
            canonical = entry.get("canonical_name", "")
            self.registry_normalized[code] = {
                "canonical": canonical,
                "normalized": normalize_coverage_name(canonical),
                "tokens": extract_tokens(normalize_coverage_name(canonical))
            }

    def find_row_candidates(self, doc) -> List[RowCandidate]:
        """
        Find row candidates using broad patterns.

        Returns all potential coverage rows for scoring.
        """
        doc_text = doc.get_all_text()
        lines = doc_text.split("\n")

        candidates = []

        for i, line in enumerate(lines):
            # Check if line matches any row start pattern
            is_row_start = False
            for pattern in self.ROW_START_PATTERNS:
                if re.search(pattern, line):
                    is_row_start = True
                    break

            if not is_row_start:
                continue

            # Build row blob (current line + 1-3 following lines)
            following_lines = []
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j].strip()

                # Stop if we hit another row start or separator
                if any(re.search(p, next_line) for p in self.ROW_START_PATTERNS):
                    break
                if re.match(r"^[─│┼├┤┬┴┌┐└┘\-|=_\s]+$", next_line):
                    break
                if not next_line:
                    break

                following_lines.append(next_line)

            row_blob = line + "\n" + "\n".join(following_lines[:3])
            normalized = normalize_coverage_name(row_blob)
            tokens = extract_tokens(normalized)

            candidate = RowCandidate(
                line_idx=i,
                row_text=line.strip(),
                row_blob=row_blob,
                normalized=normalized,
                tokens=tokens,
                page=0
            )

            candidates.append(candidate)

        return candidates

    def score_candidate(
        self,
        candidate: RowCandidate,
        target_code: str,
        target_name: str
    ) -> float:
        """
        Score row candidate for target coverage.

        Scoring components:
        1. Token overlap (weighted)
        2. Substring matching
        3. Sequence similarity (difflib)
        4. Cross-coverage penalty

        Returns: score in [0, 1]
        """
        target_normalized = normalize_coverage_name(target_name)
        target_tokens = extract_tokens(target_normalized)

        # Component 1: Token overlap
        common_tokens = set(target_tokens) & set(candidate.tokens)
        token_overlap = len(common_tokens) / max(len(target_tokens), 1) if target_tokens else 0

        # Component 2: Substring matching
        substring_score = 0.0
        if target_normalized in candidate.normalized:
            substring_score = 1.0
        elif len(target_normalized) >= 4:
            # Check for partial substring
            target_parts = [target_normalized[i:i+4] for i in range(len(target_normalized) - 3)]
            matches = sum(1 for part in target_parts if part in candidate.normalized)
            substring_score = matches / len(target_parts) if target_parts else 0

        # Component 3: Sequence similarity
        sequence_sim = SequenceMatcher(None, target_normalized, candidate.normalized).ratio()

        # Base score
        base_score = (
            token_overlap * 0.5 +
            substring_score * 0.3 +
            sequence_sim * 0.2
        )

        # Component 4: Cross-coverage penalty
        penalty = self._compute_cross_coverage_penalty(
            candidate=candidate,
            target_code=target_code
        )

        final_score = base_score * (1.0 - penalty)

        return final_score

    def _compute_cross_coverage_penalty(
        self,
        candidate: RowCandidate,
        target_code: str
    ) -> float:
        """
        Compute penalty if candidate strongly matches OTHER diagnosis coverages.

        Returns: penalty in [0, 1]
        """
        max_other_score = 0.0

        for code, info in self.registry_normalized.items():
            if code == target_code:
                continue

            # Check if other coverage name appears in candidate
            other_normalized = info["normalized"]
            other_tokens = info["tokens"]

            # Token overlap with other coverage
            common = set(other_tokens) & set(candidate.tokens)
            overlap = len(common) / max(len(other_tokens), 1) if other_tokens else 0

            # Substring match with other coverage
            substring = 1.0 if other_normalized in candidate.normalized else 0.0

            other_score = overlap * 0.6 + substring * 0.4
            max_other_score = max(max_other_score, other_score)

        # Strong match to other coverage = high penalty
        if max_other_score > 0.7:
            return 0.8
        elif max_other_score > 0.5:
            return 0.5
        elif max_other_score > 0.3:
            return 0.2

        return 0.0

    def find_best_row(
        self,
        doc,
        target_code: str,
        target_name: str,
        score_threshold: float = 0.4
    ) -> Optional[RowCandidate]:
        """
        Find best row for target coverage using similarity scoring.

        Args:
            doc: Document to search
            target_code: Target coverage code
            target_name: Target coverage name
            score_threshold: Minimum score to accept (default 0.4)

        Returns:
            Best RowCandidate or None if no candidate meets threshold
        """
        candidates = self.find_row_candidates(doc)

        if not candidates:
            return None

        # Score all candidates
        scored = []
        for candidate in candidates:
            score = self.score_candidate(
                candidate=candidate,
                target_code=target_code,
                target_name=target_name
            )
            scored.append((score, candidate))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top-1 if above threshold
        best_score, best_candidate = scored[0]

        if best_score >= score_threshold:
            return best_candidate

        return None


class RowOnlyExtractorV2:
    """Row-only evidence extractor v2 with improved locator"""

    def __init__(self, document_set, registry: Dict):
        self.document_set = document_set
        self.locator = ImprovedRowLocator(registry)

    def extract_row_evidence(
        self,
        coverage_code: str,
        coverage_name: str,
        slot_key: str
    ) -> List[Dict]:
        """
        Extract evidence using improved row locator v2.

        Returns:
            List of evidence candidates (NO ANCHOR INSERTION)
        """
        pattern = EVIDENCE_PATTERNS.get(slot_key)
        if not pattern:
            return []

        candidates = []

        # Search documents in priority order
        search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]
        documents = self.document_set.search_all_documents(search_order)

        for doc in documents:
            # Find best row for this coverage
            best_row = self.locator.find_best_row(
                doc=doc,
                target_code=coverage_code,
                target_name=coverage_name,
                score_threshold=0.4
            )

            if not best_row:
                continue

            # Check if slot keyword present in row blob
            has_slot_keyword = any(
                kw in best_row.row_blob for kw in pattern.keywords
            )

            if not has_slot_keyword:
                continue

            # Extract context around slot keyword
            context = self._extract_slot_context(
                row_blob=best_row.row_blob,
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
                "page": best_row.page,
                "line_text": best_row.row_text,
                "context": context,
                "row_blob": best_row.row_blob,
                "extraction_method": "row_only_v2_similarity"
            }

            candidates.append(candidate)

        return candidates

    def _extract_slot_context(
        self,
        row_blob: str,
        slot_keywords: List[str],
        context_lines: int
    ) -> str:
        """Extract context around slot keyword within row blob"""
        lines = row_blob.split("\n")

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


def run_step3_rowonly_v2(
    insurers: List[str] = ["samsung", "kb"],
    output_dir: str = "data/scope_v3"
):
    """
    Run Step3 row-only v2 with improved row locator.
    """
    print("=" * 80)
    print("STEP NEXT-H-2: Row-Only v2 (Improved Locator)")
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

        # Initialize v2 extractor
        extractor = RowOnlyExtractorV2(document_set, registry)

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
                    print(f"      {slot_key}: {len(candidates)} candidates (v2)")
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
                "partial_run": "STEP_NEXT_H2_V2",
                "extraction_method": "row_only_v2_similarity"
            }

            results.append(result_row)

        # Write v2 output
        output_file = Path(output_dir) / f"{insurer_key}_step3_diagnosis_rowonly_v2.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✅ Row-only v2 output written: {output_file}")
        print(f"   Total rows: {len(results)}")

    print(f"\n{'=' * 80}")
    print("✅ STEP NEXT-H-2 v2 완료")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STEP NEXT-H-2: Row-Only v2 with Improved Locator")
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

    run_step3_rowonly_v2(
        insurers=args.insurers,
        output_dir=args.output_dir
    )
