# STEP NEXT-115 / 116 — EX2→EX3 Flow Completion + Structural Summary Lock

**Date**: 2026-01-04
**Status**: ✅ COMPLETE
**Scope**: View Layer ONLY (UX Flow + Panel Summary)

---

## 0. Purpose

Before STEP NEXT-115/116, the system had:
- ✅ Perfect data structure (KPI, refs, deterministic)
- ✅ Clean ChatGPT UI (STEP NEXT-113, 114B)
- ❌ Missing: "Why should I compare?" (EX2 → EX3 transition)
- ❌ Missing: "What's the core difference?" (EX3 table interpretation)

**Goal**: Complete the conversation flow so users naturally understand next steps.

> "말풍선만 읽어도 흐름이 이해되고, 표를 보면 차이가 즉시 각인되게 만든다."

---

## 1. Problem Statement

### STEP NEXT-115 Problem
**EX2_DETAIL (설명)**: Users get explanation, but don't know why comparison matters.

**Current**:
- "이 담보는 암진단비에 해당할 때 보장합니다."
- "정액으로 3000만원을 지급하는 방식입니다."
- [END] → User thinks: "Okay, got it. What now?"

**Missing**: Bridge to comparison action.

### STEP NEXT-116 Problem
**EX3_COMPARE (비교)**: Users see table, but struggle with "So what?"

**Current**:
- Title: "삼성화재 vs 메리츠화재 암진단비 비교"
- [Immediately shows table with rows/columns]
- User thinks: "Lots of data. What should I focus on?"

**Missing**: Structural framework before details.

---

## 2. STEP NEXT-115: EX2→EX3 Comparison Transition Line

### What Changed

**Added 1 line** to EX2_DETAIL bubble_markdown (before question hints):

```markdown
같은 {담보명}라도 보험사마다 '보장을 정의하는 기준'이 달라,
비교해 보면 구조 차이가 더 분명해집니다.
```

### Why This Works

1. **No recommendation**: Just explains comparison value
2. **Neutral tone**: "~해집니다" (informative, not directive)
3. **Structural focus**: "보장을 정의하는 기준" (not price/benefit)
4. **Natural bridge**: Links explanation → comparison without forcing

### Implementation

**File**: `apps/api/response_composers/ex2_detail_composer.py`

**Location**: After condition note, before question hints

```python
# STEP NEXT-115: Comparison transition line (EX2 → EX3 flow)
# This line naturally guides users toward comparison without recommendation
lines.append(f"같은 {display_name}라도 보험사마다 '보장을 정의하는 기준'이 달라,")
lines.append("비교해 보면 구조 차이가 더 분명해집니다.\n")
```

### Rules

- ❌ NO judgment ("더 좋다", "유리하다")
- ❌ NO recommendation ("~하세요", "~해야 합니다")
- ❌ NO specific numbers/values
- ❌ NO comparison results preview
- ❌ NO LLM usage
- ✅ Explains WHY comparison is valuable
- ✅ Neutral, informative tone
- ✅ Appears after main content, before hints
- ✅ Deterministic only

---

## 3. STEP NEXT-116: EX3 Structural Comparison Summary

### What Changed

**Added `structural_summary` field** to EX3_COMPARE response:

1. **Backend**: Compose structural summary (deterministic)
2. **Frontend**: Display at top of ResultDock (before table)

### Summary Template

```
이 비교에서는 {보험사1}는 '{구조1}'이고,
{보험사2}는 '{구조2}'입니다.
```

**Example**:
```
이 비교에서는 삼성화재는 '정액 지급 방식'이고,
메리츠화재는 '지급 한도 기준'입니다.
```

### Structural Basis Detection (Deterministic)

```python
def get_definition_basis(amount, limit, payment):
    if amount != "명시 없음":
        return "정액 지급 방식"
    elif limit:
        return "지급 한도 기준"
    elif payment != "UNKNOWN":
        return f"{payment} 방식"
    else:
        return "기본 보장 방식"
```

