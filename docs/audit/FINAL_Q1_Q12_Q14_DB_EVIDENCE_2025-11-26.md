# FINAL Q1/Q12/Q14 DB EVIDENCE (2025-11-26)

**Date**: 2026-01-12
**as_of_date**: 2025-11-26
**plan_variant**: NO_REFUND

---

## Database Configuration

**DATABASE_URL**:
```
postgresql://inca_admin:inca_secure_prod_2025_db_key@127.0.0.1:5432/inca_rag_scope
```

**Container**: `inca_rag_scope_db`

**Image**: `pgvector/pgvector:pg16`

**Connection Test**:
```sql
SELECT current_database(), current_user, inet_client_addr(), inet_client_port(), version();
```

**Result**:
```
 current_database | current_user | inet_client_addr | inet_client_port |                                                              version
------------------+--------------+------------------+------------------+------------------------------------------------------------------------------------------------------------------------------------
 inca_rag_scope   | inca_admin   | 172.20.0.1       |            65428 | PostgreSQL 16.11 (Debian 16.11-1.pgdg12+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit
(1 row)
```

---

## Q14: 보험료 Top4

### Query

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT count(*) as row_count
FROM q14_premium_top4_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND';"
```

### Row Count

```
 row_count
-----------
        24
(1 row)
```

### Full Results

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT age, sex, rank, insurer_key, product_id, premium_monthly
FROM q14_premium_top4_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
ORDER BY age, sex, rank;"
```

### Output

```
 age | sex | rank | insurer_key | product_id | premium_monthly
-----+-----+------+-------------+------------+-----------------
  30 | F   |    1 | meritz      | 6ADYW      |           87373
  30 | F   |    2 | hanwha      | LA02768003 |           95704
  30 | F   |    3 | lotte       | LA0762E002 |          101258
  30 | F   |    4 | samsung     | ZPB275100  |          106756
  30 | M   |    1 | meritz      | 6ADYW      |           96111
  30 | M   |    2 | hanwha      | LA02768003 |          110981
  30 | M   |    3 | lotte       | LA0772E002 |          118594
  30 | M   |    4 | samsung     | ZPB275100  |          132685
  40 | F   |    1 | meritz      | 6ADYW      |          112513
  40 | F   |    2 | hanwha      | LA02768003 |          124159
  40 | F   |    3 | lotte       | LA0762E002 |          131175
  40 | F   |    4 | samsung     | ZPB275100  |          137015
  40 | M   |    1 | meritz      | 6ADYW      |          125987
  40 | M   |    2 | hanwha      | LA02768003 |          149253
  40 | M   |    3 | lotte       | LA0772E002 |          159325
  40 | M   |    4 | hyundai     | 137D       |          176888
  50 | F   |    1 | meritz      | 6ADYW      |          138095
  50 | F   |    2 | hanwha      | LA02768003 |          153271
  50 | F   |    3 | lotte       | LA0762E002 |          155056
  50 | F   |    4 | samsung     | ZPB275100  |          172073
  50 | M   |    1 | meritz      | 6ADYW      |          172300
  50 | M   |    2 | hanwha      | LA02768003 |          205683
  50 | M   |    3 | lotte       | LA0772E002 |          217702
  50 | M   |    4 | db          | 30633      |          238977
(24 rows)
```

### Segment Breakdown

```
Segment   | Rank 1 Insurer | Rank 2 Insurer | Rank 3 Insurer | Rank 4 Insurer
----------|----------------|----------------|----------------|----------------
30F       | meritz         | hanwha         | lotte          | samsung
30M       | meritz         | hanwha         | lotte          | samsung
40F       | meritz         | hanwha         | lotte          | samsung
40M       | meritz         | hanwha         | lotte          | hyundai
50F       | meritz         | hanwha         | lotte          | samsung
50M       | meritz         | hanwha         | lotte          | db
```

---

## Q1: 가성비 Top3

### Query

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT count(*) as row_count
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND';"
```

### Row Count

```
 row_count
-----------
        18
(1 row)
```

### Full Results

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT age, sex, rank, insurer_key, product_id,
       premium_monthly, cancer_amt, premium_per_10m
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
ORDER BY age, sex, rank;"
```

### Output

