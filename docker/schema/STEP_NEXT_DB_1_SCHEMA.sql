-- ============================================================================
-- STEP NEXT-DB-1: Production DB Schema (DDL Only)
-- ============================================================================
-- Date: 2025-12-28
-- Database: inca_rag_scope
-- Purpose: Create all 9 tables with constraints and indexes
-- Source: docs/foundation/DB_PHYSICAL_MODEL_EXTENDED.md + ERD_PHYSICAL.md
-- ============================================================================

-- ============================================================================
-- 1. EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- For gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;    -- For pgvector (future use)

-- ============================================================================
-- 2. METADATA TABLES (5 tables)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 insurer
-- ----------------------------------------------------------------------------
CREATE TABLE insurer (
  -- Primary Key
  insurer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Insurer Attributes
  insurer_name_kr TEXT NOT NULL,              -- e.g., '삼성화재'
  insurer_name_en TEXT,                       -- e.g., 'Samsung Fire & Marine Insurance'
  insurer_type TEXT CHECK (insurer_type IN ('생명', '손해')),

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

CREATE INDEX idx_insurer_name_kr ON insurer(insurer_name_kr);
CREATE INDEX idx_insurer_type ON insurer(insurer_type);

COMMENT ON TABLE insurer IS 'Insurance company metadata (생명/손해)';
COMMENT ON COLUMN insurer.insurer_name_kr IS 'Korean name (e.g., 삼성화재)';
COMMENT ON COLUMN insurer.insurer_type IS 'Insurance type: 생명 (life) or 손해 (non-life)';

-- ----------------------------------------------------------------------------
-- 2.2 doc_structure_profile
-- ----------------------------------------------------------------------------
CREATE TABLE doc_structure_profile (
  -- Primary Key
  profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Profile Attributes
  profile_name TEXT NOT NULL,
  scope_table_location TEXT,                  -- e.g., 'page_3_table_2'
  amount_table_location TEXT,                 -- e.g., 'page_5_table_1'
  metadata JSONB DEFAULT '{}'::jsonb,         -- e.g., {"scope_keywords": ["보장내용"], "amount_keywords": ["가입금액"]}

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

COMMENT ON TABLE doc_structure_profile IS 'Document structure profiles (KB/Meritz table locations)';
COMMENT ON COLUMN doc_structure_profile.scope_table_location IS 'Location of scope table in 가입설계서';
COMMENT ON COLUMN doc_structure_profile.amount_table_location IS 'Location of amount table in 가입설계서';

-- ----------------------------------------------------------------------------
-- 2.3 product
-- ----------------------------------------------------------------------------
CREATE TABLE product (
  -- Primary Key
  product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  insurer_id UUID NOT NULL REFERENCES insurer(insurer_id),
  doc_structure_profile_id UUID REFERENCES doc_structure_profile(profile_id),

  -- Product Attributes
  product_name TEXT NOT NULL,
  product_code TEXT,                          -- e.g., 'LOTTE-001'

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

CREATE INDEX idx_product_insurer ON product(insurer_id);
CREATE INDEX idx_product_profile ON product(doc_structure_profile_id);

COMMENT ON TABLE product IS 'Insurance product metadata (e.g., LOTTE Health Insurance)';
COMMENT ON COLUMN product.doc_structure_profile_id IS 'Document structure profile (KB/Meritz variants)';

-- ----------------------------------------------------------------------------
-- 2.4 product_variant
-- ----------------------------------------------------------------------------
CREATE TABLE product_variant (
  -- Primary Key
  variant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  product_id UUID NOT NULL REFERENCES product(product_id),
  doc_structure_profile_id UUID REFERENCES doc_structure_profile(profile_id),

  -- Variant Attributes
  variant_key TEXT NOT NULL,                  -- e.g., 'MALE', 'FEMALE', 'AGE_20_39'
  variant_display_name TEXT NOT NULL,         -- e.g., '남', '여', '20-39세'

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT unique_variant_per_product UNIQUE (product_id, variant_key)
);

CREATE INDEX idx_product_variant_product ON product_variant(product_id);

COMMENT ON TABLE product_variant IS 'Product variants (LOTTE Male/Female, DB Age groups)';
COMMENT ON COLUMN product_variant.variant_key IS 'Variant key (e.g., MALE, FEMALE, AGE_20_39)';
COMMENT ON COLUMN product_variant.variant_display_name IS 'Display name (e.g., 남, 여, 20-39세)';

-- ----------------------------------------------------------------------------
-- 2.5 document
-- ----------------------------------------------------------------------------
CREATE TABLE document (
  -- Primary Key
  document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  insurer_id UUID NOT NULL REFERENCES insurer(insurer_id),
  product_id UUID NOT NULL REFERENCES product(product_id),

  -- Document Attributes
  doc_type TEXT NOT NULL CHECK (doc_type IN ('약관', '사업방법서', '상품요약서', '가입설계서')),
  file_path TEXT NOT NULL,                    -- Relative path: data/pdf/samsung/...
  page_count INT,

  -- Metadata
  extracted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_insurer ON document(insurer_id);
CREATE INDEX idx_document_product ON document(product_id);
CREATE INDEX idx_document_doc_type ON document(doc_type);

COMMENT ON TABLE document IS 'Document metadata (약관/사업방법서/상품요약서/가입설계서)';
COMMENT ON COLUMN document.doc_type IS 'Document type: 약관, 사업방법서, 상품요약서, 가입설계서';
COMMENT ON COLUMN document.file_path IS 'Relative path to PDF file';

-- ============================================================================
-- 3. CANONICAL TABLE (1 table)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 coverage_canonical
-- ----------------------------------------------------------------------------
CREATE TABLE coverage_canonical (
  -- Primary Key
  coverage_code TEXT PRIMARY KEY,             -- e.g., 'A4200_1'

  -- Canonical Attributes
  coverage_name_canonical TEXT NOT NULL,      -- e.g., '암진단비(유사암제외)'
  coverage_category TEXT,                     -- e.g., '진단', '수술', '입원'
  payment_event TEXT,                         -- e.g., '암 진단 확정 시'

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,

  -- Constraints
  CONSTRAINT coverage_code_format CHECK (coverage_code ~ '^[A-Z]\d{4}(_\d+)?$')
);

CREATE INDEX idx_coverage_category ON coverage_canonical(coverage_category);
CREATE INDEX idx_coverage_name_canonical ON coverage_canonical(coverage_name_canonical);

COMMENT ON TABLE coverage_canonical IS 'Canonical coverage definitions from 담보명mapping자료.xlsx (READ-ONLY source of truth)';
COMMENT ON COLUMN coverage_canonical.coverage_code IS 'Canonical coverage code (e.g., A4200_1). Format: [A-Z]\d{4}(_\d+)?';
COMMENT ON COLUMN coverage_canonical.coverage_name_canonical IS 'Canonical coverage name (normalized across insurers)';
COMMENT ON COLUMN coverage_canonical.payment_event IS 'Payment trigger event (e.g., 암 진단 확정 시)';

-- ============================================================================
-- 4. INSTANCE TABLES (3 tables)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 coverage_instance
-- ----------------------------------------------------------------------------
CREATE TABLE coverage_instance (
  -- Primary Key
  instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  insurer_id UUID NOT NULL REFERENCES insurer(insurer_id),
  product_id UUID NOT NULL REFERENCES product(product_id),
  variant_id UUID REFERENCES product_variant(variant_id),           -- Nullable (for non-variant products)
  coverage_code TEXT NOT NULL REFERENCES coverage_canonical(coverage_code),

  -- Instance Attributes
  coverage_name_raw TEXT NOT NULL,                                  -- e.g., '암 진단비(유사암 제외)' (insurer's original text)
  source_page INT,                                                  -- Page number in 가입설계서

  -- Mapping Status
  mapping_status TEXT NOT NULL CHECK (mapping_status IN ('matched', 'unmatched')),
  match_type TEXT,                                                  -- e.g., 'exact', 'normalized_alias', 'manual'

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT unique_coverage_per_product UNIQUE (product_id, variant_id, coverage_code)
);

CREATE INDEX idx_coverage_instance_insurer ON coverage_instance(insurer_id);
CREATE INDEX idx_coverage_instance_product ON coverage_instance(product_id);
CREATE INDEX idx_coverage_instance_coverage_code ON coverage_instance(coverage_code);
CREATE INDEX idx_coverage_instance_mapping_status ON coverage_instance(mapping_status);

COMMENT ON TABLE coverage_instance IS 'Insurer-specific coverage instances from 가입설계서 scope (1:1 with scope CSV rows)';
COMMENT ON COLUMN coverage_instance.coverage_name_raw IS 'Original coverage name from insurer documents (exact text, no normalization)';
COMMENT ON COLUMN coverage_instance.variant_id IS 'Product variant (e.g., LOTTE Male/Female). NULL if product has no variants.';
COMMENT ON COLUMN coverage_instance.mapping_status IS 'matched: linked to canonical code | unmatched: no canonical code found';
COMMENT ON COLUMN coverage_instance.match_type IS 'Matching method: exact, normalized_alias, manual';

-- ----------------------------------------------------------------------------
-- 4.2 evidence_ref
-- ----------------------------------------------------------------------------
CREATE TABLE evidence_ref (
  -- Primary Key
  evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  coverage_instance_id UUID NOT NULL REFERENCES coverage_instance(instance_id),
  document_id UUID NOT NULL REFERENCES document(document_id),

  -- Evidence Attributes
  doc_type TEXT NOT NULL CHECK (doc_type IN ('약관', '사업방법서', '상품요약서', '가입설계서')),
  page INT NOT NULL CHECK (page > 0),                               -- Page number in document
  snippet TEXT NOT NULL,                                            -- Original text (no summarization)
  match_keyword TEXT,                                               -- Keyword used for matching

  -- Evidence Rank (1-3 per doc_type)
  rank INT CHECK (rank BETWEEN 1 AND 3),                            -- Evidence priority (1 = highest)

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT non_empty_snippet CHECK (length(snippet) > 0)
);

CREATE INDEX idx_evidence_coverage_instance ON evidence_ref(coverage_instance_id);
CREATE INDEX idx_evidence_document ON evidence_ref(document_id);
CREATE INDEX idx_evidence_doc_type ON evidence_ref(doc_type);
CREATE INDEX idx_evidence_rank ON evidence_ref(rank);

COMMENT ON TABLE evidence_ref IS 'Evidence references from 약관/사업방법서/상품요약서/가입설계서 (original text snippets)';
COMMENT ON COLUMN evidence_ref.snippet IS 'Original text snippet (MUST NOT be summarized or modified)';
COMMENT ON COLUMN evidence_ref.match_keyword IS 'Keyword used for matching (e.g., canonical name, raw name, alias)';
COMMENT ON COLUMN evidence_ref.rank IS 'Evidence priority within doc_type (1 = highest). Max 3 per doc_type.';

-- ----------------------------------------------------------------------------
-- 4.3 amount_fact
-- ----------------------------------------------------------------------------
CREATE TABLE amount_fact (
  -- Primary Key
  amount_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign Keys
  coverage_instance_id UUID NOT NULL REFERENCES coverage_instance(instance_id),
  evidence_id UUID REFERENCES evidence_ref(evidence_id),            -- MANDATORY if status = CONFIRMED

  -- Amount Attributes
  status TEXT NOT NULL CHECK (status IN ('CONFIRMED', 'UNCONFIRMED', 'CONFLICT')),
  value_text TEXT,                                                  -- e.g., '3000만원' (EXACT text from document)
  source_doc_type TEXT CHECK (source_doc_type IN ('가입설계서', '약관', '사업방법서', '상품요약서')),
  source_priority TEXT CHECK (source_priority IN ('PRIMARY', 'SECONDARY')),

  -- Amount Notes (fixed keywords only)
  notes JSONB DEFAULT '[]'::jsonb,                                  -- e.g., ["계산금지", "가입설계서우선"]

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT confirmed_has_evidence CHECK (
    (status = 'CONFIRMED' AND evidence_id IS NOT NULL AND value_text IS NOT NULL) OR
    (status != 'CONFIRMED')
  ),
  CONSTRAINT confirmed_has_value CHECK (
    (status = 'CONFIRMED' AND value_text IS NOT NULL) OR
    (status = 'UNCONFIRMED' AND value_text IS NULL) OR
    (status = 'CONFLICT')
  ),
  CONSTRAINT primary_from_proposal CHECK (
    (source_priority = 'PRIMARY' AND source_doc_type = '가입설계서') OR
    (source_priority = 'SECONDARY' AND source_doc_type IN ('약관', '사업방법서', '상품요약서')) OR
    (source_priority IS NULL)
  ),
  CONSTRAINT unique_amount_per_coverage UNIQUE (coverage_instance_id)
);

CREATE INDEX idx_amount_coverage_instance ON amount_fact(coverage_instance_id);
CREATE INDEX idx_amount_status ON amount_fact(status);
CREATE INDEX idx_amount_priority ON amount_fact(source_priority);

COMMENT ON TABLE amount_fact IS 'Amount facts from 가입설계서 (PRIMARY source) or 약관/사업방법서/상품요약서 (SECONDARY source)';
COMMENT ON COLUMN amount_fact.status IS 'CONFIRMED: amount found with evidence | UNCONFIRMED: amount not found | CONFLICT: multiple conflicting amounts';
COMMENT ON COLUMN amount_fact.value_text IS 'EXACT amount text from document (e.g., 3000만원). NO CALCULATION.';
COMMENT ON COLUMN amount_fact.source_priority IS 'PRIMARY: from 가입설계서 | SECONDARY: from 약관/사업방법서/상품요약서';
COMMENT ON COLUMN amount_fact.evidence_id IS 'Evidence reference. MANDATORY if status = CONFIRMED.';
COMMENT ON COLUMN amount_fact.notes IS 'Fixed keywords only. FORBIDDEN: prose, recommendations, interpretations.';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
