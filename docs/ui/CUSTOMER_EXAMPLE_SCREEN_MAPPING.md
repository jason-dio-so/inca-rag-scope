# 고객 예시 화면 기준 UI 매핑 (STEP NEXT-14-β)

**Version**: 1.0.0
**Status**: 🔒 LOCKED (Production UI Contract)
**Lock Date**: 2025-12-29
**Purpose**: 고객 예시2/3/4 화면을 UI에서 100% 재현하기 위한 ViewModel 매핑 규격

---

## 원칙 (Frontend Contract)

1. **NO PARSING**: Frontend는 VM JSON을 파싱하지 않고, `kind`별 타입 렌더링만 수행
2. **Deterministic Routing**: Production에서는 `ChatRequest.kind`를 FAQ 버튼 기반으로 항상 명시
3. **1:1 Component Mapping**: 각 Section kind는 Figma Component와 1:1 매핑
4. **Text As-Is**: `value_text`, `explanation` 등 모든 텍스트는 가공 없이 렌더

---

## 예시 2: 담보 상세 비교 (EX2_DETAIL)

### (A) 화면 블럭 순서

```
┌─ AssistantMessageCard ──────────────────────────────────────┐
│ 1. SummaryCard (요약 카드)                                    │
│ 2. ComparisonTable (상세 비교 표)                             │
│ 3. InsurerExplanationBlocks (보험사별 설명)                   │
│ 4. CommonNotes (공통사항 및 유의사항)                          │
│ 5. EvidenceAccordion (근거자료, 접힘)                         │
└──────────────────────────────────────────────────────────────┘
```

### (B) ViewModel 필드 매핑 표

| 화면 블럭 | Figma Component | ViewModel Path | 설명 |
|----------|-----------------|----------------|------|
| 1. 요약 카드 | `SummaryCard` | `AssistantMessageVM.summary_bullets` | 3~5개 bullet 텍스트 배열 |
| 2. 상세 비교 표 | `ComparisonTable` | `sections[0]` (kind=`comparison_table`, table_kind=`COVERAGE_DETAIL`) | 담보 상세 비교 표 (columns, rows) |
| 3. 보험사별 설명 | `InsurerExplanationBlocks` | `sections[1]` (kind=`insurer_explanations`) | 각 보험사별 독립 설명 블럭 (parallel, no cross-ref) |
| 4. 공통사항 및 유의사항 | `CommonNotes` | `sections[2]` (kind=`common_notes`) | title + bullets (공통사항/유의사항 통합) |
| 5. 근거자료 | `EvidenceAccordion` | `sections[3]` (kind=`evidence_accordion`) | 접힘 상태 기본, evidence items 배열 |

### (C) 예시2 Response 재현 체크리스트

- [x] Title: "암진단비 상세 비교 (삼성화재 vs 메리츠화재)"
- [x] Summary bullets: 3개 이상 (각 보험사 확인 사실)
- [x] Table columns: ["구분", "삼성화재", "메리츠화재"]
- [x] Table rows: 각 row는 비교 항목 (e.g., "진단 기준", "보장금액")
- [x] Explanation blocks: 2개 (삼성/메리츠), 교차 참조 없음
- [x] Common notes: 최소 2개 bullet (공통사항 + 유의사항)
- [x] Evidence: 접힘 상태, items 존재

---

## 예시 3: 통합 비교 (EX3_INTEGRATED)

### (A) 화면 블럭 순서

```
┌─ AssistantMessageCard ──────────────────────────────────────┐
│ 1. SummaryCard (요약 카드)                                    │
│ 2. ComparisonTable (통합 비교 표)                             │
│ 3. InsurerExplanationBlocks (보험사별 설명)                   │
│ 4. CommonNotes (공통사항 + 유의사항, 시각 분리 가능)            │
│ 5. EvidenceAccordion (근거자료, 접힘)                         │
└──────────────────────────────────────────────────────────────┘
```

