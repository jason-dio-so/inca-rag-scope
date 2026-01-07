# STEP NEXT-3 — UI Skeleton & View Model 매핑

**문서 목적**: Response View Model을 UI 구조로 매핑 (디자인 제외)
**작성일**: 2025-12-28
**선행 문서**: `docs/ui/STEP_NEXT_2_RESPONSE_VIEW_MODEL_AND_UX.md` (헌법)

---

## 0. 절대 원칙 (Immutable Rules)

### 0.1 UI의 역할
- ✅ Response View Model 5-block 구조를 **그대로 렌더링**
- ❌ 판단, 추론, 가공, 재해석 **절대 금지**

### 0.2 데이터 흐름
```
API Response (JSON)
  ↓
View Model 5 blocks
  ↓
UI Components (렌더링만)
  ↓
User Screen
```

---

## 1. 첫 화면 (Entry Screen)

### 1.1 화면 구조 (Top → Bottom)

```
┌─────────────────────────────────────────────┐
│ [1] 시스템 소개 영역                         │
│ [2] 입력창                                   │
│ [3] 예시 질문 버튼                           │
│ [4] 하단 안내                                │
└─────────────────────────────────────────────┘
```

### 1.2 영역별 상세

#### [1] 시스템 소개 영역

**컴포넌트**: `<IntroSection>`

**내용**:
```
💬 보험 상품 비교 도우미

저는 보험 약관과 가입설계서를 기반으로
객관적인 정보를 제공합니다.
```

**세부 요소** (접기/펼치기 가능):
- ✅ 제가 할 수 있는 것
  - 여러 보험사 상품의 보장 내용 비교
  - 특정 담보 보장 여부 확인
  - 문서 기반 사실 정보 제공 (출처 명시)

- ❌ 제가 할 수 없는 것
  - 개인 맞춤 상품 추천
  - 개인별 보험료 계산
  - 문서에 없는 내용 추론

---

#### [2] 입력창

**컴포넌트**: `<QueryInput>`

**속성**:
- `placeholder`: "질문을 입력하세요..."
- `maxLength`: 500
- `onSubmit`: API 호출 트리거

---

#### [3] 예시 질문 버튼

**컴포넌트**: `<ExampleQuestions>`

**버튼 3개** (고정):
1. "삼성생명과 한화생명 건강보험을 비교해줘" (예제 3형 - 종합 비교)
2. "메리츠화재와 DB손해보험 암 진단비 비교" (예제 2형 - 담보 비교)
3. "DB손해보험은 뇌출혈 보장되나요?" (예제 4형 - 보장 여부)

**동작**:
- 클릭 시 → 입력창에 질문 자동 입력 → 전송

**보험료 예제 처리**:
- 버튼 표시하되 비활성화 OR
- 클릭 시 경고 모달: "보험료 비교는 참고용 정보만 제공합니다"

---

#### [4] 하단 안내

**컴포넌트**: `<Footer>`

**내용**:
```
본 시스템은 보험 약관 및 가입설계서 기반 정보 제공만 수행합니다.
개인 맞춤 추천 및 보험료 계산은 제공하지 않습니다.
```

---

## 2. 응답 화면 (Response Screen)

### 2.1 전체 레이아웃 (고정 순서)

```
┌─────────────────────────────────────────────┐
│ [User Message Bubble]                        │
│ 삼성생명과 한화생명 건강보험을 비교해줘       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ [System Response Bubble]                     │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ [Block 1] Query Summary                 │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ [Block 2] Comparison (핵심)             │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ [Block 3] Notes                         │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ ┌─────────────────────────────────────────┐ │
│ │ [Block 4] Limitations                   │ │
│ └─────────────────────────────────────────┘ │
│                                              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ [Continue Query Input]                       │
└─────────────────────────────────────────────┘
```

### 2.2 Block 1: Query Summary

**컴포넌트**: `<QuerySummaryBlock>`

