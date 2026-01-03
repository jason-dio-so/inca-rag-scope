# STEP NEXT-106 — QA Checklist (Manual Testing)

**Date**: 2026-01-03
**Tester**: [Fill in]
**Environment**: http://localhost:3000

---

## Pre-Test Verification

- [ ] Dev server running on `http://localhost:3000`
- [ ] Frontend compiled without errors
- [ ] Browser: Chrome/Firefox/Safari (latest version)

---

## Test Scenario: EX2 → Insurer Switch → LIMIT_FIND Flow

### Step 1: Initial EX2_DETAIL Request

**Action**:
1. Open `http://localhost:3000`
2. Click **"예제2: 담보 설명"** button (삼성화재 암진단비)

**Expected**:
- ✅ EX2_DETAIL response appears
- ✅ Title: "삼성화재 암진단비(유사암제외) 담보 설명"
- ✅ Followup hints at bottom:
  - "메리츠는?"
  - "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
- ✅ Coverage input: **enabled** (normal state)

**Result**: [ ] PASS / [ ] FAIL

---

### Step 2: Insurer Switch ("메리츠는?")

**Action**:
1. Type "메리츠는?" in message input
2. Press Enter

**Expected**:
- ✅ EX2_DETAIL response appears (메리츠화재)
- ✅ Title: "메리츠화재 암진단비(유사암제외) 담보 설명"
- ✅ Top context box shows: "현재 대화 조건: 메리츠화재"
- ✅ Coverage input: **enabled** (normal state)

**Result**: [ ] PASS / [ ] FAIL

---

### Step 3: LIMIT_FIND Pattern (Insufficient Insurers)

**Action**:
1. Type "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
2. Press Enter

**Expected**:
- ✅ User message appears in chat
- ✅ Clarification panel appears (blue background)
  - Text: "추가 정보가 필요합니다"
  - Text: "보험사를 선택하세요:"
  - Insurer buttons visible (samsung, meritz, kb, hanwha, hyundai, lotte)
- ✅ Coverage input: **DISABLED** ← **CRITICAL CHECK**
  - Background: gray (`bg-gray-100`)
  - Text color: gray (`text-gray-500`)
  - Cursor: blocked (no cursor when hovering)
  - Placeholder: "비교를 위해 보험사만 추가해주세요" ← **CRITICAL CHECK**
- ✅ Top context box shows: "현재 대화 조건: 메리츠화재"

**Result**: [ ] PASS / [ ] FAIL

---

### Step 4: Coverage Input Interaction During Clarification

**Action**:
1. Try to click on coverage input field
2. Try to type in coverage input field

**Expected**:
- ✅ Coverage input: **NO FOCUS** (cursor should not enter field)
- ✅ Coverage input: **NO TYPING** (no characters appear)
- ✅ Placeholder remains: "비교를 위해 보험사만 추가해주세요"

**Result**: [ ] PASS / [ ] FAIL

---

### Step 5: Select Additional Insurer

**Action**:
1. Click on "삼성화재" button in clarification panel

**Expected**:
- ✅ Clarification panel: **DISAPPEARS**
- ✅ Coverage input: **ENABLED** (automatically restored) ← **CRITICAL CHECK**
  - Background: white (normal)
  - Text color: black (normal)
  - Cursor: normal (cursor appears when hovering)
  - Placeholder: "예: 암진단비(유사암제외)" (back to default)
- ✅ EX2_LIMIT_FIND response appears
  - Title: "암직접입원비 담보 보장한도 비교"
  - Table with 2 insurers (samsung, meritz)
- ✅ Top context box shows: "현재 대화 조건: 삼성화재 · 메리츠화재"

**Result**: [ ] PASS / [ ] FAIL

---

### Step 6: Follow-up Query (Coverage Input Restored)

**Action**:
1. Try to click on coverage input field
2. Type "뇌출혈진단비"
3. Clear coverage input

**Expected**:
- ✅ Coverage input: **FOCUS** (cursor enters field)
- ✅ Coverage input: **TYPING** (characters appear)
- ✅ Placeholder: "예: 암진단비(유사암제외)" (default placeholder)

**Result**: [ ] PASS / [ ] FAIL

---

## Edge Case Tests

### Edge Case 1: Clarification → 조건 변경

**Action**:
1. Trigger LIMIT_FIND clarification (Step 3)
2. Click "조건 변경" button in top context box
3. Confirm page reload

**Expected**:
- ✅ Confirmation dialog appears
- ✅ Page reloads
- ✅ Clarification state cleared
- ✅ Coverage input: **enabled** (reset to initial state)

**Result**: [ ] PASS / [ ] FAIL

---

### Edge Case 2: Normal Clarification (Coverage Names)

**Action**:
1. Reload page
2. Select insurers: samsung, meritz
3. Type vague query: "암진단비 알려줘" (without specifying exact coverage name)
4. (If clarification panel appears for coverage_names)

**Expected**:
- ✅ Coverage input: **ENABLED** (NOT disabled for coverage_names clarification)
- ✅ Coverage input disabled ONLY for LIMIT_FIND insurer clarification

**Result**: [ ] PASS / [ ] FAIL / [ ] N/A (clarification not triggered)

---

### Edge Case 3: EX3 / EX4 Clarification (No Impact)

**Action**:
1. Reload page
2. Select insurer: samsung only
3. Type: "제자리암 보장 가능한가요?" (EX4_ELIGIBILITY pattern)
4. (If clarification panel appears for insurers)

**Expected**:
- ✅ Coverage input: **ENABLED** (NOT disabled for EX4 clarification)
- ✅ Coverage input disabled ONLY for LIMIT_FIND clarification

**Result**: [ ] PASS / [ ] FAIL / [ ] N/A (clarification not triggered)

---

## Visual Verification

### Disabled State Visual Cues

**When coverage input is DISABLED** (Step 3):
- [ ] Background: Light gray (`#F3F4F6` or similar)
- [ ] Border: Gray (not blue on focus)
- [ ] Text: Gray (#6B7280 or similar)
- [ ] Cursor: `cursor-not-allowed` (🚫 icon on hover)
- [ ] Placeholder: "비교를 위해 보험사만 추가해주세요"

**When coverage input is ENABLED** (Step 5):
- [ ] Background: White (`#FFFFFF`)
- [ ] Border: Gray (blue on focus)
- [ ] Text: Black (`#111827` or similar)
- [ ] Cursor: `text` (I-beam on hover)
- [ ] Placeholder: "예: 암진단비(유사암제외)"

---

## Accessibility Verification

- [ ] Tab navigation: Cannot tab into disabled coverage input during clarification
- [ ] Screen reader: Disabled attribute announced as "disabled" or "unavailable"
- [ ] Keyboard only: Can navigate to insurer buttons during clarification

---

## Final Checklist

- [ ] All main scenario steps (1-6) PASS
- [ ] All edge cases (1-3) PASS or N/A
- [ ] Visual verification PASS
- [ ] Accessibility verification PASS
- [ ] NO console errors in browser DevTools
- [ ] NO TypeScript compilation errors
- [ ] Demo flow seamless: EX2 → 메리츠는? → LIMIT_FIND

---

## Notes / Issues Found

[Fill in any issues or observations during testing]

---

## Sign-off

**Tester Name**: ___________________
**Date**: ___________________
**Result**: [ ] APPROVED / [ ] ISSUES FOUND (see notes)
