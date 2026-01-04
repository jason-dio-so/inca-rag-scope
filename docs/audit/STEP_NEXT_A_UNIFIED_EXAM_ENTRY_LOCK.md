# STEP NEXT-A: Unified Exam Entry UX Lock (EX1 → EX2/EX3/EX4)

**Date**: 2026-01-04
**Purpose**: Unify entry UX for all exam types when starting from EX1 (first impression screen)
**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)
**Scope**: View layer ONLY (Frontend)

---

## 0. Purpose

**Core Problem**:
- EX1 (first screen) → EX2/EX3/EX4 buttons had inconsistent UX
- Some immediately showed results (bypassing selection)
- Some showed clarification panels with different messages
- Customer testing requires **predictable, uniform entry flow**

**Solution**:
- **ALL exam types show the same "추가 정보가 필요합니다" message** when starting from EX1
- User must select coverage/insurers and click send BEFORE any composer is called
- Entry difference occurs ONLY after selection complete (in result display)

---

## 1. Constitutional Principles (ABSOLUTE)

✅ **Unified entry message**: ALL exams use same "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요."
✅ **NO immediate results**: EX1 buttons NEVER trigger composer calls directly
✅ **Selection required**: User must choose insurers + coverage explicitly
✅ **NO auto-send**: Buttons fill input ONLY (already 129R compliant)
✅ **NO auto-routing**: Frontend gates entry BEFORE backend decides intent
✅ **Exam differences appear in results**: EX2/EX3/EX4 diverge AFTER selection, NOT before

❌ **FORBIDDEN**:
- Different entry messages for EX2 vs EX3 vs EX4
- Auto-completing selection based on keywords
- Silent payload correction / extraction
- Force routing based on data structure
- Auto-retry loops

---

## 2. Problem Definition

**Current Issues** (before STEP NEXT-A):
1. EX3 had dedicated gate (STEP NEXT-133) with "비교를 위해..." message
2. EX2/EX4 relied on backend `need_more_info` → inconsistent timing
3. User couldn't predict which screen would appear when

**Root Cause**:
- Entry gates implemented per-exam (EX3 only)
- Backend clarification used for all others
- No unified "initial entry from EX1" detection

---

## 3. Implementation Scope

**Modified Files**:
- `apps/web/app/page.tsx` (unified exam entry gate logic)

