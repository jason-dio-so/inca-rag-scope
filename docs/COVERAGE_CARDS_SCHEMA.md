# Coverage Cards 구성요소 및 생성 과정

## 개요

### Legacy Architecture (Before STEP NEXT-72)

`data/compare/{INSURER}_coverage_cards.jsonl`은 **보험사별 담보 종합 정보 SSOT (Single Source of Truth)**입니다.

모든 비교/조회 API가 이 파일을 사용하며, 담보별로 다음 정보를 통합합니다:
- 원본 담보명 (가입설계서)
- 신정원 통일코드 매핑 결과
- 약관/사업방법서/상품요약서 근거 자료
- 가입설계서 금액/보험료/기간 정보
- 문서 타입별 hit 수, flags

### **STEP NEXT-72: Slim Architecture (Current)** ✨

`data/compare/{INSURER}_coverage_cards_slim.jsonl`은 **UI/비교용 경량 카드**입니다.

근거 원문은 분리 저장소에 저장하고, **refs만** 보유:
- `data/detail/{INSURER}_proposal_detail_store.jsonl`: 가입설계서 DETAIL (보장내용 원문)
- `data/detail/{INSURER}_evidence_store.jsonl`: 사업방법서/상품요약서/약관 근거 원문

**장점**:
- ✅ 파일 크기 48% 감소 (121KB → 63KB, Samsung 기준)
- ✅ 토큰 사용량 감소, grep/read 안정성 향상
- ✅ Ref 기반 정규화 구조로 PG 이관 준비 완료
- ✅ UI는 가볍게, 상세 정보는 ref fetch로 lazy loading

---

## Coverage Card 구조

### 필드 목록

| 필드 | 타입 | 설명 | 생성 단계 |
|------|------|------|-----------|
| `insurer` | string | 보험사명 (예: `samsung`) | Step5 (고정값) |
| `coverage_name_raw` | string | 원본 담보명 (가입설계서) | Step1 |
| `coverage_code` | string? | 신정원 통일코드 (예: `A4101`) | Step2-b |
| `coverage_name_canonical` | string? | 표준 담보명 (예: `뇌혈관질환진단비`) | Step2-b |
| `mapping_status` | string | 매핑 상태: `matched` \| `unmatched` | Step2-b |
| `evidence_status` | string | 근거 발견 여부: `found` \| `not_found` | Step4 |
| `evidences` | Evidence[] | 근거 자료 목록 (최대 3개) | Step4 + Step5 (diversity selection) |
| `hits_by_doc_type` | object | 문서 타입별 hit 수 | Step4 |
| `flags` | string[] | 특수 플래그 (예: `policy_only`) | Step4 |
| `proposal_facts` | object? | 가입설계서 금액/보험료/기간 | Step1 |

---

## 필드별 상세 설명

### 1. `insurer` (보험사명)
- **생성**: Step5 (고정값)
- **예시**: `"samsung"`, `"hanwha"`, `"kb"`

### 2. `coverage_name_raw` (원본 담보명)
- **생성**: Step1 (`pipeline/step1_summary_first/extractor_v3.py`)
- **출처**: 가입설계서 PDF → 표 추출 → 담보명 컬럼
- **저장 위치**: `data/scope_v3/{INSURER}_step1_raw_scope_v3.jsonl`
- **예시**: `"뇌혈관질환 진단비(1년50%)"`

### 3. `coverage_code` (신정원 통일코드)
- **생성**: Step2-b (`pipeline/step2_canonical_mapping/run.py`)
- **출처**: `data/sources/mapping/담보명mapping자료.xlsx` (신정원 통일코드 매핑표)
- **매핑 방법**:
  - Exact match: 담보명 정확 일치 (공백/괄호 정규화 후)
  - Fuzzy match: 유사도 기반 매칭 (현재 미사용, 수동 검토 필요)
  - Unmapped: 매핑표에 없는 담보 → `None`
- **저장 위치**: `data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl`
- **예시**: `"A4101"`

### 4. `coverage_name_canonical` (표준 담보명)
- **생성**: Step2-b
- **출처**: `data/sources/mapping/담보명mapping자료.xlsx` (신정원 통일코드 매핑표)
- **규칙**: 통일코드에 매핑된 표준 담보명
- **저장 위치**: `data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl`
- **예시**: `"뇌혈관질환진단비"`

### 5. `mapping_status` (매핑 상태)
- **생성**: Step2-b
- **값**:
  - `"matched"`: 통일코드 매핑 성공 (exact 또는 fuzzy)
  - `"unmatched"`: 매핑 실패
