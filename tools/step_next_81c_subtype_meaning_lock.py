#!/usr/bin/env python3
"""
STEP NEXT-81C: Subtype Coverage Meaning Lock (HARD)
Add coverage_kind field to prevent customer misinterpretation.

INPUT:  docs/audit/step_next_81b_subtype_scope_refined.jsonl
OUTPUT: docs/audit/step_next_81c_subtype_coverage_locked.jsonl

coverage_kind ∈ {
  "diagnosis_benefit",   // 진단비 자체 (진단 시 일시금)
  "treatment_trigger",   // 치료비 지급 트리거 (진단비 아님)
  "definition_only",     // 정의/예시/범위 설명
  "excluded"            // 제외 문구
}
"""

import json
import re
from pathlib import Path
from typing import Dict, List

# Coverage type keywords
DIAGNOSIS_BENEFIT_KEYWORDS = [
    r'진단비',
    r'진단\s*급여금',
    r'진단\s*자금',
    r'암\s*진단',
]

TREATMENT_BENEFIT_KEYWORDS = [
    r'치료비',
    r'수술비',
    r'항암',
    r'약물.*치료',
    r'표적.*치료',
    r'방사선.*치료',
    r'입원일당',
]


def classify_coverage_kind(row: Dict, subtype_data: Dict) -> str:
    """
    Classify coverage_kind based on coverage type and context.

    Rules (LOCK):
    1. Coverage name contains "진단비" + scope=diagnosis → diagnosis_benefit
    2. Coverage name contains "치료비/약물" + scope=diagnosis → treatment_trigger
    3. scope=definition/example → definition_only
    4. scope=excluded or covered=false → excluded
    """
    coverage_name = row.get("coverage_name", "")
    coverage_type = row.get("coverage_type", "")
    scope = subtype_data.get("scope", "")
    original_covered = subtype_data.get("original_covered", False)

    # Rule 4: Excluded
    if not original_covered or scope == "excluded":
        return "excluded"

    # Rule 3: Definition only
    if scope in ["definition", "example", "unknown"]:
        return "definition_only"

    # Rule 1: Diagnosis benefit
    # Coverage name contains "진단비" AND scope is diagnosis/treatment
    has_diagnosis_keyword = any(
        re.search(pattern, coverage_name, re.IGNORECASE)
        for pattern in DIAGNOSIS_BENEFIT_KEYWORDS
    )

    if has_diagnosis_keyword and scope in ["diagnosis", "treatment"]:
        return "diagnosis_benefit"

    # Rule 2: Treatment trigger
    # Coverage name contains "치료비/약물/수술" AND scope is diagnosis
    has_treatment_keyword = any(
        re.search(pattern, coverage_name, re.IGNORECASE)
        for pattern in TREATMENT_BENEFIT_KEYWORDS
    )

    if has_treatment_keyword and scope == "diagnosis":
        return "treatment_trigger"

    # Treatment benefit with treatment scope
    if has_treatment_keyword and scope == "treatment":
        return "treatment_trigger"

    # Default: conservative fallback
    # If we have diagnosis scope but unclear coverage type, assume treatment_trigger
    if scope == "diagnosis":
        return "treatment_trigger"

    return "excluded"


def determine_usable_as_coverage(coverage_kind: str) -> bool:
    """
    Determine if this should be usable in coverage comparisons.
    Only diagnosis_benefit is truly usable.
    """
    return coverage_kind == "diagnosis_benefit"


def determine_q13_display_rule(coverage_kind: str) -> str:
    """
    Determine how to display in Q13 output.
    """
    rules = {
        "diagnosis_benefit": "보장 O",
        "treatment_trigger": "진단 시 치료비 지급 (진단비 아님)",
        "definition_only": "정의 문맥 언급",
        "excluded": "보장 X",
    }
    return rules.get(coverage_kind, "보장 X")


def lock_subtype_coverage(row: Dict) -> Dict:
    """
    Add coverage_kind field to subtype_coverage_refined.
    Lock the meaning of "O" based on coverage type.
    """
    refined_map = row.get("subtype_coverage_refined", {})
    if not refined_map:
        return row

    locked_map = {}
    for subtype, data in refined_map.items():
        # Classify coverage_kind
        coverage_kind = classify_coverage_kind(row, data)

        # Update usable_as_coverage based on coverage_kind
        usable = determine_usable_as_coverage(coverage_kind)

        # Get Q13 display rule
        q13_display = determine_q13_display_rule(coverage_kind)

        locked_map[subtype] = {
            **data,  # Keep all original fields
            "coverage_kind": coverage_kind,
            "usable_as_coverage": usable,
            "q13_display_rule": q13_display,
            "notes_81c": f"coverage_kind={coverage_kind}, usable={usable}"
        }

    row["subtype_coverage_locked"] = locked_map
    return row


