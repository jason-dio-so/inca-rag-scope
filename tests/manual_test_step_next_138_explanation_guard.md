# STEP NEXT-138: Single-Insurer Explanation Guard — Manual Test Plan

## Problem Statement
**REGRESSION**: "삼성화재 암진단비 설명해줘" → EXAM2 비교 화면 노출 (삼성+메리츠)

Expected: EX2_DETAIL (single-insurer detail view)
Actual: EX3_COMPARE (multi-insurer comparison)

## Root Causes Identified
1. **Missing explanation intent detection**: `detectExamType()` did not check for "설명", "알려줘"
2. **Context carryover**: Previous conversation insurers (e.g., samsung+meritz) carried over when user explicitly mentions single insurer
3. **No routing guard**: No guard to FORCE EX2_DETAIL when single insurer + explanation intent

## Fixes Applied

### 1. Detection Logic (`apps/web/lib/clarificationUtils.ts`)
- Added `EX1_DETAIL` exam type for single-insurer explanation queries
- Added explanation keywords: "설명해", "설명", "알려줘", "알려주세요"
- Priority: Explanation (without comparison keywords) → EX1_DETAIL

### 2. Context Reset Logic (`apps/web/lib/clarificationUtils.ts`)
- Added `parseInsurersFromMessage()` to extract insurers from current query
- Updated `deriveClarificationState()` to prioritize parsed insurers over locked context
- **RULE**: If insurers explicitly mentioned in message → RESET context (NO carry-over)

### 3. Routing Guard (`apps/web/app/page.tsx`)
- Added STEP NEXT-138 routing guard in `handleSend()`
- **RULE 1**: Single insurer + explanation → FORCE EX2_DETAIL (block EX3_COMPARE)
- **RULE 2**: 2+ insurers + comparison → allow EX3_COMPARE
- **RULE 3**: Explicit insurer mention → CLEAR previous multi-insurer context

## Manual Test Cases

### T1: Single-Insurer Explanation (CRITICAL REGRESSION FIX)
**Input**: "삼성화재 암진단비 설명해줘"

**Expected Behavior**:
1. `detectExamType()` → returns `"EX1_DETAIL"`
2. `parseInsurersFromMessage()` → returns `["samsung"]`
3. `resolvedInsurers` → `["samsung"]` (single insurer)
4. `showClarification` → `false` (all slots resolved)
5. Routing guard → clears any previous multi-insurer context
6. **Final Result**: EX2_DETAIL view for samsung (NO comparison)

**Verification Steps**:
1. Start fresh session (no previous context)
2. Type: "삼성화재 암진단비 설명해줘"
3. Send query
4. **CHECK**: Left bubble shows EX2_DETAIL content (explanation, NOT comparison)
5. **CHECK**: Right panel shows single-insurer detail (NO comparison table)
6. **CHECK**: Console log shows `examType: "EX1_DETAIL"`, `insurers: ["samsung"]`

### T2: Multi-Insurer Comparison
**Input**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**Expected Behavior**:
1. `detectExamType()` → returns `"EX3"` (comparison intent overrides explanation)
2. `parseInsurersFromMessage()` → returns `["samsung", "meritz"]`
3. `resolvedInsurers` → `["samsung", "meritz"]` (2 insurers)
4. `showClarification` → `false` (all slots resolved)
5. **Final Result**: EX3_COMPARE view (comparison mode)

**Verification Steps**:
1. Type: "삼성화재와 메리츠화재 암진단비 비교해줘"
2. Send query
3. **CHECK**: Left bubble shows EX3 comparison summary
4. **CHECK**: Right panel shows comparison table (2 insurers side-by-side)
5. **CHECK**: Console log shows `examType: "EX3"`, `insurers: ["samsung", "meritz"]`

### T3: Context Reset on Explicit Insurer (CRITICAL)
**Input (after T2)**: "삼성화재 수술비 설명해줘"

**Expected Behavior**:
1. Previous context: `lockedInsurers: ["samsung", "meritz"]` (from T2)
2. New query explicitly mentions "삼성화재"
3. `parseInsurersFromMessage()` → returns `["samsung"]`
4. `resolvedInsurers` → `["samsung"]` (RESET to single insurer, NOT ["samsung", "meritz"])
5. Routing guard → detects single insurer + explanation → FORCE EX2_DETAIL
6. **Final Result**: EX2_DETAIL view for samsung only (NO meritz)

