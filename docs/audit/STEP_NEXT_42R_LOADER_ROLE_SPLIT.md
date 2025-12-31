# STEP NEXT-42R: Loader Role Split (AS-IS)

## Purpose
Define what loader **receives from pipeline** vs. what loader **generates/transforms** itself.

Source: `apps/loader/step9_loader.py`

---

## Loader Philosophy (Constitutional)

From loader docstring (line 1-22):
```
Purpose:
    Load canonical truth + STEP 1-7 artifacts into 4 fact tables:
    - coverage_canonical (from Excel)
    - coverage_instance (from scope_mapped.csv)
    - evidence_ref (from coverage_cards.jsonl)  ← STEP NEXT-41S: Changed from evidence_pack
    - amount_fact (from coverage_cards.jsonl)

Rules:
    - NO LLM / NO inference / NO computation
    - Excel is the ONLY source for coverage_canonical
    - products.yml is the ONLY source for insurer/product/variant/document FK
    - Clear+reload for idempotency
    - LOTTE/DB variants are DATA, not logic
```

---

## Table 1: `coverage_canonical`

### Source
`data/sources/mapping/담보명mapping자료.xlsx` (Excel)

### Pipeline Contribution
**NONE** — Loader reads Excel directly

### Loader Operations
| Operation | Type | Description |
|-----------|------|-------------|
| Read Excel | INPUT | Load Excel file (columns: ins_cd, 보험사명, cre_cvr_cd, 신정원코드명, 담보명(가입설계서)) |
| Extract columns | EXTRACT | `coverage_code` = col[2], `coverage_name_canonical` = col[3] |
| Deduplicate | TRANSFORM | Keep first occurrence per `coverage_code` |
| UPSERT | WRITE | Insert or update `coverage_canonical` table |
| Generate timestamps | GENERATE | `created_at`, `updated_at` |

### Fields Mapping
| DB Field | Source | Loader Role |
|----------|--------|-------------|
| `coverage_code` | Excel col[2] (cre_cvr_cd) | Pass-through |
| `coverage_name_canonical` | Excel col[3] (신정원코드명) | Pass-through |
| `coverage_category` | - | **Loader sets NULL** |
| `payment_event` | - | **Loader sets NULL** |
| `created_at` | - | **Loader generates** |
| `updated_at` | - | **Loader generates** |

**CRITICAL**: `coverage_category` and `payment_event` are NOT in Excel → Loader sets NULL

---

## Table 2: `coverage_instance`

### Source
`data/scope/{insurer}_scope_mapped.csv`

### Pipeline Contribution (from Step 2)
Columns: `coverage_code`, `coverage_name_raw`, `mapping_status`, `match_type`, `source_page`

### Loader Operations
| Operation | Type | Description |
|-----------|------|-------------|
| Read CSV | INPUT | Load scope_mapped.csv |
| Normalize coverage_name_raw | TRANSFORM | Trim + collapse spaces (line 135-141) |
| Convert empty coverage_code to NULL | TRANSFORM | `if not coverage_code: coverage_code = None` (line 330-332) |
| Validate mapping_status | VALIDATE | Force to "matched"/"unmatched" (line 339-346) |
| Downgrade invalid matched | TRANSFORM | `matched` without code → `unmatched` (line 344-346) |
| Lookup insurer_id | LOOKUP | From DB metadata cache (line 293-296) |
| Lookup product_id | LOOKUP | Derive product_key from insurer_key, lookup DB (line 348-356) |
| Lookup variant_id | LOOKUP | Optional, NULL if no variants (line 358-366) |
| **Build instance_key** | **GENERATE** | **Deterministic natural key** (line 143-157) |
| Generate UUIDs | GENERATE | `instance_id` |
| UPSERT | WRITE | Insert or update `coverage_instance` table |

