# STEP NEXT-141: EX3 Bubble Structure Confirmation (NOT Comparison)

**Date**: 2026-01-04
**Scope**: EX3_COMPARE `_build_bubble_markdown()` logic
**Type**: CRITICAL UX FIX (Purpose Redefinition)

---

## Problem (CRITICAL UX VIOLATION)

**User Requirement**:
> "EX3 요약 버블에서는 ❌ 보험사 간 차이형 서술을 절대 사용하지 말 것"
> "요약 버블은 반드시 → EX3 결과에서 확정된 'PRIMARY 보장 구조'만 설명한다"

**Current Behavior (WRONG)**:
```
삼성화재는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,
메리츠화재는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.

**즉,**
- 삼성화재: 지급 조건·횟수(한도) 기준
- 메리츠화재: 지급 금액이 명확한 정액(보장금액) 기준
```

**Violations**:
1. ❌ "삼성은 A, 메리츠는 B" comparison format (EXAM2 style)
2. ❌ Insurer-specific differences in bubble (confusion with table)
3. ❌ Exploration/discovery tone (wrong for EX3 purpose)

**EX3 Purpose Confusion**:
- **EX3 ≠ EXAM2** (탐색/발굴)
- **EX3 = EXAM3** (보고서 전용, 구조 확정 설명)
- **LEFT bubble** should confirm PRIMARY structure (NOT compare)
- **RIGHT table** shows detailed differences (comparison happens here)

---

## Solution (STEP NEXT-141)

### Core Principle

**EX3 Bubble = Structure Confirmation (NOT Comparison)**

> "두 보험사는 모두 [구조]입니다" (unified structure statement)

**LEFT bubble**: Confirms PRIMARY structural basis
**RIGHT table**: Shows detailed value differences

### New Bubble Format (LOCKED)

#### AMOUNT-DRIVEN Coverage
```
이 담보는 **정액 지급 구조**입니다.

진단 또는 사고 발생 시 약정된 금액을 지급하는 방식으로,
보장금액이 계약 시점에 명확히 정의됩니다.
```

#### LIMIT-DRIVEN Coverage
```
이 담보는 **한도 기준 구조**입니다.

지급 한도, 횟수, 또는 일수 제한이 적용되며,
보장 조건 해석이 중요합니다.
```

---

## Core Rules (ABSOLUTE)

### FORBIDDEN (STEP NEXT-141)
1. ❌ **"삼성은 A, 메리츠는 B"** comparison format
2. ❌ **Insurer-specific differences** in bubble
3. ❌ **EXAM2 exploration-style** comparison logic
4. ❌ **"즉," bullet format** with insurer names
5. ❌ **6-line hardcoded template** (STEP NEXT-126/128 SUPERSEDED)

### REQUIRED (STEP NEXT-141)
1. ✅ **"이 담보는 [구조]입니다"** unified statement
2. ✅ **PRIMARY structure confirmation** ONLY
3. ✅ **NO insurer names** in bubble text
4. ✅ **4 lines max** (concise, confirmation-only)
5. ✅ **Table-driven** structure detection (from "보장 정의 기준" row)

---

## Implementation

### Structure Detection Logic

```python
# Read "보장 정의 기준" row from table (SSOT)
def determine_primary_structure(basis_text: str) -> str:
    """Determine if PRIMARY structure is AMOUNT or LIMIT"""
    if not basis_text:
        return "UNKNOWN"

    # AMOUNT-DRIVEN keywords
    if "보장금액" in basis_text or "정액" in basis_text:
        return "AMOUNT"
    # LIMIT-DRIVEN keywords
    elif "한도" in basis_text or "횟수" in basis_text:
        return "LIMIT"
    else:
        return "UNKNOWN"
```

### Majority Rule

```python
# If both insurers have SAME structure → Use it
# If different structures → Fallback to AMOUNT (most common)
if structure1 == structure2:
    primary_structure = structure1
else:
    primary_structure = "AMOUNT"  # Default
```

### Bubble Template (LOCKED)

**AMOUNT-DRIVEN**:
```python
lines = [
    "이 담보는 **정액 지급 구조**입니다.",
    "",
    "진단 또는 사고 발생 시 약정된 금액을 지급하는 방식으로,",
    "보장금액이 계약 시점에 명확히 정의됩니다."
]
```

