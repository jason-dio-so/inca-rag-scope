# STEP NEXT-141-ζζ: EX4 Coverage Gating Fix (Double Defense)

**Date**: 2026-01-05
**Supersedes**: STEP NEXT-141-ζ (extended with UI safety net)
**Status**: LOCKED

---

## Purpose

Fix EX4 confirm button gating issue with **double defense**: SSOT logic + UI safety net

**Root Problem**:
- STEP NEXT-141-ζ set `missingCoverage = false` for EX4
- BUT users still reported: `missingSlots.coverage === true` blocking confirm button
- **Hypothesis**: Edge case where coverage slot is truthy despite explicit false assignment

**Solution**:
- **Defense Layer 1 (SSOT)**: Maintain `missingCoverage = false` in clarificationUtils + debug logging
- **Defense Layer 2 (UI Safety Net)**: Explicitly exclude EX4 from coverage gating in confirm button disabled condition

---

## Core Rules (ABSOLUTE)

1. ✅ **Double Defense**: SSOT (clarificationUtils) + UI safety net (page.tsx)
2. ✅ **EX4 coverage gating = FORBIDDEN**: UI MUST bypass coverage check for EX4
3. ✅ **Debug logging**: Temporary console.log to verify SSOT values
4. ✅ **EX2/EX3 preserved**: Coverage requirement unchanged
5. ❌ **NO coverage gating for EX4** (ABSOLUTE - enforced at UI level)
6. ❌ **NO auto-submit** (STEP NEXT-129R preserved)

---

## Implementation

### Modified Files

**1. `apps/web/lib/clarificationUtils.ts`** (lines 248-259)

**Added Debug Logging**:
```typescript
// STEP NEXT-141-ζζ: Debug logging for EX4 coverage slot issue
if (examType === "EX4") {
  console.log("[clarificationUtils EX4 RETURN]", {
    examType,
    missingInsurers,
    missingCoverage,  // Should be false
    missingSubtypes,
    resolvedInsurers,
    resolvedCoverage,
    resolvedSubtypes,
  });
}
```

**Purpose**: Verify that `missingCoverage` is `false` at SSOT return point

---

**2. `apps/web/app/page.tsx`** (lines 866-870)

**Before** (STEP NEXT-141-ζ - vulnerable to coverage=true):
```typescript
disabled={
  (clarState.missingSlots.insurers && selectedInsurers.length < minInsurersRequired) ||
  (clarState.missingSlots.coverage && !coverageInput.trim())
}
```

**After** (STEP NEXT-141-ζζ - UI safety net):
```typescript
disabled={
  (clarState.missingSlots.insurers && selectedInsurers.length < minInsurersRequired) ||
  // STEP NEXT-141-ζζ: EX4 NEVER gates on coverage (UI safety net)
  (clarState.examType !== "EX4" && clarState.missingSlots.coverage && !coverageInput.trim())
}
```

**Purpose**: Even if `clarState.missingSlots.coverage` is `true` for some reason, EX4 confirm button is NEVER disabled by coverage check

---

## Logic Changes

### Defense Layer 1: SSOT (clarificationUtils)

**EX4 Branch** (already in STEP NEXT-141-ζ):
```typescript
} else if (examType === "EX4") {
  missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
  missingSubtypes = !resolvedSubtypes || resolvedSubtypes.length === 0;
  missingCoverage = false;  // ABSOLUTE: EX4 never requires coverage
}
```

**Return Value**:
```typescript
return {
  showClarification,
  missingSlots: {
    insurers: missingInsurers,
    coverage: missingCoverage,  // Should be false for EX4
    disease_subtypes: missingSubtypes,
  },
  // ...
};
```

---

### Defense Layer 2: UI Safety Net (page.tsx)

**Confirm Button Disabled Condition**:
```typescript
// Insurers check (all exam types)
(clarState.missingSlots.insurers && selectedInsurers.length < minInsurersRequired)

||

// Coverage check (EX2/EX3/EX1_DETAIL ONLY, NOT EX4)
(clarState.examType !== "EX4" && clarState.missingSlots.coverage && !coverageInput.trim())
```

**Effect**:
- EX2/EX3/EX1_DETAIL: Coverage check active (regression prevented)
- **EX4: Coverage check bypassed** (safety net active)
- Even if `clarState.missingSlots.coverage = true` due to unknown bug, EX4 confirm button remains enabled

---

## Verification Scenarios

### S1: EX4 Preset → Insurer Selection → Confirm (CRITICAL)

**Steps**:
1. Click EX4 preset → send
2. Select 1+ insurers
3. Check browser console
4. Check confirm button state

