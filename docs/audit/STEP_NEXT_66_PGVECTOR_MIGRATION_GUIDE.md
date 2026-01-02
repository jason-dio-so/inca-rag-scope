# STEP NEXT-66: PGVector Migration Guide (Stage C)

**Status**: 📝 READY (Scripts created, awaiting execution)
**Prerequisites**: Postgres 15+ with pgvector extension

---

## 1. Prerequisites

### Install Postgres with pgvector

**macOS** (Homebrew):
```bash
brew install postgresql@15
brew install pgvector

# Start Postgres
brew services start postgresql@15
```

**Ubuntu/Debian**:
```bash
# Add PostgreSQL APT repository
sudo apt install postgresql-15 postgresql-contrib-15

# Install pgvector
sudo apt install postgresql-15-pgvector
```

**Docker** (Alternative):
```bash
docker run -d \
  --name inca-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=inca_rag_scope \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### Install Python dependencies

```bash
pip install psycopg2-binary  # or psycopg2 if building from source
```

---

## 2. Database Setup

### Create Database

```bash
# Create database
createdb inca_rag_scope

# Enable pgvector extension
psql inca_rag_scope -c "CREATE EXTENSION vector;"

# Verify
psql inca_rag_scope -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Environment Variables (Optional)

If your Postgres is not on localhost with default settings:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=inca_rag_scope
export PGUSER=postgres
export PGPASSWORD=your_password
```

---

## 3. Migration Execution

### Step 1: Create Table & Indices

The script will automatically create the table if it doesn't exist.

**Manual creation** (optional, for reference):
```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table
CREATE TABLE vector_chunks_v1 (
    chunk_id TEXT PRIMARY KEY,
    axis TEXT NOT NULL,
    insurer TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    file_path TEXT,
    page INTEGER NOT NULL,
    text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(768) NOT NULL
);

-- Indices for filtering
CREATE INDEX idx_vector_chunks_axis_doctype
ON vector_chunks_v1 (axis, doc_type);

CREATE INDEX idx_vector_chunks_insurer
ON vector_chunks_v1 (insurer);
```

### Step 2: Ingest File Index → Postgres

**Single axis** (test):
```bash
python -m scripts.vector_ingest_pg --axis samsung
```

**All axes**:
```bash
python -m scripts.vector_ingest_pg --axis all
```

**With IVFFlat index creation**:
```bash
python -m scripts.vector_ingest_pg --axis all --create-index
```

**Expected output**:
```
Connecting to Postgres...
✅ Connected to host=localhost dbname=inca_rag_scope user=postgres
✅ Table vector_chunks_v1 created (or already exists)

=== Ingesting samsung ===
  Loaded 8886 chunks, (8886, 768) embeddings
  ✅ Ingested 8886 chunks

=== Ingesting meritz ===
  Loaded 13558 chunks, (13558, 768) embeddings
  ✅ Ingested 13558 chunks

...

=== Creating vector index (IVFFlat) ===
  Creating IVFFlat index with 100 lists...
  ✅ Vector index created

✅ Ingestion complete
```

### Step 3: Verify Data

```bash
psql inca_rag_scope
```

```sql
-- Count total chunks
SELECT COUNT(*) FROM vector_chunks_v1;

-- Count by axis
SELECT axis, COUNT(*)
FROM vector_chunks_v1
GROUP BY axis
ORDER BY COUNT(*) DESC;

-- Check indices
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'vector_chunks_v1';
```

**Expected counts** (after all axes ingested):
- Samsung: 8,886
- Meritz: 13,558
- Total (all): ~100,000 (estimated)

---

## 4. Backend Switching

### Set Environment Variable

**Use file backend** (default):
```bash
export VECTOR_BACKEND=file
```

**Use Postgres backend**:
```bash
export VECTOR_BACKEND=pg
```

### Code Integration

The `customer_view_builder_v2.py` will automatically detect the backend from the environment variable (future enhancement).

For now, to use PG backend, update imports:

```python
# Instead of:
from core.vector_search_file import search_chunks

