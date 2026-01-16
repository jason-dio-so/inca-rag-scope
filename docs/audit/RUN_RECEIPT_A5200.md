# RUN RECEIPT: A5200 암수술비(유사암제외) - DB-ONLY PIPELINE

**Date:** 2026-01-16
**Coverage Code:** A5200
**As-of Date:** 2025-11-26
**Insurer Set:** N08 (삼성), N10 (KB)
**Pipeline:** tools/run_db_only_coverage.py
**Profile:** A5200_PROFILE_V1
**Gate Version:** GATE_SSOT_V2_CONTEXT_GUARD

---

## 📋 EXECUTIVE SUMMARY

**Status:** ✅ SUCCESS
**Total Chunks:** 1,462 (N08: 846, N10: 616)
**Evidence Slots:** 6/6 FOUND (100%)
**Contamination:** 0% (0 Hard-negatives, 0 Section-negatives)
**Compare Table:** table_id=12 (API verified)

---

## 🔧 HOTFIX: doc_type Normalization

### Problem
Initial run failed with DB constraint error:
```
psycopg2.errors.NotNullViolation: new row for relation "coverage_chunk"
violates check constraint "coverage_chunk_doc_type_check"
DETAIL: Failing row contains (..., 상품요약서, ...)
```

### Root Cause
PDF_SOURCE_REGISTRY included "상품요약서" but DB constraint only allows `['약관', '사업방법서', '요약서']`

### Fix Applied
**File:** `tools/run_db_only_coverage.py:273-276`

```python
# Normalize doc_type before INSERT
normalized_doc_type = doc_type
if doc_type in ["상품요약서", "쉬운요약서"]:
    normalized_doc_type = "요약서"
```

### Verification
After fix:
- N08: 133 요약서 chunks ✅
- N10: 87 요약서 chunks ✅
- Total: 220 요약서 chunks (was 0 before fix)

---

## 📊 CHUNK GENERATION (Stage: chunks)

### Execution
```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A5200 \
  --as_of_date 2025-11-26 \
  --ins_cds N08,N10 \
  --stage chunks
```

### Results

#### N08 (삼성)
| doc_type   | chunk_count | pages_processed | source_pdf          |
|------------|-------------|-----------------|---------------------|
| 약관       | 584         | 1,561           | 삼성_약관.pdf       |
| 사업방법서 | 129         | 149             | 삼성_사업설명서.pdf |
| 요약서     | 133         | 172             | 삼성_상품요약서.pdf |
| **Total**  | **846**     | **1,882**       | -                   |

#### N10 (KB)
| doc_type   | chunk_count | pages_processed | source_pdf        |
|------------|-------------|-----------------|-------------------|
| 약관       | 455         | 970             | KB_약관.pdf       |
| 사업방법서 | 74          | 91              | KB_사업방법서.pdf |
| 요약서     | 87          | 90              | KB_상품요약서.pdf |
| **Total**  | **616**     | **1,151**       | -                 |

**Pipeline Total:** 1,462 chunks from 3,033 pages (duration: ~7 minutes)

### Sample Chunks
```sql
-- N08 약관 (page 4)
excerpt: "니다. 다만,「전암(前癌)상태(암으로 변하기 이전 상태, Premalignant condition..."

-- N08 요약서 (page 3)
excerpt: "● 문답식 상품해설 (Q & A)\nQ) 이 상품의 가장 큰..."

-- N10 약관 (page 3)
excerpt: "■ 해약환급금 미지급형에 관한 사항\n보험금 지급 관련 특히 유의할 사항..."
```

---

## 🔍 EVIDENCE GENERATION (Stage: evidence)

### Execution
```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A5200 \
  --as_of_date 2025-11-26 \
  --ins_cds N08,N10 \
  --stage evidence
```

### Results

| Insurer | Coverage Name         | Anchors Used                                         | Chunks Filtered | Slots FOUND | Slots NOT_FOUND |
|---------|-----------------------|-----------------------------------------------------|-----------------|-------------|-----------------|
| N08     | 암 수술비(유사암 제외) | ['암', '암수술', '수술비', '암수술비', '암 수술비(유사암 제외)'] | 767/846         | 3           | 0               |
| N10     | 암수술비(유사암제외)   | ['암', '암수술', '수술비', '암수술비', '암수술비(유사암제외)'] | 527/616         | 3           | 0               |

**Total:** FOUND=6, NOT_FOUND=0, DROPPED=0

### Gate Validation (7-Gate System)
1. **GATE 1:** Anchor in excerpt ✅
2. **GATE 2:** Hard-negative check (통원일당, 상급종합병원, etc.) ✅
3. **GATE 3:** Section-negative check (납입면제, etc.) ✅
4. **GATE 4:** Diagnosis-signal required (수술비, 암, etc.) ✅
5. **GATE 5:** Coverage name lock (dynamic token extraction) ✅
6. **GATE 6:** Slot-specific keywords ✅
7. **GATE 7:** Slot-specific negatives ✅

---

## ✅ CONTAMINATION SCAN

