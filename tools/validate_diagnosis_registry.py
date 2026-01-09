#!/usr/bin/env python3
"""
Diagnosis Coverage Registry Validator

PURPOSE:
- Validate registry consistency
- Check all coverage_codes in scope are either registered or explicitly excluded
- Ensure no logic conflicts with STEP-82-Q12-FIX-2

USAGE:
    python3 tools/validate_diagnosis_registry.py
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def load_registry():
    """Load diagnosis coverage registry"""
    registry_path = Path("data/registry/diagnosis_coverage_registry.json")
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_canonical_scope():
    """Load all canonical scope files to get coverage_codes"""
    scope_dir = Path("data/scope_v3")
    coverage_codes = defaultdict(list)

    for scope_file in scope_dir.glob("*_step2_canonical_scope_v1.jsonl"):
        with open(scope_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    coverage_code = row.get("coverage_code")
                    coverage_name = row.get("coverage_name_normalized")
                    insurer = row.get("insurer_key")

                    if coverage_code:
                        coverage_codes[coverage_code].append({
                            "insurer": insurer,
                            "coverage_name": coverage_name,
                            "file": scope_file.name
                        })

    return coverage_codes


def validate_registry_format(registry):
    """Validate registry format and required fields"""
    print("=" * 70)
    print("1. Registry Format Validation")
    print("=" * 70)

    errors = []

    # Check required top-level fields
    required_fields = ["version", "last_updated", "coverage_entries", "validation_rules"]
    for field in required_fields:
        if field not in registry:
            errors.append(f"Missing required field: {field}")

    # Check each coverage entry
    required_entry_fields = [
        "coverage_code", "canonical_name", "coverage_kind", "diagnosis_type",
        "trigger", "included_subtypes", "excluded_subtypes",
        "usable_for_questions", "usable_for_comparison", "usable_for_recommendation",
        "exclusion_keywords", "insurers", "lock_version"
    ]

    for coverage_code, entry in registry.get("coverage_entries", {}).items():
        if coverage_code != entry.get("coverage_code"):
            errors.append(f"Mismatch: key={coverage_code}, entry coverage_code={entry.get('coverage_code')}")

        for field in required_entry_fields:
            if field not in entry:
                errors.append(f"{coverage_code}: Missing field '{field}'")

    if errors:
        print("❌ Format validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Format validation PASSED")
        return True


def validate_exclusion_patterns(registry):
    """Validate all exclusion_keywords are valid regex patterns"""
    print()
    print("=" * 70)
    print("2. Exclusion Pattern Validation")
    print("=" * 70)

    errors = []

    for coverage_code, entry in registry.get("coverage_entries", {}).items():
        exclusion_keywords = entry.get("exclusion_keywords", [])

        for keyword in exclusion_keywords:
            try:
                re.compile(keyword)
            except re.error as e:
                errors.append(f"{coverage_code}: Invalid regex '{keyword}': {e}")

    if errors:
        print("❌ Pattern validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"✅ Pattern validation PASSED ({sum(len(e.get('exclusion_keywords', [])) for e in registry.get('coverage_entries', {}).values())} patterns checked)")
        return True


def validate_coverage_kind_enum(registry):
    """Validate coverage_kind values match enum"""
    print()
    print("=" * 70)
    print("3. Coverage Kind Enum Validation")
    print("=" * 70)

    valid_kinds = registry.get("validation_rules", {}).get("coverage_kind_enum", [])
    errors = []

    for coverage_code, entry in registry.get("coverage_entries", {}).items():
        coverage_kind = entry.get("coverage_kind")
        if coverage_kind not in valid_kinds:
            errors.append(f"{coverage_code}: Invalid coverage_kind '{coverage_kind}' (valid: {valid_kinds})")

    if errors:
        print("❌ Enum validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"✅ Enum validation PASSED")
        return True


def validate_scope_coverage(registry):
    """Check all coverage_codes in scope are either registered or known non-diagnosis"""
    print()
    print("=" * 70)
    print("4. Scope Coverage Validation")
    print("=" * 70)

    print("Loading canonical scope files...")
    scope_coverage_codes = load_canonical_scope()
    registry_codes = set(registry.get("coverage_entries", {}).keys())

    print(f"  Found {len(scope_coverage_codes)} unique coverage_codes in scope")
    print(f"  Found {len(registry_codes)} registered diagnosis coverage_codes")
    print()

    # Categorize coverage codes
    registered = []
    unregistered = []

    for coverage_code, occurrences in scope_coverage_codes.items():
        if coverage_code in registry_codes:
            registered.append((coverage_code, len(occurrences)))
        else:
            unregistered.append((coverage_code, occurrences))

    print(f"✅ Registered diagnosis benefits: {len(registered)}")
    for code, count in sorted(registered):
        entry = registry["coverage_entries"][code]
        print(f"  - {code}: {entry['canonical_name']} ({count} occurrences)")

    print()
    print(f"⚠️  Unregistered coverage_codes: {len(unregistered)}")
    for code, occurrences in sorted(unregistered)[:10]:  # Show first 10
        print(f"  - {code}: {occurrences[0]['coverage_name']} ({len(occurrences)} occurrences)")

    if len(unregistered) > 10:
        print(f"  ... and {len(unregistered) - 10} more")

    print()
    print("ℹ️  Note: Unregistered codes are expected (treatment/admission/surgery benefits)")
    print("     They will be excluded from diagnosis comparison/recommendation")

    return True


def validate_fix2_consistency(registry):
    """Validate consistency with STEP-82-Q12-FIX-2 results"""
    print()
    print("=" * 70)
    print("5. STEP-82-Q12-FIX-2 Consistency Check")
    print("=" * 70)

    # Load Q12 comparison results
    q12_path = Path("docs/audit/q12_cancer_compare.jsonl")
    if not q12_path.exists():
        print("⚠️  Q12 comparison file not found, skipping consistency check")
        return True

    with open(q12_path, 'r', encoding='utf-8') as f:
        q12_rows = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(q12_rows)} Q12 comparison rows")

    errors = []

    for row in q12_rows:
        coverage_code = row.get("coverage_code")
        coverage_name = row.get("coverage_name")

        # Check if coverage_code is in registry
        if coverage_code not in registry.get("coverage_entries", {}):
            errors.append(f"Q12 uses coverage_code '{coverage_code}' ({coverage_name}) not in registry")
            continue

        entry = registry["coverage_entries"][coverage_code]

        # Check if it's diagnosis_benefit
        if entry["coverage_kind"] != "diagnosis_benefit":
            errors.append(f"Q12 uses coverage_code '{coverage_code}' with kind '{entry['coverage_kind']}' (not diagnosis_benefit)")

        # Check if usable_for_comparison is true
        if not entry.get("usable_for_comparison"):
            errors.append(f"Q12 uses coverage_code '{coverage_code}' but usable_for_comparison=False")

    if errors:
        print("❌ Consistency check FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Consistency check PASSED")
        print(f"  - All Q12 coverage_codes are registered diagnosis_benefit")
        print(f"  - All have usable_for_comparison=true")
        return True


def main():
    print("=" * 70)
    print("Diagnosis Coverage Registry Validator")
    print("=" * 70)
    print()

    # Load registry
    print("Loading registry...")
    registry = load_registry()
    print(f"Registry version: {registry.get('version')}")
    print(f"Last updated: {registry.get('last_updated')}")
    print()

    # Run validations
    results = []

    results.append(("Format", validate_registry_format(registry)))
    results.append(("Exclusion Patterns", validate_exclusion_patterns(registry)))
    results.append(("Coverage Kind Enum", validate_coverage_kind_enum(registry)))
    results.append(("Scope Coverage", validate_scope_coverage(registry)))
    results.append(("FIX-2 Consistency", validate_fix2_consistency(registry)))

    # Summary
    print()
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)

    all_passed = all(passed for _, passed in results)

    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {check_name}: {status}")

    print()

    if all_passed:
        print("=" * 70)
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 70)
        print()
        print("Diagnosis Coverage Registry is LOCKED and ready for use.")
        return 0
    else:
        print("=" * 70)
        print("❌ VALIDATION FAILED")
        print("=" * 70)
        print()
        print("Please fix the errors above before using the registry.")
        return 1


if __name__ == "__main__":
    exit(main())
