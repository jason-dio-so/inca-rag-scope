# STEP NEXT-A-α: EX1 Simplified Example Text (NO Insurer Names)

**Date**: 2026-01-04
**Purpose**: Remove insurer names from EX1 example text to avoid premature decision-making
**Constitutional Basis**: STEP NEXT-A (Unified Exam Entry UX)
**Scope**: View layer text ONLY (Frontend)

---

## 0. Purpose

**Core Problem**:
- EX1 example text included insurer names: "삼성화재와 메리츠화재 암진단비 비교해줘"
- This made users think insurers were **pre-decided** (fixed choice)
- User didn't realize they could **choose any insurers** in next step
- Created UX debt for multi-insurer expansion (bound to 2 specific insurers)

**Solution**:
- Simplify EX1 example to: "암진단비 비교해줘" (NO insurer names)
- User focuses on **WHAT** to compare (coverage) in EX1
- User chooses **WHO** to compare (insurers) in next step (unified entry gate)
- Clear separation of concerns across UX steps

---

## 1. Constitutional Principles (ABSOLUTE)

✅ **EX1 = "WHAT"**: First screen asks user WHAT to compare (coverage)
✅ **Entry Gate = "WHO"**: Next step asks user WHO to compare (insurers)
✅ **NO insurer names in EX1**: Zero mentions of specific insurers on first screen
✅ **Natural flow**: Question → Selection → Results (step-by-step)
✅ **Expansion-ready**: Not bound to 2 specific insurers

❌ **FORBIDDEN**:
- Insurer names in EX1 example buttons
- Insurer names in EX1 placeholder text
- Any pre-commitment to specific insurers in first screen
- "삼성/메리츠 기준 예시" language

---

## 2. Problem Definition

**Before** (❌):
```
예: 삼성화재와 메리츠화재 암진단비 비교해줘
```

**Issues**:
1. User thinks: "Oh, this is Samsung vs Meritz comparison ONLY"
2. User doesn't realize they can choose other insurers
3. UX debt: If we add 3rd insurer, this text becomes misleading
4. Flow confusion: "Why am I selecting insurers again if they're already in the example?"

**After** (✅):
```
예: 암진단비 비교해줘
```

**Benefits**:
1. User thinks: "I want to compare 암진단비 coverage"
2. System asks: "Which insurers?" → User chooses explicitly
3. Expansion-ready: Works for 2, 3, 4+ insurers
4. Clear flow: Question (EX1) → Selection (Gate) → Results (Composer)

---

## 3. Implementation Scope

**Modified Files**:
- `apps/web/components/ChatPanel.tsx` (2 changes: example button + placeholder)

**Backend Changes**: ❌ NONE (text-only change)

**Key Insight**:
> "EX1 is about **starting**, not **deciding**. User decides insurers in the next step."

---

## 4. Changed Text (LOCKED)

### Change 1: Example Button Text

**Before**:
```typescript
onInputChange("삼성화재와 메리츠화재 암진단비 비교해줘");
```
```
예: 삼성화재와 메리츠화재 암진단비 비교해줘
```

**After**:
```typescript
onInputChange("암진단비 비교해줘");
```
```
예: 암진단비 비교해줘
```

### Change 2: Placeholder Text

**Before**:
```
placeholder="예: 삼성화재와 메리츠화재 암진단비 비교해줘"
```

**After**:
```
placeholder="예: 암진단비 비교해줘"
```

---

## 5. Processing Flow (Intended UX)

### Flow: EX1 → EX3 (Comparison)

1. **User sees EX1 first screen**:
   - Example button: "예: 암진단비 비교해줘"
   - Placeholder: "예: 암진단비 비교해줘"
   - **NO insurer names visible** ✅

2. **User clicks example button** (or types similar question):
   - Input filled: "암진단비 비교해줘"
   - **NO auto-send** (129R compliant) ✅

3. **User clicks "전송"**:
   - `isInitialEntry = true` (first message)
   - `isEX3Intent = true` (contains "비교")
   - Requirements check: insurers.length >= 2? → **NO (0 insurers)** ✅
   - **Unified entry gate opens** (STEP NEXT-A) ✅

4. **System shows entry gate**:
   - Message: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
   - Panel: "비교할 보험사 (2개 선택)" + "담보명 (1개)"
   - User explicitly selects insurers ✅

