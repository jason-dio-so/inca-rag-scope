# STEP NEXT-67D-EXT: Profile Analysis - DB/Hanwha DETAIL Tables

**Date**: 2026-01-02
**Status**: ✅ ANALYSIS COMPLETE
**Goal**: Confirm detail_table existence and structure for DB (under40/over41) and Hanwha

---

## Executive Summary

**RESULT**: ✅ **Both DB and Hanwha have detail_table = true**

All 3 axes (db_under40, db_over41, hanwha) have explicit DETAIL tables with 보장(보상)내용 columns containing coverage descriptions.

**Key Findings**:
- **DB (both variants)**: Explicit column pattern (pages 7-9, 4 columns)
- **Hanwha**: Merged column pattern (pages 5-10, 5 columns)
- Both patterns already supported by Samsung implementation (STEP NEXT-67D-FINAL)

---

## 1. DB Under 40 Profile Analysis

**Profile Path**: `data/profile/db_proposal_profile_v3.json`
**Axis**: `db_under40`

### detail_table Configuration
```json
{
  "exists": true,
  "priority": 2,
  "pages": [7, 8, 9],
  "columns": {
    "coverage_name_and_desc": ["가입담보[만기/납기]"],
    "coverage_amount": ["가입금액(만원)"],
    "premium": ["보험료(원)"],
    "description": ["보장(보상)내용"]
  },
  "structure": {
    "row_count": "19-24 rows per page",
    "col_count": "4 columns",
    "header_pattern": "가입담보[만기/납기] | 가입금액(만원) | 보험료(원) | 보장(보상)내용"
  }
}
```

### Pattern Classification
**✅ EXPLICIT COLUMN PATTERN** (Same as Samsung pattern 2)

- Coverage name column: `가입담보[만기/납기]`
- Description column: `보장(보상)내용` (separate, explicit)
- Pages: 7, 8, 9
- Column count: 4

### Sample Evidence (Page 8, Table 0)
**Header Row**:
```
가입담보[만기/납기] | 가입금액(만원) | 보험료(원) | 보장(보상)내용
```

**Sample Row 1** (고액치료비암진단비):
```
고액치료비암진단비 | 1,000 | 3,020 | 피보험자가 보장개시일(계약일로부터 90일이 지난날의 다음날, 계약일 현재 보험나이 15세 미만 피보험자의 경우 1회 보험료를 받은 때) 이후에 고액치료비암으로 진단확정된 경우 보험가입금액 지급(최초 1회에 한함) ※ 고액치료비암 : 골 및 관절연골의 악성신생물(암)/ 뇌 및 중추신경계의 기타 부위의 악성신생물(암)/ 림프, 조혈 및 관련조직의 악성신생물(암)/ 식도의 악성신생물(암)/ 췌장의 악성신생물(암) (자세한 내용은 약관 참조)
```

**Sample Row 2** (암수술비):
```
암수술비(유사암제외)(최초1회한) | 500 | 7,225 | 보장개시일(계약일로부터 90일이 지난날의 다음날, 계약일 현재 보험나이 15세 미만 피보험자의 경우 1회 보험료를 받은 때)이후에 진단확정된 암(유사암제외)으로 수술시 가입금액의 지급 (수술1회한)
```

### Extraction Strategy
**✅ Use `detail_extractor.py` EXPLICIT COLUMN logic**

- Extract from column index 3 (`보장(보상)내용`)
- Match to summary table via coverage_name normalization
- Same logic as Samsung explicit column pattern

---

## 2. DB Over 41 Profile Analysis

**Profile Path**: `data/profile/db_proposal_profile_v3.json` (same file, variant: over41)
**Axis**: `db_over41`

### detail_table Configuration
**IDENTICAL to db_under40** (same PDF structure)

```json
{
  "exists": true,
  "priority": 2,
  "pages": [7, 8, 9],
  "columns": {
    "description": ["보장(보상)내용"]
  },
  "structure": {
    "col_count": "4 columns",
    "header_pattern": "가입담보[만기/납기] | 가입금액(만원) | 보험료(원) | 보장(보상)내용"
  }
}
```

### Pattern Classification
**✅ EXPLICIT COLUMN PATTERN** (Same as db_under40)

### Notes
- DB uses same PDF template for both under40/over41
- Only difference: coverage list and premium amounts
- DETAIL table structure: IDENTICAL

---

## 3. Hanwha Profile Analysis

**Profile Path**: `data/profile/hanwha_proposal_profile_v3.json`
**Axis**: `hanwha`

### detail_table Configuration
```json
{
  "exists": true,
  "priority": 2,
  "pages": [5, 6, 7, 8, 9, 10],
  "table_name_candidates": ["가입담보 및 보장내용"],
  "columns": {
    "coverage_name_and_desc": ["가입담보 및 보장내용"],
    "coverage_amount": ["가입금액"],
    "premium": ["보험료"],
    "payment_period": ["만기/납기"]
  },
  "structure": {
    "row_count": "15-23 rows per page",
    "col_count": "5 columns",
    "header_pattern": "가입담보 및 보장내용 | 가입금액 | 보험료 | 만기/납기"
  },
  "notes": "**CRITICAL**: '가입담보 및 보장내용' merged column에 담보명 + 보장설명문이 섞여 있음."
}
```

### Pattern Classification
**✅ MERGED COLUMN PATTERN** (Same as Samsung pattern 1)

- Merged column: `가입담보 및 보장내용`
- Coverage name + description in SAME column
- Pages: 5, 6, 7, 8, 9, 10
- Column count: 5

