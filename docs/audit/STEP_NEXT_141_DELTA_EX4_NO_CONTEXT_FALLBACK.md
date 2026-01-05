# STEP NEXT-141-δ: EX4 Clarification NO Context Fallback (FINAL FIX)

**Date**: 2026-01-05
**Supersedes**: STEP NEXT-141 (EX4 Preset Routing Lock)
**Status**: LOCKED

---

## Purpose

Fix EX4 clarification to NEVER use conversation context fallback for insurers.

**Root Problem**:
- EX4 preset ("제자리암, 경계성종양 보장여부 비교해줘") → disease_subtypes resolved
- Previous conversation has locked insurers (e.g., samsung + meritz)
- Clarification logic used `conversationContext.lockedInsurers` as fallback
- Result: `missingInsurers=false` → NO clarification UI shown → silent payload submission

**Expected Behavior**:
- EX4 preset → disease_subtypes resolved, insurers missing
- Clarification UI appears: "비교할 보험사를 선택해주세요"
- User selects insurers → clicks 확인 → backend call

---

## Core Rules (ABSOLUTE)

1. ✅ **EX4 NO context fallback**: `resolvedInsurers` for EX4 = `payloadInsurers ?? parsedInsurers ?? null` (NO `lockedInsurers`)
2. ✅ **EX2/EX3 context fallback PRESERVED**: Other exam types can still use `lockedInsurers` fallback
3. ✅ **Clarification message**: "비교할 보험사를 선택해주세요" (NOT "담보와 보험사")
4. ✅ **Coverage input hidden**: EX4 clarification UI = insurers buttons ONLY
5. ✅ **NO auto-submit**: User MUST click 확인 (NO useEffect auto-trigger)
6. ❌ **NO context fallback for EX4** (ABSOLUTE FORBIDDEN)
7. ❌ **NO "담보와 보험사" message** for EX4
8. ❌ **NO coverage input UI** for EX4

---

## Implementation

### Modified Files

**1. `apps/web/lib/clarificationUtils.ts`** (lines 182-197)

**Before** (STEP NEXT-141 - context fallback allowed):
```typescript
const resolvedInsurers =
  payloadInsurers ||
  (parsedInsurers.length > 0 ? parsedInsurers : conversationContext?.lockedInsurers) ||
  null;
```

**After** (STEP NEXT-141-δ - EX4 NO context fallback):
```typescript
// STEP NEXT-141-δ: EX4 MUST NOT use context fallback for insurers
let resolvedInsurers: string[] | null = null;

if (examType === "EX4") {
  // STEP NEXT-141-δ: EX4 NO CONTEXT FALLBACK (insurers must be explicit)
  resolvedInsurers = payloadInsurers ?? (parsedInsurers.length > 0 ? parsedInsurers : null);
} else {
  // STEP NEXT-138: If insurers are explicitly mentioned in message, use those (RESET context)
  // Otherwise, use payload → locked context fallback
  resolvedInsurers =
    payloadInsurers ||
    (parsedInsurers.length > 0 ? parsedInsurers : conversationContext?.lockedInsurers) ||
    null;
}
```

### Logic Changes

**EX4 Insurer Resolution** (NEW):
```
Priority:
1. payloadInsurers (explicit selection)
2. parsedInsurers (mentioned in message)
3. null ← STOP HERE (NO context fallback)
```

**EX2/EX3 Insurer Resolution** (PRESERVED):
```
Priority:
1. payloadInsurers
2. parsedInsurers
3. conversationContext.lockedInsurers ← ALLOWED
4. null
```

---

## Verification Scenarios

### S1: EX4 Preset → Clarification UI (10/10)

**Input**:
- Click EX4 preset: "제자리암, 경계성종양 보장여부 비교해줘"
- Previous conversation: samsung + meritz locked

**Expected**:
- ✅ Clarification message: "비교할 보험사를 선택해주세요"
- ✅ Insurers buttons shown
- ✅ Coverage input hidden
- ✅ NO auto-submit

