# STEP NEXT-Q14-DB-CLEAN REVIEW: Unit Fix + Hard Evidence

**Date**: 2026-01-12
**Task**: Review Q14 DB consistency + fix premium_per_10m unit violation
**Result**: ✅ **Unit corrected (만원/1천만원 → 원/1천만원)** + All checks pass

---

## Executive Summary

**Critical Issue Found**: premium_per_10m unit violated LOCKED formula
- **Before**: 2.91 (만원/1천만원) - calculation used `cancer_amt * 10000`
- **After**: 29,124.33 (원/1천만원) - calculation uses `cancer_amt / 10_000_000` directly
- **Impact**: 10,000x magnitude error in all rankings

**Root Cause**:
1. `cancer_amt` stored as **원** (30000000), not 만원 (3000)
2. Code comment claimed "만원" but actual value was 원
3. Calculation multiplied by 10000 then divided by 10000000 → net effect `/1000`
4. Result: **만원** per 10M won instead of **원** per 10M won

**Fix Applied**:
1. Corrected calculation: `premium / (cancer_amt / 10_000_000)` (removed `* 10000`)
2. Updated all comments/prints to reflect "원" unit
3. Fixed display format: `{cancer_amt/10000:,.0f}만원` instead of `{cancer_amt:,}만`
4. Regenerated all 18 rows with correct values

**Validation**:
- ✅ V1: No duplicate keys (18 rows unique)
- ✅ V2: No orphan rows (100% LEFT JOIN match)
- ✅ V3: Expected row count (18 = 3×2×1×3)
- ✅ **NEW: Unit correctness** (stored = recomputed_won_per_10m)

---

## 1. Unit Violation Evidence (BEFORE FIX)

### psql Evidence: Stored vs Recomputed

```bash
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "
SELECT r.age, r.sex, r.insurer_key, r.product_id,
       r.premium_monthly,
       r.cancer_amt,
       r.premium_per_10m AS stored,
       ROUND((r.premium_monthly::numeric) / (r.cancer_amt::numeric/10000000), 2) AS recomputed_won_per_10m,
       ROUND(((r.premium_monthly::numeric) / (r.cancer_amt::numeric/10000000))/10000, 2) AS recomputed_manwon_per_10m
FROM q14_premium_ranking_v1 r
WHERE r.as_of_date='2025-11-26' AND r.age=30 AND r.sex='F' AND r.plan_variant='NO_REFUND'
ORDER BY r.rank;
"

 age | sex | insurer_key | product_id | premium_monthly | cancer_amt | stored | recomputed_won_per_10m | recomputed_manwon_per_10m
-----+-----+-------------+------------+-----------------+------------+--------+------------------------+---------------------------
  30 | F   | meritz      | 6ADYW      |           87373 |   30000000 |   2.91 |               29124.33 |                      2.91  ← MATCH!
  30 | F   | hanwha      | LA02768003 |           95704 |   30000000 |   3.19 |               31901.33 |                      3.19  ← MATCH!
  30 | F   | lotte       | LA0762E002 |          101258 |   30000000 |   3.38 |               33752.67 |                      3.38  ← MATCH!
```

**Diagnosis**: `stored = recomputed_manwon_per_10m` → **Unit is 만원/1천만원**, NOT 원/1천만원

### LOCKED Formula Violation

**Document (build_q14_premium_ranking.py:14)**:
```python
Core Formula (LOCKED):
  premium_per_10m = premium_monthly_total / (cancer_amt / 10_000_000)
  # Expected unit: 원/1천만원
```

**Actual Code (BEFORE FIX, line 246-247)**:
```python
cancer_amt_won = cancer_amt * 10000  # cancer_amt=30000000 → 300000000000
premium_per_10m = rec["premium_monthly_total"] / (cancer_amt_won / 10_000_000)
# = 87373 / (300000000000 / 10000000)
# = 87373 / 30000
# = 2.91 (만원/1천만원)  ← 10000x too small!
```

**Math Breakdown**:
- LOCKED: `87373 / (30000000 / 10000000) = 87373 / 3 = 29124.33` ✅
- BEFORE: `87373 / (30000000 * 10000 / 10000000) = 87373 / 30000 = 2.91` ❌

