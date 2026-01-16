# A4210 N09 SSOT Data Issue Proof

**Date**: 2026-01-16
**Coverage**: A4210 (유사암진단비)
**Insurer**: N09 (현대해상)
**Result**: Evidence generation FAILED (FOUND=0/3)
**Status**: ⛔ DEPRECATED (SSOT data incomplete)

---

## Executive Summary

**N09 "유사암진단Ⅱ(양성뇌종양포함)담보" is a VALID benefit (confirmed by proposal document), but evidence generation fails due to INCOMPLETE 약관 SSOT data.**

- ✅ **Benefit EXISTS**: 가입설계서 (proposal) page 5 clearly shows cash diagnosis benefit
- ❌ **Evidence FAILS**: FOUND=0/3 (약관 SSOT lacks detailed benefit clauses)
- 🔍 **Root Cause**: document_page_ssot missing "유사암진단Ⅱ담보" 약관 clauses

**This is a DATA ISSUE, not a gate/profile issue.**

---

## Background: CASE A Investigation

### Original Hypothesis (INCORRECT)
- Initial analysis concluded N09-A4210 was premium support benefit (보험료납입지원), not diagnosis benefit
- Marked as DEPRECATED based on 약관 analysis showing 148/349 chunks (42%) with premium support context

### User Directive: Verify with Proposal Document
- User requested verification using 가입설계서 SSOT (proposal document only)
- 3-criteria judgment:
  1. "유사암진단" mentioned
  2. Payment context (지급/보험금/가입금액/최초1회/진단확정)
  3. NOT premium support (no 보험료/납입/지원/면제)

### Verification Result: CASE A (Benefit EXISTS)
```
10. 유사암진단Ⅱ담보
기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단 확정된 경우
특약가입금액(각각 최초 1회한)(단, 최초계약일부터 1년미만 상기금액의 50%) 지급

가입금액: 6백만원
보험료: 1,248원
납기/만기: 20년납100세만기
```

**Analysis**:
- ✅ Criterion 1: "유사암진단Ⅱ담보" in benefit name
- ✅ Criterion 2: "진단 확정된 경우", "특약가입금액", "지급", "최초 1회한"
- ✅ Criterion 3: NO "보험료", "납입", "지원", "면제" in benefit clause

**Conclusion**: This is a legitimate cash diagnosis benefit (현금 진단비), NOT premium support.

---

## CASE A Restoration Attempt

### Action Taken
1. Restored N09-A4210 mapping to ACTIVE status
2. Regenerated evidence for 8 insurers (N01,N02,N03,N05,N08,N09,N10,N13)

### Result: Evidence Generation FAILED
```
2026-01-16 17:53:02,247 [INFO] ✅ Created slots: FOUND=21, NOT_FOUND=3, DROPPED=0
```

**Breakdown**:
- N01: 3/3 FOUND ✅
- N02: 3/3 FOUND ✅
- N03: 3/3 FOUND ✅
- N05: 3/3 FOUND ✅
- N08: 3/3 FOUND ✅
- **N09: 0/3 FOUND** ❌ (3 NOT_FOUND)
- N10: 3/3 FOUND ✅
- N13: 3/3 FOUND ✅

---

## Root Cause Analysis

### 1. Coverage Chunks Available
```sql
SELECT ins_cd, COUNT(*) as chunk_count
FROM coverage_chunk
WHERE coverage_code='A4210' AND as_of_date='2025-11-26'
GROUP BY ins_cd ORDER BY ins_cd;
```

**Result**: N09 has 349 chunks

**Anchor matching**: 221/349 (63%) chunks matched anchor keywords

### 2. Chunk Content Analysis

**N09 chunk composition**:
| Content Type | Percentage | Description |
|--------------|------------|-------------|
| Premium support | 42% (148 chunks) | "보험료납입지원(유사암진단)특별약관" clauses |
| Table of contents | 30% (105 chunks) | Lists coverage names without details |
| Summary tables | 20% (70 chunks) | Overview pages from요약서 |
| Exclusion clauses | 8% (26 chunks) | General cancer clauses mentioning "유사암제외" |

**Key finding**: NO chunks contain complete "유사암진단Ⅱ담보" benefit clause with:
- Waiting period terms (보장개시, 면책기간, 90일, 감액)
- Exclusion terms (보장하지 않는 사항, 면책사유)
- Subtype definitions (갑상선암/기타피부암/제자리암/경계성 정의, 범위)

