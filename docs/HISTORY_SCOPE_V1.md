# HISTORY_SCOPE_V1 – inca-rag-scope 역사적 합의

**작성일**: 2025-12-28
**목적**: DB 적재 이전까지 확정되었던 프로젝트 설계 원칙의 기록
**역할**: 기록자(Archivist) – 과거 합의 사실만 문서화

---

## 1. 프로젝트의 원래 목적

### 1.1 무엇을 해결하려 했는가

**문제**: 보험 가입설계서 30~40개 담보에 대한 정확한 **근거 자료 수집**과 **보험사 간 사실 비교**가 수작업으로 이루어지고 있었다.

**목표**:
- 가입설계서 요약 장표에 포함된 **30~40개 담보만을 범위(scope)**로 제한
- 각 담보에 대한 **정확한 표준화**(canonical mapping)
- 약관/사업방법서/상품요약서에서 **근거 문서 자동 매칭**
- 보험사 간 **사실 비교표** 자동 생성

### 1.2 무엇을 의도적으로 하지 않기로 했는가

**명시적 금지 사항** (README.md, CLAUDE.md 기준):
- ❌ **LLM 요약/추론/생성**: LLM은 근거 문서 탐색만 허용, canonical 생성/수정 금지
- ❌ **Embedding/벡터DB 사용**: 유사도 기반 자동 매칭 금지
- ❌ **담보명 자동 매칭/추천**: 사람이 Excel에서 직접 정의한 매핑만 사용
- ❌ **Scope 외 데이터 처리**: 약관 전체 담보 파싱/저장 금지
- ❌ **보고서에 "추천", "제안", "결론" 삽입**: 사실만 나열

---

## 2. 왜 Scope-First 접근을 선택했는가

### 2.1 약관 전체 파싱이 왜 실패했는지

**기존 방식 (inca-rag)**:
- 약관 전체 담보를 파싱하여 DB에 저장
- LLM으로 담보명 생성/표준화
- 결과: 담보 목록이 불확실하고, canonical 정의가 일관되지 않음

**실패 원인**:
1. **Canonical Source 부재**: 약관마다 담보 표현이 다르고, 자동 생성된 canonical이 신뢰 불가
2. **범위 무제한**: 모든 약관 담보를 처리하려다 정확도 하락
3. **LLM 의존**: 생성/추론에 의존하여 재현성 없음

### 2.2 가입설계서 30~40개 담보로 제한한 이유

**합의된 원칙**:
1. **가입설계서가 실제 필요한 범위**를 정의한다
   - 고객에게 제시되는 담보 = scope
   - 약관 전체가 아니라 가입설계서 장표만 처리

2. **Canonical은 Excel에서 사람이 정의**한다
   - `data/sources/mapping/담보명mapping자료.xlsx`가 유일한 출처
   - 코드/LLM으로 생성 금지

3. **약관/사업방법서/상품요약서는 근거 탐색용**으로만 사용
   - Scope 담보에 대한 evidence만 추출
   - 전체 파싱 금지

---

## 3. Canonical Truth에 대한 합의

### 3.1 담보명mapping자료.xlsx의 지위

**절대 기준** (CLAUDE.md, README.md):
- **유일한 정규 담보 목록 출처**
- 모든 담보 표준화는 이 파일 기준
- 이 파일에 없는 담보는 처리 금지

**Excel 구조** (STEP9_DB_POPULATION_SPEC.md):
- `coverage_code` (예: A4200_1)
- `coverage_name_canonical` (예: 암진단비(유사암제외))
- `coverage_category` (예: 진단)
- `payment_event` (예: 암 진단 확정 시)

### 3.2 자동 생성/LLM 개입을 금지한 이유

**합의된 이유**:
1. **재현성 보장**: 동일 입력 → 동일 출력 필수
2. **신뢰성 확보**: 사람이 정의한 canonical만 신뢰 가능
3. **Scope Gate 엄격 적용**: scope 외 담보는 어떤 단계에서도 처리/저장/추론 금지

**Excel 수정 정책** (STEP13_CANCER_CANONICAL_POLICY.md):
- 수동 편집은 허용
- 코드로 생성/변경 금지
- LLM / vector / embedding 금지

---

## 4. Evidence 설계의 핵심 원칙

### 4.1 문서 타입 분리 이유

**3가지 문서 타입 독립 검색** (CLAUDE.md):
- 약관 (policy)
- 사업방법서 (business)
- 상품요약서 (summary)

**분리 이유**:
- **hits_by_doc_type 필수**: 각 담보별로 어느 문서에서 나왔는지 기록
- **policy_only 플래그 유지**: 약관에만 존재하는 담보 구분
- **Doc-type diversity 우선**: Coverage Card evidence 선택 시 약관/사업방법서/상품요약서 각 1개씩 우선 (STEP6E_CARD_SELECTION_RULE.md)

