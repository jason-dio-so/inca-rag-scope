-- ============================================================================
-- STEP NEXT-DBR-2: Premium SSOT Natural Key Lock
-- ============================================================================
--
-- Purpose:
--   Add UNIQUE natural key constraints to premium tables to enable
--   proper UPSERT operations with ON CONFLICT DO UPDATE.
--
-- Constitutional Rules:
--   1. UNIQUE keys MUST include as_of_date (NOT base_dt)
--   2. Natural keys reflect business uniqueness (insurer + product + dimensions)
--   3. Enable idempotent API loads (re-run with same baseDt = safe upsert)
--
-- Tables Modified:
--   - premium_quote: Add UNIQUE constraint
--   - coverage_premium_quote: Add UNIQUE constraint
--   - product_premium_quote_v2: Already has UNIQUE constraint (verify only)
--
-- Author: STEP NEXT-DBR-2
-- Date: 2026-01-09
-- ============================================================================

-- ============================================================================
-- 1. premium_quote: UNIQUE Natural Key
-- ============================================================================

-- Drop existing constraint if exists (idempotent)
ALTER TABLE premium_quote
DROP CONSTRAINT IF EXISTS uq_premium_quote_natural_key;

-- Add UNIQUE constraint with as_of_date
ALTER TABLE premium_quote
ADD CONSTRAINT uq_premium_quote_natural_key
UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, as_of_date);

COMMENT ON CONSTRAINT uq_premium_quote_natural_key ON premium_quote IS
'Natural key for premium quotes: uniqueness per (insurer, product, plan_variant, age, sex, smoke, as_of_date)';

-- ============================================================================
-- 2. coverage_premium_quote: UNIQUE Natural Key
-- ============================================================================

-- Drop existing constraint if exists (idempotent)
ALTER TABLE coverage_premium_quote
DROP CONSTRAINT IF EXISTS uq_coverage_premium_natural_key;

-- Add UNIQUE constraint with as_of_date AND coverage_code
-- NOTE: Coverage-level granularity requires coverage_code in key
ALTER TABLE coverage_premium_quote
ADD CONSTRAINT uq_coverage_premium_natural_key
UNIQUE (insurer_key, product_id, coverage_code, plan_variant, age, sex, smoke, as_of_date);

COMMENT ON CONSTRAINT uq_coverage_premium_natural_key ON coverage_premium_quote IS
'Natural key for coverage premiums: uniqueness per (insurer, product, coverage, plan_variant, age, sex, smoke, as_of_date)';

-- ============================================================================
-- 3. product_premium_quote_v2: Verify Existing UNIQUE Constraint
-- ============================================================================

-- This table already has uq_product_premium constraint:
--   UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke,
--           pay_term_years, ins_term_years, as_of_date)
--
-- NO ACTION REQUIRED (already correct)

-- Verification query (for audit):
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'product_premium_quote_v2'::regclass AND contype = 'u';

-- ============================================================================
-- 4. Performance Indexes (as_of_date lookup)
-- ============================================================================

-- Index for premium_quote date-based queries
CREATE INDEX IF NOT EXISTS idx_premium_quote_as_of_date
ON premium_quote(as_of_date DESC);

COMMENT ON INDEX idx_premium_quote_as_of_date IS
'Performance index for date-based premium queries (e.g., latest premium, date range filters)';

-- Index for coverage_premium_quote date-based queries
CREATE INDEX IF NOT EXISTS idx_coverage_premium_as_of_date
ON coverage_premium_quote(as_of_date DESC);

COMMENT ON INDEX idx_coverage_premium_as_of_date IS
'Performance index for date-based coverage premium queries';

-- Index for product_premium_quote_v2 date-based queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_product_premium_v2_as_of_date
ON product_premium_quote_v2(as_of_date DESC);

COMMENT ON INDEX idx_product_premium_v2_as_of_date IS
'Performance index for date-based product premium queries';

-- ============================================================================
-- Verification Queries (for audit log)
-- ============================================================================

-- Run these after migration to verify:
--
-- 1. Check UNIQUE constraints:
--    SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid)
--    FROM pg_constraint
--    WHERE contype = 'u'
--      AND conrelid::regclass::text IN ('premium_quote', 'coverage_premium_quote', 'product_premium_quote_v2')
--    ORDER BY conrelid, conname;
--
-- 2. Check indexes:
--    SELECT tablename, indexname, indexdef
--    FROM pg_indexes
--    WHERE tablename IN ('premium_quote', 'coverage_premium_quote', 'product_premium_quote_v2')
--      AND indexname LIKE '%as_of_date%'
--    ORDER BY tablename, indexname;

-- ============================================================================
-- Migration Log
-- ============================================================================
-- Date: 2026-01-09
-- Applied by: STEP NEXT-DBR-2
-- Verification: Run queries above and capture output to audit doc
-- ============================================================================