---

## 2. Fix Implementation

### Code Changes

**File**: `pipeline/product_comparison/build_q14_premium_ranking.py`

**Change 1: cancer_amt unit comment (line 121-127)**
```python
# BEFORE
# Try to parse numeric value (in 만원)

# AFTER
# Try to parse numeric value (in 원)
# Clean and parse (원 단위)
```

**Change 2: cancer_amt display (line 142)**
```python
# BEFORE
print(f"  ✅ {insurer_key}: {cancer_amt:,}만원")
# Output: "30,000,000만원" (WRONG - would be 300 trillion won!)

# AFTER
print(f"  ✅ {insurer_key}: {cancer_amt:,}원 ({cancer_amt/10000:,.0f}만원)")
# Output: "30,000,000원 (3,000만원)" (CORRECT)
```

**Change 3: premium_per_10m calculation (line 244-248)**
```python
# BEFORE
# cancer_amt is in 만원 (e.g., 3000 = 30,000,000원)  ← COMMENT WAS WRONG
cancer_amt_won = cancer_amt * 10000
premium_per_10m = rec["premium_monthly_total"] / (cancer_amt_won / 10_000_000)

# AFTER
# Calculate premium_per_10m (LOCKED FORMULA)
# cancer_amt is in 원 (e.g., 30000000 = 3천만원)
# Formula: premium_monthly / (cancer_amt / 10,000,000)
# Unit: 원/1천만원 (how much premium per 10M won of coverage)
premium_per_10m = rec["premium_monthly_total"] / (cancer_amt / 10_000_000)
```

**Change 4: display format (line 381, 385)**
```python
# BEFORE
print(f"{'P/1억':<15}")
print(f"{cancer_amt:>14,}만 {p_per_10m:>14,.2f}원")
# Output: "30,000,000만  2.91원" (WRONG unit on both columns)

# AFTER
print(f"{'P/1천만원':<15}")
print(f"{cancer_amt/10000:>14,.0f}만원 {p_per_10m:>14,.2f}원")
# Output: "3,000만원  29,124.33원" (CORRECT)
```

---

## 3. Unit Correctness Validation (AFTER FIX)

### psql Evidence: Corrected Values

```bash
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "
SELECT r.age, r.sex, r.insurer_key,
       r.premium_monthly,
       r.cancer_amt,
       r.premium_per_10m AS stored,
       ROUND((r.premium_monthly::numeric) / (r.cancer_amt::numeric/10000000), 2) AS recomputed_won_per_10m
FROM q14_premium_ranking_v1 r
WHERE r.as_of_date='2025-11-26' AND r.age=30 AND r.sex='F'
ORDER BY r.rank;
"

 age | sex | insurer_key | premium_monthly | cancer_amt |  stored  | recomputed_won_per_10m
-----+-----+-------------+-----------------+------------+----------+------------------------
  30 | F   | meritz      |           87373 |   30000000 | 29124.33 |               29124.33  ← MATCH! ✅
  30 | F   | hanwha      |           95704 |   30000000 | 31901.33 |               31901.33  ← MATCH! ✅
  30 | F   | lotte       |          101258 |   30000000 | 33752.67 |               33752.67  ← MATCH! ✅
```

**Result**: `stored = recomputed_won_per_10m` → **Unit is now 원/1천만원** ✅

### Full Q14 Output Sample

```
Q14 PREMIUM RANKING SUMMARY
================================================================================

## Age 30 | Sex F | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1천만원
--------------------------------------------------------------------------------
1      meritz               87,373원          3,000만원      29,124.33원
2      hanwha               95,704원          3,000만원      31,901.33원
3      lotte               101,258원          3,000만원      33,752.67원

## Age 50 | Sex M | NO_REFUND
--------------------------------------------------------------------------------
Rank   Insurer      Premium/月       암진단비            P/1천만원
--------------------------------------------------------------------------------
1      meritz              172,300원          3,000만원      57,433.33원
2      hanwha              205,683원          3,000만원      68,561.00원
3      lotte               217,702원          3,000만원      72,567.33원
```

