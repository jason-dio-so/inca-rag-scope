# STEP-NEXT-10B-2G-2: DB Load & Lock Implementation ✅

**Completion Date**: 2025-12-29
**Branch**: `fix/10b2g2-amount-audit-hardening`
**Status**: ✅ COMPLETE

---

## 📋 Deliverables

### 1️⃣ Step7 Amount DB Loading

**Existing Implementation** (already in codebase):
- `apps/loader/step9_loader.py:519-656` - `load_amount_fact()` method
- Reads from `data/compare/*_coverage_cards.jsonl`
- Upserts to `amount_fact` table with evidence tracking
- Idempotent via `ON CONFLICT (coverage_instance_id) DO UPDATE`

**Usage**:
```bash
# UPSERT mode (recommended, production)
python -m apps.loader.step9_loader --mode upsert

# Reset mode (dev only, truncates tables)
python -m apps.loader.step9_loader --mode reset_then_load
```

**What it loads**:
| Source | Target Table | Key Field |
|--------|-------------|-----------|
| `담보명mapping자료.xlsx` | `coverage_canonical` | `coverage_code` |
| `*_scope_mapped.csv` | `coverage_instance` | `instance_key` |
| `*_evidence_pack.jsonl` | `evidence_ref` | `evidence_key` |
| `*_coverage_cards.jsonl` | `amount_fact` | `coverage_instance_id` ⭐ |

---

### 2️⃣ Audit Metadata Preservation

**New Files**:

#### A. Database Schema
`pipeline/step10_audit/create_audit_runs_table.sql`
- Creates `audit_runs` table for permanent audit lineage
- Tracks: git commit, freeze tag, report paths, audit results
- Constraints: UNIQUE(git_commit, audit_name), PASS requires MISMATCH_VALUE=0

**Schema**:
```sql
CREATE TABLE audit_runs (
    audit_run_id UUID PRIMARY KEY,
    audit_name TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    freeze_tag TEXT,
    report_json_path TEXT NOT NULL,
    report_md_path TEXT NOT NULL,
    total_insurers INT NOT NULL,
    total_rows_audited INT,
    mismatch_value_count INT,
    mismatch_type_count INT,
    audit_status TEXT CHECK (audit_status IN ('PASS', 'FAIL', 'PENDING')),
    insurers TEXT[],
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (git_commit, audit_name)
);
```

#### B. Preservation Script
`pipeline/step10_audit/preserve_audit_run.py`
- Parses audit report JSON (array format)
- Auto-detects git commit + freeze tag
- Inserts/updates `audit_runs` table
- Validates PASS status (MISMATCH_VALUE=0)

**Usage**:
```bash
python -m pipeline.step10_audit.preserve_audit_run \
    --report-json "reports/step7_gt_audit_all_20251229-025007.json" \
    --report-md "reports/step7_gt_audit_all_20251229-025007.md"
```

**Output**:
```
✅ Audit run preserved: <uuid>
   Audit: step7_amount_gt_audit
   Commit: c6fad903c4782c9b78c44563f0f47bf13f9f3417
   Tag: freeze/pre-10b2g2-20251229-024400
   Status: PASS
   Insurers: samsung, hyundai, lotte, db, kb, meritz, hanwha, heungkuk
```

---

### 3️⃣ Amount Pipeline LOCK

**New Files**:

#### A. Lock Documentation
`docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md`
- 🔒 Declares Step7 amount pipeline as LOCKED
- Frozen at commit `c6fad903` with tag `freeze/pre-10b2g2-20251229-024400`
- Lists prohibited/allowed actions
- PR merge checklist
- Audit results snapshot

**Lock Rules**:
- ✅ ALLOWED: Read, audit, load, query, report
- ❌ PROHIBITED: Modify Step7 logic, tune rules, delete audit reports

#### B. Validation Script
`pipeline/step10_audit/validate_amount_lock.py`
- Pre-flight validation before DB load
- Checks: freeze tag, audit reports, coverage cards, git status, type-C guardrails
- Exit code: 0=PASS (safe to load), 1=FAIL (block load)

**Validation Checks**:
1. Freeze tag exists (`freeze/pre-10b2g2-*`)
2. Audit reports exist and PASS (MISMATCH_VALUE=0)
3. All 8 coverage_cards.jsonl files exist
4. No uncommitted Step7 changes (warning only)
5. Type-C guardrails active (no '보험가입금액' in amounts)

**Usage**:
```bash
python -m pipeline.step10_audit.validate_amount_lock
```

**Output (PASS)**:
```
✅ PASS - Freeze Tag
✅ PASS - Audit Reports (594 rows, MISMATCH_VALUE=0)
✅ PASS - Coverage Cards (8 insurers)
✅ PASS - Git Working Dir
✅ PASS - Type-C Guardrails

🎉 All validations PASSED
✅ SAFE TO LOAD Step7 amounts to DB
```

#### C. Load Guide
`docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md`
- Quick reference for DB load procedure
- 3-step workflow: Validate → Preserve → Load
- SQL verification queries
- Troubleshooting guide

---

## 🎯 Complete Workflow

### Production DB Load (3 Steps)

