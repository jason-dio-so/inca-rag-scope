# STEP NEXT-DB-2B: Metadata Seed Report

**Date**: 2025-12-28 (Asia/Seoul)
**Database**: inca_rag_scope
**Type**: Metadata seed only (5 tables)
**Status**: ✅ SUCCESS

---

## 1. Execution Summary

| Item | Value |
|------|-------|
| Execution Date | 2025-12-28 |
| DB Container | inca_rag_scope_db (healthy) |
| DB Name | inca_rag_scope |
| DB User | inca_admin |
| Seed File | docker/seed/STEP_NEXT_DB_2B_SEED_METADATA.sql |
| Source | data/metadata/products.yml (baseline locked) |

---

## 2. Execution Command

```bash
docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope < docker/seed/STEP_NEXT_DB_2B_SEED_METADATA.sql
```

**Result**: Success (no errors)
- INSERT 0 8 (insurers)
- INSERT 0 0 (doc_structure_profile - already exists)
- INSERT 0 8 (products)
- INSERT 0 4 (product_variants)
- INSERT 0 38 (documents)

---

## 3. Row Count Results

| Table Name | Row Count | Status |
|-----------|-----------|--------|
| **Metadata Tables (seeded)** | | |
| insurer | 8 | ✅ |
| product | 8 | ✅ |
| product_variant | 4 | ✅ |
| document | 38 | ✅ |
| doc_structure_profile | 1 | ✅ |
| **Coverage/Evidence Tables (forbidden)** | | |
| coverage_canonical | 0 | ✅ Empty |
| coverage_instance | 0 | ✅ Empty |
| evidence_ref | 0 | ✅ Empty |
| amount_fact | 0 | ✅ Empty |

**Verification Query**:
```sql
select 'insurer' as table_name, count(*) from insurer
union all select 'product', count(*) from product
union all select 'product_variant', count(*) from product_variant
union all select 'document', count(*) from document
union all select 'doc_structure_profile', count(*) from doc_structure_profile
union all select 'coverage_canonical', count(*) from coverage_canonical
union all select 'coverage_instance', count(*) from coverage_instance
union all select 'evidence_ref', count(*) from evidence_ref
union all select 'amount_fact', count(*) from amount_fact;
```

---

## 4. LOTTE/DB Special Case Verification

### 4.1 LOTTE Gender Variants

**Query**:
```sql
select d.doc_type, count(*) as doc_count
from document d
join product p on d.product_id = p.product_id
where p.product_code = 'lotte_health_v1'
group by d.doc_type
order by d.doc_type;
```

**Result**:
| doc_type | doc_count |
|----------|-----------|
| 약관 | 2 |
| 가입설계서 | 2 |
| 사업방법서 | 2 |
| 상품요약서 | 2 |

✅ **LOTTE**: All 4 document types have 2 versions (male/female)

### 4.2 DB Age Variants

**Query**:
```sql
select d.doc_type, count(*) as doc_count
from document d
join product p on d.product_id = p.product_id
where p.product_code = 'db_health_v1'
group by d.doc_type
order by d.doc_type;
```

**Result**:
| doc_type | doc_count |
|----------|-----------|
| 약관 | 1 |
| 가입설계서 | 2 |
| 사업방법서 | 1 |
| 상품요약서 | 1 |

✅ **DB**: Only 가입설계서 has 2 versions (40세이하/41세이상), others have 1 version

### 4.3 Variants Table

**Query**:
```sql
select pv.variant_key, pv.variant_display_name, p.product_name
from product_variant pv
join product p on pv.product_id = p.product_id
order by p.product_name, pv.variant_key;
```

**Result**:
| variant_key | variant_display_name | product_name |
|-------------|---------------------|--------------|
| LOTTE_FEMALE | 여 | 롯데손해보험 건강보험 |
| LOTTE_MALE | 남 | 롯데손해보험 건강보험 |
| DB_AGE_O40 | 41세이상 | DB손해보험 건강보험 |
| DB_AGE_U40 | 40세이하 | DB손해보험 건강보험 |

✅ **Variants**: 4 total (LOTTE 2 gender + DB 2 age)

---

## 5. Data Integrity Verification

### 5.1 Insurers (8)

| insurer_id | insurer_name_kr | insurer_type |
|------------|-----------------|--------------|
| md5('insurer:samsung')::uuid | 삼성생명 | 생명 |
| md5('insurer:hyundai')::uuid | 현대해상 | 손해 |
| md5('insurer:lotte')::uuid | 롯데손해보험 | 손해 |
| md5('insurer:db')::uuid | DB손해보험 | 손해 |
| md5('insurer:kb')::uuid | KB손해보험 | 손해 |
| md5('insurer:meritz')::uuid | 메리츠화재 | 손해 |
| md5('insurer:hanwha')::uuid | 한화생명 | 생명 |
| md5('insurer:heungkuk')::uuid | 흥국생명 | 생명 |

