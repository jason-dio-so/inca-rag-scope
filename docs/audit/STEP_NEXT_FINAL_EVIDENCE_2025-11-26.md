# STEP NEXT-FINAL: Q1/Q14 Snapshot Evidence (2025-11-26)

**Date**: 2026-01-12
**as_of_date**: 2025-11-26
**plan_variant**: NO_REFUND
**Status**: 🔒 **LOCKED**

---

## 📋 Executive Summary

This document serves as the **IMMUTABLE SNAPSHOT EVIDENCE** for Q1 (가성비 Top3) and Q14 (보험료 Top4) results calculated from `as_of_date=2025-11-26` premium data with `plan_variant=NO_REFUND`.

**Key Declarations**:
- ✅ Q14 (보험료 Top4): **24 rows** (6 segments × 4 ranks)
- ✅ Q1 (가성비 Top3): **18 rows** (6 segments × 3 ranks)
- ✅ Total: **42 rows**
- ✅ Orphan count: **0**
- ✅ Formula mismatch: **0**
- 🔒 Recalculation: **FORBIDDEN** (new as_of_date only)

---

## 🗄️ Database Configuration

**Connection Details**:
- Host: `localhost` (Docker container: `inca_pg_step14`)
- Port: `5433` (mapped to container 5432)
- Database: `inca_rag_scope`
- User: `postgres`
- PostgreSQL Version: `17-alpine`

**Tables**:
- `q14_premium_top4_v1` — Q14 보험료 Top4 rankings
- `q14_premium_ranking_v1` — Q1 가성비 Top3 rankings

---

## 📊 Q14 (보험료 Top4) Evidence

### Snapshot Metadata

**Table**: `q14_premium_top4_v1`

**Filter Criteria**:
```sql
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
```

### Row Count Evidence

**Total Rows**: 24

**Segment Breakdown** (6 segments × 4 ranks each):
```
seg_age | seg_sex | row_count
--------|---------|----------
   30   |    F    |     4
   30   |    M    |     4
   40   |    F    |     4
   40   |    M    |     4
   50   |    F    |     4
   50   |    M    |     4
--------|---------|----------
 TOTAL  |         |    24
```

### Formula Lock

**Sorting Rule** (Constitutional):
```sql
ORDER BY premium_monthly_total ASC,
         insurer_key ASC
LIMIT 4 PER (seg_age, seg_sex, plan_variant)
```

**Where**:
- `premium_monthly_total`: Total monthly premium from Greenlight API
- `insurer_key`: Insurer canonical key (SSOT)

**Output Columns**:
1. `rank` (1-4)
2. `insurer_key`
3. `product_name`
4. `premium_monthly_total` (원)
5. `seg_age` (30/40/50)
6. `seg_sex` (M/F)
7. `plan_variant` (NO_REFUND)
8. `as_of_date` (2025-11-26)

### Orphan Check

**Orphan Definition**: Rows with NULL identity keys

**Query**:
```sql
SELECT COUNT(*) as orphan_count
FROM q14_premium_top4_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND (insurer_key IS NULL
       OR product_key IS NULL
       OR variant_key IS NULL);
```

**Result**: **0 orphans** ✅

---

## 📊 Q1 (가성비 Top3) Evidence

### Snapshot Metadata

**Table**: `q14_premium_ranking_v1`

**Filter Criteria**:
```sql
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
```

### Row Count Evidence

**Total Rows**: 18

**Segment Breakdown** (6 segments × 3 ranks each):
```
seg_age | seg_sex | row_count
--------|---------|----------
   30   |    F    |     3
   30   |    M    |     3
   40   |    F    |     3
   40   |    M    |     3
   50   |    F    |     3
   50   |    M    |     3
--------|---------|----------
 TOTAL  |         |    18
```

### Formula Lock (Constitutional)

**Calculation Formula**:
```
premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
```

**Where**:
- `premium_monthly`: Monthly premium from Greenlight API (원)
- `cancer_amt`: A4200_1 (암진단비(유사암제외)) payout_limit (원)

**Unit Verification**:
```
Example:
  cancer_amt = 30,000,000원 (3천만원)
  premium_monthly = 50,000원

  premium_per_10m = 50,000 / (30,000,000 / 10,000,000)
                  = 50,000 / 3.0
                  = 16,666.67원
```

**Interpretation**: "1천만원당 월보험료" (Monthly premium per 10 million won coverage)

**Sorting Rule** (Constitutional):
```sql
ORDER BY premium_per_10m ASC,
         premium_monthly ASC,
         insurer_key ASC
LIMIT 3 PER (seg_age, seg_sex, plan_variant)
```

**Output Columns**:
1. `rank` (1-3)
2. `insurer_key`
3. `product_name`
4. `premium_monthly` (원)
5. `cancer_amt` (원)
6. `premium_per_10m` (원/1천만원)
7. `seg_age` (30/40/50)
8. `seg_sex` (M/F)
9. `plan_variant` (NO_REFUND)
10. `as_of_date` (2025-11-26)

### Orphan Check

