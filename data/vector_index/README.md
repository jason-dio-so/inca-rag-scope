# Vector Index Directory

**Created**: 2026-01-02 (STEP NEXT-66)
**Purpose**: File-based vector index for customer_view enrichment (benefit descriptions, payment types, limits, exclusions)

---

## Directory Structure

```
data/vector_index/
├── v1/                                    # Version 1 (file-based MVP)
│   ├── _META.json                        # Index metadata (model, version)
│   ├── {axis}__chunks.jsonl              # Chunk metadata (text, page, doc_type)
│   └── {axis}__embeddings.npy            # 768-dim embeddings (numpy array)
└── README.md                              # This file
```

---

## File Format

### `_META.json`
```json
{
  "embedding_model": "jhgan/ko-sroberta-multitask",
  "embedding_version": "v1.0",
  "doc_types": ["약관", "사업방법서", "상품요약서"],
  "axes": ["samsung", "meritz", "hanwha", ...]
}
```

### `{axis}__chunks.jsonl`
Each line is a JSON object:
```json
{
  "axis": "samsung",
  "insurer": "samsung",
  "doc_type": "약관",
  "file_path": "/path/to/삼성_약관.page.jsonl",
  "page": 168,
  "chunk_id": "samsung|약관|0168|03",
  "text": "문단 텍스트...",
  "content_hash": "sha256..."
}
```

**Chunk ID format**: `{axis}|{doc_type}|{page:04d}|{seq:02d}`
- `axis`: Insurance axis (samsung, meritz, etc.)
- `doc_type`: Document type (약관, 사업방법서, 상품요약서)
- `page`: Page number (4-digit, zero-padded)
- `seq`: Chunk sequence on page (2-digit, zero-padded)

### `{axis}__embeddings.npy`
Numpy array of shape `(num_chunks, 768)`:
- Each row corresponds to a chunk in `{axis}__chunks.jsonl` (same order)
- Embedding dimension: 768 (from ko-sroberta-multitask)
- Data type: float32

---

## Current Index Stats

### Samsung
- **Chunks**: 8,886
- **Sources**: 약관 (8,374), 사업방법서 (221), 상품요약서 (262)
- **Size**: 34.4 MB (chunks.jsonl: 8.4 MB, embeddings.npy: 26 MB)

### Meritz
- **Chunks**: 13,558
- **Sources**: 약관 (12,062), 사업방법서 (1,204), 상품요약서 (292)
- **Size**: 53 MB (chunks.jsonl: 13 MB, embeddings.npy: 40 MB)

### Total (All Axes, Estimated)
- **Chunks**: ~100,000
- **Size**: ~300 MB

---

## Usage

### Build Index

```bash
# Single axis
python -m scripts.build_vector_index_file_v1 --axis samsung

# All axes
python -m scripts.build_vector_index_file_v1 --axis all
```

### Search

```python
from core.vector_search_file import search_chunks

hits = search_chunks(
    axis="samsung",
    query="암진단비",
    doc_types=["약관", "사업방법서", "상품요약서"],
    top_k=10
)

for hit in hits:
    print(f"{hit.doc_type} p.{hit.page} (score={hit.score:.3f})")
    print(f"  {hit.text[:100]}...")
```

### Enrich Coverage Cards

```bash
python -m scripts.enrich_cards_with_vector --axis samsung
```

---

## Chunking Rules (Deterministic)

1. **Target size**: 200-500 characters
2. **Split strategy**: Paragraph boundaries → Sentence boundaries
3. **Minimum sentence length**: 15 characters
4. **Noise filtering**:
   - Page numbers (e.g., "3 / 1559")
   - TOC markers (e.g., "[목차]")
   - Section numbers only (e.g., "4-1-13")

5. **Content hashing**: SHA256 of normalized text (whitespace collapsed)

---

## Embedding Model (FROZEN)

**Model**: `jhgan/ko-sroberta-multitask`
**Version**: v1.0
**Dimension**: 768
**Framework**: sentence-transformers

**Why this model?**
- Korean-optimized (trained on Korean corpora)
- Multi-task learning (semantic similarity + NLI)
- Moderate size (110M parameters, ~440MB)
- Fast inference (~2 sentences/sec on CPU)

**Reproducibility**: Model version is frozen. Do NOT change unless you rebuild ALL indices.

---

## Migration to PGVector (Stage C)

See: `docs/audit/STEP_NEXT_66_PGVECTOR_MIGRATION_GUIDE.md`

**Command**:
```bash
python -m scripts.vector_ingest_pg --axis all --create-index
```

**Backend switch**:
```bash
export VECTOR_BACKEND=pg  # Use Postgres
export VECTOR_BACKEND=file # Use file-based (default)
```

---

## Maintenance

### Rebuild Index (if source PDFs change)

1. Run step3 (extract_text) for the changed insurer
2. Rebuild vector index:
   ```bash
   python -m scripts.build_vector_index_file_v1 --axis {insurer}
   ```
3. Re-enrich coverage cards:
   ```bash
   python -m scripts.enrich_cards_with_vector --axis {insurer}
   ```

### Verify Index Integrity

```bash
# Check chunk count
wc -l data/vector_index/v1/samsung__chunks.jsonl

# Check embedding shape
python -c "import numpy as np; print(np.load('data/vector_index/v1/samsung__embeddings.npy').shape)"

# Verify hash consistency
python -c "
import json, hashlib, re
with open('data/vector_index/v1/samsung__chunks.jsonl') as f:
    for line in f:
        chunk = json.loads(line)
        text_normalized = re.sub(r'\s+', ' ', chunk['text'].strip())
        computed_hash = hashlib.sha256(text_normalized.encode('utf-8')).hexdigest()
        assert chunk['content_hash'] == computed_hash, f'Hash mismatch: {chunk[\"chunk_id\"]}'
print('✅ All hashes valid')
"
```

---

## Troubleshooting

### Q: Search returns irrelevant results

**A**: Try these:
1. Increase `top_k` (more candidates)
2. Refine query (use canonical coverage name)
3. Filter by specific `doc_types`

### Q: Index build is slow

**A**: Expected. Embedding generation is CPU-intensive.
- Samsung (8,886 chunks): ~2.5 minutes
- Meritz (13,558 chunks): ~3.8 minutes
- All axes: ~30 minutes (estimated)

To speed up:
- Use GPU (if available): `device='cuda'` in `get_model()`
- Reduce chunk count (increase MIN_CHUNK_SIZE)

### Q: Out of memory during index build

**A**: Reduce batch size in `sentence_transformers`:
```python
embeddings = model.encode(
    texts,
    batch_size=16,  # Default: 32
    convert_to_numpy=True
)
```

### Q: How to add a new insurer?

**A**:
1. Run pipeline step1-3 for the new insurer
2. Build vector index:
   ```bash
   python -m scripts.build_vector_index_file_v1 --axis {new_insurer}
   ```
3. Update `AXES` list in `build_vector_index_file_v1.py`

---

## References

- **STEP NEXT-66 Spec**: `STEP NEXT-66` task description (initial message)
- **Proof Document**: `docs/audit/STEP_NEXT_66_VECTOR_FILEBASE_PROOF.md`
- **PGVector Guide**: `docs/audit/STEP_NEXT_66_PGVECTOR_MIGRATION_GUIDE.md`
- **Code**:
  - Chunker: `core/vector_chunk.py`
  - Search (file): `core/vector_search_file.py`
  - Search (PG): `core/vector_search_pg.py`
  - Builder: `scripts/build_vector_index_file_v1.py`

---

**End of README**
