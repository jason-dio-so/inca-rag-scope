# STEP NEXT-102 — EX2 Context Continuity Lock (Frontend)

## 목표

EX2 데모 플로우를 자연스럽게 만들어 아래 시나리오가 "추가 정보 필요" 패널 없이 자동 진행되도록 고정:

1. **EX2 버튼** → 삼성 EX2_DETAIL 출력
2. **"메리츠는?"** → 담보 유지 + 보험사만 meritz로 전환 → EX2_DETAIL 출력
3. **"암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"** → 삼성+메리츠 기준 EX2_LIMIT_FIND 실행 → 표 형태 결과
4. **불필요한 clarification 패널 0회** (필요 시에만 표시)

## 헌법 준수

- ✅ LLM = 0%, deterministic only
- ✅ Intent 경계 고정 (EX2_DETAIL / EX2_LIMIT_FIND / EX2_DETAIL_DIFF)
- ✅ UI 노출 금지: coverage_code(bare: A4200_1) 절대 노출 금지
- ✅ Refs only: PD:/EV: prefix만 허용
- ✅ "추정/추천/판단" 금지 (EX2에서는 사실 표시만)
- ✅ Frontend only (backend untouched)

## 문제 정의

### STEP NEXT-101에서 발견된 추가 이슈:

1. **Insurer Switch 미지원**:
   - EX2_DETAIL(삼성) 출력 후 "메리츠는?" 입력
   - Context는 삼성으로 lock
   - 서버가 다시 삼성 EX2_DETAIL로 라우팅

2. **LIMIT_FIND 단일 보험사 오류**:
   - "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" 입력
   - insurers = ["samsung"] (1개)
   - 서버가 need_more_info 또는 EX2_DETAIL로 fallback
   - 2사 비교 필요한데 1사만 context에 존재

3. **Clarification Handler 덮어쓰기**:
   - Clarification에서 보험사 추가 선택 시
   - 기존 insurers를 replace (삼성 → 메리츠)
   - 원하는 동작: 삼성 + 메리츠 (merge)

## 해결 방법

### 1. Context Utils 추가 (`apps/web/lib/contextUtils.ts`)

#### isInsurerSwitchUtterance()
```typescript
/**
 * Detect if message is an insurer switch utterance
 * Examples: "메리츠는?", "메리츠는요?", "메리츠도", "그럼 메리츠", "메리츠화재는?"
 */
export function isInsurerSwitchUtterance(message: string): boolean {
  const patterns = [
    /^(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?(\s*는요?|\s*는|\s*도|\s*는요|\s*는지)?\??$/,
    /^그럼\s+(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?(\s*는요?|\s*는|\s*도)?\??$/,
    /^(메리츠|삼성|한화|현대|kb|롯데|흥국|홍국)(\s*화재)?\s*상품(\s*은|\s*는)?\??$/,
  ];

  return patterns.some(pattern => pattern.test(normalized));
}
```

**효과**:
- "메리츠는?" 같은 간결한 질문을 insurer switch로 인식
- Deterministic regex pattern matching
- NO LLM usage

#### extractInsurerFromSwitch()
```typescript
export function extractInsurerFromSwitch(message: string): string | null {
  const insurerMap: Record<string, string> = {
    '메리츠': 'meritz',
    '삼성': 'samsung',
    '한화': 'hanwha',
    '현대': 'hyundai',
    'kb': 'kb',
    '롯데': 'lotte',
    '흥국': 'heungkuk',
  };

  for (const [keyword, code] of Object.entries(insurerMap)) {
    if (normalized.includes(keyword)) {
      return code;
    }
  }

  return null;
}
```

**효과**:
- 보험사명 키워드 → insurer code 변환
- Deterministic keyword matching

#### isLimitFindPattern()
```typescript
export function isLimitFindPattern(message: string): boolean {
  const keywords = {
    diff: ['다른', '차이', '비교'],
    target: ['담보', '상품', '보장'],
    action: ['한도', '찾', '알려'],
  };

  const hasDiff = keywords.diff.some(k => normalized.includes(k));
  const hasTarget = keywords.target.some(k => normalized.includes(k));
  const hasAction = keywords.action.some(k => normalized.includes(k));

  // Need at least 2 out of 3 categories
  const matchCount = [hasDiff, hasTarget, hasAction].filter(Boolean).length;

  return matchCount >= 2;
}
```

**효과**:
- "다른 담보", "보장한도가 다른", "차이 찾아줘" → LIMIT_FIND 패턴 인식
- Deterministic keyword combination matching

