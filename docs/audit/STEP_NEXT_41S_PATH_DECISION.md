# STEP NEXT-41S: Path Decision (Phase A-5)

**Date**: 2025-12-31
**Decision**: **Path-2 (Schema Drift)** — Fix loader + reset data (NO DDL changes)

---

## Decision Matrix

| Criterion | Path-1 (Schema OK) | Path-2 (Schema Drift) | Path-3 (Rebuild) |
|-----------|-------------------|----------------------|------------------|
| **DB Schema Correct** | ✅ Yes | ✅ Yes (GAMMA-patched) | ❌ No |
| **Loader → SSOT Aligned** | ✅ Yes | ❌ **NO** (reads DEPRECATED) | N/A |
| **Data Current** | ✅ Yes | ❌ **NO** (285 stale rows) | N/A |
| **DDL Changes Needed** | ❌ No | ❌ **No** | ✅ Yes |
| **Data Reload Needed** | ❌ No | ✅ **YES** | ✅ Yes |
| **Loader Fix Needed** | ❌ No | ✅ **YES** | ✅ Yes |

**Selected**: **Path-2** (fix loader + reload data, NO DDL)

---

## Path-2 Execution Plan

### Phase B-1: Fix Loader Source (Code Change)

**File**: `apps/loader/step9_loader.py`
**Method**: `load_evidence_ref()` (line 397-517)

**Change**:
```python
# BEFORE (line 409):
pack_path = self.project_root / f'data/evidence_pack/{insurer_key}_evidence_pack.jsonl'

# AFTER:
pack_path = self.project_root / f'data/compare/{insurer_key}_coverage_cards.jsonl'
```

**Justification**:
- `evidence_pack.jsonl` is DEPRECATED (CLAUDE.md line 41)
- SSOT is `coverage_cards.jsonl` (Step 5 output)
- Current SSOT has `evidences[]` field with same structure

**Risk**: LOW (field structure is identical, only source file changes)

---

### Phase B-2: Reset and Reload Data (DML Only)

#### Step 1: Backup Current DB

```bash
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope -F c -f /tmp/inca_rag_scope_backup_41s.dump
docker cp inca_rag_scope_db:/tmp/inca_rag_scope_backup_41s.dump ./backups/
```

#### Step 2: Truncate Fact Tables

```sql
TRUNCATE TABLE amount_fact CASCADE;
TRUNCATE TABLE evidence_ref CASCADE;
TRUNCATE TABLE coverage_instance CASCADE;
TRUNCATE TABLE coverage_canonical CASCADE;
```

**Expected Result**:
- 4 tables empty
- Metadata tables (insurer, product, document, etc.) UNTOUCHED

#### Step 3: Run Loader (reset_then_load)

```bash
python -m apps.loader.step9_loader \
  --db-url "postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope" \
  --mode reset_then_load
```

**Expected Outcome**:
- `coverage_canonical`: ~48 rows (from Excel)
- `coverage_instance`: ~297 rows (from scope CSVs)
- `evidence_ref`: ~747 rows (from coverage_cards.jsonl `evidences[]`)
- `amount_fact`: ~297 rows (ALL UNCONFIRMED, because SSOT has no `amount` field)

#### Step 4: Verify Row Counts

```sql
SELECT 'coverage_canonical' as table_name, COUNT(*) as rows FROM coverage_canonical
UNION ALL
SELECT 'coverage_instance', COUNT(*) FROM coverage_instance
UNION ALL
SELECT 'evidence_ref', COUNT(*) FROM evidence_ref
UNION ALL
SELECT 'amount_fact', COUNT(*) FROM amount_fact;
```

#### Step 5: Verify amount_fact Status

```sql
SELECT status, COUNT(*) as count
FROM amount_fact
GROUP BY status
ORDER BY status;
```

**Expected**:
```
  status      | count
--------------+-------
 UNCONFIRMED  |   297
```

**If NOT all UNCONFIRMED**: Investigate where `amount` data came from.

---

### Phase B-3: API Contract Validation

#### Scenario 1: 암진단비 (A4200_1) Comparison

**Endpoint**: `GET /api/compare?coverage_code=A4200_1&insurers=kb,samsung,meritz`

**Expected Response Structure** (5-block contract):
```json
{
  "coverage_code": "A4200_1",
  "coverage_name_canonical": "암진단비(유사암제외)",
  "insurers": [
    {
      "insurer": "kb",
      "coverage_name_raw": "...",
      "evidence": {
        "약관": { "snippet": "...", "page": 4 },
        "사업방법서": { "snippet": "...", "page": 10 },
        "상품요약서": { "snippet": "...", "page": 9 }
      },
      "amount": {
        "status": "UNCONFIRMED",
        "value_text": null
      }
    },
    ...
  ]
}
```

**Validation Checklist**:
- ✅ Evidence blocks present (약관/사업방법서/상품요약서)
- ✅ Snippets are non-empty
- ✅ amount.status = "UNCONFIRMED" (expected until Step7 re-runs)
- ✅ amount.value_text = null

