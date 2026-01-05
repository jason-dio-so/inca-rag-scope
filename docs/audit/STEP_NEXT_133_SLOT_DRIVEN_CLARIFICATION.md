# STEP NEXT-133: Slot-Driven Clarification UI — SSOT

**Date**: 2026-01-04
**Supersedes**: STEP NEXT-A (Unified Exam Entry — extended with slot-driven logic)
**Scope**: Frontend ONLY (apps/web)
**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)

---

## Purpose

Fix clarification UI to be **slot-driven** instead of showing a fixed form, preventing re-asking for already resolved slots (especially coverage).

**Root Cause**:
- Current bug: Coverage already resolved ("암진단비 비교해줘") → clarification UI still shows coverage input
- Hardcoded text: "(2개 선택)" assumes current 2-insurer limitation
- Fixed form approach: Always shows all slots regardless of what's already known

**Solution**:
- **Missing-slot detection**: Derive which slots are resolved vs missing
- **Dynamic UI**: Only show UI for missing slots
- **No hardcoded count**: Remove "(2개 선택)" text (keep validation internal)

---

## Constitutional Principles (ABSOLUTE)

1. **Resolved Slot Non-Reask** (절대 원칙)
   - If a slot is resolved (from payload/context/parsing), NEVER show UI for it
   - Example: Coverage = "암진단비" → NO coverage input field shown

2. **Clarification UI = Dynamic Panel** (not fixed form)
   - Only render UI for `missingSlots` fields
   - Empty clarification → No panel shown

3. **No Hardcoded Insurer Count Text**
   - Remove "(2개 선택)" from UI text
   - Validation: Internal only (2 for EX3, 1+ for EX2/EX4)
   - Future-proof for N-insurer expansion

4. **Unified Logic for EX1→EX2/EX3/EX4**
   - Same slot-driven approach for all exam entry flows
   - Exam type determines required slots (not UI rendering)

5. **No Demo Auto-Complete** (STEP NEXT-129R preserved)
   - ❌ NO auto-send on button clicks
   - ❌ NO silent payload correction
   - ❌ NO forced routing

---

## Implementation

### 1. Utility Function: `deriveClarificationState()`

**File**: `apps/web/lib/clarificationUtils.ts` (NEW)

**Input**:
```typescript
{
  requestPayload: { insurers?, coverage_names?, disease_name?, message? },
  lastResponseVm?: AssistantMessageVM | null,
  lastUserText: string,
  conversationContext?: { lockedInsurers, lockedCoverageNames }
}
```

**Output**:
```typescript
{
  showClarification: boolean,
  missingSlots: { insurers: boolean, coverage: boolean, disease_subtypes: boolean },
  resolvedSlots: { insurers: string[] | null, coverage: string[] | null, disease_subtypes: string[] | null },
  examType: "EX2" | "EX3" | "EX4" | null
}
```

**Resolution Priority**:
1. `requestPayload` (current user input/selection)
2. `conversationContext` (locked values from previous turns)
3. `lastUserText` (parsed coverage/disease keywords)

**Exam Type Detection** (deterministic):
- EX2: `담보 중` OR `보장한도가 다른`
- EX3: `비교` OR `차이` OR `VS` OR `vs`
- EX4: `보장여부` OR `보장내용에 따라` OR `제자리암` OR `경계성종양`

**Missing Slot Logic**:
- **EX3**: Requires 2 insurers + 1 coverage
- **EX2**: Requires 1+ insurers + 1 coverage
- **EX4**: Requires 1+ insurers + disease subtypes

---

### 2. Frontend Changes: `apps/web/app/page.tsx`

#### 2.1 EX1 Entry Logic (handleSend)

**Before** (STEP NEXT-A):
- Fixed gate for all exam types
- Always showed both insurers + coverage UI
- Hardcoded "(2개 선택)" text

**After** (STEP NEXT-133):
```typescript
const clarState = deriveClarificationState({
  requestPayload: draftPayload,
  lastResponseVm: null,
  lastUserText: messageToSend,
  conversationContext,
});

if (clarState.showClarification && clarState.examType) {
  // Adaptive message based on missing slots
  let clarificationMessage = "추가 정보가 필요합니다.";
  if (clarState.missingSlots.coverage && clarState.missingSlots.insurers) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요.";
  } else if (clarState.missingSlots.coverage) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 담보를 입력해주세요.";
  } else if (clarState.missingSlots.insurers) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 보험사를 선택해주세요.";
  }
  // ... open gate
}
```

#### 2.2 Clarification Gate UI

**Before** (STEP NEXT-A):
- Always showed insurer selection: "비교할 보험사 (2개 선택)"
- Always showed coverage input: "담보명 (1개)"
- Fixed form structure

**After** (STEP NEXT-133):
```typescript
{ex3GateOpen && (() => {
  const clarState = deriveClarificationState({ ... });

  return (
    <div>
      {/* Only show if missing */}
      {clarState.missingSlots.insurers && (
        <div>보험사 선택</div>  {/* NO "(2개 선택)" */}
      )}

      {/* Only show if missing */}
      {clarState.missingSlots.coverage && (
        <div>담보명</div>
      )}

      <button disabled={...}>확인</button>  {/* NO count in text */}
    </div>
  );
})()}
```