### 2. handleSend() Insurer Switch Detection (`page.tsx:255-267`)

```typescript
// STEP NEXT-102: Detect insurer switch ("메리츠는?")
if (isInsurerSwitchUtterance(messageToSend)) {
  const newInsurer = extractInsurerFromSwitch(messageToSend);
  if (newInsurer && conversationContext.lockedCoverageNames) {
    console.log("[page.tsx] Insurer switch detected:", newInsurer);
    // Switch insurer, keep coverage_names
    setSelectedInsurers([newInsurer]);
    setConversationContext({
      ...conversationContext,
      lockedInsurers: [newInsurer],
    });
  }
}
```

**흐름**:
1. "메리츠는?" 감지
2. `newInsurer = "meritz"` 추출
3. `lockedInsurers = ["meritz"]`로 업데이트
4. `lockedCoverageNames`는 유지
5. 이후 payload는 meritz + 기존 coverage_names로 전송

**효과**:
- 보험사만 전환, 담보는 유지
- EX2_DETAIL → EX2_DETAIL 자연스러운 연결

### 3. handleSend() LIMIT_FIND Validation (`page.tsx:269-300`)

```typescript
// STEP NEXT-102: Detect LIMIT_FIND pattern and validate multi-insurer requirement
if (isLimitFindPattern(messageToSend)) {
  const currentInsurers = selectedInsurers.length > 0
    ? selectedInsurers
    : conversationContext.lockedInsurers || [];

  if (currentInsurers.length < 2) {
    // Need at least 2 insurers for LIMIT_FIND
    console.log("[page.tsx] LIMIT_FIND pattern detected but only 1 insurer, showing selection UI");

    // Add user message first
    const userMessage: Message = {
      role: "user",
      content: messageToSend,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Show clarification with insurers selection
    setClarification({
      missing_slots: ["insurers"],
      options: {
        insurers: config.available_insurers.map(i => i.code),
      },
      draftRequest: {
        message: messageToSend,
        coverage_names: conversationContext.lockedCoverageNames || undefined,
        llm_mode: llmMode,
      },
    });
    return;
  }
}
```

**흐름**:
1. "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" 감지
2. 현재 insurers = ["samsung"] (1개)
3. LIMIT_FIND는 2사 이상 필요 → clarification 패널 표시
4. 사용자가 메리츠 선택
5. Clarification handler가 자동 재전송 (samsung + meritz)

**효과**:
- LIMIT_FIND 요청 시 2사 이상 보장
- 부족하면 명확한 UI 유도
- 자동 재전송으로 매끄러운 UX

### 4. handleClarificationSelect() Insurer Merge (`page.tsx:416-427`)

```typescript
} else if (slotName === "insurers") {
  // STEP NEXT-102: For LIMIT_FIND flow, ADD to existing insurers (don't replace)
  const existingInsurers = conversationContext.lockedInsurers || [];
  const newInsurers = Array.isArray(value) ? value : [value];

  // Merge: keep existing + add new (dedupe)
  const mergedInsurers = [...new Set([...existingInsurers, ...newInsurers])];

  updatedRequest.insurers = mergedInsurers;
  // STEP NEXT-100: Update UI state so next request includes this value
  setSelectedInsurers(mergedInsurers);
}
```

**변경 전**:
```typescript
updatedRequest.insurers = Array.isArray(value) ? value : [value];
// Result: [meritz] (삼성 삭제됨)
```

**변경 후**:
```typescript
const mergedInsurers = [...new Set([...existingInsurers, ...newInsurers])];
updatedRequest.insurers = mergedInsurers;
// Result: [samsung, meritz] (기존 + 신규)
```

**효과**:
- Clarification에서 보험사 추가 시 기존 보험사 유지
- LIMIT_FIND 흐름에서 2사 조건 자동 충족

## 검증 시나리오

### Case A: EX2 Button → Meritz Switch → LIMIT_FIND ✅

