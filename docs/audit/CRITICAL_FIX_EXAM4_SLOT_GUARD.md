# CRITICAL FIX: EXAM4 Slot Guard (coverage_topic vs coverage_code)

**Date**: 2026-01-04
**Scope**: EXAM4 clarification message logic (frontend)
**Type**: CRITICAL UX FIX

---

## Problem (CRITICAL)

**User Requirement**:
> "EXAM4는 coverage_topic 기반 질의이다"
> "coverage_topic(예: 제자리암, 경계성종양)가 이미 선택된 경우, '추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요'는 잘못된 메시지다"

**Current Behavior (WRONG)**:
- User: "제자리암, 경계성종양 비교해줘"
- System detects: disease_subtypes=["제자리암", "경계성종양"] (RESOLVED)
- System detects: insurers=[] (MISSING)
- **Message shown**: "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요." ❌

**Problem**:
1. ❌ Asks for "담보" when disease_subtypes already resolved
2. ❌ Does not distinguish EXAM4 (coverage_topic) from EX2/EX3 (coverage_code)
3. ❌ User confusion: "I already specified disease types, why ask for coverage again?"

---

## Solution (CRITICAL FIX)

### Core Distinction

**EXAM4 ≠ EXAM2/EXAM3**:
- **EXAM4**: `coverage_topic` (disease subtypes: 제자리암, 경계성종양)
- **EXAM2/3**: `coverage_code` (담보: 암진단비, 수술비)

**Slot types**:
- EXAM4: `disease_subtypes` + `insurers`
- EXAM2/3: `coverage` + `insurers`

### Fixed Message Logic

```typescript
if (clarState.examType === "EX4") {
  // EXAM4 ONLY: coverage_topic-based
  if (clarState.missingSlots.disease_subtypes && clarState.missingSlots.insurers) {
    clarificationMessage = "추가 정보가 필요합니다.\n질병 종류와 보험사를 선택해주세요.";
  } else if (clarState.missingSlots.disease_subtypes) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 질병 종류를 선택해주세요.";
  } else if (clarState.missingSlots.insurers) {
    // CRITICAL: disease_subtypes already resolved, only insurers missing
    clarificationMessage = "비교할 보험사를 선택해주세요.";
  }
} else {
  // EX2/EX3: coverage_code-based
  if (clarState.missingSlots.coverage && clarState.missingSlots.insurers) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요.";
  } else if (clarState.missingSlots.coverage) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 담보를 입력해주세요.";
  } else if (clarState.missingSlots.insurers) {
    clarificationMessage = "추가 정보가 필요합니다.\n비교할 보험사를 선택해주세요.";
  }
}
```

---

## Core Rules (ABSOLUTE)

### EXAM4 Rules
1. ✅ **coverage_topic = disease subtypes** (제자리암, 경계성종양)
2. ✅ **NO "담보" in EXAM4 messages** (use "질병 종류" instead)
3. ✅ **Subtypes resolved + insurers missing → "비교할 보험사를 선택해주세요."**
4. ❌ **NO coverage re-ask** when disease_subtypes already resolved

### EX2/EX3 Rules
1. ✅ **coverage_code = 담보** (암진단비, 수술비)
2. ✅ **Use "담보" in messages**
3. ✅ **Coverage resolved + insurers missing → "비교할 보험사를 선택해주세요."**

---

## Test Cases (All PASS)

### Test 1: EX4 - Both missing ✅
```
Exam: EX4
Missing: disease_subtypes + insurers
Expected: "추가 정보가 필요합니다.\n질병 종류와 보험사를 선택해주세요."
Got: "추가 정보가 필요합니다.\n질병 종류와 보험사를 선택해주세요."
```

### Test 2: EX4 - Only subtypes missing ✅
```
Exam: EX4
Missing: disease_subtypes
Expected: "추가 정보가 필요합니다.\n비교할 질병 종류를 선택해주세요."
Got: "추가 정보가 필요합니다.\n비교할 질병 종류를 선택해주세요."
```

### Test 3: EX4 - Only insurers missing (CRITICAL) ✅
```
Exam: EX4
Missing: insurers
Resolved: disease_subtypes = ["제자리암", "경계성종양"]
Expected: "비교할 보험사를 선택해주세요."
Got: "비교할 보험사를 선택해주세요."
```