**구조**:
```
📋 비교 대상 상품

• 삼성생명 건강보험
• 한화생명 건강보험
```

**View Model 매핑**:

| View Model Field | UI Element | 표시 규칙 |
|---|---|---|
| `query_summary.original_query` | 숨김 (User bubble에 이미 표시) | - |
| `query_summary.interpreted_intent` | 제목 (`📋 비교 대상 상품`) | 고정 문구 |
| `query_summary.target_products[].insurer` | 리스트 항목 | 회사명 |
| `query_summary.target_products[].product_name` | 리스트 항목 | 상품명 (회사명 바로 옆) |

**렌더링 예**:
```html
<section>
  <h3>📋 비교 대상 상품</h3>
  <ul>
    {target_products.map(p =>
      <li>{p.insurer} {p.product_name}</li>
    )}
  </ul>
</section>
```

---

### 2.3 Block 2: Comparison (핵심)

**컴포넌트**: `<ComparisonBlock>`

**구조**:
```
📊 보장 비교표

┌──────────────┬─────────────────┬─────────────────┐
│ 담보         │ 삼성생명        │ 한화생명        │
│              │ 건강보험        │ 건강보험        │
├──────────────┼─────────────────┼─────────────────┤
│ 암 진단비    │ 3,000만원       │ 5,000만원       │
│              │ 📄 가입p.3      │ 📄 가입p.2      │
├──────────────┼─────────────────┼─────────────────┤
│ 유사암 진단비│ 300만원(기타피부│ 500만원(유사암  │
│              │ 암), 600만원(갑 │ 통합)           │
│              │ 상선암)         │                 │
│              │ 📄 가입p.3      │ 📄 가입p.2      │
├──────────────┼─────────────────┼─────────────────┤
│ ... (9개 담보 전체)                             │
└──────────────┴─────────────────┴─────────────────┘
```

**View Model 매핑**:

| View Model Field | UI Element | 표시 규칙 |
|---|---|---|
| `comparison.dimensions[].label` | 테이블 행 헤더 | 왼쪽 컬럼 |
| `comparison.products[].insurer` | 테이블 컬럼 헤더 (상단) | 회사명 |
| `comparison.products[].product_name` | 테이블 컬럼 헤더 (하단) | 상품명 |
| `comparison.products[].rows[key].value` | 테이블 셀 본문 | 값 (볼드체) |
| `comparison.products[].rows[key].evidence` | 테이블 셀 하단 | 작은 글씨 + 아이콘 |
| `comparison.dimensions[].type` | 셀 렌더링 방식 결정 | boolean → O/X, amount → 금액, text → 텍스트 |

**type별 렌더링 규칙**:

| type | value 예시 | 렌더링 |
|---|---|---|
| `boolean` | `true` | ✓ (O) |
| `boolean` | `false` | ✗ (X) |
| `amount` | `"3,000만원"` | 3,000만원 |
| `text` | `"90일"` | 90일 |
| `*` | `"확인 불가"` | 확인 불가 (회색) |

**Evidence 표시**:
- Evidence 있음: `📄 약관 p.12`
- Evidence 없음: `📄 확인 불가` (회색)

**모바일 대응**:
- 테이블 가로 스크롤 가능
- 첫 컬럼(담보명) 고정 (sticky)

---

### 2.4 Block 3: Notes

**컴포넌트**: `<NotesBlock>`

**구조**:
```
📝 요약

두 상품 모두 암, 뇌졸중, 심장질환을 보장합니다.

[펼치기 ▼] 상세 내용

(펼친 상태)
• 암 진단비: 한화생명이 5,000만원으로 더 높습니다 (삼성생명 3,000만원).
• 유사암 진단비: 한화생명은 통합 지급 (500만원), 삼성생명은 암종별 차등 지급.
• 뇌출혈/급성심근경색 진단비: 한화생명이 각 1,500만원으로 더 높습니다 (삼성생명 각 1,000만원).
... (7개 항목)
```

