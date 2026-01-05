# STEP NEXT-141: EX4 Preset Button Routing Lock + Clarification UI Fix

**Date**: 2026-01-05
**Status**: ✅ COMPLETE
**Scope**: Frontend ONLY (apps/web)

---

## 0. Purpose

Fix EX4 preset button ("제자리암, 경계성종양 보장여부 비교해줘") to:
1. **LOCK routing to EX4** (100% confidence, bypass detectExamType heuristics)
2. **Clarification UI shows insurers ONLY** (NO coverage input, disease subtypes already resolved from preset)

**Root Problem**:
- EX4 preset relied on keyword detection ("제자리암", "경계성종양", "보장여부") which could be:
  - Overridden by stronger EX3 signals ("비교")
  - Misrouted to EX1_DETAIL if single insurer detected
- Clarification UI showed "담보와 보험사를 선택해주세요" (wrong for EX4 - disease subtypes already in message)

---

## 1. Constitutional Principles

### 1.1 Preset Button = Explicit Intent (ABSOLUTE)
- **Preset buttons are NOT text to be parsed** - they are explicit UI actions with known intent
- **Preset click = LOCK exam type** (100% confidence, no heuristics)
- **Free-text input ONLY uses detectExamType** (fallback for manual queries)

### 1.2 EX4 Clarification = Insurers ONLY
- EX4 preset text: "제자리암, 경계성종양 보장여부 비교해줘"
- **Disease subtypes already resolved** (제자리암, 경계성종양 parsed from message)
- **Only insurers missing** → clarification asks "비교할 보험사를 선택해주세요" (NO coverage)

### 1.3 Routing Priority (SSOT)
```typescript
Priority 1: draftExamType (preset button)    // STEP NEXT-141
Priority 2: detectExamType(message)           // STEP NEXT-133 (fallback)
```

---

## 2. Implementation

### 2.1 State: draftExamType (apps/web/app/page.tsx)

**Added**:
```typescript
// STEP NEXT-141: Preset exam type lock (preset buttons → force exam type, bypass detectExamType)
const [draftExamType, setDraftExamType] = useState<"EX1_DETAIL" | "EX2" | "EX3" | "EX4" | null>(null);
```

**Reset after send** (prevent contamination):
```typescript
} finally {
  setIsLoading(false);
  // STEP NEXT-141: Reset draftExamType after send (prevent contamination)
  setDraftExamType(null);
}
```

---

### 2.2 Preset Button Click (apps/web/components/ChatPanel.tsx)

**EX4 Preset Button ONLY**:
```tsx
<button
  onClick={() => {
    // STEP NEXT-141: EX4 preset → LOCK exam type to EX4
    onInputChange("제자리암, 경계성종양 보장여부 비교해줘");
    onPresetClick?.("EX4");
  }}
  className="..."
>
  예: 제자리암, 경계성종양 보장여부 비교해줘
</button>
```

**EX2/EX3 Presets** (NO lock - rely on detectExamType):
```tsx
// EX2 preset
onClick={() => {
  onInputChange("암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘");
  // STEP NEXT-141: NO preset lock for EX2 (relies on detectExamType)
}}

// EX3 preset
onClick={() => {
  onInputChange("암진단비 비교해줘");
  // STEP NEXT-141: NO preset lock for EX3 (relies on detectExamType)
}}
```

---

### 2.3 handleSend Routing Override (apps/web/app/page.tsx)

**Override deriveClarificationState result**:
```typescript
// STEP NEXT-141: Priority 1 - draftExamType overrides detectExamType (preset button lock)
const forcedExamType = draftExamType;

if (isInitialEntry) {
  // ... derive clarState ...

  // STEP NEXT-141: Override examType if preset button was used
  if (forcedExamType) {
    console.log("[page.tsx STEP NEXT-141] Forced exam type from preset:", forcedExamType);
    clarState.examType = forcedExamType;
  }
}
```

**Same override in clarification gate UI**:
```typescript
{ex3GateOpen && (() => {
  // ... derive clarState ...

  // STEP NEXT-141: Override examType if preset button was used
  if (forcedExamType) {
    clarState.examType = forcedExamType;
  }
```

---

### 2.4 Clarification UI Fix (apps/web/app/page.tsx)

