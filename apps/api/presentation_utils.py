#!/usr/bin/env python3
"""
Presentation Utilities for UX Layer
STEP NEXT-17: Amount Display Unification & Type C Structure Communication

CRITICAL RULES:
1. This is PRESENTATION-ONLY logic (NO data modification)
2. NO amount inference or calculation
3. Type C insurers show "보험가입금액 기준" instead of amounts
4. Type A/B use unified format: "3,000만원" (with comma)
5. ZERO changes to Step7/11/12/13 extraction/storage logic

PURPOSE:
- Prevent customer confusion about Type C product structure
- Unify amount display format across all insurers
- Clearly distinguish between "confirmed amount" and "structural reference"

SINGLE SOURCE OF TRUTH:
- Type C insurer classification: config/amount_lineage_type_map.json
"""

import json
import os
from typing import Optional, Set
from apps.api.dto import AmountDTO, AmountStatus

# Type C insurers loaded from config (SINGLE SOURCE)
_TYPE_C_CACHE: Optional[Set[str]] = None


def _load_type_c_insurers() -> Set[str]:
    """
    Load Type C insurers from config file (SINGLE SOURCE)

    Returns:
        Set of insurer codes/names that are Type C
    """
    global _TYPE_C_CACHE

    if _TYPE_C_CACHE is not None:
        return _TYPE_C_CACHE

    # Load from config file
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "amount_lineage_type_map.json"
    )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            type_map = json.load(f)

        # Extract Type C insurers (codes)
        type_c_codes = {k for k, v in type_map.items() if v == "C"}

        # Add Korean display names (mapping)
        display_names = {
            "hanwha": "한화손해보험",
            "hyundai": "현대해상",
            "kb": "KB손해보험"
        }

        type_c_names = {display_names.get(code, code) for code in type_c_codes}

        # Combine codes + display names
        _TYPE_C_CACHE = type_c_codes | type_c_names

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        # Fallback to hardcoded (should not happen in production)
        _TYPE_C_CACHE = {"hanwha", "hyundai", "kb", "한화손해보험", "현대해상", "KB손해보험"}

    return _TYPE_C_CACHE


def format_amount_for_display(
    amount_dto: AmountDTO,
    insurer: str
) -> str:
    """
    Format amount for UX display

    STEP NEXT-17 Rules:
    1. Type C + UNCONFIRMED → "보험가입금액 기준" (NO amount shown)
    2. CONFIRMED (any type) → Unified format "3,000만원"
    3. UNCONFIRMED (Type A/B) → "금액 미표기"
    4. NOT_AVAILABLE → "해당 담보 없음"

    Args:
        amount_dto: Amount DTO from Step11 (READ-ONLY)
        insurer: Insurer name or code

    Returns:
        Display string (presentation-only)

    FORBIDDEN:
    - Inferring amounts for Type C
    - Showing "보험가입금액" numeric value
    - Modifying amount_dto
    """
    status = amount_dto.status

    # Type C insurer detection (case-insensitive, from config)
    type_c_insurers = _load_type_c_insurers()
    is_type_c = any(
        tc_name.lower() in insurer.lower()
        for tc_name in type_c_insurers
    )

    # Status-based presentation
    if status == "CONFIRMED":
        # CONFIRMED: Show unified amount format
        if amount_dto.value_text:
            return _unify_amount_format(amount_dto.value_text)
        else:
            # Contract violation, but handle gracefully
            return "확인 불가"

    elif status == "UNCONFIRMED":
        if is_type_c:
            # Type C: Show structural explanation (NO amount)
            return "보험가입금액 기준"
        else:
            # Type A/B: Show standard UNCONFIRMED text
            return "금액 미표기"

    elif status == "NOT_AVAILABLE":
        return "해당 담보 없음"

    else:
        # Unknown status
        return "확인 불가"


def _unify_amount_format(value_text: str) -> str:
    """
    Unify amount format to "3,000만원" style

    Transformations:
    - "3천만원" → "3,000만원"
    - "6백만원" → "600만원"
    - "3000만원" → "3,000만원"
    - "1억원" → "1억원" (no change)

    Args:
        value_text: Original value text from amount_fact

    Returns:
        Unified format string
    """
    if not value_text:
        return value_text

    result = value_text

    # Replace "천만원" with ",000만원"
    # "3천만원" → "3,000만원"
    # "5천만원" → "5,000만원"
    if "천만원" in result:
        result = result.replace("천만원", ",000만원")

    # Replace "백만원" with "00만원"
    # "6백만원" → "600만원"
    # "8백만원" → "800만원"
    if "백만원" in result:
        result = result.replace("백만원", "00만원")

    # Handle numeric-only formats (add commas if missing)
    # "3000만원" → "3,000만원"
    # "5000만원" → "5,000만원"
    if "만원" in result and "," not in result:
        # Extract numeric part
        parts = result.split("만원")
        if len(parts) == 2 and parts[0].isdigit():
            num = int(parts[0])
            if num >= 1000:
                # Add comma for thousands
                formatted_num = f"{num:,}"
                result = f"{formatted_num}만원{parts[1]}"

    return result


def get_type_c_explanation_note() -> str:
    """
    Get common note explaining Type C structure

    STEP NEXT-17: This note should appear ONCE per comparison

    Returns:
        Note text explaining product structure difference
    """
    return (
        "※ 일부 보험사는 담보별 금액을 별도로 표시하지 않고 "
        "상품 공통 '보험가입금액'을 기준으로 보장을 제공합니다."
    )


def is_type_c_insurer(insurer: str) -> bool:
    """
    Check if insurer is Type C (from config/amount_lineage_type_map.json)

    Args:
        insurer: Insurer name or code

    Returns:
        True if Type C insurer
    """
    type_c_insurers = _load_type_c_insurers()
    return any(
        tc_name.lower() in insurer.lower()
        for tc_name in type_c_insurers
    )


def should_show_type_c_note(insurers: list[str]) -> bool:
    """
    Check if Type C explanation note should be shown

    Args:
        insurers: List of insurer names/codes

    Returns:
        True if any Type C insurer is present
    """
    return any(is_type_c_insurer(ins) for ins in insurers)
