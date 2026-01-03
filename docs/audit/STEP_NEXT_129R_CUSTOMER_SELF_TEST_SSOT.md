# STEP NEXT-129R: Customer Self-Test UX Flow (SSOT Rollback)

## 0) Constitutional Declaration

**New SSOT (Single Source of Truth)**:
> "고객이 스스로 테스트 가능한 흐름 (Customer Self-Test Flow)"

**Supersedes**:
- STEP NEXT-121 (Comparison Intent Hard-Lock)
- STEP NEXT-125 (Forced EX3 Routing)
- STEP NEXT-126 (EX3 Fixed Bubble Template Override)
- STEP NEXT-128 (Bubble/Table Consistency with Template Override)

**Rationale**:
The system had evolved toward "demo auto-complete" where the frontend/backend would bypass user choices to complete flows automatically. This created unpredictable UX where users could not understand why certain screens appeared or why their input was modified silently.

**Goal**:
Restore **customer self-test capability** where:
1. User understands WHY each screen appears
2. User can REPRODUCE behavior by providing the same input
3. System NEVER bypasses `need_more_info` to force completion
4. System NEVER modifies payload silently
5. All transitions require explicit user action (button clicks, not auto-routing)

---

## 1) Rollback Summary

### 1-1. Removed Features (Execution Path = 0%)

| Feature | Location | Reason |
|---------|----------|---------|
| **Comparison Intent Hard-Lock** | `apps/api/chat_intent.py::IntentRouter.route()` | Forced EX3 routing when insurers≥2, bypassed user intent detection |
| **Silent Payload Correction** | `apps/web/app/page.tsx::handleSend()` | Extracted insurers/coverage from message and injected into payload without UI visibility |
| **EX3 Fixed Bubble Template** | `apps/web/app/page.tsx::handleSend/handleClarificationSelect()` | Frontend overrode backend `bubble_markdown` with fixed template, breaking SSOT |
| **need_more_info Bypass** | `apps/web/app/page.tsx::handleSend()` | Ignored `need_more_info=true` when comparison intent detected |
| **Auto-Context Setup on Example Click** | `apps/web/app/page.tsx::handleExampleClick()` | Silently set insurers/coverage context when example button clicked |

### 1-2. Preserved Features (Kept)

| Feature | Location | Reason |
|---------|----------|---------|
| **Insurer Switch Detection** | `apps/web/lib/contextUtils.ts::isInsurerSwitchUtterance()` | Deterministic pattern matching for "메리츠는?" transitions (explicit user intent) |
| **LIMIT_FIND Pattern Detection** | `apps/web/lib/contextUtils.ts::isLimitFindPattern()` | Validates 2-insurer requirement for LIMIT_FIND (clarification UI, not bypass) |
| **Conversation Context Lock** | `apps/web/app/page.tsx::conversationContext` | Maintains context across messages (not bypassing, just state management) |

---

## 2) EX1 Landing Page (Reset)

**Purpose**: Action-first onboarding (NO philosophy/explanation)

**Structure** (LOCKED):
```markdown
궁금한 담보를 그냥 말로 물어보세요.

[Button 1] 예: 암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘
[Button 2] 예: 삼성화재와 메리츠화재 암진단비 비교해줘
[Button 3] 예: 제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘
```

**Behavior**:
- Button click → fills input field ONLY (NO auto-send, NO auto-context)
- User must click "전송" button manually
- User can edit text before sending

**Rules**:
- ❌ NO auto-send on example click
- ❌ NO auto-context setup (insurers/coverage)
- ❌ NO philosophy/flow explanation
- ✅ 1 line + 3 buttons ONLY
- ✅ User controls ALL actions

---

## 3) EX2 ↔ EX3 Transitions (User Action-Based)

### 3-1. EX2 → EX3 Transition

**Trigger**: User selects 2 insurers + clicks "비교(EX3)" button

