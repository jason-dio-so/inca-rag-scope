#!/usr/bin/env python3
"""
STEP NEXT-F: Cross-Coverage Contamination Check

Validates that ALL G5-demoted slots have:
1. status = UNKNOWN
2. value = None

This ensures ZERO contaminated values are exposed to customers.
"""

import json
import sys
from pathlib import Path


def main():
    registry_codes = ['A4200_1', 'A4209', 'A4210', 'A4299_1', 'A4103', 'A4105']
    contamination_count = 0
    diagnosis_row_count = 0
    g5_demotion_count = 0

    compare_rows_file = Path("data/compare_v1/compare_rows_v1.jsonl")

    with open(compare_rows_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)
            code = row.get('identity', {}).get('coverage_code')

            if code not in registry_codes:
                continue

            diagnosis_row_count += 1
            slots = row.get('slots', {})

            for slot_key, slot in slots.items():
                status = slot.get('status')
                value = slot.get('value')
                notes = slot.get('notes') or ''

                if 'G5 Gate:' not in notes:
                    continue

                g5_demotion_count += 1

                # Check for contamination: if G5 gate detected issue but status is NOT UNKNOWN
                if status != 'UNKNOWN':
                    contamination_count += 1
                    print(f'❌ CONTAMINATION: {code} / {slot_key} / status={status} (expected UNKNOWN)')

                # Check for contamination: if G5 gate detected issue but value is NOT None
                if value is not None:
                    contamination_count += 1
                    print(f'❌ CONTAMINATION: {code} / {slot_key} / value={value} (expected None)')

    print("=" * 80)
    print("STEP NEXT-F: Cross-Coverage Contamination Check")
    print("=" * 80)
    print()
    print(f"📊 Scanned {diagnosis_row_count} diagnosis coverage rows")
    print(f"📊 Found {g5_demotion_count} G5 demotions")
    print()

    if contamination_count == 0:
        print("✅ ✅ ✅ CONTAMINATION = 0 ✅ ✅ ✅")
        print()
        print("All G5-demoted slots have:")
        print("  - status = UNKNOWN")
        print("  - value = None")
        print()
        print("Customer exposure: ZERO incorrect values")
        print()
        return 0
    else:
        print(f"❌ FAILED: {contamination_count} slots have wrong status/value despite G5 demotion")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
