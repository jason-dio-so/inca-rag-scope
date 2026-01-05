# CRITICAL FIX: LIMIT/AMOUNT Dimension Separation (Final Lock)

**Date**: 2026-01-04
**Scope**: EX3_COMPARE `_build_limit_section()` (EXAM3 ONLY)
**Type**: CRITICAL BUG FIX (Semantic Violation)

---

## Problem (CRITICAL)

**Semantic Violation**: LIMIT cells displayed AMOUNT as fallback, violating dimension separation rule.

### Evidence (Before Fix)

```python
# apps/api/response_composers/ex3_compare_composer.py (line 519-557)
def format_limit_display(limit: Optional[str], amount: str, payment_type: str) -> str:
    has_limit = limit and limit.strip()
    has_amount = amount and amount != "명시 없음"

    if has_limit and has_amount:
        return f"{limit} (보장금액: {amount})"  # ❌ MIXING DIMENSIONS
    elif has_limit:
        return limit
    elif has_amount:
        return f"보장금액: {amount}"  # ❌ AMOUNT IN LIMIT CELL
    else:
        return "표현 없음"
```

### Symptom

- **LIMIT missing** → shows `"보장금액: 3천만원"` in LIMIT cell
- **LIMIT + AMOUNT** → shows `"보험기간 중 1회 (보장금액: 3천만원)"` (dimension mixing)
- **Result**: User sees conflicting information (AMOUNT in LIMIT section)

### Constitutional Violation

> **STEP NEXT-138-γ**: "한 행은 반드시 동일 의미·동일 차원이어야 한다"

LIMIT section MUST contain ONLY limit information (NO amount fallback).

---

## Solution (CRITICAL FIX)

### New Logic (LOCKED)

```python
# apps/api/response_composers/ex3_compare_composer.py (line 518-533)
def format_limit_display(limit: Optional[str]) -> str:
    """
    Format limit display text (CRITICAL FIX)

    ABSOLUTE RULES:
    1. LIMIT exists → show limit
    2. LIMIT missing → "한도: 명시 없음"
    3. ❌ FORBIDDEN: Show AMOUNT in LIMIT cells
    4. ❌ FORBIDDEN: "(보장금액: ...)" in LIMIT section
    5. LIMIT = LIMIT ONLY (NO dimension mixing)
    """
    if limit and limit.strip():
        return limit
    else:
        return "한도: 명시 없음"
```

### Signature Change

**Before**:
```python
format_limit_display(limit, amount, payment_type)
```

**After**:
```python
format_limit_display(limit)  # NO amount, NO payment_type parameters
```

---

## Core Rules (ABSOLUTE)

1. ✅ **LIMIT section shows LIMIT ONLY** (NO amount fallback)
2. ✅ **Missing LIMIT → "한도: 명시 없음"** (NOT "표현 없음")
3. ✅ **NO dimension mixing** (AMOUNT in LIMIT cells = 0%, ABSOLUTE)
4. ✅ **NO "(보장금액: ...)" in LIMIT section** (ABSOLUTE FORBIDDEN)
5. ❌ **NO AMOUNT fallback** when LIMIT is missing
6. ❌ **NO combined display** like "{limit} (보장금액: {amount})"

---

## Verification

### Test Cases (All PASS)

```
Test 1: ✅ PASS
  Input: limit='보험기간 중 1회'
  Expected: 보험기간 중 1회
  Got: 보험기간 중 1회

Test 2: ✅ PASS
  Input: limit=None
  Expected: 한도: 명시 없음
  Got: 한도: 명시 없음

Test 3: ✅ PASS
  Input: limit=''
  Expected: 한도: 명시 없음
  Got: 한도: 명시 없음

Test 4: ✅ PASS
  Input: limit='   '
  Expected: 한도: 명시 없음
  Got: 한도: 명시 없음
```

### Critical Checks

- ✅ `"보장금액"` string in LIMIT cells = 0%
- ✅ Missing LIMIT → `"한도: 명시 없음"` (NOT amount fallback)
- ✅ LIMIT + AMOUNT → LIMIT shown in LIMIT section, AMOUNT shown in AMOUNT section (separate)
- ✅ NO dimension mixing in ANY cell

---

## Scope

### Modified Files

- `apps/api/response_composers/ex3_compare_composer.py` (line 518-538)
  - Simplified `format_limit_display()` function
  - Removed `amount` and `payment_type` parameters
  - Changed function calls (line 537-538)

### NOT Modified (Out of Scope)

- ❌ `ex2_detail_composer.py` (ALREADY CORRECT - proper separation at line 274, 279)
- ❌ `_build_table_section()` (AMOUNT section - UNCHANGED)
- ❌ Bubble markdown logic (UNCHANGED)
- ❌ Frontend/UI (NO client-side changes)

---

## Definition of Success

> "LIMIT 셀에서 '보장금액' 문자열 노출 = 0%. 한도 정보 없으면 '한도: 명시 없음'. AMOUNT fallback = 절대 금지."

---

## Constitutional Basis

- **STEP NEXT-138-γ**: AMOUNT/LIMIT dimension separation (EXAM3 ONLY)
- **EXAM CONSTITUTION**: "한 행은 반드시 동일 의미·동일 차원이어야 한다"
- **Data integrity rule**: LIMIT = LIMIT, AMOUNT = AMOUNT (NO cross-contamination)

---

## Regression Prevention

- ✅ EX2_DETAIL unchanged (already correct)
- ✅ AMOUNT section unchanged (still shows amounts)
- ✅ Bubble markdown unchanged (table-driven, adapts to new LIMIT display)
- ✅ NO business logic change (view layer ONLY)

---

## Implementation Status

- **Code**: ✅ COMPLETE
- **Syntax Check**: ✅ PASS
- **Server Reload**: ✅ PASS
- **Verification**: ✅ ALL TESTS PASS
- **Documentation**: ✅ THIS FILE

---

**CRITICAL FIX STATUS**: ✅ COMPLETE (2026-01-04)
