-- inca-rag-scope: Canonical Coverage Schema
-- Source: data/sources/mapping/담보명mapping자료.xlsx ONLY

-- 담보 표준 테이블
CREATE TABLE IF NOT EXISTS coverage_standard (
    coverage_id SERIAL PRIMARY KEY,
    coverage_code TEXT UNIQUE NOT NULL,  -- Canonical key from mapping excel
    coverage_name TEXT NOT NULL,         -- 표준 담보명
    category TEXT,                       -- 담보 카테고리 (사망, 진단, 수술 등)
    description TEXT,                    -- 담보 설명
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 담보 별칭 테이블 (보험사별 표기 차이)
CREATE TABLE IF NOT EXISTS coverage_alias (
    alias_id SERIAL PRIMARY KEY,
    coverage_id INTEGER NOT NULL REFERENCES coverage_standard(coverage_id) ON DELETE CASCADE,
    alias_name TEXT NOT NULL,            -- 보험사별 담보명
    insurer TEXT,                        -- 보험사명
    product_name TEXT,                   -- 상품명 (선택)
    normalized_name TEXT,                -- 정규화된 별칭 (검색용)
    source TEXT,                         -- 출처 (가입설계서, 약관 등)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_coverage_code ON coverage_standard(coverage_code);
CREATE INDEX IF NOT EXISTS idx_coverage_name ON coverage_standard(coverage_name);
CREATE INDEX IF NOT EXISTS idx_alias_coverage_id ON coverage_alias(coverage_id);
CREATE INDEX IF NOT EXISTS idx_alias_name ON coverage_alias(alias_name);
CREATE INDEX IF NOT EXISTS idx_alias_normalized ON coverage_alias(normalized_name);
CREATE INDEX IF NOT EXISTS idx_alias_insurer ON coverage_alias(insurer);

-- 주석
COMMENT ON TABLE coverage_standard IS '담보 표준 테이블 - mapping 엑셀 기준';
COMMENT ON TABLE coverage_alias IS '보험사별 담보 별칭 테이블';
COMMENT ON COLUMN coverage_standard.coverage_code IS 'Canonical key - UNIQUE, from mapping excel';
COMMENT ON COLUMN coverage_alias.normalized_name IS '검색 최적화를 위한 정규화 이름 (공백제거, 소문자 등)';
