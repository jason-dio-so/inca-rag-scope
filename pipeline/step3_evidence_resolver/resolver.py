"""
Evidence Resolver v1

STEP NEXT-67 / STEP NEXT-70-ANCHOR-FIX

Deterministic evidence extraction for coverage comparison.

Architecture:
1. Read coverage from step2_canonical_scope_v1.jsonl (contains coverage_code from mapping)
2. For each coverage, search documents for evidence slots:
   - start_date (보장개시일)
   - exclusions (면책사항)
   - payout_limit (지급한도/횟수)
   - reduction (감액기간/비율)
   - entry_age (가입나이)
   - waiting_period (면책기간)
3. Store evidence with locators (doc_type, page, excerpt)

NO LLM. NO INFERENCE. Pattern-based only.

Input: Step2-b canonical output (has coverage_code, canonical_name, mapping_method)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .document_reader import DocumentSet, DocumentSource, load_document_set
from .evidence_patterns import (
    PatternMatcher,
    EVIDENCE_PATTERNS,
    create_evidence_entry
)
from .gates import EvidenceGates


@dataclass
class EvidenceSlot:
    """A single evidence slot result"""
    slot_key: str
    status: str  # "FOUND" | "UNKNOWN" | "CONFLICT"
    value: Optional[str] = None  # Extracted value (if deterministic)
    reason: Optional[str] = None  # Why UNKNOWN or CONFLICT


class CoverageEvidenceResolver:
    """Resolves evidence for a single coverage"""

    def __init__(self, document_set: DocumentSet, enable_gates: bool = True):
        self.document_set = document_set
        self.pattern_matcher = PatternMatcher()
        self.gates = EvidenceGates() if enable_gates else None
        self.enable_gates = enable_gates

    def resolve(
        self,
        coverage: Dict,
        slots_to_resolve: List[str] = None
    ) -> Dict:
        """
        Resolve evidence slots for a coverage.

        Args:
            coverage: Coverage dict from step2_canonical_scope_v1.jsonl
            slots_to_resolve: List of slot keys to resolve (default: all)

        Returns:
            Dict with evidence_slots, evidence, evidence_status
        """
        if slots_to_resolve is None:
            slots_to_resolve = list(EVIDENCE_PATTERNS.keys())

        coverage_name = coverage.get("coverage_name_raw", "")

        # Initialize result structure
        evidence_slots = {}
        evidence_list = []
        evidence_status = {}

        # Search documents in order
        search_order = ["가입설계서", "상품요약서", "사업방법서", "약관"]
        documents = self.document_set.search_all_documents(search_order)

        if not documents:
            # No documents available
            for slot_key in slots_to_resolve:
                evidence_status[slot_key] = "UNKNOWN"
                evidence_slots[slot_key] = {
                    "status": "UNKNOWN",
                    "reason": "No documents available"
                }
            return {
                "evidence_slots": evidence_slots,
                "evidence": evidence_list,
                "evidence_status": evidence_status
            }

        # Resolve each slot
        for slot_key in slots_to_resolve:
            pattern = EVIDENCE_PATTERNS.get(slot_key)
            if not pattern:
                continue

            slot_result = self._resolve_slot(
                coverage_name,
                pattern,
                documents
            )

            evidence_slots[slot_key] = slot_result["slot"]
            evidence_status[slot_key] = slot_result["status"]

            if slot_result["evidences"]:
                evidence_list.extend(slot_result["evidences"])

        return {
            "evidence_slots": evidence_slots,
            "evidence": evidence_list,
            "evidence_status": evidence_status
        }

    def _resolve_slot(
        self,
        coverage_name: str,
        pattern,
        documents: List[DocumentSource]
    ) -> Dict:
        """
        Resolve a single evidence slot.

        Returns:
            {
                "slot": {status, value, reason},
                "status": "FOUND" | "UNKNOWN",
                "evidences": [...]
            }
        """
        all_candidates = []

        # Search each document
        for doc in documents:
            doc.load_text()

            for page_num in range(1, doc.get_page_count() + 1):
                page_text = doc.get_page_text(page_num)

                # Try table extraction first if prioritized
                if pattern.table_priority:
                    table_candidates = self.pattern_matcher.extract_table_candidates(
                        page_text, pattern, page_num
                    )
                    for candidate in table_candidates:
                        candidate["doc_type"] = doc.doc_type
                    all_candidates.extend(table_candidates)

                # Regular text search
                text_candidates = self.pattern_matcher.find_candidates(
                    page_text, pattern, page_num
                )
                for candidate in text_candidates:
                    candidate["doc_type"] = doc.doc_type
                all_candidates.extend(text_candidates)

        # Process results
        if not all_candidates:
            return {
                "slot": {
                    "status": "UNKNOWN",
                    "reason": f"No matches found for {pattern.slot_key}"
                },
                "status": "UNKNOWN",
                "evidences": []
            }

        # GATE: Apply validation to candidates
        if self.enable_gates:
            validated_candidates = []
            gate_reject_reasons = []

            # Extract coverage code from coverage_name (e.g., "206." from "206. 다빈치...")
            import re
            coverage_code_match = re.match(r'^(\d+)\.', coverage_name)
            coverage_code = coverage_code_match.group(1) if coverage_code_match else None

            for candidate in all_candidates:
                gate_result = self.gates.validate_candidate(
                    candidate,
                    pattern.slot_key,
                    coverage_name,
                    coverage_code
                )

                if gate_result.passed:
                    # Tag candidate with gate status
                    candidate["gate_status"] = gate_result.status
                    validated_candidates.append(candidate)
                else:
                    gate_reject_reasons.append(gate_result.reason)

            # If all candidates failed gates
            if not validated_candidates:
                # Collect unique reject reasons
                unique_reasons = list(set(gate_reject_reasons[:3]))
                return {
                    "slot": {
                        "status": "UNKNOWN",
                        "reason": f"All candidates failed gates: {'; '.join(unique_reasons)}"
                    },
                    "status": "UNKNOWN",
                    "evidences": []
                }

            all_candidates = validated_candidates

        # Take top 3 candidates (best matches)
        # Priority: FOUND > FOUND_GLOBAL, table matches, then by document order
        sorted_candidates = sorted(
            all_candidates,
            key=lambda c: (
                c.get("gate_status") != "FOUND" if self.enable_gates else False,
                c.get("gate_status") != "FOUND_GLOBAL" if self.enable_gates else False,
                not c.get("is_table", False),  # Tables first
                ["가입설계서", "상품요약서", "사업방법서", "약관"].index(
                    c.get("doc_type", "약관")
                )
            )
        )

        top_candidates = sorted_candidates[:3]

        # Create evidence entries
        evidences = [
            create_evidence_entry(c, c["doc_type"])
            for c in top_candidates
        ]

        # Add gate_status to evidence entries
        if self.enable_gates:
            for i, ev in enumerate(evidences):
                ev["gate_status"] = top_candidates[i].get("gate_status", "FOUND")

        # Attempt to extract value (if deterministic)
        extracted_value = None
        if top_candidates:
            first_candidate = top_candidates[0]
            # For numeric slots, try to extract values
            if pattern.slot_key in ["entry_age", "payout_limit", "reduction", "waiting_period"]:
                values = self.pattern_matcher.extract_numeric_values(
                    first_candidate["context"]
                )
                if values:
                    extracted_value = ", ".join(values[:3])  # Top 3 values

        # G3: Check for conflicts across documents
        final_status = "FOUND"
        conflict_reason = None

        if self.enable_gates and len(evidences) > 1:
            g3_result = self.gates.validate_evidences(evidences, pattern.slot_key)
            if g3_result.status == "CONFLICT":
                final_status = "CONFLICT"
                conflict_reason = g3_result.reason

        # Determine final status from gate_status tags
        if self.enable_gates and final_status != "CONFLICT":
            # If all evidence is FOUND_GLOBAL, downgrade status
            if all(ev.get("gate_status") == "FOUND_GLOBAL" for ev in evidences):
                final_status = "FOUND_GLOBAL"
            # If any evidence is FOUND, keep FOUND
            elif any(ev.get("gate_status") == "FOUND" for ev in evidences):
                final_status = "FOUND"
            else:
                final_status = "FOUND_GLOBAL"

        return {
            "slot": {
                "status": final_status,
                "value": extracted_value,
                "match_count": len(all_candidates),
                "reason": conflict_reason
            },
            "status": final_status,
            "evidences": evidences
        }


class BatchEvidenceResolver:
    """Batch evidence resolver for all coverages"""

    def __init__(self, insurer_key: str, sources_base_dir: str = None, enable_gates: bool = True):
        self.insurer_key = insurer_key
        self.document_set = load_document_set(insurer_key, sources_base_dir)
        self.resolver = CoverageEvidenceResolver(self.document_set, enable_gates=enable_gates)
        self.enable_gates = enable_gates

    def process_step2_file(
        self,
        input_jsonl: Path,
        output_jsonl: Path,
        slots_to_resolve: List[str] = None
    ) -> Dict[str, int]:
        """
        Process step2 canonical scope file and enrich with evidence.

        Args:
            input_jsonl: Input file (step2_canonical_scope_v1.jsonl)
            output_jsonl: Output file (step3_evidence_enriched_v1.jsonl)
            slots_to_resolve: List of evidence slots to resolve

        Returns:
            Statistics dict
        """
        stats = {
            "total_coverages": 0,
            "processed": 0,
            "slots_found": 0,
            "slots_found_global": 0,
            "slots_unknown": 0,
            "slots_conflict": 0
        }

        with open(input_jsonl, 'r', encoding='utf-8') as fin, \
             open(output_jsonl, 'w', encoding='utf-8') as fout:

            for line in fin:
                if not line.strip():
                    continue

                coverage = json.loads(line)
                stats["total_coverages"] += 1

                # Resolve evidence
                evidence_result = self.resolver.resolve(
                    coverage,
                    slots_to_resolve
                )

                # Merge into coverage
                coverage["evidence_slots"] = evidence_result["evidence_slots"]
                coverage["evidence"] = evidence_result.get("evidence", [])
                coverage["evidence_status"] = evidence_result["evidence_status"]

                # Update stats
                for status in evidence_result["evidence_status"].values():
                    if status == "FOUND":
                        stats["slots_found"] += 1
                    elif status == "FOUND_GLOBAL":
                        stats["slots_found_global"] += 1
                    elif status == "CONFLICT":
                        stats["slots_conflict"] += 1
                    else:
                        stats["slots_unknown"] += 1

                stats["processed"] += 1

                # Write enriched coverage
                fout.write(json.dumps(coverage, ensure_ascii=False) + '\n')

        return stats


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="STEP NEXT-67: Evidence Resolver v1"
    )
    parser.add_argument(
        "--insurer",
        type=str,
        required=True,
        help="Insurer key (e.g., kb, samsung)"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input JSONL file (default: data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSONL file (default: data/scope_v3/{insurer}_step3_evidence_enriched_v1.jsonl)"
    )
    parser.add_argument(
        "--slots",
        type=str,
        nargs="+",
        help="Evidence slots to resolve (default: all)"
    )

    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    input_file = args.input or (
        project_root / "data" / "scope_v3" /
        f"{args.insurer}_step2_canonical_scope_v1.jsonl"
    )
    output_file = args.output or (
        project_root / "data" / "scope_v3" /
        f"{args.insurer}_step3_evidence_enriched_v1.jsonl"
    )

    print(f"[STEP NEXT-67 / STEP NEXT-70-ANCHOR-FIX] Evidence Resolver v1")
    print(f"[Insurer] {args.insurer}")
    print(f"[Input] {input_file}")
    print(f"[Output] {output_file}")
    print()

    # Run resolver
    resolver = BatchEvidenceResolver(args.insurer)
    stats = resolver.process_step2_file(
        Path(input_file),
        Path(output_file),
        slots_to_resolve=args.slots
    )

    print(f"\n[Results]")
    print(f"  Total coverages: {stats['total_coverages']}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Slots FOUND: {stats['slots_found']}")
    print(f"  Slots FOUND_GLOBAL: {stats['slots_found_global']}")
    print(f"  Slots CONFLICT: {stats['slots_conflict']}")
    print(f"  Slots UNKNOWN: {stats['slots_unknown']}")
    total_slots = sum([stats['slots_found'], stats['slots_found_global'], stats['slots_conflict'], stats['slots_unknown']])
    if total_slots > 0:
        print(f"  Coverage-specific rate: {stats['slots_found'] / total_slots * 100:.1f}%")
        print(f"  Total evidence rate: {(stats['slots_found'] + stats['slots_found_global']) / total_slots * 100:.1f}%")


if __name__ == "__main__":
    main()