**Text Changes**:
- ❌ REMOVED: "비교할 보험사 (2개 선택)"
- ✅ NEW: "보험사 선택" (no count)
- ❌ REMOVED: "담보명 (1개)"
- ✅ NEW: "담보명" (no count)
- ❌ REMOVED: "비교 시작 (N/2개 보험사, ...)"
- ✅ NEW: "확인" (simple text)

---

## Verification Scenarios (DoD)

### CHECK-EX3-CLARIFY-1: Coverage Resolved → Insurers Only

**Steps**:
1. User: "암진단비 비교해줘" (EX1 button)
2. System parses coverage = "암진단비" (resolved)
3. Clarification UI opens

**Expected**:
- ✅ Assistant message: "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요."
- ✅ Clarification panel shows: **보험사 선택 ONLY**
- ❌ Coverage input field: **NOT shown** (0% exposure)
- ✅ Text: "보험사 선택" (NO "(2개 선택)")

**Bug If**:
- ❌ Coverage input shown despite coverage = "암진단비" already parsed
- ❌ Text shows "(2개 선택)"

---

### CHECK-EX3-CLARIFY-2: Submit After Selection

**Steps**:
1. (Following CHECK-EX3-CLARIFY-1)
2. User selects 2 insurers (삼성화재, 메리츠화재)
3. User clicks "확인"

**Expected**:
- ✅ Clarification panel closes
- ✅ EX3_COMPARE request sent with insurers=["samsung", "meritz"], coverage_names=["암진단비"]
- ✅ EX3 결과 표시 (normal flow)
- ❌ NO additional clarification (0% re-ask)

---

### CHECK-EX4-MULTI-SUBTYPE-1: Multiple Disease Subtypes

**Steps**:
1. User: "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘"
2. System parses subtypes = ["제자리암", "경계성종양"], insurers = 2

**Expected**:
- ✅ NO clarification (all slots resolved)
- ✅ Result screen shows: **제자리암 + 경계성종양** (2 tables or 2 sections)
- ❌ Single subtype only: **0% occurrence**

---

### CHECK-EX2-NO-REASK-1: Coverage Parsed → Insurers Only

**Steps**:
1. User: "암직접입원비 보장한도 비교해줘"
2. System parses coverage = "암직접입원비" (resolved)

**Expected**:
- ✅ Clarification message: "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요."
- ✅ Clarification panel: **보험사 선택 ONLY**
- ❌ Coverage input: **NOT shown** (0% exposure)

**Bug If**:
- ❌ Coverage input shown despite "암직접입원비" parsed
- ❌ User asked to re-enter coverage

---

## Forbidden Behaviors (ABSOLUTE)

❌ **NO re-ask for resolved slots**
- If coverage resolved → coverage UI NEVER shown
- If insurers resolved → insurers UI NEVER shown

❌ **NO hardcoded insurer count text**
- "(2개 선택)" → FORBIDDEN
- "(1개 이상)" → FORBIDDEN
- Validation is internal only

❌ **NO auto-send / auto-routing / silent correction**
- Button clicks fill input ONLY (STEP NEXT-129R preserved)
- NO forced EX3 routing
- NO payload extraction from message

❌ **NO backend changes**
- apps/api/** → UNTOUCHED
- Intent router → UNCHANGED
- Composers → UNCHANGED

---

## Files Modified

1. **NEW**: `apps/web/lib/clarificationUtils.ts`
   - `deriveClarificationState()` function
   - Exam type detection (deterministic)
   - Coverage/subtype parsing (simple keyword matching)

2. **MODIFIED**: `apps/web/app/page.tsx`
   - Import `deriveClarificationState`
   - Replace EX1 entry gate logic with slot-driven approach
   - Replace clarification gate UI with dynamic rendering (missing slots only)
   - Remove hardcoded "(2개 선택)" / "(1개)" text

---

## Definition of Success

> **"Coverage가 resolved된 케이스에서 담보 선택 UI 노출 0%"**

Specific:
- ✅ EX1 → EX3: "암진단비 비교해줘" → 보험사 선택 ONLY
- ✅ Clarification UI text: NO "(2개 선택)" (expansion-ready)
- ✅ EX4 multi-subtype: ["제자리암", "경계성종양"] → both shown
- ❌ Auto-send / forced routing / silent correction: 0%

---

## Future Extension

**Multi-Insurer Support** (N insurers):
- Current: 2 for EX3, 1+ for EX2/EX4 (internal validation)
- Future: Remove 2-insurer limit → same UI, no text changes needed
- UI already says "보험사 선택" (not "2개")

**Additional Slots** (e.g., age, region):
- Add to `MissingSlots` / `ResolvedSlots` types
- `deriveClarificationState()` detects new slots
- Clarification UI conditionally renders new fields
- NO structural changes required

---

## Regression Prevention

✅ **STEP NEXT-129R preserved**: NO auto-send, NO silent correction, NO forced routing
✅ **STEP NEXT-A preserved**: Unified exam entry UX (same message for all exams)
✅ **STEP NEXT-102 preserved**: Insurer switch detection (메리츠는?)
✅ **STEP NEXT-106 preserved**: Multi-select insurers for LIMIT_FIND

---

## Build Status

✅ TypeScript compilation: SUCCESS
✅ Next.js Turbopack: ✓ Compiled in 16ms
✅ Dev server: http://localhost:3000

---

**LOCKED**: 2026-01-04
**Next STEP**: Manual testing of CHECK scenarios + STATUS.md update