**Query**:
```sql
SELECT COUNT(*) as orphan_count
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND (insurer_key IS NULL
       OR product_key IS NULL
       OR variant_key IS NULL);
```

**Result**: **0 orphans** ✅

### Formula Verification

**Unit Consistency Check**:
```sql
SELECT COUNT(*) as mismatch_count
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND ABS(
    premium_per_10m - (premium_monthly / (cancer_amt / 10000000.0))
  ) > 0.01;
```

**Result**: **0 mismatches** ✅

---

## 📦 Data Source Evidence

### Premium Data Source

**API**: Greenlight Customer API
- Base URL: `https://new-prod.greenlight.direct/public/prdata`
- Endpoint: `/prInfo` (product-level premium)
- Method: GET with JSON body

**API Call Date** (`baseDt`): `20251126`

**Segments Called** (6 total):
```
age | sex | birthday   | API status
----|-----|------------|------------
 30 |  F  | 1995-11-26 | ✅ SUCCESS
 30 |  M  | 1995-11-26 | ✅ SUCCESS
 40 |  F  | 1985-11-26 | ✅ SUCCESS
 40 |  M  | 1985-11-26 | ✅ SUCCESS
 50 |  F  | 1975-11-26 | ✅ SUCCESS
 50 |  M  | 1975-11-26 | ✅ SUCCESS
```

**Raw Data Files**:
```
data/premium_raw/20251126/_prInfo/30_F.json (3,156 bytes)
data/premium_raw/20251126/_prInfo/30_M.json (3,154 bytes)
data/premium_raw/20251126/_prInfo/40_F.json (3,158 bytes)
data/premium_raw/20251126/_prInfo/40_M.json (3,155 bytes)
data/premium_raw/20251126/_prInfo/50_F.json (3,158 bytes)
data/premium_raw/20251126/_prInfo/50_M.json (3,155 bytes)

data/premium_raw/20251126/_prDetail/30_F.json (153,701 bytes)
data/premium_raw/20251126/_prDetail/30_M.json (153,688 bytes)
data/premium_raw/20251126/_prDetail/40_F.json (153,772 bytes)
data/premium_raw/20251126/_prDetail/40_M.json (153,760 bytes)
data/premium_raw/20251126/_prDetail/50_F.json (153,832 bytes)
data/premium_raw/20251126/_prDetail/50_M.json (153,849 bytes)
```

### Coverage Amount Source

**Table**: `compare_rows_v1.jsonl`

**Coverage Code**: `A4200_1` (암진단비(유사암제외))

**Source Field**: `proposal_facts.coverage_amount_text`

**Extraction Fix**: STEP NEXT-Y (2026-01-12)
- Prior state: 0/10 rows with payout_limit
- Fixed state: **10/10 rows** with payout_limit ✅

**Insurers with A4200_1 Coverage** (10 total):
```
1. samsung
2. db (DB손해보험, split into db_over41 / db_under40)
3. hanwha
4. heungkuk
5. hyundai
6. kb
7. lotte
8. meritz
```

---

## 🚫 Policy LOCK

### Recalculation Policy

**ABSOLUTE RULE**: Q1/Q14 results for `as_of_date=2025-11-26` are **IMMUTABLE**.

**Permitted Operations**:
- ✅ READ queries
- ✅ Snapshot export for audits
- ✅ Historical comparison (different as_of_date)

**Forbidden Operations**:
- ❌ UPDATE existing rows
- ❌ DELETE existing rows
- ❌ Partial recalculation
- ❌ Formula changes for locked date
- ❌ File-based fallbacks
- ❌ Mock data substitution

**New Calculation Policy**:
- New `as_of_date` → Full DELETE + INSERT for that date
- Never mix data from different as_of_date values
- Atomic transaction required (DELETE + INSERT must succeed together)

### Snapshot Update Policy

**When to Create New Snapshot**:
1. Premium data refresh (new API pull date)
2. Coverage amount corrections (requires new as_of_date)
3. Formula changes (requires new schema version)

**Snapshot Naming**:
```
docs/audit/STEP_NEXT_FINAL_EVIDENCE_{YYYY-MM-DD}.md
```

**Backward Compatibility**:
- Old snapshots remain valid for historical reference
- Schema version tracked in table metadata
- Migration path documented if breaking changes occur

---

## 🔍 Validation Gates

### G14-1: Row Count Gate

**Rule**: Q14 must have exactly 24 rows (6 segments × 4 ranks)

**Check**:
```sql
SELECT COUNT(*) = 24 AS pass
FROM q14_premium_top4_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND';
```

**Status**: ✅ PASS

### G14-2: Segment Completeness Gate

**Rule**: All 6 segments must have exactly 4 rows each

**Check**:
```sql
SELECT COUNT(*) = 6 AS pass
FROM (
  SELECT seg_age, seg_sex, COUNT(*) as cnt
  FROM q14_premium_top4_v1
  WHERE as_of_date = '2025-11-26'
    AND plan_variant = 'NO_REFUND'
  GROUP BY seg_age, seg_sex
  HAVING COUNT(*) = 4
) sub;
```

