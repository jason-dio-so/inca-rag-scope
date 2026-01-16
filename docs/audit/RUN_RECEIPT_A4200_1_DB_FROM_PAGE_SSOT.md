# RUN_RECEIPT_A4200_1_DB_FROM_PAGE_SSOT

**Date**: 2026-01-16
**Coverage**: A4200_1 (암진단비, 유사암제외)
**Status**: ✅ PASS
**Insurers**: N08 (삼성), N10 (KB)
**Source**: document_page_ssot (NO PDF re-parsing)

---

## 실행 명령

```bash
python3 tools/run_db_only_coverage.py \
  --coverage_code A4200_1 \
  --as_of_date 2025-11-26 \
  --ins_cds N08,N10 \
  --stage all
```

**Log**: `/tmp/a4200_1_from_page_ssot.log`

---

## Pipeline Stage 결과

### Stage 1: Chunk Generation (from document_page_ssot)

| Insurer | Paragraphs Scanned | Chunks Created | Source |
|---------|-------------------|----------------|--------|
| N08 (삼성) | 1,900 | 753 | document_page_ssot |
| N10 (KB) | 1,150 | 573 | document_page_ssot |
| **Total** | **3,050** | **1,326** | - |

**Anchors Used**:
- Profile: `["암", "암진단", "암진단비", "암 진단", "암 진단비", "일반암"]`
- Insurer name: `"암진단비(유사암제외)"` (added automatically)

**Key Changes**:
- ✅ Added whitespace variants: `"암 진단"`, `"암 진단비"`
- ✅ Source: document_page_ssot table (NO PDF files opened)
- ✅ doc_type preserved: 약관, 사업방법서, 요약서, 가입설계서

---

### Stage 2: Evidence Generation

| Insurer | Total Chunks | Anchor-Matched | Slots |
|---------|-------------|----------------|-------|
| N08 | 753 | 655 | 3 FOUND |
| N10 | 573 | 478 | 3 FOUND |

**Slots Created**: 6 (3 slots × 2 insurers)

| Slot | N08 Status | N10 Status |
|------|------------|------------|
| waiting_period | FOUND | FOUND |
| exclusions | FOUND | FOUND |
| subtype_coverage_map | FOUND | FOUND |

**Result**: FOUND=6, NOT_FOUND=0, DROPPED=0 ✅

---

### Stage 3: Compare Table Generation

**Table ID**: 16
**Payload Structure**: insurer_rows with 3 slots each

---

## 검증 결과

### ✅ Gate Compliance

| Gate | Result |
|------|--------|
| chunk_count > 0 | ✅ PASS (1,326 chunks) |
| FOUND >= 1 | ✅ PASS (FOUND=6) |
| contamination = 0 | ✅ PASS (0 contaminated rows) |
| API 200 OK | ✅ PASS (payload generated) |

---

### Contamination Scan

**Query**:
```sql
SELECT slot_key, COUNT(*) as contaminated_rows
FROM evidence_slot
WHERE coverage_code = 'A4200_1'
  AND as_of_date = '2025-11-26'
  AND ins_cd IN ('N08', 'N10')
  AND excerpt ~* '통원일당|입원일당|치료일당|일당|상급종합병원|100세만기|90세만기|납입면제|보험료.*납입면제|보장보험료|차회.*이후|면제.*사유|납입을.*면제'
GROUP BY slot_key;
```

**Result**: 0 rows (no contamination) ✅

---

### API Verification

**Endpoint**: `GET /compare_v2`

**Request**:
```
http://localhost:8000/compare_v2?coverage_code=A4200_1&as_of_date=2025-11-26&ins_cds=N08,N10
```

**Response Summary**:
```json
{
  "debug": {
    "profile_id": "A4200_1_PROFILE_V1",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",
    "chunk_rowcount_at_generation": 1326
  },
  "insurer_rows": [
    {
      "ins_cd": "N08",
      "slots": {
        "exclusions": {"status": "FOUND", "excerpt": "..."},
        "waiting_period": {"status": "FOUND", "excerpt": "..."},
        "subtype_coverage_map": {"status": "FOUND", "excerpt": "..."}
      }
    },
    {
      "ins_cd": "N10",
      "slots": {
        "exclusions": {"status": "FOUND", "excerpt": "..."},
        "waiting_period": {"status": "FOUND", "excerpt": "..."},
        "subtype_coverage_map": {"status": "FOUND", "excerpt": "..."}
      }
    }
  ]
}
```