### Fields Mapping
| DB Field | Source | Loader Role |
|----------|--------|-------------|
| `instance_id` | - | **Loader generates UUID** |
| `insurer_id` | DB metadata | **Loader lookups** from insurer_key |
| `product_id` | DB metadata | **Loader lookups** from derived product_key |
| `variant_id` | DB metadata | **Loader lookups** (NULL if no variants) |
| `coverage_code` | CSV `coverage_code` | **Pass-through (or NULL if empty)** |
| `coverage_name_raw` | CSV `coverage_name_raw` | **Normalized (trim + collapse spaces)** |
| `source_page` | CSV `source_page` | Pass-through |
| `mapping_status` | CSV `mapping_status` | **Validated (forced to matched/unmatched)** |
| `match_type` | CSV `match_type` | Pass-through |
| `instance_key` | - | **Loader generates (deterministic)** |
| `created_at` | - | **Loader generates** |
| `updated_at` | - | **Loader generates** |

### Instance Key Formula (Line 143-157)
```
Format: {insurer_key}|{product_key}|{variant_key_or_}|{coverage_code_or_}|{coverage_name_raw_normalized}

Rules:
- variant_key: "_" if NULL
- coverage_code: "_" if NULL (for unmatched)
- coverage_name_raw: normalized (trim + collapse spaces)
```

**CRITICAL**: Loader GENERATES `instance_key`, not pipeline

---

## Table 3: `evidence_ref`

### Source (STEP NEXT-41S)
`data/compare/{insurer}_coverage_cards.jsonl` (field: `evidences[]`)

**Previous source (DEPRECATED)**: `data/evidence_pack/{insurer}_evidence_pack.jsonl`

### Pipeline Contribution (from Step 5)
Per card: `evidences[]` array with:
- `doc_type`
- `file_path` (absolute)
- `page`
- `snippet`
- `match_keyword`

### Loader Operations
| Operation | Type | Description |
|-----------|------|-------------|
| Read JSONL | INPUT | Load coverage_cards.jsonl |
| Extract evidences array | EXTRACT | `card['evidences']` (max 3) |
| Lookup coverage_instance_id | LOOKUP | Match by (insurer + coverage_name_raw) → instance_id + instance_key |
| Normalize file_path | TRANSFORM | Convert absolute → relative (remove project root) |
| Lookup document_id | LOOKUP | From DB metadata cache by file_path |
| **Assign rank** | **GENERATE** | **1-3 based on array index** (line 497) |
| **Build evidence_key** | **GENERATE** | **Deterministic natural key** (line 499-501) |
| Truncate snippet | TRANSFORM | Max 500 chars (line 510) |
| Generate UUIDs | GENERATE | `evidence_id` |
| UPSERT | WRITE | Insert or update `evidence_ref` table |

### Fields Mapping
| DB Field | Source | Loader Role |
|----------|--------|-------------|
| `evidence_id` | - | **Loader generates UUID** |
| `coverage_instance_id` | DB lookup | **Loader lookups** by (insurer + coverage_name_raw) |
| `document_id` | DB metadata | **Loader lookups** by normalized file_path |
| `doc_type` | Pipeline `evidences[].doc_type` | Pass-through |
| `page` | Pipeline `evidences[].page` | Pass-through |
| `snippet` | Pipeline `evidences[].snippet` | **Truncated to 500 chars** |
| `match_keyword` | Pipeline `evidences[].match_keyword` | Pass-through |
| `rank` | - | **Loader generates (1-3 based on array index)** |
| `evidence_key` | - | **Loader generates (deterministic)** |
| `created_at` | - | **Loader generates** |
| `updated_at` | - | **Loader generates** |

### Evidence Key Formula (Line 499-501)
```
Format: {instance_key}|{file_path_normalized}|{doc_type}|{page}|{rank}

Rules:
- instance_key: from coverage_instance lookup
- file_path_normalized: relative path (data/evidence_text/...)
- rank: 1-3 based on array index
```

**CRITICAL**:
- Loader GENERATES `rank` (not in pipeline output)
- Loader GENERATES `evidence_key` (not in pipeline output)
- Pipeline provides evidences in priority order → Loader assigns rank 1-3