#### Scenario 2: Meritz Prefix Alias (e.g., "(20년갱신)" coverage)

**Coverage**: Find any Meritz coverage with `(20년갱신)` prefix (e.g., from git status samsung_scope_mapped.csv)

**Endpoint**: `GET /api/coverage/{coverage_code}?insurer=meritz`

**Expected**:
- ✅ Evidence found (evidences[] in coverage_cards should handle prefix)
- ✅ mapping_status = "matched"
- ✅ amount.status = "UNCONFIRMED"

**Validation**:
- API returns evidence (not empty)
- No 500 errors (DB FK constraints satisfied)

---

## Post-Reload Expectations

### What Changes

| Table | Before | After | Change |
|-------|--------|-------|--------|
| `coverage_canonical` | 48 rows | ~48 rows | Same (from Excel) |
| `coverage_instance` | 297 rows | ~297 rows | Same (from CSV) |
| `evidence_ref` | 747 rows | ~747 rows (from cards) | **SOURCE CHANGED** (pack→cards) |
| `amount_fact` | 285 rows | ~297 rows (UNCONFIRMED) | **STATUS CHANGED** (all UNCONFIRMED) |

### What Does NOT Change

- ✅ DB Schema (no DDL)
- ✅ Metadata tables (insurer, product, document, etc.)
- ✅ API contract (5-block structure)
- ✅ Frontend behavior (amounts will show "확인 불가" until Step7 re-runs)

### What Needs Follow-Up (Out of Scope for STEP NEXT-41S)

1. **Amount Enrichment**: Re-run Step7 amount extraction to populate `amount` field in coverage_cards.jsonl
2. **Loader Re-run**: After Step7, run loader again to populate amount_fact with CONFIRMED amounts
3. **evidence_pack Deprecation**: Move `data/evidence_pack/` to `_deprecated/` (per LEAN principles)

---

## Execution Log Template

Record to: `docs/audit/STEP_NEXT_41S_EXEC_LOG.md`

```markdown
# STEP NEXT-41S Execution Log

## Phase B-1: Loader Fix (Code Change)

**Date**: [timestamp]
**File**: apps/loader/step9_loader.py
**Line**: 409
**Change**: evidence_pack → coverage_cards
**Commit**: [git commit hash]

## Phase B-2: Data Reset + Reload

**Date**: [timestamp]

### Backup
- File: backups/inca_rag_scope_backup_41s.dump
- Size: [size]

### Truncate
- coverage_canonical: 48 rows → 0 rows
- coverage_instance: 297 rows → 0 rows
- evidence_ref: 747 rows → 0 rows
- amount_fact: 285 rows → 0 rows

### Reload
- Loader command: [command]
- Loader output: [paste output]

### Post-Reload Counts
- coverage_canonical: [count]
- coverage_instance: [count]
- evidence_ref: [count]
- amount_fact: [count]

### amount_fact Status Distribution
```sql
SELECT status, COUNT(*) FROM amount_fact GROUP BY status;
```
Result: [paste result]

## Phase B-3: API Validation

### Scenario 1: A4200_1 Comparison
- Request: [curl command]
- Response: [status code + sample]
- Evidence blocks: [약관/사업방법서/상품요약서 present?]
- amount.status: [UNCONFIRMED?]

### Scenario 2: Meritz Prefix Alias
- Request: [curl command]
- Response: [status code + sample]
- Evidence found: [YES/NO]
- Errors: [NONE/paste errors]

## Completion

**Date**: [timestamp]
**Status**: ✅ COMPLETE / ❌ BLOCKED
**Next Steps**: Re-run Step7 amount extraction (out of scope for 41S)
```

---

## DoD (Definition of Done)

STEP NEXT-41S is COMPLETE when:

1. ✅ All 5 Phase A documents created:
   - `STEP_NEXT_41S_DB_SCHEMA_SNAPSHOT.md`
   - `STEP_NEXT_41S_SSOT_SNAPSHOT.md`
   - `STEP_NEXT_41S_LOADER_BINDING_TRACE.md`
   - `STEP_NEXT_41S_ALIGNMENT_MATRIX.md`
   - `STEP_NEXT_41S_PATH_DECISION.md` (this file)

2. ✅ Phase B execution complete:
   - Loader fixed (evidence_pack → coverage_cards)
   - DB backed up
   - Data truncated + reloaded
   - Row counts verified
   - amount_fact status = ALL UNCONFIRMED

3. ✅ Phase B-3 API validation:
   - 2 scenarios tested (A4200_1 + Meritz prefix)
   - Evidence blocks present
   - No 500 errors
   - 5-block contract maintained

4. ✅ Execution log created:
   - `STEP_NEXT_41S_EXEC_LOG.md`

5. ✅ Git commit:
   - Loader change committed
   - Audit docs committed
   - STATUS.md updated

---

**Phase A-5 Complete**: Path-2 selected with full execution plan.
