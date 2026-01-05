# STEP NEXT-138: Single-Insurer Explanation Guard (CRITICAL REGRESSION FIX) — 2026-01-04

## Problem Statement

**REGRESSION BUG**:
- **Input**: "삼성화재 암진단비 설명해줘"
- **Expected**: EX2_DETAIL (single-insurer detail view)
- **Actual**: EX3_COMPARE (multi-insurer comparison view with 삼성+메리츠)

This is a critical regression that breaks the fundamental EXAM CONSTITUTION rule:
> "EXAM2/EX3/EX4는 서로의 입력/출력/상태를 절대 공유하지 않는다"

A single-insurer explanation query (EX2_DETAIL) MUST NOT route to comparison mode (EX3_COMPARE).

## Root Causes

### 1. Missing Explanation Intent Detection
**File**: `apps/web/lib/clarificationUtils.ts::detectExamType()`

**Problem**: Function did not detect "설명", "알려줘" patterns as explanation intent.

**Before**:
```typescript
function detectExamType(message: string): "EX2" | "EX3" | "EX4" | null {
  const isEX2 = message.includes("담보 중") || message.includes("보장한도가 다른");
  const isEX3 = message.includes("비교") || message.includes("차이") || ...;
  const isEX4 = message.includes("보장여부") || ...;

  if (isEX3) return "EX3";
  if (isEX4) return "EX4";
  if (isEX2) return "EX2";
  return null;
}
```

**Issue**: "삼성화재 암진단비 설명해줘" → returns `null` (no exam type detected)

### 2. Context Carryover Bug
**File**: `apps/web/lib/clarificationUtils.ts::deriveClarificationState()`

**Problem**: When user explicitly mentions insurers in new query, system still used previous locked context.

**Example**:
1. Previous query: "삼성화재와 메리츠화재 암진단비 비교해줘" → `lockedInsurers: ["samsung", "meritz"]`
2. New query: "삼성화재 수술비 설명해줘" → User explicitly mentions ONLY samsung
3. System used: `["samsung", "meritz"]` (locked context) instead of `["samsung"]` (parsed from message)

### 3. No Routing Guard
**File**: `apps/web/app/page.tsx::handleSend()`

**Problem**: No guard to FORCE EX2_DETAIL when single insurer + explanation intent detected.

Even if exam type was correctly detected, there was no enforcement to prevent multi-insurer context from overriding single-insurer intent.

## Solution

### 1. Add EX1_DETAIL Exam Type (Explanation Intent)

**File**: `apps/web/lib/clarificationUtils.ts`

**Changes**:
```typescript
/**
 * STEP NEXT-138: Added single-insurer explanation detection
 * Priority:
 * 1. EX1_DETAIL: "설명", "알려줘" (single insurer only)
 * 2. EX3: "비교", "차이" (2+ insurers)
 * 3. EX4: disease subtypes
 * 4. EX2: "담보 중", "보장한도가 다른"
 */
function detectExamType(message: string): "EX1_DETAIL" | "EX2" | "EX3" | "EX4" | null {
  const isExplanation = message.includes("설명해") || message.includes("설명") ||
    message.includes("알려줘") || message.includes("알려주세요");
  const isEX2 = message.includes("담보 중") || message.includes("보장한도가 다른");
  const isEX3 = message.includes("비교") || message.includes("차이") ||
    message.includes("VS") || message.includes("vs");
  const isEX4 = message.includes("보장여부") || message.includes("보장내용에 따라") ||
    message.includes("제자리암") || message.includes("경계성종양");

  // STEP NEXT-138: Single-insurer explanation takes priority over comparison
  if (isExplanation && !isEX3) return "EX1_DETAIL";
  if (isEX3) return "EX3";
  if (isEX4) return "EX4";
  if (isEX2) return "EX2";
  return null;
}
```

**Key Logic**:
- `isExplanation && !isEX3` → EX1_DETAIL (explanation WITHOUT comparison keywords)
- `"설명해줘"` → EX1_DETAIL
- `"비교해줘"` → EX3 (comparison overrides explanation)

**Slot Requirements**:
```typescript
if (examType === "EX1_DETAIL") {
  // EX1_DETAIL requires 1 insurer + 1 coverage
  missingInsurers = !resolvedInsurers || resolvedInsurers.length === 0;
  missingCoverage = !resolvedCoverage || resolvedCoverage.length === 0;
}
```

### 2. Add Context Reset Logic (Parse Insurers from Message)

**File**: `apps/web/lib/clarificationUtils.ts`

