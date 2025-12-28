# STEP NEXT-8: 고객 예제 → API 요청 매핑 명세 (FINAL)

## 목적 (Objective)
고객이 제시한 예제 1~4(고객-캐노니컬 시나리오)를 **백엔드 API 요청으로 "결정론적으로(compilable)" 매핑**하는 규칙을 고정한다.

- UI/LLM은 "질문 입력/선택 유도"까지만 수행한다.
- **최종 실행 요청(CompareRequest/SQL)은 deterministic rule-based compiler가 생성**한다.
- 모든 요청은 **재현 가능하도록 로그**되어야 한다.

본 문서는:
1) 각 예제가 어떤 API로 연결되는지,
2) 필요한 파라미터를 어떻게 확보/유도하는지,
3) 부족할 때 어떤 방식으로 "선택 유도"를 하는지,
4) 실패/불가 시 어떻게 응답하는지
를 규정한다.

---

## 공통 절대 원칙 (Immutable Rules)

1. **신정원 통일코드(coverage_code)는 절대 기준(canonical)**
   - 어떤 단계(ingestion/alias/backfill/compare)에서도 이를 위반하는 매핑 금지
2. **LLM은 질의 정제/선택 유도만**
   - 실행 쿼리는 rule-based compiler가 생성 (재현 가능)
3. **Evidence 없는 값은 출력 금지**
   - API가 evidence를 반환하지 못하면 View Model에서 "확인 불가"
4. **추천/판단/해석 금지**
5. **회사명 + 상품명 병기 필수**
   - API 응답의 meta/targets에 반드시 포함될 수 있어야 함
6. **예제 1 보험료는 "참고용"**
   - premium_notice 강제, 개인화/정확계산 불가
7. **새로운 응답 유형/새로운 매핑 타입 추가 금지**
   - 아래 4개 예제 타입으로만 분류/매핑

---

## 현재 API 전제 (Assumptions)
- 현재 시스템에는 비교 중심 API가 존재하며, View Model을 렌더링한다.
- Premium API(보험료 계산/조회)는 "기존 시스템 호출_api 문서" 기반이나, 현재는 검증 미완료이며 MVP에서는 제한 제공한다.
- 신규 회사/상품 등록은 CSV/JSONL → loader(upsert) → 검증(카운트/샘플쿼리)로 진행한다.

⚠️ 본 문서는 "API가 이미 존재한다"는 가정 하에, **요청 스키마를 고정**한다.
(실제 엔드포인트 이름은 구현체에서 매핑 가능)

---

## 표준 요청 스키마 (Canonical Request Shapes)

### A) CompareRequest (담보/조건/종합 비교 공통)
```json
{
  "query": "사용자 원문 질의",
  "intent": "PRODUCT_SUMMARY | COVERAGE_CONDITION_DIFF | COVERAGE_AVAILABILITY",
  "insurers": ["SAMSUNG", "HANWHA"],
  "product_scope": {
    "mode": "AUTO_TOP_PRODUCT | EXPLICIT_PRODUCTS",
    "products": [
      {"insurer": "SAMSUNG", "product_key": "samsung_xxx", "variant_key": null}
    ]
  },
  "coverage_scope": {
    "mode": "CANONICAL_SET | SINGLE_COVERAGE | MULTI_COVERAGE",
    "coverage_codes": ["A4210"],
    "canonical_set_id": "EXAMPLE3_CORE_9"
  },
  "slots": {
    "sex": "M | F | null",
    "age": 30,
    "term_years": 20,
    "pay_years": 20,
    "renewal": "NON_RENEWABLE | RENEWABLE | null",
    "plan_type": "GENERAL | NO_LAPSE | null",
    "disease": "암 | 제자리암 | 경계성종양 | ...",
    "surgery_method": "DA_VINCI | ROBOT | OPEN | null",
    "subtype": "IN_SITU | BORDERLINE | SIMILAR_CANCER | null"
  },
  "debug": {
    "resolved_coverage_codes": true,
    "trace_compiler": true
  }
}
```

