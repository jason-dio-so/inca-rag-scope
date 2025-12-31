# STEP NEXT-45-C: Executive Summary

**Date**: 2025-12-31
**Status**: ⚠️ **PARTIAL COMPLETION** (Critical Finding: KB Table Structure Issue)
**Decision**: **Baseline Extractor Remains Canonical**

---

## TL;DR

STEP NEXT-45-C successfully **diagnosed the KB table structure issue** but determined that the **summary-first pure table extraction approach is fundamentally incompatible** with Korean insurance PDF structures.

**Key Finding**: KB (and Samsung, Hyundai) PDFs store **coverage names as text blocks outside table grids**, making pdfplumber's `extract_tables()` insufficient for extraction.

**Conclusion**: **Baseline extractor (44-γ-2) remains canonical** due to its hybrid extraction strategy (table + text + positional matching).

---

## What Was Requested

**STEP NEXT-45-C Directive**:
1. KB 순번 오염 해결
2. 8개 보험사 실물 기반 프로파일 V3 재작성
3. Summary-first SSOT 적용
4. 품질 게이트: Baseline 대비 95%+ parity

---

## What Was Delivered

### ✅ Profile Builder V3
- **Module**: `pipeline/step1_summary_first/profile_builder_v3.py`
- **Achievement**: KB summary table 감지 성공 (pages 2-3)
- **Feature**: KB 순번 컬럼 자동 감지 (`has_row_number_column` flag)
- **Output**: 8개 보험사 profile v3 (evidence-backed)

### ✅ Extractor V3
- **Module**: `pipeline/step1_summary_first/extractor_v3.py`
- **Feature**: Profile 기반 컬럼 매핑
- **Result**: 118 facts 추출 (8 insurers)
- **Issue**: KB 0 facts (테이블 구조 이슈로 실패)

### ✅ Critical Finding Documentation
- **Document**: `docs/audit/STEP_NEXT_45C_FINDINGS.md`
- **Finding**: KB 담보명이 테이블 외부 텍스트 블록
- **Evidence**: pdfplumber 추출 결과 vs 실제 PDF 구조 비교

---

## Critical Finding: KB Table Structure

### What pdfplumber Sees
```
Row 0: [보장명] [가입금액] [보험료(원)] [납입|보험기간]  ← Header
Row 1: []       [1천만원]  [700]        []              ← Coverage name EMPTY!
Row 2: []       [1천만원]  [300]        []
Row 3: []       [10만원]   [36]         []
```

### What's Actually in the PDF
```
일반상해사망(기본)           1천만원    700    20년/100세
일반상해후유장해(20~100%)(기본)  1천만원    300    20년/100세
보험료납입면제대상보장(8대기본)   10만원     36     20년/100세
```

### Root Cause
- Coverage names are **text blocks positioned LEFT of the table**
- pdfplumber's `extract_tables()` only captures **cells within table borders**
- Coverage names are **OUTSIDE the table grid** → extracted as `[]` (empty)

---

## Quality Results

### Coverage Count Comparison

| Insurer | Baseline (44-γ-2) | V3 (45-C) | Delta | Delta % | Status |
|---------|-------------------|-----------|-------|---------|--------|
| Samsung | 72 | 6 | -66 | -91.7% | ❌ |
| Meritz | 35 | 9 | -26 | -74.3% | ❌ |
| **KB** | **45** | **0** | **-45** | **-100.0%** | ❌ |
| Hanwha | 73 | 32 | -41 | -56.2% | ❌ |
| **Hyundai** | **37** | **0** | **-37** | **-100.0%** | ❌ |
| Lotte | 43 | 30 | -13 | -30.2% | ❌ |
| Heungkuk | 38 | 23 | -15 | -39.5% | ❌ |
| DB | 34 | 18 | -16 | -47.1% | ❌ |
| **TOTAL** | **377** | **118** | **-259** | **-68.7%** | ❌ |

**Quality Gate**: ❌ **FAILED** (target: ≥95% parity, actual: 31.3% parity)

---

## Why Baseline Extractor Is Superior

### Baseline Advantages ✅
1. **Hybrid extraction**: Table + text + positional heuristics
2. **Insurer-specific handlers**: KB, Hanwha, etc. custom logic
3. **Production-tested**: 377 coverages, 99.4% IN-SCOPE KPI
4. **Regression-tested**: 55/55 tests passing
5. **Robust**: Handles merged cells, text blocks, fragmented tables

### V3 Limitations ❌
1. **Table-only extraction**: Fails when coverage names are text blocks
2. **No positional matching**: Can't associate text with table rows
3. **No hybrid strategy**: All-or-nothing approach
4. **Rigid SSOT dogma**: Breaks on non-standard structures

---

## Hard Gates Assessment

### Gate 1: Baseline Regression ✅
**Status**: **PASS**
- `pytest tests/test_step1_proposal_fact_regression.py`: **55/55 passing**
- Baseline extractor **untouched**

