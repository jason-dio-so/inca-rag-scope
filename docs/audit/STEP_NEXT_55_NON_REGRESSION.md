# STEP NEXT-55: Mapping Rate Non-Regression Verification

**Overall Status**: ✅ PASS
**Overall Mapping Rate**: 77.1% (249/323)

---

## Per-Insurer Verification

| Insurer/Variant | Baseline | Current | Delta | Status |
|-----------------|----------|---------|-------|--------|
| db_over41 | 0.0% | 96.7% | +96.7% | ✅ PASS |
| db_under40 | 0.0% | 96.7% | +96.7% | ✅ PASS |
| hanwha | 75.0% | 87.5% | +12.5% | ✅ PASS |
| heungkuk | 91.4% | 91.4% | +0.0% | ✅ PASS |
| hyundai | 20.9% | 60.5% | +39.5% | ✅ PASS |
| kb | 70.7% | 70.7% | +0.0% | ✅ PASS |
| lotte_female | 66.7% | 66.7% | +0.0% | ✅ PASS |
| lotte_male | 66.7% | 66.7% | +0.0% | ✅ PASS |
| meritz | 66.7% | 66.7% | +0.0% | ✅ PASS |
| samsung | 75.0% | 75.0% | +0.0% | ✅ PASS |

---

## Detailed Statistics

| Insurer/Variant | Total | Mapped | Unmapped | Rate |
|-----------------|-------|--------|----------|------|
| db_over41 | 30 | 29 | 1 | 96.7% |
| db_under40 | 30 | 29 | 1 | 96.7% |
| hanwha | 32 | 28 | 4 | 87.5% |
| heungkuk | 35 | 32 | 3 | 91.4% |
| hyundai | 43 | 26 | 17 | 60.5% |
| kb | 41 | 29 | 12 | 70.7% |
| lotte_female | 30 | 20 | 10 | 66.7% |
| lotte_male | 30 | 20 | 10 | 66.7% |
| meritz | 36 | 24 | 12 | 66.7% |
| samsung | 16 | 12 | 4 | 75.0% |

---

## Key Improvements (STEP NEXT-55)

**DB under40/over41**:
- Before: 0% mapped (100% unmapped due to leading dot markers)
- After: 96.7% mapped (29/30 rows)
- Root cause: `. 상해사망` → `상해사망` normalization

**Hyundai**:
- Before: ~41% mapped (34/43 rows had dot markers)
- After: 60.5% mapped (26/43 rows)
- Improvement: +19.5 percentage points

**Overall**:
- Mapping rate: 77.1%
- Total mapped: 249/323
