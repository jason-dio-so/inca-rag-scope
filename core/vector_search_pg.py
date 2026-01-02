"""
STEP NEXT-66: PGVector Search Backend

Postgres + pgvector backend for vector search (same interface as file backend).

Usage:
    Set environment variable: VECTOR_BACKEND=pg
"""

import os
from typing import List, Optional
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor

from core.vector_search_file import ChunkHit, get_model


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


def search_chunks_pg(
    axis: str,
    query: str,
    doc_types: Optional[List[str]] = None,
    top_k: int = 10
) -> List[ChunkHit]:
    """
    Search for chunks using Postgres + pgvector.

    Args:
        axis: Insurance axis
        query: Search query text
        doc_types: Filter by doc_type
        top_k: Number of results

    Returns:
        List of ChunkHit objects
    """
    # Get embedding model
    model = get_model()

    # Encode query
    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    # Convert to list for Postgres
    query_vec_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'

    # Build SQL query
    sql = """
        SELECT
            chunk_id,
            axis,
            doc_type,
            page,
            text,
            file_path,
            1 - (embedding <=> %s::vector) AS score
        FROM vector_chunks_v1
        WHERE axis = %s
    """

    params = [query_vec_str, axis]

    if doc_types:
        placeholders = ','.join(['%s'] * len(doc_types))
        sql += f" AND doc_type IN ({placeholders})"
        params.extend(doc_types)

    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_vec_str, top_k])

    # Execute query
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        # Convert to ChunkHit objects
        hits = []
        for row in rows:
            hit = ChunkHit(
                chunk_id=row['chunk_id'],
                axis=row['axis'],
                doc_type=row['doc_type'],
                page=row['page'],
                text=row['text'][:500],  # Truncate for preview
                score=float(row['score']),
                file_path=row.get('file_path')
            )
            hits.append(hit)

        return hits
    finally:
        conn.close()
