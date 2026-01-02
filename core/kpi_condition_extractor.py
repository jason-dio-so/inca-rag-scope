"""
STEP NEXT-76: KPI Condition Extractor

Deterministic extraction of condition KPIs:
- waiting_period (대기기간)
- reduction_condition (감액)
- exclusion_condition (면책)
- renewal_condition (갱신)

Constitutional Rules:
- NO LLM / Vector / OCR
- Regex + string normalization only
- Evidence priority: proposal_detail > business > summary > policy
- First match only (no duplicate combination)
"""

import re
from typing import Optional, List, Tuple
from core.compare_types import KPIConditionSummary


class KPIConditionExtractor:
    """조건 KPI 추출기 (Deterministic only)"""

    # 대기기간 패턴
    WAITING_PERIOD_PATTERNS = [
        (r'대기기간\s*[:\s]*(\d+일)', 'waiting_period_days'),
        (r'대기\s*[:\s]*(\d+일)', 'waiting_period_days'),
        (r'(\d+일)\s*대기', 'waiting_period_days'),
        (r'보장개시일.*?(\d+일).*?이후', 'waiting_period_days'),
        (r'책임개시일.*?(\d+일).*?이후', 'waiting_period_days'),
        (r'(\d+일)(?:간|이)?.*?(?:지난|경과)', 'waiting_period_days'),
        (r'대기기간\s*[:\s]*(\d+개월)', 'waiting_period_months'),
        (r'대기\s*[:\s]*(\d+개월)', 'waiting_period_months'),
        (r'(\d+개월)\s*대기', 'waiting_period_months'),
        (r'대기기간\s*[:\s]*(\d+년)', 'waiting_period_years'),
        (r'(\d+년)\s*대기', 'waiting_period_years'),
        (r'책임개시', 'responsibility_start'),
    ]

    # 감액 패턴
    REDUCTION_PATTERNS = [
        (r'(\d+년)\s*[이내]*\s*(\d+)%', 'reduction_year_percent'),
        (r'(\d+년)\s*[미만]*\s*지급률\s*(\d+)%', 'reduction_year_percent'),
        (r'가입\s*후\s*(\d+년)\s*[이내]*\s*(\d+)%', 'reduction_year_percent'),
        (r'(\d+)%\s*감액.*?(\d+년)', 'reduction_percent_year'),
        (r'(\d+)%\s*지급.*?(\d+년)', 'reduction_percent_year'),
        (r'지급률.*?(\d+년).*?(\d+)%', 'reduction_year_percent'),
    ]

    # 면책 패턴
    EXCLUSION_PATTERNS = [
        (r'면책.*?(유사암|경계성|상피내암)', 'exclusion_cancer_type'),
        (r'책임\s*없음.*?(유사암|경계성|상피내암)', 'exclusion_cancer_type'),
        (r'보장\s*제외.*?(유사암|경계성|상피내암)', 'exclusion_cancer_type'),
        (r'(유사암|특정암)\s*제외', 'exclusion_cancer_type_simple'),
        (r'\(유사암\s*제외\)', 'exclusion_cancer_type_simple'),
        (r'면책기간\s*[:\s]*(\d+일)', 'exclusion_period'),
        (r'면책\s*[:\s]*(\d+일)', 'exclusion_period'),
    ]

    # 갱신 패턴
    RENEWAL_PATTERNS = [
        (r'갱신형', 'renewal_type'),
        (r'비갱신형', 'non_renewal_type'),
        (r'갱신\s*없음', 'non_renewal_type'),
        (r'(\d+년)\s*갱신', 'renewal_period'),
        (r'갱신\s*주기.*?(\d+년)', 'renewal_period'),
    ]

    @classmethod
    def extract(
        cls,
        proposal_detail_text: Optional[str],
        evidence_records: List[dict],
        proposal_detail_ref: Optional[str]
    ) -> KPIConditionSummary:
        """
        조건 KPI 추출

        Args:
            proposal_detail_text: 가입설계서 DETAIL 텍스트
            evidence_records: Evidence records [{doc_type, snippet, evidence_ref}, ...]
            proposal_detail_ref: Proposal detail reference

        Returns:
            KPIConditionSummary
        """
        # Evidence 우선순위 정렬: 사업방법서 > 상품요약서 > 약관
        DOC_TYPE_PRIORITY = {
            '사업방법서': 1,
            '상품요약서': 2,
            '약관': 3
        }
        sorted_evidences = sorted(
            evidence_records,
            key=lambda x: DOC_TYPE_PRIORITY.get(x.get('doc_type', '약관'), 99)
        )

        # 1. 대기기간 추출 (proposal_detail 우선)
        waiting_period, waiting_ref = cls._extract_waiting_period(
            proposal_detail_text, sorted_evidences, proposal_detail_ref
        )

        # 2. 감액 추출 (proposal_detail 우선)
        reduction_condition, reduction_ref = cls._extract_reduction(
            proposal_detail_text, sorted_evidences, proposal_detail_ref
        )

        # 3. 면책 추출 (proposal_detail 우선)
        exclusion_condition, exclusion_ref = cls._extract_exclusion(
            proposal_detail_text, sorted_evidences, proposal_detail_ref
        )

        # 4. 갱신 추출 (proposal_detail 우선)
        renewal_condition, renewal_ref = cls._extract_renewal(
            proposal_detail_text, sorted_evidences, proposal_detail_ref
        )

        # 모든 refs 수집 및 source 추적
        all_refs = []
        source_counts = {'proposal_detail': 0, 'evidence': 0}

        for ref in [waiting_ref, reduction_ref, exclusion_ref, renewal_ref]:
            if ref:
                if ref not in all_refs:
                    all_refs.append(ref)
                # Track source type
                if ref and ref.startswith('PD:'):
                    source_counts['proposal_detail'] += 1
                elif ref and ref.startswith('EV:'):
                    source_counts['evidence'] += 1

        # 추출 노트 (실제 source 기반)
        notes_parts = []
        if waiting_period or reduction_condition or exclusion_condition or renewal_condition:
            if source_counts['proposal_detail'] > 0:
                notes_parts.append(f"source=proposal_detail ({source_counts['proposal_detail']} conditions)")
            if source_counts['evidence'] > 0:
                notes_parts.append(f"source=evidence ({source_counts['evidence']} conditions)")
            if source_counts['proposal_detail'] == 0 and source_counts['evidence'] == 0:
                notes_parts.append("source=unknown")
        else:
            notes_parts.append("no conditions found")

        return KPIConditionSummary(
            waiting_period=waiting_period,
            reduction_condition=reduction_condition,
            exclusion_condition=exclusion_condition,
            renewal_condition=renewal_condition,
            condition_evidence_refs=all_refs,
            extraction_notes=", ".join(notes_parts)
        )

    @classmethod
    def _extract_waiting_period(
        cls,
        proposal_detail_text: Optional[str],
        evidence_records: List[dict],
        proposal_detail_ref: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        대기기간 추출

        Returns:
            (waiting_period, evidence_ref)
        """
        # 1. Proposal detail 우선
        if proposal_detail_text:
            result = cls._match_waiting_period(proposal_detail_text)
            if result:
                return result, proposal_detail_ref

        # 2. Evidence 순차 검색
        for ev in evidence_records:
            snippet = ev.get('snippet', '')
            result = cls._match_waiting_period(snippet)
            if result:
                return result, ev.get('evidence_ref')

        return None, None

    @classmethod
    def _match_waiting_period(cls, text: str) -> Optional[str]:
        """대기기간 패턴 매칭"""
        if not text:
            return None

        for pattern, pattern_type in cls.WAITING_PERIOD_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if pattern_type in ['waiting_period_days', 'waiting_period_months', 'waiting_period_years']:
                    return match.group(1)
                elif pattern_type == 'responsibility_start':
                    return '책임개시'
        return None

    @classmethod
    def _extract_reduction(
        cls,
        proposal_detail_text: Optional[str],
        evidence_records: List[dict],
        proposal_detail_ref: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        감액 추출

        Returns:
            (reduction_condition, evidence_ref)
        """
        # 1. Proposal detail 우선
        if proposal_detail_text:
            result = cls._match_reduction(proposal_detail_text)
            if result:
                return result, proposal_detail_ref

        # 2. Evidence 순차 검색
        for ev in evidence_records:
            snippet = ev.get('snippet', '')
            result = cls._match_reduction(snippet)
            if result:
                return result, ev.get('evidence_ref')

        return None, None

    @classmethod
    def _match_reduction(cls, text: str) -> Optional[str]:
        """감액 패턴 매칭"""
        if not text:
            return None

        for pattern, pattern_type in cls.REDUCTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'reduction_year_percent':
                    return f"{match.group(1)} {match.group(2)}%"
                elif pattern_type == 'reduction_percent_year':
                    return f"{match.group(2)} {match.group(1)}%"
        return None

    @classmethod
    def _extract_exclusion(
        cls,
        proposal_detail_text: Optional[str],
        evidence_records: List[dict],
        proposal_detail_ref: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        면책 추출

        Returns:
            (exclusion_condition, evidence_ref)
        """
        # 1. Proposal detail 우선
        if proposal_detail_text:
            result = cls._match_exclusion(proposal_detail_text)
            if result:
                return result, proposal_detail_ref

        # 2. Evidence 순차 검색
        for ev in evidence_records:
            snippet = ev.get('snippet', '')
            result = cls._match_exclusion(snippet)
            if result:
                return result, ev.get('evidence_ref')

        return None, None

    @classmethod
    def _match_exclusion(cls, text: str) -> Optional[str]:
        """면책 패턴 매칭"""
        if not text:
            return None

        for pattern, pattern_type in cls.EXCLUSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'exclusion_cancer_type':
                    return f"{match.group(1)} 제외"
                elif pattern_type == 'exclusion_cancer_type_simple':
                    return f"{match.group(1)} 제외"
                elif pattern_type == 'exclusion_period':
                    return match.group(1)
        return None

    @classmethod
    def _extract_renewal(
        cls,
        proposal_detail_text: Optional[str],
        evidence_records: List[dict],
        proposal_detail_ref: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        갱신 추출

        Returns:
            (renewal_condition, evidence_ref)
        """
        # 1. Proposal detail 우선
        if proposal_detail_text:
            result = cls._match_renewal(proposal_detail_text)
            if result:
                return result, proposal_detail_ref

        # 2. Evidence 순차 검색
        for ev in evidence_records:
            snippet = ev.get('snippet', '')
            result = cls._match_renewal(snippet)
            if result:
                return result, ev.get('evidence_ref')

        return None, None

    @classmethod
    def _match_renewal(cls, text: str) -> Optional[str]:
        """갱신 패턴 매칭"""
        if not text:
            return None

        for pattern, pattern_type in cls.RENEWAL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'renewal_type':
                    return '갱신형'
                elif pattern_type == 'non_renewal_type':
                    return '비갱신형'
                elif pattern_type == 'renewal_period':
                    return f"{match.group(1)} 갱신"
        return None
