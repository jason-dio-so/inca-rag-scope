# A4200_1 8-Insurer Baseline Snapshot

**Date**: 2026-01-16
**Coverage**: A4200_1 (암진단비, 유사암제외)
**Insurers**: N01, N02, N03, N05, N08, N09, N10, N13 (8사)
**As of Date**: 2025-11-26
**Status**: ✅ FROZEN

---

## Database State (5433/inca_ssot)

### 1. compare_table_v2

```sql
SELECT table_id, coverage_code, as_of_date,
       jsonb_array_length(payload->'insurer_rows') as insurer_count,
       (payload->'debug'->>'chunk_rowcount_at_generation')::int as chunk_count
FROM compare_table_v2
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26';
```

| table_id | coverage_code | as_of_date | insurer_count | chunk_count |
|----------|---------------|------------|---------------|-------------|
| 17 | A4200_1 | 2025-11-26 | 8 | 5875 |

**Verification**: ✅ 1 row exists with 8 insurers

---

### 2. evidence_slot

```sql
SELECT
  COUNT(*) as total_slots,
  SUM(CASE WHEN status = 'FOUND' THEN 1 ELSE 0 END) as found_count,
  SUM(CASE WHEN status = 'NOT_FOUND' THEN 1 ELSE 0 END) as not_found_count
FROM evidence_slot
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26';
```

| total_slots | found_count | not_found_count |
|-------------|-------------|-----------------|
| 24 | 24 | 0 |

**Verification**: ✅ FOUND=24/24 (8 insurers × 3 slots)

#### By Insurer

