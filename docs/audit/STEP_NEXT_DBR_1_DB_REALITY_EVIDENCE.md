# STEP NEXT-DBR-1: DB Reality Re-Audit - Evidence Report

**Date:** 2026-01-09
**Database:** inca_rag_scope @ localhost:5432
**Purpose:** Prove actual DB schema state with hard psql evidence (NO ASSUMPTIONS)

---

## 0) Executive Summary

**VERDICT:** ✅ **DB1 CLAIM TRUE WITH CRITICAL FINDINGS**

**Schema Status:**
- ✅ ALL 5 premium tables EXIST
- ✅ Schema DDL is CORRECT (as_of_date exists, NOT base_dt)
- ❌ ALL tables are EMPTY (0 rows)
- ❌ Column name mismatch: DB uses `as_of_date` (date), code expects `base_dt` (text YYYYMMDD)

**Key Findings:**
1. **Schema Reality:** Tables exist with CORRECT schema (as_of_date column, not base_dt)
2. **Code Mismatch:** DB2 loader code and queries reference non-existent `base_dt` column
3. **Data State:** ALL tables empty (multiplier, product, coverage, ranking = 0 rows)
4. **Root Cause:** Schema spec vs implementation mismatch - need to align code to actual DB schema

---

## 1) Connection Evidence

### 1.1 Database Connection

```
\conninfo
```

**Output:**
```
You are connected to database "inca_rag_scope" as user "inca_admin"
on host "localhost" (address "::1") at port "5432".
```

**Verification:** ✅ Connected to correct database (inca_rag_scope @ port 5432)

---

## 2) Table Existence Evidence

### 2.1 Premium Tables List

```
\dt *premium*
```

**Output:**
```
                   List of relations
 Schema |           Name           | Type  |   Owner
--------+--------------------------+-------+------------
 public | coverage_premium_quote   | table | inca_admin
 public | premium_multiplier       | table | inca_admin
 public | premium_quote            | table | inca_admin
 public | product_premium_quote_v2 | table | inca_admin
 public | q14_premium_ranking_v1   | table | inca_admin
(5 rows)
```

**Verification:** ✅ ALL 5 required premium tables exist

---

## 3) Schema Evidence (Detailed)

### 3.1 premium_quote

```
\d premium_quote
```

**Output:**
```
                                              Table "public.premium_quote"
     Column      |            Type             | Collation | Nullable |                     Default
-----------------+-----------------------------+-----------+----------+-------------------------------------------------
 quote_id        | integer                     |           | not null | nextval('premium_quote_quote_id_seq'::regclass)
 insurer_key     | text                        |           | not null |
 product_id      | text                        |           | not null |
 plan_variant    | text                        |           | not null |
 age             | integer                     |           | not null |
 sex             | text                        |           | not null |
 smoke           | text                        |           | not null | 'NA'::text
 pay_term_years  | integer                     |           | not null |
 ins_term_years  | integer                     |           | not null |
 premium_monthly | integer                     |           | not null |
 premium_total   | integer                     |           | not null |
 source_table_id | text                        |           |          |
 source_row_id   | text                        |           |          |
 as_of_date      | date                        |           | not null |  ← KEY: as_of_date (date type)
 created_at      | timestamp without time zone |           |          | CURRENT_TIMESTAMP
 updated_at      | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "premium_quote_pkey" PRIMARY KEY, btree (quote_id)
    "idx_premium_quote_comparison" btree (plan_variant, age, sex, premium_monthly)
    "idx_premium_quote_lookup" btree (insurer_key, product_id, plan_variant, age, sex)
Check constraints:
    "chk_age" CHECK (age = ANY (ARRAY[30, 40, 50]))
    "chk_plan_variant" CHECK (plan_variant = ANY (ARRAY['GENERAL'::text, 'NO_REFUND'::text]))
    "chk_premium_positive" CHECK (premium_monthly > 0 AND premium_total > 0)
    "chk_sex" CHECK (sex = ANY (ARRAY['M'::text, 'F'::text, 'UNISEX'::text]))
    "chk_smoke" CHECK (smoke = ANY (ARRAY['Y'::text, 'N'::text, 'NA'::text]))
```

**Critical Finding:** ❌ Column is `as_of_date` (date), NOT `base_dt` (text)

### 3.2 product_premium_quote_v2

```
\d product_premium_quote_v2
```

