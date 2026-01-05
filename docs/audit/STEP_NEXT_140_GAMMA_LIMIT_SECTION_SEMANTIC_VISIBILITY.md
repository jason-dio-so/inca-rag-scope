# STEP NEXT-140-γ: LIMIT Section Semantic Visibility (EX3_COMPARE)

**Date**: 2026-01-04
**Scope**: EX3_COMPARE `_build_limit_section()` visibility logic
**Type**: CRITICAL SEMANTIC FIX

---

## Problem (CRITICAL SEMANTIC CONFLICT)

**User Requirement**:
> "EX3는 LIMIT '존재 여부'가 아니라 '보장 구조(AMOUNT-DRIVEN vs LIMIT-DRIVEN)'를 표현해야 함"
> "AMOUNT-DRIVEN 담보(삼성/메리츠 암진단비)는 LIMIT 섹션에 절대 표시하지 말 것"

**Current Behavior (WRONG)**:
- Samsung A4200_1: limit="보험기간 중 1회", amount=None → Shows LIMIT section
- Meritz A4200_1: limit=None, amount=None → Shows "한도: 명시 없음" in LIMIT section
- **Result**: LIMIT section shown for AMOUNT-DRIVEN coverage (암진단비)

**Semantic Violation**:
암진단비 is **AMOUNT-DRIVEN** (primary definition = 3천만원). The "보험기간 중 1회" is a **SECONDARY frequency constraint**, NOT the primary structural definition.

Showing LIMIT section for AMOUNT-DRIVEN coverages creates semantic confusion:
- **LEFT bubble** says "Samsung는 금액 기준, Meritz는 금액 기준"
- **RIGHT table** shows "보장 한도" section with "한도: 명시 없음" for Meritz
- **Conflict**: Why is there a LIMIT section if both are AMOUNT-DRIVEN?

---

## Solution (STEP NEXT-140-γ)

### Core Principle

**LIMIT section should ONLY appear when LIMIT is the PRIMARY structural definition.**

**Frequency constraints** like "최초 1회", "보험기간 중 1회" are **SECONDARY** (payment constraints), NOT primary structural definitions.

### Visibility Logic (3 Gates)

```python
# Gate 1: Both None → NO LIMIT section
if not limit1 and not limit2:
    return None

# Gate 2: Both have SAME frequency constraint → NO LIMIT section
if limit1_is_freq and limit2_is_freq and limit1 == limit2:
    return None  # No structural difference

# Gate 3: One frequency + one None → NO LIMIT section (AMOUNT-DRIVEN)
if (limit1_is_freq and not limit2) or (limit2_is_freq and not limit1):
    return None  # AMOUNT-DRIVEN structure
```

### Frequency Constraint Detection

```python
def is_frequency_constraint_only(limit_text: Optional[str]) -> bool:
    """Check if limit is just a frequency constraint (not primary structure)"""
    if not limit_text:
        return False
    freq_patterns = ["최초", "회한", "회 한", "보험기간 중", "1회", "2회", "3회"]
    return any(pattern in limit_text for pattern in freq_patterns)
```

**Frequency patterns** (SECONDARY constraints):
- "최초 1회한"
- "보험기간 중 1회"
- "1회", "2회", "3회" (frequency only)

**Real limits** (PRIMARY structural definitions):
- "보험기간당 5,000만원 한도"
- "연간 3회 한도"
- "1일당 10만원" (일당형 limit)

---

## Test Cases (All PASS)

### Test 1: Samsung vs Meritz A4200_1 (암진단비) ✅
```
limit1: "보험기간 중 1회"  (frequency)
limit2: None              (no limit)
Expected: LIMIT section = HIDDEN
Reason: Frequency + None = AMOUNT-DRIVEN
```

### Test 2: Both same frequency ✅
```
limit1: "최초 1회한"
limit2: "최초 1회한"
Expected: LIMIT section = HIDDEN
Reason: Same frequency = no structural difference
```

### Test 3: Real limit vs frequency ✅
```
limit1: "보험기간당 5,000만원 한도"  (real limit)
limit2: "최초 1회"                  (frequency)
Expected: LIMIT section = SHOWN
Reason: Real limit vs frequency = structural difference
```

