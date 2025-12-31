# PIPELINE INVENTORY

**Purpose**: Complete catalog of all pipeline steps, entry files, I/O artifacts, and decision points.

**Status**: FACT ONLY — NO INTERPRETATION

---

## Pipeline Steps Catalog

### STEP 0: Scope Filter (Experimental/Deprecated)
- **Entry**: `pipeline/step0_scope_filter/filter_scope_mapped.py`
- **Input**: `data/scope/{insurer}_scope_mapped.csv`
- **Output**: `data/scope/{insurer}_scope_mapped_filtered.csv`
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**: Experimental filter, NOT part of current pipeline (STEP NEXT-18X)

---

### STEP 1a: Extract Scope (Legacy — Proposal-based)
- **Entry**: `pipeline/step1_extract_scope/run.py`
- **Input**: `data/sources/insurers/{insurer}/가입설계서/*.pdf`
- **Output**: `data/scope/{insurer}_scope.csv`
  - Columns: `coverage_name_raw`, `insurer`, `source_page`
- **Coverage Existence Decision**: ✅ YES — FIRST DECISION
  - Location: `pipeline/step1_extract_scope/run.py:29-120`
  - Logic: PDF table/text parsing → extract coverage names
  - Hardening fallback: `pipeline/step1_extract_scope/hardening.py` (if count < 30)
- **Coverage Identity Decision**: NO (no coverage_code assigned)
- **Notes**:
  - Extracts raw coverage names from proposal PDFs
  - Determines "this coverage exists in this insurer's proposal"
  - NO canonical mapping yet

---

### STEP 1b: Sanitize Scope (Current SSOT Pipeline)
- **Entry**: `pipeline/step1_sanitize_scope/run.py`
- **Input**: `data/scope/{insurer}_scope_mapped.csv`
- **Output**: `data/scope/{insurer}_scope_mapped.sanitized.csv`
  - Preserves columns: `coverage_name_raw`, `coverage_code`, `mapping_status`, etc.
- **Coverage Existence Decision**: ⚠️ PARTIAL — FILTER ONLY
  - Location: `pipeline/step1_sanitize_scope/run.py:58-86`
  - Logic: DROP condition sentences, non-coverage entries
  - Does NOT create new coverages, only filters existing ones
- **Coverage Identity Decision**: NO (preserves existing coverage_code)
- **Notes**:
  - Assumes INPUT already has `coverage_code` (from STEP 2)
  - Normalizes `mapping_status` (line 134-136)
  - Outputs `*_scope_filtered_out.jsonl` audit trail

---

### STEP 2: Canonical Mapping (Legacy — Creates Identity)
- **Entry**: `pipeline/step2_canonical_mapping/map_to_canonical.py`
- **Input**:
  - Scope: `data/scope/{insurer}_scope.csv`
  - Mapping: `data/sources/mapping/담보명mapping자료.xlsx` (EXCEL — IMMUTABLE)
- **Output**: `data/scope/{insurer}_scope_mapped.csv`
  - Columns: `coverage_name_raw`, `insurer`, `source_page`, `coverage_code`, `coverage_name_canonical`, `mapping_status`, `match_type`
- **Coverage Existence Decision**: NO (preserves STEP 1a decisions)
- **Coverage Identity Decision**: ✅ YES — ASSIGNS coverage_code
  - Location: `pipeline/step2_canonical_mapping/map_to_canonical.py:110-144`
  - Logic:
    - Exact match → coverage_code
    - Normalized match → coverage_code
    - No match → mapping_status=unmatched, coverage_code=''
- **Notes**:
  - INPUT contract: Excel file (manual, NO code generation allowed per CLAUDE.md)
  - Creates canonical identity (`coverage_code`)
  - `mapping_status` = 'matched' | 'unmatched'

---

### STEP 3: Extract Text (Evidence Preparation)
- **Entry**: `pipeline/step3_extract_text/extract_pdf_text.py`
- **Input**: PDF files (약관, 사업방법서, 상품요약서)
- **Output**: `data/evidence_text/{insurer}/{doc_type}/*.page.jsonl`
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**:
  - Pure text extraction (OCR-like)
  - No coverage decisions made

---

### STEP 4: Evidence Search (Evidence Linking)
- **Entry**: `pipeline/step4_evidence_search/search_evidence.py`
- **Input**:
  - Scope: `data/scope/{insurer}_scope_mapped.csv` (or variants via resolver)
  - Text: `data/evidence_text/{insurer}/*/*.page.jsonl`
- **Output**: `data/evidence_pack/{insurer}_evidence_pack.jsonl`
- **Coverage Existence Decision**: NO (uses existing scope)
- **Coverage Identity Decision**: NO (uses existing coverage_code)
- **Notes**:
  - Links evidence to EXISTING coverages
  - Does NOT create or delete coverages
  - Uses `core/scope_gate.py` to filter

