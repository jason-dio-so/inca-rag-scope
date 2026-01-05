# STEP NEXT-141-δ: Manual Verification Guide

**Date**: 2026-01-05
**Purpose**: Verify EX4 clarification NO context fallback behavior

---

## Setup

1. Start dev server:
   ```bash
   cd apps/web && npm run dev
   ```

2. Open browser: http://localhost:3000

---

## Test Scenarios

### S1: EX4 Preset → Clarification UI (CRITICAL)

**Steps**:
1. Click EX4 preset button: "제자리암, 경계성종양 보장여부 비교해줘"
2. Observe clarification UI

**Expected** ✅:
- Clarification message: "비교할 보험사를 선택해주세요"
- Insurer selection buttons shown
- Coverage input field: HIDDEN (NOT shown)
- "확인" button shown (not auto-submit)

**Forbidden** ❌:
- "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요"
- Coverage input field visible
- Auto-submit (clarification → result without user clicking)

**Status**: [ ] PASS / [ ] FAIL

---

### S2: EX4 Clarification → Result Flow

**Steps**:
1. Continue from S1
2. Select 2 insurers (e.g., 삼성화재, 메리츠화재)
3. Click "확인"
4. Observe result

**Expected** ✅:
- EX4 O/X table shown
- 2 disease subtypes × 2 insurers
- Evidence refs attached (PD:samsung:*, PD:meritz:*)

**Forbidden** ❌:
- EX3 comparison table (wrong exam type)
- EX2 detail view (wrong exam type)
- Error message / need_more_info

**Status**: [ ] PASS / [ ] FAIL

---

### S3: EX4 Context Isolation (CRITICAL)

**Steps**:
1. First query: "삼성화재와 메리츠화재 암진단비 비교해줘" (EX3)
2. Observe: "대화 중: 삼성화재 · 메리츠화재" shown
3. Click EX4 preset button: "제자리암, 경계성종양 보장여부 비교해줘"
4. Observe clarification UI

**Expected** ✅:
- Clarification UI appears (insurers selection required)
- "비교할 보험사를 선택해주세요"
- Previous locked insurers (삼성, 메리츠) NOT used silently

**Forbidden** ❌:
- Direct EX4 result without clarification (context fallback)
- Using previous locked insurers automatically

**Status**: [ ] PASS / [ ] FAIL

---

### S4 (Regression): EX3 "암진단비 비교해줘" → Clarification

**Steps**:
1. Fresh page reload
2. Type: "암진단비 비교해줘"
3. Observe clarification UI

**Expected** ✅:
- "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요"
- Insurer selection buttons
- Coverage input: HIDDEN (already resolved from message)

**Forbidden** ❌:
- Coverage input shown (already said "암진단비")
- EX4 routing (wrong exam type)

**Status**: [ ] PASS / [ ] FAIL

---

### S5 (Regression): EX2 Context Carryover

**Steps**:
1. Fresh page reload
2. Type: "삼성화재 암진단비 설명해줘" → EX2_DETAIL result shown
3. Type: "수술비는?"

**Expected** ✅:
- EX2_DETAIL result for 수술비 (삼성화재)
- NO clarification (context carries over)

**Forbidden** ❌:
- Clarification asking for insurer again
- EX3/EX4 routing

**Status**: [ ] PASS / [ ] FAIL

---

### S6 (Regression): EX4 Preset Routing Lock

**Steps**:
1. Click EX4 preset 5 times consecutively
2. Each time, select insurers → submit

**Expected** ✅:
- 5/5 route to EX4 O/X table (NOT EX3/EX1_DETAIL)

**Forbidden** ❌:
- EX3 comparison table shown
- EX2 detail view shown

**Status**: [ ] PASS / [ ] FAIL

---

## Definition of Success

All 6 scenarios PASS:
- ✅ S1: EX4 preset → clarification UI (insurers-only)
- ✅ S2: EX4 clarification → result flow
- ✅ S3: EX4 context isolation (NO carryover)
- ✅ S4: EX3 clarification (coverage resolved)
- ✅ S5: EX2 context carryover (PRESERVED)
- ✅ S6: EX4 preset routing lock (100%)

---

## Debug Checklist

If S1/S3 FAIL (context fallback still happening):

1. Check browser console for:
   ```
   [clarificationUtils] resolvedInsurers for EX4: ...
   [page.tsx] showClarification: ...
   ```

2. Verify `clarificationUtils.ts` lines 187-189:
   ```typescript
   if (examType === "EX4") {
     resolvedInsurers = payloadInsurers ?? (parsedInsurers.length > 0 ? parsedInsurers : null);
   ```

3. Verify NO fallback to `lockedInsurers` for EX4

4. Check `page.tsx` lines 222-232:
   - EX4 clarification message should be "비교할 보험사를 선택해주세요"
   - NOT "담보와 보험사"

---

## Notes

- Frontend tests in Python (`test_step_next_138_*.py`) will fail (TypeScript import error)
- These are documentation tests only
- Actual verification requires browser testing
- Backend EX4 tests (`test_step_next_130_ex4_ox_table.py`) should still PASS (8/8)

---

**Verified By**: _______________
**Date**: _______________
**Signature**: _______________
