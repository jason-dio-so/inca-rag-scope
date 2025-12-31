# STEP NEXT-41S: Loader Binding Trace (Phase A-3)

**Date**: 2025-12-31
**Loader**: `apps/loader/step9_loader.py`
**Purpose**: Map SSOT fields → DB columns (evidence-only trace, no interpretation)

---

## Loader Sources (READ)

| Method | Source File | SSOT Field | Notes |
|--------|-------------|------------|-------|
| `load_coverage_canonical()` | `data/sources/mapping/담보명mapping자료.xlsx` | N/A | Excel, not JSONL |
| `load_coverage_instance()` | `data/scope/{insurer}_scope_mapped.csv` | N/A | CSV, not JSONL |
| `load_evidence_ref()` | `data/evidence_pack/{insurer}_evidence_pack.jsonl` | `evidences[]` | **DEPRECATED** (per CLAUDE.md) |
| `load_amount_fact()` | `data/compare/{insurer}_coverage_cards.jsonl` | `amount` | **CRITICAL: SSOT has NO amount** |

---

## coverage_canonical Binding

**Source**: Excel (`담보명mapping자료.xlsx`)
**Loader Method**: `load_coverage_canonical()` (line 202-279)

| DB Column | Excel Column (idx) | Loader Code (line) | Transform |
|-----------|-------------------|-------------------|-----------|
| `coverage_code` | `cre_cvr_cd` (2) | 233 | `str(row[2]).strip()` |
| `coverage_name_canonical` | `신정원코드명` (3) | 234 | `str(row[3]).strip()` |
| `coverage_category` | N/A | 269 | `None` (not from Excel) |
| `payment_event` | N/A | 270 | `None` (not from Excel) |
| `created_at` | N/A | 271 | `datetime.now()` |
| `updated_at` | N/A | 259 | `CURRENT_TIMESTAMP` (on conflict) |

**UPSERT SQL** (line 253-260):
```sql
INSERT INTO coverage_canonical
(coverage_code, coverage_name_canonical, coverage_category, payment_event, created_at)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (coverage_code) DO UPDATE SET
    coverage_name_canonical = EXCLUDED.coverage_name_canonical,
    updated_at = CURRENT_TIMESTAMP
```

---

## coverage_instance Binding

**Source**: CSV (`data/scope/{insurer}_scope_mapped.csv`)
**Loader Method**: `load_coverage_instance()` (line 281-395)

| DB Column | CSV Field | Loader Code (line) | Transform |
|-----------|-----------|-------------------|-----------|
| `instance_id` | N/A | 191 | `gen_random_uuid()` (DB default) |
| `insurer_id` | N/A | 293 | Lookup from `insurer_map[insurer_key]` |
| `product_id` | N/A | 349-350 | Derived `{insurer_key}_health_v1` |
| `variant_id` | N/A | 358 | `None` (no variant in CSV) |
| `coverage_code` | `coverage_code` | 324 | `.strip()`, convert empty→None (332) |
| `coverage_name_raw` | `coverage_name_raw` | 325 | `.strip()` |
| `source_page` | `source_page` | 328 | `.strip()`, convert to int or None (362-367) |
| `mapping_status` | `mapping_status` | 326 | `.strip()`, validate ∈ {matched, unmatched} (339) |
| `match_type` | `match_type` | 327 | `.strip()`, convert empty→None (384) |
| `created_at` | N/A | 386 | `datetime.now()` |
| **`instance_key`** | N/A | 370-372 | **Generated** via `_build_instance_key()` |
| **`updated_at`** | N/A | 317 | `CURRENT_TIMESTAMP` (on conflict) |

**UPSERT SQL** (line 306-318):
```sql
INSERT INTO coverage_instance
(insurer_id, product_id, variant_id, coverage_code,
 coverage_name_raw, source_page, mapping_status, match_type, instance_key, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (instance_key)
DO UPDATE SET
    coverage_name_raw = EXCLUDED.coverage_name_raw,
    source_page = EXCLUDED.source_page,
    mapping_status = EXCLUDED.mapping_status,
    match_type = EXCLUDED.match_type,
    updated_at = CURRENT_TIMESTAMP
```

**instance_key Generation** (line 143-157):
```python
def _build_instance_key(self, insurer_key, product_key, variant_key, coverage_code, coverage_name_raw):
    variant_part = variant_key if variant_key else "_"
    code_part = coverage_code if coverage_code else "_"
    name_part = self._normalize_text(coverage_name_raw)  # trim + collapse spaces
    return f"{insurer_key}|{product_key}|{variant_part}|{code_part}|{name_part}"
```

---

## evidence_ref Binding

**Source**: JSONL (`data/evidence_pack/{insurer}_evidence_pack.jsonl`)
**Loader Method**: `load_evidence_ref()` (line 397-517)

**CRITICAL**: SSOT is `coverage_cards.jsonl`, but loader reads `evidence_pack.jsonl` (DEPRECATED per CLAUDE.md).

| DB Column | JSONL Field Path | Loader Code (line) | Transform |
|-----------|-----------------|-------------------|-----------|
| `evidence_id` | N/A | 230 | `gen_random_uuid()` (DB default) |
| `coverage_instance_id` | N/A | 438-455 | Lookup via `coverage_name_raw` match |
| `document_id` | `evidences[].file_path` | 477-491 | Normalize path, lookup `document_map` |
| `doc_type` | `evidences[].doc_type` | 461 | Direct read `.get('doc_type')` |
| `page` | `evidences[].page` | 462 | Direct read `.get('page')` |
| `snippet` | `evidences[].snippet` | 463 | Direct read `.get('snippet')`, truncate to 500 (507) |
| `match_keyword` | `evidences[].match_keyword` | 464 | Direct read `.get('match_keyword')` |
| `rank` | N/A | 494 | **Generated**: `idx + 1` (1-3) |
| `created_at` | N/A | 511 | `datetime.now()` |
| **`evidence_key`** | N/A | 498 | **Generated** via format string |
| **`updated_at`** | N/A | 425 | `CURRENT_TIMESTAMP` (on conflict) |

