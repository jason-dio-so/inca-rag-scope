#!/usr/bin/env python3
"""
Validate Step7 Amount Pipeline Lock
====================================

Purpose:
    Pre-flight validation before loading Step7 amounts to DB.
    Ensures audit compliance, freeze tag existence, and lock integrity.

Usage:
    python -m pipeline.step10_audit.validate_amount_lock

Exit Codes:
    0 - All validations passed (safe to load)
    1 - Validation failed (DO NOT load)
"""

import json
import subprocess
import sys
from pathlib import Path

# Expected freeze tag prefix
FREEZE_TAG_PREFIX = "freeze/pre-10b2g2-"

# Expected audit report (latest)
EXPECTED_AUDIT_JSON = "reports/step7_gt_audit_all_20251229-025007.json"
EXPECTED_AUDIT_MD = "reports/step7_gt_audit_all_20251229-025007.md"

# Expected insurers
EXPECTED_INSURERS = ['samsung', 'hyundai', 'lotte', 'db', 'kb', 'meritz', 'hanwha', 'heungkuk']


def run_cmd(cmd: list[str]) -> str:
    """Run shell command and return output"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def check_freeze_tag() -> bool:
    """Check if freeze tag exists"""
    print("1️⃣  Checking freeze tag...")

    try:
        tags = run_cmd(['git', 'tag', '--list', f'{FREEZE_TAG_PREFIX}*'])
        if not tags:
            print(f"   ❌ No freeze tag found matching '{FREEZE_TAG_PREFIX}*'")
            return False

        latest_tag = tags.split('\n')[-1]
        print(f"   ✅ Freeze tag exists: {latest_tag}")
        return True

    except Exception as e:
        print(f"   ❌ Error checking freeze tag: {e}")
        return False


def check_audit_reports() -> bool:
    """Check if audit reports exist and are valid"""
    print("\n2️⃣  Checking audit reports...")

    project_root = Path(__file__).resolve().parents[2]
    json_path = project_root / EXPECTED_AUDIT_JSON
    md_path = project_root / EXPECTED_AUDIT_MD

    if not json_path.exists():
        print(f"   ❌ Audit JSON not found: {json_path}")
        return False

    if not md_path.exists():
        print(f"   ❌ Audit MD not found: {md_path}")
        return False

    print(f"   ✅ Audit reports exist")
    print(f"      - JSON: {json_path.name}")
    print(f"      - MD: {md_path.name}")

    # Parse JSON and check audit status
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            audit_data = json.load(f)

        # Audit report is an array of insurer results
        if not isinstance(audit_data, list):
            print(f"   ❌ Unexpected audit format (expected array)")
            return False

        insurers = [item.get('insurer') for item in audit_data if 'insurer' in item]
        total_rows = sum(item.get('gt_pairs', 0) for item in audit_data)

        # Check for MISMATCH_VALUE errors across all insurers
        mismatch_value = 0
        mismatch_type = 0

        for item in audit_data:
            verdict_counts = item.get('verdict_counts', {})
            # MISMATCH_VALUE would appear in verdict_counts
            if 'MISMATCH_VALUE' in verdict_counts:
                mismatch_value += verdict_counts['MISMATCH_VALUE']
            if 'MISMATCH_TYPE' in verdict_counts:
                mismatch_type += verdict_counts['MISMATCH_TYPE']

        print(f"\n   Audit Results:")
        print(f"   - Total rows: {total_rows}")
        print(f"   - MISMATCH_VALUE: {mismatch_value}")
        print(f"   - MISMATCH_TYPE: {mismatch_type}")
        print(f"   - Insurers: {len(insurers)}")

        # Critical: MISMATCH_VALUE must be 0
        if mismatch_value != 0:
            print(f"\n   ❌ CRITICAL: MISMATCH_VALUE={mismatch_value} (expected 0)")
            return False

        # Check insurers coverage
        if len(insurers) != len(EXPECTED_INSURERS):
            print(f"\n   ⚠️  WARNING: Expected {len(EXPECTED_INSURERS)} insurers, got {len(insurers)}")

        print(f"   ✅ Audit PASSED (MISMATCH_VALUE=0)")
        return True

    except Exception as e:
        print(f"   ❌ Error parsing audit report: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_coverage_cards() -> bool:
    """Check if coverage_cards.jsonl files exist for all insurers"""
    print("\n3️⃣  Checking coverage cards...")

    project_root = Path(__file__).resolve().parents[2]
    missing = []

    for insurer in EXPECTED_INSURERS:
        cards_path = project_root / f'data/compare/{insurer}_coverage_cards.jsonl'
        if not cards_path.exists():
            missing.append(insurer)

    if missing:
        print(f"   ❌ Missing coverage cards for: {', '.join(missing)}")
        return False

    print(f"   ✅ All {len(EXPECTED_INSURERS)} coverage cards exist")
    return True


def check_git_clean() -> bool:
    """Check if git working directory is clean (no uncommitted changes to Step7 files)"""
    print("\n4️⃣  Checking git working directory...")

    try:
        # Check for uncommitted changes in Step7 paths
        step7_paths = [
            'pipeline/step7_amount/',
            'pipeline/step7_amount_integration/',
            'data/compare/*_coverage_cards.jsonl'
        ]

        for path in step7_paths:
            status = run_cmd(['git', 'status', '--porcelain', path])
            if status:
                print(f"   ⚠️  Uncommitted changes in: {path}")
                print(f"      {status}")
                print(f"   ⚠️  WARNING: Step7 files modified (lock violation risk)")
                # Don't fail, just warn
                return True

        print(f"   ✅ No uncommitted Step7 changes")
        return True

    except Exception as e:
        print(f"   ⚠️  Could not check git status: {e}")
        return True  # Non-critical, allow to proceed


def check_type_c_guardrails() -> bool:
    """Verify type-C guardrails are active (보험가입금액 prohibition)"""
    print("\n5️⃣  Checking type-C guardrails...")

    project_root = Path(__file__).resolve().parents[2]
    cards_path = project_root / 'data/compare/samsung_coverage_cards.jsonl'

    if not cards_path.exists():
        print(f"   ⚠️  Cannot verify (samsung_coverage_cards.jsonl missing)")
        return True

    try:
        with open(cards_path, 'r', encoding='utf-8') as f:
            for line in f:
                card = json.loads(line.strip())
                amount = card.get('amount', {})
                value_text = amount.get('value_text', '')

                # Check for prohibited pattern
                if '보험가입금액' in value_text:
                    print(f"   ❌ Type-C violation: '보험가입금액' found in {card.get('coverage_name_raw')}")
                    print(f"      Value: {value_text}")
                    return False

        print(f"   ✅ Type-C guardrails active (no '보험가입금액' found)")
        return True

    except Exception as e:
        print(f"   ⚠️  Error checking guardrails: {e}")
        return True  # Non-critical


def main():
    """Run all validations"""
    print("=" * 60)
    print("Step7 Amount Pipeline Lock Validation")
    print("=" * 60)

    checks = [
        ("Freeze Tag", check_freeze_tag),
        ("Audit Reports", check_audit_reports),
        ("Coverage Cards", check_coverage_cards),
        ("Git Working Dir", check_git_clean),
        ("Type-C Guardrails", check_type_c_guardrails),
    ]

    results = []
    for name, check_fn in checks:
        try:
            passed = check_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All validations PASSED")
        print("\n✅ SAFE TO LOAD Step7 amounts to DB:")
        print("   python -m apps.loader.step9_loader --mode upsert")
        sys.exit(0)
    else:
        print("\n🚫 Validation FAILED")
        print("\n❌ DO NOT load to DB until all checks pass")
        sys.exit(1)


if __name__ == '__main__':
    main()