5. **User selects insurers + clicks "비교 시작"**:
   - `/chat` called with kind: "EX3_COMPARE", insurers, coverage_names
   - EX3_COMPARE table displayed ✅

**Result**: Natural, step-by-step flow with NO premature decisions.

---

## 6. Forbidden Actions (ABSOLUTE)

❌ **NO insurer names in EX1** (삼성화재, 메리츠화재, KB손해보험, etc.)
❌ **NO "삼성/메리츠 기준 예시"** language
❌ **NO auto-filling insurers** based on example text
❌ **NO pre-commitment** to specific insurers in first screen

---

## 7. Verification Scenarios

### CHECK-Aα-1: EX1 First Screen (Visual Inspection)

**Input**: Open first screen (EX1)
**Expected**:
- Example button text: "예: 암진단비 비교해줘" ✅
- Placeholder text: "예: 암진단비 비교해줘" ✅
- **NO insurer names visible anywhere on screen** ✅

### CHECK-Aα-2: EX1 → Entry Gate Flow

**Input**: Click "예: 암진단비 비교해줘" → "전송"
**Expected**:
- User message: "암진단비 비교해줘"
- System message: "추가 정보가 필요합니다..." ✅
- Gate panel shows: "비교할 보험사 (2개 선택)" ✅
- User selects insurers explicitly ✅

### CHECK-Aα-3: Expansion Readiness

**Input**: Add 3rd insurer (e.g., KB손해보험) to system
**Expected**:
- EX1 text unchanged ("암진단비 비교해줘") ✅
- Entry gate shows 3 insurer options ✅
- **NO text change needed** ✅

---

## 8. Test/Documentation/Git

**Documentation**:
- This file: `docs/audit/STEP_NEXT_A_ALPHA_EX1_SIMPLIFIED_TEXT_LOCK.md`
- Includes: Purpose, rationale, flow, verification

**Testing**:
- Visual inspection (EX1 first screen)
- Manual flow test (EX1 → Entry Gate → Selection)

**Git**:
- Branch: feat/step-next-14-chat-ui (preserved)
- Commit message: `feat(step-next-a-alpha): simplify EX1 example text (remove insurer names)`
- CLAUDE.md: Add STEP NEXT-A-α section

---

## 9. Definition of Done

✅ **EX1 screen has ZERO insurer names** (no "삼성화재", "메리츠화재", etc.)
✅ **Example button text**: "예: 암진단비 비교해줘" (simplified)
✅ **Placeholder text**: "예: 암진단비 비교해줘" (simplified)
✅ **Flow works**: EX1 → Entry Gate → Insurer Selection → Results (natural progression)
✅ **Expansion-ready**: Adding 3rd insurer requires NO text changes

---

## 10. Key Insights

**Design Philosophy**:
> "EX1 is the **question**, not the **answer**. User asks WHAT to compare. System asks WHO to compare. Separation of concerns."

**UX Principle**:
> "First screen sets the topic. Next screen sets the scope. Don't conflate them."

**STEP NEXT-A Compliance**:
- STEP NEXT-A: Unified entry gate for all exam types
- STEP NEXT-A-α: Simplified entry question (NO insurers in EX1)
- Together: Natural "Question → Selection → Results" flow

**Relationship to STEP NEXT-A**:
- STEP NEXT-A: Unifies entry **gate** (same message for all exams)
- STEP NEXT-A-α: Simplifies entry **question** (remove insurers from EX1 text)
- Both work together to create predictable, expansion-ready UX

---

## 11. Example User Journey

**Before** (with insurer names):
1. User sees: "예: 삼성화재와 메리츠화재 암진단비 비교해줘"
2. User thinks: "Ah, this compares Samsung vs Meritz"
3. User clicks → System asks: "비교할 보험사를 선택해주세요"
4. User confused: "Wait, why am I selecting insurers again?"

**After** (without insurer names):
1. User sees: "예: 암진단비 비교해줘"
2. User thinks: "I want to compare 암진단비 coverage"
3. User clicks → System asks: "비교할 보험사를 선택해주세요"
4. User understands: "Ah, now I choose which insurers to compare" ✅

---

**FINAL LOCK**: This is the EX1 simplified text SSOT. NO insurer names allowed in EX1 screen. Any changes require new STEP number + user testing evidence.
