# A4210 N09 Policy Text Gap Report

**Date**: 2026-01-16
**Coverage**: A4210 (유사암진단비)
**Insurer**: N09 (현대해상)
**Objective**: Verify if "유사암진단Ⅱ담보" special terms exist in document_page_ssot
**Result**: ⛔ **POLICY_TEXT_MISSING** (약관 PDF 누락)

---

## Executive Summary

**판정**: N09 "유사암진단Ⅱ담보" 특별약관 본문이 document_page_ssot에 존재하지 않음.

**Evidence**:
- 목차에 "유사암진단Ⅱ보장 특별약관" 명시 (page 257 예정)
- Page 257에는 다른 약관 (기타피부암/갑상선암/제자리암/경계성종양 진단비) 있음
- 실제 "유사암진단Ⅱ담보" 제1조 (보험금 지급사유) 없음
- 약관 SSOT에서 찾을 수 있는 것: "보험료납입지원(유사암진단)" (premium support) only

**Result**: 약관 PDF 누락 → Evidence generation 불가능

---

## Background: Investigation Directive

사용자 지시사항:
1. 7사 baseline 유지 (FROZEN 상태)
2. N09 ACTIVE 복원하되 8사 Freeze 금지
3. document_page_ssot에서 모든 패턴 검색
4. 약관 본문 누락 시 즉시 중단
5. 대응 방안 제시

---

## Document Overview

### N09 Document Inventory (as_of_date=2025-11-26)

| doc_type | page_count | Description |
|----------|------------|-------------|
| 약관 | 1,283 | Policy terms (special terms) |
| 사업방법서 | 142 | Business plan document |
| 요약서 | 111 | Summary booklet |
| 가입설계서 | 11 | Proposal document |

**Total**: 1,547 pages in document_page_ssot

---

## Pattern Search Statistics

### Coverage-Related Keywords

| Pattern | 약관 | 사업방법서 | 요약서 | 가입설계서 | Total |
|---------|------|-----------|-------|-----------|-------|
| 유사암진단Ⅱ | 8 | 16 | 15 | 2 | 41 |
| 유사암진단 (all) | 14 | 22 | 22 | 2 | 60 |
| 기타피부암 | 280 | 9 | 28 | 4 | 321 |
| 갑상선암 | 344 | 32 | 38 | 6 | 420 |
| 제자리암 | 93 | 0 | 12 | 4 | 109 |
| 경계성종양 | 94 | 0 | 13 | 4 | 111 |

### Evidence-Required Keywords

| Pattern | 약관 | 사업방법서 | 요약서 | 가입설계서 | Total |
|---------|------|-----------|-------|-----------|-------|
| 보장개시 | 485 | 2 | 30 | 6 | 523 |
| 면책 | 20 | 19 | 22 | 0 | 61 |
| 90일 | 170 | 17 | 23 | 2 | 212 |
| 감액 | 17 | 1 | 5 | 2 | 25 |
| 지급률 | 36 | 0 | 4 | 1 | 41 |
| 보장하지 | 414 | 0 | 1 | 0 | 415 |
| 지급하지 | 628 | 2 | 5 | 1 | 636 |

**Interpretation**:
- ✅ Keywords exist in adequate quantity
- ✅ Terms spread across multiple doc_types
- ⚠️ But NO pages combine "유사암진단Ⅱ" + "제1조" + "보험금 지급사유"

---

## Context Analysis: 약관 Pages with "유사암진단"

### Combined Search Results

| Context Type | Page Count | Description |
|--------------|------------|-------------|
| WITH 보장개시 | 4 | Contains waiting period terms |
| WITH 면책 | 5 | Contains exclusion terms |
| WITH 보장하지 | 1 | Contains non-covered terms |
| WITH 지급사유 | 6 | Contains payment trigger terms |
| ONLY 유사암진단 | 14 | Total pages mentioning "유사암진단" |

---

## Classification Results

### Category A: Diagnosis Benefit Terms (진단비 본문)

**Status**: ⛔ **NOT FOUND**

**Expected**: Pages with all of:
- Title: "유사암진단Ⅱ보장 특별약관"
- Article 1 (제1조): 보험금의 지급사유
- Article 2 (제2조): 보험금 지급에 관한 세부규정
- Article 3 (제3조): 보험금을 지급하지 않는 사유
- Definitions: 유사암 정의 및 범위 (기타피부암, 갑상선암, 제자리암, 경계성종양)

**Actual**: ZERO pages matching this pattern in document_page_ssot

---

### Category B: Premium Support Benefit (보험료납입지원)

**Status**: ✅ FOUND (Page 777)

**Sample** (page 777):
```
제2조 (보험금의 지급사유)
① 회사는 피보험자가 보험기간 중에 '유사암'으로 진단확정된 경우에는 최초 1회에 한하여
아래의 금액을 보험수익자에게 보험금으로 지급합니다.

단, 보험료 납입지원금은 제2항 및 제3항에서 정한 보험료 납입지원기간동안 매년 보험료
납입지원금 지급사유 발생해당일(지급사유 발생일 포함)에 지급합니다.
```