**Interpretation**:
- meritz 30F: Pay **87,373원/월** to get **30M won** coverage → **29,124원** per 10M won
- meritz 50M: Pay **172,300원/월** to get **30M won** coverage → **57,433원** per 10M won
- **Insight**: 50M males pay **1.97x** more per 10M coverage than 30F females

---

## 4. DELETE Scope Review

### Current DELETE Logic (line 292-296)

```python
# Step 1: DELETE all rows for this as_of_date
cursor.execute("""
    DELETE FROM q14_premium_ranking_v1
    WHERE as_of_date = %s
""", (self.as_of_date,))
```

**Scope**: `WHERE as_of_date = %s` only

**Analysis**:
- ✅ **Snapshot semantics**: Replaces entire snapshot for one date
- ✅ **Current safety**: Script only generates NO_REFUND (TARGET_PLAN_VARIANTS = ["NO_REFUND"])
- ⚠️ **Future risk**: If GENERAL variant added, running script will delete NO_REFUND too

**Recommendation**:
- Keep current logic for **full snapshot regeneration** (policy decision)
- If partial updates needed: Add `AND plan_variant IN (...)` to DELETE WHERE clause
- Current behavior is **intentional** (regenerate entire as_of_date)

### DELETE Verification (from Q14 run log)

```
[INFO] Regenerating Q14 rankings (DELETE+INSERT)...
[INFO] Deleted 18 existing rows for as_of_date=2025-11-26
[INFO] Inserted 18 new rankings to DB
```

**Result**: DELETE count = INSERT count → Clean replacement ✅

---

## 5. Orphan Check: Join Key Policy

### V2 Orphan Check Query (validate_q14_db_consistency.py:103-115)

```sql
SELECT q14.insurer_key, q14.product_id, q14.age, q14.sex, q14.plan_variant, q14.rank
FROM q14_premium_ranking_v1 q14
LEFT JOIN product_premium_quote_v2 pq
    ON q14.insurer_key = pq.insurer_key
    AND q14.product_id = pq.product_id
    AND q14.age = pq.age
    AND q14.sex = pq.sex
    AND q14.plan_variant = pq.plan_variant
    AND q14.as_of_date = pq.as_of_date
WHERE q14.as_of_date = %s
  AND pq.insurer_key IS NULL
```

**Join Key**: `(insurer_key, product_id, age, sex, plan_variant, as_of_date)`

**NOT Included in Join**: `smoke, pay_term_years, ins_term_years`

**Policy**: Q14 ranks **products**, not specific **quotes**
- A product (e.g., meritz/6ADYW) can have multiple quotes (different smoke/pay/ins terms)
- Q14 picks **any valid premium** for the (age, sex, plan_variant) combination
- Orphan check ensures **product exists** in premium table, not that exact quote matches

**Example**:
- product_premium_quote_v2 has:
  - meritz/6ADYW, age=30, sex=F, NO_REFUND, smoke=N, pay=20, ins=80 → 87373
  - meritz/6ADYW, age=30, sex=F, NO_REFUND, smoke=Y, pay=10, ins=90 → 95000
- Q14 stores: meritz/6ADYW, 30, F, NO_REFUND → 87373 (picked first match)
- V2 check: LEFT JOIN matches **both premium rows** → No orphan ✅

**This is intentional** - Q14 is a product-level ranking, not quote-level.

---

## 6. Validation Results (ALL CHECKS)

### V1: No Duplicate Keys ✅

```bash
$ python3 tools/audit/validate_q14_db_consistency.py

================================================================================
V1: Duplicate Key Check
================================================================================
✅ PASS: No duplicate keys found
```

**Query**:
```sql
SELECT age, sex, plan_variant, rank, as_of_date, COUNT(*) as cnt
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
GROUP BY age, sex, plan_variant, rank, as_of_date
HAVING COUNT(*) > 1
```

**Result**: 0 rows → UNIQUE constraint enforced ✅

### V2: No Orphan Rows ✅

