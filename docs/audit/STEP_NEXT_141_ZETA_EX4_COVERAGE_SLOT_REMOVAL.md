# STEP NEXT-141-ζ: EX4 Coverage Slot Removal (FINAL FIX)

**Date**: 2026-01-05
**Supersedes**: STEP NEXT-141-δ (extended with coverage slot fix)
**Status**: LOCKED

---

## Purpose

Fix EX4 clarification gate to NEVER require coverage slot, resolving the issue where the confirm button was blocked even after selecting insurers.

**Root Problem**:
- EX4 preset → disease_subtypes resolved, insurers missing
- User selects insurers (samsung + meritz)
- Clarification gate stays open, confirm button disabled/hidden
- **Root Cause**: `missingSlots.coverage` was not explicitly set to `false` for EX4
- Result: Confirm button disabled condition included coverage check, blocking EX4 flow

**Console Evidence**:
```
examType: "EX4"
resolvedSlots.disease_subtypes: ["제자리암", "경계성종양"]
selectedInsurers: ["samsung", "meritz"]
missingSlots.coverage: undefined (should be false)  ← BUG
showClarification: true (should be false after insurer selection)
```

**Expected Behavior**:
- EX4 required slots = **{ insurers, disease_subtypes } ONLY**
- Coverage slot = NEVER required for EX4
- After selecting insurers → confirm button enabled → submit

---

## Core Rules (ABSOLUTE)

1. ✅ **EX4 coverage slot = false**: `missingCoverage = false` explicitly set for EX4
2. ✅ **EX4 required slots ONLY**: insurers + disease_subtypes (NO coverage)
3. ✅ **Confirm button logic**: NO coverage check for EX4
4. ✅ **EX2/EX3 preserved**: Coverage requirement unchanged
5. ❌ **NO coverage requirement for EX4** (ABSOLUTE FORBIDDEN)
6. ❌ **NO coverage in EX4 payload** (disease_subtypes ≠ coverage)
7. ❌ **NO auto-submit** (STEP NEXT-129R preserved)

---

## Implementation

### Modified Files

**1. `apps/web/lib/clarificationUtils.ts`** (lines 236-242)

**Before** (STEP NEXT-141-δ - missing explicit coverage = false):
```typescript
} else if (examType === "EX4") {
  // EX4 requires 1+ insurers + disease subtypes
  missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
  missingSubtypes = !resolvedSubtypes || resolvedSubtypes.length === 0;
  // missingCoverage NOT SET ← BUG
}
```

**After** (STEP NEXT-141-ζ - explicit coverage = false):
```typescript
} else if (examType === "EX4") {
  // STEP NEXT-141-ζ: EX4 requires 1+ insurers + disease subtypes ONLY
  // EX4 uses disease_subtypes (질병 서브타입), NOT coverage (담보)
  // Coverage slot MUST NOT gate EX4 clarification
  missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
  missingSubtypes = !resolvedSubtypes || resolvedSubtypes.length === 0;
  missingCoverage = false;  // ABSOLUTE: EX4 never requires coverage
}
```

### Logic Changes

**EX4 Missing Slots** (NEW):
```
missingInsurers: !resolvedInsurers || resolvedInsurers.length === 0
missingSubtypes: !resolvedSubtypes || resolvedSubtypes.length === 0
missingCoverage: false  ← EXPLICIT (prevents gating)
```

**Confirm Button Disabled Condition** (PRESERVED):
```typescript
disabled={
  (clarState.missingSlots.insurers && selectedInsurers.length < minInsurersRequired) ||
  (clarState.missingSlots.coverage && !coverageInput.trim())
}
```

With `missingCoverage = false`:
- `(false && !coverageInput.trim())` = `false`
- Coverage check never blocks EX4 confirm button

---

## Verification Scenarios

### S1: EX4 Preset → Insurer Selection → Confirm (CRITICAL)

**Steps**:
1. Click EX4 preset: "제자리암, 경계성종양 보장여부 비교해줘"
2. Send message
3. Select 1+ insurers (e.g., samsung)
4. Check confirm button state

**Expected** ✅:
- Console log:
  ```
  examType: "EX4"
  missingSlots.insurers: false (after selection)
  missingSlots.disease_subtypes: false (resolved from preset)
  missingSlots.coverage: false  ← FIX VERIFIED
  showClarification: false
  ```
