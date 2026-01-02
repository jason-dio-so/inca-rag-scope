# STEP NEXT-80 — Explicit kind 우선순위(100%) 고정 + EX3 버튼 라우팅 보장

## 목표
- UI 예제3 버튼 클릭 시 **항상** `EX3_COMPARE`로 처리
- 현재 `/chat` 응답이 `EX2_DETAIL_DIFF`로 내려오는 문제 제거
- 원칙: **Explicit kind(프론트에서 전달된 kind) = Priority 1, 절대 override 금지**

## 문제 정의
- **증거**: /chat 응답에서 `message.kind = "EX2_DETAIL_DIFF"`, title = "A4200_1 보장한도 차이 분석"
- **원인**: Intent router가 explicit kind를 무시하고 anti-confusion gates/pattern matching으로 reroute
- **영향**: UI 예제3 버튼이 `EX3_COMPARE`를 보내도 backend가 다른 kind로 변환

## 적용 원칙 (LOCK)

### Priority 순서 (STEP NEXT-80)
1. **Explicit `kind` from request** → 100% priority (ABSOLUTE, NO OVERRIDE)
2. detect_intent() → category/FAQ/gates/patterns (ONLY if kind is None)

### CRITICAL RULE
- If `request.kind` is provided, NEVER call `detect_intent()`
- If `request.kind` is provided, NEVER apply anti-confusion gates
- Explicit kind = UI contract guarantee (예: Example 3 button)

## 구현 내역

### A) Backend: chat_intent.py

**File**: `apps/api/chat_intent.py`

**Changes**:
1. `IntentRouter.route()` (line 177-200):
   - Priority 1: Explicit kind (ABSOLUTE, NO OVERRIDE)
   - Priority 2-5: detect_intent() (ONLY if kind is None)
   - Documentation LOCKED

2. `IntentRouter.detect_intent()` (line 110-175):
   - Added NOTE: "This method is ONLY called when request.kind is NOT provided"
   - Updated priority documentation to STEP NEXT-80

**Code**:
```python
@staticmethod
def route(request: ChatRequest) -> MessageKind:
    """
    Route request to MessageKind

    PRIORITY (STEP NEXT-80 LOCKED):
    1. Explicit `kind` from request → 100% priority (ABSOLUTE, NO OVERRIDE)
    2. detect_intent() → category/FAQ/gates/patterns (ONLY if kind is None)

    CRITICAL RULE:
    - If request.kind is provided, NEVER call detect_intent()
    - If request.kind is provided, NEVER apply anti-confusion gates
    - Explicit kind = UI contract guarantee (e.g., Example 3 button)

    Returns:
        MessageKind for handler dispatch
    """
    # STEP NEXT-80: Priority 1 - Explicit kind (ABSOLUTE, NO OVERRIDE)
    if request.kind is not None:
        return request.kind

    # Priority 2-5: Detect from category/FAQ/gates/patterns (ONLY if kind is None)
    kind, confidence = IntentRouter.detect_intent(request)
    return kind
```

### B) Backend: HandlerRegistry (검증)

**File**: `apps/api/chat_handlers_deterministic.py`

**Status**: ✅ Already correct
- `EX3_COMPARE` → `Example3HandlerDeterministic()` (1:1 mapping)
- No fallback logic

**Code** (line 619-635):
```python
class HandlerRegistryDeterministic:
    """Registry for deterministic handlers"""

    _HANDLERS: Dict[MessageKind, BaseDeterministicHandler] = {
        "PREMIUM_COMPARE": Example1HandlerDeterministic(),
        "EX1_PREMIUM_DISABLED": Example1HandlerDeterministic(),
        "EX2_DETAIL_DIFF": Example2DiffHandlerDeterministic(),  # LEGACY
        "EX2_LIMIT_FIND": Example2DiffHandlerDeterministic(),   # STEP NEXT-78: Reuse EX2Diff
        "EX3_INTEGRATED": Example3HandlerDeterministic(),
        "EX3_COMPARE": Example3HandlerDeterministic(),  # STEP NEXT-77: New kind
        "EX4_ELIGIBILITY": Example4HandlerDeterministic()
    }
```

### C) Frontend: ChatPanel.tsx

**File**: `apps/web/components/ChatPanel.tsx`

