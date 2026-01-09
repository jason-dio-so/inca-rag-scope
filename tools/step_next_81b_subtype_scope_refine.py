#!/usr/bin/env python3
"""
STEP NEXT-81B: Subtype Coverage Scope Refinement (LOCK)
Deterministic, rule-based classification only. NO LLM.

INPUT:  docs/audit/step_next_81_subtype_coverage.jsonl
OUTPUT: docs/audit/step_next_81b_subtype_scope_refined.jsonl

Rules:
- Split/filter/sample to avoid reading entire file
- Only process decision=O or items with inclusion evidence
- Classify scope: diagnosis|treatment|definition|example|unknown
- Apply GATE-81B rules
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Scope classification patterns (deterministic)
DIAGNOSIS_PATTERNS = [
    r'진단\s*확정\s*시',
    r'진단이\s*확정된\s*경우',
    r'진단받은\s*때',
    r'진단\s*시\s*지급',
    r'진단\s*받았을\s*때',
    r'진단\s*시',
]

TREATMENT_PATTERNS = [
    r'치료',
    r'수술',
    r'항암',
    r'약물허가치료',
    r'방사선',
    r'표적치료',
    r'입원일당',
    r'항암제',
    r'약물',
]

DEFINITION_PATTERNS = [
    r'유사암',
    r'정의',
    r'분류',
    r'해당하는',
    r'기타피부암',
    r'갑상선암',
    r'제자리암',
    r'경계성종양',
    r'상피내암',
    r'범위',
    r'다음의',
]

EXAMPLE_PATTERNS = [
    r'예를\s*들어',
    r'예시',
    r'참고',
    r'예\)',
    r'다음과\s*같',
]


def classify_scope(excerpt: str) -> str:
    """
    Classify scope based on excerpt content.
    Priority: diagnosis/treatment > definition > example > unknown
    """
    excerpt_lower = excerpt.lower()

    # Check diagnosis/treatment triggers first (highest priority)
    has_diagnosis = any(re.search(p, excerpt, re.IGNORECASE) for p in DIAGNOSIS_PATTERNS)
    has_treatment = any(re.search(p, excerpt, re.IGNORECASE) for p in TREATMENT_PATTERNS)

    if has_diagnosis:
        return "diagnosis"
    if has_treatment:
        return "treatment"

    # Check definition patterns
    has_definition = any(re.search(p, excerpt, re.IGNORECASE) for p in DEFINITION_PATTERNS)
    if has_definition:
        # Make sure it's not a trigger context
        if not (has_diagnosis or has_treatment):
            return "definition"

    # Check example patterns
    has_example = any(re.search(p, excerpt, re.IGNORECASE) for p in EXAMPLE_PATTERNS)
    if has_example:
        return "example"

    return "unknown"


def determine_condition_type(scope: str) -> str:
    """Map scope to condition_type"""
    mapping = {
        "diagnosis": "지급사유",
        "treatment": "지급사유",
        "definition": "정의",
        "example": "예시",
        "unknown": "기타",
    }
    return mapping.get(scope, "기타")


def refine_subtype_coverage(row: Dict) -> Dict:
    """
    Refine a single row's subtype_coverage structure.
    Add scope/condition_type/evidence_refs fields.
    """
    subtype_coverage = row.get("subtype_coverage", {})
    if not subtype_coverage:
        return row

    refined_map = {}
    for subtype, data in subtype_coverage.items():
        covered = data.get("covered", False)
        evidence = data.get("evidence", [])

        # Classify scope based on evidence
        scope = "unknown"
        if evidence:
            # Use first evidence excerpt for classification
            scope = classify_scope(evidence[0].get("excerpt", ""))

        # Determine decision based on scope
        # GATE-81B-2: definition/example/unknown -> X or usable_as_coverage=false
        original_decision = "O" if covered else "X"
        final_decision = original_decision
        usable_as_coverage = True

        if scope in ["definition", "example", "unknown"] and original_decision == "O":
            # Conservative: downgrade to X
            final_decision = "X"
            usable_as_coverage = False

        # Format evidence refs
        evidence_refs = []
        for ev in evidence[:3]:  # Top 3 evidence
            evidence_refs.append({
                "doc_type": ev.get("doc_type", ""),
                "page": f"{ev.get('page_start', '')}-{ev.get('page_end', '')}" if ev.get('page_start') else "",
                "excerpt": ev.get("excerpt", ""),
                "locator": ev.get("locator", ""),
            })

        refined_map[subtype] = {
            "decision": final_decision,
            "original_decision": original_decision,
            "original_covered": covered,
            "scope": scope,
            "condition_type": determine_condition_type(scope),
            "evidence_refs": evidence_refs,
            "usable_as_coverage": usable_as_coverage,
            "confidence": data.get("confidence", ""),
            "reason": data.get("reason", ""),
            "notes": f"Scope: {scope}, Original: {original_decision}"
        }

    row["subtype_coverage_refined"] = refined_map
    return row


def process_file_in_chunks(input_path: Path, output_path: Path, chunk_size: int = 1000):
    """
    Process file in chunks to avoid memory issues.
    Filter: only process rows with covered=true.
    """
    processed_count = 0
    filtered_count = 0
    o_decision_count = 0

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        chunk = []
        for line in fin:
            if not line.strip():
                continue

            row = json.loads(line)

            # Filter: only process if has covered=true in any subtype
            subtype_coverage = row.get("subtype_coverage", {})
            has_o_decision = any(data.get("covered", False) for data in subtype_coverage.values())

            if not has_o_decision:
                filtered_count += 1
                continue

            # Process this row
            o_decision_count += 1
            refined_row = refine_subtype_coverage(row)
            fout.write(json.dumps(refined_row, ensure_ascii=False) + '\n')
            processed_count += 1

            # Progress indicator
            if processed_count % 100 == 0:
                print(f"Processed: {processed_count}, Filtered out: {filtered_count}")

    return {
        "processed_count": processed_count,
        "filtered_count": filtered_count,
        "o_decision_count": o_decision_count,
    }


def validate_gate_81b(output_path: Path) -> Dict[str, any]:
    """
    Validate GATE-81B rules:
    GATE-81B-1: All O items must have scope filled
    GATE-81B-2: definition/example/unknown must have usable_as_coverage=false
    GATE-81B-3: Sample 10 items for manual review
    """
    results = {
        "gate_81b_1": {"passed": True, "failures": []},
        "gate_81b_2": {"passed": True, "failures": []},
        "gate_81b_3": {"samples": []},
    }

    with open(output_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue

            row = json.loads(line)
            refined_map = row.get("subtype_coverage_refined", {})
            row_id = f"{row.get('insurer_key', '')}|{row.get('product_name', '')}|{row.get('coverage_name', '')}"

            for subtype, data in refined_map.items():
                # GATE-81B-1: scope must be filled for O items
                if data.get("original_decision") == "O":
                    if not data.get("scope") or data.get("scope") == "unknown":
                        if data.get("evidence_refs"):  # Only fail if we had evidence
                            results["gate_81b_1"]["passed"] = False
                            results["gate_81b_1"]["failures"].append({
                                "row_id": row_id,
                                "subtype": subtype,
                                "scope": data.get("scope", "missing"),
                            })

                # GATE-81B-2: definition/example/unknown must not be usable
                if data.get("scope") in ["definition", "example", "unknown"]:
                    if data.get("usable_as_coverage", True):
                        results["gate_81b_2"]["passed"] = False
                        results["gate_81b_2"]["failures"].append({
                            "row_id": row_id,
                            "subtype": subtype,
                            "scope": data.get("scope"),
                            "usable_as_coverage": data.get("usable_as_coverage"),
                        })

            # GATE-81B-3: Collect samples
            if i < 10:
                sample = {
                    "row_id": row_id,
                    "subtypes": {}
                }
                for subtype, data in refined_map.items():
                    sample["subtypes"][subtype] = {
                        "decision": data.get("decision"),
                        "scope": data.get("scope"),
                        "condition_type": data.get("condition_type"),
                        "evidence_excerpt": data.get("evidence_refs", [{}])[0].get("excerpt", "")[:200] if data.get("evidence_refs") else "",
                    }
                results["gate_81b_3"]["samples"].append(sample)

    return results


def main():
    input_path = Path("docs/audit/step_next_81_subtype_coverage.jsonl")
    output_path = Path("docs/audit/step_next_81b_subtype_scope_refined.jsonl")

    print("STEP NEXT-81B: Subtype Scope Refinement")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()

    # Process file in chunks
    print("Processing...")
    stats = process_file_in_chunks(input_path, output_path)

    print()
    print("Processing complete:")
    print(f"  Processed: {stats['processed_count']}")
    print(f"  Filtered out (X only): {stats['filtered_count']}")
    print(f"  O-decision items: {stats['o_decision_count']}")
    print()

    # Validate GATE-81B
    print("Validating GATE-81B rules...")
    validation = validate_gate_81b(output_path)

    print()
    print("GATE-81B-1 (All O items have scope):")
    print(f"  Status: {'✅ PASS' if validation['gate_81b_1']['passed'] else '❌ FAIL'}")
    if not validation['gate_81b_1']['passed']:
        print(f"  Failures: {len(validation['gate_81b_1']['failures'])}")
        for failure in validation['gate_81b_1']['failures'][:5]:
            print(f"    - {failure['row_id']} / {failure['subtype']}: scope={failure['scope']}")

    print()
    print("GATE-81B-2 (definition/example/unknown not usable):")
    print(f"  Status: {'✅ PASS' if validation['gate_81b_2']['passed'] else '❌ FAIL'}")
    if not validation['gate_81b_2']['passed']:
        print(f"  Failures: {len(validation['gate_81b_2']['failures'])}")
        for failure in validation['gate_81b_2']['failures'][:5]:
            print(f"    - {failure['row_id']} / {failure['subtype']}: scope={failure['scope']}, usable={failure['usable_as_coverage']}")

    print()
    print("GATE-81B-3 (Sample 10 for review):")
    for i, sample in enumerate(validation['gate_81b_3']['samples'], 1):
        print(f"\nSample {i}: {sample['row_id']}")
        for subtype, data in sample['subtypes'].items():
            print(f"  {subtype}:")
            print(f"    decision: {data['decision']}")
            print(f"    scope: {data['scope']}")
            print(f"    condition_type: {data['condition_type']}")
            if data['evidence_excerpt']:
                print(f"    evidence: {data['evidence_excerpt']}...")

    # Save validation results
    validation_path = Path("docs/audit/step_next_81b_validation.json")
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)

    print()
    print(f"Validation results saved: {validation_path}")

    # Final status
    all_passed = validation['gate_81b_1']['passed'] and validation['gate_81b_2']['passed']
    print()
    print(f"Overall GATE Status: {'✅ ALL PASS' if all_passed else '❌ GATE FAILURE'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