**Flow**:
1. EX2 result displayed (e.g., list of products with different limit values)
2. Bottom of result: CTA button "선택한 2개 보험사로 비교(EX3)"
3. User selects 2 insurers from EX2 result (checkbox/button UI)
4. User clicks CTA button
5. System sends EX3 request with `kind="EX3_COMPARE"` + selected insurers + coverage

**Rules**:
- ❌ NO auto-transition (insurers≥2 does NOT trigger EX3 automatically)
- ❌ NO silent payload modification
- ✅ User MUST click button (explicit action)
- ✅ Button is visible/available ONLY when 2 insurers are selected

### 3-2. EX3 → EX2 Return

**Trigger**: User clicks "다른 담보/조건으로 다시 찾기(EX2)" button

**Flow**:
1. EX3 result displayed (comparison table)
2. Top/bottom of result: CTA button "다른 담보/조건으로 다시 찾기(EX2)"
3. User clicks CTA button
4. Input field is filled with EX2-style template text (e.g., "{담보명} 담보 중 보장한도가 다른 상품 찾아줘")
5. User can edit text before sending
6. User clicks "전송" button

**Rules**:
- ❌ NO auto-send (button fills input, user must send manually)
- ❌ NO auto-transition
- ✅ User MUST click button (explicit action)
- ✅ User can edit text before sending

---

## 4) EX4 Implementation (O/X Eligibility Table)

### 4-1. Input/Intent

**Example Query**:
```
제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘
```

**Intent**: `EX4_ELIGIBILITY` (already exists in system)

**Required Slots**:
- `disease_name`: "제자리암" or "경계성종양" (extracted deterministically)
- `insurers`: ["samsung", "meritz"] (2 insurers REQUIRED)

### 4-2. Output Structure (LOCKED)

**Left Bubble (Markdown)**:
- 1-2 line summary of what the table shows
- NO recommendations/judgments
- Example: "제자리암·경계성종양 관련 5개 항목의 보장 가능 여부(O/X)를 비교합니다."

**Right Panel (Sections)**:

#### Section 1: 보장 가능 여부 표

| 비교 항목 | 삼성화재 | 메리츠화재 |
|----------|---------|----------|
| 진단비 | O | X |
| 수술비 | O | O |
| 항암약물 | X | O |
| 표적항암 | X | O |
| 다빈치수술 | O | X |

**Cell Value Rules**:
- `O` = 보장됨 (evidence confirms coverage)
- `X` = 보장 안됨 (evidence confirms exclusion OR no evidence found)
- NO `Unknown` / `△` / `?` (customer testing requires clear answers)

**Cell Metadata**:
- Each cell MUST have `evidence_refs` (e.g., `PD:samsung:A4200_1`, `EV:meritz:A4200_1:0`)
- "근거 보기" link opens evidence modal

#### Section 2: 종합 평가 (NO Recommendations)

**Purpose**: Explain table interpretation (NOT recommend products)

**Template** (LOCKED):
```markdown
## 종합 평가

항목별로 O/X는 '해당 하위개념이 명시적으로 보장 대상으로 포함되는지' 기준입니다.
세부 지급 조건(면책/감액/대기기간)은 근거 보기에서 확인하세요.
보장한도/보험료는 별도 비교 항목에서 확인이 필요합니다.
```

**Rules**:
- ❌ NO "더 좋다", "유리하다", "추천" (ABSOLUTE FORBIDDEN)
- ❌ NO product scoring/ranking
- ✅ Table interpretation guide ONLY (2-3 sentences)
- ✅ Remind user to check details in evidence

### 4-3. Evidence Priority (SSOT)

**Priority Order** (deterministic):
1. **PD (가입설계서)**: Proposal details (highest priority)
2. **사업방법서 (Business Methods)**: Coverage rules
3. **상품요약서 (Product Summary)**: Summary statements
4. **약관 (Policy Terms)**: Legal terms (fallback)

