"""
STEP NEXT-56: GATE-56-1 - Step1 Stability Test

Constitutional requirement:
- Same input (manifest + PDF) → Same output (profile + raw extraction)
- 3 consecutive runs MUST produce identical checksums
- Tests Samsung, Hyundai, DB (regression precedents)

Enforcement:
- Profile checksum: Identical (3/3)
- Raw output checksum: Identical (3/3)
- Row count: Identical (3/3)
"""

import subprocess
import hashlib
import json
from pathlib import Path
import pytest


MANIFEST_PATH = "data/manifests/proposal_pdfs_v1.json"
PROFILE_DIR = Path("data/profile")
SCOPE_DIR = Path("data/scope_v3")

# Critical insurers (Samsung, Hyundai, DB)
CRITICAL_INSURERS = [
    ("samsung", "default"),
    ("hyundai", "default"),
    ("db", "under40"),
    ("db", "over41"),
]


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of file (excluding timestamp)"""
    with open(file_path, 'rb') as f:
        data = f.read()

    # For JSON files, exclude generated_at timestamp
    if file_path.suffix == '.json':
        try:
            obj = json.loads(data)
            if 'generated_at' in obj:
                obj.pop('generated_at')
            data = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode('utf-8')
        except:
            pass  # Not JSON, use raw data

    return hashlib.sha256(data).hexdigest()


def run_step1(manifest_path: str) -> None:
    """Run Step1 (profile + extract)"""
    # Profile builder
    subprocess.run(
        ["python", "-m", "pipeline.step1_summary_first.profile_builder_v3", "--manifest", manifest_path],
        check=True,
        capture_output=True
    )

    # Extractor
    subprocess.run(
        ["python", "-m", "pipeline.step1_summary_first.extractor_v3", "--manifest", manifest_path],
        check=True,
        capture_output=True
    )


def get_profile_path(insurer: str, variant: str) -> Path:
    """Get profile file path"""
    if variant == "default":
        filename = f"{insurer}_proposal_profile_v3.json"
    else:
        filename = f"{insurer}_{variant}_proposal_profile_v3.json"
    return PROFILE_DIR / filename


def get_raw_scope_path(insurer: str, variant: str) -> Path:
    """Get raw scope file path"""
    if variant == "default":
        filename = f"{insurer}_step1_raw_scope_v3.jsonl"
    else:
        filename = f"{insurer}_{variant}_step1_raw_scope_v3.jsonl"
    return SCOPE_DIR / filename


@pytest.mark.parametrize("insurer,variant", CRITICAL_INSURERS)
def test_gate_56_1_step1_stability_3runs(insurer: str, variant: str):
    """
    GATE-56-1: Step1 Stability (3 consecutive runs)

    Constitutional requirement:
    - Profile checksum: Identical (3/3)
    - Raw output checksum: Identical (3/3)
    - Row count: Identical (3/3)
    """
    profile_path = get_profile_path(insurer, variant)
    raw_scope_path = get_raw_scope_path(insurer, variant)

    profile_checksums = []
    raw_checksums = []
    row_counts = []

    # Run 3 times
    for run_num in range(1, 4):
        print(f"\n=== Run {run_num}/3: {insurer} ({variant}) ===")

        # Execute Step1
        run_step1(MANIFEST_PATH)

        # Capture checksums
        profile_sha = compute_file_sha256(profile_path)
        raw_sha = compute_file_sha256(raw_scope_path)

        # Count rows
        with open(raw_scope_path, 'r') as f:
            row_count = sum(1 for _ in f)

        profile_checksums.append(profile_sha)
        raw_checksums.append(raw_sha)
        row_counts.append(row_count)

        print(f"  Profile SHA: {profile_sha[:16]}...")
        print(f"  Raw SHA: {raw_sha[:16]}...")
        print(f"  Row count: {row_count}")

    # Verify all runs produced identical results
    assert len(set(profile_checksums)) == 1, \
        f"Profile checksums differ across runs: {profile_checksums}"

    assert len(set(raw_checksums)) == 1, \
        f"Raw output checksums differ across runs: {raw_checksums}"

    assert len(set(row_counts)) == 1, \
        f"Row counts differ across runs: {row_counts}"

    print(f"\n✅ GATE-56-1 PASSED ({insurer}/{variant}): All 3 runs identical")


def test_gate_56_1_samsung_no_regression():
    """
    Samsung-specific regression check (STEP NEXT-55A precedent)

    Requirements:
    - Row count ≥ 30 (was 17 before fix, now 32)
    - Null coverage_name rate < 30% (was 82.2% before fix, now 24.4%)
    """
    raw_scope_path = get_raw_scope_path("samsung", "default")

    # Run Step1
    run_step1(MANIFEST_PATH)

    # Count total rows and null coverage names
    total_rows = 0
    null_count = 0

    with open(raw_scope_path, 'r') as f:
        for line in f:
            total_rows += 1
            obj = json.loads(line)
            if not obj.get('coverage_name_raw'):
                null_count += 1

    null_rate = (null_count / total_rows) * 100 if total_rows > 0 else 0

    print(f"\nSamsung Step1 metrics:")
    print(f"  Total rows: {total_rows}")
    print(f"  Null coverage_name: {null_count} ({null_rate:.1f}%)")

    # Constitutional requirements
    assert total_rows >= 30, \
        f"Samsung row count regression: {total_rows} < 30 (expected ≥30)"

    assert null_rate < 30, \
        f"Samsung null rate regression: {null_rate:.1f}% ≥ 30% (expected <30%)"

    print(f"✅ Samsung regression check PASSED")


def test_gate_56_1_db_hyundai_prefix_preservation():
    """
    DB/Hyundai prefix preservation check (STEP NEXT-55 precedent)

    Requirements:
    - Zero broken prefixes (". 상해사망" pattern)
    - Proper prefixes intact ("1. ", "2. ", etc.)
    """
    test_cases = [
        ("db", "under40"),
        ("db", "over41"),
        ("hyundai", "default"),
    ]

    # Run Step1
    run_step1(MANIFEST_PATH)

    for insurer, variant in test_cases:
        raw_scope_path = get_raw_scope_path(insurer, variant)

        broken_count = 0
        proper_count = 0

        with open(raw_scope_path, 'r') as f:
            for line in f:
                obj = json.loads(line)
                name = obj.get('coverage_name_raw', '')

                # Check for broken prefix
                if name.startswith('. '):
                    broken_count += 1

                # Check for proper prefix
                if name and name[0].isdigit() and '. ' in name[:5]:
                    proper_count += 1

        print(f"\n{insurer}/{variant} prefix check:")
        print(f"  Broken prefixes ('. '): {broken_count}")
        print(f"  Proper prefixes ('1. '): {proper_count}")

        assert broken_count == 0, \
            f"{insurer}/{variant}: Found {broken_count} broken prefixes (CONSTITUTIONAL VIOLATION)"

        assert proper_count > 0, \
            f"{insurer}/{variant}: No proper prefixes found (expected >0)"

    print(f"\n✅ DB/Hyundai prefix preservation PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
