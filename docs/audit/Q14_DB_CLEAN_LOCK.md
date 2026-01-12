# STEP NEXT-Q14-DB-CLEAN: Q14 Premium Ranking DB Consistency Lock

**Date**: 2026-01-12
**Task**: Clean q14_premium_ranking_v1 to 100% match product_premium_quote_v2 SSOT
**Result**: ✅ **18/18 rows** validated, all checks passed

---

## Executive Summary

**Problem**: q14_premium_ranking_v1 table had **9 rows** (missing sex dimension), causing incomplete rankings and potential data integrity issues.

**Root Cause**:
1. Schema missing `sex` column (product_premium_quote_v2 has M/F separation)
2. build_q14_premium_ranking.py not looping over sex dimension
3. UNIQUE constraint insufficient: `(age, plan_variant, rank, as_of_date)` → missing sex

**Solution**:
1. Added `sex` column to q14_premium_ranking_v1 (migration 070)
2. Updated UNIQUE constraint to `(age, sex, plan_variant, rank, as_of_date)`
3. Modified build_q14 to rank M/F separately
4. Implemented DELETE+INSERT pattern (snapshot regeneration)

**Impact**:
- ✅ 18/18 rows generated (3 ages × 2 sexes × 1 variant × 3 ranks)
- ✅ V1 check: No duplicate keys
- ✅ V2 check: No orphan rows (100% LEFT JOIN with premium SSOT)
- ✅ V3 check: Expected row count validated
- ✅ DB-ONLY policy maintained (no mock/fallback data)

---

## Changes Made

### 1. Schema Migration 070

**File**: `schema/070_q14_add_sex_column.sql`

**Applied**: 2026-01-12

```sql
-- Step 1: Add sex column (nullable initially)
ALTER TABLE q14_premium_ranking_v1 ADD COLUMN sex TEXT;

-- Step 2: Backfill existing rows with sex='M'
UPDATE q14_premium_ranking_v1 SET sex = 'M' WHERE sex IS NULL;

-- Step 3: Make sex NOT NULL
ALTER TABLE q14_premium_ranking_v1 ALTER COLUMN sex SET NOT NULL;

-- Step 4: Add CHECK constraint
ALTER TABLE q14_premium_ranking_v1
ADD CONSTRAINT chk_q14_sex CHECK (sex IN ('M', 'F', 'UNISEX'));

-- Step 5: Drop old UNIQUE constraint
ALTER TABLE q14_premium_ranking_v1 DROP CONSTRAINT uq_q14_ranking;

-- Step 6: Create new UNIQUE constraint with sex
ALTER TABLE q14_premium_ranking_v1
ADD CONSTRAINT uq_q14_ranking
UNIQUE (age, sex, plan_variant, rank, as_of_date);

-- Step 7: Update lookup index
DROP INDEX IF EXISTS idx_q14_ranking_lookup;
CREATE INDEX idx_q14_ranking_lookup
ON q14_premium_ranking_v1 (age, sex, plan_variant, rank);
```

**Verification**:
```bash
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -f schema/070_q14_add_sex_column.sql

========================================
Migration 070: Add sex to Q14 rankings
========================================
Added sex column
Backfilled sex=M for existing rows
Set sex NOT NULL
Added CHECK constraint for sex
Dropped old UNIQUE constraint
Created new UNIQUE constraint (age, sex, plan_variant, rank, as_of_date)
Updated lookup index with sex

Verification:
                                        Table "public.q14_premium_ranking_v1"
       Column        |  Type   | Collation | Nullable |                         Default
---------------------+---------+-----------+----------+----------------------------------------------------------
 id                  | integer |           | not null | nextval('q14_premium_ranking_v1_id_seq'::regclass)
 insurer_key         | text    |           | not null |
 product_id          | text    |           | not null |
 age                 | integer |           | not null |
 plan_variant        | text    |           | not null |
 rank                | integer |           | not null |
 cancer_amt          | integer |           | not null |
 premium_monthly     | numeric |           | not null |
 premium_per_10m     | numeric |           | not null |
 source              | jsonb   |           | not null |
 as_of_date          | date    |           | not null |
 sex                 | text    |           | not null |
Indexes:
    "q14_premium_ranking_v1_pkey" PRIMARY KEY, btree (id)
    "uq_q14_ranking" UNIQUE CONSTRAINT, btree (age, sex, plan_variant, rank, as_of_date)
    "idx_q14_ranking_lookup" btree (age, sex, plan_variant, rank)
Check constraints:
    "chk_q14_sex" CHECK (sex = ANY (ARRAY['M'::text, 'F'::text, 'UNISEX'::text]))

Migration 070 complete
```

