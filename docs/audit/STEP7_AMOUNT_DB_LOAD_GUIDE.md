# Step7 Amount DB Load Guide

**Quick Reference**: How to load Step7 amount results to DB with full audit compliance

---

## 📋 Prerequisites

1. All 8 insurers processed through Step7
2. Coverage cards exist: `data/compare/*_coverage_cards.jsonl`
3. Audit passed: `MISMATCH_VALUE = 0`
4. Freeze tag exists: `freeze/pre-10b2g2-*`

---

## 🚀 Load Procedure (3 Steps)

### Step 1: Validate Lock Compliance

```bash
python -m pipeline.step10_audit.validate_amount_lock
```

**Expected Output**:
```
✅ PASS - Freeze Tag
✅ PASS - Audit Reports
✅ PASS - Coverage Cards
✅ PASS - Git Working Dir
✅ PASS - Type-C Guardrails

🎉 All validations PASSED
✅ SAFE TO LOAD Step7 amounts to DB
```

**If FAILED**: Fix issues before proceeding. DO NOT load.

---

### Step 2: Preserve Audit Metadata

```bash
python -m pipeline.step10_audit.preserve_audit_run \
    --report-json "reports/step7_gt_audit_all_20251229-025007.json" \
    --report-md "reports/step7_gt_audit_all_20251229-025007.md"
```

**What it does**:
- Creates `audit_runs` table record
- Links git commit + freeze tag
- Stores audit results summary
- Enables lineage tracking

**Expected Output**:
```
✅ Audit run preserved: <uuid>
   Audit: step7_amount_gt_audit
   Commit: c6fad903c4782c9b78c44563f0f47bf13f9f3417
   Tag: freeze/pre-10b2g2-20251229-024400
   Status: PASS
   Insurers: samsung, hyundai, lotte, db, kb, meritz, hanwha, heungkuk
```

---

### Step 3: Load to DB

```bash
# Option A: UPSERT mode (recommended, idempotent)
python -m apps.loader.step9_loader --mode upsert

# Option B: Reset then load (DEV ONLY - truncates tables!)
python -m apps.loader.step9_loader --mode reset_then_load
```

**What it loads**:
1. `coverage_canonical` - From mapping Excel
2. `coverage_instance` - From scope_mapped.csv
3. `evidence_ref` - From evidence_pack.jsonl
4. `amount_fact` - From coverage_cards.jsonl ⭐

**Expected Output**:
```
✅ Upserted 240 amount facts for all insurers
   (created X evidence_ref entries, skipped Y)
```

---

## 📊 Verify Load Success

```sql
-- Check amount_fact coverage
SELECT
    i.insurer_name_kr,
    COUNT(*) as total_amounts,
    SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed,
    SUM(CASE WHEN status = 'UNCONFIRMED' THEN 1 ELSE 0 END) as unconfirmed
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
JOIN insurer i ON ci.insurer_id = i.insurer_id
GROUP BY i.insurer_name_kr
ORDER BY i.insurer_name_kr;

-- Verify audit_runs record
SELECT
    audit_name,
    git_commit,
    freeze_tag,
    audit_status,
    mismatch_value_count,
    total_rows_audited,
    generated_at
FROM audit_runs
ORDER BY generated_at DESC
LIMIT 1;
```

**Expected**:
- 8 insurers with amounts
- `CONFIRMED` count matches audit report
- `audit_status = 'PASS'`

---

## 🔐 Lock Enforcement

After loading, Step7 amount pipeline is **LOCKED**:

❌ **Prohibited**:
- Modifying `pipeline/step7_amount/` code
- Changing amount extraction logic
- Tuning type-C guardrails
- Re-running Step7 without version bump

✅ **Allowed**:
- Reading `amount_fact` table
- Querying amounts for reports
- Re-loading (idempotent upsert)

---

## 🔄 Re-Load (Idempotent)

Safe to re-run if needed:

```bash
# Validation + load
python -m pipeline.step10_audit.validate_amount_lock && \
python -m apps.loader.step9_loader --mode upsert
```

**No data loss**: UPSERT mode updates existing records, no truncate.

---

## 🆘 Troubleshooting

### Validation fails: "No freeze tag found"

```bash
# Check if tag exists
git tag --list 'freeze/pre-10b2g2-*'

# If missing, create one
git tag freeze/pre-10b2g2-$(date +%Y%m%d-%H%M%S)
git push origin --tags
```

### Load fails: "Document not found"

Check that metadata tables are populated:
```sql
SELECT COUNT(*) FROM insurer;  -- Should be 8
SELECT COUNT(*) FROM product;  -- Should be 8
SELECT COUNT(*) FROM document; -- Should have proposal docs
```

If empty, run metadata loader first (see Step9 docs).

### Amount status shows UNCONFIRMED

Check evidence_ref linkage:
```sql
SELECT
    ci.coverage_name_raw,
    af.status,
    af.value_text,
    af.evidence_id
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
WHERE af.status = 'UNCONFIRMED'
LIMIT 10;
```

If `evidence_id IS NULL`, check coverage_cards.jsonl has `amount.evidence_ref`.

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `apps/loader/step9_loader.py` | Main DB loader (includes `load_amount_fact`) |
| `pipeline/step10_audit/validate_amount_lock.py` | Pre-flight validation script |
| `pipeline/step10_audit/preserve_audit_run.py` | Audit metadata preservation |
| `pipeline/step10_audit/create_audit_runs_table.sql` | Audit table schema |
| `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` | Lock documentation |

---

**Last Updated**: 2025-12-29
**Frozen Commit**: c6fad903c4782c9b78c44563f0f47bf13f9f3417
