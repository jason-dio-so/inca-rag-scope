# Pipeline Step3-5 입출력 및 기능 설명

## 개요

Step3-5는 **근거 자료 수집 및 카드 생성** 파이프라인으로, 가입설계서에서 추출한 scope(담보 목록)에 대해 보험사 약관/사업방법서/상품요약서에서 근거를 검색하고 최종 비교용 카드를 생성합니다.

**핵심 원칙**:
- **No LLM**: 모든 처리는 deterministic (정규표현식, 문자열 매칭)
- **No Embedding/Vector DB**: 텍스트 그대로 검색
- **No 요약/추론**: 원문 그대로 보존

---

## Step 3: PDF Text Extraction

### 목적
보험사별 근거 문서(약관, 사업방법서, 상품요약서)를 페이지별 텍스트로 추출합니다.

### 입력
- **Manifest CSV**: `data/evidence_sources/{INSURER}_manifest.csv`
  - 필드: `doc_type`, `file_path`
  - 각 보험사별 근거 문서 목록 (약관/사업방법서/상품요약서 PDF 경로)

### 출력
- **페이지별 텍스트 JSONL**: `data/evidence_text/{INSURER}/{doc_type}/{basename}.page.jsonl`
  - 각 줄: `{"page": 1, "text": "..."}`
  - 페이지 번호는 1-based
  - OCR 없음 (PyMuPDF 기본 텍스트 추출만 사용)

### 기능
1. **PDF 열기**: PyMuPDF (fitz) 사용
2. **페이지별 텍스트 추출**: `page.get_text("text")`
3. **GATE-3-1**: 추출된 페이지 수 = PDF 메타데이터 페이지 수 검증
4. **JSONL 저장**: 페이지별 1줄씩 기록

### 실행
```bash
python -m pipeline.step3_extract_text.run --insurer samsung
```

### 코드 위치
- `pipeline/step3_extract_text/extract_pdf_text.py`

---

## Step 4: Evidence Search

### 목적
담보별로 약관/사업방법서/상품요약서에서 근거(evidence) 검색합니다.

### 입력
- **Canonical Scope JSONL** (STEP NEXT-61 SSOT): `data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl`
  - Step2-b에서 생성한 정제된 담보 목록 (신정원 통일코드 매핑 완료)
  - 필드: `coverage_name_raw`, `canonical_name`, `coverage_code`, `mapping_method`
- **Evidence Text**: `data/evidence_text/{INSURER}/{doc_type}/*.page.jsonl`
  - Step3에서 생성한 페이지별 텍스트

### 출력
- **Evidence Pack JSONL**: `data/evidence_pack/{INSURER}_evidence_pack.jsonl`
  - 첫 줄: meta record (생성 시각, scope hash, schema version)
  - 이후: 담보별 evidence 목록
- **Unmatched Review JSONL**: `data/scope_v3/{INSURER}_step4_unmatched_review.jsonl`
  - 매핑되지 않은 담보의 검색 결과 (수동 검토용)

### 기능
1. **문서 타입별 독립 검색** (필수):
   - 약관, 사업방법서, 상품요약서 각각 독립적으로 검색
   - `hits_by_doc_type`: 각 문서 타입별 hit 수 기록
2. **Query Variants** (보험사별):
   - **현대**: suffix 제거 (`담보`, `특약`, `보장`), 진단비↔진단 변환
   - **한화**: 암 용어 브릿지 (`4대유사암` ↔ `유사암(4대)`), suffix 제거
3. **Fallback 검색** (한화 전용):
   - Token-AND Search: 핵심 토큰 2개 이상 동일 라인 내 존재 시 매칭
4. **보험사별 특수 규칙**:
   - **KB A4200_1** (암진단비(유사암제외)): 사업방법서 정의 Hit 판정 (STEP 6-δ)
5. **Snippet 추출**:
   - 키워드 포함 라인 ± 2줄 (총 5줄)
   - 최대 500자

### Evidence Pack JSONL 구조
```jsonl
{"record_type": "meta", "insurer": "samsung", "scope_file": "samsung_step2_canonical_scope_v1.jsonl", "scope_content_hash": "abc123...", "created_at": "2025-01-01T12:00:00Z", "schema_version": "step_next_61_v1"}
{"insurer": "samsung", "coverage_name_raw": "뇌혈관질환 진단비(1년50%)", "coverage_code": "A4101", "mapping_status": "matched", "needs_alias_review": false, "evidences": [...], "hits_by_doc_type": {"약관": 3, "사업방법서": 3, "상품요약서": 3}, "flags": []}
...
```

