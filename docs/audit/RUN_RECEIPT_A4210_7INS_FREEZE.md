# A4210 7-Insurer Baseline Freeze Receipt

**Date**: 2026-01-16
**Coverage**: A4210 (유사암진단비)
**Insurers**: N01, N02, N03, N05, N08, N10, N13 (7사)
**As of Date**: 2025-11-26
**Status**: ✅ FROZEN

---

## Executive Summary

A4210 (유사암진단비) baseline successfully established with **7 insurers**.

- **FOUND**: 21/21 (7 insurers × 3 slots)
- **Contamination**: 0
- **API**: ✅ 200 OK, returns 7 insurers
- **N09 Status**: DEPRECATED (not a diagnosis benefit, see decision doc)

---

## Background: N09 Exclusion

### Original Plan
Expand A4210 to 8 insurers (N01,N02,N03,N05,N08,N09,N10,N13)

### N09 Failure
**Result**: FOUND=0/3 (complete failure)

**Root Cause**: N09 "유사암진단Ⅱ(양성뇌종양포함)담보" is NOT a diagnosis benefit (진단비), but a **premium waiver benefit** (보험료납입지원).

**Evidence**:
- 349 chunks with "유사암"
- 148 chunks (42%) contain "유사암납입" (premium support)
- 326 chunks (93%) contain "유사암 제외" (exclusion context)
- Only 4 chunks (1%) mention "유사암진단비", all in "(유사암제외)" exclusion phrases

**Action Taken**: Marked N09-A4210 mapping as `status='DEPRECATED'` in coverage_mapping_ssot

**References**:
- `docs/audit/A4210_N09_MAPPING_FAIL_PROOF.md` — Failure evidence
- `docs/audit/A4210_N09_MAPPING_DECISION.md` — Decision rationale

---

## Database State (5433/inca_ssot)

### 1. coverage_mapping_ssot

```sql
SELECT ins_cd, insurer_coverage_name, status
FROM coverage_mapping_ssot
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26'
ORDER BY ins_cd;
```

| ins_cd | insurer_coverage_name | status |
|--------|-----------------------|--------|
| N01 | 유사암진단비 | ACTIVE |
| N02 | 4대유사암진단비(경계성종양) | ACTIVE |
| N03 | 갑상선암·기타피부암·유사암진단비 | ACTIVE |
| N05 | 유사암진단비 | ACTIVE |
| N08 | 유사암 진단비(경계성종양)(1년50%) | ACTIVE |
| N09 | 유사암진단Ⅱ(양성뇌종양포함)담보 | **DEPRECATED** |
| N10 | 유사암진단비 | ACTIVE |
| N13 | 유사암진단비Ⅱ(1년감액지급) | ACTIVE |

**Result**: 7 ACTIVE, 1 DEPRECATED

---

### 2. coverage_chunk

```sql
SELECT ins_cd, COUNT(*) as total_chunks
FROM coverage_chunk
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26'
GROUP BY ins_cd
ORDER BY ins_cd;
```

| ins_cd | total_chunks |
|--------|--------------|
| N01 | 3,433 |
| N02 | 294 |
| N03 | 325 |
| N05 | 229 |
| N08 | 2,554 |
| N09 | 349 |
| N10 | 166 |
| N13 | 187 |

**Total**: 7,537 chunks (includes N09, but N09 not used in evidence/compare)

**Note**: N09 chunks remain in table but are NOT used for evidence/compare due to DEPRECATED status.

---

### 3. evidence_slot

```sql
SELECT
  COUNT(*) as total_slots,
  SUM(CASE WHEN status = 'FOUND' THEN 1 ELSE 0 END) as found_count,
  SUM(CASE WHEN status = 'NOT_FOUND' THEN 1 ELSE 0 END) as not_found_count
FROM evidence_slot
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26';
```

| total_slots | found_count | not_found_count |
|-------------|-------------|-----------------|
| 21 | 21 | 0 |

**Verification**: ✅ FOUND=21/21 (7 insurers × 3 slots)

#### By Insurer

```sql
SELECT ins_cd,
       COUNT(*) as slot_count,
       SUM(CASE WHEN status = 'FOUND' THEN 1 ELSE 0 END) as found
FROM evidence_slot
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26'
GROUP BY ins_cd
ORDER BY ins_cd;
```

| ins_cd | slot_count | found |
|--------|------------|-------|
| N01 | 3 | 3 |
| N02 | 3 | 3 |
| N03 | 3 | 3 |
| N05 | 3 | 3 |
| N08 | 3 | 3 |
| N10 | 3 | 3 |
| N13 | 3 | 3 |

**Verification**: ✅ All 7 insurers have 3/3 FOUND

---

### 4. compare_table_v2

```sql
SELECT table_id, coverage_code, as_of_date,
       jsonb_array_length(payload->'insurer_rows') as insurer_count,
       (payload->'debug'->>'chunk_rowcount_at_generation')::int as chunk_count
FROM compare_table_v2
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26';
```

| table_id | coverage_code | as_of_date | insurer_count | chunk_count |
|----------|---------------|------------|---------------|-------------|
| 18 | A4210 | 2025-11-26 | 7 | 7,537 |

**Verification**: ✅ 1 row exists with 7 insurers

---

## Contamination Scan

