# STEP NEXT-GENERAL-SSOT Evidence (2025-11-26)

**Date**: 2026-01-12
**as_of_date**: 2025-11-26
**Status**: ⚠️ **BLOCKED - Coverage Name Mismatch**

---

## Executive Summary

**Goal**: Enable GENERAL premium calculation from NO_REFUND × multipliers

**Result**: **BLOCKED** due to fundamental naming mismatch between API data and multiplier Excel

**Formula**: `coverage_general = round(no_refund × multiplier_percent / 100)`

**Blocker**: Coverage codes (API) ≠ Coverage names (Excel)

---

## Steps Completed

### ✅ (A) Schema Migration

**File**: `schema/090_premium_multiplier_asof.sql`

**Changes**:
- Added `as_of_date DATE NOT NULL` to `premium_multiplier`
- Updated UNIQUE constraint to `(insurer_key, coverage_name, as_of_date)`
- Added index on `as_of_date`
- Updated lookup index to include `as_of_date`

**Application**:
```bash
psql "$DATABASE_URL" -f schema/090_premium_multiplier_asof.sql
```

**Result**:
```
ALTER TABLE
UPDATE 0
ALTER TABLE
ALTER TABLE
ALTER TABLE
CREATE INDEX
DROP INDEX
CREATE INDEX
COMMENT
```

**Verification**:
```sql
\d premium_multiplier
```

**Schema After Migration**:
```
 multiplier_id      | integer                     | not null | nextval('premium_multiplier_multiplier_id_seq'::regclass)
 insurer_key        | text                        | not null |
 coverage_name      | text                        | not null |
 multiplier_percent | numeric(5,2)                | not null |
 source_file        | text                        | not null |
 source_row_id      | integer                     |          |
 created_at         | timestamp without time zone |          | CURRENT_TIMESTAMP
 as_of_date         | date                        | not null |

Indexes:
    "premium_multiplier_pkey" PRIMARY KEY, btree (multiplier_id)
    "idx_multiplier_asof" btree (as_of_date)
    "idx_multiplier_lookup_v2" btree (insurer_key, coverage_name, as_of_date)
    "uq_insurer_coverage_asof" UNIQUE CONSTRAINT, btree (insurer_key, coverage_name, as_of_date)
```

### ✅ (B) Multiplier Excel Loader

**File**: `tools/premium/load_multiplier_from_excel.py`

**Source**: `data/sources/insurers/4. 일반보험요율예시.xlsx`

**Execution**:
```bash
python3 tools/premium/load_multiplier_from_excel.py --asOfDate 2025-11-26
```

**Output**:
```
[START] Loading multipliers from Excel
  Excel: data/sources/insurers/4. 일반보험요율예시.xlsx
  as_of_date: 2025-11-26
  DB: 127.0.0.1:5432/inca_rag_scope

[INFO] Loaded Excel: 30 rows, 9 columns
[WARN] Invalid multiplier (0.0) for heungkuk/다빈치로봇암수술비 - SKIP
[INFO] Extracted 220 valid multiplier records
[INFO] Skipped 0 rows with null coverage names
[SUCCESS] Inserted/updated 220 multiplier records
[VERIFY] as_of_date=2025-11-26, total_rows=212
[VERIFY] Insurer breakdown:
  db: 27 rows
  hanwha: 25 rows
  heungkuk: 27 rows
  hyundai: 28 rows
  kb: 28 rows
  lotte: 27 rows
  meritz: 26 rows
  samsung: 24 rows

[COMPLETE] Multiplier load finished successfully
```

**Database Verification**:
```sql
SELECT insurer_key, COUNT(*) as cnt
FROM premium_multiplier
WHERE as_of_date = '2025-11-26'
GROUP BY insurer_key
ORDER BY insurer_key;
```

**Result**:
```
 insurer_key | cnt
-------------+-----
 db          |  27
 hanwha      |  25
 heungkuk    |  27
 hyundai     |  28
 kb          |  28
 lotte       |  27
 meritz      |  26
 samsung     |  24
(8 rows)
```

**Total**: 212 multipliers loaded successfully

