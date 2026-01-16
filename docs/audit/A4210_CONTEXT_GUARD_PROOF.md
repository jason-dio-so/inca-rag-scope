# A4210 CONTEXT GUARD PROOF

**Date:** 2026-01-16
**Database:** localhost:5433/inca_ssot
**Coverage:** A4210 (유사암진단비)
**Gate Version:** GATE_SSOT_V2_CONTEXT_GUARD

## Objective

Block 3 contamination cases in N08:
1. 통원일당 담보 혼입 (케이스 1+2)
2. 납입면제 섹션 혼입 (케이스 3)

## Implementation

### 5-Gate Context Guard

1. **GATE 1:** Anchor in excerpt (baseline)
2. **GATE 2:** Hard-negative check → DROP 통원일당, 상급종합병원, 연간n회한, 100세만기
3. **GATE 3:** Section-negative check → DROP 납입면제, 보장보험료, 면제 사유
4. **GATE 4:** Diagnosis-signal required → DROP if missing 진단비, 보험금
5. **GATE 5:** Coverage name lock → DROP if failed (유사암 + 진단비 tokens)

### Functions Added (tools/run_db_only_coverage.py)

- `GateContext` class
- `apply_gates(slot_key, chunk_text, excerpt, ctx)` → (bool, reasons)
- Profile-based validation

## BEFORE vs AFTER

### Contamination Case 1+2: 통원일당

**BEFORE (Anchor-lock only):**
```
excerpt: "·암 직접치료 통원일당(상급종합병원)(연간10회한) 100세만기"
status: FOUND (contaminated)
```

**AFTER (Context Guard):**
```
excerpt: "·유사암(90일면책) 진단비(1년50%)"
status: FOUND (clean)
DROP reason: hard_negative (통원일당, 상급종합병원)
```

### Contamination Case 3: 납입면제

**BEFORE (Anchor-lock only):**
```
excerpt: "납입면제의 보장개시일 ... 암 진단비(유사암 제외)"
status: FOUND (contaminated)
```

**AFTER (Context Guard):**
```
excerpt: "·유사암(90일면책) 진단비(1년50%)"
status: FOUND (clean)
DROP reason: section_negative (납입면제, 보장보험료)
```

## Verification

### Database Check
```sql
SELECT ins_cd, slot_key,
  CASE WHEN excerpt ~ '통원일당|납입면제' THEN 'CONTAMINATED' ELSE 'CLEAN' END
FROM evidence_slot
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26';
```

**Result:** 6/6 slots CLEAN (0% contamination)

### API Check
```bash
curl "http://localhost:8000/compare_v2?coverage_code=A4210" | grep -E "통원일당|납입면제"
```

**Result:** (empty) ✅ NO CONTAMINATION

## Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Contaminated slots (N08) | 3/3 (100%) | 0/6 (0%) | ✅ -100% |
| FOUND slots | 6/6 | 6/6 | ✅ Maintained |
| Chunk count | 5,219 | 5,219 | ✅ Unchanged |

## DoD

- ✅ Contamination cases (3) blocked with gate reasons
- ✅ Normal cases (3) pass validation
- ✅ API shows zero contamination keywords
- ✅ Chunk rowcount unchanged (--skip-chunks)