### B) PremiumRequest (보험료 "참고용")
```json
{
  "query": "사용자 원문 질의",
  "intent": "PREMIUM_REFERENCE",
  "filters": {
    "sex": "M|F",
    "age": 30,
    "category": "종합",
    "plan_type": ["GENERAL", "NO_LAPSE"],
    "top_k": 4,
    "sort_by": "MONTHLY_PREMIUM_ASC"
  },
  "notice": {
    "premium_notice": true,
    "disclaimer_level": "STRONG"
  }
}
```

---

## 예제별 매핑 규칙 (Customer Examples → API)

### 예제 1: 보험료 비교 (PREMIUM_REFERENCE)

**고객 입력(예)**
- "가장 저렴한 보험료 정렬순으로 4개만 비교해줘"
- (옵션) 성별/나이/보험종류(종합/암2대 등)

**매핑 타겟**
- PremiumRequest 생성

**필수 파라미터**
- sex, age, category(보험종류), plan_type(일반/무해지), top_k=4, sort_by

**파라미터 확보 규칙**
1. 사용자가 이미 입력폼(첫 화면)에서 성별/나이/보험종류를 제공하면 그대로 사용
2. 누락 시 LLM이 한 번만 선택 유도 질문:
   - "성별/나이/보험종류(종합/암2대) 중 무엇으로 비교할까요?"
3. 그래도 없으면:
   - sex=null, age=null이면 보험료 비교 실행 금지
   - View Model로 "필수 조건 부족" 반환

**출력 제약**
- premium_notice=true 강제
- "참고용" 경고 문구/limitations 강제

---

### 예제 2: 담보 조건 차이 (COVERAGE_CONDITION_DIFF)

**고객 입력(예)**
- "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

**매핑 타겟**
- CompareRequest(intent=COVERAGE_CONDITION_DIFF)

**필수 파라미터**
- coverage_codes(=신정원 통일코드로 resolve)
- insurer scope (AUTO: 전체 or 사용자가 특정 보험사 지정)

**파라미터 확보 규칙**
1. 담보명(한글)이 들어오면:
   - rule-based coverage resolver가 canonical coverage_code 후보 생성
2. 후보가 1개면 확정
3. 후보가 복수면:
   - LLM이 "선택 유도" (최대 1회)
   - 예: "암직접입원비가 (A코드) vs (B코드) 중 어떤 담보인가요?"
4. 보험사 스코프:
   - 사용자가 보험사를 말하지 않으면 기본은 "등록된 보험사 전체"
   - 단, 결과가 과도하면 UI가 Top-N(예: 6개)만 보여주고 "더 보기" 제공

**coverage_scope 규칙**
- mode=SINGLE_COVERAGE
- coverage_codes=[resolved_code]

**product_scope 규칙**
- mode=AUTO_TOP_PRODUCT (보험사별 대표상품 1개 또는 최신 등록상품 1개)
- 선택 기준은 결정론적 규칙으로 문서화/로그

---

### 예제 3: 상품 종합 비교 ⭐ (PRODUCT_SUMMARY)

**고객 입력(예)**
- "삼성생명, 한화생명의 암진단비를 비교해줘"

**매핑 타겟**
- CompareRequest(intent=PRODUCT_SUMMARY)

**필수 파라미터**
- insurers: 2개 이상 (고객이 제시)
- coverage_scope: canonical_set_id = EXAMPLE3_CORE_9 (9개 담보 고정)
- product_scope: 각 insurer별 product_key 확정 필요
- (선택) age/sex/term/pay 등은 UI 기본정보로 받되, 없으면 null 허용

