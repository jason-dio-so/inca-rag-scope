# LEGACY DIRECTORY — DO NOT USE

**⚠️ WARNING: This directory is DEPRECATED.**

## Status
- **LEGACY ONLY** — All outputs have been migrated to `data/scope_v3/`
- **DO NOT READ** — Downstream steps must use `data/scope_v3/` only
- **DO NOT WRITE** — Pipeline outputs must go to `data/scope_v3/` only

## SSOT (Single Source of Truth)
**ALL pipeline outputs MUST be in `data/scope_v3/`**:
```
data/scope_v3/{insurer}_step1_raw_scope_v3.jsonl          # Step1 output
data/scope_v3/{insurer}_step2_sanitized_scope_v1.jsonl    # Step2-a output
data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl    # Step2-b output
data/scope_v3/{insurer}_step2_dropped.jsonl               # Step2-a audit
data/scope_v3/{insurer}_step2_mapping_report.jsonl        # Step2-b audit
```

## Constitutional Rule
1. **Step1 output** → `data/scope_v3/`
2. **Step2-a/Step2-b output** → `data/scope_v3/`
3. **Step3+ input** → `data/scope_v3/` ONLY

## Archive History
- **2026-01-01 (STEP NEXT-52-HK)**: Legacy Step2 outputs moved to `archive/scope_legacy/run_20260101_step_next_52_hk/`

## Enforcement
- Code-level validation in Step2-a and Step2-b rejects non-`scope_v3/` paths
- Test suite fails if any `*_step2_*.jsonl` files exist in this directory
- See `tests/test_scope_ssot_no_legacy_step2_outputs.py`
