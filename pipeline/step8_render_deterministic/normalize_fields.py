"""
STEP NEXT-COMPARE-FILTER-DETAIL-02: Field Normalization Module

Deterministic parsing and normalization of coverage fields:
- Limit (count/period/range/qualifier)
- PaymentType (lump_sum/per_day/per_event)
- Conditions (tags from evidence)

FORBIDDEN:
- NO LLM usage
- NO guessing/inference
- Pattern matching ONLY
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class EvidenceRef:
    """Evidence reference for traceability"""
    doc_type: str
    page: int
    file_path: Optional[str] = None
    snippet: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "page": self.page,
            "file_path": self.file_path,
            "snippet": self.snippet
        }


@dataclass
class NormalizedLimit:
    """Structured limit representation"""
    count: Optional[int] = None
    period: Optional[str] = None  # "lifetime" | "annual" | "monthly" | "per_event"
    range: Optional[Dict[str, Any]] = None  # {min, max, unit}
    qualifier: List[str] = field(default_factory=list)  # 최초, 보험기간중, 매년, etc.
    raw_text: str = ""
    evidence_refs: List[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "period": self.period,
            "range": self.range,
            "qualifier": self.qualifier,
            "raw_text": self.raw_text,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs]
        }

    def to_display_text(self) -> str:
        """Generate human-readable display text"""
        if not self.raw_text:
            return "명시 없음"

        parts = []
        if self.qualifier:
            parts.extend(self.qualifier)
        if self.count and self.period:
            period_map = {
                "lifetime": "평생",
                "annual": "연간",
                "monthly": "월",
                "per_event": "건당"
            }
            parts.append(f"{self.count}{period_map.get(self.period, '')}회")
        elif self.count:
            parts.append(f"{self.count}회")
        if self.range:
            unit = self.range.get("unit", "일")
            parts.append(f"{self.range['min']}~{self.range['max']}{unit}")

        return " ".join(parts) if parts else self.raw_text


@dataclass
class NormalizedPaymentType:
    """Structured payment type representation"""
    kind: str = "unknown"  # "lump_sum" | "per_day" | "per_event" | "unknown"
    raw_text: str = ""
    evidence_refs: List[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "raw_text": self.raw_text,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs]
        }

    def to_display_text(self) -> str:
        """Generate human-readable display text"""
        kind_map = {
            "lump_sum": "일시금",
            "per_day": "일당",
            "per_event": "건당",
            "unknown": self.raw_text or "명시 없음"
        }
        return kind_map.get(self.kind, self.raw_text or "명시 없음")


@dataclass
class NormalizedConditions:
    """Structured conditions representation"""
    tags: List[str] = field(default_factory=list)
    raw_text: str = ""
    evidence_refs: List[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tags": self.tags,
            "raw_text": self.raw_text,
            "evidence_refs": [ref.to_dict() for ref in self.evidence_refs]
        }

    def to_display_text(self) -> str:
        """Generate human-readable display text"""
        if self.tags:
            return ", ".join(self.tags)
        return self.raw_text or "명시 없음"


class LimitNormalizer:
    """Normalize limit/frequency fields"""

    # Count patterns (횟수 검출)
    COUNT_PATTERNS = [
        (r'최초\s*(\d+)\s*회', 'count_with_qualifier'),  # 최초 1회
        (r'연간?\s*(\d+)\s*회', 'count_annual'),         # 연 1회, 연간 1회
        (r'평생\s*(\d+)\s*회', 'count_lifetime'),       # 평생 3회
        (r'보험기간\s*중\s*(\d+)\s*회', 'count_lifetime'),  # 보험기간중 1회
        (r'(\d+)\s*회\s*한', 'count_simple'),           # 1회 한
        (r'(\d+)\s*회', 'count_simple'),                # 3회
    ]

    # Range patterns (기간 범위 검출)
    RANGE_PATTERNS = [
        (r'(\d+)\s*~\s*(\d+)\s*일', 'day'),
        (r'(\d+)\s*~\s*(\d+)\s*개월', 'month'),
        (r'(\d+)\s*~\s*(\d+)\s*년', 'year'),
        (r'(\d+)\s*일', 'day_single'),
    ]

    # Qualifier patterns (조건어 검출)
    QUALIFIER_PATTERNS = [
        r'최초',
        r'매년',
        r'보험기간\s*중',
        r'\d+년\s*경과\s*전',
        r'\d+년\s*경과\s*후',
        r'계약일로부터',
    ]

    @classmethod
    def normalize(cls, evidences: List[Dict[str, Any]]) -> NormalizedLimit:
        """
        Normalize limit field from evidences

        Args:
            evidences: List of evidence dicts with snippet/doc_type/page

        Returns:
            NormalizedLimit with parsed structure
        """
        if not evidences:
            return NormalizedLimit(raw_text="명시 없음")

        # Try to extract from snippets
        for ev in evidences:
            snippet = ev.get("snippet", "")
            if not snippet:
                continue

            # Create evidence ref
            ev_ref = EvidenceRef(
                doc_type=ev.get("doc_type", ""),
                page=ev.get("page", 0),
                file_path=ev.get("file_path"),
                snippet=snippet[:200]
            )

            # Try count patterns
            count = None
            period = None
            qualifiers = []

            for pattern, pattern_type in cls.COUNT_PATTERNS:
                match = re.search(pattern, snippet)
                if match:
                    count = int(match.group(1))
                    if pattern_type == 'count_annual':
                        period = "annual"
                    elif pattern_type == 'count_lifetime':
                        period = "lifetime"
                    elif pattern_type == 'count_with_qualifier':
                        qualifiers.append("최초")
                    break

            # Try range patterns
            range_data = None
            for pattern, unit_type in cls.RANGE_PATTERNS:
                match = re.search(pattern, snippet)
                if match:
                    if unit_type.endswith('_single'):
                        unit_base = unit_type.replace('_single', '')
                        val = int(match.group(1))
                        range_data = {"min": val, "max": val, "unit": unit_base}
                    else:
                        range_data = {
                            "min": int(match.group(1)),
                            "max": int(match.group(2)),
                            "unit": unit_type
                        }
                    break

            # Extract qualifiers
            for q_pattern in cls.QUALIFIER_PATTERNS:
                if re.search(q_pattern, snippet):
                    qualifiers.append(re.search(q_pattern, snippet).group(0))

            # If we found something, return it
            if count or range_data or qualifiers:
                return NormalizedLimit(
                    count=count,
                    period=period,
                    range=range_data,
                    qualifier=qualifiers,
                    raw_text=snippet[:100],
                    evidence_refs=[ev_ref]
                )

        # Fallback: return raw text from first evidence
        first_ev = evidences[0]
        return NormalizedLimit(
            raw_text=first_ev.get("snippet", "")[:100],
            evidence_refs=[EvidenceRef(
                doc_type=first_ev.get("doc_type", ""),
                page=first_ev.get("page", 0),
                snippet=first_ev.get("snippet", "")[:200]
            )]
        )


class PaymentTypeNormalizer:
    """Normalize payment type fields"""

    PAYMENT_TYPE_PATTERNS = [
        (r'일시금.*지급', 'lump_sum'),
        (r'보험가입금액.*지급', 'lump_sum'),
        (r'정액.*지급', 'lump_sum'),
        (r'진단.*일시금', 'lump_sum'),
        (r'입원.*일당', 'per_day'),
        (r'입원.*일수당', 'per_day'),
        (r'일당.*지급', 'per_day'),
        (r'수술.*건당', 'per_event'),
        (r'수술.*회당', 'per_event'),
        (r'건당.*지급', 'per_event'),
    ]

    @classmethod
    def normalize(cls, evidences: List[Dict[str, Any]]) -> NormalizedPaymentType:
        """
        Normalize payment type from evidences

        Args:
            evidences: List of evidence dicts

        Returns:
            NormalizedPaymentType
        """
        if not evidences:
            return NormalizedPaymentType(kind="unknown", raw_text="명시 없음")

        for ev in evidences:
            snippet = ev.get("snippet", "")
            if not snippet:
                continue

            ev_ref = EvidenceRef(
                doc_type=ev.get("doc_type", ""),
                page=ev.get("page", 0),
                snippet=snippet[:200]
            )

            for pattern, kind in cls.PAYMENT_TYPE_PATTERNS:
                if re.search(pattern, snippet):
                    return NormalizedPaymentType(
                        kind=kind,
                        raw_text=snippet[:100],
                        evidence_refs=[ev_ref]
                    )

        # Fallback: unknown with raw text
        first_ev = evidences[0]
        return NormalizedPaymentType(
            kind="unknown",
            raw_text=first_ev.get("snippet", "")[:100],
            evidence_refs=[EvidenceRef(
                doc_type=first_ev.get("doc_type", ""),
                page=first_ev.get("page", 0),
                snippet=first_ev.get("snippet", "")[:200]
            )]
        )


class ConditionsNormalizer:
    """Normalize conditions/restrictions fields"""

    # Forbidden patterns (목차/절 번호 등 제외)
    FORBIDDEN_PATTERNS = [
        r'^\d+[-\.]\d+$',  # "4-1", "3.2"
        r'^제\d+조',       # "제5조"
        r'^약관\s*\d+',    # "약관 10"
        r'^\d+$',          # Standalone numbers
        r'^[A-Z]\d+',      # "A4200"
    ]

    # Condition keyword tags
    CONDITION_TAGS = {
        '면책': '면책',
        '감액': '감액',
        '대기기간': '대기기간',
        '갱신': '갱신형',
        '90일': '대기기간 90일',
        '1년 경과': '1년 경과 조건',
        '50%': '50% 지급',
        '진단확정': '진단확정 기준',
    }

    @classmethod
    def normalize(cls, evidences: List[Dict[str, Any]]) -> NormalizedConditions:
        """
        Normalize conditions from evidences

        Args:
            evidences: List of evidence dicts

        Returns:
            NormalizedConditions with tags
        """
        if not evidences:
            return NormalizedConditions(raw_text="명시 없음")

        tags = []
        raw_texts = []
        evidence_refs = []

        for ev in evidences:
            snippet = ev.get("snippet", "")
            if not snippet:
                continue

            # Check forbidden patterns
            is_forbidden = any(re.match(pat, snippet.strip()) for pat in cls.FORBIDDEN_PATTERNS)
            if is_forbidden:
                continue

            ev_ref = EvidenceRef(
                doc_type=ev.get("doc_type", ""),
                page=ev.get("page", 0),
                snippet=snippet[:200]
            )

            # Extract tags
            for keyword, tag in cls.CONDITION_TAGS.items():
                if keyword in snippet:
                    if tag not in tags:
                        tags.append(tag)

            # Collect raw text
            if tags:  # Only include if we found condition keywords
                raw_texts.append(snippet[:100])
                evidence_refs.append(ev_ref)

        if tags:
            return NormalizedConditions(
                tags=tags,
                raw_text=" / ".join(raw_texts[:2]),  # Max 2 snippets
                evidence_refs=evidence_refs[:2]
            )

        # Fallback: no valid conditions found
        return NormalizedConditions(
            raw_text="명시 없음",
            evidence_refs=[]
        )


def normalize_field(field_name: str, evidences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize field based on field name

    Args:
        field_name: "보장한도" | "지급유형" | "조건" | etc.
        evidences: List of evidence dicts

    Returns:
        Normalized structure (NormalizedLimit/PaymentType/Conditions)
    """
    if field_name in ["보장한도", "입원한도", "limit"]:
        return LimitNormalizer.normalize(evidences).to_dict()
    elif field_name in ["지급유형", "payment_type"]:
        return PaymentTypeNormalizer.normalize(evidences).to_dict()
    elif field_name in ["조건", "conditions"]:
        return ConditionsNormalizer.normalize(evidences).to_dict()
    else:
        # Unknown field: return raw text from first evidence
        if evidences:
            first_ev = evidences[0]
            return {
                "raw_text": first_ev.get("snippet", "")[:100],
                "evidence_refs": [EvidenceRef(
                    doc_type=first_ev.get("doc_type", ""),
                    page=first_ev.get("page", 0),
                    snippet=first_ev.get("snippet", "")[:200]
                ).to_dict()]
            }
        return {"raw_text": "명시 없음", "evidence_refs": []}


def main():
    """Test normalization"""
    import json

    # Test limit normalization
    test_evidences = [
        {
            "doc_type": "약관",
            "page": 10,
            "snippet": "최초 1회 한 진단비를 보험가입금액으로 지급합니다"
        }
    ]

    limit = LimitNormalizer.normalize(test_evidences)
    print("Limit:", json.dumps(limit.to_dict(), ensure_ascii=False, indent=2))
    print("Display:", limit.to_display_text())

    # Test payment type normalization
    payment = PaymentTypeNormalizer.normalize(test_evidences)
    print("\nPayment Type:", json.dumps(payment.to_dict(), ensure_ascii=False, indent=2))
    print("Display:", payment.to_display_text())

    # Test conditions normalization
    test_evidences_cond = [
        {
            "doc_type": "약관",
            "page": 5,
            "snippet": "90일의 대기기간이 적용되며, 1년 경과 후 100% 지급"
        }
    ]
    conditions = ConditionsNormalizer.normalize(test_evidences_cond)
    print("\nConditions:", json.dumps(conditions.to_dict(), ensure_ascii=False, indent=2))
    print("Display:", conditions.to_display_text())


if __name__ == "__main__":
    main()
