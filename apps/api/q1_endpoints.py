"""
Q1 Premium Ranking Endpoints

Purpose: BY_COVERAGE mode premium ranking with canonical coverage resolution
Rules:
- SSOT DB only (inca_ssot@5433)
- Product-level aggregation: (insurer_code, product_code)
- MANDATORY: insurer_name + product_name in all rows
- EXCLUDE rows without insurer_name OR product_name
"""

import logging
from typing import List, Optional
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import DictCursor

from apps.api.utils.coverage_resolver import resolve_coverage_candidates

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class Q1CoverageRankingRequest(BaseModel):
    """Request for BY_COVERAGE premium ranking"""
    ins_cds: List[str]  # ["N01", "N02", ...]
    age: int  # 30|40|50
    gender: str  # "M"|"F"
    sort_by: str = "total"  # "total"|"monthly"
    plan_variant_scope: str = "all"  # "all"|"standard"|"no_refund"
    coverage_codes: List[str]  # ["A4200_1", ...]
    as_of_date: str = "2025-11-26"


class Q1PremiumRow(BaseModel):
    """Single premium ranking row"""
    rank: int
    insurer_code: str
    insurer_name: str
    product_code: str
    product_name: str
    premium_monthly: Optional[int] = None
    premium_total: Optional[int] = None
    premium_monthly_general: Optional[int] = None
    premium_total_general: Optional[int] = None


class CoverageLabel(BaseModel):
    """Coverage metadata"""
    coverage_code: str
    canonical_name: str


class Q1ViewModel(BaseModel):
    """Q1 response view model"""
    mode: str = "BY_COVERAGE"
    coverage_codes: List[str]
    coverage_labels: List[CoverageLabel]
    rows: List[Q1PremiumRow]


class Q1Response(BaseModel):
    """Q1 endpoint response"""
    kind: str = "Q1"
    viewModel: Q1ViewModel


class Q1CoverageCandidatesRequest(BaseModel):
    """Request for coverage candidate resolution"""
    query_text: str
    max_candidates: int = 3


class CoverageCandidate(BaseModel):
    """Single coverage candidate"""
    coverage_code: str
    canonical_name: str
    score: float
    match_reason: str


class Q1CoverageCandidatesResponse(BaseModel):
    """Response for coverage candidates endpoint"""
    query_text: str
    candidates: List[CoverageCandidate]


# ============================================================================
# Business Logic
# ============================================================================