**View Model 매핑**:

| View Model Field | UI Element | 표시 규칙 |
|---|---|---|
| `notes.summary` | 본문 상단 | 항상 표시 |
| `notes.details[]` | 리스트 (접기/펼치기) | 기본 숨김, 클릭 시 펼침 |

**기본 상태**: 접힌 상태 (summary만 표시)

---

### 2.5 Block 4: Limitations

**컴포넌트**: `<LimitationsBlock>`

**구조**:
```
⚠️ 주의사항

[접기/펼치기 ▼]

(펼친 상태)
• 본 비교는 약관 및 가입설계서에 기반한 정보 제공입니다.
• 대기기간, 감액기간, 면책사항 등 세부 조건은 약관을 직접 확인하시기 바랍니다.
• 개인 조건에 따른 보험료 계산은 포함되지 않습니다.
• 상품 추천이나 가입 판단을 대신하지 않습니다.
• 보장 내용은 가입 시점 및 특약 구성에 따라 달라질 수 있습니다.
```

**View Model 매핑**:

| View Model Field | UI Element | 표시 규칙 |
|---|---|---|
| `limitations[]` | 리스트 (접기/펼치기) | 기본 접힘, 클릭 시 펼침 |

**기본 상태**: 접힌 상태

---

## 3. 특수 케이스 처리

### 3.1 Premium Notice (보험료 경고)

**조건**: `meta.premium_notice === true`

**UI 동작**:
- Query Summary 위에 경고 박스 삽입

**구조**:
```
┌─────────────────────────────────────────────┐
│ ⚠️ 보험료 안내                               │
│                                              │
│ 보험료는 개인별 조건 (나이, 성별, 건강상태   │
│ 등)에 따라 달라집니다. 본 시스템은 개인별    │
│ 보험료 계산 기능을 제공하지 않으며, 문서상   │
│ 예시만 표시합니다.                           │
│                                              │
│ 정확한 보험료는 보험사 또는 설계사를 통해    │
│ 확인하시기 바랍니다.                         │
└─────────────────────────────────────────────┘
```

**컴포넌트**: `<PremiumNotice>`

**조건부 렌더링**:
```javascript
{meta.premium_notice && <PremiumNotice />}
```

---

### 3.2 확인 불가 (No Evidence)

**조건**: `value === "확인 불가"` OR `evidence === null`

**UI 표시**:
- 값: `확인 불가` (회색)
- Evidence: `📄 확인 불가` (회색)

**예**:
```
┌──────────────┬─────────────────┐
│ 대기기간     │ 확인 불가       │
│              │ 📄 확인 불가    │
└──────────────┴─────────────────┘
```

---

## 4. View Model → UI 전체 매핑 테이블

### 4.1 Meta Block

| View Model Field | UI Component | 위치 | 표시 규칙 |
|---|---|---|---|
| `meta.response_type` | 숨김 | - | 내부 로직 전용 |
| `meta.confidence_level` | 숨김 | - | 항상 "document-based" |
| `meta.premium_notice` | `<PremiumNotice>` | Query Summary 위 | true → 경고 박스 표시 |
| `meta.generated_at` | `<Footer>` | 화면 최하단 | "생성 시각: 2025-12-28 10:00" |

### 4.2 Query Summary Block

| View Model Field | UI Component | 위치 | 표시 규칙 |
|---|---|---|---|
| `query_summary.original_query` | 숨김 | - | User bubble에 이미 표시 |
| `query_summary.interpreted_intent` | `<h3>` | Block 제목 | "📋 비교 대상 상품" 고정 |
| `query_summary.target_insurers[]` | 숨김 | - | target_products에 포함 |
| `query_summary.target_products[]` | `<ul><li>` | 리스트 | "회사명 상품명" |

### 4.3 Comparison Block