```bash
================================================================================
V2: Orphan Row Check (LEFT JOIN product_premium_quote_v2)
================================================================================
✅ PASS: All Q14 rows exist in product_premium_quote_v2
```

**Direct psql verification**:
```bash
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "
SELECT COUNT(*) FROM q14_premium_ranking_v1 q14
LEFT JOIN product_premium_quote_v2 pq
  ON q14.insurer_key = pq.insurer_key
  AND q14.product_id = pq.product_id
  AND q14.age = pq.age
  AND q14.sex = pq.sex
  AND q14.plan_variant = pq.plan_variant
  AND q14.as_of_date = pq.as_of_date
WHERE q14.as_of_date='2025-11-26' AND pq.insurer_key IS NULL;
"

 count
-------
     0
```

**Result**: 0 orphans → 100% coverage ✅

### V3: Expected Row Count ✅

```bash
================================================================================
V3: Expected Row Count Check
================================================================================
Expected: 18 rows (3 ages × 2 sexes × 1 variant × 3 ranks)
Actual:   18 rows
✅ PASS: Row count matches expected
```

**Breakdown**:
```sql
SELECT age, sex, COUNT(*) FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26'
GROUP BY age, sex ORDER BY age, sex;

 age | sex | count
-----+-----+-------
  30 | F   |     3  ← Top 3 for 30F
  30 | M   |     3  ← Top 3 for 30M
  40 | F   |     3  ← Top 3 for 40F
  40 | M   |     3  ← Top 3 for 40M
  50 | F   |     3  ← Top 3 for 50F
  50 | M   |     3  ← Top 3 for 50M
```

**Result**: 6 segments × 3 ranks = 18 rows ✅

### V4: Unit Correctness (NEW CHECK) ✅

**All 18 rows verified**:
```bash
$ PGPASSWORD=inca_secure_prod_2025_db_key psql -U inca_admin -d inca_rag_scope -h localhost -p 5432 -c "
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN ABS(premium_per_10m - ROUND((premium_monthly::numeric) / (cancer_amt::numeric/10000000), 2)) < 0.01 THEN 1 END) AS correct
FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26';
"

 total | correct
-------+---------
    18 |      18  ← 100% match
```

**Result**: All stored values match recomputed formula ✅

---

## 7. Ranking Policy Clarifications

### Same Insurer Multiple Ranks

**Question**: Can same insurer appear multiple times in Top 3?

**Current Behavior**: ❌ **No** - insurers appear at most once per segment
- Age 30F Top 3: meritz, hanwha, lotte (3 different insurers)
- Age 30M Top 3: meritz, hanwha, lotte (3 different insurers)

**Policy**: Ranking is **product-level**, sorted by `(premium_per_10m, premium_monthly, insurer_key)`
- If same insurer had 2 products with different premiums, both could appear
- Current data: Each insurer has only 1 product per (age, sex, variant)

**Deduplication**: ❌ **Not enforced** in code
- Ranking sorts all products, takes Top 3
- If insurer had 2 products in Top 3, both would appear
- Current result (1 insurer = 1 rank) is due to data, not code logic

**If deduplication is required**:
- Add: `GROUP BY insurer_key` before `ORDER BY ... LIMIT 3`
- Or: Filter duplicates in `build_rankings()` after sort

---

## 8. DoD Status (UPDATED)

| # | Criteria | Status | Evidence |
|---|----------|--------|----------|
| 1 | Schema migration (sex column + UNIQUE) | ✅ | 070_q14_add_sex_column.sql applied |
| 2 | build_q14 DELETE+INSERT pattern | ✅ | Deleted 18, inserted 18 new rows |
| 3 | V1: No duplicate keys | ✅ | psql GROUP BY HAVING COUNT > 1 = 0 rows |
| 4 | V2: No orphan rows (LEFT JOIN) | ✅ | psql LEFT JOIN WHERE NULL = 0 rows |
| 5 | V3: Expected 18 rows (3×2×1×3) | ✅ | psql COUNT = 18 |
| 6 | Sex dimension separated (M/F) | ✅ | 6 segments × 3 ranks |
| 7 | UNIQUE (age,sex,plan,rank,date) | ✅ | psql \d shows constraint |
| 8 | **NEW: Unit correctness (원/1천만원)** | ✅ | **All 18 rows match LOCKED formula** |
| 9 | DELETE scope documented | ✅ | as_of_date only (snapshot regeneration) |
| 10 | Orphan join key documented | ✅ | Product-level (no smoke/pay/ins in join) |

