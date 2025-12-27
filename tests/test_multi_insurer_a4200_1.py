"""
REBOOT STEP 7: Multi-Insurer A4200_1 Tests (MANDATORY)

전체 보험사 A4200_1 비교 검증
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def base_dir():
    """프로젝트 루트 디렉토리"""
    return Path(__file__).parent.parent


@pytest.fixture
def all_comparison(base_dir):
    """All insurers A4200_1 comparison"""
    compare_file = base_dir / 'data' / 'single' / 'a4200_1_all_compare.json'
    with open(compare_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def report_text(base_dir):
    """Multi-insurer report markdown text"""
    report_file = base_dir / 'reports' / 'a4200_1_all_insurers.md'
    with open(report_file, 'r', encoding='utf-8') as f:
        return f.read()


def test_comparison_file_exists(base_dir):
    """a4200_1_all_compare.json 파일 존재"""
    compare_file = base_dir / 'data' / 'single' / 'a4200_1_all_compare.json'
    assert compare_file.exists(), f"Comparison file not found: {compare_file}"


def test_report_file_exists(base_dir):
    """a4200_1_all_insurers.md 파일 존재"""
    report_file = base_dir / 'reports' / 'a4200_1_all_insurers.md'
    assert report_file.exists(), f"Report file not found: {report_file}"


def test_no_forbidden_words_in_report(report_text):
    """리포트에 금지어 없음 (추천, 종합의견, 유리, 불리, 해석)"""
    forbidden_words = ['추천', '종합의견', '유리', '불리', '해석']

    for word in forbidden_words:
        assert word not in report_text, f"Forbidden word '{word}' found in report"


def test_all_profiles_have_a4200_1(base_dir):
    """생성된 insurer들의 coverage_code가 모두 A4200_1"""
    single_dir = base_dir / 'data' / 'single'

    for profile_file in single_dir.glob('*_A4200_1_profile.json'):
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)
            assert profile.get('coverage_code') == 'A4200_1', \
                f"Invalid coverage_code in {profile_file.name}: {profile.get('coverage_code')}"


def test_comparison_has_insurers(all_comparison):
    """Comparison에 insurers 리스트 존재"""
    assert 'insurers' in all_comparison, "Missing 'insurers' field"
    assert isinstance(all_comparison['insurers'], list), "insurers should be a list"
    assert len(all_comparison['insurers']) > 0, "No insurers in comparison"


def test_comparison_has_doc_type_coverage(all_comparison):
    """Comparison에 doc_type_coverage 존재"""
    assert 'doc_type_coverage' in all_comparison, "Missing 'doc_type_coverage' field"

    for insurer in all_comparison['insurers']:
        assert insurer in all_comparison['doc_type_coverage'], \
            f"Missing doc_type_coverage for {insurer}"


def test_comparison_has_slot_status(all_comparison):
    """Comparison에 slot_status 존재"""
    assert 'slot_status' in all_comparison, "Missing 'slot_status' field"

    required_slots = ['payout_amount', 'waiting_period', 'reduction_period', 'excluded_cancer', 'definition_excerpt', 'payment_condition_excerpt']

    for slot in required_slots:
        assert slot in all_comparison['slot_status'], f"Missing slot '{slot}'"

        for insurer in all_comparison['insurers']:
            assert insurer in all_comparison['slot_status'][slot], \
                f"Missing {insurer} in slot '{slot}'"
            assert 'status' in all_comparison['slot_status'][slot][insurer], \
                f"Missing 'status' for {insurer} in slot '{slot}'"


def test_report_has_all_insurers(report_text, all_comparison):
    """리포트에 모든 insurer가 포함됨"""
    for insurer in all_comparison['insurers']:
        assert insurer.upper() in report_text, f"Insurer {insurer.upper()} not in report"


def test_report_has_doc_type_table(report_text):
    """리포트에 Document Type Coverage 테이블 존재"""
    assert "Document Type Coverage" in report_text, "Missing Document Type Coverage section"
    assert "약관" in report_text, "Missing 약관 column"
    assert "사업방법서" in report_text, "Missing 사업방법서 column"
    assert "상품요약서" in report_text, "Missing 상품요약서 column"


def test_report_has_slot_sections(report_text):
    """리포트에 모든 슬롯 섹션 존재"""
    slot_names = ['Payout Amount', 'Waiting Period', 'Reduction Period', 'Excluded Cancer', 'Definition Excerpt', 'Payment Condition']

    for slot_name in slot_names:
        assert slot_name in report_text, f"Missing slot section '{slot_name}'"