**Verification Steps**:
1. After T2 (comparison between samsung+meritz)
2. Type: "삼성화재 수술비 설명해줘"
3. Send query
4. **CHECK**: Context reset occurs (samsung ONLY, meritz dropped)
5. **CHECK**: Left bubble shows EX2_DETAIL (explanation, NOT comparison)
6. **CHECK**: Console log shows `insurers: ["samsung"]` (NOT ["samsung", "meritz"])

### T4: Explanation Without Insurer (Clarification Required)
**Input**: "설명해줘"

**Expected Behavior**:
1. `detectExamType()` → returns `"EX1_DETAIL"`
2. `parseInsurersFromMessage()` → returns `[]` (no insurer)
3. `resolvedInsurers` → `null`
4. `missingSlots.insurers` → `true`
5. `showClarification` → `true`
6. **Final Result**: Clarification panel asking for insurer selection

**Verification Steps**:
1. Start fresh session
2. Type: "설명해줘"
3. Send query
4. **CHECK**: Clarification panel appears
5. **CHECK**: Message: "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요."

### T5: Comparison Without Insurer (Clarification Required)
**Input**: "암진단비 비교해줘"

**Expected Behavior**:
1. `detectExamType()` → returns `"EX3"`
2. `parseInsurersFromMessage()` → returns `[]` (no insurer)
3. `parseCoverageFromMessage()` → returns `["암진단비"]`
4. `resolvedInsurers` → `null`
5. `missingSlots.insurers` → `true` (need 2+ insurers for EX3)
6. `showClarification` → `true`
7. **Final Result**: Clarification panel asking for insurer selection

**Verification Steps**:
1. Start fresh session
2. Type: "암진단비 비교해줘"
3. Send query
4. **CHECK**: Clarification panel appears
5. **CHECK**: Message: "추가 정보가 필요합니다. 비교할 보험사를 선택해주세요."

### T6: Single Insurer MUST NOT Route to EX3
**Input**: "삼성화재 암진단비 설명해줘" (with payload `insurers: ["samsung"]`)

**Expected Behavior**:
1. `detectExamType()` → returns `"EX1_DETAIL"` (NOT EX3)
2. Routing guard → confirms single insurer + explanation intent
3. **Final Result**: EX2_DETAIL view (NEVER EX3_COMPARE)

**Verification Steps**:
1. Type: "삼성화재 암진단비 설명해줘"
2. Send query
3. **CHECK**: NEVER shows EX3_COMPARE (comparison view)
4. **CHECK**: ALWAYS shows EX2_DETAIL (explanation view)

## Code Changes Summary

### Modified Files
1. `apps/web/lib/clarificationUtils.ts`:
   - Added `EX1_DETAIL` exam type
   - Added `parseInsurersFromMessage()` function
   - Updated `detectExamType()` to detect explanation intent
   - Updated `deriveClarificationState()` to reset context when insurers explicitly mentioned

2. `apps/web/app/page.tsx`:
   - Added STEP NEXT-138 routing guard in `handleSend()`
   - Enforces single-insurer + explanation → FORCE EX2_DETAIL
   - Clears multi-insurer context when single insurer explicitly mentioned

### Created Files
1. `tests/manual_test_step_next_138_explanation_guard.md` (this file)

## Definition of Success
> "삼성화재 암진단비 설명해줘"를 10번 반복해도 EX3_COMPARE 화면이 1번도 안 나오고, 매번 EX2_DETAIL (단일 보험사 설명)만 나오면 성공"

## Regression Prevention
- All 6 test cases must pass
- T1 (single-insurer explanation) is CRITICAL — this was the regression
- T3 (context reset) is CRITICAL — prevents carry-over bugs
- T6 (routing guard) is CRITICAL — prevents accidental EX3 routing

## Next Steps
1. Manual verification of all 6 test cases
2. Create SSOT documentation: `docs/audit/STEP_NEXT_138_SINGLE_INSURER_EXPLANATION_GUARD.md`
3. Update `CLAUDE.md` with STEP NEXT-138 reference
