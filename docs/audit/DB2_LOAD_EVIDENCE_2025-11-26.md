# DB2 Load Evidence - as_of_date=2025-11-26

**Date:** 2026-01-09
**Loader:** tools/premium/run_db2_load.py
**baseDt:** 20251126
**as_of_date:** 2025-11-26
**Status:** ✅ VERIFIED

---

## Query 1: Product Count Verification

**Query:**
```sql
SELECT count(*) FROM product_premium_quote_v2 WHERE as_of_date='2025-11-26';
```

**Result:**
```
 count
-------
    48
(1 row)
```

**Status:** ✅ PASS (48 products loaded)

---

## Query 2: Sum Mismatch Verification (ZERO TOLERANCE)

**Query:**
```sql
SELECT p.insurer_key, p.product_id, p.age, p.sex,
       p.premium_monthly_total as header,
       COALESCE(SUM(c.premium_monthly_coverage),0) as sum_cov,
       (p.premium_monthly_total - COALESCE(SUM(c.premium_monthly_coverage),0)) as diff
FROM product_premium_quote_v2 p
LEFT JOIN coverage_premium_quote c
  ON c.insurer_key=p.insurer_key
 AND c.product_id=p.product_id
 AND c.plan_variant=p.plan_variant
 AND c.age=p.age AND c.sex=p.sex AND c.smoke=p.smoke
 AND c.as_of_date=p.as_of_date
WHERE p.as_of_date='2025-11-26'
GROUP BY 1,2,3,4,5
HAVING (p.premium_monthly_total - COALESCE(SUM(c.premium_monthly_coverage),0)) <> 0
LIMIT 5;
```

**Result:**
```
 insurer_key | product_id | age | sex | header | sum_cov | diff
-------------+------------+-----+-----+--------+---------+------
(0 rows)
```

**Status:** ✅ PASS (0 mismatches - ZERO TOLERANCE enforced)

---

## Conclusion

✅ **DB2 Load Success Evidence (LOCKED)**

- Product records: 48 rows
- Coverage records: 1494 rows (from previous verification)
- Sum validation: 0 mismatches
- All products have matching coverage sum (premium_monthly_total == sum(premium_monthly_coverage))

**Evidence timestamp:** 2026-01-09
**DB:** inca_rag_scope @ localhost:5432
**Natural key:** as_of_date (NOT base_dt)
