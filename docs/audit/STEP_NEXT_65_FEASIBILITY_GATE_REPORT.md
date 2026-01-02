# STEP NEXT-65: FEASIBILITY GATE REPORT

## Executive Summary

**GATE STATUS**: ❌ **BLOCKED**

The STEP NEXT-65 directive cannot be executed as specified due to a critical data availability gap:

**Finding**: ALL insurers (13/13) have `detail_table.exists = false`
**Impact**: DETAIL table "보장(보상)내용" field does not exist in any insurer profile
**Directive Requirement**: "coverage_description → detail_table['보장(보상)내용']"
**Current Reality**: NO detail_table data has been extracted by Step1

---

## Investigation Results

### 1. Proposal Profile Analysis

Checked all v3 proposal profiles in `data/profile/*_v3.json`:

| Insurer | detail_table.exists | summary_table.exists |
|---------|---------------------|----------------------|
| samsung | ❌ false | ✅ true |
| hanwha | ❌ false | ✅ true |
| kb | ❌ false | ✅ true |
| hyundai | ❌ false | ✅ true |
| heungkuk | ❌ false | ✅ true |
| lotte | ❌ false | ✅ true |
| lotte_male | ❌ false | ✅ true |
| lotte_female | ❌ false | ✅ true |
| meritz | ❌ false | ✅ true |
| db | ❌ false | ✅ true |
| db_under40 | ❌ false | ✅ true |
| db_over41 | ❌ false | ✅ true |

**Result**: 0/12 insurers have DETAIL tables

### 2. Current proposal_facts Structure

From `data/compare/samsung_coverage_cards.jsonl` (line 7, A4200_1 암진단비):

```json
{
  "proposal_facts": {
    "coverage_amount_text": "3,000만원",
    "premium_text": "40,620",
    "period_text": "20년납 100세만기\nZD8",
    "payment_method_text": null,
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 2,
        "row_index": 4,
        "raw_row": ["", "암 진단비(유사암 제외)", "3,000만원", "40,620", "20년납 100세만기\nZD8"]
      }
    ]
  }
}
```

**Current Source**: SUMMARY table only (담보명, 가입금액, 보험료, 납입기간)
**Missing**: 보장(보상)내용 field (담보 상세 설명 문장)

### 3. Samsung Proposal Profile Structure

From `data/profile/samsung_proposal_profile_v3.json`:

```json
{
  "summary_table": {
    "exists": true,
    "pages": [2, 3],
    "column_map": {
      "coverage_name": 1,
      "coverage_amount": 2,
      "premium": 3,
      "period": 4
    }
  },
  "detail_table": {
    "exists": false,
    "pages": []
  }
}
```

**Note**: No "보장(보상)내용" column in summary_table

---

## Directive vs. Reality Gap

### Directive Requirements (STEP NEXT-65)

Section 3-2 states:

```
coverage_name        → summary_table
coverage_amount      → summary_table
premium              → summary_table
payment_period       → summary_table

coverage_description → detail_table["보장(보상)내용"]  ⚠️ KEY REQUIREMENT
```

Section 3-2 Warning:
```
⚠️ 중요:
    •    보장내용은 summary에서 절대 추출하지 말 것
    •    DETAIL table이 존재하는데도 쓰지 않으면 실패로 간주
```

### Current System Reality

- ✅ `coverage_name`, `coverage_amount`, `premium`, `period` → available from summary_table
- ❌ `coverage_description` → **NO source available** (detail_table does not exist)

### Constitutional Constraint

STEP NEXT-65 Section 1 states:

```
절대 규칙 (Constitutional Rules):
    •    ❌ Step1 / Step2 재실행 금지
```

**Contradiction**:
- DETAIL table extraction would require Step1 rewrite → violates constitutional rule
- Current Step1 (`pipeline/step1_summary_first/`) only extracts SUMMARY tables
- Profile builder (`profile_builder_v3.py`) has `detail_table.exists = false` hardcoded (no detection logic)

---

## Root Cause Analysis

### Why NO DETAIL tables?

1. **Step1 Profile Builder** (`pipeline/step1_summary_first/profile_builder_v3.py`):
   - Only detects SUMMARY tables (보장가입현황)
   - No DETAIL table detection logic implemented
   - `detail_table` field always returns `{"exists": false, "pages": []}`

2. **Step1 Extractor** (`pipeline/step1_summary_first/extractor_v3.py`):
   - Only reads `summary_table` signatures from profile
   - No code to extract DETAIL tables even if profile had them

3. **Historical Context**:
   - Step1 was designed for "summary-first" extraction (file name reflects this)
   - DETAIL table extraction was likely never implemented
   - No evidence of prior DETAIL table data in any STEP NEXT- audit logs

---

## Impact Assessment

### What CAN'T Be Done (as specified in directive)

