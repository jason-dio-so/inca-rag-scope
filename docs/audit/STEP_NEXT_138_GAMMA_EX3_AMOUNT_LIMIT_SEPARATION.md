# STEP NEXT-138-γ: EXAM3 AMOUNT/LIMIT Dimension Separation (SSOT) — 2026-01-04

## Problem Statement

**SEMANTIC CONFUSION IN EXAM3 COMPARISON VIEW**:
- AMOUNT (정액금액: "3천만원") and LIMIT (한도: "보험기간 중 1회") mixed in same row
- "핵심 보장 내용" cell shows: "3천만원" OR "보험기간 중 1회" (dimension mixing)
- Report semantic integrity violated (same row = different dimensions)

**Example of BUG (Before)**:
```
핵심 보장 내용:
Samsung: "보험기간 중 1회"  (LIMIT)
Meritz: "3천만원"           (AMOUNT)
```
→ **Same row compares different dimensions** (횟수 vs 금액) ← SEMANTIC VIOLATION

## Constitutional Basis

**EXAM CONSTITUTION**:
> "EXAM3 (EX3): 고객 전달용 보고서 (보고서 전용)"

**EXAM3 Report Principle**:
> "한 행은 반드시 **동일 의미·동일 차원**이어야 한다"

**STEP NEXT-138-γ Extension**:
> "AMOUNT와 LIMIT는 같은 칸에 절대 섞이지 않는다"

## Solution

### Core Principle: Dimension Separation
**AMOUNT and LIMIT are DIFFERENT dimensions** → Must be in DIFFERENT sections

- **AMOUNT** (정액금액): "3천만원", "2만원"
- **LIMIT** (한도): "보험기간 중 1회", "180일", "3회"

### Implementation Strategy

#### 1. Dimension Tagging (EXAM3 ONLY)
```python
def _tag_dimension(amount: str, limit: Optional[str]) -> str:
    """
    Tag dimension: AMOUNT | LIMIT | MIXED

    EXAM3 ONLY (DO NOT use in EXAM2)
    """
    has_amount = amount != "명시 없음"
    has_limit = limit and limit.strip()

    if has_amount and has_limit:
        return "MIXED"
    elif has_amount:
        return "AMOUNT"
    elif has_limit:
        return "LIMIT"
    else:
        return "AMOUNT"  # Default fallback
```

#### 2. Main Table (AMOUNT-First Rule)
**"핵심 보장 내용" row shows ONLY AMOUNT**:
```python
has_any_amount = (amount1 != "명시 없음") or (amount2 != "명시 없음")

if has_any_amount:
    # Show AMOUNT (even if some insurers = "명시 없음")
    row = {"text": "핵심 보장 내용", "cells": [amount1, amount2]}
else:
    # Fallback: NO amount exists → show limit
    # (Triggers summary bullet warning)
    row = {"text": "핵심 보장 내용", "cells": [limit1, limit2]}
```

#### 3. Separate LIMIT Section
**"보장 한도" section (shown BELOW main table)**:
```python
def _build_limit_section(...):
    """
    Build separate LIMIT section
    Only shown if at least one insurer has limit
    """
    if not limit1 and not limit2:
        return None  # Don't show section

    rows = [{
        "cells": [
            {"text": "보장 한도"},
            {"text": limit1 or "표현 없음", "meta": meta1},
            {"text": limit2 or "표현 없음", "meta": meta2}
        ]
    }]

    return {
        "kind": "comparison_table",
        "table_kind": "LIMIT_INFO",
        "title": f"{coverage_name} 보장 한도",
        "rows": rows
    }
```

#### 4. Structural Basis (AMOUNT-First)
**"보장 정의 기준" row**:
```python
def get_definition_basis(dim: str) -> str:
    if dim in ("AMOUNT", "MIXED"):
        return "보장금액(정액) 기준"
    elif dim == "LIMIT":
        return "지급 한도/횟수 기준"
    else:
        return "표현 없음"
```

**AMOUNT-first logic**: If both exist (MIXED), basis = "보장금액(정액) 기준"

## Core Rules (ABSOLUTE)

### Rule 1: Main Table Shows ONLY AMOUNT
```
핵심 보장 내용:
Samsung: "3천만원"        ✅ (AMOUNT)
Meritz: "3천만원"         ✅ (AMOUNT)

NOT:
Samsung: "보험기간 중 1회"  ❌ (LIMIT)
```

**Exception**: If NO amount exists for ALL insurers → fallback to limit (with warning)