### (B) ViewModel 필드 매핑 표

| 화면 블럭 | Figma Component | ViewModel Path | 설명 |
|----------|-----------------|----------------|------|
| 1. 요약 카드 | `SummaryCard` | `AssistantMessageVM.summary_bullets` | 담보별 비교 요약 (3~5개) |
| 2. 통합 비교 표 | `ComparisonTable` | `sections[0]` (kind=`comparison_table`, table_kind=`INTEGRATED_COMPARE`) | 여러 담보 통합 비교 표 |
| 3. 보험사별 설명 | `InsurerExplanationBlocks` | `sections[1]` (kind=`insurer_explanations`) | 각 보험사별 독립 설명 블럭 |
| 4. 공통사항 및 유의사항 | `CommonNotes` (groups 지원) | `sections[2]` (kind=`common_notes`) | **GROUPS**: [{title: "공통사항", bullets}, {title: "유의사항", bullets}] |
| 5. 근거자료 | `EvidenceAccordion` | `sections[3]` (kind=`evidence_accordion`) | 접힘 상태 기본 |

### (C) 예시3 Response 재현 체크리스트 (확대 이미지 기준)

**화면 구성요소 (위 → 아래 순서)**:

- [x] **요약 카드**: "암진단비와 뇌출혈진단비를 비교했습니다", "각 보험사별로..." (3~5개 bullets)
- [x] **통합 비교 표**:
  - Columns: ["담보명", "삼성화재", "메리츠화재"]
  - Rows: ["암진단비", "뇌출혈진단비"]
  - 각 cell에 금액 또는 상태 표시
- [x] **보험사별 설명**:
  - 삼성화재 블럭 (독립)
  - 메리츠화재 블럭 (독립)
  - 교차 참조 없음 ("삼성은...", "메리츠는..." 형태)
- [x] **공통사항**: "모든 보험사에서 가입설계서에 금액을 명시하고 있습니다" (2~3개 bullets)
- [x] **유의사항**: "가입설계서 기준이며 실제 약관과 다를 수 있습니다" (2~3개 bullets)
- [x] **근거자료**: 접힌 상태 (클릭 시 펼침), 각 담보별 evidence items 존재

**IMPORTANT**: 공통사항과 유의사항은 `groups` 배열로 분리 렌더 가능 (아래 Section 4 참조)

---

## 예시 4: 가입가능 여부 확인 (EX4_ELIGIBILITY)

### (A) 화면 블럭 순서

```
┌─ AssistantMessageCard ──────────────────────────────────────┐
│ 1. SummaryCard (요약 카드)                                    │
│ 2. ComparisonTable (가입가능 여부 표)                          │
│ 3. CommonNotes (유의사항)                                     │
│ 4. EvidenceAccordion (근거자료, 접힘)                         │
└──────────────────────────────────────────────────────────────┘
```

### (B) ViewModel 필드 매핑 표

| 화면 블럭 | Figma Component | ViewModel Path | 설명 |
|----------|-----------------|----------------|------|
| 1. 요약 카드 | `SummaryCard` | `AssistantMessageVM.summary_bullets` | 질병별 가입가능 여부 요약 |
| 2. 가입가능 여부 표 | `ComparisonTable` | `sections[0]` (kind=`comparison_table`, table_kind=`ELIGIBILITY_MATRIX`) | 질병 x 보험사 매트릭스 |
| 3. 유의사항 | `CommonNotes` | `sections[1]` (kind=`common_notes`) | 가입가능 여부 관련 유의사항 |
| 4. 근거자료 | `EvidenceAccordion` | `sections[2]` (kind=`evidence_accordion`) | 접힘 상태 기본 |

### (C) 예시4 Response 재현 체크리스트

