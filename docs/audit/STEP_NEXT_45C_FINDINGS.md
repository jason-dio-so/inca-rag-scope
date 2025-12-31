# STEP NEXT-45-C: Findings and Analysis

**Date**: 2025-12-31
**Status**: ⚠️ **PARTIAL COMPLETION** (Profile V3 Complete, Extraction Blocked by KB Table Structure Issue)
**Decision**: **Baseline Extractor Remains Canonical**

---

## Executive Summary

STEP NEXT-45-C successfully created **Profile V3** with KB summary table detection, but encountered a **fundamental table extraction limitation** with KB's PDF structure that blocks the summary-first approach.

### Key Achievements ✅
1. **Profile Builder V3**: Automatic profile generation with KB row-number column detection
2. **KB Summary Table Detection**: Successfully detected KB summary tables (pages 2-3)
3. **Column Offset Logic**: Implemented row-number column detection (`has_row_number_column` flag)
4. **Evidence-Backed Profiles**: All 8 insurers have v3 profiles with structural evidence

### Critical Blocker ❌
**KB Table Structure Issue**: KB's coverage names are **outside pdfplumber's table extraction boundary** (positioned as separate text blocks, not table cells).

---

## Problem Analysis

### KB PDF Structure (Pages 2-3)

**What pdfplumber sees**:
```
Row 0: [보장명] [가입금액] [보험료(원)] [납입|보험기간]  ← Header
Row 1: []       [1천만원]  [700]        []              ← Data (NO coverage name!)
Row 2: []       [1천만원]  [300]        []
Row 3: []       [10만원]   [36]         []
...
```

**What's actually in the PDF** (from text extraction):
```
일반상해사망(기본)           1천만원    700    20년/100세
일반상해후유장해(20~100%)(기본)  1천만원    300    20년/100세
보험료납입면제대상보장(8대기본)   10만원     36     20년/100세
...
```

**Root Cause**:
- Coverage names are **text blocks positioned to the left of the table**
- pdfplumber's `extract_tables()` only captures cells within table borders
- Coverage names are OUTSIDE the table grid → extracted as empty strings `[]`

---

## Why Baseline Extractor (44-γ-2) Works

The baseline extractor (`pipeline/step1_extract_scope/proposal_fact_extractor_v2.py`) uses:
1. **Mixed extraction strategy**: Combines table extraction + text parsing
2. **Positional heuristics**: Matches text blocks by position/proximity to table cells
3. **Insurer-specific logic**: Has KB-specific handlers for this exact scenario

This is why baseline successfully extracts 45 KB coverages while v3 extracts 0.

---

## V3 Extraction Results (Quality Regression)

| Insurer | Baseline (44-γ-2) | V3 (45-C) | Delta | Delta % |
|---------|-------------------|-----------|-------|---------|
| Samsung | 72 | 6 | -66 | -91.7% |
| Meritz | 35 | 9 | -26 | -74.3% |
| KB | 45 | 0 | -45 | **-100.0%** |
| Hanwha | 73 | 32 | -41 | -56.2% |
| Hyundai | 37 | 0 | -37 | -100.0% |
| Lotte | 43 | 30 | -13 | -30.2% |
| Heungkuk | 38 | 23 | -15 | -39.5% |
| DB | 34 | 18 | -16 | -47.1% |
| **TOTAL** | **377** | **118** | **-259** | **-68.7%** |

**Quality Gate**: ❌ FAILED (-68.7%, target: ≥95%)

---

## Root Cause Analysis (Other Insurers)

### Samsung (-91.7%, 72 → 6)
**Issue**: Similar to KB - coverage names likely positioned outside table grid
**Evidence**: Extracted only 6 facts (probably subtotals or section headers that ARE in tables)

### Hyundai (-100%, 37 → 0)
**Issue**: Complete extraction failure, likely same structural issue as KB

### Hanwha (-56.2%, 73 → 32)
**Issue**: Partial extraction success
**Note**: Better than others, but still significant under-extraction

### Meritz/Lotte/Heungkuk/DB
**Issue**: Moderate under-extraction (-30% to -74%)
**Likely cause**: Similar table/text positioning issues, but less severe

---

## Architectural Insights

### What Works ✅
1. **Profile-Based Approach**: Separation of structure detection from extraction is sound
2. **KB Row-Number Column Detection**: Correctly identified row-number columns (when they exist)
3. **Evidence-Backed Profiles**: All profiles have page + snippet + table dimensions

### What Doesn't Work ❌
1. **Pure Table Extraction**: pdfplumber's `extract_tables()` is insufficient for Korean insurance PDFs
2. **Assumption of Grid-Based Tables**: Many PDFs use **text blocks positioned near tables**, not actual table cells
3. **Summary-First Dogma**: "Summary table SSOT" breaks when summary tables have non-standard structure

---

## Why Baseline Extractor Is Superior

**Baseline (`proposal_fact_extractor_v2.py`) advantages**:
1. **Hybrid extraction**: Combines tables + text + positional heuristics
2. **Insurer-specific handlers**: Has custom logic for KB, Hanwha, etc.
3. **Production-tested**: 377 coverages extracted, 99.4% IN-SCOPE KPI
4. **Regression-tested**: 55/55 tests passing
5. **Robust**: Handles edge cases (merged cells, text blocks, fragmented tables)

