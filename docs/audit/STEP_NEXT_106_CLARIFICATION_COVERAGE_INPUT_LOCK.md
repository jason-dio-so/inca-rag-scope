# STEP NEXT-106 — Clarification 상태 UI Lock (담보명 입력 Disable)

**Date**: 2026-01-03
**Scope**: Frontend View Layer ONLY
**Files Modified**: 2
**Tests**: Manual QA (demo flow)

---

## 1. Purpose (Why)

### Problem Statement

When LIMIT_FIND clarification occurs (보험사 추가 필요), the UI shows:
- Top context box (현재 대화 조건)
- Clarification panel (보험사를 선택하세요)
- **ENABLED coverage input field** ← Problem

This causes customer confusion:
- "담보를 다시 입력해야 하나?"
- "기존 맥락이 초기화된 건가?"
- "암진단비야? 암직접입원비야?"

This breaks the natural question continuity built in STEP NEXT-102/104:
**EX2_DETAIL → 메리츠는? → LIMIT_FIND**

---

## 2. Constitutional UX Rule

> **Clarification = Single Action Only**
>
> During clarification, leave ONLY the action the customer must perform.
> Lock all other input elements.

In STEP NEXT-106, the target is **coverage input field**.

---

## 3. Scope

- ✅ Frontend View Layer ONLY
- ❌ NO Backend / API / Intent Router / Composer changes
- ✅ EX2_LIMIT_FIND Clarification UX enhancement

---

## 4. Implementation

### 4.1 Condition (WHEN)

Coverage input is disabled when:

```typescript
isLimitFindPattern(utterance) === true
&& insurers.length < 2
```

i.e., LIMIT_FIND pattern detected BUT insufficient insurers (<2).

---

### 4.2 Coverage Input Field Lock (Required)

**Before** (Problem):
- Coverage input: **enabled**
- Customer tries to modify coverage unnecessarily

**After** (Fixed):
- Coverage input:
  - `disabled = true`
  - Gray background (`bg-gray-100`)
  - Gray text (`text-gray-500`)
  - Cursor blocked (`cursor-not-allowed`)

**Placeholder Text** (Fixed):

```
비교를 위해 보험사만 추가해주세요
```

⚠️ **Visual clarity**: Coverage name is LOCKED during clarification.

---

### 4.3 Context Box Consistency

Top context box shows:

```
현재 대화 조건:
- 보험사: 메리츠화재
- 담보: 암직접입원비

※ 비교를 위해 보험사 1곳을 추가해주세요
```

- Insurer selector: `disabled`
- Coverage input: `disabled`
- "조건 변경" button: enabled (explicit reset option)

---

### 4.4 Recovery After Clarification

After insurer selection → EX2_LIMIT_FIND success:
- Coverage input → `enabled`
- Insurer selector → `enabled`
- Clarification panel → removed
- Flow returns to normal

---

## 5. Prohibited Behaviors (Explicit NO)

❌ NO coverage name re-input during clarification
❌ NO automatic coverage modification
❌ NO multiple inputs during clarification
❌ NO impact on existing EX2 / EX3 / EX4 Intents

---

## 6. Validation Scenario (QA)

### Demo Flow

1. **EX2_DETAIL** (삼성 암진단비)
   → Response shows followup hints

2. **"메리츠는?"**
   → Insurer switch → EX2_DETAIL (meritz)

3. **"암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"**
   → LIMIT_FIND pattern detected
   → 1 insurer only (meritz)
   → Clarification panel appears

4. **Check UI State**:
   ✅ Coverage input: **disabled** (gray, cursor blocked)
   ✅ Placeholder: "비교를 위해 보험사만 추가해주세요"
   ✅ Insurer buttons: clickable

5. **Select insurer** (e.g., samsung)
   → Auto-resend with merged insurers (samsung + meritz)

6. **EX2_LIMIT_FIND table output**
   → Coverage input: **enabled** (automatically restored)

---

## 7. Constitutional Guarantees

✅ NO Business Logic change
✅ NO Intent routing change
✅ NO API / Payload change
✅ View Layer UX Lock ONLY
✅ Context Integrity strengthened

---

## 8. Code Changes

### 8.1 ChatPanel.tsx

**Added**:
- `coverageInputDisabled?: boolean` prop (default: `false`)
- Conditional `disabled` attribute on coverage input
- Conditional placeholder text
- Conditional CSS classes (`bg-gray-100 text-gray-500 cursor-not-allowed`)

**Lines Modified**: 3 locations
1. Props interface (line 23)
2. Function params (line 38)
3. Input element (lines 277-288)

---

### 8.2 page.tsx

**Added**:
- `isLimitFindClarification` state (boolean, default: `false`)
- Set `true` when LIMIT_FIND pattern + <2 insurers (line 300)
- Set `false` when clarification completes (line 451)
- Pass to `ChatPanel` as `coverageInputDisabled` prop (line 557)

**Lines Modified**: 4 locations
1. State declaration (line 50)
2. LIMIT_FIND detection (line 300)
3. Clarification handler (line 451)
4. ChatPanel props (line 557)

---

## 9. Definition of Done (DoD)

✅ Coverage input **disabled** during LIMIT_FIND clarification
✅ Customer does NOT ask "담보를 다시 써야 하나요?"
✅ Customer focus: **insurer selection ONLY**
✅ EX2 → 전환 → LIMIT_FIND demo flow: **seamless** (no breaks)

---

## 10. Final Statement

> **Clarification is NOT about asking more questions.**
> **Clarification is about guiding the NEXT SINGLE ACTION.**
> Therefore, coverage input MUST be locked.

---

**Constitutional Lock**: ✅ STEP NEXT-106 Complete
**View Layer**: UI state management ONLY
**Business Logic**: NO changes
**Intent Routing**: NO changes
**Demo Flow**: EX2 → 전환 → LIMIT_FIND continuity preserved
