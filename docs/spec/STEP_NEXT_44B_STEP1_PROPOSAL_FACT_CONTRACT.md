# STEP NEXT-44-β: Step1 Proposal Fact Contract (SSOT LOCK)

**Status**: 🔒 LOCKED
**Date**: 2025-12-31
**Purpose**: Step1 가입설계서 Proposal Fact 추출 계약 (SSOT)

---

## 1. 계약 범위 (Scope)

### 1.1 입력 (Input)
- **파일**: `data/sources/insurers/{insurer}/가입설계서/*.pdf`
- **보험사**: 8개 고정 (samsung, meritz, kb, db, hanwha, heungkuk, hyundai, lotte)

### 1.2 출력 (Output - SSOT)
- **파일**: `data/scope/{insurer}_step1_raw_scope.jsonl`
- **형식**: JSONL (1 line = 1 coverage)
- **인코딩**: UTF-8

---

## 2. JSONL 레코드 스키마 (LOCKED)

각 라인은 다음 구조를 가진다:

```json
{
  "insurer": "samsung",
  "coverage_name_raw": "암진단비(유사암제외)",
  "proposal_facts": {
    "coverage_amount_text": "3,000만원",
    "premium_amount_text": "12,340",
    "payment_period_text": "20년납",
    "payment_method_text": "월납",
    "renewal_terms_text": "20년갱신",
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 3,
        "snippet": "암진단비(유사암제외): 3,000만원",
        "source": "table",
        "bbox": null
      }
    ]
  }
}
```

### 2.1 필수 필드

| 필드 | 타입 | 설명 | Null 허용 |
|------|------|------|-----------|
| `insurer` | string | 보험사 코드 (소문자) | ❌ |
| `coverage_name_raw` | string | 담보명 (PDF 원문) | ❌ |
| `proposal_facts` | object | 제안 사실 객체 | ❌ |
| `proposal_facts.coverage_amount_text` | string | 가입금액 (텍스트 원문) | ✅ |
| `proposal_facts.premium_amount_text` | string | 보험료 (텍스트 원문) | ✅ |
| `proposal_facts.payment_period_text` | string | 납입기간 (텍스트 원문) | ✅ |
| `proposal_facts.payment_method_text` | string | 납입방법 (텍스트 원문) | ✅ |
| `proposal_facts.renewal_terms_text` | string | 갱신조건 (텍스트 원문) | ✅ |
| `proposal_facts.evidences` | array | 증거 배열 (최소 1개) | ❌ |

### 2.2 Evidence 스키마

각 evidence는 다음 필드를 포함:

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `doc_type` | string | 문서 타입 (고정값: "가입설계서") | "가입설계서" |
| `page` | integer | 페이지 번호 (1-based) | 3 |
| `snippet` | string | 원문 스니펫 (trim 최소화) | "암진단비(유사암제외): 3,000만원" |
| `source` | string | 추출 방법 ("table" 또는 "text") | "table" |
| `bbox` | object\|null | 좌표 (선택, {x0,y0,x1,y1}) | null |

---

## 3. Constitutional Rules (LOCKED)

### 3.1 Fact-only (사실만)
- ✅ PDF에 "문자 그대로 존재하는 값"만 추출
- ❌ 계산, 추론, 정규화 금지
- 예:
  - ✅ "3,000만원" → `"3,000만원"`
  - ❌ "3,000만원" → `30000000` (정수 변환 금지)

### 3.2 Evidence Mandatory (증거 필수)
- 모든 추출 값은 최소 1개 evidence 필수
- Evidence 없으면 해당 fact는 null

### 3.3 Null Allowed (널 허용)
- PDF에 해당 컬럼/텍스트가 없으면 null 허용
- 단, evidence로 "없음"을 주장하지 말 것

### 3.4 Layer Discipline (계층 규율)
- **Step1**: PDF → raw facts + evidence (이번 계약)
- **Step2~5**: mapping/정규화/카드 생성 (후속)
- **Step7**: (향후) 추가 검증/보강 역할 (이번 스텝에서 언급 금지)

---

## 4. 담보명 판별 규칙 (Coverage Name Detection)

### 4.1 최소 조건
- 한글/영문 포함 + 길이 ≥ 3
- 숫자-only 금지: `^\d+$`
- 금액 패턴만 있는 경우 제외

### 4.2 Rejection Patterns (HARD GATE)

다음 패턴에 매치되면 담보명으로 **절대 허용 안 함**:

| 패턴 | 설명 | 예시 |
|------|------|------|
| `^\d+\.?$` | 행 번호 (KB/현대) | "10.", "11." |
| `^\d+\)$` | 행 번호 (괄호) | "10)", "11)" |
| `^\d+(,\d{3})*(원\|만원)?$` | 금액 | "3,000원", "3,000만원" |
| `^\d+만(원)?$` | 금액 (만 단위) | "10만", "10만원" |
| `^\d+[천백십](만)?원?$` | 금액 (한글 단위) | "1천만원", "5백만원" |
| `^[천백십만억]+원?$` | 금액 (한글 단위 only) | "천원", "만원", "억원" |

### 4.3 테이블 컬럼 우선순위

담보명 컬럼 탐지 순서:
1. "담보명", "보장명", "가입담보", "담보가입현황" 포함 헤더
2. "가입금액", "보험료", "납기", "만기" 컬럼은 담보명으로 **절대 사용 금지**
3. 첫 번째 컬럼이 `^\d+\.$` 패턴이면 "번호 컬럼"으로 간주하고 skip

