# STEP NEXT-44-β — Proposal Fact SSOT Final Implementation

**Date**: 2025-12-31
**Status**: ✅ **COMPLETE**

---

## Executive Summary

**Proposal 담보금액 SSOT 확정 & Step7 역할 축소**

🎯 **Core Decision (LOCKED)**:
1. 담보금액은 가입설계서(Proposal)에서 Step1에 포함해 추출한다
2. Step1 결과가 SSOT의 유일한 출처다
3. Step7은 재추출 단계가 아니다 (선택적 검증만 수행)
4. KB / 흥국 회귀 문제는 Step1에서 완전히 차단
5. PDF 변경 시 Step1부터 전량 재실행 → DB reset & reload

---

## Implementation Results

### ✅ All 8 Insurers Processed Successfully

| Insurer | Coverages | coverage_amount_text | premium_amount_text | payment_period_text |
|---------|-----------|----------------------|---------------------|---------------------|
| Samsung | 62 | 61 (98.4%) | 47 (75.8%) | 47 (75.8%) |
| Meritz | 36 | 33 (91.7%) | 33 (91.7%) | 33 (91.7%) |
| KB | 37 | 36 (97.3%) | 36 (97.3%) | 0 (0.0%) |
| Hanwha | 80 | 62 (77.5%) | 61 (76.2%) | 58 (72.5%) |
| Hyundai | 35 | 35 (100.0%) | 35 (100.0%) | 35 (100.0%) |
| Lotte | 65 | 61 (93.8%) | 61 (93.8%) | 61 (93.8%) |
| Heungkuk | 23 | 23 (100.0%) | 23 (100.0%) | 0 (0.0%) |
| DB | 50 | 44 (88.0%) | 44 (88.0%) | 32 (64.0%) |
| **TOTAL** | **388** | **355 (91.5%)** | **340 (87.6%)** | **266 (68.6%)** |

---

## Contract Structure (FINAL)

### Step1 Output Format

**File**: `data/scope/{insurer}_step1_raw_scope.jsonl`

**Structure**:
```json
{
  "insurer": "kb",
  "coverage_name_raw": "암 진단비(유사암 제외)",
  "proposal": {
    "coverage_amount_text": "3,000만원",
    "premium_amount_text": "12,340",
    "payment_period_text": "20년납/100세만기",
    "payment_method_text": "월납",
    "evidence": {
      "coverage_amount": { "page": 2, "snippet": "가입금액 3,000만원" },
      "premium_amount": { "page": 2, "snippet": "보험료 12,340" },
      "payment_period": { "page": 2, "snippet": "20년납/100세만기" },
      "payment_method": { "page": 2, "snippet": "월납" }
    }
  }
}
```

**Rules (LOCKED)**:
- ❌ 계산/추론 금지
- ❌ 값 없이 evidence만 금지
- ✅ 값이 없으면 `null` + `evidence.reason: "not_present_in_proposal"`
- ✅ All values extracted as-is from PDF

---

## Hard Gates Implementation

### KB/Heungkuk Regression Prevention

**Rejected Coverage Name Patterns**:
```python
REJECT_PATTERNS = [
    r'^\d+\.?$',              # "10.", "11."
    r'^\d+\)$',               # "10)", "11)"
    r'^\d+(,\d{3})*(원|만원)?$',  # "3,000원", "3,000만원"
    r'^\d+만(원)?$',          # "10만", "10만원"
    r'^\d+[천백십](만)?원?$',  # "1천만원", "5백만원"
    r'^[천백십만억]+원?$',    # "천원", "만원", "억원"
]
```

**Verification Result**:
- ✅ **KB**: No rejected patterns found (37 coverages)
- ✅ **Heungkuk**: No rejected patterns found (23 coverages)
- ✅ **All other insurers**: No rejected patterns found

---

## Key Technical Improvements

### 1. Row Number Detection
- **Problem**: KB PDF has row numbers in column 0, coverage names in column 1
- **Solution**: Detect `^\d+\.?$` pattern in column 0, shift coverage column to column 1
- **Result**: KB extraction improved from 8 to 37 coverages