def get_coverage_labels(conn, coverage_codes: List[str]) -> List[CoverageLabel]:
    """Get canonical names for coverage codes"""
    if not coverage_codes:
        return []

    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT coverage_code, canonical_name
            FROM coverage_canonical
            WHERE coverage_code = ANY(%s)
            ORDER BY coverage_code
        """, (coverage_codes,))

        return [
            CoverageLabel(
                coverage_code=row['coverage_code'],
                canonical_name=row['canonical_name']
            )
            for row in cur.fetchall()
        ]


def aggregate_coverage_premiums(
    conn,
    ins_cds: List[str],
    age: int,
    sex: str,
    plan_variant_scope: str,
    coverage_codes: List[str],
    as_of_date: str
) -> List[dict]:
    """
    Aggregate coverage premiums by (insurer_code, product_code)

    Option A: When scope="all", aggregate BOTH NO_REFUND and GENERAL separately

    Returns: List of dicts with aggregated premiums
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        if plan_variant_scope == "all":
            # Aggregate BOTH plan variants, OUTER JOIN to get complete picture
            cur.execute("""
                WITH no_refund_agg AS (
                    SELECT
                        cpq.ins_cd,
                        cpq.product_id,
                        SUM(cpq.premium_monthly_coverage) as sum_premium_monthly,
                        MAX(cpq.pay_term_years) as pay_term_years
                    FROM coverage_premium_quote cpq
                    WHERE cpq.ins_cd = ANY(%s)
                      AND cpq.age = %s
                      AND cpq.sex = %s
                      AND cpq.plan_variant = 'NO_REFUND'
                      AND cpq.coverage_code = ANY(%s)
                      AND cpq.as_of_date = %s
                      AND cpq.premium_monthly_coverage IS NOT NULL
                    GROUP BY cpq.ins_cd, cpq.product_id
                ),
                general_agg AS (
                    SELECT
                        cpq.ins_cd,
                        cpq.product_id,
                        SUM(cpq.premium_monthly_coverage) as sum_premium_monthly,
                        MAX(cpq.pay_term_years) as pay_term_years
                    FROM coverage_premium_quote cpq
                    WHERE cpq.ins_cd = ANY(%s)
                      AND cpq.age = %s
                      AND cpq.sex = %s
                      AND cpq.plan_variant = 'GENERAL'
                      AND cpq.coverage_code = ANY(%s)
                      AND cpq.as_of_date = %s
                      AND cpq.premium_monthly_coverage IS NOT NULL
                    GROUP BY cpq.ins_cd, cpq.product_id
                ),
                combined AS (
                    SELECT
                        COALESCE(nr.ins_cd, g.ins_cd) as ins_cd,
                        COALESCE(nr.product_id, g.product_id) as product_id,
                        nr.sum_premium_monthly as premium_monthly_no_refund,
                        nr.pay_term_years as pay_term_years_no_refund,
                        g.sum_premium_monthly as premium_monthly_general,
                        g.pay_term_years as pay_term_years_general
                    FROM no_refund_agg nr
                    FULL OUTER JOIN general_agg g ON nr.ins_cd = g.ins_cd AND nr.product_id = g.product_id
                ),
                with_names AS (
                    SELECT
                        c.ins_cd as insurer_code,
                        c.product_id as product_code,
                        c.premium_monthly_no_refund as premium_monthly,
                        CASE
                            WHEN c.pay_term_years_no_refund IS NOT NULL AND c.pay_term_years_no_refund > 0
                            THEN c.premium_monthly_no_refund * c.pay_term_years_no_refund * 12
                            ELSE c.premium_monthly_no_refund * 20 * 12
                        END as premium_total,
                        c.premium_monthly_general,
                        CASE
                            WHEN c.pay_term_years_general IS NOT NULL AND c.pay_term_years_general > 0
                            THEN c.premium_monthly_general * c.pay_term_years_general * 12
                            ELSE c.premium_monthly_general * 20 * 12
                        END as premium_total_general,
                        i.insurer_name_ko as insurer_name,
                        p.product_full_name as product_name
                    FROM combined c
                    LEFT JOIN insurer i ON c.ins_cd = i.ins_cd
                    LEFT JOIN product p ON c.product_id = p.product_id
                )
                SELECT *
                FROM with_names
                WHERE insurer_name IS NOT NULL
                  AND product_name IS NOT NULL
                  AND product_name != ''
                ORDER BY insurer_code, product_code
            """, (ins_cds, age, sex, coverage_codes, as_of_date,
                  ins_cds, age, sex, coverage_codes, as_of_date))

            return [dict(row) for row in cur.fetchall()]

        else:
            # Single plan variant (standard or no_refund)
            plan_variant = 'GENERAL' if plan_variant_scope == "standard" else 'NO_REFUND'

            cur.execute("""
                WITH coverage_agg AS (
                    SELECT
                        cpq.ins_cd,
                        cpq.product_id,
                        SUM(cpq.premium_monthly_coverage) as sum_premium_monthly,
                        MAX(cpq.pay_term_years) as pay_term_years
                    FROM coverage_premium_quote cpq
                    WHERE cpq.ins_cd = ANY(%s)
                      AND cpq.age = %s
                      AND cpq.sex = %s
                      AND cpq.plan_variant = %s
                      AND cpq.coverage_code = ANY(%s)
                      AND cpq.as_of_date = %s
                      AND cpq.premium_monthly_coverage IS NOT NULL
                    GROUP BY cpq.ins_cd, cpq.product_id
                ),
                with_names AS (
                    SELECT
                        agg.ins_cd as insurer_code,
                        agg.product_id as product_code,
                        agg.sum_premium_monthly as premium_monthly,
                        CASE
                            WHEN agg.pay_term_years IS NOT NULL AND agg.pay_term_years > 0
                            THEN agg.sum_premium_monthly * agg.pay_term_years * 12
                            ELSE agg.sum_premium_monthly * 20 * 12
                        END as premium_total,
                        i.insurer_name_ko as insurer_name,
                        p.product_full_name as product_name
                    FROM coverage_agg agg
                    LEFT JOIN insurer i ON agg.ins_cd = i.ins_cd
                    LEFT JOIN product p ON agg.product_id = p.product_id
                )
                SELECT *
                FROM with_names
                WHERE insurer_name IS NOT NULL
                  AND product_name IS NOT NULL
                  AND product_name != ''
                ORDER BY insurer_code, product_code
            """, (ins_cds, age, sex, plan_variant, coverage_codes, as_of_date))

            return [dict(row) for row in cur.fetchall()]


