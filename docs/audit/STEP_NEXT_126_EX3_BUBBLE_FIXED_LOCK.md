# STEP NEXT-126: EX3_COMPARE Fixed Bubble Template Lock

**Status**: ✅ LOCKED
**Date**: 2026-01-04
**Scope**: View Layer ONLY (Frontend)

---

## 목표

EX3_COMPARE 화면에서 왼쪽 말풍선(Left Bubble) 내용을 **항상 동일한 "6줄 구조 요약 템플릿"**으로 완전 고정한다.

**핵심 원칙**:
- **재현성**: 같은 입력 → 항상 같은 말풍선
- **예측 가능성**: 고객 테스트 환경에서 일관된 UX 제공
- **View Layer ONLY**: 프론트엔드 렌더링 분기만 수정, API/백엔드 변경 금지

---

## 문제 정의 (증거 기반)

### 증상
- 네트워크 payload에 `kind: "EX3_COMPARE"`가 와도,
- 왼쪽 말풍선이 고정 템플릿이 아닌 `title`/`summary_bullets` 기반 텍스트로 렌더되어 변경이 없어 보이는 문제 발생

### 근본 원인
- UI가 EX3 전용 말풍선 경로를 100% 쓰지 않고 legacy 요약 경로를 혼용 중
- `bubble_markdown`, `title`, `summary_bullets`가 모두 말풍선에 혼용되어 데이터 변화에 따라 텍스트가 달라짐

---

## 구현 방식

### 1. Fixed Bubble Template (LOCKED, 6 lines)

**템플릿 구조** (줄바꿈 포함 그대로 사용):

```markdown
{A}는 진단 시 **정해진 금액을 지급하는 구조**이고,
{B}는 **보험기간 중 지급 횟수 기준으로 보장이 정의됩니다.**

**즉,**
- {A}: 지급 금액이 명확한 정액 구조
- {B}: 지급 조건 해석이 중요한 한도 구조
```

**변수**:
- `{A}` = 보험사1 display name (예: "삼성화재")
- `{B}` = 보험사2 display name (예: "메리츠화재")

**템플릿 특성**:
- "암진단비 케이스" 기준으로 이미 고객/팀이 합의한 구조 요약
- 현 단계 목표: **내용의 완전 고정 (재현성)**
- 커버리지별 문구 다양화는 다음 STEP에서만 허용

---

### 2. 구현 파일

#### 신규 유틸리티: `apps/web/lib/ex3BubbleTemplate.ts`
- `buildEX3FixedBubble(insurer1Code, insurer2Code)`: 고정 템플릿 생성
- `extractInsurerCodesForEX3(requestPayload)`: Payload에서 보험사 코드 추출

#### 수정 파일: `apps/web/app/page.tsx`
- Import: `buildEX3FixedBubble`, `extractInsurerCodesForEX3`
- `handleSend`: EX3_COMPARE 분기 추가 (lines 324-334)
- `handleClarificationSelect`: EX3_COMPARE 분기 추가 (lines 450-460)

**핵심 로직**:
```typescript
if (vm?.kind === "EX3_COMPARE") {
  // STEP NEXT-126: Force fixed template (ignore all backend text)
  const insurerCodes = extractInsurerCodesForEX3(requestPayload);
  if (insurerCodes) {
    summaryText = buildEX3FixedBubble(insurerCodes[0], insurerCodes[1]);
  } else {
    // Fallback: cannot extract insurers
    summaryText = vm?.bubble_markdown || "비교 결과를 표시할 수 없습니다.";
  }
} else if (vm?.bubble_markdown) {
  // Other kinds use bubble_markdown
  summaryText = vm.bubble_markdown;
} else {
  // Legacy fallback
  summaryText = [title, ...bullets].join("\n\n");
}
```

---

## Constitutional Rules (LOCKED)

### ✅ Allowed
- EX3_COMPARE 말풍선: 고정 6줄 템플릿만 사용
- 보험사명: Display name ONLY (삼성화재, 메리츠화재)
- Deterministic pattern matching
- View layer ONLY (frontend 렌더링 분기)

### ❌ Forbidden
- EX3_COMPARE에서 `summary_bullets`/`title`/`bubble_markdown` 텍스트를 말풍선에 섞기
- "EX3_COMPARE bubble을 데이터 기반으로 더 똑똑하게 만들기" (다음 단계)
- 백엔드/IntentRouter/Composer 수정 (이번 STEP은 프론트 고정만)
- EX2/EX4 말풍선 구조 변경
- 추천/판단/유리함 언급
- "일부 보험사는 …" 문구 재도입
- Insurer code 노출 (samsung, meritz 등)