- **저장 위치**: `data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl`

### 6. `evidence_status` (근거 발견 여부)
- **생성**: Step4 (`pipeline/step4_evidence_search/search_evidence.py`)
- **값**:
  - `"found"`: 약관/사업방법서/상품요약서 중 1개 이상에서 근거 발견
  - `"not_found"`: 근거 미발견
- **저장 위치**: `data/evidence_pack/{INSURER}_evidence_pack.jsonl` → Step5에서 통합

### 7. `evidences` (근거 자료 목록)
- **생성**: Step4 (검색) + Step5 (diversity selection)
- **구조**: `Evidence[]` (최대 3개)
  - `doc_type`: 문서 타입 (`"약관"`, `"사업방법서"`, `"상품요약서"`)
  - `file_path`: 원본 JSONL 파일 경로
  - `page`: 페이지 번호 (1-based)
  - `snippet`: 근거 텍스트 (최대 500자)
  - `match_keyword`: 매칭된 키워드 (검색어)

#### Evidence 생성 과정

**Step 4 (Evidence Search)**:
1. Step2-b canonical scope JSONL 읽기
2. 담보별로 약관/사업방법서/상품요약서 독립 검색:
   - 키워드: canonical name (있으면) + raw name
   - 보험사별 query variants 생성 (suffix 제거, 용어 브릿지)
   - Snippet 추출: 키워드 포함 라인 ± 2줄
3. Fallback 검색 (한화 전용):
   - Token-AND Search: 핵심 토큰 2개 이상 동일 라인 내
4. 문서 타입별 hit 수 기록 (`hits_by_doc_type`)

**Step 5 (Diversity Selection)**:
1. Evidence 중복 제거:
   - 기준: (doc_type, file_path, page, snippet)
2. Fallback 판정:
   - `match_keyword`에 `fallback_` 포함 OR `token_and(` 시작
3. 우선순위 정렬:
   1. Non-fallback 우선
   2. 약관 > 사업방법서 > 상품요약서
   3. 페이지 오름차순
4. Diversity pass: 각 doc_type에서 1개씩 선택
5. Fill-up pass: 최대 3개까지 부족분 채우기

**예시**:
```json
{
  "doc_type": "약관",
  "file_path": "/Users/.../약관.page.jsonl",
  "page": 6,
  "snippet": "6-1-13. 뇌혈관질환 진단비(1년50%) 특별약관\n267\n...",
  "match_keyword": "뇌혈관질환진단비"
}
```

### 8. `hits_by_doc_type` (문서 타입별 hit 수)
- **생성**: Step4
- **구조**: `{"약관": 3, "사업방법서": 3, "상품요약서": 0}`
- **의미**: 각 문서 타입에서 발견된 evidence 수 (diversity selection 전 raw 수)
- **예시**:
```json
{
  "약관": 3,
  "사업방법서": 3,
  "상품요약서": 3
}
```

### 9. `flags` (특수 플래그)
- **생성**: Step4
- **종류**:
  - `"policy_only"`: 약관에만 존재 (사업방법서/상품요약서 0건)
  - `"fallback_token_and"`: Token-AND Search로 발견 (한화 전용)
  - `"kb_bm_definition_hit"`: KB 사업방법서 정의 Hit 보정 (A4200_1 전용)
- **예시**: `["policy_only"]`, `[]`

### 10. `proposal_facts` (가입설계서 금액/보험료/기간)
- **생성**: Step1 (`pipeline/step1_summary_first/extractor_v3.py`)
- **출처**: 가입설계서 PDF → 표 추출 → 금액/보험료/기간 컬럼
- **저장 위치**:
  - Step1: `data/scope_v3/{INSURER}_step1_raw_scope_v3.jsonl` (필드: `proposal_facts`)
  - Step2-b: 그대로 복사
  - Step5: 메모리 전용 (CSV 변환 시 제외 → 최종 cards에 복원)
- **구조**:
```json
{
  "coverage_amount_text": "1,000만원",
  "premium_text": "9,300",
  "period_text": "20년납 100세만기\nZD4",
  "payment_method_text": null,
  "evidences": [
    {
      "doc_type": "가입설계서",
      "page": 2,
      "row_index": 13,
      "raw_row": ["", "뇌혈관질환 진단비(1년50%)", "1,000만원", "9,300", "20년납 100세만기\nZD4"]
    }
  ]
}
```

