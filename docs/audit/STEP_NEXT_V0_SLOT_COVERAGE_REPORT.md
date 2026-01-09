# STEP NEXT-V0: Slot Coverage Audit Report

**Generated**: 2026-01-09 17:51:29

**JSONL Source**: `data/compare_v1/compare_rows_v1.jsonl`

**Total Rows**: 340

**Total Insurers**: 8

**Total Unique Slots**: 7

**Policy Source**: `data/policy/question_card_routing.json`

---

## Executive Summary

This report provides a deterministic audit of slot coverage in `compare_rows_v1.jsonl`.

**Audit Rules**:
- ✅ Slot "present" = non-empty value (not None/""/{}/(])
- ✅ Measurement only (no LLM estimation or imputation)
- ✅ Q12 Premium Gate (G10): FAIL if ANY insurer has missing premium

---

## Runtime-Only Slots (Not in JSONL)

**Important**: Some slots are NOT extracted from documents but injected at runtime via SSOT.

**Runtime-Only Slot**: `premium_monthly`

**JSONL Coverage**: 0% (Expected - this is NOT a document slot)

**Note**: premium_monthly is a runtime-only slot (not in JSONL). Use premium_runtime_audit.py for Q12 G10 gate validation.

### Q12 Premium Gate (G10) - Runtime Validation Required

**Q12 Readiness Status**: ⚠️ **NOT DETERMINED** (requires Premium Runtime Audit)

**Why**: `premium_monthly` is injected at runtime from Premium SSOT, not extracted from documents.

**Action Required**: Run `tools/audit/premium_runtime_audit.py` to validate Q12 G10 gate compliance.

### Premium Slot in JSONL (for reference)

| Insurer | Present | Missing | Total | Ratio |
|---------|---------|---------|-------|-------|
| db | 0 | 0 | 0 | 0.00% |
| hanwha | 0 | 0 | 0 | 0.00% |
| heungkuk | 0 | 0 | 0 | 0.00% |
| hyundai | 0 | 0 | 0 | 0.00% |
| kb | 0 | 0 | 0 | 0.00% |
| lotte | 0 | 0 | 0 | 0.00% |
| meritz | 0 | 0 | 0 | 0.00% |
| samsung | 0 | 0 | 0 | 0.00% |

**Expected Result**: All 0 (premium is runtime-only)

---

## Insurer-Level Statistics

| Insurer | Row Count | Unique Slots (Present) |
|---------|-----------|------------------------|
| db | 62 | 7 |
| hanwha | 33 | 7 |
| heungkuk | 36 | 7 |
| hyundai | 37 | 7 |
| kb | 43 | 7 |
| lotte | 60 | 7 |
| meritz | 37 | 7 |
| samsung | 32 | 7 |

---

## Global Slot Coverage - TOP 20 (by Presence Ratio)

| Slot | Present | Missing | Total | Ratio |
|------|---------|---------|-------|-------|
| mandatory_dependency | 340 | 0 | 340 | 100.00% |
| entry_age | 340 | 0 | 340 | 100.00% |
| reduction | 340 | 0 | 340 | 100.00% |
| exclusions | 340 | 0 | 340 | 100.00% |
| start_date | 340 | 0 | 340 | 100.00% |
| payout_limit | 340 | 0 | 340 | 100.00% |
| waiting_period | 340 | 0 | 340 | 100.00% |

---

## Global Slot Coverage - BOTTOM 20 (by Presence Ratio)

| Slot | Present | Missing | Total | Ratio |
|------|---------|---------|-------|-------|
| mandatory_dependency | 340 | 0 | 340 | 100.00% |
| entry_age | 340 | 0 | 340 | 100.00% |
| reduction | 340 | 0 | 340 | 100.00% |
| exclusions | 340 | 0 | 340 | 100.00% |
| start_date | 340 | 0 | 340 | 100.00% |
| payout_limit | 340 | 0 | 340 | 100.00% |
| waiting_period | 340 | 0 | 340 | 100.00% |

---

## Missing Slots by Insurer (TOP 20)

| Insurer | Slot | Missing Count |
|---------|------|---------------|

---

## Metadata

- **Script**: `tools/audit/slot_coverage_audit.py`
- **Execution Time**: 2026-01-09 17:51:29
- **JSONL Rows**: 340
- **Insurers**: 8
- **Unique Document Slots**: 7
- **Runtime-Only Slots**: `premium_monthly` (see Premium Runtime Audit)
- **Q12 Readiness**: ⚠️ NOT DETERMINED (Premium Runtime Audit required)