- Confirm button: ENABLED
- Click confirm → EX4 request sent

**Forbidden** ❌:
- `missingSlots.coverage: true`
- Confirm button disabled after insurer selection
- "담보를 입력해주세요" message

---

### S2: EX4 Preset → No Insurers → Clarification

**Steps**:
1. Click EX4 preset
2. Send message
3. No insurers selected

**Expected** ✅:
- Clarification message: "비교할 보험사를 선택해주세요"
- Insurer buttons shown
- Coverage input: HIDDEN
- Confirm button: DISABLED (insurers missing)

**Forbidden** ❌:
- Coverage input field visible
- "담보와 보험사를 선택해주세요"

---

### S3 (Regression): EX3 Coverage Requirement

**Steps**:
1. Type: "암진단비 비교해줘"
2. Send message

**Expected** ✅:
- Clarification message: "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요"
- Coverage input: HIDDEN (already resolved from message)
- Insurer buttons shown
- EX3 still requires coverage (regression OK)

**Forbidden** ❌:
- EX3 coverage requirement removed

---

### S4 (Regression): EX2_LIMIT_FIND Coverage

**Steps**:
1. After EX2_DETAIL, type: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
2. Send message

**Expected** ✅:
- EX2_LIMIT_FIND routing
- Coverage extracted from message (암직접입원비)
- No clarification needed (auto-expand insurers)

**Forbidden** ❌:
- Coverage clarification shown

---

### S5 (Regression): EX4 Context Fallback

**Steps**:
1. Previous: "삼성화재와 메리츠화재 암진단비 비교해줘" (EX3, insurers locked)
2. Current: Click EX4 preset → send

**Expected** ✅:
- EX4 clarification shown (insurers required)
- NO context fallback (STEP NEXT-141-δ preserved)
- User must select insurers explicitly

**Forbidden** ❌:
- Silent auto-submit using locked insurers

---

## Build Status

✅ `npm run build` - **PASSED** (no TypeScript errors)
✅ Logic verified (coverage slot explicit for EX4)

---

## Constitutional Basis

**STEP NEXT-129R**: Customer Self-Test Flow
- ❌ NO auto-submit / auto-route
- ✅ UI state = request payload (ALWAYS)

**STEP NEXT-133**: Slot-Driven Clarification
- ✅ Missing slot → clarification UI shown
- ✅ Resolved slot → NO UI exposure

**STEP NEXT-141**: EX4 Preset Routing Lock
- ✅ Preset button → explicit intent (100% confidence)

**STEP NEXT-141-δ**: EX4 Context Isolation
- ✅ EX4 NO context fallback for insurers

**STEP NEXT-141-ζ**: EX4 Coverage Slot Removal (THIS STEP)
- ✅ EX4 NO coverage requirement (ABSOLUTE)

---

## Definition of Success

> "EX4 프리셋 → 보험사 선택 → 확인 버튼 100% 활성화. Coverage 체크로 인한 gating 0%. 콘솔에서 `missingSlots.coverage=false` 확인."

---

## Key Insight

**Problem Chain**:
1. STEP NEXT-141: Preset button locks exam type routing ✅
2. STEP NEXT-141-δ: EX4 locks insurers resolution (NO context fallback) ✅
3. **STEP NEXT-141-ζ: EX4 locks coverage slot (ALWAYS false)** ✅ ← THIS FIX

**Before**:
```
EX4 → insurers selected → coverage undefined → gating stuck
```

**After**:
```
EX4 → insurers selected → coverage=false → confirm enabled → submit
```

---

## Regression Prevention

- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ STEP NEXT-138 preserved (Single-insurer explanation guard)
- ✅ STEP NEXT-141 preserved (EX4 preset routing lock)
- ✅ STEP NEXT-141-δ preserved (EX4 context isolation)
- ✅ EX2/EX3 coverage requirement PRESERVED

---

## Manual Testing Required

See verification scenarios S1-S5 above.

**Critical Path**: S1 (EX4 preset → insurers → confirm enabled)

**Regression Checks**: S3 (EX3 coverage), S4 (EX2 coverage), S5 (EX4 context)

---

**LOCKED**: This is the final fix for EX4 coverage slot gating issue.
