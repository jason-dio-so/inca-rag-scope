#!/usr/bin/env python3
"""
STEP NEXT-45-C-β: KB Gate Test

Hard gate: KB must have zero empty coverage names after hybrid extraction.
"""

import json
from pathlib import Path


def test_kb_no_empty_coverage_names():
    """
    KB GATE: Verify KB extracted facts have NO empty coverage names.

    Background:
    - KB pages 2-3 have coverage names as text blocks (not in table cells)
    - pdfplumber returns empty coverage names (100% empty ratio)
    - Hybrid extractor must extract coverage names from text blocks
    """
    kb_facts_path = Path("data/scope_v3/kb_step1_raw_scope_v3.jsonl")

    assert kb_facts_path.exists(), f"KB facts not found: {kb_facts_path}"

    # Load KB facts
    facts = []
    with open(kb_facts_path, "r", encoding="utf-8") as f:
        for line in f:
            fact = json.loads(line)
            facts.append(fact)

    # Gate 1: Must have extracted facts
    assert len(facts) > 0, "KB extracted 0 facts (should have >0)"

    # Gate 2: Zero empty coverage names
    empty_count = 0
    for fact in facts:
        coverage_name = fact.get("coverage_name_raw", "").strip()
        if not coverage_name:
            empty_count += 1

    assert empty_count == 0, (
        f"KB GATE FAILED: {empty_count} facts have empty coverage names "
        f"(out of {len(facts)} total facts)"
    )

    print(f"✅ KB GATE PASSED: All {len(facts)} facts have non-empty coverage names")


def test_kb_evidence_present():
    """
    Evidence Gate: All KB facts must have at least one evidence record.
    """
    kb_facts_path = Path("data/scope_v3/kb_step1_raw_scope_v3.jsonl")

    assert kb_facts_path.exists(), f"KB facts not found: {kb_facts_path}"

    # Load KB facts
    facts = []
    with open(kb_facts_path, "r", encoding="utf-8") as f:
        for line in f:
            fact = json.loads(line)
            facts.append(fact)

    # Check evidence
    no_evidence_count = 0
    for fact in facts:
        evidences = fact.get("proposal_facts", {}).get("evidences", [])
        if not evidences or len(evidences) == 0:
            no_evidence_count += 1

    assert no_evidence_count == 0, (
        f"Evidence GATE FAILED: {no_evidence_count} facts have no evidence "
        f"(out of {len(facts)} total facts)"
    )

    print(f"✅ Evidence GATE PASSED: All {len(facts)} facts have evidence")


def test_kb_coverage_sample():
    """
    Sanity check: Verify top 5 KB facts have expected structure.
    """
    kb_facts_path = Path("data/scope_v3/kb_step1_raw_scope_v3.jsonl")

    assert kb_facts_path.exists(), f"KB facts not found: {kb_facts_path}"

    # Load KB facts
    facts = []
    with open(kb_facts_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 5:  # Only check first 5
                break
            fact = json.loads(line)
            facts.append(fact)

    # Check structure
    for idx, fact in enumerate(facts):
        coverage_name = fact.get("coverage_name_raw", "")
        proposal_facts = fact.get("proposal_facts", {})

        # Must have coverage name
        assert coverage_name and coverage_name.strip(), f"Fact {idx + 1}: Empty coverage name"

        # Must have amount/premium/period
        amount = proposal_facts.get("coverage_amount_text")
        premium = proposal_facts.get("premium_text")
        period = proposal_facts.get("period_text")

        assert amount, f"Fact {idx + 1}: Missing amount"
        assert premium, f"Fact {idx + 1}: Missing premium"
        assert period, f"Fact {idx + 1}: Missing period"

        # Must have evidence with page and y-coordinates
        evidences = proposal_facts.get("evidences", [])
        assert len(evidences) > 0, f"Fact {idx + 1}: No evidence"

        evidence = evidences[0]
        assert "page" in evidence, f"Fact {idx + 1}: Evidence missing page"
        assert "y0" in evidence or "row_index" in evidence, (
            f"Fact {idx + 1}: Evidence missing position (y0 or row_index)"
        )

        print(f"  [{idx + 1}] {coverage_name} | {amount} | {premium} | {period}")

    print(f"✅ KB sample check PASSED: {len(facts)} facts validated")


if __name__ == "__main__":
    test_kb_no_empty_coverage_names()
    test_kb_evidence_present()
    test_kb_coverage_sample()
    print("\n✅ All KB gates PASSED")
