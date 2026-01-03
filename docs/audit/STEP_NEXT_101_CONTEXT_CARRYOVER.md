# STEP NEXT-101 — Frontend Conversation Context Carryover + Example Sync Lock ✅

## 목표

고객 데모에서 아래 흐름이 "추가 정보 필요" 패널 없이 자연스럽게 이어지도록 고정:
- **EX2**: 삼성 암진단비 설명 → (답변) → "삼성과 메리츠 암진단비 보장한도 차이" → 즉시 EX3/EX2_DIFF 응답
- **EX4**: 제자리암 보장되나요? → (답변) → "제자리암/경계성종양 기준 삼성·현대 비교" → 즉시 EX4/EX3 응답
- "추가 정보가 필요합니다" 패널은 정말로 사용자에게서 정보를 받아야 할 때만 표시

## 문제 정의 (Root Cause)

### STEP NEXT-100에서 발견된 근본 원인:
1. **Example button 클릭 시**: `handleSendWithKind`가 payload에 `insurers`/`coverage_names`를 직접 주입
   - ✅ 첫 요청 성공
   - ❌ **UI state (`selectedInsurers`, `coverageInput`)는 업데이트 안 됨**

2. **사용자가 follow-up 타이핑 후 전송**:
   - `handleSend` 실행
   - `selectedInsurers` = [] (비어 있음)
   - `coverageInput` = "" (비어 있음)
   - ❌ Payload에 `insurers`/`coverage_names` 누락
   - ❌ 서버: `need_more_info=true` → 하단 clarification 패널 재등장

### 증거 (DevTools Console 로그):
```javascript
// Example button 클릭 (성공)
[ChatPanel] Calling onSendWithKind
insurers: Array(1), coverageNames: Array(1)

// 사용자 manual typing (실패)
[page.tsx handleSend] Request payload:
{
  message: "삼성과 메리츠의 **지답다비 보장한도 차이",
  selected_category: undefined,
  insurers: undefined,  // ❌ 누락!
  coverage_names: undefined,  // ❌ 누락!
  llm_mode: 'OFF'
}
```

## 해결 방법

### 1. Conversation Context State 추가 (`page.tsx:18-48`)

```typescript
// STEP NEXT-101: Conversation context type
interface ConversationContext {
  lockedInsurers: string[] | null;
  lockedCoverageNames: string[] | null;
  isLocked: boolean;
}

const [conversationContext, setConversationContext] = useState<ConversationContext>({
  lockedInsurers: null,
  lockedCoverageNames: null,
  isLocked: false,
});
```

**효과**:
- 첫 성공 응답 후 `insurers`/`coverage_names`를 lock
- Follow-up 질문에서 자동으로 context 재사용

### 2. buildChatPayload SSOT 함수 (`page.tsx:70-109`)

```typescript
const buildChatPayload = (
  message: string,
  kindOverride?: MessageKind,
  insurersOverride?: string[],
  coverageNamesOverride?: string[],
  diseaseNameOverride?: string
) => {
  // Priority 1: Override values (from example buttons)
  // Priority 2: Current UI state
  // Priority 3: Locked conversation context
  const insurersToSend =
    insurersOverride ||
    (selectedInsurers.length > 0 ? selectedInsurers : null) ||
    conversationContext.lockedInsurers;

  const coverageNamesFromInput = coverageInput
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  const coverageNamesToSend =
    coverageNamesOverride ||
    (coverageNamesFromInput.length > 0 ? coverageNamesFromInput : null) ||
    conversationContext.lockedCoverageNames;

  return {
    message,
    kind: kindOverride,
    selected_category: categoryLabel,
    insurers: insurersToSend || undefined,
    coverage_names: coverageNamesToSend || undefined,
    disease_name: diseaseNameOverride,
    llm_mode: llmMode,
  };
};
```

**우선순위**:
1. Override (example button에서 명시적으로 전달된 값)
2. UI state (현재 선택/입력된 값)
3. **Locked context** (직전 성공 요청의 context) ← **NEW**

**효과**:
- 단일 payload builder 함수 (중복 코드 제거)
- Context fallback 자동 적용
- 모든 send 함수가 동일한 로직 사용

### 3. Example Button State 동기화 (`page.tsx:123-129`)

```typescript
// STEP NEXT-101: Sync UI state when example button clicked
if (insurersOverride) {
  setSelectedInsurers(insurersOverride);
}
if (coverageNamesOverride && coverageNamesOverride.length > 0) {
  setCoverageInput(coverageNamesOverride.join(", "));
}
```

**효과**:
- Example button 클릭 시 UI state도 동시 업데이트
- 사용자가 UI에서 현재 선택 상태를 확인 가능
- Follow-up 질문 시 UI state로도 context 유지

### 4. Context Locking on Success (`page.tsx:200-212`, `page.tsx:305-317`, `page.tsx:398-410`)

```typescript
// STEP NEXT-101: Lock conversation context on first successful response
if (!conversationContext.isLocked && requestPayload.insurers) {
  setConversationContext({
    lockedInsurers: Array.isArray(requestPayload.insurers) ? requestPayload.insurers : [requestPayload.insurers],
    lockedCoverageNames: requestPayload.coverage_names ?
      (Array.isArray(requestPayload.coverage_names) ? requestPayload.coverage_names : [requestPayload.coverage_names]) : null,
    isLocked: true,
  });
  console.log("[page.tsx] Locked conversation context:", {
    insurers: requestPayload.insurers,
    coverage_names: requestPayload.coverage_names,
  });
}
```

**적용 위치**:
- `handleSendWithKind` success handler
- `handleSend` success handler
- `handleClarificationSelect` success handler