---

## Table 4: `amount_fact`

### Source
`data/compare/{insurer}_coverage_cards.jsonl` (field: `amount`)

### Pipeline Contribution (from Step 7, OPTIONAL)
If Step 7 ran, card has `amount` object with:
- `status` ("CONFIRMED", "UNCONFIRMED", "CONFLICT")
- `value_text` (e.g., "3000만원")
- `source_doc_type` ("가입설계서", "약관", etc.)
- `source_priority` ("PRIMARY", "SECONDARY")
- `evidence_ref` (embedded evidence object, if CONFIRMED)

**If Step 7 did NOT run**: `amount` field is **ABSENT** (NULL)

### Loader Operations
| Operation | Type | Description |
|-----------|------|-------------|
| Read JSONL | INPUT | Load coverage_cards.jsonl |
| Extract amount field | EXTRACT | `card.get('amount')` → None if absent |
| Lookup coverage_instance_id | LOOKUP | Match by (insurer + coverage_name_raw) |
| **Handle missing amount** | **GENERATE** | **If amount=NULL → status=UNCONFIRMED, all fields NULL** (line 574-580) |
| Lookup evidence_id | LOOKUP | Match by (coverage_instance_id + source_doc_type) |
| Create evidence_ref if missing | CONDITIONAL CREATE | If CONFIRMED but no evidence_ref, create from `amount.evidence_ref` (line 605-615) |
| **Downgrade to UNCONFIRMED** | **VALIDATE** | **If CONFIRMED but no evidence_id → UNCONFIRMED** (line 617-625) |
| Generate UUIDs | GENERATE | `amount_id` |
| UPSERT | WRITE | Insert or update `amount_fact` table |

### Fields Mapping
| DB Field | Source | Loader Role |
|----------|--------|-------------|
| `amount_id` | - | **Loader generates UUID** |
| `coverage_instance_id` | DB lookup | **Loader lookups** by (insurer + coverage_name_raw) |
| `evidence_id` | DB lookup | **Loader lookups** (or creates from `amount.evidence_ref`) |
| `status` | Pipeline `amount.status` | **Pass-through (or "UNCONFIRMED" if amount=NULL)** |
| `value_text` | Pipeline `amount.value_text` | **Pass-through (or NULL if amount=NULL)** |
| `source_doc_type` | Pipeline `amount.source_doc_type` | **Pass-through (or NULL if amount=NULL)** |
| `source_priority` | Pipeline `amount.source_priority` | **Pass-through (or NULL if amount=NULL)** |
| `notes` | - | **Loader sets empty array `[]`** (line 649) |
| `created_at` | - | **Loader generates** |
| `updated_at` | - | **Loader generates** |

**CRITICAL**:
- **If `amount` field is ABSENT (Step 5 output, NO Step 7)**: Loader writes `status=UNCONFIRMED`, all fields NULL
- **If `amount.status=CONFIRMED` but no evidence_id**: Loader DOWNGRADES to UNCONFIRMED (safety gate)
- Loader does NOT extract/infer amounts from snippets (line 526-527)

---

## Summary: Loader-Generated Fields vs. Pipeline Fields

### Loader ALWAYS Generates
| Field | Table | Generation Method |
|-------|-------|-------------------|
| `instance_key` | coverage_instance | Deterministic formula (insurer\|product\|variant\|code\|name) |
| `evidence_key` | evidence_ref | Deterministic formula (instance_key\|path\|doc_type\|page\|rank) |
| `rank` | evidence_ref | Array index (1-3) |
| All UUIDs | All tables | `gen_random_uuid()` or Python uuid |
| All timestamps | All tables | `datetime.now()` or `CURRENT_TIMESTAMP` |