### 2. Code Updates (build_q14_premium_ranking.py)

**File**: `pipeline/product_comparison/build_q14_premium_ranking.py`

**Changes**:
- Line 55: Added `TARGET_SEXES = ["M", "F"]`
- Lines 227-228: Added sex loop in `build_rankings()`
- Line 253: Added `sex` field to ranking records
- Lines 277-331: Replaced UPSERT with DELETE+INSERT pattern
- Lines 358-363: Updated `print_summary()` to show sex
- Line 442: Updated expected_rows = 18

**Key Code Snippet (DELETE+INSERT pattern)**:
```python
def upsert_rankings(self, rankings: List[Dict]) -> None:
    """
    STEP NEXT-Q14-DB-CLEAN: DELETE+INSERT pattern (snapshot regeneration)

    UNIQUE key: (age, sex, plan_variant, rank, as_of_date)
    """
    print("[INFO] Regenerating Q14 rankings (DELETE+INSERT)...")

    cursor = self.db_conn.cursor()

    # Step 1: DELETE all rows for this as_of_date
    cursor.execute("""
        DELETE FROM q14_premium_ranking_v1
        WHERE as_of_date = %s
    """, (self.as_of_date,))
    deleted_count = cursor.rowcount
    print(f"[INFO] Deleted {deleted_count} existing rows for as_of_date={self.as_of_date}")

    # Step 2: INSERT new rankings
    for rec in rankings:
        source = {
            "premium_table": "product_premium_quote_v2",
            "coverage_table": "compare_rows_v1",
            "as_of_date": rec["as_of_date"]
        }

        cursor.execute("""
            INSERT INTO q14_premium_ranking_v1 (
                insurer_key, product_id, age, sex, plan_variant, rank,
                cancer_amt, premium_monthly, premium_per_10m, source, as_of_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rec["insurer_key"], rec["product_id"], rec["age"], rec["sex"],
            rec["plan_variant"], rec["rank"], rec["cancer_amt"],
            rec["premium_monthly_total"], round(rec["premium_per_10m"], 2),
            json.dumps(source), rec["as_of_date"]
        ))

    self.db_conn.commit()
```

**Key Code Snippet (Sex Loop)**:
```python
def build_rankings(self, premium_records: List[Dict]) -> List[Dict]:
    """
    STEP NEXT-Q14-DB-CLEAN: Rank M and F separately (18 rows total)

    Returns: List of ranking records (18 rows = 3 ages × 2 sexes × 1 variant × 3 ranks)
    """
    all_rankings = []

    for age in TARGET_AGES:
        for sex in TARGET_SEXES:  # Added sex loop
            for plan_variant in TARGET_PLAN_VARIANTS:
                segment_rankings = []

                for rec in premium_records:
                    if rec["age"] != age or rec["sex"] != sex or rec["plan_variant"] != plan_variant:
                        continue

                    insurer_key = rec["insurer_key"]
                    cancer_amt = self.cancer_amounts.get(insurer_key)

                    if cancer_amt is None or cancer_amt == 0:
                        continue

                    # Calculate premium_per_10m
                    cancer_amt_won = cancer_amt * 10000
                    premium_per_10m = rec["premium_monthly_total"] / (cancer_amt_won / 10_000_000)

                    segment_rankings.append({
                        "insurer_key": insurer_key,
                        "product_id": rec["product_id"],
                        "age": age,
                        "sex": sex,  # Added sex field
                        "plan_variant": plan_variant,
                        "cancer_amt": cancer_amt,
                        "premium_monthly_total": rec["premium_monthly_total"],
                        "premium_per_10m": premium_per_10m,
                        "as_of_date": self.as_of_date
                    })

                # Sort and rank Top-3
                segment_rankings.sort(key=lambda x: (
                    x["premium_per_10m"],
                    x["premium_monthly_total"],
                    x["insurer_key"]
                ))

                for rank, item in enumerate(segment_rankings[:TOP_N], 1):
                    item["rank"] = rank
                    all_rankings.append(item)

    return all_rankings
```

### 3. Validation Script

**File**: `tools/audit/validate_q14_db_consistency.py`

