# ⚠️ ARCHIVED — DO NOT USE

**This pipeline has been archived as of STEP NEXT-53 (2026-01-01)**

## Archive Location
```
archive/legacy_pipelines/run_20260101_004654_step_next_53/step1_extract_scope/
```

## Use Instead
**Canonical Step1**: `pipeline/step1_summary_first/`

Current Step1 pipeline:
- `profile_builder_v3.py` — Manifest-driven profile builder
- `extractor_v3.py` — Manifest-driven extraction with fingerprint gate
- `pdf_fingerprint.py` — PDF change detection

## Why Archived?
This was the legacy Step1 extraction pipeline (pre-v3):
- No manifest support
- No fingerprint gate
- No profile-based extraction
- Outputs to `data/scope/` (deprecated)

The canonical pipeline (v3) now:
- Uses manifest SSOT (`data/manifests/proposal_pdfs_v1.json`)
- Implements fingerprint gate (fail-fast on PDF changes)
- Outputs to `data/scope_v3/` (SSOT)

## Migration
```bash
# OLD (deprecated)
python -m pipeline.step1_extract_scope.run --insurer hanwha

# NEW (canonical)
python -m pipeline.step1_summary_first.profile_builder_v3 --manifest data/manifests/proposal_pdfs_v1.json --insurer hanwha
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/manifests/proposal_pdfs_v1.json --insurer hanwha
```

See `CLAUDE.md` for full runbook.
