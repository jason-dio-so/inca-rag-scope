# Canonical Pipeline Declaration

**Effective Date**: 2025-12-31
**Authority**: Pipeline Constitution Audit (STEP NEXT-31)
**Status**: OFFICIAL PIPELINE DEFINITION

---

## Constitutional Principles

1. **Single Pipeline**: One canonical execution path from PDF → SSOT
2. **Step Numbers are Unique**: No duplicates; deprecated steps archived
3. **SSOT is Sacred**: `coverage_cards.jsonl` is immutable truth (except optional enrichment)
4. **Determinism Default**: All core steps MUST be deterministic; LLM steps are OPTIONAL only
5. **Input Alignment**: Downstream steps MUST use identical scope file versions (no drift)

---

## Canonical Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     CANONICAL PIPELINE v1.0                      │
│                  (Single Source of Truth Path)                   │
└─────────────────────────────────────────────────────────────────┘

INPUTS (Immutable Tier-0 Sources)
┌────────────────────────────────────────────────────────┐
│  • data/sources/insurers/{INS}/가입설계서/*.pdf         │
│  • data/sources/insurers/{INS}/약관/*.pdf               │
│  • data/sources/insurers/{INS}/사업방법서/*.pdf         │
│  • data/sources/insurers/{INS}/상품요약서/*.pdf         │
│  • data/sources/mapping/담보명mapping자료.xlsx          │
└────────────────────────────────────────────────────────┘
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 1: Extract Scope from Proposal                    ┃
┃ Module: pipeline/step1_extract_scope/run.py            ┃
┃ Command: python -m pipeline.step1_extract_scope.run    ┃
┃         --insurer {INS}                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  가입설계서/*.pdf                                ┃
┃ Output: data/scope/{INS}_scope.csv                      ┃
┃ Deterministic: ⚠️  NO (heuristic table extraction)      ┃
┃ Contract: extracted_count >= 30                         ┃
┃ Failure: STOP if count < 30 (hardening loop triggers)   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 2: Map to Canonical Coverage Codes                ┃
┃ Module: pipeline/step2_canonical_mapping/              ┃
┃         map_to_canonical.py                             ┃
┃ Command: python -m pipeline.step2_canonical_mapping.   ┃
┃          map_to_canonical --insurer {INS}               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  {INS}_scope.csv, mapping 엑셀                   ┃
┃ Output: {INS}_scope_mapped.csv                          ┃
┃ Deterministic: ✅ YES (exact string match)              ┃
┃ Contract: mapping_rate tracked (matched/unmatched)      ┃
┃ Failure: WARN if mapping_rate < 70%, but do not STOP   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 1B: Sanitize Scope (Condition Sentence Removal)   ┃
┃ Module: pipeline/step1_sanitize_scope/run.py           ┃
┃ Command: python -m pipeline.step1_sanitize_scope.run   ┃
┃          --insurer {INS}                                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  {INS}_scope_mapped.csv                          ┃
┃ Output: {INS}_scope_mapped.sanitized.csv                ┃
┃         {INS}_scope_filtered_out.jsonl (audit trail)    ┃
┃ Deterministic: ✅ YES (rule-based DROP patterns)        ┃
┃ Contract: INPUT contract for Step 4 and Step 5          ┃
┃ Failure: STOP if output is empty                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ├──────────────────────────────────────────┐
         ▼                                          ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 3: Extract Evidence Text  ┃    ┃ (Step 1B sanitized scope     ┃
┃ Module: pipeline/               ┃    ┃  flows to Step 4 and Step 5) ┃
┃   step3_extract_text/           ┃    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┃   extract_pdf_text.py           ┃
┃ Command: python -m pipeline.    ┃
┃   step3_extract_text.           ┃
┃   extract_pdf_text              ┃
┃   --insurer {INS}               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  약관/*.pdf               ┃
┃         사업방법서/*.pdf         ┃
┃         상품요약서/*.pdf         ┃
┃ Output: data/evidence_text/     ┃
┃   {INS}/{doc_type}/*.page.jsonl ┃
┃ Deterministic: ✅ YES (PyMuPDF)  ┃
┃ Contract: All PDFs extracted     ┃
┃ Failure: STOP if extraction fails┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 4: Search Evidence (Keyword-Based)                ┃
┃ Module: pipeline/step4_evidence_search/                ┃
┃         search_evidence.py                              ┃
┃ Command: python -m pipeline.step4_evidence_search.     ┃
┃          search_evidence --insurer {INS}                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  {INS}_scope_mapped.sanitized.csv  ⚠️  FIX       ┃
┃         evidence_text/**/*.page.jsonl                   ┃
┃ Output: {INS}_evidence_pack.jsonl                       ┃
┃         {INS}_unmatched_review.csv                      ┃
┃ Deterministic: ✅ YES (keyword search + variants)       ┃
┃ Contract: evidence_found_rate tracked                   ┃
┃ Failure: WARN if found_rate < 50%, but do not STOP     ┃
┃                                                          ┃
┃ 🐛 KNOWN BUG: Currently uses scope_mapped.csv           ┃
┃              Should use scope_mapped.sanitized.csv      ┃
┃              (Constitutional Violation - Input Drift)   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 5: Build Coverage Cards (SSOT GENERATION)         ┃
┃ Module: pipeline/step5_build_cards/build_cards.py      ┃
┃ Command: python -m pipeline.step5_build_cards.         ┃
┃          build_cards --insurer {INS}                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  {INS}_scope_mapped.sanitized.csv                ┃
┃         {INS}_evidence_pack.jsonl                       ┃
┃ Output: data/compare/{INS}_coverage_cards.jsonl ⭐ SSOT ┃
┃ Deterministic: ✅ YES (join logic)                      ┃
┃ Contract: join_rate >= 95% (scope vs evidence_pack)    ┃
┃ Failure: STOP if join_rate < 95% (input staleness)     ┃
┃                                                          ┃
┃ 📊 SSOT FIELDS:                                         ┃
┃   - coverage_name_raw                                   ┃
┃   - coverage_code (canonical)                           ┃
┃   - coverage_name_canonical                             ┃
┃   - mapping_status (matched/unmatched)                  ┃
┃   - evidence_status (found/not_found)                   ┃
┃   - evidences (max 3, doc-type diverse)                 ┃
┃   - hits_by_doc_type (약관/사업방법서/상품요약서)          ┃
┃   - flags (policy_only, fallback_*, etc.)               ┃
┃   - amount (initially null, enriched in Step 7 if run)  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         │ (CORE PIPELINE ENDS HERE)
         │ (Steps below are OPTIONAL)
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 7: Amount Extraction (OPTIONAL ENRICHMENT)        ┃
┃ Module: pipeline/step7_amount_extraction/              ┃
┃         extract_and_enrich_amounts.py                   ┃
┃ Command: python -m pipeline.step7_amount_extraction.   ┃
┃          extract_and_enrich_amounts --insurer {INS}     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  {INS}_coverage_cards.jsonl                      ┃
┃         가입설계서/*.pdf (for amount extraction)         ┃
┃ Output: {INS}_coverage_cards.jsonl (IN-PLACE ENRICH)    ┃
┃ Deterministic: ⚠️  NO (LLM-based extraction)            ┃
┃ Contract: amount field populated (may be null/error)    ┃
┃ Failure: WARN if extraction_rate < 80%, DO NOT STOP    ┃
┃                                                          ┃
┃ ⚠️  CONSTITUTIONAL CONCERN:                             ┃
┃   Modifies SSOT in-place (violates immutability)        ┃
┃   Recommendation: Write to *_enriched.jsonl instead     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
         │
         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ AUDIT: Validate and Aggregate (REPORTING ONLY)         ┃
┃ Module: tools/audit/run_step_next_17b_audit.py         ┃
┃ Command: python tools/audit/run_step_next_17b_audit.py ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Input:  data/compare/*_coverage_cards.jsonl (all)       ┃
┃ Output: docs/audit/AMOUNT_STATUS_DASHBOARD.md (SSOT)   ┃
┃ Deterministic: ✅ YES (aggregation only)                ┃
┃ Contract: Read-only; generates audit reports            ┃
┃ Failure: WARN only (audit is not blocking)              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

FINAL OUTPUT (Tier-4 SSOT)
┌────────────────────────────────────────────────────────┐
│  data/compare/{INS}_coverage_cards.jsonl               │
│  (Single Source of Truth for all coverage queries)     │
└────────────────────────────────────────────────────────┘
```

---

## Step Renumbering Proposal

To eliminate duplicates and enforce unique step IDs:

| Current | Proposed | Module | Reason |
|---------|----------|--------|--------|
| step1_extract_scope | **step1** | `extract_scope/run.py` | KEEP (first extraction step) |
| step2_canonical_mapping | **step2** | `canonical_mapping/map_to_canonical.py` | KEEP (mapping is step 2) |
| step1_sanitize_scope | **step3** | `sanitize_scope/run.py` | RENAME (sanitize after mapping) |
| step3_extract_text | **step4** | `extract_text/extract_pdf_text.py` | RENAME (evidence extraction) |
| step4_evidence_search | **step5** | `evidence_search/search_evidence.py` | RENAME (search after text) |
| step5_build_cards | **step6** | `build_cards/build_cards.py` | RENAME (SSOT build) |
| step7_amount_extraction | **step7** | `amount_extraction/extract_and_enrich_amounts.py` | KEEP (enrichment) |

**Deprecated Steps** (Archive to `_deprecated/`):
- step0_scope_filter → `_deprecated/step0_scope_filter/`
- step2_extract_pdf → DELETE (ghost directory)
- step7_compare → `_deprecated/step7_compare/`
- step8_multi_compare → `_deprecated/step8_multi_compare/`
- step10_audit → `_deprecated/step10_audit/`

**Tool Relocation**:
- step8_single_coverage → `tools/query_coverage.py`

---

## Execution Sequence (Full Pipeline)

```bash
# Per-insurer pipeline (e.g., samsung)
INSURER=samsung

# CORE PIPELINE (Steps 1-5 → SSOT)
python -m pipeline.step1_extract_scope.run --insurer $INSURER
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer $INSURER
python -m pipeline.step1_sanitize_scope.run --insurer $INSURER
python -m pipeline.step3_extract_text.extract_pdf_text --insurer $INSURER
python -m pipeline.step4_evidence_search.search_evidence --insurer $INSURER
python -m pipeline.step5_build_cards.build_cards --insurer $INSURER

# OPTIONAL ENRICHMENT (Step 7)
python -m pipeline.step7_amount_extraction.extract_and_enrich_amounts --insurer $INSURER

# AUDIT (Reporting)
python tools/audit/run_step_next_17b_audit.py
```

**Multi-Insurer Execution**:
```bash
for insurer in samsung meritz db kb hanwha hyundai heungkuk lotte; do
    # Run steps 1-5 for each insurer
    # ...
done

# Audit all insurers
python tools/audit/run_step_next_17b_audit.py
```

---

## Data Flow Diagram (Tier-Based)

```
Tier 0: IMMUTABLE INPUTS
┌──────────────────────────────────────┐
│ sources/insurers/**/*.pdf            │
│ sources/mapping/담보명mapping자료.xlsx │
└──────────────────────────────────────┘
            ↓ (Step 1, Step 3)
