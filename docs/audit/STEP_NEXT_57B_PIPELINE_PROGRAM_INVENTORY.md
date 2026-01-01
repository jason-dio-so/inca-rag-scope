# STEP NEXT-57B — Pipeline Program Inventory

**Date**: 2026-01-01
**Purpose**: 100% definitive mapping of "which programs actually create Step1/Step2 outputs"

---

## 📋 Table 1: Entrypoints (Execution Paths)

| File Path | Execution Command | Input | Output | SSOT Compliant? | Variant-Aware? | Status |
|-----------|-------------------|-------|--------|-----------------|----------------|--------|
| **tools/run_pipeline_v3.sh** | `./tools/run_pipeline_v3.sh --manifest <path>` | Manifest JSON | `data/scope_v3/*_step*.jsonl` | ✅ YES | ✅ YES | ✅ CANONICAL |
| **tools/run_step1_from_manifest.sh** | `./tools/run_step1_from_manifest.sh [manifest]` | Manifest JSON | `data/scope_v3/*_step1_*.jsonl` | ✅ YES | ✅ YES | ⚠️ PARTIAL (Step1 only) |
| **tools/rebuild_insurer.sh** | `./tools/rebuild_insurer.sh <insurer>` | Insurer name | `data/scope/${INSURER}_*.csv` | ❌ NO | ❌ NO | ❌ LEGACY (uses data/scope/) |
| **pipeline.step1_summary_first.profile_builder_v3** | `python -m pipeline.step1_summary_first.profile_builder_v3 --manifest <path>` | Manifest JSON | `data/profile/*_proposal_profile_v3.json` | ✅ YES | ✅ YES | ✅ CANONICAL |
| **pipeline.step1_summary_first.extractor_v3** | `python -m pipeline.step1_summary_first.extractor_v3 --manifest <path>` | Manifest JSON + Profile | `data/scope_v3/*_step1_raw_scope_v3.jsonl` | ✅ YES | ✅ YES | ✅ CANONICAL |
| **pipeline.step2_sanitize_scope.run** | `python -m pipeline.step2_sanitize_scope.run` | `data/scope_v3/*_step1_raw_scope_v3.jsonl` (glob) | `data/scope_v3/*_step2_sanitized_scope_v1.jsonl` | ✅ YES | ✅ YES | ✅ CANONICAL |
| **pipeline.step2_canonical_mapping.run** | `python -m pipeline.step2_canonical_mapping.run` | `data/scope_v3/*_step2_sanitized_scope_v1.jsonl` (glob) | `data/scope_v3/*_step2_canonical_scope_v1.jsonl` | ✅ YES | ✅ YES | ✅ CANONICAL |
| **pipeline.step2_canonical_mapping.map_to_canonical** | `python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer <name>` | `data/scope/${INSURER}_scope.csv` | `data/scope/${INSURER}_scope_mapped.csv` | ❌ NO | ❌ NO | ❌ LEGACY (CSV-based) |

### Legend
- ✅ **CANONICAL**: Current, SSOT-compliant, variant-aware
- ⚠️ **PARTIAL**: Correct but incomplete (e.g., Step1-only)
- ❌ **LEGACY**: Uses wrong paths/formats, needs archival

---

## 📋 Table 2: Contracts (Input/Output Rules)

| Contract | Rule | Enforcement | Violation Behavior |
|----------|------|-------------|-------------------|
| **Step1 Output Naming** | `{insurer}_{variant?}_step1_raw_scope_v3.jsonl` | Filename pattern | Profile builder enforces variant suffix |
| **Step2-a Input** | MUST read Step1 raw ONLY (`*_step1_raw_scope_v3.jsonl`) | Glob pattern in `step2_sanitize_scope/run.py` | Reads all Step1 raw files automatically |
| **Step2-b Input** | MUST read Step2-a sanitized ONLY (`*_step2_sanitized_scope_v1.jsonl`) | Hard gate in `step2_canonical_mapping/run.py:73-76` | Exit code 2 if wrong input |
| **SSOT Path** | ALL outputs → `data/scope_v3/` | Code-level validation in Step2 | Exit code 2 if output path violates SSOT |
| **Variant Preservation** | DB (under40/over41), LOTTE (male/female) | Filename parsing in Step2 runners | Step2 preserves variant from Step1 filename |
| **Profile Lock** | Same PDF fingerprint → column_map MUST match | `profile_builder_v3.py:_verify_profile_lock()` | Exit code 2 if profile changes for same PDF |
| **Row Reduction Ban** | Step2-b MUST NOT reduce row count | Anti-contamination gate in canonical mapper | RuntimeError if input_count ≠ output_count |