### Flags
- `policy_only`: 약관에만 존재 (사업방법서/상품요약서 0건)
- `fallback_token_and`: Token-AND Search로 발견
- `kb_bm_definition_hit`: KB 사업방법서 정의 Hit 보정

### 실행
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer samsung
```

### 코드 위치
- `pipeline/step4_evidence_search/search_evidence.py`

---

## Step 5: Build Coverage Cards

### 목적
담보별 종합 정보 카드(Coverage Card)를 생성합니다. 이는 **SSOT (Single Source of Truth)**로 모든 비교/조회 API가 이 파일을 사용합니다.

### 입력
- **Canonical Scope JSONL** (STEP NEXT-61): `data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl`
  - Step2-b 출력 (Step5는 임시 CSV로 변환 후 사용)
- **Evidence Pack JSONL**: `data/evidence_pack/{INSURER}_evidence_pack.jsonl`
  - Step4 출력

### 출력
- **Coverage Cards JSONL** (SSOT): `data/compare/{INSURER}_coverage_cards.jsonl`
  - 담보별 1줄, 모든 정보 통합

### 기능
1. **GATE-5-1**: Coverage count 일치 검증 (scope vs evidence_pack)
2. **GATE-5-2**: Join rate ≥ 95% 검증 (scope와 evidence_pack 조인율)
3. **Doc-Type Diversity Evidence Selection** (STEP 6-ε.2):
   - Evidence 중복 제거 (doc_type, file_path, page, snippet 기준)
   - Fallback 판정: `fallback_` 포함 OR `token_and(` 시작
   - 우선순위 정렬:
     1. Non-fallback 우선
     2. 약관 > 사업방법서 > 상품요약서
     3. 페이지 오름차순
   - Diversity pass: 각 doc_type에서 1개씩 (최대 3개)
   - Fill-up pass: 부족분 채우기
4. **Proposal Facts 보존** (STEP NEXT-UI-FIX-04):
   - Step1 가입설계서에서 추출한 금액/보험료/기간 정보 유지
   - CSV에는 저장 안 됨 (메모리 전용)

### Coverage Card JSONL 구조
```jsonl
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
      "file_path": "/.../약관.page.jsonl",
      "page": 6,
      "snippet": "...",
      "match_keyword": "뇌혈관질환진단비"
    },
    ...
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
    "evidences": [...]
  }
}
```

### 실행
```bash
python -m pipeline.step5_build_cards.build_cards --insurer samsung
```

### 코드 위치
- `pipeline/step5_build_cards/build_cards.py`
- `core/compare_types.py`: CoverageCard/Evidence 데이터 클래스 정의

---

## 데이터 흐름 요약

```
Step 3: PDF → 페이지별 텍스트
  입력: data/evidence_sources/{INSURER}_manifest.csv
  출력: data/evidence_text/{INSURER}/{doc_type}/*.page.jsonl

Step 4: Scope + 텍스트 → Evidence Pack
  입력: data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl
        data/evidence_text/{INSURER}/**/*.page.jsonl
  출력: data/evidence_pack/{INSURER}_evidence_pack.jsonl
        data/scope_v3/{INSURER}_step4_unmatched_review.jsonl

Step 5: Scope + Evidence Pack → Coverage Cards (SSOT)
  입력: data/scope_v3/{INSURER}_step2_canonical_scope_v1.jsonl
        data/evidence_pack/{INSURER}_evidence_pack.jsonl
  출력: data/compare/{INSURER}_coverage_cards.jsonl
```

---

## Gates (품질 검증)

| Gate | 위치 | 조건 | 실패 시 |
|------|------|------|---------|
| GATE-3-1 | Step3 | 추출 페이지 수 = PDF 메타데이터 페이지 수 | RuntimeError (PDF 무결성 문제) |
| GATE-5-1 | Step5 | Coverage count 일치 (scope vs pack) | Warning (의도적 필터링일 수 있음) |
| GATE-5-2 | Step5 | Join rate ≥ 95% | RuntimeError (evidence_pack 재생성 필요) |

---

## 참고 문서
- `CLAUDE.md`: 프로젝트 전체 아키텍처 및 SSOT 정의
- `core/compare_types.py`: CoverageCard/Evidence 스키마 정의