Tier 1: EXTRACTED RAW DATA
┌──────────────────────────────────────┐
│ scope/{INS}_scope.csv                │
│ evidence_text/**/*.page.jsonl        │
└──────────────────────────────────────┘
            ↓ (Step 2)
Tier 2: MAPPED SCOPE
┌──────────────────────────────────────┐
│ scope/{INS}_scope_mapped.csv         │
└──────────────────────────────────────┘
            ↓ (Step 1B Sanitize)
Tier 3: SANITIZED SCOPE + EVIDENCE PACK
┌──────────────────────────────────────┐
│ scope/{INS}_scope_mapped.sanitized.csv│
│ evidence_pack/{INS}_evidence_pack.jsonl│
└──────────────────────────────────────┘
            ↓ (Step 5 Join)
Tier 4: SSOT (SINGLE SOURCE OF TRUTH)
┌──────────────────────────────────────┐
│ compare/{INS}_coverage_cards.jsonl ⭐ │
└──────────────────────────────────────┘
            ↓ (Step 7 Optional)
Tier 4': ENRICHED SSOT
┌──────────────────────────────────────┐
│ compare/{INS}_coverage_cards.jsonl   │
│ (with amount field populated)        │
└──────────────────────────────────────┘
            ↓ (Audit)
Tier 5: AUDIT AGGREGATES
┌──────────────────────────────────────┐
│ docs/audit/AMOUNT_STATUS_DASHBOARD.md│
└──────────────────────────────────────┘
```

---

## Critical Fixes Required

### Fix #1: Step4 Input Alignment (Constitutional Violation)

**Current State**:
```python
# step4_evidence_search/search_evidence.py:732
scope_mapped_csv = base_dir / "data" / "scope" / f"{insurer}_scope_mapped.csv"
```

**Problem**: step4 uses `scope_mapped.csv`, but step5 uses `scope_mapped.sanitized.csv`
→ JOIN KEY DRIFT → Hanwha evidence 0/41 failure

**Fix**:
```python
# step4_evidence_search/search_evidence.py:732 (CORRECTED)
from core.scope_gate import resolve_scope_csv
scope_mapped_csv = resolve_scope_csv(insurer, base_dir / "data" / "scope")
# This resolves to scope_mapped.sanitized.csv (same as step5)
```

**File**: `pipeline/step4_evidence_search/search_evidence.py:732`

---

### Fix #2: Step7 SSOT Mutation (Immutability Violation)

**Current State**: step7_amount_extraction modifies `coverage_cards.jsonl` in-place

**Problem**: Violates SSOT immutability; if amount extraction fails, SSOT is corrupted

**Recommendation**: Write to separate enriched file
```python
# Option A: Separate enriched file
output_cards_jsonl = base_dir / "data" / "compare" / f"{insurer}_coverage_cards_enriched.jsonl"

