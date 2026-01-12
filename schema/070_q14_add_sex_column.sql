-- ============================================================================
-- Schema Migration 070: Add sex column to q14_premium_ranking_v1
-- ============================================================================
-- Date: 2026-01-12
-- Task: STEP NEXT-Q14-DB-CLEAN
--
-- Changes:
-- 1. Add sex column to q14_premium_ranking_v1
-- 2. Update UNIQUE constraint to include sex
-- 3. Backfill existing rows with sex='M' (current data is male-only)
--
-- Rationale:
-- - product_premium_quote_v2 has sex (M/F)
-- - Q14 must rank M and F separately
-- - Current UNIQUE (age, plan_variant, rank, as_of_date) is insufficient
-- ============================================================================

\echo '========================================';
\echo 'Migration 070: Add sex to Q14 rankings';
\echo '========================================';

-- ============================================================================
-- Step 1: Add sex column (nullable initially for backfill)
-- ============================================================================

ALTER TABLE q14_premium_ranking_v1
ADD COLUMN sex TEXT;

\echo 'Added sex column';

-- ============================================================================
-- Step 2: Backfill existing rows with sex='M'
-- ============================================================================
-- Current data (as_of_date=2025-11-26) is male-only based on diagnosis

UPDATE q14_premium_ranking_v1
SET sex = 'M'
WHERE sex IS NULL;

\echo 'Backfilled sex=M for existing rows';

-- ============================================================================
-- Step 3: Make sex NOT NULL
-- ============================================================================

ALTER TABLE q14_premium_ranking_v1
ALTER COLUMN sex SET NOT NULL;

\echo 'Set sex NOT NULL';

-- ============================================================================
-- Step 4: Add CHECK constraint for sex values
-- ============================================================================

ALTER TABLE q14_premium_ranking_v1
ADD CONSTRAINT chk_q14_sex CHECK (sex IN ('M', 'F', 'UNISEX'));

\echo 'Added CHECK constraint for sex';

-- ============================================================================
-- Step 5: Drop old UNIQUE constraint
-- ============================================================================

ALTER TABLE q14_premium_ranking_v1
DROP CONSTRAINT uq_q14_ranking;

\echo 'Dropped old UNIQUE constraint';

-- ============================================================================
-- Step 6: Create new UNIQUE constraint with sex
-- ============================================================================

ALTER TABLE q14_premium_ranking_v1
ADD CONSTRAINT uq_q14_ranking UNIQUE (age, sex, plan_variant, rank, as_of_date);

\echo 'Created new UNIQUE constraint (age, sex, plan_variant, rank, as_of_date)';

-- ============================================================================
-- Step 7: Update lookup index to include sex
-- ============================================================================

DROP INDEX IF EXISTS idx_q14_ranking_lookup;

CREATE INDEX idx_q14_ranking_lookup ON q14_premium_ranking_v1 (age, sex, plan_variant, rank);

\echo 'Updated lookup index with sex';

-- ============================================================================
-- Verification
-- ============================================================================

\echo '';
\echo 'Verification:';
\d q14_premium_ranking_v1

\echo '';
\echo 'Migration 070 complete';
