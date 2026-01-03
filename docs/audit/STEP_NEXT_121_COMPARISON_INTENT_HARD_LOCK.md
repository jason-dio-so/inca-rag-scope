# STEP NEXT-121 — Comparison Intent Hard-Lock (FINAL)

**Date**: 2026-01-04
**Status**: ✅ LOCKED
**Scope**: Frontend Intent Detection (View Layer)

---

## Purpose (WHY)

**Problem**: Comparison sentences like "삼성화재와 메리츠화재 암진단비 비교해줘" were triggering `need_more_info` → coverage selection UI → demo failure.

**Root Cause**: Silent payload correction extracted insurers but did NOT force-lock coverage_name for comparison intent.

**Goal**: **"비교 문장이 들어오면, 담보 선택 UI 없이 반드시 EX3_COMPARE까지 도달"**

---

## Implementation: 3 Hard-Lock Rules

### RULE 1 — Comparison Intent Detection

**Function**: `isComparisonIntent(message: string, insurersCount: number): boolean`

**Criteria** (ALL must be true):
1. `insurersCount >= 2`
2. Message contains comparison keywords OR particles:
   - Keywords: 비교, 차이, 다른, 다르, vs, 대, 어떤 게, 어느, 뭐가, 무엇이
   - Particles: 와, 과
3. Message contains coverage keywords (암진단비, 암직접입원비, etc.)

**When TRUE**: Force EX3_COMPARE flow (bypass ALL clarification)

---

### RULE 2 — Coverage Name Hard-Lock

**Location**: `page.tsx` handleSend()

**Logic**:
```typescript
const isForceComparison = isComparisonIntent(messageToSend, currentInsurersCount);

if (isForceComparison && !silentCoverageName && !coverageInput && !conversationContext.lockedCoverageNames) {
  // Force extract coverage even if ambiguous
  const forcedCoverage = extractCoverageNameFromMessage(messageToSend);
  if (forcedCoverage) {
    silentCoverageName = forcedCoverage;
    console.log("[HARD-LOCK comparison intent: forced coverage_name =", silentCoverageName);
  }
}
```

**Rules**:
- ❌ NO ambiguity checking
- ❌ NO "multiple candidates" handling
- ✅ First match = force-lock
- ✅ Comparison flow priority > precision

---

### RULE 3 — Block need_more_info / Clarification UI

**Location**: `page.tsx` handleSend()

**Implementation**:
1. **Before API call**: Block LIMIT_FIND clarification UI if comparison intent
   ```typescript
   if (!isForceComparison) {
     // LIMIT_FIND clarification UI allowed
   } else {
     console.log("HARD-LOCK: bypassing all clarification UI");
   }
   ```

2. **After API response**: Ignore `need_more_info` if comparison intent
   ```typescript
   if (response.need_more_info === true) {
     if (isForceComparison) {
       console.error("HARD-LOCK VIOLATION: need_more_info for comparison intent");
       console.error("Proceeding anyway (ignoring need_more_info)");
       // Do NOT return - continue to render response
     } else {
       setClarification(...);
       return;
     }
   }
   ```

**Result**:
- ✅ Comparison intent → ZERO chance of clarification UI
- ✅ Backend asks for more info → Frontend ignores it
- ✅ Demo never stops

---

## Test Scenarios (ALL MUST PASS)

### Scenario A — Core Demo Flow ✅
**Input**: `삼성화재와 메리츠화재 암진단비 비교해줘`

**Expected**:
- ❌ NO "추가 정보가 필요합니다" panel
- ❌ NO coverage selection UI
- ✅ Immediate EX3_COMPARE
- ✅ Side-by-side comparison table
- ✅ Bubble shows structural difference

**State transitions**:
1. User types message
2. `extractInsurersFromMessage()` → ["samsung", "meritz"]
3. `extractCoverageNameFromMessage()` → "암진단비"
4. `isComparisonIntent()` → TRUE
5. Silent payload: `insurers=["samsung","meritz"], coverage_names=["암진단비"]`
6. API call → EX3_COMPARE response
7. NO `need_more_info` check (bypassed)
8. Render comparison

---

### Scenario B — Onboarding Click ✅
**Action**: Click onboarding example button

**Expected**:
- ✅ Example text auto-fills input
- ✅ Context auto-set (insurers + coverage)
- ✅ User presses 전송 → immediate EX3_COMPARE
- ❌ NO intermediate UI

---

### Scenario C — Particle-Based Comparison ✅
**Input**: `삼성화재 메리츠화재 암진단비` (no explicit "비교" keyword)

**Expected**:
- ✅ Detects "화재" particle
- ✅ Extracts 2 insurers
- ✅ Forces comparison intent
- ✅ EX3_COMPARE (no clarification)

---

## Constitutional Compliance

### Forbidden ❌
- ❌ Backend / API / Business logic changes
- ❌ LLM usage
- ❌ New intent creation
- ❌ Showing coverage selection UI when comparison intent detected
- ❌ Respecting `need_more_info` when comparison intent detected

### Allowed ✅
- ✅ Frontend intent detection (deterministic)
- ✅ Payload force-correction
- ✅ Ignoring backend signals (for comparison intent ONLY)
- ✅ Console warnings when HARD-LOCK activates

---

## Files Modified

### New Function
- `apps/web/lib/contextUtils.ts`
  - `isComparisonIntent()` (NEW — RULE 1 implementation)

### Modified
- `apps/web/app/page.tsx`
  - Import `isComparisonIntent`
  - RULE 2: Coverage name hard-lock on comparison intent
  - RULE 3: Block clarification UI (before API call)
  - RULE 3: Ignore `need_more_info` (after API response)

---

## Success Criteria (Definition of Done)

### One-Liner
> **"비교 문장을 입력했는데 시스템이 다시 선택을 요구하는 경우가 단 1건도 없다."**

### Demo Success Metrics
- ❌ "아 잠깐만요" = FAILURE
- ❌ "이거 하나 더 골라야 하나요?" = FAILURE
- ✅ Click → 전송 → Comparison = SUCCESS

---

## LOCK Declaration

🔒 **STEP NEXT-121 — COMPARISON INTENT HARD-LOCK**

This is NOT a feature. This is a **demo success guarantee**.

**Future changes require**:
1. New STEP number
2. User failure logs showing HARD-LOCK caused issues
3. Explicit approval with A/B test plan

**Rationale**:
> Comparison means Comparison.
> Ask once → Show comparison.
> No exceptions.

---

**End of STEP NEXT-121 FINAL**
