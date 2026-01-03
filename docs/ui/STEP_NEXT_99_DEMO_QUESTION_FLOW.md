# STEP NEXT-99 — 고객 데모용 대표 질문 시나리오 LOCK

**Status**: 🔒 LOCKED
**Date**: 2026-01-03
**Scope**: Demo Flow / Docs / Example UX ONLY (NO logic changes)

---

## Purpose (목적)

고객이 설명 없이도 1분 안에

**"아, 이건 설명 → 비교 → 판단까지 자연스럽게 이어지는 시스템이구나"**

를 이해하도록 **대표 질문 흐름을 정답처럼 고정**한다.

⚠️ 본 STEP은 **기능 추가가 아닌 '질문 흐름의 표준화'**이다.

---

## Why EX3 Must Be Included (왜 EX3를 포함해야 하는가)

현재 시스템 구조는 이미 완성되어 있음:
- **EX2**: "이 상품이 뭐냐" (설명)
- **EX3**: "두 회사를 직접 비교" (비교)
- **EX4**: "이 조건이 되냐 안 되냐" (판단)

❗ **고객 데모에서 EX3가 빠지면**:
> "비교가 핵심인 시스템인데 왜 설명/판단만 보여주지?"

👉 따라서 대표 흐름에 **EX3를 '중앙 단계'로 명시적으로 고정**한다.

**EX3 Constitutional Lock**:
- ✅ 단일 담보 + 복수 보험사 비교 전용
- ❌ 담보 군집화 / eligibility / 추천 금지
- ❌ 다중 담보 비교 금지
- ✅ 본 STEP은 기존 EX3 설계 유지를 전제로 한다

---

## Representative Question Scenarios (대표 질문 시나리오 LOCK)

### 🎯 시나리오 A — EX2 → EX3 → EX2
**(설명 → 직접 비교 → 탐색 확장)**

#### [1] 설명 (Entry Point)
```
Q: 삼성화재 암진단비 얼마 나오나요?
```
- **Intent**: `EX2_DETAIL`
- **고객 질문**: "얼마 받지?"
- **Response**: 보장금액/한도/지급유형 + 질문 힌트 (STEP NEXT-98)

#### [2] 직접 비교 (Core Value)
```
Q: 삼성화재와 메리츠화재 암진단비 비교해줘
```
- **Intent**: `EX3_COMPARE`
- **고객 인식**: "아, 핵심 비교가 여기구나"
- **Response**: 2사 비교 테이블 (보장금액, 지급유형, 조건 차이)

#### [3] 탐색 확장 (Follow-up Discovery)
```
Q: 암진단비 관련 다른 담보 중 보장한도가 다른 상품
```
- **Intent**: `EX2_LIMIT_FIND`
- **고객 인식**: "상품 탐색까지 이어지네"
- **Response**: 보장한도 차이 분석 결과

**📌 Lock**: EX3는 반드시 **'1개 담보 × 2개 보험사' 비교만** 사용
(multi-coverage EX3 금지 유지)

---

### 🎯 시나리오 B — EX4 → EX3 → EX2
**(판단 → 비교 → 구조 이해)**

#### [1] 판단 (Entry Point)
```
Q: 제자리암 보장되나요?
```
- **Intent**: `EX4_ELIGIBILITY`
- **고객 질문**: "되는지 안 되는지"
- **Response**: O/△/X 매트릭스 + 종합평가 + 확장 힌트 (STEP NEXT-98)

#### [2] 비교 (Core Understanding)
```
Q: 제자리암 기준으로 삼성화재와 메리츠화재 상품 비교해줘
```
- **Intent**: `EX3_COMPARE`
- **고객 인식**: "보험사마다 다르네"
- **Response**: 제자리암 관련 담보 2사 비교

#### [3] 구조 확장 (Optional Deep Dive)
```
Q: 제자리암 관련 담보 중 보장한도가 다른 상품
```
- **Intent**: `EX2_LIMIT_FIND`
- **고객 인식**: "판단 → 비교 → 담보 구조까지 이어진다"
- **Response**: 보장한도 차이 분석

---

### 🎯 시나리오 C — EX3 단독 데모 (비교 핵심 강조)
**(직접 비교로 시작 → 전체 가치 전달)**

#### [1] 비교 바로 진입
```
Q: 삼성화재와 메리츠화재 암진단비 비교해줘
```
- **Intent**: `EX3_COMPARE`
- **데모 포인트**:
  - 보장금액 차이
  - 지급유형 차이
  - 조건 차이 (감액, 대기기간, 면책, 갱신)
- **고객 인식**:
  > "아, 이 시스템은 비교가 중심이구나"

**Follow-up Hints** (STEP NEXT-98):
- 말풍선 하단 힌트로 EX2 / EX4 자연스럽게 유도
- 고객이 스스로 다음 질문 생성

---

## Demo Flow Selection Guide (시나리오 선택 가이드)

| 고객 페르소나 | 추천 시나리오 | 이유 |
|------------|------------|------|
| **처음 사용자** | A (EX2 → EX3 → EX2) | "뭐 받지?"부터 시작해 자연스럽게 비교로 이어짐 |
| **비교 중심 고객** | C (EX3 단독) | 핵심 가치(비교)를 즉시 전달 |
| **조건 중심 고객** | B (EX4 → EX3 → EX2) | "되는지"부터 시작해 구조 이해로 확장 |
| **전체 시연** | A → B 순차 | 3가지 Intent 모두 시연 (5분 데모) |

---

## Forbidden Actions (절대 금지 사항)

❌ **신규 비즈니스 로직 추가**
❌ **자동 질문 실행 / 버튼 / 추천**
❌ **LLM 사용**
❌ **Intent 경계 침범**
  - EX2 = 설명
  - EX3 = 비교
  - EX4 = 판단