**Classification**: ❌ Premium waiver benefit, NOT diagnosis benefit

**Characteristics**:
- Benefit name: "보험료납입지원(유사암진단)특별약관"
- Payment type: Monthly premium waiver (not lump sum cash)
- Duration: Annual payment during premium payment period
- Prevalence: 148/349 chunks (42%) in N09 A4210 coverage_chunk

---

### Category C: Table of Contents / Summary Pages (목차/요약표)

**Status**: ✅ FOUND (Pages 8, 31, 53, 89, 117, 118, 1269)

**Page 8** (Table of Contents):
```
2-10 유사암진단Ⅱ보장 특별약관 / 유사암진단Ⅱ(갱신형)보장 특별약관 /
유사암진단Ⅱ[맞춤고지Ⅱ]보장 특별약관
```

**Page 1269** (Index):
```
유사암진단Ⅱ보장 특별약관/ 유사암진단Ⅱ(갱신형)보장 특별약관/
유사암진단Ⅱ[맞춤고지Ⅱ]보장 특별약관/
유사암진단Ⅱ[맞춤고지Ⅱ](갱신형)보장 특별약관··························257
```

**Critical Finding**: Index references page 257, but actual content missing

**Page 31, 53, 89** (Summary tables):
```
유사암진단Ⅱ, 유사암진단Ⅱ(갱신형)
최초계약일부터 1년미만 50% 감액지급
```

**Classification**: ✅ TOC/Summary only (no detailed terms)

---

### Category D: Exclusion Context ("유사암제외" 언급)

**Status**: ✅ FOUND (Multiple pages)

**Sample** (page 31):
```
암진단Ⅱ(유사암제외) 가입 후 90일간 보장 제외
```

**Sample** (page 257):
```
회사는 피보험자가 이 특별약관의 보험기간 중에 '기타피부암','갑상선암','제자리암'
또는 '경계성종양'으로 진단 확정된 경우에는 각각 최초 1회에 한하여 아래의 금액을
보험수익자에게 보험금으로 지급합니다.
```

**Classification**: ✅ Different coverage (기타피부암/갑상선암/제자리암/경계성종양 진단비)

**Note**: Page 257 contains diagnosis benefit for individual similar cancer types, NOT "유사암진단Ⅱ" (combined similar cancer diagnosis)

---

## Root Cause: Policy Text Missing

### Evidence Chain

**1. Table of Contents References Page 257**

Index (page 1269) states:
```
유사암진단Ⅱ[맞춤고지Ⅱ](갱신형)보장 특별약관··························257
```

**2. Page 257 Contains Different Coverage**

Actual content (page 257):
```
회사는 피보험자가 이 특별약관의 보험기간 중에 '기타피부암','갑상선암','제자리암'
또는 '경계성종양'으로 진단 확정된 경우...
```

This is 2-8 "암진단Ⅱ(유사암제외)보장 특별약관", NOT 2-10 "유사암진단Ⅱ보장 특별약관"

**3. Search for Article 1 (제1조) Yields Zero Results**

Query:
```sql
SELECT * FROM document_page_ssot
WHERE ins_cd='N09' AND doc_type='약관'
  AND raw_text ~* '유사암진단(Ⅱ|II|2).*특별약관'
  AND raw_text ~* '제1조.*보험금.*지급사유';
```

**Result**: 0 rows

**4. Only Premium Support Benefit Found**

Page 777 contains "보험료납입지원(유사암진단)" NOT "유사암진단Ⅱ담보"

---

### Possible Causes

**Theory 1: PDF Parsing Error**
- "유사암진단Ⅱ담보" special terms section skipped during PDF extraction
- Page numbering mismatch between TOC and actual content
- Possible OCR failure for specific pages

**Theory 2: Missing PDF File**
- "유사암진단Ⅱ담보" special terms stored in separate PDF file
- File not included in original data/sources directory
- Proposal document references benefit that doesn't exist in policy terms

**Theory 3: Document Structure Anomaly**
- Special terms located in unexpected section of약관
- Non-standard formatting prevented pattern matching
- Merged with other coverage terms (less likely given TOC clarity)

---

## Impact Analysis

### Evidence Generation Requirements

**Profile requires 3 slots**:
1. `waiting_period`: [면책, 보장개시, 책임개시, 90일, 감액, 지급률]
2. `exclusions`: [제외, 보장하지, 지급하지, 보상하지, 면책]
3. `subtype_coverage_map`: [제자리암, 경계성, 갑상선암, 기타피부암, 범위]

**Current SSOT status** (N09):
- ❌ NO pages with waiting period clause for "유사암진단Ⅱ담보"
- ❌ NO pages with exclusion clause for "유사암진단Ⅱ담보"
- ❌ NO pages with subtype definitions for "유사암진단Ⅱ담보"

**Conclusion**: Evidence generation IMPOSSIBLE without약관 source text

---

## Comparison with Other Insurers (7사)

### Successful Insurers (21/21 FOUND)

