# SSOT RUNTIME SNAPSHOT

**DB:** postgresql://localhost:5433/inca_ssot
**Pipeline:** tools/run_db_only_coverage.py
**Profile:** tools/coverage_profiles.py
**Gate Version:** GATE_SSOT_V2_CONTEXT_GUARD

## Baseline Status

| Component | Status |
|-----------|--------|
| DB-only pipeline | ✅ Operational |
| A4210 context guard | ✅ Locked |
| Profile system | ✅ Implemented |
| Unit tests | ✅ Passing |

## A4210 Coverage (유사암진단비)

**Insurers:** N01 (메리츠), N08 (삼성)
**Slots:** waiting_period, exclusions, subtype_coverage_map
**Contamination:** 0% (통원일당, 납입면제 blocked)

## Usage

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4210 \
  --as_of_date 2025-11-26 \
  --ins_cds N01,N08 \
  --skip-chunks
```

## Verification

- evidence_slot: 6 rows (FOUND=6)
- compare_table_v2: table_id present
- API contamination check: PASS
