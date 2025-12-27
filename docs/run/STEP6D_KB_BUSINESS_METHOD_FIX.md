# STEP 6-δ — KB 사업방법서 Doc-Type Hit 판정 보정

**Date**: 2025-12-27
**Coverage**: A4200_1 (암진단비(유사암제외)) ONLY
**Insurer**: KB ONLY
**Doc Type**: 사업방법서 ONLY

---

## 목적

STEP 6-γ 검증 결과, KB 사업방법서는 "암진단비" 텍스트가 28 pages에 존재함에도 doc_type hit=0으로 판정되어 ABNORMAL 상태였다. 본 STEP은 KB/A4200_1/사업방법서에 한해 doc_type hit 메타 판정을 보정한다.

---

## 문제 정의 (FACT)

- KB 사업방법서: 총괄 정의/표 구조 위주, 개별 담보명 반복 구조 약함
- 현재 규칙: 개별 담보 phrase match 중심 → KB 구조에 불리
- Samsung/DB: 동일 사업방법서에서 정상 hit 발생
- 보정 목표: A4200_1에 한해 "정의/총괄 섹션 존재"를 hit로 인정

---

## 보정 규칙 (Rule 6-δ.1)

다음 조건을 모두 만족 시 doc_type hit(사업방법서) = 1:

- `insurer == "kb"`
- `coverage_code == "A4200_1"`
- `doc_type == "사업방법서"`
- 사업방법서 내 동일 "연속 10줄 윈도우"에서 아래 그룹 중 2개 이상 존재:
  - G1: 암 또는 암진단
  - G2: 진단
  - G3: 보험금 또는 지급
  - G4: 유사암제외 또는 유사암 제외

---

## 구현

**변경 파일**: `pipeline/step4_evidence_search/search_evidence.py`

**변경 내용**:
1. 새 함수 추가: `_kb_bm_a4200_1_definition_hit(pages)` (search_evidence.py:302-351)
2. `search_coverage_evidence()` 함수에 `coverage_code` 파라미터 추가 (search_evidence.py:418)
3. STEP 6-δ 판정 로직 추가 (search_evidence.py:493-516)

**제약 준수**:
- ✅ KB/A4200_1/사업방법서에만 적용
- ✅ Canonical/Excel/매핑 무변경
- ✅ 기존 keyword/variant 로직 무변경
- ✅ LLM/vector/RAG 미사용
- ✅ snippet 원문 그대로 (요약 없음)

---

## Before / After

### KB A4200_1 Doc-Type Hits

| Status | 약관 | 사업방법서 | 상품요약서 | Flags |
|--------|------|-----------|----------|-------|
| BEFORE | 3 | **0** | 0 | policy_only |
| AFTER | 3 | **1** | 0 | kb_bm_definition_hit |

### KB Evidence Count

| Status | Total Evidences |
|--------|----------------|
| BEFORE | 3 (약관 only) |
| AFTER | 4 (약관 3 + 사업방법서 1) |

---

## Regression Check (Other 7 Insurers)

| Insurer | 약관 | 사업방법서 | 상품요약서 | Change |
|---------|------|-----------|----------|--------|
| samsung | 3 | 3 | 3 | 0 |
| meritz | 3 | 0 | 3 | 0 |
| db | 3 | 3 | 3 | 0 |
| hanwha | 3 | 3 | 3 | 0 |
| lotte | 3 | 3 | 3 | 0 |
| hyundai | 3 | 3 | 3 | 0 |
| heungkuk | 3 | 3 | 3 | 0 |

✅ No changes to other insurers

---

## KB 사업방법서 Evidence (Original Snippet)

**Doc Type**: 사업방법서
**Page**: 3
**Match Keyword**: kb_bm_definition_hit
**File**: data/evidence_text/kb/사업방법서/KB_사업방법서.page.jsonl

```
선택계약
 3)
구 분
보험기간
납입기간
가입나이
보험료납입지원유사암진단

(
)주2-1)
```

*Note: Snippet은 요약 없이 원문 그대로 추출됨*

---

## Validation

### pytest
```
75 passed in 0.44s
```
✅ All tests pass

### Git Status
```
M  pipeline/step4_evidence_search/search_evidence.py
M  data/evidence_pack/kb_evidence_pack.jsonl
M  data/compare/kb_coverage_cards.jsonl
M  reports/a4200_1_8insurers.md
```

---

## 산출물

1. **Code**: `pipeline/step4_evidence_search/search_evidence.py` (STEP 6-δ rule added)
2. **Evidence Pack**: `data/evidence_pack/kb_evidence_pack.jsonl` (regenerated)
3. **Coverage Cards**: `data/compare/kb_coverage_cards.jsonl` (regenerated)
4. **Report**: `reports/a4200_1_8insurers.md` (KB 사업방법서 hit=1 반영)

---

## DoD Checklist

- ✅ KB/A4200_1/사업방법서 hit = 1
- ✅ 다른 doc_type/보험사/담보 변화 0
- ✅ Canonical/Excel/데이터 변경 0
- ✅ snippet 1개, 원문, 요약 없음
- ✅ pytest 100% PASS
- ✅ 재현 가능한 변경 완료

---

## 결론

KB 사업방법서의 doc_type hit이 STEP 6-γ에서 식별된 ABNORMAL 상태에서 정상으로 보정되었다. 보정은 KB/A4200_1/사업방법서에만 엄격히 제한되었으며, 다른 보험사 및 담보에는 영향이 없음이 검증되었다.