| ins_cd | Coverage Name | 약관 Status | Evidence |
|--------|---------------|-------------|----------|
| N01 | 유사암진단비 | ✅ Complete약관 | 3/3 FOUND |
| N02 | 4대유사암진단비(경계성종양) | ✅ Complete약관 | 3/3 FOUND |
| N03 | 갑상선암·기타피부암·유사암진단비 | ✅ Complete약관 | 3/3 FOUND |
| N05 | 유사암진단비 | ✅ Complete약관 | 3/3 FOUND |
| N08 | 유사암 진단비(경계성종양)(1년50%) | ✅ Complete약관 | 3/3 FOUND |
| N10 | 유사암진단비 | ✅ Complete약관 | 3/3 FOUND |
| N13 | 유사암진단비Ⅱ(1년감액지급) | ✅ Complete약관 | 3/3 FOUND |

**Each successful insurer has**:
- Complete special terms (특별약관) in약관 SSOT
- Article 1 (보험금 지급사유)
- Article 2 (보험금 지급에 관한 세부규정)
- Article 3 (보험금을 지급하지 않는 사유)
- Definitions (유사암 정의 및 범위)

---

### N09 Status

| ins_cd | Coverage Name | 약관 Status | Evidence |
|--------|---------------|-------------|----------|
| **N09** | **유사암진단Ⅱ(양성뇌종양포함)담보** | **❌ 약관 본문 누락** | **0/3 FOUND** |

**What N09 has**:
- ✅ Proposal document proof (가입설계서 page 5)
- ✅ TOC/Index references (pages 8, 1269)
- ✅ Premium support약관 (page 777)
- ❌ Actual "유사암진단Ⅱ담보" special terms

---

## Recommended Actions

### 대응 1 (권장): PDF 재파싱 및 SSOT 재적재

**Scope**: Locate and re-parse missing "유사암진단Ⅱ담보" special terms

**Steps**:
1. Check `data/sources` for N09 original PDF files
2. Search for separate PDF containing "유사암진단Ⅱ보장 특별약관"
3. Verify file naming patterns (e.g., separate rider terms file)
4. Re-parse complete약관 using `tools/pdf_to_json_ssot.py`
5. Reload document_page_ssot for N09
6. Re-run evidence generation

**Expected result**: FOUND=24/24 (8 insurers × 3 slots)

---

### 대응 2 (임시/SSOT 준수): NOT_FOUND 기록

**Scope**: Mark N09 evidence slots as NOT_FOUND with reason=POLICY_TEXT_MISSING

**Implementation**:
```sql
-- Create NOT_FOUND evidence slots for N09
INSERT INTO evidence_slot
(ins_cd, coverage_code, as_of_date, slot_key, status, reason, excerpt)
VALUES
('N09', 'A4210', '2025-11-26', 'waiting_period', 'NOT_FOUND', 'POLICY_TEXT_MISSING', NULL),
('N09', 'A4210', '2025-11-26', 'exclusions', 'NOT_FOUND', 'POLICY_TEXT_MISSING', NULL),
('N09', 'A4210', '2025-11-26', 'subtype_coverage_map', 'NOT_FOUND', 'POLICY_TEXT_MISSING', NULL);
```

**Status**:
- N09 mapping remains ACTIVE (benefit exists per proposal)
- Evidence generation skipped (약관 SSOT incomplete)
- 7사 baseline remains FROZEN (N01,N02,N03,N05,N08,N10,N13)
- 8사 Freeze prohibited until N09 resolved

---

## Next Steps

### Immediate Action (Recommended)

1. **Verify source PDF files** (`data/sources/N09/`)
   - List all PDF files for N09
   - Check for separate rider terms document
   - Verify file completeness

2. **If PDF found**: Re-parse and reload
   ```bash
   python3 tools/pdf_to_json_ssot.py --ins_cd N09 --doc_type 약관 --pdf_path [PATH]
   python3 tools/load_to_ssot.py --ins_cd N09 --reload
   ```

3. **If PDF missing**: Request source document from client
   - Specify: "유사암진단Ⅱ보장 특별약관" (page 257 per index)
   - Provide proposal evidence (page 5) as proof of benefit existence

4. **After resolution**: Re-run A4210 pipeline for 8 insurers
   ```bash
   python3 tools/run_db_only_coverage.py \
     --coverage_code A4210 --as_of_date 2025-11-26 \
     --ins_cds N01,N02,N03,N05,N08,N09,N10,N13 \
     --stage evidence
   ```

5. **Expected result**: FOUND=24/24 → Proceed with 8사 Freeze

---

## DoD Checklist

- [x] Queried all doc_types for pattern statistics
- [x] Classified results into A/B/C/D categories
- [x] Verified 약관 본문 missing for "유사암진단Ⅱ담보"
- [x] Confirmed TOC references page 257 but content missing
- [x] Documented premium support benefit (page 777) as different coverage
- [x] Compared with 7 successful insurers
- [x] Provided recommended actions
- [x] Specified completion condition (FOUND=24/24 for 8사 Freeze)

---

**STATUS**: Policy text gap confirmed ⛔ — N09 "유사암진단Ⅱ담보" 약관 본문 누락

**Freeze Status**: 7사 baseline FROZEN (table_id=20) / 8사 Freeze 금지

**Last Verified**: 2026-01-16 18:10