- [x] Title: "암 진단 시 보장 가능 여부 확인"
- [x] Summary bullets: 질병별 가입가능 여부 요약
- [x] Table: Eligibility matrix (O/X/△ 형태)
- [x] Common notes: 가입가능 여부 해석 방법, 유의사항
- [x] Evidence: 약관 근거 (접힘)

---

## Section 4: 공통사항/유의사항 시각 분리 계약 확장 (예시3 전용)

### 문제 정의

예시3 화면(확대 이미지)에서 "공통사항"과 "유의사항"이 시각적으로 분리되어 표시됨:

```
공통사항:
• 모든 보험사에서 가입설계서에 금액을 명시하고 있습니다
• ...

유의사항:
• 가입설계서 기준이며 실제 약관과 다를 수 있습니다
• ...
```

### 해결 방안: `CommonNotesSection.groups` 추가

**ViewModel 레벨 확장** (Step12 침범 없음):

```python
class CommonNotesSection(BaseModel):
    kind: Literal["common_notes"] = "common_notes"
    title: str = "공통사항 및 유의사항"
    bullets: List[str] = []  # LEGACY (호환성 유지)
    groups: Optional[List[BulletGroup]] = None  # NEW (시각 분리용)

class BulletGroup(BaseModel):
    title: str  # e.g., "공통사항", "유의사항"
    bullets: List[str]
```

### Frontend 렌더링 우선순위

```typescript
// Pseudo-code
if (section.groups && section.groups.length > 0) {
  // Render grouped (예시3)
  section.groups.forEach(group => {
    <h4>{group.title}</h4>
    <ul>{group.bullets.map(b => <li>{b}</li>)}</ul>
  })
} else {
  // Render flat (예시2/4)
  <h3>{section.title}</h3>
  <ul>{section.bullets.map(b => <li>{b}</li>)}</ul>
}
```

### 예시별 적용

| 예시 | `groups` 사용 여부 | 렌더링 형태 |
|-----|-------------------|-----------|
| 예시2 | `null` | Flat bullets (title + bullets) |
| 예시3 | `[{title:"공통사항", ...}, {title:"유의사항", ...}]` | Grouped (각 group별 title + bullets) |
| 예시4 | `null` | Flat bullets |

---

## Section 5: Section Types 전체 스펙 (5 Core Types)

### 1. `comparison_table`

```typescript
interface ComparisonTableSection {
  kind: "comparison_table"
  table_kind: "COVERAGE_DETAIL" | "INTEGRATED_COMPARE" | "ELIGIBILITY_MATRIX"
  columns: string[]  // e.g., ["구분", "삼성화재", "메리츠화재"]
  rows: Array<{
    label: string
    values: string[]  // 각 column에 대응되는 값
  }>
}
```

### 2. `insurer_explanations`

```typescript
interface InsurerExplanationsSection {
  kind: "insurer_explanations"
  explanations: Array<{
    insurer: string
    text: string  // Render as-is (NO parsing, NO cross-reference)
  }>
}
```

### 3. `common_notes`

```typescript
interface CommonNotesSection {
  kind: "common_notes"
  title: string  // e.g., "공통사항 및 유의사항"
  bullets: string[]  // LEGACY (flat bullets)
  groups?: Array<{  // NEW (grouped bullets for visual separation)
    title: string
    bullets: string[]
  }>
}
```

**Rendering Priority**: `groups` (if exists) > `bullets` (fallback)

### 4. `evidence_accordion`

```typescript
interface EvidenceAccordionSection {
  kind: "evidence_accordion"
  items: Array<{
    evidence_ref_id: string
    insurer: string
    coverage_name: string
    doc_type: string  // "약관", "사업방법서", "상품요약서"
    page: number | null
    snippet: string | null
  }>
  defaultCollapsed: true  // Always collapsed by default
}
```

### 5. `summary` (Top-level, not a section)

```typescript
interface AssistantMessageVM {
  kind: MessageKind
  title: string
  summary_bullets: string[]  // Rendered as SummaryCard (always first)
  sections: Section[]  // Array of 4 section types above
  lineage: LineageMetadata
}
```

