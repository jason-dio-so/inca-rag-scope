# Q13 Ready Evidence (2026-01-13)

## Status
**READY (LIMITED MODE)**

## Implementation Summary
- API: `GET /q13` endpoint
- UI: Q13SubtypeCoverageCard component + standalone page `/q13`
- SSOT: `docs/audit/step_next_81c_subtype_coverage_locked.jsonl`
- Data completeness: **1/8 insurers** (KB only)

## Validation Results

### API Response Validation
```
✅ Query ID: Q13
✅ Data completeness: 1/8
✅ Matrix rows: 8
✅ KB in_situ: ⚠️ 진단비 아님(치료비 트리거)
✅ KB borderline: ⚠️ 진단비 아님(치료비 트리거)
✅ samsung in_situ: — NO_DATA
✅ treatment_trigger as O: ✅ PASS
```

### Output Rules (LOCKED)
- ✅ diagnosis_benefit → "O" (✅, green, usable=true)
- ✅ treatment_trigger → "⚠️ 진단비 아님(치료비 트리거)" (orange, usable=false)
- ✅ NO_DATA → "—" (gray, NOT excluded)
- ✅ NEVER show treatment_trigger as "O" (HARD LOCK violated: 0 cases)

### Coverage
- **KB**: 1 담보 (표적항암약물허가치료비, 치료비 타입)
  - in_situ: treatment_trigger ✅
  - borderline: treatment_trigger ✅
- **Other 7 insurers**: NO_DATA (— displayed, NOT X)

## Policy
- docs/audit/STEP_NEXT_82_Q13_OUTPUT_LOCK.md
- SSOT Gate: step_next_81c_subtype_coverage_locked.jsonl ONLY

## Limitations
- LIMITED MODE: Only 1 insurer (KB) has data
- Comparison matrix is 8×2 but 7 rows show NO_DATA
- NOT a blocker: UI/API correctly distinguish NO_DATA from excluded (X)

## Next Steps
- Expand SSOT to all insurers (requires Step3/Step4 pipeline extension)
- Add more diagnosis_benefit coverage (current KB coverage is treatment_trigger only)

## DoD
- [x] API endpoint /q13 functional
- [x] UI renders matrix (8 insurers × 2 subtypes)
- [x] NO_DATA displayed as "—" not "X"
- [x] treatment_trigger NOT shown as "O"
- [x] Evidence refs accessible (KB has evidence)
- [x] Commit complete

---
Created: 2026-01-13
Status: **READY (LIMITED)**
