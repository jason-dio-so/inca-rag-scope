# FINAL SMOKE GATE - Q1/Q12/Q14 Validation Log

**Date**: 2026-01-12
**as_of_date**: 2025-11-26
**Script**: `tools/audit/validate_final_q1_q12_q14.py`
**Result**: ✅ PASS

---

## Execution

```bash
export DATABASE_URL="postgresql://inca_admin:inca_secure_prod_2025_db_key@127.0.0.1:5432/inca_rag_scope"
python3 tools/audit/validate_final_q1_q12_q14.py --as-of-date 2025-11-26
```

---

## Full Output

```
================================================================================
FINAL SMOKE GATE - Q1/Q12/Q14 VALIDATION
================================================================================
as_of_date: 2025-11-26

✅ Connected to database

================================================================================
DATABASE METADATA
================================================================================
Database: inca_rag_scope
User: inca_admin
Version: PostgreSQL 16.11 (Debian 16.11-1.pgdg12+1) on aarc...

Required Tables:
  ✅ product_premium_quote_v2
  ✅ coverage_premium_quote
  ✅ q14_premium_ranking_v1
  ✅ q14_premium_top4_v1

================================================================================
Q14 VALIDATION: Premium Top4
================================================================================

[CHECK] Row counts by plan_variant
  ✅ GENERAL: 24 rows (expected: 24)
  ✅ NO_REFUND: 24 rows (expected: 24)

[CHECK] Segment breakdown (age × sex × variant)
  ✅ All segments have exactly 4 rows

[CHECK] Sorting order within segments
  ✅ All segments sorted correctly

================================================================================
Q1 VALIDATION: Cost-Efficiency Ranking
================================================================================

[CHECK] Row counts by plan_variant
  ✅ GENERAL: 18 rows (expected: 18)
  ✅ NO_REFUND: 18 rows (expected: 18)

[CHECK] Formula integrity: premium_per_10m = premium_monthly / (cancer_amt / 10M)
  ✅ Formula mismatches: 0 (expected: 0)

[CHECK] Orphan detection (rankings without matching product)
  ✅ Orphan rows: 0 (expected: 0)

[CHECK] Segment breakdown (age × sex × variant)
  ✅ All segments have exactly 3 rows

================================================================================
Q12 VALIDATION: Samsung vs Meritz Comparison
================================================================================

[CHECK] Samsung and Meritz data availability
  ✅ All segments present for both insurers

[CHECK] Sample comparison (age=30, sex=M, variant=NO_REFUND)
  ✅ meritz: product_id=6ADYW, premium=96,111원
  ✅ samsung: product_id=ZPB275100, premium=132,685원
  ✅ Cheaper: meritz, Difference: 36,574원 (27.56%)

================================================================================
FINAL SUMMARY
================================================================================

✅ FINAL LOCK PASS

All validation checks passed:
  ✅ Q14: 48 rows (24 NO_REFUND + 24 GENERAL)
  ✅ Q14: All segments have 4 rows
  ✅ Q14: Sorting verified
  ✅ Q1: 36 rows (18 NO_REFUND + 18 GENERAL)
  ✅ Q1: Formula integrity verified
  ✅ Q1: No orphan rows
  ✅ Q1: All segments have 3 rows
  ✅ Q12: Samsung and Meritz data available
```

---

## Exit Code

```
0 (PASS)
```

---

## Validation Summary

### Q14 (Premium Top4)
- ✅ Total: 48 rows (24 NO_REFUND + 24 GENERAL)
- ✅ Segments: 12 segments × 4 rows = 48 total
- ✅ Sorting: premium_monthly ASC, insurer_key ASC verified
- ✅ Table: `q14_premium_top4_v1`

### Q1 (Cost-Efficiency)
- ✅ Total: 36 rows (18 NO_REFUND + 18 GENERAL)
- ✅ Segments: 12 segments × 3 rows = 36 total
- ✅ Formula: `premium_per_10m = premium_monthly / (cancer_amt / 10M)` verified
- ✅ Orphans: 0 (all rankings have matching products)
- ✅ Table: `q14_premium_ranking_v1`

### Q12 (Samsung vs Meritz)
- ✅ Data availability: Both insurers present in all segments
- ✅ Sample comparison: 30M NO_REFUND shows meritz 27.56% cheaper
- ✅ Table: `product_premium_quote_v2`

---

## Governance

- ❌ No estimation or fallback used
- ❌ No data imputation
- ✅ DB SSOT only
- ✅ Zero tolerance validation (all checks PASS)
- ✅ Deterministic snapshot (as_of_date=2025-11-26)

---

## Next Steps

This validation log confirms that:
1. Q1/Q12/Q14 data is complete and accurate
2. All formulas and sorting rules are correct
3. Ready for frontend/backend integration
4. ViewModel spec locked (see `docs/ui/FINAL_VIEWMODEL_LOCK.md`)
