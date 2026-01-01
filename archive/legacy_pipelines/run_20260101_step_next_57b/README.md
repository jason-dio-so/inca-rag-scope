# DEPRECATED: rebuild_insurer.sh

**Status**: ❌ ARCHIVED (STEP NEXT-57B)
**Date**: 2026-01-01

---

## Reason for Archival

This script was archived due to multiple SSOT violations and architectural misalignment:

1. ❌ Uses legacy `data/scope/` paths (violates SSOT constitution)
2. ❌ Calls legacy `map_to_canonical.py` module (CSV-based, deprecated)
3. ❌ CSV-based workflow (legacy format, incompatible with JSONL pipeline)
4. ❌ NOT variant-aware (cannot handle DB under40/over41, LOTTE male/female)

**Constitutional Gates Failed**:
- GATE-57B-1: Multiple Entrypoint Confusion (conflicts with `run_pipeline_v3.sh`)
- GATE-57B-2: SSOT Violation (writes to `data/scope/` instead of `data/scope_v3/`)

---

## Migration

Use canonical pipeline instead:

```bash
# ❌ OLD (WRONG):
./tools/rebuild_insurer.sh hanwha

# ✅ NEW (CORRECT):
./tools/run_pipeline_v3.sh --manifest data/manifests/proposal_pdfs_v1.json
```

### Why the Canonical Pipeline is Better

| Feature | `rebuild_insurer.sh` (OLD) | `run_pipeline_v3.sh` (NEW) |
|---------|---------------------------|----------------------------|
| Output directory | `data/scope/` (legacy) | `data/scope_v3/` (SSOT) |
| Format | CSV | JSONL |
| Variant support | ❌ NO | ✅ YES (DB/LOTTE) |
| Constitutional gates | ❌ NO | ✅ YES (4 mandatory gates) |
| Reproducibility | ⚠️ PARTIAL | ✅ FULL (fingerprint lock) |
| Profile lock | ❌ NO | ✅ YES |
| Step2 modules | Legacy (`map_to_canonical.py`) | Canonical (`run.py`) |

---

## ⚠️ DO NOT USE

This script will:
- Cause SSOT violations (outputs incompatible with canonical pipeline)
- Break variant axis (cannot handle DB/LOTTE variants)
- Fail constitutional gates (tests will reject outputs)

**If you need to rebuild pipeline outputs, use `tools/run_pipeline_v3.sh` instead.**

---

## Historical Context

**Created**: STEP NEXT-31-P3 (Atomic Rebuild Script)
**Purpose**: Single-insurer content-hash rebuild
**Deprecated**: STEP NEXT-57B (Pipeline Alignment + Legacy Purge)

**Replacement**: `tools/run_pipeline_v3.sh` (STEP NEXT-56: Pipeline Constitution Lock)