**Backend Changes**: ❌ FORBIDDEN (NO apps/api/** changes)

**Key Insight**:
> "Entry UX unification is a **frontend concern**. Backend sees normal requests with insurers + coverage after selection."

---

## 4. Detection Logic (Deterministic)

**Initial Entry Detection**:
```typescript
const isInitialEntry = messages.length === 0;
```

**Exam Intent Detection** (keyword matching):
```typescript
const isEX2Intent = messageToSend.includes("담보 중") || messageToSend.includes("보장한도가 다른");
const isEX3Intent = messageToSend.includes("비교") || messageToSend.includes("차이") || messageToSend.includes("VS") || messageToSend.includes("vs");
const isEX4Intent = messageToSend.includes("보장여부") || messageToSend.includes("보장내용에 따라");
```

**Requirements per Exam**:
- **EX3**: 2 insurers + 1 coverage
- **EX2/EX4**: 1+ insurers + 1 coverage (or disease name for EX4)

**Gate Trigger**:
```typescript
if (isInitialEntry && (isEX2Intent || isEX3Intent || isEX4Intent)) {
  if (!requirementsMet) {
    // Show unified entry gate
  }
}
```

---

## 5. Processing Flow

### Flow 1: EX1 → EX2 (LIMIT_FIND)

1. User clicks "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" button
   - Input filled (NO auto-send) ✅
2. User clicks "전송"
   - `isInitialEntry = true` (messages.length === 0)
   - `isEX2Intent = true` (contains "담보 중", "보장한도가 다른")
   - Requirements check: insurers.length > 0 && coverage.length > 0
   - **Gate opens** (insurers = 0) ✅
3. User sees message: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
4. Panel shows: "보험사 선택 (1개 이상)" + "담보명 (1개)"
5. User selects insurers + coverage → clicks "확인"
   - `/chat` called with insurers, coverage_names, NO kind specified
   - Backend routes to EX2_LIMIT_FIND (auto-detection)

### Flow 2: EX1 → EX3 (COMPARE)

1. User clicks "삼성화재와 메리츠화재 암진단비 비교해줘" button
   - Input filled (NO auto-send) ✅
2. User clicks "전송"
   - `isInitialEntry = true`
   - `isEX3Intent = true` (contains "비교")
   - Requirements check: insurers.length >= 2 && coverage.length > 0
   - **Gate opens** (insurers = 0) ✅
3. User sees **same message**: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
4. Panel shows: "비교할 보험사 (2개 선택)" + "담보명 (1개)"
5. User selects 2 insurers + coverage → clicks "비교 시작"
   - `/chat` called with kind: "EX3_COMPARE", insurers, coverage_names
   - Backend uses EX3_COMPARE composer

### Flow 3: EX1 → EX4 (ELIGIBILITY)

1. User clicks "제자리암, 경계성종양 보장여부 비교해줘" button
   - Input filled (NO auto-send) ✅
2. User clicks "전송"
   - `isInitialEntry = true`
   - `isEX4Intent = true` (contains "보장여부", "보장내용에 따라")
   - Requirements check: insurers.length > 0
   - **Gate opens** (insurers = 0) ✅
3. User sees **same message**: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
4. Panel shows: "보험사 선택 (1개 이상)" + "담보명 (1개)"
5. User selects insurers + disease names → clicks "확인"
   - `/chat` called with insurers, disease keywords
   - Backend routes to EX4_ELIGIBILITY

---

## 6. UI Text LOCK (Unified Entry Gate)

**Assistant Message** (LOCKED, same for ALL exam types):
```
추가 정보가 필요합니다.
비교할 담보와 보험사를 선택해주세요.
```

**Panel Header** (LOCKED):
```
추가 정보 선택
```

**Panel Labels** (adaptive):
- Insurer section:
  - EX3: "비교할 보험사 (2개 선택)"
  - EX2/EX4: "보험사 선택 (1개 이상)"
- Coverage section: "담보명 (1개)"

**Submit Button** (adaptive):
- EX3: "비교 시작 (N/2개 보험사, 담보 입력됨/담보 없음)"
- EX2/EX4: "확인 (N개 보험사, 담보 입력됨/담보 없음)"

**FORBIDDEN**:
- ❌ "비교를 위해 먼저 선택..." (EX3-specific, no longer used)
- ❌ Different entry messages per exam type
- ❌ "일부 보험사는..." (vague language)

---

## 7. Forbidden Actions (ABSOLUTE)

❌ **NO immediate composer calls** from EX1 buttons
❌ **NO different entry messages** for EX2 vs EX3 vs EX4
❌ **NO auto-send** on button click (already 129R)
❌ **NO silent payload correction** / extraction / injection
❌ **NO force routing** based on data structure
❌ **NO auto-retry** loops
❌ **NO backend call** while gate is open

---

## 8. Verification Scenarios

### CHECK-A-1: EX1 → EX2 Entry

**Input**: First screen → "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" button → send
**Expected**:
- Gate message: "추가 정보가 필요합니다..." ✅
- Panel shows: "보험사 선택 (1개 이상)" ✅
- NO backend call (0 requests) ✅
- User selects insurers + coverage → "확인" → EX2_LIMIT_FIND result

**Console Logs**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX2", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "AUTO", insurers: [...], coverages: [...]}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {message: "요청", insurers: [...], coverage_names: [...]}
```

### CHECK-A-2: EX1 → EX3 Entry

**Input**: First screen → "삼성화재와 메리츠화재 암진단비 비교해줘" button → send
**Expected**:
- Gate message: **SAME** "추가 정보가 필요합니다..." ✅
- Panel shows: "비교할 보험사 (2개 선택)" ✅
- NO backend call (0 requests) ✅
- User selects 2 insurers + coverage → "비교 시작" → EX3_COMPARE table

**Console Logs**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX3", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "EX3_COMPARE", insurers: [...], coverages: [...]}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {kind: "EX3_COMPARE", ...}
```

### CHECK-A-3: EX1 → EX4 Entry

**Input**: First screen → "제자리암, 경계성종양 보장여부 비교해줘" button → send
**Expected**:
- Gate message: **SAME** "추가 정보가 필요합니다..." ✅
- Panel shows: "보험사 선택 (1개 이상)" ✅
- NO backend call (0 requests) ✅
- User selects insurers + disease names → "확인" → EX4_ELIGIBILITY O/X table

**Console Logs**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX4", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "AUTO", insurers: [...], coverages: [...]}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {message: "요청", insurers: [...], coverage_names: [...]}
```

### CHECK-A-4: Regression (Exam-to-Exam Transitions)

**Input**: EX2 result → "메리츠는?" (insurer switch)
**Expected**: NO gate shown (exam transitions not affected by STEP NEXT-A)

**Input**: EX2 result → "비교해줘" (EX3 transition)
**Expected**: Follows existing transition logic (not initial entry)

---

## 9. Test/Documentation/Git

**Documentation**:
- This file: `docs/audit/STEP_NEXT_A_UNIFIED_EXAM_ENTRY_LOCK.md`
- Includes: Purpose, principles, flows, forbidden, scenarios

**Testing**:
- Manual verification (no frontend test runner)
- Console logs for tracking:
  - `EXAM_ENTRY_GATE_OPEN`
  - `EXAM_ENTRY_GATE_SUBMIT`
  - `EXAM_ENTRY_REQUEST_SENT`

**Git**:
- Branch: feat/step-next-14-chat-ui (preserved)
- Commit message: `feat(step-next-a): unified exam entry UX for EX1→EX2/EX3/EX4`
- CLAUDE.md: Add STEP NEXT-A section

---

## 10. Definition of Done

✅ **EX1 → EX2** shows "추가 정보가 필요합니다..." (NO backend call before selection)
✅ **EX1 → EX3** shows **SAME MESSAGE** (NO EX3-specific entry message)
✅ **EX1 → EX4** shows **SAME MESSAGE** (unified with EX2/EX3)
✅ **Exam differences** appear ONLY in results (after selection complete)
✅ **Entry UX = 100% identical** across all exam types when starting from EX1

---

## 11. Key Insights

**Design Philosophy**:
> "Entry UX is about **where you start**, not **where you go**. All exams start the same way (select insurers + coverage). Results differ based on backend routing."

**UX Principle**:
> "Customer testing requires predictability. If all EX1 buttons lead to the same selection screen, users learn the pattern once and apply it everywhere."

**129R Compliance**:
- NO forced routing (backend decides intent after selection)
- NO silent correction (gate validates BEFORE backend call)
- NO auto-send (buttons fill input, user clicks send)
- User action required for all transitions

**Relationship to STEP NEXT-133**:
- STEP NEXT-133: EX3-specific gate (deprecated entry message)
- STEP NEXT-A: Unified gate for ALL exam types (supersedes 133's message)
- Gate mechanics preserved, message unified

---

## 12. Example Console Output

**Successful EX2 Entry**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX2", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "AUTO", insurers: ['samsung'], coverages: ['암직접입원일당']}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {message: '요청', insurers: ['samsung'], coverage_names: ['암직접입원일당'], llm_mode: 'OFF'}
```

**Successful EX3 Entry**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX3", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "EX3_COMPARE", insurers: ['samsung', 'meritz'], coverages: ['암진단비']}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {kind: 'EX3_COMPARE', insurers: ['samsung', 'meritz'], coverage_names: ['암진단비'], llm_mode: 'OFF'}
```

**Successful EX4 Entry**:
```
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_OPEN: insufficient context {examType: "EX4", insurers: 0, coverages: 0}
[page.tsx STEP NEXT-A] EXAM_ENTRY_GATE_SUBMIT {examType: "AUTO", insurers: ['samsung', 'meritz'], coverages: ['제자리암', '경계성종양']}
[page.tsx STEP NEXT-A] EXAM_ENTRY_REQUEST_SENT {message: '요청', insurers: ['samsung', 'meritz'], coverage_names: ['제자리암', '경계성종양'], llm_mode: 'OFF'}
```

---

**FINAL LOCK**: This is the unified exam entry UX SSOT. All EX1 → Exam flows must use this pattern. Any changes require new STEP number + user testing evidence.