---

## 📋 Table 3: Forbidden Dependencies (Import/Library Audit)

| Module | Forbidden Import | Actual Usage | Status |
|--------|-----------------|--------------|--------|
| **pipeline.step2_sanitize_scope** | `pipeline.step1_*` | ✅ None found | ✅ PASS |
| **pipeline.step2_canonical_mapping** | `pipeline.step1_*` | ✅ None found | ✅ PASS |
| **pipeline.step2_sanitize_scope** | `pdfplumber`, `pdf.*` | ✅ None found | ✅ PASS |
| **pipeline.step2_canonical_mapping** | `pdfplumber`, `pdf.*` | ✅ None found | ✅ PASS |
| **pipeline.step2_sanitize_scope** | `openai`, `anthropic`, LLM libraries | ✅ None found | ✅ PASS |
| **pipeline.step2_canonical_mapping** | `openai`, `anthropic`, LLM libraries | ✅ None found | ✅ PASS |

**Verification Commands**:
```bash
# Check Step2 doesn't import Step1
grep -rn "from pipeline.step1" pipeline/step2_* --include="*.py"
# (Expected: no output)

# Check Step2 doesn't use PDF
grep -rn "pdfplumber\|pdf\." pipeline/step2_* --include="*.py"
# (Expected: no output)
```

---

## 📋 Table 4: Legacy Programs (Candidates for Archival)

| File Path | Reason for Archival | Migration Path | Action Required |
|-----------|---------------------|----------------|-----------------|
| **tools/rebuild_insurer.sh** | Uses `data/scope/` (violates SSOT), calls legacy `map_to_canonical.py` | Use `tools/run_pipeline_v3.sh` instead | ⚠️ ARCHIVE + deprecation notice |
| **pipeline/step2_canonical_mapping/map_to_canonical.py** | CSV-based (legacy format), uses `data/scope/` paths | Use `pipeline.step2_canonical_mapping.run` instead | ⚠️ ARCHIVE (keeps class for reference) |
| **pipeline/step1_summary_first/debug_*.py** | Debug scripts (not part of canonical pipeline) | N/A (debugging tools) | ✅ KEEP (utility) |
| **pipeline/step1_summary_first/verify_kb_layout*.py** | Verification scripts (not part of canonical pipeline) | N/A (analysis tools) | ✅ KEEP (utility) |

### Legacy Path References (Documentation Only)
The following files contain **legacy path references in DOCSTRINGS/COMMENTS ONLY**:
- `pipeline/step2_sanitize_scope/__init__.py` (line 15-19): Comments show old `data/scope/` examples
- `pipeline/step2_canonical_mapping/__init__.py` (line 15-19): Comments show old `data/scope/` examples

**Action**: Update docstrings to reflect `data/scope_v3/` paths.

---

## 📋 Table 5: Execution Flow Diagram (Canonical vs Legacy)

