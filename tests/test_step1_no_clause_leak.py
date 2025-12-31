"""
STEP NEXT-45-C-β-4 P0-F2: Clause Leak Detection Gate Test

Ensures that extracted facts do not contain clause-heavy/invalid coverage names.
This prevents Pass B from extracting detail table rows with long clause descriptions.
"""

import json
import pytest
import re
from pathlib import Path


def has_clause_leak(coverage_name: str) -> bool:
    """
    Check if coverage name is clearly a clause/condition (not a valid coverage name)

    Returns True if:
    - Contains excessive clause keywords (>3)
    - Very long text (>150 chars) with clause patterns
    - Starts with clause markers
    """
    # Clause keywords
    clause_keywords = ['경우', '시', '합니다', '됩니다', '진단 확정', '보장개시일', '면책', '지급하지', '지급사유']

    # Count clause keywords
    clause_count = sum(1 for kw in clause_keywords if kw in coverage_name)

    # Excessive clause keywords
    if clause_count > 3:
        return True

    # Long text with clause patterns
    if len(coverage_name) > 150 and clause_count > 2:
        return True

    # Starts with clause markers
    clause_starters = ['진단 확정된 경우', '보장개시일 이후', '지급사유가 발생']
    if any(coverage_name.startswith(starter) for starter in clause_starters):
        return True

    return False


def test_no_clause_leak():
    """
    Test that extracted facts do not contain clause-heavy coverage names

    GATE: clause_leak_rate < 5% per insurer
    """
    insurers = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "heungkuk", "db"]
    extracted_dir = Path("data/scope_v3")

    results = []

    for insurer in insurers:
        extracted_path = extracted_dir / f"{insurer}_step1_raw_scope_v3.jsonl"

        if not extracted_path.exists():
            pytest.skip(f"{insurer}: V3 extraction not found")

        # Read extracted facts
        facts = []
        with open(extracted_path, 'r', encoding='utf-8') as f:
            for line in f:
                facts.append(json.loads(line))

        # Check for clause leaks
        clause_leaks = []
        for fact in facts:
            coverage_name = fact.get('coverage_name_raw', '')

            if has_clause_leak(coverage_name):
                clause_leaks.append({
                    'coverage_name': coverage_name[:100],  # Truncate for display
                    'page': fact.get('proposal_facts', {}).get('evidences', [{}])[0].get('page', 'N/A'),
                    'length': len(coverage_name)
                })

        # Calculate leak rate
        total_count = len(facts)
        leak_count = len(clause_leaks)
        leak_rate = leak_count / total_count if total_count > 0 else 0

        results.append({
            'insurer': insurer,
            'total_count': total_count,
            'leak_count': leak_count,
            'leak_rate': leak_rate,
            'clause_leaks': clause_leaks[:5]  # Top 5 examples
        })

    # Display results
    print("\nClause Leak Detection Gate:")
    print("-" * 80)
    print(f"{'Insurer':<12} {'Total':>6} {'Leaks':>6} {'Rate':>7} {'Status':>8}")
    print("-" * 80)

    all_passed = True
    for r in results:
        status = "✅" if r['leak_rate'] < 0.05 else "❌"
        if r['leak_rate'] >= 0.05:
            all_passed = False

        print(
            f"{r['insurer']:<12} {r['total_count']:>6} {r['leak_count']:>6} "
            f"{r['leak_rate']:>6.1%} {status:>8}"
        )

        if r['clause_leaks']:
            print(f"  Clause leak examples:")
            for leak in r['clause_leaks']:
                print(f"    - Page {leak['page']} ({leak['length']} chars): {leak['coverage_name']}...")

    print("-" * 80)

    if all_passed:
        print("✅ All insurers passed clause leak gate (leak rate < 5%)")
    else:
        print("❌ Some insurers failed clause leak gate")

    assert all_passed, "Clause leak gate failed: some insurers have leak rate ≥ 5%"