# Option B: Atomic update (backup → enrich → restore if fail)
backup = shutil.copy(cards_jsonl, f"{cards_jsonl}.backup")
try:
    enrich_amounts(cards_jsonl)
except Exception:
    shutil.move(backup, cards_jsonl)  # Restore on failure
```

---

## Core vs Optional Steps

### CORE Steps (Required for SSOT Generation)
1. **step1_extract_scope**: Proposal → scope.csv
2. **step2_canonical_mapping**: scope.csv → scope_mapped.csv
3. **step1_sanitize_scope**: scope_mapped.csv → sanitized.csv
4. **step3_extract_text**: PDFs → evidence_text/
5. **step4_evidence_search**: evidence_text + scope → evidence_pack.jsonl
6. **step5_build_cards**: scope + evidence_pack → **coverage_cards.jsonl (SSOT)**

**Pipeline Success Definition**: coverage_cards.jsonl generated with join_rate >= 95%

### OPTIONAL Steps (Enrichment/Reporting)
7. **step7_amount_extraction**: coverage_cards.jsonl → enriched with amounts
8. **Audit**: coverage_cards.jsonl → AMOUNT_STATUS_DASHBOARD.md

**Enrichment Failure**: WARN only; SSOT remains valid without amounts

---

## Failure Propagation Rules

| Step | Failure Condition | Action |
|------|-------------------|--------|
| step1 | extracted_count < 30 | STOP (hardening triggers; if still < 30, manual review) |
| step2 | mapping 엑셀 not found | STOP (cannot proceed without canonical codes) |
| step3 | PDF extraction fails | STOP (evidence required for downstream) |
| step4 | evidence_found_rate < 50% | WARN (proceed; step5 marks as not_found) |
| step5 | join_rate < 95% | STOP (input staleness detected; regenerate evidence_pack) |
| step7 | amount extraction fails | WARN (SSOT valid without amounts) |
| audit | generation fails | WARN (reporting only; no pipeline impact) |

---

## Input Snapshot Locking (Proposed)

To prevent join-key drift, implement content hash tracking:

```python
# Step4 (evidence_search) generates evidence_pack with metadata:
{
    "scope_file_hash": "sha256(...)",
    "scope_file_path": "scope_mapped.sanitized.csv",
    "generated_at": "2025-12-31T12:00:00Z",
    ...
}