1. ❌ Extract `coverage_description` from DETAIL table "보장(보상)내용" field
2. ❌ Enforce evidence priority: **proposal DETAIL** → SUMMARY → business → summary → policy
3. ❌ Populate `customer_view.benefit_description` from DETAIL table
4. ❌ Validate with "Samsung A4200_1 DETAIL 문장" test case

### What CAN Be Done (alternative interpretation)

1. ✅ Add `customer_view` schema to CoverageCard
2. ✅ Extract `benefit_description` from **existing evidence sources**:
   - 사업방법서 (business method book) - often has brief descriptions
   - 상품요약서 (product summary) - customer-facing summaries
   - 약관 (policy) - legal coverage definitions
3. ✅ Implement rule-based `payment_type` / `limit_conditions` / `exclusion_notes` extraction
4. ✅ Enforce evidence priority: **가입설계서 (SUMMARY)** → business → summary → policy

---

## Recommended Path Forward

### Option A: Reinterpret Directive (NO Step1 changes)

**Approach**:
- Use existing `proposal_facts` as "가입설계서 evidence" (already highest priority in Step5:67)
- Extract `benefit_description` from **사업방법서 / 상품요약서** (not proposal DETAIL)
- Evidence priority becomes: **proposal (SUMMARY)** → business → summary → policy

**Pros**:
- ✅ No Step1/Step2 re-run needed (respects constitutional rule)
- ✅ Leverages existing evidence pipeline
- ✅ Customer-view schema still valuable
- ✅ Can implement payment_type/limit_conditions extraction

**Cons**:
- ❌ Proposal evidence won't have "보장내용 설명 문장" (only 금액/보험료/기간)
- ❌ Doesn't match directive's vision

**Code Changes**:
1. Add `customer_view` to CoverageCard schema (core/compare_types.py)
2. Extract `benefit_description` from business/summary evidence (Step5)
3. Implement rule-based payment_type/limit_conditions (Step5)

---

### Option B: Implement DETAIL Table Extraction (violates constitutional rule)

**Approach**:
- Rewrite Step1 profile_builder_v3.py to detect DETAIL tables
- Rewrite Step1 extractor_v3.py to extract "보장(보상)내용" field
- Re-run Step1 for all insurers
- Re-run Step2-5 for all insurers

**Pros**:
- ✅ Matches directive's vision exactly
- ✅ Richer proposal evidence (includes descriptions)

**Cons**:
- ❌ **VIOLATES CONSTITUTIONAL RULE**: "❌ Step1 / Step2 재실행 금지"
- ❌ Requires full pipeline re-execution (Step1-5 for 12 insurers)
- ❌ High risk of data regression
- ❌ Unknown: do all proposal PDFs even HAVE detail tables?

---

### Option C: Partial Implementation + Future Work

**Phase 1 (Now)**: Implement customer_view with existing data
- Add `customer_view` schema
- Use business/summary for `benefit_description`
- Implement payment_type/limit_conditions extraction
- Document as "STEP NEXT-65 Phase 1"

**Phase 2 (Future)**: DETAIL table extraction (when allowed)
- Requires lifting Step1 freeze
- Profile builder rewrite
- Extractor rewrite
- Full re-run

---

## Decision Required

**Question for User**:

1. Should we proceed with **Option A** (reinterpret directive, no Step1 changes)?
2. Should we proceed with **Option B** (violate const constitutional rule, implement DETAIL extraction)?
3. Should we proceed with **Option C** (phased approach)?
4. Should we halt and wait for clarification on intent?

---

## Current Code Status

### Already Implemented (accidentally aligned with Option A)

- ✅ Step5 already prioritizes 가입설계서 evidence (line 67-110 in build_cards.py)
- ✅ `proposal_facts` already in CoverageCard (line 54 in core/compare_types.py)
- ✅ Evidence diversity selection already working

### Not Implemented (requires work for any option)

- ❌ `customer_view` schema in CoverageCard
- ❌ `benefit_description` extraction logic
- ❌ `payment_type` / `limit_conditions` / `exclusion_notes` rule-based extraction

---

## Audit Trail

- **Checked**: 12 insurer profiles (data/profile/*_v3.json)
- **Result**: 0/12 have detail_table.exists = true
- **Checked**: Step1 codebase (pipeline/step1_summary_first/)
- **Result**: No DETAIL table detection/extraction logic exists
- **Checked**: Current coverage_cards (data/compare/*.jsonl)
- **Result**: proposal_facts contain SUMMARY fields only

---

## Conclusion

STEP NEXT-65 as written **assumes a capability that does not exist**: DETAIL table extraction.

**Gate Decision**: ❌ **BLOCKED** - cannot proceed with directive as specified.

**Next Action**: Await user decision on Option A / B / C.

---

**Generated**: 2026-01-02 (STEP NEXT-65 feasibility audit)
**Status**: Awaiting decision
