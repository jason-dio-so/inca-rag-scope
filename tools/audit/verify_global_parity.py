"""
STEP NEXT-45-C-β-4 P0-F1: Global Valid Parity Verification

Calculates global valid parity with:
1. Validity filter (exclude clause-heavy/noise rows)
2. Deduplication (normalize coverage_name + amount_text)
3. Per-insurer breakdown with examples
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


def normalize_coverage_name(name: str) -> str:
    """Normalize coverage name for dedup"""
    # Remove whitespace, parentheses variations
    normalized = name.strip()
    normalized = re.sub(r'\s+', '', normalized)
    normalized = normalized.lower()
    return normalized


def is_valid_coverage(coverage_name: str) -> bool:
    """
    Validity filter: exclude clause-heavy/noise rows

    Reject if:
    - Too short (<2 chars)
    - Contains total/disclaimer keywords
    - Is just numbers/symbols
    - Contains excessive clause patterns
    """
    if len(coverage_name) < 2:
        return False

    # Total keywords
    total_keywords = ['합계', '총계', '보험료 합계', '보장보험료 합계', '보험료합계']
    if any(kw in coverage_name for kw in total_keywords):
        return False

    # Disclaimer keywords
    disclaimer_keywords = ['◆', '※', '가입한 담보', '반드시', '확인', '주의사항']
    if any(kw in coverage_name for kw in disclaimer_keywords):
        return False

    # Just numbers or row numbers
    if re.match(r'^\d+\.?$', coverage_name) or re.match(r'^\d+\)$', coverage_name):
        return False

    # Excessive clause patterns (>50% of text is clause keywords)
    clause_keywords = ['경우', '시', '합니다', '됩니다', '진단 확정', '보장개시일', '면책', '지급하지']
    clause_count = sum(1 for kw in clause_keywords if kw in coverage_name)
    if clause_count > 3:  # More than 3 clause keywords
        return False

    return True


def deduplicate_facts(facts: List[Dict]) -> Tuple[List[Dict], int, List[Tuple[str, int]]]:
    """
    Deduplicate facts by normalized coverage_name + amount_text

    Returns:
        (deduped_facts, duplicate_count, duplicate_examples)
    """
    seen_keys: Set[str] = set()
    deduped = []
    duplicates = []
    duplicate_examples = []

    for fact in facts:
        coverage_name = fact.get('coverage_name_raw', '')
        amount_text = fact.get('proposal_facts', {}).get('coverage_amount_text', '')

        # Dedup key: normalized_name + amount_text
        normalized_name = normalize_coverage_name(coverage_name)
        dedup_key = f"{normalized_name}|{amount_text or ''}"

        if dedup_key in seen_keys:
            duplicates.append(fact)
            if len(duplicate_examples) < 10:
                duplicate_examples.append((coverage_name, amount_text or 'N/A'))
        else:
            seen_keys.add(dedup_key)
            deduped.append(fact)

    return deduped, len(duplicates), duplicate_examples


def calculate_parity_for_insurer(insurer: str, baseline_path: Path, extracted_path: Path, fallback_baseline_path: Path = None) -> Dict[str, Any]:
    """Calculate parity metrics for a single insurer"""

    # Read baseline (V2, fallback to V1 if V2 doesn't exist)
    baseline_facts = []
    if baseline_path.exists():
        with open(baseline_path, 'r', encoding='utf-8') as f:
            for line in f:
                baseline_facts.append(json.loads(line))
    elif fallback_baseline_path and fallback_baseline_path.exists():
        # Fallback to V1 baseline (from scope.csv - need to convert)
        # For KB, use the sanitized mapped CSV
        import csv
        with open(fallback_baseline_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                baseline_facts.append({
                    'coverage_name_raw': row.get('coverage_name_raw', row.get('담보명_원문', row.get('coverage_name', ''))),
                    'proposal_facts': {
                        'coverage_amount_text': row.get('coverage_amount_text', row.get('가입금액', row.get('coverage_amount', ''))),
                        'evidences': []
                    }
                })

    # Read extracted (V3)
    extracted_facts = []
    if extracted_path.exists():
        with open(extracted_path, 'r', encoding='utf-8') as f:
            for line in f:
                extracted_facts.append(json.loads(line))

    # Apply validity filter
    baseline_valid = [f for f in baseline_facts if is_valid_coverage(f.get('coverage_name_raw', ''))]
    extracted_valid = [f for f in extracted_facts if is_valid_coverage(f.get('coverage_name_raw', ''))]

    # Apply deduplication
    baseline_dedup, baseline_dup_count, _ = deduplicate_facts(baseline_valid)
    extracted_dedup, extracted_dup_count, extracted_dup_examples = deduplicate_facts(extracted_valid)

    # Calculate parity
    parity = (len(extracted_dedup) / len(baseline_dedup) * 100) if len(baseline_dedup) > 0 else 0
    dedup_ratio = (len(extracted_dedup) / len(extracted_valid)) if len(extracted_valid) > 0 else 1.0

    # Find new coverages (in extracted but not in baseline)
    baseline_names = set(normalize_coverage_name(f.get('coverage_name_raw', '')) for f in baseline_dedup)
    new_coverages = []
    for fact in extracted_dedup:
        normalized = normalize_coverage_name(fact.get('coverage_name_raw', ''))
        if normalized not in baseline_names:
            new_coverages.append({
                'coverage_name': fact.get('coverage_name_raw', ''),
                'amount': fact.get('proposal_facts', {}).get('coverage_amount_text', ''),
                'page': fact.get('proposal_facts', {}).get('evidences', [{}])[0].get('page', 'N/A')
            })

    return {
        'baseline_raw': len(baseline_facts),
        'baseline_valid': len(baseline_valid),
        'baseline_dedup': len(baseline_dedup),
        'baseline_dup_count': baseline_dup_count,
        'extracted_raw': len(extracted_facts),
        'extracted_valid': len(extracted_valid),
        'extracted_dedup': len(extracted_dedup),
        'extracted_dup_count': extracted_dup_count,
        'extracted_dup_examples': extracted_dup_examples,
        'parity': parity,
        'dedup_ratio': dedup_ratio,
        'new_coverages': new_coverages[:10]  # Top 10
    }


def main():
    """Calculate global valid parity with breakdown"""

    insurers = ["samsung", "meritz", "kb", "hanwha", "hyundai", "lotte", "heungkuk", "db"]

    baseline_dir = Path("data/scope_v2")
    extracted_dir = Path("data/scope_v3")

    print("=" * 100)
    print("STEP NEXT-45-C-β-4 P0-F1: Global Valid Parity Verification")
    print("=" * 100)
    print()

    results = {}
    global_baseline_dedup = 0
    global_extracted_dedup = 0

    for insurer in insurers:
        baseline_path = baseline_dir / f"{insurer}_step1_raw_scope_v2.jsonl"
        extracted_path = extracted_dir / f"{insurer}_step1_raw_scope_v3.jsonl"

        # Fallback to V1 baseline (scope_mapped.sanitized.csv) if V2 doesn't exist
        fallback_baseline_path = Path(f"data/scope/{insurer}_scope_mapped.sanitized.csv")

        result = calculate_parity_for_insurer(insurer, baseline_path, extracted_path, fallback_baseline_path)
        results[insurer] = result

        global_baseline_dedup += result['baseline_dedup']
        global_extracted_dedup += result['extracted_dedup']

    # Print detailed breakdown
    print("Per-Insurer Breakdown:")
    print("-" * 100)
    print(f"{'Insurer':<10} {'B_Raw':>7} {'B_Valid':>8} {'B_Dedup':>8} | {'E_Raw':>7} {'E_Valid':>8} {'E_Dedup':>8} | {'Parity':>8} {'DedupR':>8}")
    print("-" * 100)

    for insurer in insurers:
        r = results[insurer]
        status = "✅" if r['parity'] >= 95 else ("⚠️" if r['parity'] >= 85 else "❌")
        dedup_status = "✅" if r['dedup_ratio'] >= 0.90 else "❌"

        print(
            f"{insurer:<10} {r['baseline_raw']:>7} {r['baseline_valid']:>8} {r['baseline_dedup']:>8} | "
            f"{r['extracted_raw']:>7} {r['extracted_valid']:>8} {r['extracted_dedup']:>8} | "
            f"{r['parity']:>7.1f}% {status} {r['dedup_ratio']:>6.1%} {dedup_status}"
        )

    print("-" * 100)
    global_parity = (global_extracted_dedup / global_baseline_dedup * 100) if global_baseline_dedup > 0 else 0
    global_status = "✅" if global_parity >= 95 else ("⚠️" if global_parity >= 85 else "❌")

    print(
        f"{'TOTAL':<10} {sum(r['baseline_raw'] for r in results.values()):>7} "
        f"{sum(r['baseline_valid'] for r in results.values()):>8} "
        f"{global_baseline_dedup:>8} | "
        f"{sum(r['extracted_raw'] for r in results.values()):>7} "
        f"{sum(r['extracted_valid'] for r in results.values()):>8} "
        f"{global_extracted_dedup:>8} | "
        f"{global_parity:>7.1f}% {global_status}"
    )
    print()

    # Global gate status
    if global_parity >= 95:
        print(f"🎯 GATE PASSED: Global valid parity {global_parity:.1f}% ≥ 95%")
    else:
        print(f"❌ GATE FAILED: Global valid parity {global_parity:.1f}% < 95%")
    print()

    # Duplicate gate check
    print("Duplicate Detection Gate:")
    print("-" * 100)
    duplicate_failures = []
    for insurer in insurers:
        r = results[insurer]
        if r['dedup_ratio'] < 0.90:
            duplicate_failures.append(insurer)
            print(f"❌ {insurer}: Dedup ratio {r['dedup_ratio']:.1%} < 90% (duplicates: {r['extracted_dup_count']})")
            if r['extracted_dup_examples']:
                print(f"   Examples:")
                for name, amount in r['extracted_dup_examples'][:5]:
                    print(f"     - {name} ({amount})")

    if not duplicate_failures:
        print("✅ All insurers passed duplicate gate (dedup ratio ≥ 90%)")
    print()

    # New coverages (why >100%?)
    print("New Coverages (Extracted but not in Baseline):")
    print("-" * 100)
    for insurer in insurers:
        r = results[insurer]
        if r['new_coverages']:
            print(f"\n{insurer.upper()} ({len(r['new_coverages'])} new):")
            for cov in r['new_coverages'][:5]:
                print(f"  - Page {cov['page']}: {cov['coverage_name']} ({cov['amount']})")
    print()

    # Save detailed results to JSON
    output_path = Path("data/profile/global_parity_verification_v3.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'global_parity': global_parity,
            'global_baseline_dedup': global_baseline_dedup,
            'global_extracted_dedup': global_extracted_dedup,
            'per_insurer': results
        }, f, ensure_ascii=False, indent=2)

    print(f"✓ Detailed results saved to: {output_path}")
    print()


if __name__ == '__main__':
    main()