**O/X Decision Logic** (deterministic keyword matching):
- `O`: Evidence contains "보장" + coverage keyword (e.g., "진단비")
- `X`: Evidence contains "제외" OR "면책" OR NO relevant evidence found

**Notes Field** (optional):
- If `X` due to NO evidence: Add note "근거 없음 (가입설계서, 사업방법서, 상품요약서, 약관 확인 완료)"
- If `O` or `X` with evidence: No note needed (근거 보기 available)

---

## 5) Backend Changes

### 5-1. Intent Router (`apps/api/chat_intent.py`)

**Removed**:
- STEP NEXT-125: Comparison intent gate (insurers≥2 + comparison keywords → force EX3)

**Current Routing Logic** (STEP NEXT-129R):
```python
def route(request: ChatRequest) -> MessageKind:
    # Priority 1: Explicit kind (NO override)
    if request.kind is not None:
        return request.kind

    # Priority 2: insurers count gate (EX2_DETAIL for insurers=1)
    if len(insurers) == 1:
        return "EX2_DETAIL"

    # Priority 3: detect_intent() (category/FAQ/gates/patterns)
    kind, confidence = IntentRouter.detect_intent(request)
    return kind
```

**Key Change**:
- Removed forced EX3 routing based on insurers≥2 + comparison keywords
- System now relies on `request.kind` (explicit UI) OR pattern matching (natural)
- NO forced routing based on data structure

### 5-2. EX4 Handler (To Be Implemented)

**File**: `apps/api/response_composers/ex4_eligibility_composer.py`

**Required Enhancements**:
1. O/X table builder (5 rows: 진단비/수술비/항암약물/표적항암/다빈치수술)
2. Evidence priority resolver (PD > 사업방법서 > 상품요약서 > 약관)
3. Deterministic O/X decision logic (keyword matching)
4. "종합 평가" section builder (NO recommendations, guidance ONLY)

**Output Structure**:
```python
{
    "kind": "EX4_ELIGIBILITY",
    "bubble_markdown": "...",  # 1-2 line summary
    "sections": [
        {
            "title": "보장 가능 여부",
            "type": "table",
            "comparison_table": {
                "headers": ["비교 항목", "삼성화재", "메리츠화재"],
                "rows": [
                    {
                        "coverage_item": "진단비",
                        "cells": [
                            {
                                "insurer": "samsung",
                                "value": "O",
                                "meta": {
                                    "evidence_refs": ["PD:samsung:A4200_1"]
                                }
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }
        },
        {
            "title": "종합 평가",
            "type": "text",
            "text": "항목별로 O/X는..."  # Fixed template
        }
    ]
}
```

---

## 6) Frontend Changes

### 6-1. Removed Logic

| File | Line | Change |
|------|------|--------|
| `apps/web/app/page.tsx` | ~133-166 | Removed silent payload correction (extractInsurersFromMessage, extractCoverageNameFromMessage) |
| `apps/web/app/page.tsx` | ~192-232 | Removed comparison intent hard-lock (isComparisonIntent, need_more_info bypass) |
| `apps/web/app/page.tsx` | ~268-297 | Removed EX3 fixed bubble template override (buildEX3FixedBubble, extractInsurerCodesForEX3) |
| `apps/web/app/page.tsx` | ~302-312 | Removed handleExampleClick (auto-context setup) |
| `apps/web/components/ChatPanel.tsx` | ~79-99 | Replaced STEP NEXT-121A example click with STEP NEXT-129R (fill input ONLY) |
| `apps/web/lib/contextUtils.ts` | ~101-206 | Kept but NOT used in handleSend (extractInsurersFromMessage/isComparisonIntent unused) |

### 6-2. EX1 Landing (ChatPanel.tsx)