**Priority**:
1. Amount (보장금액) → "정액 지급 방식"
2. Limit summary → "지급 한도 기준"
3. Payment type → "{type} 방식"
4. Fallback → "기본 보장 방식"

### Implementation

#### Backend: `ex3_compare_composer.py`

```python
# STEP NEXT-116: Build structural comparison summary
if basis1 == basis2:
    structural_summary_panel = f"이 비교에서는 {insurer1_display}와 {insurer2_display} 모두 {basis1}으로 보장이 정의된 구조입니다."
else:
    structural_summary_panel = (
        f"이 비교에서는 {insurer1_display}는 '{basis1}'이고, "
        f"{insurer2_display}는 '{basis2}'입니다."
    )

# Add to response
response = {
    ...
    "structural_summary": structural_summary_panel,  # STEP NEXT-116
    ...
}
```

#### Frontend: `ResultDock.tsx`

```tsx
{/* STEP NEXT-116: Structural Comparison Summary (EX3_COMPARE only) */}
{response.kind === "EX3_COMPARE" && (response as any).structural_summary && (
  <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 -mt-2">
    <p className="text-xs text-blue-900 leading-relaxed">
      {(response as any).structural_summary}
    </p>
  </div>
)}
```

### Frontend Styling

- **Background**: bg-blue-50 (light blue, subtle)
- **Border**: border-blue-100
- **Text**: text-xs, text-blue-900
- **Padding**: p-3
- **Margin**: -mt-2 (visually connected to title section)
- **Location**: Between title section and table sections

### Rules

- ❌ NO "일부 보험사는..." (vague, abstract language)
- ❌ NO recommendation / superiority judgment
- ❌ NO specific numbers (3천만원, 1회 etc.)
- ❌ NO vertical card layout (one insurer per card)
- ❌ NO LLM usage
- ✅ Explicit insurer names (삼성화재, 메리츠화재)
- ✅ Structural description ONLY
- ✅ Appears BEFORE detailed table
- ✅ Deterministic only

---

## 4. UX Flow (Before & After)

### Before STEP NEXT-115/116

**EX2 Flow**:
1. User asks: "삼성화재 암진단비 설명해줘"
2. Gets: Explanation bubble
3. Thinks: "Okay, got it. [closes]"
4. Missing: Why compare?

**EX3 Flow**:
1. User asks: "삼성화재와 메리츠화재 암진단비 비교해줘"
2. Gets: Table with lots of rows
3. Thinks: "What am I looking for?"
4. Missing: Structural framework

### After STEP NEXT-115/116

**EX2 Flow** (115):
1. User asks: "삼성화재 암진단비 설명해줘"
2. Gets: Explanation bubble
3. Reads transition: "보험사마다 보장 정의 기준이 달라, 비교해 보면 구조 차이가 더 분명해집니다"
4. Thinks: "Ah, I should compare to see structural differences"
5. Naturally asks: "메리츠는?" or "비교해줘"

**EX3 Flow** (116):
1. User asks: "삼성화재와 메리츠화재 암진단비 비교해줘"
2. Sees structural summary first: "삼성화재는 '정액 지급 방식'이고, 메리츠화재는 '지급 한도 기준'입니다"
3. Thinks: "Ah, they define coverage differently. Let me see details."
4. Looks at table with context: Focus on structural difference
5. Understands: Core difference is clear before diving into numbers

---

## 5. Technical Details

### Modified Files

1. **`apps/api/response_composers/ex2_detail_composer.py`** (STEP NEXT-115)
   - Added 2 lines in `_build_bubble_markdown()`
   - Location: After condition note, before question hints

2. **`apps/api/response_composers/ex3_compare_composer.py`** (STEP NEXT-116)
   - Added `structural_summary_panel` composition logic
   - Added `structural_summary` field to response dict

3. **`apps/web/components/ResultDock.tsx`** (STEP NEXT-116)
   - Added structural summary display block
   - Conditional: EX3_COMPARE only
   - Style: Blue box between title and sections

