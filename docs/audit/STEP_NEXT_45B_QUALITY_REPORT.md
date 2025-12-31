# STEP NEXT-45-B: Quality Report v2 (Summary-First Redesign)

**Date**: 2025-12-31
**Status**: ⚠️ **PARTIAL IMPLEMENTATION** (Not Ready for Production)
**Scope**: Zero-base redesign of Step1 with summary-first SSOT + multi-PDF reader

---

## Executive Summary

**Result**: ❌ **Quality Regression Detected** (Not Ready to Deprecate Baseline)

| Metric | Baseline (44-γ-2) | V2 (45-B) | Status |
|--------|-------------------|-----------|--------|
| Insurers with data | 8/8 | 7/8 (KB failed) | ❌ REGRESSION |
| Total coverages | 339 | 148 | ❌ -56% |
| Samsung coverage count | 73 | 8 | ❌ -89% |
| Hyundai coverage count | 38 | 1 | ❌ -97% |
| DB coverage count | 35 | 44 | ⚠️ +26% (over-extraction?) |

**Verdict**: Summary-first approach is directionally correct, but implementation needs significant refinement before production readiness.

---

## 1. Coverage Count Comparison (Baseline vs V2)

### 1.1 By Insurer

| Insurer | Baseline (44-γ-2) | V2 (45-B) | Delta | Delta % | Status |
|---------|-------------------|-----------|-------|---------|--------|
| Samsung | 73 | 8 | -65 | -89% | ❌ CRITICAL |
| Meritz | 36 | 10 | -26 | -72% | ❌ CRITICAL |
| KB | 33 | 0 | -33 | -100% | ❌ CRITICAL (no summary table) |
| Hanwha | 74 | 32 | -42 | -57% | ❌ CRITICAL |
| Hyundai | 38 | 1 | -37 | -97% | ❌ CRITICAL |
| Lotte | 44 | 30 | -14 | -32% | ❌ HIGH |
| Heungkuk | 39 | 23 | -16 | -41% | ❌ HIGH |
| DB | 35 | 44 | +9 | +26% | ⚠️ SUSPICIOUS |

**Total**: 339 (baseline) → 148 (v2) = **-56% coverage loss**

### 1.2 Hard Gate Violations (Section 6.3)

**Gate 1**: "Summary table 존재 보험사: 주요 fact가 summary 기반이 아니면 FAIL"
- Status: ✅ PASS (all 7/8 extracted from summary)

**Gate 2**: "보험사별 담보 수 급감/급증 FAIL"
- Status: ❌ **FAIL** (all 7 insurers show -32% to -97% drops)

**Gate 3**: "evidence 없는 row 존재 시 FAIL"
- Status: ✅ PASS (all rows have evidences)

---

## 2. Root Cause Analysis

### 2.1 Samsung (-89%, 73→8)

**Issue**: Extractor only reading **first few data rows** from summary table

**Evidence**:
- Profile correctly detected 2 summary tables (pages 2-3) with 31 + 18 rows
- Extractor only extracted 8 facts total
- Likely cause: Header row detection skipping too many rows

**Fix Required**:
- Improve `_detect_header_rows()` heuristic
- Verify table extraction reads ALL data rows, not just first N

### 2.2 Hyundai (-97%, 38→1)

**Issue**: Severe under-extraction, only 1 fact from 2 summary tables

**Evidence**:
- Profile detected 2 summary tables (pages 2-3)
- Column map auto-detection may have failed
- Header row detection likely skipped all data rows

**Fix Required**:
- Debug column map detection for Hyundai PDF
- Verify header row detection doesn't skip data rows

### 2.3 KB (-100%, 33→0)

**Issue**: No summary table detected by profile builder

**Evidence**:
- Profile: `"summary_table": { "exists": false }`
- Baseline (44-γ-2) successfully extracted 33 coverages
- STEP NEXT-44D profile report states KB should have summary tables on pages 2-4

**Fix Required**:
- Relax summary table detection rules in profile builder
- KB may use different header keywords than current detection rules

### 2.4 DB (+26%, 35→44)

**Issue**: Possible over-extraction (noise rows)

**Evidence**:
- 9 extra coverages compared to baseline
- May include header rows, totals, disclaimers as coverages
- `_is_noise()` filter may be too permissive