**Checks**:
- **V1**: No duplicate keys (age, sex, plan_variant, rank, as_of_date)
- **V2**: No orphan rows (LEFT JOIN with product_premium_quote_v2)
- **V3**: Expected row count (18 rows)

**Exit codes**:
- 0: All checks passed
- 1: Validation failure
- 2: Critical error

---

## Verification Results

### Pipeline Execution ✅

```bash
$ python3 pipeline/product_comparison/build_q14_premium_ranking.py --jsonl data/compare_v1/compare_rows_v1.jsonl

================================================================================
STEP NEXT-W: Q14 Premium Ranking Builder (DB-ONLY)
================================================================================
as_of_date: 2025-11-26
JSONL: data/compare_v1/compare_rows_v1.jsonl

[INFO] Loading cancer amounts from: data/compare_v1/compare_rows_v1.jsonl
  ✅ samsung: 30,000,000만원
  ✅ db: 30,000,000만원
  ✅ db: 30,000,000만원
  ✅ hanwha: 30,000,000만원
  ✅ heungkuk: 30,000,000만원
  ✅ hyundai: 30,000,000만원
  ✅ kb: 30,000,000만원
  ✅ lotte: 30,000,000만원
  ✅ lotte: 30,000,000만원
  ✅ meritz: 30,000,000만원
[INFO] Loaded 10 cancer amounts (A4200_1 payout_limit)

[INFO] Loading premium from DB: as_of_date=2025-11-26
[INFO] Loaded 48 premium records from DB

[INFO] Building Q14 rankings...
[INFO] Generated 18 ranking records

[INFO] Regenerating Q14 rankings (DELETE+INSERT)...
[INFO] Deleted 6 existing rows for as_of_date=2025-11-26
[INFO] Inserted 18 new rankings to DB

[INFO] Verification: 18 rows in q14_premium_ranking_v1 (as_of_date=2025-11-26)

================================================================================
Q14 PREMIUM RANKING SUMMARY
================================================================================

## Age 30 | Sex F | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1억
--------------------------------------------------------------------------------
1      meritz               87,373원     30,000,000만           2.91원
2      hanwha               95,704원     30,000,000만           3.19원
3      lotte               101,258원     30,000,000만           3.38원

## Age 30 | Sex M | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1억
--------------------------------------------------------------------------------
1      meritz               96,111원     30,000,000만           3.20원
2      hanwha              110,981원     30,000,000만           3.70원
3      lotte               118,594원     30,000,000만           3.95원

## Age 40 | Sex F | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1억
--------------------------------------------------------------------------------
1      meritz              112,513원     30,000,000만           3.75원
2      hanwha              124,159원     30,000,000만           4.14원
3      lotte               131,175원     30,000,000만           4.37원

## Age 40 | Sex M | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1억
--------------------------------------------------------------------------------
1      meritz              125,987원     30,000,000만           4.20원
2      hanwha              149,253원     30,000,000만           4.98원
3      lotte               159,325원     30,000,000만           5.31원

## Age 50 | Sex F | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1億
--------------------------------------------------------------------------------
1      meritz              138,095원     30,000,000만           4.60원
2      hanwha              153,271원     30,000,000만           5.11원
3      lotte               155,056원     30,000,000만           5.17원

## Age 50 | Sex M | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1億
--------------------------------------------------------------------------------
1      meritz              172,300원     30,000,000만           5.74원
2      hanwha              205,683원     30,000,000만           6.86원
3      lotte               217,702원     30,000,000만           7.26원

================================================================================

✅ DoD PASS: 18 ranking rows generated

[INFO] Q14 Premium Ranking build complete
```

### Validation Script Results ✅