**New Function**:
```typescript
/**
 * Parse insurers from user message (STEP NEXT-138)
 */
function parseInsurersFromMessage(message: string): string[] {
  const normalized = message.trim().toLowerCase();

  const insurerMap: Record<string, string> = {
    '삼성화재': 'samsung', '삼성': 'samsung',
    '메리츠화재': 'meritz', '메리츠': 'meritz',
    '한화손해보험': 'hanwha', '한화': 'hanwha',
    '현대해상': 'hyundai', '현대': 'hyundai',
    'kb손해보험': 'kb', 'kb': 'kb',
    '롯데손해보험': 'lotte', '롯데': 'lotte',
    '흥국화재': 'heungkuk', '흥국': 'heungkuk',
  };

  const found: string[] = [];
  const seenCodes = new Set<string>();

  for (const [keyword, code] of Object.entries(insurerMap)) {
    if (normalized.includes(keyword) && !seenCodes.has(code)) {
      found.push(code);
      seenCodes.add(code);
    }
  }

  return found;
}
```

**Updated Resolution Logic**:
```typescript
// STEP NEXT-138: Parse insurers from message (context reset if explicitly mentioned)
const parsedInsurers = parseInsurersFromMessage(lastUserText);

// STEP NEXT-138: If insurers are explicitly mentioned in message, use those (RESET context)
// Otherwise, use payload → locked context fallback
const resolvedInsurers =
  payloadInsurers ||
  (parsedInsurers.length > 0 ? parsedInsurers : conversationContext?.lockedInsurers) ||
  null;
```

**Priority**:
1. `payloadInsurers` (explicit selection)
2. `parsedInsurers` (mentioned in message) ← **NEW (STEP NEXT-138)**
3. `lockedInsurers` (conversation context)

**Effect**: When user explicitly mentions insurers in message, previous context is RESET.

### 3. Add Routing Guard (FORCE EX2_DETAIL)

**File**: `apps/web/app/page.tsx::handleSend()`

**Changes** (TWO guards added):

#### Guard 1: Initial Entry Guard (inside `isInitialEntry` block)
```typescript
// STEP NEXT-138: Intent routing guard (CRITICAL REGRESSION FIX)
// RULE 1: Single insurer + explanation → FORCE EX2_DETAIL (block EX3_COMPARE)
// RULE 2: 2+ insurers + comparison → allow EX3_COMPARE
// RULE 3: When new query explicitly mentions insurers → CLEAR previous context
if (clarState.examType === "EX1_DETAIL" &&
    clarState.resolvedSlots.insurers &&
    clarState.resolvedSlots.insurers.length === 1) {
  console.log("[page.tsx STEP NEXT-138] Single-insurer explanation detected, forcing EX2_DETAIL");

  // Clear any previous multi-insurer context
  setSelectedInsurers(clarState.resolvedSlots.insurers);
  setConversationContext({
    lockedInsurers: clarState.resolvedSlots.insurers,
    lockedCoverageNames: clarState.resolvedSlots.coverage,
    isLocked: false,  // Not locked yet (will lock after first response)
  });
}
```

#### Guard 2: Ongoing Conversation Guard (outside `isInitialEntry` block) ← **CRITICAL FIX**
```typescript
// STEP NEXT-138: Detect single-insurer explanation (ONGOING conversation guard)
// This runs OUTSIDE isInitialEntry to catch follow-up queries like:
// Previous: "삼성화재와 메리츠화재 비교해줘" (2 insurers locked)
// Current: "삼성화재 암진단비 설명해줘" (should RESET to single insurer)
const isExplanation = messageToSend.includes("설명해") || messageToSend.includes("설명") ||
  messageToSend.includes("알려줘") || messageToSend.includes("알려주세요");
const isComparison = messageToSend.includes("비교") || messageToSend.includes("차이") ||
  messageToSend.includes("VS") || messageToSend.includes("vs");

if (isExplanation && !isComparison && !effectiveInsurers) {
  const parsedInsurers = extractInsurersFromMessage(messageToSend);

  if (parsedInsurers.length === 1) {
    console.log("[page.tsx STEP NEXT-138] Single-insurer explanation detected (ongoing):", parsedInsurers[0]);
    // FORCE single insurer (override any multi-insurer context)
    effectiveInsurers = parsedInsurers;
    effectiveKind = "EX2_DETAIL" as MessageKind;

    // Update state for future requests
    setSelectedInsurers(parsedInsurers);
    setConversationContext({
      lockedInsurers: parsedInsurers,
      lockedCoverageNames: conversationContext.lockedCoverageNames,
      isLocked: false,  // Not locked yet (will lock after response)
    });
  }
}
```

**Why TWO Guards?**
- **Guard 1** (Initial): Runs during first message (`messages.length === 0`)
- **Guard 2** (Ongoing): Runs during follow-up messages (`messages.length > 0`) ← **THIS WAS MISSING**
- Screenshot bug showed ongoing conversation ("대화 중: 삼성화재 · 메리츠화재")
- Guard 2 catches case where user has locked multi-insurer context from previous query

