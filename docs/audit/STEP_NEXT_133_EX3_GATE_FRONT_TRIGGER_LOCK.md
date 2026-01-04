# STEP NEXT-133: EX3 Gate Front-Trigger Lock

**Date**: 2026-01-04
**Purpose**: Customer Self-Test UX — Front-end EX3 selection gate (NO backend need_more_info)
**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)
**Scope**: View layer ONLY (Frontend)

---

## 0. Purpose

**Core Problem**:
- EX1 → EX3 button → unpredictable screens (보고서/빈 화면/추가정보 엉킴)
- EX3 routed to EX2_DETAIL_DIFF unexpectedly
- Customer testing requires predictable, reproducible UX

**Solution**:
- Frontend triggers EX3-specific selection panel BEFORE backend call
- NO reliance on backend need_more_info for EX3 flow
- User-driven flow: "보험사/담보 선택 → 비교" (always predictable)

---

## 1. Constitutional Principles (ABSOLUTE)

✅ **User-driven ONLY**: Buttons fill input, NO auto-send/auto-select/auto-retry
✅ **EX3 entry = same UX**: Always "비교를 하려면 보험사/담보를 먼저 선택"
✅ **Backend need_more_info = NOT used for EX3**: Frontend controls gate
✅ **No business logic change**: Server routing/intent/data/extraction UNCHANGED
✅ **No LLM** (always OFF), **No silent payload correction**, **No force routing** (129R preserved)

❌ **FORBIDDEN**:
- Triggering backend need_more_info intentionally by emptying payload
- Auto-send on button click
- Silent payload correction/extraction/injection
- Force routing (121/125류 부활)
- Auto-retry loops

---

## 2. Problem Definition

**Current Issues**:
1. EX1 EX3 button → "보고서 보기/비교 보기/추가정보" states mixed
2. First screen shows unwanted screens (보고서/빈 화면/추가정보)
3. EX3 sometimes routed to EX2_DETAIL_DIFF → unpredictable

**Root Cause**:
- Backend need_more_info used for all clarification
- EX3 flow not explicitly separated from EX2/EX4 clarification
- Frontend lacks EX3-specific gate logic

---

## 3. Implementation Scope

**Modified Files**:
- `apps/web/app/page.tsx` (EX3 gate state + detection + panel + submission)
- `apps/web/components/ChatPanel.tsx` (example button text update)