# Step5 (build_cards) validates:
current_scope_hash = hashlib.sha256(open(scope_csv, 'rb').read()).hexdigest()
pack_metadata = json.loads(open(evidence_pack).readline())

if pack_metadata["scope_file_hash"] != current_scope_hash:
    raise ValueError("Evidence pack stale: scope file changed since pack generation")
```

---

## Atomic Regeneration Rule

**IF** any Tier N artifact is regenerated, **THEN** all Tier N+1 artifacts MUST be regenerated.

**Example**:
```bash
# If scope.csv changes (Tier 1)
rm data/scope/{INS}_scope_mapped.csv                      # Tier 2
rm data/scope/{INS}_scope_mapped.sanitized.csv            # Tier 3
rm data/evidence_pack/{INS}_evidence_pack.jsonl           # Tier 3
rm data/compare/{INS}_coverage_cards.jsonl                # Tier 4

# Then re-run downstream pipeline
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer {INS}
# ... (steps 3, 4, 5)
```

**Implementation**: Use `Makefile` or pipeline orchestrator with dependency tracking.

---

## Definition of Pipeline Success

A pipeline run is **SUCCESSFUL** if and only if:

1. ✅ `coverage_cards.jsonl` exists for target insurer
2. ✅ `total_coverages >= 30` (minimum scope gate)
3. ✅ `evidence_found / total_coverages >= 0.5` (50% evidence found rate)
4. ✅ No STOP-level failures in steps 1-5
5. ✅ (Optional) `amount_extraction_rate >= 0.8` if step7 executed

**Failure**: Any STOP condition triggers full pipeline halt; manual intervention required.

---

## Next Document

See **STEP_CLEANUP_PLAN.md** for concrete actions to implement this canonical pipeline.