| View Model Field | UI Component | 위치 | 표시 규칙 |
|---|---|---|---|
| `comparison.dimensions[]` | `<table>` 행 | 왼쪽 컬럼 | label 표시 |
| `comparison.dimensions[].key` | 숨김 | - | 내부 매핑 전용 |
| `comparison.dimensions[].label` | `<th>` | 테이블 행 헤더 | 담보명 |
| `comparison.dimensions[].type` | 렌더링 로직 | 셀 내부 | boolean → O/X, amount → 금액, text → 텍스트 |
| `comparison.products[]` | `<table>` 열 | 상단 컬럼 | 회사명 + 상품명 |
| `comparison.products[].insurer` | `<th>` 상단 | 컬럼 헤더 | 굵게 |
| `comparison.products[].product_name` | `<th>` 하단 | 컬럼 헤더 | 일반 크기 |
| `comparison.products[].rows[key].value` | `<td>` 본문 | 셀 상단 | 값 표시 |
| `comparison.products[].rows[key].evidence` | `<td>` 하단 | 셀 하단 | 작은 글씨 + 📄 아이콘 |

### 4.4 Notes Block

| View Model Field | UI Component | 위치 | 표시 규칙 |
|---|---|---|---|
| `notes.summary` | `<p>` | Block 상단 | 항상 표시 |
| `notes.details[]` | `<ul><li>` | Block 하단 | 접기/펼치기, 기본 숨김 |

### 4.5 Limitations Block

| View Model Field | UI Component | 위치 | 표시 규칙 |
|---|---|---|---|
| `limitations[]` | `<ul><li>` | Block 전체 | 접기/펼치기, 기본 접힘 |

---

## 5. UI 컴포넌트 계층 구조

```
<App>
  ├─ <EntryScreen>
  │    ├─ <IntroSection>
  │    ├─ <QueryInput>
  │    ├─ <ExampleQuestions>
  │    └─ <Footer>
  │
  └─ <ResponseScreen>
       ├─ <UserMessageBubble>
       │
       └─ <SystemResponseBubble>
            ├─ <PremiumNotice> (조건부)
            ├─ <QuerySummaryBlock>
            ├─ <ComparisonBlock>
            │    └─ <ComparisonTable>
            │         ├─ <TableHeader>
            │         └─ <TableRow>
            │              └─ <TableCell>
            │                   ├─ value
            │                   └─ evidence
            ├─ <NotesBlock>
            │    ├─ summary
            │    └─ details (접기/펼치기)
            └─ <LimitationsBlock> (접기/펼치기)
```

---

## 6. 상태 관리 (State)

### 6.1 필요한 상태

| 상태 이름 | 타입 | 초기값 | 용도 |
|---|---|---|---|
| `currentQuery` | `string` | `""` | 입력창 내용 |
| `responseData` | `ResponseViewModel | null` | `null` | API 응답 저장 |
| `isLoading` | `boolean` | `false` | 로딩 상태 |
| `notesExpanded` | `boolean` | `false` | Notes details 펼침 상태 |
| `limitationsExpanded` | `boolean` | `false` | Limitations 펼침 상태 |

### 6.2 금지 사항

- ❌ `responseData` 가공/변환 금지
- ❌ Evidence 재해석 금지
- ❌ 담보 정렬/필터링 금지 (API 응답 순서 그대로)

---

## 7. 데이터 흐름 (Data Flow)

```
[1] 사용자 질문 입력
    ↓
[2] API 호출: POST /api/compare
    body: { "query": "삼성생명과 한화생명 건강보험 비교" }
    ↓
[3] API 응답: Response View Model (JSON)
    ↓
[4] setState(responseData)
    ↓
[5] UI 렌더링 (매핑 테이블 기준)
    ↓
[6] 화면 표시
```

**중요**: [3] → [4] 사이에 어떠한 가공도 없음

---

## 8. 신규 상품 추가 시 UI 영향