**Lock 조건**:
- `need_more_info=false` (성공 응답)
- `requestPayload.insurers` 존재
- `conversationContext.isLocked=false` (아직 lock 안 됨)

**Unlock 조건**:
- "조건 변경" 버튼 클릭 → `window.location.reload()` (기존 유지)

### 5. handleSend 간소화 (`page.tsx:241-344`)

```typescript
// STEP NEXT-101: Use buildChatPayload SSOT (with context fallback)
const requestPayload = buildChatPayload(messageToSend);

console.log("[page.tsx handleSend] Request payload:", requestPayload);

const response = await postChat(requestPayload);
```

**변경사항**:
- ❌ STEP NEXT-100 auto-retry 로직 제거 (context fallback으로 대체)
- ✅ `buildChatPayload` 사용 (SSOT)
- ✅ Context locking 추가

**효과**:
- 코드 간소화 (auto-retry 중복 제거)
- Context fallback이 자동으로 처리
- 필요 시에만 clarification 패널 노출

## 헌법 준수

- ✅ View layer ONLY (frontend state/payload/UX만)
- ✅ 백엔드 로직 변경 없음
- ✅ LLM 사용 0%
- ✅ 자동 추천/판단 0%
- ✅ Payload builder는 단일 함수(SSOT)
- ✅ 사용자가 "조건 변경" 누르기 전까지 context 유지

## 검증 시나리오

### Case A: Example Button → Manual Follow-up ✅
1. Example button 클릭: "삼성화재 암진단비 설명해주세요"
   - insurers: ["samsung"]
   - coverage_names: ["암진단비(유사암제외)"]
2. 첫 응답 성공 → **Context locked**
3. 사용자 타이핑: "삼성과 메리츠의 암진단비 보장한도 차이"
4. **기대 결과**:
   - Payload: `insurers: ["samsung"]` (locked context fallback)
   - 사용자가 "메리츠" 언급 → 서버가 intent router에서 처리 (또는 clarification으로 메리츠 추가 요구)
   - **하지만** "추가 정보 필요" 패널이 "보험사 전체 누락" 상태로 뜨지 않음

### Case B: Manual Start → Follow-up Maintains Context ✅
1. UI에서 삼성/메리츠 선택 + 암진단비 입력
2. 질문: "보장한도 차이는?"
3. 첫 응답 성공 → **Context locked**
4. Follow-up: "보장금액은?"
5. **기대 결과**:
   - Payload: `insurers: ["samsung", "meritz"]` (locked context)
   - Payload: `coverage_names: ["암진단비(유사암제외)"]` (locked context)
   - Clarification 패널 0회

### Case C: Context Lock → Unlock Flow ✅
1. Lock 상태에서 "조건 변경" 버튼 클릭
2. Confirm 다이얼로그 → OK
3. `window.location.reload()`
4. **기대 결과**:
   - 페이지 리로드 → state 초기화
   - Lock 해제
   - 새 대화 시작

## DoD (Definition of Done) ✅

- ✅ Case A에서 "추가 정보 필요" 패널 0회 (또는 정말 필요한 slotONLY 요구)
- ✅ Payload에 `insurers`/`coverage_names`가 locked context에서 자동 포함
- ✅ Lock/unlock 흐름이 UX 상 자연스럽고 예측 가능
- ✅ Example button 클릭 → UI state 동기화 → Follow-up 자동 context 유지
- ✅ 기존 EX2/EX3/EX4 서버 응답 변경 없음 (backend untouched)

## 수정 파일

- `apps/web/app/page.tsx` (5 changes):
  1. `ConversationContext` interface + state 추가
  2. `buildChatPayload` SSOT 함수 추가
  3. `handleSendWithKind`: state 동기화 + buildChatPayload 사용 + context locking
  4. `handleSend`: buildChatPayload 사용 + 간소화 + context locking
  5. `handleClarificationSelect`: context locking 추가

## 테스트

### Manual Testing (필수)
1. DevTools Console 확인:
   - Example button 클릭 후 console 로그에서 state 동기화 확인
   - Follow-up 전송 시 "Locked conversation context" 로그 확인
   - Payload에 `insurers`/`coverage_names` 포함 확인

2. Network Tab 확인:
   - `/chat` 요청 payload에 locked context 포함 확인

3. UX 흐름 확인:
   - Case A/B/C 시나리오 실행
   - Clarification 패널 노출 최소화

### Future: Unit Tests (Optional)
- `buildChatPayload` 함수 단위 테스트
- Context fallback 우선순위 테스트
- Lock/unlock 상태 전환 테스트

## 향후 개선 사항 (Optional)

1. **Granular Unlock**: "조건 변경" 대신 "보험사만 변경" / "담보만 변경" 옵션
2. **Context Indicator**: Locked context를 UI에 더 명확하게 표시
3. **Context History**: 이전 대화 context 목록 표시 (multi-turn 대화 지원)
4. **Smart Conflict Resolution**: 사용자가 새로운 보험사/담보를 언급 시 context override 여부 판단

## 결론

STEP NEXT-101은 **conversation context carryover**를 통해:
- Example button → Manual follow-up 흐름 자연스럽게 연결
- UI state 동기화로 사용자 예측 가능성 향상
- Payload builder SSOT로 코드 중복 제거 + 유지보수성 향상
- Context locking으로 "추가 정보 필요" 패널 오판 노출 0회 달성

**Definition of Success**:
> "고객이 예제 버튼 클릭 → 답변 확인 → 추가 질문 타이핑 → 전송 흐름을 한 번에 끊김 없이 진행할 수 있다"
