# STEP NEXT-9: API Contract 고정 (FINAL)

## 목적 (Objective)
UI/백엔드 분리 개발을 가능하게 하는 **API 계약(Contract)**을 고정한다.

- **Request**: 고객 예제 → deterministic compiler → CompareRequest
- **Response**: Response View Model (5-block 구조)
- **Mock API**: DB/리트리벌 없이 fixture 기반으로 계약 검증
- **UI Integration**: fixture 직접 로드 → API 호출로 전환

---

## 절대 원칙 (Immutable Rules)

1. **회사(보험사) 영문 용어는 insurer 사용**
2. **신정원 통일코드(coverage_code)는 canonical**
   - Request/Response 어디에서도 이를 변경/생성하지 않음
3. **LLM 역할은 질문 정제/선택 유도까지만**
   - 최종 실행 요청(CompareRequest/SQL)은 deterministic compiler가 생성
4. **응답은 STEP NEXT-2의 Response View Model(5-block) 구조 절대 변경 금지**
5. **Evidence 없는 값은 출력 금지**
   - 값이 없으면 "확인 불가" + evidence도 "확인 불가"
6. **추천/판단/해석 금지**
   - "더 좋음", "유리", "추천", "가입 권유", "확정적 결론" 금지
7. **보험료는 예제 1 범위에서 "참고용"만**
   - premium_notice=true 강제

---

## API Endpoints

### Base URL
```
http://localhost:8001
```

### Endpoints