```
 age | sex | rank | insurer_key | product_id | premium_monthly | cancer_amt | premium_per_10m
-----+-----+------+-------------+------------+-----------------+------------+-----------------
  30 | F   |    1 | meritz      | 6ADYW      |           87373 |   30000000 |        29124.33
  30 | F   |    2 | hanwha      | LA02768003 |           95704 |   30000000 |        31901.33
  30 | F   |    3 | lotte       | LA0762E002 |          101258 |   30000000 |        33752.67
  30 | M   |    1 | meritz      | 6ADYW      |           96111 |   30000000 |        32037.00
  30 | M   |    2 | hanwha      | LA02768003 |          110981 |   30000000 |        36993.67
  30 | M   |    3 | lotte       | LA0772E002 |          118594 |   30000000 |        39531.33
  40 | F   |    1 | meritz      | 6ADYW      |          112513 |   30000000 |        37504.33
  40 | F   |    2 | hanwha      | LA02768003 |          124159 |   30000000 |        41386.33
  40 | F   |    3 | lotte       | LA0762E002 |          131175 |   30000000 |        43725.00
  40 | M   |    1 | meritz      | 6ADYW      |          125987 |   30000000 |        41995.67
  40 | M   |    2 | hanwha      | LA02768003 |          149253 |   30000000 |        49751.00
  40 | M   |    3 | lotte       | LA0772E002 |          159325 |   30000000 |        53108.33
  50 | F   |    1 | meritz      | 6ADYW      |          138095 |   30000000 |        46031.67
  50 | F   |    2 | hanwha      | LA02768003 |          153271 |   30000000 |        51090.33
  50 | F   |    3 | lotte       | LA0762E002 |          155056 |   30000000 |        51685.33
  50 | M   |    1 | meritz      | 6ADYW      |          172300 |   30000000 |        57433.33
  50 | M   |    2 | hanwha      | LA02768003 |          205683 |   30000000 |        68561.00
  50 | M   |    3 | lotte       | LA0772E002 |          217702 |   30000000 |        72567.33
(18 rows)
```

### Formula Verification

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT age, sex, rank, insurer_key,
       premium_monthly, cancer_amt, premium_per_10m,
       ROUND(premium_monthly / (cancer_amt / 10000000.0), 2) as calculated,
       ABS(premium_per_10m - (premium_monthly / (cancer_amt / 10000000.0))) as diff
FROM q14_premium_ranking_v1
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
ORDER BY age, sex, rank;"
```

### Formula Check Output

```
 age | sex | rank | insurer_key | premium_monthly | cancer_amt | premium_per_10m | calculated |        diff
-----+-----+------+-------------+-----------------+------------+-----------------+------------+--------------------
  30 | F   |    1 | meritz      |           87373 |   30000000 |        29124.33 |   29124.33 | 0.0033333333333333
  30 | F   |    2 | hanwha      |           95704 |   30000000 |        31901.33 |   31901.33 | 0.0033333333333333
  30 | F   |    3 | lotte       |          101258 |   30000000 |        33752.67 |   33752.67 | 0.0033333333333333
  30 | M   |    1 | meritz      |           96111 |   30000000 |        32037.00 |   32037.00 | 0.0000000000000000
  30 | M   |    2 | hanwha      |          110981 |   30000000 |        36993.67 |   36993.67 | 0.0033333333333333
  30 | M   |    3 | lotte       |          118594 |   30000000 |        39531.33 |   39531.33 | 0.0033333333333333
  40 | F   |    1 | meritz      |          112513 |   30000000 |        37504.33 |   37504.33 | 0.0033333333333333
  40 | F   |    2 | hanwha      |          124159 |   30000000 |        41386.33 |   41386.33 | 0.0033333333333333
  40 | F   |    3 | lotte       |          131175 |   30000000 |        43725.00 |   43725.00 | 0.0000000000000000
  40 | M   |    1 | meritz      |          125987 |   30000000 |        41995.67 |   41995.67 | 0.0033333333333333
  40 | M   |    2 | hanwha      |          149253 |   30000000 |        49751.00 |   49751.00 | 0.0000000000000000
  40 | M   |    3 | lotte       |          159325 |   30000000 |        53108.33 |   53108.33 | 0.0033333333333333
  50 | F   |    1 | meritz      |          138095 |   30000000 |        46031.67 |   46031.67 | 0.0033333333333333
  50 | F   |    2 | hanwha      |          153271 |   30000000 |        51090.33 |   51090.33 | 0.0033333333333333
  50 | F   |    3 | lotte       |          155056 |   30000000 |        51685.33 |   51685.33 | 0.0033333333333333
  50 | M   |    1 | meritz      |          172300 |   30000000 |        57433.33 |   57433.33 | 0.0033333333333333
  50 | M   |    2 | hanwha      |          205683 |   30000000 |        68561.00 |   68561.00 | 0.0000000000000000
  50 | M   |    3 | lotte       |          217702 |   30000000 |        72567.33 |   72567.33 | 0.0033333333333333
