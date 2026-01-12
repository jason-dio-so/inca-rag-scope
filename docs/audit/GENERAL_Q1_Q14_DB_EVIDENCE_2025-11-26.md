# GENERAL Q1/Q14 Expansion - DB Evidence (2025-11-26)

**Date**: 2026-01-12
**Scope**: Extend Q1 (cost-efficiency) and Q14 (premium ranking) to include GENERAL variant
**Status**: ✅ PASS

---

## Preconditions: GENERAL SSOT Validation

### (A) Product Premium Rows
```sql
SELECT COUNT(*) AS n
FROM product_premium_quote_v2
WHERE as_of_date='2025-11-26' AND plan_variant='GENERAL';
```
**Result**: 48 ✅

### (B) Coverage Premium Rows
```sql
SELECT COUNT(*) AS n
FROM coverage_premium_quote
WHERE as_of_date='2025-11-26' AND plan_variant='GENERAL';
```
**Result**: 1164 ✅

### (C) Header vs Coverage Sum Integrity
```sql
SELECT COUNT(*) AS mismatch_cnt
FROM (
  SELECT p.insurer_key, p.product_id, p.age, p.sex, p.plan_variant, p.as_of_date,
         p.premium_monthly_total AS header,
         COALESCE(SUM(c.premium_monthly_coverage),0) AS sum_cov,
         (p.premium_monthly_total - COALESCE(SUM(c.premium_monthly_coverage),0)) AS diff
  FROM product_premium_quote_v2 p
  LEFT JOIN coverage_premium_quote c
    ON c.insurer_key=p.insurer_key
   AND c.product_id=p.product_id
   AND c.plan_variant=p.plan_variant
   AND c.age=p.age AND c.sex=p.sex AND c.smoke=p.smoke
   AND c.as_of_date=p.as_of_date
  WHERE p.as_of_date='2025-11-26' AND p.plan_variant='GENERAL'
  GROUP BY 1,2,3,4,5,6,7
) t
WHERE t.diff <> 0;
```
**Result**: 0 ✅

---

## Q1: Cost-Efficiency Ranking (q14_premium_ranking_v1)

### Total Row Counts by Variant
```sql
SELECT plan_variant, COUNT(*) AS n
FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26'
GROUP BY 1
ORDER BY 1;
```
**Result**:
```
 plan_variant | n
--------------+----
 GENERAL      | 18
 NO_REFUND    | 18
```
**Total**: 36 ✅ (Expected: 18 + 18 = 36)

### Segment Breakdown (age × sex × variant)
```sql
SELECT age, sex, plan_variant, COUNT(*) AS n
FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26'
GROUP BY 1,2,3
ORDER BY 1,2,3;
```
**Result**:
```
 age | sex | plan_variant | n
-----+-----+--------------+---
  30 | F   | GENERAL      | 3
  30 | F   | NO_REFUND    | 3
  30 | M   | GENERAL      | 3
  30 | M   | NO_REFUND    | 3
  40 | F   | GENERAL      | 3
  40 | F   | NO_REFUND    | 3
  40 | M   | GENERAL      | 3
  40 | M   | NO_REFUND    | 3
  50 | F   | GENERAL      | 3
  50 | F   | NO_REFUND    | 3
  50 | M   | GENERAL      | 3
  50 | M   | NO_REFUND    | 3
```
**All segments**: 3 records each ✅

### Formula Integrity Check
```sql
SELECT COUNT(*) AS mismatch_cnt
FROM (
  SELECT r.*,
         ROUND(r.premium_monthly / (r.cancer_amt / 10000000.0), 2) AS recomputed
  FROM q14_premium_ranking_v1 r
  WHERE r.as_of_date='2025-11-26'
) t
WHERE ABS(t.premium_per_10m - t.recomputed) > 0.01;
```
**Result**: 0 ✅

---

## Q14: Premium Top4 (q14_premium_top4_v1)

### Total Row Counts by Variant
```sql
SELECT plan_variant, COUNT(*) AS n
FROM q14_premium_top4_v1
WHERE as_of_date='2025-11-26'
GROUP BY 1
ORDER BY 1;
```
**Result**:
```
 plan_variant | n
--------------+----
 GENERAL      | 24
 NO_REFUND    | 24
```
**Total**: 48 ✅ (Expected: 24 + 24 = 48)

### Segment Breakdown (age × sex × variant)
```sql
SELECT age, sex, plan_variant, COUNT(*) AS n
FROM q14_premium_top4_v1
WHERE as_of_date='2025-11-26'
GROUP BY 1,2,3
ORDER BY 1,2,3;
```
**Result**:
```
 age | sex | plan_variant | n
-----+-----+--------------+---
  30 | F   | GENERAL      | 4
  30 | F   | NO_REFUND    | 4
  30 | M   | GENERAL      | 4
  30 | M   | NO_REFUND    | 4
  40 | F   | GENERAL      | 4
  40 | F   | NO_REFUND    | 4
  40 | M   | GENERAL      | 4
  40 | M   | NO_REFUND    | 4
  50 | F   | GENERAL      | 4
  50 | F   | NO_REFUND    | 4
  50 | M   | GENERAL      | 4
  50 | M   | NO_REFUND    | 4
```
**All segments**: 4 records each ✅

---

## Implementation Details

### Changes Made
1. **build_q14_premium_ranking.py**:
   - Updated `TARGET_PLAN_VARIANTS` to include `["NO_REFUND", "GENERAL"]`
   - Fixed SQL query to include both variants
   - Fixed DELETE logic to only delete target plan_variants (not all rows)
   - Fixed indentation bug in ranking loop that was skipping NO_REFUND processing

2. **build_q14_premium_top4.py**:
   - Updated `TARGET_PLAN_VARIANTS` to include `["NO_REFUND", "GENERAL"]`
   - Fixed SQL query to include both variants
   - Fixed DELETE logic to only delete target plan_variants (not all rows)

### Execution Commands
```bash
python3 pipeline/product_comparison/build_q14_premium_ranking.py --as-of-date 2025-11-26
python3 pipeline/product_comparison/build_q14_premium_top4.py --as-of-date 2025-11-26
```

---

## Final Status

```
GENERAL→Q1/Q14 EXPAND RESULT (as_of_date=2025-11-26)

Q1 q14_premium_ranking_v1:
- NO_REFUND rows: 18
- GENERAL rows:   18
- TOTAL:          36
- formula mismatch_cnt: 0

Q14 q14_premium_top4_v1:
- NO_REFUND rows: 24
- GENERAL rows:   24
- TOTAL:          48
- segment counts OK (3 or 4)

STATUS: PASS (DB EVIDENCE LOCKED)
```

---

## Governance
- ❌ No estimation or imputation used
- ❌ No fallback or averaging
- ✅ DB data only (product_premium_quote_v2)
- ✅ Zero tolerance validation (all checks = 0 mismatches)
- ✅ Deterministic snapshot regeneration (DELETE+INSERT per variant)
