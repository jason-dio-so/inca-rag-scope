-- ============================================================================
-- STEP NEXT-DB-2B: Metadata Seed (insurer/product/variant/document only)
-- ============================================================================
-- Date: 2025-12-28
-- Database: inca_rag_scope
-- Purpose: Load metadata from products.yml into DB (5 tables only)
-- Source: data/metadata/products.yml (baseline locked)
--
-- SCOPE:
--   ✅ insurer, product, product_variant, document, doc_structure_profile
--   ❌ coverage_canonical, coverage_instance, evidence_ref, amount_fact
--
-- STRATEGY:
--   - Use deterministic UUIDs based on natural keys (for idempotency)
--   - UPSERT pattern: INSERT ... ON CONFLICT DO UPDATE
--   - Maintain FK relationships via UUID generation consistency
-- ============================================================================

-- Enable pgcrypto for UUID generation
-- (Already installed in STEP NEXT-DB-1, but verify)
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Helper: Generate deterministic UUID from natural key using MD5
-- ============================================================================
-- Pattern: md5('prefix:' || key)::uuid
-- This creates deterministic UUIDs that are reproducible across runs
-- No extension required beyond standard PostgreSQL functions

-- ============================================================================
-- 1. INSURERS (8)
-- ============================================================================
-- Natural key: insurer_key (globally unique)
-- UUID generation: uuid_generate_v5(namespace, 'insurer:' || insurer_key)

INSERT INTO insurer (insurer_id, insurer_name_kr, insurer_name_en, insurer_type, created_at)
VALUES
  (md5('insurer:samsung')::uuid, '삼성생명', 'Samsung Life Insurance', '생명', NOW()),
  (md5('insurer:hyundai')::uuid, '현대해상', 'Hyundai Marine & Fire Insurance', '손해', NOW()),
  (md5('insurer:lotte')::uuid, '롯데손해보험', 'Lotte Insurance', '손해', NOW()),
  (md5('insurer:db')::uuid, 'DB손해보험', 'DB Insurance', '손해', NOW()),
  (md5('insurer:kb')::uuid, 'KB손해보험', 'KB Insurance', '손해', NOW()),
  (md5('insurer:meritz')::uuid, '메리츠화재', 'Meritz Fire & Marine Insurance', '손해', NOW()),
  (md5('insurer:hanwha')::uuid, '한화생명', 'Hanwha Life Insurance', '생명', NOW()),
  (md5('insurer:heungkuk')::uuid, '흥국생명', 'Heungkuk Life Insurance', '생명', NOW())
ON CONFLICT (insurer_id) DO UPDATE
  SET insurer_name_kr = EXCLUDED.insurer_name_kr,
      insurer_name_en = EXCLUDED.insurer_name_en,
      insurer_type = EXCLUDED.insurer_type,
      updated_at = NOW();

-- ============================================================================
-- 2. DOC_STRUCTURE_PROFILE (placeholder - will be refined later)
-- ============================================================================
-- For now, create a default/unknown profile
-- Real profiles will be added in STEP9 profiling phase

INSERT INTO doc_structure_profile (profile_id, profile_name, scope_table_location, amount_table_location, metadata, created_at)
VALUES
  (md5('profile:default')::uuid, 'Default Profile (UNKNOWN)', NULL, NULL, '{}'::jsonb, NOW())
ON CONFLICT (profile_id) DO NOTHING;

-- ============================================================================
-- 3. PRODUCTS (8)
-- ============================================================================
-- Natural key: product_key (globally unique)
-- UUID generation: uuid_generate_v5(namespace, 'product:' || product_key)
-- FK: insurer_id must reference insurer