**Enforcement**:
- Detects explanation intent ("설명해", "알려줘")
- Confirms NO comparison intent
- Parses insurers from message
- If exactly 1 insurer → **FORCE** `EX2_DETAIL` (override any locked multi-insurer context)

## Core Rules (ABSOLUTE)

### Rule 1: Single Insurer + Explanation → FORCE EX2_DETAIL
```
IF insurer_count == 1 AND intent in ["설명", "알려줘", "설명해줘"]
→ FORCE EX2_DETAIL (single-insurer detail view)
→ EX3_COMPARE HARD BLOCK (ignore multi-insurer context)
```

### Rule 2: EXAM3 Entry Requires BOTH
```
EX3_COMPARE requires:
- insurer_count >= 2 (ABSOLUTE)
- explicit compare signal ("비교", "차이", "다른", "vs")
```

Single insurer + comparison keywords → clarification (ask for 2nd insurer)

### Rule 3: Explicit Insurer Mention → Context Reset
```
When new query explicitly mentions insurers:
→ CLEAR previous conversation insurers (NO carry-over)
→ Use ONLY insurers mentioned in current query
```

**Example**:
- Previous: `lockedInsurers: ["samsung", "meritz"]`
- New query: "삼성화재 수술비 설명해줘"
- Result: `resolvedInsurers: ["samsung"]` (meritz DROPPED)

## Verification Scenarios

### ✅ CHECK-138-1: Single-Insurer Explanation (CRITICAL)
**Input**: "삼성화재 암진단비 설명해줘"

**Expected**:
1. `examType` → `"EX1_DETAIL"`
2. `resolvedInsurers` → `["samsung"]`
3. `resolvedCoverage` → `["암진단비"]`
4. `showClarification` → `false`
5. **Result**: EX2_DETAIL view (NO comparison)

**Verification**: Left bubble = EX2_DETAIL content, Right panel = single-insurer detail

### ✅ CHECK-138-2: Multi-Insurer Comparison
**Input**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected**:
1. `examType` → `"EX3"`
2. `resolvedInsurers` → `["samsung", "meritz"]`
3. `resolvedCoverage` → `["암진단비"]`
4. `showClarification` → `false`
5. **Result**: EX3_COMPARE view

**Verification**: Left bubble = EX3 summary, Right panel = comparison table

### ✅ CHECK-138-3: Context Reset on Explicit Insurer (CRITICAL)
**Input (after CHECK-138-2)**: "삼성화재 수술비 설명해줘"

**Expected**:
1. Previous: `lockedInsurers: ["samsung", "meritz"]`
2. New: `parsedInsurers: ["samsung"]`
3. **RESET**: `resolvedInsurers: ["samsung"]` (meritz dropped)
4. `examType` → `"EX1_DETAIL"`
5. **Result**: EX2_DETAIL view for samsung ONLY

**Verification**: Console log shows `insurers: ["samsung"]` (NOT `["samsung", "meritz"]`)

### ✅ CHECK-138-4: Explanation Without Insurer
**Input**: "설명해줘"

**Expected**:
1. `examType` → `"EX1_DETAIL"`
2. `resolvedInsurers` → `null`
3. `missingSlots.insurers` → `true`
4. `showClarification` → `true`

**Verification**: Clarification panel appears, asks for insurer + coverage

### ✅ CHECK-138-5: Comparison Without Insurer
**Input**: "암진단비 비교해줘"

**Expected**:
1. `examType` → `"EX3"`
2. `resolvedInsurers` → `null`
3. `resolvedCoverage` → `["암진단비"]`
4. `missingSlots.insurers` → `true` (needs 2+ for EX3)
5. `showClarification` → `true`

**Verification**: Clarification panel appears, asks for insurers

### ✅ CHECK-138-6: Single Insurer MUST NOT Route to EX3
**Input**: "삼성화재 암진단비 설명해줘"

**Expected**:
1. `examType` → `"EX1_DETAIL"` (NOT EX3)
2. **NEVER** shows EX3_COMPARE
3. **ALWAYS** shows EX2_DETAIL

**Verification**: Repeated 10 times → EX3_COMPARE appears 0 times

## Implementation

### Modified Files
1. **`apps/web/lib/clarificationUtils.ts`**:
   - Added `EX1_DETAIL` exam type to `ClarificationState`
   - Added `parseInsurersFromMessage()` function
   - Updated `detectExamType()` to detect explanation intent
   - Updated `deriveClarificationState()` to reset context when insurers mentioned
   - Updated slot requirements for `EX1_DETAIL`

