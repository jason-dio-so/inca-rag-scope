# STEP NEXT-139A/B: EXAM3 View-Layer Formatting Applied — 2026-01-04

## Problem Statement

STEP NEXT-139A/B formatting rules were implemented in the **backend composer** but NOT reflected in the **frontend UI** because the view-layer normalizer/renderer was not updated.

**Symptom**:
- API response JSON contains formatted strings
- UI still shows old formatting (no "일당" prefix, numeric amounts, LUMP_SUM labels)

**Root Cause**:
- Backend composer formats data correctly
- Frontend `renderCellValue()` renders cell objects but doesn't apply EXAM3-specific formatting
- View-layer formatting was missing

## Solution

Applied STEP NEXT-139A/B formatting rules in the **frontend view layer** (`apps/web/lib/renderers/valueRenderer.ts`).

## Modified Files

### `apps/web/lib/normalize/table.ts` (PRIMARY)

**Why**: This is where cell objects are converted to strings - the ONLY point where we still have access to `meta.kpi_summary`

**Changes**:
1. Added `applyEX3FormattingDuringNormalization()` function (~80 lines)
2. Modified `normalizeRows()` to call formatting BEFORE `renderCellValue()` (preserves meta)
3. Implemented 4 formatting rules

**Key Insight**: Formatting must happen DURING normalization because `renderCellValue()` converts cell objects to strings, losing the `meta.kpi_summary` data needed for formatting.

### `apps/web/lib/renderers/valueRenderer.ts` (UPDATED)

**Why**: Document that formatting moved to normalization layer

**Changes**:
1. Removed `applyEX3Formatting()` function (moved to table.ts)
2. Added comment explaining where formatting now happens:

## Formatting Rules (LOCKED)

### Rule 1: LIMIT + AMOUNT Combination (STEP NEXT-139A)
```typescript
// Pattern: Both limit and amount exist
if (limitSummary && text && paymentType === "일당형") {
  return `${limit} (일당 ${cleanAmount})`;
}
```

**Example**:
- Before: `limit_summary: "보험기간 중 1회"`, `text: "2만원"`
- After: `"보험기간 중 1회 (일당 2만원)"`

### Rule 2: 일당형 Amount Prefix (STEP NEXT-139B)
```typescript
if (paymentType === "일당형") {
  if (!koreanOnly.startsWith("일당")) {
    return `일당 ${koreanOnly}`;
  }
}
```

**Example**:
- Before: `"2만원"`
- After: `"일당 2만원"`

### Rule 3: Korean-Only Amount Display (STEP NEXT-139B)
```typescript
// Remove numeric parenthetical
const koreanOnly = amount.replace(/\s*\([0-9,]+원\)\s*$/, "").trim();
```

**Example**:
- Before: `"3천만원 (30,000,000원)"`
- After: `"3천만원"`

### Rule 4: Payment Type Label Substitution (STEP NEXT-139B)
```typescript
const labelMap = {
  "LUMP_SUM": "정액 지급",
  "일당형": "일당 지급",
  "건별형": "건별 지급",
  "실손형": "실손 지급",
  "UNKNOWN": "표현 없음"
};
```

**Example**:
- Before: `"LUMP_SUM"`
- After: `"정액 지급"`

## Detection Logic

```typescript
function applyEX3Formatting(o: Record<string, any>): string | null {
  // Extract meta.kpi_summary
  const meta = o.meta;
  if (!meta?.kpi_summary) return null;

  const paymentType = meta.kpi_summary.payment_type;
  const limitSummary = meta.kpi_summary.limit_summary;

  // Apply formatting based on presence of limit/amount
  // ...
}
```

**Key Point**: Only applies formatting when `meta.kpi_summary` exists (EXAM3 cells only)

## Core Rules (ABSOLUTE)

1. ✅ **View-layer ONLY**: NO backend logic change
2. ✅ **String concatenation ONLY**: NO calculation, NO inference
3. ✅ **Meta-driven**: Reads from `meta.kpi_summary` (backend provides data)
4. ✅ **Priority formatting**: Applied BEFORE generic object patterns
5. ✅ **Korean amounts ONLY**: Strips numeric parentheticals
6. ❌ **NO EXAM2 impact**: Formatting only applies when `meta.kpi_summary` exists
7. ❌ **NO unit inference**: Uses payment_type from backend data
8. ❌ **NO calculation**: Pure string manipulation

## Verification Checklist

When testing EXAM3 comparison view ("삼성화재와 메리츠화재 암진단비 비교해줘"):

- [ ] **139A-1**: LIMIT + AMOUNT → "{한도} (일당 {금액})" (if 일당형)
- [ ] **139B-1**: 일당형 amount shows "일당 " prefix
- [ ] **139B-2**: 정액형 amount shows NO prefix (just "3천만원")
- [ ] **139B-3**: NO numeric amounts (e.g., "(30,000,000원)" stripped)
- [ ] **139B-4**: Payment type shows "정액 지급" (NOT "LUMP_SUM")
- [ ] **REGRESSION-1**: EXAM2 unchanged (NO impact on EX2_DETAIL / EX2_LIMIT_FIND)
- [ ] **REGRESSION-2**: Build succeeds (NO TypeScript errors)

## Frontend Build Status

```bash
cd apps/web && npm run build
# ✅ Compiled successfully in 1426.4ms
```

## Definition of Success

> "UI 화면에서 3가지 포맷팅이 모두 적용됨: (1) 일당 prefix, (2) 한글 금액만, (3) 정액 지급 라벨. API JSON만 바뀌고 화면 그대로 = 실패."

## Constitutional Basis

- **STEP NEXT-139A**: LIMIT + AMOUNT formatting specification
- **STEP NEXT-139B**: Amount display standardization specification
- **View Layer Lock**: NO backend/composer/handler changes allowed

## SSOT Lock Date

**2026-01-04**

**Lock Status**: ✅ FINAL (View-layer formatting applied)

Any future EXAM3 formatting changes MUST:
1. Update `applyEX3Formatting()` in `valueRenderer.ts`
2. Provide UI screenshot evidence
3. Verify NO impact on EXAM2 (EX2_DETAIL / EX2_LIMIT_FIND)
4. Update this document with new rules