INSERT INTO product (product_id, insurer_id, product_name, product_code, doc_structure_profile_id, created_at)
VALUES
  -- Samsung
  (md5('product:samsung_health_v1')::uuid,
   md5('insurer:samsung')::uuid,
   '삼성생명 건강보험', 'samsung_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- Hyundai
  (md5('product:hyundai_health_v1')::uuid,
   md5('insurer:hyundai')::uuid,
   '현대해상 건강보험', 'hyundai_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- Lotte
  (md5('product:lotte_health_v1')::uuid,
   md5('insurer:lotte')::uuid,
   '롯데손해보험 건강보험', 'lotte_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- DB
  (md5('product:db_health_v1')::uuid,
   md5('insurer:db')::uuid,
   'DB손해보험 건강보험', 'db_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- KB
  (md5('product:kb_health_v1')::uuid,
   md5('insurer:kb')::uuid,
   'KB손해보험 건강보험', 'kb_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- Meritz
  (md5('product:meritz_health_v1')::uuid,
   md5('insurer:meritz')::uuid,
   '메리츠화재 건강보험', 'meritz_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- Hanwha
  (md5('product:hanwha_health_v1')::uuid,
   md5('insurer:hanwha')::uuid,
   '한화생명 건강보험', 'hanwha_health_v1',
   md5('profile:default')::uuid, NOW()),

  -- Heungkuk
  (md5('product:heungkuk_health_v1')::uuid,
   md5('insurer:heungkuk')::uuid,
   '흥국생명 건강보험', 'heungkuk_health_v1',
   md5('profile:default')::uuid, NOW())
ON CONFLICT (product_id) DO UPDATE
  SET product_name = EXCLUDED.product_name,
      product_code = EXCLUDED.product_code,
      updated_at = NOW();

-- ============================================================================
-- 4. PRODUCT_VARIANTS (4 total: LOTTE 2 gender + DB 2 age)
-- ============================================================================
-- Natural key: variant_key (globally unique)
-- UUID generation: uuid_generate_v5(namespace, 'variant:' || variant_key)
-- FK: product_id must reference product

INSERT INTO product_variant (variant_id, product_id, variant_key, variant_display_name, doc_structure_profile_id, created_at)
VALUES
  -- LOTTE Male
  (md5('variant:LOTTE_MALE')::uuid,
   md5('product:lotte_health_v1')::uuid,
   'LOTTE_MALE', '남',
   md5('profile:default')::uuid, NOW()),

  -- LOTTE Female
  (md5('variant:LOTTE_FEMALE')::uuid,
   md5('product:lotte_health_v1')::uuid,
   'LOTTE_FEMALE', '여',
   md5('profile:default')::uuid, NOW()),

  -- DB Age Under 40
  (md5('variant:DB_AGE_U40')::uuid,
   md5('product:db_health_v1')::uuid,
   'DB_AGE_U40', '40세이하',
   md5('profile:default')::uuid, NOW()),

  -- DB Age Over 40
  (md5('variant:DB_AGE_O40')::uuid,
   md5('product:db_health_v1')::uuid,
   'DB_AGE_O40', '41세이상',
   md5('profile:default')::uuid, NOW())
ON CONFLICT (variant_id) DO UPDATE
  SET variant_display_name = EXCLUDED.variant_display_name;

-- ============================================================================
-- 5. DOCUMENTS (38 total)
-- ============================================================================
-- Natural key: document_key (globally unique)
-- UUID generation: uuid_generate_v5(namespace, 'document:' || document_key)
-- FK: product_id, variant_id (nullable), insurer_id

-- Helper: Get page count from file (placeholder - will set to NULL for now)
-- Real page counts can be extracted later from .page.jsonl files

INSERT INTO document (document_id, insurer_id, product_id, doc_type, file_path, page_count, created_at)
VALUES
  -- ========================================================================
  -- SAMSUNG (5 documents, no variants)
  -- ========================================================================
  (md5('document:samsung_policy_v1')::uuid,
   md5('insurer:samsung')::uuid,
   md5('product:samsung_health_v1')::uuid,
   '약관', 'data/evidence_text/samsung/약관/삼성_약관.page.jsonl', NULL, NOW()),

  (md5('document:samsung_business_v1')::uuid,
   md5('insurer:samsung')::uuid,
   md5('product:samsung_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/samsung/사업방법서/삼성_사업설명서.page.jsonl', NULL, NOW()),

  (md5('document:samsung_summary_v1')::uuid,
   md5('insurer:samsung')::uuid,
   md5('product:samsung_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/samsung/상품요약서/삼성_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:samsung_summary_easy_v1')::uuid,
   md5('insurer:samsung')::uuid,
   md5('product:samsung_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/samsung/상품요약서/삼성_쉬운요약서.page.jsonl', NULL, NOW()),

  (md5('document:samsung_proposal_v1')::uuid,
   md5('insurer:samsung')::uuid,
   md5('product:samsung_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/samsung/가입설계서/삼성_가입설계서_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- HYUNDAI (4 documents, no variants)
  -- ========================================================================
  (md5('document:hyundai_policy_v1')::uuid,
   md5('insurer:hyundai')::uuid,
   md5('product:hyundai_health_v1')::uuid,
   '약관', 'data/evidence_text/hyundai/약관/현대_약관.page.jsonl', NULL, NOW()),

  (md5('document:hyundai_business_v1')::uuid,
   md5('insurer:hyundai')::uuid,
   md5('product:hyundai_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/hyundai/사업방법서/현대_사업방법서.page.jsonl', NULL, NOW()),

  (md5('document:hyundai_summary_v1')::uuid,
   md5('insurer:hyundai')::uuid,
   md5('product:hyundai_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/hyundai/상품요약서/현대_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:hyundai_proposal_v1')::uuid,
   md5('insurer:hyundai')::uuid,
   md5('product:hyundai_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/hyundai/가입설계서/현대_가입설계서_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- KB (4 documents, no variants)
  -- ========================================================================
  (md5('document:kb_policy_v1')::uuid,
   md5('insurer:kb')::uuid,
   md5('product:kb_health_v1')::uuid,
   '약관', 'data/evidence_text/kb/약관/KB_약관.page.jsonl', NULL, NOW()),

  (md5('document:kb_business_v1')::uuid,
   md5('insurer:kb')::uuid,
   md5('product:kb_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/kb/사업방법서/KB_사업방법서.page.jsonl', NULL, NOW()),

  (md5('document:kb_summary_v1')::uuid,
   md5('insurer:kb')::uuid,
   md5('product:kb_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/kb/상품요약서/KB_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:kb_proposal_v1')::uuid,
   md5('insurer:kb')::uuid,
   md5('product:kb_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/kb/가입설계서/KB_가입설계서.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- MERITZ (4 documents, no variants)
  -- ========================================================================
  (md5('document:meritz_policy_v1')::uuid,
   md5('insurer:meritz')::uuid,
   md5('product:meritz_health_v1')::uuid,
   '약관', 'data/evidence_text/meritz/약관/메리츠_약관.page.jsonl', NULL, NOW()),

  (md5('document:meritz_business_v1')::uuid,
   md5('insurer:meritz')::uuid,
   md5('product:meritz_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/meritz/사업방법서/메리츠_사업설명서.page.jsonl', NULL, NOW()),

  (md5('document:meritz_summary_v1')::uuid,
   md5('insurer:meritz')::uuid,
   md5('product:meritz_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/meritz/상품요약서/메리츠_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:meritz_proposal_v1')::uuid,
   md5('insurer:meritz')::uuid,
   md5('product:meritz_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/meritz/가입설계서/메리츠_가입설계서_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- HANWHA (4 documents, no variants)
  -- ========================================================================
  (md5('document:hanwha_policy_v1')::uuid,
   md5('insurer:hanwha')::uuid,
   md5('product:hanwha_health_v1')::uuid,
   '약관', 'data/evidence_text/hanwha/약관/한화_약관.page.jsonl', NULL, NOW()),

  (md5('document:hanwha_business_v1')::uuid,
   md5('insurer:hanwha')::uuid,
   md5('product:hanwha_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/hanwha/사업방법서/한화_사업방법서.page.jsonl', NULL, NOW()),

  (md5('document:hanwha_summary_v1')::uuid,
   md5('insurer:hanwha')::uuid,
   md5('product:hanwha_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/hanwha/상품요약서/한화_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:hanwha_proposal_v1')::uuid,
   md5('insurer:hanwha')::uuid,
   md5('product:hanwha_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/hanwha/가입설계서/한화_가입설계서_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- HEUNGKUK (4 documents, no variants)
  -- ========================================================================
  (md5('document:heungkuk_policy_v1')::uuid,
   md5('insurer:heungkuk')::uuid,
   md5('product:heungkuk_health_v1')::uuid,
   '약관', 'data/evidence_text/heungkuk/약관/흥국_약관.page.jsonl', NULL, NOW()),

  (md5('document:heungkuk_business_v1')::uuid,
   md5('insurer:heungkuk')::uuid,
   md5('product:heungkuk_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/heungkuk/사업방법서/흥국_사업방법서.page.jsonl', NULL, NOW()),

  (md5('document:heungkuk_summary_v1')::uuid,
   md5('insurer:heungkuk')::uuid,
   md5('product:heungkuk_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/heungkuk/상품요약서/흥국_상품요약서.page.jsonl', NULL, NOW()),

  (md5('document:heungkuk_proposal_v1')::uuid,
   md5('insurer:heungkuk')::uuid,
   md5('product:heungkuk_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/heungkuk/가입설계서/흥국_가입설계서_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- LOTTE (8 documents: 4 male + 4 female variants)
  -- ========================================================================
  -- NOTE: LOTTE documents are NOT inserted here because the document table
  -- does NOT have a variant_id FK column in the current schema.
  -- Documents are linked to products, not variants.
  -- Variants are applied at the coverage_instance level.
  -- For now, we'll insert LOTTE documents without variant linkage.
  -- The variant relationship will be established when loading coverage_instance.

  -- Male variants (약관, 사업방법서, 상품요약서, 가입설계서)
  (md5('document:lotte_policy_male_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '약관', 'data/evidence_text/lotte/약관/롯데_약관(남).page.jsonl', NULL, NOW()),

  (md5('document:lotte_business_male_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/lotte/사업방법서/롯데_사업방법서(남).page.jsonl', NULL, NOW()),

  (md5('document:lotte_summary_male_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/lotte/상품요약서/롯데_상품요약서(남).page.jsonl', NULL, NOW()),

  (md5('document:lotte_proposal_male_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/lotte/가입설계서/롯데_가입설계서(남)_2511.page.jsonl', NULL, NOW()),

  -- Female variants (약관, 사업방법서, 상품요약서, 가입설계서)
  (md5('document:lotte_policy_female_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '약관', 'data/evidence_text/lotte/약관/롯데_약관(여).page.jsonl', NULL, NOW()),

  (md5('document:lotte_business_female_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/lotte/사업방법서/롯데_사업방법서(여).page.jsonl', NULL, NOW()),

  (md5('document:lotte_summary_female_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/lotte/상품요약서/롯데_상품요약서(여).page.jsonl', NULL, NOW()),

  (md5('document:lotte_proposal_female_v1')::uuid,
   md5('insurer:lotte')::uuid,
   md5('product:lotte_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/lotte/가입설계서/롯데_가입설계서(여)_2511.page.jsonl', NULL, NOW()),

  -- ========================================================================
  -- DB (5 documents: 3 no-variant + 2 age-variant 가입설계서)
  -- ========================================================================
  -- No-variant documents (약관, 사업방법서, 상품요약서)
  (md5('document:db_policy_v1')::uuid,
   md5('insurer:db')::uuid,
   md5('product:db_health_v1')::uuid,
   '약관', 'data/evidence_text/db/약관/DB_약관.page.jsonl', NULL, NOW()),

  (md5('document:db_business_v1')::uuid,
   md5('insurer:db')::uuid,
   md5('product:db_health_v1')::uuid,
   '사업방법서', 'data/evidence_text/db/사업방법서/DB_사업방법서.page.jsonl', NULL, NOW()),

  (md5('document:db_summary_v1')::uuid,
   md5('insurer:db')::uuid,
   md5('product:db_health_v1')::uuid,
   '상품요약서', 'data/evidence_text/db/상품요약서/DB_상품요약서.page.jsonl', NULL, NOW()),

  -- Age-variant documents (가입설계서: 40세이하/41세이상)
  -- NOTE: Like LOTTE, variant linkage is established at coverage_instance level
  (md5('document:db_proposal_u40_v1')::uuid,
   md5('insurer:db')::uuid,
   md5('product:db_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/db/가입설계서/DB_가입설계서(40세이하)_2511.page.jsonl', NULL, NOW()),

  (md5('document:db_proposal_o40_v1')::uuid,
   md5('insurer:db')::uuid,
   md5('product:db_health_v1')::uuid,
   '가입설계서', 'data/evidence_text/db/가입설계서/DB_가입설계서(41세이상)_2511.page.jsonl', NULL, NOW())

ON CONFLICT (document_id) DO UPDATE
  SET file_path = EXCLUDED.file_path,
      doc_type = EXCLUDED.doc_type;

-- ============================================================================
-- END OF SEED
-- ============================================================================
-- Summary:
--   - insurer: 8 rows
--   - doc_structure_profile: 1 row (default placeholder)
--   - product: 8 rows
--   - product_variant: 4 rows (LOTTE 2 + DB 2)
--   - document: 38 rows
--
-- NOT SEEDED (remains 0 rows):
--   - coverage_canonical
--   - coverage_instance
--   - evidence_ref
--   - amount_fact
-- ============================================================================