### ✅ (C) GENERAL Premium Builder

**File**: `pipeline/premium_ssot/build_general_from_no_refund.py`

**Formula**: `coverage_general = round(no_refund × multiplier_percent / 100)`

**Execution**:
```bash
python3 pipeline/premium_ssot/build_general_from_no_refund.py --asOfDate 2025-11-26
```

**Output**:
```
[START] Building GENERAL premium for 2025-11-26
  Formula: coverage_general = round(no_refund × multiplier%/100)

=== STEP 1: Coverage-level GENERAL ===
[INFO] Loaded 1494 NO_REFUND coverage records
[INFO] Loaded 212 multipliers
[INFO] Generated 0 GENERAL coverage records
[INFO] Skipped 1494 coverages without multipliers
[WARN] No GENERAL records to insert

=== STEP 2: Product-level GENERAL ===
[INFO] Aggregated 0 GENERAL product records
[WARN] No GENERAL product records to insert

[COMPLETE] GENERAL premium build finished
```

**Result**: **0 GENERAL records generated**

---

## ⚠️ BLOCKER Analysis

### Root Cause

**Coverage Namespace Mismatch**:

**API Data** (coverage_premium_quote):
- Uses `coverage_code` (e.g., S100, A4200_1, C1100)
- `coverage_title_raw`: NULL
- `coverage_name_normalized`: NULL

**Multiplier Excel** (premium_multiplier):
- Uses Korean coverage names (e.g., "상해사망", "암진단비(유사암제외)", "질병사망")
- NO coverage codes

**Join Attempt**:
```python
multiplier_key = (row["insurer_key"], coverage_key)
multiplier = multipliers.get(multiplier_key)  # ← ALWAYS RETURNS None
```

**Why It Fails**:
- API: `(meritz, S100)` → coverage_name = NULL
- Excel: `(meritz, "상해사망")` → coverage_code = UNKNOWN
- **No common key to join on**

### Evidence

**Sample API Data**:
```sql
SELECT coverage_code, coverage_title_raw, coverage_name_normalized, premium_monthly_coverage
FROM coverage_premium_quote
WHERE insurer_key = 'meritz'
  AND as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
LIMIT 5;
```

**Result**:
```
 coverage_code | coverage_title_raw | coverage_name_normalized | premium_monthly_coverage
---------------+--------------------+--------------------------+--------------------------
 S100          |                    |                          |                     1124
 S110          |                    |                          |                     3278
 S200          |                    |                          |                     2186
 A4200_1       |                    |                          |                    29933
 A4200_2       |                    |                          |                    13467
```

**Sample Multiplier Data**:
```sql
SELECT insurer_key, coverage_name, multiplier_percent
FROM premium_multiplier
WHERE insurer_key = 'meritz'
  AND as_of_date = '2025-11-26'
LIMIT 5;
```

**Result**:
```
 insurer_key | coverage_name | multiplier_percent
-------------+---------------+--------------------
 meritz      | 상해사망       |             120.00
 meritz      | 질병사망       |             122.00
 meritz      | 암진단비(유사암제외) |         134.00
 meritz      | 고액암진단비   |             117.00
 meritz      | 유사암진단비   |             130.00
```

**Coverage Code Examples**:
- `S100` → ??? (Unknown Korean name)
- `A4200_1` → "암진단비(유사암제외)" (POSSIBLE, but not confirmed)
- `C1100` → ??? (Unknown Korean name)

### Join Attempts

**Attempt 1: coverage_name_normalized**
```python
coverage_key = row["coverage_name_normalized"]  # → NULL
multiplier_key = (row["insurer_key"], coverage_key)  # → (meritz, NULL)
multiplier = multipliers.get(multiplier_key)  # → None (NULL never matches)
```

**Attempt 2: coverage_title_raw**
```python
coverage_key = row["coverage_title_raw"]  # → NULL
# Same failure
```

**Attempt 3: coverage_code (not attempted, would also fail)**
```python
# Multiplier table has NO coverage_code column
# Cannot join on codes
```

---

## Resolution Options

