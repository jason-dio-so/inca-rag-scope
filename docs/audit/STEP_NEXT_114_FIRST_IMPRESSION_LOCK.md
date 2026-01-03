# STEP NEXT-114 — First Impression Screen UX Lock

**Date**: 2026-01-04
**Status**: ✅ COMPLETE (114B: Final Copy & Layout Tuning)
**Scope**: View Layer ONLY (Initial State UI)

---

## 0. Purpose

Before STEP NEXT-114, the system had:
- ❌ Example buttons on first screen (looked like "button demo", not ChatGPT)
- ❌ No clear system identity at first glance
- ❌ EX2 response could appear as first screen (confused users about product purpose)

**Goal**: Show system identity in **5 seconds** at first screen.

> "이 시스템이 '보험을 구조적으로 비교해주는 도우미'임을 질문 전에 인지시키는 것"

---

## 1. What Changed

### Before (STEP NEXT-113 and earlier)
- First screen: Header + 4 example buttons (EX2, EX3, EX4 examples)
- No onboarding message
- ResultDock visible even before first question

### After (STEP NEXT-114)
- First screen: Single onboarding bubble (ChatGPT style)
- NO example buttons
- ResultDock hidden until first response
- Clean, conversational introduction

---

## 2. Implementation

### Modified Files
1. **`apps/web/components/ChatPanel.tsx`**:
   - Added `isInitialState` flag (`messages.length === 0`)
   - Replaced example buttons with fixed onboarding bubble
   - Removed `onSendWithKind` prop and `handleExampleClick` function
   - Removed `MessageKind` import (no longer needed)

2. **`apps/web/app/page.tsx`**:
   - Removed `handleSendWithKind` function (no example buttons)
   - Removed `onSendWithKind` prop from ChatPanel
   - Added `messages.length > 0` check to ResultDock visibility
   - Removed unused imports: `extractDiseaseName`, `getInsurerDisplayName`

---

## 3. Locked Onboarding Copy

### STEP NEXT-114B: Final Copy (LOCKED)

**Left Bubble (Assistant Message)**:
```
보험 상품을 단순히 나열하는 대신,
보장이 어떻게 정의되어 있는지를 기준으로 비교해 드립니다.

예를 들어
"삼성화재 암진단비 설명해줘"
같은 질문부터 시작해 보세요.
```

**Input Placeholder**:
```
예: 삼성화재 암진단비 설명해줘
```

**Rules**:
- ❌ NO "이 도우미는..." (service introduction tone)
- ❌ NO "설명 → 비교 → 이해" (abstract flow diagram)
- ❌ NO bullets/bold/numbers
- ❌ NO insurer names in bubble (only in example)
- ❌ NO product names
- ✅ Conversational tone ("~해 드립니다", "~보세요")
- ✅ Concrete example question (not abstract)
- ✅ Left-aligned bubble (60-65% max width)
- ✅ Plain text style

---

## 4. UX Flow

### Initial State (Before Any Questions)
1. **Left Chat Area**:
   - Single assistant bubble with onboarding text
   - NO example buttons
   - NO user messages

2. **Right Result Dock**:
   - Hidden (not rendered)

3. **Bottom Input Area**:
   - Collapsed by default (STEP NEXT-108 preserved)
   - Options panel available via "보험사/담보 선택 ▾"

### Transition to Active State
**Trigger**: User sends first question OR clicks example button (future)

**Changes**:
1. Onboarding bubble disappears (replaced by conversation)
2. ResultDock appears (right panel active)
3. Conversation context locks (STEP NEXT-101 preserved)

---

## 5. Technical Details

