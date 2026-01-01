# ⚠️ ARCHIVED — DO NOT USE

**This directory has been archived as of STEP NEXT-53 (2026-01-01)**

## Archive Location
```
archive/legacy_outputs/run_20260101_004654_step_next_53/data_scope/
```

## Use Instead
**SSOT (Single Source of Truth)**: `data/scope_v3/`

All pipeline outputs now reside in `data/scope_v3/`:
- `*_step1_raw_scope_v3.jsonl` — Step1 extraction
- `*_step2_sanitized_scope_v1.jsonl` — Step2-a sanitization
- `*_step2_canonical_scope_v1.jsonl` — Step2-b canonical mapping

## Why Archived?
This directory contained legacy Step1 outputs from deprecated pipelines:
- `step1_extract_scope` (replaced by `step1_summary_first`)
- Manual CSV exports and mapping artifacts

The canonical pipeline now follows:
```
manifest → step1_summary_first → step2_sanitize_scope → step2_canonical_mapping
```

See `CLAUDE.md` for current runbook.
