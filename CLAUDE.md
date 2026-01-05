# CLAUDE Context – inca-rag-scope

# EXAM CONSTITUTION (SSOT)

본 시스템에서 EXAM은 서로 독립적인 문제 유형이다.

- EXAM1, EXAM2, EXAM3, EXAM4는 서로의 입력/출력/상태를 절대 공유하지 않는다.
- 하나의 EXAM 결과가 다른 EXAM의 입력으로 사용되는 것은 금지된다.
- "정리/확장/보고서화/자연스럽게 이어짐" 같은 표현을 근거로 EXAM 간 연결을 추측하지 않는다.
- EXAM 간 전환은 오직 사용자 명시 동작(버튼/선택)으로만 가능하다.

**정의**:
- **EXAM1 (EX1)**: 진입/선택/의도 결정 (라우팅만)
- **EXAM2 (EX2)**: 조건 기반 탐색 및 차이 발견 (탐색 전용) — **추가정보 플로우 금지 (ABSOLUTE)**
- **EXAM3 (EX3)**: 고객 전달용 보고서 (보고서 전용)
- **EXAM4 (EX4)**: 가능/불가 (O/X) 판단 (OX 전용)

**이 헌법을 위반하는 설계/코드/설명은 버그로 간주한다.**

**⚠️ EXAM RULE NOTICE (MANDATORY)**
- 본 작업은 지정된 EXAM에 한정된다.
- 다른 EXAM(EXAM1/2/3/4)을 참조/연계/혼합하는 것은 금지된다.
- 문서에 명시되지 않은 EXAM 전환은 구현하지 않는다.
- 불명확하면 추측하지 말고 질문한다.

---

# EXECUTION BASELINE (SSOT)

This file defines the **current reality** of the system.
Any output that contradicts this baseline is considered a **bug or hallucination**.

---

## 0. STEP NEXT-129R: Customer Self-Test Flow (SSOT Rollback) — **2026-01-04**

**New Constitutional Principle**:
> "고객이 스스로 테스트 가능한 흐름 (Customer Self-Test Flow)"

**Supersedes and ROLLBACK**:
- ~~STEP NEXT-121: Comparison Intent Hard-Lock~~ (ROLLED BACK)
- ~~STEP NEXT-125: Forced EX3 Routing~~ (ROLLED BACK)
- ~~STEP NEXT-126: EX3 Fixed Bubble Template Override~~ (ROLLED BACK)
- ~~STEP NEXT-128: Bubble/Table Consistency with Template Override~~ (ROLLED BACK)

**Core Rules (ABSOLUTE)**:
1. ❌ **NO forced routing** based on data structure (insurers≥2 does NOT force EX3)
2. ❌ **NO silent payload correction** (NO extraction from message to inject into payload)
3. ❌ **NO need_more_info bypass** (ALWAYS show clarification UI when backend requests it)
4. ❌ **NO frontend override** of backend bubble_markdown (Backend is SSOT)
5. ❌ **NO auto-send** on example button clicks (Fill input ONLY)
6. ✅ **Backend bubble_markdown is SSOT** for all message content
7. ✅ **User action required** for all transitions (button clicks, not auto-routing)
8. ✅ **Predictable UX** (same input → same behavior, reproducible)

**Implementation Status**:
- Backend: IntentRouter.route() simplified (removed forced EX3 routing)
- Frontend: Removed silent payload correction, need_more_info bypass, EX3 template override
- EX1 Landing: 1 line + 3 example buttons (fill input ONLY, NO auto-send)
- EX4: O/X eligibility table (COMPLETE - STEP NEXT-130)

**SSOT Document**: `docs/audit/STEP_NEXT_129R_CUSTOMER_SELF_TEST_SSOT.md`

**Rationale**:
The system evolved toward "demo auto-complete" where frontend/backend bypassed user choices to complete flows automatically. This created unpredictable UX where users could not understand why certain screens appeared. STEP NEXT-129R restores customer self-test capability.

---

## 0.1 STEP NEXT-130: EX4 O/X Eligibility Table — **2026-01-04**

**Purpose**: Customer self-test for disease subtype eligibility (제자리암/경계성종양)

**Core Rules (ABSOLUTE)**:
1. ✅ **Fixed 5 rows**: 진단비, 수술비, 항암약물, 표적항암, 다빈치수술 (order LOCKED)
2. ✅ **O/X only**: Binary eligibility (NO △/Unknown/조건부)
3. ✅ **Fixed 2 insurers**: samsung, meritz (demo mode)
4. ✅ **Deterministic keyword matching**: NO LLM, NO inference
5. ✅ **Display names ONLY**: 삼성화재, 메리츠화재 (NO code exposure)
6. ✅ **Left bubble: 2-4 sentences**: Short guidance only
7. ✅ **Evidence refs attached**: PD:{insurer}:{coverage_code} format
8. ❌ **NO recommendation/judgment**: "유리", "불리", "추천" 금지
9. ❌ **NO pipeline/data changes**: View layer ONLY

**Category Keywords (Deterministic)**:
- 진단비: `["진단", "진단비"]`
- 수술비: `["수술", "수술비"]`
- 항암약물: `["항암", "약물", "항암약물", "화학", "화학요법"]`
- 표적항암: `["표적", "표적항암", "표적치료"]`
- 다빈치수술: `["다빈치", "로봇", "로봇수술"]`

**O/X Logic** (STEP NEXT-131 Update):
- **O**: `category_keyword IN coverage_name_raw` ONLY (담보 존재 여부)
- **X**: Coverage not found (NO LLM fallback, NO △/Unknown allowed)
- **Subtype conditions**: Guided in Notes section (NOT in O/X logic)

**Rationale** (STEP NEXT-131):
- STEP NEXT-130: Too strict (category AND subtype) → All X
- STEP NEXT-131: Relaxed (category ONLY) → Mix O/X, useful overview
- Disease subtype guidance → Notes: "세부 조건은 약관 확인"

**Multi-Disease Support** (STEP NEXT-132):
- **Input**: `subtype_keywords: List[str]` (e.g., `["제자리암", "경계성종양"]`)
- **Output**: One O/X table section per disease (NO single-disease reduction)
- **Example**: "제자리암, 경계성종양 비교해줘" → 2 tables (NO EX2 fallback)

**Implementation**:
- **Composer**: `apps/api/response_composers/ex4_eligibility_composer.py` (REPLACED)
- **Tests**: `tests/test_step_next_130_ex4_ox_table.py` (8/8 PASS)
- **SSOT**: `docs/audit/STEP_NEXT_130_EX4_OX_TABLE_LOCK.md` + `STEP_NEXT_131_EX4_RELAXED_LOGIC.md` + `STEP_NEXT_132_EX4_MULTI_DISEASE.md`

**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)

**Definition of Success**:
> "고객이 표를 10초 안에 읽고 'O는 지원, X는 미지원'을 즉시 이해하면 성공"

---

## 0.2 STEP NEXT-A: Unified Exam Entry UX (EX1 → EX2/EX3/EX4) — **2026-01-04**

**Purpose**: Unify entry UX for all exam types when starting from EX1 (first impression screen)

**Core Problem**:
- EX1 → EX2/EX3/EX4 buttons had inconsistent UX
- Some immediately showed results (bypassing selection)
- Some showed clarification panels with different messages
- Customer testing requires predictable, uniform entry flow

**Solution**:
- **ALL exam types show same "추가 정보가 필요합니다" message** when starting from EX1
- User must select coverage/insurers and click send BEFORE any composer is called
- Entry difference occurs ONLY after selection complete (in result display)

**Core Rules (ABSOLUTE)**:
1. ✅ **Unified entry message**: ALL exams use same "추가 정보가 필요합니다. 비교할 담보와 보험사를 선택해주세요."
2. ✅ **NO immediate results**: EX1 buttons NEVER trigger composer calls directly
3. ✅ **Selection required**: User must choose insurers + coverage explicitly
4. ✅ **NO auto-send**: Buttons fill input ONLY (129R compliant)
5. ✅ **NO auto-routing**: Frontend gates entry BEFORE backend decides intent
6. ✅ **Exam differences appear in results**: EX2/EX3/EX4 diverge AFTER selection, NOT before
7. ❌ **NO different entry messages** for EX2 vs EX3 vs EX4
8. ❌ **NO immediate composer calls** from EX1 buttons

**Detection Logic** (deterministic):
```typescript
const isInitialEntry = messages.length === 0;

const isEX2Intent = messageToSend.includes("담보 중") || messageToSend.includes("보장한도가 다른");
const isEX3Intent = messageToSend.includes("비교") || messageToSend.includes("차이");
const isEX4Intent = messageToSend.includes("보장여부") || messageToSend.includes("보장내용에 따라");

if (isInitialEntry && (isEX2Intent || isEX3Intent || isEX4Intent)) {
  // Show unified entry gate
}
```

**Requirements per Exam**:
- **EX3**: 2 insurers + 1 coverage
- **EX2/EX4**: 1+ insurers + 1 coverage (or disease name for EX4)

