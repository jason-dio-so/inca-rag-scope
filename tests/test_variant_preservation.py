"""
STEP NEXT-56: GATE-56-2 - Variant Preservation Test

Constitutional requirement:
- DB: under40 AND over41 files MUST exist (pair)
- LOTTE: male AND female files MUST exist (pair)
- Single-variant files FORBIDDEN (db_step2_*.jsonl violates constitution)

Enforcement:
- Variant pairs verified across all steps
- No single-variant files allowed
- File naming convention enforced
"""

import pytest
from pathlib import Path


SCOPE_DIR = Path("data/scope_v3")

# Variant-aware insurers (constitutional list)
VARIANT_INSURERS = {
    "db": ["under40", "over41"],
    "lotte": ["male", "female"],
}

# Step file patterns
STEP_PATTERNS = [
    "step1_raw_scope_v3.jsonl",
    "step2_sanitized_scope_v1.jsonl",
    "step2_canonical_scope_v1.jsonl",
    "step2_dropped.jsonl",
    "step2_mapping_report.jsonl",
]


def test_gate_56_2_variant_pairs_exist():
    """
    GATE-56-2: Variant Preservation - Pair Existence

    Constitutional requirement:
    - DB: Both under40 AND over41 files exist
    - LOTTE: Both male AND female files exist
    """
    failures = []

    for insurer, variants in VARIANT_INSURERS.items():
        for pattern in STEP_PATTERNS:
            for variant in variants:
                filename = f"{insurer}_{variant}_{pattern}"
                file_path = SCOPE_DIR / filename

                if not file_path.exists():
                    failures.append(f"Missing: {filename}")

    if failures:
        pytest.fail(
            f"GATE-56-2 FAILED: Variant files missing\n" +
            "\n".join(f"  ❌ {f}" for f in failures)
        )

    print("✅ GATE-56-2 PASSED: All variant pairs exist")


def test_gate_56_2_no_single_variant_files():
    """
    GATE-56-2: Variant Preservation - Single-Variant Prohibition

    Constitutional violation:
    - db_step2_canonical_scope_v1.jsonl (should be db_under40_* and db_over41_*)
    - lotte_step2_sanitized_scope_v1.jsonl (should be lotte_male_* and lotte_female_*)
    """
    forbidden_patterns = []

    for insurer in VARIANT_INSURERS.keys():
        for pattern in STEP_PATTERNS:
            # Check for single-variant file (NO variant suffix)
            forbidden_file = SCOPE_DIR / f"{insurer}_{pattern}"

            if forbidden_file.exists():
                forbidden_patterns.append(str(forbidden_file))

    if forbidden_patterns:
        pytest.fail(
            f"GATE-56-2 FAILED: Single-variant files detected (CONSTITUTIONAL VIOLATION)\n" +
            "\n".join(f"  ❌ {f}" for f in forbidden_patterns) +
            "\n\nVariant files MUST include variant suffix (e.g., db_under40_*, db_over41_*)"
        )

    print("✅ GATE-56-2 PASSED: No single-variant files detected")


def test_gate_56_2_profile_variant_preservation():
    """
    GATE-56-2: Variant Preservation - Profile Files

    Constitutional requirement:
    - DB: under40 and over41 profile files exist
    - LOTTE: male and female profile files exist
    """
    profile_dir = Path("data/profile")
    failures = []

    for insurer, variants in VARIANT_INSURERS.items():
        for variant in variants:
            profile_filename = f"{insurer}_{variant}_proposal_profile_v3.json"
            profile_path = profile_dir / profile_filename

            if not profile_path.exists():
                failures.append(f"Missing profile: {profile_filename}")

    if failures:
        pytest.fail(
            f"GATE-56-2 FAILED: Profile variant files missing\n" +
            "\n".join(f"  ❌ {f}" for f in failures)
        )

    print("✅ GATE-56-2 PASSED: All profile variant files exist")


def test_gate_56_2_variant_row_count_sanity():
    """
    GATE-56-2: Variant Preservation - Row Count Sanity

    Sanity check:
    - Variants should have different row counts (different age/gender data)
    - If identical, likely indicates variant collapse
    """
    for insurer, variants in VARIANT_INSURERS.items():
        for pattern in ["step1_raw_scope_v3.jsonl", "step2_canonical_scope_v1.jsonl"]:
            variant_counts = {}

            for variant in variants:
                filename = f"{insurer}_{variant}_{pattern}"
                file_path = SCOPE_DIR / filename

                if file_path.exists():
                    with open(file_path, 'r') as f:
                        count = sum(1 for _ in f)
                    variant_counts[variant] = count

            # If all variants have same count, warn (likely collapse)
            if len(set(variant_counts.values())) == 1 and len(variant_counts) > 1:
                print(f"⚠️  WARNING: {insurer} {pattern} has identical counts across variants: {variant_counts}")
                print(f"   This may indicate variant collapse (not a hard failure, but suspicious)")
            else:
                print(f"✅ {insurer} {pattern}: Variant counts differ (expected): {variant_counts}")


def test_gate_56_2_forbidden_variant_names():
    """
    GATE-56-2: Variant Preservation - Forbidden Naming

    Forbidden patterns (common mistakes):
    - db_default_* (DB has NO default variant)
    - lotte_default_* (LOTTE has NO default variant)
    """
    forbidden_variants = [
        ("db", "default"),
        ("lotte", "default"),
    ]

    violations = []

    for insurer, forbidden_variant in forbidden_variants:
        for pattern in STEP_PATTERNS:
            forbidden_file = SCOPE_DIR / f"{insurer}_{forbidden_variant}_{pattern}"

            if forbidden_file.exists():
                violations.append(str(forbidden_file))

    if violations:
        pytest.fail(
            f"GATE-56-2 FAILED: Forbidden variant naming detected\n" +
            "\n".join(f"  ❌ {v}" for v in violations) +
            "\n\nDB uses 'under40'/'over41', LOTTE uses 'male'/'female' (NOT 'default')"
        )

    print("✅ GATE-56-2 PASSED: No forbidden variant names detected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