**NOTE**: `summary_bullets`는 `sections` 배열에 포함되지 않음 (top-level field)

---

## Section 6: Production Request Flow (100% Deterministic)

### FAQ Button → Explicit `kind` (RECOMMENDED)

```typescript
// User clicks FAQ button: "암진단비 상세 비교"
const request: ChatRequest = {
  message: "암진단비 상세 비교",
  kind: "EX2_DETAIL",  // <-- Explicit (100% deterministic)
  coverage_names: ["암진단비"],
  insurers: ["삼성화재", "메리츠화재"]
}
```

### Keyword-based (FALLBACK, not recommended)

```typescript
// User types free text (no FAQ button)
const request: ChatRequest = {
  message: "암진단비 비교해주세요",
  kind: null,  // <-- Will use keyword router (accuracy not guaranteed)
  coverage_names: null,
  insurers: null
}
// → Server will use IntentRouter.detect_intent() (pattern matching)
```

---

## Section 7: Verification Checklist

### 예시2 (EX2_DETAIL)

- [x] 5개 블럭 순서 고정 (요약/표/설명/공통/근거)
- [x] Table kind = `COVERAGE_DETAIL`
- [x] Explanation blocks: 교차 참조 없음
- [x] Common notes: Flat bullets (no groups)

### 예시3 (EX3_INTEGRATED)

- [x] 5개 블럭 순서 고정
- [x] Table kind = `INTEGRATED_COMPARE`
- [x] Common notes: **GROUPS** 사용 (공통사항/유의사항 분리)
- [x] Evidence: 여러 담보 통합

### 예시4 (EX4_ELIGIBILITY)

- [x] 4개 블럭 순서 고정 (요약/표/유의/근거)
- [x] Table kind = `ELIGIBILITY_MATRIX`
- [x] No insurer explanations section

---

## Section 8: 금지 사항

- ❌ Frontend에서 텍스트 파싱 기반 표 생성
- ❌ `value_text`, `explanation` 텍스트 가공/해석
- ❌ Section 순서 변경
- ❌ Section kind 추가 생성
- ❌ `kind=null` 요청을 Production UX 기본 경로로 사용

---

## Appendix: Example Response JSON (예시3)

```json
{
  "kind": "EX3_INTEGRATED",
  "title": "암진단비, 뇌출혈진단비 통합 비교",
  "summary_bullets": [
    "암진단비와 뇌출혈진단비를 비교했습니다",
    "각 보험사별로 가입설계서 기준 금액을 확인했습니다",
    "담보별 보장 내용은 아래 표에서 확인하실 수 있습니다"
  ],
  "sections": [
    {
      "kind": "comparison_table",
      "table_kind": "INTEGRATED_COMPARE",
      "columns": ["담보명", "삼성화재", "메리츠화재"],
      "rows": [
        {"label": "암진단비", "values": ["3천만원", "2천만원"]},
        {"label": "뇌출혈진단비", "values": "5백만원", "1천만원"]}
      ]
    },
    {
      "kind": "insurer_explanations",
      "explanations": [
        {"insurer": "삼성화재", "text": "삼성화재의 암진단비는..."},
        {"insurer": "메리츠화재", "text": "메리츠화재의 암진단비는..."}
      ]
    },
    {
      "kind": "common_notes",
      "title": "공통사항 및 유의사항",
      "bullets": [],
      "groups": [
        {
          "title": "공통사항",
          "bullets": ["모든 보험사에서 가입설계서에 금액을 명시하고 있습니다"]
        },
        {
          "title": "유의사항",
          "bullets": ["가입설계서 기준이며 실제 약관과 다를 수 있습니다"]
        }
      ]
    },
    {
      "kind": "evidence_accordion",
      "items": [...]
    }
  ],
  "lineage": {...}
}
```

---

**END OF DOCUMENT**
