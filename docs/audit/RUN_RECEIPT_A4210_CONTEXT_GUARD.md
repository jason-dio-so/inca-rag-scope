# A4210 CONTEXT GUARD - RUN RECEIPT

**Date:** 2026-01-16
**Profile:** A4210_PROFILE_V1
**Gate Version:** GATE_SSOT_V2_CONTEXT_GUARD
**Database:** postgresql://localhost:5433/inca_ssot

## Execution Command

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4210 \
  --as_of_date 2025-11-26 \
  --ins_cds N01,N08 \
  --skip-chunks
```

## Results

### Rowcount Summary

| Table | Count |
|-------|-------|
| coverage_chunk | 5,219 (unchanged) |
| evidence_slot | 6 (FOUND=6, NOT_FOUND=0) |
| compare_table_v2 | 1 |

### evidence_slot Breakdown

| ins_cd | slot_key | status | gate_version |
|--------|----------|--------|--------------|
| N01 | exclusions | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |
| N01 | subtype_coverage_map | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |
| N01 | waiting_period | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |
| N08 | exclusions | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |
| N08 | subtype_coverage_map | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |
| N08 | waiting_period | FOUND | GATE_SSOT_V2_CONTEXT_GUARD |

### compare_table_v2 Metadata

```json
{
  "debug": {
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",
    "profile_id": "A4210_PROFILE_V1",
    "generated_by": "tools/run_db_only_coverage.py",
    "generated_at": "2026-01-16T12:34:15Z",
    "chunk_rowcount_at_generation": 5219
  }
}
```

## Contamination Verification

### Database Check
```sql
SELECT COUNT(*) FROM evidence_slot
WHERE coverage_code = 'A4210'
  AND excerpt ~ '통원일당|상급종합병원|연간.*회한|납입면제|보장보험료';
```

**Result:** 0 rows ✅

### API Check
```bash
curl "http://localhost:8000/compare_v2?coverage_code=A4210&as_of_date=2025-11-26&ins_cds=N01,N08" \
  | grep -E "통원일당|납입면제"
```

**Result:** (empty) ✅ NO CONTAMINATION

## DoD Verification

- ✅ Profile separation (tools/coverage_profiles.py)
- ✅ Gate engine refactor (GateContext + apply_gates)
- ✅ Payload metadata (profile_id, gate_version)
- ✅ Unit tests (3 contamination DROP, 3 normal PASS)
- ✅ Contamination elimination (0/6 contaminated)
- ✅ --skip-chunks invariant (5219 → 5219)

## Files Changed

**New:**
- tools/run_db_only_coverage.py
- tools/coverage_profiles.py
- docs/SSOT_RUNTIME_SNAPSHOT.md
- docs/audit/A4210_PROFILE_SPEC.md
- docs/audit/A4210_CONTEXT_GUARD_PROOF.md
- docs/audit/RUN_RECEIPT_A4210_CONTEXT_GUARD.md

## Reproducibility

```bash
git checkout <COMMIT_HASH>
python3 tools/run_db_only_coverage.py --coverage_code A4210 --as_of_date 2025-11-26 --ins_cds N01,N08 --skip-chunks
```

**Status:** ✅ OPERATIONAL
