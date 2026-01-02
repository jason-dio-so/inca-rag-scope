"""
STEP NEXT-66: PGVector Migration Script

Migrate file-based vector index to Postgres + pgvector.

Usage:
    python -m scripts.vector_ingest_pg --axis samsung
    python -m scripts.vector_ingest_pg --axis all

Prerequisites:
    - Postgres with pgvector extension enabled
    - Database: inca_rag_scope (or set PGDATABASE env var)
    - Table: vector_chunks_v1 (created by this script if not exists)
"""

import json
import argparse
import os
from pathlib import Path
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm


# Database connection
def get_db_connection():
    """Get Postgres connection (from env vars or defaults)"""
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5432'),
        database=os.getenv('PGDATABASE', 'inca_rag_scope'),
        user=os.getenv('PGUSER', 'postgres'),
        password=os.getenv('PGPASSWORD', '')
    )
    return conn


def create_table_if_not_exists(conn):
    """Create vector_chunks_v1 table with pgvector extension"""
    with conn.cursor() as cur:
        # Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vector_chunks_v1 (
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
        """)

        # Create indices
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vector_chunks_axis_doctype
            ON vector_chunks_v1 (axis, doc_type);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vector_chunks_insurer
            ON vector_chunks_v1 (insurer);
        """)

        # IVFFlat index for fast similarity search
        # NOTE: This requires some data to be present first
        # We'll create it after initial ingestion
        # cur.execute("""
        #     CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding_ivfflat
        #     ON vector_chunks_v1
        #     USING ivfflat (embedding vector_cosine_ops)
        #     WITH (lists = 100);
        # """)

    conn.commit()
    print("✅ Table vector_chunks_v1 created (or already exists)")


def ingest_axis(axis: str, index_dir: Path, conn):
    """
    Ingest vector index for a single axis into Postgres.

    Args:
        axis: Insurance axis
        index_dir: Vector index directory
        conn: Postgres connection
    """
    print(f"\n=== Ingesting {axis} ===")

    chunks_path = index_dir / f"{axis}__chunks.jsonl"
    embeddings_path = index_dir / f"{axis}__embeddings.npy"

    if not chunks_path.exists():
        print(f"  SKIP: {chunks_path} not found")
        return

    if not embeddings_path.exists():
        print(f"  SKIP: {embeddings_path} not found")
        return

    # Load chunks
    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))

    # Load embeddings
    embeddings = np.load(embeddings_path)

    print(f"  Loaded {len(chunks)} chunks, {embeddings.shape} embeddings")

    # Upsert into Postgres
    with conn.cursor() as cur:
        # Prepare data for bulk insert
        rows = []
        for chunk, embedding in zip(chunks, embeddings):
            row = (
                chunk['chunk_id'],
                chunk['axis'],
                chunk['insurer'],
                chunk['doc_type'],
                chunk.get('file_path'),
                chunk['page'],
                chunk['text'],
                chunk['content_hash'],
                embedding.tolist()  # Convert numpy array to list
            )
            rows.append(row)

        # Bulk upsert (ON CONFLICT DO UPDATE for idempotency)
        execute_values(
            cur,
            """
            INSERT INTO vector_chunks_v1
            (chunk_id, axis, insurer, doc_type, file_path, page, text, content_hash, embedding)
            VALUES %s
            ON CONFLICT (chunk_id)
            DO UPDATE SET
                axis = EXCLUDED.axis,
                insurer = EXCLUDED.insurer,
                doc_type = EXCLUDED.doc_type,
                file_path = EXCLUDED.file_path,
                page = EXCLUDED.page,
                text = EXCLUDED.text,
                content_hash = EXCLUDED.content_hash,
                embedding = EXCLUDED.embedding
            """,
            rows
        )

    conn.commit()
    print(f"  ✅ Ingested {len(rows)} chunks")


def create_vector_index(conn):
    """Create IVFFlat index for fast similarity search"""
    print("\n=== Creating vector index (IVFFlat) ===")

    with conn.cursor() as cur:
        # Check if we have enough data
        cur.execute("SELECT COUNT(*) FROM vector_chunks_v1;")
        count = cur.fetchone()[0]

        if count < 1000:
            print(f"  ⚠️  Only {count} rows, skipping index creation (need at least 1000)")
            return

        # Drop existing index if any
        cur.execute("DROP INDEX IF EXISTS idx_vector_chunks_embedding_ivfflat;")

        # Create IVFFlat index
        # lists = sqrt(rows) is a common heuristic
        lists = int(np.sqrt(count))
        lists = max(10, min(lists, 1000))  # Clamp to [10, 1000]

        print(f"  Creating IVFFlat index with {lists} lists...")

        cur.execute(f"""
            CREATE INDEX idx_vector_chunks_embedding_ivfflat
            ON vector_chunks_v1
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = {lists});
        """)

    conn.commit()
    print("  ✅ Vector index created")


def main():
    parser = argparse.ArgumentParser(description="Ingest vector index into Postgres")
    parser.add_argument(
        "--axis", type=str, default="all",
        help="Axis to ingest (default: all)"
    )
    parser.add_argument(
        "--index-dir", type=str, default="data/vector_index/v1",
        help="Vector index directory"
    )
    parser.add_argument(
        "--create-index", action="store_true",
        help="Create IVFFlat index after ingestion"
    )

    args = parser.parse_args()

    index_dir = Path(args.index_dir)

    # Axes
    axes = [
        "samsung", "meritz", "hanwha", "heungkuk", "hyundai",
        "kb", "db", "lotte_male", "lotte_female"
    ]

    # Connect to Postgres
    print("Connecting to Postgres...")
    conn = get_db_connection()
    print(f"✅ Connected to {conn.dsn}")

    # Create table
    create_table_if_not_exists(conn)

    # Ingest axes
    if args.axis == "all":
        for axis in axes:
            ingest_axis(axis, index_dir, conn)
    else:
        ingest_axis(args.axis, index_dir, conn)

    # Create vector index
    if args.create_index:
        create_vector_index(conn)

    conn.close()
    print("\n✅ Ingestion complete")


if __name__ == "__main__":
    main()
