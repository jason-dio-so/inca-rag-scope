# CHECK 1: INSURER TABLE SNAPSHOT & SSOT CONSISTENCY

**Date**: 2026-01-17
**Check Type**: insurer 테이블 단일 진실 확인
**Status**: ✅ **PASS**

---

## Purpose

DB `insurer` 테이블이 고객 제공 SSOT (담보명mapping자료.xlsx)와 1:1로 일치하는지 검증.

---

## Query Executed

```sql
SELECT ins_cd, insurer_name_ko, insurer_name_en, created_at, updated_at
FROM insurer
ORDER BY ins_cd;
```

---

## Result: Current DB insurer Table

| ins_cd | insurer_name_ko | insurer_name_en | created_at | updated_at |
|--------|----------------|-----------------|------------|------------|
| N01 | 메리츠 | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| N02 | 한화 | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| **N03** | **롯데** | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| N05 | 흥국 | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| N08 | 삼성 | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| N09 | 현대 | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| N10 | KB | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |
| **N13** | **DB** | | 2026-01-15 06:38:50 | 2026-01-15 07:23:29 |

**Total Rows**: 8

---

## SSOT Excel Reference

**Source**: `data/derived/insurer_map_ssot.json` (generated from `data/sources/insurers/담보명mapping자료.xlsx`)

| ins_cd | insurer_name_ko (SSOT) | insurer_enum | premium_code |
|--------|----------------------|--------------|--------------|
| N01 | 메리츠 | MERITZ | meritz |
| N02 | 한화 | HANWHA | hanwha |
| **N03** | **롯데** | LOTTE | lotte |
| N05 | 흥국 | HEUNGKUK | heungkuk |
| N08 | 삼성 | SAMSUNG | samsung |
| N09 | 현대 | HYUNDAI | hyundai |
| N10 | KB | KB | kb |
| **N13** | **DB** | DB | db |

---

## Comparison: DB vs SSOT Excel

| ins_cd | DB insurer_name_ko | SSOT insurer_name_ko | Match? |
|--------|--------------------|---------------------|--------|
| N01 | 메리츠 | 메리츠 | ✅ |
| N02 | 한화 | 한화 | ✅ |
| **N03** | **롯데** | **롯데** | ✅ **CORRECTED** |
| N05 | 흥국 | 흥국 | ✅ |
| N08 | 삼성 | 삼성 | ✅ |
| N09 | 현대 | 현대 | ✅ |
| N10 | KB | KB | ✅ |
| **N13** | **DB** | **DB** | ✅ **CORRECTED** |

**Match Rate**: 8/8 (100%)

---

## Change History

### Before N03/N13 Swap (2026-01-17 earlier)

```
N03 → DB (WRONG)
N13 → 롯데 (WRONG)
```

### After N03/N13 Swap (2026-01-17 20:41 UTC)

```sql
BEGIN;
UPDATE insurer SET insurer_name_ko = 'TEMP' WHERE ins_cd = 'N03';
UPDATE insurer SET insurer_name_ko = 'DB' WHERE ins_cd = 'N13';
UPDATE insurer SET insurer_name_ko = '롯데' WHERE ins_cd = 'N03';
COMMIT;
```

**Result**:
```
N03 → 롯데 ✅ (matches SSOT)
N13 → DB ✅ (matches SSOT)
```

---

## Verification: Product Brand Consistency

To confirm N03/N13 swap correctness, cross-reference with actual product brands:

### N03 Products (Should be 롯데)

```sql
SELECT product_id, product_full_name
FROM product
WHERE ins_cd = 'N03' AND as_of_date = '2025-11-26';
```

**Sample**:
- LA0772E002: 무배당 **let:smile** 종합건강보험(더끌림 포맨)
- LA0762E002: 무배당 **let:smile** 종합건강보험(더끌림 포우먼)

**Brand**: "let:smile" → **롯데손해보험** ✅

### N13 Products (Should be DB)

```sql
SELECT product_id, product_full_name
FROM product
WHERE ins_cd = 'N13' AND as_of_date = '2025-11-26';
```

**Sample**:
- 30633: 무배당 **프로미라이프** 참좋은훼밀리더블플러스종합보험2508

**Brand**: "프로미라이프" → **DB손해보험** ✅

---

## Verdict

**✅ PASS**

- DB `insurer` table matches SSOT Excel 100% (8/8 insurers)
- N03/N13 swap successfully corrected previous mismatch
- Product brands (let:smile, 프로미라이프) confirm correct mapping

---

## Notes

1. **updated_at** timestamps show last modification was 2026-01-15 07:23:29, predating the N03/N13 swap
   - This indicates the swap query updated the table without updating the `updated_at` column
   - Consider adding `updated_at = CURRENT_TIMESTAMP` to future UPDATE queries

2. **insurer_name_en** column is empty for all rows
   - Not critical for current operations but may be needed for internationalization

3. **Change Tracking**
   - No audit log table exists for `insurer` table changes
   - Consider adding trigger/audit trail for future SSOT modifications

---

**CHECK 1 STATUS**: ✅ **PASS** — DB insurer table is consistent with SSOT Excel

---

**Next Check**: CHECK 2 - Product table consistency (N03/N13 sample verification)