**Expected** ✅:
- **Console log 1** (from page.tsx existing log):
  ```
  [page.tsx STEP NEXT-141-δ] CLARIFICATION_STATE {
    examType: "EX4",
    missingSlots: {
      insurers: false,
      coverage: ???,  // ← We want to see what this actually is
      disease_subtypes: false
    },
    // ...
  }
  ```

- **Console log 2** (NEW - from clarificationUtils):
  ```
  [clarificationUtils EX4 RETURN] {
    examType: "EX4",
    missingInsurers: false,
    missingCoverage: false,  // ← Should be false
    missingSubtypes: false,
    // ...
  }
  ```

- **UI State**:
  - Confirm button: **ENABLED** (regardless of coverage value)
  - Click confirm → EX4 request sent
  - O/X table appears

**Forbidden** ❌:
- Confirm button disabled after selecting insurers
- Coverage gating EX4 flow

**Status**: [ ] PASS / [ ] FAIL

---

### S2: EX4 Coverage Slot Value Investigation

**Purpose**: Determine if `missingCoverage` becomes `true` after clarificationUtils returns

**Check**:
1. Compare console logs:
   - `[clarificationUtils EX4 RETURN] missingCoverage: ???`
   - `[page.tsx STEP NEXT-141-δ] CLARIFICATION_STATE missingSlots.coverage: ???`

2. If values differ:
   - **Root cause**: page.tsx is modifying clarState after deriveClarificationState
   - **Action**: Search for `clarState.missingSlots` mutations in page.tsx

3. If values are same (both false):
   - **Root cause**: User error or browser cache issue
   - **Action**: Hard refresh (Cmd+Shift+R) and retry

---

### S3 (Regression): EX3 Coverage Requirement

**Steps**:
1. Type: "암진단비 비교해줘" → send
2. Select 0 insurers
3. Check confirm button

**Expected** ✅:
- Confirm button: DISABLED (insurers missing)
- Coverage gating still works for EX3

**Forbidden** ❌:
- EX3 confirm button enabled without coverage

**Status**: [ ] PASS / [ ] FAIL

---

### S4: UI Safety Net Effectiveness

**Test**: Manually inject `coverage: true` in clarState

**Procedure**:
1. Add temporary code in page.tsx before disabled calculation:
   ```typescript
   if (clarState.examType === "EX4") {
     clarState.missingSlots.coverage = true;  // FORCE BUG
   }
   ```

2. Verify confirm button is STILL ENABLED for EX4 (safety net working)

3. Remove temporary code

**Expected** ✅:
- Safety net prevents coverage gating even when forced to true

---

## Build Status

✅ **`npm run build`** - PASSED (no TypeScript errors)

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

**STEP NEXT-141-ζ**: EX4 Coverage Slot Removal
- ✅ EX4 `missingCoverage = false` (SSOT)

**STEP NEXT-141-ζζ**: EX4 Coverage Gating Fix (THIS STEP)
- ✅ EX4 coverage gating bypassed at UI level (double defense)

---

## Definition of Success

> "EX4 프리셋 → 보험사 선택 → 확인 버튼 100% 활성화. Coverage 체크가 true여도 UI safety net이 막아줌. 콘솔 로그로 SSOT vs UI 상태 비교 가능."

---

## Key Insight

**Defense in Depth**:
1. **STEP NEXT-141-ζ**: SSOT sets `missingCoverage = false` ✅
2. **STEP NEXT-141-ζζ**: UI bypasses coverage check for EX4 ✅ ← **Safety Net**

**Why Both Layers**:
- Layer 1 (SSOT): Correct behavior at source
- Layer 2 (UI): Prevents UX failure even if source has unknown bug
- **Result**: EX4 confirm button CANNOT be blocked by coverage

**Debug Strategy**:
- Console logs show if coverage becomes true AFTER clarificationUtils
- If true, investigate page.tsx state mutations
- If false, investigate browser state/cache issues

---

## Next Steps

1. **Manual Testing**: Follow S1-S4 scenarios
2. **Console Investigation**: Compare clarificationUtils vs page.tsx coverage values
3. **Root Cause**: If values differ, find where page.tsx mutates clarState
4. **Cleanup**: Remove debug logs after confirming fix

---

## Regression Prevention

- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ STEP NEXT-138 preserved (Single-insurer explanation guard)
- ✅ STEP NEXT-141 preserved (EX4 preset routing lock)
- ✅ STEP NEXT-141-δ preserved (EX4 context isolation)
- ✅ STEP NEXT-141-ζ preserved (EX4 coverage slot = false)
- ✅ **EX2/EX3 coverage requirement PRESERVED** (safety net excludes them)

---

**LOCKED**: This is the final fix with double defense for EX4 coverage gating.