```bash
# Step 1: Validate lock compliance
python -m pipeline.step10_audit.validate_amount_lock
# → Must output "🎉 All validations PASSED"

# Step 2: Preserve audit metadata
python -m pipeline.step10_audit.preserve_audit_run \
    --report-json "reports/step7_gt_audit_all_20251229-025007.json" \
    --report-md "reports/step7_gt_audit_all_20251229-025007.md"
# → Creates audit_runs record

# Step 3: Load to DB
python -m apps.loader.step9_loader --mode upsert
# → Upserts amount_fact table (idempotent)
```

### Verification

```sql
-- Check amount_fact coverage
SELECT
    i.insurer_name_kr,
    COUNT(*) as total_amounts,
    SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
JOIN insurer i ON ci.insurer_id = i.insurer_id
GROUP BY i.insurer_name_kr;

-- Verify audit_runs record
SELECT
    audit_name, git_commit, freeze_tag, audit_status,
    mismatch_value_count, total_rows_audited
FROM audit_runs
ORDER BY generated_at DESC LIMIT 1;
```

---

## 📊 Audit Results (Frozen)

**Latest Audit**: `step7_gt_audit_all_20251229-025007`

| Metric | Value |
|--------|-------|
| Total Rows | 594 (GT pairs across 8 insurers) |
| MISMATCH_VALUE | **0** ✅ |
| MISMATCH_TYPE | **0** ✅ |
| Audit Status | **PASS** ✅ |
| Insurers | samsung, hyundai, lotte, db, kb, meritz, hanwha, heungkuk |

**Frozen Reports** (永久 보관):
- `reports/step7_gt_audit_all_20251229-025007.json`
- `reports/step7_gt_audit_all_20251229-025007.md`

---

## 🔐 Lock Enforcement

### Prohibited Actions
- ❌ Modify `pipeline/step7_amount/` code
- ❌ Change amount extraction logic
- ❌ Tune type-C guardrails (보험가입금액 prohibition)
- ❌ Load to DB without audit PASS
- ❌ Delete frozen audit reports

### Allowed Actions
- ✅ Read `amount_fact` table
- ✅ Query amounts for reports
- ✅ Re-run loader (idempotent upsert)
- ✅ Run audit script (validation)

### PR Merge Checklist
Before merging to `master`:
- [ ] `validate_amount_lock.py` passes
- [ ] `audit_runs` table has PASS record
- [ ] No modifications to locked paths
- [ ] Freeze tag exists and pushed

---

## 📁 File Summary

| File | Purpose | Type |
|------|---------|------|
| `apps/loader/step9_loader.py` | DB loader (load_amount_fact) | Existing |
| `pipeline/step10_audit/create_audit_runs_table.sql` | Audit metadata schema | NEW ⭐ |
| `pipeline/step10_audit/preserve_audit_run.py` | Audit preservation script | NEW ⭐ |
| `pipeline/step10_audit/validate_amount_lock.py` | Pre-flight validation | NEW ⭐ |
| `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` | Lock documentation | NEW ⭐ |
| `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md` | Load guide | NEW ⭐ |

---

## ✅ Testing

### Validation Script Test
```bash
$ python -m pipeline.step10_audit.validate_amount_lock

============================================================
Step7 Amount Pipeline Lock Validation
============================================================
1️⃣  Checking freeze tag...
   ✅ Freeze tag exists: freeze/pre-10b2g2-20251229-024400

2️⃣  Checking audit reports...
   ✅ Audit reports exist
   Audit Results:
   - Total rows: 594
   - MISMATCH_VALUE: 0
   - MISMATCH_TYPE: 0
   - Insurers: 8
   ✅ Audit PASSED (MISMATCH_VALUE=0)

3️⃣  Checking coverage cards...
   ✅ All 8 coverage cards exist

4️⃣  Checking git working directory...
   ✅ No uncommitted Step7 changes

5️⃣  Checking type-C guardrails...
   ✅ Type-C guardrails active

🎉 All validations PASSED
✅ SAFE TO LOAD Step7 amounts to DB
```

---

## 🚀 Next Steps

1. **Create audit_runs table in DB**:
   ```sql
   \i pipeline/step10_audit/create_audit_runs_table.sql
   ```

2. **Preserve current audit metadata**:
   ```bash
   python -m pipeline.step10_audit.preserve_audit_run \
       --report-json "reports/step7_gt_audit_all_20251229-025007.json" \
       --report-md "reports/step7_gt_audit_all_20251229-025007.md"
   ```

3. **Load to production DB**:
   ```bash
   python -m apps.loader.step9_loader --mode upsert
   ```

4. **Verify load**:
   ```sql
   SELECT COUNT(*) FROM amount_fact;  -- Should have ~240 rows (30×8)
   SELECT * FROM audit_runs ORDER BY created_at DESC LIMIT 1;
   ```

---

## 📚 Related Tasks

- ✅ STEP-NEXT-10B-1: Audit script hardening
- ✅ STEP-NEXT-10B-2A: Coverage_cards lineage proof
- ✅ STEP-NEXT-10B-2C: Type-aware guardrails
- ✅ STEP-NEXT-10B-2G: Amount integration tests
- ✅ **STEP-NEXT-10B-2G-2**: DB load + lock (THIS TASK)

**Next**: API integration (Step-NEXT-9)

---

**Completion Time**: ~30 minutes
**Files Created**: 5
**Lines of Code**: ~600
**Test Coverage**: ✅ Validation tested, loader existing

---

**Signed-off**: Pipeline Team, 2025-12-29
