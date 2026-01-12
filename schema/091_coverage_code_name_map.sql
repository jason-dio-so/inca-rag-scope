-- inca-rag-scope: Coverage Code to Multiplier Name Mapping
-- STEP NEXT-GENERAL-MAP-1: Enable GENERAL premium calculation via deterministic mapping
-- Purpose: Join coverage_premium_quote.coverage_code ↔ premium_multiplier.coverage_name

-- Mapping table (canonical coverage code → multiplier Korean name)
CREATE TABLE IF NOT EXISTS coverage_code_name_map (
    coverage_code TEXT PRIMARY KEY,
    multiplier_coverage_name TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for reverse lookup (multiplier name → code)
CREATE INDEX IF NOT EXISTS idx_ccnm_multiplier_name
ON coverage_code_name_map (multiplier_coverage_name);

-- Comments
COMMENT ON TABLE coverage_code_name_map IS 'Deterministic mapping between coverage codes and multiplier Excel names';
COMMENT ON COLUMN coverage_code_name_map.coverage_code IS 'Canonical coverage code (e.g., A4200_1, S100)';
COMMENT ON COLUMN coverage_code_name_map.multiplier_coverage_name IS 'EXACT match with premium_multiplier.coverage_name from Excel';
COMMENT ON COLUMN coverage_code_name_map.note IS 'Optional explanation of mapping';

-- Example seed data (commented out - load from seed file)
-- INSERT INTO coverage_code_name_map (coverage_code, multiplier_coverage_name, note) VALUES
--     ('A4200_1', '암진단비(유사암제외)', 'Cancer diagnosis excluding carcinoma in situ'),
--     ('S100', '상해사망', 'Accidental death'),
--     ('S200', '질병사망', 'Disease death');