**Implementation**:
```tsx
{isInitialState ? (
  <div className="flex justify-start mt-8">
    <div className="max-w-[65%] rounded-lg px-4 py-3 bg-gray-100 text-gray-800">
      <div className="text-sm leading-relaxed">
        <p className="mb-3">궁금한 담보를 그냥 말로 물어보세요.</p>
        <div className="space-y-2">
          <button onClick={() => onInputChange("암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘")}>
            예: 암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘
          </button>
          <button onClick={() => onInputChange("삼성화재와 메리츠화재 암진단비 비교해줘")}>
            예: 삼성화재와 메리츠화재 암진단비 비교해줘
          </button>
          <button onClick={() => onInputChange("제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘")}>
            예: 제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘
          </button>
        </div>
      </div>
    </div>
  </div>
) : ...
```

### 6-3. Bubble Rendering (page.tsx)

**Before (STEP NEXT-126)**:
```typescript
if (vm?.kind === "EX3_COMPARE") {
  summaryText = buildEX3FixedBubble(insurerCodes[0], insurerCodes[1]);  // Frontend override
}
```

**After (STEP NEXT-129R)**:
```typescript
if (vm?.bubble_markdown) {
  summaryText = vm.bubble_markdown;  // Backend SSOT
}
```

**Key Change**:
- Frontend ALWAYS uses `vm.bubble_markdown` from backend (NO override)
- Backend is SSOT for all message content

---

## 7) Verification Scenarios

### CHECK-1: EX1 Landing (First Screen)

**Expected**:
1. Screen shows 1 line: "궁금한 담보를 그냥 말로 물어보세요."
2. 3 example buttons visible
3. Click button → input field filled with example text
4. **NO** auto-send
5. User can edit text
6. User clicks "전송" button manually

**Pass Criteria**:
- ❌ NO auto-send after button click
- ❌ NO auto-context setup (insurers/coverage not set)
- ✅ Input field contains button text
- ✅ User must click "전송" to send

### CHECK-2: EX2 → EX3 Transition

**Expected**:
1. User sends EX2 query (e.g., "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘")
2. EX2 result displayed (list of products)
3. User selects 2 insurers from result (checkbox/button UI)
4. "비교(EX3)" button visible (enabled when 2 insurers selected)
5. User clicks button → EX3 request sent with `kind="EX3_COMPARE"`
6. EX3 comparison table displayed

**Pass Criteria**:
- ❌ NO auto-transition to EX3 (insurers≥2 in context does NOT trigger EX3)
- ✅ User MUST click button to transition
- ✅ Button disabled when <2 insurers selected

### CHECK-3: EX3 → EX2 Return

**Expected**:
1. EX3 result displayed (comparison table)
2. "다른 담보/조건으로 다시 찾기(EX2)" button visible
3. User clicks button → input field filled with EX2-style template
4. **NO** auto-send
5. User can edit text
6. User clicks "전송" button manually

**Pass Criteria**:
- ❌ NO auto-send after button click
- ✅ Input field contains EX2-style query
- ✅ User must click "전송" to send

### CHECK-4: EX4 O/X Table

**Expected**:
1. User sends EX4 query (e.g., "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘")
2. Left bubble: 1-2 line summary
3. Right panel: "보장 가능 여부" table (5 rows × 3 columns)
4. Each cell shows O or X (NO Unknown/△/?)
5. Each cell has "근거 보기" link
6. Click "근거 보기" → evidence modal opens
7. "종합 평가" section: 2-3 sentences (NO recommendations)

**Pass Criteria**:
- ✅ Table has exactly 5 rows (진단비/수술비/항암약물/표적항암/다빈치수술)
- ✅ All cells show O or X (NO other values)
- ✅ All cells have evidence_refs metadata
- ❌ NO "더 좋다", "유리하다", "추천" in 종합 평가

---

## 8) Prohibited Actions (ABSOLUTE)