### 3. Evidence Requirements vs Available Data

**Profile requires 3 slots**:
```python
"required_terms_by_slot": {
    "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률"],
    "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책"],
    "subtype_coverage_map": ["제자리암", "경계성", "갑상선암", "기타피부암", "범위"]
}
```

**N09 약관 SSOT status**:
- ❌ Waiting period clause: NOT FOUND in document_page_ssot
- ❌ Exclusion clause: NOT FOUND in document_page_ssot
- ❌ Subtype definitions: NOT FOUND in document_page_ssot

**Why other 7 insurers succeed**:
- All have complete약관 clauses in document_page_ssot
- Each slot requirement met by multiple chunks
- Clean separation between diagnosis benefit and premium support clauses

---

## Document_page_ssot Investigation

### Query: N09약관 with "유사암진단" keyword
```sql
SELECT doc_type, COUNT(*)
FROM document_page_ssot
WHERE ins_cd='N09' AND raw_text ~* '유사암진단'
GROUP BY doc_type ORDER BY doc_type;
```

**Result**:
| doc_type | count |
|----------|-------|
| 가입설계서 | 2 | ← **Benefit exists here** ✅
| 사업방법서 | 22 |
| 약관 | 14 | ← **Should contain detailed clauses** ❌
| 요약서 | 22 |

### Sample약관 Pages Analysis

**Page 777** (Premium support clause):
```
① 회사는 피보험자가 보험기간 중에 '유사암'으로 진단확정된 경우에는 최초 1회에 한하
여 아래의 금액을 보험수익자에게 보험금으로 지급합니다.
단, 보험료 납입지원금은 제2항 및 제3항에서 정한 보험료 납입지원기간동안 매년 보험
료 납입지원금 지급사유 발생해당일(지급사유 발생일 포함)에 지급합니다.
```
→ **This is premium support**, not diagnosis benefit

**Page 8** (Table of contents):
```
2-9 암진단Ⅱ(유사암제외)(갱신형)보장 특별약관 / 암진단Ⅱ(유사암제외)[맞춤고지Ⅱ]
```
→ **Lists coverage names only**, no benefit details

**Page 31** (Summary page):
```
암진단Ⅱ(유사암제외) 가입 후 90일간 보장 제외
```
→ **Overview table**, not actual약관 clause

**Missing**: Actual "유사암진단Ⅱ담보" special terms (특별약관) with:
- Section title: "유사암진단Ⅱ(양성뇌종양포함)담보 특별약관"
- Article 1: 보험금의 지급사유 (Payment trigger)
- Article 2: 보험금을 지급하지 않는 사유 (Exclusions)
- Article 3: 암/유사암 정의 및 범위 (Definitions)
- Waiting period clause: 보장개시일, 면책기간, 감액지급

---

## Comparison with Other Insurers

### Insurers with 3/3 FOUND (7사)

**N01 Example** (유사암진단비):
- 약관 SSOT contains:
  - Waiting period: "계약일부터 90일간 면책, 1년 미만 50% 감액지급"
  - Exclusions: "피보험자의 고의, 계약 전 발생..."
  - Subtype map: "갑상선암(C73), 기타피부암(C44), 제자리암(D00-D09)..."
- Result: 3/3 FOUND ✅

**N08 Example** (유사암 진단비(경계성종양)(1년50%)):
- 약관 SSOT contains:
  - Waiting period: "최초계약일부터 1년 미만 50% 감액"
  - Exclusions: "보장하지 않는 사유 제3조..."
  - Subtype map: "갑상선암, 기타피부암, 제자리암, 경계성종양 범위..."
- Result: 3/3 FOUND ✅

### N09 (0/3 FOUND)

**약관 SSOT status**:
- ❌ NO waiting period clause for "유사암진단Ⅱ담보"
- ❌ NO exclusion clause for "유사암진단Ⅱ담보"
- ❌ NO subtype definition clause for "유사암진단Ⅱ담보"

**Proposal document**:
- ✅ Confirms benefit exists with basic details (coverage, amount, waiting period mention)
- ✅ Shows it's a cash diagnosis benefit
- ⚠️ Lacks detailed약관-level terms required for evidence generation

---

## Why This Is NOT a Gate/Profile Issue