---

## Coverage Cards 생성 파이프라인

```
Step 1: 가입설계서 PDF → Raw Scope
  출력: data/scope_v3/{INSURER}_step1_raw_scope_v3.jsonl
  생성 필드:
    - coverage_name_raw
    - proposal_facts (coverage_amount_text, premium_text, period_text, evidences)

Step 2-a: Raw Scope → Sanitized Scope (노이즈 제거)
  출력: data/scope_v3/{INSURER}_step2_sanitized_scope_v1.jsonl
  생성 필드: (coverage_name_raw만 정제)

Step 2-b: Sanitized Scope → Canonical Scope (신정원 통일코드 매핑)
  입력: data/sources/mapping/담보명mapping자료.xlsx
  출력: data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl
  생성 필드:
    - coverage_code
    - canonical_name (coverage_name_canonical)
    - mapping_method → mapping_status

Step 3: 근거 문서 PDF → 페이지별 텍스트
  출력: data/evidence_text/{INSURER}/{doc_type}/*.page.jsonl

Step 4: Canonical Scope + 텍스트 → Evidence Pack
  출력: data/evidence_pack/{INSURER}_evidence_pack.jsonl
  생성 필드:
    - evidences (raw, diversity selection 전)
    - hits_by_doc_type
    - flags
    - evidence_status

Step 5: Canonical Scope + Evidence Pack → Coverage Cards (SSOT)
  출력: data/compare/{INSURER}_coverage_cards.jsonl
  생성 필드:
    - insurer (고정값)
    - evidences (diversity selection 후 최대 3개)
    - proposal_facts (Step1에서 가져옴)
```

---

## Coverage Cards SSOT 사용처

Coverage Cards는 **SSOT (Single Source of Truth)**로 다음 컴포넌트에서 사용됩니다:

1. **API Layer** (`apps/api/`):
   - `chat_intent.py`: 단일 담보 조회 (`/api/chat/intent`)
   - `chat_vm.py`: 다중 담보 비교 (`/api/chat/vm`)
   - `chat_handlers_deterministic.py`: 결정론적 핸들러
   - `chat_server.py`: 비교 UI 서버

2. **UI** (`apps/web/`):
   - Next.js 비교 UI (테이블 렌더링)
   - 담보별 상세 정보 표시
   - 근거 자료 원문 표시

3. **Audit Tools** (`tools/audit/`):
   - KPI 집계 (`AMOUNT_STATUS_DASHBOARD.md` 생성)
   - 품질 검증 (mapping rate, evidence fill rate)

---

## 예시: 전체 Coverage Card

```json
{
  "insurer": "samsung",
  "coverage_name_raw": "뇌혈관질환 진단비(1년50%)",
  "coverage_code": "A4101",
  "coverage_name_canonical": "뇌혈관질환진단비",
  "mapping_status": "matched",
  "evidence_status": "found",
  "evidences": [
    {
      "doc_type": "약관",
      "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/samsung/약관/삼성_약관.page.jsonl",
      "page": 6,
      "snippet": "6-1-13. 뇌혈관질환 진단비(1년50%) 특별약관\n267\n...",
      "match_keyword": "뇌혈관질환진단비"
    },
    {
      "doc_type": "사업방법서",
      "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/samsung/사업방법서/삼성_사업설명서.page.jsonl",
      "page": 8,
      "snippet": "·뇌혈관질환 진단비(1년50%) \n·허혈성심장질환 진단비(1년50%)  \n...",
      "match_keyword": "뇌혈관질환진단비"
    },
    {
      "doc_type": "상품요약서",
      "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/samsung/상품요약서/삼성_상품요약서.page.jsonl",
      "page": 17,
      "snippet": "뇌혈관질환 진단비(1년50%), \n[갱신형] 뇌혈관질환 진단비(1년50%), \n...",
      "match_keyword": "뇌혈관질환진단비"
    }
  ],
  "hits_by_doc_type": {
    "약관": 3,
    "사업방법서": 3,
    "상품요약서": 3
  },
  "flags": [],
  "proposal_facts": {
    "coverage_amount_text": "1,000만원",
    "premium_text": "9,300",
    "period_text": "20년납 100세만기\nZD4",
    "payment_method_text": null,
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 2,
        "row_index": 13,
        "raw_row": [
          "",
          "뇌혈관질환 진단비(1년50%)",
          "1,000만원",
          "9,300",
          "20년납 100세만기\nZD4"
        ]
      }
    ]
  }
}
```

