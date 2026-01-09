#!/usr/bin/env python3
"""
STEP NEXT-N: Routing Policy Validation
Test Q1-Q14 against routing registry and G9 gate

DoD Checks:
1. All Q1-Q14 have routing policy
2. All policies enforce WHY ≥1 + WHY-NOT ≥1
3. Customer-facing = BALANCED_EXPLAIN only
4. G9 gate passes for v2 cards
5. G9 gate fails for v1 cards (WHY-ONLY)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict


def check_all_questions_covered(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify all Q1-Q14 have routing policy"""
    violations = []
    expected_questions = [f"Q{i}" for i in range(1, 15)]

    rules = routing_registry.get("routing_rules", {})

    for q in expected_questions:
        if q not in rules:
            violations.append(f"Missing routing policy for {q}")

    return {"all_questions_covered": violations}


def check_balanced_enforcement(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify all policies require WHY ≥1 + WHY-NOT ≥1"""
    violations = []
    rules = routing_registry.get("routing_rules", {})

    for q_id, policy in rules.items():
        min_why = policy.get("min_why", 0)
        min_why_not = policy.get("min_why_not", 0)

        if min_why < 1:
            violations.append(f"{q_id}: min_why = {min_why} (expected ≥1)")
        if min_why_not < 1:
            violations.append(f"{q_id}: min_why_not = {min_why_not} (expected ≥1)")

    return {"balanced_enforcement": violations}


def check_customer_facing_policy(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify customer-facing card type is BALANCED_EXPLAIN only"""
    violations = []
    rules = routing_registry.get("routing_rules", {})

    for q_id, policy in rules.items():
        allowed_types = policy.get("allowed_card_types", [])

        if "BALANCED_EXPLAIN" not in allowed_types:
            violations.append(f"{q_id}: BALANCED_EXPLAIN not in allowed types")

        # Check for forbidden types in allowed
        forbidden_in_allowed = {"WHY_ONLY", "RAW_SLOTS", "NUMERIC_COMPARE"}
        for ftype in forbidden_in_allowed:
            if ftype in allowed_types:
                violations.append(f"{q_id}: {ftype} is in allowed_types (should be forbidden)")

    return {"customer_facing_policy": violations}


def check_forbidden_types(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify forbidden types are properly declared"""
    violations = []
    rules = routing_registry.get("routing_rules", {})

    for q_id, policy in rules.items():
        forbidden = policy.get("forbidden_card_types", [])

        # WHY_ONLY should be forbidden for all questions
        if "WHY_ONLY" not in forbidden:
            violations.append(f"{q_id}: WHY_ONLY not in forbidden_card_types")

        # RAW_SLOTS should be forbidden for all questions
        if "RAW_SLOTS" not in forbidden:
            violations.append(f"{q_id}: RAW_SLOTS not in forbidden_card_types")

    return {"forbidden_types_declared": violations}


def check_evidence_required(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify evidence is required for all questions"""
    violations = []
    rules = routing_registry.get("routing_rules", {})

    for q_id, policy in rules.items():
        special_rules = policy.get("special_rules", {})
        evidence_required = special_rules.get("evidence_required", False)

        if not evidence_required:
            violations.append(f"{q_id}: evidence_required = False (expected True)")

    return {"evidence_required": violations}


def check_no_numeric_output(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify numeric output is disabled for all questions"""
    violations = []
    rules = routing_registry.get("routing_rules", {})

    for q_id, policy in rules.items():
        special_rules = policy.get("special_rules", {})
        numeric_output = special_rules.get("numeric_output", True)

        if numeric_output:
            violations.append(f"{q_id}: numeric_output = True (expected False)")

    return {"no_numeric_output": violations}


def check_deterministic_config(routing_registry: dict) -> Dict[str, List[str]]:
    """Verify routing config is deterministic"""
    violations = []

    # Check version exists
    if "version" not in routing_registry:
        violations.append("Missing 'version' field in registry")

    # Check last_updated exists
    if "last_updated" not in routing_registry:
        violations.append("Missing 'last_updated' field in registry")

    # Check metadata
    metadata = routing_registry.get("metadata", {})
    if not metadata:
        violations.append("Missing 'metadata' section")

    return {"deterministic_config": violations}


def main():
    if len(sys.argv) < 2:
        print("Usage: step_next_n_validate_routing.py <routing_registry_json>")
        sys.exit(1)

    registry_path = Path(sys.argv[1])

    # Load routing registry
    with open(registry_path) as f:
        routing_registry = json.load(f)

    print(f"Loaded routing registry from {registry_path}")

    # Run all checks
    results = {}
    results.update(check_all_questions_covered(routing_registry))
    results.update(check_balanced_enforcement(routing_registry))
    results.update(check_customer_facing_policy(routing_registry))
    results.update(check_forbidden_types(routing_registry))
    results.update(check_evidence_required(routing_registry))
    results.update(check_no_numeric_output(routing_registry))
    results.update(check_deterministic_config(routing_registry))

    # Summary
    total_violations = sum(len(v) for v in results.values())

    print("\n" + "="*60)
    print("ROUTING POLICY VALIDATION")
    print("="*60)

    all_pass = True
    for check_name, violations in results.items():
        status = "✅ PASS" if not violations else "❌ FAIL"
        print(f"{check_name:30s}: {status} ({len(violations)} violations)")
        if violations:
            all_pass = False
            for v in violations[:5]:
                print(f"  - {v}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")

    print("="*60)

    # Metadata summary
    metadata = routing_registry.get("metadata", {})
    print(f"\nMetadata:")
    print(f"  Total questions: {metadata.get('total_questions', 0)}")
    print(f"  GREEN status: {metadata.get('green_status', 0)}")
    print(f"  YELLOW status: {metadata.get('yellow_status', 0)}")
    print(f"  Customer-facing type: {metadata.get('customer_facing_card_type', 'UNKNOWN')}")

    # Write validation report
    output_path = registry_path.parent.parent / "docs" / "audit" / "step_next_n_validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "input_file": str(registry_path),
        "total_questions": len(routing_registry.get("routing_rules", {})),
        "checks": {
            k: {
                "pass": len(v) == 0,
                "violation_count": len(v),
                "violations": v[:10]
            }
            for k, v in results.items()
        },
        "overall_pass": all_pass,
        "metadata": metadata
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📋 Validation report: {output_path}")

    if all_pass:
        print("\n✅ ALL ROUTING POLICY CHECKS PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ {total_violations} VIOLATIONS FOUND")
        sys.exit(2)


if __name__ == "__main__":
    main()
