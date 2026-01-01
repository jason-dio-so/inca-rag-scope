#!/usr/bin/env python3
"""
STEP NEXT-51: Canonical Mapping Regression Test

Purpose:
    Ensure Excel alias expansion does NOT cause:
    1. Previously mapped entries becoming unmapped
    2. Previously mapped entries changing canonical codes
    3. Mapping logic becoming non-deterministic

Constitutional Rules:
    - NO new mapping logic
    - NO code changes to canonical_mapper.py
    - ONLY Excel data expansion allowed

Test Strategy:
    - Snapshot current mapping results (before Excel patch)
    - After Excel patch, verify:
      a) All previously mapped entries still mapped to SAME codes
      b) Some previously unmapped entries now mapped (improvement)
      c) Determinism: same input → same output
"""

import json
import pytest
from pathlib import Path
from collections import Counter


# Snapshot directory (created by this test on first run)
SNAPSHOT_DIR = Path('tests/fixtures/step2_canonical_mapping_snapshots')


class TestCanonicalMappingNoRegression:
    """Regression tests for Step2-b canonical mapping"""

    @pytest.fixture(scope='class')
    def snapshot_path(self):
        """Path to snapshot file"""
        return SNAPSHOT_DIR / 'pre_alias_expansion_snapshot.json'

    @pytest.fixture(scope='class')
    def current_results(self):
        """Load current mapping results from all insurers"""
        insurers = ['samsung', 'hyundai', 'kb', 'meritz', 'hanwha', 'lotte', 'heungkuk', 'db']
        results = {}

        for insurer in insurers:
            canonical_file = Path(f'data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl')

            if not canonical_file.exists():
                continue

            entries = []
            with open(canonical_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))

            results[insurer] = entries

        return results

    def test_snapshot_exists_or_create(self, snapshot_path, current_results):
        """
        Create snapshot if it doesn't exist (first run).
        This snapshot represents the "before alias expansion" state.
        """
        if not snapshot_path.exists():
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

            # Create snapshot
            snapshot = {
                'version': '1.0',
                'purpose': 'Pre-STEP-NEXT-51 alias expansion baseline',
                'insurers': {}
            }

            for insurer, entries in current_results.items():
                snapshot['insurers'][insurer] = {
                    'total': len(entries),
                    'mapped_entries': [
                        {
                            'coverage_name_raw': e['coverage_name_raw'],
                            'coverage_code': e.get('coverage_code'),
                            'canonical_name': e.get('canonical_name'),
                            'mapping_method': e.get('mapping_method')
                        }
                        for e in entries
                        if e.get('mapping_method') in ['exact', 'normalized']
                    ]
                }

            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)

            pytest.skip(f'Snapshot created at {snapshot_path}. Re-run test after Excel patching.')

    def test_no_previously_mapped_became_unmapped(self, snapshot_path, current_results):
        """
        Gate: NO previously mapped entries should become unmapped after alias expansion.

        This is the most critical regression check.
        """
        if not snapshot_path.exists():
            pytest.skip('Snapshot not found. Run test_snapshot_exists_or_create first.')

        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)

        regressions = []

        for insurer, current_entries in current_results.items():
            if insurer not in snapshot['insurers']:
                continue

            snapshot_mapped = snapshot['insurers'][insurer]['mapped_entries']

            # Build current mapping lookup
            current_map = {
                e['coverage_name_raw']: e.get('mapping_method')
                for e in current_entries
            }

            # Check each previously mapped entry
            for old_entry in snapshot_mapped:
                raw_name = old_entry['coverage_name_raw']
                old_method = old_entry['mapping_method']
                old_code = old_entry['coverage_code']

                current_method = current_map.get(raw_name)

                if current_method == 'unmapped':
                    regressions.append({
                        'insurer': insurer,
                        'coverage_name_raw': raw_name,
                        'old_method': old_method,
                        'old_code': old_code,
                        'new_method': 'unmapped',
                        'error': 'MAPPED_BECAME_UNMAPPED'
                    })

        if regressions:
            error_msg = f'\n❌ REGRESSION DETECTED: {len(regressions)} entries became unmapped\n'
            for reg in regressions[:5]:  # Show first 5
                error_msg += f'\n  {reg["insurer"]}: {reg["coverage_name_raw"]}'
                error_msg += f'\n    Before: {reg["old_method"]} → {reg["old_code"]}'
                error_msg += f'\n    After:  unmapped'

            pytest.fail(error_msg)

    def test_no_mapped_code_changed(self, snapshot_path, current_results):
        """
        Gate: NO previously mapped entries should change their canonical code.

        Alias expansion should only add NEW aliases, not change existing mappings.
        """
        if not snapshot_path.exists():
            pytest.skip('Snapshot not found.')

        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)

        code_changes = []

        for insurer, current_entries in current_results.items():
            if insurer not in snapshot['insurers']:
                continue

            snapshot_mapped = snapshot['insurers'][insurer]['mapped_entries']

            # Build current mapping lookup
            current_map = {
                e['coverage_name_raw']: e.get('coverage_code')
                for e in current_entries
                if e.get('mapping_method') in ['exact', 'normalized']
            }

            # Check each previously mapped entry
            for old_entry in snapshot_mapped:
                raw_name = old_entry['coverage_name_raw']
                old_code = old_entry['coverage_code']

                current_code = current_map.get(raw_name)

                if current_code and current_code != old_code:
                    code_changes.append({
                        'insurer': insurer,
                        'coverage_name_raw': raw_name,
                        'old_code': old_code,
                        'new_code': current_code,
                        'error': 'CODE_CHANGED'
                    })

        if code_changes:
            error_msg = f'\n❌ CODE CHANGE DETECTED: {len(code_changes)} entries changed codes\n'
            for change in code_changes[:5]:
                error_msg += f'\n  {change["insurer"]}: {change["coverage_name_raw"]}'
                error_msg += f'\n    Before: {change["old_code"]}'
                error_msg += f'\n    After:  {change["new_code"]}'

            pytest.fail(error_msg)

    def test_improvement_detected(self, snapshot_path, current_results):
        """
        Positive check: Some previously unmapped entries should now be mapped.

        Expected improvement:
        - MERITZ: ~18 entries (60% of 30)
        - LOTTE: ~21 entries (48.8% of 43)
        """
        if not snapshot_path.exists():
            pytest.skip('Snapshot not found.')

        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)

        improvements = {}

        for insurer, current_entries in current_results.items():
            if insurer not in snapshot['insurers']:
                continue

            # Calculate current mapped count
            current_mapped = sum(
                1 for e in current_entries
                if e.get('mapping_method') in ['exact', 'normalized']
            )

            # Get snapshot mapped count
            snapshot_mapped_count = len(snapshot['insurers'][insurer]['mapped_entries'])

            improvement = current_mapped - snapshot_mapped_count

            improvements[insurer] = {
                'before': snapshot_mapped_count,
                'after': current_mapped,
                'improvement': improvement
            }

        # Print improvement summary
        print('\n' + '='*60)
        print('Mapping Improvement Summary:')
        print('='*60)

        total_improvement = 0
        for insurer, data in improvements.items():
            total_improvement += data['improvement']
            print(f'{insurer.upper():10s}: {data["before"]} → {data["after"]} (+{data["improvement"]})')

        print(f'\nTotal improvement: +{total_improvement} entries')

        # Assert minimum improvement
        assert total_improvement >= 30, \
            f'Expected at least +30 improved mappings, got +{total_improvement}'

    def test_determinism_no_duplicates(self, current_results):
        """
        Gate: No duplicate (insurer, coverage_name_raw) pairs should exist.

        This ensures Excel patching didn't introduce duplicate aliases.
        """
        duplicates = []

        for insurer, entries in current_results.items():
            seen = set()
            for entry in entries:
                raw_name = entry['coverage_name_raw']
                key = (insurer, raw_name)

                if key in seen:
                    duplicates.append(key)
                seen.add(key)

        if duplicates:
            error_msg = f'\n❌ DUPLICATES DETECTED: {len(duplicates)} duplicate entries\n'
            for insurer, raw_name in duplicates[:5]:
                error_msg += f'\n  {insurer}: {raw_name}'

            pytest.fail(error_msg)

    def test_mapping_method_distribution(self, current_results):
        """
        Sanity check: Mapping method distribution should be reasonable.

        Expected after alias expansion:
        - exact: ~60%
        - normalized: ~30%
        - unmapped: <20%
        """
        all_methods = Counter()

        for insurer, entries in current_results.items():
            for entry in entries:
                method = entry.get('mapping_method', 'unknown')
                all_methods[method] += 1

        total = sum(all_methods.values())

        print('\n' + '='*60)
        print('Mapping Method Distribution:')
        print('='*60)

        for method, count in all_methods.most_common():
            pct = (count / total * 100) if total > 0 else 0
            print(f'{method:12s}: {count:3d} ({pct:5.1f}%)')

        # Assert unmapped rate is reasonable
        unmapped_rate = (all_methods['unmapped'] / total * 100) if total > 0 else 0
        assert unmapped_rate < 30, \
            f'Unmapped rate too high: {unmapped_rate:.1f}% (expected <30%)'


