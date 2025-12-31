# STEP NEXT-33 Not Found Case Analysis

**Date**: 2025-12-31
**Purpose**: Root cause analysis for Meritz single not_found case
**Insurer**: Meritz

---

## 대상 not_found 케이스

- **Insurer**: Meritz
- **Coverage_name_raw**: `(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회\n한)`
- **Evidence_status**: `not_found`
- **Source**: `data/compare/meritz_coverage_cards.jsonl`

---

## 분석 결과

### STEP 1: Scope 존재 여부 확인

**Command**:
```bash
grep -n "중증질환자" data/scope/meritz_scope_mapped.sanitized.csv
```

**Result**: ✅ **존재 확인**
```
Line 14: "(20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회
한)",meritz,3,,,unmatched,none
```

**Finding**: Scope entry contains **newline character** `\n` between "1회" and "한"

---

### STEP 2: Evidence Text 존재 여부 확인

**Command**:
```bash
grep -R "중증질환자(뇌혈관질환)" data/evidence_text/meritz/
```

**Result**: ✅ **존재 확인** (extensive evidence)

**Evidence locations**:
- `data/evidence_text/meritz/상품요약서/메리츠_상품요약서.page.jsonl` (page 5, 6, 54, 63)
- `data/evidence_text/meritz/약관/메리츠_약관.page.jsonl` (page 21, 72, 1524, 1528, 1529, 1532, 1533)

**Sample evidence snippet** (약관 page 1532):
```
"갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)"
```

**Note**: Evidence text contains the **complete coverage name WITHOUT newline**

---

### STEP 3: Evidence → Card Join 실패 여부 확인

**Command**:
```bash
jq 'select(.coverage_name_raw | contains("중증질환자(뇌혈관질환)"))' \
data/compare/meritz_coverage_cards.jsonl
```

**Result**: ❌ **Join 실패**

**Coverage card content**:
```json
{
  "evidences": [],
  "hits_by_doc_type": {
    "약관": 0,
    "사업방법서": 0,
    "상품요약서": 0
  },
  "evidence_status": "not_found"
}
```

**Evidence pack content**:
```json
{
  "evidences": [],
  "hits_by_doc_type": {
    "약관": 0,
    "사업방법서": 0,
    "상품요약서": 0
  }
}
```

**Finding**: Step4 search returned 0 hits despite extensive evidence existing

---

### STEP 4: Comparative Analysis

**Comparison**: Similar coverage "(20년갱신)갱신형 중증질환자(**심장질환**) 산정특례대상 진단비(연간1회한)"

**Result**: ✅ **Found successfully**

**Evidence pack** (심장질환 variant):
```json
{
  "evidences": [
    {
      "doc_type": "가입설계서",
      "page": 3,
      "snippet": "716\n(20년갱신)갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)\n1백만원\n188",
      "match_keyword": "(20년갱신)갱신형 중증질환자(심장질환) 산정특례대상 진단비(연간1회한)"
    }
  ],
  "hits_by_doc_type": { "약관": 0, "사업방법서": 0, "상품요약서": 0 }
}
```

**Key Difference**:
- **뇌혈관질환** variant: Scope contains `연간1회\n한` (with newline)
- **심장질환** variant: Scope contains `연간1회한` (no newline)
- **심장질환** found in 가입설계서 but not in 약관/상품요약서
- **뇌혈관질환** has evidence in 약관/상품요약서 but Step4 exact-match search failed

---

## 최종 분류

**Case**: **C (Join Failure)**

**분류 근거**:
1. ✅ Scope exists (Step1 extracted correctly)
2. ✅ Evidence text exists extensively (약관 + 상품요약서)
3. ❌ Step4 exact-match search failed (0 hits)
4. ❌ Step5 join rate 0% (no evidence candidates)

**Root Cause**:
- **Scope coverage name contains embedded newline**: `연간1회\n한`
- **Evidence text contains canonical name**: `연간1회한` (no newline)
- **Step4 search uses exact string match**: Newline breaks the match
- **Result**: Search query `"...(연간1회\n한)"` does not match document text `"...(연간1회한)"`

---

## 정책적 판단 (초안)

This case falls into:
- [x] **Scope normalization issue** (newline removal required)
- [ ] alias 추가 대상
- [ ] evidence ingestion 보강 대상
- [ ] intentional not_found 유지

**Recommended action** (for next step):
- Step1 sanitization should normalize newlines within coverage names
- OR Step4 search should normalize query strings before exact-match search
- Current behavior is structurally correct (exact match is failing as expected)
- Fix location: **Step1 post-processing** or **Step4 pre-search normalization**

**Impact Assessment**:
- **Frequency**: Single case (1/34 = 2.9%)
- **Evidence availability**: High (extensive 약관 + 상품요약서 coverage)
- **Workaround**: Manual scope CSV edit (not scalable)
- **Proper fix**: Automated newline normalization in pipeline

---

## 검증 자료

**File paths**:
- Scope: `data/scope/meritz_scope_mapped.sanitized.csv:14`
- Evidence pack: `data/evidence_pack/meritz_evidence_pack.jsonl` (search: 중증질환자(뇌혈관질환))
- Coverage card: `data/compare/meritz_coverage_cards.jsonl` (search: 중증질환자(뇌혈관질환))

**Commands for reproduction**:
```bash
# 1. Verify scope newline
sed -n '14p' data/scope/meritz_scope_mapped.sanitized.csv | cat -A

# 2. Verify evidence text existence
grep -R "중증질환자(뇌혈관질환)" data/evidence_text/meritz/ | wc -l

# 3. Verify join failure
jq '.evidences | length' data/evidence_pack/meritz_evidence_pack.jsonl | grep -E '^0$' | wc -l
```

---

## 다음 단계 권고사항

**STEP NEXT-34** 후보:
1. **Option A**: Step1 post-processing에 newline normalization 추가
2. **Option B**: Step4 search에 query normalization 추가
3. **Option C**: 수동 scope CSV 수정 (not scalable, not recommended)

**추천**: Option A (Step1 level fix for data hygiene)
