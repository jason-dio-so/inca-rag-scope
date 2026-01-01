"""
Amount Parser — Deterministic rules-based extraction

CONSTITUTIONAL RULES:
- NO LLM / NO inference
- Extract ONLY what's explicitly stated
- NO interpretation / NO summarization
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class AmountLimit:
    """지급 한도 구조"""
    count: Optional[int] = None  # 횟수 (1회, 3회, ...)
    period: Optional[str] = None  # 기간 (lifetime, per_year, per_month)
    max_amount: Optional[int] = None  # 금액 한도


@dataclass
class AmountStructure:
    """지급 금액 구조 (deterministic)"""
    payment_type: Optional[str] = None  # lump_sum, per_event, per_day, percentage
    amount: Optional[int] = None  # 금액 (원 단위)
    percentage: Optional[float] = None  # 비율 (%)
    unit: str = "KRW"
    limit: Optional[AmountLimit] = None
    conditions: List[str] = field(default_factory=list)  # 조건 (갱신형, 감액, ...)
    raw_text: str = ""  # 원문

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화"""
        result = {
            "payment_type": self.payment_type,
            "amount": self.amount,
            "percentage": self.percentage,
            "unit": self.unit,
            "conditions": self.conditions,
            "raw_text": self.raw_text
        }
        if self.limit:
            result["limit"] = asdict(self.limit)
        return result


class AmountParser:
    """
    결정론적 Amount Parser

    GATE-7-3 Enforcement: 동일 입력 → 동일 출력
    """

    # 금액 패턴 (예: 3,000만원, 500만원, 200만)
    AMOUNT_PATTERNS = [
        r'(\d{1,3}(?:,\d{3})*)\s*만\s*원',  # 3,000만원
        r'(\d{1,3}(?:,\d{3})*)\s*만',      # 3,000만
        r'(\d+)\s*원',                      # 5000원
        r'보험가입금액의\s*(\d+)\s*%',     # 보험가입금액의 50%
        r'가입금액의\s*(\d+)\s*%',         # 가입금액의 100%
    ]

    # 지급 유형 패턴
    PAYMENT_TYPE_PATTERNS = {
        'lump_sum': [r'최초\s*1\s*회', r'1\s*회\s*한', r'진단\s*시'],
        'per_event': [r'매\s*회', r'수술\s*1\s*회당', r'1\s*회당'],
        'per_day': [r'입원\s*일당', r'1\s*일당', r'일\s*당'],
    }

    # 조건 패턴
    CONDITION_PATTERNS = {
        '갱신형': r'갱신형',
        '최초1회': r'최초\s*1\s*회',
        '연간한도': r'연간\s*(\d+)\s*회\s*한',
        '감액': r'(\d+)\s*%\s*감액',
        '면책': r'(\d+)\s*일\s*면책',
    }

    def parse(self, evidence_snippets: List[Dict[str, Any]]) -> AmountStructure:
        """
        Evidence snippet에서 금액 구조 추출

        Args:
            evidence_snippets: [{"doc_type": "약관", "snippet": "...", "page": 42}, ...]

        Returns:
            AmountStructure (deterministic)
        """
        # 모든 snippet을 결합
        combined_text = "\n".join([e.get("snippet", "") for e in evidence_snippets])

        structure = AmountStructure(raw_text=combined_text[:500])  # 원문 일부 보존

        # 1. 금액 추출
        structure.amount = self._extract_amount(combined_text)
        structure.percentage = self._extract_percentage(combined_text)

        # 2. 지급 유형 추출
        structure.payment_type = self._extract_payment_type(combined_text)

        # 3. 한도 추출
        structure.limit = self._extract_limit(combined_text)

        # 4. 조건 추출
        structure.conditions = self._extract_conditions(combined_text)

        return structure

    def _extract_amount(self, text: str) -> Optional[int]:
        """금액 추출 (만원 → 원 단위 변환)"""
        # 패턴 우선순위: 구체적 → 일반적
        for pattern in self.AMOUNT_PATTERNS[:3]:  # 금액 패턴만
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = int(amount_str)

                # 만원 단위 → 원 단위
                if '만' in pattern:
                    amount *= 10000

                return amount

        return None

    def _extract_percentage(self, text: str) -> Optional[float]:
        """비율 추출 (보험가입금액의 X%)"""
        match = re.search(r'보험가입금액의\s*(\d+)\s*%|가입금액의\s*(\d+)\s*%', text)
        if match:
            pct_str = match.group(1) or match.group(2)
            return float(pct_str)
        return None

    def _extract_payment_type(self, text: str) -> Optional[str]:
        """지급 유형 추출"""
        for ptype, patterns in self.PAYMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return ptype

        # 기본값: per_event (명시 안 되어 있으면)
        return None

    def _extract_limit(self, text: str) -> Optional[AmountLimit]:
        """한도 추출"""
        limit = AmountLimit()

        # 횟수 한도 (예: 연간 3회 한도, 최초 1회 한)
        count_match = re.search(r'최초\s*(\d+)\s*회|연간\s*(\d+)\s*회|(\d+)\s*회\s*한', text)
        if count_match:
            count_str = count_match.group(1) or count_match.group(2) or count_match.group(3)
            limit.count = int(count_str)

        # 기간 (최초 → lifetime, 연간 → per_year)
        if re.search(r'최초', text):
            limit.period = "lifetime"
        elif re.search(r'연간', text):
            limit.period = "per_year"

        return limit if (limit.count or limit.period) else None

    def _extract_conditions(self, text: str) -> List[str]:
        """조건 추출 (갱신형, 감액, 면책, ...)"""
        conditions = []

        for condition_name, pattern in self.CONDITION_PATTERNS.items():
            if re.search(pattern, text):
                # 숫자 추출해서 함께 저장
                match = re.search(pattern, text)
                if match and match.groups():
                    conditions.append(f"{condition_name}({match.group(1)})")
                else:
                    conditions.append(condition_name)

        return sorted(set(conditions))  # 중복 제거 + 정렬 (determinism)


def parse_coverage_amount(coverage_card: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coverage card에서 amount 구조 추출

    Args:
        coverage_card: {
            "insurer": "samsung",
            "coverage_code": "A4103",
            "evidences": [{"doc_type": "약관", "snippet": "...", "page": 42}, ...]
        }

    Returns:
        {
            "coverage_code": "A4103",
            "insurer": "samsung",
            "amount_structure": {...},
            "evidence_refs": [{"doc_type": "약관", "page": 42}, ...]
        }
    """
    parser = AmountParser()

    evidences = coverage_card.get("evidences", [])
    amount_structure = parser.parse(evidences)

    # Evidence references 추출
    evidence_refs = [
        {
            "doc_type": e.get("doc_type"),
            "page": e.get("page"),
            "file_path": e.get("file_path")
        }
        for e in evidences
    ]

    return {
        "coverage_code": coverage_card.get("coverage_code"),
        "coverage_name_canonical": coverage_card.get("coverage_name_canonical"),
        "insurer": coverage_card.get("insurer"),
        "amount_structure": amount_structure.to_dict(),
        "evidence_refs": evidence_refs,
        "mapping_status": coverage_card.get("mapping_status"),
    }