def process_and_lock(input_path: Path, output_path: Path):
    """
    Process 81B output and add coverage_kind locks.
    """
    processed = 0
    diagnosis_benefit_count = 0
    treatment_trigger_count = 0
    definition_only_count = 0
    excluded_count = 0

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        for line in fin:
            if not line.strip():
                continue

            row = json.loads(line)
            locked_row = lock_subtype_coverage(row)

            # Count coverage_kind distribution
            for subtype, data in locked_row.get("subtype_coverage_locked", {}).items():
                kind = data.get("coverage_kind", "")
                if kind == "diagnosis_benefit":
                    diagnosis_benefit_count += 1
                elif kind == "treatment_trigger":
                    treatment_trigger_count += 1
                elif kind == "definition_only":
                    definition_only_count += 1
                elif kind == "excluded":
                    excluded_count += 1

            fout.write(json.dumps(locked_row, ensure_ascii=False) + '\n')
            processed += 1

    return {
        "processed": processed,
        "diagnosis_benefit": diagnosis_benefit_count,
        "treatment_trigger": treatment_trigger_count,
        "definition_only": definition_only_count,
        "excluded": excluded_count,
    }


def validate_81c(output_path: Path) -> Dict:
    """
    Validate STEP NEXT-81C requirements:
    - treatment_trigger must NOT be displayed as "진단비 O"
    - diagnosis_benefit and treatment_trigger must be clearly separated
    """
    results = {
        "treatment_trigger_misclassified": [],
        "diagnosis_benefit_cases": [],
        "samples": [],
    }

    with open(output_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue

            row = json.loads(line)
            locked_map = row.get("subtype_coverage_locked", {})
            row_id = f"{row.get('insurer_key', '')}|{row.get('coverage_name', '')}"

            for subtype, data in locked_map.items():
                coverage_kind = data.get("coverage_kind", "")
                q13_rule = data.get("q13_display_rule", "")

                # Check: treatment_trigger must not show "보장 O"
                if coverage_kind == "treatment_trigger" and q13_rule == "보장 O":
                    results["treatment_trigger_misclassified"].append({
                        "row_id": row_id,
                        "subtype": subtype,
                        "coverage_kind": coverage_kind,
                        "q13_rule": q13_rule,
                    })

                # Collect diagnosis_benefit cases
                if coverage_kind == "diagnosis_benefit":
                    results["diagnosis_benefit_cases"].append({
                        "row_id": row_id,
                        "subtype": subtype,
                        "q13_rule": q13_rule,
                    })

                # Collect samples
                if i < 5:
                    results["samples"].append({
                        "row_id": row_id,
                        "subtype": subtype,
                        "coverage_kind": coverage_kind,
                        "scope": data.get("scope", ""),
                        "q13_display": q13_rule,
                    })

    return results


def main():
    input_path = Path("docs/audit/step_next_81b_subtype_scope_refined.jsonl")
    output_path = Path("docs/audit/step_next_81c_subtype_coverage_locked.jsonl")

    print("STEP NEXT-81C: Subtype Coverage Meaning Lock")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()

    # Process and lock
    print("Processing and locking coverage_kind...")
    stats = process_and_lock(input_path, output_path)

    print()
    print("Processing complete:")
    print(f"  Total processed: {stats['processed']}")
    print(f"  diagnosis_benefit: {stats['diagnosis_benefit']}")
    print(f"  treatment_trigger: {stats['treatment_trigger']}")
    print(f"  definition_only: {stats['definition_only']}")
    print(f"  excluded: {stats['excluded']}")
    print()

    # Validate
    print("Validating STEP NEXT-81C requirements...")
    validation = validate_81c(output_path)

    print()
    print("Validation Results:")
    print(f"  treatment_trigger misclassified as '보장 O': {len(validation['treatment_trigger_misclassified'])}")
    if validation['treatment_trigger_misclassified']:
        for case in validation['treatment_trigger_misclassified'][:3]:
            print(f"    ❌ {case['row_id']} / {case['subtype']}")

    print(f"  diagnosis_benefit cases: {len(validation['diagnosis_benefit_cases'])}")
    if validation['diagnosis_benefit_cases']:
        for case in validation['diagnosis_benefit_cases'][:3]:
            print(f"    ✅ {case['row_id']} / {case['subtype']}")

    print()
    print("Sample classifications:")
    for sample in validation['samples']:
        print(f"  {sample['row_id']}")
        print(f"    subtype: {sample['subtype']}")
        print(f"    coverage_kind: {sample['coverage_kind']}")
        print(f"    scope: {sample['scope']}")
        print(f"    Q13 display: {sample['q13_display']}")
        print()

    # Save validation results
    validation_path = Path("docs/audit/step_next_81c_validation.json")
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)

    print(f"Validation saved: {validation_path}")

    # Final status
    all_passed = len(validation['treatment_trigger_misclassified']) == 0
    print()
    print(f"DoD Status: {'✅ PASS' if all_passed else '❌ FAIL'}")
    print(f"  - treatment_trigger → 진단비 O 출력: {len(validation['treatment_trigger_misclassified'])} 건")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
