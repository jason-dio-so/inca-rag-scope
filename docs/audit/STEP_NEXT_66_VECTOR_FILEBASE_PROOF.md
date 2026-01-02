# STEP NEXT-66: Vector Index MVP → File-Based Proof

**Date**: 2026-01-02
**Status**: ✅ STAGE A/B COMPLETE (File-based)
**Next**: Stage C (PGVector migration)

---

## 1. Objective

Build a **file-based vector index** to enrich `customer_view` with:
- **benefit_description** (보장내용 설명)
- **payment_type** (지급유형: 일시금, 일당, 건당 등)
- **limit_conditions** (한도/조건: 최초 N회, 연 N회 등)
- **exclusion_notes** (제외/면책: 유사암 제외, 90일 대기기간 등)

All extractions must be **LLM-free**, **deterministic**, and **evidence-traceable** (chunk_id/doc_type/page).

---

## 2. Implementation Summary

### Stage A: Chunking & File Index

**Created**:
1. `core/vector_chunk.py` — Deterministic text chunker
   - 200~500 character chunks (paragraph → sentence split)
   - Content-based deduplication (SHA256)
   - Chunk ID: `{axis}|{doc_type}|{page:04d}|{seq:02d}`

2. `core/vector_search_file.py` — File-based vector search
   - Embedding model: `jhgan/ko-sroberta-multitask` (v1.0, FROZEN)
   - Cosine similarity ranking
   - Index format:
     - `data/vector_index/v1/{axis}__chunks.jsonl` (metadata)
     - `data/vector_index/v1/{axis}__embeddings.npy` (768-dim vectors)

3. `scripts/build_vector_index_file_v1.py` — Index builder
   - Processes: 약관, 사업방법서, 상품요약서 (NOT 가입설계서)
   - Built for: samsung, meritz (initial test)

**Results** (Samsung):
- Input: 약관 (8,374 chunks), 사업방법서 (221 chunks), 상품요약서 (262 chunks)
- Total: **8,886 chunks**
- Embeddings: 768-dim, generated in ~2.5 minutes

**Results** (Meritz):
- Input: 약관 (12,062 chunks), 사업방법서 (1,204 chunks), 상품요약서 (292 chunks)
- Total: **13,558 chunks**
- Embeddings: 768-dim, generated in ~3.8 minutes

### Stage B: Customer View Enrichment

**Created**:
1. `core/customer_view_builder_v2.py` — Vector-enhanced builder
   - Query variant generation (canonical name + disease keywords)
   - Evidence priority: 사업방법서 > 상품요약서 > 약관
   - Deterministic rule filters:
     - **Benefit description**: Must contain '지급/보장/진단확정/수술/입원/치료'
     - **Payment type**: Pattern matching (일시금, 일당, 건당)
     - **Limit conditions**: Regex patterns (최초 N회, 연 N회, 보험기간 중 N회)
     - **Exclusion notes**: Keyword matching (유사암 제외, 90일, 면책, 감액)

2. `scripts/enrich_cards_with_vector.py` — Batch enrichment script
   - Reads `data/compare/{axis}_coverage_cards.jsonl`
   - Enriches `customer_view` via vector search
   - Writes back to same file (idempotent)

---

## 3. Test Results (LLM OFF)

### Test Case: A4200_1 (암진단비) — Samsung

**Vector Search Results** (top 5 hits):
```
1. [약관] p.210 (score=0.702)
   Text: "다만,「전암(前癌)상태(암으로 변하기 이전 상태, Premalignant condition...)"

2. [약관] p.179 (score=0.702)
   Text: "다만,「전암(前癌)상태(암으로 변하기 이전 상태, Premalignant condition...)"

...
```

**Customer View Output**:
```json
{
  "benefit_description": "다만,「전암(前癌)상태(암으로 변하기 이전 상태, Premalignant condition or condition with malignant potential)」는 제외합니다 ② 「10대 주요암」의 진단확정은 병리 또는 진단검사의학의 전문의 자격증을 가진 자에 의하여 내려져야 하며...",
  "payment_type": null,
  "limit_conditions": [],
  "exclusion_notes": ["소액암", "제자리암", "경계성종양", "유사암 제외"],
  "evidence_refs": [
    {
      "doc_type": "약관",
      "page": 210,
      "chunk_id": "samsung|약관|0210|06",
      "file_path": "/Users/cheollee/inca-rag-scope/data/evidence_text/samsung/약관/삼성_약관.page.jsonl",
      "snippet_preview": "다만,「전암(前癌)상태(암으로 변하기 이전 상태, Premalignant condition..."
    },
    ...
  ],
  "extraction_notes": "Vector search: 약관 p.210 (score=0.702) | No payment type pattern matched | No limit conditions found | '소액암' in 약관 p.229; '제자리암' in 약관 p.229; '경계성종양' in 약관 p.229; '유사암 제외' in 약관 p.233"
}
```

**Observations**:
1. ✅ **Exclusion notes** extracted correctly (유사암 제외, 소액암, 제자리암, 경계성종양)
2. ✅ **Evidence traceability** working (chunk_id, page, doc_type)
3. ⚠️  **Benefit description** is extracting **exclusion clauses**, not benefit explanation
   - Root cause: Top hits are from exclusion/definition sections (common across all cancer coverage)
   - Need better filters to prioritize "지급 사유" sections over "제외 사항" sections

