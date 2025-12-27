"""
REBOOT STEP 6: Single Coverage A4200_1 Tests (MANDATORY)

암진단비 단일 담보 deep dive 검증
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def base_dir():
    """프로젝트 루트 디렉토리"""
    return Path(__file__).parent.parent


@pytest.fixture
def samsung_profile(base_dir):
    """Samsung A4200_1 profile"""
    profile_file = base_dir / 'data' / 'single' / 'samsung_A4200_1_profile.json'
    with open(profile_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def meritz_profile(base_dir):
    """Meritz A4200_1 profile"""
    profile_file = base_dir / 'data' / 'single' / 'meritz_A4200_1_profile.json'
    with open(profile_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def comparison(base_dir):
    """Comparison JSON"""
    compare_file = base_dir / 'data' / 'single' / 'samsung_vs_meritz_A4200_1_compare.json'
    with open(compare_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def report_text(base_dir):
    """Report markdown text"""
    report_file = base_dir / 'reports' / 'single_A4200_1_samsung_vs_meritz.md'
    with open(report_file, 'r', encoding='utf-8') as f:
        return f.read()


def test_profile_files_exist(base_dir):
    """두 profile json 파일 존재"""
    samsung_file = base_dir / 'data' / 'single' / 'samsung_A4200_1_profile.json'
    meritz_file = base_dir / 'data' / 'single' / 'meritz_A4200_1_profile.json'

    assert samsung_file.exists(), f"Samsung profile not found: {samsung_file}"
    assert meritz_file.exists(), f"Meritz profile not found: {meritz_file}"


def test_coverage_code_is_a4200_1(samsung_profile, meritz_profile):
    """두 profile의 coverage_code == A4200_1"""
    assert samsung_profile['coverage_code'] == 'A4200_1', "Samsung coverage_code mismatch"
    assert meritz_profile['coverage_code'] == 'A4200_1', "Meritz coverage_code mismatch"


def test_doc_type_coverage_has_three_keys(samsung_profile, meritz_profile):
    """doc_type_coverage에 3개 키 존재 (약관, 사업방법서, 상품요약서)"""
    for profile, name in [(samsung_profile, 'samsung'), (meritz_profile, 'meritz')]:
        doc_type_coverage = profile.get('doc_type_coverage', {})
        assert '약관' in doc_type_coverage, f"{name}: Missing '약관'"
        assert '사업방법서' in doc_type_coverage, f"{name}: Missing '사업방법서'"
        assert '상품요약서' in doc_type_coverage, f"{name}: Missing '상품요약서'"


def test_no_forbidden_words_in_report(report_text):
    """리포트에 금지어 없음 (추천, 종합의견, 유리, 불리, 해석)"""
    forbidden_words = ['추천', '종합의견', '유리', '불리', '해석']

    for word in forbidden_words:
        assert word not in report_text, f"Forbidden word '{word}' found in report"


def test_doc_type_hits_in_report(report_text, comparison):
    """리포트에 삼성/메리츠의 doc_type hit 수가 그대로 들어있음 (STEP 5와 일치)"""
    samsung_hits = comparison['doc_type_hits']['samsung']
    meritz_hits = comparison['doc_type_hits']['meritz']

    # 약관 hit 수
    assert str(samsung_hits['약관']) in report_text, "Samsung 약관 hits not in report"
    assert str(meritz_hits['약관']) in report_text, "Meritz 약관 hits not in report"

    # 사업방법서 hit 수
    assert str(samsung_hits['사업방법서']) in report_text, "Samsung 사업방법서 hits not in report"
    assert str(meritz_hits['사업방법서']) in report_text, "Meritz 사업방법서 hits not in report"

    # 상품요약서 hit 수
    assert str(samsung_hits['상품요약서']) in report_text, "Samsung 상품요약서 hits not in report"
    assert str(meritz_hits['상품요약서']) in report_text, "Meritz 상품요약서 hits not in report"


def test_canonical_strategy_slots_present(samsung_profile, meritz_profile):
    """Canonical strategy 슬롯이 모두 존재"""
    required_slots = [
        'coverage_code',
        'canonical_name',
        'raw_name',
        'payout_amount',
        'waiting_period',
        'reduction_period',
        'excluded_cancer',
        'definition_excerpt',
        'payment_condition_excerpt',
        'doc_type_coverage',
        'evidence_refs'
    ]

    for profile, name in [(samsung_profile, 'samsung'), (meritz_profile, 'meritz')]:
        for slot in required_slots:
            assert slot in profile, f"{name}: Missing slot '{slot}'"


def test_slot_structure(samsung_profile, meritz_profile):
    """각 슬롯이 text, refs, status 구조를 가짐"""
    slot_keys = [
        'payout_amount',
        'waiting_period',
        'reduction_period',
        'excluded_cancer',
        'definition_excerpt',
        'payment_condition_excerpt'
    ]

    for profile, name in [(samsung_profile, 'samsung'), (meritz_profile, 'meritz')]:
        for slot_key in slot_keys:
            slot = profile[slot_key]
            assert 'text' in slot, f"{name}.{slot_key}: Missing 'text'"
            assert 'refs' in slot, f"{name}.{slot_key}: Missing 'refs'"
            assert 'status' in slot, f"{name}.{slot_key}: Missing 'status'"
            assert slot['status'] in ['found', 'unknown'], f"{name}.{slot_key}: Invalid status '{slot['status']}'"


def test_comparison_has_both_insurers(comparison):
    """Comparison에 양쪽 보험사 데이터 존재"""
    assert 'samsung' in comparison['doc_type_hits'], "Samsung not in comparison"
    assert 'meritz' in comparison['doc_type_hits'], "Meritz not in comparison"

    for slot_name in ['payout_amount', 'waiting_period', 'reduction_period', 'excluded_cancer', 'definition_excerpt', 'payment_condition_excerpt']:
        assert 'samsung' in comparison['slots'][slot_name], f"Samsung not in {slot_name} slot"
        assert 'meritz' in comparison['slots'][slot_name], f"Meritz not in {slot_name} slot"


def test_step5_doc_type_hits_match(comparison):
    """STEP 5에서 확정된 doc_type hit 수와 일치"""
    # STEP 5 결과:
    # Samsung: 약관 3, 사업방법서 3, 상품요약서 3
    # Meritz: 약관 3, 사업방법서 0, 상품요약서 3

    samsung_hits = comparison['doc_type_hits']['samsung']
    assert samsung_hits['약관'] == 3, "Samsung 약관 hits mismatch"
    assert samsung_hits['사업방법서'] == 3, "Samsung 사업방법서 hits mismatch"
    assert samsung_hits['상품요약서'] == 3, "Samsung 상품요약서 hits mismatch"

    meritz_hits = comparison['doc_type_hits']['meritz']
    assert meritz_hits['약관'] == 3, "Meritz 약관 hits mismatch"
    assert meritz_hits['사업방법서'] == 0, "Meritz 사업방법서 hits mismatch"
    assert meritz_hits['상품요약서'] == 3, "Meritz 상품요약서 hits mismatch"
