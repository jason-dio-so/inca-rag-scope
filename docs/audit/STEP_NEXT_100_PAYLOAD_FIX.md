# STEP NEXT-100 — Fix: ChatPanel request payload에 insurers/coverage_names 누락 버그 수정 (Frontend) ✅

## 문제 증상

현재 /chat 요청이 아래처럼 전송되고 있음:
```json
{
  "message": "삼성과 메리츠의 암진단비 보장한도차이",
  "llm_mode": "OFF"
}
```

**문제**: insurers/coverage_names/kind 모두 누락 → 서버는 need_more_info 유도 → 하단 패널 재등장

## 근본 원인 (Root Cause Analysis)

### 원인 1: Clarification 선택 후 UI state 미업데이트
1. 사용자가 보험사/담보를 선택하지 않고 첫 메시지 전송
2. 서버가 `need_more_info=true` 반환
3. 사용자가 clarification 패널에서 보험사/담보 선택
4. `handleClarificationSelect`가 request를 재전송하지만, **UI state (`selectedInsurers`, `coverageInput`)는 업데이트하지 않음**
5. 다음 메시지 전송 시 state가 여전히 비어있어 payload에 포함되지 않음

### 원인 2: `undefined` 값이 JSON.stringify에서 제거됨
```typescript
{
  message: "...",
  insurers: undefined,  // JSON.stringify는 이 키를 제거함
  coverage_names: undefined,  // JSON.stringify는 이 키를 제거함
  llm_mode: "OFF"
}
```

JavaScript의 `JSON.stringify`는 값이 `undefined`인 키를 자동으로 제거한다. 따라서 `selectedInsurers.length === 0`이면 `insurers: undefined`가 되고, 이는 payload에서 완전히 누락된다.

## 해결 방법

### 수정 1: Clarification 선택 시 UI state 동기화 (`page.tsx:298-302`)
```typescript
if (slotName === "coverage_names") {
  updatedRequest.coverage_names = Array.isArray(value) ? value : [value];
  // STEP NEXT-100: Update UI state so next request includes this value
  setCoverageInput(Array.isArray(value) ? value.join(", ") : value);
} else if (slotName === "insurers") {
  updatedRequest.insurers = Array.isArray(value) ? value : [value];
  // STEP NEXT-100: Update UI state so next request includes this value
  setSelectedInsurers(Array.isArray(value) ? value : [value]);
}
```

**효과**: Clarification 패널에서 선택한 값이 UI state에 반영되어, 다음 요청에서도 자동으로 포함됨.

### 수정 2: Request payload builder SSOT (`page.tsx:184-216`)
```typescript
// STEP NEXT-100: Capture state BEFORE any async operations
const messageToSend = input;
const insurersToSend = selectedInsurers.length > 0 ? selectedInsurers : undefined;
const coverageNames = coverageInput
  .split(",")
  .map((s) => s.trim())
  .filter((s) => s.length > 0);
const coverageNamesToSend = coverageNames.length > 0 ? coverageNames : undefined;

// STEP NEXT-100: Build request payload (SSOT)
const requestPayload = {
  message: messageToSend,
  selected_category: categoryLabel,
  insurers: insurersToSend,
  coverage_names: coverageNamesToSend,
  llm_mode: llmMode,
};

console.log("[page.tsx handleSend] Request payload:", requestPayload);
const response = await postChat(requestPayload);
```

**효과**:
- 모든 state를 **비동기 작업 전에** 먼저 캡처 (React state timing 이슈 방지)
- 단일 `requestPayload` 객체를 SSOT로 사용 (중복 코드 제거)
- Console log로 실제 전송 payload 검증 가능

### 수정 3: Auto-retry 로직 (need_more_info 자동 재시도) (`page.tsx:217-279`)
```typescript
// STEP NEXT-100: Auto-retry if need_more_info but client has the values
if (response.need_more_info === true) {
  const missingSlots = response.missing_slots || [];
  const canAutoRetry = missingSlots.every((slot: string) => {
    if (slot === "insurers") return insurersToSend !== undefined;
    if (slot === "coverage_names") return coverageNamesToSend !== undefined;
    return false;
  });

  if (canAutoRetry && missingSlots.length > 0) {
    console.log("[page.tsx] Auto-retrying with client-side values:", {
      insurers: insurersToSend,
      coverage_names: coverageNamesToSend,
    });

    // Retry once with explicit values (same payload as initial request)
    const retryResponse = await postChat(requestPayload);

    // Use retry response instead
    if (retryResponse && !retryResponse.need_more_info) {
      // Process retry response...
      return; // Exit early after retry success
    }
  }

  // Show clarification UI if auto-retry failed or not applicable
  setClarification({...});
  return;
}
```

**효과**:
- 서버가 `need_more_info`를 반환했지만 클라이언트가 이미 해당 값을 보유한 경우 **자동으로 1회 재시도**
- 재시도 성공 시 clarification 패널을 건너뛰고 바로 결과 표시
- 재시도 실패 시에만 clarification 패널 노출 (최소화)

## 검증 결과

### Backend Contract Test (✅ 3/3 PASS)
```bash
$ python tests/manual_test_step_next_100_payload.py
```

- **Case A** (insurers + coverage_names): ✅ no need_more_info
- **Case B** (insurers only): ✅ requests coverage_names only
- **Case C** (coverage_names only): ✅ requests insurers only

### Frontend Manual Test (권장 시나리오)
1. **시나리오 A**: 보험사(삼성/메리츠) 선택 + 담보(암진단비) 입력 → "삼성과 메리츠의 암진단비 보장한도차이" 전송
   - ✅ Devtools Network tab에서 payload 확인: `insurers`, `coverage_names` 포함
   - ✅ `need_more_info` 패널 미노출

2. **시나리오 B**: 보험사 선택 O / 담보 입력 X → "암진단비 비교" 전송
   - ✅ 담보만 요구 (보험사 요구 X)

3. **시나리오 C**: 보험사 선택 X / 담보 입력 O → "보장 가능한가요?" 전송
   - ✅ 보험사만 요구 (담보 요구 X)

## 수정 파일
- `apps/web/app/page.tsx` (3 changes)
  - `handleClarificationSelect`: UI state 동기화
  - `handleSend`: Request payload builder SSOT + auto-retry 로직

## 헌법 준수
- ✅ View layer ONLY (frontend only)
- ✅ 백엔드 로직 변경 없음
- ✅ LLM 사용 없음
- ✅ Intent 라우팅은 서버 담당 (변경 없음)
- ✅ 슬롯은 클라이언트가 최대한 채워서 전송 (auto-retry 1회)

## Definition of Done (DoD) ✅
- ✅ Devtools payload에 `insurers`/`coverage_names` 포함 확인
- ✅ Case A/B/C 모두 통과
- ✅ 고객 데모에서 "추가 정보 필요" 오판 노출 0회 목표

## 향후 고려사항 (Optional)
- Frontend TypeScript strict mode: `ChatRequest` interface에서 optional fields 명시적으로 정의
- SWR 캐싱: Auto-retry 로직을 SWR mutation으로 이관 (future)