| Category | Prohibited Action | Enforcement |
|----------|-------------------|-------------|
| **Routing** | Force EX3 based on insurers≥2 | Removed from IntentRouter.route() |
| **Payload** | Extract insurers/coverage from message and inject into payload | Removed from handleSend() |
| **Bypass** | Ignore need_more_info=true | Removed from handleSend() |
| **Override** | Frontend override backend bubble_markdown | Removed from handleSend/handleClarificationSelect() |
| **Auto-Send** | Send request on example button click | Changed to fill input ONLY |
| **Auto-Context** | Set insurers/coverage on example button click | Removed handleExampleClick() |
| **LLM Usage** | Use LLM for O/X decision | EX4 uses deterministic keyword matching |
| **Recommendations** | "더 좋다", "유리하다", "추천" in EX4 | Template enforces guidance-only text |

---

## 9) Definition of Done (DoD)

- [ ] All forced routing/silent correction/bypass code removed (execution path = 0%)
- [ ] EX1 landing shows 1 line + 3 buttons (NO auto-send, NO auto-context)
- [ ] EX2 ↔ EX3 transitions require explicit button clicks (NO auto-transition)
- [ ] EX4 O/X table implemented (5 rows, evidence refs, NO recommendations)
- [ ] All 4 CHECK scenarios pass (EX1/EX2/EX3/EX4)
- [ ] CLAUDE.md updated to rollback STEP NEXT-121/125/126/128
- [ ] This SSOT document (STEP_NEXT_129R_CUSTOMER_SELF_TEST_SSOT.md) created
- [ ] Git commit: `feat(step-next-129r): rollback demo-autoflow; restore self-test UX; implement ex4 eligibility ox`

---

## 10) Git History

**Branch**: `feat/step-next-129r-self-test-ssot`

**Commit Message**:
```
feat(step-next-129r): rollback demo-autoflow; restore self-test UX; implement ex4 eligibility ox

ROLLBACK:
- STEP NEXT-121: Comparison intent hard-lock (insurers≥2 → force EX3)
- STEP NEXT-125: Forced EX3 routing in IntentRouter
- STEP NEXT-126: EX3 fixed bubble template override (frontend)
- STEP NEXT-128: Bubble/table consistency with template override
- Silent payload correction (extractInsurersFromMessage/extractCoverageNameFromMessage)
- need_more_info bypass logic
- handleExampleClick auto-context setup

NEW FEATURES:
- EX1 landing: 1 line + 3 example buttons (fill input ONLY, NO auto-send)
- EX2 ↔ EX3 transitions: User action-based (button clicks, NO auto-routing)
- EX4 O/X eligibility table: 5 rows (진단비/수술비/항암약물/표적항암/다빈치수술)
- Backend bubble_markdown as SSOT (NO frontend override)

NEW SSOT:
- Customer Self-Test Flow: "User understands WHY each screen appears"
- No forced routing / No silent payload modification / No auto-send
- All transitions require explicit user action

DOCUMENTATION:
- docs/audit/STEP_NEXT_129R_CUSTOMER_SELF_TEST_SSOT.md (this file)
- CLAUDE.md updated to declare new SSOT and rollback previous LOCKs
```

---

## 11) SSOT Hierarchy

**Effective Date**: 2026-01-04 (STEP NEXT-129R)

**SSOT Priority**:
1. **This document** (`STEP_NEXT_129R_CUSTOMER_SELF_TEST_SSOT.md`)
2. **CLAUDE.md** (updated to reflect rollback)
3. Backend code (`apps/api/chat_intent.py`, `apps/api/response_composers/ex4_eligibility_composer.py`)
4. Frontend code (`apps/web/app/page.tsx`, `apps/web/components/ChatPanel.tsx`)

**Conflict Resolution**:
- If code contradicts this document → code is WRONG, fix code
- If CLAUDE.md contradicts this document → CLAUDE.md is WRONG, update CLAUDE.md
- If previous STEP (121/125/126/128) contradicts this document → previous STEP is SUPERSEDED, follow this document

**Amendment Policy**:
- This document can ONLY be amended with new STEP number (e.g., STEP NEXT-130)
- No silent edits allowed (all changes must be tracked in Git)
- Rollback requires explicit new STEP with rationale

---

**END OF SSOT DOCUMENT**