### Option 1: Manual Coverage Code ↔ Name Mapping Table

**Approach**: Create `coverage_code_name_map` table

**Structure**:
```sql
CREATE TABLE coverage_code_name_map (
    coverage_code TEXT NOT NULL,
    coverage_name TEXT NOT NULL,
    insurer_key TEXT,  -- NULL = applies to all insurers
    PRIMARY KEY (coverage_code, COALESCE(insurer_key, ''))
);
```

**Example Data**:
```sql
INSERT INTO coverage_code_name_map VALUES
    ('A4200_1', '암진단비(유사암제외)', NULL),
    ('S100', '상해사망', NULL),
    ('S200', '질병사망', NULL);
```

**Builder Change**:
```python
# Step 1: Load mapping
cur.execute("SELECT coverage_code, coverage_name FROM coverage_code_name_map")
code_to_name = {row["coverage_code"]: row["coverage_name"] for row in cur}

# Step 2: Join using mapping
for row in no_refund_rows:
    coverage_code = row["coverage_code"]
    coverage_name = code_to_name.get(coverage_code)  # ← Use mapping

    if not coverage_name:
        skipped += 1
        continue

    multiplier_key = (row["insurer_key"], coverage_name)
    multiplier = multipliers.get(multiplier_key)
```

**Pros**:
- Clean, deterministic
- Versionable (can add as_of_date if codes change)

**Cons**:
- Requires manual mapping creation (tedious but one-time)
- ~30-50 codes to map

### Option 2: Enrich API Data with Korean Names

**Approach**: Modify API loader to populate `coverage_title_raw` from a lookup table

**Builder Change**: None (current logic would work)

**Cons**:
- Requires reverse-engineering API coverage codes
- May not be feasible if API doesn't provide names

### Option 3: Use Coverage Code in Multiplier Excel

**Approach**: Add coverage_code column to Excel, reload multipliers

**Cons**:
- Requires Excel modification
- Still needs manual code assignment

---

## Current State Summary

| Component | Status | Records | Notes |
|-----------|--------|---------|-------|
| premium_multiplier | ✅ LOADED | 212 | Korean names, 8 insurers |
| coverage_premium_quote (NO_REFUND) | ✅ LOADED | 1494 | Coverage codes only |
| coverage_premium_quote (GENERAL) | ⚠️ BLOCKED | 0 | Cannot join |
| product_premium_quote_v2 (GENERAL) | ⚠️ BLOCKED | 0 | Depends on coverage |

---

## Recommendation

**SHORT TERM**: Create `coverage_code_name_map` table with manual mappings for common coverages (Option 1)

**PRIORITY MAPPINGS** (for Q1/Q14):
- `A4200_1` → "암진단비(유사암제외)" (cancer diagnosis, needed for Q1)
- Other high-frequency codes

**EXECUTION PLAN**:
1. Extract unique coverage_code list from API data
2. Create mapping table schema
3. Manually map codes to Excel names (with insurer validation)
4. Update builder to use mapping
5. Re-run build

---

## Files Created

1. `schema/090_premium_multiplier_asof.sql` — Schema migration
2. `tools/premium/load_multiplier_from_excel.py` — Excel loader (functional)
3. `pipeline/premium_ssot/build_general_from_no_refund.py` — GENERAL builder (blocked)

---

## Next Steps

1. **DECISION**: Choose resolution option (recommend Option 1)
2. **MAPPING**: Create coverage_code ↔ name mapping (manual work)
3. **UPDATE**: Modify builder to use mapping
4. **RETRY**: Re-run GENERAL build
5. **Q14/Q1**: Extend rankings to GENERAL (if GENERAL data exists)

---

## Zero Tolerance Compliance

✅ **NO estimation or fallback used**
✅ **NO default multipliers applied**
✅ **Blocker documented, not bypassed**
✅ **0 GENERAL records correctly reflects inability to join**

**Status**: Task completed to the extent possible without manual intervention. Further progress requires coverage name mapping.

---

**Document Version**: 1.0
**Status**: ⚠️ BLOCKED (DOCUMENTED)
**Last Updated**: 2026-01-12
