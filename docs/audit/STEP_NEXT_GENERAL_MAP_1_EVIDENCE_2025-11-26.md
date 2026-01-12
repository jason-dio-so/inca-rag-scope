# STEP NEXT-GENERAL-MAP-1 Evidence (2025-11-26)

**Date**: 2026-01-12
**as_of_date**: 2025-11-26
**Status**: ✅ **SUCCESS**

---

## Executive Summary

**Goal**: Enable GENERAL premium calculation via coverage code ↔ multiplier name mapping

**Result**: ✅ **1,164 GENERAL coverage records + 48 GENERAL product records created**

**Method**: Manual 1:1 mapping (ZERO TOLERANCE - no estimation)

---

## Implementation Steps

### ✅ Step 1: Create Mapping Table

**File**: `schema/091_coverage_code_name_map.sql`

**Structure**:
```sql
CREATE TABLE coverage_code_name_map (
    coverage_code TEXT PRIMARY KEY,
    multiplier_coverage_name TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Application**:
```bash
psql "$DATABASE_URL" -f schema/091_coverage_code_name_map.sql
```

**Result**:
```
CREATE TABLE
CREATE INDEX
COMMENT (×4)
```

### ✅ Step 2: Extract Coverage Codes & Multiplier Names

**Coverage Codes** (from coverage_premium_quote):
```sql
SELECT DISTINCT coverage_code
FROM coverage_premium_quote
WHERE as_of_date = '2025-11-26' AND plan_variant = 'NO_REFUND'
ORDER BY coverage_code;
```

**Total**: 33 unique coverage codes

**Multiplier Names** (from premium_multiplier):
```sql
SELECT DISTINCT coverage_name
FROM premium_multiplier
WHERE as_of_date = '2025-11-26'
ORDER BY coverage_name;
```

**Total**: 28 unique multiplier names

### ✅ Step 3: Manual Mapping

**File**: `data/premium/mapping/coverage_code_name_map_seed.sql`

**Method**: Manual 1:1 matching based on canonical coverage definitions

**Mapping Categories**:
1. Death: S100 → 상해사망, S200 → 질병사망
2. Surgery: S101 → 상해수술비, S201 → 질병수술비
3. Hospitalization: S300 → 상해입원비
4. Cancer (11 codes): A4200_1 → 암진단비(유사암제외), etc.
5. Cerebrovascular (5 codes): A5100 → 뇌혈관질환진단비, etc.
6. Cardiovascular (3 codes): A6100_1 → 허혈성심장질환진단비, etc.
7. Other diagnoses (2 codes): A9617_1 → 골절진단비(치아파절제외), etc.
8. Disability: A1100 → 상해후유장해(3~100%)

**Total Mapped**: 27 codes

**Unmapped** (6 codes):
- A1300, A3300_1, A4210, A5298_001, A9620_1, A9640_1
- Reason: Unknown/unclear coverage definitions

**Loading**:
```bash
psql "$DATABASE_URL" -f data/premium/mapping/coverage_code_name_map_seed.sql
```

**Result**:
```
TRUNCATE TABLE
INSERT 0 2
INSERT 0 2
INSERT 0 1
INSERT 0 11
INSERT 0 5
INSERT 0 3
INSERT 0 2
INSERT 0 1
```

**Verification**:
```sql
SELECT COUNT(*) as mapped_count FROM coverage_code_name_map;
```

```
 mapped_count
--------------
           27
(1 row)
```

**Coverage Percentage**:
```sql
SELECT
    (SELECT COUNT(DISTINCT coverage_code) FROM coverage_premium_quote WHERE as_of_date='2025-11-26' AND plan_variant='NO_REFUND') as total_codes,
    (SELECT COUNT(*) FROM coverage_code_name_map) as mapped_codes,
    ROUND(100.0 * (SELECT COUNT(*) FROM coverage_code_name_map) / (SELECT COUNT(DISTINCT coverage_code) FROM coverage_premium_quote WHERE as_of_date='2025-11-26' AND plan_variant='NO_REFUND'), 1) as coverage_pct;
```

```
 total_codes | mapped_codes | coverage_pct
-------------+--------------+--------------
          33 |           27 |         81.8
(1 row)
```

**Result**: **81.8% of coverage codes mapped**

### ✅ Step 4: Update GENERAL Builder

**File**: `pipeline/premium_ssot/build_general_from_no_refund.py`

**Changes**:
1. Load mapping: `SELECT coverage_code, multiplier_coverage_name FROM coverage_code_name_map`
2. Join logic:
   - Step 1: `coverage_code → multiplier_coverage_name` (via mapping)
   - Step 2: `(insurer_key, multiplier_coverage_name) → multiplier_percent` (via premium_multiplier)
3. Skip tracking: Separate counts for "no mapping" vs "no multiplier"
4. Fix: Handle `pay_term_years = 0` case (avoid constraint violation)

**Formula**: `coverage_general = round(no_refund × multiplier_percent / 100)`

### ✅ Step 5: Generate GENERAL Premium Data

**Execution**:
```bash
python3 pipeline/premium_ssot/build_general_from_no_refund.py --asOfDate 2025-11-26
```

**Output**:
```
[START] Building GENERAL premium for 2025-11-26
  Formula: coverage_general = round(no_refund × multiplier%/100)

=== STEP 1: Coverage-level GENERAL ===
[INFO] Loaded 27 coverage code mappings
[INFO] Loaded 1494 NO_REFUND coverage records
[INFO] Loaded 212 multipliers
[INFO] Generated 1164 GENERAL coverage records
[INFO] Skipped 258 coverages without mapping
[INFO] Skipped 72 coverages without multipliers
[INFO] Deleted 1164 old GENERAL coverage records
[SUCCESS] Inserted 1164 GENERAL coverage records

