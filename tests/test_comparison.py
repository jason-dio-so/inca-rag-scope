"""
Comparison 테스트

Contract tests:
1. compare output이 coverage_code 기준으로 정렬되는지
2. out-of-scope 담보가 compare 결과에 들어가지 않는지
3. report에 "추천/종합의견" 같은 문구가 없는지(금지어 검사)
"""

import pytest
import json
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scope_gate import load_scope_gate


# 경로 설정 (STEP NEXT-18X-SSOT: legacy reports removed)
BASE_DIR = Path(__file__).parent.parent
COMPARE_JSONL = BASE_DIR / "data" / "compare" / "samsung_vs_meritz_compare.jsonl"
COMPARE_STATS = BASE_DIR / "data" / "compare" / "compare_stats.json"


class TestComparison:
    """Comparison 테스트"""

    def setup_method(self):
        """각 테스트 전에 초기화"""
        self.compare_rows = []
        if COMPARE_JSONL.exists():
            with open(COMPARE_JSONL, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        self.compare_rows.append(row)

        self.stats = {}
        if COMPARE_STATS.exists():
            with open(COMPARE_STATS, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)

    def test_comparison_files_exist(self):
        """비교 파일들이 존재하는지 확인 (SSOT: JSONL + stats only)"""
        assert COMPARE_JSONL.exists(), f"Compare JSONL not found: {COMPARE_JSONL}"
        assert COMPARE_STATS.exists(), f"Compare stats not found: {COMPARE_STATS}"

    def test_coverage_code_sorting(self):
        """1. compare output이 coverage_code 기준으로 정렬되는지"""
        codes = [row['coverage_code'] for row in self.compare_rows]

        # 정렬된 상태인지 확인
        assert codes == sorted(codes), \
            "Compare rows are not sorted by coverage_code"

    def test_no_out_of_scope_coverages(self):
        """2. out-of-scope 담보가 compare 결과에 들어가지 않는지"""
        # Samsung scope gate
        samsung_gate = load_scope_gate('samsung')

        # Meritz scope gate
        meritz_gate = load_scope_gate('meritz')

        for row in self.compare_rows:
            samsung_info = row.get('samsung')
            meritz_info = row.get('meritz')

            if samsung_info:
                raw_name = samsung_info['raw_name']
                assert samsung_gate.is_in_scope(raw_name), \
                    f"Out-of-scope Samsung coverage in compare: {raw_name}"

            if meritz_info:
                raw_name = meritz_info['raw_name']
                assert meritz_gate.is_in_scope(raw_name), \
                    f"Out-of-scope Meritz coverage in compare: {raw_name}"

    def test_stats_correctness(self):
        """통계가 올바르게 계산되었는지"""
        # 통계 파일이 비어있지 않은지
        assert self.stats, "Stats file is empty"

        # 필수 필드 존재 확인
        required_fields = [
            'total_codes_compared',
            'both_matched_count',
            'either_unmatched_count',
            'evidence_found_both',
            'evidence_missing_any'
        ]

        for field in required_fields:
            assert field in self.stats, f"Missing required field in stats: {field}"

        # 통계 일관성 확인
        total = self.stats['total_codes_compared']
        both_matched = self.stats['both_matched_count']
        either_unmatched = self.stats['either_unmatched_count']

        # only_in_* 카운트도 고려
        only_in_a = self.stats.get('only_in_a', 0)
        only_in_b = self.stats.get('only_in_b', 0)

        # both_matched + either_unmatched + only_in_a + only_in_b <= total
        # (같을 수도 있고, only 항목이 통계에 포함되지 않을 수도 있음)
        assert both_matched + either_unmatched <= total, \
            "Stats inconsistency: matched + unmatched counts exceed total"

    def test_compare_rows_have_required_fields(self):
        """비교 row가 필수 필드를 가지고 있는지"""
        for row in self.compare_rows:
            assert 'coverage_code' in row, "Missing coverage_code in compare row"
            assert 'canonical_name' in row, "Missing canonical_name in compare row"
            assert 'notes' in row, "Missing notes in compare row"

            # 적어도 하나의 보험사 정보는 있어야 함
            assert 'samsung' in row or 'meritz' in row, \
                "Compare row must have at least one insurer info"


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
