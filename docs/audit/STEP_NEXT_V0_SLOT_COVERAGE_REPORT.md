# STEP NEXT-V0: Slot Coverage Audit Report

**Generated**: 2026-01-09 17:33:26

**JSONL Source**: `data/compare_v1/compare_rows_v1.jsonl`

**Total Rows**: 340

**Total Insurers**: 8

**Total Unique Slots**: 8

**Policy Source**: `data/policy/question_card_routing.json`

---

## Executive Summary

This report provides a deterministic audit of slot coverage in `compare_rows_v1.jsonl`.

**Audit Rules**:
- ✅ Slot "present" = non-empty value (not None/""/{}/(])
- ✅ Measurement only (no LLM estimation or imputation)
- ✅ Q12 Premium Gate (G10): FAIL if ANY insurer has missing premium

---

## Q12 Premium Gate (G10) Status

**Premium Slot**: `premium_monthly`

**Gate Status**: **PASS**

**Reason**: All insurers have complete premium data

### Premium Coverage by Insurer

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
| payout_limit | 340 | 0 | 340 | 100.00% |
| entry_age | 340 | 0 | 340 | 100.00% |
| reduction | 340 | 0 | 340 | 100.00% |
| start_date | 340 | 0 | 340 | 100.00% |
| waiting_period | 340 | 0 | 340 | 100.00% |
| exclusions | 340 | 0 | 340 | 100.00% |
| premium_monthly | 0 | 0 | 0 | 0.00% |

---

## Global Slot Coverage - BOTTOM 20 (by Presence Ratio)

| Slot | Present | Missing | Total | Ratio |
|------|---------|---------|-------|-------|
| mandatory_dependency | 340 | 0 | 340 | 100.00% |
| payout_limit | 340 | 0 | 340 | 100.00% |
| entry_age | 340 | 0 | 340 | 100.00% |
| reduction | 340 | 0 | 340 | 100.00% |
| start_date | 340 | 0 | 340 | 100.00% |
| waiting_period | 340 | 0 | 340 | 100.00% |
| exclusions | 340 | 0 | 340 | 100.00% |
| premium_monthly | 0 | 0 | 0 | 0.00% |

---

## Missing Slots by Insurer (TOP 20)

| Insurer | Slot | Missing Count |
|---------|------|---------------|

---

## Policy-Expected Slots with Zero Occurrence

The following slots are expected by policy but have ZERO occurrences in JSONL:

- `premium_monthly`

---

## Metadata

- **Script**: `tools/audit/slot_coverage_audit.py`
- **Execution Time**: 2026-01-09 17:33:26
- **JSONL Rows**: 340
- **Insurers**: 8
- **Unique Slots**: 8
- **Premium Gate (Q12)**: **PASS**