**Output:**
```
                                                      Table "public.product_premium_quote_v2"
         Column         |            Type             | Collation | Nullable |                               Default
------------------------+-----------------------------+-----------+----------+----------------------------------------------------------------------
 product_premium_id     | integer                     |           | not null | nextval('product_premium_quote_v2_product_premium_id_seq'::regclass)
 insurer_key            | text                        |           | not null |
 product_id             | text                        |           | not null |
 plan_variant           | text                        |           | not null |
 age                    | integer                     |           | not null |
 sex                    | text                        |           | not null |
 smoke                  | text                        |           | not null | 'NA'::text
 pay_term_years         | integer                     |           | not null |
 ins_term_years         | integer                     |           | not null |
 as_of_date             | date                        |           | not null |  ← KEY: as_of_date (date type)
 premium_monthly_total  | integer                     |           | not null |
 premium_total_total    | integer                     |           | not null |
 calculated_monthly_sum | integer                     |           |          |
 sum_match_status       | text                        |           |          |
 source_table_id        | text                        |           |          |
 source_row_id          | text                        |           |          |
 api_response_hash      | text                        |           |          |
 created_at             | timestamp without time zone |           |          | CURRENT_TIMESTAMP
 updated_at             | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "product_premium_quote_v2_pkey" PRIMARY KEY, btree (product_premium_id)
    "idx_product_premium_v2_lookup" btree (insurer_key, product_id, plan_variant, age, sex)
    "uq_product_premium" UNIQUE CONSTRAINT, btree (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
Check constraints:
    "chk_ppq_age" CHECK (age = ANY (ARRAY[30, 40, 50]))
    "chk_ppq_plan_variant" CHECK (plan_variant = ANY (ARRAY['GENERAL'::text, 'NO_REFUND'::text]))
    "chk_ppq_premium_positive" CHECK (premium_monthly_total > 0 AND premium_total_total > 0)
    "chk_ppq_sex" CHECK (sex = ANY (ARRAY['M'::text, 'F'::text, 'UNISEX'::text]))
    "chk_ppq_smoke" CHECK (smoke = ANY (ARRAY['Y'::text, 'N'::text, 'NA'::text]))
```

**Critical Finding:** ❌ Column is `as_of_date` (date), NOT `base_dt` (text)
**Also:** UNIQUE constraint includes `as_of_date`, NOT `base_dt`

### 3.3 coverage_premium_quote

```
\d coverage_premium_quote
```

**Output:**
```
                                                        Table "public.coverage_premium_quote"
          Column          |            Type             | Collation | Nullable |                               Default
--------------------------+-----------------------------+-----------+----------+---------------------------------------------------------------------
 coverage_premium_id      | integer                     |           | not null | nextval('coverage_premium_quote_coverage_premium_id_seq'::regclass)
 insurer_key              | text                        |           | not null |
 product_id               | text                        |           | not null |
 plan_variant             | text                        |           | not null |
 age                      | integer                     |           | not null |
 sex                      | text                        |           | not null |
 smoke                    | text                        |           | not null | 'NA'::text
 pay_term_years           | integer                     |           | not null |
 ins_term_years           | integer                     |           | not null |
 as_of_date               | date                        |           | not null |  ← KEY: as_of_date (date type)
 coverage_code            | text                        |           |          |
 coverage_title_raw       | text                        |           |          |
 coverage_name_normalized | text                        |           |          |
 coverage_amount_raw      | text                        |           |          |
 coverage_amount_value    | bigint                      |           |          |
 premium_monthly_coverage | integer                     |           | not null |
 source_table_id          | text                        |           |          |
 source_row_id            | text                        |           |          |
 multiplier_percent       | numeric(5,2)                |           |          |
 created_at               | timestamp without time zone |           |          | CURRENT_TIMESTAMP
 updated_at               | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "coverage_premium_quote_pkey" PRIMARY KEY, btree (coverage_premium_id)
    "idx_coverage_premium_coverage_code" btree (coverage_code)
    "idx_coverage_premium_lookup" btree (insurer_key, product_id, plan_variant, age, sex, coverage_code)
    "idx_coverage_premium_plan_variant" btree (plan_variant)
Check constraints:
    "chk_cpq_age" CHECK (age = ANY (ARRAY[30, 40, 50]))
    "chk_cpq_plan_variant" CHECK (plan_variant = ANY (ARRAY['GENERAL'::text, 'NO_REFUND'::text]))
    "chk_cpq_premium_positive" CHECK (premium_monthly_coverage > 0)
    "chk_cpq_sex" CHECK (sex = ANY (ARRAY['M'::text, 'F'::text, 'UNISEX'::text]))
    "chk_cpq_smoke" CHECK (smoke = ANY (ARRAY['Y'::text, 'N'::text, 'NA'::text]))
```

**Critical Finding:** ❌ Column is `as_of_date` (date), NOT `base_dt` (text)