```sql
SELECT COUNT(*) as contaminated_slots
FROM evidence_slot
WHERE coverage_code = 'A4210' AND as_of_date = '2025-11-26'
  AND excerpt ~* '통원일당|입원일당|치료일당|일당|상급종합병원|100세만기|90세만기|납입면제|보험료.*납입면제|보장보험료|차회.*이후|면제.*사유|납입을.*면제';
```

**Result**: 0 rows (no contamination) ✅

---

## API Verification

### Command

```bash
curl -s "http://localhost:8000/compare_v2?coverage_code=A4210&as_of_date=2025-11-26&ins_cds=N01,N02,N03,N05,N08,N10,N13" \
| python3 -c 'import json,sys; d=json.load(sys.stdin); print("insurers:", len(d["insurer_rows"])); print("chunk_count:", d.get("debug", {}).get("chunk_rowcount_at_generation"));'
```

### Result

```
insurers: 7
chunk_count: 7537
```

**Status**: ✅ 200 OK, API returns 7 insurers

---

## Profile Configuration

**File**: `tools/coverage_profiles.py`
**Profile ID**: A4210_PROFILE_V1
**Gate Version**: GATE_SSOT_V2_CONTEXT_GUARD

### Anchor Keywords

```python
["유사암", "유사암진단", "유사암진단비", "유사 암", "유사암 진단", "유사암 진단비"]
```

**Note**: Includes whitespace variants to match N08 "유사암 진단비(경계성종양)(1년50%)"

### Required Slots

- `waiting_period`: 면책, 보장개시, 책임개시, 90일, 감액, 지급률, 진단확정
- `exclusions`: 제외, 보장하지, 지급하지, 보상하지, 면책
- `subtype_coverage_map`: 제자리암, 상피내암, 전암, 경계성, 경계성종양, 유사암, 소액암, 기타피부암, 갑상선암, 정의, 범위

---

## Pipeline Execution Log

### Stage 1: Chunks (Previously Completed)

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4210 --as_of_date 2025-11-26 \
  --ins_cds N01,N02,N03,N05,N08,N09,N10,N13 \
  --stage chunks
```

**Result**: 7,537 chunks generated (including N09)

**Log**: `/tmp/a4210_chunks.log`

---

### Stage 2: Evidence (7 insurers only)

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4210 --as_of_date 2025-11-26 \
  --ins_cds N01,N02,N03,N05,N08,N10,N13 \
  --stage evidence
```

**Result**: FOUND=21, NOT_FOUND=0, DROPPED=0 ✅

**Log**: `/tmp/a4210_7ins_evidence.log`

**Summary**:
- N01: 2321/3433 anchor-matched → 3/3 FOUND
- N02: 190/294 anchor-matched → 3/3 FOUND
- N03: 208/325 anchor-matched → 3/3 FOUND
- N05: 139/229 anchor-matched → 3/3 FOUND
- N08: 809/2554 anchor-matched → 3/3 FOUND
- N10: 83/166 anchor-matched → 3/3 FOUND
- N13: 143/187 anchor-matched → 3/3 FOUND

---

### Stage 3: Compare (7 insurers)

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4210 --as_of_date 2025-11-26 \
  --ins_cds N01,N02,N03,N05,N08,N10,N13 \
  --stage compare
```

**Result**: table_id=18 created ✅

**Log**: `/tmp/a4210_7ins_compare.log`

---

## Freeze Rules

1. **NO modifications to**:
   - `tools/coverage_profiles.py` → A4210_PROFILE
   - Anchor keywords (includes whitespace variants)
   - Gate structure (7 gates maintained)
   - Required terms by slot

2. **DB state locked**:
   - coverage_chunk: 7,537 rows (DO NOT regenerate)
   - evidence_slot: 21 rows (FOUND=21)
   - compare_table_v2: table_id=18
   - coverage_mapping_ssot: N09 status=DEPRECATED

3. **N09 Status**:
   - Mapping marked as DEPRECATED (not deleted)
   - Chunks remain in coverage_chunk but not used
   - Can be reactivated if new evidence found

---

## Change Log

### 2026-01-16: Initial 7-Insurer Baseline

**Actions**:
1. Generated chunks for 8 insurers (N01-N13 including N09)
2. N09 failed evidence generation (FOUND=0/3)
3. Investigated N09 failure → confirmed not a diagnosis benefit
4. Marked N09-A4210 mapping as DEPRECATED
5. Re-ran evidence/compare for 7 insurers (excluding N09)
6. Achieved FOUND=21/21, contamination=0

**Files Modified**:
- `tools/coverage_profiles.py`: Added whitespace variants to A4210 anchor keywords
- `coverage_mapping_ssot`: N09-A4210 status='DEPRECATED'

**Files Created**:
- `docs/audit/A4210_N09_MAPPING_FAIL_PROOF.md`
- `docs/audit/A4210_N09_MAPPING_DECISION.md`
- `docs/audit/RUN_RECEIPT_A4210_7INS_FREEZE.md` (this file)

**Commits**:
- `fix(a4210): freeze 7-insurer baseline (exclude N09 mapping anomaly)`

---

## DoD Checklist

- [x] evidence_slot: FOUND=21/21 (7사×3슬롯)
- [x] contamination scan: 0
- [x] compare_table_v2: 7 insurers
- [x] API /compare_v2: 200 OK, returns 7 insurers
- [x] N09 mapping decision documented
- [x] N09 mapping marked as DEPRECATED
- [x] Run receipt created
- [x] Git commit ready

---

**STATUS**: A4210 7-insurer baseline frozen ✅

**Last Verified**: 2026-01-16 17:13
