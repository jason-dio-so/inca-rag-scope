"""
STEP NEXT-70-ANCHOR-FIX: Unanchored Coverage Analysis

Generate sample of unanchored coverages with A/B classification:
- (A) Step2-b also has no coverage_code → mapping/Excel gap
- (B) Step2-b has coverage_code but Step4 has null → Step4 carry-through bug

Since we now use Step2-b → Step3 → Step4, case (B) should be 0.
"""

import json
from pathlib import Path
from typing import List, Dict


def load_step2_mapping(step2_file: Path) -> Dict[str, str]:
    """
    Load Step2-b canonical mapping.

    Returns:
        Dict[coverage_name_raw, coverage_code]
    """
    mapping = {}
    with open(step2_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("coverage_name_raw", "")
            code = row.get("coverage_code")
            if key:
                mapping[key] = code
    return mapping


def analyze_unanchored_samples(
    compare_rows_file: Path,
    step2_files: Dict[str, Path],
    sample_size: int = 20
) -> List[Dict]:
    """
    Analyze unanchored coverage samples.

    Returns:
        List of sample dicts with A/B classification
    """
    # Load all Step2-b mappings
    all_step2_mapping = {}
    for insurer, step2_file in step2_files.items():
        if step2_file.exists():
            mapping = load_step2_mapping(step2_file)
            all_step2_mapping[insurer] = mapping

    # Load compare rows
    with open(compare_rows_file, 'r', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f]

    # Filter unanchored
    unanchored = [r for r in rows if r['meta']['unanchored']]

    print(f"Total rows: {len(rows)}")
    print(f"Unanchored: {len(unanchored)} ({len(unanchored)/len(rows)*100:.1f}%)")
    print()

    # Sample and classify
    samples = []
    for i, row in enumerate(unanchored[:sample_size]):
        insurer = row['identity']['insurer_key']
        coverage_name_raw = row['identity']['coverage_name_raw']
        coverage_code_step4 = row['identity'].get('coverage_code')

        # Check Step2-b
        step2_mapping = all_step2_mapping.get(insurer, {})
        coverage_code_step2 = step2_mapping.get(coverage_name_raw)

        # Classify
        if not coverage_code_step2:
            classification = "A"
            reason = "Step2-b also has no coverage_code (mapping/Excel gap)"
        elif not coverage_code_step4:
            classification = "B"
            reason = "Step2-b has coverage_code but Step4 has null (carry-through bug)"
        else:
            classification = "?"
            reason = "Unexpected: both have coverage_code but unanchored"

        sample = {
            "index": i + 1,
            "classification": classification,
            "insurer_key": insurer,
            "product_key": row['identity']['product_key'],
            "variant_key": row['identity']['variant_key'],
            "coverage_name_raw": coverage_name_raw[:70],
            "coverage_code_step2": coverage_code_step2,
            "coverage_code_step4": coverage_code_step4,
            "reason": reason
        }
        samples.append(sample)

    return samples


def main():
    project_root = Path(__file__).parent.parent.parent
    compare_rows_file = project_root / "data" / "compare_v1" / "compare_rows_v1.jsonl"

    # Map insurers to Step2-b files
    step2_files = {
        "samsung": project_root / "data" / "scope_v3" / "samsung_step2_canonical_scope_v1.jsonl",
        "hanwha": project_root / "data" / "scope_v3" / "hanwha_step2_canonical_scope_v1.jsonl",
        "heungkuk": project_root / "data" / "scope_v3" / "heungkuk_step2_canonical_scope_v1.jsonl",
        "hyundai": project_root / "data" / "scope_v3" / "hyundai_step2_canonical_scope_v1.jsonl",
        "kb": project_root / "data" / "scope_v3" / "kb_step2_canonical_scope_v1.jsonl",
        "meritz": project_root / "data" / "scope_v3" / "meritz_step2_canonical_scope_v1.jsonl",
        "db": project_root / "data" / "scope_v3" / "db_over41_step2_canonical_scope_v1.jsonl",
        "lotte": project_root / "data" / "scope_v3" / "lotte_female_step2_canonical_scope_v1.jsonl",
    }

    samples = analyze_unanchored_samples(compare_rows_file, step2_files, sample_size=20)

    # Print markdown table
    print("## Unanchored Coverage Samples (n=20)")
    print()
    print("| # | Class | Insurer | Coverage Name (raw) | Step2 Code | Step4 Code | Reason |")
    print("|---|-------|---------|---------------------|------------|------------|--------|")

    for s in samples:
        print(f"| {s['index']} | **{s['classification']}** | {s['insurer_key']} | {s['coverage_name_raw']} | {s['coverage_code_step2'] or 'NULL'} | {s['coverage_code_step4'] or 'NULL'} | {s['reason']} |")

    print()

    # Count by classification
    a_count = sum(1 for s in samples if s['classification'] == 'A')
    b_count = sum(1 for s in samples if s['classification'] == 'B')
    other_count = sum(1 for s in samples if s['classification'] not in ['A', 'B'])

    print(f"## Classification Summary")
    print(f"- **(A) Mapping/Excel gap**: {a_count} / {len(samples)}")
    print(f"- **(B) Carry-through bug**: {b_count} / {len(samples)}")
    print(f"- **(?) Other**: {other_count} / {len(samples)}")
    print()

    if b_count > 0:
        print("⚠️ WARNING: Found carry-through bugs (type B)")
    else:
        print("✅ No carry-through bugs detected")


if __name__ == "__main__":
    main()