### Rule 2: LIMIT Goes to Separate Section
```
보장 한도:
Samsung: "보험기간 중 1회"  ✅ (LIMIT)
Meritz: "보험기간 중 1회"  ✅ (LIMIT)
```

**Location**: AFTER main table, BEFORE footnotes

### Rule 3: NO Mixing AMOUNT and LIMIT in Same Cell
```
❌ FORBIDDEN:
"3천만원 (보험기간 중 1회)"
"한도: 보험기간 중 1회 (일당 2만원)"
```

**Enforcement**: Dimension tagging prevents mixing

### Rule 4: Structural Basis is AMOUNT-First
```
If AMOUNT exists (even with LIMIT):
보장 정의 기준 = "보장금액(정액) 기준"  ✅

NOT:
보장 정의 기준 = "지급 한도/횟수 기준"  ❌
```

## Modified Files

### 1. `apps/api/response_composers/ex3_compare_composer.py`
**Changes**:
- Added `_tag_dimension()` method (dimension tagging)
- Modified `_build_table_section()` (AMOUNT-only main table)
- Added `_build_limit_section()` (separate LIMIT section)
- Updated section building order (main table → limit section → footnotes)

**Lines Modified**: ~100 lines (3 methods)

### NO Changes
- ❌ EXAM2 handlers / composers (NO impact)
- ❌ EXAM4 handlers / composers (NO impact)
- ❌ Data pipeline (NO KPI extraction changes)
- ❌ Coverage cards structure (NO schema changes)

## Verification Scenarios

### ✅ CHECK-138-γ-1: Samsung vs Meritz 암진단비 (CRITICAL)
**Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected**:
1. Main table "핵심 보장 내용":
   - Samsung: "3천만원" ✅
   - Meritz: "3천만원" ✅
   - **NO "보험기간 중 1회" in this row** ✅

2. Separate "보장 한도" section:
   - Samsung: "보험기간 중 1회" ✅
   - Meritz: "보험기간 중 1회" ✅

3. "보장 정의 기준":
   - Samsung: "보장금액(정액) 기준" ✅
   - Meritz: "보장금액(정액) 기준" ✅

**Verification**: AMOUNT and LIMIT appear in DIFFERENT sections (NO mixing)

### ✅ CHECK-138-γ-2: Coverage with ONLY LIMIT (No Amount)
**Setup**: Coverage with limit but NO amount

**Expected**:
1. Main table "핵심 보장 내용":
   - Shows limit (fallback exception)

2. "보장 한도" section:
   - NOT shown (already in main table)

3. Summary bullet:
   - "정액 보장금액이 명시되지 않음" (warning)

**Rationale**: Exception rule when NO amount exists anywhere

### ✅ CHECK-138-γ-3: Coverage with ONLY AMOUNT (No Limit)
**Setup**: Coverage with amount but NO limit

**Expected**:
1. Main table "핵심 보장 내용":
   - Shows amount ✅

2. "보장 한도" section:
   - NOT shown ✅

3. "보장 정의 기준":
   - "보장금액(정액) 기준" ✅

### ✅ CHECK-138-γ-4: Asymmetric Dimensions (Samsung=AMOUNT, Meritz=LIMIT)
**Setup**: Samsung has amount, Meritz has limit

**Expected**:
1. Main table "핵심 보장 내용":
   - Samsung: Shows amount ✅
   - Meritz: "명시 없음" ✅ (because we show AMOUNT row, not limit)

2. "보장 한도" section:
   - Samsung: "표현 없음" ✅
   - Meritz: Shows limit ✅

3. "보장 정의 기준":
   - Samsung: "보장금액(정액) 기준" ✅
   - Meritz: "지급 한도/횟수 기준" ✅

**Verification**: Dimension asymmetry clearly visible in separate sections

## Forbidden Patterns (ABSOLUTE)

### ❌ FORBIDDEN-1: AMOUNT + LIMIT in Same Cell
```
"3천만원 (보험기간 중 1회)"
"한도: 보험기간 중 1회 (일당 2만원)"
```
**Violation**: Dimension mixing in same cell

### ❌ FORBIDDEN-2: Limit in Main Table When Amount Exists
```
핵심 보장 내용:
Samsung: "보험기간 중 1회"  # When amount="3천만원" exists
```
**Violation**: AMOUNT must be shown first (AMOUNT-first rule)

### ❌ FORBIDDEN-3: Raw Text String Comparison
```python
if "보험기간 중" in raw_text:
    return "LIMIT"
```
**Violation**: Must use structured KPI fields (kpi_summary.limit_summary)

