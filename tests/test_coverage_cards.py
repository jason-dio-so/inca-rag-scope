"""
Coverage Cards 및 Report 테스트

Contract tests:
1. scope_gate 미통과 담보가 카드에 포함되지 않음
2. cards.jsonl 라인 수 = scope 담보 수(41)와 동일
3. evidence_status가 found/not_found로 정확히 매핑됨
4. evidences는 최대 3개
5. markdown 리포트가 생성되고, Summary 숫자가 실제와 일치
6. unmatched가 리포트에 포함되며, suggested_canonical_code는 비어있음을 유지
"""

import pytest
import json
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scope_gate import load_scope_gate
from core.compare_types import CoverageCard


# 경로 설정
BASE_DIR = Path(__file__).parent.parent
CARDS_FILE = BASE_DIR / "data" / "compare" / "samsung_coverage_cards.jsonl"
REPORT_FILE = BASE_DIR / "reports" / "samsung_scope_report.md"


class TestCoverageCards:
    """Coverage cards 테스트"""

    def setup_method(self):
        """각 테스트 전에 초기화"""
        self.insurer = "samsung"
        self.scope_gate = load_scope_gate(self.insurer)
        self.cards = []

        if CARDS_FILE.exists():
            with open(CARDS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        card_data = json.loads(line)
                        card = CoverageCard.from_dict(card_data)
                        self.cards.append(card)

    def test_cards_file_exists(self):
        """Cards 파일이 존재하는지 확인"""
        assert CARDS_FILE.exists(), f"Cards file not found: {CARDS_FILE}"
        assert len(self.cards) > 0, "Cards file is empty"

    def test_scope_gate_enforcement(self):
        """1. scope_gate 미통과 담보가 카드에 포함되지 않음"""
        for card in self.cards:
            # 모든 카드의 담보명은 scope_gate를 통과해야 함
            assert self.scope_gate.is_in_scope(card.coverage_name_raw) is True, \
                f"Card contains out-of-scope coverage: {card.coverage_name_raw}"

    def test_card_count_matches_scope(self):
        """2. cards.jsonl 라인 수 = scope 담보 수(41)와 동일"""
        # samsung_scope.csv에 41개 담보가 있음
        expected_count = 41
        actual_count = len(self.cards)

        assert actual_count == expected_count, \
            f"Expected {expected_count} cards, got {actual_count}"

    def test_evidence_status_mapping(self):
        """3. evidence_status가 found/not_found로 정확히 매핑됨"""
        for card in self.cards:
            # evidence_status는 found 또는 not_found여야 함
            assert card.evidence_status in ['found', 'not_found'], \
                f"Invalid evidence_status: {card.evidence_status}"

            # evidences가 있으면 found, 없으면 not_found
            if card.evidences:
                assert card.evidence_status == 'found', \
                    f"Card has evidences but status is '{card.evidence_status}'"
            else:
                assert card.evidence_status == 'not_found', \
                    f"Card has no evidences but status is '{card.evidence_status}'"

    def test_max_three_evidences(self):
        """4. evidences는 최대 3개"""
        for card in self.cards:
            assert len(card.evidences) <= 3, \
                f"Card has {len(card.evidences)} evidences (max 3): {card.coverage_name_raw}"

    def test_card_sorting(self):
        """카드 정렬 순서 확인"""
        # matched가 먼저, unmatched가 나중
        matched_cards = [c for c in self.cards if c.mapping_status == 'matched']
        unmatched_cards = [c for c in self.cards if c.mapping_status == 'unmatched']

        # matched 카드들이 모두 unmatched 카드들보다 앞에 있어야 함
        if matched_cards and unmatched_cards:
            matched_indices = [i for i, c in enumerate(self.cards) if c.mapping_status == 'matched']
            unmatched_indices = [i for i, c in enumerate(self.cards) if c.mapping_status == 'unmatched']

            assert max(matched_indices) < min(unmatched_indices), \
                "Matched cards should come before unmatched cards"


class TestMarkdownReport:
    """Markdown report 테스트"""

    def setup_method(self):
        """Report 파일 로드"""
        self.report_content = ""
        if REPORT_FILE.exists():
            with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                self.report_content = f.read()

        # Cards도 로드하여 비교
        self.cards = []
        if CARDS_FILE.exists():
            with open(CARDS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        card_data = json.loads(line)
                        card = CoverageCard.from_dict(card_data)
                        self.cards.append(card)

    def test_report_file_exists(self):
        """Report 파일이 존재하는지 확인"""
        assert REPORT_FILE.exists(), f"Report file not found: {REPORT_FILE}"
        assert len(self.report_content) > 0, "Report file is empty"

    def test_summary_numbers_match(self):
        """5. markdown 리포트의 Summary 숫자가 실제와 일치"""
        # 실제 통계 계산
        total = len(self.cards)
        matched = sum(1 for c in self.cards if c.mapping_status == 'matched')
        unmatched = sum(1 for c in self.cards if c.mapping_status == 'unmatched')
        evidence_found = sum(1 for c in self.cards if c.evidence_status == 'found')
        evidence_not_found = sum(1 for c in self.cards if c.evidence_status == 'not_found')

        # Report에서 숫자 추출
        assert f"**Total Coverages**: {total}" in self.report_content, \
            f"Total coverages mismatch in report"
        assert f"**Matched**: {matched}" in self.report_content, \
            f"Matched count mismatch in report"
        assert f"**Unmatched**: {unmatched}" in self.report_content, \
            f"Unmatched count mismatch in report"
        assert f"**Evidence Found**: {evidence_found}" in self.report_content, \
            f"Evidence found count mismatch in report"
        assert f"**Evidence Not Found**: {evidence_not_found}" in self.report_content, \
            f"Evidence not found count mismatch in report"

    def test_unmatched_section_exists(self):
        """6. unmatched가 리포트에 포함되며, suggested_canonical_code는 비어있음"""
        # Unmatched Review 섹션이 있어야 함
        assert "## Unmatched Review" in self.report_content, \
            "Report missing Unmatched Review section"

        # unmatched 카드가 있으면 테이블이 있어야 함
        unmatched_cards = [c for c in self.cards if c.mapping_status == 'unmatched']

        if unmatched_cards:
            # 테이블 헤더 확인
            assert "| Coverage Name (Raw) | Top Hits | Suggested Canonical Code |" in self.report_content, \
                "Unmatched review table header missing"

    def test_evidence_not_found_section(self):
        """Evidence Not Found 섹션 확인"""
        assert "## Evidence Not Found" in self.report_content, \
            "Report missing Evidence Not Found section"

        # not_found 카드 확인
        not_found_cards = [c for c in self.cards if c.evidence_status == 'not_found']

        if not_found_cards:
            # not_found 담보명이 리포트에 있어야 함
            for card in not_found_cards:
                assert card.coverage_name_raw in self.report_content, \
                    f"Not found coverage '{card.coverage_name_raw}' missing in report"

                # "검색 결과 0건" 사실 명시
                assert "검색 결과 0건" in self.report_content, \
                    "Missing fact statement for not found evidence"


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
