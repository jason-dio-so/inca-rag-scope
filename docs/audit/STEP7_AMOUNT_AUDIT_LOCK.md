# ⛔️ DEPRECATED — DO NOT USE ⛔️

**STEP NEXT-18X-SSOT-FINAL-A**: This document is obsolete.

**Current SSOT**:
- Coverage: `data/compare/*_coverage_cards.jsonl`
- Audit: `docs/audit/AMOUNT_STATUS_DASHBOARD.md`

**Deprecated Workflow**: step10_audit freeze/lock/preserve workflow is no longer used.

---

# Step7 Amount Pipeline LOCK (Historical Record Only)

**Status**: 🔒 LOCKED (DEPRECATED)
**Lock Date**: 2025-12-29
**Frozen Commit**: `c6fad903c4782c9b78c44563f0f47bf13f9f3417`
**Freeze Tag**: `freeze/pre-10b2g2-20251229-024400`
**Audit Report**: ~~reports/step7_gt_audit_all_20251229-025007.md~~ (removed)

---

## 🎯 Lock Purpose

The Step7 amount pipeline is **permanently locked** to prevent rework and ensure production stability. This lock:

1. **Freezes** the amount extraction logic at the current commit
2. **Prevents** modifications to Step7 amount-related code
3. **Enforces** audit compliance before DB loading
4. **Preserves** audit reports as immutable evidence

---

## 📋 Lock Rules

### ✅ ALLOWED

- **READ** Step7 amount results (data/compare/*_coverage_cards.jsonl)
- **AUDIT** using frozen audit scripts
- **LOAD** to DB after audit PASS
- **QUERY** amount_fact table
- **REPORT** on existing amounts

### ❌ PROHIBITED

- **MODIFY** Step7 amount extraction logic
- **TUNE** amount parsing/inference rules
- **ADD** new amount sources without new version
- **CHANGE** type-C guardrails (보험가입금액 prohibition)
- **LOAD** to DB without audit PASS
- **DELETE** frozen audit reports

---

## 🔐 Audit Requirements

Before loading Step7 amounts to DB:

### 1. Run Audit Script

```bash
python pipeline/step10_audit/audit_step7_amount_gt.py
```

**Pass Criteria**:
- `MISMATCH_VALUE = 0` (no amount value errors)
- `mismatch_type_count >= 0` (type errors allowed but tracked)
- All 8 insurers audited

### 2. Preserve Audit Metadata (DEPRECATED)

~~python -m pipeline.step10_audit.preserve_audit_run~~ (removed)

**Current SSOT**: `docs/audit/AMOUNT_STATUS_DASHBOARD.md`

### 3. Load to DB

```bash
python -m apps.loader.step9_loader --mode upsert
```

**Effect**:
- Upserts `amount_fact` table (coverage_instance_id → amount)
- Preserves evidence linkage (evidence_ref)
- Idempotent (safe to re-run)

---

## 📊 Frozen Audit Results

**Latest Audit**: `step7_gt_audit_all_20251229-025007`

| Metric | Value |
|--------|-------|
| Total Rows | 240 |
| Insurers | 8 (samsung, hyundai, lotte, db, kb, meritz, hanwha, heungkuk) |
| MISMATCH_VALUE | **0** ✅ |
| MISMATCH_TYPE | 0 ✅ |
| Audit Status | **PASS** ✅ |

**Frozen Reports** (REMOVED):
- ~~`reports/step7_gt_audit_all_20251229-025007.json`~~ (REMOVED)
- ~~`reports/step7_gt_audit_all_20251229-025007.md`~~ (REMOVED)

---

## 🚦 PR Merge Checklist

Before merging PRs to `master`, ensure:

- [ ] **Audit script passes** (`MISMATCH_VALUE = 0`)
- [ ] **Type-C guardrails active** (보험가입금액 prohibited)
- [ ] **Freeze tag exists** (`freeze/pre-10b2g2-*`)
- [ ] **Audit metadata preserved** (audit_runs table)
- [ ] **No modifications to**:
  - `pipeline/step7_amount/`
  - `pipeline/step7_amount_integration/`
  - Amount extraction logic in step9_loader.py

**Enforcement**: CI should block PRs that modify locked paths without version bump.

---

## 🔄 Future Enhancements

New amount features (e.g., inference, fallback sources) require:

1. **New version** (e.g., `step7_amount_v2/`)
2. **New freeze tag** (e.g., `freeze/v2-*`)
3. **New audit run** with PASS status
4. **Migration plan** for existing data

**DO NOT** modify locked v1 pipeline.

---

## 📚 Related Documents

- **Audit Script**: `pipeline/step10_audit/audit_step7_amount_gt.py`
- **DB Loader**: `apps/loader/step9_loader.py` (load_amount_fact method)
- **Schema**: `pipeline/step10_audit/create_audit_runs_table.sql`
- **Preservation**: `pipeline/step10_audit/preserve_audit_run.py`
- **Type Guardrails**: `docs/guardrails/STEP7_TYPE_AWARE_GUARDRAILS.md`

---

## 🔖 Git Tags

Freeze tags mark immutable snapshots:

```bash
# List all freeze tags
git tag --list 'freeze/pre-10b2g2-*'

# Current frozen snapshot
freeze/pre-10b2g2-20251229-024400
```

**Tag Format**: `freeze/pre-{issue-id}-{timestamp}`

---

## 📝 Version History

| Date | Commit | Event | Status |
|------|--------|-------|--------|
| 2025-12-29 | c6fad90 | Initial lock | LOCKED ✅ |

---

**Lock Owner**: Pipeline Team
**Next Review**: On demand (new version proposal only)
