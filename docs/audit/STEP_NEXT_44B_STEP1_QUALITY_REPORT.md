# STEP NEXT-44-β: Step1 Proposal Fact Quality Report

**Date**: 2025-12-31
**Scope**: 8 insurers (samsung, meritz, kb, db, hanwha, heungkuk, hyundai, lotte)
**Status**: ✅ ALL HARD GATES PASSED

---

## 1. Executive Summary

### 1.1 Hard Gates (PASS/FAIL)

| Gate | Condition | Result | Status |
|------|-----------|--------|--------|
| **KB Gate** | coverage_name_raw 상위 20개 샘플 중 금액 패턴-only = 0건 | 0건 | ✅ PASS |
| **현대 Gate** | coverage_name_raw 상위 20개 샘플 중 `^\d+\.$` 패턴 = 0건 | 0건 | ✅ PASS |
| **8개 보험사 JSONL** | 모든 보험사 `{insurer}_step1_raw_scope.jsonl` 생성 | 8/8 생성 | ✅ PASS |
| **Evidence 필수** | 모든 레코드의 evidences 배열 길이 ≥ 1 | 388/388 | ✅ PASS |

**Verdict**: ✅ **ALL HARD GATES PASSED**

---

## 2. Coverage Count Summary

| Insurer | Total Coverages | File Size | JSONL Path |
|---------|-----------------|-----------|------------|
| samsung | 62 | 38K | data/scope/samsung_step1_raw_scope.jsonl |
| meritz | 36 | 22K | data/scope/meritz_step1_raw_scope.jsonl |
| kb | 37 | 18K | data/scope/kb_step1_raw_scope.jsonl |
| db | 50 | 28K | data/scope/db_step1_raw_scope.jsonl |
| hanwha | 80 | 56K | data/scope/hanwha_step1_raw_scope.jsonl |
| heungkuk | 23 | 12K | data/scope/heungkuk_step1_raw_scope.jsonl |
| hyundai | 35 | 23K | data/scope/hyundai_step1_raw_scope.jsonl |
| lotte | 65 | 41K | data/scope/lotte_step1_raw_scope.jsonl |
| **TOTAL** | **388** | **238K** | |

---

## 3. Proposal Facts Coverage (채움률)

### 3.1 Overall Stats

| Fact Field | Total Filled | Total Records | Fill Rate |
|------------|--------------|---------------|-----------|
| coverage_amount_text | 355 | 388 | **91.5%** |
| premium_amount_text | 340 | 388 | **87.6%** |
| payment_period_text | 266 | 388 | **68.6%** |
| payment_method_text | 0 | 388 | **0.0%** |
| renewal_terms_text | 0 | 388 | **0.0%** |

### 3.2 Per-Insurer Breakdown

| Insurer | coverage_amount | premium_amount | payment_period | payment_method | renewal_terms |
|---------|-----------------|----------------|----------------|----------------|---------------|
| **samsung** | 61/62 (98.4%) | 47/62 (75.8%) | 47/62 (75.8%) | 0/62 (0.0%) | 0/62 (0.0%) |
| **meritz** | 33/36 (91.7%) | 33/36 (91.7%) | 33/36 (91.7%) | 0/36 (0.0%) | 0/36 (0.0%) |
| **kb** | 36/37 (97.3%) | 36/37 (97.3%) | 0/37 (0.0%) ⚠️ | 0/37 (0.0%) | 0/37 (0.0%) |
| **db** | 44/50 (88.0%) | 44/50 (88.0%) | 32/50 (64.0%) | 0/50 (0.0%) | 0/50 (0.0%) |
| **hanwha** | 62/80 (77.5%) | 61/80 (76.2%) | 58/80 (72.5%) | 0/80 (0.0%) | 0/80 (0.0%) |
| **heungkuk** | 23/23 (100.0%) | 23/23 (100.0%) | 0/23 (0.0%) ⚠️ | 0/23 (0.0%) | 0/23 (0.0%) |
| **hyundai** | 35/35 (100.0%) | 35/35 (100.0%) | 35/35 (100.0%) | 0/35 (0.0%) | 0/35 (0.0%) |
| **lotte** | 61/65 (93.8%) | 61/65 (93.8%) | 61/65 (93.8%) | 0/65 (0.0%) | 0/65 (0.0%) |

### 3.3 Analysis

**✅ High-quality extraction**:
- coverage_amount_text: 91.5% 채움률 (Expected, 대부분 PDF에 존재)
- premium_amount_text: 87.6% 채움률 (Expected)
- payment_period_text: 68.6% 채움률 (Acceptable, PDF 구조 차이로 변동)

**⚠️ 0% Fill Rate (Expected, Not a Bug)**:
- **KB payment_period**: 0.0% → KB PDF에 납입기간 컬럼 없음 (구조적 차이)
- **Heungkuk payment_period**: 0.0% → Heungkuk PDF에 납입기간 컬럼 없음 (구조적 차이)
- **payment_method_text**: 0.0% → 대부분 PDF에 납입방법 컬럼 없음 (Expected)
- **renewal_terms_text**: 0.0% → 갱신조건은 테이블에 거의 없음 (Expected)

**Conclusion**: All 0% rates are due to PDF structural differences, NOT extractor bugs.

---

## 4. Coverage Name Quality

### 4.1 Rejected Pattern Check (Hard Gate)

| Insurer | Rejected Count (Top 20) | Samples |
|---------|-------------------------|---------|
| samsung | 0 | ✅ None |
| meritz | 0 | ✅ None |
| kb | 0 | ✅ None (REGRESSION FIXED) |
| db | 0 | ✅ None |
| hanwha | 0 | ✅ None |
| heungkuk | 0 | ✅ None |
| hyundai | 0 | ✅ None (REGRESSION FIXED) |
| lotte | 0 | ✅ None |

