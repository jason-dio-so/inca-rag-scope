# Step1 Summary-First Redesign (STEP NEXT-45-B)

**Status**: ⚠️ **NOT PRODUCTION READY** (Architecture Complete, Quality Regression Detected)

**Date**: 2025-12-31

---

## Purpose

Zero-base redesign of Step1 proposal fact extraction with:
1. **Summary-first SSOT**: Summary table as single source of truth
2. **Multi-PDF reader**: pdfplumber + PyMuPDF with quality-based selection
3. **Profile-driven extraction**: Automatic profile generation, no manual writing
4. **Layer discipline**: Raw text only, no inference, no amount parsing

---

## Modules

### 1. `multi_pdf_reader.py`
Multi-reader PDF parser with quality-based selection.

**Readers**:
- `pdfplumber` (fast, good for clean tables)
- `pymupdf` (fitz, good for complex layouts)
- `camelot` (optional, best for structured tables)

**Quality Metric**:
- Summary table detection rate
- Average row count for summary candidates
- Keyword completeness (coverage + amount + period)

**Usage**:
```python
from pipeline.step1_summary_first.multi_pdf_reader import MultiPDFReader

reader = MultiPDFReader(pdf_path, insurer="samsung")
results = reader.read_all_readers()
best_structure = reader.select_best_reader(results)
```

### 2. `profile_builder.py`
Automatic proposal profile builder (NO manual writing).

**Summary Table Detection Rules** (Section 4.3):
- Has coverage keyword (담보, 가입담보)
- Has amount keyword (가입금액)
- Has premium OR period keyword (보험료, 납입, 만기, 납기)
- Does NOT have disqualifying keywords (보장내용, 지급사유)

**Output Schema**:
```json
{
  "insurer": "...",
  "summary_table": {
    "exists": true,
    "pages": [3, 4],
    "table_signatures": [
      {
        "page": 3,
        "header_rows": ["가입담보", "가입금액", "보험료", "납기/만기"],
        "column_map": {
          "coverage_name": 1,
          "coverage_amount": 2,
          "premium": 3,
          "period": 4
        },
        "evidence": {
          "page": 3,
          "snippet": "...",
          "sample_rows": ["암 진단비 | 3,000만원 | 12,340원 | 20년"]
        }
      }
    ]
  }
}
```

**Usage**:
```bash
python -m pipeline.step1_summary_first.profile_builder
```

### 3. `extractor.py`
Summary-first Step1 extractor.

**Processing Order** (FIXED):
1. Load profile
2. Check summary_table.exists
3. If True: extract from summary table ONLY
4. If False: raise NotImplementedError (fallback not implemented)

**Output Schema** (LOCKED):
```json
{
  "coverage_name_raw": "...",
  "proposal_facts": {
    "coverage_amount_text": "...",
    "premium_amount_text": "...",
    "payment_period_text": "...",
    "payment_method_text": null,
    "evidences": [...]
  }
}
```

**Prohibitions**:
- ❌ coverage_code generation
- ❌ Amount parsing (text as-is)
- ❌ Detail table usage (if summary exists)

**Usage**:
```bash
python -m pipeline.step1_summary_first.extractor
```

---

## Quality Status

### Baseline Comparison (44-γ-2 vs 45-B)

| Insurer | Baseline | V2 | Delta | Status |
|---------|----------|-----|-------|--------|
| Samsung | 73 | 8 | -89% | ❌ CRITICAL |
| Meritz | 36 | 10 | -72% | ❌ CRITICAL |
| KB | 33 | 0 | -100% | ❌ CRITICAL |
| Hanwha | 74 | 32 | -57% | ❌ CRITICAL |
| Hyundai | 38 | 1 | -97% | ❌ CRITICAL |
| Lotte | 44 | 30 | -32% | ❌ HIGH |
| Heungkuk | 39 | 23 | -41% | ❌ HIGH |
| DB | 35 | 44 | +26% | ⚠️ SUSPICIOUS |

**Total**: 339 → 148 (**-56% coverage loss**)

**Verdict**: ❌ **Quality Regression** (Not Ready for Production)

---

## Known Issues

### 1. Header Row Detection Too Aggressive
- Samsung: Profile detected 31 + 18 row tables, but extractor only extracted 8 facts
- Hyundai: Only 1/38 facts extracted
- **Fix Required**: Debug `_detect_header_rows()` heuristic

### 2. Column Map Auto-Detection Failing
- Samsung: `column_map: {}` (empty) → auto-detection required but failed
- Hyundai: Column detection failed
- **Fix Required**: Improve `_auto_detect_column_map()` robustness

### 3. KB Summary Table Detection Failed
- Profile marked KB as "no summary table"
- STEP NEXT-44-D states KB should have summary tables (pages 2-4)
- **Fix Required**: Relax detection rules, add alternative keyword patterns

### 4. Noise Filtering Issues
- Samsung: Extracted "보장보험료 합계" (total row)
- Samsung: Extracted "◆ 가입한 담보에 대한..." (disclaimer)
- **Fix Required**: Strengthen `_is_noise()` filter

---

## Deprecation Status

**Baseline Extractor**: ✅ **REMAINS CANONICAL** (`pipeline/step1_extract_scope/`)

**Deprecation Conditions** (Section 8):
1. ❌ Baseline 대비 품질 우위 → NOT MET (-56% coverage loss)
2. ✅ Quality Report v2 → Generated, shows regression
3. ❌ Regression tests 100% → Not required (quality failure)

**Verdict**: Baseline extractor CANNOT be deprecated.

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

## Documentation

- **Quality Report**: `docs/audit/STEP_NEXT_45B_QUALITY_REPORT.md`
- **Executive Summary**: `docs/audit/STEP_NEXT_45B_SUMMARY.md`
- **STATUS.md**: Updated with partial completion status

---

## Architecture Value (Long-term)

Despite quality regression, the architecture has long-term value:

1. **Multi-reader approach**: Correct for PDF fragility (different insurers, different parsers)
2. **Profile-driven extraction**: Separation of structure detection from value extraction enables rapid iteration
3. **Summary-first SSOT**: Aligns with constitutional enforcement (STEP NEXT-31-P1)
4. **Evidence-backed profiles**: Automatic generation with page + snippet verification

If quality parity is achieved, this architecture can replace baseline.

---

## Conclusion

**STEP NEXT-45-B**: Architecture foundation complete, but not production-ready due to quality regression.

**Recommendation**: Keep baseline extractor canonical until quality parity is achieved.

**No Immediate Action Required**: Baseline (44-γ-2) is stable and production-ready (99.4% IN-SCOPE KPI).
