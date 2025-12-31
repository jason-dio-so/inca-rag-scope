# Duplicate Step Analysis

**Audit Date**: 2025-12-31
**Auditor**: Claude (Pipeline Constitution Auditor)
**Purpose**: Explain why multiple steps share the same number and resolve conflicts

---

## Executive Summary

The pipeline contains **6 step number collisions** across 13 modules:
- step0 (×2), step1 (×2), step2 (×2), step7 (×2), step8 (×2), step10 (×3)

**Root Cause**: Evolutionary pipeline development without enforced step numbering convention. Steps were added/deprecated without renumbering, leading to namespace pollution.

**Impact**:
- Developer confusion about execution order
- Documentation fragmentation (CLAUDE.md says step7_compare deprecated, but step7_amount_extraction active)
- Risk of executing wrong step variant

---

## Q1: Why does step2 exist twice?

### step2_canonical_mapping vs step2_extract_pdf

| Aspect | step2_canonical_mapping | step2_extract_pdf |
|--------|------------------------|-------------------|
| **Module** | `map_to_canonical.py` | (empty directory) |
| **Entrypoint** | ✅ `python -m pipeline.step2_canonical_mapping.map_to_canonical` | ❌ NONE |
| **Input** | `{INS}_scope.csv`, mapping 엑셀 | N/A |
| **Output** | `{INS}_scope_mapped.csv` | N/A |
| **Purpose** | Map extracted coverages to canonical codes | (unknown - no code exists) |
| **Used Now?** | ✅ YES (CORE STEP) | ❌ NO (GHOST) |
| **Evidence** | Recently modified (Dec 30 18:49) | Directory has `__pycache__` but no `.py` files |

### Answer

**step2_canonical_mapping** is the legitimate step2.

**step2_extract_pdf** is a **GHOST STEP**:
- Directory exists with `__pycache__/` (证明 historical code existed)
- But all `.py` files have been deleted
- Likely superseded by step3_extract_text during refactoring
- **Action**: DELETE directory entirely

### Do they overlap?

**NO**. step2_canonical_mapping handles coverage name → canonical code mapping (deterministic).
step2_extract_pdf was likely PDF text extraction (now done by step3_extract_text).

**Roles are completely different** → one is mapping logic, other was PDF I/O.

---

## Q2: Why does step7 exist twice?

### step7_amount_extraction vs step7_compare

| Aspect | step7_amount_extraction | step7_compare |
|--------|------------------------|---------------|
| **Module** | `extract_and_enrich_amounts.py` | `compare_insurers.py` |
| **Entrypoint** | ✅ `python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts` | ✅ `python -m pipeline.step7_compare.compare_insurers` |
| **Input** | `coverage_cards.jsonl`, PDFs | `{A}_coverage_cards.jsonl`, `{B}_coverage_cards.jsonl` |
| **Output** | `coverage_cards.jsonl` (enriched with amounts) | `{A}_vs_{B}_compare.jsonl` |
| **Modifies SSOT?** | ✅ **YES** (in-place enrichment) | ❌ NO (separate output) |
| **Deterministic?** | ⚠️ NO (LLM-based extraction) | ✅ YES (canonical code join) |
| **Used Now?** | ✅ YES (196 references in codebase) | ❌ NO (DEPRECATED per CLAUDE.md:113) |
| **Purpose** | OPTIONAL SSOT ENRICHMENT | Legacy comparison report generator |

### Answer

**step7_amount_extraction** is the active step7.

**step7_compare** is **DEPRECATED**:
- CLAUDE.md line 113 explicitly states: `~~step7_compare~~ (실행 금지, JSONL 출력만 남음)`
- Originally generated Markdown reports in `reports/` (now removed)
- Functionality superseded by step8 variants and tools/audit
- **Action**: ARCHIVE or DELETE

### Do they modify SSOT?

**CRITICAL DIFFERENCE**:
- **step7_amount_extraction**: Modifies `coverage_cards.jsonl` **in-place** (SSOT mutation)
- **step7_compare**: Creates separate comparison artifacts (read-only on SSOT)

