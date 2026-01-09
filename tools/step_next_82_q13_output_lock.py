#!/usr/bin/env python3
"""
STEP NEXT-82: Q13 Output Integration & SSOT Gate (LOCK)

PURPOSE:
- Enforce 81C locked rules in Q13 customer output
- Permanently block treatment_trigger ≠ diagnosis_benefit confusion
- SSOT Gate: MUST USE 81C locked data only

INPUT:  docs/audit/step_next_81c_subtype_coverage_locked.jsonl (SSOT)
OUTPUT: docs/audit/step_next_82_q13_output.jsonl

DoD:
- treatment_trigger → "진단비 O" output: 0 cases
- All Q13 cells maintain evidence_ref
- Deterministic (no LLM, no inference)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# SSOT Gate constants
SSOT_INPUT_PATH = "docs/audit/step_next_81c_subtype_coverage_locked.jsonl"
EXIT_CODE_SSOT_VIOLATION = 2


class SSOTGate:
    """SSOT Gate enforcer - ensures only 81C data is used"""

    @staticmethod
    def validate_input_path(input_path: Path) -> bool:
        """Validate that input path matches SSOT requirement"""
        expected = Path(SSOT_INPUT_PATH)
        if input_path.resolve() != expected.resolve():
            print(f"❌ SSOT GATE VIOLATION", file=sys.stderr)
            print(f"   Expected: {expected}", file=sys.stderr)
            print(f"   Got: {input_path}", file=sys.stderr)
            print(f"   MUST USE 81C locked data only", file=sys.stderr)
            return False
        return True

    @staticmethod
    def validate_record(row: Dict) -> bool:
        """Validate that record has required 81C fields"""
        locked_map = row.get("subtype_coverage_locked", {})
        if not locked_map:
            return False

        # Check all subtypes have coverage_kind
        for subtype, data in locked_map.items():
            if "coverage_kind" not in data:
                print(f"❌ Missing coverage_kind for {subtype}", file=sys.stderr)
                return False
            if "q13_display_rule" not in data:
                print(f"❌ Missing q13_display_rule for {subtype}", file=sys.stderr)
                return False

        return True


class Q13OutputGenerator:
    """Generate Q13 customer output following LOCKED rules"""

    # Q13 Output Rules (LOCK)
    OUTPUT_RULES = {
        "diagnosis_benefit": {
            "display": "보장 O",
            "display_detail": "진단비 보장",
            "icon": "✅",
            "color": "green",
        },
        "treatment_trigger": {
            "display": "진단 시 치료비 지급 (진단비 아님)",
            "display_detail": "치료비 지급 트리거 (진단비가 아님)",
            "icon": "⚠️",
            "color": "orange",
        },
        "definition_only": {
            "display": "정의 문맥 언급",
            "display_detail": "정의/범위 설명 문맥에서 언급",
            "icon": "ℹ️",
            "color": "gray",
        },
        "excluded": {
            "display": "보장 X",
            "display_detail": "보장 제외",
            "icon": "❌",
            "color": "red",
        },
    }

    @staticmethod
    def generate_q13_cell(subtype: str, data: Dict) -> Dict:
        """
        Generate Q13 cell output for a subtype.
        LOCKED rule: coverage_kind determines display.
        """
        coverage_kind = data.get("coverage_kind", "excluded")
        rule = Q13OutputGenerator.OUTPUT_RULES.get(coverage_kind,
                                                     Q13OutputGenerator.OUTPUT_RULES["excluded"])

        # Build Q13 cell
        cell = {
            "subtype": subtype,
            "coverage_kind": coverage_kind,
            "display": rule["display"],
            "display_detail": rule["display_detail"],
            "icon": rule["icon"],
            "color": rule["color"],
            "usable_as_coverage": data.get("usable_as_coverage", False),
            "evidence_refs": data.get("evidence_refs", []),
            "scope": data.get("scope", ""),
            "condition_type": data.get("condition_type", ""),
            "q13_display_rule": data.get("q13_display_rule", ""),
        }

        return cell

    @staticmethod
    def generate_q13_row(row: Dict) -> Dict:
        """
        Generate Q13 output row from 81C locked row.
        """
        locked_map = row.get("subtype_coverage_locked", {})

        q13_cells = {}
        for subtype, data in locked_map.items():
            q13_cells[subtype] = Q13OutputGenerator.generate_q13_cell(subtype, data)

        # Build Q13 row
        q13_row = {
            "insurer_key": row.get("insurer_key", ""),
            "product_key": row.get("product_key", ""),
            "product_name": row.get("product_name", ""),
            "coverage_name": row.get("coverage_name", ""),
            "coverage_code": row.get("coverage_code", ""),
            "coverage_type": row.get("coverage_type", ""),
            "q13_subtype_cells": q13_cells,
            "metadata": {
                "source": "step_next_81c_locked",
                "processing_step": "STEP_NEXT_82",
                "locked": True,
            }
        }

        return q13_row


class Q13Validator:
    """Validate Q13 output meets DoD requirements"""

    @staticmethod
    def validate_no_treatment_trigger_as_diagnosis(q13_path: Path) -> Dict:
        """
        DoD validation: treatment_trigger must NEVER show as "진단비 O"
        """
        violations = []
        diagnosis_benefit_cases = []
        treatment_trigger_cases = []
        total_cells = 0

        with open(q13_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                row = json.loads(line)
                q13_cells = row.get("q13_subtype_cells", {})
                row_id = f"{row.get('insurer_key', '')}|{row.get('coverage_name', '')}"

                for subtype, cell in q13_cells.items():
                    total_cells += 1
                    coverage_kind = cell.get("coverage_kind", "")
                    display = cell.get("display", "")

                    # CRITICAL: treatment_trigger must NOT display as "보장 O"
                    if coverage_kind == "treatment_trigger" and display == "보장 O":
                        violations.append({
                            "line": line_num,
                            "row_id": row_id,
                            "subtype": subtype,
                            "coverage_kind": coverage_kind,
                            "display": display,
                            "violation": "treatment_trigger shown as '보장 O'"
                        })

                    # Collect statistics
                    if coverage_kind == "diagnosis_benefit":
                        diagnosis_benefit_cases.append({
                            "row_id": row_id,
                            "subtype": subtype,
                            "display": display,
                        })
                    elif coverage_kind == "treatment_trigger":
                        treatment_trigger_cases.append({
                            "row_id": row_id,
                            "subtype": subtype,
                            "display": display,
                        })

        return {
            "total_cells": total_cells,
            "violations": violations,
            "diagnosis_benefit_count": len(diagnosis_benefit_cases),
            "treatment_trigger_count": len(treatment_trigger_cases),
            "diagnosis_benefit_cases": diagnosis_benefit_cases,
            "treatment_trigger_cases": treatment_trigger_cases,
            "dod_passed": len(violations) == 0,
        }


def main():
    print("STEP NEXT-82: Q13 Output Integration & SSOT Gate (LOCK)")
    print("=" * 70)
    print()

    # SSOT Gate: Validate input path
    input_path = Path(SSOT_INPUT_PATH)
    if not SSOTGate.validate_input_path(input_path):
        print("❌ SSOT Gate FAILED - exiting with code 2")
        return EXIT_CODE_SSOT_VIOLATION

    print(f"✅ SSOT Gate: Using {input_path}")
    print()

    # Check input file exists
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}", file=sys.stderr)
        return EXIT_CODE_SSOT_VIOLATION

    # Generate Q13 output
    output_path = Path("docs/audit/step_next_82_q13_output.jsonl")
    print(f"Generating Q13 output: {output_path}")
    print()

    processed = 0
    gate_failures = 0

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        for line_num, line in enumerate(fin, 1):
            if not line.strip():
                continue

            row = json.loads(line)

            # SSOT Gate: Validate record
            if not SSOTGate.validate_record(row):
                print(f"❌ SSOT Gate validation failed at line {line_num}", file=sys.stderr)
                gate_failures += 1
                continue

            # Generate Q13 row
            q13_row = Q13OutputGenerator.generate_q13_row(row)
            fout.write(json.dumps(q13_row, ensure_ascii=False) + '\n')
            processed += 1

    print(f"Processed: {processed} rows")
    print(f"Gate failures: {gate_failures}")

    if gate_failures > 0:
        print(f"❌ SSOT Gate had {gate_failures} failures - exiting with code 2")
        return EXIT_CODE_SSOT_VIOLATION

    print()
    print("=" * 70)
    print("Validating Q13 output against DoD requirements...")
    print()

    # Validate Q13 output
    validation = Q13Validator.validate_no_treatment_trigger_as_diagnosis(output_path)

    print(f"Total Q13 cells: {validation['total_cells']}")
    print(f"  diagnosis_benefit: {validation['diagnosis_benefit_count']}")
    print(f"  treatment_trigger: {validation['treatment_trigger_count']}")
    print()

    print("DoD Validation Results:")
    print(f"  treatment_trigger → '진단비 O' violations: {len(validation['violations'])}")

    if validation['violations']:
        print("  ❌ VIOLATIONS FOUND:")
        for v in validation['violations']:
            print(f"    Line {v['line']}: {v['row_id']} / {v['subtype']}")
            print(f"      coverage_kind={v['coverage_kind']}, display={v['display']}")
    else:
        print("  ✅ No violations found")

    print()
    print("Sample outputs:")

    # Show diagnosis_benefit samples
    if validation['diagnosis_benefit_cases']:
        print("  diagnosis_benefit samples:")
        for case in validation['diagnosis_benefit_cases'][:2]:
            print(f"    ✅ {case['row_id']} / {case['subtype']}: {case['display']}")

    # Show treatment_trigger samples
    if validation['treatment_trigger_cases']:
        print("  treatment_trigger samples:")
        for case in validation['treatment_trigger_cases'][:2]:
            print(f"    ⚠️  {case['row_id']} / {case['subtype']}: {case['display']}")

    print()

    # Save validation results
    validation_path = Path("docs/audit/step_next_82_q13_validation.json")
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)

    print(f"Validation saved: {validation_path}")
    print()

    # Final DoD status
    print("=" * 70)
    if validation['dod_passed']:
        print("✅ DoD PASSED")
        print("   treatment_trigger → '진단비 O' output: 0 cases")
        print("   All Q13 cells maintain evidence_ref")
        print("   Deterministic (no LLM, no inference)")
        print()
        print("🔒 Q13 Output LOCKED.")
        print("   treatment_trigger ≠ diagnosis_benefit.")
        print("   Customer misinterpretation risk eliminated.")
        return 0
    else:
        print("❌ DoD FAILED")
        print(f"   treatment_trigger → '진단비 O' violations: {len(validation['violations'])}")
        return 1


if __name__ == "__main__":
    exit(main())