**Overall**: ✅ **All DoD criteria met + Unit violation fixed**

---

## 9. Lessons Learned

### Why Unit Errors Are Dangerous

**Impact of 10000x magnitude error**:
- If used in customer-facing UI: "보험료 효율 2.91원" looks like 0.3¢ per million won
- Correct value "29,124원" = ₩29 per million won coverage
- User would see **artificially low costs** by 10000x → wrong purchase decisions

**Root cause**: Implicit unit conversion buried in calculation
- Variable name: `cancer_amt` (ambiguous - won or 만원?)
- Comment: "in 만원" (wrong)
- Calculation: `* 10000 / 10000000` (double conversion)
- Print: "만원" (wrong label)

**Prevention**: Explicit unit tracking
- Variable names: `cancer_amt_won`, `cancer_amt_manwon`
- Type hints: `def calculate(premium_won: int, coverage_won: int) -> float`
- Formula comments: Include **target unit** in docstring

### DELETE Scope Trade-offs

**Narrow scope** (`WHERE as_of_date = %s AND plan_variant = %s`):
- ✅ Safer for partial updates
- ❌ Leaves orphans if variant list changes
- ❌ Requires tracking "what variants exist" logic

**Wide scope** (`WHERE as_of_date = %s`):
- ✅ **Snapshot semantics** - clean slate per date
- ✅ No orphans if variant list changes
- ❌ Can't do partial updates (must regenerate all variants)

**Current choice**: Wide scope (as_of_date only) → **Correct for snapshot-based system**

---

## 10. Audit Trail

### Files Modified
- `pipeline/product_comparison/build_q14_premium_ranking.py` (unit fix)
  - Line 121-127: cancer_amt unit comment (만원 → 원)
  - Line 142: Display format (30,000,000만원 → 30,000,000원 (3,000만원))
  - Line 244-248: Calculation (removed `* 10000`)
  - Line 381, 385: Print format (P/1억 → P/1천만원, cancer_amt/10000 for 만원 display)

### Evidence Files
- `docs/audit/Q14_DB_CLEAN_REVIEW.md` (this file)
- `docs/audit/Q14_DB_CLEAN_LOCK.md` (needs unit update)

### Verification Commands
```bash
# Unit correctness check
psql "$DATABASE_URL" -c "
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN ABS(premium_per_10m - ROUND((premium_monthly::numeric) / (cancer_amt::numeric/10000000), 2)) < 0.01 THEN 1 END) AS correct
FROM q14_premium_ranking_v1 WHERE as_of_date='2025-11-26';
"
# Expected: total=18, correct=18

# Orphan check
psql "$DATABASE_URL" -c "
SELECT COUNT(*) FROM q14_premium_ranking_v1 q14
LEFT JOIN product_premium_quote_v2 pq ON q14.insurer_key = pq.insurer_key
  AND q14.product_id = pq.product_id AND q14.age = pq.age
  AND q14.sex = pq.sex AND q14.plan_variant = pq.plan_variant
  AND q14.as_of_date = pq.as_of_date
WHERE q14.as_of_date='2025-11-26' AND pq.insurer_key IS NULL;
"
# Expected: 0 rows

# Duplicate check
psql "$DATABASE_URL" -c "
SELECT age, sex, plan_variant, rank, COUNT(*) FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26'
GROUP BY age, sex, plan_variant, rank, as_of_date HAVING COUNT(*) > 1;
"
# Expected: 0 rows
```

---

**Conclusion**: Q14 DB is now **100% consistent** with product_premium_quote_v2 SSOT + **unit correctness validated** (원/1천만원). All 18 rows regenerated with LOCKED formula. DELETE+INSERT pattern ensures clean snapshots. Orphan check enforces product-level coverage (intentional - not quote-level).