### 4.2 원문 보존 원칙

**Evidence 원칙** (CLAUDE.md):
- 검색 결과는 원문 그대로 보존
- 요약/해석 금지
- Snippet은 증거 텍스트 보존용 (500자 이내)

### 4.3 policy_only 개념의 의미

**정의**: 약관에만 존재하고 가입설계서/사업방법서/상품요약서에는 없는 담보

**용도**:
- 담보의 존재 여부를 문서 타입별로 추적
- 약관 기준 검증

---

## 5. CSV 기반 검증 파이프라인의 의미

### 5.1 왜 DB 이전에 CSV로 검증했는지

**7 STEP 파이프라인** (CLAUDE.md, README.md):

1. **load_scope**: mapping → scope.csv
2. **pdf_extract**: PDF → 페이지 텍스트
3. **search**: 담보명 검색 → 매칭 페이지
4. **evidence**: 원문 추출 → pack.jsonl
5. **validation**: 증거 품질 체크
6. **report**: 보험사별 단일 보고서
7. **compare**: 보험사 간 대조표

**CSV 기반 이유**:
- **검증 가능**: 사람이 각 단계 결과를 직접 확인
- **재현 가능**: 동일 입력 → 동일 CSV 보장
- **DB 독립**: DB는 최종 저장소, 파이프라인은 CSV 기반

### 5.2 사람이 확인하는 단계가 어디였는지

**사람 확인 지점**:
1. **STEP 1**: `{insurer}_scope.csv` – 가입설계서에서 추출된 담보 목록
2. **STEP 2**: `{insurer}_scope_mapped.csv` – canonical mapping 결과 (matched/unmatched)
3. **STEP 4**: `{insurer}_evidence_pack.jsonl` – 담보별 근거 문서 snippet
4. **STEP 5**: `{insurer}_coverage_cards.jsonl` – 담보별 금액/조건 카드
5. **STEP 6**: `{insurer}_report.md` – 보험사별 사실 보고서

**검증 원칙**:
- pytest 전체 PASS
- Regression 0 (기존 보험사 결과 변화 없음)
- 각 STEP 산출물을 사람이 직접 검토

---

## 6. 명시적으로 폐기한 선택지들

### 6.1 inca-rag-final 방식

**폐기 이유**:
- 약관 전체 담보 DB화 → scope 무제한 → 정확도 하락
- LLM 생성/추론 의존 → 재현성 없음
- Canonical 자동 생성 → 신뢰 불가

### 6.2 약관 전체 담보 DB화

**폐기 이유** (README.md):
- 가입설계서 30~40개만 필요
- scope 외 담보는 처리/저장/추론 금지

### 6.3 API/LLM에서의 결론 보정

**폐기 이유** (STEP9_DB_POPULATION_SPEC.md):
- DB는 사실(fact)만 저장
- 결론/추론/계산은 DB 밖에서 수행
- API는 DB 조회만 수행, 생성/보정 금지

---

## 7. DB의 원래 예정된 역할

### 7.1 DB는 무엇을 저장해야 했는가

**STEP 9 DB POPULATION SPECIFICATION** 기준:

**9개 테이블**:
1. `insurer`, `product`, `product_variant`, `doc_structure_profile` (metadata)
2. `document` (PDF 문서 메타데이터)
3. `coverage_canonical` (Excel에서 로드된 canonical 정의)
4. `coverage_instance` (보험사별 scope 담보 인스턴스)
5. `evidence_ref` (담보별 근거 문서 snippet)
6. `amount_fact` (담보별 금액/조건 사실)

**저장 원칙**:
- **사실(fact)만 저장**: CSV/JSONL에서 추출된 원본 데이터
- **FK 제약 보장**: 부모-자식 관계 보장
- **Idempotent UPSERT**: 재실행 가능

### 7.2 DB가 절대 해서는 안 되는 일

**STEP 9 명시적 금지** (STEP9_DB_POPULATION_SPEC.md Section 14):

```sql
-- ❌ WRONG: Generate coverage_code in DB
INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical)
SELECT
  'A' || LPAD(ROW_NUMBER() OVER ()::TEXT, 4, '0'),
  coverage_name
FROM temp_coverage_list;

-- ✅ RIGHT: Load from Excel ONLY
INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical)
SELECT coverage_code, coverage_name_canonical
FROM excel_import;
```

**DB = Storage Layer**:
- ✅ Store facts from files
- ✅ Enforce FK constraints
- ✅ Enforce CHECK constraints
- ✅ Enable fast queries

**DB ≠ Generator**:
- ❌ Generate canonical codes
- ❌ Infer missing amounts
- ❌ Calculate amounts from rates
- ❌ Summarize evidence snippets

---