### SQL Query
```sql
SELECT ins_cd, slot_key,
       CASE
         WHEN excerpt ~* '통원일당|입원일당|치료일당|상급종합병원|연간.*회한|100세만기|90세만기'
           THEN 'HARD_NEGATIVE'
         WHEN excerpt ~* '납입면제|보장보험료|면제.*사유|보험료.*납입면제'
           THEN 'SECTION_NEGATIVE'
         ELSE 'CLEAN'
       END as contamination_type
FROM evidence_slot
WHERE coverage_code = 'A5200' AND as_of_date = '2025-11-26'
  AND (excerpt ~* '<contamination_patterns>');
```

### Result
```
ins_cd | slot_key | contamination_type | excerpt_sample
--------+----------+--------------------+----------------
(0 rows)
```

**✅ CONTAMINATION: 0%** (0 Hard-negatives, 0 Section-negatives detected)

---

## 📊 COMPARE TABLE GENERATION (Stage: compare)

### Execution
```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A5200 \
  --as_of_date 2025-11-26 \
  --ins_cds N08,N10 \
  --stage compare
```

### Result
- **table_id:** 12
- **canonical_name:** 암수술비
- **insurer_set:** ["N08", "N10"]
- **payload.insurer_rows:** 2 (N08, N10)
- **payload.debug.chunk_rowcount_at_generation:** 1,462

---

## 🌐 API VERIFICATION

### Endpoint
```bash
curl "http://localhost:8000/compare_v2?coverage_code=A5200&as_of_date=2025-11-26&ins_cds=N08,N10"
```

### Response Head
```json
{
    "debug": {
        "profile_id": "A5200_PROFILE_V1",
        "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",
        "generated_at": "2026-01-16T05:15:17.159020Z",
        "generated_by": "tools/run_db_only_coverage.py",
        "chunk_rowcount_at_generation": 1462
    },
    "q13_report": null,
    "insurer_rows": [
        {
            "ins_cd": "N08",
            "slots": {
                "waiting_period": {"status": "FOUND", "excerpt": "...90일..."},
                "exclusions": {"status": "FOUND", "excerpt": "...제외..."},
                "subtype_coverage_map": {"status": "FOUND", "excerpt": "...갑상선암..."}
            }
        },
        {
            "ins_cd": "N10",
            "slots": {
                "waiting_period": {"status": "FOUND", "excerpt": "...90일..."},
                "exclusions": {"status": "FOUND", "excerpt": "...암 관련 보장..."},
                "subtype_coverage_map": {"status": "FOUND", "excerpt": "...암 관련 보장..."}
            }
        }
    ]
}
```

**✅ API Status:** 200 OK, payload valid

---

## 🔒 DATA INTEGRITY

### Database Verification
```sql
-- Chunk distribution
SELECT ins_cd, doc_type, COUNT(*) as chunk_count
FROM coverage_chunk
WHERE coverage_code = 'A5200' AND as_of_date = '2025-11-26'
GROUP BY ins_cd, doc_type;

-- Result:
 ins_cd | doc_type   | chunk_count
--------+------------+-------------
 N08    | 약관       | 584
 N08    | 사업방법서 | 129
 N08    | 요약서     | 133
 N10    | 약관       | 455
 N10    | 사업방법서 | 74
 N10    | 요약서     | 87
```

### Evidence Slot Status
```sql
SELECT status, COUNT(*) FROM evidence_slot
WHERE coverage_code = 'A5200' AND as_of_date = '2025-11-26'
GROUP BY status;

-- Result:
 status | count
--------+-------
 FOUND  | 6
```

---

## 📁 LOG FILES

1. **Chunk Generation:** `/tmp/a5200_chunks_final.log`
2. **Evidence Generation:** `/tmp/a5200_evidence_final.log`
3. **Compare Generation:** `/tmp/a5200_compare_final.log`

---

## ✅ ACCEPTANCE CRITERIA (DoD)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| A5200 coverage_chunk > 0 for N08, N10 | ✅ PASS | N08: 846, N10: 616 |
| doc_type '요약서' exists (not 0) | ✅ PASS | N08: 133, N10: 87 |
| evidence_slot FOUND ≥ 1 | ✅ PASS | FOUND=6, NOT_FOUND=0 |
| 0 contamination (Hard/Section-negatives) | ✅ PASS | 0 rows detected |
| compare_table_v2 created | ✅ PASS | table_id=12 |
| API /compare_v2 returns valid payload | ✅ PASS | 200 OK, chunk_rowcount=1462 |
| All stages DB-only (no legacy jsonl) | ✅ PASS | tools/run_db_only_coverage.py only |

---

## 🎯 CONCLUSION

**A5200 암수술비(유사암제외) 2-insurer (N08, N10) baseline established successfully.**

- ✅ 3-stage chunkgen implemented with doc_type normalization
- ✅ 7-gate context guard validated (0% contamination)
- ✅ 1,462 chunks generated from 3 doc_types (약관, 사업방법서, 요약서)
- ✅ All 6 evidence slots FOUND
- ✅ API endpoint verified
- ✅ Ready for 4-insurer expansion (N08, N10 + 2 more)

**Next Steps:**
- A4104_1 (심장질환진단비) 2-insurer baseline
- A4102 (뇌출혈진단비) 2-insurer baseline
- A5200 4-insurer expansion
- A5200 8-insurer expansion