**Hide coverage input for EX4**:
```tsx
{/* STEP NEXT-133/141: Only show coverage input if missing AND NOT EX4 */}
{/* STEP NEXT-141: EX4 uses disease_subtypes (already resolved from preset), NOT coverage */}
{clarState.missingSlots.coverage && clarState.examType !== "EX4" && (
  <div className="mb-3">
    <div className="text-blue-800 text-xs mb-2">
      담보명
    </div>
    <input ... />
  </div>
)}
```

**Clarification message already correct** (STEP NEXT-133):
```typescript
if (clarState.examType === "EX4") {
  if (clarState.missingSlots.insurers) {
    // STEP NEXT-141: CRITICAL - disease_subtypes already resolved (from preset), only insurers missing
    clarificationMessage = "비교할 보험사를 선택해주세요.";
  }
}
```

---

## 3. Forbidden Patterns

❌ **NO** detectExamType-only routing for preset buttons
❌ **NO** keyword-based preset detection ("if message.includes('제자리암')")
❌ **NO** coverage input UI for EX4 clarification
❌ **NO** "담보와 보험사를 선택해주세요" for EX4 (disease subtypes ≠ coverage)
❌ **NO** draftExamType carryover (must reset after send)

---

## 4. Verification Scenarios

### S1: EX4 Preset LOCK (CRITICAL)
**Input**: Click "제자리암, 경계성종양 보장여부 비교해줘" 10 times
**Expected**: 10/10 route to EX4 (NOT EX3/EX1_DETAIL)
**Verification**: Console log shows `[STEP NEXT-141] Forced exam type from preset: EX4`

### S2: EX4 Clarification UI (CRITICAL)
**Input**: EX4 preset → no insurers selected → send
**Expected**:
- Message: "비교할 보험사를 선택해주세요" (NO "담보와")
- UI: Insurer selection buttons ONLY (NO coverage input field)
**Verification**: Coverage input field `display: none` or not rendered

### S3: Free-text EX4 (Fallback)
**Input**: Manually type "제자리암 경계성종양 보장여부 비교해줘" (NO preset button)
**Expected**: detectExamType detects EX4 (fallback heuristics still work)

### S4: EX2/EX3 Regression
**Input**: Click EX2/EX3 preset buttons
**Expected**: NO draftExamType lock (rely on detectExamType heuristics)
**Verification**: EX2 → "담보 중" detection, EX3 → "비교" detection

### S5: draftExamType Reset
**Input**: EX4 preset → send → new EX2 query
**Expected**: draftExamType = null after first send (NO contamination)
**Verification**: Second query NOT forced to EX4

---

## 5. Definition of Success

> **"EX4 프리셋 버튼 클릭 10/10 → EX4 처리 (EX3/EX1_DETAIL 0%). Clarification에서 담보 입력 요구 0%."**

**Metrics**:
- EX4 preset routing accuracy: 10/10 (100%)
- EX4 clarification coverage UI exposure: 0%
- EX4 clarification copy correctness: "비교할 보험사를 선택해주세요" (NO "담보와")
- EX2/EX3 regression: 0 (no impact)

---

## 6. Git Commit

**Modified Files**:
- `apps/web/app/page.tsx`: draftExamType state + routing override + clarification UI fix
- `apps/web/components/ChatPanel.tsx`: onPresetClick prop + EX4 preset button

**Commit Message**:
```
feat(step-next-141): lock EX4 preset routing + clarification copy

- Add draftExamType state (preset button → force exam type)
- Override detectExamType when preset button clicked
- Hide coverage input for EX4 clarification (insurers ONLY)
- Reset draftExamType after send (prevent contamination)
- EX4 preset: "제자리암, 경계성종양 보장여부 비교해줘" → 100% EX4

DoD: EX4 preset 10/10 → EX4, clarification coverage UI 0%
```

---

## 7. Related Steps

**Prerequisites**:
- STEP NEXT-133: Slot-driven clarification (detectExamType baseline)
- STEP NEXT-138: Single-insurer explanation guard (EX1_DETAIL detection)

**Preserved**:
- STEP NEXT-129R: Customer self-test flow (NO auto-send, NO silent correction)
- STEP NEXT-A: Unified exam entry UX
- STEP NEXT-133: Slot-driven clarification (free-text fallback)

**Follow-up** (if needed):
- STEP NEXT-142: EX2/EX3 preset locks (if heuristics fail in testing)
- STEP NEXT-143: Disease subtype UI selector (if manual input needed)