### ✅ CANONICAL PIPELINE (SSOT-Compliant)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRYPOINT: tools/run_pipeline_v3.sh --manifest <path>     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1-A: profile_builder_v3 --manifest <path>             │
│   Output: data/profile/*_proposal_profile_v3.json          │
│   Gate: Profile lock (fingerprint-based)                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1-B: extractor_v3 --manifest <path>                   │
│   Output: data/scope_v3/*_step1_raw_scope_v3.jsonl         │
│   Gate: Fingerprint verification                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2-A: pipeline.step2_sanitize_scope.run                │
│   Input: data/scope_v3/*_step1_raw_scope_v3.jsonl (glob)   │
│   Output: data/scope_v3/*_step2_sanitized_scope_v1.jsonl   │
│   Gate: SSOT path enforcement, Variant preservation        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2-B: pipeline.step2_canonical_mapping.run             │
│   Input: data/scope_v3/*_step2_sanitized_scope_v1.jsonl    │
│   Output: data/scope_v3/*_step2_canonical_scope_v1.jsonl   │
│   Gate: Input contract (sanitized only), No row reduction  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    [Step 3+ continues]
```

### ❌ LEGACY PIPELINE (SSOT-Violating, DO NOT USE)

```
┌─────────────────────────────────────────────────────────────┐
│ ❌ ENTRYPOINT: tools/rebuild_insurer.sh <insurer>          │
│    (Violates SSOT: uses data/scope/)                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ❌ STEP 2 (legacy): map_to_canonical --insurer <name>      │
│    Input: data/scope/${INSURER}_scope.csv                  │
│    Output: data/scope/${INSURER}_scope_mapped.csv          │
│    Issue: CSV format, legacy paths, NOT variant-aware      │
└─────────────────────────────────────────────────────────────┘
```

**Migration**: Replace all `rebuild_insurer.sh` calls with `run_pipeline_v3.sh`.

---

## 📊 Inventory Statistics

| Metric | Count | Status |
|--------|-------|--------|
| Total entrypoints found | 8 | |
| Canonical entrypoints | 5 | ✅ |
| Partial entrypoints (Step1-only) | 1 | ⚠️ |
| Legacy entrypoints | 2 | ❌ |
| SSOT-compliant programs | 5 | ✅ |
| SSOT-violating programs | 2 | ❌ |
| Variant-aware programs | 5 | ✅ |
| Variant-unaware programs | 2 | ❌ |
| Step2 imports Step1 violations | 0 | ✅ |
| Step2 uses PDF violations | 0 | ✅ |

---

## 🎯 Alignment Recommendations

### Priority 1: Archive Legacy Programs
1. **tools/rebuild_insurer.sh** → `archive/legacy_pipelines/run_20260101_step_next_57b/rebuild_insurer.sh`
   - Add `README.md` with deprecation notice
   - Update all references to use `run_pipeline_v3.sh`

2. **pipeline/step2_canonical_mapping/map_to_canonical.py** → Keep file but add deprecation notice
   - Update docstring: "DEPRECATED: Use pipeline.step2_canonical_mapping.run instead"
   - Reason: Contains `CanonicalMapper` class still used by `run.py`

### Priority 2: Update Documentation
1. Fix docstring legacy path references:
   - `pipeline/step2_sanitize_scope/__init__.py`
   - `pipeline/step2_canonical_mapping/__init__.py`

2. Update `CLAUDE.md` to reference only canonical entrypoints

### Priority 3: Add Singleton Test
Create `tests/test_pipeline_entrypoint_singleton.py`:
- Test: No legacy `data/scope/` writes in Step2
- Test: `rebuild_insurer.sh` moved to archive (exists → FAIL)
- Test: Only canonical entrypoints exist

---

## ✅ Conclusion

**Single Source of Truth Entrypoint**: `tools/run_pipeline_v3.sh`

**Canonical Step Modules**:
- Step1: `pipeline.step1_summary_first.{profile_builder_v3, extractor_v3}`
- Step2-a: `pipeline.step2_sanitize_scope.run`
- Step2-b: `pipeline.step2_canonical_mapping.run`

**Legacy Programs Requiring Archival**: 2
- `tools/rebuild_insurer.sh` (SSOT violation)
- Legacy references in `map_to_canonical.py` (CSV-based, deprecated)

**Gates Status**: ALL PASS (no Step1 imports, no PDF usage in Step2)

**Next Action**: Execute GATE-57B tests + archive legacy programs.