**Fix Required**:
- Strengthen noise filtering (reject totals, disclaimers, merged headers)
- Review extracted rows for false positives

---

## 3. Summary-First Architecture Assessment

### 3.1 What Worked ✅

**Multi-PDF Reader**:
- Successfully implemented pdfplumber + PyMuPDF dual-reader architecture
- Quality-based reader selection (quality score metric)
- All 8 PDFs successfully parsed

**Profile Builder**:
- Automatic profile generation (no manual writing)
- Evidence-backed detection (page + snippet + table dimensions)
- Structural risk identification (merged headers, fragmentation)

**Summary-First SSOT Contract**:
- Clear layer discipline (Step1 = raw text only, no inference)
- Schema contract enforced (coverage_amount_text as-is, no parsing)
- Summary table prioritization logic implemented

### 3.2 What Needs Refinement ❌

**Profile Builder Detection Rules**:
- Too strict: KB summary table not detected (should exist per 44-D)
- May need keyword variations for different insurers
- Row count threshold (10+ rows) may be too high for some insurers

**Extractor Table Reading**:
- Header row detection too aggressive (skipping data rows)
- Column map auto-detection failing for some insurers (Hyundai, Samsung)
- Not reading all rows in multi-row summary tables

**Noise Filtering**:
- Too permissive: extracting totals, disclaimers (Samsung row 7-8)
- Too restrictive: may be skipping valid coverages (Samsung, Hyundai)

---

## 4. Summary vs Detail Metrics (Section 6.2)

### 4.1 Summary Table Usage

| Insurer | Summary Exists | Summary Pages | Signatures | Facts Extracted | Source |
|---------|----------------|---------------|------------|-----------------|--------|
| Samsung | ✅ Yes | [2, 3] | 2 | 8 | Summary |
| Meritz | ✅ Yes | [3, 4] | 2 | 10 | Summary |
| KB | ❌ No | [] | 0 | 0 | N/A (failed) |
| Hanwha | ✅ Yes | [3] | 1 | 32 | Summary |
| Hyundai | ✅ Yes | [2, 3] | 2 | 1 | Summary |
| Lotte | ✅ Yes | [2] | 1 | 30 | Summary |
| Heungkuk | ✅ Yes | [7] | 1 | 23 | Summary |
| DB | ✅ Yes | [8, 9] | 2 | 44 | Summary |

**Summary-Based Extraction Rate**: 100% (7/7 successful insurers used summary, 0 used detail fallback)

### 4.2 Fact Completeness (V2 Only)

Sample check (3 insurers):

**Hanwha** (32 facts):
- coverage_amount_text fill rate: 100% (32/32)
- premium_amount_text fill rate: 100% (32/32)
- payment_period_text fill rate: 100% (32/32)
- evidences fill rate: 100% (32/32)

**Lotte** (30 facts):
- (TBD - needs manual inspection)

**DB** (44 facts):
- (TBD - needs manual inspection for over-extraction)

---

## 5. DoD (Definition of Done) Checklist

From STEP NEXT-45-B Section 10:

- ✅ Profile이 수동 작성이 아닌 자동 생성 산출물
- ✅ Step1이 summary-first SSOT 구조로 동작
- ✅ 8개 보험사 전체 재실행 완료
- ✅ Quality Report v2 생성
- ❌ **기존 Step1 폐기 조건 명시** → NOT MET (quality regression detected)

---

## 6. Deprecation Rule Assessment (Section 8)

**Conditions for Deprecating Baseline**:
1. ❌ 새 Step1이 8개 보험사에서 baseline 대비 품질 우위
   - Current: **56% coverage loss** (339 → 148)
   - Status: **NOT MET**

2. ✅ Quality Report v2 통과
   - Report generated ✅
   - But shows quality regression ❌

3. ❌ Regression tests 100% 통과
   - Not implemented yet (pending)

**Verdict**: ❌ **Baseline extractor CANNOT be deprecated**

---

## 7. Recommendations

### 7.1 Immediate (Required for Production)

**P0: Fix Critical Under-Extraction**:
1. Debug header row detection (Samsung, Hyundai)
2. Verify all table rows are read (not just first N)
3. Fix column map auto-detection (Hyundai, Samsung)
4. Relax KB summary table detection rules