def build_ranking_rows(
    aggregated_data: List[dict],
    sort_by: str,
    plan_variant_scope: str
) -> List[Q1PremiumRow]:
    """
    Build ranking rows from aggregated data

    For scope="all": rows already have both NO_REFUND and GENERAL fields
    For scope="standard"|"no_refund": rows have single premium fields
    """
    products = []

    for row in aggregated_data:
        if plan_variant_scope == "all":
            # Rows from FULL OUTER JOIN already have both fields
            products.append({
                'insurer_code': row['insurer_code'],
                'insurer_name': row['insurer_name'],
                'product_code': row['product_code'],
                'product_name': row['product_name'],
                'premium_monthly': row.get('premium_monthly'),
                'premium_total': row.get('premium_total'),
                'premium_monthly_general': row.get('premium_monthly_general'),
                'premium_total_general': row.get('premium_total_general'),
            })
        else:
            # Single plan variant: map to appropriate fields
            if plan_variant_scope == "standard":
                products.append({
                    'insurer_code': row['insurer_code'],
                    'insurer_name': row['insurer_name'],
                    'product_code': row['product_code'],
                    'product_name': row['product_name'],
                    'premium_monthly': None,
                    'premium_total': None,
                    'premium_monthly_general': row['premium_monthly'],
                    'premium_total_general': row['premium_total'],
                })
            else:  # "no_refund"
                products.append({
                    'insurer_code': row['insurer_code'],
                    'insurer_name': row['insurer_name'],
                    'product_code': row['product_code'],
                    'product_name': row['product_name'],
                    'premium_monthly': row['premium_monthly'],
                    'premium_total': row['premium_total'],
                    'premium_monthly_general': None,
                    'premium_total_general': None,
                })

    # Determine sort key based on sort_by and plan_variant_scope
    if sort_by == "monthly":
        if plan_variant_scope == "standard":
            sort_key = lambda p: p['premium_monthly_general'] or float('inf')
        elif plan_variant_scope == "no_refund":
            sort_key = lambda p: p['premium_monthly'] or float('inf')
        else:  # "all"
            # Use NO_REFUND monthly if available, otherwise GENERAL
            sort_key = lambda p: p['premium_monthly'] or p['premium_monthly_general'] or float('inf')
    else:  # "total"
        if plan_variant_scope == "standard":
            sort_key = lambda p: p['premium_total_general'] or float('inf')
        elif plan_variant_scope == "no_refund":
            sort_key = lambda p: p['premium_total'] or float('inf')
        else:  # "all"
            # Use NO_REFUND total if available, otherwise GENERAL
            sort_key = lambda p: p['premium_total'] or p['premium_total_general'] or float('inf')

    # Sort and assign ranks
    products.sort(key=sort_key)

    # Top 4 only
    top4 = products[:4]

    rows = []
    for rank, product in enumerate(top4, start=1):
        rows.append(Q1PremiumRow(
            rank=rank,
            insurer_code=product['insurer_code'],
            insurer_name=product['insurer_name'],
            product_code=product['product_code'],
            product_name=product['product_name'],
            premium_monthly=product['premium_monthly'],
            premium_total=product['premium_total'],
            premium_monthly_general=product['premium_monthly_general'],
            premium_total_general=product['premium_total_general']
        ))

    return rows


def execute_coverage_ranking(request: Q1CoverageRankingRequest, conn) -> Q1Response:
    """Execute BY_COVERAGE premium ranking"""
    logger.info(f"Q1 BY_COVERAGE: age={request.age}, sex={request.gender}, "
                f"coverage_codes={request.coverage_codes}, "
                f"plan_variant_scope={request.plan_variant_scope}, "
                f"sort_by={request.sort_by}")

    # Get coverage labels
    coverage_labels = get_coverage_labels(conn, request.coverage_codes)

    # Aggregate premiums
    aggregated_data = aggregate_coverage_premiums(
        conn,
        ins_cds=request.ins_cds,
        age=request.age,
        sex=request.gender,
        plan_variant_scope=request.plan_variant_scope,
        coverage_codes=request.coverage_codes,
        as_of_date=request.as_of_date
    )

    logger.info(f"Q1 BY_COVERAGE: aggregated {len(aggregated_data)} product-variant rows")

    # Build ranking rows
    rows = build_ranking_rows(
        aggregated_data,
        sort_by=request.sort_by,
        plan_variant_scope=request.plan_variant_scope
    )

    logger.info(f"Q1 BY_COVERAGE: returning top {len(rows)} products")

    return Q1Response(
        kind="Q1",
        viewModel=Q1ViewModel(
            mode="BY_COVERAGE",
            coverage_codes=request.coverage_codes,
            coverage_labels=coverage_labels,
            rows=rows
        )
    )


def execute_coverage_candidates(request: Q1CoverageCandidatesRequest, conn) -> Q1CoverageCandidatesResponse:
    """
    Resolve coverage free text to canonical coverage_code candidates

    Uses deterministic matching strategies (NO LLM):
    1. Exact match on canonical_name
    2. Contains match on canonical_name
    3. Contains match on insurer_coverage_name (alias)
    4. Token match on canonical_name

    Returns max 3 candidates sorted by score desc
    """
    logger.info(f"Q1 coverage_candidates: query_text='{request.query_text}', max_candidates={request.max_candidates}")

    # Use existing coverage_resolver utility (it creates its own connection)
    candidates = resolve_coverage_candidates(
        query_text=request.query_text,
        max_candidates=request.max_candidates
    )

    logger.info(f"Q1 coverage_candidates: found {len(candidates)} candidates")

    # Convert to response format
    candidate_models = [
        CoverageCandidate(
            coverage_code=c.coverage_code,
            canonical_name=c.canonical_name,
            score=c.score,
            match_reason=c.match_reason
        )
        for c in candidates
    ]

    return Q1CoverageCandidatesResponse(
        query_text=request.query_text,
        candidates=candidate_models
    )