**Implementation**:
- **Modified Files**: `apps/web/app/page.tsx` (unified exam entry gate logic)
- **Backend Changes**: ❌ FORBIDDEN (NO apps/api/** changes)
- **SSOT**: `docs/audit/STEP_NEXT_A_UNIFIED_EXAM_ENTRY_LOCK.md`

**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)

**Definition of Success**:
> "EX1 → EX2/EX3/EX4 모두 동일한 '추가 정보가 필요합니다' 메시지 표시. 백엔드 호출 0회 (선택 완료 전까지). Entry UX = 100% 동일."

---

## 0.2.1 STEP NEXT-A-α: EX1 Simplified Example Text — **2026-01-04**

**Purpose**: Remove insurer names from EX1 to avoid premature decision-making

**Core Change**:
- **Before**: "삼성화재와 메리츠화재 암진단비 비교해줘"
- **After**: "암진단비 비교해줘"

**Rationale**:
1. EX1 = "WHAT" to compare (coverage) ← User focuses here
2. Entry Gate = "WHO" to compare (insurers) ← User decides in next step
3. Expansion-ready: Not bound to 2 specific insurers
4. Clear flow: Question → Selection → Results

**Core Rules (ABSOLUTE)**:
1. ✅ **NO insurer names in EX1** (example buttons, placeholder)
2. ✅ **EX1 asks WHAT**: User specifies coverage
3. ✅ **Gate asks WHO**: User selects insurers explicitly
4. ❌ **NO "삼성/메리츠 기준 예시"** language
5. ❌ **NO premature insurer commitment** in first screen

**Implementation**:
- **Modified Files**: `apps/web/components/ChatPanel.tsx` (2 text changes)
- **Backend Changes**: ❌ NONE (text-only)
- **SSOT**: `docs/audit/STEP_NEXT_A_ALPHA_EX1_SIMPLIFIED_TEXT_LOCK.md`

**Constitutional Basis**: STEP NEXT-A (Unified Exam Entry UX)

**Definition of Success**:
> "EX1 화면에 보험사명 0개. '암진단비 비교해줘' 클릭 → 추가 정보 요청 → 보험사 선택. 자연스러운 단계별 진행."

---

## 0.3 STEP NEXT-133: Slot-Driven Clarification UI — **2026-01-04** (FINAL)

**Purpose**: Fix clarification UI to be **slot-driven** instead of showing fixed form, preventing re-asking for resolved slots

**Supersedes**: STEP NEXT-A (Unified Exam Entry — extended with slot-driven logic)

**Core Problem**:
- Current bug: Coverage already resolved ("암진단비 비교해줘") → clarification UI still shows coverage input
- Fixed form approach: Always shows both insurers + coverage UI regardless of what's already known
- Hardcoded text: "(2개 선택)" assumes current 2-insurer limitation (expansion blocker)

**Solution**:
- **Missing-slot detection**: `deriveClarificationState()` utility determines which slots are resolved vs missing
- **Dynamic UI**: Only show UI for missing slots (resolved slots NEVER re-asked)
- **No hardcoded count**: Remove "(2개 선택)" text (validation stays internal)

**Core Rules (ABSOLUTE)**:
1. ✅ **Resolved Slot Non-Reask** (절대 원칙): If coverage resolved → coverage UI NEVER shown
2. ✅ **Clarification UI = Dynamic Panel**: Only render UI for `missingSlots` fields
3. ✅ **No Hardcoded Count**: Remove "(2개 선택)" from UI text (internal validation only)
4. ✅ **Unified Logic**: Same slot-driven approach for EX1→EX2/EX3/EX4
5. ✅ **No Demo Auto-Complete**: NO auto-send, NO silent correction, NO forced routing (129R preserved)
6. ❌ **NO re-ask for resolved slots**: Coverage="암진단비" → coverage UI = 0% exposure
7. ❌ **NO hardcoded insurer count**: "(2개 선택)" FORBIDDEN
8. ❌ **NO backend changes**: apps/api/** UNTOUCHED

**Detection Logic** (deterministic):
```typescript
const clarState = deriveClarificationState({
  requestPayload: draftPayload,
  lastResponseVm: null,
  lastUserText: messageToSend,
  conversationContext,
});

// Exam type: EX2/EX3/EX4 (keyword-based)
// Missing slots: { insurers: boolean, coverage: boolean, disease_subtypes: boolean }
// Resolved slots: { insurers: string[] | null, coverage: string[] | null, ... }
```

**UI Rendering** (LOCKED):
```typescript
{clarState.missingSlots.insurers && (
  <div>보험사 선택</div>  // NO "(2개 선택)"
)}

{clarState.missingSlots.coverage && (
  <div>담보명</div>  // NO "(1개)"
)}

<button>확인</button>  // NO count in text
```

**Implementation**:
- **NEW**: `apps/web/lib/clarificationUtils.ts` (slot detection logic)
- **MODIFIED**: `apps/web/app/page.tsx` (slot-driven clarification gate)
- **Backend Changes**: ❌ FORBIDDEN (NO apps/api/** changes)
- **SSOT**: `docs/audit/STEP_NEXT_133_SLOT_DRIVEN_CLARIFICATION.md`

**Verification Scenarios**:
- ✅ CHECK-EX3-CLARIFY-1: "암진단비 비교해줘" → 보험사 선택 ONLY (담보 UI 0% 노출)
- ✅ CHECK-EX3-CLARIFY-2: 보험사 2개 선택 → 확인 → EX3 결과 표시
- ✅ CHECK-EX4-MULTI-SUBTYPE-1: "제자리암, 경계성종양 비교" → 2개 서브타입 모두 표시
- ✅ CHECK-EX2-NO-REASK-1: "암직접입원비 보장한도 비교" → 담보 UI 0% 노출

**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)

**Definition of Success**:
> "Coverage가 resolved된 케이스에서 담보 선택 UI 노출 0%. EX3 진입 시 '보험사 선택만' 요구."

**Regression Prevention**:
- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction, NO forced routing)
- ✅ STEP NEXT-A preserved (Unified exam entry UX)
- ✅ STEP NEXT-102/106 preserved (Insurer switch, multi-select)

---

## 0.3.1 STEP NEXT-138: Single-Insurer Explanation Guard (CRITICAL REGRESSION FIX) — **2026-01-04**

**Purpose**: Fix regression where single-insurer explanation queries route to comparison mode

**Root Problem**:
- **Input**: "삼성화재 암진단비 설명해줘"
- **Expected**: EX2_DETAIL (single-insurer detail view)
- **Actual**: EX3_COMPARE (multi-insurer comparison with 삼성+메리츠)

**Root Causes**:
1. Missing explanation intent detection ("설명", "알려줘" patterns)
2. Context carryover (previous multi-insurer context overrides explicit single-insurer mention)
3. No routing guard to FORCE EX2_DETAIL when single insurer + explanation

**Solution**:
1. **Added EX1_DETAIL exam type** for single-insurer explanation queries
2. **Context reset logic**: Parse insurers from message → explicit mention = reset context
3. **TWO routing guards**:
   - Guard 1 (Initial entry, first message)
   - Guard 2 (Ongoing conversation, follow-up messages) ← **CRITICAL FIX**

**Core Rules (ABSOLUTE)**:
1. ✅ **Single insurer + explanation → FORCE EX2_DETAIL** (NEVER EX3_COMPARE)
2. ✅ **EX3 requires BOTH**: insurer_count ≥ 2 AND comparison signal ("비교", "차이")
3. ✅ **Explicit insurer mention → RESET context** (NO carryover)
4. ✅ **EX1_DETAIL detection**: "설명해", "설명", "알려줘", "알려주세요"
5. ❌ **NO forced comparison** when single insurer + explanation
6. ❌ **NO context carryover** when insurers explicitly mentioned

**Detection Priority**:
1. `isExplanation && !isEX3` → EX1_DETAIL (explanation without comparison keywords)
2. `isEX3` → EX3 (comparison overrides explanation)
3. `isEX4` → EX4
4. `isEX2` → EX2

**Insurer Resolution Priority** (STEP NEXT-138):
1. `payloadInsurers` (explicit selection)
2. `parsedInsurers` (mentioned in message) ← **NEW (context reset)**
3. `lockedInsurers` (conversation context)

**Implementation**:
- **Modified**: `apps/web/lib/clarificationUtils.ts` (EX1_DETAIL type, parseInsurersFromMessage, detectExamType)
- **Modified**: `apps/web/app/page.tsx` (TWO routing guards: initial + ongoing)
- **Modified**: `apps/web/lib/contextUtils.ts` (exported extractInsurersFromMessage)
- **Tests**: `tests/manual_test_step_next_138_explanation_guard.md` (6 test cases)
- **SSOT**: `docs/audit/STEP_NEXT_138_SINGLE_INSURER_EXPLANATION_GUARD.md`

**Verification Scenarios**:
- ✅ CHECK-138-1: "삼성화재 암진단비 설명해줘" → EX2_DETAIL (NO EX3)
- ✅ CHECK-138-2: "삼성화재와 메리츠화재 암진단비 비교해줘" → EX3_COMPARE
- ✅ CHECK-138-3: After EX3, "삼성화재 수술비 설명해줘" → context reset to single insurer
- ✅ CHECK-138-4: "설명해줘" (no insurer) → clarification required
- ✅ CHECK-138-5: "암진단비 비교해줘" (no insurer) → clarification required
- ✅ CHECK-138-6: Single insurer + explanation → NEVER routes to EX3

**Constitutional Basis**: EXAM CONSTITUTION (EXAM2/EX3 NO state sharing) + STEP NEXT-129R (Predictable UX)

**Definition of Success**:
> "삼성화재 암진단비 설명해줘"를 10번 반복해도 EX3_COMPARE 화면이 1번도 안 나오고, 매번 EX2_DETAIL만 나오면 성공"

**Regression Prevention**:
- ✅ STEP NEXT-129R preserved (NO forced routing, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ STEP NEXT-102 preserved (Insurer switch)
- ✅ STEP NEXT-106 preserved (Multi-select insurer)

---

## 0.3.3 STEP NEXT-141: EX4 Preset Routing Lock + Clarification UI Fix — **2026-01-05**

**Purpose**: Lock EX4 preset button routing to 100% confidence, remove coverage input from EX4 clarification

**Root Problem**:
- EX4 preset ("제자리암, 경계성종양 보장여부 비교해줘") relied on keyword-based detectExamType
- Could be overridden by stronger EX3 signals ("비교") or EX1_DETAIL (single insurer)
- Clarification UI showed "담보와 보험사를 선택해주세요" (wrong - disease subtypes already resolved)

**Solution (Frontend ONLY)**:
1. **Preset button LOCK**: Click EX4 preset → set `draftExamType="EX4"` → bypass detectExamType
2. **Routing priority**: `draftExamType` (preset) > `detectExamType` (free-text fallback)
3. **Clarification UI**: Hide coverage input for EX4 (insurers-only selection)
4. **Reset**: Clear `draftExamType` after send (prevent contamination)

**Core Rules (ABSOLUTE)**:
1. ✅ **Preset button = explicit intent** (100% confidence, NO heuristics)
2. ✅ **EX4 clarification = insurers ONLY** (disease subtypes already in message)
3. ✅ **draftExamType reset** after send (NO carryover to next query)
4. ✅ **Free-text fallback preserved** (detectExamType for manual queries)
5. ❌ **NO keyword-based preset detection** ("if message.includes('제자리암')")
6. ❌ **NO coverage input UI for EX4** (disease subtypes ≠ coverage_code)
7. ❌ **NO "담보와 보험사" copy for EX4** (insurers-only message)

**Implementation**:
- **MODIFIED**: `apps/web/app/page.tsx`
  - Added `draftExamType` state
  - Override `clarState.examType` when `forcedExamType` present
  - Hide coverage input: `{... && examType !== "EX4"}`
  - Reset in finally block: `setDraftExamType(null)`
- **MODIFIED**: `apps/web/components/ChatPanel.tsx`
  - Added `onPresetClick` prop
  - EX4 preset button calls `onPresetClick("EX4")`
  - EX2/EX3 presets NO lock (rely on detectExamType)
- **SSOT**: `docs/audit/STEP_NEXT_141_EX4_PRESET_LOCK.md`

**Verification Scenarios**:
- ✅ S1: EX4 preset 10 clicks → 10/10 route to EX4 (NOT EX3/EX1_DETAIL)
- ✅ S2: EX4 clarification message → "비교할 보험사를 선택해주세요" (NO "담보와")
- ✅ S3: EX4 clarification UI → insurers buttons ONLY (NO coverage input field)
- ✅ S4: EX2/EX3 presets → NO draftExamType lock (heuristics work)
- ✅ S5: After send → draftExamType reset (NO contamination)

**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow) + STEP NEXT-133 (Slot-driven clarification)

**Definition of Success**:
> "EX4 프리셋 클릭 10/10 → EX4 처리 (EX3/EX1_DETAIL 0%). Clarification에서 담보 입력 요구 0%."

**Regression Prevention**:
- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification for free-text)
- ✅ STEP NEXT-138 preserved (Single-insurer explanation guard)
- ✅ EX2/EX3 detectExamType logic unchanged

---

## 0.3.4 STEP NEXT-138-γ: EXAM3 AMOUNT/LIMIT Dimension Separation (Backend) — **2026-01-04**

**Purpose**: Fix semantic confusion where AMOUNT (정액금액: "3천만원") and LIMIT (한도: "보험기간 중 1회") were mixed in the same table row, violating the report principle "한 행은 반드시 동일 의미·동일 차원이어야 한다".

**Core Problem**:
- Samsung: "보험기간 중 1회" (LIMIT)
- Meritz: "3천만원" (AMOUNT)
- **Same row compares different dimensions** (횟수 vs 금액) ← SEMANTIC VIOLATION

**Solution (Backend)**:
1. **Dimension Tagging**: AMOUNT | LIMIT | MIXED detection
2. **Main Table (AMOUNT-only)**: 핵심 보장 내용 shows ONLY AMOUNT
3. **Separate LIMIT Section**: 보장 한도 section (below main table)
4. **Structural Basis (AMOUNT-first)**: "보장금액(정액) 기준" vs "지급 한도/횟수 기준"

**Core Rules (ABSOLUTE)**:
1. ✅ **Main table shows ONLY AMOUNT** (핵심 보장 내용 = 정액금액)
2. ✅ **LIMIT in separate section** (보장 한도 = 한도/횟수)
3. ✅ **NO mixing AMOUNT and LIMIT in same cell** (ABSOLUTE)
4. ✅ **AMOUNT-first structural basis** (보장금액 > 지급한도 priority)
5. ❌ **NO dimension mixing** ("3천만원 (보험기간 중 1회)" FORBIDDEN)
6. ❌ **NO EXAM2/EX4 impact** (EXAM3 ONLY)

**Implementation**:
- **MODIFIED**: `apps/api/response_composers/ex3_compare_composer.py`
  - Added `_tag_dimension()` method
  - Modified `_build_table_section()` (AMOUNT-only main table)
  - Added `_build_limit_section()` (separate LIMIT section)
- **MODIFIED**: `apps/api/chat_vm.py` (Added "LIMIT_INFO" to TableKind Literal)
- **SSOT**: `docs/audit/STEP_NEXT_138_GAMMA_EX3_AMOUNT_LIMIT_SEPARATION.md`

**Verification Scenarios**:
- ✅ CHECK-138-γ-1: "삼성화재와 메리츠화재 암진단비 비교해줘" → 핵심 보장 내용 = amounts ONLY, 보장 한도 = limits ONLY
- ✅ CHECK-138-γ-2: Coverage with ONLY LIMIT → main table shows limit (fallback)
- ✅ CHECK-138-γ-3: Coverage with ONLY AMOUNT → limit section NOT shown
- ✅ CHECK-138-γ-4: Asymmetric dimensions → clear separation in different sections

**Definition of Success**:
> "Samsung vs Meritz 암진단비 비교에서 '핵심 보장 내용' 행에 '3천만원'만 표시되고, '보험기간 중 1회'는 별도 '보장 한도' 섹션에만 표시되면 성공"

---

## 0.3.3 STEP NEXT-139C: EXAM3 Backend Formatting Fix (FINAL) — **2026-01-04**

**Purpose**: Fix EX3 formatting at the SOURCE (backend ViewModel creation), NOT in frontend normalization.

**Root Cause (Evidence-Based)**:
- DevTools Network payload showed `cells[].text` as `"LUMP_SUM"` (raw enum)
- Amounts inconsistent: `"3,000만원 (30,000,000원)"` vs `"3천만원"` (mixing formats)
- Backend composer was sending unformatted strings directly to cells

**Solution (Backend Fix)**:
Applied formatting in `apps/api/response_composers/ex3_compare_composer.py` where cell text is created.

**Formatting Rules (LOCKED)**:

### Rule 1: LIMIT + AMOUNT Combination (139A)
```
Pattern: Both limit and amount exist
Output: "{한도 설명} (일당 {금액})"

Example: "보험기간 중 1회 (일당 2만원)"
```

### Rule 2: 일당형 Amount Prefix (139B)
```
Pattern: payment_type = "일당형"
Output: "일당 {금액}"

Example: "일당 2만원"
```

### Rule 3: Korean-Only Amount Display (139B)
```
Pattern: Amount with numeric parenthetical
Output: Strip numeric part

Example: "3천만원 (30,000,000원)" → "3천만원"
```

### Rule 4: Payment Type Label Substitution (139B)
```
Pattern: Raw payment_type label
Output: Korean label

Examples:
- "LUMP_SUM" → "정액 지급"
- "일당형" → "일당 지급"
- "UNKNOWN" → "표현 없음"
```

**Core Rules (ABSOLUTE)**:
1. ✅ **NO raw enum values in cells**: `"LUMP_SUM"` → `"정액 지급"`
2. ✅ **Korean-only amounts**: `"3천만원 (30,000,000원)"` → `"3천만원"`
3. ✅ **일당형 prefix**: `"2만원"` → `"일당 2만원"` (when payment_type = 일당형)
4. ✅ **Consistent formatting**: ALL amounts use same format (no mixing)
5. ❌ **NO numeric parentheticals**: `(30,000,000원)` FORBIDDEN in final display
6. ❌ **NO raw payment_type**: `LUMP_SUM`, `UNKNOWN` FORBIDDEN in cells

**Implementation**:
- **MODIFIED**: `apps/api/response_composers/ex3_compare_composer.py`
  - Added `format_payment_type()` function (lines 435-447)
  - Updated `format_amount_display()` with Korean-only stripping (lines 392-405)
  - Updated `format_limit_display()` with Korean-only stripping (lines 539-541)
- **REVERTED**: `apps/web/lib/normalize/table.ts` (removed frontend formatting - unnecessary)
- **Build Status**: ✅ Backend syntax OK, Frontend build succeeded
- **SSOT**: `docs/audit/STEP_NEXT_139C_BACKEND_FORMATTING_FIX.md`

**Verification (Network Payload)**:
- ✅ cells[].text shows `"정액 지급"` (NOT `"LUMP_SUM"`)
- ✅ cells[].text shows `"3천만원"` (NOT `"3천만원 (30,000,000원)"`)
- ✅ cells[].text shows `"일당 2만원"` for 일당형 (NOT `"2만원"`)
- ✅ NO comma formats: `"3,000만원"` = 0%

**Definition of Success**:
> "Network payload의 `cells[].text` 필드에서 `LUMP_SUM` 0%, `3,000만원` 0%, `(30,000,000원)` 0%이면 성공."

---

## 0.4 STEP NEXT-134: EXAM2 "찾아줘" Query Routing Lock + Context Isolation — **2026-01-04**

**Purpose**: Prevent EXAM2 "search/discovery" queries from routing to wrong intent and using previous context

**Core Problem**:
- "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" → routed to `EX2_DETAIL_DIFF` (comparison, NOT search)
- Response uses `A4200_1` (암진단비) from previous EX3 context, NOT `A6200` (암직접입원일당)
- Coverage mismatch: Query asks for "암직접입원일당", system uses "암진단비"

**Solution**:
- **Gate 2 (STEP NEXT-134)**: "찾아줘/발굴/다른 상품" patterns → `EX2_LIMIT_FIND` (ABSOLUTE, 100% confidence)
- **Coverage extraction**: `extract_coverage_name_from_message()` extracts from CURRENT message ONLY (NO carryover)
- **Coverage code mapping**: Added `A6200` (암직접입원일당), `A6100_1` (입원일당)

**Core Rules (ABSOLUTE)**:
1. ✅ **"찾아줘" = search intent → EX2_LIMIT_FIND** (NOT EX2_DETAIL_DIFF)
2. ✅ **Coverage from current message ONLY** (NO previous context carryover)
3. ✅ **Auto-expand insurers to all 8** if not specified
4. ✅ **Deterministic coverage extraction** (NO LLM)
5. ✅ **Handler respects routed kind** (kind from compiled_query, NOT hardcoded)
6. ❌ **NO context carryover** from previous EX3/EX4 messages
7. ❌ **NO "보장한도" (field) as coverage_name** (must be actual coverage like "암직접입원일당")

**Search Patterns** (Gate 2):
```python
search_patterns = [
    r"찾아줘", r"찾아주세요", r"찾아주",
    r"다른\s*상품", r"있는\s*상품", r"발굴",
    r"보장한도가?\s*다른", r"차이가?\s*나는\s*상품"
]
```

**Implementation**:
- **MODIFIED**: `apps/api/chat_intent.py` (Gate 2 + coverage extraction + mappings)
- **MODIFIED**: `apps/api/chat_handlers_deterministic.py` (Handler kind lock - respects routed intent)
- **SSOT**: `docs/audit/STEP_NEXT_134_EXAM2_LIMIT_FIND_ROUTING_LOCK.md`

**Verification Scenarios**:
- ✅ "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" → `EX2_LIMIT_FIND` + `A6200` refs (NOT A4200_1)
- ✅ After EX3 (암진단비) → EXAM2 query → NO A4200_1 carryover (context isolation)
- ✅ "삼성화재와 메리츠화재 암직접입원일당 보장한도 비교해줘" → `EX2_DETAIL_DIFF` OK (comparison intent clear)

**Constitutional Basis**: EXAM CONSTITUTION (EXAM2 = 탐색/발굴, NO context sharing)

**Definition of Success**:
> "'암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘'를 10번 반복해도 A4200_1 refs가 1번도 안 나오고, 매번 A6200 refs만 나오면 성공"

---

## 0.5 STEP NEXT-135-β: EXAM2 Coverage Code Resolution Lock (FINAL) — **2026-01-04**

**Purpose**: Fix A4200_1 contamination in EX2_LIMIT_FIND evidence refs when query asks for different coverage

**Supersedes**: STEP NEXT-135 (partial fix - missed EX2_DETAIL_DIFF)

**Core Problem**:
- "암직접입원일당 담보 중... 찾아줘" → Evidence refs use `PD:samsung:A4200_1` (암진단비)
- **Expected**: `PD:samsung:A6200` (암직접입원일당)
- **Root Cause (DOUBLE BUG)**:
  1. `QueryCompiler.compile()` line 580 did NOT include `EX2_DETAIL_DIFF` in coverage_code compilation condition
  2. Handler fallback: `coverage_code = compiled_query.get("coverage_code", "A4200_1")` → Always fallback to 진단비
  3. Result: 암직접입원일당 query → A4200_1 refs (contamination)

**Solution (STEP NEXT-135-β)**:
1. **QueryCompiler Fix**: Add `"EX2_DETAIL_DIFF"` to coverage_code compilation condition
   - Line 582: `if kind in ["EX3_COMPARE", "EX2_DETAIL", "EX2_DETAIL_DIFF", "EX2_LIMIT_FIND"]:`
2. **Handler Fallback Removal**: Remove ALL `coverage_code = compiled_query.get("coverage_code", "A4200_1")` patterns
   - Replaced with explicit `ValueError` when coverage_code missing
   - 3 handlers fixed: Example2DiffHandlerDeterministic, Example3HandlerDeterministic, Example2DetailHandlerDeterministic

**Core Rules (ABSOLUTE)**:
1. ✅ **Coverage code MUST be compiled** for ALL EX2 intents (EX2_LIMIT_FIND, EX2_DETAIL_DIFF, EX2_DETAIL)
2. ✅ **Evidence refs MUST match query coverage** (NO A4200_1 fallback contamination)
3. ✅ **Coverage extraction from current message ONLY** (STEP NEXT-134 preserved)
4. ✅ **Deterministic coverage name → code mapping** (NO LLM)
5. ❌ **NO coverage_code omission** for ANY EX2 kind in compiled_query
6. ❌ **NO A4200_1 fallback EVER** (ABSOLUTE FORBIDDEN)

**Implementation**:
- **MODIFIED**: `apps/api/chat_intent.py` (Line 582: Added "EX2_DETAIL_DIFF" to condition)
- **MODIFIED**: `apps/api/chat_handlers_deterministic.py` (Removed A4200_1 fallbacks × 3)
- **TESTS**: `tests/test_step_next_135_exam2_coverage_resolve_lock.py` (9/12 PASS - core tests 100%)
- **SSOT**: `docs/audit/STEP_NEXT_135_EXAM2_COVERAGE_RESOLVE_LOCK.md`

**Verification Results (STEP NEXT-135-β)**:
- ✅ "암직접입원일당..." → A4200_1 refs = **0%** (10회 반복)
- ✅ "암직접입원일당..." → A6200 refs = **100%**
- ✅ "암진단비..." → A4200_1 refs = **100%** (regression OK)
- ✅ EX2_DETAIL_DIFF coverage_code compilation verified
- ✅ Handler ValueError on missing coverage_code (NO silent fallback)

**Constitutional Basis**: EXAM CONSTITUTION (Coverage resolution MUST match query, NO fallback contamination)

**Definition of Success**:
> "Coverage code compilation prevents A4200_1 fallback. Evidence refs always match user query coverage."

---

## 1. Active Architecture (as of STEP NEXT-79)

### Primary Data
- coverage_cards_slim.jsonl  ← **Primary comparison input**
- proposal_detail_store.jsonl ← 가입설계서 DETAIL 원문 저장소
- evidence_store.jsonl        ← 근거 스니펫 저장소

### Access Rule
- All DETAIL / EVIDENCE access is **ref-based only**
  - PD:{insurer}:{coverage_code}
  - EV:{insurer}:{coverage_code}:{idx}

❌ No direct raw text embedding in cards  
❌ No full coverage_cards.jsonl usage

---

## 2. Data Flow (Authoritative)

Step5 (Slim Cards + refs)
 → Store Loader (in-memory)
 → API (lazy load by ref)
 → UI (modal / toggle)

---

## 3. KPI Implementation (COMPLETE)

### KPI Summary (STEP NEXT-74)
- payment_type (정액형 / 일당형 / 건별 / 실손 / UNKNOWN)
- limit_summary
- kpi_evidence_refs

### KPI Condition (STEP NEXT-76)
- exclusion_condition
- waiting_period
- reduction_condition
- renewal_type

Rules:
- Deterministic only (regex-based)
- Priority: Proposal DETAIL → Evidence
- UNKNOWN must be explicit, never inferred

---

## 4. /chat API Rules

- /chat MUST operate on Slim Cards output
- Judgment is based on:
  - customer_view
  - kpi_summary
  - kpi_condition
- raw_text is **supplementary only**

### STEP NEXT-77: EX3_COMPARE Response Schema Lock

- **SSOT**: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md`
- **Composer**: `apps/api/response_composers/ex3_compare_composer.py`
- **MessageKind**: `EX3_COMPARE` (added to `chat_vm.py`)
- **Rules**:
  - ❌ NO raw text in response body (refs only)
  - ✅ All refs use `PD:` or `EV:` prefix
  - ✅ KPI section (optional) with refs
  - ✅ Table rows with `meta.proposal_detail_ref` + `meta.evidence_refs`
  - ✅ Deterministic only (NO LLM)

### STEP NEXT-78: Intent Router Lock + EX2_LIMIT_FIND

- **SSOT**: `docs/ui/INTENT_ROUTER_RULES.md`
- **Composer**: `apps/api/response_composers/ex2_limit_find_composer.py`
- **MessageKind**: `EX2_LIMIT_FIND` (added to `chat_vm.py`)
- **Intent Separation** (Anti-Confusion Gates):
  - EX2_LIMIT_FIND: 보장한도/조건 **값 차이 비교** (NO O/X)
  - EX4_ELIGIBILITY: 질병 하위개념 **보장 가능 여부** (O/X/△)
- **Routing Priority**:
  1. Explicit kind (100%)
  2. Category (100%)
  3. Anti-confusion gates (100%)
  4. Pattern matching (fallback)
- **Rules**:
  - ❌ NO O/X/△ in EX2_LIMIT_FIND output
  - ✅ Disease subtypes (제자리암, 유사암, etc.) → EX4_ELIGIBILITY
  - ✅ "보장한도 다른" → EX2_LIMIT_FIND
  - ✅ Intent is LOCKED (cannot be overridden)

### STEP NEXT-79: EX4_ELIGIBILITY Overall Evaluation Lock

- **SSOT**: `docs/audit/STEP_NEXT_79_EX4_OVERALL_EVALUATION_LOCK.md`
- **Composer**: `apps/api/response_composers/ex4_eligibility_composer.py`
- **MessageKind**: `EX4_ELIGIBILITY` (already in `chat_vm.py`)

### STEP NEXT-86/96/113: EX2_DETAIL Lock (담보 설명 전용 모드 + ChatGPT UX)

- **SSOT**:
  - `docs/ui/STEP_NEXT_86_EX2_LOCK.md` (Base lock - DEPRECATED by STEP NEXT-113)
  - `docs/ui/STEP_NEXT_96_EX2_CUSTOMER_FIRST_ORDER.md` (Customer-first ordering - PRESERVED in sections)
  - `docs/audit/STEP_NEXT_113_EX2_CHATGPT_UX_LOCK.md` (ChatGPT UX redesign - CURRENT SSOT)
- **Composer**: `apps/api/response_composers/ex2_detail_composer.py`
- **Handler**: `apps/api/chat_handlers_deterministic.py::Example2DetailHandlerDeterministic`
- **MessageKind**: `EX2_DETAIL` (added to `chat_vm.py`)
- **Intent Routing**:
  - `insurers = 1` → **EX2_DETAIL** (설명 전용)
  - `insurers ≥ 2` + "차이/비교" → **EX2_LIMIT_FIND** or **EX3_COMPARE**
- **STEP NEXT-113: ChatGPT UX Structure Redesign (LOCKED)**:
  - **Left Bubble** = Conversational summary ONLY (2-3 sentences, NO tables/lists)
  - **Right Panel** = All detailed info (보장 요약 + 조건 요약 + 근거 자료)
  - **NO duplication** between bubble and sections
  - **Product Header**: 보험사 · 담보명 · 기준 (STEP NEXT-110A preserved)
  - **Conversational Tone**: "이 담보는..." + "정액으로..." + "조건이 적용됩니다"
- **Rules**:
  - ❌ NO comparison / recommendation / judgment
  - ❌ NO coverage_code exposure (e.g., "A4200_1") in UI
  - ❌ NO tables/lists/sections in bubble_markdown (STEP NEXT-113)
  - ❌ NO specific condition values in bubble (e.g., "50%", "90일")
  - ✅ Lightweight bubble (2-3 sentences, readable in 10 seconds)
  - ✅ refs MUST use `PD:` / `EV:` prefix
  - ✅ "표현 없음" / "근거 없음" when missing data
  - ✅ Deterministic only (NO LLM)
- **STEP NEXT-96: Customer-First KPI Ordering (PRESERVED in sections)**:
  - **보장 요약 순서**: 보장금액 (NEW) → 보장한도 → 지급유형
  - **보장금액** displayed FIRST in right panel (when available)
  - View layer ONLY (NO business logic change)
- **Definition**:
  > EX2_DETAIL = "ChatGPT처럼 대화로 시작하는 담보 설명"
  > 왼쪽 말풍선 = 설명 (conversation), 오른쪽 패널 = 상세 (drill-down)
  > 비교·추천·판단은 EX3 / EX4 전용
- **Contract Tests**:
  - `tests/test_step_next_113_ex2_chatgpt_ux.py` (10 tests, all PASS - CURRENT SSOT)
  - `tests/test_ex2_bubble_contract_DEPRECATED_STEP_NEXT_113.py` (DEPRECATED - expects sections in bubble)
  - `tests/test_step_next_96_customer_first_order_DEPRECATED_STEP_NEXT_113.py` (DEPRECATED - expects sections in bubble)

### STEP NEXT-94/95: Coverage Grouping UX (담보 군집화) Lock

- **SSOT**: `docs/audit/STEP_NEXT_94_COVERAGE_GROUPING_LOCK.md`
- **Runtime Proof**: `docs/audit/STEP_NEXT_95_GROUPING_RUNTIME_PROOF.md`
- **Utility**: `apps/api/response_composers/utils.py::assign_coverage_group()`
- **Applied to**: EX4_ELIGIBILITY bubble_markdown ONLY
- **NOT Applied to**: EX2_DETAIL, EX2_LIMIT_FIND, EX3_COMPARE (단일 담보 설계)

**Core Rules**:
- ❌ NO business logic change (view layer ONLY)
- ❌ NO LLM usage (deterministic keyword matching)
- ❌ NO grouping in judgment/comparison logic
- ✅ 3 groups max: "진단 관련 담보", "치료/수술 관련 담보", "기타 담보"
- ✅ Single group → NO header, Multiple groups → show headers
- ✅ Group label is display text ONLY (not used in statistics/judgment)

### STEP NEXT-112/113: EX3_COMPARE Comparison-First UX Lock (FINAL LOCK)

- **SSOT**:
  - `docs/audit/STEP_NEXT_112_EX3_COMPARISON_FIRST_LOCK.md` (Base lock - SUPERSEDED by STEP NEXT-113)
  - `docs/audit/STEP_NEXT_113_FINAL_LOCK_EX2_EX3_UX_REBUILD.md` (CURRENT SSOT - FINAL LOCK)
- **Composer**: `apps/api/response_composers/ex3_compare_composer.py::_build_bubble_markdown()`
- **MessageKind**: `EX3_COMPARE` (already in `chat_vm.py`)
- **Supersedes**: STEP NEXT-82 (deprecated bubble format), STEP NEXT-112 (intermediate lock)
- **Scope**: View Layer ONLY (bubble_markdown format redesign)

**STEP NEXT-113 FINAL LOCK (Structural UX Rebuild)**:
- **Left Bubble**: 6-7 lines max (lightweight conversation, NO tables)
- **Right Panel**: Side-by-side comparison table (horizontal, NO card layout)
- **NO "일부 보험사는..."**: Explicit insurer names ONLY
- **Structural comparison**: "{Insurer1}는... {Insurer2}는..." pattern

**Bubble Structure (LOCKED)**:
```markdown
메리츠화재는 진단 시 **정해진 금액을 지급하는 구조**이고,
삼성화재는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**

**즉,**
- 메리츠화재: 지급 금액이 명확한 정액 구조
- 삼성화재: 지급 조건 해석이 중요한 한도 구조
```

**Rules (FINAL LOCK)**:
- ❌ NO "일부 보험사는..." (ABSOLUTE FORBIDDEN)
- ❌ NO vertical cards (1 insurer per card)
- ❌ NO tables in left bubble (table is in right panel ONLY)
- ❌ NO recommendations / superiority judgments
- ❌ NO coverage_code / insurer_code in bubble_markdown (refs OK)
- ✅ Explicit insurer names in structural summary
- ✅ 6-7 lines max in left bubble
- ✅ Side-by-side table in right panel (same row = direct comparison)
- ✅ Deterministic only (NO LLM)

**Structural Basis Detection** (deterministic priority):
1. `amount != "명시 없음"` → **보장금액 기준**
2. `limit_summary exists` → **지급 한도 기준**
3. `payment_type != "UNKNOWN"` → **{payment_type} 방식**
4. Fallback → **기본 보장 방식**

**Contract Tests**:
- Manual verification PASS (EX3 bubble format compliant)
- Right panel table: horizontal comparison (NO card layout)
- Left bubble: 6 lines (within 6-7 line limit)
- NO "일부 보험사는..." found

**Definition of Success (FINAL LOCK)**:
> "말풍선만 읽어도 '차이'를 설명할 수 있고, 표를 보면 한눈에 대비가 된다"

### STEP NEXT-97: Customer Demo UX Stabilization (UI/Flow ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_97_DEMO_UX_STABILIZATION.md`
- **Modified Files**:
  - `apps/web/components/ChatPanel.tsx` (auto-scroll + context lock)
  - `apps/web/components/SidebarCategories.tsx` (collapsible sidebar)
  - `apps/web/lib/normalize/table.ts` (kpi_condition type fix)
- **Rules**:
  - ✅ Left sidebar collapsed by default (12px, demo mode)
  - ✅ Auto-scroll on new bubble (only if user near bottom, threshold 100px)
  - ✅ Conversation context lock (insurer selector disabled after first message)
  - ✅ Visual indicator: "현재 대화 조건: 삼성화재 · 메리츠화재"
  - ✅ "조건 변경" button → confirm → page reload
  - ❌ NO backend/API/business logic change
  - ❌ NO LLM usage
  - ❌ NO data structure change
- **Definition of Success**:
  > "고객이 설명 없이 1분 안에 써보고 '아, 이렇게 쓰는 거구나' 라고 말하면 성공"

### STEP NEXT-98: Question Continuity Hints (View Layer Text ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_98_QUESTION_CONTINUITY_LOCK.md`
- **Modified Files**:
  - `apps/api/response_composers/ex2_detail_composer.py` (question hints in bubble_markdown)
  - `apps/api/response_composers/ex4_eligibility_composer.py` (subtype expansion hints in bubble_markdown)
- **Rules**:
  - ✅ EX2_DETAIL: 설명 → 탐색 연결 (보장한도 차이 질문 힌트)
  - ✅ EX4_ELIGIBILITY: 판단 → 조건 확장 비교 연결 (subtype 확장 힌트)
  - ✅ 순수 텍스트 힌트만 (NO 버튼, NO 자동 실행)
  - ✅ 고객이 그대로 복사해 물어도 동작
  - ❌ NO 자동 질문 실행
  - ❌ NO 추천/점수/랭킹
  - ❌ NO EX2 ↔ EX4 자동 점프
  - ❌ NO LLM usage
  - ❌ NO business logic change
- **Definition of Success**:
  > "답변은 닫고, 질문은 연다 — 시스템은 사고의 다음 계단만 보여준다"
- **Tests**: 19 contract tests PASS (7 EX2 + 12 EX4, all PASSED)

### STEP NEXT-99: 고객 데모용 대표 질문 시나리오 LOCK (Docs ONLY)

- **SSOT**: `docs/ui/STEP_NEXT_99_DEMO_QUESTION_FLOW.md`
- **Audit**: `docs/audit/STEP_NEXT_99_DEMO_LOCK.md`
- **Scope**: Demo Flow / Docs / Example UX ONLY (NO code changes)
- **3 Locked Scenarios**:
  - **Scenario A**: EX2 → EX3 → EX2 (설명 → 직접 비교 → 탐색 확장)
  - **Scenario B**: EX4 → EX3 → EX2 (판단 → 비교 → 구조 이해)
  - **Scenario C**: EX3 단독 (비교 핵심 강조)
- **Rules**:
  - ✅ EX3 positioned as central step (비교가 핵심)
  - ✅ All scenarios use single coverage × multiple insurers (EX3 constitutional lock)
  - ✅ Demo scripts for 1-min / 3-min / 5-min presentations
  - ✅ Frontend example buttons already aligned
  - ❌ NO functional changes (ZERO code modified)
  - ❌ NO auto-execution / buttons / recommendations
  - ❌ NO LLM usage
  - ❌ NO Intent boundary violations
- **Definition of Success**:
  > "EX2(설명) → EX3(비교) → EX4(판단), 3가지 Intent가 자연스럽게 이어지는 질문 흐름이 곧 제품의 핵심 UX다"
- **Code Changes**: ZERO (documentation only)
- **Tests**: 19/19 PASS (unchanged)

### STEP NEXT-100: Frontend Payload Bug Fix (View Layer ONLY)

- **SSOT**: `docs/audit/STEP_NEXT_100_PAYLOAD_FIX.md`
- **Modified Files**: `apps/web/app/page.tsx` (3 changes)
- **Root Cause**:
  1. Clarification 선택 후 UI state (`selectedInsurers`, `coverageInput`) 미업데이트
  2. `undefined` 값이 `JSON.stringify`에서 자동 제거됨
- **Fixes**:
  - ✅ `handleClarificationSelect`: UI state 동기화 (setCoverageInput, setSelectedInsurers)
  - ✅ `handleSend`: Request payload builder SSOT (state capture before async)
  - ✅ Auto-retry 로직: `need_more_info` 반환 시 클라이언트 값으로 1회 자동 재시도
- **Rules**:
  - ❌ NO backend/API change
  - ❌ NO LLM usage
  - ✅ View layer ONLY (frontend only)
  - ✅ Auto-retry 최대 1회 (무한 루프 방지)
- **Tests**: 3/3 PASS (manual_test_step_next_100_payload.py)
- **Definition of Success**:
  > "Payload에 insurers/coverage_names 누락 = 0회, 고객 데모에서 추가 정보 필요 오판 노출 = 0회"

### STEP NEXT-101: Conversation Context Carryover (Frontend) + Example Sync Lock

- **SSOT**: `docs/audit/STEP_NEXT_101_CONTEXT_CARRYOVER.md`
- **Modified Files**: `apps/web/app/page.tsx` (5 changes)
- **Root Cause**:
  - Example button은 payload에 값 주입하지만 UI state 미업데이트
  - Follow-up 질문 시 state 비어있음 → payload 누락 → need_more_info 오발생
- **Fixes**:
  - ✅ `ConversationContext` state 추가 (lockedInsurers, lockedCoverageNames, isLocked)
  - ✅ `buildChatPayload` SSOT 함수 (우선순위: override → UI state → locked context)
  - ✅ `handleSendWithKind`: Example button 클릭 시 UI state 동기화 + context locking
  - ✅ `handleSend`: buildChatPayload 사용 + 간소화 + context locking
  - ✅ `handleClarificationSelect`: context locking 추가
- **Context Lock Trigger**: 첫 성공 응답 (`need_more_info=false` + `insurers` 존재)
- **Context Unlock**: "조건 변경" 버튼 → page reload
- **Rules**:
  - ❌ NO backend change
  - ❌ NO LLM usage
  - ✅ View layer ONLY (state/payload/UX)
  - ✅ Payload builder는 단일 함수 (SSOT)
  - ✅ Context 유지 (사용자가 unlock하기 전까지)
- **Definition of Success**:
  > "Example button → 답변 → Follow-up 타이핑 → 전송 흐름이 추가 정보 패널 없이 자연스럽게 연결"

### STEP NEXT-102: EX2 Context Continuity Lock (Frontend) — Insurer Switch + LIMIT_FIND Validation

- **SSOT**: `docs/ui/STEP_NEXT_102_EX2_CONTEXT_CONTINUITY_LOCK.md`
- **Modified Files**:
  - `apps/web/lib/contextUtils.ts` (NEW): 4 deterministic pattern matchers
  - `apps/web/app/page.tsx` (3 changes)
- **Root Cause**:
  1. Insurer switch 미지원 ("메리츠는?" → 삼성 유지)
  2. LIMIT_FIND 단일 보험사 오류 (2사 필요한데 1사만 context에 존재)
  3. Clarification handler 덮어쓰기 (삼성 → 메리츠 replace, 원하는 동작: merge)
- **Fixes**:
  - ✅ `isInsurerSwitchUtterance()`: "메리츠는?" 감지 (deterministic regex)
  - ✅ `extractInsurerFromSwitch()`: 보험사명 → code 변환
  - ✅ `isLimitFindPattern()`: "다른 담보", "한도 차이" 감지 (keyword combination)
  - ✅ `handleSend`: Insurer switch 감지 → context update (보험사만 전환, 담보 유지)
  - ✅ `handleSend`: LIMIT_FIND 감지 → 2사 미만이면 clarification 패널 표시
  - ✅ `handleClarificationSelect`: Insurer merge 로직 (기존 + 신규, replace 금지)
- **Demo Flow**:
  1. EX2 버튼 (삼성 암진단비) → EX2_DETAIL
  2. "메리츠는?" → insurer switch → EX2_DETAIL (meritz)
  3. "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" → LIMIT_FIND 감지 → 1사만 존재 → 보험사 추가 UI → 삼성 선택 → 자동 재전송 (samsung + meritz) → EX2_LIMIT_FIND 표 출력
- **Rules**:
  - ❌ NO LLM usage (deterministic only)
  - ❌ NO backend change
  - ❌ NO coverage_code UI 노출
  - ✅ Insurer switch는 frontend pattern matching
  - ✅ LIMIT_FIND는 2사 이상 보장
  - ✅ Clarification은 merge (not replace)
- **Definition of Success**:
  > "삼성 EX2 → 메리츠는? → LIMIT_FIND 흐름이 추가 정보 패널 없이 자연스럽게 이어진다"

### STEP NEXT-103: EX2 Insurer Switch Payload Override + EX2_DETAIL Display Name Lock

- **SSOT**: `docs/audit/STEP_NEXT_103_EX2_SWITCH_PAYLOAD_PROOF.md`
- **Modified Files**:
  - `apps/web/app/page.tsx` (payload override in handleSend)
  - `apps/api/response_composers/ex2_detail_composer.py` (display name usage)
- **Root Cause**:
  1. Frontend: "메리츠는?" 감지 후 state 업데이트만 하고 payload는 이전 값 전송
  2. Backend: EX2_DETAIL title/summary에서 insurer code (samsung, meritz) 노출
- **Fixes**:
  - ✅ Frontend: Insurer switch 감지 시 `effectiveInsurers`/`effectiveKind` 우선 적용 (payload SSOT)
  - ✅ Backend: `format_insurer_name()` 사용하여 display name (삼성화재, 메리츠화재) 통일
  - ✅ Question hints도 display name 사용 ("삼성화재와 다른 보험사의...")
- **Rules**:
  - ❌ NO insurer code in title/summary/bubble_markdown (samsung, meritz, kb 등)
  - ❌ NO coverage_code exposure (A4200_1 등)
  - ✅ Display names ONLY (삼성화재, 메리츠화재, KB손해보험, 한화손해보험, 현대해상, 롯데손해보험, DB손해보험, 흥국화재)
  - ✅ Insurer codes OK in refs (PD:samsung:, EV:meritz: 등)
  - ✅ Deterministic only (NO LLM)
- **Contract Tests**:
  - `tests/test_ex2_detail_display_name_no_code.py` (7 tests, all PASS)
  - Regression: `tests/test_ex2_bubble_contract.py` (7 tests, all PASS)
  - Regression: `tests/test_step_next_96_customer_first_order.py` (8 tests, all PASS)
- **Definition of Success**:
  > "고객 데모에서 '메리츠는?'를 입력하면 즉시 메리츠 데이터로 전환되고, 응답 타이틀에 '메리츠화재'가 표시된다. 추가 설명 없이 자연스럽다."

### STEP NEXT-104: EX2_DETAIL Followup Hints Demo Flow Lock

- **Modified Files**: `apps/api/response_composers/ex2_detail_composer.py` (followup hints)
- **Root Cause**: Dynamic hints (삼성화재와 다른... / {담보명} 관련 다른...) caused inconsistent demo experience
- **Fix**: LOCK followup hints to fixed demo flow (2 hints, always the same)
  - Hint 1: "메리츠는?" (insurer switch demo)
  - Hint 2: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" (LIMIT_FIND demo)
- **Rules**:
  - ❌ NO dynamic text (hints are FIXED, not based on insurer/coverage_name)
  - ❌ NO auto-execute / NO buttons (text-only hints)
  - ❌ NO placeholders (e.g., {담보명}) — hints must be copy-paste ready
  - ❌ NO insurer codes (samsung, meritz) in hints
  - ✅ Exactly 2 hints (always the same)
  - ✅ Hints guide demo flow: EX2_DETAIL (설명) → 메리츠는? (전환) → LIMIT_FIND (탐색)
  - ✅ Deterministic only (NO LLM)
- **Contract Tests**:
  - `tests/test_step_next_104_ex2_detail_followup_hints.py` (8 tests, all PASS)
  - Regression: `tests/test_ex2_bubble_contract.py` (7 tests, all PASS)
  - Regression: `tests/test_step_next_96_customer_first_order.py` (8 tests, all PASS)
- **Definition of Success**:
  > "EX2_DETAIL 응답 하단 힌트가 항상 '메리츠는?' / '암직접입원비 담보 중 보장한도가 다른 상품 찾아줘' 2줄로 고정된다. 고객이 그대로 복사해서 질문하면 데모 플로우가 자연스럽게 이어진다."

### STEP NEXT-106: Clarification 상태 UI Lock (담보명 입력 Disable) + Multi-Select Insurer

- **SSOT**: `docs/audit/STEP_NEXT_106_CLARIFICATION_COVERAGE_INPUT_LOCK.md`
- **Modified Files**:
  - `apps/web/components/ChatPanel.tsx` (coverage input disabled prop)
  - `apps/web/app/page.tsx` (LIMIT_FIND clarification state tracking + multi-select)
- **Root Cause**:
  1. During LIMIT_FIND clarification, coverage input remained enabled → customer confusion
  2. Insurer selection was single-click instant submit → couldn't select multiple insurers for LIMIT_FIND
- **Fix**:
  1. Disable coverage input field when `isLimitFindPattern === true && insurers.length < 2`
  2. Multi-select insurer UI with "확인 (N개 선택됨)" button
- **Rules**:
  - ❌ NO coverage name re-input during clarification
  - ❌ NO automatic coverage modification
  - ❌ NO backend/API/Intent/Composer changes
  - ✅ View Layer UX Lock ONLY
  - ✅ Coverage input disabled during LIMIT_FIND clarification
  - ✅ Multi-select insurers (toggle selection, blue highlight)
  - ✅ Auto-restore when clarification completes
  - ✅ Context integrity strengthened (single action focus)
- **Constitutional UX Rule**:
  > "Clarification = Single Action Only. During clarification, leave ONLY the action the customer must perform. Lock all other input elements."
- **Definition of Success**:
  > "Clarification 상태에서 담보명 입력 불가. 보험사 복수 선택 가능. 고객이 '담보를 다시 써야 하나요?'라고 묻지 않음. EX2 → 전환 → LIMIT_FIND 데모 흐름 단절 없음."

### STEP NEXT-108: ChatGPT UI 정합 — Left Bubble 강화 + Bottom Dock 최소화

- **SSOT**: `docs/audit/STEP_NEXT_108_CHATGPT_UI_LOCK.md`
- **Modified Files**:
  - `apps/web/components/ChatPanel.tsx` (markdown rendering + collapsible bottom dock)
  - `apps/web/tailwind.config.ts` (NEW - typography plugin)
- **Packages Added**: `react-markdown`, `remark-gfm`, `@tailwindcss/typography`
- **Root Cause**:
  1. Left bubble (말풍선): 빈약 ("제목 + 1~2줄") → 테이블/핵심 값 안 보임
  2. Bottom dock: 화면 절반 차지 → ChatGPT와 다르게 "설문/폼"처럼 보임
- **Fix**:
  1. **Left Bubble Markdown Rendering**: Assistant messages render as markdown (tables, headings, lists, links)
  2. **Bottom Dock Collapsed by Default**: 옵션 ▾ 버튼으로 보험사/담보 선택 숨김, 질문 입력만 노출
- **Rules**:
  - ❌ NO backend비교/판단 로직 변경
  - ❌ NO 추천/추론/스코어링 추가
  - ❌ NO 버튼으로 자동 질문 실행
  - ❌ NO coverage_code UI 노출
  - ❌ NO LLM usage
  - ✅ View Layer ONLY (UI rendering + layout)
  - ✅ Markdown tables in left bubble (미니 요약 카드)
  - ✅ Collapsible options panel (보험사/담보 선택)
  - ✅ ChatGPT-style input (single line, rounded borders)
  - ✅ Chat area occupies majority of screen
- **UI Behavior**:
  - **Initial**: "보험사/담보 선택 ▾" + input → collapsed
  - **Active**: "대화 중: 삼성화재 · 메리츠화재" + "옵션 ▾" + input → collapsed
  - **Expanded**: Click ▾ → shows insurer buttons + coverage input (scrollable, max-h-48)
  - **Left Bubble**: Markdown with tables, prose styles (compact spacing, small font)
- **Definition of Success**:
  > "Left Bubble에 미니 테이블/요약이 즉시 보이고, Bottom Dock이 collapsed 기본값이며, 고객이 'ChatGPT처럼 대화로 진행된다'고 느끼면 성공이다."

### STEP NEXT-110A: Product Header SSOT Lock (Without product_name)

- **SSOT**: `docs/ui/STEP_NEXT_110A_HEADER_SSOT_LOCK.md`
- **Modified Files**:
  - `apps/api/response_composers/ex2_detail_composer.py` (product header at top)
  - `apps/web/components/ChatPanel.tsx` (header styling)
- **Evidence**: grep search confirmed NO product_name data in system
- **Header Structure** (LOCKED):
  ```
  **[보험사 표시명]**
  **담보명**
  _기준: 가입설계서_
  ---
  ```
- **SSOT Priority**:
  1. 보험사: `format_insurer_name(insurer_code)` (삼성화재, 메리츠화재, etc.)
  2. 담보명: `display_coverage_name(coverage_name, coverage_code)` (NO code exposure)
  3. 기준: 고정 "가입설계서" (현재 모든 데이터 source)
  4. 상품명: ❌ NOT IMPLEMENTED (데이터 없음, STEP NEXT-110B로 연기)
- **Rules**:
  - ❌ NO product_name guessing/assuming (evidence-based ONLY)
  - ❌ NO placeholder text (혼란 초래)
  - ❌ NO coverage_code UI 노출
  - ❌ NO LLM usage
  - ❌ NO business logic change
  - ✅ Header MUST be at top of bubble_markdown
  - ✅ Header MUST use display names (NOT codes)
  - ✅ Header structure LOCKED (format + order)
  - ✅ Deterministic only
- **Frontend Styling**:
  - **[보험사]**: Bold, Large (text-lg)
  - **담보명**: Bold, Large
  - _기준_: Italic
  - Horizontal rule (---): Visual separator
- **Tests**: `tests/test_step_next_110a_product_header_contract.py` (5/5 PASS)
  1. Header exists at top
  2. Header uses display names
  3. NO coverage_code in header
  4. Header structure locked
  5. Regression: sections preserved
- **Definition of Success**:
  > "EX2_DETAIL 응답 최상단에 보험사 + 담보명 + 기준이 표시되고, coverage_code 노출 0%, 구조 LOCKED. Product_name은 데이터 없어 STEP NEXT-110B로 연기."

### STEP NEXT-114 / 114B: First Impression Screen UX Lock (ChatGPT Onboarding — Final)

- **SSOT**: `docs/audit/STEP_NEXT_114_FIRST_IMPRESSION_LOCK.md`
- **Modified Files**:
  - `apps/web/components/ChatPanel.tsx` (onboarding bubble + placeholder + removed example buttons)
  - `apps/web/app/page.tsx` (ResultDock visibility + removed handleSendWithKind)
- **Purpose**: Show system identity + example question in **10 seconds** at first screen (ChatGPT-style)
- **Root Cause**:
  - Example buttons made system look like "button demo", not ChatGPT
  - Abstract flow explanation ("설명 → 비교 → 이해") lacked concrete guidance
  - Placeholder "질문을 입력하세요..." too generic
- **114B Fixes (Final Tuning)**:
  - ✅ Conversational tone ("~해 드립니다", "~보세요")
  - ✅ Concrete example question ("삼성화재 암진단비 설명해줘")
  - ✅ Placeholder with same example (immediate action guidance)
  - ✅ Left-aligned bubble (60-65% max width)
  - ✅ Removed "이 도우미는..." introduction tone
- **Onboarding Copy** (LOCKED — 114B Final):
  ```
  보험 상품을 단순히 나열하는 대신,
  보장이 어떻게 정의되어 있는지를 기준으로 비교해 드립니다.

  예를 들어
  "삼성화재 암진단비 설명해줘"
  같은 질문부터 시작해 보세요.
  ```
- **Placeholder** (LOCKED — 114B):
  ```
  예: 삼성화재 암진단비 설명해줘
  ```
- **Rules**:
  - ❌ NO "이 도우미는..." (service introduction tone)
  - ❌ NO "설명 → 비교 → 이해" (abstract flow diagram)
  - ❌ NO example buttons on first screen
  - ❌ NO data/numbers/tables in onboarding
  - ❌ NO bullets/bold in onboarding text
  - ❌ NO LLM usage (fixed text only)
  - ✅ Conversational tone (assistant's first message)
  - ✅ Concrete example question (copy-paste ready)
  - ✅ Left-aligned bubble (ChatGPT style)
  - ✅ Deterministic only
- **Transition Trigger**: User sends first question → onboarding disappears, ResultDock appears
- **Build Status**: ✅ `npm run build` succeeded (no TypeScript errors)
- **Definition of Success** (114B Final):
  > "사용자가 첫 화면에서 10초 안에 '아, 여기다 이렇게 물어보면 되는구나'라고 생각하고 질문을 입력하기 시작하면 성공."

### STEP NEXT-115: EX2→EX3 Comparison Transition Line (Flow Guidance)

- **Modified Files**: `apps/api/response_composers/ex2_detail_composer.py` (bubble_markdown)
- **Purpose**: Guide users naturally from EX2 (explanation) to EX3 (comparison) without recommendation
- **Fix**: Added comparison transition line at end of EX2 bubble (before question hints)
- **Transition Line** (LOCKED):
  ```
  같은 {담보명}라도 보험사마다 '보장을 정의하는 기준'이 달라,
  비교해 보면 구조 차이가 더 분명해집니다.
  ```
- **Rules**:
  - ❌ NO judgment ("더 좋다", "유리하다")
  - ❌ NO recommendation
  - ❌ NO specific numbers/values
  - ❌ NO LLM usage
  - ✅ Explains comparison value (structural difference)
  - ✅ Neutral tone ("~해집니다")
  - ✅ Appears after main explanation, before hints
  - ✅ Deterministic only
- **Tests**: 10/10 PASS (test_step_next_113_ex2_chatgpt_ux.py)
- **Definition of Success**:
  > "EX2 말풍선을 읽은 후 사용자가 '다른 보험사와 비교해봐야겠다'고 자연스럽게 생각하면 성공."

### STEP NEXT-116: EX3 Structural Comparison Summary (Right Panel Header)

- **Modified Files**:
  - `apps/api/response_composers/ex3_compare_composer.py` (structural_summary field)
  - `apps/web/components/ResultDock.tsx` (display structural_summary)
- **Purpose**: Show structural difference framework BEFORE detailed table
- **Fix**: Added `structural_summary` field to EX3_COMPARE response, displayed at top of right panel
- **Summary Template** (LOCKED):
  ```
  이 비교에서는 {보험사1}는 '{구조1}'이고,
  {보험사2}는 '{구조2}'입니다.
  ```
- **Structural Basis Detection** (Deterministic):
  1. `amount != "명시 없음"` → "정액 지급 방식"
  2. `limit_summary exists` → "지급 한도 기준"
  3. `payment_type != "UNKNOWN"` → "{payment_type} 방식"
  4. Fallback → "기본 보장 방식"
- **Frontend Display**:
  - Location: Top of ResultDock (EX3_COMPARE only)
  - Style: Blue background box (bg-blue-50, border-blue-100)
  - Font: text-xs, blue-900
  - Margin: -mt-2 (visually connected to title section)
- **Rules**:
  - ❌ NO "일부 보험사는..." (vague language)
  - ❌ NO recommendation / superiority judgment
  - ❌ NO specific numbers (3천만, 1회 etc.) in summary
  - ❌ NO LLM usage
  - ✅ Explicit insurer names
  - ✅ Structural description only
  - ✅ Appears before table
  - ✅ Deterministic only
- **Tests**: Manual verification PASS (structural_summary appears before table)
- **Definition of Success**:
  > "사용자가 표를 보기 전에 '아, 구조가 다르구나'를 먼저 이해하면 성공."

### STEP NEXT-117: Onboarding Copy FINAL LOCK (Action-First, No-Think UX)

- **SSOT**: `docs/audit/STEP_NEXT_117_ONBOARDING_FINAL_LOCK.md`
- **Modified Files**: `apps/web/components/ChatPanel.tsx` (onboarding bubble)
- **Purpose**: Eliminate thinking/reading step, trigger immediate first question
- **Root Cause**:
  - Previous copy (114B) explained service philosophy ("보장이 어떻게 정의되어 있는지...")
  - User had to read → understand → think → act (4 steps)
  - Goal: User sees screen → acts (1 step)
- **Final Copy** (LOCKED, 2 lines):
  ```
  궁금한 보험 담보를 그냥 말로 물어보세요.
  예: "삼성화재 암진단비 설명해줘"
  ```
- **Forbidden Language** (ABSOLUTE):
  - ❌ "이 도우미는..." (service introduction)
  - ❌ "보험 상품을 단순히 나열하는 대신..." (philosophy)
  - ❌ "보장이 어떻게 정의되어 있는지..." (feature description)
  - ❌ "설명 → 비교 → 구조 차이 이해" (flow diagram)
  - ❌ "질문부터 시작해 보세요" (thinking trigger)
  - ❌ ANY sentence that makes user read/understand/think
- **Rules**:
  - ❌ NO service introduction
  - ❌ NO feature explanation
  - ❌ NO philosophy/approach description
  - ❌ NO "please start with..." (creates thinking step)
  - ❌ NO LLM usage
  - ✅ Direct action prompt ("그냥 말로 물어보세요")
  - ✅ Concrete example (copy-paste ready)
  - ✅ Placeholder matches example exactly
  - ✅ 2 lines ONLY (no elaboration)
  - ✅ Deterministic only
- **Placeholder** (unchanged, already correct):
  ```
  예: 삼성화재 암진단비 설명해줘
  ```
- **Build Status**: ✅ `npm run build` succeeded (no errors)
- **Definition of Success** (10-second rule):
  > "사용자가 첫 화면 진입 후 10초 이내에 커서를 입력창에 두거나 예시를 입력하기 시작하면 성공."
- **FINAL LOCK Notice**: This is the final onboarding copy. Any future changes require:
  1. New STEP number
  2. A/B test evidence
  3. User feedback data

### STEP NEXT-126: EX3_COMPARE Fixed Bubble Template Lock

- **SSOT**: `docs/audit/STEP_NEXT_126_EX3_BUBBLE_FIXED_LOCK.md`
- **Modified Files**:
  - `apps/web/lib/ex3BubbleTemplate.ts` (NEW - fixed template generator)
  - `apps/web/app/page.tsx` (EX3_COMPARE bubble override in handleSend + handleClarificationSelect)
- **Purpose**: Lock EX3_COMPARE left bubble to fixed 6-line template (same input → same bubble)
- **Root Cause**:
  - EX3_COMPARE bubble was using `bubble_markdown`/`title`/`summary_bullets` (data-driven variation)
  - Customer testing requires predictable, reproducible UX
- **Fixed Template** (LOCKED, 6 lines):
  ```markdown
  {A}는 진단 시 **정해진 금액을 지급하는 구조**이고,
  {B}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**

  **즉,**
  - {A}: 지급 금액이 명확한 정액 구조
  - {B}: 지급 조건 해석이 중요한 한도 구조
  ```
  - `{A}` = 보험사1 display name (예: "삼성화재")
  - `{B}` = 보험사2 display name (예: "메리츠화재")
- **Implementation**:
  - `buildEX3FixedBubble(insurer1, insurer2)`: Generate fixed template
  - `extractInsurerCodesForEX3(requestPayload)`: Extract insurer codes from payload
  - Frontend intercepts `kind === "EX3_COMPARE"` → force fixed template
- **Rules**:
  - ❌ NO `summary_bullets`/`title`/`bubble_markdown` in EX3 bubble
  - ❌ NO data-driven variation (template is CONSTANT)
  - ❌ NO "일부 보험사는..." (explicit insurer names ONLY)
  - ❌ NO insurer code exposure (samsung, meritz)
  - ❌ NO backend/API/Composer changes (view layer ONLY)
  - ❌ NO LLM usage
  - ✅ Fixed 6-line template for ALL EX3_COMPARE messages
  - ✅ Insurer display names (삼성화재, 메리츠화재)
  - ✅ EX2/EX4 unchanged (no regression)
  - ✅ Deterministic only
- **Template Characteristics**:
  - Based on "암진단비" case (customer/team agreed structure summary)
  - Current goal: **Complete fixation (reproducibility)**
  - Coverage-specific variation allowed in NEXT STEP ONLY
- **Definition of Success**:
  > "Same input → always same bubble (reproducibility). User testing shows predictable UX."

### STEP NEXT-127: EX3_COMPARE Table Per-Insurer Cells + Meta (FINAL FIX)

- **SSOT**: `docs/audit/STEP_NEXT_127_EX3_TABLE_PER_INSURER_LOCK.md`
- **Modified Files**:
  - `apps/api/response_composers/ex3_compare_composer.py` (_build_table_section, _build_kpi_section)
  - `tests/test_step_next_127_ex3_table_per_insurer_cells.py` (NEW - 8 contract tests, all PASS)
- **Purpose**: Fix EX3 table to show limit vs amount correctly per insurer (NOT hidden in meta)
- **Root Cause**:
  - Samsung limit ("보험기간 중 1회") only in `meta.kpi_summary.limit_summary` (NOT in cells.text)
  - All row meta used samsung refs ONLY (meritz cells had samsung refs - cross-contamination)
  - Structural basis always "정액 지급 방식" (SAME for both, no difference visible)
- **Fixes**:
  1. **Per-insurer meta**: Each cell has its own insurer's refs (samsung cell → samsung refs, meritz cell → meritz refs)
  2. **Limit priority**: If limit exists → show limit in cells.text (NOT just amount)
  3. **Structural basis**: "지급 한도/횟수 기준" vs "보장금액(정액) 기준" (reflects limit vs amount difference)
- **Table Structure** (3 rows, LOCKED):
  - Row 1: "보장 정의 기준" (per-insurer basis: limit-based vs amount-based)
  - Row 2: "핵심 보장 내용" (limit or amount per insurer)
  - Row 3: "지급유형" (payment_type)
- **Priority Rule** (LOCKED):
  1. If `limit exists` → basis = "지급 한도/횟수 기준", detail = limit
  2. Elif `amount != "명시 없음"` → basis = "보장금액(정액) 기준", detail = amount
  3. Else → basis = "표현 없음", detail = None
- **Rules**:
  - ❌ NO meta sharing (samsung refs in meritz cell = 0%, ABSOLUTE)
  - ❌ NO amount priority when limit exists (limit FIRST)
  - ❌ NO business logic change (view layer ONLY)
  - ❌ NO LLM usage
  - ❌ NO coverage_code exposure
  - ✅ Per-cell meta (each cell carries its own insurer's refs)
  - ✅ Samsung limit ("보험기간 중 1회") in cells.text (visible in table)
  - ✅ Meritz amount ("3천만원") in cells.text
  - ✅ Structural difference visible at-a-glance
  - ✅ Deterministic only
- **Contract Tests** (8/8 PASS):
  1. Samsung limit shown in cells.text ✅
  2. Meritz amount shown in cells.text ✅
  3. Structural basis different per insurer ✅
  4. NO samsung refs in meritz cells ✅ **(CRITICAL)**
  5. Meritz refs present in meritz cells ✅
  6. Samsung refs present in samsung cells ✅
  7. Bubble unchanged (STEP NEXT-126 preserved) ✅
  8. NO coverage_code exposure ✅
- **Definition of Success**:
  > "Table shows '한도 vs 금액' structural difference at-a-glance. Samsung refs NEVER appear in meritz column (cross-contamination = 0%)."

### STEP NEXT-128: EX3_COMPARE Bubble ↔ Table Consistency (FINAL FIX)

- **SSOT**: `docs/audit/STEP_NEXT_128_EX3_BUBBLE_TABLE_CONSISTENCY_LOCK.md`
- **Modified Files**:
  - `apps/api/response_composers/ex3_compare_composer.py` (_build_bubble_markdown - table-driven)
  - `tests/test_step_next_128_ex3_bubble_table_consistency.py` (NEW - 7 contract tests, all PASS)
  - `tests/test_step_next_127_ex3_table_per_insurer_cells.py` (updated - bubble expectation fixed)
- **Purpose**: Fix bubble ↔ table structural inconsistency (bubble said OPPOSITE of table)
- **Root Cause**:
  - Bubble hardcoded: Samsung = amount, Meritz = limit (STEP NEXT-126 assumption)
  - Table correct: Samsung = limit ("보험기간 중 1회"), Meritz = amount ("3천만원")
  - Result: **Bubble said opposite of table** → user confusion 100%
- **Fix**: Bubble reads structure from TABLE (SSOT), adapts accordingly
- **Core Principle**:
  > "Bubble is NOT an explanation - it RE-READS the table in natural language"
- **Structure Detection** (DETERMINISTIC):
  - Read "핵심 보장 내용" row from comparison_table
  - LIMIT indicators: ["보험기간 중", "지급 한도", "횟수", "회"]
  - AMOUNT indicators: ["만원", "천만원", "원"]
  - Priority: LIMIT > AMOUNT
- **Bubble Template** (6 lines, STEP NEXT-126 format preserved):
  - If Samsung = LIMIT, Meritz = AMOUNT → "Samsung는 보험기간 중 지급 횟수/한도 기준..."
  - If Samsung = AMOUNT, Meritz = LIMIT → "Samsung는 진단 시 정해진 금액(보장금액) 기준..."
- **Rules**:
  - ❌ NO hardcoded insurer order (table-driven ONLY)
  - ❌ NO "일부 보험사는..." (STEP NEXT-123 preserved)
  - ❌ NO new UX / new sections (bubble logic ONLY)
  - ❌ NO LLM usage
  - ✅ Table = SSOT (bubble MUST match table structure 100%)
  - ✅ 6-line format preserved (STEP NEXT-126)
  - ✅ Deterministic keyword matching
  - ✅ Bubble adapts to insurer order
- **Contract Tests** (7/7 PASS):
  1. Samsung (limit) vs Meritz (amount) → bubble says Samsung = limit ✅ **(CRITICAL)**
  2. Reversed order → bubble adapts ✅
  3. 6 lines format preserved ✅
  4. NO "일부 보험사" ✅
  5. Bubble ↔ Table consistency verified ✅ **(CRITICAL)**
  6. Table unchanged (STEP NEXT-127) ✅
  7. Reproducibility preserved ✅
- **Definition of Success**:
  > "Bubble ↔ Table inconsistency = 0%. User never asks '왜 말이 다르지?'"
- **Key Insight**:
  > "STEP NEXT-126 fixed format + STEP NEXT-128 table-driven content = Reproducibility + Consistency"

❌ Do NOT assume PostgreSQL as SSOT
❌ DB connection errors are out-of-scope

---

## 5. Forbidden Assumptions (Hard Stop)

- coverage_cards.jsonl (full) is deprecated
- Vector DB / LLM inference is NOT used for KPI
- “명시 없음” is allowed **only if**
  - DETAIL does not exist structurally

---

If unsure, ASK. Do not guess.

## Project Purpose
가입설계서 30~40개 보장 scope에 대한 **근거 자료 자동 수집 + 사실 비교** 파이프라인.
보험사별 약관/사업방법서/상품요약서에서 "scope 내 담보"만 검색 → 원문 추출 → 보험사 간 사실 대조표 생성.

## Input Contract (Canonical Truth for Mapping)
**`data/sources/mapping/담보명mapping자료.xlsx`**
- 담보명 매핑의 단일 출처 (INPUT contract)
- 이 파일에 없는 담보는 처리 금지
- 수동 편집은 허용, 코드로 생성/변경 금지
- **주의**: 이는 INPUT이며, SSOT(Single Source of Truth)가 아님

## Scope Gate (철칙)
1. **Scope 내 담보만 처리**: mapping 파일에 정의된 담보만
2. **보험사 확장 전 scope 검증**: 신규 보험사 추가 시 mapping 파일 먼저 확인
3. **Scope 밖 요청 거부**: "전체 담보", "추가 보장", "유사 상품" 같은 확장 요청 즉시 차단

## Evidence (증거 자료) 원칙
- **3가지 문서 타입 독립 검색**: 약관(policy), 사업방법서(business), 상품요약서(summary)
- **hits_by_doc_type 필수**: 각 담보별로 어느 문서에서 나왔는지 기록
- **policy_only 플래그 유지**: 약관에만 존재하는 담보 구분
- 검색 결과는 원문 그대로 보존 (요약/해석 금지)

## SSOT (Single Source of Truth) — FINAL CONTRACT

**Coverage SSOT**:
```
data/compare/*_coverage_cards.jsonl
```
- 담보별 카드 (mapping_status, evidence_status, amount)
- 모든 coverage 관련 검증의 기준

**Audit Aggregate SSOT**:
```
docs/audit/AMOUNT_STATUS_DASHBOARD.md
```
- KPI 집계 및 품질 검증의 기준

---

## Output SSOT (Single Source of Truth) — STEP NEXT-49

**ALL pipeline outputs are in `data/scope_v3/`** (SSOT enforced):
```
data/scope_v3/{insurer}_step1_raw_scope_v3.jsonl          # Step1 output
data/scope_v3/{insurer}_step2_sanitized_scope_v1.jsonl    # Step2-a output
data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl    # Step2-b output
data/scope_v3/{insurer}_step2_dropped.jsonl               # Step2-a audit
data/scope_v3/{insurer}_step2_mapping_report.jsonl        # Step2-b audit
```

**Run Metadata** (reproducibility):
```
data/scope_v3/LATEST                    # Current run ID
data/scope_v3/_RUNS/{run_id}/           # Run-specific metadata
  ├── manifest.yaml                     # Input manifest (if used)
  ├── profiles_sha.txt                  # Profile checksums
  ├── outputs_sha.txt                   # Output checksums
  └── SUMMARY.md                        # Execution counts
```

**Constitutional Rule** (STEP NEXT-52-HK enforced):
1. **Step1/Step2 outputs** → `data/scope_v3/` ONLY
2. **Step3+ inputs** → `data/scope_v3/` ONLY
3. **NEVER read or write** to `data/scope/` (legacy, archived)

**SSOT Enforcement Guardrails** (STEP NEXT-52-HK):
- Code-level validation: Step2-a and Step2-b reject non-`scope_v3/` paths (exit 2)
- Test suite: `tests/test_scope_ssot_no_legacy_step2_outputs.py` fails if any Step2 outputs exist in `data/scope/`
- Physical archive: Legacy Step2 outputs moved to `archive/scope_legacy/run_20260101_step_next_52_hk/`

**Legacy directories** (archived, DO NOT USE):
- `data/scope/` → Legacy only (see `data/scope/README.md`)
- `data/scope_v2/` → `archive/scope_v2_legacy/`

---

## Input/Intermediate Files (NOT SSOT)

**Canonical Mapping Source (INPUT)**:
```
data/sources/mapping/담보명mapping자료.xlsx
```
- 신정원 통일코드 매핑의 단일 출처
- 이 파일에 없는 담보는 처리 금지

**Stats (보조)**:
```
data/compare/*.json
```
- 통계 보조 파일 (SSOT 아님)

**Status Tracking**:
```
STATUS.md
```
- 진행 상황 기록 (historical log)

---

## DEPRECATED (완전 제거됨 / _deprecated로 이동)

**❌ DO NOT USE** (STEP NEXT-31-P2: Moved to _deprecated/):
- `reports/*.md` — STEP NEXT-18X-SSOT에서 완전 제거
- `data/evidence_pack/` — Step5+에서 coverage_cards로 통합
- `_deprecated/pipeline/step0_scope_filter/` — Canonical pipeline 미사용
- `_deprecated/pipeline/step7_compare/` — 비교는 API layer에서 수행
- `_deprecated/pipeline/step8_multi_compare/` — 비교는 API layer에서 수행
- `_deprecated/pipeline/step8_single_coverage/` — 조회는 API layer에서 수행
- `_deprecated/pipeline/step10_audit/` — 보고서 생성은 tools/audit에서 수행
- `pipeline/step6_build_report/` — 제거됨
- `pipeline/step9_single_compare/` — 제거됨
- `pipeline/step10_multi_single_compare/` — 제거됨

## 금지 사항
- LLM 요약/추론/생성
- Embedding/벡터DB 사용
- 담보명 자동 매칭/추천
- Scope 외 데이터 처리
- 보고서에 "추천", "제안", "결론" 삽입

## 실행 기본 명령 (Canonical Pipeline - STEP NEXT-46)

### Step1: Extract Scope (Raw Extraction)
```bash
# Step1a: Build profile (run once per insurer, or when PDF changes)
python -m pipeline.step1_summary_first.profile_builder_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer hanwha

# Step1b: Extract raw scope from proposal PDF
python -m pipeline.step1_summary_first.extractor_v3 \
  --manifest data/sources/proposal/MANIFEST.yaml \
  --insurer hanwha

# Output: data/scope_v3/hanwha_step1_raw_scope_v3.jsonl (SSOT)
```

### Step2-a: Sanitize Scope (Fragment/Noise Removal)
```bash
# Step2-a: Sanitize raw extraction (deterministic pattern matching)
python -m pipeline.step2_sanitize_scope.run --insurer hanwha

# Input:  data/scope_v3/hanwha_step1_raw_scope_v3.jsonl
# Output: data/scope_v3/hanwha_step2_sanitized_scope_v1.jsonl (SSOT)
#         data/scope_v3/hanwha_step2_dropped.jsonl (audit trail)
```

### Step2-b: Canonical Mapping (신정원 통일코드)
```bash
# Step2-b: Map to canonical coverage codes (deterministic only)
python -m pipeline.step2_canonical_mapping.run --insurer hanwha

# Input:  data/scope_v3/hanwha_step2_sanitized_scope_v1.jsonl
# Output: data/scope_v3/hanwha_step2_canonical_scope_v1.jsonl (SSOT)
#         data/scope_v3/hanwha_step2_mapping_report.jsonl
```

### Step3+: Downstream Pipeline (STEP NEXT-61 Compliant)
```bash
# Step3: Extract evidence text
python -m pipeline.step3_extract_text.run --insurer hanwha

# Step4: Search evidence (STEP NEXT-61: reads from data/scope_v3/)
python -m pipeline.step4_evidence_search.search_evidence --insurer hanwha

# Step5: Build coverage cards (SSOT)
python -m pipeline.step5_build_cards.build_cards --insurer hanwha

# Step7 (optional): Amount enrichment
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer hanwha
```

### Quick Start (All Steps)
```bash
# Run all steps for single insurer
INSURER=hanwha

# Step1: Extract raw scope
python -m pipeline.step1_summary_first.profile_builder_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer $INSURER
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer $INSURER

# Step2-a: Sanitize
python -m pipeline.step2_sanitize_scope.run --insurer $INSURER

# Step2-b: Canonical mapping
python -m pipeline.step2_canonical_mapping.run --insurer $INSURER

# Step3+: Downstream
python -m pipeline.step3_extract_text.run --insurer $INSURER
python -m pipeline.step4_evidence_search.search_evidence --insurer $INSURER
python -m pipeline.step5_build_cards.build_cards --insurer $INSURER
```

### Health Check
```bash
# 테스트
pytest -q

# 현재 상태 확인
git status -sb
ls data/scope | head
```

## Pipeline Architecture (Canonical Steps - STEP NEXT-46)

**Canonical Pipeline** (정식 실행 순서):
1. **step1_summary_first** (v3): 가입설계서 PDF → raw scope JSONL (`*_step1_raw_scope.jsonl`)
   - FROZEN: NO sanitization / filtering / judgment logic
   - Output: Raw extraction with proposal_facts + evidences
2. **step2_sanitize_scope** (Step2-a): raw scope → sanitized scope JSONL (`*_step2_sanitized_scope_v1.jsonl`)
   - Deterministic pattern matching (NO LLM)
   - Drops: fragments, clauses, premium waiver targets, sentence-like noise
   - Audit trail: `*_step2_dropped.jsonl`
3. **step2_canonical_mapping** (Step2-b): sanitized scope → canonical scope JSONL (`*_step2_canonical_scope_v1.jsonl`)
   - Maps to 신정원 unified coverage codes (deterministic only)
   - NO row reduction (anti-contamination gate)
   - Unmapped when ambiguous (no guessing)
   - Audit trail: `*_step2_mapping_report.jsonl`
4. **step3_extract_text**: PDF → evidence text (약관/사업방법서/상품요약서)
5. **step4_evidence_search**: canonical scope + text → evidence_pack.jsonl
6. **step5_build_cards**: canonical scope + evidence_pack → coverage_cards.jsonl (SSOT)
7. **step7_amount_extraction** (optional): coverage_cards + PDF → amount enrichment

**Constitutional Enforcement** (STEP NEXT-47):
- Step1 is FROZEN (no further filtering/sanitization logic allowed)
- Step2-a handles ALL sanitization (fragments, clauses, variants)
- Step2-b maps to canonical codes (deterministic only, NO LLM, NO guessing)
- Step2-b MUST preserve row count (anti-reduction gate)
- Step4 MUST use canonical scope input (hard gate: RuntimeError if wrong input)
- Step5 join-rate gate: 95% threshold (RuntimeError if < 95%)

**Audit Tools** (외부, pipeline 아님):
- `tools/audit/run_step_next_17b_audit.py`: AMOUNT_STATUS_DASHBOARD.md 생성

**DEPRECATED Steps** (STEP NEXT-31-P2: Moved to _deprecated/):
- ~~step0_scope_filter~~ → _deprecated/pipeline/step0_scope_filter/
- ~~step2_extract_pdf~~ → removed (ghost directory)
- ~~step6_build_report~~ → removed
- ~~step7_compare~~ → _deprecated/pipeline/step7_compare/
- ~~step8_multi_compare~~ → _deprecated/pipeline/step8_multi_compare/
- ~~step8_single_coverage~~ → _deprecated/pipeline/step8_single_coverage/
- ~~step9_single_compare~~ → removed
- ~~step10_multi_single_compare~~ → removed
- ~~step10_audit~~ → _deprecated/pipeline/step10_audit/

## Working Directory
`/Users/cheollee/inca-rag-scope`

## Session Start Protocol
매 세션 시작 시:
1. `docs/SESSION_HANDOFF.md` 읽기
2. `STATUS.md` 최신 상태 확인
3. `git status -sb` + `pytest -q` 실행
4. 요청 사항이 scope 내인지 검증 후 진행