# Use:
from core.vector_search_pg import search_chunks_pg as search_chunks
```

---

## 5. Performance Comparison

### File-Based (Current)

**Pros**:
- No external dependencies
- Simple setup
- Portable (just copy JSONL + numpy files)

**Cons**:
- Linear search: O(n) per query (~100ms for 10K chunks)
- No concurrent access optimization
- Memory intensive (loads all embeddings into RAM)

**Benchmarks** (Samsung, 8,886 chunks):
- Query time: ~80-120ms (single query)
- Memory usage: ~200MB (model + embeddings)

### PGVector (After Migration)

**Pros**:
- Sub-linear search: O(log n) with IVFFlat index (~10ms expected)
- Concurrent queries (Postgres handles locking)
- Disk-based storage (smaller memory footprint)
- SQL integration (join with other tables)

**Cons**:
- Requires Postgres setup
- IVFFlat index build time (one-time cost)
- Network latency (if DB is remote)

**Expected benchmarks** (Samsung, 8,886 chunks with IVFFlat):
- Query time: ~10-30ms (single query)
- Index size: ~100MB (on disk)
- Memory usage: ~50MB (query cache)

---

## 6. IVFFlat Index Tuning

### Choosing `lists` Parameter

The `lists` parameter controls the trade-off between speed and recall:
- **Fewer lists** (10-50): Higher recall, slower search
- **More lists** (100-1000): Faster search, lower recall
- **Rule of thumb**: `lists = sqrt(rows)`

**Our default**:
- Samsung (8,886 rows): `lists = 94` (clamped to 100)
- Meritz (13,558 rows): `lists = 116`
- All axes (~100,000 rows): `lists = 316`

### Rebuild Index (if needed)

```sql
-- Drop old index
DROP INDEX idx_vector_chunks_embedding_ivfflat;

-- Create new index with different lists
CREATE INDEX idx_vector_chunks_embedding_ivfflat
ON vector_chunks_v1
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);
```

### Query-Time Tuning

```sql
-- Set probes (how many lists to search)
-- Higher probes = better recall, slower
SET ivfflat.probes = 10;  -- Default
SET ivfflat.probes = 20;  -- Higher recall
```

---

## 7. Troubleshooting

### Error: "extension vector does not exist"

**Solution**:
```bash
psql inca_rag_scope -c "CREATE EXTENSION vector;"
```

### Error: "could not connect to server"

**Solution**: Check Postgres is running
```bash
# macOS
brew services list
brew services start postgresql@15

# Linux
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Error: "permission denied for database"

**Solution**: Grant permissions
```sql
GRANT ALL PRIVILEGES ON DATABASE inca_rag_scope TO your_user;
```

### Slow IVFFlat index creation

**Explanation**: IVFFlat uses k-means clustering, which can be slow for large datasets.

**Workaround**:
1. Use `--skip-index` flag initially
2. Build index manually during off-peak hours
3. Consider HNSW index (faster build, but uses more memory)

```sql
-- HNSW alternative (pgvector 0.5.0+)
CREATE INDEX idx_vector_chunks_embedding_hnsw
ON vector_chunks_v1
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## 8. Rollback to File Backend

If PGVector has issues, you can always roll back:

1. Set `VECTOR_BACKEND=file`
2. Restart application
3. File-based index is still available in `data/vector_index/v1/`

No data loss!

---

## 9. Maintenance

### Vacuum & Analyze (Recommended after bulk insert)

```sql
VACUUM ANALYZE vector_chunks_v1;
```

### Update Statistics (For query planner)

```sql
ANALYZE vector_chunks_v1;
```

### Monitor Index Usage

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'vector_chunks_v1';
```

---

## 10. Next Steps (After Migration)

1. **Performance benchmarks**:
   - Compare file vs. PG query times
   - Measure recall@10 accuracy
   - Document in `STEP_NEXT_66_PGVECTOR_MIGRATION_PROOF.md`

2. **Integration with API**:
   - Update `apps/api/chat_vm.py` to use PG backend
   - Add fallback logic (PG → file if connection fails)

3. **UI enhancements**:
   - Display customer_view fields in comparison tables
   - Evidence accordion with chunk references
   - Filter by doc_type in UI

4. **Monitoring**:
   - Add Prometheus metrics for query latency
   - Alert on PG connection failures
   - Dashboard for vector search usage

---

**End of PGVector Migration Guide**
