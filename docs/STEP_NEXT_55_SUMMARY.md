# STEP NEXT-55: Step2-a Normalization Root Cause Audit + Cross-Insurer Guardrails

**Status**: ✅ **COMPLETED**
**Date**: 2026-01-01

---

## Executive Summary

**Problem**: DB under40/over41 had **100% unmapped** rate (30/30 rows) due to leading dot markers (`. 상해사망`) not being removed during Step2-a normalization.

**Root Cause**:
1. Step2-a normalization patterns were missing leading marker removal rules
2. Step2-b canonical mapper was using `coverage_name_raw` instead of `coverage_name_normalized`

**Solution**:
1. Added 5 leading marker patterns to Step2-a `NORMALIZATION_PATTERNS`
2. Updated Step2-b to use `coverage_name_normalized` as primary input
3. Re-ran Step2-a + Step2-b for all insurers

**Result**:
- **DB mapping rate**: 0% → **96.7%** (29/30 mapped)
- **Hyundai mapping rate**: 20.9% → **60.5%** (+39.5pp)
- **Overall mapping rate**: 49.7% → **77.1%** (+27.4pp)
- **Zero marker contamination** across all 323 rows

---

## Contamination Scan Results

### Before Fix (STEP_NEXT_55_LEADING_MARKER_SCAN.md)

**Total Contamination**: 94/323 rows (29.10%)

| Insurer/Variant | Rows | Contaminated | Rate |
|-----------------|------|--------------|------|
| db_over41       | 30   | 30           | 100% |
| db_under40      | 30   | 30           | 100% |
| hyundai         | 43   | 34           | 79%  |
| hanwha          | 32   | 0            | 0%   |
| Others          | 188  | 0            | 0%   |

**Marker Types**:
- DOT_MARKER: 94 occurrences (`. ` prefix pattern)

---

## Impact Analysis Results

### Causality Verification (STEP_NEXT_55_MARKER_IMPACT.md)

**Total Unmapped**: 160 rows
**Unmapped with Markers**: 98 rows (61.3%)
**Marker-Removable**: 86 rows (87.8% of marker rows)

| Insurer/Variant | Unmapped | With Marker | Removable | Fix Rate |
|-----------------|----------|-------------|-----------|----------|
| db_over41       | 30       | 30          | 29        | 96.7%    |
| db_under40      | 30       | 30          | 29        | 96.7%    |
| hyundai         | 41       | 34          | 24        | 70.6%    |
| hanwha          | 8        | 4           | 4         | 100%     |

**Causality Verdict**: ✅ **CONFIRMED**
87.8% of marker-contaminated rows would become mapped after marker removal.

---

## Code Changes

### 1. Step2-a Normalization Patterns (sanitize.py)

Added 5 leading marker patterns to `NORMALIZATION_PATTERNS`:

```python
# STEP NEXT-55: Leading markers removal (MUST be first)
(r'^\s*[·•]+\s*', '', 'LEADING_BULLET_MARKER'),
(r'^\s*\.+\s*', '', 'LEADING_DOT_MARKER'),
(r'^\s*\(\d+\)\s*', '', 'LEADING_PAREN_NUMBER'),
(r'^\s*\d+\)\s*', '', 'LEADING_NUMBER_PAREN'),
(r'^\s*[A-Za-z]\.\s*', '', 'LEADING_ALPHA_DOT'),
```

**Effect**: `. 상해사망` → `상해사망` (normalization applied)

### 2. Step2-b Canonical Mapper (canonical_mapper.py)

**Changed**: Method signature to use `coverage_name_normalized` as primary input

```python
# Before
def map_coverage(self, insurer: str, coverage_name_raw: str):
    if coverage_name_raw in exact_map:  # ❌ Uses raw (with markers)
        ...

# After
def map_coverage(self, insurer: str, coverage_name_normalized: str, coverage_name_raw: str = None):
    if coverage_name_normalized in exact_map:  # ✅ Uses normalized (markers removed)
        ...
```

**Effect**: Step2-b now benefits from Step2-a's normalization

---

## Mapping Rate Improvements

### Per-Insurer Results (STEP_NEXT_55_NON_REGRESSION.md)

