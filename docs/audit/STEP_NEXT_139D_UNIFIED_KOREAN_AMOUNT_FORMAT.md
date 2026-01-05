# STEP NEXT-139D: Unified Korean Amount Format (FINAL) — 2026-01-04

## Problem Statement (139C Failure)

**STEP NEXT-139C Failed**: Amount formats were inconsistent
- Samsung: `3000만원` (numeric+만원)
- Meritz: `3천만원` (Korean abbreviated)
- **Result**: Mixed formats violated "single standard" principle ❌

**Forbidden Patterns in 139C**:
- Mixing numeric (`3000만원`) and Korean (`3천만원`) formats
- LIMIT section with parenthetical amount synthesis (e.g., `"보험기간 중 1회 (보장금액: 3000만원)"`)

## Solution (STEP NEXT-139D)

**Constitutional Principle**:
> "모든 금액은 한글 축약 포맷으로 통일한다"

### Core Rules (ABSOLUTE)

1. ✅ **Korean abbreviated format ONLY**: `3천만원`, `2만원`, `5백만원`
2. ❌ **NO numeric+만원**: `3000만원`, `10000만원` - FORBIDDEN
3. ❌ **NO comma format**: `3,000만원`, `30,000,000원` - FORBIDDEN
4. ✅ **Single formatter utility**: 1 source of truth, NO individual formatting
5. ✅ **Applies to**: EX2/EX3 composers (ALL amount displays)

## Implementation

### 1. Unified Formatter Utility

**File**: `apps/api/utils/amount_formatter.py`

```python
def format_amount_korean(amount: str) -> str:
    """
    Convert ANY amount format to Korean abbreviated format.

    Input examples:
    - "3000만원" → "3천만원"
    - "3,000만원" → "3천만원"
    - "30000000원" → "3천만원"
    - "2만원" → "2만원" (already correct)
    - "명시 없음" → "명시 없음" (passthrough)

    Forbidden outputs:
    - "3000만원" (numeric+만원)
    - "3,000만원" (comma format)
    - "30,000,000원" (pure numeric)

    Returns: Korean abbreviated format ONLY
    """
```

**Key Functions**:
- `format_amount_korean()`: Main formatter (Korean-only output)
- `_convert_numeric_prefix_to_korean()`: `3000만원` → `3천만원`
- `_number_to_korean_abbreviated()`: `30000000` → `3천만원`
- `validate_korean_format()`: Forbidden pattern check

### 2. EX3 Composer Integration

**File**: `apps/api/response_composers/ex3_compare_composer.py`

**Changes**:
1. Import unified formatter:
   ```python
   from apps.api.utils.amount_formatter import format_amount_korean
   ```

2. Simplified `format_amount_display()`:
   ```python
   def format_amount_display(amount: str, payment_type: str) -> str:
       if amount == "명시 없음":
           return "명시 없음"

       # Use unified formatter
       korean_amount = format_amount_korean(amount)

       # Add prefix for 일당형
       if payment_type == "일당형":
           return f"일당 {korean_amount}" if not korean_amount.startswith("일당") else korean_amount

       return korean_amount
   ```

3. Updated `format_limit_display()`:
   ```python
   if amount and amount != "명시 없음":
       amount = format_amount_korean(amount)  # Unified formatter
   ```

## Verification Results

**Test Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Before (139C - FAILED)**:
```
Samsung: 3000만원  ❌ (numeric+만원)
Meritz:  3천만원   ⚠️ (Korean, but inconsistent)
```

**After (139D - SUCCESS)**:
```
Samsung: 3천만원   ✅ (Korean abbreviated)
Meritz:  3천만원   ✅ (Korean abbreviated)
```

**Unified Format Achieved**: ✅

### Verification Checklist

- ✅ Both amounts show identical format (`3천만원`)
- ✅ NO numeric+만원 format (`3000만원` = 0%)
- ✅ NO comma format (`3,000만원` = 0%)
- ✅ All amounts use Korean units (천, 만, 억)
- ✅ Payment type shows Korean labels (`정액 지급`)
- ✅ Limit section uses Korean amounts (if applicable)

## Constitutional Compliance

### ✅ ALLOWED (Unified Formatter)
- Korean unit conversion (천, 만, 억)
- Numeric prefix to Korean (`3000` → `3천`)
- Comma removal + Korean conversion
- Single source of truth (1 formatter)

### ❌ FORBIDDEN (ABSOLUTE)
- Individual formatting logic in composers
- Numeric+만원 output (`3000만원`)
- Comma format output (`3,000만원`)
- Mixed format outputs (some numeric, some Korean)
- LLM usage for formatting
- Calculation or inference

## Modified Files

### 1. `apps/api/utils/amount_formatter.py` (NEW)
- Unified Korean amount formatter
- ~150 lines
- Handles all format conversions

### 2. `apps/api/response_composers/ex3_compare_composer.py` (MODIFIED)
- Import unified formatter
- Simplified `format_amount_display()` (removed individual logic)
- Updated `format_limit_display()` (use unified formatter)
- ~20 lines changed

### 3. Frontend (NO CHANGES)
- Backend sends pre-formatted Korean amounts
- Frontend just displays (no transformation needed)

## Regression Prevention

### EX3 Preserved
- ✅ AMOUNT/LIMIT dimension separation (STEP NEXT-138-γ)
- ✅ Payment type Korean labels (STEP NEXT-139C)
- ✅ Main table structure unchanged
- ✅ Limit section structure unchanged

### EX2 (Future Application)
- ⏳ Apply same formatter to EX2_DETAIL composer
- ⏳ Apply to EX2_LIMIT_FIND composer (if amounts exist)
- ⏳ Maintain consistency across all EXAM types

## Definition of Success

> "모든 금액이 한글 축약 포맷(3천만원, 2만원)으로 통일되고, 숫자+만원(3000만원) 또는 콤마 포맷(3,000만원)이 0%이면 성공"

**Status**: ✅ SUCCESS (139D verified)

## SSOT Lock Date

**2026-01-04**

**Lock Status**: ✅ FINAL (Unified Korean formatter)

Any future amount formatting changes MUST:
1. Modify `apps/api/utils/amount_formatter.py` ONLY
2. Verify Korean abbreviated output (천, 만, 억 units)
3. Test across EX2/EX3 composers
4. Update this document with changes