---

## STEP NEXT-72: Slim Architecture 상세

### Slim Schema 예시

#### 1. CoverageCardSlim (경량 카드)

```json
{
  "insurer": "samsung",
  "coverage_code": "A4101",
  "coverage_name_canonical": "뇌혈관질환진단비",
  "coverage_name_raw": "뇌혈관질환 진단비(1년50%)",
  "mapping_status": "matched",
  "proposal_facts": {
    "coverage_amount_text": "1,000만원",
    "premium_text": "9,300",
    "period_text": "20년납 100세만기\nZD4"
  },
  "customer_view": {
    "benefit_description": "보험기간 중 약관에 정한 뇌혈관질환(뇌졸중포함)으로 진단 확정된 경우...",
    "payment_type": null,
    "limit_conditions": [],
    "exclusion_notes": ["면책 조건", "90일 대기기간"]
  },
  "refs": {
    "proposal_detail_ref": "PD:samsung:A4101",
    "evidence_refs": [
      "EV:samsung:A4101:01",
      "EV:samsung:A4101:02",
      "EV:samsung:A4101:03"
    ]
  }
}
```

**삭제된 필드**: `evidences` (원문), `hits_by_doc_type`, `flags`, `proposal_detail_facts`

---

#### 2. ProposalDetailRecord (가입설계서 DETAIL 저장소)

```json
{
  "proposal_detail_ref": "PD:samsung:A4101",
  "insurer": "samsung",
  "coverage_code": "A4101",
  "doc_type": "가입설계서",
  "page": 6,
  "benefit_description_text": "보험기간 중 약관에 정한 뇌혈관질환(뇌졸중포함)으로 진단 확정된 경우 가 입금액 지급(최초 1회한) ※ 최초 보험가입후 1년 미만에 보험금 지급사유가 발생한 경우 50% 감액 지급",
  "hash": "a4aa6293e0a7e0e22c32df272caaed5400d12e5662da3dfed280c521f11450ba"
}
```

---

#### 3. EvidenceRecord (근거 자료 저장소)

```json
{
  "evidence_ref": "EV:samsung:A4101:01",
  "insurer": "samsung",
  "coverage_code": "A4101",
  "doc_type": "가입설계서",
  "page": 2,
  "snippet": "20년납 100세만기\nZD2779010\n뇌혈관질환 진단비(1년50%)\n1,000만원\n9,300",
  "match_keyword": "뇌혈관질환진단비",
  "hash": "2d500f91577c908d006c265843836c90fde92abfeadded46679f57726a6ff93c"
}
```

---

### Ref ID 규칙

- **Proposal Detail Ref**: `PD:{insurer}:{coverage_code}`
- **Evidence Ref**: `EV:{insurer}:{coverage_code}:{nn}` (nn=01, 02, 03...)
- **Hash**: SHA256 (무결성 검증 + dedup)

---

### Size Reduction KPI (Samsung)

| 항목 | Legacy | Slim | 감소율 |
|------|--------|------|--------|
| 파일 크기 | 121 KB | 63 KB | **48%** |
| 평균 row | 3.9 KB | 2.0 KB | **49%** |
| Ref 역추적 | N/A | 100% | ✅ |

---

## 파일 위치

### Legacy (Before STEP NEXT-72)
- **데이터 타입 정의**: `core/compare_types.py` (CoverageCard, Evidence 클래스)
- **Coverage Cards JSONL**: `data/compare/{INSURER}_coverage_cards.jsonl`
- **생성 스크립트**: `pipeline/step5_build_cards/build_cards.py`

### Slim (STEP NEXT-72)
- **데이터 타입 정의**: `core/compare_types.py` (CoverageCardSlim, ProposalDetailRecord, EvidenceRecord 클래스)
- **Coverage Cards Slim JSONL**: `data/compare/{INSURER}_coverage_cards_slim.jsonl`
- **Proposal Detail Store**: `data/detail/{INSURER}_proposal_detail_store.jsonl`
- **Evidence Store**: `data/detail/{INSURER}_evidence_store.jsonl`
- **생성 스크립트**: `pipeline/step5_build_cards/build_cards_slim.py`

---

## 참고 문서
- `PIPELINE_STEP3_TO_STEP5.md`: Step3-5 파이프라인 상세 설명
- `CLAUDE.md`: 프로젝트 전체 아키텍처
- `core/compare_types.py`: 데이터 타입 정의 (CoverageCard, Evidence)
