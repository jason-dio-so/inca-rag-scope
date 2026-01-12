-- inca-rag-scope: Premium Multiplier as_of_date Migration
-- STEP NEXT-GENERAL-SSOT: Add snapshot capability to premium_multiplier
-- Purpose: Enable versioned multiplier snapshots for GENERAL premium calculation

-- Add as_of_date column (nullable initially for existing rows)
ALTER TABLE premium_multiplier
ADD COLUMN IF NOT EXISTS as_of_date DATE;

-- Backfill existing rows with default date (if any exist)
UPDATE premium_multiplier
SET as_of_date = '2025-11-26'
WHERE as_of_date IS NULL;

-- Make as_of_date NOT NULL after backfill
ALTER TABLE premium_multiplier
ALTER COLUMN as_of_date SET NOT NULL;

-- Drop old unique constraint
ALTER TABLE premium_multiplier
DROP CONSTRAINT IF EXISTS uq_insurer_coverage;

-- Add new unique constraint including as_of_date
ALTER TABLE premium_multiplier
ADD CONSTRAINT uq_insurer_coverage_asof
UNIQUE (insurer_key, coverage_name, as_of_date);

-- Add index on as_of_date for efficient date-based queries
CREATE INDEX IF NOT EXISTS idx_multiplier_asof
ON premium_multiplier (as_of_date);

-- Update lookup index to include as_of_date
DROP INDEX IF EXISTS idx_multiplier_lookup;
CREATE INDEX idx_multiplier_lookup_v2
ON premium_multiplier (insurer_key, coverage_name, as_of_date);

-- Add comment
COMMENT ON COLUMN premium_multiplier.as_of_date IS 'Snapshot date for multiplier values (YYYY-MM-DD)';
