# STEP NEXT-42R: Single Path Decision (NON-NEGOTIABLE)

## Purpose
Define THE ONLY path forward. No options, no "선택지", no "나중에".

---

## Constitutional Decisions (LOCKED)

### Decision 1: Pipeline Stops at Step 5 (Facts Only)

**We are using:**
- Pipeline Step 1-5 as canonical truth
- Step 5 output = `data/compare/*_coverage_cards.jsonl`
- **NO `amount` field in canonical output**

**We are NOT using:**
- Step 7 (amount extraction via LLM)
- Any LLM-based inference
- Any "임시로 amount 추가"

**Enforcement:**
```
Canonical pipeline = Step 1-5
Step 7 = DEPRECATED (moved to _deprecated/ or marked as experimental)
Production loader expects NO amount field
```

**Consequence:**
- All `amount_fact` rows have `status = UNCONFIRMED`
- `value_text = NULL`, `evidence_id = NULL`
- API does NOT return amounts (or returns "확인 불가")

---

### Decision 2: Loader is Transformation Layer (NOT Pass-Through)

**We are using:**
- Loader GENERATES: `instance_key`, `evidence_key`, `rank`, UUIDs, timestamps
- Loader LOOKUPS: `insurer_id`, `product_id`, `variant_id`, `document_id`
- Loader TRANSFORMS: `file_path` (absolute→relative), `snippet` (truncate to 500)
- Loader VALIDATES: `mapping_status`, `coverage_code` NULL handling

**We are NOT using:**
- Pipeline generating DB keys
- Pipeline outputting UUIDs
- "Loader는 단순 복사만" 같은 제약

**Enforcement:**
```
Loader responsibility = File-system primitives → Relational model
Pipeline responsibility = Extract facts from PDFs/Excel
Clear separation of concerns
```

**Consequence:**
- Pipeline outputs stay file-based (paths, keys, arrays)
- Loader code stays complex (lookups, key generation, normalization)
- **DO NOT simplify loader to "just copy"**

---

### Decision 3: DB Schema is Future-Ready (Keep Nullable Columns)

**We are using:**
- DB columns that are currently NULL-only: `coverage_category`, `payment_event`, `variant_id`
- DB tables that are currently UNCONFIRMED-only: `amount_fact`
- DB constraints that enforce data integrity: FK constraints, check constraints

**We are NOT using:**
- "Unused column → Delete immediately"
- "All rows NULL → Drop column"
- Schema thrashing

**Enforcement:**
```
DB schema = Stable contract for future enrichment
Nullable columns = Future manual enrichment gates
amount_fact = Future Step 7 alternative (non-LLM) or manual entry
variant_id = Future Step 1 enhancement (extract variants)
```

**Consequence:**
- DB schema changes are RARE and DELIBERATE
- Loader writes NULL for unpopulated fields (correct behavior)
- Future features can populate these columns WITHOUT schema migration

---

### Decision 4: API Reads DB (NOT coverage_cards.jsonl Directly)

**We are using:**
- Production API (`apps/api/server.py`) queries PostgreSQL
- API reads from: `coverage_canonical`, `coverage_instance`, `evidence_ref`, `amount_fact`
- API does NOT read JSONL files directly

**We are NOT using:**
- API reading `data/compare/*.jsonl` (file I/O in production)
- "Mock API로 대충 확인"
- "JSONL을 그대로 반환"

**Enforcement:**
```
API data source = PostgreSQL ONLY
JSONL files = Loader INPUT, NOT API input
Mock API = Development tool, NOT production
```

**Consequence:**
- SSOT (coverage_cards.jsonl) → Loader → DB → API (one-way flow)
- API never bypasses DB
- API never reads files directly

---

### Decision 5: Amount Fact = UNCONFIRMED Until Alternative to Step 7 Exists

**We are using:**
- `amount_fact.status = UNCONFIRMED` for ALL rows (current state)
- `amount_fact.value_text = NULL` for ALL rows
- API returns `"확인 불가"` or omits amount field

**We are NOT using:**
- "임시로 Step 7 돌리자"
- "LLM 한 번만 쓰자"
- "Snippet에서 금액 추출"

**Enforcement:**
```
amount_fact writes = UNCONFIRMED only (loader line 574-580)
Step 7 = SUSPENDED (not part of canonical pipeline)
Future alternative = Manual entry OR deterministic extraction (NO LLM)
```

**Consequence:**
- **We accept that amounts are unavailable in current production**
- **We do NOT compromise "NO LLM" principle**
- Future: Manual CSV upload OR regex-based extraction (deterministic)

---

## Architecture Layers (FINAL)

```
Layer 1: INPUT (Excel + PDFs)
  ↓
Layer 2: Pipeline (Step 1-5)
  Output: coverage_cards.jsonl (SSOT, NO amount field)
  ↓
Layer 3: Loader (Transformation)
  Generates: instance_key, evidence_key, rank, UUIDs
  Lookups: insurer_id, product_id, variant_id, document_id
  Writes: coverage_canonical, coverage_instance, evidence_ref, amount_fact (UNCONFIRMED)
  ↓
Layer 4: Database (PostgreSQL)
  Storage: Relational model with FK integrity
  ↓
Layer 5: API (Production)
  Queries: PostgreSQL ONLY
  Returns: Compare Response View Model (5-block contract)
```

**Flow is ONE-WAY**: Excel/PDF → Pipeline → Loader → DB → API

**NO SHORTCUTS**:
- ❌ API bypassing DB to read JSONL
- ❌ Loader bypassing pipeline to read PDFs
- ❌ Pipeline writing to DB directly

---

## Responsibility Matrix (WHO DOES WHAT)

