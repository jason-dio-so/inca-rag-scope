# STEP NEXT-138-γ: EXAM3 AMOUNT/LIMIT Dimension Separation — Manual Test Plan

## Purpose
Verify that EXAM3 comparison view correctly separates AMOUNT (정액금액) and LIMIT (한도) into different sections, preventing semantic confusion.

## Core Rules Tested
1. **Main table shows ONLY AMOUNT** (핵심 보장 내용 = 정액금액)
2. **LIMIT goes to separate section** (보장 한도)
3. **NO mixing AMOUNT and LIMIT in same row**

## Test Cases

### TC1: Samsung vs Meritz 암진단비 (CRITICAL — Regression Test)
**Query**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected Behavior**:
1. Main table "핵심 보장 내용" row:
   - Samsung: "3천만원" (AMOUNT)
   - Meritz: "3천만원" (AMOUNT)
   - ❌ NO "보험기간 중 1회" in this row

2. Separate "보장 한도" section:
   - Samsung: "보험기간 중 1회" (LIMIT)
   - Meritz: "보험기간 중 1회" (LIMIT)

3. "보장 정의 기준" row:
   - Samsung: "보장금액(정액) 기준"
   - Meritz: "보장금액(정액) 기준"

**Verification Steps**:
1. Send query
2. **CHECK**: Main table "핵심 보장 내용" shows ONLY amounts (NO limit text)
3. **CHECK**: Separate "보장 한도" section exists BELOW main table
4. **CHECK**: Limit info (보험기간 중 1회) appears ONLY in 보장 한도 section

### TC2: Coverage with ONLY LIMIT (No Amount)
**Setup**: Coverage that has limit but NO amount (e.g., some 일당 담보)

**Expected Behavior**:
1. Main table "핵심 보장 내용":
   - Shows limit (fallback exception rule)
   - Summary bullet warns: "정액 보장금액이 명시되지 않음"

2. "보장 한도" section:
   - NOT shown (already in main table)

**Rationale**: Exception rule when NO amount exists anywhere

### TC3: Coverage with ONLY AMOUNT (No Limit)
**Setup**: Coverage with amount but NO limit

**Expected Behavior**:
1. Main table "핵심 보장 내용":
   - Shows amount

2. "보장 한도" section:
   - NOT shown (no limit info exists)

3. "보장 정의 기준":
   - "보장금액(정액) 기준"

### TC4: Mixed Dimensions (Samsung=AMOUNT, Meritz=LIMIT)
**Setup**: Samsung has amount, Meritz has limit (asymmetric)

**Expected Behavior**:
1. Main table "핵심 보장 내용":
   - Samsung: Shows amount
   - Meritz: "명시 없음" (because we show AMOUNT row, not limit)

2. "보장 한도" section:
   - Samsung: "표현 없음"
   - Meritz: Shows limit

3. "보장 정의 기준":
   - Samsung: "보장금액(정액) 기준"
   - Meritz: "지급 한도/횟수 기준"

**Verification**: Dimension asymmetry is clearly visible in separate sections

## Forbidden Patterns (Must NOT appear)

### ❌ FORBIDDEN-1: AMOUNT + LIMIT in Same Cell
**Example of BUG**:
```
핵심 보장 내용:
Samsung: "3천만원 (보험기간 중 1회)"
```

**This MUST NOT happen**. Amount and limit must be in different sections.

### ❌ FORBIDDEN-2: Limit in Main Table When Amount Exists
**Example of BUG**:
```
핵심 보장 내용:
Samsung: "보험기간 중 1회"  # When amount="3천만원" exists
```

**This MUST NOT happen**. If amount exists, show amount (not limit) in main table.

### ❌ FORBIDDEN-3: Raw Text Comparison
**Example of BUG**:
```python
if "보험기간 중" in raw_text:
    return "LIMIT"
```

**This MUST NOT happen**. Use structured KPI fields only.

## Success Metrics

### Definition of Success (Samsung vs Meritz 암진단비)
> "핵심 보장 내용 행에 '3천만원'만 표시되고, '보험기간 중 1회'는 별도 보장 한도 섹션에만 표시되면 성공"

### Regression Prevention
- ✅ EXAM2 unchanged (NO impact on "찾아줘" queries)
- ✅ EXAM4 unchanged (NO impact on O/X table)
- ✅ EXAM3 bubble unchanged (structural summary preserved)

## Implementation Notes

### Modified Files
- `apps/api/response_composers/ex3_compare_composer.py`:
  - Added `_tag_dimension()` (AMOUNT/LIMIT/MIXED tagging)
  - Modified `_build_table_section()` (AMOUNT-only in main table)
  - Added `_build_limit_section()` (separate LIMIT section)

### NO Changes
- ❌ EXAM2 handlers (NO impact)
- ❌ EXAM4 handlers (NO impact)
- ❌ Data pipeline (NO changes)

### Core Algorithm
```python
# Dimension tagging
has_amount = amount != "명시 없음"
has_limit = limit is not None and limit.strip()

if has_amount and has_limit:
    dim = "MIXED"
elif has_amount:
    dim = "AMOUNT"
elif has_limit:
    dim = "LIMIT"
else:
    dim = "AMOUNT"  # Default

# Main table (AMOUNT-first)
if has_any_amount:
    # Show amount (even if some insurers have "명시 없음")
    main_table = amount
else:
    # Fallback: Show limit (when NO amount exists)
    main_table = limit

# Separate section (LIMIT)
if has_any_limit:
    limit_section = limit
else:
    limit_section = None  # Don't show section
```

## Manual Verification Checklist

Before marking complete:
- [ ] TC1 verified (Samsung vs Meritz 암진단비)
- [ ] Main table shows ONLY amount
- [ ] Separate 보장 한도 section appears
- [ ] NO limit text in main table
- [ ] Summary bullets are AMOUNT-first
- [ ] EXAM2 regression test passed (NO impact)
- [ ] EXAM4 regression test passed (NO impact)
