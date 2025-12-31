# STEP NEXT-42R: Mismatch Matrix (Type A/B/C Classification)

## Classification Rules

- **Type A**: Pipeline is correct, DB/Loader expects legacy field → **DB/Loader must adapt**
- **Type B**: DB structure is correct, Pipeline output is insufficient → **Pipeline must extend**
- **Type C**: Neither is correct, both are legacy cruft → **Remove from both**

---

## Mismatch 1: `amount` field (CRITICAL)

### Current State
- **Pipeline (Step 5)**: Does NOT output `amount` field
- **Pipeline (Step 7)**: Optionally adds `amount` field (LLM-based extraction)
- **DB**: Expects `amount_fact` table with CONFIRMED/UNCONFIRMED status
- **Loader**: Writes UNCONFIRMED if `amount` field missing (line 574-580)

### Analysis
| Aspect | Pipeline | DB | Reality |
|--------|----------|-----|---------|
| Design intent | Step 1-5 = facts only (no amounts) | Store CONFIRMED amounts with evidence | Step 7 is optional LLM step |
| Current output | Step 5: NO `amount` field | `amount_fact` table exists | Loader handles missing `amount` |
| Production path | Pipeline WITHOUT Step 7 | DB expects amounts | Loader writes UNCONFIRMED |

### Classification: **Type A (Pipeline is correct)**

**Reasoning**:
- Canonical pipeline (Step 1-5) is fact-based, NO amounts
- Step 7 is OPTIONAL and uses LLM (violates "NO LLM" principle)
- DB `amount_fact` table is **premature optimization** for future feature
- Loader correctly handles missing `amount` by writing UNCONFIRMED

**Resolution**:
- ✅ Keep Pipeline Step 1-5 WITHOUT `amount` field
- ✅ Keep Loader safety gate (missing `amount` → UNCONFIRMED)
- ⚠️ `amount_fact` table is "future-ready infrastructure" (keep, but ALL rows = UNCONFIRMED for now)
- ❌ Do NOT force Pipeline to add `amount` field
- ❌ Do NOT run Step 7 in canonical pipeline

---

## Mismatch 2: `coverage_category` and `payment_event` (coverage_canonical)

### Current State
- **Pipeline**: Does NOT provide these fields (not in Excel)
- **DB**: Has columns `coverage_category`, `payment_event` (nullable)
- **Loader**: Sets both to NULL (line 268-270)

### Analysis
| Field | Excel Source | DB Column | Loader Behavior |
|-------|--------------|-----------|-----------------|
| `coverage_category` | ❌ Not in Excel | ✅ Exists (nullable) | Sets NULL |
| `payment_event` | ❌ Not in Excel | ✅ Exists (nullable) | Sets NULL |

### Classification: **Type A (Pipeline is correct)**

**Reasoning**:
- Excel (INPUT contract) does NOT have these fields
- DB added these columns for "future enrichment"
- Loader correctly sets NULL (no inference)

**Resolution**:
- ✅ Keep Excel as-is (do NOT add columns)
- ✅ Keep DB columns (nullable, for future manual enrichment)
- ✅ Keep Loader setting NULL
- ❌ Do NOT infer these fields from coverage names

---

## Mismatch 3: `instance_key` and `evidence_key` (natural keys)

### Current State
- **Pipeline**: Does NOT output natural keys
- **DB**: Has `instance_key` (coverage_instance), `evidence_key` (evidence_ref)
- **Loader**: GENERATES both keys (deterministic formulas)

### Analysis
| Key | Pipeline Output | DB Column | Loader Role |
|-----|----------------|-----------|-------------|
| `instance_key` | ❌ Not in CSV | ✅ Unique constraint | **Generates** from (insurer\|product\|variant\|code\|name) |
| `evidence_key` | ❌ Not in JSONL | ✅ Unique constraint | **Generates** from (instance_key\|path\|doc_type\|page\|rank) |

### Classification: **Type B (DB is correct, Pipeline insufficient)**

**Reasoning**:
- Natural keys are **required for idempotent upsert**
- Pipeline outputs raw data, not DB-optimized keys
- Loader is **correct layer** to generate natural keys (transformation layer)

**Resolution**:
- ✅ Keep DB natural key columns
- ✅ Keep Loader generating keys
- ✅ Pipeline stays "key-agnostic" (raw data only)
- ❌ Do NOT force Pipeline to generate DB keys

**Justification**: Loader is the **transformation layer** between file-based pipeline and relational DB.

---

## Mismatch 4: `rank` field (evidence_ref)

