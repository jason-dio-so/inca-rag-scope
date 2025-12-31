# STEP NEXT-41S: DB Schema Snapshot (Phase A-1)

**Date**: 2025-12-31
**Container**: `inca_rag_scope_db` (pgvector/pgvector:pg16)
**Status**: Up 2 days (healthy)
**Database**: `inca_rag_scope`
**User**: `inca_admin`

---

## Table Inventory

| Table | Size | Row Count | Description |
|-------|------|-----------|-------------|
| coverage_canonical | 16 kB | 48 | Canonical coverage definitions |
| coverage_instance | 112 kB | 297 | Insurer-specific coverage instances |
| evidence_ref | 632 kB | 747 | Evidence references |
| amount_fact | 72 kB | 285 | Amount facts |
| insurer | 16 kB | - | Insurance company metadata |
| product | 16 kB | - | Insurance product metadata |
| product_variant | 16 kB | - | Product variants |
| doc_structure_profile | 16 kB | - | Document structure profiles |
| document | 48 kB | - | Document metadata |
| audit_runs | 16 kB | - | Frozen audit run metadata |

---

## Core Table Schemas (4 SSOT-linked tables)

### 1. coverage_canonical

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| coverage_code | text | NOT NULL | - | PK: Canonical coverage code (e.g., A4200_1) |
| coverage_name_canonical | text | NOT NULL | - | Canonical coverage name |
| coverage_category | text | NULL | - | Category (진단/수술/입원) |
| payment_event | text | NULL | - | Payment trigger event |
| created_at | timestamptz | NOT NULL | now() | Created timestamp |
| updated_at | timestamptz | NULL | - | Updated timestamp |

**Indexes**:
- PRIMARY KEY: `coverage_code`
- `idx_coverage_category` (btree)
- `idx_coverage_name_canonical` (btree)

**Constraints**:
- `coverage_code_format`: `coverage_code ~ '^[A-Z]\d{4}(_\d+)?$'`

---

### 2. coverage_instance

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| instance_id | uuid | NOT NULL | gen_random_uuid() | PK: Instance ID |
| insurer_id | uuid | NOT NULL | - | FK to insurer |
| product_id | uuid | NOT NULL | - | FK to product |
| variant_id | uuid | NULL | - | FK to product_variant |
| coverage_code | text | NULL | - | FK to coverage_canonical (NULL for unmatched) |
| coverage_name_raw | text | NOT NULL | - | Original coverage name |
| source_page | integer | NULL | - | Page number in 가입설계서 |
| mapping_status | text | NOT NULL | - | 'matched' or 'unmatched' |
| match_type | text | NULL | - | Matching method |
| created_at | timestamptz | NOT NULL | now() | Created timestamp |
| **instance_key** | **text** | **NULL** | - | **Natural key (GAMMA patch)** |
| **updated_at** | **timestamptz** | **NULL** | - | **Updated timestamp (GAMMA patch)** |

**Indexes**:
- PRIMARY KEY: `instance_id`
- UNIQUE: `instance_key` (idx_coverage_instance_key)
- UNIQUE: `(product_id, variant_id, coverage_code)`
- `idx_coverage_instance_coverage_code` (btree)
- `idx_coverage_instance_insurer` (btree)
- `idx_coverage_instance_mapping_status` (btree)
- `idx_coverage_instance_product` (btree)

**Constraints**:
- `mapping_status` IN ('matched', 'unmatched')

**GAMMA Patch Columns**:
- `instance_key`: Natural key for idempotent upsert
- `updated_at`: Modification timestamp

---

### 3. evidence_ref

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| evidence_id | uuid | NOT NULL | gen_random_uuid() | PK: Evidence ID |
| coverage_instance_id | uuid | NOT NULL | - | FK to coverage_instance |
| document_id | uuid | NOT NULL | - | FK to document |
| doc_type | text | NOT NULL | - | Document type |
| page | integer | NOT NULL | - | Page number (> 0) |
| snippet | text | NOT NULL | - | Original text snippet |
| match_keyword | text | NULL | - | Keyword used for matching |
| rank | integer | NULL | - | Evidence priority (1-3) |
| created_at | timestamptz | NOT NULL | now() | Created timestamp |
| **evidence_key** | **text** | **NULL** | - | **Natural key (GAMMA patch)** |
| **updated_at** | **timestamptz** | **NULL** | - | **Updated timestamp (GAMMA patch)** |

**Indexes**:
- PRIMARY KEY: `evidence_id`
- UNIQUE: `evidence_key` (idx_evidence_key)
- `idx_evidence_coverage_instance` (btree)
- `idx_evidence_doc_type` (btree)
- `idx_evidence_document` (btree)
- `idx_evidence_rank` (btree)

**Constraints**:
- `doc_type` IN ('약관', '사업방법서', '상품요약서', '가입설계서')
- `page > 0`
- `rank BETWEEN 1 AND 3`
- `length(snippet) > 0`

**GAMMA Patch Columns**:
- `evidence_key`: Natural key for idempotent upsert
- `updated_at`: Modification timestamp

---

### 4. amount_fact

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| amount_id | uuid | NOT NULL | gen_random_uuid() | PK: Amount ID |
| coverage_instance_id | uuid | NOT NULL | - | FK to coverage_instance |
| evidence_id | uuid | NULL | - | FK to evidence_ref (MANDATORY if CONFIRMED) |
| status | text | NOT NULL | - | CONFIRMED/UNCONFIRMED/CONFLICT |
| value_text | text | NULL | - | EXACT amount text |
| source_doc_type | text | NULL | - | Document type |
| source_priority | text | NULL | - | PRIMARY/SECONDARY |
| notes | jsonb | NULL | '[]'::jsonb | Fixed keywords only |
| created_at | timestamptz | NOT NULL | now() | Created timestamp |
| **updated_at** | **timestamptz** | **NULL** | - | **Updated timestamp (GAMMA patch)** |

**Indexes**:
- PRIMARY KEY: `amount_id`
- UNIQUE: `coverage_instance_id` (unique_amount_per_coverage)
- `idx_amount_coverage_instance` (btree)
- `idx_amount_priority` (btree)
- `idx_amount_status` (btree)

**Constraints**:
- `status` IN ('CONFIRMED', 'UNCONFIRMED', 'CONFLICT')
- `source_doc_type` IN ('가입설계서', '약관', '사업방법서', '상품요약서')
- `source_priority` IN ('PRIMARY', 'SECONDARY')
- `confirmed_has_evidence`: CONFIRMED requires non-NULL evidence_id and value_text
- `confirmed_has_value`: CONFIRMED requires non-NULL value_text
- `primary_from_proposal`: PRIMARY requires source_doc_type = '가입설계서'

**GAMMA Patch Columns**:
- `updated_at`: Modification timestamp

---

## Schema Provenance

**Base Schema**: `docker/schema/STEP_NEXT_DB_1_SCHEMA.sql`
**Applied Patches**:
1. `STEP_NEXT_DB_2C_GAMMA_PATCH.sql` (applied)
   - Added `instance_key` + unique index to `coverage_instance`
   - Added `evidence_key` + unique index to `evidence_ref`
   - Added `updated_at` to all 3 instance tables + `amount_fact`

**Schema State**: GAMMA-patched (idempotent upsert ready)

---

## Evidence Collection Method

```bash
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "\dt+"
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "\d+ coverage_canonical"
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "\d+ coverage_instance"
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "\d+ evidence_ref"
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "\d+ amount_fact"
docker exec inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "SELECT COUNT(*) FROM [table]"
```

---

**Phase A-1 Complete**: DB schema snapshot captured with GAMMA patch state confirmed.