### 2. Multi-Cell Header Handling
- **Problem**: Headers may span multiple cells or have empty cells
- **Solution**: Check adjacent cells for header text, adjust column indices dynamically
- **Result**: Robust header detection across all insurer PDF formats

### 3. Amount Column Avoidance
- **Problem**: Fallback logic sometimes picked amount column as coverage name
- **Solution**: Explicitly skip `amount_col` when searching for coverage name
- **Result**: No amount values mistaken for coverage names

---

## DoD (Definition of Done) Checklist

- [x] 8개 보험사 Step1 결과 재현 가능
- [x] KB / 흥국에서 순번·금액이 담보명으로 나오지 않음
- [x] proposal_facts가 모든 coverage에 존재 (388/388)
- [x] Step7 미실행 상태 (검증 전용으로 역할 축소)
- [x] Evidence 없는 값 0건 (모든 값은 evidence 보유)

---

## Output Files

```
data/scope/samsung_step1_raw_scope.jsonl     (62 lines)
data/scope/meritz_step1_raw_scope.jsonl      (36 lines)
data/scope/kb_step1_raw_scope.jsonl          (37 lines)
data/scope/hanwha_step1_raw_scope.jsonl      (80 lines)
data/scope/hyundai_step1_raw_scope.jsonl     (35 lines)
data/scope/lotte_step1_raw_scope.jsonl       (65 lines)
data/scope/heungkuk_step1_raw_scope.jsonl    (23 lines)
data/scope/db_step1_raw_scope.jsonl          (50 lines)
```

**Total**: 388 coverages with proposal facts

---

## Step2/5 Integration Plan (Next Steps)

### Step5 SSOT Reflection

`coverage_cards.jsonl` structure:
```json
{
  "coverage_code": "A4200_1",
  "coverage_name_canonical": "암진단비",
  "insurer": "kb",
  "proposal_facts": {
    "coverage_amount_text": "3,000만원",
    "premium_amount_text": "12,340",
    "payment_period_text": "20년납/100세만기",
    "payment_method_text": "월납",
    "evidence": { ...Step1 그대로... }
  }
}
```

- Step5는 Step1 결과를 이동/정리만 수행
- ❌ 새 추출, ❌ 보정, ❌ 추론 금지

### Step7 Redefinition

**역할 축소 (선택적 검증)**:
- 입력: `coverage_cards.jsonl`
- 출력: `amount_fact.status` only

**Status Values**:
- `UNCONFIRMED`: 기본값 (정상)
- `CONFIRMED`: 약관/사업방법서에 동일 금액 명시 발견
- `CONFLICT`: Proposal vs 약관 상충 발견

**당분간 Step7 비활성 유지 가능**

---

## API Display Principle

- `amount_fact = UNCONFIRMED` 이어도:
- `proposal_facts.coverage_amount_text`는 **"가입설계서 기준 금액"**으로 노출
- `amount_fact`는 별도 블록에서 "확인 불가"

---

## DB Schema (Minimal Change Required)

**Recommended**:
```sql
ALTER TABLE coverage_instance
ADD COLUMN proposal_facts JSONB;
```

- Loader는 SSOT → DB 단방향
- DB는 Pipeline 종료 후에만 reset/reload

---

## 🔒 Final Consensus Statement

**"담보금액은 가입설계서에서 Step1에 고정 추출한다.
Step7은 재추출이 아니라 검증(optional)이다."**

---

## Execution Record

**Execution Date**: 2025-12-31
**Tool**: `pipeline/step1_extract_scope/proposal_fact_extractor_v2.py`
**Method**: `python -m pipeline.step1_extract_scope.proposal_fact_extractor_v2 --insurer {insurer}`

**Results**:
- ✅ All 8 insurers completed successfully
- ✅ No errors encountered
- ✅ All regression gates passed
- ✅ Evidence compliance 100%

---

🔒 **STEP NEXT-44-β COMPLETE**

This implementation establishes proposal facts as the SSOT for all coverage amounts.
All downstream steps (Step2, Step5, DB loading) will use these results as INPUT.

**Next Action**: STEP NEXT-45 — Step2 Canonical Mapping (Proposal Fact 유지)
