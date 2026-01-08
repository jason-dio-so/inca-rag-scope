# STEP NEXT-63-A: Unmapped Analysis (Constitution-Compliant)

**Date**: 2026-01-08
**Scope**: ALL insurers (post STEP NEXT-63-PREP)
**Constitution**: ACTIVE_CONSTITUTION.md §7.2

## Executive Summary

- **Total rows**: 340
- **Unmapped rows**: 62 (18.2%)
- **Classification**:
  - 🐛 **Pipeline bugs** (Excel-hit unmapped): 0 (0.0% of unmapped)
  - 📋 **Mapping gaps** (Excel-miss unmapped): 62 (100.0% of unmapped)

## Per-Insurer Breakdown

| Insurer | Total | Unmapped | Rate | Pipeline Bugs | Mapping Gaps |
|---------|-------|----------|------|---------------|--------------|
| kb           |    43 |       13 |  30.2% |             0 |           13 |
| hyundai      |    37 |       12 |  32.4% |             0 |           12 |
| meritz       |    37 |        9 |  24.3% |             0 |            9 |
| SAMSUNG      |    32 |        5 |  15.6% |             0 |            5 |
| hanwha       |    33 |        5 |  15.2% |             0 |            5 |
| lotte_female |    30 |        5 |  16.7% |             0 |            5 |
| lotte_male   |    30 |        5 |  16.7% |             0 |            5 |
| heungkuk     |    36 |        4 |  11.1% |             0 |            4 |
| db_over41    |    31 |        2 |   6.5% |             0 |            2 |
| db_under40   |    31 |        2 |   6.5% |             0 |            2 |

## Unmapped Classification (Constitution §7.2)

### 1. Excel-Hit Unmapped (Pipeline Bugs)

**Definition**: Terms that exist in `담보명mapping자료.xlsx` but were not matched by mapping logic.

**Root Cause**: Mapping logic bug (deterministic pattern matching failed).

**Action Required**: Fix mapping logic in `pipeline/step2_canonical_mapping/`.

**Count**: 0

### 2. Excel-Miss Unmapped (Mapping Gaps)

**Definition**: Terms that do NOT exist in `담보명mapping자료.xlsx`.

**Root Cause**: Coverage not in canonical mapping reference.

**Action Required**: Update `담보명mapping자료.xlsx` with new coverage definitions.

**Count**: 62

## Detail Files

Per-insurer diagnosis files (4D identity preserved):

- `data/scope_v3/SAMSUNG_step2_unmapped_diagnosis.json`
- `data/scope_v3/db_over41_step2_unmapped_diagnosis.json`
- `data/scope_v3/db_under40_step2_unmapped_diagnosis.json`
- `data/scope_v3/hanwha_step2_unmapped_diagnosis.json`
- `data/scope_v3/heungkuk_step2_unmapped_diagnosis.json`
- `data/scope_v3/hyundai_step2_unmapped_diagnosis.json`
- `data/scope_v3/kb_step2_unmapped_diagnosis.json`
- `data/scope_v3/lotte_female_step2_unmapped_diagnosis.json`
- `data/scope_v3/lotte_male_step2_unmapped_diagnosis.json`
- `data/scope_v3/meritz_step2_unmapped_diagnosis.json`

## Constitution Compliance

✅ **§7.1**: All counts are line-based (SSOT)
✅ **§7.2**: Unmapped classification = ANALYSIS ONLY (NO automatic fixing)
✅ **§2**: 4D identity preserved in all outputs
✅ **§6.3**: Unmapped defined as `mapping_method == "unmapped"`

## Next Steps

1. **Fix pipeline bugs** (0 rows):
   - Review mapping logic in `pipeline/step2_canonical_mapping/canonical_mapper.py`
   - Add missing normalization rules or exact match patterns
   - Re-run Step2-b for affected insurers

2. **Close mapping gaps** (62 rows):
   - Review unmapped terms in diagnosis files
   - Update `담보명mapping자료.xlsx` with new canonical codes
   - Re-run Step2-b after Excel update

---

**Report Generated**: 2026-01-08
**Constitution Version**: ACTIVE_CONSTITUTION.md (2026-01-08)