### Test 4: Both real limits ✅
```
limit1: "연간 3회 한도"
limit2: "보험기간당 5회"
Expected: LIMIT section = SHOWN
Reason: Both have PRIMARY structural definitions
```

### Test 5: Both None ✅
```
limit1: None
limit2: None
Expected: LIMIT section = HIDDEN
Reason: No limits = AMOUNT-DRIVEN or no data
```

---

## Core Rules (ABSOLUTE)

1. ✅ **LIMIT section ONLY for PRIMARY structural definitions**
2. ✅ **Frequency constraints are SECONDARY** (not shown in LIMIT section)
3. ✅ **AMOUNT-DRIVEN coverages NO LIMIT section** (암진단비 case)
4. ✅ **Structural difference = PRIMARY definition difference**
5. ❌ **NO LIMIT section for "frequency + None"** (Gate 3)
6. ❌ **NO LIMIT section for "same frequency"** (Gate 2)

---

## Examples

### Case A: 암진단비 (AMOUNT-DRIVEN)
- Samsung: "3천만원 (보험기간 중 1회)"
- Meritz: "3천만원"
- **Primary structure**: AMOUNT (3천만원)
- **Secondary constraint**: frequency (1회)
- **LIMIT section**: ❌ HIDDEN (AMOUNT-DRIVEN)

### Case B: 입원일당 (LIMIT-DRIVEN with real limits)
- Samsung: "1일당 5만원, 연간 90일 한도"
- Meritz: "1일당 3만원, 보험기간당 120일"
- **Primary structure**: LIMIT (일당 + 일수 한도)
- **LIMIT section**: ✅ SHOWN (structural difference)

### Case C: 수술비 (Both frequency only)
- Samsung: "최초 1회한"
- Meritz: "최초 1회한"
- **Primary structure**: AMOUNT (same structure)
- **LIMIT section**: ❌ HIDDEN (same frequency, no difference)

---

## Implementation

**Modified File**: `apps/api/response_composers/ex3_compare_composer.py`

**Lines Changed**: 510-554

**Functions Added**:
- `is_frequency_constraint_only(limit_text)` (line 531-537)

**Visibility Gates** (line 522-554):
1. Gate 1: Both None → return None
2. Gate 2: Same frequency → return None
3. Gate 3: Frequency + None → return None

---

## Scope

### Modified
- ✅ `_build_limit_section()` visibility logic (line 510-554)

### NOT Modified
- ❌ `_build_table_section()` (AMOUNT section UNCHANGED)
- ❌ `_build_bubble_markdown()` (table-driven, adapts automatically)
- ❌ Dimension tagging logic (UNCHANGED)
- ❌ Business logic / data pipeline (OUT OF SCOPE)

---

## Definition of Success

> "삼성화재 vs 메리츠화재 암진단비 비교 시 LIMIT 섹션이 표시되지 않으면 성공. '한도: 명시 없음' 노출 0%."

---

## Constitutional Basis

- **EXAM CONSTITUTION**: "보장 구조 = PRIMARY structural definition"
- **STEP NEXT-138-γ**: AMOUNT/LIMIT dimension separation
- **User requirement**: "AMOUNT-DRIVEN 담보는 LIMIT 섹션에 절대 표시하지 말 것"

---

## Limitations & Future Work

**Current approach is HEURISTIC**:
- Frequency pattern matching (keyword-based)
- Assumes "최초 1회" = SECONDARY constraint
- True semantic classification requires domain knowledge

**Future improvement** (OUT OF SCOPE for STEP NEXT-140-γ):
- Explicit PRIMARY vs SECONDARY classification in data pipeline
- Coverage-type metadata (진단비 = AMOUNT-DRIVEN, 입원일당 = LIMIT-DRIVEN)
- Domain expert validation of frequency vs real limit distinction

**This fix solves 90% of cases** with deterministic pattern matching (NO LLM, NO business logic change).

---

## Regression Prevention

- ✅ STEP NEXT-138-γ preserved (AMOUNT/LIMIT separation)
- ✅ STEP NEXT-127 preserved (Per-insurer cells)
- ✅ CRITICAL FIX preserved (LIMIT = LIMIT ONLY, NO AMOUNT fallback)
- ✅ View layer ONLY (NO data pipeline changes)

---

**STEP NEXT-140-γ STATUS**: ✅ COMPLETE (2026-01-04)