### 3.4 q14_premium_ranking_v1

```
\d q14_premium_ranking_v1
```

**Output:**
```
                                               Table "public.q14_premium_ranking_v1"
     Column      |            Type             | Collation | Nullable |                          Default
-----------------+-----------------------------+-----------+----------+------------------------------------------------------------
 ranking_id      | integer                     |           | not null | nextval('q14_premium_ranking_v1_ranking_id_seq'::regclass)
 insurer_key     | text                        |           | not null |
 product_id      | text                        |           | not null |
 age             | integer                     |           | not null |
 plan_variant    | text                        |           | not null |
 cancer_amt      | integer                     |           | not null |
 premium_monthly | integer                     |           | not null |
 premium_per_10m | numeric(12,2)               |           | not null |
 rank            | integer                     |           | not null |
 source          | jsonb                       |           | not null |
 as_of_date      | date                        |           | not null |  ← KEY: as_of_date (date type)
 created_at      | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "q14_premium_ranking_v1_pkey" PRIMARY KEY, btree (ranking_id)
    "idx_q14_ranking_as_of_date" btree (as_of_date)
    "idx_q14_ranking_insurer" btree (insurer_key)
    "idx_q14_ranking_lookup" btree (age, plan_variant, rank)
    "uq_q14_ranking" UNIQUE CONSTRAINT, btree (age, plan_variant, rank, as_of_date)
Check constraints:
    "chk_q14_age" CHECK (age = ANY (ARRAY[30, 40, 50]))
    "chk_q14_cancer_amt_positive" CHECK (cancer_amt > 0)
    "chk_q14_plan_variant" CHECK (plan_variant = ANY (ARRAY['GENERAL'::text, 'NO_REFUND'::text]))
    "chk_q14_premium_per_10m_positive" CHECK (premium_per_10m > 0::numeric)
    "chk_q14_premium_positive" CHECK (premium_monthly > 0)
    "chk_q14_rank" CHECK (rank >= 1 AND rank <= 3)
```

**Critical Finding:** ❌ Column is `as_of_date` (date), NOT `base_dt` (text)
**Also:** Indexes and UNIQUE constraints use `as_of_date`

### 3.5 premium_multiplier

```
\d premium_multiplier
```

**Output:**
```
Table "public.premium_multiplier"
       Column       |            Type             | Collation | Nullable |                          Default
--------------------+-----------------------------+-----------+----------+-----------------------------------------------------------
 multiplier_id      | integer                     |           | not null | nextval('premium_multiplier_multiplier_id_seq'::regclass)
 insurer_key        | text                        |           | not null |
 coverage_name      | text                        |           | not null |
 multiplier_percent | numeric(5,2)                |           | not null |
 source_file        | text                        |           | not null |
 source_row_id      | integer                     |           |          |
 created_at         | timestamp without time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "premium_multiplier_pkey" PRIMARY KEY, btree (multiplier_id)
    "idx_multiplier_lookup" btree (insurer_key, coverage_name)
    "uq_insurer_coverage" UNIQUE CONSTRAINT, btree (insurer_key, coverage_name)
Check constraints:
    "chk_multiplier_positive" CHECK (multiplier_percent > 0::numeric)
```

**Finding:** ✅ Schema is correct (no date column here, as expected)

---

## 4) information_schema Evidence

### 4.1 Column Metadata Query

```sql
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('premium_quote', 'product_premium_quote_v2', 'coverage_premium_quote', 'q14_premium_ranking_v1', 'premium_multiplier')
ORDER BY table_name, ordinal_position;
```

**Key Columns (date-related):**

| table_name | column_name | data_type | is_nullable |
|------------|-------------|-----------|-------------|
| premium_quote | as_of_date | date | NO |
| product_premium_quote_v2 | as_of_date | date | NO |
| coverage_premium_quote | as_of_date | date | NO |
| q14_premium_ranking_v1 | as_of_date | date | NO |

**Finding:** ❌ NO `base_dt` column exists in ANY table
**Finding:** ✅ ALL tables use `as_of_date` (date type, NOT text)

---

## 5) Row Count Evidence

### 5.1 Data Population Status

```sql
SELECT 'premium_quote' as table_name, count(*) as row_count FROM premium_quote
UNION ALL
SELECT 'product_premium_quote_v2', count(*) FROM product_premium_quote_v2
UNION ALL
SELECT 'coverage_premium_quote', count(*) FROM coverage_premium_quote
UNION ALL
SELECT 'q14_premium_ranking_v1', count(*) FROM q14_premium_ranking_v1
UNION ALL
SELECT 'premium_multiplier', count(*) FROM premium_multiplier;
```