## 8. Evidence와 Amount의 분리

### 8.1 Evidence의 역할

**정의** (STEP9_DB_POPULATION_SPEC.md Section 7):
- `evidence_ref` 테이블: 담보별 근거 문서 snippet 저장
- **snippet**: 원문 텍스트 (요약 금지, 500자 이내)
- **doc_type**: 약관/사업방법서/상품요약서/가입설계서
- **rank**: 우선순위 (1-3)

**역할**:
- 사실의 **근거**를 제공
- 원문 그대로 보존
- 사람이 검증 가능

### 8.2 Amount의 역할

**정의** (STEP9_DB_POPULATION_SPEC.md Section 8):
- `amount_fact` 테이블: 담보별 **금액/조건 사실** 저장
- **value_text**: 금액 텍스트 (예: "3000만원")
- **status**: CONFIRMED / UNCONFIRMED
- **source_doc_type**: 가입설계서 우선 (PRIMARY)

**역할**:
- 담보의 **금액** 저장
- Evidence와 분리 (evidence_id FK로 연결)
- CONFIRMED는 반드시 evidence 보유

**분리 이유**:
- Evidence는 "근거 텍스트"
- Amount는 "사실 값"
- 같은 evidence에서 여러 amount 추출 가능

---

## 9. Coverage Card Evidence Selection Rule

### 9.1 규칙의 목적

**문제** (STEP6E_CARD_SELECTION_RULE.md):
- Evidence pack에는 doc_type별 다수 evidence 존재
- Coverage card는 최대 3개만 저장
- Doc-type 편중 발생 가능 (예: 약관만 3개)

**해결** (Rule 6-ε):
1. **Doc-Type Diversity 우선**: 약관 1개 → 사업방법서 1개 → 상품요약서 1개
2. **동일 doc_type 내 우선순위**: page 번호가 가장 앞선 것 우선
3. **최대 개수 고정**: 절대 3개 초과 금지

### 9.2 역사적 의미

**합의 시점**: STEP 6-ε (2025-12-27)

**의미**:
- Evidence 선택이 **결정적(deterministic)**으로 고정됨
- Doc-type diversity 보장
- 재현 가능

---

## 10. Canonical 분해 원칙 (암 담보)

### 10.1 STEP 13 Cancer Canonical Policy

**적용 대상**: 암 담보 (A42 계열) ONLY

**분리 기준** (STEP13_CANCER_CANONICAL_POLICY.md):
- **YES (분리한다)**: 지급 이벤트가 다르면 분리
  - 암진단비 vs 재진단암 (최초 진단 vs 재진단)
  - 암진단비 vs 암치료비 (진단 vs 치료)
  - 암진단비 vs 항암약물치료비 (진단 vs 약물치료)

- **NO (분리하지 않는다)**: 지급 이벤트 동일, 표기만 다른 경우
  - 보험사별 명칭 차이 (동일 지급 이벤트 + 동일 지급 구조)
  - 괄호 표기 차이 (예: "암진단비(유사암제외)" vs "암(유사암제외)진단비")

**단일 판단 기준**:
> "지급 이벤트와 지급 조건이 동일하면 alias, 이벤트가 다르면 suffix 또는 신규 Canonical"

### 10.2 명시적 금지

**DO NOT** (STEP13_CANCER_CANONICAL_POLICY.md):
- ❌ 매칭률 기준으로 Canonical 설계
- ❌ 자동 분류 / 키워드 유사도
- ❌ 질병코드 (ICD/KCD) 도입
- ❌ LLM / vector / embedding
- ❌ 숫자 suffix 무한 증식 (최대 _9)

---

## 11. 역사적 결론

### 11.1 프로젝트의 핵심 원칙 (요약)

1. **Scope-First**: 가입설계서 30~40개 담보만 처리
2. **Canonical Truth ONLY**: Excel이 유일한 출처, 자동 생성 금지
3. **Evidence 원문 보존**: 요약/해석 금지, snippet 그대로 저장
4. **DB는 Storage**: 생성/추론/계산 금지, 사실만 저장
5. **CSV 기반 검증**: 사람이 각 단계 확인 가능
6. **재현 가능**: 동일 입력 → 동일 출력 보장

### 11.2 이 문서의 용도

**목적**:
- DB 적재 이후 발생한 문제의 원인을 추적할 때
- 원래 설계 의도와 실제 구현의 괴리를 확인할 때
- "왜 이렇게 설계했는가"에 대한 역사적 기록

**금지**:
- ❌ 새로운 설계 제안
- ❌ 개선안, 리팩토링 제안
- ❌ "앞으로는 이렇게 하자" 류의 문장
- ❌ 현재 DB 상태에 대한 평가

**원칙**:
> 오직 **과거에 이미 합의된 사실만** 기록한다.

---

**문서 종료**