**LIMIT-DRIVEN**:
```python
lines = [
    "이 담보는 **한도 기준 구조**입니다.",
    "",
    "지급 한도, 횟수, 또는 일수 제한이 적용되며,",
    "보장 조건 해석이 중요합니다."
]
```

---

## Test Cases (All PASS)

### Test 1: Both AMOUNT-DRIVEN (암진단비) ✅
```
basis1: "보장금액(정액) 기준"
basis2: "보장금액(정액) 기준"
Expected: "이 담보는 **정액 지급 구조**입니다."
Got: "이 담보는 **정액 지급 구조**입니다."
```

### Test 2: Both LIMIT-DRIVEN (입원일당) ✅
```
basis1: "지급 한도/횟수 기준"
basis2: "지급 한도/횟수 기준"
Expected: "이 담보는 **한도 기준 구조**입니다."
Got: "이 담보는 **한도 기준 구조**입니다."
```

### Test 3: Different structures (fallback) ✅
```
basis1: "보장금액(정액) 기준"
basis2: "지급 한도/횟수 기준"
Expected: "이 담보는 **정액 지급 구조**입니다." (fallback to AMOUNT)
Got: "이 담보는 **정액 지급 구조**입니다."
```

---

## Examples

### Case A: 암진단비 (AMOUNT-DRIVEN)

**OLD (WRONG)**:
```
삼성화재는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,
메리츠화재는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.
```

**NEW (CORRECT)**:
```
이 담보는 **정액 지급 구조**입니다.

진단 또는 사고 발생 시 약정된 금액을 지급하는 방식으로,
보장금액이 계약 시점에 명확히 정의됩니다.
```

### Case B: 입원일당 (LIMIT-DRIVEN)

**OLD (WRONG)**:
```
삼성화재는 지급 한도 기준이고,
메리츠화재는 지급 한도 기준입니다.
```

**NEW (CORRECT)**:
```
이 담보는 **한도 기준 구조**입니다.

지급 한도, 횟수, 또는 일수 제한이 적용되며,
보장 조건 해석이 중요합니다.
```

---

## Scope

### Modified
- ✅ `_build_bubble_markdown()` (line 669-775)
  - Removed comparison logic
  - Added structure confirmation logic
  - 4 lines (was 6 lines)

### SUPERSEDED
- ~~STEP NEXT-126~~: Fixed 6-line template (comparison format)
- ~~STEP NEXT-128~~: Table-driven bubble (comparison format)

### Preserved
- ✅ Table-driven structure detection (reads from "보장 정의 기준" row)
- ✅ Deterministic logic (NO LLM)
- ✅ View layer ONLY (NO business logic change)

---

## Definition of Success

> "EX3 버블에 보험사명 0%. '이 담보는 [구조]입니다' 확정 설명만. Comparison은 table에만."

---

## UX Impact

### Before (Comparison Format)
- **Bubble**: Shows differences (삼성 vs 메리츠)
- **Table**: Shows differences (side-by-side)
- **Problem**: Duplication + confusion (what's the point of bubble?)

### After (Confirmation Format)
- **Bubble**: Confirms PRIMARY structure (정액 or 한도)
- **Table**: Shows detailed value differences
- **Benefit**: Clear separation of purpose (confirmation vs comparison)

---

## Constitutional Basis

- **EXAM CONSTITUTION**: "EX3 = 보고서 전용 (탐색 금지)"
- **STEP NEXT-140-γ**: PRIMARY vs SECONDARY structure distinction
- **User requirement**: "EX3 요약 = 구조 확정 설명 ONLY"

---

## Regression Prevention

- ✅ STEP NEXT-140-γ preserved (LIMIT section visibility)
- ✅ STEP NEXT-138-γ preserved (AMOUNT/LIMIT separation)
- ✅ CRITICAL FIX preserved (LIMIT = LIMIT ONLY)
- ✅ View layer ONLY (NO data pipeline changes)

---

**STEP NEXT-141 STATUS**: ✅ COMPLETE (2026-01-04)