### 5.2 Products (8)

All 8 products created (1 per insurer):
- samsung_health_v1
- hyundai_health_v1
- lotte_health_v1
- db_health_v1
- kb_health_v1
- meritz_health_v1
- hanwha_health_v1
- heungkuk_health_v1

### 5.3 Documents (38)

**Breakdown**:
- Samsung: 5 docs (4 standard + 1 extra 상품요약서)
- Hyundai: 4 docs
- KB: 4 docs
- Meritz: 4 docs
- Hanwha: 4 docs
- Heungkuk: 4 docs
- **LOTTE**: 8 docs (4 types × 2 gender variants)
- **DB**: 5 docs (3 no-variant + 2 가입설계서 age variants)

**Total**: 38 documents

---

## 6. UUID Generation Strategy

**Method**: MD5-based deterministic UUIDs

```sql
-- Example: Insurer UUID
md5('insurer:samsung')::uuid
-- Example: Product UUID
md5('product:samsung_health_v1')::uuid
-- Example: Variant UUID
md5('variant:LOTTE_MALE')::uuid
-- Example: Document UUID
md5('document:samsung_policy_v1')::uuid
```

**Benefits**:
- ✅ Deterministic (same key → same UUID every time)
- ✅ Idempotent (can re-run seed without conflicts)
- ✅ No extension dependencies (uses built-in md5 function)
- ✅ Human-traceable (key embedded in generation logic)

---

## 7. Forbidden Tables (0 rows)

**Verification Query**:
```sql
select count(*) from coverage_canonical;  -- 0
select count(*) from coverage_instance;   -- 0
select count(*) from evidence_ref;        -- 0
select count(*) from amount_fact;         -- 0
```

**Result**: ✅ All forbidden tables remain at 0 rows

These tables will be populated in STEP NEXT-DB-2C (STEP9 Loader Implementation/Run).

---

## 8. Key Design Decisions

### 8.1 Document-Variant Relationship

**Current Schema**: `document` table does NOT have a `variant_id` FK column.
**Reason**: Variants are applied at the `coverage_instance` level, not document level.

**LOTTE/DB Approach**:
- Documents are linked to `product_id` only
- Variant differentiation is achieved by:
  - LOTTE: file_path includes (남)/(여) markers
  - DB: file_path includes (40세이하)/(41세이상) markers
- When loading `coverage_instance`, the loader will:
  1. Read file_path to determine which variant applies
  2. Link coverage_instance to the correct `variant_id`

**Why This Works**:
- ✅ Avoids schema changes
- ✅ Maintains data-driven approach (file paths in products.yml)
- ✅ Defers variant resolution to coverage_instance loading phase

### 8.2 doc_structure_profile Placeholder

**Current**: 1 default/unknown profile created
**Reason**: Real document structure profiles will be defined in STEP9 profiling phase
**Future**: KB/Meritz/LOTTE/DB will each get their own profile based on actual document analysis

---

## 9. Compliance Checklist

| Item | Status | Notes |
|------|--------|-------|
| Metadata 5 tables seeded | ✅ | insurer, product, product_variant, document, doc_structure_profile |
| LOTTE variants (남/여) | ✅ | 2 variants + 8 documents |
| DB variants (age) | ✅ | 2 variants + 5 documents (3 no-variant + 2 age-variant) |
| Coverage/evidence tables 0 rows | ✅ | All forbidden tables empty |
| SQL + report created | ✅ | 2 files |
| No data inference/guessing | ✅ | All data from products.yml |
| No file-based variant logic | ✅ | Variant linkage deferred to coverage_instance phase |

---

## 10. Next Steps

**BLOCKED**: STEP NEXT-DB-2C (STEP9 Loader Implementation/Run)

**Requirements for STEP NEXT-DB-2C**:
- ✅ Metadata tables seeded (this step)
- ⏳ coverage_canonical loader (from 담보명mapping자료.xlsx)
- ⏳ coverage_instance loader (from scope CSVs)
- ⏳ evidence_ref loader (from evidence_pack JSONLs)
- ⏳ amount_fact loader (from coverage_cards JSONLs)

**Current Status**: Metadata baseline established. Ready for STEP9 loaders.

---

## CONCLUSION

✅ **STEP NEXT-DB-2B COMPLETED**

- **Metadata seeded**: 8 insurers, 8 products, 4 variants, 38 documents, 1 profile
- **LOTTE/DB variants**: Verified through data (no code logic)
- **Forbidden tables**: Remain at 0 rows (as required)
- **Next**: STEP NEXT-DB-2C (STEP9 Loader Implementation) — awaiting user approval

**No coverage/evidence/amount data loaded. Metadata only.**