2. **`apps/web/app/page.tsx`**:
   - Added STEP NEXT-138 routing guard in `handleSend()`
   - Enforces single-insurer + explanation → FORCE EX2_DETAIL
   - Clears multi-insurer context when single insurer explicitly mentioned

### Created Files
1. **`tests/manual_test_step_next_138_explanation_guard.md`** (manual test plan)
2. **`docs/audit/STEP_NEXT_138_SINGLE_INSURER_EXPLANATION_GUARD.md`** (this file)

### Backend Changes
❌ **NONE** (frontend-only fix)

## Constitutional Basis

**EXAM CONSTITUTION (SSOT)**:
> "EXAM1, EXAM2, EXAM3, EXAM4는 서로의 입력/출력/상태를 절대 공유하지 않는다."

**Definitions**:
- **EXAM1 (EX1)**: 진입/선택/의도 결정 (라우팅만)
- **EXAM2 (EX2)**: 조건 기반 탐색 및 차이 발견 (탐색 전용)
- **EXAM3 (EX3)**: 고객 전달용 보고서 (보고서 전용)

**EX2_DETAIL** (단일 보험사 설명) is a subset of EXAM2. It MUST NOT share state with EX3_COMPARE (multi-insurer comparison).

**STEP NEXT-129R (Customer Self-Test Flow)**:
> "고객이 스스로 테스트 가능한 흐름 (Customer Self-Test Flow)"

**Rules**:
- ❌ NO forced routing based on data structure
- ❌ NO silent payload correction
- ❌ NO auto-send on button clicks
- ✅ User action required for all transitions
- ✅ Predictable UX (same input → same behavior, reproducible)

## Definition of Success

> "삼성화재 암진단비 설명해줘"를 10번 반복해도 EX3_COMPARE 화면이 1번도 안 나오고, 매번 EX2_DETAIL (단일 보험사 설명)만 나오면 성공"

**Success Metrics**:
1. Single-insurer explanation queries → EX2_DETAIL 100%
2. EX3_COMPARE routing when single insurer + explanation → 0%
3. Context reset on explicit insurer mention → 100%
4. Clarification shown when slots missing → 100%
5. User-reported confusion: "왜 비교가 나왔지?" → 0 reports

## Regression Prevention

### Tests to Run
1. ✅ CHECK-138-1: Single-insurer explanation (CRITICAL)
2. ✅ CHECK-138-2: Multi-insurer comparison
3. ✅ CHECK-138-3: Context reset (CRITICAL)
4. ✅ CHECK-138-4: Explanation without insurer
5. ✅ CHECK-138-5: Comparison without insurer
6. ✅ CHECK-138-6: Routing guard (CRITICAL)

### Critical Test Cases
- **T1 (CHECK-138-1)**: This is the reported regression — must pass 100%
- **T3 (CHECK-138-3)**: Context carryover was root cause — must verify reset
- **T6 (CHECK-138-6)**: Routing guard enforcement — must block EX3

### Preserved Features
- ✅ STEP NEXT-129R (Customer Self-Test Flow)
- ✅ STEP NEXT-133 (Slot-Driven Clarification)
- ✅ STEP NEXT-102 (Insurer Switch)
- ✅ STEP NEXT-106 (Multi-Select Insurer)

## Notes

### Why EX1_DETAIL (not EX2_DETAIL)?
- `EX2_DETAIL` is the backend message kind (composer output)
- `EX1_DETAIL` is the frontend exam type (intent detection)
- Naming reflects frontend entry point (EX1 → user's initial query)

### Why Parse Insurers from Message?
- Previous approach: Only used locked context → carryover bug
- New approach: Parse from message → explicit mention = context reset
- Aligns with STEP NEXT-129R (NO silent correction, predictable UX)

### Why Routing Guard?
- Detection alone insufficient (could be overridden by context)
- Guard enforces intent (single insurer + explanation = EX2_DETAIL ONLY)
- Prevents accidental multi-insurer context from forcing EX3

## Future Work

### Potential Enhancements (NOT in scope)
- ❌ Auto-suggest 2nd insurer when user says "비교해줘" with 1 insurer
- ❌ Smart context preservation (e.g., "같은 담보로 메리츠는?")
- ❌ LLM-based intent classification

### Expansion Readiness
- Insurer parsing supports all 8 insurers (samsung, meritz, hanwha, hyundai, kb, lotte, heungkuk)
- Coverage parsing supports common keywords (암진단비, 암직접입원비, 수술비, etc.)
- Easy to add new explanation keywords ("어떤지", "궁금해", etc.)

## SSOT Lock Date
**2026-01-04**

**Lock Status**: ✅ FINAL (ABSOLUTE)

Any changes to single-insurer explanation routing logic MUST:
1. Cite STEP NEXT-138
2. Provide regression test evidence
3. Update this document with new STEP number