**UPSERT SQL** (line 416-426):
```sql
INSERT INTO evidence_ref
(coverage_instance_id, document_id, doc_type, page,
 snippet, match_keyword, rank, evidence_key, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (evidence_key)
DO UPDATE SET
    snippet = EXCLUDED.snippet,
    match_keyword = EXCLUDED.match_keyword,
    updated_at = CURRENT_TIMESTAMP
```

**evidence_key Generation** (line 498):
```python
evidence_key = f"{instance_key}|{file_path_normalized}|{doc_type}|{page}|{rank}"
```

**Path Normalization** (line 479-485):
```python
# Convert absolute path to relative
# /Users/cheollee/inca-rag-scope/data/... → data/...
if 'data' in parts:
    data_idx = parts.index('data')
    file_path_normalized = str(Path(*parts[data_idx:]))
```

---

## amount_fact Binding

**Source**: JSONL (`data/compare/{insurer}_coverage_cards.jsonl`)
**Loader Method**: `load_amount_fact()` (line 519-656)

**CRITICAL FINDING**: Loader expects `card.get('amount')` field (line 569), but **SSOT has NO amount field**.

| DB Column | JSONL Field Path | Loader Code (line) | Transform |
|-----------|-----------------|-------------------|-----------|
| `amount_id` | N/A | 267 | `gen_random_uuid()` (DB default) |
| `coverage_instance_id` | N/A | 550-566 | Lookup via `coverage_name_raw` match |
| `evidence_id` | `amount.evidence_ref` | 589-612 | If CONFIRMED, lookup or create |
| `status` | `amount.status` | 580 | Default `'UNCONFIRMED'` if missing |
| `value_text` | `amount.value_text` | 581 | Direct read or `None` |
| `source_doc_type` | `amount.source_doc_type` | 582 | Direct read or `None` |
| `source_priority` | `amount.source_priority` | 583 | Direct read or `None` |
| `notes` | N/A | 646 | `json.dumps([])` (always empty) |
| `created_at` | N/A | 647 | `datetime.now()` |
| **`updated_at`** | N/A | 637 | `CURRENT_TIMESTAMP` (on conflict) |

**UPSERT SQL** (line 625-638):
```sql
INSERT INTO amount_fact
(coverage_instance_id, evidence_id, status, value_text,
 source_doc_type, source_priority, notes, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (coverage_instance_id) DO UPDATE SET
    evidence_id = EXCLUDED.evidence_id,
    status = EXCLUDED.status,
    value_text = EXCLUDED.value_text,
    source_doc_type = EXCLUDED.source_doc_type,
    source_priority = EXCLUDED.source_priority,
    updated_at = CURRENT_TIMESTAMP
```

**Fallback Behavior** (line 571-577):
```python
if not amount_data:
    # Amount field missing → write UNCONFIRMED with NULL values
    status = 'UNCONFIRMED'
    value_text = None
    source_doc_type = None
    source_priority = None
    evidence_id = None
```

---

## CRITICAL MISMATCHES

### 1. evidence_ref Source Mismatch

**Loader Reads**: `data/evidence_pack/{insurer}_evidence_pack.jsonl` (line 409)
**SSOT**: `data/compare/{insurer}_coverage_cards.jsonl` (`evidences[]` field)
**Status**: `evidence_pack/` marked DEPRECATED in CLAUDE.md (line 41)

**Implication**:
- Loader is reading **DEPRECATED source** instead of SSOT.
- If `evidence_pack.jsonl` is stale/missing, DB will be empty or outdated.

---

### 2. amount Field Missing in SSOT

**Loader Expects**: `card.get('amount')` (line 569)
**SSOT Has**: NO `amount` field (confirmed in Phase A-2)
**Fallback**: Loader writes `UNCONFIRMED` with NULL values (line 571-577)

**Implication**:
- If loader runs on current SSOT, all amount_fact rows will be `UNCONFIRMED`.
- DB has 285 amount_fact rows → came from **different source** (not current SSOT).

---

### 3. rank Field Generated (not in SSOT)

**SSOT evidences[]**: NO `rank` field
**Loader**: Generates `rank = idx + 1` (line 494)

**Implication**:
- Loader correctly generates rank from array index.
- No mismatch, but confirms rank is **loader-generated**, not SSOT data.

---

### 4. Path Format Mismatch

**SSOT file_path**: Absolute paths (`/Users/cheollee/inca-rag-scope/data/evidence_text/...`)
**DB file_path**: Relative paths (`data/pdf/...`)
**Loader**: Normalizes absolute → relative (line 479-485)

**Implication**:
- Loader tries to normalize, but may fail if `document` table has different path format.
- Lookup failures cause `skipped` evidence (line 488-491).

---

## Loader Execution Command

```bash
python -m apps.loader.step9_loader \
  --db-url "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope" \
  --mode reset_then_load
```

**Modes**:
- `upsert` (default): Idempotent upsert, no truncate
- `reset_then_load`: Truncate fact tables, then load (line 824-828)

---

**Phase A-3 Complete**: Loader binding traced with 4 critical mismatches.