```sql
SELECT ins_cd,
       COUNT(*) as slot_count,
       SUM(CASE WHEN status = 'FOUND' THEN 1 ELSE 0 END) as found
FROM evidence_slot
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26'
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
| N09 | 3 | 3 |
| N10 | 3 | 3 |
| N13 | 3 | 3 |

**Verification**: ✅ All 8 insurers have 3/3 FOUND

---

### 3. coverage_chunk

```sql
SELECT ins_cd, COUNT(*) as total_chunks
FROM coverage_chunk
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26'
GROUP BY ins_cd
ORDER BY ins_cd;
```

| ins_cd | total_chunks |
|--------|--------------|
| N01 | 987 |
| N02 | 597 |
| N03 | 627 |
| N05 | 576 |
| N08 | 753 |
| N09 | 793 |
| N10 | 573 |
| N13 | 969 |

**Total**: 5,875 chunks

#### By Insurer and doc_type

```sql
SELECT ins_cd, doc_type, COUNT(*) as chunks
FROM coverage_chunk
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26'
GROUP BY ins_cd, doc_type
ORDER BY ins_cd, doc_type;
```

| ins_cd | doc_type | chunks |
|--------|----------|--------|
| N01 | 가입설계서 | 10 |
| N01 | 사업방법서 | 228 |
| N01 | 약관 | 649 |
| N01 | 요약서 | 100 |
| N02 | 가입설계서 | 15 |
| N02 | 사업방법서 | 172 |
| N02 | 약관 | 349 |
| N02 | 요약서 | 61 |
| N03 | 가입설계서 | 20 |
| N03 | 사업방법서 | 81 |
| N03 | 약관 | 449 |
| N03 | 요약서 | 77 |
| N05 | 가입설계서 | 10 |
| N05 | 사업방법서 | 67 |
| N05 | 약관 | 437 |
| N05 | 요약서 | 62 |
| N08 | 가입설계서 | 9 |
| N08 | 사업방법서 | 122 |
| N08 | 약관 | 495 |
| N08 | 요약서 | 127 |
| N09 | 가입설계서 | 9 |
| N09 | 사업방법서 | 94 |
| N09 | 약관 | 610 |
| N09 | 요약서 | 80 |
| N10 | 가입설계서 | 11 |
| N10 | 사업방법서 | 74 |
| N10 | 약관 | 407 |
| N10 | 요약서 | 81 |
| N13 | 가입설계서 | 14 |
| N13 | 사업방법서 | 130 |
| N13 | 약관 | 704 |
| N13 | 요약서 | 121 |

**Verification**: ✅ All 8 insurers have chunks across 4 doc_types

---

## API Reproduction Command

### One-liner Verification

```bash
curl -s "http://localhost:8000/compare_v2?coverage_code=A4200_1&as_of_date=2025-11-26&ins_cds=N01,N02,N03,N05,N08,N09,N10,N13" \
| python3 -c 'import json,sys; d=json.load(sys.stdin); print("insurers",len(d["insurer_rows"])); print("q12",bool(d.get("q12_report"))); print("q13",bool(d.get("q13_report")));'
```

**Expected Output**:
```
insurers 8
q12 False
q13 False
```

**Verification**: ✅ API returns 8 insurers

### Full Payload Inspection

```bash
curl -s "http://localhost:8000/compare_v2?coverage_code=A4200_1&as_of_date=2025-11-26&ins_cds=N01,N02,N03,N05,N08,N09,N10,N13" | jq '.debug'
```

**Expected**:
```json
{
  "profile_id": "A4200_1_PROFILE_V1",
  "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",
  "chunk_rowcount_at_generation": 5875
}
```

---

## Baseline Characteristics

### Coverage Names by Insurer

| ins_cd | insurer_coverage_name |
|--------|-----------------------|
| N01 | 암진단비(유사암제외) |
| N02 | 암(4대유사암제외)진단비 |
| N03 | 일반암진단비Ⅱ |
| N05 | 암진단비(유사암제외) |
| N08 | 암진단비(유사암제외) |
| N09 | 암진단Ⅱ(유사암제외)담보 |
| N10 | 암진단비(유사암제외) |
| N13 | 암진단비Ⅱ(유사암제외) |

### GATE 5 Token Extraction

**Critical Cases** (fixed by patch):
- **N03**: "일반암진단비Ⅱ" → `["일반암진단비"]` (len=6, substring match: "암진단비")
- **N09**: "암진단Ⅱ(유사암제외)담보" → `["암진단"]` (after stripping "담보" suffix)

### Profile Configuration

**File**: `tools/coverage_profiles.py`
**Profile ID**: A4200_1_PROFILE_V1
**Gate Version**: GATE_SSOT_V2_CONTEXT_GUARD

**Anchor Keywords**:
```python
["암", "암진단", "암진단비", "암 진단", "암 진단비", "일반암"]
```

**Required Slots**:
- `waiting_period`: 면책, 보장개시, 책임개시, 90일, 감액, 지급률, 진단확정
- `exclusions`: 제외, 보장하지, 지급하지, 보상하지, 면책
- `subtype_coverage_map`: 제자리암, 상피내암, 전암, 경계성, 유사암, 소액암, 기타피부암, 갑상선암, 대장점막내암, 정의, 범위

---

## Regression Prevention

### GATE 5 Test Cases

**Test File**: `tests/test_gate5_token_lock_regression.py`

**Test 1 - N03 "일반암진단비Ⅱ"**:
- Token: `"일반암진단비"` (len=6)
- Condition: `len >= 6` → substring match enabled
- Substring "암진단비" must be found in sample chunks

**Test 2 - N09 "암진단Ⅱ(유사암제외)담보"**:
- After processing: `"암진단"` (suffix "담보" removed)
- Condition: single token, len < 6 → exact match
- Token "암진단" must be found in sample chunks

---

## Change Log

### 2026-01-16: Initial 8-Insurer Baseline

**Patch**: GATE 5 token lock fix
- Changed: `> 6` → `>= 6` for substring matching
- Added: Generic suffix stripping before tokenization
- Impact: N03, N09 now pass GATE 5

**Files Modified**:
- `tools/run_db_only_coverage.py` (GATE 5 logic)
- `tools/coverage_profiles.py` (unchanged, for reference)

**Commit**: `fix(a4200_1): gate5 token lock patch + 8-insurer baseline freeze`

---

## Freeze Rules

1. **NO modifications to**:
   - `tools/coverage_profiles.py` → A4200_1_PROFILE
   - Anchor keywords
   - Gate structure (7 gates maintained)
   - Required terms by slot

2. **DB state locked**:
   - coverage_chunk: 5,875 rows (DO NOT regenerate)
   - evidence_slot: 24 rows (FOUND=24)
   - compare_table_v2: table_id=17

3. **Regression tests required** before any GATE 5 changes

---

**STATUS**: Baseline frozen ✅
**Last Verified**: 2026-01-16
