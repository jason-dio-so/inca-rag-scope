# Premium SSOT Policy (LOCKED)

**Date:** 2026-01-09
**Status:** ACTIVE

---

## Policy Statement

**Premium SSOT for runtime/Q12/Q14 is `product_premium_quote_v2` + `coverage_premium_quote` (DB-ONLY).**

**`premium_quote` table is DEPRECATED and MUST NOT be read by runtime gates or Q12/Q14 logic.**

---

## Rationale

1. **Natural Key Migration**: Premium SSOT has migrated from `base_dt` to `as_of_date` natural keys (STEP NEXT-DBR-2).

2. **Schema Evolution**: `product_premium_quote_v2` includes contract terms (pay_term_years, ins_term_years) that are missing in legacy `premium_quote`.

3. **DB-ONLY Enforcement**: All premium data MUST come from DB tables loaded via `tools/premium/run_db2_load.py`. NO file-based premium, NO mock data.

---

## Tables (ACTIVE)

### ✅ `product_premium_quote_v2`
- **Status**: ACTIVE (DB-ONLY source)
- **Purpose**: Product-level premium aggregates (NO_REFUND + GENERAL)
- **Natural Key**: (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
- **Usage**: Q12 G10 gate, Q14 ranking

### ✅ `coverage_premium_quote`
- **Status**: ACTIVE (DB-ONLY source)
- **Purpose**: Coverage-level premium granularity
- **Natural Key**: (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date)
- **Usage**: Coverage-level analysis, sum validation

### ❌ `premium_quote`
- **Status**: DEPRECATED (DO NOT USE)
- **Reason**: Legacy schema without contract terms, base_dt natural key
- **Migration**: Use `product_premium_quote_v2` instead
- **Action**: Runtime gates MUST NOT query this table

---

## Code Enforcement

### Forbidden Patterns

❌ **NEVER use:**
```python
# FORBIDDEN: Reading from premium_quote table
cursor.execute("SELECT * FROM premium_quote WHERE ...")

# FORBIDDEN: File-based premium fallback
with open("data/premium/...") as f:
    premium_data = json.load(f)

# FORBIDDEN: Mock/estimated premium data
premium_monthly = estimate_premium(age, sex)
```

### Required Patterns

✅ **ALWAYS use:**
```python
# CORRECT: DB-ONLY premium from product_premium_quote_v2
cursor.execute("""
    SELECT premium_monthly_total
    FROM product_premium_quote_v2
    WHERE insurer_key = %s
      AND product_id = %s
      AND plan_variant = %s
      AND age = %s
      AND sex = %s
      AND smoke = %s
      AND as_of_date = %s
""", (insurer_key, product_id, plan_variant, age, sex, smoke, as_of_date))
```

---

## Data Loading

**ONLY** load premium data via:
```bash
python3 tools/premium/run_db2_load.py --baseDt 20251126
```

**Loaders:**
- `tools/premium/run_db2_load.py` - Greenlight API → DB (DB-ONLY)

**Validators:**
- `docs/audit/DB2_LOAD_EVIDENCE_2025-11-26.md` - DB load verification

---

## Migration Checklist

For any code that currently reads `premium_quote`:

1. ✅ Replace table reference: `premium_quote` → `product_premium_quote_v2`
2. ✅ Update natural key: `base_dt` → `as_of_date`
3. ✅ Add contract terms: Include `pay_term_years`, `ins_term_years` if needed
4. ✅ Verify DB-ONLY: NO file fallback, NO mock data

---

## Audit Trail

**Policy Owner:** STEP NEXT-DB2 / STEP NEXT-W
**Enforcement Date:** 2026-01-09
**Verification:**
- product_premium_quote_v2: 48 rows (as_of_date=2025-11-26)
- coverage_premium_quote: 1494 rows (as_of_date=2025-11-26)
- q14_premium_ranking_v1: 9 rows (NO_REFUND only)

**Evidence:** `docs/audit/DB2_LOAD_EVIDENCE_2025-11-26.md`
