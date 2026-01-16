# A4104_1 FAILURE REPORT

**Date:** 2026-01-16
**Status:** FAIL
**Action:** Canonical SPLIT attempted, both branches failed validation

---

## SPLIT DECISION

| Original | Split To | Insurer | Coverage Name |
|----------|----------|---------|---------------|
| A4104_1 | A4104_1A | N08, N02, N05, N09, N13 | 특정심장질환진단비 (급성심근경색 등) |
| A4104_1 | A4104_1B | N10 | 부정맥진단비 (I49) |

---

## A4104_1A RESULTS (N08)

**chunks:** 217
**doc_type:** 약관(128) + 사업방법서(42) + 요약서(47)
**evidence:** FOUND=2, NOT_FOUND=1

| slot_key | status |
|----------|--------|
| exclusions | FOUND |
| subtype_coverage_map | FOUND |
| waiting_period | **NOT_FOUND** |

**Status:** FAIL (missing: waiting_period)

---

## A4104_1B RESULTS (N10)

**chunks:** 42
**doc_type:** 약관(27) + 사업방법서(5) + 요약서(10)
**evidence:** FOUND=0, NOT_FOUND=3

| slot_key | status |
|----------|--------|
| waiting_period | NOT_FOUND |
| exclusions | NOT_FOUND |
| subtype_coverage_map | NOT_FOUND |

**Status:** FAIL (all slots failed)

---

## ROOT CAUSE

1. **A4104_1A:** Insufficient waiting_period evidence in N08 heart disease coverage
2. **A4104_1B:** Arrhythmia (I49) canonical mismatch - too few relevant chunks (42 total)

---

## DB STATE

```sql
-- coverage_canonical
A4104_1A: 특정심장질환진단비
A4104_1B: 부정맥진단비

-- coverage_mapping_ssot
N08 → A4104_1A
N10 → A4104_1B

-- coverage_chunk
A4104_1A: 217 chunks (N08)
A4104_1B: 42 chunks (N10)

-- evidence_slot
A4104_1A: 2 slots (N08)
A4104_1B: 0 slots (N10)
```

---

## ACTIONS TAKEN

- [x] SPLIT A4104_1 into A4104_1A / A4104_1B
- [x] Created 2 profiles in coverage_profiles.py
- [x] Updated coverage_mapping_ssot
- [x] Generated chunks + evidence for both

---

## ACTIONS BLOCKED

- ❌ Gate relaxation
- ❌ Profile modification to force FOUND
- ❌ Anchor keyword expansion
- ❌ N10 absorption into A4104_1A

---

## FINAL STATUS

**A4104_1:** BLOCKED (cannot achieve 2-insurer baseline with N08, N10)
