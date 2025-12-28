-- ============================================================================
-- STEP NEXT-DB-2C-γ Schema Patch: Idempotent UPSERT with Natural Keys
-- ============================================================================
-- Date: 2025-12-28
-- Purpose: Add instance_key and evidence_key for idempotent upsert operations
--
-- CRITICAL FIX:
-- 1. coverage_instance: Add instance_key (natural key) + UNIQUE index
--    - Enables idempotent upsert even when coverage_code is NULL (unmatched)
-- 2. evidence_ref: Add evidence_key (natural key) + UNIQUE index
--    - Prevents duplicate evidence rows on repeated upsert
-- 3. Add updated_at columns for tracking last modification time
--
-- DEPLOYMENT SEQUENCE:
-- 1. Run this patch to add columns (without NOT NULL constraint)
-- 2. Modify loader to generate instance_key and evidence_key
-- 3. Run loader with reset_then_load mode to populate keys
-- 4. Manually add NOT NULL constraint after data backfill (optional)
-- ============================================================================

-- ============================================================================
-- PART 1: coverage_instance - Add instance_key
-- ============================================================================

-- Add instance_key column (nullable initially for safe migration)
ALTER TABLE coverage_instance
ADD COLUMN instance_key TEXT;

-- Add updated_at column
ALTER TABLE coverage_instance
ADD COLUMN updated_at TIMESTAMPTZ;

-- Add UNIQUE index on instance_key (will enforce after backfill)
-- Note: Index allows NULL values, but loader will ensure instance_key is always populated
CREATE UNIQUE INDEX idx_coverage_instance_key ON coverage_instance(instance_key);

COMMENT ON COLUMN coverage_instance.instance_key IS
'Natural key: {insurer_key}|{product_key}|{variant_key_or_}|{coverage_code_or_}|{coverage_name_raw}. Deterministic, loader-generated only.';

-- ============================================================================
-- PART 2: evidence_ref - Add evidence_key
-- ============================================================================

-- Add evidence_key column (nullable initially for safe migration)
ALTER TABLE evidence_ref
ADD COLUMN evidence_key TEXT;

-- Add updated_at column
ALTER TABLE evidence_ref
ADD COLUMN updated_at TIMESTAMPTZ;

-- Add UNIQUE index on evidence_key (will enforce after backfill)
CREATE UNIQUE INDEX idx_evidence_key ON evidence_ref(evidence_key);

COMMENT ON COLUMN evidence_ref.evidence_key IS
'Natural key: {instance_key}|{file_path}|{doc_type}|{page}|{rank}. Deterministic, loader-generated only. Does NOT include snippet/match_keyword.';

-- ============================================================================
-- PART 3: amount_fact - Add updated_at
-- ============================================================================

-- Add updated_at column for consistency
ALTER TABLE amount_fact
ADD COLUMN updated_at TIMESTAMPTZ;

-- ============================================================================
-- DEPLOYMENT NOTES
-- ============================================================================
--
-- After running this patch:
-- 1. Update loader to generate instance_key and evidence_key
-- 2. Run: python -m apps.loader.step9_loader --mode reset_then_load
-- 3. Verify all rows have non-NULL instance_key and evidence_key
-- 4. (Optional) Add NOT NULL constraint:
--    ALTER TABLE coverage_instance ALTER COLUMN instance_key SET NOT NULL;
--    ALTER TABLE evidence_ref ALTER COLUMN evidence_key SET NOT NULL;
--
-- ============================================================================
-- End of STEP NEXT-DB-2C-γ Patch
-- ============================================================================