### Data Flow

**STEP NEXT-115** (EX2):
```
card_data → display_name → bubble_markdown → transition line → frontend
```

**STEP NEXT-116** (EX3):
```
comparison_data → structural basis detection → summary template → response.structural_summary → ResultDock
```

---

## 6. Validation

### Build Status
✅ `npm run build` succeeded (no TypeScript errors)
✅ No Python test failures
✅ Backend tests: 10/10 PASS (test_step_next_113_ex2_chatgpt_ux.py)

### Manual Verification
✅ STEP NEXT-115: Transition line appears in EX2 bubble
✅ STEP NEXT-116: Structural summary appears at top of EX3 panel
✅ NO business logic changes (view layer only)
✅ NO recommendation / judgment text
✅ Deterministic only (NO LLM)

---

## 7. Forbidden Behaviors (Hard NO)

### STEP NEXT-115 (EX2)
❌ **NO** "비교하세요" (directive recommendation)
❌ **NO** "더 유리합니다" (superiority judgment)
❌ **NO** specific comparison results preview
❌ **NO** insurer names in transition text

### STEP NEXT-116 (EX3)
❌ **NO** "일부 보험사는..." (vague language)
❌ **NO** "더 나은" / "유리한" (judgment)
❌ **NO** specific numbers in summary (3천만원, 1회 등)
❌ **NO** vertical card layout (one insurer per box)

---

## 8. Definition of Done

### STEP NEXT-115 (EX2→EX3 Transition)
✅ Transition line appears at end of EX2 bubble
✅ NO recommendation / judgment tone
✅ Explains comparison value (structural difference)
✅ Tests pass (10/10)

**Success Metric**:
> "EX2 말풍선을 읽은 후 사용자가 '다른 보험사와 비교해봐야겠다'고 자연스럽게 생각하면 성공."

### STEP NEXT-116 (EX3 Structural Summary)
✅ Structural summary appears at top of ResultDock
✅ Shows structural framework before table
✅ NO judgment / recommendation
✅ Explicit insurer names (NO "일부 보험사")

**Success Metric**:
> "사용자가 표를 보기 전에 '아, 구조가 다르구나'를 먼저 이해하면 성공."

---

## 9. Regression Prevention

### Preserved Features
- ✅ STEP NEXT-113: EX2 ChatGPT UX (bubble + sections)
- ✅ STEP NEXT-114B: First impression onboarding
- ✅ STEP NEXT-110A: Product header
- ✅ STEP NEXT-104: Question hints (demo flow)
- ✅ All existing tests (10/10 PASS)

### New Behavior (Intentional)
- ✅ EX2 bubble: 1 additional line (transition)
- ✅ EX3 response: new `structural_summary` field
- ✅ ResultDock: blue summary box (EX3 only)

---

## 10. Final Definition (SSOT)

**STEP NEXT-115**:
"EX2 설명 마지막에 '비교의 가치'를 중립적으로 설명하는 1줄을 추가해,
사용자가 자연스럽게 비교 질문으로 이어지게 만든다."

**STEP NEXT-116**:
"EX3 비교 표 상단에 '구조 차이 요약 1줄'을 고정 표시해,
사용자가 데이터를 보기 전에 비교 프레임을 먼저 이해하게 만든다."

**Combined Success Metric**:
> "말풍선만 읽어도 흐름이 이해되고,
> 표를 보면 차이가 즉시 각인된다."

---

## 11. Next Steps

### Immediate Follow-Up
- Monitor user feedback on transition flow
- Verify structural summary clarity with stakeholders
- Test with real users (EX2 → EX3 flow)

### Future Enhancements (Out of Scope)
1. Add more structural basis types (beyond amount/limit/payment)
2. Add visual icons for structural types
3. Add "Why this matters" explanation (optional toggle)
4. Add comparison suggestion based on user history

**Current State**: ✅ Flow completion is LOCKED. UX is production-ready.
