# STEP NEXT-DBR-2: Premium SSOT Natural Key Lock - Audit Report

**Date:** 2026-01-09
**Database:** inca_rag_scope @ localhost:5432
**Status:** ✅ COMPLETE

---

## Summary

Applied UNIQUE natural key constraints to premium tables to enable proper UPSERT with `as_of_date`.

---

## Migration Applied

**File:** `schema/060_premium_ssot_keys.sql`

**Changes:**
1. Added UNIQUE constraint to `premium_quote`
2. Added UNIQUE constraint to `coverage_premium_quote`
3. Verified existing UNIQUE constraint on `product_premium_quote_v2`
4. Added performance indexes on `as_of_date` columns

---

## Evidence: UNIQUE Constraints

**Query:**
```sql
SELECT conrelid::regclass AS table_name, conname AS constraint_name,
       pg_get_constraintdef(oid) AS constraint_def
FROM pg_constraint
WHERE contype = 'u'
  AND conrelid::regclass::text IN ('premium_quote', 'coverage_premium_quote', 'product_premium_quote_v2')
ORDER BY conrelid, conname;
```

**Output:**
```
        table_name        |         constraint_name         |                                               constraint_def
--------------------------+---------------------------------+-------------------------------------------------------------------------------------------------------------
 premium_quote            | uq_premium_quote_natural_key    | UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, as_of_date)
 coverage_premium_quote   | uq_coverage_premium_natural_key | UNIQUE (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date)
 product_premium_quote_v2 | uq_product_premium              | UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
(3 rows)
```

**Verification:** ✅ ALL 3 tables have UNIQUE constraints with `as_of_date`

---

## Natural Key Design

### premium_quote
```
UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, as_of_date)
```
**Business Logic:** One quote per (insurer, product, plan variant, demographics, date)

### coverage_premium_quote
```
UNIQUE (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date)
```
**Business Logic:** One premium per (insurer, product, coverage, plan variant, demographics, date)

### product_premium_quote_v2
```
UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
```
**Business Logic:** One product premium per (insurer, product, plan variant, demographics, terms, date)

---

## UPSERT Pattern Enabled

With natural keys locked, code can now use:

```sql
INSERT INTO product_premium_quote_v2 (
    insurer_key, product_id, plan_variant, age, sex, smoke,
    pay_term_years, ins_term_years, as_of_date,
    premium_monthly_total, premium_total_total, ...
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ...)
ON CONFLICT (insurer_key, product_id, plan_variant, age, sex, smoke,
             pay_term_years, ins_term_years, as_of_date)
DO UPDATE SET
    premium_monthly_total = EXCLUDED.premium_monthly_total,
    premium_total_total = EXCLUDED.premium_total_total,
    updated_at = CURRENT_TIMESTAMP;
```

**Benefits:**
- Idempotent API loads (safe to re-run with same baseDt)
- No duplicate rows
- Proper data versioning by `as_of_date`

---

## Performance Indexes

**Indexes Created:**
```
idx_premium_quote_as_of_date
idx_coverage_premium_as_of_date
idx_product_premium_v2_as_of_date
```

**Purpose:** Fast date-based queries (latest premium, date range filters)

---

## Next Steps

1. Fix code to use `as_of_date` (NOT `base_dt`)
2. Implement baseDt → as_of_date conversion
3. Update all UPSERT logic to use ON CONFLICT
4. Execute DB2 real load (12 API calls)
5. Verify row counts > 0

---

**STATUS:** ✅ Natural keys locked and verified
**BLOCKER REMOVED:** DB schema now ready for proper UPSERT operations