**Backend Changes**: ❌ FORBIDDEN (NO apps/api/** changes)

---

## 4. State Model (SSOT: page.tsx)

**New State Variables**:
```typescript
const [pendingKind, setPendingKind] = useState<"EX3_COMPARE" | null>(null);
const [ex3GateOpen, setEx3GateOpen] = useState(false);
const [ex3GateMessageId, setEx3GateMessageId] = useState<string | null>(null);
```

**Purpose**:
- `pendingKind`: User's intended intent (temporarily stored during gate)
- `ex3GateOpen`: EX3 gate panel visibility switch
- `ex3GateMessageId`: Unique ID for gate message (avoid duplicates)

---

## 5. Detection Logic (Deterministic)

**EX3 Intent Trigger** (keyword matching):
```typescript
const isEX3Intent =
  messageToSend.includes("비교") ||
  messageToSend.includes("차이") ||
  messageToSend.includes("VS") ||
  messageToSend.includes("vs");
```

**Gate Condition**:
```typescript
// EX3 requires 2 insurers + 1 coverage
if (currentInsurers.length < 2 || currentCoverageNames.length === 0) {
  // Open EX3 gate
}
```

**Gate Actions**:
1. Add user message to conversation
2. Add assistant gate message: "비교를 위해 담보와 보험사를 먼저 선택해 주세요..."
3. Show EX3 gate panel
4. **NO backend call**

---

## 6. Processing Flow

### Flow 1: EX1 → EX3 (First Screen)

1. User clicks "삼성화재와 메리츠화재 암진단비 비교해줘" button
   - Input filled (NO auto-send)
2. User clicks "전송"
   - EX3 intent detected
   - Gate opens (insurers < 2 OR coverage missing)
   - Assistant message: "비교를 위해 담보와 보험사를 먼저 선택해 주세요..."
3. User selects 2 insurers + 1 coverage → clicks "비교 시작"
   - /chat called with kind:"EX3_COMPARE", insurers:[2], coverage_names:[1]
   - Gate closes
   - EX3_COMPARE response displayed

### Flow 2: EX2/EX4 → EX3 (Transition - Future)

- Same logic: EX3 intent → check gate conditions → show panel OR proceed
- If insurers/coverage already sufficient → skip gate, direct to EX3

---

## 7. UI Text LOCK (EX3 Gate Specific)

**Assistant Message** (LOCKED):
```
비교를 위해 담보와 보험사를 먼저 선택해 주세요.
아래에서 보험사 2개와 담보명 1개를 고르면 바로 비교표를 보여드릴게요.
```

**Panel Labels** (LOCKED):
- Header: "비교를 위한 정보 선택"
- Insurer section: "비교할 보험사 (2개 선택)"
- Coverage section: "비교할 담보 (1개)"
- Submit button: "비교 시작 (N/2개 보험사, 담보 입력됨/담보 없음)"

**FORBIDDEN**:
- ❌ "추가 정보가 필요합니다" (confusing with EX2/EX4 clarification)
- Recommendation: Use EX3-specific wording ("비교를 위해 먼저 선택")

---

## 8. Forbidden Actions (ABSOLUTE)

❌ **NO triggering backend need_more_info** intentionally for EX3
❌ **NO silent payload correction** / auto-extraction / auto-injection
❌ **NO force routing** (121/125류 부활)
❌ **NO auto-send** (button click → immediate transmission)
❌ **NO auto-retry** loops
❌ **NO backend call** while EX3 gate is open
❌ **NO component reuse** with EX2/EX4 clarification (separation required)

---

## 9. Verification Scenarios

### CHECK-EX3-1: EX1 → EX3 Start

**Input**: First screen → EX3 button → send
**Expected**:
- EX3 gate message + selection panel displayed
- NO backend call (0 requests)
- User selects 2 insurers + coverage → "비교 시작"
- EX3_COMPARE table displayed

**Console Logs**:
```
[page.tsx STEP NEXT-133] EX3_GATE_OPEN: insufficient context
[page.tsx STEP NEXT-133] EX3_GATE_SUBMIT
[page.tsx STEP NEXT-133] EX3_CHAT_REQUEST_SENT
```

### CHECK-EX3-2: EX2 → EX3 Transition

**Input**: EX2_DETAIL completed → EX3 transition (manual)
**Expected**:
- If insurers/coverage already sufficient → NO gate, direct to EX3
- If insufficient → gate panel shown → selection → EX3

### CHECK-EX3-3: EX4 → EX3 Transition

**Input**: EX4 result screen → EX3 transition
**Expected**: Same as CHECK-EX3-2 (NO mixing with EX4 clarification)

### CHECK-EX3-4: Regression

**Input**: EX2/EX4 normal flow (NO EX3 intent)
**Expected**:
- EX2/EX4 need_more_info works normally (unchanged)
- NO EX3 gate interference
- Report view (132) shows empty state if no EX3 data (first screen report = BUG)

---

## 10. Test/Documentation/Git

**Documentation**:
- This file: `docs/audit/STEP_NEXT_133_EX3_GATE_FRONT_TRIGGER_LOCK.md`
- Includes: Purpose, principles, flow, forbidden, scenarios, console logs

**Testing**:
- Manual verification (no frontend test runner available)
- Console logs for tracking:
  - `EX3_GATE_OPEN`
  - `EX3_GATE_SUBMIT`
  - `EX3_CHAT_REQUEST_SENT`

**Git**:
- Branch: feat/step-next-14-chat-ui (preserved)
- Commit message: `feat(step-next-133): front-trigger EX3 selection gate (no backend need_more_info)`
- CLAUDE.md: Add STEP NEXT-133 section with "129R customer self-test" compliance note

---

## 11. Definition of Done

✅ **EX1 → EX3** always shows EX3 gate first (backend calls = 0)
✅ **Selection complete** → EX3_COMPARE called (NOT before)
✅ **EX2/EX4 flows** unchanged (NO regression)
✅ **"왜 이 화면이 나왔지?"** confusion eliminated (EX3 = "선택 → 비교" always)

---

## 12. Key Insights

**Design Philosophy**:
> "EX3 = explicit comparison, not implicit routing. User must choose what to compare BEFORE seeing results."

**UX Principle**:
> "Customer self-test requires predictability. Same input → same flow → same screen sequence."

**129R Compliance**:
- NO forced routing (user chooses insurers/coverage explicitly)
- NO silent correction (frontend validates BEFORE backend call)
- NO need_more_info bypass (gate replaces need_more_info for EX3)
- User action required for all transitions (button clicks, not auto)

---

## 13. Example Console Output

**Successful EX3 Flow**:
```
[page.tsx STEP NEXT-133] EX3_GATE_OPEN: insufficient context {insurers: 0, coverages: 0}
[page.tsx STEP NEXT-133] EX3_GATE_SUBMIT {insurers: ['samsung', 'meritz'], coverages: ['암진단비']}
[page.tsx STEP NEXT-133] EX3_CHAT_REQUEST_SENT {message: '비교 요청', kind: 'EX3_COMPARE', ...}
```

**Gate Already Satisfied** (context exists):
```
[page.tsx] EX3 intent detected, context sufficient, direct to EX3
[page.tsx STEP NEXT-133] EX3_CHAT_REQUEST_SENT {kind: 'EX3_COMPARE', ...}
```

---

**FINAL LOCK**: This is the EX3 front-trigger gate SSOT. Any changes require new STEP number + user testing evidence.
