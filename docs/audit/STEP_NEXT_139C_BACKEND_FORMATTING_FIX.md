# STEP NEXT-139C: EX3 Backend Formatting Fix — 2026-01-04

## Problem Statement (Evidence-Based)

**DevTools Network Payload Analysis**:
```json
{
  "cells": [
    {"text": "지급유형"},
    {"text": "LUMP_SUM", "meta": {...}},  // ❌ Raw enum value
    {"text": "LUMP_SUM", "meta": {...}}   // ❌ Raw enum value
  ]
}

{
  "cells": [
    {"text": "핵심 보장 내용"},
    {"text": "3,000만원 (30,000,000원)", "meta": {...}},  // ❌ Numeric + parenthetical
    {"text": "3천만원", "meta": {...}}                    // ✅ Korean only
  ]
}
```

**Root Cause**: Backend composer (`ex3_compare_composer.py`) was sending unformatted strings directly to cells:
1. **Payment type**: Raw enum (`"LUMP_SUM"`) instead of Korean label (`"정액 지급"`)
2. **Amounts**: Inconsistent formatting (some with numeric parentheticals, some without)

## Solution (Backend Fix)

Applied formatting **AT THE SOURCE** (where ViewModel cells are created), NOT in frontend normalization.

### Why Backend (Not Frontend)?

**Tried First**: Frontend normalization (`apps/web/lib/normalize/table.ts`)
- **Problem**: By the time frontend receives data, backend already sent raw strings
- **Result**: Frontend can't access raw values to determine formatting logic

**Correct Approach**: Backend composer
- Format values BEFORE creating cell objects
- Send pre-formatted strings to frontend
- Frontend just displays what backend provides (no transformation needed)

## Modified Files

### `apps/api/response_composers/ex3_compare_composer.py`

**Changes**:

#### 1. Payment Type Formatting (Lines 434-450)
```python
# STEP NEXT-139C: Format payment_type for display (NO raw enum values)
def format_payment_type(payment_type: str) -> str:
    """Maps raw enum values to Korean labels"""
    label_map = {
        "LUMP_SUM": "정액 지급",
        "일당형": "일당 지급",
        "건별형": "건별 지급",
        "실손형": "실손 지급",
        "UNKNOWN": "표현 없음"
    }
    return label_map.get(payment_type, payment_type)

payment1_display = format_payment_type(payment1)
payment2_display = format_payment_type(payment2)
```

**Before**: `{"text": "LUMP_SUM"}`
**After**: `{"text": "정액 지급"}`

#### 2. Amount Korean-Only Formatting (Lines 392-405)
```python
# STEP NEXT-139C: Strip numeric parenthetical (Korean-only display)
import re
korean_only = re.sub(r'\s*\([0-9,]+원\)\s*$', '', amount).strip()

if payment_type == "일당형":
    if not korean_only.startswith("일당"):
        return f"일당 {korean_only}"
    return korean_only

return korean_only  # 정액형: just Korean amount
```

**Before**: `{"text": "3천만원 (30,000,000원)"}`
**After**: `{"text": "3천만원"}`

**Before**: `{"text": "2만원"}` (일당형)
**After**: `{"text": "일당 2만원"}`

#### 3. Limit Display Formatting (Lines 539-541)
```python
# STEP NEXT-139C: Strip numeric parenthetical from amount
if amount and amount != "명시 없음":
    amount = re.sub(r'\s*\([0-9,]+원\)\s*$', '', amount).strip()
```

Applied same Korean-only formatting to limit section amounts.

## Core Rules (ABSOLUTE)

1. ✅ **NO raw enum values in cells**: `"LUMP_SUM"` → `"정액 지급"`
2. ✅ **Korean-only amounts**: `"3천만원 (30,000,000원)"` → `"3천만원"`
3. ✅ **일당형 prefix**: `"2만원"` → `"일당 2만원"` (when payment_type = 일당형)
4. ✅ **Consistent formatting**: ALL amounts use same format (no mixing)
5. ❌ **NO numeric parentheticals**: `(30,000,000원)` FORBIDDEN in final display
6. ❌ **NO raw payment_type**: `LUMP_SUM`, `UNKNOWN` FORBIDDEN in cells

## Verification (Network Payload)

**Test Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected Network Response** (cells[].text):
```json
// Row: 지급유형
{"text": "정액 지급"}  // NOT "LUMP_SUM"

// Row: 핵심 보장 내용
{"text": "3천만원"}  // NOT "3,000만원" or "3천만원 (30,000,000원)"

// Row: 보장 한도 (if exists)
{"text": "보험기간 중 1회"}  // Consistent formatting
```

**Forbidden Patterns**:
- ❌ `"LUMP_SUM"` (raw enum)
- ❌ `"3,000만원"` (comma format)
- ❌ `"3천만원 (30,000,000원)"` (numeric parenthetical)
- ❌ `"2만원"` for 일당형 (missing prefix)

## Frontend Impact

**REVERTED**: `apps/web/lib/normalize/table.ts` changes
- Removed `applyEX3FormattingDuringNormalization()` function
- Normalization now just passes through backend strings (no transformation)

**Rationale**: Backend formatting makes frontend formatting redundant.

## Definition of Success

> "Network payload의 `cells[].text` 필드에서 `LUMP_SUM` 0%, `3,000만원` 0%, `(30,000,000원)` 0%이면 성공."

**Test**: Open DevTools → Network → Send query → Inspect payload → Verify all cells use Korean labels and Korean-only amounts.

## Constitutional Compliance

### ✅ ALLOWED (Backend String Formatting)
- Label mapping (enum → Korean)
- Regex pattern matching (strip parentheticals)
- Prefix addition (일당 for 일당형)
- String concatenation

### ❌ FORBIDDEN (NOT DONE)
- Calculation / inference
- LLM usage
- New data fields
- Logic changes (view-layer formatting ONLY)

## SSOT Lock Date

**2026-01-04**

**Lock Status**: ✅ FINAL (Backend formatting at source)

Any future EX3 formatting changes MUST:
1. Modify `ex3_compare_composer.py` formatting functions
2. Provide Network payload evidence (DevTools screenshot)
3. Verify NO raw enum values in payload
4. Update this document with changes