(18 rows)
```

**Formula**: `premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)`

**Verification Status**: ✅ PASS
- Maximum difference: 0.0033 (well below 0.01 threshold)
- All 18 rows verified

### Segment Breakdown

```
Segment   | Rank 1 Insurer | Rank 2 Insurer | Rank 3 Insurer
----------|----------------|----------------|----------------
30F       | meritz         | hanwha         | lotte
30M       | meritz         | hanwha         | lotte
40F       | meritz         | hanwha         | lotte
40M       | meritz         | hanwha         | lotte
50F       | meritz         | hanwha         | lotte
50M       | meritz         | hanwha         | lotte
```

---

## Q12: Samsung vs Meritz Premium Comparison

### Query

```bash
export PGPASSWORD=inca_secure_prod_2025_db_key && psql -h 127.0.0.1 -p 5432 -U inca_admin -d inca_rag_scope -c "
SELECT insurer_key, product_id, age, sex, premium_monthly_total
FROM product_premium_quote_v2
WHERE as_of_date = '2025-11-26'
  AND plan_variant = 'NO_REFUND'
  AND insurer_key IN ('samsung', 'meritz')
ORDER BY insurer_key, age, sex;"
```

### Output

```
 insurer_key | product_id | age | sex | premium_monthly_total
-------------+------------+-----+-----+-----------------------
 meritz      | 6ADYW      |  30 | F   |                 87373
 meritz      | 6ADYW      |  30 | M   |                 96111
 meritz      | 6ADYW      |  40 | F   |                112513
 meritz      | 6ADYW      |  40 | M   |                125987
 meritz      | 6ADYW      |  50 | F   |                138095
 meritz      | 6ADYW      |  50 | M   |                172300
 samsung     | ZPB275100  |  30 | F   |                106756
 samsung     | ZPB275100  |  30 | M   |                132685
 samsung     | ZPB275100  |  40 | F   |                137015
 samsung     | ZPB275100  |  40 | M   |                177383
 samsung     | ZPB275100  |  50 | F   |                172073
 samsung     | ZPB275100  |  50 | M   |                244969
(12 rows)
```

### Comparison Summary

```
Age/Sex | Meritz Premium | Samsung Premium | Difference | Meritz Lower By
--------|----------------|-----------------|------------|----------------
30F     | 87,373원       | 106,756원       | 19,383원   | 18.2%
30M     | 96,111원       | 132,685원       | 36,574원   | 27.6%
40F     | 112,513원      | 137,015원       | 24,502원   | 17.9%
40M     | 125,987원      | 177,383원       | 51,396원   | 29.0%
50F     | 138,095원      | 172,073원       | 33,978원   | 19.7%
50M     | 172,300원      | 244,969원       | 72,669원   | 29.7%
```

**Result**: Meritz is consistently cheaper than Samsung across all 6 segments (30/40/50 × M/F) by 17.9% to 29.7%.

---

## Summary

### Row Count Verification

| Query | Expected | Actual | Status |
|-------|----------|--------|--------|
| Q14 (보험료 Top4) | 24 | 24 | ✅ PASS |
| Q1 (가성비 Top3) | 18 | 18 | ✅ PASS |
| Q12 (Samsung vs Meritz) | 12 | 12 | ✅ PASS |

### Segment Coverage

| Age | Sex | Q14 Rows | Q1 Rows |
|-----|-----|----------|---------|
| 30  | F   | 4        | 3       |
| 30  | M   | 4        | 3       |
| 40  | F   | 4        | 3       |
| 40  | M   | 4        | 3       |
| 50  | F   | 4        | 3       |
| 50  | M   | 4        | 3       |
| **Total** | | **24** | **18** |

### Top Insurers

**Q14 (보험료 Top4)**:
- Rank 1: meritz (6/6 segments = 100%)
- Rank 2: hanwha (6/6 segments = 100%)
- Rank 3: lotte (6/6 segments = 100%)
- Rank 4: samsung (4/6 segments), hyundai (1/6), db (1/6)

**Q1 (가성비 Top3)**:
- Rank 1: meritz (6/6 segments = 100%)
- Rank 2: hanwha (6/6 segments = 100%)
- Rank 3: lotte (6/6 segments = 100%)

### Formula Integrity

**Q1 Formula Check**:
- Formula: `premium_per_10m = premium_monthly / (cancer_amt / 10_000_000)`
- Rows verified: 18/18
- Maximum difference: 0.0033
- Threshold: 0.01
- Status: ✅ PASS

### Database Details

- **Host**: 127.0.0.1
- **Port**: 5432
- **Database**: inca_rag_scope
- **User**: inca_admin
- **Container**: inca_rag_scope_db
- **Image**: pgvector/pgvector:pg16
- **PostgreSQL Version**: 16.11 (Debian)
- **Architecture**: aarch64-unknown-linux-gnu
- **Client IP**: 172.20.0.1

---

**Document Status**: ✅ COMPLETE
**Evidence Type**: RAW DB OUTPUT
**No Interpretation**: All outputs are direct psql results
**No Redesign**: Queries executed as specified
**No Fallback**: All data from production database