**Status**: 200 OK ✅

---

## 주요 변경 사항

### 1. Pipeline Input: document_page_ssot ONLY

**Before** (PDF-based):
```python
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        # ...
```

**After** (SSOT-based):
```python
self.cur.execute("""
    SELECT raw_text, doc_type, source_pdf, page_start, page_end, content_hash
    FROM document_page_ssot
    WHERE ins_cd = %s
""", (ins_cd,))
for para in paragraphs:
    if any(anchor in para['raw_text'] for anchor in anchors):
        # Create chunk from SSOT
```

**Impact**:
- ❌ NO PDF file I/O (pdfplumber eliminated)
- ✅ All paragraphs pre-extracted in document_page_ssot
- ✅ Consistent deduplication via content_hash (SHA256)

---

### 2. Profile Update: Whitespace Variants

**tools/coverage_profiles.py**:
```python
# Before
"anchor_keywords": ["암", "암진단", "암진단비", "일반암"]

# After
"anchor_keywords": ["암", "암진단", "암진단비", "암 진단", "암 진단비", "일반암"]
```

**Reason**: 삼성(N08) PDF contains `"암 진단비"` with whitespace

---

### 3. DB Schema Update: doc_type Constraint

**coverage_chunk table**:
```sql
-- Before
CHECK (doc_type IN ('약관', '사업방법서', '요약서'))

-- After
CHECK (doc_type IN ('약관', '사업방법서', '요약서', '가입설계서'))
```

**Reason**: document_page_ssot includes '가입설계서'

---

## DB State

```sql
-- coverage_chunk
SELECT ins_cd, doc_type, COUNT(*) as chunks
FROM coverage_chunk
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26'
GROUP BY ins_cd, doc_type;

-- Result:
-- N08, 가입설계서, 6
-- N08, 사업방법서, 63
-- N08, 약관, 630
-- N08, 요약서, 54
-- N10, 가입설계서, 6
-- N10, 사업방법서, 39
-- N10, 약관, 504
-- N10, 요약서, 24
-- Total: 1326 chunks
```

```sql
-- evidence_slot
SELECT ins_cd, slot_key, status
FROM evidence_slot
WHERE coverage_code = 'A4200_1' AND as_of_date = '2025-11-26'
ORDER BY ins_cd, slot_key;

-- Result: 6 rows (3 slots × 2 insurers), all FOUND
```

---

## Performance

| Metric | Value |
|--------|-------|
| Total execution time | ~1 second |
| Chunk generation | ~0.5 sec |
| Evidence generation | ~0.3 sec |
| Compare generation | ~0.1 sec |

**Note**: 33 minutes saved vs PDF re-parsing (document_page_ssot pre-built)

---

## 절대 금지 사항 준수

| Forbidden Action | Status |
|------------------|--------|
| PDF 직접 재파싱 | ✅ AVOIDED (document_page_ssot used) |
| jsonl 레거시 파일 사용 | ✅ AVOIDED (DB-only) |
| gate 완화 | ✅ AVOIDED (GATE_SSOT_V2_CONTEXT_GUARD maintained) |
| profile 강제 FOUND | ✅ AVOIDED (natural matching) |
| vector/LLM | ✅ AVOIDED (keyword-based only) |

---

## Next Steps (NOT NOW)

1. A4200_1 확장: 2사 → 4사 → 8사
2. A4210 현행화: document_page_ssot 기반으로 재실행
3. A5200 현행화: document_page_ssot 기반으로 재실행

---

**STATUS**: A4200_1 baseline re-established from document_page_ssot ✅

**CONCLUSION**: "모든 보험사 PDF가 담보 무관 JSON SSOT로 고정되었고, A4200_1은 이 SSOT를 재사용하여 현행화 완료"