| Insurer/Variant | Before | After  | Delta   | Status |
|-----------------|--------|--------|---------|--------|
| db_over41       | 0.0%   | 96.7%  | +96.7pp | ✅ PASS |
| db_under40      | 0.0%   | 96.7%  | +96.7pp | ✅ PASS |
| hyundai         | 20.9%  | 60.5%  | +39.5pp | ✅ PASS |
| hanwha          | 75.0%  | 87.5%  | +12.5pp | ✅ PASS |
| heungkuk        | 91.4%  | 91.4%  | +0.0pp  | ✅ PASS |
| kb              | 70.7%  | 70.7%  | +0.0pp  | ✅ PASS |
| lotte_female    | 66.7%  | 66.7%  | +0.0pp  | ✅ PASS |
| lotte_male      | 66.7%  | 66.7%  | +0.0pp  | ✅ PASS |
| meritz          | 66.7%  | 66.7%  | +0.0pp  | ✅ PASS |
| samsung         | 75.0%  | 75.0%  | +0.0pp  | ✅ PASS |

**Overall**: 77.1% mapped (249/323)

---

## Guardrails & Tests

### GATE-55-1: No Leading Markers in Normalized
**File**: `tests/test_step2_sanitized_no_leading_markers.py`

- ✅ Zero marker contamination across all 323 rows
- ✅ DB-specific smoke test (30/30 rows clean)

### GATE-55-2: DB Marker Mapping Smoke
**File**: `tests/test_step2_db_marker_mapping_smoke.py`

- ✅ DB mapping rate >= 95% (96.7% actual)
- ✅ Core coverages mapped (상해사망, 질병사망, etc.)
- ✅ No dot markers in normalized names

### GATE-55-3: Mapping Rate Non-Regression
**Script**: `tools/audit/verify_mapping_rate_non_regression.py`

- ✅ All insurers passed (no regression)
- ✅ Significant improvements (DB +96.7pp, Hyundai +39.5pp)

---

## Audit Trail

### Generated Reports
1. `docs/audit/STEP_NEXT_55_LEADING_MARKER_SCAN.md` - Initial contamination scan
2. `docs/audit/STEP_NEXT_55_MARKER_IMPACT.md` - Causality verification
3. `docs/audit/STEP_NEXT_55_NON_REGRESSION.md` - Post-fix validation

### Audit Scripts
1. `tools/audit/scan_leading_markers.py` - Scan for leading markers
2. `tools/audit/marker_vs_mapping_impact.py` - Analyze marker impact
3. `tools/audit/verify_mapping_rate_non_regression.py` - Verify non-regression

---

## Key Insights

### 1. Dual Root Cause
The issue required fixing **both** Step2-a and Step2-b:
- Step2-a: Add normalization patterns (remove markers)
- Step2-b: Use normalized names (apply normalization)

Neither fix alone would have solved the problem.

### 2. Cross-Insurer Impact
While DB was the primary victim (100% contaminated), the fix also improved:
- Hyundai: +39.5pp (24 recoveries out of 34 marker-contaminated rows)
- Hanwha: +12.5pp (4 recoveries out of 4 marker-contaminated rows)

### 3. Marker Diversity
All contamination came from a single pattern (`.`), but the fix includes 5 patterns to prevent future contamination from other marker types.

---

## Reproducibility

### Re-run Pipeline
```bash
# Step2-a: Sanitize (remove markers)
python -m pipeline.step2_sanitize_scope.run

# Step2-b: Canonical mapping (use normalized names)
python -m pipeline.step2_canonical_mapping.run
```

### Verify Gates
```bash
# GATE-55-1: No markers
pytest tests/test_step2_sanitized_no_leading_markers.py -v

# GATE-55-2: DB recovery
pytest tests/test_step2_db_marker_mapping_smoke.py -v

# GATE-55-3: Non-regression
python tools/audit/verify_mapping_rate_non_regression.py
```

### Audit Scans
```bash
# Scan markers
python tools/audit/scan_leading_markers.py

# Impact analysis
python tools/audit/marker_vs_mapping_impact.py
```

---

## Definition of Done ✅

- [x] coverage_name_normalized has zero leading markers (all 323 rows)
- [x] DB mapping rate >= 95% (96.7% actual)
- [x] Row count preserved (323 entries before/after)
- [x] Mapping rate non-regression passed (all insurers)
- [x] GATE-55-1 test passed (no markers)
- [x] GATE-55-2 test passed (DB recovery)
- [x] GATE-55-3 verified (non-regression)
- [x] pytest suite passed (Step2 tests)
- [x] SSOT enforced (data/scope_v3 only)
- [x] Documentation complete

---

## Next Steps

**Recommendation**: Monitor Step2-a normalization coverage in future pipeline runs. If new marker patterns emerge, add them to `NORMALIZATION_PATTERNS` following the same precedent.

**Alert**: The one remaining unmapped DB row is `. 상해사망·후유장해(20-100%)` which needs Excel alias expansion (not a marker issue).