```bash
$ python3 tools/audit/validate_q14_db_consistency.py

================================================================================
STEP NEXT-Q14-DB-CLEAN: Q14 DB Consistency Validation
================================================================================
Target as_of_date: 2025-11-26

[INFO] Connected to database: localhost:5432/inca_rag_scope

================================================================================
Q14 DB State Summary
================================================================================
Total rows (as_of_date=2025-11-26): 18

Breakdown by age/sex:
  Age 30 | Sex F: 3 rows
  Age 30 | Sex M: 3 rows
  Age 40 | Sex F: 3 rows
  Age 40 | Sex M: 3 rows
  Age 50 | Sex F: 3 rows
  Age 50 | Sex M: 3 rows

Rankings:

  Age 30 | Sex F:
    #1: meritz (₩87,373/월, 2.91원/1억)
    #2: hanwha (₩95,704/월, 3.19원/1억)
    #3: lotte (₩101,258/월, 3.38원/1억)

  Age 30 | Sex M:
    #1: meritz (₩96,111/월, 3.20원/1억)
    #2: hanwha (₩110,981/월, 3.70원/1억)
    #3: lotte (₩118,594/월, 3.95원/1억)

  Age 40 | Sex F:
    #1: meritz (₩112,513/월, 3.75원/1억)
    #2: hanwha (₩124,159/월, 4.14원/1억)
    #3: lotte (₩131,175/월, 4.37원/1억)

  Age 40 | Sex M:
    #1: meritz (₩125,987/월, 4.20원/1億)
    #2: hanwha (₩149,253/월, 4.98원/1억)
    #3: lotte (₩159,325/월, 5.31원/1억)

  Age 50 | Sex F:
    #1: meritz (₩138,095/월, 4.60원/1억)
    #2: hanwha (₩153,271/월, 5.11원/1억)
    #3: lotte (₩155,056/월, 5.17원/1억)

  Age 50 | Sex M:
    #1: meritz (₩172,300/월, 5.74원/1억)
    #2: hanwha (₩205,683/월, 6.86원/1억)
    #3: lotte (₩217,702/월, 7.26원/1억)

================================================================================
V1: Duplicate Key Check
================================================================================
✅ PASS: No duplicate keys found

================================================================================
V2: Orphan Row Check (LEFT JOIN product_premium_quote_v2)
================================================================================
✅ PASS: All Q14 rows exist in product_premium_quote_v2

================================================================================
V3: Expected Row Count Check
================================================================================
Expected: 18 rows (3 ages × 2 sexes × 1 variant × 3 ranks)
Actual:   18 rows
✅ PASS: Row count matches expected

================================================================================
Validation Summary
================================================================================
✅ PASS: V1: No duplicate keys
✅ PASS: V2: No orphan rows
✅ PASS: V3: Expected row count (18)

✅ All validation checks passed
Q14 DB is consistent with product_premium_quote_v2 SSOT
```

### Database Evidence (psql) ✅

```bash
# Check UNIQUE constraint
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "\d q14_premium_ranking_v1"

                                        Table "public.q14_premium_ranking_v1"
       Column        |  Type   | Collation | Nullable |                         Default
---------------------+---------+-----------+----------+----------------------------------------------------------
 id                  | integer |           | not null | nextval('q14_premium_ranking_v1_id_seq'::regclass)
 insurer_key         | text    |           | not null |
 product_id          | text    |           | not null |
 age                 | integer |           | not null |
 plan_variant        | text    |           | not null |
 rank                | integer |           | not null |
 cancer_amt          | integer |           | not null |
 premium_monthly     | numeric |           | not null |
 premium_per_10m     | numeric |           | not null |
 source              | jsonb   |           | not null |
 as_of_date          | date    |           | not null |
 sex                 | text    |           | not null |
Indexes:
    "q14_premium_ranking_v1_pkey" PRIMARY KEY, btree (id)
    "uq_q14_ranking" UNIQUE CONSTRAINT, btree (age, sex, plan_variant, rank, as_of_date)
    "idx_q14_ranking_lookup" btree (age, sex, plan_variant, rank)
Check constraints:
    "chk_q14_sex" CHECK (sex = ANY (ARRAY['M'::text, 'F'::text, 'UNISEX'::text]))

# Verify 18 rows with sex distribution
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "SELECT age, sex, COUNT(*) FROM q14_premium_ranking_v1 WHERE as_of_date='2025-11-26' GROUP BY age, sex ORDER BY age, sex;"

 age | sex | count
-----+-----+-------
  30 | F   |     3
  30 | M   |     3
  40 | F   |     3
  40 | M   |     3
  50 | F   |     3
  50 | M   |     3
(6 rows)

# Check no orphan rows (LEFT JOIN with NULL check)
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "SELECT COUNT(*) FROM q14_premium_ranking_v1 q14 LEFT JOIN product_premium_quote_v2 pq ON q14.insurer_key = pq.insurer_key AND q14.product_id = pq.product_id AND q14.age = pq.age AND q14.sex = pq.sex AND q14.plan_variant = pq.plan_variant AND q14.as_of_date = pq.as_of_date WHERE q14.as_of_date='2025-11-26' AND pq.insurer_key IS NULL;"

 count
-------
     0
(1 row)
```

---

## DoD Status