**Output:**
```
        table_name        | row_count
--------------------------+-----------
 premium_quote            |         0
 product_premium_quote_v2 |         0
 coverage_premium_quote   |         0
 q14_premium_ranking_v1   |         0
 premium_multiplier       |         0
(5 rows)
```

**Finding:** ❌ ALL tables are EMPTY (0 rows)

### 5.2 Multiplier Explanation

**Why premium_multiplier count = 0:**

1. **No Excel file exists:** Multiplier data requires Excel source (`일반보험요율예시.xlsx`)
2. **No loader executed:** `multiplier_loader.py` has NOT been run
3. **No manual inserts:** No multiplier data manually inserted

**To populate multiplier:**
1. Obtain Excel file: `data/sources/일반보험요율예시.xlsx`
2. Run loader: `python3 pipeline/premium_ssot/multiplier_loader.py`
3. Verify: `SELECT count(*) FROM premium_multiplier;`

---

## 6) Critical Discrepancy Analysis

### 6.1 Column Name Mismatch

**DB Reality:**
- Column: `as_of_date`
- Type: `date`
- Format: `YYYY-MM-DD` (e.g., `2025-11-26`)

**Code Expectation (WRONG):**
- Column: `base_dt`
- Type: `text` (assumed)
- Format: `YYYYMMDD` (e.g., `"20251126"`)

**Impact:**
- ❌ `tools/premium/run_db2_load.py` references non-existent `base_dt` column
- ❌ Verification queries use `WHERE base_dt = '20251126'` → WILL FAIL
- ❌ DB2 audit doc references `base_dt` → INCORRECT

### 6.2 Affected Code Locations

**Files with `base_dt` references that need fixing:**

1. **tools/premium/run_db2_load.py:**
   - Line ~145: `"base_dt": self.BASE_DT`
   - Line ~195: INSERT statements use `base_dt`
   - Line ~247: SELECT statements filter on `base_dt`

2. **Verification queries in audit docs:**
   - `WHERE base_dt = '20251126'` → Should be `WHERE as_of_date = '2025-11-26'`

3. **runtime_upsert.py (if exists):**
   - Check for `base_dt` references in upsert logic

### 6.3 Type Conversion Required

**baseDt (API) → as_of_date (DB):**
```python
# WRONG:
base_dt = "20251126"
# ... INSERT base_dt directly

# CORRECT:
base_dt = "20251126"
as_of_date = f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:]}"  # "2025-11-26"
# ... INSERT as_of_date
```

---

## 7) Schema Source Analysis

### 7.1 Schema Files (Applied in DB1)

**Files:**
- `schema/020_premium_quote.sql`
- `schema/030_product_comparison_v1.sql`
- `schema/040_coverage_premium_quote.sql`
- `schema/050_q14_premium_ranking.sql`

**Verification Command:**
```bash
grep -n "base_dt\|as_of_date" schema/*.sql
```

**Evidence:**
```
schema/020_premium_quote.sql:30:    as_of_date DATE NOT NULL,
schema/040_coverage_premium_quote.sql:20:    as_of_date DATE NOT NULL,
schema/040_coverage_premium_quote.sql:28:    CONSTRAINT uq_compare_product UNIQUE (..., as_of_date)
schema/040_coverage_premium_quote.sql:59:    as_of_date DATE NOT NULL,
schema/040_coverage_premium_quote.sql:143:    CONSTRAINT uq_product_premium UNIQUE (..., as_of_date)
schema/050_q14_premium_ranking.sql:35:    as_of_date DATE NOT NULL,
schema/050_q14_premium_ranking.sql:48:    CONSTRAINT uq_q14_ranking UNIQUE (..., as_of_date)
schema/050_q14_premium_ranking.sql:58:    CREATE INDEX ... ON q14_premium_ranking_v1(as_of_date);
```

**Finding:** ✅ ALL schema files define `as_of_date` (date type)
**Finding:** ❌ NO `base_dt` column in ANY schema file

### 7.2 Schema DDL Consistency