**Constitutional Violation**: step7_amount_extraction violates SSOT immutability principle by enriching existing file. Recommendation: write to `{INS}_coverage_cards_enriched.jsonl` instead.

---

## Q3: Why does step8 exist twice?

### step8_multi_compare vs step8_single_coverage

| Aspect | step8_multi_compare | step8_single_coverage |
|--------|---------------------|----------------------|
| **Module** | `compare_all_insurers.py` | `extract_single_coverage.py` |
| **Entrypoint** | ✅ `python -m pipeline.step8_multi_compare.compare_all_insurers` | ✅ `python -m pipeline.step8_single_coverage.extract_single_coverage` |
| **Input** | `*_coverage_cards.jsonl` (3+ insurers) | `*_coverage_cards.jsonl` (all insurers) |
| **Output** | `all_insurers_compare.jsonl` | Single coverage JSON (ad-hoc query) |
| **Purpose** | Compare 3+ insurers across all canonical codes | Extract single canonical coverage across all insurers |
| **Used Now?** | ❌ NO (DEPRECATED per CLAUDE.md:114) | ⚠️ TOOL (not pipeline step) |
| **Deterministic?** | ✅ YES | ✅ YES |

### Answer

**BOTH are effectively deprecated as pipeline steps.**

**step8_multi_compare**:
- DEPRECATED per CLAUDE.md line 114: `~~step8_multi_compare~~ (실행 금지)`
- Originally part of comparison pipeline (now superseded)
- **Action**: ARCHIVE

**step8_single_coverage**:
- NOT a pipeline step; it's an **analysis tool**
- Used for ad-hoc queries (e.g., "show me A4200_1 across all insurers")
- Should be moved to `tools/` directory, not `pipeline/`
- **Action**: MOVE to `tools/query_coverage.py`

### Do they overlap?

**NO**. step8_multi_compare generates bulk comparison matrices.
step8_single_coverage is a query tool for individual coverage inspection.

**Recommendation**: Neither should occupy "step8" namespace. Rename step8_multi_compare → `_deprecated/`, move step8_single_coverage → `tools/`.

---

## Q4: Is step2_extract_pdf identical to step3_extract_text?

### Comparison

| Aspect | step2_extract_pdf | step3_extract_text |
|--------|------------------|-------------------|
| **Code Exists?** | ❌ NO (ghost directory) | ✅ YES (`extract_pdf_text.py`) |
| **Purpose** | (unknown - no code) | Extract page-by-page text from evidence PDFs |
| **Input** | (unknown) | PDF files (약관/사업방법서/상품요약서) |
| **Output** | (unknown) | `{INS}/{doc_type}/*.page.jsonl` |
| **Used Now?** | ❌ NO | ✅ YES (CORE STEP) |
| **Library** | (unknown) | PyMuPDF (fitz) |
| **Deterministic?** | (unknown) | ✅ YES |

### Answer

**Cannot confirm complete duplication because step2_extract_pdf code no longer exists.**

**Historical hypothesis** (based on naming):
- step2_extract_pdf was an early PDF extraction attempt
- step3_extract_text replaced it with better implementation (PyMuPDF)
- Refactoring deleted step2 code but left directory

**Evidence supporting hypothesis**:
- step2_extract_pdf has `__pycache__/` → code existed recently
- No references to step2_extract_pdf in current codebase (0 grep hits)
- step3_extract_text is actively used (7 references, README documentation)

### Is step3 the canonical PDF extractor?

**YES**. step3_extract_text is the **only active PDF → text extraction step**.

**Action**: DELETE `pipeline/step2_extract_pdf/` directory entirely.

---

## Structural Analysis: Why Duplications Emerged

### Timeline Reconstruction (Evidence-Based)

