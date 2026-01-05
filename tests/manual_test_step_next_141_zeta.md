# STEP NEXT-141-ζ: Manual Verification Guide

**Date**: 2026-01-05
**Purpose**: Verify EX4 coverage slot removal fix

---

## Setup

1. Start servers:
   ```bash
   # Terminal 1: Backend
   cd /Users/cheollee/inca-rag-scope
   uvicorn apps.api.main:app --reload --port 8000

   # Terminal 2: Frontend
   cd apps/web && npm run dev
   ```

2. Open browser: http://localhost:3000
3. Open browser console: Cmd+Option+J

---

## Test Scenarios

### S1: EX4 Preset → Insurer Selection → Confirm (CRITICAL)

**Steps**:
1. Reload page (Cmd+Shift+R)
2. Click EX4 preset button: "제자리암, 경계성종양 보장여부 비교해줘"
3. Click send (전송)
4. Observe clarification panel
5. Select 1 insurer (e.g., 삼성화재)
6. Check console log
7. Check confirm button state

**Expected** ✅:
- **Console log** (after selecting insurer):
  ```
  [page.tsx STEP NEXT-141-δ] CLARIFICATION_STATE {
    examType: "EX4",
    missingSlots: {
      insurers: false,         // ← After selection
      coverage: false,         // ← FIX: Explicit false
      disease_subtypes: false  // ← Resolved from preset
    },
    resolvedSlots: {
      insurers: ["samsung"],
      coverage: null,
      disease_subtypes: ["제자리암", "경계성종양"]
    },
    selectedInsurers: ["samsung"],
    minInsurersRequired: 1,
    draftExamType: "EX4"
  }
  ```

- **UI State**:
  - Clarification panel: "추가 정보 선택"
  - Insurer buttons: 삼성화재 = BLUE (selected), others = white
  - Coverage input: NOT VISIBLE (EX4 doesn't need coverage)
  - **Confirm button**: "확인" - **ENABLED** (not disabled, not hidden)

- **After clicking confirm**:
  - EX4 request sent to backend
  - O/X table shown with 2 disease subtypes × 1 insurer

**Forbidden** ❌:
- `missingSlots.coverage: true` in console
- `missingSlots.coverage: undefined` in console
- Confirm button disabled after selecting insurer
- Coverage input field visible
- "담보를 입력해주세요" message

**Status**: [ ] PASS / [ ] FAIL

---

### S2: EX4 Preset → No Insurers → Clarification

**Steps**:
1. Reload page
2. Click EX4 preset → send
3. Observe clarification panel (without selecting insurers)

**Expected** ✅:
- Console log:
  ```
  missingSlots: {
    insurers: true,          // ← Not selected yet
    coverage: false,         // ← FIX: Explicit false
    disease_subtypes: false  // ← Resolved from preset
  }
  ```

- UI:
  - Message: "비교할 보험사를 선택해주세요"
  - Insurer buttons: All white (none selected)
  - Coverage input: NOT VISIBLE
  - Confirm button: DISABLED (insurers missing)

**Forbidden** ❌:
- "담보와 보험사를 선택해주세요"
- Coverage input visible

**Status**: [ ] PASS / [ ] FAIL

---

### S3 (Regression): EX3 Coverage Requirement

**Steps**:
1. Reload page
2. Type: "암진단비 비교해줘"
3. Send

**Expected** ✅:
- Console log:
  ```
  examType: "EX3"
  missingSlots: {
    insurers: true,
    coverage: false,  // ← Resolved from message
    disease_subtypes: false
  }
  ```

- UI:
  - Message: "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요"
  - Coverage input: NOT VISIBLE (already said "암진단비")
  - Insurer buttons: Visible

- After selecting 2 insurers + confirm:
  - EX3 comparison table shown

**Forbidden** ❌:
- EX3 not requiring coverage anymore (regression)

**Status**: [ ] PASS / [ ] FAIL

---

### S4 (Regression): EX2_LIMIT_FIND

**Steps**:
1. Reload page
2. Type: "삼성화재 암진단비 설명해줘" → send (EX2_DETAIL)
3. Type: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" → send

**Expected** ✅:
- No clarification shown (coverage extracted from message)
- EX2_LIMIT_FIND table shown with 암직접입원비 (A6200)

**Forbidden** ❌:
- Coverage clarification required

**Status**: [ ] PASS / [ ] FAIL

---

### S5 (Regression): EX4 Context Isolation

**Steps**:
1. Reload page
2. Type: "삼성화재와 메리츠화재 암진단비 비교해줘" → send (EX3)
3. Observe: "대화 중: 삼성화재 · 메리츠화재" at bottom
4. Click EX4 preset → send

**Expected** ✅:
- Console log:
  ```
  conversationContext: ["samsung", "meritz"]  // ← From EX3
  resolvedInsurers: null  // ← NOT using context (STEP NEXT-141-δ)
  missingSlots.insurers: true
  missingSlots.coverage: false  // ← FIX
  ```

- UI:
  - Clarification panel shown (insurers required)
  - User must select insurers explicitly
  - NO auto-submit using locked insurers

**Forbidden** ❌:
- Direct EX4 result without clarification
- Auto-submit using previous locked insurers

**Status**: [ ] PASS / [ ] FAIL

---

## Definition of Success

All 5 scenarios PASS:
- ✅ S1: EX4 preset → insurers selected → confirm button ENABLED (CRITICAL)
- ✅ S2: EX4 preset → no insurers → clarification shown
- ✅ S3: EX3 coverage requirement preserved (regression OK)
- ✅ S4: EX2_LIMIT_FIND coverage extraction works (regression OK)
- ✅ S5: EX4 context isolation preserved (STEP NEXT-141-δ regression OK)

---

## Debug Checklist

If S1 FAIL (confirm button still disabled):

1. Check console for:
   ```
   missingSlots.coverage: ???
   ```
   - Should be `false` (not `true`, not `undefined`)

2. Verify `clarificationUtils.ts` line 242:
   ```typescript
   missingCoverage = false;  // ABSOLUTE: EX4 never requires coverage
   ```

3. Check `page.tsx` line 866-869:
   ```typescript
   disabled={
     (clarState.missingSlots.insurers && selectedInsurers.length < minInsurersRequired) ||
     (clarState.missingSlots.coverage && !coverageInput.trim())
   }
   ```
   - With `missingCoverage = false`, the second condition = `(false && ...) = false`

4. Check `selectedInsurers` array in console:
   - Should contain selected insurer codes (e.g., `["samsung"]`)

5. Hard refresh browser (Cmd+Shift+R) and retry

---

**Verified By**: _______________
**Date**: _______________
**Result**: [ ] ALL PASS / [ ] SOME FAIL
