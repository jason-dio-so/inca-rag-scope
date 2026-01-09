-- inca-rag-scope: Product Comparison Table (PCT) v1 Schema
-- STEP NEXT-P: Q1/Q2/Q3 Common Product Comparison Table
-- Purpose: Enable Q1 (premium per coverage), Q2 (underwriting), Q3 (base contract minimization)

-- ==========================================
-- Table 1: compare_rows_v1 (Coverage SSOT)
-- ==========================================

CREATE TABLE IF NOT EXISTS compare_rows_v1 (
    row_id SERIAL PRIMARY KEY,

    -- 4D Identity
    insurer_key TEXT NOT NULL,
    product_key TEXT NOT NULL,
    variant_key TEXT NOT NULL,
    coverage_code TEXT,                      -- Canonical coverage code (A4200_1, A4101, etc.)
    coverage_title TEXT,                     -- Coverage display name
    coverage_name_raw TEXT,                  -- Raw coverage name from proposal

    -- Slots (JSON storage for flexibility)
    slots JSONB NOT NULL,                    -- All slot data (start_date, exclusions, payout_limit, etc.)
    meta JSONB,                              -- Metadata (slot_status_summary, has_conflict, unanchored, etc.)

    -- Extracted Key Fields (for query performance)
    payout_limit_value TEXT,                 -- Extracted from slots.payout_limit.value
    payout_limit_status TEXT,                -- FOUND | FOUND_GLOBAL | UNKNOWN | CONFLICT

    start_date_value TEXT,                   -- Extracted from slots.start_date.value
    start_date_status TEXT,

    exclusions_value TEXT,                   -- Extracted from slots.exclusions.value
    exclusions_status TEXT,

    underwriting_condition_value TEXT,       -- Extracted from slots.underwriting_condition.value
    underwriting_condition_status TEXT,

    mandatory_dependency_value TEXT,         -- Extracted from slots.mandatory_dependency.value
    mandatory_dependency_status TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_payout_limit_status CHECK (payout_limit_status IN ('FOUND', 'FOUND_GLOBAL', 'UNKNOWN', 'CONFLICT', NULL)),
    CONSTRAINT chk_start_date_status CHECK (start_date_status IN ('FOUND', 'FOUND_GLOBAL', 'UNKNOWN', 'CONFLICT', NULL))
);

-- Indexes for compare_rows_v1
CREATE INDEX IF NOT EXISTS idx_compare_rows_lookup
    ON compare_rows_v1(insurer_key, product_key, variant_key);

CREATE INDEX IF NOT EXISTS idx_compare_rows_coverage_code
    ON compare_rows_v1(coverage_code);

CREATE INDEX IF NOT EXISTS idx_compare_rows_payout_limit_status
    ON compare_rows_v1(payout_limit_status);

-- ==========================================
-- Table 2: product_coverage_bundle (Aggregated Coverage Info)
-- ==========================================

CREATE TABLE IF NOT EXISTS product_coverage_bundle (
    bundle_id SERIAL PRIMARY KEY,

    -- Product Identity
    insurer_key TEXT NOT NULL,
    product_key TEXT NOT NULL,
    variant_key TEXT NOT NULL,

    -- Coverage Aggregate
    coverage_list JSONB NOT NULL,           -- Array of {coverage_code, coverage_title, payout_limit, monthly_premium}

    -- Derived Metrics
    base_contract_monthly_sum INTEGER,      -- 의무담보 월보험료 합계
    optional_contract_monthly_sum INTEGER,  -- 선택담보 월보험료 합계

    -- Base Contract Flags
    base_contract_min_flags JSONB,          -- {has_death: bool, has_disability: bool, min_level: int}

    -- Underwriting Tags
    underwriting_tags JSONB,                -- {has_chronic_no_surcharge: bool, has_simplified: bool}

    as_of_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_product_bundle UNIQUE (insurer_key, product_key, variant_key, as_of_date)
);

-- Index for product_coverage_bundle
CREATE INDEX IF NOT EXISTS idx_bundle_product
    ON product_coverage_bundle(insurer_key, product_key, variant_key);

-- ==========================================
-- View: product_comparison_v1 (PCT v1)
-- ==========================================

CREATE OR REPLACE VIEW product_comparison_v1 AS
SELECT
    -- Key Dimensions
    pq.insurer_key,
    pq.product_id AS product_key,
    pq.plan_variant,
    pq.age,
    pq.sex,
    pq.smoke,
    pq.pay_term_years,
    pq.ins_term_years,
    pq.as_of_date,

    -- Premium (from premium_quote SSOT)
    pq.premium_monthly,
    pq.premium_total,

    -- Coverage Bundle (from product_coverage_bundle)
    pcb.coverage_list,
    pcb.base_contract_monthly_sum,
    pcb.optional_contract_monthly_sum,
    pcb.base_contract_min_flags,
    pcb.underwriting_tags,

    -- Q1 Derived Field: Cancer Coverage Amount (A4200_1)
    (
        SELECT (elem->>'payout_limit')::NUMERIC
        FROM jsonb_array_elements(pcb.coverage_list) AS elem
        WHERE elem->>'coverage_code' = 'A4200_1'
        LIMIT 1
    ) AS cancer_diagnosis_amount,

    -- Q2 Derived Fields: Cerebrovascular (A4101) + Ischemic (A4105)
    (
        SELECT (elem->>'payout_limit')::NUMERIC
        FROM jsonb_array_elements(pcb.coverage_list) AS elem
        WHERE elem->>'coverage_code' = 'A4101'
        LIMIT 1
    ) AS cerebrovascular_amount,

    (
        SELECT (elem->>'payout_limit')::NUMERIC
        FROM jsonb_array_elements(pcb.coverage_list) AS elem
        WHERE elem->>'coverage_code' = 'A4105'
        LIMIT 1
    ) AS ischemic_amount

FROM premium_quote pq
LEFT JOIN product_coverage_bundle pcb
    ON pq.insurer_key = pcb.insurer_key
    AND pq.product_id = pcb.product_key
    AND pq.as_of_date = pcb.as_of_date
;

-- Comments
COMMENT ON TABLE compare_rows_v1 IS 'STEP NEXT-P: Coverage SSOT from compare_rows_v1.jsonl';
COMMENT ON TABLE product_coverage_bundle IS 'STEP NEXT-P: Aggregated coverage bundle per product';
COMMENT ON VIEW product_comparison_v1 IS 'STEP NEXT-P: Product Comparison Table v1 for Q1/Q2/Q3';

COMMENT ON COLUMN compare_rows_v1.slots IS 'Full slot data (JSONB) - preserves all evidence and metadata';
COMMENT ON COLUMN compare_rows_v1.payout_limit_value IS 'Extracted payout_limit value for query performance';
COMMENT ON COLUMN product_coverage_bundle.base_contract_min_flags IS 'Base contract minimization flags (Q3)';
COMMENT ON COLUMN product_coverage_bundle.underwriting_tags IS 'Underwriting tags (Q2) - evidence-based ONLY, NO inference';
