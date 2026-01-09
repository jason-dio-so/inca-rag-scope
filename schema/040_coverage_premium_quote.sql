-- inca-rag-scope: Coverage Premium Quote Schema
-- STEP NEXT-Q: Premium Allocation + Product-ID Alignment LOCK
-- Purpose: Per-coverage premium SSOT + product_id mapping

-- ==========================================
-- Table 1: product_id_map (정합 SSOT)
-- ==========================================

CREATE TABLE IF NOT EXISTS product_id_map (
    map_id SERIAL PRIMARY KEY,

    -- Identity
    insurer_key TEXT NOT NULL,

    -- Product ID Mapping
    compare_product_id TEXT NOT NULL,       -- compare_rows_v1의 product_key
    premium_product_id TEXT NOT NULL,       -- API prCd 또는 premium_quote의 product_id

    -- Metadata
    as_of_date DATE NOT NULL,
    source TEXT NOT NULL,                   -- MANUAL | DERIVED | API
    evidence_ref TEXT,                      -- 매핑 근거 (파일명, API 응답 등)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_compare_product UNIQUE (insurer_key, compare_product_id, as_of_date),
    CONSTRAINT chk_source CHECK (source IN ('MANUAL', 'DERIVED', 'API'))
);

-- Index for product_id_map
CREATE INDEX IF NOT EXISTS idx_product_id_map_lookup
    ON product_id_map(insurer_key, compare_product_id);

CREATE INDEX IF NOT EXISTS idx_product_id_map_reverse
    ON product_id_map(insurer_key, premium_product_id);

-- ==========================================
-- Table 2: coverage_premium_quote (Coverage Premium SSOT)
-- ==========================================

CREATE TABLE IF NOT EXISTS coverage_premium_quote (
    coverage_premium_id SERIAL PRIMARY KEY,

    -- Key Dimensions (match premium_quote)
    insurer_key TEXT NOT NULL,
    product_id TEXT NOT NULL,               -- premium_product_id 기준
    plan_variant TEXT NOT NULL,             -- GENERAL | NO_REFUND

    -- Persona
    age INTEGER NOT NULL,                   -- 30, 40, 50 ONLY
    sex TEXT NOT NULL,                      -- M | F | UNISEX
    smoke TEXT NOT NULL DEFAULT 'NA',      -- Y | N | NA

    -- Contract Terms
    pay_term_years INTEGER NOT NULL,
    ins_term_years INTEGER NOT NULL,
    as_of_date DATE NOT NULL,

    -- Coverage Identity
    coverage_code TEXT,                     -- Canonical coverage code (A4200_1, A4101, etc.)
    coverage_title_raw TEXT,                -- API cvrNm 원문
    coverage_name_normalized TEXT,          -- Normalized coverage name

    -- Coverage Amount
    coverage_amount_raw TEXT,               -- API accAmt 원문
    coverage_amount_value BIGINT,           -- Parsed amount (원)

    -- Coverage Premium (SSOT)
    premium_monthly_coverage INTEGER NOT NULL,  -- API monthlyPrem (NO_REFUND) or calculated (GENERAL)

    -- Traceability
    source_table_id TEXT,                   -- API calSubSeq / cvrCd
    source_row_id TEXT,                     -- API row tracking key
    multiplier_percent NUMERIC(5,2),        -- For GENERAL: multiplier used

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_cpq_plan_variant CHECK (plan_variant IN ('GENERAL', 'NO_REFUND')),
    CONSTRAINT chk_cpq_age CHECK (age IN (30, 40, 50)),
    CONSTRAINT chk_cpq_sex CHECK (sex IN ('M', 'F', 'UNISEX')),
    CONSTRAINT chk_cpq_smoke CHECK (smoke IN ('Y', 'N', 'NA')),
    CONSTRAINT chk_cpq_premium_positive CHECK (premium_monthly_coverage > 0)
);

-- Indexes for coverage_premium_quote
CREATE INDEX IF NOT EXISTS idx_coverage_premium_lookup
    ON coverage_premium_quote(insurer_key, product_id, plan_variant, age, sex, coverage_code);