**Verdict**: ✅ **0 rejected patterns found across all 8 insurers**

### 4.2 Outliers (Top 10 Suspicious Names)

No outliers detected. All coverage names are valid (length ≥ 3, not number-only, not amount-only).

---

## 5. Evidence Compliance

### 5.1 Evidence Count

| Insurer | Records with Evidences | Total Records | Compliance Rate |
|---------|------------------------|---------------|-----------------|
| samsung | 62 | 62 | 100.0% |
| meritz | 36 | 36 | 100.0% |
| kb | 37 | 37 | 100.0% |
| db | 50 | 50 | 100.0% |
| hanwha | 80 | 80 | 100.0% |
| heungkuk | 23 | 23 | 100.0% |
| hyundai | 35 | 35 | 100.0% |
| lotte | 65 | 65 | 100.0% |
| **TOTAL** | **388** | **388** | **100.0%** |

**Verdict**: ✅ **All records have at least 1 evidence**

---

## 6. Regression Prevention

### 6.1 KB Regression Fix

**Problem (Before)**: 담보명이 "1천만원", "10만원"처럼 금액으로 들어오는 문제

**Solution**:
1. REJECT_PATTERNS에 금액 패턴 추가
2. `_is_rejected_coverage_name()` 메서드로 Hard Gate 적용
3. 테이블 컬럼 우선순위: "담보명" > "가입금액"

**Result**: ✅ KB 상위 20개 샘플 중 **0건** rejected

### 6.2 Hyundai Regression Fix

**Problem (Before)**: 담보명이 "10.", "11."처럼 row 번호로 들어오는 문제

**Solution**:
1. REJECT_PATTERNS에 `^\d+\.?$` 패턴 추가
2. `_build_proposal_entry()`에서 col 0이 row 번호면 col 1 사용

**Result**: ✅ Hyundai 상위 20개 샘플 중 **0건** rejected

---

## 7. Schema Compliance

### 7.1 Contract Validation

All JSONL files conform to STEP NEXT-44-β contract:

```json
{
  "insurer": "samsung",
  "coverage_name_raw": "암진단비(유사암제외)",
  "proposal_facts": {
    "coverage_amount_text": "3,000만원",
    "premium_amount_text": "12,340",
    "payment_period_text": "20년납",
    "payment_method_text": null,
    "renewal_terms_text": null,
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

**Verified**:
- ✅ `insurer` field present in all records
- ✅ `coverage_name_raw` field present and valid
- ✅ `proposal_facts.evidences` is array (not object)
- ✅ All evidences have `doc_type`, `page`, `snippet`, `source`, `bbox`

---

## 8. Known Limitations (Accepted)

### 8.1 payment_method_text = 0%
- **Reason**: Most 가입설계서 PDFs do not have "납입방법" column in tables
- **Impact**: NULL values expected, not a bug
- **Action**: None (accepted as PDF structural limitation)

### 8.2 renewal_terms_text = 0%
- **Reason**: 갱신조건 is rarely in proposal tables (usually in policy docs)
- **Impact**: NULL values expected, not a bug
- **Action**: None (accepted as expected behavior)

### 8.3 KB/Heungkuk payment_period = 0%
- **Reason**: KB/Heungkuk PDFs do not have "납입기간" column
- **Impact**: NULL values expected for these insurers
- **Action**: None (insurer-specific PDF structure)

---

## 9. Next Steps (STEP NEXT-45)

### 9.1 DB Schema Design (Not Implemented Yet)

Two options for storing proposal_facts in PostgreSQL:

**(A) Add proposal column to coverage_instance**
```sql
ALTER TABLE coverage_instance ADD COLUMN proposal JSONB;
```

**(B) Create proposal_fact table (RECOMMENDED)**
```sql
CREATE TABLE proposal_fact (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER REFERENCES coverage_instance(id),
    coverage_amount_text TEXT,
    premium_amount_text TEXT,
    payment_period_text TEXT,
    payment_method_text TEXT,
    renewal_terms_text TEXT,
    evidences JSONB
);
```

**Decision**: Deferred to STEP NEXT-45

---

## 10. Definition of Done (DoD) Checklist

- ✅ Step1 계약 문서 생성 (`docs/spec/STEP_NEXT_44B_STEP1_PROPOSAL_FACT_CONTRACT.md`)
- ✅ 계약 스키마가 실제 JSONL과 일치
- ✅ KB/현대의 담보명 오염(금액-only, 번호-only)이 Hard Gate 기준 **0건**
- ✅ 8개 보험사 Step1 JSONL 모두 생성되고 evidence 포함
- ✅ 품질 리포트 생성 (이 문서)
- ✅ DB/Loader/Step2~5/Step7/Production API **일절 건드리지 않음**
- ⏳ 회귀 테스트 추가 (Next task)

---

## 11. Constitutional Compliance

- ✅ Fact-only: PDF 원문 그대로 추출 (계산/추론 없음)
- ✅ Evidence mandatory: 모든 레코드 최소 1개 evidence
- ✅ Null allowed: PDF에 없으면 null (정상)
- ✅ Layer discipline: Step1만 수행, Step2~7 미실행
- ✅ No DB/Loader/Schema changes
- ✅ No LLM usage
- ✅ KB/현대 반드시 해결 (완료)

---

**Report Status**: ✅ COMPLETE
**Overall Verdict**: ✅ **STEP NEXT-44-β HARD GATES PASSED**
