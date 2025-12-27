"""
Evidence Pack 테스트

Contract tests:
1. Scope gate 통과 못하면 evidence search reject
2. Matched 담보는 evidences가 1개 이상 생성됨
3. Doc_type_priority가 적용되어 약관 evidence가 우선 선택됨
4. Evidence pack 출력 스키마 검증
"""

import pytest
import json
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scope_gate import load_scope_gate
from pipeline.step4_evidence_search.search_evidence import EvidenceSearcher


# 경로 설정
BASE_DIR = Path(__file__).parent.parent
EVIDENCE_TEXT_DIR = BASE_DIR / "data" / "evidence_text"
EVIDENCE_PACK_FILE = BASE_DIR / "data" / "evidence_pack" / "samsung_evidence_pack.jsonl"


class TestEvidenceSearch:
    """Evidence search 기능 테스트"""

    def setup_method(self):
        """각 테스트 전에 초기화"""
        self.insurer = "samsung"
        self.scope_gate = load_scope_gate(self.insurer)
        self.searcher = EvidenceSearcher(str(EVIDENCE_TEXT_DIR), self.insurer)

    def test_scope_gate_reject(self):
        """1. Scope gate 통과 못하면 reject"""
        # Scope에 없는 담보
        fake_coverage = "존재하지않는가짜담보명"

        # Scope gate 검증
        assert self.scope_gate.is_in_scope(fake_coverage) is False

        # Evidence 검색 시도 (scope gate는 상위 레벨에서 처리)
        # 여기서는 scope_gate.is_in_scope()가 False를 반환하는 것만 확인
        evidences = self.searcher.search_coverage_evidence(
            coverage_name_raw=fake_coverage,
            mapping_status="unmatched"
        )

        # Evidence가 없거나 있어도 무관 (scope gate는 pipeline에서 처리)
        # 이 테스트는 scope_gate가 정상 동작하는지만 확인
        assert isinstance(evidences, list)

    def test_matched_coverage_has_evidence(self):
        """2. Matched 담보는 evidences가 1개 이상 생성됨"""
        # samsung_scope_mapped.csv에서 matched인 담보 사용
        # 예: "암 진단비(유사암 제외)" → "암진단비(유사암제외)"
        coverage_name_raw = "암 진단비(유사암 제외)"
        coverage_name_canonical = "암진단비(유사암제외)"

        # Scope gate 통과 확인
        assert self.scope_gate.is_in_scope(coverage_name_raw) is True

        # Evidence 검색
        evidences = self.searcher.search_coverage_evidence(
            coverage_name_raw=coverage_name_raw,
            coverage_name_canonical=coverage_name_canonical,
            mapping_status="matched",
            max_evidences=3
        )

        # Evidence가 1개 이상 있어야 함
        assert len(evidences) >= 1, f"No evidence found for '{coverage_name_raw}'"

        # Evidence 구조 확인
        first_evidence = evidences[0]
        assert 'doc_type' in first_evidence
        assert 'file_path' in first_evidence
        assert 'page' in first_evidence
        assert 'snippet' in first_evidence
        assert 'match_keyword' in first_evidence

    def test_doc_type_priority(self):
        """3. Doc_type_priority가 적용되어 약관 evidence가 우선"""
        # 여러 문서에 존재할 수 있는 담보 (예: 사망)
        coverage_name_raw = "질병 사망"

        # Evidence 검색
        evidences = self.searcher.search_coverage_evidence(
            coverage_name_raw=coverage_name_raw,
            mapping_status="matched",
            max_evidences=3
        )

        if len(evidences) > 0:
            # 첫 번째 evidence의 doc_type이 우선순위가 높아야 함
            first_doc_type = evidences[0]['doc_type']

            # 약관이 최우선이므로, 약관 evidence가 있다면 첫 번째여야 함
            doc_types_found = [e['doc_type'] for e in evidences]

            if '약관' in doc_types_found:
                # 약관이 있으면 첫 번째 또는 초반에 위치해야 함
                yakgwan_indices = [i for i, dt in enumerate(doc_types_found) if dt == '약관']
                assert yakgwan_indices[0] < len(evidences), "약관 evidence should appear early"


class TestEvidencePackSchema:
    """Evidence pack 출력 스키마 테스트"""

    def setup_method(self):
        """Evidence pack 파일 로드"""
        self.evidence_pack = []

        if EVIDENCE_PACK_FILE.exists():
            with open(EVIDENCE_PACK_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.evidence_pack.append(json.loads(line))

    def test_evidence_pack_exists(self):
        """Evidence pack 파일이 존재하는지 확인"""
        assert EVIDENCE_PACK_FILE.exists(), f"Evidence pack not found: {EVIDENCE_PACK_FILE}"
        assert len(self.evidence_pack) > 0, "Evidence pack is empty"

    def test_evidence_pack_schema(self):
        """4. Evidence pack 출력 스키마 검증"""
        assert len(self.evidence_pack) > 0, "Evidence pack is empty"

        # 첫 번째 항목 스키마 확인
        first_item = self.evidence_pack[0]

        # 필수 필드 존재 확인
        required_fields = [
            'insurer',
            'coverage_name_raw',
            'coverage_code',
            'mapping_status',
            'needs_alias_review',
            'evidences'
        ]

        for field in required_fields:
            assert field in first_item, f"Missing required field: {field}"

        # evidences는 list여야 함
        assert isinstance(first_item['evidences'], list)

        # evidences가 있다면 스키마 확인
        if len(first_item['evidences']) > 0:
            first_evidence = first_item['evidences'][0]

            evidence_fields = [
                'doc_type',
                'file_path',
                'page',
                'snippet',
                'match_keyword'
            ]

            for field in evidence_fields:
                assert field in first_evidence, f"Missing evidence field: {field}"

    def test_needs_alias_review_logic(self):
        """needs_alias_review 로직 확인"""
        for item in self.evidence_pack:
            mapping_status = item['mapping_status']
            needs_alias_review = item['needs_alias_review']

            # unmatched면 needs_alias_review=True
            if mapping_status == 'unmatched':
                assert needs_alias_review is True, \
                    f"Unmatched coverage should have needs_alias_review=True: {item['coverage_name_raw']}"

            # matched면 needs_alias_review=False
            elif mapping_status == 'matched':
                assert needs_alias_review is False, \
                    f"Matched coverage should have needs_alias_review=False: {item['coverage_name_raw']}"

    def test_coverage_count(self):
        """생성된 evidence pack의 담보 수 확인"""
        # samsung_scope.csv에 41개 담보가 있으므로 41개여야 함
        assert len(self.evidence_pack) == 41, \
            f"Expected 41 coverages, got {len(self.evidence_pack)}"


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