CREATE INDEX IF NOT EXISTS idx_coverage_premium_coverage_code
    ON coverage_premium_quote(coverage_code);

CREATE INDEX IF NOT EXISTS idx_coverage_premium_plan_variant
    ON coverage_premium_quote(plan_variant);

-- ==========================================
-- Table 3: product_premium_quote_v2 (Product Premium with tracking)
-- ==========================================

CREATE TABLE IF NOT EXISTS product_premium_quote_v2 (
    product_premium_id SERIAL PRIMARY KEY,

    -- Key Dimensions
    insurer_key TEXT NOT NULL,
    product_id TEXT NOT NULL,
    plan_variant TEXT NOT NULL,

    -- Persona
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    smoke TEXT NOT NULL DEFAULT 'NA',

    -- Contract Terms
    pay_term_years INTEGER NOT NULL,
    ins_term_years INTEGER NOT NULL,
    as_of_date DATE NOT NULL,

    -- Total Premium (SSOT)
    premium_monthly_total INTEGER NOT NULL,     -- API monthlyPremSum
    premium_total_total INTEGER NOT NULL,       -- API totalPremSum

    -- Verification
    calculated_monthly_sum INTEGER,             -- sum(coverage_premium_quote.premium_monthly_coverage)
    sum_match_status TEXT,                      -- MATCH | MISMATCH | UNKNOWN

    -- Traceability
    source_table_id TEXT,
    source_row_id TEXT,
    api_response_hash TEXT,                     -- SHA256 of raw API response

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_ppq_plan_variant CHECK (plan_variant IN ('GENERAL', 'NO_REFUND')),
    CONSTRAINT chk_ppq_age CHECK (age IN (30, 40, 50)),
    CONSTRAINT chk_ppq_sex CHECK (sex IN ('M', 'F', 'UNISEX')),
    CONSTRAINT chk_ppq_smoke CHECK (smoke IN ('Y', 'N', 'NA')),
    CONSTRAINT chk_ppq_premium_positive CHECK (premium_monthly_total > 0 AND premium_total_total > 0),
    CONSTRAINT uq_product_premium UNIQUE (insurer_key, product_id, plan_variant, age, sex, smoke, pay_term_years, ins_term_years, as_of_date)
);

-- Index for product_premium_quote_v2
CREATE INDEX IF NOT EXISTS idx_product_premium_v2_lookup
    ON product_premium_quote_v2(insurer_key, product_id, plan_variant, age, sex);

-- Comments
COMMENT ON TABLE product_id_map IS 'STEP NEXT-Q: Product ID mapping (compare_rows ↔ premium_quote)';
COMMENT ON TABLE coverage_premium_quote IS 'STEP NEXT-Q: Per-coverage premium SSOT';
COMMENT ON TABLE product_premium_quote_v2 IS 'STEP NEXT-Q: Product-level premium with sum verification';

COMMENT ON COLUMN product_id_map.compare_product_id IS 'compare_rows_v1.product_key';
COMMENT ON COLUMN product_id_map.premium_product_id IS 'premium_quote.product_id or API prCd';
COMMENT ON COLUMN product_id_map.evidence_ref IS 'Mapping evidence (file, API response, etc.)';

COMMENT ON COLUMN coverage_premium_quote.plan_variant IS 'NO_REFUND=API direct | GENERAL=multiplier calculated';
COMMENT ON COLUMN coverage_premium_quote.premium_monthly_coverage IS 'SSOT per-coverage premium (NO LLM/estimation)';
COMMENT ON COLUMN coverage_premium_quote.multiplier_percent IS 'For GENERAL: multiplier from 일반보험요율예시.xlsx';

COMMENT ON COLUMN product_premium_quote_v2.calculated_monthly_sum IS 'sum(coverage_premium_quote) for verification';
COMMENT ON COLUMN product_premium_quote_v2.sum_match_status IS 'MATCH=0 error | MISMATCH=sum error detected';
