-- inca-rag-scope: Q14 Premium Ranking Schema
-- STEP NEXT-W: Q14 보험료 가성비 Top-N Ranking
-- Purpose: Deterministic premium value ranking for Q14 responses

-- ==========================================
-- Table: q14_premium_ranking_v1
-- ==========================================

CREATE TABLE IF NOT EXISTS q14_premium_ranking_v1 (
    ranking_id SERIAL PRIMARY KEY,

    -- Identity
    insurer_key TEXT NOT NULL,           -- 보험사 키 (samsung, db, hanwha, ...)
    product_id TEXT NOT NULL,            -- 상품 ID (product_key format)

    -- Persona Dimensions
    age INTEGER NOT NULL,                -- 30, 40, 50 ONLY
    plan_variant TEXT NOT NULL,          -- GENERAL | NO_REFUND

    -- Coverage Amount (from compare_rows_v1 A4200_1)
    cancer_amt INTEGER NOT NULL,         -- 암진단비 (만원 단위, e.g., 3000 = 3천만원)

    -- Premium (from PREMIUM SSOT)
    premium_monthly INTEGER NOT NULL,    -- 월납 보험료 (원)

    -- Calculated Metric (LOCKED FORMULA)
    premium_per_10m NUMERIC(12,2) NOT NULL,  -- premium_monthly / (cancer_amt / 10_000_000)
                                             -- "1억원당 월보험료" (원)

    -- Ranking
    rank INTEGER NOT NULL,               -- 1, 2, 3 (Top-N per age × plan_variant)

    -- Traceability
    source JSONB NOT NULL,               -- {premium_table, coverage_table, baseDt, as_of_date}
    as_of_date DATE NOT NULL,            -- 랭킹 생성 기준일

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_q14_age CHECK (age IN (30, 40, 50)),
    CONSTRAINT chk_q14_plan_variant CHECK (plan_variant IN ('GENERAL', 'NO_REFUND')),
    CONSTRAINT chk_q14_rank CHECK (rank >= 1 AND rank <= 3),
    CONSTRAINT chk_q14_cancer_amt_positive CHECK (cancer_amt > 0),
    CONSTRAINT chk_q14_premium_positive CHECK (premium_monthly > 0),
    CONSTRAINT chk_q14_premium_per_10m_positive CHECK (premium_per_10m > 0),

    -- Unique constraint: one rank per (age, plan_variant, rank)
    CONSTRAINT uq_q14_ranking UNIQUE (age, plan_variant, rank, as_of_date)
);

-- Indexes for q14_premium_ranking_v1
CREATE INDEX IF NOT EXISTS idx_q14_ranking_lookup
    ON q14_premium_ranking_v1(age, plan_variant, rank);

CREATE INDEX IF NOT EXISTS idx_q14_ranking_insurer
    ON q14_premium_ranking_v1(insurer_key);

CREATE INDEX IF NOT EXISTS idx_q14_ranking_as_of_date
    ON q14_premium_ranking_v1(as_of_date);

-- ==========================================
-- View: q14_premium_ranking_current
-- ==========================================

CREATE OR REPLACE VIEW q14_premium_ranking_current AS
SELECT
    insurer_key,
    product_id,
    age,
    plan_variant,
    cancer_amt,
    premium_monthly,
    premium_per_10m,
    rank,
    source,
    as_of_date
FROM q14_premium_ranking_v1
WHERE as_of_date = (SELECT MAX(as_of_date) FROM q14_premium_ranking_v1)
ORDER BY age, plan_variant, rank;

-- ==========================================
-- Comments
-- ==========================================

COMMENT ON TABLE q14_premium_ranking_v1 IS
'STEP NEXT-W: Q14 보험료 가성비 Top-N ranking (age × plan_variant × rank)';

COMMENT ON COLUMN q14_premium_ranking_v1.cancer_amt IS
'암진단비 금액 (만원, e.g., 3000 = 3천만원) - from compare_rows_v1 A4200_1';

COMMENT ON COLUMN q14_premium_ranking_v1.premium_monthly IS
'월납 보험료 (원) - from PREMIUM SSOT (product_premium_quote_v2 or premium_quote)';

COMMENT ON COLUMN q14_premium_ranking_v1.premium_per_10m IS
'1억원당 월보험료 (원) - LOCKED FORMULA: premium_monthly / (cancer_amt / 10_000_000)
계산 예시: cancer_amt=3000만원, premium_monthly=50,000원
  → premium_per_10m = 50,000 / (30,000,000 / 10,000,000) = 50,000 / 3 = 16,666.67원';

COMMENT ON COLUMN q14_premium_ranking_v1.rank IS
'순위 (1/2/3) - 정렬 기준: premium_per_10m ASC, premium_monthly ASC, insurer_key ASC';

COMMENT ON COLUMN q14_premium_ranking_v1.source IS
'JSONB: {premium_table: "product_premium_quote_v2", coverage_table: "compare_rows_v1", baseDt: "2026-01-09", as_of_date: "2026-01-09"}';

COMMENT ON VIEW q14_premium_ranking_current IS
'Q14 ranking current view - latest as_of_date only, ordered by age/plan_variant/rank';

-- ==========================================
-- Validation Rules (Documentation)
-- ==========================================

-- Formula Validation:
--   premium_per_10m = premium_monthly / (cancer_amt_won / 10_000_000)
--   where: cancer_amt_won = cancer_amt * 10_000
--
-- Example:
--   cancer_amt = 3000 (3천만원)
--   cancer_amt_won = 3000 * 10_000 = 30,000,000원
--   premium_monthly = 50,000원
--   premium_per_10m = 50,000 / (30,000,000 / 10,000,000)
--                  = 50,000 / 3.0
--                  = 16,666.67원
--
-- Sorting Rules (LOCKED):
--   1. premium_per_10m ASC (lower is better = 가성비 우수)
--   2. premium_monthly ASC (tie-breaker: lower premium)
--   3. insurer_key ASC (tie-breaker: alphabetical)
--
-- Exclusion Rules:
--   - NULL/missing premium_monthly → EXCLUDE (not insert)
--   - NULL/missing cancer_amt → EXCLUDE (not insert)
--   - cancer_amt = 0 → EXCLUDE (division by zero)
--
-- Prohibited Operations:
--   ❌ Premium calculation/imputation/averaging
--   ❌ Cancer amount estimation/inference
--   ❌ Partial insurer ranking (must have complete data)
--   ❌ LLM-based ranking adjustment
