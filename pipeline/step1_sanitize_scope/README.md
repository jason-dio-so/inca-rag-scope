# ⚠️ ARCHIVED — DO NOT USE

**This pipeline has been archived as of STEP NEXT-53 (2026-01-01)**

## Archive Location
```
archive/legacy_pipelines/run_20260101_004654_step_next_53/step1_sanitize_scope/
```

## Use Instead
**Canonical Step2-a**: `pipeline/step2_sanitize_scope/`

Current sanitization pipeline:
- `run.py` — JSONL-only sanitization (no PDF, no LLM)
- `sanitize.py` — Deterministic pattern matching

## Why Archived?
This was the legacy Step1-level sanitization:
- Mixed Step1/Step2 concerns (constitutional violation)
- Unclear input/output contract

Sanitization is now Step2-a:
- Input: `*_step1_raw_scope_v3.jsonl` (from Step1)
- Output: `*_step2_sanitized_scope_v1.jsonl` (to Step2-b)
- NO Step1 module imports (independence gate)

## Migration
```bash
# OLD (deprecated)
python -m pipeline.step1_sanitize_scope.run --insurer hanwha

# NEW (canonical)
python -m pipeline.step2_sanitize_scope.run --insurer hanwha
```

See `CLAUDE.md` for full runbook.
