# Pipeline Step Registry

**Audit Date**: 2025-12-31
**Auditor**: Claude (Pipeline Constitution Auditor)
**Purpose**: Complete inventory of all pipeline steps with evidence-based usage analysis

---

## Registry Table

| step_id | module_path | entrypoint | input_files | output_files | writes? | deterministic | purpose | downstream_reads | used_now? | notes |
|---------|-------------|------------|-------------|--------------|---------|---------------|---------|------------------|-----------|-------|
| **step0_scope_filter** | `pipeline/step0_scope_filter/coverage_candidate_filter.py` | `python -m pipeline.step0_scope_filter.coverage_candidate_filter --insurer {INS}` | `*.page.jsonl` (proposal) | `{INS}_scope.csv`, `{INS}_filtered_out.jsonl` | YES | YES (rule-based) | Filter non-coverage sentences from extracted proposals | None (deprecated) | ❌ NO | STEP NEXT-18D artifact; superseded by step1_sanitize_scope |
| **step0_scope_filter** | `pipeline/step0_scope_filter/filter_scope_mapped.py` | `python -m pipeline.step0_scope_filter.filter_scope_mapped --insurer {INS}` | `{INS}_scope_mapped.csv` | `{INS}_scope_mapped.sanitized.csv`, `{INS}_scope_filtered_out.jsonl` | YES | YES (rule-based) | Remove condition sentences from existing scope_mapped.csv | step5_build_cards | ❌ NO | Superseded by step1_sanitize_scope/run.py |
| **step1_extract_scope** | `pipeline/step1_extract_scope/run.py` | `python -m pipeline.step1_extract_scope.run --insurer {INS}` | `가입설계서/*.pdf` | `{INS}_scope.csv` | YES | ⚠️ NO (heuristic) | Extract coverage list from subscription proposal PDF | step2_canonical_mapping | ✅ YES | CORE STEP; non-deterministic table extraction |
| **step1_sanitize_scope** | `pipeline/step1_sanitize_scope/run.py` | `python -m pipeline.step1_sanitize_scope.run --insurer {INS}` | `{INS}_scope_mapped.csv` | `{INS}_scope_mapped.sanitized.csv`, `{INS}_scope_filtered_out.jsonl` | YES | YES (rule-based) | Sanitize scope_mapped.csv by removing condition sentences | step4_evidence_search, step5_build_cards | ✅ YES | CORE STEP; INPUT contract for step5 |
| **step2_canonical_mapping** | `pipeline/step2_canonical_mapping/map_to_canonical.py` | `python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer {INS}` | `{INS}_scope.csv`, `mapping 엑셀` | `{INS}_scope_mapped.csv` | YES | YES (exact match) | Map extracted coverages to canonical coverage codes | step1_sanitize_scope | ✅ YES | CORE STEP; deterministic exact match against mapping Excel |
| **step2_extract_pdf** | `pipeline/step2_extract_pdf/` | NONE | N/A | N/A | NO | N/A | Empty directory (no Python files) | None | ❌ NO | **GHOST STEP**: Directory exists but contains NO code |
| **step3_extract_text** | `pipeline/step3_extract_text/extract_pdf_text.py` | `python -m pipeline.step3_extract_text.extract_pdf_text --insurer {INS}` | PDF files (약관/사업방법서/상품요약서) | `{INS}/{doc_type}/*.page.jsonl` (evidence_text) | YES | YES (PyMuPDF) | Extract page-by-page text from evidence PDFs | step4_evidence_search | ✅ YES | CORE STEP; deterministic PDF text extraction |
| **step4_evidence_search** | `pipeline/step4_evidence_search/search_evidence.py` | `python -m pipeline.step4_evidence_search.search_evidence --insurer {INS}` | `{INS}_scope_mapped.csv`, `evidence_text/**/*.page.jsonl` | `{INS}_evidence_pack.jsonl`, `{INS}_unmatched_review.csv` | YES | YES (keyword search) | Search evidence for each coverage via deterministic keyword matching | step5_build_cards | ✅ YES | CORE STEP; **BUG**: uses scope_mapped.csv (should use sanitized) |
| **step5_build_cards** | `pipeline/step5_build_cards/build_cards.py` | `python -m pipeline.step5_build_cards.build_cards --insurer {INS}` | `{INS}_scope_mapped.sanitized.csv`, `{INS}_evidence_pack.jsonl` | `{INS}_coverage_cards.jsonl` | YES | YES (join logic) | Build coverage cards (SSOT) by joining scope + evidence | step7_amount_extraction, step7_compare, step8_multi_compare, tools/audit/** | ✅ YES | **SSOT GENERATOR**; critical join step |
| **step7_amount_extraction** | `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` | `python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer {INS}` | `{INS}_coverage_cards.jsonl`, PDFs | `{INS}_coverage_cards.jsonl` (enriched) | YES (in-place) | ⚠️ NO (LLM-based) | Extract coverage amounts from PDFs and enrich coverage_cards | step10_audit, tools/audit/** | ✅ YES | OPTIONAL ENRICHMENT; **modifies SSOT in-place** |
| **step7_compare** | `pipeline/step7_compare/compare_insurers.py` | `python -m pipeline.step7_compare.compare_insurers --insurers {A},{B}` | `{A}_coverage_cards.jsonl`, `{B}_coverage_cards.jsonl` | `{A}_vs_{B}_compare.jsonl`, `compare_stats.json` | YES | YES (canonical join) | Compare two insurers' coverage cards | None (deprecated) | ❌ NO | DEPRECATED per CLAUDE.md line 113; JSONL output only, reports/ removed |
| **step8_multi_compare** | `pipeline/step8_multi_compare/compare_all_insurers.py` | `python -m pipeline.step8_multi_compare.compare_all_insurers --insurers {A},{B},{C}` | `*_coverage_cards.jsonl` (multiple) | `all_insurers_compare.jsonl` | YES | YES (canonical join) | Compare 3+ insurers across all canonical codes | None (deprecated) | ❌ NO | DEPRECATED per CLAUDE.md line 114; 실행 금지 |
| **step8_single_coverage** | `pipeline/step8_single_coverage/extract_single_coverage.py` | `python -m pipeline.step8_single_coverage.extract_single_coverage --code {CODE}` | `*_coverage_cards.jsonl` (all insurers) | Single coverage JSONL | YES | YES | Extract single canonical coverage across all insurers | None (tool) | ⚠️ TOOL | Analysis tool, not pipeline step |
| **step10_audit** | `pipeline/step10_audit/validate_amount_lock.py` | `python -m pipeline.step10_audit.validate_amount_lock` | `*_coverage_cards.jsonl` | Audit reports | NO (read-only) | YES | Validate amount extraction quality | None (deprecated) | ❌ NO | DEPRECATED per CLAUDE.md line 116; replaced by tools/audit/** |
| **step10_audit** | `pipeline/step10_audit/audit_step7_amount_gt.py` | `python -m pipeline.step10_audit.audit_step7_amount_gt` | `*_coverage_cards.jsonl` | Audit ground truth | NO (read-only) | YES | Generate amount extraction ground truth | None (deprecated) | ❌ NO | DEPRECATED; replaced by tools/audit/run_step_next_17b_audit.py |
| **step10_audit** | `pipeline/step10_audit/preserve_audit_run.py` | Manual script | Audit artifacts | Preserved snapshots | YES | N/A | Preserve audit run snapshots | None (utility) | ❌ NO | Utility script for archival |

---

## Evidence Sources

### Usage Evidence Collection Method
```bash
# Step usage evidence gathered via:
grep -r "step{N}_" --include="*.py" --include="*.sh" --include="*.md" .
# Import analysis
grep -r "from pipeline.step" --include="*.py" .
# Entrypoint verification
grep "if __name__" pipeline/step*/*.py
```

### Usage Metrics
| Step | References in codebase | Status |
|------|------------------------|--------|
| step0_scope_filter | 10 (docs only) | DEPRECATED |
| step1_extract_scope | Active (entrypoint exists) | ACTIVE |
| step1_sanitize_scope | Active (entrypoint exists) | ACTIVE |
| step2_canonical_mapping | Active (entrypoint exists) | ACTIVE |
| step2_extract_pdf | 0 (empty directory) | GHOST |
| step3_extract_text | 7 (docs + README) | ACTIVE |
| step4_evidence_search | Active (just executed) | ACTIVE |
| step5_build_cards | Active (just executed) | ACTIVE |
| step7_amount_extraction | 196 references | ACTIVE |
| step7_compare | 22 references (deprecated docs) | DEPRECATED |
| step8_multi_compare | 16 references (docs) | DEPRECATED |
| step8_single_coverage | 5 references (tool usage) | TOOL |
| step10_audit | 0 (superseded) | DEPRECATED |

---

## Critical Findings

### 1. Step Number Duplication
- **step0**: 2 modules (coverage_candidate_filter.py, filter_scope_mapped.py)
- **step1**: 2 modules (extract_scope, sanitize_scope)
- **step2**: 2 modules (canonical_mapping, extract_pdf [GHOST])
- **step7**: 2 modules (amount_extraction, compare)
- **step8**: 2 modules (multi_compare, single_coverage)
- **step10**: 3 modules (validate_amount_lock, audit_step7_amount_gt, preserve_audit_run)

### 2. Ghost Step
- **step2_extract_pdf**: Directory exists with `__pycache__` but **NO Python source files**
  - Evidence: `ls pipeline/step2_extract_pdf/` shows only `__pycache__/` and no `.py` files
  - **Conclusion**: Deleted but directory not removed

### 3. SSOT Contamination Risk
- **step7_amount_extraction** modifies `coverage_cards.jsonl` **in-place**
  - This violates immutability principle
  - Recommendation: Write to separate enriched file OR make enrichment atomic

### 4. Input Misalignment (Constitutional Violation)
- **step4_evidence_search** uses `scope_mapped.csv` as input
- **step5_build_cards** uses `scope_mapped.sanitized.csv` as input
- → **JOIN KEY DRIFT** root cause identified
- See: Hanwha evidence not_found 0/41 failure (STEP NEXT-31 original task)

---

## Step Lifecycle Classification

| Step | Status | Reason |
|------|--------|--------|
| step0_scope_filter | DEPRECATED | Superseded by step1_sanitize_scope/run.py |
| step1_extract_scope | ACTIVE CORE | Essential: proposal PDF → scope.csv |
| step1_sanitize_scope | ACTIVE CORE | Essential: scope_mapped.csv → sanitized (INPUT contract) |
| step2_canonical_mapping | ACTIVE CORE | Essential: scope.csv → scope_mapped.csv |
| step2_extract_pdf | GHOST | No code exists; delete directory |
| step3_extract_text | ACTIVE CORE | Essential: PDFs → evidence_text/*.page.jsonl |
| step4_evidence_search | ACTIVE CORE | Essential: evidence_text + scope → evidence_pack.jsonl |
| step5_build_cards | ACTIVE CORE | **SSOT GENERATOR**: scope + evidence → coverage_cards.jsonl |
| step7_amount_extraction | ACTIVE OPTIONAL | Enrichment: coverage_cards + PDFs → amounts |
| step7_compare | DEPRECATED | Per CLAUDE.md line 113 (실행 금지) |
| step8_multi_compare | DEPRECATED | Per CLAUDE.md line 114 (실행 금지) |
| step8_single_coverage | TOOL | Analysis utility, not pipeline step |
| step10_audit | DEPRECATED | Superseded by tools/audit/run_step_next_17b_audit.py |

---

## Recommendations

1. **Delete Ghost**: Remove `pipeline/step2_extract_pdf/` directory
2. **Rename Duplicates**: Resolve step number collisions (see DUPLICATE_STEP_ANALYSIS.md)
3. **Fix Input Alignment**: step4 must use `scope_mapped.sanitized.csv` (not `scope_mapped.csv`)
4. **Archive Deprecated**: Move step0, step7_compare, step8_multi_compare, step10_audit to `_deprecated/`
5. **Document Canonical Pipeline**: Create single-source-of-truth pipeline flow (see CANONICAL_PIPELINE.md)
