# Q1 UI Smoke Test — Chat UI v2 Integration

**Date**: 2026-01-17
**Target**: Q1 Premium View (Frontend Integration)
**Scope**: UI Rendering + Evidence Rail + Anti-Legacy Guards

---

## 0. Test Objective

Verify Q1 Premium View renders correctly in Chat UI v2 with:
- ✅ viewModel-based rendering (NO legacy sections/title/summary)
- ✅ Main table: Numbers ONLY (NO formulas/percentages)
- ✅ Evidence Rail: Complete evidence (base_premium + rate_multiplier)
- ✅ Rail-Only design: Formulas/multipliers ONLY in Evidence Rail
- ✅ Anti-legacy guards: Runtime checks prevent regression

---

## 1. Implementation Summary

### 1.1 Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `types/premium.ts` | Updated type definitions | Align with backend response structure |
| `components/chat/Q1PremiumView.tsx` | Fixed field names | Use `insurer_code`, `premium_monthly` (not `_no_refund`) |
| `app/chat/page.tsx` | Added anti-legacy guards | Throw error if Q1 uses legacy fields |
| `app/api/chat_query/route.ts` | Q1 handler comments | Clarify `/premium/ranking` response structure |

### 1.2 Type Alignment (Backend ↔ Frontend)

**Backend Response** (`Q1HandlerDeterministic`):
```json
{
  "kind": "Q1",
  "query_params": {
    "age": 40,
    "sex": "M",
    "plan_variant": "BOTH",
    "sort_by": "monthly_total",
    "top_n": 4
  },
  "rows": [
    {
      "rank": 1,
      "insurer_code": "N01",
      "insurer_name": "DB손해보험",
      "product_name": "...",
      "premium_monthly": 125987,
      "premium_total": 30236880,
      "premium_monthly_general": 163783,
      "premium_total_general": 39307944,
      "evidence": {
        "base_premium": {
          "source_table": "product_premium_quote_v2",
          "ins_cd": "N01",
          "no_refund": {
            "premium_monthly": 125987,
            "premium_total": 30236880,
            "source": "API"
          },
          "general": {
            "premium_monthly": 163783,
            "premium_total": 39307944,
            "source": "CALC NO_REFUND×130% (DB round)"
          }
        },
        "rate_multiplier": {
          "source_table": "product_premium_quote_v2",
          "multiplier_percent": 130,
          "note": "Product-level GENERAL multiplier (hardcoded fallback)",
          "formula": "GENERAL = NO_REFUND × 130%"
        }
      }
    }
  ]
}
```

**Frontend Types** (`premium.ts`):
```typescript
interface Q1PremiumRow {
  rank: number;
  insurer_code: string;  // ✅ Aligned
  insurer_name: string;
  product_name?: string;
  premium_monthly: number;  // ✅ Aligned (NO_REFUND baseline)
  premium_total: number;
  premium_monthly_general?: number;
  premium_total_general?: number;
  evidence: {
    base_premium: {
      source_table: 'product_premium_quote_v2';
      ins_cd: string;
      age: number;
      sex: 'M' | 'F';
      no_refund: PremiumData;  // ✅ Nested structure
      general?: PremiumData;
    };
    rate_multiplier?: {
      source_table: string;
      multiplier_percent: number;
      formula?: string;
      note?: string;
    };
  };
}
```

---

## 2. Anti-Legacy Guards (Runtime Protection)

### 2.1 Guard Implementation (`page.tsx` lines 115-124)

```typescript
// ANTI-LEGACY GUARD: Prevent regression to legacy response structure
if (data.kind === 'Q1') {
  // Q1 MUST use viewModel (Chat UI v2), NOT sections/title/summary
  if (!data.viewModel) {
    throw new Error('[Q1 Anti-Legacy Guard] Q1 response must have viewModel field');
  }
  if (data.sections || data.title || data.summary_bullets) {
    throw new Error('[Q1 Anti-Legacy Guard] Q1 must NOT have legacy fields (sections/title/summary)');
  }
}
```

### 2.2 Guard Behavior

**Scenario A: Valid Q1 Response**
```json
{ "kind": "Q1", "viewModel": {...} }
```
✅ **PASS**: Guard allows render

**Scenario B: Missing viewModel**
```json
{ "kind": "Q1" }
```
❌ **FAIL**: Throws error, UI shows error state

**Scenario C: Legacy Fields Present**
```json
{ "kind": "Q1", "viewModel": {...}, "sections": [...] }
```
❌ **FAIL**: Throws error immediately (prevents silent regression)

---

## 3. UI Component Structure

### 3.1 Q1PremiumView Layout