### Current State
- **Pipeline**: Outputs `evidences[]` array in priority order (max 3 items)
- **DB**: Has `rank` column (1-3)
- **Loader**: Assigns `rank` based on array index (line 497)

### Analysis
| Aspect | Pipeline | DB | Loader |
|--------|----------|-----|--------|
| Evidence ordering | Array order = priority | `rank INT` (1-3) | `rank = idx + 1` |
| Explicit rank field | ❌ No | ✅ Yes | **Generates** |

### Classification: **Type B (DB is correct, Pipeline insufficient)**

**Reasoning**:
- Pipeline outputs evidences in **implicit priority order** (array position)
- DB requires **explicit rank** for query sorting
- Loader correctly transforms implicit order → explicit rank

**Resolution**:
- ✅ Keep Pipeline outputting ordered array (no `rank` field)
- ✅ Keep DB `rank` column
- ✅ Keep Loader assigning rank based on index
- ❌ Do NOT force Pipeline to add `rank` field

**Justification**: Array position (pipeline) → Explicit rank (DB) is valid transformation.

---

## Mismatch 5: Metadata FKs (insurer_id, product_id, variant_id, document_id)

### Current State
- **Pipeline**: Uses file paths and insurer keys (lowercase: "kb", "samsung")
- **DB**: Uses UUIDs for all metadata FKs
- **Loader**: Lookups UUIDs from DB metadata cache

### Analysis
| FK Field | Pipeline | DB | Loader |
|----------|----------|-----|--------|
| `insurer_id` | Insurer key ("kb") | UUID FK | Looks up by key |
| `product_id` | Implicit (file path) | UUID FK | Derives product_key, looks up |
| `variant_id` | Not present | UUID FK (nullable) | Looks up (NULL if none) |
| `document_id` | File path (absolute) | UUID FK | Normalizes path, looks up |

### Classification: **Type B (DB is correct, Pipeline insufficient)**

**Reasoning**:
- Pipeline works with **file-system primitives** (paths, keys)
- DB requires **relational FK integrity** (UUIDs)
- Loader is **correct layer** to bridge file-system → relational model

**Resolution**:
- ✅ Keep Pipeline using file paths / insurer keys
- ✅ Keep DB using UUIDs for FK integrity
- ✅ Keep Loader performing lookups
- ❌ Do NOT force Pipeline to output UUIDs

**Justification**: Pipeline is file-based, Loader is DB-aware. Separation of concerns is correct.

---

## Mismatch 6: `notes` field (amount_fact)

### Current State
- **Pipeline**: Does NOT output `notes` field
- **DB**: Has `notes JSONB` column (default: `[]`)
- **Loader**: Sets `notes = []` (empty array, line 649)

### Analysis
| Field | Pipeline | DB | Loader | API Intent |
|-------|----------|-----|--------|------------|
| `notes` | ❌ Not in `amount` object | ✅ JSONB (nullable) | Sets `[]` | "Fixed keywords only" |

### Classification: **Type C (Both are legacy cruft)**

**Reasoning**:
- Pipeline does NOT produce notes
- DB has `notes` but loader always writes empty array
- DB comment says "Fixed keywords only. FORBIDDEN: prose, recommendations"
- **No one populates this field, no one reads this field**

**Resolution**:
- 🚧 **CANDIDATE for removal** (but low priority)
- ✅ Keep for now (harmless empty array)
- ⚠️ Future: Remove column if never populated

---

## Mismatch 7: `file_path` normalization (evidence_ref)

### Current State
- **Pipeline**: Outputs absolute paths (e.g., `/Users/cheollee/inca-rag-scope/data/...`)
- **DB document table**: Stores relative paths (e.g., `data/evidence_text/...`)
- **Loader**: Normalizes absolute → relative (line 482-493)

### Classification: **Type B (DB is correct, Pipeline insufficient)**

**Reasoning**:
- Pipeline outputs absolute paths (correct for local execution)
- DB requires **portable relative paths** (correct for multi-env deployment)
- Loader correctly transforms absolute → relative

**Resolution**:
- ✅ Keep Pipeline outputting absolute paths (execution context)
- ✅ Keep DB storing relative paths (portability)
- ✅ Keep Loader normalizing paths
- ❌ Do NOT force Pipeline to output relative paths (breaks local execution)

---

## Mismatch 8: `snippet` truncation (evidence_ref)

### Current State
- **Pipeline**: Outputs full snippets (up to ~400 chars, Step 5 line 267)
- **DB**: No length constraint, but snippet can be large
- **Loader**: Truncates to 500 chars (line 510)

### Classification: **Type A (Pipeline is correct, Loader is defensive)**

