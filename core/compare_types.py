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
class Amount:
    """SSOT vNext: Amount field (MANDATORY in all coverage cards)"""
    status: str  # "CONFIRMED" | "UNCONFIRMED" | "NOT_AVAILABLE"
    value_text: Optional[str] = None  # e.g., "3,000만원" | "명시 없음" | null
    evidence_refs: List[str] = field(default_factory=list)  # e.g., ["PD:samsung:A4200_1"]

    def to_dict(self) -> dict:
        return {
            'status': self.status,
            'value_text': self.value_text,
            'evidence_refs': self.evidence_refs
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Amount':
        return cls(
            status=data['status'],
            value_text=data.get('value_text'),
            evidence_refs=data.get('evidence_refs', [])
        )


@dataclass
class CustomerView:
    """STEP NEXT-65R: Customer-facing benefit explanation"""
    benefit_description: str
    payment_type: Optional[str] = None  # "lump_sum" | "per_day" | "per_event" | null
    limit_conditions: List[str] = field(default_factory=list)
    exclusion_notes: List[str] = field(default_factory=list)
    evidence_refs: List[dict] = field(default_factory=list)
    extraction_notes: str = ""

    def to_dict(self) -> dict:
        return {
            'benefit_description': self.benefit_description,
            'payment_type': self.payment_type,
            'limit_conditions': self.limit_conditions,
            'exclusion_notes': self.exclusion_notes,
            'evidence_refs': self.evidence_refs,
            'extraction_notes': self.extraction_notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CustomerView':
        return cls(
            benefit_description=data.get('benefit_description', ''),
            payment_type=data.get('payment_type'),
            limit_conditions=data.get('limit_conditions', []),
            exclusion_notes=data.get('exclusion_notes', []),
            evidence_refs=data.get('evidence_refs', []),
            extraction_notes=data.get('extraction_notes', '')
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
    proposal_facts: Optional[dict] = None  # STEP NEXT-UI-FIX-04: Step1 가입설계서 금액/보험료/기간
    proposal_detail_facts: Optional[dict] = None  # STEP NEXT-68H: Step1 가입설계서 DETAIL 보장내용
    customer_view: Optional[CustomerView] = None  # STEP NEXT-65R: Customer-facing explanation
    amount: Optional['Amount'] = None  # SSOT vNext: Amount field (MANDATORY)

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSONL 출력용)"""
        result = {
            'insurer': self.insurer,
            'coverage_name_raw': self.coverage_name_raw,
            'coverage_code': self.coverage_code,
            'coverage_name_canonical': self.coverage_name_canonical,
            'mapping_status': self.mapping_status,
            'evidence_status': self.evidence_status,
            'evidences': [e.to_dict() for e in self.evidences],
            'hits_by_doc_type': self.hits_by_doc_type,
            'flags': self.flags,
            'proposal_facts': self.proposal_facts,
            'proposal_detail_facts': self.proposal_detail_facts  # STEP NEXT-68H
        }
        if self.customer_view:
            result['customer_view'] = self.customer_view.to_dict()
        if self.amount:
            result['amount'] = self.amount.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'CoverageCard':
        """딕셔너리에서 생성 (JSONL 읽기용)"""
        evidences = [Evidence.from_dict(e) for e in data.get('evidences', [])]
        customer_view = None
        if 'customer_view' in data and data['customer_view']:
            customer_view = CustomerView.from_dict(data['customer_view'])
        amount = None
        if 'amount' in data and data['amount']:
            amount = Amount.from_dict(data['amount'])
        return cls(
            insurer=data['insurer'],
            coverage_name_raw=data['coverage_name_raw'],
            coverage_code=data.get('coverage_code'),
            coverage_name_canonical=data.get('coverage_name_canonical'),
            mapping_status=data['mapping_status'],
            evidence_status=data['evidence_status'],
            evidences=evidences,
            hits_by_doc_type=data.get('hits_by_doc_type', {}),
            flags=data.get('flags', []),
            proposal_facts=data.get('proposal_facts'),
            proposal_detail_facts=data.get('proposal_detail_facts'),  # STEP NEXT-68H
            customer_view=customer_view,
            amount=amount
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


# ============================================================
# STEP NEXT-72: Slim Coverage Cards + Split Stores
# ============================================================

@dataclass
class ProposalDetailRecord:
    """STEP NEXT-72: 가입설계서 DETAIL 저장소 레코드"""
    proposal_detail_ref: str  # PD:{insurer}:{coverage_code}
    insurer: str
    coverage_code: str
    doc_type: str  # "가입설계서"
    page: int
    benefit_description_text: str
    hash: str  # sha256

    def to_dict(self) -> dict:
        return {
            'proposal_detail_ref': self.proposal_detail_ref,
            'insurer': self.insurer,
            'coverage_code': self.coverage_code,
            'doc_type': self.doc_type,
            'page': self.page,
            'benefit_description_text': self.benefit_description_text,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProposalDetailRecord':
        return cls(
            proposal_detail_ref=data['proposal_detail_ref'],
            insurer=data['insurer'],
            coverage_code=data['coverage_code'],
            doc_type=data['doc_type'],
            page=data['page'],
            benefit_description_text=data['benefit_description_text'],
            hash=data['hash']
        )


@dataclass
class EvidenceRecord:
    """STEP NEXT-72: 근거 자료 저장소 레코드"""
    evidence_ref: str  # EV:{insurer}:{coverage_code}:{nn}
    insurer: str
    coverage_code: str
    doc_type: str
    page: int
    snippet: str
    match_keyword: str
    hash: str  # sha256

    def to_dict(self) -> dict:
        return {
            'evidence_ref': self.evidence_ref,
            'insurer': self.insurer,
            'coverage_code': self.coverage_code,
            'doc_type': self.doc_type,
            'page': self.page,
            'snippet': self.snippet,
            'match_keyword': self.match_keyword,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EvidenceRecord':
        return cls(
            evidence_ref=data['evidence_ref'],
            insurer=data['insurer'],
            coverage_code=data['coverage_code'],
            doc_type=data['doc_type'],
            page=data['page'],
            snippet=data['snippet'],
            match_keyword=data['match_keyword'],
            hash=data['hash']
        )


@dataclass
class KPISummary:
    """STEP NEXT-74: KPI Summary (지급유형 / 한도)"""
    payment_type: str  # "LUMP_SUM" | "PER_DAY" | "PER_EVENT" | "REIMBURSEMENT" | "UNKNOWN"
    limit_summary: Optional[str] = None
    kpi_evidence_refs: List[str] = field(default_factory=list)
    extraction_notes: str = ""

    def to_dict(self) -> dict:
        return {
            'payment_type': self.payment_type,
            'limit_summary': self.limit_summary,
            'kpi_evidence_refs': self.kpi_evidence_refs,
            'extraction_notes': self.extraction_notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'KPISummary':
        return cls(
            payment_type=data['payment_type'],
            limit_summary=data.get('limit_summary'),
            kpi_evidence_refs=data.get('kpi_evidence_refs', []),
            extraction_notes=data.get('extraction_notes', '')
        )


@dataclass
class KPIConditionSummary:
    """STEP NEXT-76: KPI Condition Summary (면책/감액/대기기간/갱신)"""
    waiting_period: Optional[str] = None  # 예: "90일", "1년"
    reduction_condition: Optional[str] = None  # 예: "1년 50%"
    exclusion_condition: Optional[str] = None  # 예: "유사암 제외"
    renewal_condition: Optional[str] = None  # 예: "갱신형", "비갱신형"
    condition_evidence_refs: List[str] = field(default_factory=list)
    extraction_notes: str = ""

    def to_dict(self) -> dict:
        return {
            'waiting_period': self.waiting_period,
            'reduction_condition': self.reduction_condition,
            'exclusion_condition': self.exclusion_condition,
            'renewal_condition': self.renewal_condition,
            'condition_evidence_refs': self.condition_evidence_refs,
            'extraction_notes': self.extraction_notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'KPIConditionSummary':
        return cls(
            waiting_period=data.get('waiting_period'),
            reduction_condition=data.get('reduction_condition'),
            exclusion_condition=data.get('exclusion_condition'),
            renewal_condition=data.get('renewal_condition'),
            condition_evidence_refs=data.get('condition_evidence_refs', []),
            extraction_notes=data.get('extraction_notes', '')
        )


@dataclass
class CoverageCardSlim:
    """STEP NEXT-72: 경량 Coverage Card (UI/비교용, refs only)"""
    insurer: str
    coverage_code: Optional[str]
    coverage_name_canonical: Optional[str]
    coverage_name_raw: str
    mapping_status: str  # "matched" | "unmatched"
    product_name: str  # STEP NEXT-PRODUCT-1: product_name_display from products.yml
    variant_key: Optional[str] = None  # STEP NEXT-PRODUCT-1: variant_key (LOTTE_MALE/FEMALE, DB_AGE_U40/O40, or null)
    proposal_facts: Optional[dict] = None
    customer_view: Optional[CustomerView] = None
    refs: dict = field(default_factory=dict)  # {proposal_detail_ref, evidence_refs}
    kpi_summary: Optional[KPISummary] = None  # STEP NEXT-74
    kpi_condition: Optional[KPIConditionSummary] = None  # STEP NEXT-76

    def to_dict(self) -> dict:
        result = {
            'insurer': self.insurer,
            'coverage_code': self.coverage_code,
            'coverage_name_canonical': self.coverage_name_canonical,
            'coverage_name_raw': self.coverage_name_raw,
            'mapping_status': self.mapping_status,
            'product_name': self.product_name,
            'variant_key': self.variant_key,
            'proposal_facts': self.proposal_facts,
            'refs': self.refs
        }
        if self.customer_view:
            result['customer_view'] = self.customer_view.to_dict()
        if self.kpi_summary:
            result['kpi_summary'] = self.kpi_summary.to_dict()
        if self.kpi_condition:
            result['kpi_condition'] = self.kpi_condition.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'CoverageCardSlim':
        customer_view = None
        if 'customer_view' in data and data['customer_view']:
            customer_view = CustomerView.from_dict(data['customer_view'])

        kpi_summary = None
        if 'kpi_summary' in data and data['kpi_summary']:
            kpi_summary = KPISummary.from_dict(data['kpi_summary'])

        kpi_condition = None
        if 'kpi_condition' in data and data['kpi_condition']:
            kpi_condition = KPIConditionSummary.from_dict(data['kpi_condition'])

        return cls(
            insurer=data['insurer'],
            coverage_code=data.get('coverage_code'),
            coverage_name_canonical=data.get('coverage_name_canonical'),
            coverage_name_raw=data['coverage_name_raw'],
            mapping_status=data['mapping_status'],
            product_name=data['product_name'],
            variant_key=data.get('variant_key'),
            proposal_facts=data.get('proposal_facts'),
            customer_view=customer_view,
            refs=data.get('refs', {}),
            kpi_summary=kpi_summary,
            kpi_condition=kpi_condition
        )

    def sort_key(self) -> tuple:
        """정렬 키 (기존 CoverageCard와 동일 규칙)"""
        status_priority = 0 if self.mapping_status == "matched" else 1
        if self.mapping_status == "matched":
            sort_value = self.coverage_code or ""
        else:
            sort_value = self.coverage_name_raw
        return (status_priority, sort_value)