```
┌─────────────────────────────────────────────┬─────────────────┐
│ Main Content (flex-1)                       │ Evidence Rail   │
│                                             │ (w-96)          │
│ ┌─────────────────────────────────────────┐ │ ┌─────────────┐ │
│ │ Header (Blue)                           │ │ │ Evidence    │ │
│ │ - 보험료 비교 (Top 4)                    │ │ │ Header      │ │
│ │ - age/sex/as_of_date                    │ │ │ (Purple)    │ │
│ └─────────────────────────────────────────┘ │ └─────────────┘ │
│                                             │                 │
│ ┌─────────────────────────────────────────┐ │ ┌─────────────┐ │
│ │ Comparison Table                        │ │ │ Base        │ │
│ │                                         │ │ │ Premium     │ │
│ │ Rank | 보험사 | 상품명 | 무해지 | 일반  │ │ │ Evidence    │ │
│ │  1   | DB    | ...   | 1,259  | 1,638 │ │ │             │ │
│ │  2   | 롯데  | ...   | 1,493  | 1,940 │ │ │ NO_REFUND:  │ │
│ │                                         │ │ │ 월납: ...   │ │
│ │ ✅ Numbers ONLY (NO formulas/%)         │ │ │             │ │
│ └─────────────────────────────────────────┘ │ │ GENERAL:    │ │
│                                             │ │ 월납: ...   │ │
│ ┌─────────────────────────────────────────┐ │ └─────────────┘ │
│ │ Guidance Notice (Yellow)                │ │                 │
│ │ - 근거는 우측 Evidence에서 확인         │ │ ┌─────────────┐ │
│ └─────────────────────────────────────────┘ │ │ Rate        │ │
│                                             │ │ Multiplier  │ │
│ ┌─────────────────────────────────────────┐ │ │ (Orange)    │ │
│ │ Note Block (Gray)                       │ │ │             │ │
│ │ - DB 기준, as_of_date                   │ │ │ 130%        │ │
│ └─────────────────────────────────────────┘ │ │ Formula:... │ │
│                                             │ └─────────────┘ │
└─────────────────────────────────────────────┴─────────────────┘
```

### 3.2 Evidence Rail (Rail-Only Design)

**Displayed ONLY in Rail** (NEVER in main table):
- ✅ Multiplier percentage (130%)
- ✅ Formula text ("GENERAL = NO_REFUND × 130%")
- ✅ Source table names
- ✅ Source references (API, CALC, etc.)
- ✅ Evidence metadata (age, sex, as_of_date)

**Main Table Displays**:
- ✅ Numbers ONLY (만원 단위)
- ❌ NO formulas
- ❌ NO percentages
- ❌ NO "×" or calculation symbols

---

## 4. Manual Test Protocol

### 4.1 Prerequisites

**Services Running**:
```bash
# Terminal 1: API Server
cd /Users/cheollee/inca-rag-scope
export SSOT_DB_URL="postgresql://postgres:postgres@localhost:5433/inca_ssot"
python -m uvicorn apps.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2: Web Server
cd /Users/cheollee/inca-rag-scope/apps/web
export NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev
```

### 4.2 Test Cases

#### TC1: Basic Q1 Rendering

**Steps**:
1. Open browser: `http://localhost:3000/chat`
2. Enter query: "보험료 저렴한 순서대로 비교해줘"
3. Select insurers: N01, N02, N08, N10 (or use "4개" preset)
4. Set filters: age=40, sex=M
5. Click "비교 생성"

**Expected**:
- ✅ Response kind badge shows "보험료 비교"
- ✅ Main table displays 4 rows (ranked 1-4)
- ✅ Columns: 순위 | 보험사 | 상품명 | 무해지 월납 | 무해지 총납 | 일반 월납 | 일반 총납 | 근거
- ✅ All premium cells show numbers only (만원 format)
- ✅ NO formulas/percentages in main table
- ✅ "근거 보기" button in each row
- ✅ NO console errors

**Actual**: [TO BE FILLED DURING TEST]

---

#### TC2: Evidence Rail Display

**Steps**:
1. (Continue from TC1)
2. Click on the first row (rank 1)

**Expected**:
- ✅ Evidence Rail appears on right side (w-96)
- ✅ Rail shows "근거 (Evidence)" header with insurer/product name
- ✅ Section 1: Base Premium Evidence
  - Source table: `product_premium_quote_v2`
  - Conditions: age=40, sex=M, as_of_date=2025-11-26
  - NO_REFUND: 월납/총납 (만원)
  - GENERAL: 월납/총납 (만원)
  - Source labels (API, CALC, etc.)
- ✅ Section 2: Rate Multiplier Evidence
  - Source table: `product_premium_quote_v2` or `coverage_premium_quote`
  - Multiplier: 130%
  - Formula: "GENERAL = NO_REFUND × 130%"
  - Note: "Product-level GENERAL multiplier (hardcoded fallback)"
- ✅ NO formulas/percentages in main table (still)
- ✅ NO console errors

**Actual**: [TO BE FILLED DURING TEST]

---

#### TC3: Anti-Legacy Guard Test

