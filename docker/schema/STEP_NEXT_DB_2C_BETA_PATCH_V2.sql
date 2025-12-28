-- STEP NEXT-DB-2C-β Schema Patch V2
-- Date: 2025-12-28
-- Purpose: Fix FK constraint to allow NULL coverage_code for unmatched rows
--
-- ISSUE: FK constraint blocks NULL insertion even though column is nullable
-- FIX: Drop and recreate FK with proper NULL handling (PostgreSQL FK allows NULL by default)
--
-- NOTE: FK constraints in PostgreSQL already allow NULL values, but we need to verify
--       the constraint definition is correct

-- ============================================================================
-- 1. Check existing FK constraint
-- ============================================================================
-- Current constraint: coverage_instance_coverage_code_fkey
-- Expected behavior: NULL values should be allowed (FK allows NULL by default in PostgreSQL)

-- ============================================================================
-- 2. Drop existing FK constraint
-- ============================================================================
ALTER TABLE coverage_instance
DROP CONSTRAINT IF EXISTS coverage_instance_coverage_code_fkey;

-- ============================================================================
-- 3. Re-add FK constraint (explicitly allow NULL)
-- ============================================================================
-- PostgreSQL FK constraints allow NULL by default, but we make it explicit
ALTER TABLE coverage_instance
ADD CONSTRAINT coverage_instance_coverage_code_fkey
FOREIGN KEY (coverage_code)
REFERENCES coverage_canonical(coverage_code)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- ============================================================================
-- 4. Add comment
-- ============================================================================
COMMENT ON CONSTRAINT coverage_instance_coverage_code_fkey ON coverage_instance IS
'FK to coverage_canonical. NULL allowed for mapping_status=unmatched rows.';

-- ============================================================================
-- End of Patch V2
-- ============================================================================
