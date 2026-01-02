# Vector Index Quick Start

**TL;DR**: How to build, search, and maintain the vector index.

---

## Build Index (One-time Setup)

### Single Insurer
```bash
python -m scripts.build_vector_index_file_v1 --axis samsung
```

### All Insurers
```bash
python -m scripts.build_vector_index_file_v1 --axis all
```

**Time**: ~3-5 minutes per insurer
**Output**: `data/vector_index/v1/{axis}__chunks.jsonl` + `{axis}__embeddings.npy`

---

## Search (Python)

```python
from core.vector_search_file import search_chunks

# Simple search
hits = search_chunks(
    axis="samsung",
    query="암진단비",
    top_k=10
)

# Filtered search
hits = search_chunks(
    axis="samsung",
    query="암진단비",
    doc_types=["약관", "사업방법서"],  # Exclude 상품요약서
    top_k=20
)

# Print results
for hit in hits:
    print(f"{hit.doc_type} p.{hit.page} (score={hit.score:.3f})")
    print(f"  {hit.text[:100]}...")
```

---

## Enrich Coverage Cards

```bash
# Single insurer
python -m scripts.enrich_cards_with_vector --axis samsung

# Check results
head -1 data/compare/samsung_coverage_cards.jsonl | jq .customer_view
```

---

## Migrate to PGVector (Optional)

### Prerequisites
```bash
# Install Postgres with pgvector
brew install postgresql@15 pgvector

# Create database
createdb inca_rag_scope
psql inca_rag_scope -c "CREATE EXTENSION vector;"
```

### Ingest
```bash
python -m scripts.vector_ingest_pg --axis all --create-index
```

### Switch Backend
```bash
export VECTOR_BACKEND=pg  # Use Postgres
export VECTOR_BACKEND=file # Use file-based (default)
```

---

## Maintenance

### Rebuild Index (if PDF changes)
```bash
# 1. Re-run step3 (extract text)
python -m pipeline.step3_extract_text.run --insurer samsung

# 2. Rebuild vector index
python -m scripts.build_vector_index_file_v1 --axis samsung

# 3. Re-enrich cards
python -m scripts.enrich_cards_with_vector --axis samsung
```

### Check Index Stats
```bash
# Chunk count
wc -l data/vector_index/v1/samsung__chunks.jsonl

# Embedding shape
python -c "import numpy as np; print(np.load('data/vector_index/v1/samsung__embeddings.npy').shape)"
```

### Test Search
```bash
python -m scripts.test_vector_search
```

---

## Troubleshooting

### "Index not found" error
**Solution**: Build index first
```bash
python -m scripts.build_vector_index_file_v1 --axis {insurer}
```

### Slow search
**Solution**: Reduce top_k or switch to PGVector
```python
hits = search_chunks(axis="samsung", query="암진단비", top_k=5)  # Faster
```

### Out of memory
**Solution**: Reduce batch size in `build_vector_index_file_v1.py`
```python
embeddings = model.encode(texts, batch_size=16)  # Default: 32
```

---

## Files & Directories

```
data/vector_index/v1/          # Vector index (file-based)
  ├── _META.json               # Index metadata
  ├── {axis}__chunks.jsonl     # Chunk metadata
  └── {axis}__embeddings.npy   # Embeddings (768-dim)

core/
  ├── vector_chunk.py          # Chunker
  ├── vector_search_file.py    # File-based search
  ├── vector_search_pg.py      # PGVector search
  └── customer_view_builder_v2.py  # Enrichment logic

scripts/
  ├── build_vector_index_file_v1.py    # Index builder
  ├── enrich_cards_with_vector.py      # Batch enrichment
  ├── test_vector_search.py            # Test script
  └── vector_ingest_pg.py              # PGVector ingestion

docs/
  ├── VECTOR_INDEX_QUICK_START.md      # This file
  ├── STEP_NEXT_66_FINAL_SUMMARY.md    # Full documentation
  └── audit/
      ├── STEP_NEXT_66_VECTOR_FILEBASE_PROOF.md     # Stage A/B proof
      └── STEP_NEXT_66_PGVECTOR_MIGRATION_GUIDE.md  # Stage C guide
```

---

## References

- **Full Documentation**: `docs/STEP_NEXT_66_FINAL_SUMMARY.md`
- **Proof Document**: `docs/audit/STEP_NEXT_66_VECTOR_FILEBASE_PROOF.md`
- **Migration Guide**: `docs/audit/STEP_NEXT_66_PGVECTOR_MIGRATION_GUIDE.md`
- **Index README**: `data/vector_index/README.md`

---

**Quick Reference**: Built 2026-01-02 (STEP NEXT-66)
