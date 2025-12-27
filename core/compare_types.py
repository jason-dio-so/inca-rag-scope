"""
Coverage Card 데이터 타입 정의

Scope-only 비교를 위한 공용 스키마
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Evidence:
    """Evidence 항목"""
    doc_type: str
    file_path: str
    page: int
    snippet: str
    match_keyword: str

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'doc_type': self.doc_type,
            'file_path': self.file_path,
            'page': self.page,
            'snippet': self.snippet,
            'match_keyword': self.match_keyword
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Evidence':
        """딕셔너리에서 생성"""
        return cls(
            doc_type=data['doc_type'],
            file_path=data['file_path'],
            page=data['page'],
            snippet=data['snippet'],
            match_keyword=data['match_keyword']
        )


@dataclass
class CoverageCard:
    """Coverage Card - 담보별 종합 정보"""
    insurer: str
    coverage_name_raw: str
    coverage_code: Optional[str]
    coverage_name_canonical: Optional[str]
    mapping_status: str  # "matched" | "unmatched"
    evidence_status: str  # "found" | "not_found"
    evidences: List[Evidence] = field(default_factory=list)
    hits_by_doc_type: dict = field(default_factory=dict)  # NEW
    flags: List[str] = field(default_factory=list)  # NEW

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSONL 출력용)"""
        return {
            'insurer': self.insurer,
            'coverage_name_raw': self.coverage_name_raw,
            'coverage_code': self.coverage_code,
            'coverage_name_canonical': self.coverage_name_canonical,
            'mapping_status': self.mapping_status,
            'evidence_status': self.evidence_status,
            'evidences': [e.to_dict() for e in self.evidences],
            'hits_by_doc_type': self.hits_by_doc_type,
            'flags': self.flags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CoverageCard':
        """딕셔너리에서 생성 (JSONL 읽기용)"""
        evidences = [Evidence.from_dict(e) for e in data.get('evidences', [])]
        return cls(
            insurer=data['insurer'],
            coverage_name_raw=data['coverage_name_raw'],
            coverage_code=data.get('coverage_code'),
            coverage_name_canonical=data.get('coverage_name_canonical'),
            mapping_status=data['mapping_status'],
            evidence_status=data['evidence_status'],
            evidences=evidences,
            hits_by_doc_type=data.get('hits_by_doc_type', {}),
            flags=data.get('flags', [])
        )

    def get_top_evidence_ref(self) -> str:
        """
        상위 evidence 참조 (리포트용)

        Returns:
            str: "doc_type p.{page}" 형식 또는 "-"
        """
        if self.evidences:
            top = self.evidences[0]
            return f"{top.doc_type} p.{top.page}"
        return "-"

    def get_evidence_source_summary(self) -> str:
        """
        Evidence source 요약 (리포트용)

        Returns:
            str: "약관 p.X | 사업방법서 p.Y | 상품요약서 p.Z" 형식
        """
        parts = []
        for doc_type in ['약관', '사업방법서', '상품요약서']:
            # 해당 타입의 첫 evidence 찾기
            evidence = next((e for e in self.evidences if e.doc_type == doc_type), None)
            if evidence:
                parts.append(f"{doc_type} p.{evidence.page}")

        return " | ".join(parts) if parts else "-"

    def sort_key(self) -> tuple:
        """
        정렬 키 생성

        정렬 규칙:
        1. matched 먼저, unmatched 나중
        2. matched 내에서는 coverage_code 오름차순
        3. unmatched 내에서는 coverage_name_raw 오름차순

        Returns:
            tuple: (mapping_status_priority, sort_value)
        """
        # matched=0, unmatched=1
        status_priority = 0 if self.mapping_status == "matched" else 1

        # 정렬 값: matched면 coverage_code, unmatched면 raw name
        if self.mapping_status == "matched":
            sort_value = self.coverage_code or ""
        else:
            sort_value = self.coverage_name_raw

        return (status_priority, sort_value)


@dataclass
class CompareStats:
    """비교 통계"""
    total_coverages: int
    matched: int
    unmatched: int
    evidence_found: int
    evidence_not_found: int

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'total_coverages': self.total_coverages,
            'matched': self.matched,
            'unmatched': self.unmatched,
            'evidence_found': self.evidence_found,
            'evidence_not_found': self.evidence_not_found
        }
