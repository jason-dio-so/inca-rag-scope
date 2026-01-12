# Q1/Q14 Presentation Spec LOCK

**Date**: 2026-01-12
**Task**: STEP NEXT-FINAL
**Status**: 🔒 **LOCKED**

---

## Executive Summary

**Purpose**: Define separate, non-interchangeable presentation specs for Q14 (보험료 Top4) and Q1 (가성비 Top3).

**Core Principle**: **Q14 and Q1 use the same SSOT but MUST NOT mix calculation/sorting/formatting logic.**

---

## Q14: 보험료 Top4 (Premium Ranking)

### Purpose
Show **pure premium ranking** - cheapest monthly premiums per segment.

### Data Source (LOCKED)
- **Table**: `q14_premium_top4_v1`
- **SSOT**: `product_premium_quote_v2`
- **Scope**: NO_REFUND only (GENERAL requires multiplier, not in SSOT)

### Sorting Rules (LOCKED)
```sql
ORDER BY premium_monthly_total ASC, insurer_key ASC
LIMIT 4
```

**Prohibited**:
- ❌ `premium_per_10m` calculation (this is Q1's metric, NOT Q14's)
- ❌ Coverage amount normalization
- ❌ Any efficiency metrics

### Output Format (LOCKED)

**Table Columns**:
1. 순위 (Rank)
2. 보험사 (Insurer)
3. 상품명 (Product Name)
4. 월납보험료 - 무해지 (Monthly Premium - NO_REFUND)
5. 월납보험료 - 일반 (Monthly Premium - GENERAL)

**Current Reality**:
- NO_REFUND column: ✅ Show actual DB value
- GENERAL column: ⚠️ Show "-" or blank (NO estimation/calculation allowed)

**Metadata (below table)**:
- as_of_date
- Segment: (age, sex, plan_variant)
- Source: product_premium_quote_v2

### Expected Rows
- **24 rows** = 3 ages × 2 sexes × 1 variant × Top 4
- Future (with GENERAL): 48 rows = 3 ages × 2 sexes × 2 variants × Top 4

---

## Q1: 가성비 Top3 (Cost-Efficiency Ranking)

### Purpose
Show **normalized cost-efficiency** - premium per 10M won of cancer coverage.

### Data Source (LOCKED)
- **Table**: `q14_premium_ranking_v1`
- **SSOT**: `product_premium_quote_v2` + `compare_rows_v1.jsonl` (A4200_1 payout_limit)

### Calculation (LOCKED)
```python
cancer_amt = compare_rows[insurer_key]["A4200_1"]["payout_limit"]  # 원 단위
premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)
# Unit: 원/1천만원
```

**Prohibited**:
- ❌ Fixed cancer_amt fallback (e.g., 3000만원 assumption)
- ❌ Estimation/averaging of payout_limit
- ❌ Using coverage from other cancer codes (only A4200_1)

### Sorting Rules (LOCKED)
```sql
ORDER BY premium_per_10m ASC, premium_monthly_total ASC, insurer_key ASC
LIMIT 3
```

### Output Format (LOCKED)

**Age-Separated Blocks** (30세 / 40세 / 50세):

Each block has **Top 3 table**:
1. 순위 (Rank)
2. 보험사 (Insurer)
3. 월보험료 (Monthly Premium)
4. 암진단비 (Cancer Coverage Amount)
5. 1천만원당 보험료 (Premium per 10M won)

**Metadata (below each block)**:
- as_of_date
- Segment: (age, sex, plan_variant)
- Source: product_premium_quote_v2, compare_rows_v1

### Expected Rows
- **18 rows** = 3 ages × 2 sexes × 1 variant × Top 3
- Only includes insurers with valid A4200_1 payout_limit (NO fallback)

---

## Separation Rules (CRITICAL)

### 1. Q14 vs Q1 Distinction (LOCKED)

| Aspect | Q14 (보험료 Top4) | Q1 (가성비 Top3) |
|--------|------------------|-----------------|
| **Metric** | Premium (원) | Premium per 10M coverage (원/1천만원) |
| **Sorting** | premium_monthly ASC | premium_per_10m ASC |
| **Top-N** | 4 | 3 |
| **Coverage Requirement** | ❌ Not needed | ✅ Required (A4200_1 payout_limit) |
| **Calculation** | ❌ None | ✅ Normalization formula |
| **Table** | q14_premium_top4_v1 | q14_premium_ranking_v1 |

### 2. When Showing Both (UI/Report)

**MUST**:
- Use separate sections with clear labels
- Q14 label: "월보험료 순위 (Top 4)"
- Q1 label: "암진단비 1천만원당 보험료 순위 (Top 3)"

**Prohibited**:
- ❌ Mixing Q14 and Q1 data in same table
- ❌ Using Q1 calculation in Q14
- ❌ Using Q14 sorting in Q1

### 3. Prohibited Behaviors (ABSOLUTE)

#### ❌ GENERAL Variant Estimation
```python
# PROHIBITED
if plan_variant == "GENERAL" and not in SSOT:
    general_premium = no_refund_premium * multiplier  # ❌ NO!
```

**Policy**: If GENERAL not in SSOT, show blank/"-" or skip entirely.

#### ❌ Cancer Amount Fallback
```python
# PROHIBITED
cancer_amt = payout_limit or 30_000_000  # ❌ NO FALLBACK!
```

**Policy**: If payout_limit missing/null, **exclude that insurer** from Q1 ranking.