### 4.4 KB/현대 특수 처리

**KB 문제**: 담보명이 "1천만원", "10만원"처럼 금액으로 들어오는 경우
- **해결**:
  - 테이블 컬럼 매칭 로직 강화
  - "가입담보/담보/보장/담보명" 우선
  - 담보명 후보가 금액 패턴이면, 같은 row의 다른 컬럼에서 재탐색

**현대 문제**: 담보명이 "10.", "11."처럼 row 번호로 들어오는 경우
- **해결**:
  - row 첫 컬럼이 `^\d+\.$` 패턴이면 "번호 컬럼"으로 간주하고 skip
  - 담보명은 다음 컬럼에서 가져오기

---

## 5. Proposal Facts 판별 규칙

### 5.1 coverage_amount_text (가입금액)
- Text-only로 보존 (정수 변환 금지)
- 예: "3,000만원", "1천만원", "10만원"

### 5.2 premium_amount_text (보험료)
- Text-only로 보존
- "0", "미부과"도 그대로 저장

### 5.3 payment_period_text (납입기간)
- 예: "20년납", "전기납", "10년/20년"

### 5.4 payment_method_text (납입방법)
- 예: "월납", "연납", "일시납"

### 5.5 renewal_terms_text (갱신조건)
- 예: "20년갱신", "갱신형", "비갱신"
- 대부분 PDF에 명시되지 않음 → null 예상

---

## 6. Hard Gates (FAIL 시 스텝 실패)

### 6.1 KB 게이트
- **조건**: coverage_name_raw 상위 20개 샘플 중 금액 패턴-only가 **0건**
- **패턴**: `^\d+(,\d{3})*(원|만원)?$`, `^\d+[천백십](만)?원?$`

### 6.2 현대 게이트
- **조건**: coverage_name_raw 상위 20개 샘플 중 `^\d+\.$` 패턴이 **0건**

### 6.3 8개 보험사 JSONL 생성
- **조건**: 모든 보험사에 대해 `{insurer}_step1_raw_scope.jsonl` 파일 생성

### 6.4 Evidence 필수
- **조건**: 모든 레코드의 `evidences` 배열 길이 ≥ 1

---

## 7. Soft Metrics (보고만, FAIL 아님)

| 메트릭 | 설명 | 임계값 |
|--------|------|--------|
| coverage_amount 채움률 | 가입금액 있는 비율 | 참고만 |
| premium_amount 채움률 | 보험료 있는 비율 | 참고만 |
| payment_period 채움률 | 납입기간 있는 비율 | 참고만 |

**주의**: 보험사별 PDF 구조 차이로 채움률 변동 가능. 단, **0%이면 원인 분석 + 개선 시도** 필수.

---

## 8. 금지 사항 (Non-negotiable)

### 8.1 Step7 언급 금지
- ❌ "Step7 다시 돌려야 함" 같은 표현/암시 금지
- Step7은 향후 역할 (이번 스텝 범위 밖)

### 8.2 DB/Loader 금지
- ❌ DB 초기화/적재/Loader 실행/Schema 변경/Production API 기동 금지

### 8.3 LLM 금지
- ❌ LLM 사용 금지 (추출/정규화/분류)

### 8.4 "어쩔 수 없음" 금지
- ❌ "문제는 문서가 이상해서 어쩔 수 없음"으로 결론 금지
- KB/현대는 **반드시 해결**

---

## 9. 테이블/스키마 관리 (설계만, 구현 안 함)

### 9.1 현재 스텝 (STEP NEXT-44-β)
- DB 스키마를 바꾸지 **않는다**

### 9.2 다음 스텝 (STEP NEXT-45) 고려사항
- **proposal_facts를 어디에 저장할지** 설계 초안만 작성:
  - **(A) coverage_instance에 proposal 컬럼 추가**
  - **(B) proposal_fact 별도 테이블 (1 row per instance_id)** ← 추천
- **결론은 내리지 말고** "다음 스텝에서 결정"으로만 기록

---

## 10. 회귀 방지 (Regression Prevention)

### 10.1 테스트 픽스처
- 최소 2개 보험사 샘플("KB", "현대")을 테스트 픽스처로 고정
- 테스트는 "담보명 금액/번호 오염이 0"을 보장

### 10.2 품질 리포트
- `docs/audit/STEP_NEXT_44B_STEP1_QUALITY_REPORT.md` 생성
- insurer별:
  - 총 row 수
  - coverage_name_raw 유효 비율
  - 각 fact별 채움률
  - 상위 10개 이상치 샘플

---

## 11. DoD (Definition of Done)

- ✅ Step1 계약 문서 생성 (이 문서)
- ✅ 계약 스키마가 실제 JSONL과 일치
- ✅ KB/현대의 담보명 오염(금액-only, 번호-only)이 Hard Gate 기준 **0건**
- ✅ 8개 보험사 Step1 JSONL 모두 생성되고 evidence 포함
- ✅ 품질 리포트와 회귀 테스트 추가
- ✅ DB/Loader/Step2~5/Step7/Production API **일절 건드리지 않음**

---

**계약 잠금 (Contract Lock)**: 이 문서는 Step1 Proposal Fact 추출의 **SSOT**입니다. 변경 시 Constitutional Review 필수.
