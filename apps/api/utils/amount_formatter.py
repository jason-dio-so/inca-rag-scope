"""
STEP NEXT-139D: Unified Amount Formatter (Korean Format ONLY)

Constitutional Rules:
- ALL amounts MUST use Korean abbreviated format (3천만원, 2만원)
- NO numeric+만원 format (3000만원) - FORBIDDEN
- NO comma format (3,000만원) - FORBIDDEN
- Single source of truth for amount formatting
- Used by EX2/EX3 composers (NO individual formatting)
"""

import re


def format_amount_korean(amount: str) -> str:
    """
    Convert ANY amount format to Korean abbreviated format.

    Rules:
    - "3000만원" → "3천만원"
    - "3,000만원" → "3천만원"
    - "30000000원" → "3천만원"
    - "2만원" → "2만원" (already correct)
    - "명시 없음" → "명시 없음" (passthrough)

    Forbidden outputs:
    - "3000만원" (numeric+만원)
    - "3,000만원" (comma format)
    - "30,000,000원" (pure numeric)

    Returns:
    - Korean abbreviated format ONLY
    - Passthrough for special values ("명시 없음", "표현 없음")
    """
    if not amount or amount in ("명시 없음", "표현 없음", "-"):
        return amount

    # Strip whitespace and parenthetical numeric amounts
    # e.g., "3천만원 (30,000,000원)" → "3천만원"
    amount = re.sub(r'\s*\([0-9,]+원\)\s*$', '', amount).strip()

    # Remove all commas first
    amount_no_comma = amount.replace(',', '')

    # Check if already in Korean format (contains 천, 만, 억)
    if any(unit in amount_no_comma for unit in ['천', '만', '억']):
        # Already Korean - but might have numeric prefix like "3000만원"
        # Convert "3000만원" → "3천만원"
        amount_no_comma = _convert_numeric_prefix_to_korean(amount_no_comma)
        return amount_no_comma

    # Pure numeric amount (e.g., "30000000원")
    # Convert to Korean abbreviated format
    if amount_no_comma.endswith('원'):
        try:
            # Extract numeric part
            numeric_str = amount_no_comma[:-1]  # Remove '원'
            value = int(numeric_str)
            return _number_to_korean_abbreviated(value)
        except ValueError:
            # Not a valid number, return as-is
            return amount

    # Unknown format, return as-is
    return amount


def _convert_numeric_prefix_to_korean(amount: str) -> str:
    """
    Convert numeric prefix to Korean in amounts like "3000만원" → "3천만원"

    Patterns:
    - "3000만원" → "3천만원"
    - "5000만원" → "5천만원"
    - "1000만원" → "1천만원"
    - "500만원" → "500만원" (< 1000, keep as-is)
    """
    # Pattern: N000만원 → N천만원 (where N is 1-9)
    amount = re.sub(r'(\d)000만원', r'\1천만원', amount)

    # Pattern: N00만원 → N백만원 (where N is 1-9)
    amount = re.sub(r'(\d)00만원', r'\1백만원', amount)

    return amount


def _number_to_korean_abbreviated(value: int) -> str:
    """
    Convert pure numeric value to Korean abbreviated format.

    Examples:
    - 30000000 → "3천만원"
    - 20000 → "2만원"
    - 5000000 → "5백만원"
    - 100000000 → "1억원"

    Rules:
    - Use 억, 만, 천, 백 units
    - Omit 일 (1) prefix except for 억
    """
    if value == 0:
        return "0원"

    parts = []

    # 억 (hundred million)
    eok = value // 100000000
    if eok > 0:
        if eok == 1:
            parts.append("1억")
        else:
            parts.append(f"{eok}억")
        value %= 100000000

    # 만 (ten thousand)
    man = value // 10000
    if man > 0:
        # Check for 천 (thousand) within 만
        cheon = man // 1000
        if cheon > 0:
            parts.append(f"{cheon}천")
            man %= 1000

        # Check for 백 (hundred) within 만
        baek = man // 100
        if baek > 0:
            parts.append(f"{baek}백")
            man %= 100

        # Remaining 만
        if man > 0:
            parts.append(f"{man}")

        if parts and not parts[-1].endswith('만'):
            parts.append("만")
        elif not parts:
            parts.append(f"{value // 10000}만")

        value %= 10000

    # If there's remaining value < 10000, it's typically omitted in abbreviated format
    # But if it's the only value, show it
    if value > 0 and not parts:
        if value >= 1000:
            parts.append(f"{value // 1000}천")
            value %= 1000
        if value >= 100:
            parts.append(f"{value // 100}백")
            value %= 100
        if value > 0:
            parts.append(f"{value}")

    result = "".join(parts) + "원"
    return result


# Forbidden patterns (for validation/testing)
FORBIDDEN_PATTERNS = [
    r'\d{4,}만원',  # e.g., "3000만원", "10000만원"
    r'\d+,\d+',     # e.g., "3,000만원", "30,000,000원"
]


def validate_korean_format(amount: str) -> bool:
    """
    Validate that amount is in correct Korean format.

    Returns True if valid (Korean abbreviated format).
    Returns False if contains forbidden patterns.
    """
    if not amount or amount in ("명시 없음", "표현 없음", "-"):
        return True

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, amount):
            return False

    return True
