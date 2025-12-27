"""
Consistency Lock Tests

Contract tests:
1. Snapshot-based line counts are non-zero and consistent
2. compare_stats.json total_codes_compared == wc -l compare.jsonl
"""

import pytest
import json
from pathlib import Path


# 경로 설정
BASE_DIR = Path(__file__).parent.parent


class TestConsistency:
    """Consistency lock tests"""

    def test_scope_csv_line_counts_non_zero(self):
        """Scope CSV files have expected line counts (with headers)"""
        samsung_scope = BASE_DIR / "data" / "scope" / "samsung_scope.csv"
        meritz_scope = BASE_DIR / "data" / "scope" / "meritz_scope.csv"

        samsung_lines = len(samsung_scope.read_text().strip().split('\n'))
        meritz_lines = len(meritz_scope.read_text().strip().split('\n'))

        # Expected: header + data rows
        assert samsung_lines == 42, f"Samsung scope expected 42 lines, got {samsung_lines}"
        assert meritz_lines == 35, f"Meritz scope expected 35 lines, got {meritz_lines}"

    def test_cards_match_scope_data_count(self):
        """Cards JSONL line count matches scope data rows (excluding header)"""
        samsung_scope = BASE_DIR / "data" / "scope" / "samsung_scope.csv"
        meritz_scope = BASE_DIR / "data" / "scope" / "meritz_scope.csv"
        samsung_cards = BASE_DIR / "data" / "compare" / "samsung_coverage_cards.jsonl"
        meritz_cards = BASE_DIR / "data" / "compare" / "meritz_coverage_cards.jsonl"

        # Scope CSV has header, cards JSONL does not
        samsung_scope_lines = len(samsung_scope.read_text().strip().split('\n')) - 1
        meritz_scope_lines = len(meritz_scope.read_text().strip().split('\n')) - 1

        samsung_cards_lines = len(samsung_cards.read_text().strip().split('\n'))
        meritz_cards_lines = len(meritz_cards.read_text().strip().split('\n'))

        assert samsung_cards_lines == samsung_scope_lines, \
            f"Samsung cards {samsung_cards_lines} != scope data {samsung_scope_lines}"
        assert meritz_cards_lines == meritz_scope_lines, \
            f"Meritz cards {meritz_cards_lines} != scope data {meritz_scope_lines}"

    def test_evidence_pack_match_scope_data_count(self):
        """Evidence pack JSONL line count matches scope data rows"""
        samsung_scope = BASE_DIR / "data" / "scope" / "samsung_scope.csv"
        meritz_scope = BASE_DIR / "data" / "scope" / "meritz_scope.csv"
        samsung_evidence = BASE_DIR / "data" / "evidence_pack" / "samsung_evidence_pack.jsonl"
        meritz_evidence = BASE_DIR / "data" / "evidence_pack" / "meritz_evidence_pack.jsonl"

        samsung_scope_lines = len(samsung_scope.read_text().strip().split('\n')) - 1
        meritz_scope_lines = len(meritz_scope.read_text().strip().split('\n')) - 1

        samsung_evidence_lines = len(samsung_evidence.read_text().strip().split('\n'))
        meritz_evidence_lines = len(meritz_evidence.read_text().strip().split('\n'))

        assert samsung_evidence_lines == samsung_scope_lines, \
            f"Samsung evidence {samsung_evidence_lines} != scope data {samsung_scope_lines}"
        assert meritz_evidence_lines == meritz_scope_lines, \
            f"Meritz evidence {meritz_evidence_lines} != scope data {meritz_scope_lines}"

    def test_compare_stats_matches_jsonl_line_count(self):
        """compare_stats.json total_codes_compared == wc -l compare.jsonl"""
        compare_jsonl = BASE_DIR / "data" / "compare" / "samsung_vs_meritz_compare.jsonl"
        stats_json = BASE_DIR / "data" / "compare" / "compare_stats.json"

        compare_lines = len(compare_jsonl.read_text().strip().split('\n'))

        with open(stats_json, 'r') as f:
            stats = json.load(f)

        assert stats['total_codes_compared'] == compare_lines, \
            f"Stats total_codes_compared {stats['total_codes_compared']} != JSONL lines {compare_lines}"

    def test_stats_internal_consistency(self):
        """Stats fields are internally consistent"""
        stats_json = BASE_DIR / "data" / "compare" / "compare_stats.json"

        with open(stats_json, 'r') as f:
            stats = json.load(f)

        total = stats['total_codes_compared']
        both_matched = stats['both_matched_count']
        either_unmatched = stats['either_unmatched_count']
        only_in_a = stats['only_in_a']
        only_in_b = stats['only_in_b']

        # Codes in both insurers: both_matched + either_unmatched
        # Codes only in one: only_in_a + only_in_b
        # Total should be sum of all
        codes_in_both = both_matched + either_unmatched
        codes_only = only_in_a + only_in_b

        assert codes_in_both + codes_only == total, \
            f"Inconsistent stats: {codes_in_both} + {codes_only} != {total}"

    def test_snapshot_file_exists(self):
        """Consistency snapshot file exists"""
        snapshot = BASE_DIR / "reports" / "step5_consistency_snapshot.txt"
        assert snapshot.exists(), "Consistency snapshot not found"

        content = snapshot.read_text()
        assert "=== STATS JSON ===" in content, "Snapshot missing stats section"
        assert "total_codes_compared" in content, "Snapshot missing stats data"

    def test_locked_values_match_snapshot(self):
        """Key values match the consistency snapshot"""
        stats_json = BASE_DIR / "data" / "compare" / "compare_stats.json"

        with open(stats_json, 'r') as f:
            stats = json.load(f)

        # These are the locked values from snapshot
        assert stats['total_codes_compared'] == 25, "total_codes_compared changed"
        assert stats['both_matched_count'] == 15, "both_matched_count changed"
        assert stats['evidence_found_both'] == 15, "evidence_found_both changed"
        assert stats['only_in_a'] == 4, "only_in_a changed"
        assert stats['only_in_b'] == 6, "only_in_b changed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
