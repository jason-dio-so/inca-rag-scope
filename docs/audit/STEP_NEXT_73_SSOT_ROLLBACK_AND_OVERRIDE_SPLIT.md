# STEP NEXT-73: SSOT Rollback + Local Override Split + Zero-Tolerance Gate

**Date**: 2026-01-08
**Author**: Claude (STEP NEXT-73 execution)
**Status**: ✅ COMPLETED

---

## Executive Summary

STEP NEXT-73 rolled back unauthorized SSOT modifications and implemented a zero-tolerance gate system to prevent future SSOT pollution. The system now enforces strict separation between approved SSOT mappings and unapproved candidate mappings.

---

## 1. Problem Statement

STEP NEXT-72 analysis produced high-confidence mapping candidates that were **incorrectly merged directly into the SSOT Excel file** (`담보명mapping자료.xlsx`) without customer approval. This violated the constitutional principle that SSOT changes require explicit authorization.

**Impact**:
- SSOT integrity compromised
- No audit trail for what was customer-approved vs. auto-suggested
- Risk of incorrect mappings in production

---

## 2. Solution Architecture

### 2.1 SSOT Rollback

**Action**: Restored `data/sources/mapping/담보명mapping자료.xlsx` to last committed state.

**Verification**:
```bash
# Pre-rollback
sha256: 920932ae7e4b242243c57d066a9db632c66af3493a981cef253b50336a3ef9ce
Rows: (modified, unknown count)

# Post-rollback
sha256: 8de2aeed81f83415377f2bf9e662ea0cd8eb72445a38c4d1d59664e05cd3a0f4
Rows: 288 (confirmed original)
```

### 2.2 Local Override Layer (Candidate Storage)

**New file**: `data/sources/mapping/local_alias_overrides.csv`

**Purpose**: Store PROPOSED mappings from STEP NEXT-72 analysis without contaminating SSOT.

**Schema**:
```csv
insurer_key,product_key,variant_key,coverage_name_normalized,suggested_coverage_code,resolution_type,confidence,reason,source_ref
```

**Contents**: 23 high-confidence alias candidates (extracted from `unanchored_backlog_v2.csv`)

**Resolution types**:
- `ALIAS_EXISTING`: Candidate matches existing canonical code (high confidence)
- `INTENTIONAL_UNMAPPED`: Likely intentional unmapped (not a mapping gap)

**File header warning**:
```
# ⚠️ This file contains PROPOSED mappings from STEP NEXT-72 unanchored backlog analysis.
# ⚠️ These are NOT approved for production use without customer confirmation.
# ⚠️ DO NOT merge these into the SSOT Excel file without explicit authorization.
```

### 2.3 Zero-Tolerance Gate Implementation

#### Gate Architecture

**Default mode**: `approved` (SSOT Excel only)
**Testing mode**: `local` (SSOT + local overrides, blocked by default)

#### Modified Files

**1. `pipeline/step2_canonical_mapping/run.py`**

Added CLI argument:
```bash
python -m pipeline.step2_canonical_mapping.run --mapping-source {approved|local}
```

Default: `approved` (production-safe)

**Gate enforcement logic**:
```python
if args.mapping_source == 'approved':
    # Use SSOT Excel ONLY
    # Block local_alias_overrides.csv even if present
    print("🔒 Local overrides: BLOCKED (file exists but not loaded)")

elif args.mapping_source == 'local':
    # Require explicit opt-in
    # Print warnings
    # Exit with error (integration not yet implemented)
```

**2. `tools/run_pipeline.py`**

Updated `run_step2b()` signature:
```python
def run_step2b(self, mapping_source: str = "approved") -> Dict:
```

**Receipt tracking**: Added `mapping_source` field to execution receipt for full audit trail.

---

## 3. Verification Results

### 3.1 SSOT Rollback Verification

✅ **Excel restored**: `8de2aeed81f83415` (288 rows)
✅ **Git status**: `data/sources/mapping/담보명mapping자료.xlsx` clean (no modifications)

### 3.2 Local Override Layer

✅ **File created**: `data/sources/mapping/local_alias_overrides.csv`
✅ **Row count**: 24 (1 header + 23 candidate mappings)
✅ **Source traceability**: All candidates link back to `unanchored_backlog_v2.csv`

### 3.3 Gate Enforcement Test (Approved Mode)

**Command**:
```bash
python3 tools/run_pipeline.py --stage step2b
```

**Output**:
```
🚦 Mapping source mode: APPROVED
[GATE ENFORCEMENT] Mode: APPROVED (SSOT Excel only)
  ✅ Mapping source: 담보명mapping자료.xlsx
  🔒 Local overrides: BLOCKED (file exists but not loaded)
```