**Reasoning**:
- Pipeline already limits snippets to ~400 chars (Step 5 diversity selection)
- Loader adds defensive truncation to 500 chars (safety, not requirement)
- **No mismatch** — Both are correct

**Resolution**:
- ✅ Keep Pipeline limiting to ~400 chars
- ✅ Keep Loader truncating to 500 chars (defensive)
- ✅ Aligned correctly

---

## Mismatch 9: `variant_id` (coverage_instance, optional)

### Current State
- **Pipeline**: Does NOT have variant concept (no sex/age_band in scope CSV)
- **DB**: Has `variant_id` FK (nullable)
- **Loader**: Sets `variant_id = NULL` (line 358-366)

### Analysis
| Insurer | Has Variants? | Pipeline | DB | Loader |
|---------|---------------|----------|-----|--------|
| LOTTE | Yes (Male/Female) | ❌ No field | ✅ variant table | Sets NULL |
| DB | Yes (Age bands) | ❌ No field | ✅ variant table | Sets NULL |
| Others | No | ❌ No field | ✅ NULL allowed | Sets NULL |

### Classification: **Type B (DB is correct, Pipeline insufficient)**

**Reasoning**:
- LOTTE/DB insurers **actually have gender/age variants** (real data)
- Pipeline scope CSV does NOT capture variant info (extraction gap)
- DB correctly models variants
- Loader correctly sets NULL (no data available)

**Resolution**:
- ✅ Keep DB `variant_id` column (real requirement)
- ⚠️ **Future**: Pipeline Step 1 should extract variant info for LOTTE/DB
- ✅ Loader correctly sets NULL for now
- ❌ Do NOT remove `variant_id` from DB (real data model)

**Note**: This is a **data extraction gap**, not a schema mismatch.

---

## Summary Table: All Mismatches

| # | Field/Concept | Type | Resolution | Action |
|---|---------------|------|------------|--------|
| 1 | `amount` field | **A** | Pipeline correct (no amounts in Step 1-5) | Keep as-is, amount_fact writes UNCONFIRMED |
| 2 | `coverage_category`, `payment_event` | **A** | Pipeline correct (not in Excel) | Keep DB cols (nullable), loader sets NULL |
| 3 | `instance_key`, `evidence_key` | **B** | DB correct (idempotent upsert) | Loader generates keys |
| 4 | `rank` field | **B** | DB correct (explicit rank) | Loader assigns rank from array index |
| 5 | Metadata FKs (UUIDs) | **B** | DB correct (relational integrity) | Loader lookups UUIDs |
| 6 | `notes` field | **C** | Both are cruft | Keep for now (harmless), future removal candidate |
| 7 | `file_path` normalization | **B** | DB correct (portability) | Loader normalizes absolute→relative |
| 8 | `snippet` truncation | **A** | Both correct (aligned) | No action needed |
| 9 | `variant_id` | **B** | DB correct (real data model) | Future: Pipeline extracts variant info |

---

## Key Findings

### Finding 1: Pipeline (Step 1-5) is Fact-Based (Type A wins)
- Pipeline does NOT produce amounts → **Correct**
- Pipeline does NOT infer categories/events → **Correct**
- `amount_fact` table exists but writes UNCONFIRMED → **Acceptable**

### Finding 2: Loader is Transformation Layer (Type B wins)
- Loader GENERATES natural keys → **Correct**
- Loader LOOKUPS UUIDs → **Correct**
- Loader NORMALIZES paths → **Correct**
- Loader ASSIGNS rank → **Correct**

### Finding 3: No Critical Type C (Removal Required)
- Only `notes` field is candidate for removal (low priority)
- All other fields serve a purpose

### Finding 4: Variant Support Gap (Future Work)
- LOTTE/DB insurers have real variants
- Pipeline does NOT extract variant info (Step 1 gap)
- DB/Loader correctly model variants (set NULL for now)
- **Action**: Future Step 1 enhancement to extract variants

---

## Alignment Decision Matrix

| Layer | Responsibility | Boundary |
|-------|---------------|----------|
| **Pipeline (Step 1-5)** | Extract facts from PDFs/Excel | File-based, NO DB awareness |
| **Loader** | Transform files → DB | DB-aware, generates keys/ranks, lookups FKs |
| **DB** | Store facts with relational integrity | Relational model, FK constraints |

**Golden Rule**: Pipeline = file-system primitives, Loader = transformation layer, DB = relational model

---

## Next: Single Path Decision
See: `STEP_NEXT_42R_SINGLE_PATH_DECISION.md`