**Status**: ✅ PASS

### G1-1: Row Count Gate

**Rule**: Q1 must have exactly 18 rows (6 segments × 3 ranks)

**Check**:
```sql
SELECT COUNT(*) = 18 AS pass
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND';
```

**Status**: ✅ PASS

### G1-2: Formula Consistency Gate

**Rule**: `premium_per_10m` must match calculated value within 0.01원

**Check**:
```sql
SELECT COUNT(*) = 0 AS pass
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND ABS(
    premium_per_10m - (premium_monthly / (cancer_amt / 10000000.0))
  ) > 0.01;
```

**Status**: ✅ PASS

### G-ORPHAN: Identity Completeness Gate

**Rule**: No rows with NULL identity keys

**Check** (applies to both Q1 and Q14):
```sql
-- Q14
SELECT COUNT(*) = 0 AS pass_q14
FROM q14_premium_top4_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND (insurer_key IS NULL OR product_key IS NULL OR variant_key IS NULL);

-- Q1
SELECT COUNT(*) = 0 AS pass_q1
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND (insurer_key IS NULL OR product_key IS NULL OR variant_key IS NULL);
```

**Status**: ✅ PASS (both)

---

## 📝 Commit Evidence

**Commit Hash**: `c1dd59163101ae218ccbf837e72e0cd2dc332f63`

**Commit Message**:
```
feat(q1-q14-sep): Separate Q14 Premium Top4 from Q1 Cost-Efficiency Top3
```

**Related Commits**:
- `e162699` — docs(q14-lock): Add 3 policy LOCKs (snapshot/join-key/scope)
- `bb64ee4` — fix(q14-unit): CRITICAL - Fix premium_per_10m unit (만원→원/1천만원)
- `973df0c` — feat(q14-db-clean): Q14 DB consistency (sex separation + DELETE+INSERT pattern)
- `8e15160` — fix(step-next-y): restore A4200_1 payout_limit from proposal_facts (10/10 rows)

**Branch**: `feat/step-next-14-chat-ui`

**Base Branch**: `master`

---

## 🎯 Reproducibility Checklist

To reproduce Q1/Q14 results for `as_of_date=2025-11-26`:

### Prerequisites
- [x] PostgreSQL 17 with tables `q14_premium_top4_v1` and `q14_premium_ranking_v1`
- [x] Greenlight API access (`https://new-prod.greenlight.direct/public/prdata`)
- [x] `compare_rows_v1.jsonl` with A4200_1 payout_limit (10/10 rows)
- [x] Premium raw data files in `data/premium_raw/20251126/`

### Execution Steps
1. **Load Premium Data** (if not in DB):
   ```bash
   # Script: tools/premium/load_premium_from_api.py
   # Loads prInfo + prDetail for 6 segments into DB
   ```

2. **Generate Q14 Rankings**:
   ```bash
   python3 pipeline/product_comparison/build_q14_premium_top4.py \
     --as-of-date 2025-11-26 \
     --plan-variant NO_REFUND \
     --db-url $DATABASE_URL
   ```

3. **Generate Q1 Rankings**:
   ```bash
   python3 pipeline/product_comparison/build_q14_premium_ranking.py \
     --as-of-date 2025-11-26 \
     --plan-variant NO_REFUND \
     --jsonl data/compare_v1/compare_rows_v1.jsonl \
     --db-url $DATABASE_URL
   ```

4. **Validate Results**:
   ```bash
   python3 tools/audit/validate_q14_db_consistency.py \
     --as-of-date 2025-11-26 \
     --plan-variant NO_REFUND
   ```

### Expected Output
- Q14: 24 rows in `q14_premium_top4_v1`
- Q1: 18 rows in `q14_premium_ranking_v1`
- Orphan count: 0
- Formula mismatch count: 0

---

## 📚 References

**Policy Documents**:
- `docs/policy/Q1_Q14_RESPONSE_FORMAT_LOCK.md` (created in this STEP)
- `docs/active_constitution.md` (pipeline rules)

**Implementation**:
- `pipeline/product_comparison/build_q14_premium_top4.py`
- `pipeline/product_comparison/build_q14_premium_ranking.py`

**Schema**:
- `schema/050_q14_premium_ranking.sql`
- `schema/051_q14_premium_top4.sql`

**Audit Trail**:
- `docs/audit/STEP_NEXT_W_Q14_RANKING_LOCK.md` (Q1 implementation)
- `docs/audit/STEP_NEXT_Y_A4200_1_PAYOUT_LIMIT_FIX.md` (A4200_1 fix)
- `docs/audit/STEP_NEXT_DB2_PREMIUM_REAL_LOAD_LOCK.md` (Premium API load)

**Raw Data**:
- `data/premium_raw/20251126/_prInfo/*.json`
- `data/premium_raw/20251126/_prDetail/*.json`
- `data/compare_v1/compare_rows_v1.jsonl`

---

**Document Version**: 1.0
**Status**: 🔒 **IMMUTABLE**
**Last Updated**: 2026-01-12
**Next Review**: Only for new as_of_date