---

### STEP 5: Build Cards (SSOT Generation)
- **Entry**: `pipeline/step5_build_cards/build_cards.py`
- **Input**:
  - Scope: Resolved via `resolve_scope_csv()` (line 271)
    - Priority: sanitized → mapped → original
  - Evidence: `data/evidence_pack/{insurer}_evidence_pack.jsonl`
- **Output**: `data/compare/{insurer}_coverage_cards.jsonl` ← **SSOT**
- **Coverage Existence Decision**: NO (uses scope INPUT)
- **Coverage Identity Decision**: NO (preserves coverage_code from scope)
- **Coverage Lock Decision**: ✅ YES — LOCKS INTO SSOT
  - Location: `pipeline/step5_build_cards/build_cards.py:230-241`
  - Logic: Each scope entry → CoverageCard
  - Fields locked: `coverage_code`, `coverage_name_raw`, `mapping_status`, `evidence_status`
- **Notes**:
  - **This step creates SSOT** (coverage_cards.jsonl)
  - Uses `core/scope_gate.py:resolve_scope_csv()` (3-tier fallback)
  - Evidence selection: max 3, doc-type diversity (line 226-227)

---

### STEP 7: Amount Extraction (SSOT Enrichment)
- **Entry**: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py`
- **Input**:
  - Scope: Resolved via `resolve_scope_csv()` (line 458)
  - Proposal: `data/evidence_text/{insurer}/가입설계서/*.page.jsonl`
  - Cards: `data/compare/{insurer}_coverage_cards.jsonl`
- **Output**: `data/compare/{insurer}_coverage_cards.jsonl` (IN-PLACE UPDATE)
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Amount Decision**: ✅ YES — ADDS amount FIELD
  - Location: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:369-440`
  - Logic:
    - Extract (coverage_name, amount) from proposal
    - Match to coverage_code via normalized name
    - Enrich cards with `amount.status` = CONFIRMED | UNCONFIRMED
- **Notes**:
  - Does NOT change coverage_code
  - Does NOT add/remove coverages
  - Only enriches EXISTING cards

---

### STEP 7 Compare (Legacy Report — Execution Prohibited)
- **Entry**: `pipeline/step7_compare/compare_insurers.py`
- **Input**: Multiple `*_coverage_cards.jsonl`
- **Output**:
  - `data/compare/comparison_{hash}.jsonl`
  - `data/compare/comparison_stats_{hash}.json`
  - ~~`reports/*.md`~~ (REMOVED in STEP NEXT-18X-SSOT-FINAL)
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**:
  - Legacy report generation REMOVED (line 206-207 in STATUS.md)
  - JSONL/JSON output only
  - **DO NOT EXECUTE** (per CLAUDE.md)

---

### STEP 8: Multi-Compare (Legacy — Execution Prohibited)
- **Entry**: `pipeline/step8_multi_compare/compare_all_insurers.py`
- **Input**: All `*_coverage_cards.jsonl`
- **Output**:
  - `data/compare/multi_insurer_matrix.json`
  - `data/compare/multi_insurer_stats.json`
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**:
  - **DO NOT EXECUTE** (per CLAUDE.md)
  - SSOT-only outputs retained

---

### STEP 8: Single Coverage (Deprecated)
- **Entry**: `pipeline/step8_single_coverage/extract_single_coverage.py`
- **Input**: Unknown
- **Output**: Unknown
- **Coverage Existence Decision**: Unknown
- **Coverage Identity Decision**: Unknown
- **Notes**: File exists but NOT part of documented pipeline

---

### STEP 10: Audit (DEPRECATED)
- **Entry**:
  - `pipeline/step10_audit/validate_amount_lock.py`
  - `pipeline/step10_audit/preserve_audit_run.py`
- **Input**: `data/compare/*_coverage_cards.jsonl`
- **Output**: ~~DB audit_runs~~ (DEPRECATED)
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**:
  - **DEPRECATED** (STEP NEXT-18X-SSOT-FINAL-A)
  - Fail-fast on import (line 122-123 in STATUS.md)
  - Historical reference only

---

### Tools: Audit (Current SSOT Audit)
- **Entry**: `tools/audit/run_step_next_17b_audit.py`
- **Input**: All `*_coverage_cards.jsonl`
- **Output**: `docs/audit/AMOUNT_STATUS_DASHBOARD.md` ← **AUDIT SSOT**
- **Coverage Existence Decision**: NO
- **Coverage Identity Decision**: NO
- **Notes**:
  - Generates KPI aggregate (IN-SCOPE only)
  - Type classification
  - Structural outlier detection

---

## Resolver Logic (Canonical Scope Contract)

**File**: `core/scope_gate.py:115-154`

**Function**: `resolve_scope_csv(insurer, scope_dir)`

**Priority** (3-tier fallback):
1. `{insurer}_scope_mapped.sanitized.csv` ← HIGHEST (sanitized SSOT)
2. `{insurer}_scope_mapped.csv` ← MIDDLE (raw mapping)
3. `{insurer}_scope.csv` ← LAST (original extraction)

**Used by**:
- `pipeline/step5_build_cards/build_cards.py:271`
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py:458`

**Throws**: `FileNotFoundError` if ALL 3 fail

---

## Decision Summary Table

| Step | Existence? | Identity? | Lock to SSOT? | Notes |
|------|-----------|-----------|---------------|-------|
| **1a Extract** | ✅ FIRST | ❌ | ❌ | Creates `*_scope.csv` from proposal |
| **2 Mapping** | ❌ | ✅ ASSIGNS | ❌ | Creates `coverage_code` from Excel |
| **1b Sanitize** | ⚠️ FILTER | ❌ | ❌ | Removes non-coverages, preserves code |
| **4 Evidence** | ❌ | ❌ | ❌ | Links evidence to existing scope |
| **5 Build Cards** | ❌ | ❌ | ✅ LOCK | **Creates SSOT** (coverage_cards.jsonl) |
| **7 Amount** | ❌ | ❌ | ❌ | Enriches SSOT with amount field |
| **7/8 Compare** | ❌ | ❌ | ❌ | Legacy, execution prohibited |
| **Tools Audit** | ❌ | ❌ | ❌ | Generates audit SSOT (dashboard) |

---

## Critical Discovery

### Issue 1: "Coverage Existence" Decided TOO EARLY
- **Decision point**: STEP 1a (proposal PDF parsing)
- **Problem**: Proposal coverage names ≠ canonical coverage names
  - Example: Proposal "4대유사암" ≠ Scope "유사암(8대)"
  - Extraction happens BEFORE mapping
  - If proposal name doesn't match Excel, coverage is "unmatched" but still EXISTS in scope

### Issue 2: "Coverage Identity" Decided in ISOLATION
- **Decision point**: STEP 2 (Excel mapping)
- **Problem**: Mapping uses STATIC Excel file
  - No alias/variant generation
  - No proposal-name → canonical-name bridge
  - Mapping happens AFTER extraction → cannot fix extraction failures

### Issue 3: STEP 1b (Sanitize) is MISPLACED
- **Current order**: Extract (1a) → Map (2) → Sanitize (1b) → Build Cards (5)
- **Problem**: Sanitize expects `coverage_code` to exist (from STEP 2)
  - But runs as "STEP 1b" (confusing naming)
  - Should sanitize BEFORE mapping, but code assumes mapping already done

### Issue 4: Resolver (step5/step7) CANNOT FIX UPSTREAM FAILURES
- **Location**: `core/scope_gate.py:resolve_scope_csv()`
- **Fallback priority**: sanitized → mapped → original
- **Problem**: If STEP 1a fails to extract a coverage, NO fallback can recover it
  - Example: If "유사암(8대)" not in proposal table → never extracted → never mapped → never in SSOT

---

## Data Flow (Current Reality)

```
Proposal PDF
    ↓
[STEP 1a Extract] — DECIDES "coverage exists"
    ↓
{insurer}_scope.csv (coverage_name_raw ONLY, NO coverage_code)
    ↓
[STEP 2 Mapping] — ASSIGNS coverage_code (from Excel)
    ↓
{insurer}_scope_mapped.csv (coverage_name_raw + coverage_code + mapping_status)
    ↓
[STEP 1b Sanitize] — FILTERS non-coverages (expects coverage_code to exist)
    ↓
{insurer}_scope_mapped.sanitized.csv
    ↓
[STEP 5 Build Cards] — LOCKS to SSOT
    ↓
{insurer}_coverage_cards.jsonl ← SSOT
    ↓
[STEP 7 Amount] — ENRICHES with amount
    ↓
{insurer}_coverage_cards.jsonl (updated)
```

---

## Key Artifacts

### INPUT Contracts (Immutable)
- `data/sources/mapping/담보명mapping자료.xlsx` — Canonical mapping (manual, NO code generation)
- Proposal PDFs — Source of truth for "what customer was shown"

### INTERMEDIATE Artifacts (NOT SSOT)
- `data/scope/{insurer}_scope.csv` — Raw extraction
- `data/scope/{insurer}_scope_mapped.csv` — After mapping
- `data/scope/{insurer}_scope_mapped.sanitized.csv` — After sanitization (INPUT to STEP 5)

### SSOT Artifacts (LOCKED)
- `data/compare/{insurer}_coverage_cards.jsonl` — Coverage SSOT
- `docs/audit/AMOUNT_STATUS_DASHBOARD.md` — Audit SSOT

---

**END OF INVENTORY**