**P0: Fix KB Summary Table Detection**:
1. Inspect KB PDF pages 2-4 manually
2. Add alternative header keyword patterns
3. Lower row count threshold if needed

**P0: Strengthen Noise Filtering**:
1. Reject rows with keywords: "합계", "◆", "가입한 담보"
2. Reject rows with no coverage_amount_text AND no premium_amount_text
3. Add length-based heuristics (Korean coverage names typically 3-20 chars)

### 7.2 Short-term (Quality Parity)

**Achieve Quality Parity with Baseline**:
- Target: 95%+ coverage count match (per insurer)
- Target: No false positives (totals, disclaimers)
- Target: 8/8 insurers successful (no KB failure)

**Implement Regression Tests**:
- Known coverage preservation tests (3-5 coverages per insurer)
- Coverage count stability tests (±10% tolerance)
- Summary vs detail usage tests

### 7.3 Long-term (Quality Superiority)

**Multi-PDF Reader Benefits**:
- Leverage Camelot for complex table structures (install camelot-py)
- Use quality score to auto-select best reader per insurer
- Profile builder + extractor decoupling enables rapid iteration

**Summary-First Benefits**:
- Cleaner separation of summary vs detail tables
- Evidence-backed extraction (page + row + snippet)
- Layer discipline enforcement (no inference in Step1)

---

## 8. Sign-off

**STEP NEXT-45-B Status**: ⚠️ **PARTIAL IMPLEMENTATION (Not Production Ready)**

**Key Achievements**:
- ✅ Multi-PDF reader architecture (pdfplumber + PyMuPDF)
- ✅ Automatic profile builder (evidence-backed)
- ✅ Summary-first SSOT extractor (zero-base redesign)
- ✅ New module: `pipeline/step1_summary_first/`

**Blockers for Production**:
- ❌ 56% coverage loss vs baseline (339 → 148)
- ❌ KB summary table detection failed (0 coverages)
- ❌ Samsung/Hyundai severe under-extraction (-89%, -97%)

**Next Steps**:
1. Debug + fix critical under-extraction (P0)
2. Achieve quality parity (95%+ coverage match)
3. Implement regression tests
4. Re-run Quality Report v2
5. If quality superiority proven → deprecate baseline

**Baseline Extractor**: ✅ **REMAINS CANONICAL** (pipeline/step1_extract_scope/)

---

## Appendix A: V2 Output Samples

### A.1 Samsung (8 facts, -89%)

```json
{"coverage_name_raw": "진단", "proposal_facts": {"coverage_amount_text": "10만원", "premium_amount_text": "189", ...}}
{"coverage_name_raw": "입원", "proposal_facts": {"coverage_amount_text": "1만원", "premium_amount_text": "1,267", ...}}
...
{"coverage_name_raw": "보장보험료 합계", ...}  // ❌ NOISE (total row)
{"coverage_name_raw": "◆ 가입한 담보에 대한 보장내용은...", ...}  // ❌ NOISE (disclaimer)
```

**Issues**:
- Only 8/73 coverages extracted (-89%)
- Noise rows extracted (totals, disclaimers)

### A.2 Hanwha (32 facts, -57%)

```json
{"coverage_name_raw": "상해사망", "proposal_facts": {"coverage_amount_text": "1억원", "premium_amount_text": "3,200", ...}}
...
```

**Issues**:
- 32/74 coverages extracted (-57%)
- Better than Samsung, but still significant under-extraction

---

## Appendix B: Profile Builder Output Samples

### B.1 Samsung Profile

```json
{
  "insurer": "samsung",
  "reader_type": "pymupdf",
  "summary_table": {
    "exists": true,
    "pages": [2, 3],
    "table_signatures": [
      {
        "page": 2,
        "row_count": 31,
        "col_count": 5,
        "column_map": {},  // ❌ Empty (auto-detection required)
        ...
      }
    ]
  }
}
```

### B.2 KB Profile (Failed Detection)

```json
{
  "insurer": "kb",
  "summary_table": {
    "exists": false,  // ❌ Should be true per 44-D
    "pages": []
  },
  "structural_risks": [
    "CRITICAL: No summary tables detected (fallback to detail extraction required)"
  ]
}
```

---

**Report End**