| Responsibility | Owner | NOT Owner |
|----------------|-------|-----------|
| Extract coverage names from PDF | Pipeline Step 1 | Loader, API |
| Map coverage names to canonical codes | Pipeline Step 2 | Loader, API |
| Search evidence in PDF text | Pipeline Step 4 | Loader, API |
| Build coverage cards (SSOT) | Pipeline Step 5 | Loader, API |
| Generate instance_key, evidence_key | **Loader** | Pipeline, API |
| Lookup insurer_id, product_id | **Loader** | Pipeline, API |
| Normalize file paths (absolute→relative) | **Loader** | Pipeline, API |
| Assign evidence rank (1-3) | **Loader** | Pipeline, API |
| Enforce FK constraints | **DB** | Pipeline, Loader, API |
| Query comparison data | **API** | Pipeline, Loader |
| Validate request schema (Pydantic) | **API** | Pipeline, Loader, DB |
| Build Response View Model (5-block) | **API** | Pipeline, Loader, DB |

**Golden Rule**: Each layer owns its transformation, NO layer skips levels.

---

## What We Do NOT Do (Absolute Prohibitions)

### Prohibition 1: NO LLM in Production Pipeline
- ❌ Step 7 (amount extraction via GPT-4)
- ❌ "한 번만 LLM 쓰자"
- ❌ Snippet summarization
- ❌ Coverage name inference

### Prohibition 2: NO Temporary Patches
- ❌ "임시로 amount 하드코딩"
- ❌ "일단 mock 데이터로"
- ❌ "나중에 고치자"

### Prohibition 3: NO Schema Thrashing
- ❌ "Unused column 삭제"
- ❌ "NULL이 많으니 DROP"
- ❌ "Schema 변경해서 맞추자"

### Prohibition 4: NO Layer Bypass
- ❌ API reading JSONL directly
- ❌ Loader reading PDFs directly
- ❌ Pipeline writing to DB directly

### Prohibition 5: NO Scope Expansion
- ❌ "전체 담보 추가"
- ❌ "유사 상품 비교"
- ❌ "추천 기능"

---

## Current Production State (Accept Reality)

### What We Have NOW
✅ Pipeline Step 1-5 running for 8 insurers (KB, Samsung, Meritz, etc.)
✅ coverage_cards.jsonl populated (NO amount field)
✅ Loader script functional (writes UNCONFIRMED to amount_fact)
✅ DB schema stable (FK constraints enforced)
✅ Production API code exists (queries DB)

### What We DO NOT Have NOW
❌ Amount data (all amount_fact rows = UNCONFIRMED)
❌ Variant extraction (LOTTE/DB gender/age splits)
❌ Coverage category / payment event (all NULL)
❌ Production API running (STEP NEXT-42 suspended)
❌ E2E test with real data

### What We Accept
- **Amounts are unavailable** → API returns "확인 불가"
- **Variants are missing** → variant_id = NULL for all rows
- **Categories are NULL** → Future manual enrichment
- **This is correct behavior** → NO shortcuts

---

## Next WRITE Steps (After This STEP)

### STEP NEXT-43: Production API E2E (DB-backed, NO amount)
**Scope**:
- Execute Production API on clean port
- Run 2 E2E scenarios (A4200_1, Meritz (20년갱신) prefix)
- Validate Response View Model (5-block contract)
- **Accept**: All amount fields = "확인 불가"
- **Accept**: All amount_fact rows = UNCONFIRMED

**Deliverables**:
- E2E test log (2 scenarios)
- Schema validation PASS
- CURRENT_SYSTEM_PATH.md (single path doc)

**Prohibitions**:
- ❌ Running Step 7 to get amounts
- ❌ Mocking amount data
- ❌ Changing API contract to hide missing amounts

---

### STEP NEXT-44: Variant Extraction Enhancement (Optional)
**Scope**:
- Enhance Pipeline Step 1 to extract gender/age info for LOTTE/DB
- Update scope CSV schema to include variant column
- Loader maps variant info to variant_id

**Deliverables**:
- Updated Step 1 code
- Updated scope CSV schema
- Loader variant mapping logic

**Trigger**: Only if LOTTE/DB production deployment requires variant splits

---

### STEP NEXT-45: Manual Amount Entry (Future Alternative)
**Scope**:
- Define CSV format for manual amount entry
- Loader ingests amount CSV → amount_fact (CONFIRMED)
- API returns amounts from DB

**Deliverables**:
- Amount CSV schema
- Loader amount ingestion logic
- E2E test with amounts

**Trigger**: Only if client demands amount comparison

**Note**: This is NON-LLM alternative to Step 7

---

## FINAL PATH (Single Sentence)

**We use Pipeline Step 1-5 (NO amounts) → Loader (transformation layer) → DB (future-ready schema) → API (DB-backed, accepts missing amounts), and we do NOT use Step 7, mock APIs, temporary patches, or layer bypasses.**

---

## Enforcement Checklist (Before Any WRITE Action)

Before making ANY code/schema/data change, verify:

- [ ] Does this change violate "NO LLM"?
- [ ] Does this bypass a layer (Pipeline→API, Loader→PDF, API→JSONL)?
- [ ] Does this add "임시" or "temporary" logic?
- [ ] Does this remove a future-ready nullable column?
- [ ] Does this expand scope beyond canonical pipeline?

**If ANY checkbox is YES → REJECT THE CHANGE**

---

## DoD (This STEP Complete)

- ✅ 5 documents created (Contract, Intent, Role Split, Mismatch, Decision)
- ✅ Single path defined (no options)
- ✅ Execution count = 0 (READ-ONLY enforced)
- ✅ DB state unchanged
- ✅ API not executed

**Next**: STEP NEXT-43 (Production API E2E with accepted missing amounts)