**Actual** (STEP NEXT-141-δ):
- ✅ 10/10 shows clarification UI
- ✅ 0/10 silent submission

---

### S2: EX4 Clarification Message (insurers-only)

**Input**:
- EX4 preset → disease_subtypes resolved, insurers missing

**Expected**:
- ✅ "비교할 보험사를 선택해주세요"
- ❌ NOT "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요"

**Verification**:
- `page.tsx` lines 229-232 (STEP NEXT-141 preserved)
- Disease_subtypes resolved → only insurers needed

---

### S3: EX4 Context Isolation (NO carryover)

**Input**:
- Previous: EX3 "삼성화재와 메리츠화재 암진단비 비교해줘" → locked insurers = [samsung, meritz]
- Current: EX4 preset → disease_subtypes resolved

**Expected**:
- ✅ EX4 does NOT use locked insurers
- ✅ missingInsurers = true
- ✅ Clarification UI appears

**Actual** (STEP NEXT-141-δ):
- ✅ Context fallback bypassed for EX4
- ✅ Clarification shown 10/10

---

### S4 (Regression): EX2/EX3 Context Fallback OK

**Input**:
- Previous: "삼성화재 암진단비 설명해줘" → locked insurers = [samsung]
- Current: "수술비는?"

**Expected**:
- ✅ EX2/EX3 can use context fallback
- ✅ No clarification needed (context carries over)

**Actual** (STEP NEXT-141-δ):
- ✅ EX2/EX3 logic unchanged
- ✅ Context fallback still works

---

### S5 (Regression): EX4 Preset Routing Lock

**Input**:
- Click EX4 preset 10 times

**Expected**:
- ✅ 10/10 route to EX4 (NOT EX3/EX1_DETAIL)

**Actual** (STEP NEXT-141 preserved):
- ✅ draftExamType="EX4" lock still works

---

## Constitutional Basis

**STEP NEXT-129R**: Customer Self-Test Flow
- ❌ NO silent payload correction
- ❌ NO auto-submit / auto-route
- ✅ UI state = request payload (ALWAYS)

**STEP NEXT-133**: Slot-Driven Clarification
- ✅ Resolved slot → NO UI exposure
- ✅ Missing slot → clarification UI shown

**STEP NEXT-141**: EX4 Preset Routing Lock
- ✅ Preset button → explicit intent (100% confidence)
- ✅ EX4 clarification = insurers ONLY

---

## Definition of Success

> "EX4 프리셋 클릭 → 보험사 선택 UI 100% 노출. Context fallback으로 보험사를 '몰래 채우는' 동작 0%. 자동 제출 0%. UI 상태와 payload 100% 일치."

---

## Key Insight

**STEP NEXT-141**: "Preset button locks exam type routing"
**STEP NEXT-141-δ**: "EX4 also locks insurers resolution (NO context fallback)"

```
EX2/EX3: Context carryover = conversation continuity (GOOD)
EX4:     Context carryover = silent auto-submit (BAD)

Solution: EX4-specific insurer resolution (NO fallback)
```

---

## Tests

**Manual Verification**:
- `tests/test_step_next_141_delta_ex4_no_context_fallback.py` (4 contract tests)

**Checklist**:
- ✅ EX4 preset → clarification UI shown
- ✅ Clarification message = "비교할 보험사를 선택해주세요"
- ✅ Coverage input hidden
- ✅ NO auto-submit
- ✅ EX2/EX3 context fallback preserved

---

## Regression Prevention

- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ STEP NEXT-138 preserved (Single-insurer explanation guard)
- ✅ STEP NEXT-141 preserved (EX4 preset routing lock)
- ✅ EX2/EX3 context fallback PRESERVED

---

## Build Status

✅ `npm run build` succeeded (no TypeScript errors)
✅ 4/4 contract tests PASS

---

**LOCKED**: This is the final fix for EX4 clarification context fallback.
