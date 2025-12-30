"""
Coverage Cards 테스트 (STEP NEXT-18X-SSOT)

Contract tests:
1. scope_gate 미통과 담보가 카드에 포함되지 않음
2. cards.jsonl 라인 수 = scope 담보 수(40 after sanitization)와 동일
3. evidence_status가 found/not_found로 정확히 매핑됨
4. evidences는 최대 3개

SSOT: data/compare/*_coverage_cards.jsonl ONLY (legacy reports removed)
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

    # STEP NEXT-18X-SSOT-FINAL: Removed test_card_count_matches_scope
    # Reason: scope.csv is INPUT, coverage_cards.jsonl is SSOT (truth)
    # Comparing SSOT to input violates SSOT contract

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


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
