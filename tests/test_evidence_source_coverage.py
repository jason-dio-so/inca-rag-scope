"""
REBOOT STEP 5: Evidence Source Coverage Tests (MANDATORY)

모든 테스트가 PASS해야 함.
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def base_dir():
    """프로젝트 루트 디렉토리"""
    return Path(__file__).parent.parent


@pytest.fixture
def coverage_cards(base_dir):
    """Coverage cards 로드 (삼성 & 메리츠)"""
    cards = {'samsung': [], 'meritz': []}

    for insurer in ['samsung', 'meritz']:
        cards_file = base_dir / 'data' / 'compare' / f'{insurer}_coverage_cards.jsonl'
        if cards_file.exists():
            with open(cards_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        cards[insurer].append(json.loads(line))

    return cards


def test_all_cards_have_hits_by_doc_type(coverage_cards):
    """모든 coverage_card에 hits_by_doc_type 필드 존재"""
    for insurer in ['samsung', 'meritz']:
        for card in coverage_cards[insurer]:
            assert 'hits_by_doc_type' in card, f"Missing hits_by_doc_type in {insurer} card: {card.get('coverage_name_raw')}"


def test_all_three_doc_types_present(coverage_cards):
    """세 문서 유형(약관, 사업방법서, 상품요약서)이 모두 명시됨"""
    for insurer in ['samsung', 'meritz']:
        for card in coverage_cards[insurer]:
            hits = card.get('hits_by_doc_type', {})
            assert '약관' in hits, f"Missing '약관' in {insurer} card: {card.get('coverage_name_raw')}"
            assert '사업방법서' in hits, f"Missing '사업방법서' in {insurer} card: {card.get('coverage_name_raw')}"
            assert '상품요약서' in hits, f"Missing '상품요약서' in {insurer} card: {card.get('coverage_name_raw')}"


def test_policy_only_flag_accuracy(coverage_cards):
    """policy_only flag는 조건을 정확히 만족할 때만 생성"""
    for insurer in ['samsung', 'meritz']:
        for card in coverage_cards[insurer]:
            hits = card.get('hits_by_doc_type', {})
            flags = card.get('flags', [])

            # policy_only 조건: 약관 >= 1, 사업방법서 = 0, 상품요약서 = 0
            should_have_policy_only = (
                hits.get('약관', 0) >= 1 and
                hits.get('사업방법서', 0) == 0 and
                hits.get('상품요약서', 0) == 0
            )

            has_policy_only = 'policy_only' in flags

            assert should_have_policy_only == has_policy_only, \
                f"policy_only flag mismatch in {insurer} card: {card.get('coverage_name_raw')} (hits: {hits}, flags: {flags})"


def test_no_forbidden_words_in_reports(base_dir):
    """Report에 금지어(추천, 종합의견, 유리, 불리) 없음"""
    forbidden_words = ['추천', '종합의견', '유리', '불리']

    for insurer in ['samsung', 'meritz']:
        report_file = base_dir / 'reports' / f'{insurer}_scope_report.md'
        if report_file.exists():
            content = report_file.read_text(encoding='utf-8')
            for word in forbidden_words:
                assert word not in content, f"Forbidden word '{word}' found in {insurer} report"


def test_cancer_diagnosis_doc_type_breakdown(coverage_cards):
    """암진단비 coverage에 대해 doc_type별 hit 수가 출력됨"""
    cancer_keywords = ['암진단비', '암', 'cancer']

    for insurer in ['samsung', 'meritz']:
        cancer_cards = [
            card for card in coverage_cards[insurer]
            if any(kw in (card.get('coverage_name_canonical', '') or card.get('coverage_name_raw', ''))
                   for kw in cancer_keywords)
        ]

        # 최소 1개 이상의 암진단비 담보가 있어야 함
        assert len(cancer_cards) > 0, f"No cancer diagnosis coverage found in {insurer}"

        # 모든 암진단비 담보는 hits_by_doc_type을 가져야 함
        for card in cancer_cards:
            assert 'hits_by_doc_type' in card, f"Missing hits_by_doc_type in {insurer} cancer card"
            hits = card['hits_by_doc_type']

            # 세 문서 유형 모두 명시되어야 함
            assert '약관' in hits
            assert '사업방법서' in hits
            assert '상품요약서' in hits

            # 숫자 타입이어야 함
            assert isinstance(hits['약관'], int)
            assert isinstance(hits['사업방법서'], int)
            assert isinstance(hits['상품요약서'], int)


def test_evidence_pack_has_doc_type_breakdown(base_dir):
    """Evidence pack에도 hits_by_doc_type 포함"""
    for insurer in ['samsung', 'meritz']:
        pack_file = base_dir / 'data' / 'evidence_pack' / f'{insurer}_evidence_pack.jsonl'
        if pack_file.exists():
            with open(pack_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        assert 'hits_by_doc_type' in item, f"Missing hits_by_doc_type in {insurer} evidence pack"
                        hits = item['hits_by_doc_type']
                        assert '약관' in hits
                        assert '사업방법서' in hits
                        assert '상품요약서' in hits
