# STEP 4-λ — Regression Test Report (8 Insurers)

## Test Objective

Verify that Hanwha-specific fallback enhancements do NOT impact evidence search results for other 7 insurers.

## Test Scope

**Insurers Tested**: 8
- samsung
- meritz
- db
- lotte
- kb
- hyundai
- heungkuk
- hanwha (target)

**Metric**: Evidence nonempty/empty counts

**Expected**: 0 delta for all non-hanwha insurers

## Test Results

| Insurer | Total | Matched | Unmatched | Nonempty | Empty | Status |
|---------|-------|---------|-----------|----------|-------|--------|
| samsung | 41 | 33 | 8 | 40 | 1 | ✅ UNCHANGED |
| meritz | 34 | 26 | 8 | 27 | 7 | ✅ UNCHANGED |
| db | 31 | 26 | 5 | 31 | 0 | ✅ UNCHANGED |
| lotte | 37 | 30 | 7 | 35 | 2 | ✅ UNCHANGED |
| kb | 45 | 25 | 20 | 37 | 8 | ✅ UNCHANGED |
| hyundai | 37 | 25 | 12 | 33 | 4 | ✅ UNCHANGED |
| heungkuk | 36 | 30 | 6 | 32 | 4 | ✅ UNCHANGED |
| **hanwha** | **37** | **23** | **14** | **20** | **17** | **✅ IMPROVED** |

## Delta Analysis

### Non-Hanwha Insurers (7)

**Nonempty Delta**: 0
**Empty Delta**: 0

**Regression Count**: **0**

✅ All 7 insurers maintained exact same evidence counts.

### Hanwha (Target)

**Before (STEP 4-κ)**:
- Nonempty: 13
- Empty: 24

**After (STEP 4-λ)**:
- Nonempty: 20
- Empty: 17

**Delta**:
- Nonempty: **+7** ✅
- Empty: **-7** ✅

**Improvement**: 13 → 20 (53.8% increase in nonempty)

## Fallback Isolation Verification

**Code Gating**: All fallback logic wrapped in:
```python
if self.insurer == 'hanwha':
    # Fallback logic here
```

**Verification Method**:
1. Ran full evidence search pipeline for all 8 insurers
2. Compared output evidence pack JSONL files
3. Counted nonempty/empty per insurer
4. Verified 0 delta for non-hanwha

**Result**: ✅ **PASS** (Hanwha-only isolation confirmed)

## Test Execution

```bash
# Run evidence search for all insurers
for insurer in samsung meritz db lotte kb hyundai heungkuk hanwha; do
    python -m pipeline.step4_evidence_search.search_evidence --insurer $insurer
done

# Verify counts
python3 << 'PYEOF'
import json
from pathlib import Path

for insurer in ['samsung', 'meritz', 'db', 'lotte', 'kb', 'hyundai', 'heungkuk', 'hanwha']:
    pack_file = Path(f'data/evidence_pack/{insurer}_evidence_pack.jsonl')
    rows = [json.loads(line) for line in open(pack_file) if line.strip()]
    nonempty = sum(1 for r in rows if len(r['evidences']) > 0)
    empty = sum(1 for r in rows if len(r['evidences']) == 0)
    print(f"{insurer}: nonempty={nonempty}, empty={empty}")
PYEOF
```

## pytest Validation

```bash
pytest -q
```

**Result**: ✅ **75 passed in 0.45s**

All existing tests continue to pass, including:
- test_scope_gate.py (11 tests)
- test_evidence_pack.py (7 tests)
- test_coverage_cards.py (10 tests)
- test_comparison.py (7 tests)
- test_consistency.py (7 tests)
- test_multi_insurer.py (8 tests)
- test_evidence_source_coverage.py (6 tests)
- test_single_coverage_a4200_1.py (9 tests)
- test_multi_insurer_a4200_1.py (10 tests)

## Conclusion

✅ **REGRESSION TEST PASSED**

**Summary**:
- 0 changes in 7 insurers (samsung, meritz, db, lotte, kb, hyundai, heungkuk)
- +7 nonempty improvement in hanwha (target insurer)
- 0 test failures
- Code isolation verified (hanwha-only gating)

**Confidence Level**: **HIGH**

The fallback enhancements are correctly isolated to Hanwha and do not affect other insurers.

---

**Date**: 2025-12-27
**STEP**: 4-λ (Hanwha Evidence Search Fallback)
**Status**: ✅ **COMPLETE**