```
1. EX2 예제 버튼: "삼성화재 암진단비 설명해주세요"
   → EX2_DETAIL, insurers: ["samsung"], coverage_names: ["암진단비(유사암제외)"]
   → Context locked: {lockedInsurers: ["samsung"], lockedCoverageNames: ["암진단비(유사암제외)"]}

2. 입력: "메리츠는?"
   → isInsurerSwitchUtterance() = true
   → extractInsurerFromSwitch() = "meritz"
   → Context update: {lockedInsurers: ["meritz"], lockedCoverageNames: ["암진단비(유사암제외)"]}
   → Payload: {insurers: ["meritz"], coverage_names: ["암진단비(유사암제외)"]}
   → EX2_DETAIL, meritz

3. 입력: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
   → isLimitFindPattern() = true
   → currentInsurers = ["meritz"] (1개)
   → Clarification 패널: "비교할 보험사 추가"
   → 사용자 선택: "삼성화재"
   → mergedInsurers = ["meritz", "samsung"] (2개)
   → Payload: {insurers: ["meritz", "samsung"], coverage_names: [...]}
   → EX2_LIMIT_FIND, 표 형태 결과
```

**기대 결과**:
- ✅ "메리츠는?" → 보험사만 전환
- ✅ LIMIT_FIND → 2사 조건 충족 → 표 출력
- ✅ Clarification 패널 1회만 (필요 시)

### Case B: Single Insurer LIMIT_FIND → Add Insurer UI ✅

```
1. EX2_DETAIL 상태: insurers: ["samsung"]
2. 입력: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
   → isLimitFindPattern() = true
   → currentInsurers = ["samsung"] (1개 < 2)
   → Clarification 패널: insurers selection
3. 사용자 선택: "메리츠화재"
   → mergedInsurers = ["samsung", "meritz"]
   → 자동 재전송
   → EX2_LIMIT_FIND 실행
```

**기대 결과**:
- ✅ 부족한 보험사 선택 UI 표시
- ✅ 선택 즉시 자동 재전송
- ✅ 불필요한 clarification 패널 최소화

### Case C: Payload Integrity Check ✅

DevTools Console 로그:
```javascript
[page.tsx] Insurer switch detected: meritz
[page.tsx] LIMIT_FIND pattern detected but only 1 insurer, showing selection UI
[page.tsx handleClarificationSelect] Merged insurers: ["meritz", "samsung"]
[page.tsx handleClarificationSelect] Request payload: {
  message: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘",
  insurers: ["meritz", "samsung"],
  coverage_names: ["암진단비(유사암제외)"],
  llm_mode: "OFF"
}
```

**기대 결과**:
- ✅ 모든 send에서 insurers/coverage_names 포함
- ✅ Context fallback 동작
- ✅ Merge 로직 동작

## 수정 파일

- `apps/web/lib/contextUtils.ts` (NEW):
  - `isInsurerSwitchUtterance()`
  - `extractInsurerFromSwitch()`
  - `isLimitFindPattern()`
  - `getInsurerDisplayName()`

- `apps/web/app/page.tsx` (3 changes):
  1. Import contextUtils functions
  2. `handleSend()`: Insurer switch detection + LIMIT_FIND validation
  3. `handleClarificationSelect()`: Insurer merge logic

## 금지 사항

- ❌ "메리츠는?"를 서버에서 LLM으로 해석 금지
- ❌ insurers 자동추정/자동추가 금지
- ❌ coverage_code UI/말풍선 노출 금지
- ❌ EX2에서 추천/판단 문구 금지
- ❌ 무한 재시도/자동 루프 금지 (auto-retry는 최대 1회)
- ❌ DB 스키마 작업 금지
- ❌ Backend 변경 금지

## DoD (Definition of Done)

- ✅ Case A/B/C 모두 통과 (로그 포함)
- ✅ EX2 흐름에서 불필요한 "추가 정보 필요" 패널 0회 (auto-retry/context로 해결)
- ✅ "메리츠는?"가 항상 보험사 전환으로 동작
- ✅ LIMIT_FIND 질문이 2사 기준으로 실행되거나, 1사면 추가 선택 → 자동 재전송
- ✅ coverage_code UI 노출 0%
- ✅ 회귀 테스트 PASS (기존 EX2/EX3/EX4 계약 테스트 유지)

## 향후 개선 사항 (Optional)

1. **Smart Insurer Inference**: "메리츠와 삼성 비교" → 자동으로 insurers = ["meritz", "samsung"]
2. **Coverage Switch**: "그럼 뇌출혈진단비는?" → coverage_names 전환
3. **Multi-turn History**: 이전 N턴의 context 저장 및 rollback
4. **Undo/Redo**: "이전 보험사로 돌아가줘" 같은 명령 지원

## Definition of Success

> "삼성 EX2 → 메리츠는? → LIMIT_FIND 흐름이 추가 정보 패널 없이 자연스럽게 이어진다"