**Mapping results** (approved SSOT baseline):
```
Total input: 340 entries
Total mapped: 278 entries (81.8%)
Total unmapped: 62 entries (18.2%)
```

**Per-insurer unmapped counts**:
- SAMSUNG: 5
- DB (over41): 2
- DB (under40): 2
- HANWHA: 5
- HEUNGKUK: 4
- HYUNDAI: 12
- KB: 13
- LOTTE (female): 5
- LOTTE (male): 5
- MERITZ: 9

**Receipt verification**:
```bash
$ cat docs/audit/run_receipt.json | python3 -c "import json, sys; d = json.load(sys.stdin); print('mapping_source:', d[-1].get('mapping_source'))"
mapping_source: approved
```

✅ **Gate enforced**: Local overrides NOT loaded
✅ **Receipt logged**: `mapping_source: approved` recorded
✅ **Baseline restored**: 81.8% mapping rate matches pre-STEP-72 baseline

---

## 4. Operational Rules

### 4.1 Production Execution (MANDATORY)

**Always use approved mode** (default):
```bash
python3 tools/run_pipeline.py --stage step2b
```

**Never use**:
```bash
python3 -m pipeline.step2_canonical_mapping.run  # ❌ Direct execution bypasses gate logging
```

### 4.2 Local Mode (Testing/Review Only)

**Not yet implemented** - requires:
1. CSV overlay merge logic in `canonical_mapper.py`
2. Conflict resolution rules (override vs. SSOT precedence)
3. Customer approval workflow

**Current behavior**: Exit with error if `--mapping-source local` specified.

### 4.3 SSOT Update Workflow

To promote candidates from `local_alias_overrides.csv` to SSOT:

1. **Customer review**: Share candidates for approval
2. **Manual Excel update**: Authorized person adds approved mappings to `담보명mapping자료.xlsx`
3. **Commit with audit**: Git commit with clear message (e.g., "feat: add 15 approved alias mappings from STEP NEXT-72")
4. **Remove from local overrides**: Delete promoted entries from CSV
5. **Verify**: Re-run `--mapping-source approved` to confirm new baseline

---

## 5. File Inventory

### Modified Files
- `pipeline/step2_canonical_mapping/run.py` (gate enforcement, CLI args)
- `tools/run_pipeline.py` (mapping source parameter, receipt tracking)

### New Files
- `data/sources/mapping/local_alias_overrides.csv` (23 candidate mappings)
- `docs/audit/STEP_NEXT_73_SSOT_ROLLBACK_AND_OVERRIDE_SPLIT.md` (this document)

### Restored Files
- `data/sources/mapping/담보명mapping자료.xlsx` (git restore to sha256: `8de2aeed`)

---

## 6. Completion Checklist

- [x] (1) Excel rolled back to pre-STEP-72 state (sha256: `8de2aeed`, 288 rows)
- [x] (2) `local_alias_overrides.csv` created (23 candidate rows)
- [x] (3) Step2-b gate implemented (`--mapping-source approved` default)
- [x] (4) Gate enforcement verified (approved mode blocks local file)
- [x] (5) Receipt tracking includes `mapping_source` field
- [x] (6) Baseline mapping rate restored (81.8% mapped, 62 unmapped)
- [x] (7) Audit documentation complete (this file)

---

## 7. Key Metrics

| Metric | Value |
|--------|-------|
| SSOT Excel SHA256 | `8de2aeed81f83415` |
| SSOT Excel Rows | 288 |
| Local Override Candidates | 23 |
| Baseline Mapping Rate | 81.8% |
| Baseline Unmapped | 62 entries |
| Default Gate Mode | `approved` (SSOT only) |

---

## 8. Risks Mitigated

✅ **SSOT pollution**: Unapproved mappings cannot reach production
✅ **Accidental promotion**: Local mode requires explicit opt-in (and currently errors)
✅ **Audit trail**: Every execution logs `mapping_source` in receipt
✅ **Rollback safety**: SSOT restored to known-good state (pre-STEP-72)

---

## 9. Next Steps (Optional, Not in Scope)

1. **Implement local overlay merge logic** (if customer requests testing mode)
2. **Customer review workflow** for alias candidates in `local_alias_overrides.csv`
3. **Promote approved mappings** to SSOT Excel (manual, authorized only)

---

## Constitutional Compliance

✅ **Zero-Tolerance Enforcement**: Default mode prevents SSOT pollution
✅ **Single Entry Point**: `tools/run_pipeline.py` is ONLY execution path (as documented in CLAUDE.md)
✅ **Receipt Logging**: Every run generates audit receipt with `mapping_source`
✅ **No LLM/Inference**: All mapping logic remains deterministic

---

**STEP NEXT-73 Status**: ✅ **COMPLETED**