❌ **EX3에서 담보 군집화 / eligibility 추가**
❌ **EX3에서 다중 담보 비교**

---

## Allowed Exposures (허용 방식)

✅ **Example Card** (frontend, 문구 고정)
✅ **Demo Script** (human guide)
✅ **docs/ui 문서** (this file)
✅ **말풍선 하단 텍스트 힌트** (STEP NEXT-98)

❌ **자동 실행** ❌
❌ **버튼화** ❌
❌ **추천 문구** ❌

---

## Example Card Alignment (프론트엔드 예제 카드)

**Current State** (apps/web/components/ChatPanel.tsx):
```tsx
// 예제2: 담보 설명 (EX2_DETAIL)
"삼성화재 암진단비 설명해주세요"

// 예제3: 2사 비교 (EX3_COMPARE)
"삼성화재와 메리츠화재의 암진단비를 비교해주세요"

// 예제4: 보장 여부 확인 (EX4_ELIGIBILITY)
"제자리암 보장 가능한가요?"
```

**Alignment with Scenarios**:
- ✅ 시나리오 A Step 1 → 예제2 (EX2_DETAIL)
- ✅ 시나리오 A Step 2 → 예제3 (EX3_COMPARE)
- ✅ 시나리오 B Step 1 → 예제4 (EX4_ELIGIBILITY)
- ✅ All scenarios covered

**No Changes Required** — Current example buttons already aligned! ✅

---

## Demo Script (데모 진행 스크립트)

### 1-Minute Demo (핵심만)
```
[시나리오 C 사용]

"이 시스템은 보험 상품을 비교하는 도우미입니다.
예를 들어, '삼성화재와 메리츠화재 암진단비 비교해줘'라고 물어보면..."

[EX3_COMPARE 결과 표시]

"보시다시피 보장금액, 지급유형, 조건 차이를 한눈에 볼 수 있습니다.
말풍선 하단의 힌트를 따라 다음 질문도 이어갈 수 있어요."
```

### 3-Minute Demo (전체 흐름)
```
[시나리오 A 사용]

"먼저 하나의 상품을 설명해볼게요.
'삼성화재 암진단비 얼마 나오나요?'"

[EX2_DETAIL 결과 표시]

"보장금액과 조건이 나오죠. 그런데 혼자만 보면 모르니까,
말풍선 하단 힌트를 보면 '다른 보험사와 비교'를 제안하네요.
그럼 '삼성화재와 메리츠화재 암진단비 비교해줘'라고 물어볼까요?"

[EX3_COMPARE 결과 표시]

"이제 차이가 명확하게 보이죠.
이런 식으로 설명 → 비교 → 탐색이 자연스럽게 이어집니다."
```

### 5-Minute Demo (A + B 순차)
```
[시나리오 A 먼저, 이어서 시나리오 B]

"지금까지는 '얼마 받지?'로 시작했는데,
반대로 '되는지 안 되는지'로 시작할 수도 있어요.

'제자리암 보장되나요?'"

[EX4_ELIGIBILITY 결과 표시]

"O/△/X로 보장 여부를 보여주고,
아래 힌트를 따라 다시 비교로 이어질 수 있습니다.

즉, 설명 → 비교, 판단 → 비교, 비교 → 탐색
모든 경로가 자연스럽게 연결됩니다."
```

---

## Verification Checklist (검증 체크리스트)

### Functional
- [ ] 시나리오 A의 3단계 질문이 모두 정상 응답
- [ ] 시나리오 B의 3단계 질문이 모두 정상 응답
- [ ] 시나리오 C의 단독 질문이 정상 응답
- [ ] EX3 응답에 담보 군집화 없음 (단일 담보만)
- [ ] 모든 응답에 coverage_code 노출 0%

### UX
- [ ] 말풍선 하단 힌트(STEP NEXT-98)가 시나리오와 정합
- [ ] 예제 버튼이 시나리오 A/B/C와 정합
- [ ] 자동 실행 없음 (텍스트 힌트만)
- [ ] 고객이 1분 안에 "비교가 중심" 이해 가능

### Constitutional
- [ ] 기존 Intent 경계 침범 없음
- [ ] EX3 헌법 위반 없음 (단일 담보 + 복수 보험사만)
- [ ] 기존 로직 변경 0
- [ ] 기존 테스트 전부 PASS

---

## Definition of Done (DoD)

- [x] EX2 · EX3 · EX4 모두 포함된 대표 질문 흐름 고정
- [x] 고객 데모 시 이 시나리오만으로 전체 가치 전달 가능
- [x] 기존 로직/테스트 변경 0
- [x] 헌법 위반 0
- [x] "이 시스템은 비교(EX3)가 중심" 메시지 명확

---

## Final Declaration (최종 선언)

**STEP NEXT-99는 '기능 개발'이 아니라**
**'이 제품을 어떻게 보여줄 것인가'에 대한 최종 답이다.**

- **시스템은 이미 충분히 강하다**
- **이제는 질문 순서 자체가 UX**

**LOCK 상태**: 🔒 **LOCKED**
**적용 범위**: **Demo / Docs / Example UX ONLY**

---

## Related Documents

- STEP NEXT-77: EX3_COMPARE Response Schema Lock
- STEP NEXT-86: EX2_DETAIL Lock
- STEP NEXT-79: EX4_ELIGIBILITY Overall Evaluation Lock
- STEP NEXT-98: Question Continuity Hints
- STEP NEXT-97: Customer Demo UX Stabilization

---

**한 줄 요약**: "EX2(설명) → EX3(비교) → EX4(판단), 3가지 Intent가 자연스럽게 이어지는 질문 흐름이 곧 제품의 핵심 UX다." 🔒
