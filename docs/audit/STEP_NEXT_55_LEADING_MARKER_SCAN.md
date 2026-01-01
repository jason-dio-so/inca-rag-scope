# STEP NEXT-55: Leading Marker Contamination Scan

**Scan Date**: 1767231757.1110687
**Total Insurers/Variants**: 10
**Total Rows**: 323
**Marker Hits**: 0
**Contamination Rate**: 0.00%

---

## Summary by Insurer/Variant

| Insurer/Variant | Total Rows | Marker Hits | Contamination % |
|-----------------|------------|-------------|-----------------|
| db_over41 | 30 | 0 | 0.00% |
| db_under40 | 30 | 0 | 0.00% |
| hanwha | 32 | 0 | 0.00% |
| heungkuk | 35 | 0 | 0.00% |
| hyundai | 43 | 0 | 0.00% |
| kb | 41 | 0 | 0.00% |
| lotte_female | 30 | 0 | 0.00% |
| lotte_male | 30 | 0 | 0.00% |
| meritz | 36 | 0 | 0.00% |
| samsung | 16 | 0 | 0.00% |

---

## Marker Type Distribution (All Insurers)

| Marker Type | Total Count |
|-------------|-------------|

---

## Examples by Insurer/Variant (Top 20 per insurer)

---

## Root Cause Verdict

**Observation**:
- 0 rows (0.00%) have leading markers in `coverage_name_normalized`
- This confirms Step2-a normalization is missing marker removal patterns

**Action Required**:
- Add LEADING_BULLET_MARKER, LEADING_DOT_MARKER patterns to NORMALIZATION_PATTERNS
- Re-run Step2-a to clean coverage_name_normalized
- Verify GATE-55-1 (zero marker contamination)