### 8.1 영향 없는 항목 (자동 반영)

- ✅ 신규 보험사 추가
- ✅ 신규 상품 추가
- ✅ 담보 개수 변경
- ✅ Evidence 출처 변경
- ✅ 보장 금액 변경

**이유**: UI는 `comparison.dimensions[]` 와 `comparison.products[]` 를 **그대로 순회**하기 때문

### 8.2 영향 있는 항목 (수동 갱신 필요)

- ⚠️ 예시 질문 버튼 (선택적)
- ⚠️ 시스템 소개 문구 (선택적)

**절차**:
1. 신규 상품 추가 완료
2. `<ExampleQuestions>` 컴포넌트에서 버튼 텍스트만 수정
3. 배포

---

## 9. 반응형 대응 (Responsive)

### 9.1 모바일 (< 768px)

**Comparison Table**:
- 가로 스크롤 활성화
- 첫 컬럼 (담보명) sticky

**Notes/Limitations**:
- 기본 접힌 상태 유지

### 9.2 태블릿/데스크톱 (≥ 768px)

**Comparison Table**:
- 전체 테이블 표시
- 스크롤 불필요

**Notes/Limitations**:
- 기본 접힌 상태 유지 (동일)

---

## 10. 접근성 (Accessibility)

### 10.1 필수 요구사항

- `<table>` 에 `<caption>` 추가: "보장 비교표"
- Evidence 아이콘에 `aria-label`: "문서 출처"
- 접기/펼치기 버튼에 `aria-expanded` 속성
- 보험료 경고 박스에 `role="alert"`

### 10.2 키보드 네비게이션

- Tab 키로 모든 interactive 요소 접근 가능
- Enter/Space로 접기/펼치기 토글

---

## 11. 에러 처리

### 11.1 API 오류

**조건**: API 호출 실패 또는 500 에러

**UI 표시**:
```
┌─────────────────────────────────────────────┐
│ ⚠️ 일시적인 오류가 발생했습니다.             │
│ 잠시 후 다시 시도해주세요.                   │
└─────────────────────────────────────────────┘
```

### 11.2 비정상 응답

**조건**: Response View Model 구조 불일치

**UI 표시**:
```
┌─────────────────────────────────────────────┐
│ ⚠️ 응답 형식 오류                            │
│ 관리자에게 문의하세요.                       │
└─────────────────────────────────────────────┘
```

### 11.3 빈 응답

**조건**: `comparison.products.length === 0`

**UI 표시**:
```
┌─────────────────────────────────────────────┐
│ 📭 비교 가능한 상품이 없습니다.              │
│ 다른 질문을 시도해보세요.                   │
└─────────────────────────────────────────────┘
```

---

## 12. 예제별 UI 렌더링 시나리오

### 12.1 예제 1번 (보장 여부 확인)

**질문**: "삼성생명 건강보험은 암 진단 시 보장되나요?"

**UI 특징**:
- `comparison.products[]` 길이 = 1 (단일 회사)
- `comparison.dimensions[]` 길이 = 2 (보장 여부, 보장 금액)
- 테이블 컬럼 수 = 2 (담보명, 삼성생명)

**렌더링**:
```
📋 비교 대상 상품
• 삼성생명 건강보험

📊 보장 비교표
┌──────────┬───────────┐
│ 담보     │ 삼성생명  │
├──────────┼───────────┤
│ 암 보장  │ ✓         │
│          │ 📄 약관p.12│
├──────────┼───────────┤
│ 보장금액 │ 3,000만원 │
│          │ 📄 가입p.3│
└──────────┴───────────┘
```

### 12.2 예제 2번 (담보 비교)

**질문**: "삼성생명과 한화생명의 암 진단비를 비교해줘"

**UI 특징**:
- `comparison.products[]` 길이 = 2
- `comparison.dimensions[]` 길이 = 5 (보장여부, 금액, 대기기간, 감액기간, 제외암)
- 테이블 컬럼 수 = 3 (담보명, 삼성생명, 한화생명)