**CRITICAL CHECK**:
- ✅ NO "담보" in message
- ✅ NO "추가 정보가 필요합니다" prefix (subtypes already resolved)

### Test 4: EX3 - Both missing ✅
```
Exam: EX3
Missing: coverage + insurers
Expected: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
Got: "추가 정보가 필요합니다.\n비교할 담보와 보험사를 선택해주세요."
```

### Test 5: EX3 - Only insurers missing ✅
```
Exam: EX3
Missing: insurers
Resolved: coverage = ["암진단비"]
Expected: "추가 정보가 필요합니다.\n비교할 보험사를 선택해주세요."
Got: "추가 정보가 필요합니다.\n비교할 보험사를 선택해주세요."
```

---

## Examples

### Example 1: EXAM4 Flow (제자리암, 경계성종양)

**User input**: "제자리암, 경계성종양 비교해줘"

**System detects**:
- examType: EX4
- disease_subtypes: ["제자리암", "경계성종양"] (RESOLVED)
- insurers: [] (MISSING)

**OLD message (WRONG)**:
```
추가 정보가 필요합니다.
비교할 담보와 보험사를 선택해주세요.
```

**NEW message (CORRECT)**:
```
비교할 보험사를 선택해주세요.
```

**Why correct**:
1. ✅ NO "담보" (EXAM4 uses coverage_topic, not coverage_code)
2. ✅ NO "추가 정보가 필요합니다" prefix (disease_subtypes already resolved)
3. ✅ Only asks for what's missing (insurers)

---

### Example 2: EXAM3 Flow (암진단비)

**User input**: "암진단비 비교해줘"

**System detects**:
- examType: EX3
- coverage: ["암진단비"] (RESOLVED)
- insurers: [] (MISSING)

**Message (CORRECT)**:
```
추가 정보가 필요합니다.
비교할 보험사를 선택해주세요.
```

**Why correct**:
1. ✅ Uses "담보" terminology (coverage_code-based)
2. ✅ Shows "추가 정보가 필요합니다" prefix (standard for EX2/EX3)
3. ✅ Only asks for what's missing (insurers)

---

## Implementation

**File**: `apps/web/app/page.tsx`

**Lines**: 192-216

**Changes**:
1. Added `if (clarState.examType === "EX4")` branch
2. EXAM4-specific messages (질병 종류 instead of 담보)
3. CRITICAL: When disease_subtypes resolved + insurers missing → SHORT message (NO prefix)

---

## Scope

### Modified
- ✅ `apps/web/app/page.tsx` (clarification message logic, line 192-216)

### NOT Modified
- ❌ Backend logic (apps/api/**)
- ❌ Slot detection (apps/web/lib/clarificationUtils.ts) - ALREADY CORRECT
- ❌ UI rendering (message display ONLY)

---

## Definition of Success

> "EXAM4에서 '제자리암, 경계성종양 비교해줘' 입력 시 '비교할 보험사를 선택해주세요.' 메시지만 표시. '담보' 노출 0%."

---

## Verification Checklist

For EXAM4 clarification:
1. ✅ NO "담보" in message (use "질병 종류" instead)
2. ✅ When disease_subtypes resolved + insurers missing → SHORT message
3. ✅ NO coverage re-ask when disease_subtypes resolved
4. ✅ Message adapts to exam type (EX4 vs EX2/EX3)

---

## Constitutional Basis

- **EXAM CONSTITUTION**: "EXAM4 = 질병 하위개념 보장 가능 여부 (O/X)"
- **Slot types**: EXAM4 uses `coverage_topic` (disease subtypes), NOT `coverage_code` (담보)
- **User requirement**: "EXAM4에서 coverage_code 또는 담보 재선택 요구 금지"

---

## Regression Prevention

- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ EX2/EX3 unchanged (coverage_code-based flow)
- ✅ Frontend ONLY (NO backend changes)
- ✅ TypeScript build succeeded

---

**CRITICAL FIX STATUS**: ✅ COMPLETE (2026-01-04)
