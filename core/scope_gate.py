"""
Scope Gate: 담보 범위 검증

scope CSV에 없는 담보는 즉시 reject
모든 파이프라인 단계에서 scope 검증에 사용
"""

import csv
from pathlib import Path
from typing import Set, Optional


class ScopeGate:
    """담보 범위 검증 게이트"""

    def __init__(self, scope_csv_path: str):
        """
        Args:
            scope_csv_path: {INSURER}_scope.csv 파일 경로
        """
        self.scope_csv_path = Path(scope_csv_path)
        self.scope_coverages: Set[str] = self._load_scope()

    def _load_scope(self) -> Set[str]:
        """
        Scope CSV 파일에서 담보 목록 로드

        Returns:
            Set[str]: 허용된 담보명 집합 (coverage_name_raw)
        """
        if not self.scope_csv_path.exists():
            raise FileNotFoundError(f"Scope CSV not found: {self.scope_csv_path}")

        coverages = set()

        with open(self.scope_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # 필수 컬럼 검증
            if "coverage_name_raw" not in reader.fieldnames:
                raise ValueError(f"Missing required column 'coverage_name_raw' in {self.scope_csv_path}")

            for row in reader:
                coverage_name = row["coverage_name_raw"].strip()
                if coverage_name:
                    coverages.add(coverage_name)

        return coverages

    def is_in_scope(self, coverage_name: str) -> bool:
        """
        담보가 scope에 포함되는지 검증

        Args:
            coverage_name: 검증할 담보명

        Returns:
            bool: scope에 포함되면 True, 아니면 False
        """
        return coverage_name.strip() in self.scope_coverages

    def validate_or_reject(self, coverage_name: str, raise_error: bool = False) -> bool:
        """
        담보 검증, scope 외 담보 처리

        Args:
            coverage_name: 검증할 담보명
            raise_error: True면 scope 외 담보에 대해 예외 발생

        Returns:
            bool: scope에 포함되면 True, 아니면 False

        Raises:
            ValueError: raise_error=True이고 scope 외 담보인 경우
        """
        if self.is_in_scope(coverage_name):
            return True

        if raise_error:
            raise ValueError(
                f"Coverage '{coverage_name}' is NOT in scope. "
                f"Only {len(self.scope_coverages)} coverages from scope CSV are allowed."
            )

        return False

    def filter_in_scope(self, coverage_names: list) -> list:
        """
        담보 목록에서 scope에 포함된 것만 필터링

        Args:
            coverage_names: 담보명 리스트

        Returns:
            list: scope에 포함된 담보명만 포함
        """
        return [name for name in coverage_names if self.is_in_scope(name)]

    def get_scope_info(self) -> dict:
        """
        Scope 정보 반환

        Returns:
            dict: {"total_count": int, "coverages": Set[str]}
        """
        return {
            "total_count": len(self.scope_coverages),
            "coverages": self.scope_coverages,
            "source": str(self.scope_csv_path)
        }


# Utility functions

def resolve_scope_csv(insurer: str, scope_dir: Optional[Path] = None) -> Path:
    """
    STEP NEXT-18X: Canonical scope CSV resolver with fallback priority

    Priority (SSOT contract):
    1. {insurer}_scope_mapped.sanitized.csv (highest priority - sanitized SSOT)
    2. {insurer}_scope_mapped.csv (middle fallback - raw mapping)
    3. {insurer}_scope.csv (last fallback - original scope)

    Args:
        insurer: 보험사명 (예: "samsung")
        scope_dir: scope CSV 디렉토리 (기본값: data/scope)

    Returns:
        Path: 존재하는 최우선 scope CSV 경로

    Raises:
        FileNotFoundError: 모든 fallback이 실패한 경우
    """
    if scope_dir is None:
        scope_dir = Path(__file__).parent.parent / "data" / "scope"
    else:
        scope_dir = Path(scope_dir)

    # Priority order
    candidates = [
        scope_dir / f"{insurer}_scope_mapped.sanitized.csv",  # 1st priority
        scope_dir / f"{insurer}_scope_mapped.csv",            # 2nd priority
        scope_dir / f"{insurer}_scope.csv"                     # 3rd priority
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # All failed
    raise FileNotFoundError(
        f"No scope CSV found for insurer '{insurer}'. Tried:\n" +
        "\n".join(f"  - {c}" for c in candidates)
    )


def load_scope_gate(insurer: str, scope_dir: Optional[str] = None) -> ScopeGate:
    """
    보험사별 Scope Gate 로드 (STEP NEXT-18X: Use canonical resolver)

    Args:
        insurer: 보험사명 (예: "삼성생명")
        scope_dir: scope CSV 디렉토리 (기본값: data/scope)

    Returns:
        ScopeGate: 초기화된 scope gate 인스턴스
    """
    scope_dir_path = Path(scope_dir) if scope_dir else None
    scope_csv = resolve_scope_csv(insurer, scope_dir_path)
    return ScopeGate(str(scope_csv))


# Example usage
if __name__ == "__main__":
    # Example: scope gate 사용 예시
    # scope_gate = load_scope_gate("삼성생명")
    # print(scope_gate.get_scope_info())
    #
    # # 검증
    # if scope_gate.is_in_scope("일반암진단비"):
    #     print("✓ 일반암진단비: IN SCOPE")
    # else:
    #     print("✗ 일반암진단비: OUT OF SCOPE")
    pass