### 1. Gates Are Working Correctly
- GATE 1 (anchor): 221/349 chunks matched ✅
- GATE 2 (hard negative): Filters inappropriate contexts ✅
- GATE 3 (section negative): Filters premium support contexts ✅
- GATE 4 (diagnosis signal): Requires payment context ✅
- GATE 5 (coverage name lock): Token matching works ✅
- GATE 6 (slot terms): Requires waiting/exclusion/subtype terms ✅
- GATE 7 (slot negatives): Filters contamination ✅

### 2. Profile Is Correctly Defined
```python
A4210_PROFILE = {
    "anchor_keywords": ["유사암", "유사암진단", "유사암진단비", "유사 암", "유사암 진단", "유사암 진단비"],
    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책"],
        "subtype_coverage_map": ["제자리암", "경계성", "갑상선암", "기타피부암", "범위"]
    }
    # ... (other fields)
}
```

### 3. The Issue Is Missing Source Data
- Other 7 insurers have complete약관 clauses → 3/3 FOUND
- N09 lacks약관 clauses → 0/3 FOUND
- Gates/profile would work IF약관 clauses existed in SSOT

---

## Recommended Action

### ✅ Implemented: Mark N09-A4210 as DEPRECATED

**Reason**: "약관 SSOT incomplete - requires document re-parsing"

**SQL**:
```sql
UPDATE coverage_mapping_ssot
SET status='DEPRECATED', updated_at=CURRENT_TIMESTAMP
WHERE ins_cd='N09' AND coverage_code='A4210' AND as_of_date='2025-11-26';
```

**Status after update**:
| ins_cd | coverage_name | status |
|--------|---------------|--------|
| N01 | 유사암진단비 | ACTIVE |
| N02 | 4대유사암진단비(경계성종양) | ACTIVE |
| N03 | 갑상선암·기타피부암·유사암진단비 | ACTIVE |
| N05 | 유사암진단비 | ACTIVE |
| N08 | 유사암 진단비(경계성종양)(1년50%) | ACTIVE |
| **N09** | **유사암진단Ⅱ(양성뇌종양포함)담보** | **DEPRECATED** |
| N10 | 유사암진단비 | ACTIVE |
| N13 | 유사암진단비Ⅱ(1년감액지급) | ACTIVE |

---

### Future Action (Optional): Investigate Document Parsing

**Scope**: Determine why N09 "유사암진단Ⅱ담보" special terms (특별약관) are missing from document_page_ssot

**Possible causes**:
1. PDF parsing error: Section not recognized during PDF extraction
2. Document structure anomaly: Special terms located in unexpected location
3. File missing: "유사암진단Ⅱ담보" 약관 not included in source PDF

**Constraint**: Investigation must NOT modify gates/profile or relax validation criteria

---

## Baseline Decision: 7-Insurer Freeze

### Final Baseline
- **Insurers**: N01, N02, N03, N05, N08, N10, N13 (7사)
- **Evidence slots**: FOUND=21/21 (7 insurers × 3 slots)
- **Contamination**: 0 rows
- **Compare table**: table_id=20
- **API**: ✅ Returns 7 insurers

### N09 Status
- **Mapping status**: DEPRECATED (not deleted)
- **Reason**: "약관 SSOT incomplete - benefit exists per proposal but lacks detailed약관 clauses for evidence generation"
- **Can be reactivated**: IF document_page_ssot is updated with complete약관 clauses

---

## Key Findings Summary

1. ✅ **Mapping is CORRECT**: N09 "유사암진단Ⅱ담보" is a valid diagnosis benefit (proven by proposal)
2. ❌ **약관 SSOT is INCOMPLETE**: Missing detailed benefit clauses required for evidence generation
3. ✅ **Gates/Profile are CORRECT**: Working as designed; issue is missing source data
4. 🔍 **Root cause**: document_page_ssot missing "유사암진단Ⅱ담보" special terms (특별약관)

**This is a DATA ISSUE, not a validation logic issue.**

---

## DoD Checklist

- [x] Verified benefit exists in proposal document
- [x] Attempted evidence generation with N09 (FAILED: 0/3)
- [x] Investigated약관 SSOT content (detailed clauses missing)
- [x] Compared with other insurers (all have complete약관)
- [x] Confirmed gates/profile working correctly
- [x] Marked N09-A4210 as DEPRECATED with reason documented
- [x] Regenerated evidence for 7 insurers (FOUND=21/21)
- [x] Created compare table (table_id=20)
- [x] Verified API returns 7 insurers

---

**STATUS**: N09-A4210 marked as DEPRECATED due to incomplete약관 SSOT ✅

**Last Verified**: 2026-01-16 17:57