### ❌ FORBIDDEN-4: EXAM3 Logic in EXAM2
```python
# In EXAM2 handler:
dim = _tag_dimension(amount, limit)  # ❌ FORBIDDEN
```
**Violation**: Dimension tagging is EXAM3 ONLY (NO impact on EXAM2)

## Regression Prevention

### EXAM2 Preservation
- ✅ "찾아줘" queries unchanged
- ✅ EX2_LIMIT_FIND output unchanged
- ✅ EX2_DETAIL output unchanged
- ✅ Handler logic unchanged

**Tests**: Run existing EXAM2 tests → ALL PASS (NO regression)

### EXAM4 Preservation
- ✅ O/X eligibility table unchanged
- ✅ EX4_ELIGIBILITY output unchanged
- ✅ Disease subtype logic unchanged

**Tests**: Run existing EXAM4 tests → ALL PASS (NO regression)

### EXAM3 Bubble Preservation
- ✅ Structural summary preserved (STEP NEXT-116)
- ✅ Bubble markdown preserved (STEP NEXT-128)
- ✅ Per-insurer meta preserved (STEP NEXT-127)

**Tests**: Run existing EXAM3 bubble tests → ALL PASS (table changed, bubble unchanged)

## Definition of Success

> "Samsung vs Meritz 암진단비 비교에서 '핵심 보장 내용' 행에 '3천만원'만 표시되고, '보험기간 중 1회'는 별도 '보장 한도' 섹션에만 표시되면 성공"

**Success Metrics**:
1. AMOUNT/LIMIT mixing in same cell → 0%
2. Main table shows ONLY AMOUNT (when exists) → 100%
3. LIMIT section appears separately → 100%
4. EXAM2/EXAM4 regression → 0%

## Algorithm Summary

```python
# Step 1: Dimension tagging (EXAM3 ONLY)
dim1 = _tag_dimension(amount1, limit1)
dim2 = _tag_dimension(amount2, limit2)

# Step 2: Main table (AMOUNT-first)
has_any_amount = (amount1 != "명시 없음") or (amount2 != "명시 없음")

if has_any_amount:
    main_table = [amount1, amount2]  # Show AMOUNT
else:
    main_table = [limit1, limit2]   # Fallback to LIMIT

# Step 3: Separate LIMIT section
if limit1 or limit2:
    limit_section = build_limit_section([limit1, limit2])
else:
    limit_section = None  # Don't show

# Step 4: Structural basis (AMOUNT-first)
basis1 = "보장금액(정액) 기준" if dim1 in ("AMOUNT", "MIXED") else "지급 한도/횟수 기준"
basis2 = "보장금액(정액) 기준" if dim2 in ("AMOUNT", "MIXED") else "지급 한도/횟수 기준"
```

## Testing Strategy

### Manual Tests
1. Run "삼성화재와 메리츠화재 암진단비 비교해줘"
2. Verify main table shows ONLY amounts
3. Verify separate 보장 한도 section appears
4. Verify NO limit text in main table

### Regression Tests
1. Run existing EXAM2 tests → ALL PASS
2. Run existing EXAM4 tests → ALL PASS
3. Run existing EXAM3 bubble tests → ALL PASS (bubble unchanged)

### Edge Cases
1. NO amount for all insurers → fallback to limit in main table
2. NO limit for all insurers → limit section NOT shown
3. Asymmetric dimensions → clear separation in different sections

## Notes

### Why Not Merge LIMIT Into Conditions Section?
**Considered**: Merge limit into KPI conditions section

**Rejected**:
- Conditions = exclusion/waiting/reduction (qualifiers)
- Limit = core coverage spec (횟수/기간 정의)
- Different semantic levels → separate sections

### Why AMOUNT-First (Not LIMIT-First)?
**Rationale**:
- Customer expectation: "얼마 받아?" (AMOUNT) > "몇 번 받아?" (LIMIT)
- Report clarity: 금액 = concrete, 한도 = constraint
- Aligns with existing "보장금액" priority in UI

### Why Dimension Tagging (Not Direct Field Check)?
**Benefits**:
- Reusable logic (single source of truth for dimension detection)
- Clear separation of concerns (tagging → rendering)
- Easy to extend (future: RATE, PERIOD, etc.)

## SSOT Lock Date
**2026-01-04**

**Lock Status**: ✅ FINAL (ABSOLUTE)

Any changes to EXAM3 AMOUNT/LIMIT rendering MUST:
1. Cite STEP NEXT-138-γ
2. Provide regression test evidence
3. Update this document with new STEP number
