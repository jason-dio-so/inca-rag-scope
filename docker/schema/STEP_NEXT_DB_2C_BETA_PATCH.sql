-- STEP NEXT-DB-2C-β Schema Patch
-- Date: 2025-12-28
-- Purpose: Allow unmatched coverages (coverage_code NULL for mapping_status='unmatched')
--
-- CRITICAL FIX:
-- - coverage_instance.coverage_code was NOT NULL, causing data loss (unmatched rows skipped)
-- - Change to NULLABLE to support mapping_status='unmatched' with coverage_code=NULL
-- - matched rows MUST have coverage_code (enforced by loader logic, not DB constraint)

-- ============================================================================
-- 1. ALTER coverage_instance.coverage_code to NULLABLE
-- ============================================================================
ALTER TABLE coverage_instance
ALTER COLUMN coverage_code DROP NOT NULL;

-- Verify constraint removed
COMMENT ON COLUMN coverage_instance.coverage_code IS
'Coverage code FK to coverage_canonical. NULL allowed for mapping_status=unmatched. matched rows MUST have non-NULL value (enforced by loader).';

-- ============================================================================
-- 2. Add CHECK constraint (optional, for clarity)
-- ============================================================================
-- Ensure matched rows have coverage_code
-- NOTE: This is enforced by loader, DB constraint would block flexibility
-- SKIP for now - rely on loader validation

-- ============================================================================
-- 3. Verification Query
-- ============================================================================
-- Run after patch:
-- SELECT column_name, is_nullable, data_type
-- FROM information_schema.columns
-- WHERE table_name='coverage_instance' AND column_name='coverage_code';
--
-- Expected: is_nullable = 'YES'

-- ============================================================================
-- End of Patch
-- ============================================================================
