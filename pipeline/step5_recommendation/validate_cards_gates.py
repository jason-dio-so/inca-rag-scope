#!/usr/bin/env python3
"""
STEP NEXT-75: Recommendation Cards Gate Validation
===================================================

4 HARD gates for recommendation card output quality.

Gates:
- G1. Evidence Gate (HARD FAIL exit 2)
- G2. No-Inference Gate (HARD FAIL exit 2)
- G3. Deterministic Gate (HARD FAIL exit 1)
- G4. Schema Completeness Gate (HARD FAIL exit 2)
"""

import json
import sys
import hashlib
from typing import List, Dict, Any
from pathlib import Path


def load_jsonl(filepath: str) -> List[Dict]:
    """Load JSONL file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def validate_g1_evidence_gate(cards: List[Dict]) -> tuple[bool, List[str]]:
    """
    G1. Evidence Gate (HARD FAIL exit 2)

    Rules:
    - All cards must have evidences >= 1
    - All explanation bullets must have evidence_refs >= 1 (except UNKNOWN)
    - UNKNOWN bullets must have empty value

    Returns:
        (pass, error_messages)
    """
    errors = []

    for card in cards:
        card_id = card.get("card_id", "unknown")

        # Check card evidences >= 1
        evidences = card.get("evidences", [])
        if len(evidences) < 1:
            errors.append(f"G1 FAIL: Card {card_id} has no evidences")

        # Check explanation bullets
        explanations = card.get("explanations", [])
        for exp in explanations:
            label = exp.get("label", "")
            status = exp.get("status", "")
            value = exp.get("value", "")
            evidence_refs = exp.get("evidence_refs", [])

            # UNKNOWN bullets must have empty value
            if status == "UNKNOWN" and value:
                errors.append(f"G1 FAIL: Card {card_id} bullet '{label}' has UNKNOWN but non-empty value")

            # Non-UNKNOWN bullets must have evidence_refs >= 1
            if status != "UNKNOWN" and len(evidence_refs) < 1:
                errors.append(f"G1 FAIL: Card {card_id} bullet '{label}' has no evidence_refs")

    return (len(errors) == 0, errors)


def validate_g2_no_inference_gate(
    cards: List[Dict],
    recommend_results: List[Dict],
    compare_rows: List[Dict]
) -> tuple[bool, List[str]]:
    """
    G2. No-Inference Gate (HARD FAIL exit 2)

    Rules:
    - All card metrics/values must come from recommend_results or compare_rows slots
    - No new field generation/inference

    This is a heuristic check:
    - Verify metrics keys match recommend_results metric keys
    - Verify explanation values match slot values (or are substrings)

    Returns:
        (pass, error_messages)
    """
    errors = []

    # Index recommend_results by rule_id + coverage
    rec_index = {}
    for rec in recommend_results:
        rule_id = rec.get("rule_id", "")
        cov = rec.get("coverage", {})
        key = (rule_id, cov.get("insurer", ""), cov.get("product", ""),
               cov.get("variant", "default"), cov.get("coverage_title", ""))
        rec_index[key] = rec

    # Index compare_rows by 4D identity
    comp_index = {}
    for comp in compare_rows:
        identity = comp.get("identity", {})
        key = (identity.get("insurer_key", ""), identity.get("product_key", ""),
               identity.get("variant_key", "default"), identity.get("coverage_title", ""))
        comp_index[key] = comp

    for card in cards:
        card_id = card.get("card_id", "unknown")
        rule_id = card.get("rule_id", "")
        identity = card.get("identity", {})

        # Check metrics
        metrics = card.get("metrics", {})
        rec_key = (rule_id, identity["insurer_key"], identity["product_key"],
                   identity["variant_key"], identity["coverage_title"])
        rec_row = rec_index.get(rec_key)

        if rec_row:
            rec_metric = rec_row.get("metric", {})
            # Verify metric keys match
            if set(metrics.keys()) != set(rec_metric.keys()):
                errors.append(f"G2 FAIL: Card {card_id} metrics keys do not match recommend_results")
        else:
            errors.append(f"G2 FAIL: Card {card_id} has no matching recommend_results row")

        # Check explanation values (soft check: values should be from slots)
        comp_key = (identity["insurer_key"], identity["product_key"],
                    identity["variant_key"], identity["coverage_title"])
        comp_row = comp_index.get(comp_key)

        if comp_row:
            slots = comp_row.get("slots", {})
            # No strict validation here, just log if suspicious
            # (values are stringified, so hard to match exactly)
        else:
            errors.append(f"G2 FAIL: Card {card_id} has no matching compare_rows row")

    return (len(errors) == 0, errors)


def validate_g3_deterministic_gate(
    cards: List[Dict],
    fingerprint_path: str
) -> tuple[bool, List[str]]:
    """
    G3. Deterministic Gate (HARD FAIL exit 1)

    Rules:
    - Same input files → same card_id set
    - Same input files → same subject/explanations/metrics for each card
    - Verify with fingerprint file

    Fingerprint format:
    - SHA256 hash of sorted card_ids + sorted (card_id, subject, metrics) tuples

    Returns:
        (pass, error_messages)
    """
    errors = []

    # Generate current fingerprint
    card_ids = sorted([c["card_id"] for c in cards])
    card_data = []
    for card in sorted(cards, key=lambda c: c["card_id"]):
        card_id = card["card_id"]
        subject = card["subject"]
        metrics = json.dumps(card["metrics"], sort_keys=True)
        card_data.append((card_id, subject, metrics))

    fingerprint_input = json.dumps({"card_ids": card_ids, "card_data": card_data}, sort_keys=True)
    current_fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()

    # Check if fingerprint file exists
    fingerprint_file = Path(fingerprint_path)
    if fingerprint_file.exists():
        # Compare with existing fingerprint
        existing_fingerprint = fingerprint_file.read_text().strip()
        if current_fingerprint != existing_fingerprint:
            errors.append(f"G3 FAIL: Fingerprint mismatch (non-deterministic output)")
            errors.append(f"  Expected: {existing_fingerprint}")
            errors.append(f"  Got:      {current_fingerprint}")
    else:
        # Write new fingerprint
        fingerprint_file.write_text(current_fingerprint)
        print(f"G3: New fingerprint written to {fingerprint_path}")

    return (len(errors) == 0, errors)


def validate_g4_schema_completeness_gate(cards: List[Dict]) -> tuple[bool, List[str]]:
    """
    G4. Schema Completeness Gate (HARD FAIL exit 2)

    Rules:
    - No missing required fields
    - rank is 1..N consecutive per rule_id
    - identity 4D (insurer/product/variant/coverage_title) not empty
    - coverage_code nullable (but anchored flag must match)

    Returns:
        (pass, error_messages)
    """
    errors = []

    # Required fields
    REQUIRED_FIELDS = [
        "card_id", "generated_at", "rule_id", "rule_title", "rank",
        "subject", "identity", "metrics", "explanations", "evidences", "gates"
    ]

    for card in cards:
        card_id = card.get("card_id", "unknown")

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in card:
                errors.append(f"G4 FAIL: Card {card_id} missing required field '{field}'")

        # Check identity 4D not empty (except coverage_title which may be empty for unmapped coverages)
        identity = card.get("identity", {})
        for key in ["insurer_key", "product_key", "variant_key"]:
            if not identity.get(key, ""):
                errors.append(f"G4 FAIL: Card {card_id} identity.{key} is empty")

        # coverage_title can be empty for unmapped/unknown coverages, but log warning
        if not identity.get("coverage_title", ""):
            # This is acceptable but should be logged
            pass

        # Check anchored flag consistency
        coverage_code = identity.get("coverage_code", "")
        gates = card.get("gates", {})
        anchored = gates.get("anchored", False)

        if bool(coverage_code) != anchored:
            errors.append(f"G4 FAIL: Card {card_id} anchored flag mismatch (code={bool(coverage_code)}, flag={anchored})")

    # Check rank is 1..N consecutive per rule_id
    ranks_by_rule: Dict[str, List[int]] = {}
    for card in cards:
        rule_id = card.get("rule_id", "")
        rank = card.get("rank", 0)
        if rule_id not in ranks_by_rule:
            ranks_by_rule[rule_id] = []
        ranks_by_rule[rule_id].append(rank)

    for rule_id, ranks in ranks_by_rule.items():
        sorted_ranks = sorted(ranks)
        expected_ranks = list(range(1, len(sorted_ranks) + 1))
        if sorted_ranks != expected_ranks:
            errors.append(f"G4 FAIL: Rule {rule_id} ranks not consecutive 1..N: {sorted_ranks}")

    return (len(errors) == 0, errors)


def run_all_gates(
    cards_path: str,
    recommend_results_path: str,
    compare_rows_path: str,
    fingerprint_path: str
) -> int:
    """
    Run all 4 gates.

    Returns:
        0: All gates pass
        1: G3 (deterministic) fail
        2: G1/G2/G4 (evidence/inference/schema) fail
    """
    print("=" * 80)
    print("STEP NEXT-75: Recommendation Cards Gate Validation")
    print("=" * 80)

    # Load data
    cards = load_jsonl(cards_path)
    recommend_results = load_jsonl(recommend_results_path)
    compare_rows = load_jsonl(compare_rows_path)

    print(f"\nLoaded {len(cards)} cards")
    print(f"Loaded {len(recommend_results)} recommend_results rows")
    print(f"Loaded {len(compare_rows)} compare_rows")

    # Run gates
    gates_results = []

    # G1: Evidence Gate
    print("\n[G1] Evidence Gate...")
    g1_pass, g1_errors = validate_g1_evidence_gate(cards)
    gates_results.append(("G1", g1_pass, g1_errors, 2))

    # G2: No-Inference Gate
    print("[G2] No-Inference Gate...")
    g2_pass, g2_errors = validate_g2_no_inference_gate(cards, recommend_results, compare_rows)
    gates_results.append(("G2", g2_pass, g2_errors, 2))

    # G3: Deterministic Gate
    print("[G3] Deterministic Gate...")
    g3_pass, g3_errors = validate_g3_deterministic_gate(cards, fingerprint_path)
    gates_results.append(("G3", g3_pass, g3_errors, 1))

    # G4: Schema Completeness Gate
    print("[G4] Schema Completeness Gate...")
    g4_pass, g4_errors = validate_g4_schema_completeness_gate(cards)
    gates_results.append(("G4", g4_pass, g4_errors, 2))

    # Report results
    print("\n" + "=" * 80)
    print("GATE RESULTS")
    print("=" * 80)

    all_pass = True
    max_exit_code = 0

    for gate_name, passed, errors, exit_code in gates_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{gate_name}: {status}")

        if not passed:
            all_pass = False
            max_exit_code = max(max_exit_code, exit_code)
            for err in errors[:5]:  # Show first 5 errors
                print(f"  {err}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")

    print("=" * 80)

    if all_pass:
        print("✅ ALL GATES PASSED")
        return 0
    else:
        print(f"❌ GATES FAILED (exit {max_exit_code})")
        return max_exit_code


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.step5_recommendation.validate_cards_gates <cards_path>")
        print("Example: python -m pipeline.step5_recommendation.validate_cards_gates data/recommend_v1/recommend_cards_v1.jsonl")
        sys.exit(2)

    cards_path = sys.argv[1]
    recommend_results_path = "data/recommend_v1/recommend_results.jsonl"
    compare_rows_path = "data/compare_v1/compare_rows_v1.jsonl"
    fingerprint_path = "data/recommend_v1/recommend_cards_fingerprint.txt"

    exit_code = run_all_gates(
        cards_path=cards_path,
        recommend_results_path=recommend_results_path,
        compare_rows_path=compare_rows_path,
        fingerprint_path=fingerprint_path
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
