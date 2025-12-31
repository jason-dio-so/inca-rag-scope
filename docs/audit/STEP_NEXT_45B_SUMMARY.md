# STEP NEXT-45-B: Executive Summary

**Date**: 2025-12-31
**Status**: ⚠️ **PARTIAL IMPLEMENTATION** (Architecture Complete, Quality Verification Failed)
**Decision**: **Baseline Extractor Remains Canonical** (Not Ready for Deprecation)

---

## What Was Built

### ✅ Multi-PDF Reader Architecture
- **Module**: `pipeline/step1_summary_first/multi_pdf_reader.py`
- **Readers**: pdfplumber, PyMuPDF (fitz)
- **Quality-Based Selection**: Automatic best-reader selection per insurer
- **Result**: 8/8 insurers successfully parsed

### ✅ Automatic Profile Builder
- **Module**: `pipeline/step1_summary_first/profile_builder.py`
- **NO Manual Writing**: Fully automatic generation (compliance with 45-B section 4.1)
- **Evidence-Backed**: All profiles include page + snippet + table dimensions
- **Output**: `data/profile/*_proposal_profile_v2.json` (8 insurers)

### ✅ Summary-First Extractor
- **Module**: `pipeline/step1_summary_first/extractor.py`
- **SSOT Contract**: Summary table as single source of truth
- **Layer Discipline**: Raw text only, no inference, no amount parsing
- **Processing Order**: Profile → Summary check → Extract from summary (or fallback)

### ✅ Quality Report v2
- **Document**: `docs/audit/STEP_NEXT_45B_QUALITY_REPORT.md`
- **Comparison**: Baseline (44-γ-2) vs V2 (45-B)
- **Root Cause Analysis**: Under-extraction, over-extraction, KB failure

---

## What Went Wrong

### ❌ Quality Regression (-56% Coverage Loss)

| Metric | Baseline | V2 | Delta |
|--------|----------|-----|-------|
| Total coverages | 339 | 148 | **-56%** |
| Samsung | 73 | 8 | **-89%** |
| Hyundai | 38 | 1 | **-97%** |
| KB | 33 | 0 | **-100%** |

### Root Causes

**1. Header Row Detection Too Aggressive**
- Samsung: Profile detected 31 + 18 row tables, but extractor only extracted 8 facts
- Likely skipping too many rows as "headers"
- Data rows being misclassified as header rows

**2. Column Map Auto-Detection Failing**
- Samsung: `column_map: {}` (empty) → auto-detection required
- Hyundai: Only 1/38 facts extracted → column detection failed
- Auto-detection heuristics not robust enough for all insurer PDF formats

**3. KB Summary Table Detection Failed**
- Profile builder marked KB as "no summary table"
- STEP NEXT-44-D profile report states KB **should** have summary tables (pages 2-4)
- Detection rules too strict (keyword-based heuristics insufficient)

**4. Noise Filtering Issues**
- Samsung: Extracted "보장보험료 합계" (total row) as coverage
- Samsung: Extracted "◆ 가입한 담보에 대한..." (disclaimer) as coverage
- `_is_noise()` filter too permissive

---

## Deprecation Rule Assessment (Section 8)

**Conditions for Deprecating Baseline**:
1. ❌ 새 Step1이 baseline 대비 품질 우위 → **NOT MET** (-56% coverage loss)
2. ✅ Quality Report v2 통과 → Generated, but shows regression
3. ❌ Regression tests 100% 통과 → Not implemented (not required given quality failure)

**Verdict**: **Baseline extractor CANNOT be deprecated**

---

## What Remains Canonical

**Baseline Extractor**: `pipeline/step1_extract_scope/`
- `proposal_fact_extractor_v2.py` (44-β + 44-γ + 44-γ-2)
- 8/8 insurers supported
- 339 total coverages extracted
- IN-SCOPE KPI: 99.4% ✅

**New Module Status**: `pipeline/step1_summary_first/`
- ⚠️ **NOT PRODUCTION READY**
- Available for future refinement
- Architecture foundation in place

---

## Next Steps (If Continued)

**P0: Fix Critical Under-Extraction**
1. Debug header row detection (Samsung, Hyundai)
2. Verify all table rows read (not just first N)
3. Fix column map auto-detection
4. Relax KB summary table detection rules

**P0: Strengthen Noise Filtering**
1. Reject rows with keywords: "합계", "◆", "가입한 담보"
2. Reject rows with no amount AND no premium
3. Add length-based heuristics (coverage names typically 3-20 chars)

**Quality Parity Target**
- 95%+ coverage count match (per insurer)
- 0 false positives (totals, disclaimers)
- 8/8 insurers successful (no KB failure)

**After Quality Parity**
1. Implement regression tests
2. Re-run Quality Report v2
3. If quality superiority proven → deprecate baseline

---

## Lessons Learned

### What Worked
1. **Multi-reader architecture**: Correct approach for PDF fragility
2. **Profile-driven extraction**: Separation of structure detection from value extraction
3. **Evidence-backed profiles**: Automatic generation with page + snippet verification
4. **Summary-first SSOT**: Correct layer discipline (no inference in Step1)

### What Needs Improvement
1. **Header detection heuristics**: Too aggressive, needs per-insurer tuning
2. **Column map detection**: Keyword-based insufficient, needs layout analysis
3. **Summary table detection**: Too strict, missing KB summary tables
4. **Quality gates enforcement**: Should fail-fast on coverage count drops >10%

### Architecture Value (Long-term)
- Profile builder + extractor decoupling enables rapid iteration
- Multi-reader quality scoring enables automatic PDF parser selection
- Summary-first SSOT aligns with constitutional enforcement (STEP NEXT-31-P1)

---

## Sign-off

**STEP NEXT-45-B**: ⚠️ **Architecture Complete, Quality Verification Failed**

**Key Deliverables**:
- ✅ Multi-PDF reader (pdfplumber + PyMuPDF)
- ✅ Automatic profile builder (evidence-backed)
- ✅ Summary-first extractor (zero-base redesign)
- ✅ Quality Report v2 (regression analysis)

**Production Status**:
- ❌ NOT READY (56% coverage loss vs baseline)
- ✅ Baseline extractor remains canonical

**Future Work**:
- Optional: Refine and achieve quality parity
- Optional: Leverage multi-reader for complex PDFs
- Optional: Profile-driven approach for new insurers

**No Immediate Action Required**: Baseline extractor (44-γ-2) is stable and production-ready.

---

**Report End**