---

## 검증 시나리오

### 시나리오 A (핵심)
**입력**: "삼성화재와 메리츠화재 암진단비 비교해줘"

**기대**:
- 네트워크: `kind = "EX3_COMPARE"`
- 왼쪽 말풍선: 위 6줄 템플릿이 항상 동일
- `summary_bullets`가 무엇이든 왼쪽 말풍선에는 절대 등장하지 않음

### 시나리오 B (회귀)
**EX2_DETAIL**: "삼성화재 암진단비 설명해줘"
- 기대: EX2는 기존대로 (고정 헤더/가벼운 대화형 문장 유지)

**EX4_ELIGIBILITY**: 기존 입력 1개
- 기대: 변경 없음

### 시나리오 C (코드 노출 0%)
- UI 어디에도 `samsung`, `meritz` 같은 insurer_code 문자열이 보이면 실패

---

## 테스트

### 수동 검증 (Required)
1. "삼성화재와 메리츠화재 암진단비 비교해줘" 입력
2. 왼쪽 말풍선 텍스트 확인 → 6줄 템플릿과 정확히 일치해야 함
3. 동일 입력 5회 반복 → 항상 동일한 텍스트
4. 개발자 콘솔 로그 확인: `[page.tsx handleSend] EX3_COMPARE: Using fixed 6-line template`
5. 오른쪽 ResultDock: 상세 비교 테이블 정상 표시
6. EX2/EX4 회귀 테스트: 기존대로 동작

### Contract Test (Future)
- `tests/test_step_next_126_ex3_bubble_fixed.py` (프론트 테스트 인프라 구축 시)
- EX3_COMPARE일 때 bubble markdown이 정확히 템플릿과 일치하는지 (줄바꿈 포함)
- `summary_bullets` 텍스트가 bubble에 포함되지 않는지

---

## Definition of Done (DoD)

- ✅ EX3_COMPARE 왼쪽 말풍선이 항상 동일한 6줄 템플릿으로 출력된다
- ✅ EX3_COMPARE에서 `summary_bullets`/`title` 기반 텍스트가 말풍선에 0% 등장한다
- ✅ EX2/EX4 회귀 없음
- ✅ Insurer code 노출 0%
- ✅ Dev server 정상 실행 (`npm run dev` 성공)
- ✅ SSOT 문서 + CLAUDE.md 업데이트 완료

---

## 구현 증거

### 파일 목록
1. **신규**: `apps/web/lib/ex3BubbleTemplate.ts`
   - `buildEX3FixedBubble()`: 고정 템플릿 생성기
   - `extractInsurerCodesForEX3()`: Payload에서 보험사 코드 추출

2. **수정**: `apps/web/app/page.tsx`
   - `handleSend`: EX3_COMPARE 분기 (lines 324-334)
   - `handleClarificationSelect`: EX3_COMPARE 분기 (lines 450-460)
   - Import 추가: `buildEX3FixedBubble`, `extractInsurerCodesForEX3`

3. **문서**: `docs/audit/STEP_NEXT_126_EX3_BUBBLE_FIXED_LOCK.md` (This file)

### Build 상태
```bash
npm run dev
# ✓ Compiled successfully
# ▲ Next.js ready at http://localhost:3000
```

---

## 다음 단계 (STEP NEXT-127+)

**STEP NEXT-127**: EX3 Bubble Template Variation (커버리지별 문구 다양화)
- 현재: "암진단비" 케이스 고정 템플릿
- 다음: 커버리지 종류(진단/치료/수술)별 구조 요약 문구 분기
- 단, **재현성 원칙 유지**: 같은 커버리지 → 항상 같은 템플릿

**금지 사항 (ABSOLUTE)**:
- 데이터 기반 동적 문구 생성 (LLM 사용 금지)
- "더 똑똑한" 요약 (추론/판단/추천 금지)
- 보험사별 차이를 수치로 설명 (구조 차이만 설명)

---

**LOCKED**: 2026-01-04
**Review Required**: 새로운 EX3 bubble 요구사항 발생 시 이 문서를 먼저 확인하고 STEP 번호 부여