=== STEP 2: Product-level GENERAL ===
[INFO] Aggregated 48 GENERAL product records
[INFO] Deleted 0 old GENERAL product records
[SUCCESS] Inserted 48 GENERAL product records

[COMPLETE] GENERAL premium build finished
```

**Analysis**:
- Total NO_REFUND records: 1,494
- Mapped & multiplied: 1,164 (77.9%)
- Skipped (no mapping): 258 (17.3%)
- Skipped (no multiplier): 72 (4.8%)

---

## Database Verification

### Coverage-Level Data

```sql
SELECT plan_variant, COUNT(*) as cnt
FROM coverage_premium_quote
WHERE as_of_date = '2025-11-26'
GROUP BY plan_variant
ORDER BY plan_variant;
```

**Result**:
```
 plan_variant | cnt
--------------+------
 GENERAL      | 1164
 NO_REFUND    | 1494
(2 rows)
```

### Product-Level Data

```sql
SELECT plan_variant, COUNT(*) as cnt
FROM product_premium_quote_v2
WHERE as_of_date = '2025-11-26'
GROUP BY plan_variant
ORDER BY plan_variant;
```

**Result**:
```
 plan_variant | cnt
--------------+-----
 GENERAL      |  48
 NO_REFUND    |  48
(2 rows)
```

**Status**: ✅ **48 GENERAL products = 8 insurers × 6 segments (30/40/50 × M/F)**

### Sample GENERAL Data

```sql
SELECT insurer_key, age, sex, premium_monthly_total
FROM product_premium_quote_v2
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'GENERAL'
  AND insurer_key = 'meritz'
  AND age = 30
ORDER BY sex;
```

**Result**:
```
 insurer_key | age | sex | premium_monthly_total
-------------+-----+-----+-----------------------
 meritz      |  30 | F   |                 96279
 meritz      |  30 | M   |                108609
(2 rows)
```

**Comparison with NO_REFUND**:
```sql
SELECT plan_variant, age, sex, premium_monthly_total
FROM product_premium_quote_v2
WHERE insurer_key = 'meritz' AND age = 30 AND as_of_date = '2025-11-26'
ORDER BY plan_variant, sex;
```

```
 plan_variant | age | sex | premium_monthly_total
--------------+-----+-----+-----------------------
 GENERAL      |  30 | F   |                 96279
 GENERAL      |  30 | M   |                108609
 NO_REFUND    |  30 | F   |                 87373
 NO_REFUND    |  30 | M   |                 96111
```

**Multiplier Verification**:
- 30F: 96,279 / 87,373 ≈ 1.102 (110.2%)
- 30M: 108,609 / 96,111 ≈ 1.130 (113.0%)

**Expected**: Varies by coverage-level multipliers (not uniform across product)

---

## Zero Tolerance Compliance

✅ **NO estimation used**
- All mappings manually created
- No fuzzy matching or similarity algorithms

✅ **NO fallback applied**
- Unmapped codes → skipped (258 records)
- No multiplier → skipped (72 records)

✅ **Deterministic join**
- coverage_code → multiplier_coverage_name (via mapping table)
- (insurer_key, multiplier_coverage_name) → multiplier_percent (exact match)

✅ **Manual intervention documented**
- 27/33 codes mapped (81.8%)
- 6 unmapped codes listed with reason

---

## Impact on Q1/Q14

### Current State (NO_REFUND only)

**Q14** (보험료 Top4):
- Segments: 6 (30/40/50 × M/F)
- Rows per segment: 4
- Total: 24 rows

**Q1** (가성비 Top3):
- Segments: 6
- Rows per segment: 3
- Total: 18 rows

### Future State (with GENERAL)

**Q14**:
- Segments: 12 (6 × 2 plan_variants)
- Total: 48 rows

**Q1**:
- Segments: 12
- Total: 36 rows

**Next Step**: Rebuild Q14/Q1 to include GENERAL plan_variant

---

## Files Created/Modified

1. `schema/091_coverage_code_name_map.sql` — Mapping table schema
2. `data/premium/mapping/coverage_code_name_map_seed.sql` — 27 manual mappings
3. `pipeline/premium_ssot/build_general_from_no_refund.py` — Updated with mapping join

---

## Unmapped Coverage Codes

**Total**: 6 codes (18.2% of total)

**List**:
1. `A1300` — Unknown
2. `A3300_1` — Unknown
3. `A4210` — Unknown (possibly cancer-related)
4. `A5298_001` — Unknown (possibly cerebrovascular)
5. `A9620_1` — Unknown
6. `A9640_1` — Unknown

**Action**: Requires canonical coverage code documentation or domain expert consultation

---

## Summary

| Metric | Value |
|--------|-------|
| Coverage codes (total) | 33 |
| Mappings created | 27 (81.8%) |
| Multipliers available | 212 (8 insurers × ~26 coverages) |
| GENERAL coverage records | 1,164 |
| GENERAL product records | 48 (8 insurers × 6 segments) |
| Skip rate (no mapping) | 17.3% |
| Skip rate (no multiplier) | 4.8% |

**Status**: ✅ GENERAL premium SSOT enabled for 2025-11-26

**Next**: Rebuild Q14/Q1 rankings to include GENERAL plan_variant

---

**Document Version**: 1.0
**Status**: ✅ COMPLETE
**Last Updated**: 2026-01-12
