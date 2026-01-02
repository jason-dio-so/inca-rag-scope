"""
STEP NEXT-74: KPI Extractor (지급유형 / 한도)

Constitutional Rules:
- NO LLM
- NO Vector/OCR/Embedding
- Deterministic rule-based only
- All KPI must be traceable to evidence_refs

KPI Definitions:
1. payment_type: LUMP_SUM | PER_DAY | PER_EVENT | REIMBURSEMENT | UNKNOWN
2. limit_summary: Single-line normalized string
"""

import re
from enum import Enum
from typing import Optional


class PaymentType(str, Enum):
    """지급유형 (Canonical)"""
    LUMP_SUM = "LUMP_SUM"           # 진단 시 일시금
    PER_DAY = "PER_DAY"             # 입원/통원 일당
    PER_EVENT = "PER_EVENT"         # 수술/처치 1회당
    REIMBURSEMENT = "REIMBURSEMENT" # 실손/비례보상
    UNKNOWN = "UNKNOWN"             # 판단 불가


def extract_payment_type(text: str) -> PaymentType:
    """
    Extract payment type from benefit description text

    Args:
        text: Benefit description (from proposal_detail or evidence)

    Returns:
        PaymentType enum value

    Rules (priority order):
    1. LUMP_SUM: 진단확정, 진단시, 발생시, 지급
    2. PER_DAY: 입원 1일당, 통원 1일당, 일당
    3. PER_EVENT: 수술 1회당, 수술시, 처치 1회당
    4. REIMBURSEMENT: 실손, 비례보상, 보상하는, 실제
    5. UNKNOWN: None of above
    """
    if not text or not isinstance(text, str):
        return PaymentType.UNKNOWN

    text_normalized = text.replace(" ", "").replace("\n", "")

    # Priority 1: PER_DAY (most specific)
    per_day_patterns = [
        r'입원.*?1?일당',
        r'통원.*?1?일당',
        r'1일당',
        r'일당.*?입원',
        r'일당.*?통원',
    ]
    for pattern in per_day_patterns:
        if re.search(pattern, text_normalized):
            return PaymentType.PER_DAY

    # Priority 2: PER_EVENT
    per_event_patterns = [
        r'수술.*?1?회당',
        r'수술.*?시',
        r'처치.*?1?회당',
        r'1회당',
        r'회당.*?수술',
    ]
    for pattern in per_event_patterns:
        if re.search(pattern, text_normalized):
            return PaymentType.PER_EVENT

    # Priority 3: REIMBURSEMENT
    reimbursement_patterns = [
        r'실손',
        r'비례보상',
        r'보상하는',
        r'실제.*?부담',
        r'실제.*?지출',
    ]
    for pattern in reimbursement_patterns:
        if re.search(pattern, text_normalized):
            return PaymentType.REIMBURSEMENT

    # Priority 4: LUMP_SUM (broadest, catch-all for diagnosis)
    lump_sum_patterns = [
        r'진단확정',
        r'진단.*?시',
        r'발생.*?시',
        r'지급',
        r'가입금액',
    ]
    for pattern in lump_sum_patterns:
        if re.search(pattern, text_normalized):
            return PaymentType.LUMP_SUM

    return PaymentType.UNKNOWN


def extract_limit_summary(text: str) -> Optional[str]:
    """
    Extract limit summary from benefit description text

    Args:
        text: Benefit description (from proposal_detail or evidence)

    Returns:
        Normalized limit summary string or None

    Examples:
        "최초 1회한" -> "보험기간 중 1회"
        "연 1회" -> "연 1회"
        "1일당 5만원 (최대 30일)" -> "1일당 5만원 (최대 30일)"

    Patterns (priority order):
    1. 최초 N회 -> "보험기간 중 N회"
    2. 연 N회 -> "연 N회"
    3. 보험기간 중 N회 -> "보험기간 중 N회"
    4. 1일당 X원 (최대 N일) -> "1일당 X원 (최대 N일)"
    5. 1회당 X원 한도 -> "1회당 X원 한도"
    """
    if not text or not isinstance(text, str):
        return None

    text_normalized = text.replace(" ", "").replace("\n", "")

    # Pattern 1: 최초 N회한
    match = re.search(r'최초(\d+)회', text_normalized)
    if match:
        count = match.group(1)
        return f"보험기간 중 {count}회"

    # Pattern 2: 연 N회
    match = re.search(r'연(\d+)회', text_normalized)
    if match:
        count = match.group(1)
        return f"연 {count}회"

    # Pattern 3: 보험기간 중 N회
    match = re.search(r'보험기간.*?중.*?(\d+)회', text_normalized)
    if match:
        count = match.group(1)
        return f"보험기간 중 {count}회"

    # Pattern 4: 1일당 X만원 (최대 N일)
    match = re.search(r'1일당.*?(\d+(?:,\d+)*)만?원.*?최대.*?(\d+)일', text_normalized)
    if match:
        amount = match.group(1)
        days = match.group(2)
        return f"1일당 {amount}만원 (최대 {days}일)"

    # Pattern 4b: 1일당 X만원 (without 최대)
    match = re.search(r'1일당.*?(\d+(?:,\d+)*)만?원', text_normalized)
    if match:
        amount = match.group(1)
        return f"1일당 {amount}만원"

    # Pattern 5: 1회당 X만원 한도
    match = re.search(r'1회당.*?(\d+(?:,\d+)*)만?원.*?한도', text_normalized)
    if match:
        amount = match.group(1)
        return f"1회당 {amount}만원 한도"

    # Pattern 5b: 1회당 X만원 (without 한도)
    match = re.search(r'1회당.*?(\d+(?:,\d+)*)만?원', text_normalized)
    if match:
        amount = match.group(1)
        return f"1회당 {amount}만원"

    # Pattern 6: Generic X회 한
    match = re.search(r'(\d+)회한', text_normalized)
    if match:
        count = match.group(1)
        return f"보험기간 중 {count}회"

    return None


def extract_kpi_from_text(text: str) -> dict:
    """
    Extract all KPI from a single text source

    Args:
        text: Benefit description text

    Returns:
        {
            "payment_type": PaymentType,
            "limit_summary": str | None
        }
    """
    return {
        "payment_type": extract_payment_type(text),
        "limit_summary": extract_limit_summary(text)
    }