```
Phase 1: Initial Pipeline (unknown date)
├─ step2_extract_pdf (PDF extraction)
├─ step7_compare (insurer comparison)
├─ step8_multi_compare (multi-insurer reports)
└─ step10_audit (quality validation)

Phase 2: STEP NEXT-18 Series Refactoring (Dec 2024)
├─ STEP NEXT-18D: Add step0_scope_filter (condition sentence removal)
├─ STEP NEXT-18X-SSOT: Deprecate reports/, move to JSONL-only
│   └─ step7_compare marked as "실행 금지"
└─ coverage_cards.jsonl becomes SSOT

Phase 3: Amount Extraction Priority Shift (Dec 2024)
├─ step7_amount_extraction added (LLM-based amounts)
│   └─ Supersedes step7_compare in priority
├─ step10_audit deprecated
└─ tools/audit/** created (new audit infrastructure)

Phase 4: Scope Sanitization Consolidation (Dec 30, 2024)
├─ step0_scope_filter superseded by step1_sanitize_scope
└─ step1_sanitize_scope becomes INPUT contract (CLAUDE.md:105)

Current State: 13 step modules, 6 number collisions
```

### Root Causes

1. **No Step Numbering Authority**
   - No single document defines "step X must be Y"
   - Developers added steps with next available number without checking conflicts

2. **Deprecation Without Removal**
   - Old steps marked as deprecated in docs but code/directories remain
   - CLAUDE.md says "deprecated" but `pipeline/` still contains code

3. **Evolutionary Feature Additions**
   - step7_amount_extraction added without renumbering step7_compare
   - Both needed to coexist during transition → permanent collision

4. **Missing Lifecycle Management**
   - No `_deprecated/` or `_archive/` directory convention
   - Ghost directories (step2_extract_pdf) left behind after code deletion

---

## Impact Assessment

### Developer Confusion Scenarios

**Scenario 1**: New developer needs to extract PDF text
```bash
# Sees step2_extract_pdf directory
cd pipeline/step2_extract_pdf
ls  # No .py files! Confusion ensues.
```

**Scenario 2**: Running "step7"
```bash
# Which step7?
python -m pipeline.step7_compare.compare_insurers  # DEPRECATED!
python -m pipeline.step7_amount_extraction  # CORRECT!
```

**Scenario 3**: Documentation says step7 deprecated
```
# CLAUDE.md:113 says step7_compare deprecated
# But step7_amount_extraction is CORE and has 196 references
# Which is truth?
```

### Data Corruption Risks

**Risk 1: Wrong Step Execution**
- User runs deprecated step7_compare thinking it's current
- Generates stale comparison reports
- Misses amount-enriched data from step7_amount_extraction

**Risk 2: Input File Confusion**
- step4 uses `scope_mapped.csv`
- step5 uses `scope_mapped.sanitized.csv`
- **JOIN KEY DRIFT** → Hanwha evidence 0/41 failure

---

## Conclusion: Answers to Mandatory Questions

### Q1: Why does step2 exist twice?
**Answer**: step2_canonical_mapping is legitimate; step2_extract_pdf is a GHOST (deleted code, orphaned directory).

### Q2: Why does step7 exist twice?
**Answer**: step7_amount_extraction is active SSOT enrichment; step7_compare is deprecated comparison report generator.

### Q3: Why does step8 exist twice?
**Answer**: step8_multi_compare is deprecated; step8_single_coverage is a query tool (not pipeline step).

### Q4: Is step2_extract_pdf same as step3_extract_text?
**Answer**: Cannot confirm (no code left), but evidence suggests step3 replaced step2 during refactoring.

### Q5: Do any duplicates modify SSOT?
**Answer**: Only step7_amount_extraction modifies SSOT (in-place enrichment of coverage_cards.jsonl).

### Q6: Why did duplications arise?
**Answer**: Evolutionary development + lack of step numbering governance + deprecation without removal = namespace pollution.

---

## Next Document

See **CANONICAL_PIPELINE.md** for the single authoritative pipeline flow and **STEP_CLEANUP_PLAN.md** for remediation actions.