**렌더링**: STEP NEXT-2 예제 2번 참조

### 12.3 예제 3번 (종합 비교) ⭐ **핵심**

**질문**: "삼성생명과 한화생명 건강보험을 비교해줘"

**UI 특징**:
- `comparison.products[]` 길이 = 2
- `comparison.dimensions[]` 길이 = 9 (암, 유사암, 뇌출혈, 심장, 입원, 수술, 사망 질병, 사망 상해, 장해)
- 테이블 컬럼 수 = 3
- `notes.details[]` 길이 = 7 (가장 상세)

**렌더링**: STEP NEXT-2 예제 3번 참조

### 12.4 예제 4번 (보험료 비교)

**질문**: "삼성생명과 한화생명 건강보험 보험료를 비교해줘"

**UI 특징**:
- `meta.premium_notice = true` → `<PremiumNotice>` 표시
- `comparison.dimensions[]` 길이 = 2 (월보험료, 산출조건)
- 경고 박스 필수

**렌더링**: STEP NEXT-2 예제 4번 참조

---

## 13. 구현 체크리스트

### 13.1 Entry Screen
- [ ] `<IntroSection>` 구현 (할 수 있는 것/없는 것)
- [ ] `<QueryInput>` 구현 (maxLength 500)
- [ ] `<ExampleQuestions>` 구현 (3개 버튼)
- [ ] `<Footer>` 구현

### 13.2 Response Screen
- [ ] `<PremiumNotice>` 조건부 렌더링
- [ ] `<QuerySummaryBlock>` 구현
- [ ] `<ComparisonBlock>` 구현
  - [ ] 테이블 헤더 (회사명 + 상품명)
  - [ ] 테이블 행 (dimensions loop)
  - [ ] 테이블 셀 (value + evidence)
  - [ ] type별 렌더링 (boolean/amount/text)
- [ ] `<NotesBlock>` 구현 (접기/펼치기)
- [ ] `<LimitationsBlock>` 구현 (접기/펼치기)

### 13.3 반응형
- [ ] 모바일 테이블 가로 스크롤
- [ ] 첫 컬럼 sticky

### 13.4 접근성
- [ ] `<table>` caption
- [ ] aria-label
- [ ] aria-expanded
- [ ] 키보드 네비게이션

### 13.5 에러 처리
- [ ] API 오류 UI
- [ ] 비정상 응답 UI
- [ ] 빈 응답 UI

---

## 14. 금지 사항 재확인

### UI 구현 시 절대 금지
- ❌ Response View Model 가공/변환
- ❌ Evidence 재해석
- ❌ 담보 정렬/필터링 (API 순서 그대로)
- ❌ 추천/판단 로직 추가
- ❌ 보험료 계산 로직 추가
- ❌ "확인 불가"를 숨기거나 다른 값으로 대체

### 이 문서에서 다루지 않는 것
- ❌ 디자인 시안 (색상, 폰트, 아이콘)
- ❌ CSS 프레임워크 선택
- ❌ 컴포넌트 라이브러리 추천
- ❌ API 엔드포인트 구현

---

## 15. Definition of Done (DoD)

- [x] STEP NEXT-2 View Model과 100% 정합
- [x] 예제 3번 (상품 종합 비교)이 UI 중심
- [x] View Model → UI 매핑 테이블 완성
- [x] 컴포넌트 계층 구조 명시
- [x] 신규 상품 추가 시 UI 영향 없음 확인
- [x] 4개 예제 모두 렌더링 시나리오 포함
- [x] 접근성 요구사항 명시
- [x] 에러 처리 UI 정의
- [x] 금지 사항 명시

---

**본 문서는 프론트엔드 구현의 단일 기준이며, 디자인 제외 모든 구조를 확정한다.**