### Sample Evidence (Page 5, Table 1)
**Header Row**:
```
가입담보 및 보장내용 |  | 가입금액 | 보험료 | 만기/납기
```

**Sample Row** (보통약관 상해사망):
```
1 보통약관(상해사망)  | 1,000만원 | 590원 | 100세만기 / 20년납
보험기간 중 상해의 직접 결과로써 사망한 경우(질병으로 인한 사망은 제외) 보험가입금액 지급
```

**Multi-row structure**:
- Row 1: Coverage name + metadata
- Row 2+: Benefit description text

### Extraction Strategy
**✅ Use `detail_extractor.py` MERGED COLUMN logic**

- Parse merged column for coverage name pattern (row 1)
- Extract description from subsequent rows until next coverage name
- Same logic as Samsung merged column pattern

---

## 4. Pattern Comparison

| Axis | Pattern Type | Column Name | Pages | Col Count |
|------|--------------|-------------|-------|-----------|
| **db_under40** | EXPLICIT | `보장(보상)내용` | 7-9 | 4 |
| **db_over41** | EXPLICIT | `보장(보상)내용` | 7-9 | 4 |
| **hanwha** | MERGED | `가입담보 및 보장내용` | 5-10 | 5 |
| **samsung** (ref) | MERGED | `보장·보상내용` | 4-7 | 4 |

---

## 5. Implementation Readiness

### Existing Code Support (from STEP NEXT-67D-FINAL)

**File**: `pipeline/step1_summary_first/detail_extractor.py`

**Already Implemented**:
1. ✅ **Explicit Column Pattern** (lines 200-250)
   - Extract from dedicated description column
   - DB uses this pattern → **Ready to use**

2. ✅ **Merged Column Pattern** (lines 250-350)
   - Parse coverage name + description from same column
   - Hanwha uses this pattern → **Ready to use**

3. ✅ **Profile-Driven Selection** (lines 100-150)
   - Reads `detail_table.columns.description` to determine pattern
   - No hardcoding required

### Required Changes
**✅ ZERO CODE CHANGES NEEDED**

Both DB and Hanwha patterns already supported by existing Samsung implementation.

---

## 6. Verification Checklist

### DB (both under40/over41)
- [x] detail_table.exists = true
- [x] Pages identified (7-9)
- [x] Column structure matches explicit pattern
- [x] Sample rows contain full descriptions (not TOC/fragments)
- [x] Existing code supports pattern

### Hanwha
- [x] detail_table.exists = true
- [x] Pages identified (5-10)
- [x] Column structure matches merged pattern
- [x] Sample rows contain full descriptions
- [x] Existing code supports pattern

---

## 7. Expected Extraction Outcomes

### DB Under 40 (Estimate)
- Summary table: ~30-35 coverages (from pages 4-5, 7-9)
- DETAIL table: ~45-50 facts (from pages 7-9)
- Expected match rate: **≥ 85%** (based on Samsung 90%)

### DB Over 41 (Estimate)
- Summary table: ~30-35 coverages
- DETAIL table: ~45-50 facts
- Expected match rate: **≥ 85%**

### Hanwha (Estimate)
- Summary table: ~33 coverages (from page 3)
- DETAIL table: ~50-60 facts (from pages 5-10, merged rows)
- Expected match rate: **≥ 80%** (merged pattern may have more noise)

---

## 8. Risk Assessment

### LOW RISK ✅
1. **Code Reuse**: Both patterns already verified on Samsung
2. **Profile-Driven**: No insurer hardcoding required
3. **Constitutional Compliance**: All deterministic (NO LLM/OCR/Vector)

### MEDIUM RISK ⚠️
1. **Coverage Name Variants**: DB/Hanwha may have different naming conventions
   - Mitigation: Use existing normalization logic (step2_sanitize_scope)
2. **Merged Column Noise** (Hanwha only): May include exclusion clauses
   - Mitigation: Existing filters for disclaimer patterns (※, ◆, 보험금 지급하지 않는)

---

## 9. Next Steps (PROCEED TO EXECUTION)

**STEP 1**: Run Step1 extraction for all 3 axes ✅ READY
```bash
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer db_under40
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer db_over41
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer hanwha
```

**STEP 2**: Verify proposal_detail_facts existence
```bash
grep -c '"proposal_detail_facts"' data/scope_v3/db_under40_step1_raw_scope_v3.jsonl
grep -c '"proposal_detail_facts"' data/scope_v3/db_over41_step1_raw_scope_v3.jsonl
grep -c '"proposal_detail_facts"' data/scope_v3/hanwha_step1_raw_scope_v3.jsonl
```

**STEP 3**: Run Step2 + Step5 for customer_view integration
```bash
# (Step2-a, Step2-b, Step3, Step4 already completed for all insurers)
python -m pipeline.step5_build_cards.build_cards --insurer db_under40
python -m pipeline.step5_build_cards.build_cards --insurer db_over41
python -m pipeline.step5_build_cards.build_cards --insurer hanwha
```

**STEP 4**: Verify customer_view.benefit_description quality
```bash
# Sample A4200_1 (암진단비) or equivalent coverage
```

---

## Status

**PROFILE ANALYSIS: ✅ COMPLETE**

Ready to proceed with Step1 execution (Task 4).

---

**Constitutional Compliance**:
- ✅ NO LLM usage (all analysis from profile JSON)
- ✅ NO insurer hardcoding (profile-driven only)
- ✅ NO new patterns required (reuse Samsung implementation)
