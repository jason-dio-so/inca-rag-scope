-- ============================================================================
-- Schema Migration 080: Create q14_premium_top4_v1 table
-- ============================================================================
-- Date: 2026-01-12
-- Task: STEP NEXT-FINAL
--
-- Purpose:
-- Q14 "보험료 Top4" table (separate from Q1 "가성비 Top3")
-- Stores pure premium ranking (no premium_per_10m calculation)
--
-- Sorting: ORDER BY premium_monthly ASC, insurer_key ASC LIMIT 4
-- ============================================================================

\echo '========================================'
\echo 'Migration 080: Create Q14 Premium Top4 table'
\echo '========================================'

-- ============================================================================
-- Create q14_premium_top4_v1 table
-- ============================================================================

CREATE TABLE IF NOT EXISTS q14_premium_top4_v1 (
    id SERIAL PRIMARY KEY,
    as_of_date DATE NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    plan_variant TEXT NOT NULL,
    rank INTEGER NOT NULL,
    insurer_key TEXT NOT NULL,
    product_id TEXT NOT NULL,
    premium_monthly NUMERIC NOT NULL,
    premium_total NUMERIC NOT NULL,
    source JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

\echo 'Created q14_premium_top4_v1 table'

-- ============================================================================
-- Add CHECK constraints
-- ============================================================================

ALTER TABLE q14_premium_top4_v1
ADD CONSTRAINT chk_q14_top4_sex CHECK (sex IN ('M', 'F', 'UNISEX'));

ALTER TABLE q14_premium_top4_v1
ADD CONSTRAINT chk_q14_top4_rank CHECK (rank BETWEEN 1 AND 4);

\echo 'Added CHECK constraints'

-- ============================================================================
-- Create UNIQUE constraint
-- ============================================================================
-- Ensures exactly 1 product per rank per segment

ALTER TABLE q14_premium_top4_v1
ADD CONSTRAINT uq_q14_top4_ranking UNIQUE (as_of_date, age, sex, plan_variant, rank);

\echo 'Created UNIQUE constraint (as_of_date, age, sex, plan_variant, rank)'

-- ============================================================================
-- Create indexes
-- ============================================================================

CREATE INDEX idx_q14_top4_lookup ON q14_premium_top4_v1 (as_of_date, age, sex, plan_variant, rank);

CREATE INDEX idx_q14_top4_insurer ON q14_premium_top4_v1 (insurer_key, product_id);

\echo 'Created indexes'

-- ============================================================================
-- Verification
-- ============================================================================

\echo ''
\echo 'Verification:'
\d q14_premium_top4_v1

\echo ''
\echo 'Migration 080 complete'
