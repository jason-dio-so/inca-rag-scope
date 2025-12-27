"""
Multi-Insurer Comparison Tests

Contract tests:
1. Matrix sorted by coverage_code
2. No out-of-scope coverages
3. No forbidden phrases in report
"""

import pytest
import json
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scope_gate import load_scope_gate


# 경로 설정
BASE_DIR = Path(__file__).parent.parent
MATRIX_JSON = BASE_DIR / "data" / "compare" / "all_insurers_matrix.json"
STATS_JSON = BASE_DIR / "data" / "compare" / "all_insurers_stats.json"
OVERVIEW_MD = BASE_DIR / "reports" / "all_insurers_overview.md"


class TestMultiInsurer:
    """Multi-insurer comparison tests"""

    def setup_method(self):
        """각 테스트 전에 초기화"""
        self.matrix = []
        if MATRIX_JSON.exists():
            with open(MATRIX_JSON, 'r', encoding='utf-8') as f:
                self.matrix = json.load(f)

        self.stats = {}
        if STATS_JSON.exists():
            with open(STATS_JSON, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)

        self.report = ""
        if OVERVIEW_MD.exists():
            with open(OVERVIEW_MD, 'r', encoding='utf-8') as f:
                self.report = f.read()

    def test_files_exist(self):
        """Multi-insurer files exist"""
        assert MATRIX_JSON.exists(), f"Matrix not found: {MATRIX_JSON}"
        assert STATS_JSON.exists(), f"Stats not found: {STATS_JSON}"
        assert OVERVIEW_MD.exists(), f"Report not found: {OVERVIEW_MD}"

    def test_matrix_sorted_by_coverage_code(self):
        """1. Matrix sorted by coverage_code"""
        codes = [row['coverage_code'] for row in self.matrix]

        assert codes == sorted(codes), \
            "Matrix rows are not sorted by coverage_code"

    def test_no_out_of_scope_coverages(self):
        """2. No out-of-scope coverages in matrix"""
        # Get all insurers from stats
        insurers = list(self.stats.get('unmatched_rate_per_insurer', {}).keys())

        # Load scope gates
        scope_gates = {}
        for insurer in insurers:
            scope_gates[insurer] = load_scope_gate(insurer)

        # Check each matrix row
        for row in self.matrix:
            for insurer, data in row['insurers'].items():
                if data.get('present', False):
                    raw_name = data.get('raw_name')
                    if raw_name:
                        assert scope_gates[insurer].is_in_scope(raw_name), \
                            f"Out-of-scope coverage in {insurer}: {raw_name}"

    def test_no_forbidden_phrases_in_report(self):
        """3. No forbidden phrases in report"""
        forbidden_phrases = [
            '추천',
            '종합의견',
            '유리',
            '불리',
            '권장',
            '제안',
            '판단',
            '평가',
            '요약하면',
            '결론적으로'
        ]

        for phrase in forbidden_phrases:
            assert phrase not in self.report, \
                f"Forbidden phrase '{phrase}' found in multi-insurer report"

    def test_stats_have_required_fields(self):
        """Stats have required fields"""
        required_fields = [
            'total_canonical_codes',
            'total_insurers',
            'insurer_count_per_code',
            'codes_common_to_all',
            'codes_unique_per_insurer',
            'unmatched_rate_per_insurer'
        ]

        for field in required_fields:
            assert field in self.stats, f"Missing required field: {field}"

    def test_matrix_has_valid_structure(self):
        """Matrix rows have valid structure"""
        for row in self.matrix:
            assert 'coverage_code' in row, "Missing coverage_code"
            assert 'canonical_name' in row, "Missing canonical_name"
            assert 'insurers' in row, "Missing insurers"

            # Each insurer entry should have 'present'
            for insurer, data in row['insurers'].items():
                assert 'present' in data, f"Missing 'present' for {insurer}"

                if data['present']:
                    assert 'raw_name' in data, f"Missing raw_name for {insurer}"
                    assert 'matched' in data, f"Missing matched for {insurer}"
                    assert 'evidence_found' in data, f"Missing evidence_found for {insurer}"

    def test_common_codes_are_actually_common(self):
        """Codes listed as common are actually in all insurers"""
        common_codes = set(self.stats.get('codes_common_to_all', []))
        all_insurers = set(self.stats.get('unmatched_rate_per_insurer', {}).keys())

        for code in common_codes:
            # Find this code in matrix
            row = next((r for r in self.matrix if r['coverage_code'] == code), None)
            assert row is not None, f"Common code {code} not found in matrix"

            # Check present in all insurers
            present_insurers = {
                ins for ins, data in row['insurers'].items()
                if data.get('present', False)
            }

            assert present_insurers == all_insurers, \
                f"Code {code} listed as common but not in all insurers: {present_insurers} vs {all_insurers}"

    def test_unique_codes_are_actually_unique(self):
        """Codes listed as unique are actually in only one insurer"""
        for insurer, unique_codes in self.stats.get('codes_unique_per_insurer', {}).items():
            for code in unique_codes:
                # Find this code in matrix
                row = next((r for r in self.matrix if r['coverage_code'] == code), None)
                assert row is not None, f"Unique code {code} not found in matrix"

                # Check present in only this insurer
                present_insurers = [
                    ins for ins, data in row['insurers'].items()
                    if data.get('present', False)
                ]

                assert len(present_insurers) == 1, \
                    f"Code {code} listed as unique for {insurer} but present in {present_insurers}"
                assert present_insurers[0] == insurer, \
                    f"Code {code} listed as unique for {insurer} but actually in {present_insurers[0]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
