"""
STEP NEXT-45-C-β-4 P0-F2: Duplicate Detection Gate Test

Ensures that extracted facts do not have excessive duplicates (>10% duplicate ratio).
This prevents Pass B detection from extracting the same table multiple times.
"""

import json
import pytest
from pathlib import Path
from typing import Set


def normalize_coverage_name(name: str) -> str:
    """Normalize coverage name for dedup"""
    import re
    normalized = name.strip()
    normalized = re.sub(r'\s+', '', normalized)
    normalized = normalized.lower()
    return normalized


def test_no_excessive_duplicates():
    """
    Test that each insurer has dedup ratio ≥ 0.90 (i.e., duplicate rate ≤ 10%)

    GATE: dedup_ratio = dedup_count / valid_count ≥ 0.90
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

        # Deduplicate
        seen_keys: Set[str] = set()
        dedup_count = 0
        duplicate_examples = []

        for fact in facts:
            coverage_name = fact.get('coverage_name_raw', '')
            amount_text = fact.get('proposal_facts', {}).get('coverage_amount_text', '')

            # Dedup key: normalized_name + amount_text
            normalized_name = normalize_coverage_name(coverage_name)
            dedup_key = f"{normalized_name}|{amount_text or ''}"

            if dedup_key in seen_keys:
                # Duplicate found
                if len(duplicate_examples) < 5:
                    duplicate_examples.append({
                        'coverage_name': coverage_name,
                        'amount': amount_text or 'N/A',
                        'page': fact.get('proposal_facts', {}).get('evidences', [{}])[0].get('page', 'N/A')
                    })
            else:
                seen_keys.add(dedup_key)
                dedup_count += 1

        # Calculate dedup ratio
        valid_count = len(facts)
        dedup_ratio = dedup_count / valid_count if valid_count > 0 else 1.0
        duplicate_count = valid_count - dedup_count

        results.append({
            'insurer': insurer,
            'valid_count': valid_count,
            'dedup_count': dedup_count,
            'duplicate_count': duplicate_count,
            'dedup_ratio': dedup_ratio,
            'duplicate_examples': duplicate_examples
        })

    # Display results
    print("\nDuplicate Detection Gate:")
    print("-" * 80)
    print(f"{'Insurer':<12} {'Valid':>6} {'Dedup':>6} {'Dups':>5} {'Ratio':>7} {'Status':>8}")
    print("-" * 80)

    all_passed = True
    for r in results:
        status = "✅" if r['dedup_ratio'] >= 0.90 else "❌"
        if r['dedup_ratio'] < 0.90:
            all_passed = False

        print(
            f"{r['insurer']:<12} {r['valid_count']:>6} {r['dedup_count']:>6} "
            f"{r['duplicate_count']:>5} {r['dedup_ratio']:>6.1%} {status:>8}"
        )

        if r['duplicate_examples']:
            print(f"  Duplicate examples:")
            for dup in r['duplicate_examples']:
                print(f"    - Page {dup['page']}: {dup['coverage_name']} ({dup['amount']})")

    print("-" * 80)

    if all_passed:
        print("✅ All insurers passed duplicate gate (dedup ratio ≥ 90%)")
    else:
        print("❌ Some insurers failed duplicate gate")

    assert all_passed, "Duplicate gate failed: some insurers have dedup ratio < 90%"
