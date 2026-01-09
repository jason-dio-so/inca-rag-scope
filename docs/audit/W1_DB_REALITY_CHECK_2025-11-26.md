# FIX-W1: DB Reality Check - as_of_date=2025-11-26

**Date:** 2026-01-09
**Purpose:** Verify DB state before Q14 ranking fix (remove fallback, achieve 18 rows)

---

## Query 1: product_premium_quote_v2 Variant Distribution

**Query:**
```sql
SELECT plan_variant, COUNT(*)
FROM product_premium_quote_v2
WHERE as_of_date='2025-11-26'
GROUP BY 1;
```

**Result:**
```
 plan_variant | count
--------------+-------
 NO_REFUND    |    48
(1 row)
```

**Analysis:**
- ✅ NO_REFUND: 48 rows (DB loaded)
- ❌ GENERAL: 0 rows (NOT loaded)
- **Implication**: Q14 can only generate 9 rows (3 ages × NO_REFUND × 3 ranks) until GENERAL is loaded

---

## Query 2: premium_multiplier Count

**Query:**
```sql
SELECT COUNT(*) FROM premium_multiplier;
```

**Result:**
```
 count
-------
     0
(1 row)
```

**Analysis:**
- ❌ premium_multiplier is EMPTY
- **Implication**: Cannot calculate GENERAL premiums (requires multipliers)
- **Action Required**: Load multipliers from `일반보험요율예시.xlsx` before GENERAL generation

---

## Query 3: q14_premium_ranking_v1 Variant Distribution

**Query:**
```sql
SELECT plan_variant, COUNT(*)
FROM q14_premium_ranking_v1
WHERE as_of_date='2025-11-26'
GROUP BY 1;
```

**Result:**
```
 plan_variant | count
--------------+-------
 NO_REFUND    |     9
(1 row)
```

**Analysis:**
- ✅ NO_REFUND: 9 rows (3 ages × 3 ranks)
- ❌ GENERAL: 0 rows (expected 9 rows, but source data unavailable)
- **Current**: 9/18 rows (50%)

---

## Conclusion

**DB Reality (LOCKED):**
1. **GENERAL variant is NOT available** in product_premium_quote_v2
2. **premium_multiplier is EMPTY** (required for GENERAL calculation)
3. **Q14 can only generate 9 rows** with current DB state (NO_REFUND only)

**Path to 18 Rows:**
- **Option 1**: Load GENERAL premiums via DB2 expansion (requires multipliers + API or calculation)
- **Option 2**: Document that 18 rows requires GENERAL variant (future work)

**Current Fix Scope (FIX-W1):**
- Remove cancer_amt fallback (3000만원) - POLICY VIOLATION
- Extract real payout_limit from compare_rows_v1 or SKIP insurers
- Generate 9 rows (NO_REFUND only) with NO fallback logic
- Document that 18 rows requires GENERAL variant loading (blocked by multipliers)

**Status:** DB-ONLY enforcement maintained, but GENERAL unavailable (external blocker)