**파라미터 확보 규칙**
1. 보험사 2개 이상 명시되면 그대로
2. 상품명/상품키가 명시되지 않으면:
   - product_scope.mode = AUTO_TOP_PRODUCT
   - 각 insurer에서 "대표 상품 1개"를 결정론적으로 선택
   - 선택 기준(예):
     - 최신 가입설계서 존재 + coverage_instance 매칭률 높은 상품 우선
     - 없으면 최근 ingest된 상품
   - 선택 결과는 meta.targets에 "자동 선택됨"으로 표시

**coverage_scope 규칙**
- mode=CANONICAL_SET
- canonical_set_id="EXAMPLE3_CORE_9"
- coverage_codes는 내부적으로 set에서 확정 (신정원 코드)

**Notes 생성 규칙**
- Notes는 비교 결과에서 파생된 사실 요약만 허용
- "종합 평가/추천" 금지
- evidence 없는 Notes 금지 (Notes도 evidence 또는 evidence_refs 필요)

---

### 예제 4: 보장 가능 여부 O/X (COVERAGE_AVAILABILITY)

**고객 입력(예)**
- "제자리암, 경계성종양 보장내용에 따라 A사, B사 상품 비교해줘"

**매핑 타겟**
- CompareRequest(intent=COVERAGE_AVAILABILITY)

**필수 파라미터**
- insurers: 2개 이상
- disease/subtype slots: IN_SITU / BORDERLINE 등
- coverage_scope: MULTI_COVERAGE 또는 CANONICAL_SET("subtype 판정 대상 세트")

**파라미터 확보 규칙**
1. 질병 하위개념 키워드 탐지:
   - "제자리암" → subtype=IN_SITU
   - "경계성종양" → subtype=BORDERLINE
2. 어떤 담보를 기준으로 O/X인지가 모호하면:
   - 기본은 "암 진단비/유사암 진단비" 세트로 수행 (결정론적)
3. 결과가 evidence로 판정 불가하면:
   - O/X 대신 "확인 불가" (회색)

---

## 예외 처리 (Failure Modes)

### 1. coverage_code 해석 불가
- View Model: limitations에 "담보 식별 불가"
- LLM은 1회 선택 유도 가능, 그 이상 금지

### 2. product_key 선정 불가
- 해당 insurer는 "확인 불가(상품 선택 실패)"로 처리
- 시스템은 다른 insurer 비교는 계속 가능

### 3. evidence 부족
- 값은 "확인 불가"
- notes도 생성 금지

---

## 로깅 / 재현성 (Logging & Reproducibility)

모든 API 요청은 다음을 로그로 남긴다:
- raw query
- intent 결정 결과
- resolved insurers
- resolved product_keys(자동선택이면 선택 규칙/근거)
- resolved_coverage_codes(신정원 코드)
- compiler version hash
- request payload canonical JSON

---

## 신규 회사/상품 등록 SOP 연동 (SOP Hook)

예제 실행 이전에 "등록 완료"는 다음 조건을 만족해야 한다:
- loader upsert idempotent (instance_key/evidence_key) 통과
- coverage_instance / evidence_ref / amount_fact 카운트 안정
- 최소 1개 예제(권장: 예제3)에서 evidence가 반환됨

---

## 금지 사항 (Strict Prohibitions)
- 추천/판단/해석 문구 생성
- LLM이 실행 쿼리(CompareRequest/SQL)를 직접 생성
- 신정원 통일코드 아닌 임의 코드 사용
- evidence 없이 값/notes 생성
- 예제 1 보험료를 "정확값"처럼 표현

---

## DoD (Definition of Done)
- ✅ 예제 1~4 각각에 대해 "입력 → API Request(JSON) → View Model" 경로가 문서로 고정됨
- ✅ 각 예제에 대해 필수/선택 파라미터와 선택 유도 규칙이 명확함
- ✅ intent 분류 규칙이 4개로만 제한됨
- ✅ 모든 요청이 재현 가능한 로그 스키마를 가짐
- ✅ 금지 사항/실패 처리 규칙이 포함됨
- ⏳ STATUS.md에 STEP NEXT-8 완료 요약이 반영됨
