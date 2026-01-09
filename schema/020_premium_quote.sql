-- inca-rag-scope: Premium SSOT Schema
-- STEP NEXT-O: Premium Quote Single Source of Truth
-- Purpose: Q1/Q12/Q14 enablement (보험료 가성비 비교, 회사 간 비교, Top-N 비교)

-- 보험료 견적 테이블 (SSOT)
CREATE TABLE IF NOT EXISTS premium_quote (
    quote_id SERIAL PRIMARY KEY,

    -- 4D Identity
    insurer_key TEXT NOT NULL,           -- 보험사 키 (kb, samsung, hanwha, ...)
    product_id TEXT NOT NULL,            -- 상품 ID (product_key format)
    plan_variant TEXT NOT NULL,          -- GENERAL | NO_REFUND

    -- Persona (연령/성별/흡연)
    age INTEGER NOT NULL,                -- 30, 40, 50 ONLY
    sex TEXT NOT NULL,                   -- M | F | UNISEX
    smoke TEXT NOT NULL DEFAULT 'NA',   -- Y | N | NA (없으면 NA 고정)

    -- 계약 조건
    pay_term_years INTEGER NOT NULL,     -- 납입 기간 (년)
    ins_term_years INTEGER NOT NULL,     -- 보험 기간 (년)

    -- 보험료 (SSOT)
    premium_monthly INTEGER NOT NULL,    -- 월납 보험료 (원)
    premium_total INTEGER NOT NULL,      -- 총납 보험료 (원)

    -- Traceability
    source_table_id TEXT,                -- API 응답 또는 엑셀 시트 식별자
    source_row_id TEXT,                  -- 원본 행 식별자
    as_of_date DATE NOT NULL,            -- 견적 기준일

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_plan_variant CHECK (plan_variant IN ('GENERAL', 'NO_REFUND')),
    CONSTRAINT chk_age CHECK (age IN (30, 40, 50)),
    CONSTRAINT chk_sex CHECK (sex IN ('M', 'F', 'UNISEX')),
    CONSTRAINT chk_smoke CHECK (smoke IN ('Y', 'N', 'NA')),
    CONSTRAINT chk_premium_positive CHECK (premium_monthly > 0 AND premium_total > 0)
);

-- 일반형 보험요율 배수 테이블
CREATE TABLE IF NOT EXISTS premium_multiplier (
    multiplier_id SERIAL PRIMARY KEY,

    insurer_key TEXT NOT NULL,           -- 보험사 키 (kb, samsung, hanwha, ...)
    coverage_name TEXT NOT NULL,         -- 담보명 (괄호 포함 완전 일치)
    multiplier_percent NUMERIC(5,2) NOT NULL,  -- 배수 (116 → 1.16)

    source_file TEXT NOT NULL,           -- /data/sources/insurers/4. 일반보험요율예시.xlsx
    source_row_id INTEGER,               -- 엑셀 행 번호

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_multiplier_positive CHECK (multiplier_percent > 0),
    CONSTRAINT uq_insurer_coverage UNIQUE (insurer_key, coverage_name)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_premium_quote_lookup
    ON premium_quote(insurer_key, product_id, plan_variant, age, sex);

CREATE INDEX IF NOT EXISTS idx_premium_quote_comparison
    ON premium_quote(plan_variant, age, sex, premium_monthly);

CREATE INDEX IF NOT EXISTS idx_multiplier_lookup
    ON premium_multiplier(insurer_key, coverage_name);

-- 주석
COMMENT ON TABLE premium_quote IS 'STEP NEXT-O: 보험료 SSOT - Q1/Q12/Q14 활성화';
COMMENT ON COLUMN premium_quote.plan_variant IS 'GENERAL=일반형(배수 적용) | NO_REFUND=무해지형(API 원본)';
COMMENT ON COLUMN premium_quote.premium_monthly IS 'LLM 계산/추정/보정 절대 금지 - 외부 테이블이 진실';
COMMENT ON COLUMN premium_quote.premium_total IS 'LLM 계산/추정/보정 절대 금지 - 외부 테이블이 진실';

COMMENT ON TABLE premium_multiplier IS '일반형 보험요율 배수 (무해지 → 일반 변환용)';
COMMENT ON COLUMN premium_multiplier.multiplier_percent IS '엑셀 116 → 1.16 변환 적용';
COMMENT ON COLUMN premium_multiplier.coverage_name IS '담보명 괄호 포함 완전 일치 필수';