**V3 Summary-First disadvantages**:
1. **Table-only extraction**: Fails when coverage names are text blocks
2. **No positional matching**: Can't associate text blocks with table rows
3. **No hybrid strategy**: All-or-nothing approach
4. **No fallback**: Rigid "summary-first SSOT" fails completely on structural anomalies

---

## Recommendations

### Immediate (STEP NEXT-45-C Conclusion)
1. ✅ **Keep baseline extractor canonical** (`pipeline/step1_extract_scope/`)
2. ✅ **Document Profile V3 as research output** (useful for future work)
3. ✅ **Mark 45-C as "Partial Completion"** (profile built, extraction blocked)
4. ❌ **Do NOT deprecate baseline** (quality regression too severe)

### Short-term (Optional Future Work)
1. **Hybrid Extractor**: Combine Profile V3 + text-based extraction
2. **Layout Analysis**: Use PyMuPDF's layout detection to associate text blocks with tables
3. **Camelot Integration**: Try Camelot's lattice/stream modes for better table detection
4. **Per-Insurer Strategies**: Recognize that "one extractor to rule them all" may be infeasible

### Long-term (Architecture Evolution)
1. **Accept Insurer-Specific Logic**: Korean insurance PDFs have too much variance for pure generalization
2. **Profile as Metadata**: Use profiles to SELECT extraction strategy, not dictate it
3. **Quality Over Purity**: Baseline's "messy but working" approach beats "clean but broken"

---

## Hard Gates Assessment (Section 5)

### Gate 1: Baseline Regression ✅
**Status**: PASS
- `pytest tests/test_step1_proposal_fact_regression.py`: 55/55 passing
- Baseline extractor untouched

### Gate 2: KB Summary-Table Gate ❌
**Status**: FAIL
- KB summary_table.exists == true ✅ (profile detection)
- KB extraction result == 0 ❌ (extraction failed)
- Reason: Coverage names outside table grid

### Gate 3: Over-Filtering Gate ✅
**Status**: N/A (extractor not deployed)

### Gate 4: Evidence Gate ⚠️
**Status**: PARTIAL PASS
- All extracted records have evidences ✅
- But 68.7% of records NOT extracted ❌

---

## DoD (Definition of Done) Assessment (Section 9)

- ❌ KB 요약표를 SSOT로 읽고, 순번 오염 때문에 detail로 넘어가는 현상 0
  - **Result**: KB extracted 0 facts (not due to row-numbers, but table structure)

- ✅ 8 insurer Step1 v3 재생성 완료
  - **Result**: All 8 insurers have v3 profiles + v3 extraction output

- ✅ Baseline 회귀 테스트 100% PASS 유지
  - **Result**: 55/55 passing

- ❌ 새 KB 회귀 테스트 PASS
  - **Result**: Not implemented (blocked by extraction failure)

- ✅ Quality Report v3 생성
  - **Result**: This document + extraction results

- ⏳ STATUS.md 업데이트
  - **Result**: Pending

- ⏳ 모든 변경사항 커밋 완료
  - **Result**: Pending

---

## Deliverables

### Generated Files ✅
```
pipeline/step1_summary_first/
├── profile_builder_v3.py       (KB column-offset detection)
└── extractor_v3.py              (profile-based extraction)

data/profile/
└── *_proposal_profile_v3.json  (8 insurers, evidence-backed)

data/scope_v3/
└── *_step1_raw_scope_v3.jsonl  (8 insurers, 118 total facts)

docs/audit/
└── STEP_NEXT_45C_FINDINGS.md   (this document)
```

### Not Generated ❌
- Regression tests (blocked by extraction failure)
- Quality report v3 (findings document serves as substitute)

---

## Lessons Learned

### Technical Lessons
1. **PDF Table Extraction Is Fragile**: pdfplumber's `extract_tables()` assumes grid-based tables
2. **Korean Insurance PDFs Are Non-Standard**: Text blocks + tables, not pure tables
3. **One-Size-Fits-All Fails**: Insurer-specific logic is necessary, not a code smell

### Process Lessons
1. **Profile ≠ Extraction**: Good profile detection doesn't guarantee good extraction
2. **Early Validation**: Should have validated extraction on KB before full 8-insurer rollout
3. **Baseline Respect**: Baseline extractor's "messy" approach reflects PDF reality, not poor design

### Architecture Lessons
1. **SSOT Dogma Can Backfire**: "Summary-first SSOT" breaks when summary structure is non-standard
2. **Hybrid > Pure**: Mixed extraction strategies beat pure table extraction
3. **Quality > Elegance**: Working extraction beats elegant architecture

---

## Conclusion

STEP NEXT-45-C **successfully identified and documented the KB table structure issue**, but this issue **blocks the summary-first extraction approach** for KB and several other insurers.

The **baseline extractor (44-γ-2) remains the canonical implementation** because:
1. It handles KB's non-standard table structure correctly
2. It has 99.4% IN-SCOPE KPI with 377 coverages extracted
3. It has 55 regression tests all passing
4. It uses hybrid extraction strategies proven to work

**Profile V3** is valuable as **research output and metadata** for future work, but does NOT replace the baseline extractor.

**No immediate action required**: Baseline is stable and production-ready.

---

**Report End**
