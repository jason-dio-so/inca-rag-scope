# STEP NEXT-42R: DB Schema Intent Model (AS-IS)

## Purpose
Define **what the DB schema was designed to store**, independent of current data state.

**NOT**: "What data is currently in the DB"
**YES**: "What was this table meant to represent"

---

## Table Hierarchy (Relational Model)

```
insurer (보험사)
  └─ product (상품)
       ├─ product_variant (상품 변형: 남/녀 구분 등)
       ├─ document (문서: PDF 메타데이터)
       └─ coverage_instance (담보 인스턴스)
            ├─ evidence_ref (근거 자료 참조)
            └─ amount_fact (보장 금액 사실)

coverage_canonical (담보 표준 코드 사전)
```

---

## 1. Metadata Tables (Static Entities)

### `insurer` (보험사)
**Intent**: 보험사 마스터 테이블

| Field | Type | Intent |
|-------|------|--------|
| `insurer_id` | UUID PK | Unique insurer identifier |
| `insurer_name_kr` | TEXT NOT NULL | Korean name (e.g., "삼성생명") |
| `insurer_type` | TEXT | "생명" or "손해" |

**Design Intent**: Static reference table, manually populated

---

### `product` (상품)
**Intent**: 보험 상품 마스터 (e.g., "무배당 삼성화재 실손의료비보험")

| Field | Type | Intent |
|-------|------|--------|
| `product_id` | UUID PK | Unique product identifier |
| `insurer_id` | UUID FK | Parent insurer |
| `product_name` | TEXT NOT NULL | Product name |
| `product_code` | TEXT | Optional insurer-specific code |
| `doc_structure_profile_id` | UUID FK | Doc structure variant (KB/Meritz variants) |

**Design Intent**: One product per insurer's insurance offering

---

### `product_variant` (상품 변형)
**Intent**: Gender/age-specific variants (e.g., LOTTE Male/Female)

| Field | Type | Intent |
|-------|------|--------|
| `variant_id` | UUID PK | Unique variant identifier |
| `product_id` | UUID FK | Parent product |
| `variant_key` | TEXT | Variant key (e.g., "MALE", "FEMALE") |
| `variant_label` | TEXT | Display name |

**Design Intent**: Handle products with gender/age splits in coverage

---

### `document` (문서)
**Intent**: PDF document metadata (약관/사업방법서/상품요약서/가입설계서)

| Field | Type | Intent |
|-------|------|--------|
| `document_id` | UUID PK | Unique document identifier |
| `insurer_id` | UUID FK | Parent insurer |
| `product_id` | UUID FK | Parent product |
| `doc_type` | TEXT | "약관", "사업방법서", "상품요약서", "가입설계서" |
| `file_path` | TEXT | Relative path to PDF |
| `page_count` | INT | Total pages |

**Design Intent**: Track which PDFs exist, link evidence to specific files

---

## 2. Coverage Canonical (Standard Dictionary)

### `coverage_canonical` (담보 표준 코드)
**Intent**: Canonical coverage code dictionary (mapping Excel source of truth)

| Field | Type | Intent |
|-------|------|--------|
| `coverage_code` | TEXT PK | Canonical code (e.g., "A4200_1") |
| `coverage_name_canonical` | TEXT NOT NULL | Canonical name (e.g., "암 진단비(유사암 제외)") |
| `coverage_category` | TEXT | Category (e.g., "암", "심혈관") |
| `payment_event` | TEXT | Payment trigger (e.g., "암 진단 확정 시") |

**Design Intent**: Single source of truth for coverage codes (loaded from mapping Excel)

**Constraint**: `coverage_code` format: `^[A-Z]\d{4}(_\d+)?$`

---

## 3. Coverage Instance (Insurer-Specific Coverage)

### `coverage_instance` (담보 인스턴스)
**Intent**: Represent ONE coverage as it appears in ONE insurer's product

| Field | Type | Nullable | Intent |
|-------|------|----------|--------|
| `instance_id` | UUID PK | NO | Unique instance |
| `insurer_id` | UUID FK | NO | Which insurer |
| `product_id` | UUID FK | NO | Which product |
| `variant_id` | UUID FK | **YES** | Which variant (NULL if no variants) |
| `coverage_code` | TEXT FK | **YES** | FK to canonical code (**NULL if unmatched**) |
| `coverage_name_raw` | TEXT | NO | Original coverage name from PDF |
| `source_page` | INT | YES | Page number in PDF |
| `mapping_status` | TEXT | NO | `"matched"` or `"unmatched"` |
| `match_type` | TEXT | YES | `"exact"`, `"normalized_alias"`, `"manual"` |
| `instance_key` | TEXT UNIQUE | YES | Natural key for dedup |

**Design Intent**:
- **One row = one coverage in one insurer's product**
- `coverage_code` NULL allowed for `mapping_status="unmatched"`
- `coverage_code` MUST be non-NULL for `mapping_status="matched"` (enforced by loader, not DB constraint)
- Unique constraint: `(product_id, variant_id, coverage_code)` ensures no duplicate coverages per product

**Instance Key Format**: `{insurer_key}|{product_key}|{variant_key_or_}|{coverage_code_or_}|{coverage_name_raw}`

---

## 4. Evidence Ref (Evidence Search Results)

### `evidence_ref` (근거 자료 참조)
**Intent**: Store evidence snippets found in documents (약관/사업방법서/상품요약서)

