"""
STEP NEXT-76-A: Extended Coverage Slot Schema
==============================================

Extends existing 6 slots with 4 new slots for customer questions 1-5, 8.

ABSOLUTE RULES:
- ❌ NO LLM calls
- ❌ NO inference/calculation
- ✅ Evidence-based ONLY (from 약관/요약서/사업방법서)
- ✅ Filled by Step3 Evidence Resolver
- ✅ Same gate rules as existing slots

Existing Slots (unchanged):
- start_date
- exclusions
- payout_limit
- reduction
- entry_age
- waiting_period

NEW Extended Slots:
"""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class UnderwritingConditionSlot:
    """
    Slot: underwriting_condition

    Purpose: 유병자/특정 질환자 인수 조건
    Customer Question: "고혈압/당뇨 있어도 가입 가능한가?"

    Evidence Required:
    - Keywords: "유병자", "고혈압", "당뇨", "인수 가능", "가입 가능",
                "건강고지", "특별조건", "할증"
    - Doc Priority: 사업방법서 > 가입설계서 > 약관

    Value Format (deterministic):
    - allowed_conditions: [string]  # e.g., ["고혈압", "당뇨병"]
    - surcharge_required: bool | null  # True if 할증 mentioned
    - max_age_limit: int | null  # 최대 인수 나이
    """
    allowed_conditions: List[str]  # Extracted condition names
    surcharge_required: Optional[bool] = None
    max_age_limit: Optional[int] = None

    # Evidence traceability (required)
    evidences: List[Dict] = None  # type: ignore


@dataclass
class MandatoryDependencySlot:
    """
    Slot: mandatory_dependency

    Purpose: 특약 필수 가입 조건
    Customer Question: "이 특약만 단독 가입 가능한가?"

    Evidence Required:
    - Keywords: "주계약 필수", "필수 가입", "최소 가입금액",
                "동시 가입", "의무 가입"
    - Doc Priority: 약관 > 가입설계서

    Value Format:
    - required_coverages: [coverage_code]  # Must be anchored codes
    - min_amount: {coverage_code: amount} | null
    - standalone_allowed: bool  # False if dependencies exist
    """
    required_coverages: List[str]  # Coverage codes (anchored)
    min_amount: Optional[Dict[str, int]] = None  # {code: amount}
    standalone_allowed: bool = True

    evidences: List[Dict] = None  # type: ignore


@dataclass
class PayoutFrequencySlot:
    """
    Slot: payout_frequency

    Purpose: 지급 빈도/반복 조건
    Customer Question: "여러 번 재발해도 계속 받을 수 있나?"

    Evidence Required:
    - Keywords: "1회한", "연간", "평생", "재발", "재진단",
                "반복지급", "회수 제한"
    - Doc Priority: 약관 > 상품요약서

    Value Format:
    - type: "per_event" | "per_year" | "per_lifetime"
    - max_count: int | null  # null = unlimited
    - reset_period_days: int | null  # Days between payouts
    """
    type: str  # per_event, per_year, per_lifetime
    max_count: Optional[int] = None  # null = unlimited
    reset_period_days: Optional[int] = None  # Minimum gap between payouts

    evidences: List[Dict] = None  # type: ignore


@dataclass
class IndustryAggregateLimitSlot:
    """
    Slot: industry_aggregate_limit

    Purpose: 업계 누적 한도 (타사 가입 합산)
    Customer Question: "다른 보험사 가입도 영향 주나?"

    Evidence Required:
    - Keywords: "업계 누적", "타사 가입", "합산", "총 한도",
                "다른 보험사", "전체 보험"
    - Doc Priority: 사업방법서 > 약관

    Value Format:
    - applies: bool  # True if limit exists
    - max_amount: int | null  # Total across all insurers
    - affected_coverage_types: [string]  # Which coverages count
    """
    applies: bool  # True if industry limit exists
    max_amount: Optional[int] = None  # Total limit
    affected_coverage_types: List[str] = None  # type: ignore  # e.g., ["암진단비", "입원비"]

    evidences: List[Dict] = None  # type: ignore


# Slot registry for Step3/Step4 integration
EXTENDED_SLOT_KEYS = [
    "underwriting_condition",
    "mandatory_dependency",
    "payout_frequency",
    "industry_aggregate_limit"
]

# All slots (existing + extended)
ALL_SLOT_KEYS = [
    # Existing (Step1-Step5 active)
    "start_date",
    "exclusions",
    "payout_limit",
    "reduction",
    "entry_age",
    "waiting_period",
    # Extended (STEP NEXT-76)
    "underwriting_condition",
    "mandatory_dependency",
    "payout_frequency",
    "industry_aggregate_limit"
]

# EXCLUDED (intentionally not supported)
EXCLUDED_SLOTS = [
    "discount",  # 할인 (마케팅)
    "refund_rate",  # 환급률 (저축)
    "family_discount",  # 가족결합 (마케팅)
    "marketing_phrases"  # 홍보 문구
]