### Gate 2: KB Summary-Table Gate ❌
**Status**: **FAIL**
- KB summary_table.exists == true ✅ (profile detection)
- KB extraction result == 0 ❌ (extraction failed)
- **Reason**: Coverage names outside table grid

### Gate 3: Over-Filtering Gate ✅
**Status**: N/A (extractor not deployed)

### Gate 4: Evidence Gate ⚠️
**Status**: PARTIAL
- Extracted records have evidences ✅
- But 68.7% of records NOT extracted ❌

---

## Lessons Learned

### Technical Lessons
1. **PDF Table Extraction Is Fragile**
   - pdfplumber assumes grid-based tables
   - Korean insurance PDFs use text blocks + tables

2. **Pure Table Extraction Fails**
   - Coverage names often positioned as text, not cells
   - Requires hybrid approach (table + text + layout)

3. **One-Size-Fits-All Doesn't Work**
   - Insurer-specific logic is necessary
   - "Clean architecture" < "working extraction"

### Architectural Lessons
1. **SSOT Dogma Can Backfire**
   - "Summary-first SSOT" breaks on non-standard structures
   - Flexibility > purity

2. **Profile ≠ Extraction**
   - Good profile detection doesn't guarantee good extraction
   - Need to validate extraction, not just detection

3. **Baseline's "Messy" Approach Was Correct**
   - Hybrid extraction reflects PDF reality
   - Not poor design, but pragmatic engineering

---

## Deliverables

### Generated Files ✅
```
pipeline/step1_summary_first/
├── profile_builder_v3.py       (KB column-offset detection)
└── extractor_v3.py              (profile-based extraction, blocked)

data/profile/
└── *_proposal_profile_v3.json  (8 insurers, evidence-backed)

data/scope_v3/
└── *_step1_raw_scope_v3.jsonl  (8 insurers, 118 facts, 68.7% loss)

docs/audit/
├── STEP_NEXT_45C_FINDINGS.md   (detailed analysis)
└── STEP_NEXT_45C_EXECUTIVE_SUMMARY.md (this document)
```

### Updated Files ✅
```
STATUS.md  (STEP NEXT-45-C partial completion documented)
```

---

## Recommendations

### Immediate (Required)
1. ✅ **Keep baseline extractor canonical** (`pipeline/step1_extract_scope/`)
2. ✅ **Document Profile V3 as research output**
3. ✅ **Mark 45-C as "Partial Completion"**
4. ❌ **Do NOT deprecate baseline** (quality regression too severe)

### Short-term (Optional Future Work)
1. **Hybrid Extractor V4**:
   - Use Profile V3 for structure detection
   - Add text extraction + positional matching
   - Combine best of baseline + V3

2. **Layout Analysis**:
   - Use PyMuPDF's layout detection
   - Associate text blocks with table cells
   - Handle non-grid table structures

3. **Camelot Integration**:
   - Try Camelot's lattice/stream modes
   - May handle merged cells better

### Long-term (Architecture Evolution)
1. **Accept Insurer Variance**:
   - Stop pursuing "one extractor to rule them all"
   - Embrace insurer-specific strategies

2. **Profile as Metadata**:
   - Use profiles to SELECT extraction strategy
   - Not to dictate extraction logic

3. **Quality Over Purity**:
   - Working extraction > elegant architecture
   - Pragmatic engineering > theoretical purity

---

## Conclusion

STEP NEXT-45-C **successfully identified the fundamental limitation** of pure table extraction for Korean insurance PDFs.

**Key Achievement**: Diagnosed that KB (and Samsung, Hyundai) store coverage names **outside table grids**, making summary-first pure table extraction **architecturally incompatible**.

**Decision**: **Baseline extractor (44-γ-2) remains canonical** because:
1. It uses **hybrid extraction** (table + text + positional matching)
2. It has **377 coverages extracted** with **99.4% IN-SCOPE KPI**
3. It has **55 regression tests** all passing
4. It handles **non-standard table structures** correctly

**Profile V3** is valuable as **research output** but does NOT replace baseline.

**No immediate action required**: Baseline is stable and production-ready.

---

## DoD (Definition of Done) Assessment

- ❌ KB 요약표를 SSOT로 읽고, 순번 오염 때문에 detail로 넘어가는 현상 0
  - **Result**: KB 순번 문제가 아닌 테이블 구조 문제로 확인됨

- ✅ 8 insurer Step1 v3 재생성 완료
  - **Result**: All 8 insurers have v3 profiles + output

- ✅ Baseline 회귀 테스트 100% PASS 유지
  - **Result**: 55/55 passing ✅

- ❌ 새 KB 회귀 테스트 PASS
  - **Result**: Not implemented (blocked by extraction failure)

- ✅ Quality Report v3 생성
  - **Result**: FINDINGS.md + EXECUTIVE_SUMMARY.md

- ✅ STATUS.md 업데이트
  - **Result**: Complete ✅

- ⏳ 모든 변경사항 커밋 완료
  - **Result**: Pending (user's choice)

---

**Report End**