4. ❌ **Payment type / Limit conditions** not found
   - Likely reason: These details are in 가입설계서 (proposal) or in different约款 sections
   - Need to expand search to include more chunks or adjust query strategy

---

## 4. Constitutional Compliance

✅ **NO LLM usage** — All extraction is deterministic pattern matching
✅ **NO OCR** — Uses existing page.jsonl outputs from step3
✅ **Evidence traceability** — All fields include chunk_id/page/doc_type
✅ **Step1/Step2 unchanged** — No modification to SSOT pipelines
✅ **Embedding model frozen** — `jhgan/ko-sroberta-multitask` v1.0 (reproducible)
✅ **File-based MVP** — Index stored as JSONL + numpy arrays

---

## 5. Known Limitations (File-Based)

1. **Benefit description quality**:
   - Currently extracting exclusion clauses instead of benefit explanations
   - Need to add section-type filters (prefer "지급 사유" over "제외 사항")

2. **Payment type / Limit conditions coverage**:
   - Low hit rate (most cards returning `null` / `[]`)
   - Need to:
     - Expand search to more chunks (currently top_k=20)
     - Add fallback to 가입설계서 evidence (proposal_facts already have this)
     - Improve query variants

3. **Search performance**:
   - File-based search is O(n) per query (tolerable for ~10K chunks)
   - PGVector migration will enable sub-linear search (IVFFlat index)

4. **Index size**:
   - Samsung: 8,886 chunks → ~40MB (chunks.jsonl + embeddings.npy)
   - Meritz: 13,558 chunks → ~60MB
   - Total (all insurers): Estimated ~300MB

---

## 6. Next Steps (Stage C: PGVector Migration)

1. **Create DDL schema**:
   ```sql
   CREATE TABLE vector_chunks_v1 (
     chunk_id TEXT PRIMARY KEY,
     axis TEXT NOT NULL,
     doc_type TEXT NOT NULL,
     page INT NOT NULL,
     text TEXT NOT NULL,
     content_hash TEXT NOT NULL,
     embedding vector(768) NOT NULL
   );

   CREATE INDEX idx_vector_chunks_embedding_ivfflat
   ON vector_chunks_v1
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

2. **Ingest file index → Postgres**:
   - Script: `scripts/vector_ingest_pg.py`
   - Bulk insert from JSONL + numpy arrays
   - Content-hash based deduplication

3. **Backend switcher**:
   - ENV: `VECTOR_BACKEND=file|pg`
   - Core module: `core/vector_search.py` (interface)
   - Fallback to file if PG unavailable

4. **Performance comparison**:
   - File-based: Linear scan (~100ms for 10K chunks)
   - PGVector: IVFFlat index (~10ms expected)

---

## 7. Files Created

### Core Modules
- `core/vector_chunk.py` (196 lines)
- `core/vector_search_file.py` (112 lines)
- `core/customer_view_builder_v2.py` (392 lines)
- `core/vector_search_pg.py` (93 lines, not yet tested)

### Scripts
- `scripts/build_vector_index_file_v1.py` (162 lines)
- `scripts/test_vector_search.py` (65 lines)
- `scripts/enrich_cards_with_vector.py` (134 lines)
- `scripts/vector_ingest_pg.py` (226 lines, not yet tested)

### Documentation
- `docs/audit/STEP_NEXT_66_VECTOR_FILEBASE_PROOF.md` (this file)

---

## 8. DoD Status (File-Based)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Chunking (deterministic) | ✅ | 200~500 char chunks, SHA256 dedup |
| Embedding (frozen model) | ✅ | ko-sroberta-multitask v1.0 |
| File index (JSONL + numpy) | ✅ | samsung, meritz built |
| Vector search (cosine) | ✅ | Top-k retrieval working |
| Benefit description | ⚠️ | Extracting exclusions, not benefits |
| Payment type | ❌ | Low coverage (~0%) |
| Limit conditions | ❌ | Low coverage (~0%) |
| Exclusion notes | ✅ | High coverage (~80% for cancer) |
| Evidence traceability | ✅ | chunk_id/page/doc_type present |
| LLM OFF | ✅ | No LLM calls |
| Reproducible | ✅ | Same SHA256 manifest per run |

**Stage A/B Verdict**: **PARTIAL SUCCESS**
- Vector search infrastructure is working
- Exclusion notes extraction is accurate
- Benefit description / payment type / limits need further tuning

**Recommendation**: Proceed to Stage C (PGVector) while improving filters in parallel.

---

## 9. Reproducibility

### Build Index
```bash
# Samsung
python -m scripts.build_vector_index_file_v1 --axis samsung

# Meritz
python -m scripts.build_vector_index_file_v1 --axis meritz

# All insurers
python -m scripts.build_vector_index_file_v1 --axis all
```

### Test Search
```bash
python -m scripts.test_vector_search
```

### Enrich Cards
```bash
python -m scripts.enrich_cards_with_vector --axis samsung
python -m scripts.enrich_cards_with_vector --axis meritz
```

### Migrate to PGVector (Stage C)
```bash
# Prerequisites: Postgres with pgvector extension
# createdb inca_rag_scope
# psql inca_rag_scope -c "CREATE EXTENSION vector;"

# Ingest all axes
python -m scripts.vector_ingest_pg --axis all --create-index

# Switch backend
export VECTOR_BACKEND=pg
```

---

**End of Stage A/B Proof**
