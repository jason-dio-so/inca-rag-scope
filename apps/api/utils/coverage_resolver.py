"""
Coverage Resolver - Canonical Coverage Code Resolution

Purpose: Resolve user's free-text coverage query to canonical coverage_code(s)
Rules:
- NO LLM, deterministic only
- SSOT DB only (inca_ssot@5433)
- Max 3 candidates
- Auto-confirm only if exactly 1 candidate
"""

import os
import re
from typing import List, Optional
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import DictCursor


@dataclass
class CoverageCandidate:
    """Coverage resolution candidate"""
    coverage_code: str
    canonical_name: str
    score: float
    match_reason: str


def normalize_text(text: str) -> str:
    """Normalize Korean text for matching"""
    if not text:
        return ""

    # Remove spaces, special chars, lowercase
    normalized = text.lower()
    normalized = re.sub(r'\s+', '', normalized)
    normalized = re.sub(r'[^\w가-힣]', '', normalized)

    return normalized


def get_db_connection():
    """Get SSOT database connection"""
    ssot_db_url = os.environ.get('SSOT_DB_URL')
    if not ssot_db_url:
        raise ValueError("SSOT_DB_URL environment variable not set")

    # Parse postgresql://user:password@host:port/dbname
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', ssot_db_url)
    if not match:
        raise ValueError(f"Invalid SSOT_DB_URL format: {ssot_db_url}")

    user, password, host, port, dbname = match.groups()

    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        dbname=dbname
    )
    return conn


def resolve_coverage_candidates(query_text: str, max_candidates: int = 3) -> List[CoverageCandidate]:
    """
    Resolve coverage query to canonical coverage_code candidates

    Args:
        query_text: User's free-text coverage query (e.g., "암진단비", "뇌졸중")
        max_candidates: Maximum number of candidates to return (default 3)

    Returns:
        List of CoverageCandidate, sorted by score descending

    Resolution strategy:
        1. Exact match on canonical_name
        2. Contains match on canonical_name
        3. Contains match on insurer_coverage_name (aliases)
        4. Token match on canonical_name
    """
    if not query_text or not query_text.strip():
        return []

    normalized_query = normalize_text(query_text)
    if not normalized_query:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            candidates = []
            seen_codes = set()

            # Strategy 1: Exact match on canonical_name (score=100)
            cur.execute("""
                SELECT coverage_code, canonical_name
                FROM coverage_canonical
                WHERE LOWER(REGEXP_REPLACE(canonical_name, '[^가-힣a-zA-Z0-9]', '', 'g')) = %s
                LIMIT 3
            """, (normalized_query,))

            for row in cur.fetchall():
                if row['coverage_code'] not in seen_codes:
                    candidates.append(CoverageCandidate(
                        coverage_code=row['coverage_code'],
                        canonical_name=row['canonical_name'],
                        score=100.0,
                        match_reason='exact_canonical'
                    ))
                    seen_codes.add(row['coverage_code'])

            # Strategy 2: Contains match on canonical_name (score=80)
            if len(candidates) < max_candidates:
                cur.execute("""
                    SELECT coverage_code, canonical_name
                    FROM coverage_canonical
                    WHERE LOWER(REGEXP_REPLACE(canonical_name, '[^가-힣a-zA-Z0-9]', '', 'g')) LIKE %s
                    LIMIT 10
                """, (f'%{normalized_query}%',))

                for row in cur.fetchall():
                    if row['coverage_code'] not in seen_codes:
                        candidates.append(CoverageCandidate(
                            coverage_code=row['coverage_code'],
                            canonical_name=row['canonical_name'],
                            score=80.0,
                            match_reason='contains_canonical'
                        ))
                        seen_codes.add(row['coverage_code'])

                        if len(candidates) >= max_candidates:
                            break

            # Strategy 3: Contains match on insurer_coverage_name (score=60)
            if len(candidates) < max_candidates:
                cur.execute("""
                    SELECT DISTINCT cm.coverage_code, cc.canonical_name
                    FROM coverage_mapping_ssot cm
                    JOIN coverage_canonical cc ON cm.coverage_code = cc.coverage_code
                    WHERE LOWER(REGEXP_REPLACE(cm.insurer_coverage_name, '[^가-힣a-zA-Z0-9]', '', 'g')) LIKE %s
                      AND cm.status = 'ACTIVE'
                    LIMIT 10
                """, (f'%{normalized_query}%',))

                for row in cur.fetchall():
                    if row['coverage_code'] not in seen_codes:
                        candidates.append(CoverageCandidate(
                            coverage_code=row['coverage_code'],
                            canonical_name=row['canonical_name'],
                            score=60.0,
                            match_reason='contains_alias'
                        ))
                        seen_codes.add(row['coverage_code'])

                        if len(candidates) >= max_candidates:
                            break

            # Strategy 4: Token match on canonical_name (score=40)
            if len(candidates) < max_candidates and len(normalized_query) >= 2:
                # Extract tokens (2-char minimum)
                tokens = []
                for i in range(len(normalized_query) - 1):
                    tokens.append(normalized_query[i:i+2])

                if tokens:
                    token_pattern = '|'.join(re.escape(t) for t in tokens[:5])  # Use first 5 tokens max

                    cur.execute("""
                        SELECT coverage_code, canonical_name
                        FROM coverage_canonical
                        WHERE LOWER(REGEXP_REPLACE(canonical_name, '[^가-힣a-zA-Z0-9]', '', 'g')) ~ %s
                        LIMIT 10
                    """, (token_pattern,))

                    for row in cur.fetchall():
                        if row['coverage_code'] not in seen_codes:
                            candidates.append(CoverageCandidate(
                                coverage_code=row['coverage_code'],
                                canonical_name=row['canonical_name'],
                                score=40.0,
                                match_reason='token_canonical'
                            ))
                            seen_codes.add(row['coverage_code'])

                            if len(candidates) >= max_candidates:
                                break

            # Sort by score descending
            candidates.sort(key=lambda c: c.score, reverse=True)

            return candidates[:max_candidates]

    finally:
        conn.close()


def auto_confirm_coverage(query_text: str) -> Optional[str]:
    """
    Resolve coverage query and auto-confirm if exactly 1 candidate

    Args:
        query_text: User's coverage query

    Returns:
        coverage_code if exactly 1 candidate found, None otherwise
    """
    candidates = resolve_coverage_candidates(query_text, max_candidates=3)

    if len(candidates) == 1:
        return candidates[0].coverage_code

    return None