### ChatPanel.tsx (STEP NEXT-114B)
```typescript
// STEP NEXT-114B: Initial state flag
const isInitialState = messages.length === 0;

// Render logic
{isInitialState ? (
  <div className="flex justify-start mt-8">
    <div className="max-w-[65%] rounded-lg px-4 py-3 bg-gray-100 text-gray-800">
      <div className="text-sm leading-relaxed whitespace-pre-line">
보험 상품을 단순히 나열하는 대신,
보장이 어떻게 정의되어 있는지를 기준으로 비교해 드립니다.

예를 들어
"삼성화재 암진단비 설명해줘"
같은 질문부터 시작해 보세요.
      </div>
    </div>
  </div>
) : (
  messages.map((msg, idx) => /* existing message rendering */)
)}

// Placeholder (STEP NEXT-114B)
<textarea
  placeholder="예: 삼성화재 암진단비 설명해줘"
  // ... other props
/>
```

### page.tsx
```typescript
// STEP NEXT-114: Hide ResultDock in initial state
{latestResponse && messages.length > 0 && (
  <div className="w-1/2 border-l border-gray-200 overflow-y-auto p-4 bg-gray-50">
    <ResultDock response={latestResponse} />
  </div>
)}
```

---

## 6. Validation

### Build Status
✅ `npm run build` succeeded (no TypeScript errors)
✅ No unused imports
✅ No missing dependencies

### Visual Verification
✅ First screen shows onboarding bubble ONLY
✅ NO example buttons
✅ ResultDock hidden before first question
✅ Clean ChatGPT-style layout

### Acceptance Criteria
✅ User sees system identity in 5 seconds
✅ NO data/numbers/tables on first screen
✅ Conversation starts naturally (not "button demo")
✅ ResultDock activates only after first response

---

## 7. Forbidden Behaviors (Hard NO)

❌ **NO** example buttons on first screen
❌ **NO** data preview before first question
❌ **NO** tables/cards in onboarding bubble
❌ **NO** insurer names in onboarding text
❌ **NO** product names in onboarding text
❌ **NO** recommendations/judgments in onboarding
❌ **NO** LLM usage (fixed text only)

---

## 8. Definition of Done

✅ First screen: Single onboarding bubble + input field
✅ NO example buttons
✅ ResultDock hidden until first response
✅ Build succeeds with no errors
✅ ChatGPT UI alignment maintained (STEP NEXT-108 preserved)
✅ Conversation context preserved (STEP NEXT-101 preserved)

---

## 9. Regression Prevention

### Preserved Features
- ✅ STEP NEXT-108: Collapsible options panel (ChatGPT style)
- ✅ STEP NEXT-106: Clarification UI (coverage input disable)
- ✅ STEP NEXT-101: Conversation context carryover
- ✅ STEP NEXT-102: Insurer switch detection
- ✅ STEP NEXT-113: EX2_DETAIL ChatGPT UX (bubble + sections)

### Removed Features (Intentional)
- ❌ Example buttons on first screen (replaced by onboarding bubble)
- ❌ `onSendWithKind` handler (no longer needed without example buttons)

---

## 10. Final Definition (SSOT)

**STEP NEXT-114 / 114B**:
"ChatGPT처럼 '대화를 시작하는' 첫 화면.
시스템 소개가 아니라 assistant의 첫 말처럼 보여야 성공."

**Success Metric (114)**:
"사용자가 첫 화면에 진입한 뒤 5초 이내에
'아, 이건 보험 비교 도우미구나'라고 인지하면 성공."

**Success Metric (114B — Final)**:
"사용자가 첫 화면에서 10초 안에
'아, 여기다 이렇게 물어보면 되는구나'라고 생각하고
질문을 입력하기 시작하면 성공."

---

## 11. Next Steps

### Future Enhancements (Out of Scope)
1. Add example question suggestions (as text hints, NOT buttons)
2. Add "빠른 시작" section below onboarding bubble
3. Add animated typing effect for onboarding text
4. Add tutorial mode for first-time users

### Immediate Follow-Up
- Monitor user feedback on first impression
- Verify onboarding copy clarity with stakeholders
- Test with real users (5-second test)