**Steps**:
1. (Mock scenario) Modify `handleQ1` to return legacy structure:
```typescript
return {
  kind: "Q1",
  viewModel: {...},
  sections: [{...}],  // ← Legacy field
  title: "..."         // ← Legacy field
};
```
2. Submit Q1 query

**Expected**:
- ❌ Error thrown: "[Q1 Anti-Legacy Guard] Q1 must NOT have legacy fields..."
- ✅ UI shows error state (not silent failure)
- ✅ Console shows error message

**Actual**: [TO BE TESTED WITH CODE MODIFICATION]

---

#### TC4: Missing Evidence Handling

**Steps**:
1. (Continue from TC1)
2. Click on a row with missing evidence (if any)

**Expected**:
- ✅ Evidence Rail shows available evidence
- ✅ If no rate_multiplier: Shows warning "⚠️ GENERAL variant이지만 multiplier evidence를 찾을 수 없습니다."
- ✅ NO crash, graceful degradation

**Actual**: [TO BE FILLED DURING TEST]

---

## 5. Validation Checklist

### 5.1 Response Structure

- [ ] Q1 response has `viewModel` field
- [ ] Q1 response does NOT have `sections` field
- [ ] Q1 response does NOT have `title` field
- [ ] Q1 response does NOT have `summary_bullets` field
- [ ] `viewModel.rows` is an array of Q1PremiumRow
- [ ] Each row has `insurer_code` (not `ins_cd`)
- [ ] Each row has `premium_monthly` (not `premium_monthly_no_refund`)

### 5.2 Main Table Display

- [ ] Table shows numbers ONLY (만원 format)
- [ ] NO formulas in main table
- [ ] NO percentages in main table
- [ ] NO "×" symbols in main table
- [ ] Missing values display as "—"
- [ ] Rows are clickable
- [ ] Selected row highlights (bg-blue-50)

### 5.3 Evidence Rail

- [ ] Rail appears when row clicked
- [ ] Rail shows Base Premium Evidence
- [ ] Rail shows Rate Multiplier Evidence (if GENERAL)
- [ ] Multiplier percentage displayed (e.g., "130%")
- [ ] Formula displayed (e.g., "GENERAL = NO_REFUND × 130%")
- [ ] Source tables shown
- [ ] NO formulas leaked into main table

### 5.4 Anti-Legacy Guards

- [ ] Guard throws error if `viewModel` missing
- [ ] Guard throws error if legacy fields present
- [ ] Error message is clear and actionable
- [ ] UI shows error state (not silent failure)

### 5.5 Legacy Imports

- [ ] Q1PremiumView does NOT import `Q12ReportView`
- [ ] Q1PremiumView does NOT import `demo-q12` components
- [ ] Q1PremiumView does NOT import legacy comparison tables
- [ ] All imports are Chat UI v2 compliant

---

## 6. Test Results

**Test Date**: [TO BE FILLED]

**Environment**:
- API Server: Running on http://localhost:8000
- Web Server: Running on http://localhost:3000
- Database: inca_ssot@5433 (SSOT)

**TC1 Result**: [ ] PASS / [ ] FAIL
**TC2 Result**: [ ] PASS / [ ] FAIL
**TC3 Result**: [ ] PASS / [ ] FAIL
**TC4 Result**: [ ] PASS / [ ] FAIL

**Overall Status**: [ ] ALL PASS / [ ] PARTIAL / [ ] BLOCKED

---

## 7. Known Limitations

1. **Web Server Required**: UI tests cannot run without `npm run dev`
2. **Browser Manual Testing**: No automated E2E tests yet
3. **Evidence Completeness**: Depends on backend data availability
4. **Anti-Legacy Guard Coverage**: Only checks top-level fields (not nested)

---

## 8. Next Steps

**If All Tests PASS**:
1. ✅ Declare Q1 UI Integration COMPLETE
2. ✅ Update STATUS.md with Q1 UI DONE
3. ✅ Commit changes with message:
   ```
   feat(ui): complete Q1 Premium View integration (Chat UI v2)

   - Align types with backend response structure
   - Add anti-legacy guards to prevent regression
   - Implement Evidence Rail with Rail-Only design
   - Test main table (numbers only) + Evidence Rail
   ```

**If Tests FAIL**:
1. ❌ Document failure mode
2. ❌ Identify root cause (backend vs frontend)
3. ❌ Apply fix
4. ❌ Re-run smoke test

---

## 9. Declaration

**Q1 UI Integration Status**: [TO BE DECLARED AFTER TEST]

**Declaration Statement** (if PASS):

> "Q1 Premium View는 Chat UI v2 스펙에 완전히 정합하며,
> legacy UI 패턴(sections/title/summary)을 사용하지 않고,
> viewModel 기반 렌더링 및 Evidence Rail-Only 디자인을 준수합니다.
> Anti-legacy guard가 활성화되어 회귀를 방지합니다."

---

**Test Completed**: [PENDING WEB SERVER STARTUP]