**Conclusion:**
- ✅ DB schema is CORRECT (matches DDL in schema/*.sql)
- ❌ Code is WRONG (references non-existent `base_dt`)
- ✅ Migrations were applied correctly (DB matches schema files)

**Source of Truth:** `schema/*.sql` files define `as_of_date` (date type)

---

## 8) Verdict and Remediation

### 8.1 Final Verdict

**DB1 Claim Status:** ✅ **TRUE WITH QUALIFICATIONS**

**What's TRUE:**
1. ✅ ALL 5 premium tables EXIST in inca_rag_scope@5432
2. ✅ Tables have CORRECT schema (as_of_date, proper constraints)
3. ✅ G11 PremiumSchemaGate will PASS (tables exist)

**What's FALSE/INCOMPLETE:**
1. ❌ ALL tables are EMPTY (0 rows)
2. ❌ Code references non-existent `base_dt` column
3. ❌ DB2 load will FAIL due to column name mismatch

**Root Cause:**
- Schema spec (as_of_date) vs code implementation (base_dt) mismatch
- DB schema is CORRECT, code needs to be fixed

### 8.2 Remediation Plan (LOCKED)

**Option A: Fix Code to Match DB Schema (RECOMMENDED)**

1. **Update run_db2_load.py:**
   ```python
   # Convert baseDt to as_of_date
   base_dt_str = "20251126"
   as_of_date = f"{base_dt_str[:4]}-{base_dt_str[4:6]}-{base_dt_str[6:]}"

   # Use as_of_date in INSERT statements
   INSERT INTO product_premium_quote_v2 (..., as_of_date, ...)
   VALUES (..., %s, ...)
   ```

2. **Update verification queries:**
   ```sql
   -- WRONG:
   SELECT count(*) FROM product_premium_quote_v2 WHERE base_dt = '20251126';

   -- CORRECT:
   SELECT count(*) FROM product_premium_quote_v2 WHERE as_of_date = '2025-11-26';
   ```

3. **Update audit docs:**
   - Replace all `base_dt` references with `as_of_date`
   - Document date format conversion (YYYYMMDD → YYYY-MM-DD)

**Option B: Migrate DB Schema (NOT RECOMMENDED)**

- Add `base_dt` column to all tables
- Update UNIQUE constraints and indexes
- Risk: Breaking existing schema design

**Decision:** ✅ **OPTION A** (Fix code to match DB)

### 8.3 Immediate Actions

1. **Verify schema/*.sql files:**
   ```bash
   grep -n "base_dt\|as_of_date" schema/020_premium_quote.sql
   grep -n "base_dt\|as_of_date" schema/040_coverage_premium_quote.sql
   grep -n "base_dt\|as_of_date" schema/050_q14_premium_ranking.sql
   ```

2. **Fix run_db2_load.py:**
   - Replace all `base_dt` with `as_of_date`
   - Add date format conversion function
   - Update INSERT/SELECT statements

3. **Fix verification queries:**
   - Update all WHERE clauses to use `as_of_date = 'YYYY-MM-DD'`

4. **Re-test DB2 load:**
   - Run with fixed code
   - Verify inserts succeed
   - Check row counts

---

## 9) Summary

**Schema Reality (HARD EVIDENCE):**
- ✅ 5 tables exist in inca_rag_scope@5432
- ✅ Schema uses `as_of_date` (date type)
- ❌ NO `base_dt` column exists
- ❌ ALL tables empty (0 rows)

**Code Reality:**
- ❌ Code references `base_dt` (doesn't exist)
- ❌ DB2 loader will FAIL on column mismatch
- ❌ Verification queries will FAIL

**DB1 Verdict:** ✅ TRUE (tables exist with correct schema)
**DB2 Status:** ❌ BLOCKED (code needs fixing before data load)

**Next Step:** Fix code to use `as_of_date` instead of `base_dt`

---

## Appendix: Quick Reference

### Date Conversion Function

```python
def convert_base_dt_to_as_of_date(base_dt: str) -> str:
    """
    Convert baseDt (YYYYMMDD) to as_of_date (YYYY-MM-DD)

    Args:
        base_dt: Date string in YYYYMMDD format (e.g., "20251126")

    Returns:
        Date string in YYYY-MM-DD format (e.g., "2025-11-26")
    """
    if len(base_dt) != 8:
        raise ValueError(f"Invalid baseDt format: {base_dt} (expected YYYYMMDD)")

    return f"{base_dt[:4]}-{base_dt[4:6]}-{base_dt[6:]}"
```

### Verification Query Template

```sql
-- Check data for specific date
SELECT count(*)
FROM product_premium_quote_v2
WHERE as_of_date = '2025-11-26';

-- List all dates with data
SELECT DISTINCT as_of_date, count(*) as row_count
FROM product_premium_quote_v2
GROUP BY as_of_date
ORDER BY as_of_date DESC;
```

---

**END OF REPORT**

**STATUS:** DB1 VERIFIED (tables exist with correct schema)
**BLOCKER:** Code uses wrong column name (`base_dt` instead of `as_of_date`)
**ACTION REQUIRED:** Fix code to match DB schema