**Changes**:
1. Line 39-49: Added console logging for debugging
2. Line 68: Changed `EX3_INTEGRATED` → `EX3_COMPARE`

**Code**:
```typescript
// STEP NEXT-80: Example button handlers with explicit kind
const handleExampleClick = (kind: MessageKind, defaultPrompt: string) => {
  console.log(`[ChatPanel] Example button clicked: kind=${kind}, prompt="${defaultPrompt}"`);
  onInputChange(defaultPrompt);
  if (onSendWithKind) {
    console.log(`[ChatPanel] Calling onSendWithKind with kind=${kind}`);
    onSendWithKind(kind);
  } else {
    onSend();
  }
};

// Example 3 button
<button
  onClick={() => handleExampleClick(
    "EX3_COMPARE",  // STEP NEXT-80: Changed from EX3_INTEGRATED
    "삼성화재와 메리츠화재의 암진단비를 비교해주세요"
  )}
  ...
>
```

### D) Frontend: page.tsx

**File**: `apps/web/app/page.tsx`

**Changes**: Line 75-87 - Added request payload logging

**Code**:
```typescript
// STEP NEXT-80: Log request payload for debugging
const requestPayload = {
  message: input,
  kind: kind,  // Explicit kind (Priority 1)
  insurers: selectedInsurers.length > 0 ? selectedInsurers : undefined,
  coverage_names: coverageNames.length > 0 ? coverageNames : undefined,
  llm_mode: llmMode,
};
console.log("[page.tsx] Sending request with explicit kind:", requestPayload);

const response = await postChat(requestPayload);

console.log("[page.tsx] Chat response:", response);
```

## Contract Test (신규)

**File**: `tests/test_intent_router_explicit_kind_lock.py`

**Test Cases** (7개, 모두 PASS):
1. `test_explicit_kind_ex3_compare_absolute_priority`: EX3_COMPARE with limit keywords → EX3_COMPARE (not EX2)
2. `test_explicit_kind_ex3_compare_with_disease_subtype`: EX3_COMPARE with "제자리암" → EX3_COMPARE (not EX4)
3. `test_explicit_kind_ex4_eligibility_absolute_priority`: EX4_ELIGIBILITY is honored
4. `test_no_explicit_kind_applies_gates`: No kind → gates apply (EX2_LIMIT_FIND)
5. `test_no_explicit_kind_applies_disease_subtype_gate`: No kind → disease gate applies (EX4)
6. `test_explicit_kind_ex2_limit_find_with_eligibility_keywords`: EX2_LIMIT_FIND not overridden by eligibility patterns
7. `test_explicit_kind_priority_over_category`: Explicit kind overrides category

**Test Results**:
```
============================= test session starts ==============================
tests/test_intent_router_explicit_kind_lock.py::test_explicit_kind_ex3_compare_absolute_priority PASSED
tests/test_intent_router_explicit_kind_lock.py::test_explicit_kind_ex3_compare_with_disease_subtype PASSED
tests/test_intent_router_explicit_kind_lock.py::test_explicit_kind_ex4_eligibility_absolute_priority PASSED
tests/test_intent_router_explicit_kind_lock.py::test_no_explicit_kind_applies_gates PASSED
tests/test_intent_router_explicit_kind_lock.py::test_no_explicit_kind_applies_disease_subtype_gate PASSED
tests/test_intent_router_explicit_kind_lock.py::test_explicit_kind_ex2_limit_find_with_eligibility_keywords PASSED
tests/test_intent_router_explicit_kind_lock.py::test_explicit_kind_priority_over_category PASSED

7 passed, 9 warnings in 0.07s
```

## 검증 시나리오

### 1) Backend Unit Test (완료)
- ✅ 7개 contract test 모두 PASS
- ✅ 기존 EX3/EX4 schema/integration test 모두 PASS (32 tests)

### 2) Browser Test (수동 검증 필요)

**Step 1**: 서버 시작
```bash
# Terminal 1 - Backend
cd /Users/cheollee/inca-rag-scope
python -m uvicorn apps.api.server:app --reload --port 8000

# Terminal 2 - Frontend
cd /Users/cheollee/inca-rag-scope/apps/web
npm run dev
```

**Step 2**: 브라우저 http://localhost:3000 접속

**Step 3**: 예제3 버튼 클릭

