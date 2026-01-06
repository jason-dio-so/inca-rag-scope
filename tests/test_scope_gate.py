"""
Scope Gate 테스트

scope CSV에 있는 담보 → allowed=True
scope CSV에 없는 담보 → allowed=False
"""

import pytest
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scope_gate import ScopeGate, load_scope_gate, resolve_scope_csv


# 테스트용 보험사
INSURER = "samsung"


class TestScopeGate:
    """ScopeGate 기능 테스트"""

    def setup_method(self):
        """각 테스트 전에 ScopeGate 초기화"""
        scope_csv = resolve_scope_csv(INSURER)
        self.scope_gate = ScopeGate(str(scope_csv))

    def test_scope_gate_initialization(self):
        """ScopeGate 초기화 테스트"""
        assert self.scope_gate is not None
        assert len(self.scope_gate.scope_coverages) > 0

    def test_coverage_in_scope_exact_match(self):
        """Scope에 있는 담보 - exact match"""
        # samsung_scope.csv에 실제로 있는 담보명 사용
        coverage_in_scope = "암 진단비(유사암 제외)"

        assert self.scope_gate.is_in_scope(coverage_in_scope) is True
        assert self.scope_gate.validate_or_reject(coverage_in_scope) is True

    def test_coverage_in_scope_multiple(self):
        """Scope에 있는 여러 담보들"""
        coverages_in_scope = [
            "암 진단비(유사암 제외)",
            "뇌출혈 진단비",
            "상해 입원일당(1일이상)",
            "질병 입원일당(1일이상)",
            "유사암 진단비(갑상선암)(1년50%)"
        ]

        for coverage in coverages_in_scope:
            assert self.scope_gate.is_in_scope(coverage) is True, \
                f"Coverage '{coverage}' should be in scope"

    def test_coverage_not_in_scope(self):
        """Scope에 없는 담보 - False 반환"""
        coverage_out_of_scope = "존재하지않는담보"

        assert self.scope_gate.is_in_scope(coverage_out_of_scope) is False
        assert self.scope_gate.validate_or_reject(coverage_out_of_scope) is False

    def test_coverage_not_in_scope_multiple(self):
        """Scope에 없는 여러 담보들"""
        coverages_out_of_scope = [
            "존재하지않는담보",
            "가짜담보명",
            "테스트용담보",
            "Fake Coverage Name"
        ]

        for coverage in coverages_out_of_scope:
            assert self.scope_gate.is_in_scope(coverage) is False, \
                f"Coverage '{coverage}' should NOT be in scope"

    def test_validate_or_reject_with_error(self):
        """Scope 외 담보 - raise_error=True일 때 예외 발생"""
        coverage_out_of_scope = "존재하지않는담보"

        with pytest.raises(ValueError) as exc_info:
            self.scope_gate.validate_or_reject(coverage_out_of_scope, raise_error=True)

        assert "NOT in scope" in str(exc_info.value)

    def test_filter_in_scope(self):
        """Scope 필터링 - in scope만 반환"""
        mixed_coverages = [
            "암 진단비(유사암 제외)",  # in scope
            "존재하지않는담보",  # out of scope
            "뇌출혈 진단비",  # in scope
            "가짜담보",  # out of scope
            "상해 입원일당(1일이상)"  # in scope
        ]

        filtered = self.scope_gate.filter_in_scope(mixed_coverages)

        assert len(filtered) == 3
        assert "암 진단비(유사암 제외)" in filtered
        assert "뇌출혈 진단비" in filtered
        assert "상해 입원일당(1일이상)" in filtered
        assert "존재하지않는담보" not in filtered
        assert "가짜담보" not in filtered

    def test_get_scope_info(self):
        """Scope 정보 조회"""
        info = self.scope_gate.get_scope_info()

        assert "total_count" in info
        assert "coverages" in info
        assert "source" in info
        assert info["total_count"] > 0
        assert isinstance(info["coverages"], set)
        # Source should contain samsung and be a CSV file (don't hardcode exact filename)
        assert "samsung" in info["source"]
        assert info["source"].endswith(".csv")

    def test_whitespace_handling(self):
        """공백 처리 테스트"""
        # 앞뒤 공백이 있어도 정상 동작
        coverage_with_spaces = "  암 진단비(유사암 제외)  "

        assert self.scope_gate.is_in_scope(coverage_with_spaces) is True


class TestLoadScopeGate:
    """load_scope_gate 유틸리티 함수 테스트"""

    def test_load_scope_gate_default_dir(self):
        """기본 디렉토리에서 로드"""
        scope_gate = load_scope_gate("samsung")

        assert scope_gate is not None
        assert len(scope_gate.scope_coverages) > 0

    def test_load_scope_gate_custom_dir(self):
        """커스텀 디렉토리에서 로드"""
        # Use resolve_scope_csv to get the correct directory
        scope_csv = resolve_scope_csv("samsung")
        scope_dir = scope_csv.parent
        scope_gate = load_scope_gate("samsung", str(scope_dir))

        assert scope_gate is not None
        assert len(scope_gate.scope_coverages) > 0


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