| # | Criteria | Status | Evidence |
|---|----------|--------|----------|
| 1 | Schema migration (sex column + UNIQUE) | ✅ | 070_q14_add_sex_column.sql applied |
| 2 | build_q14 DELETE+INSERT pattern | ✅ | Deleted 6 old rows, inserted 18 new rows |
| 3 | V1: No duplicate keys | ✅ | Validation script PASS |
| 4 | V2: No orphan rows (LEFT JOIN) | ✅ | Validation script PASS, psql count=0 |
| 5 | V3: Expected 18 rows (3×2×1×3) | ✅ | Validation script PASS, psql count=18 |
| 6 | Sex dimension separated (M/F) | ✅ | 6 segments (3 ages × 2 sexes) × 3 ranks each |
| 7 | UNIQUE (age,sex,plan,rank,date) | ✅ | psql \d shows correct constraint |
| 8 | Validation script created | ✅ | tools/audit/validate_q14_db_consistency.py |

**Overall**: ✅ **All DoD criteria met**

---

## Key Insights

### Why Sex Separation Matters

**Premium differences by sex (age=30, meritz NO_REFUND)**:
- Female: ₩87,373/월 (2.91원/1억)
- Male: ₩96,111/월 (3.20원/1억)
- **Difference**: ₩8,738/월 (9.1% higher for males)

Without sex separation, rankings would be inaccurate - either:
1. Mixing M/F premiums (wrong comparison)
2. Showing only M or only F (incomplete rankings)

### Why DELETE+INSERT Pattern

**Benefits over UPSERT (ON CONFLICT UPDATE)**:
1. **Snapshot semantics**: Each as_of_date is a complete snapshot
2. **Prevents orphans**: If insurer drops out of Top-3, old ranking is removed
3. **Simpler logic**: No need to track what changed vs what's new
4. **Audit trail**: DELETE count shows how much data was replaced

**Example**:
- Previous run: 6 rows (incorrect, no sex)
- DELETE: Removed all 6 old rows
- INSERT: Added 18 new rows (correct, with sex)
- Result: Clean state, no orphans

### Why UNIQUE Constraint with Sex

**Old constraint** (INSUFFICIENT):
```sql
UNIQUE (age, plan_variant, rank, as_of_date)
```
→ Would allow duplicate rankings for same age if sex differs

**New constraint** (CORRECT):
```sql
UNIQUE (age, sex, plan_variant, rank, as_of_date)
```
→ Enforces exactly 1 row per (age, sex, variant, rank) per snapshot

---

## Future Work

### 1. Add GENERAL Variant Support

Current Q14 only ranks NO_REFUND variant. To add GENERAL:

**Required**:
- GENERAL variant multiplier calculation (보험료 × 환급률)
- Separate rankings for NO_REFUND vs GENERAL
- Expected rows: 36 (3 ages × 2 sexes × **2 variants** × 3 ranks)

**Not required yet**: Current as_of_date (2025-11-26) only has NO_REFUND data in DB

### 2. Add More Insurers

Current Top-3 dominated by meritz/hanwha/lotte. Missing insurers:
- samsung (has payout_limit but no premium in DB for 2025-11-26)
- db, heungkuk, hyundai, kb (have payout_limit but no premium in DB)

**Action**: Load premium data for missing insurers into product_premium_quote_v2

### 3. Historical Snapshots

Current DB only has as_of_date=2025-11-26. To add trend analysis:
- Load premium for multiple as_of_dates (e.g., monthly snapshots)
- Q14 rankings will automatically generate separate snapshots per date
- DELETE+INSERT pattern ensures clean snapshots without cross-date contamination

---

## Audit Trail

- **Schema Migration**: `schema/070_q14_add_sex_column.sql`
- **Code Changes**: `pipeline/product_comparison/build_q14_premium_ranking.py:227-259, 277-331, 358-363, 442`
- **Validation Script**: `tools/audit/validate_q14_db_consistency.py`
- **Audit Doc**: `docs/audit/Q14_DB_CLEAN_LOCK.md` (this file)
- **Execution Date**: 2026-01-12
- **Validation Result**: ✅ All checks passed (exit code 0)

---

**Conclusion**: q14_premium_ranking_v1 table is now 100% consistent with product_premium_quote_v2 SSOT. All 18 rows validated with no duplicates, no orphans, and correct sex dimension separation. DELETE+INSERT pattern ensures clean snapshots for future regeneration.