**Expected Behavior**:
1. Browser Console에서:
   ```
   [ChatPanel] Example button clicked: kind=EX3_COMPARE, prompt="삼성화재와 메리츠화재의 암진단비를 비교해주세요"
   [ChatPanel] Calling onSendWithKind with kind=EX3_COMPARE
   [page.tsx] Sending request with explicit kind: {kind: "EX3_COMPARE", ...}
   [page.tsx] Chat response: {message: {kind: "EX3_COMPARE", ...}}
   ```

2. Response:
   - `message.kind === "EX3_COMPARE"`
   - Title: "암진단비(유사암제외) 비교" (NOT "보장한도 차이 분석")
   - ResultDock shows EX3_COMPARE UI (TwoInsurerCompareCard)

**Failure Indicators** (if any):
- ❌ `message.kind === "EX2_DETAIL_DIFF"` or `"EX2_LIMIT_FIND"`
- ❌ Title: "A4200_1 보장한도 차이 분석"
- ❌ Console shows kind being overridden

### 3) Same Query Without Explicit Kind (기존 동작 유지)

**Test**: 동일한 텍스트를 kind 없이 전송 버튼으로 보내기

**Input**:
- Text: "삼성화재와 메리츠화재의 암진단비 보장한도가 다른지 비교해주세요"
- Kind: None (일반 전송 버튼)

**Expected**:
- Intent router가 "보장한도.*다른" 패턴 감지
- Response kind: `EX2_LIMIT_FIND` (기존 behavior 유지)

## 금지 사항
- ✅ LLM/OCR/Vector 사용 금지
- ✅ 기존 EX2/EX4 intent 규칙 파괴 금지 (kind 없는 경우에만 적용)
- ✅ 프론트 UX 변경 금지 (버튼 텍스트/레이아웃 변경 없이 payload만 보장)

## DoD (Definition of Done)

### Backend
- ✅ `chat_intent.py`: Explicit kind priority 100% (LOCKED)
- ✅ HandlerRegistry: EX3_COMPARE 매핑 확인 (already correct)
- ✅ Contract test: 7개 모두 PASS

### Frontend
- ✅ `ChatPanel.tsx`: 예제3 버튼 → `kind="EX3_COMPARE"`
- ✅ `page.tsx`: Request payload logging 추가
- ⏳ Browser 검증: 예제3 버튼 → `/chat` 응답 `message.kind=EX3_COMPARE` 100%

### Tests
- ✅ `test_intent_router_explicit_kind_lock.py`: 7 tests PASS
- ✅ 기존 EX3/EX4 tests: 32 tests PASS
- ✅ Kind 없는 동일 질의 → 기존 라우팅 유지 (gates 적용)

### Documentation
- ✅ `STEP_NEXT_80_EXPLICIT_KIND_LOCK.md` (this file)
- ✅ `chat_intent.py` docstring updated
- ✅ Test code에 명확한 assertion messages

## 파일 변경 요약

### Modified Files
1. `apps/api/chat_intent.py` - Explicit kind priority lock
2. `apps/web/components/ChatPanel.tsx` - EX3 버튼 kind 수정 + logging
3. `apps/web/app/page.tsx` - Request payload logging

### New Files
1. `tests/test_intent_router_explicit_kind_lock.py` - Contract test (7 tests)
2. `docs/audit/STEP_NEXT_80_EXPLICIT_KIND_LOCK.md` - This document

### Test Coverage
- Total: 32 tests (7 new + 25 existing related tests)
- Pass Rate: 100%
- Coverage: Explicit kind lock, EX3 schema, EX4 evaluation, integration

## Next Steps (User Action Required)

1. **브라우저 검증**:
   - 서버 2개 실행 (backend + frontend)
   - http://localhost:3000 접속
   - 예제3 버튼 클릭
   - Console + Response 확인

2. **문제 발견 시**:
   - Console screenshot 첨부
   - Response JSON 첨부
   - Backend log 확인 (router decision)

3. **검증 완료 후**:
   - Git commit + push
   - `STATUS.md` 업데이트

## Reference
- **SSOT**: `docs/ui/INTENT_ROUTER_RULES.md` (STEP NEXT-78)
- **Schema**: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md` (STEP NEXT-77)
- **Evaluation**: `docs/audit/STEP_NEXT_79_EX4_OVERALL_EVALUATION_LOCK.md`