| Field | Type | Nullable | Intent |
|-------|------|----------|--------|
| `evidence_id` | UUID PK | NO | Unique evidence |
| `coverage_instance_id` | UUID FK | NO | Parent coverage instance |
| `document_id` | UUID FK | NO | Source document |
| `doc_type` | TEXT | NO | "약관", "사업방법서", "상품요약서" |
| `page` | INT | NO | Page number (1-indexed) |
| `snippet` | TEXT | NO | Original text snippet (**NO summarization**) |
| `match_keyword` | TEXT | YES | Keyword used for search |
| `rank` | INT | YES | Evidence priority (1-3) within doc_type |
| `evidence_key` | TEXT UNIQUE | YES | Natural key for dedup |

**Design Intent**:
- **One row = one evidence snippet for one coverage**
- Max 3 evidences per doc_type (rank 1-3)
- `snippet` MUST be original text (NO LLM summarization)
- `doc_type` constraint: `{"약관", "사업방법서", "상품요약서", "가입설계서"}`
- `rank` constraint: 1-3

**Evidence Key Format**: `{instance_key}|{file_path}|{doc_type}|{page}|{rank}`

**CRITICAL**: Evidence key does NOT include `snippet` or `match_keyword` (allows snippet updates without key change)

---

## 5. Amount Fact (보장 금액 사실)

### `amount_fact` (보장 금액 사실)
**Intent**: Store CONFIRMED amount facts with evidence (가입설계서 or 약관 기반)

| Field | Type | Nullable | Intent |
|-------|------|----------|--------|
| `amount_id` | UUID PK | NO | Unique amount fact |
| `coverage_instance_id` | UUID FK | NO | Parent coverage instance |
| `evidence_id` | UUID FK | **YES** | **MANDATORY if status=CONFIRMED** |
| `status` | TEXT | NO | `"CONFIRMED"`, `"UNCONFIRMED"`, `"CONFLICT"` |
| `value_text` | TEXT | **YES** | **EXACT amount text** (e.g., "3000만원") |
| `source_doc_type` | TEXT | YES | "가입설계서", "약관", "사업방법서", "상품요약서" |
| `source_priority` | TEXT | YES | `"PRIMARY"` (가입설계서) or `"SECONDARY"` (약관 etc.) |
| `notes` | JSONB | YES | **Fixed keywords only** (NO prose) |

**Design Intent**:
- **One row per coverage instance** (unique constraint: `coverage_instance_id`)
- `status="CONFIRMED"` → `evidence_id` MUST be non-NULL, `value_text` MUST be non-NULL
- `status="UNCONFIRMED"` → `value_text` MUST be NULL
- `status="CONFLICT"` → Multiple conflicting amounts found
- `value_text` = **EXACT text from document**, NO calculation
- `source_priority="PRIMARY"` → MUST have `source_doc_type="가입설계서"`
- `source_priority="SECONDARY"` → MUST have `source_doc_type` in {"약관", "사업방법서", "상품요약서"}

**DB Constraints**:
- `confirmed_has_evidence`: CONFIRMED → evidence_id NOT NULL AND value_text NOT NULL
- `confirmed_has_value`: CONFIRMED → value_text NOT NULL | UNCONFIRMED → value_text NULL
- `primary_from_proposal`: PRIMARY → source_doc_type="가입설계서"

---

## Summary: What Each Table Represents

| Table | Represents | Cardinality |
|-------|-----------|-------------|
| `insurer` | 보험사 마스터 | ~8 rows (삼성/한화/메리츠 etc.) |
| `product` | 보험 상품 | ~8+ rows (1 per insurer) |
| `product_variant` | 상품 변형 (남/녀) | 0-2 per product (optional) |
| `document` | PDF 메타데이터 | ~32 rows (8 insurers × 4 doc types) |
| `coverage_canonical` | 담보 표준 코드 사전 | ~200 rows (mapping Excel) |
| `coverage_instance` | 보험사별 담보 인스턴스 | ~300 rows (8 insurers × ~40 coverages) |
| `evidence_ref` | 근거 자료 스니펫 | ~900 rows (3 doc_types × 3 ranks × ~100 coverages) |
| `amount_fact` | 보장 금액 사실 | ~300 rows (1 per coverage instance, if confirmed) |

---

## Design Philosophy

1. **Metadata = Static**: `insurer`, `product`, `document` are reference tables
2. **Canonical = Single Source**: `coverage_canonical` loaded from mapping Excel
3. **Instance = Insurer Reality**: `coverage_instance` represents insurer's actual coverage
4. **Evidence = Search Results**: `evidence_ref` stores original snippets (NO summarization)
5. **Amount = Fact**: `amount_fact` stores CONFIRMED amounts with evidence (NO inference)

---

## Critical Intent Clarifications

### `coverage_instance.coverage_code` NULL Allowed
- **Intent**: Represent unmatched coverages from insurer documents
- `mapping_status="unmatched"` → `coverage_code=NULL` is VALID
- `mapping_status="matched"` → `coverage_code` MUST be non-NULL (loader enforces, not DB constraint)

### `amount_fact.evidence_id` NULL Allowed (BUT...)
- **Intent**: Evidence is MANDATORY for CONFIRMED amounts
- DB constraint: `status="CONFIRMED"` → `evidence_id` MUST be non-NULL
- DB constraint enforces this, but schema allows NULL for UNCONFIRMED/CONFLICT

### `amount_fact` One Row Per Coverage
- **Intent**: Store SINGLE fact per coverage (no duplicates)
- Unique constraint: `(coverage_instance_id)` ensures this

### Evidence Rank (1-3)
- **Intent**: Priority ranking within same doc_type
- Rank 1 = highest quality, Rank 3 = lowest quality
- Loader decides rank based on search quality/fallback status

---

## Next: Compare with Loader Role
See: `STEP_NEXT_42R_LOADER_ROLE_SPLIT.md`