#### ❌ Q1/Q14 Metric Mixing
```python
# PROHIBITED in Q14
q14_rankings.sort(key=lambda x: x["premium_per_10m"])  # ❌ Q14 uses premium_monthly only!

# PROHIBITED in Q1
q1_rankings.sort(key=lambda x: x["premium_monthly"])  # ❌ Q1 uses premium_per_10m!
```

---

## Validation (DoD)

### D1: Q14 Output ✅
- 24 rows (3 ages × 2 sexes × NO_REFUND × Top 4)
- Sorted by premium_monthly ASC, insurer_key ASC
- V1: Row counts ≤ 4 per segment
- V2: No orphan rows (100% LEFT JOIN match)
- V3: Sorting matches recomputed (3 segments verified)

**Evidence**:
```bash
$ python3 tools/audit/validate_q14_top4.py
✅ All validation checks passed
```

### D2: Q1 Output ✅
- 18 rows (3 ages × 2 sexes × NO_REFUND × Top 3)
- Sorted by premium_per_10m ASC
- Only insurers with valid A4200_1 payout_limit
- V1: No duplicate keys
- V2: No orphan rows
- V3: Expected 18 rows
- V4: Unit correctness (원/1천만원)

**Evidence**:
```bash
$ python3 tools/audit/validate_q14_db_consistency.py
✅ All validation checks passed
```

### D3: No Fallback Logic (grep audit)
```bash
$ grep -r "30_000_000" pipeline/product_comparison/
# Expected: 0 matches (no hardcoded cancer_amt)

$ grep -r "multiplier" pipeline/product_comparison/build_q14*.py
# Expected: 0 matches (no GENERAL estimation)
```

### D4: Calculation Verification (psql)
**Q1 (premium_per_10m)**:
```sql
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN ABS(premium_per_10m - ROUND((premium_monthly::numeric) / (cancer_amt::numeric/10000000), 2)) < 0.01 THEN 1 END) AS correct
FROM q14_premium_ranking_v1 WHERE as_of_date='2025-11-26';
-- Expected: total=18, correct=18 ✅
```

**Q14 (premium_monthly)**:
```sql
SELECT q14.insurer_key, q14.premium_monthly,
       ROUND(pq.premium_monthly_total, 2) AS ssot_premium
FROM q14_premium_top4_v1 q14
JOIN product_premium_quote_v2 pq
  ON q14.insurer_key = pq.insurer_key
  AND q14.product_id = pq.product_id
  AND q14.age = pq.age
  AND q14.sex = pq.sex
  AND q14.plan_variant = pq.plan_variant
  AND q14.as_of_date = pq.as_of_date
WHERE q14.as_of_date='2025-11-26'
  AND ABS(q14.premium_monthly - pq.premium_monthly_total) > 0.01;
-- Expected: 0 rows ✅
```

---

## Implementation References

### Q14 (보험료 Top4)
- **Schema**: `schema/080_q14_premium_top4.sql`
- **Builder**: `pipeline/product_comparison/build_q14_premium_top4.py`
- **Validator**: `tools/audit/validate_q14_top4.py`
- **Table**: `q14_premium_top4_v1`

### Q1 (가성비 Top3)
- **Schema**: Reuses `q14_premium_ranking_v1` (legacy naming, but correct data)
- **Builder**: `pipeline/product_comparison/build_q14_premium_ranking.py`
- **Validator**: `tools/audit/validate_q14_db_consistency.py`
- **Table**: `q14_premium_ranking_v1`

**Note**: `q14_premium_ranking_v1` naming is historical (from when Q14 was cost-efficiency). Consider renaming to `q1_cost_efficiency_v1` in future migration to avoid confusion.

---

## Sample Output (Mock UI)

### Q14: 월보험료 순위 (Top 4)

**30세 남성 | 무해지환급형 | 2025-11-26 기준**

| 순위 | 보험사 | 상품명 | 월납보험료 (무해지) | 월납보험료 (일반) |
|-----|--------|--------|-------------------|------------------|
| 1 | 메리츠 | 6ADYW | 96,111원 | - |
| 2 | 한화 | LA02768003 | 110,981원 | - |
| 3 | 롯데 | LA0772E002 | 118,594원 | - |
| 4 | 삼성 | ZPB275100 | 132,685원 | - |

---

### Q1: 암진단비 1천만원당 보험료 순위 (Top 3)

**30세 남성 | 무해지환급형 | 2025-11-26 기준**

| 순위 | 보험사 | 월보험료 | 암진단비 | 1천만원당 보험료 |
|-----|--------|---------|---------|----------------|
| 1 | 메리츠 | 96,111원 | 3,000만원 | 32,037원 |
| 2 | 한화 | 110,981원 | 3,000만원 | 36,994원 |
| 3 | 롯데 | 118,594원 | 3,000만원 | 39,531원 |

---

**Interpretation**:
- **Q14**: 메리츠 is cheapest premium (96,111원/월)
- **Q1**: 메리츠 has best efficiency (32,037원 per 10M won coverage)
- Both metrics agree (메리츠 ranks #1) but **calculation/sorting/purpose are different**

---

## Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-12 | Created Q1_Q14_PRESENTATION_LOCK.md | STEP NEXT-FINAL - Separate Q14 (Top4 premium) from Q1 (Top3 efficiency) |

---

**Status**: 🔒 **LOCKED** - No modifications without explicit approval + audit trail