#### 1. Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "ok",
  "version": "mock-0.1.0",
  "timestamp": "2025-12-28T10:00:00Z"
}
```

#### 2. Compare API
```
POST /compare
```

**Request**: See `CompareRequest` schema below

**Response**: See `CompareResponse` (= Response View Model) schema below

---

## Request Schema: CompareRequest

### Structure

```json
{
  "intent": "PRODUCT_SUMMARY | COVERAGE_CONDITION_DIFF | COVERAGE_AVAILABILITY | PREMIUM_REFERENCE",
  "insurers": ["SAMSUNG", "HANWHA"],
  "products": [
    {
      "insurer": "SAMSUNG",
      "product_name": "삼성화재 무배당 New 원더풀 암보험"
    },
    {
      "insurer": "HANWHA",
      "product_name": "한화생명 무배당 암보험"
    }
  ],
  "target_coverages": [
    {
      "coverage_code": "A4200_1",
      "coverage_name_raw": "암 진단비(유사암 제외)"
    }
  ],
  "options": {
    "include_notes": true,
    "include_evidence": true,
    "premium_reference_only": false
  },
  "debug": {
    "force_example": "example3",
    "compiler_version": "v1.0.0"
  }
}
```

### Field Definitions

#### Required Fields

- **intent** (string, required)
  - `PRODUCT_SUMMARY`: 예제 3 - 상품 종합 비교 (9개 담보)
  - `COVERAGE_CONDITION_DIFF`: 예제 2 - 담보 조건 차이
  - `COVERAGE_AVAILABILITY`: 예제 4 - 보장 가능 여부 O/X
  - `PREMIUM_REFERENCE`: 예제 1 - 보험료 비교 (참고용)

- **insurers** (string[], required)
  - 비교 대상 보험사 코드 (영문 대문자)
  - 최소 1개, 권장 2개 이상

- **products** (object[], required)
  - 각 보험사별 상품 정보
  - `insurer`: 보험사 코드 (insurers와 일치)
  - `product_name`: 상품명 (한글 원문)
  - ⚠️ 회사명+상품명 병기가 필수이므로 반드시 포함

- **target_coverages** (object[], required for non-premium intents)
  - 비교 대상 담보 목록
  - `coverage_code`: 신정원 통일코드 (matched인 경우)
  - `coverage_name_raw`: 담보명 원문 (unmatched이거나 사용자 입력)
  - 둘 중 하나는 반드시 있어야 함

#### Optional Fields

- **options** (object, optional)
  - `include_notes`: Notes 포함 여부 (기본: true)
  - `include_evidence`: Evidence 포함 여부 (기본: true)
  - `premium_reference_only`: 보험료만 비교 (예제 1, 기본: false)

- **debug** (object, optional)
  - `force_example`: Mock API에서 강제로 특정 예제 반환 (개발용)
  - `compiler_version`: 요청 생성 compiler 버전

---

## Response Schema: CompareResponse (= Response View Model)

### Structure (5-Block)

```json
{
  "meta": {
    "query_id": "uuid-v4",
    "timestamp": "2025-12-28T10:00:00Z",
    "intent": "PRODUCT_SUMMARY",
    "compiler_version": "v1.0.0"
  },
  "query_summary": {
    "targets": [
      {
        "insurer": "SAMSUNG",
        "product_name": "삼성화재 무배당 New 원더풀 암보험",
        "source": "auto_selected"
      }
    ],
    "coverage_scope": {
      "type": "CANONICAL_SET",
      "canonical_set_id": "EXAMPLE3_CORE_9",
      "count": 9
    },
    "premium_notice": false
  },
  "comparison": {
    "type": "COVERAGE_TABLE",
    "columns": ["SAMSUNG", "HANWHA"],
    "rows": [
      {
        "coverage_code": "A4200_1",
        "coverage_name": "암 진단비(유사암 제외)",
        "values": {
          "SAMSUNG": {
            "value_text": "3,000만원",
            "evidence": {
              "status": "found",
              "source": "약관 p.27",
              "snippet": "암(유사암 제외) 진단 시 보험가입금액(3,000만원) 지급"
            }
          },
          "HANWHA": {
            "value_text": "확인 불가",
            "evidence": {
              "status": "unavailable",
              "reason": "해당 상품 정보 없음"
            }
          }
        }
      }
    ]
  },
  "notes": [
    {
      "title": "암진단비 지급 조건",
      "content": "삼성: 최초 1회 한도. 한화: 확인 불가.",
      "evidence_refs": ["약관 p.27"]
    }
  ],
  "limitations": [
    "본 비교는 약관 기준이며, 실제 가입 시 상품 변경 가능성이 있습니다.",
    "보험료는 참고용이며, 개인별 정확한 보험료는 설계사를 통해 확인하세요."
  ]
}
```

### Field Definitions

#### 1. meta (Metadata Block)

- **query_id**: 요청 고유 ID (UUID v4)
- **timestamp**: 응답 생성 시간 (ISO 8601)
- **intent**: 요청 intent (request와 동일)
- **compiler_version**: 사용된 compiler 버전

#### 2. query_summary (Query Summary Block)

- **targets**: 비교 대상 상품 목록
  - `insurer`: 보험사 코드
  - `product_name`: 상품명 (한글 원문)
  - `source`: 선택 방식 ("user_specified" | "auto_selected")

- **coverage_scope**: 담보 범위
  - `type`: "CANONICAL_SET" | "SINGLE_COVERAGE" | "MULTI_COVERAGE"
  - `canonical_set_id`: 고정 세트 ID (예: "EXAMPLE3_CORE_9")
  - `count`: 담보 개수

- **premium_notice**: 보험료 참고용 경고 표시 여부 (boolean)
  - 예제 1: true (강제)
  - 예제 2~4: false

#### 3. comparison (Comparison Block)

- **type**: "COVERAGE_TABLE" | "OX_TABLE" | "PREMIUM_LIST"

- **columns**: 보험사 코드 배열 (테이블 컬럼 헤더)

- **rows**: 비교 항목 배열
  - `coverage_code`: 신정원 통일코드 (있으면)
  - `coverage_name`: 담보명 (한글)
  - `values`: 보험사별 값
    - `{INSURER}`: 보험사 코드를 key로 사용
      - `value_text`: 표시 값 (예: "3,000만원", "O", "X", "확인 불가")
      - `evidence`: Evidence 객체
        - `status`: "found" | "unavailable"
        - `source`: 출처 (예: "약관 p.27")
        - `snippet`: 원문 발췌 (최대 200자)
        - `reason`: unavailable인 경우 이유

#### 4. notes (Notes Block)

- **title**: Notes 제목
- **content**: 사실 요약 (추론/판단 금지)
- **evidence_refs**: 근거 출처 배열 (예: ["약관 p.27", "사업방법서 p.10"])

⚠️ **Notes 생성 규칙**:
- Evidence 없는 Notes 금지
- "추천", "유리", "불리", "더 좋음" 등 판단 금지
- 사실 비교 요약만 허용

#### 5. limitations (Limitations Block)

- 문자열 배열
- 시스템 제약 사항/경고 문구
- 예제 1은 보험료 참고용 경고 강제 포함

---

## 예제별 Request/Response 매핑

### 예제 1: 보험료 비교 (PREMIUM_REFERENCE)

**Request**:
```json
{
  "intent": "PREMIUM_REFERENCE",
  "insurers": ["SAMSUNG", "HANWHA", "MERITZ", "DB"],
  "products": [
    {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
    {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"},
    {"insurer": "MERITZ", "product_name": "메리츠화재 무배당 암보험"},
    {"insurer": "DB", "product_name": "DB손해보험 무배당 암보험"}
  ],
  "target_coverages": [],
  "options": {
    "premium_reference_only": true,
    "include_notes": false,
    "include_evidence": false
  }
}
```

**Response 특징**:
- `query_summary.premium_notice`: **true** (강제)
- `comparison.type`: "PREMIUM_LIST"
- `limitations`: 보험료 참고용 경고 포함

---

### 예제 2: 담보 조건 차이 (COVERAGE_CONDITION_DIFF)

**Request**:
```json
{
  "intent": "COVERAGE_CONDITION_DIFF",
  "insurers": ["SAMSUNG", "HANWHA"],
  "products": [
    {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
    {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
  ],
  "target_coverages": [
    {"coverage_code": "A4210", "coverage_name_raw": "암 직접치료 입원일당"}
  ]
}
```

**Response 특징**:
- `comparison.type`: "COVERAGE_TABLE"
- 단일 담보에 대한 조건 차이 (보장한도, 대기기간 등)

---

### 예제 3: 상품 종합 비교 (PRODUCT_SUMMARY) ⭐

**Request**:
```json
{
  "intent": "PRODUCT_SUMMARY",
  "insurers": ["SAMSUNG", "HANWHA"],
  "products": [
    {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
    {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
  ],
  "target_coverages": [
    {"coverage_code": "A4200_1"},
    {"coverage_code": "A4210"},
    {"coverage_code": "A5200"},
    {"coverage_code": "A5100"},
    {"coverage_code": "A6100_1"},
    {"coverage_code": "A6300_1"},
    {"coverage_code": "A9617_1"},
    {"coverage_code": "A9640_1"},
    {"coverage_code": "A4102"}
  ],
  "options": {
    "include_notes": true,
    "include_evidence": true
  }
}
```

**Response 특징**:
- `coverage_scope.canonical_set_id`: "EXAMPLE3_CORE_9"
- `comparison.rows`: 9개 담보 비교
- `notes`: 7개 항목 (evidence 기반 사실 요약)

---

### 예제 4: 보장 가능 여부 O/X (COVERAGE_AVAILABILITY)

**Request**:
```json
{
  "intent": "COVERAGE_AVAILABILITY",
  "insurers": ["SAMSUNG", "HANWHA"],
  "products": [
    {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
    {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
  ],
  "target_coverages": [
    {"coverage_name_raw": "제자리암"},
    {"coverage_name_raw": "경계성종양"}
  ]
}
```

**Response 특징**:
- `comparison.type`: "OX_TABLE"
- `values.value_text`: "O" | "X" | "확인 불가"

---

## Mock API 동작 규칙

### Routing Logic

1. **Request 파싱**
   - `debug.force_example`이 있으면 해당 fixture 강제 반환
   - 없으면 `intent`로 라우팅:
     - `PRODUCT_SUMMARY` → example3
     - `COVERAGE_CONDITION_DIFF` → example2
     - `COVERAGE_AVAILABILITY` → example4
     - `PREMIUM_REFERENCE` → example1

2. **Fixture 반환**
   - `apps/mock-api/fixtures/example{N}.json` 로드
   - Response View Model 그대로 반환

3. **절대 금지**
   - DB 연결
   - 리트리벌/검색
   - LLM 호출
   - 동적 값 생성

---

## 에러 모델

### Error Response

```json
{
  "error": {
    "code": "INVALID_REQUEST | COVERAGE_NOT_FOUND | INSURER_NOT_FOUND",
    "message": "Human-readable error message",
    "details": {
      "field": "insurers",
      "reason": "At least 1 insurer required"
    }
  }
}
```

### Error Codes

- `INVALID_REQUEST`: Request 스키마 검증 실패
- `COVERAGE_NOT_FOUND`: coverage_code 해석 불가
- `INSURER_NOT_FOUND`: insurer 미등록
- `INTERNAL_ERROR`: 서버 내부 오류

---

## 로깅 / 재현성

### Request Logging

모든 요청은 다음을 로그로 남긴다:

```json
{
  "request_id": "uuid",
  "timestamp": "iso8601",
  "intent": "PRODUCT_SUMMARY",
  "insurers": ["SAMSUNG", "HANWHA"],
  "resolved_coverage_codes": ["A4200_1", "A4210"],
  "compiler_version": "v1.0.0",
  "payload_hash": "sha256"
}
```

---

## Validation

### Schema Validation

- `compare_request.schema.json`에 대해 example 1~4 통과
- `compare_response_view_model.schema.json`에 대해 fixture 1~4 통과

### Contract Tests

```python
# tests/test_api_contract.py
def test_request_schema_validation():
    for i in range(1, 5):
        request = load_example_request(i)
        validate(request, schema="compare_request.schema.json")

def test_response_schema_validation():
    for i in range(1, 5):
        response = load_fixture(i)
        validate(response, schema="compare_response_view_model.schema.json")
```

---

## 금지 사항 (Strict Prohibitions)

1. **DB/리트리벌/LLM 절대 금지** (Mock API 범위)
2. **Response View Model 구조 변경 금지**
3. **신정원 통일코드 임의 생성/변형 금지**
4. **추천/판단/해석 문구 생성 금지**
5. **보험료 계산/개인화 금지** (예제 1은 참고용만)

---

## DoD (Definition of Done)

- ✅ API Contract 문서 완성 (이 문서)
- ⏳ JSON Schema 2개 생성 + 예제 4개 검증 통과
- ⏳ Mock API 서버 실행 가능 (/health, /compare)
- ⏳ web-prototype API 호출 전환
- ⏳ 예제 1~4 모두 정상 렌더링
- ⏳ 금지어 0건 검증
- ⏳ STATUS.md 업데이트 + 커밋