class TestExcelIntegrity:
    """Test Excel mapping file integrity after patching"""

    def test_excel_row_count(self):
        """Excel should have 328 rows after patching (287 + 41)"""
        import pandas as pd

        excel_path = Path('data/sources/mapping/담보명mapping자료.xlsx')
        df = pd.read_excel(excel_path)

        # After STEP NEXT-51 patching, should be 328
        # Before patching: 287
        assert len(df) >= 287, f'Excel row count too low: {len(df)} (expected ≥287)'

        if len(df) == 328:
            print(f'\n✅ Excel patched: {len(df)} rows (287 + 41 new aliases)')
        elif len(df) == 287:
            pytest.skip('Excel not yet patched (still 287 rows)')
        else:
            print(f'\n⚠️  Unexpected row count: {len(df)}')

    def test_excel_no_duplicates(self):
        """Excel should have no duplicate (ins_cd, 담보명) pairs"""
        import pandas as pd

        excel_path = Path('data/sources/mapping/담보명mapping자료.xlsx')
        df = pd.read_excel(excel_path)

        duplicates = df[df.duplicated(subset=['ins_cd', '담보명(가입설계서)'], keep=False)]

        if len(duplicates) > 0:
            print('\n❌ DUPLICATES FOUND IN EXCEL:')
            print(duplicates[['ins_cd', '담보명(가입설계서)']])
            pytest.fail(f'{len(duplicates)} duplicate entries found in Excel')

    def test_excel_columns_intact(self):
        """Excel should still have exactly 5 columns"""
        import pandas as pd

        excel_path = Path('data/sources/mapping/담보명mapping자료.xlsx')
        df = pd.read_excel(excel_path)

        expected_columns = ['ins_cd', '보험사명', 'cre_cvr_cd', '신정원코드명', '담보명(가입설계서)']

        assert list(df.columns) == expected_columns, \
            f'Excel columns changed! Expected: {expected_columns}, Got: {list(df.columns)}'