### Loader Lookups (NOT in Pipeline)
| Field | Table | Lookup Source |
|-------|-------|---------------|
| `insurer_id` | coverage_instance | DB metadata (by insurer_key) |
| `product_id` | coverage_instance | DB metadata (by product_key) |
| `variant_id` | coverage_instance | DB metadata (by variant_key, NULL if none) |
| `coverage_instance_id` | evidence_ref, amount_fact | DB query (by insurer + coverage_name_raw) |
| `document_id` | evidence_ref | DB metadata (by file_path) |
| `evidence_id` | amount_fact | DB query (by coverage_instance_id + source_doc_type) |

### Loader Transforms (Pipeline → DB)
| Field | Table | Transformation |
|-------|-------|----------------|
| `coverage_name_raw` | coverage_instance | Normalize (trim + collapse spaces) |
| `coverage_code` | coverage_instance | Empty string → NULL |
| `mapping_status` | coverage_instance | Validate (force to matched/unmatched) |
| `file_path` | evidence_ref | Absolute → relative |
| `snippet` | evidence_ref | Truncate to 500 chars |
| `status` | amount_fact | NULL → "UNCONFIRMED" (if amount field missing) |

### Pure Pass-Through (Pipeline → DB)
| Fields | Table | No Transformation |
|--------|-------|-------------------|
| `coverage_code`, `coverage_name_canonical` | coverage_canonical | From Excel |
| `source_page`, `match_type` | coverage_instance | From scope_mapped.csv |
| `doc_type`, `page`, `match_keyword` | evidence_ref | From coverage_cards.evidences[] |
| `value_text`, `source_doc_type`, `source_priority` | amount_fact | From coverage_cards.amount |

---

## Pipeline Gaps That Loader Fills

### Gap 1: Metadata FKs (insurer_id, product_id, variant_id, document_id)
- **Why**: Pipeline works with file paths, not DB UUIDs
- **Loader solution**: Load metadata from DB, build lookup maps
- **Source**: `products.yml` (loaded into DB metadata tables separately)

### Gap 2: Natural Keys (instance_key, evidence_key)
- **Why**: Idempotent upsert requires deterministic keys
- **Loader solution**: Generate keys from normalized data
- **Formula**: Documented in lines 143-157 (instance_key), 499-501 (evidence_key)

### Gap 3: Evidence Rank (1-3)
- **Why**: Pipeline outputs evidences in priority order, but no explicit rank field
- **Loader solution**: Assign rank based on array index (1st = rank 1, 2nd = rank 2, 3rd = rank 3)

### Gap 4: Missing Amount Field (Step 5 output without Step 7)
- **Why**: Step 7 is optional, Step 5 output has NO `amount` field
- **Loader solution**: Write `status=UNCONFIRMED` with NULL values
- **Safety**: Loader does NOT infer/extract amounts from snippets

---

## What Loader Does NOT Do

❌ **Extract amounts from snippets** (line 526-527)
❌ **Infer coverage_category or payment_event** (sets NULL)
❌ **Calculate or normalize amounts** (exact text only)
❌ **Generate prose or recommendations** (notes = empty array)
❌ **Modify snippet content** (only truncates to 500 chars)
❌ **Change doc_type or page numbers** (pass-through)
❌ **Interpret match_keyword** (pass-through)

---

## Loader Safety Gates

### Gate 1: Matched without code → Unmatched (line 344-346)
```python
if mapping_status == 'matched' and coverage_code is None:
    logger.warning(f"Matched coverage without code: {coverage_name_raw}, forcing to unmatched")
    mapping_status = 'unmatched'
```

### Gate 2: CONFIRMED without evidence_id → UNCONFIRMED (line 617-625)
```python
if not evidence_id:
    logger.warning(f"No evidence_ref for {coverage_name_raw}, downgrading to UNCONFIRMED")
    status = 'UNCONFIRMED'
    value_text = None
```

### Gate 3: Missing amount field → UNCONFIRMED (line 574-580)
```python
if not amount_data:
    status = 'UNCONFIRMED'
    value_text = None
    evidence_id = None
```

---

## Next: Classify Mismatch Types
See: `STEP_NEXT_42R_MISMATCH_MATRIX.md`
