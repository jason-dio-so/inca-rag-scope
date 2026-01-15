--
-- PostgreSQL database dump
--

\restrict havpIup4bIFQlgDSWQihdSiWBcbPRnWjpfP1aBmQOrCDi2eKa4L195shZcNYbbX

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: compare_table_v2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.compare_table_v2 (
    table_id bigint NOT NULL,
    as_of_date date DEFAULT '2025-11-26'::date NOT NULL,
    coverage_code character varying(20) NOT NULL,
    canonical_name text NOT NULL,
    insurer_set jsonb NOT NULL,
    payload jsonb NOT NULL,
    computed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    pipeline_version character varying(20) DEFAULT 'V2'::character varying
);


ALTER TABLE public.compare_table_v2 OWNER TO postgres;

--
-- Name: TABLE compare_table_v2; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.compare_table_v2 IS 'Step4 결과: Q12/Q13/Q14 비교표 (UI SSOT, JSONB 유연성)';


--
-- Name: compare_table_v2_table_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.compare_table_v2_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.compare_table_v2_table_id_seq OWNER TO postgres;

--
-- Name: compare_table_v2_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.compare_table_v2_table_id_seq OWNED BY public.compare_table_v2.table_id;


--
-- Name: coverage_canonical; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coverage_canonical (
    coverage_code character varying(20) NOT NULL,
    canonical_name character varying(200) NOT NULL,
    coverage_category character varying(50),
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.coverage_canonical OWNER TO postgres;

--
-- Name: TABLE coverage_canonical; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.coverage_canonical IS '담보 정규명 마스터 (coverage_code → canonical_name)';


--
-- Name: COLUMN coverage_canonical.coverage_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_canonical.coverage_code IS '담보 코드 (e.g., A4200_1)';


--
-- Name: COLUMN coverage_canonical.canonical_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_canonical.canonical_name IS '정규 담보명 (e.g., 암진단비(유사암제외))';


--
-- Name: coverage_chunk; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coverage_chunk (
    chunk_id bigint NOT NULL,
    ins_cd character varying(10) NOT NULL,
    coverage_code character varying(20) NOT NULL,
    as_of_date date DEFAULT '2025-11-26'::date NOT NULL,
    doc_type character varying(20) NOT NULL,
    source_pdf text NOT NULL,
    page_start integer NOT NULL,
    page_end integer NOT NULL,
    excerpt text NOT NULL,
    chunk_text text NOT NULL,
    chunk_kind text,
    anchor_text text,
    content_hash text,
    chunk_length integer GENERATED ALWAYS AS (length(chunk_text)) STORED,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT coverage_chunk_doc_type_check CHECK (((doc_type)::text = ANY ((ARRAY['약관'::character varying, '사업방법서'::character varying, '요약서'::character varying])::text[])))
);


ALTER TABLE public.coverage_chunk OWNER TO postgres;

--
-- Name: TABLE coverage_chunk; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.coverage_chunk IS 'Step2 결과: 약관/사업방법서 coverage 기반 chunk (SSOT FK 강제)';


--
-- Name: coverage_chunk_chunk_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.coverage_chunk_chunk_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.coverage_chunk_chunk_id_seq OWNER TO postgres;

--
-- Name: coverage_chunk_chunk_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.coverage_chunk_chunk_id_seq OWNED BY public.coverage_chunk.chunk_id;


--
-- Name: coverage_mapping_ssot; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coverage_mapping_ssot (
    ins_cd character varying(10) NOT NULL,
    coverage_code character varying(20) NOT NULL,
    insurer_coverage_name text NOT NULL,
    as_of_date date NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source character varying(20) DEFAULT 'MANUAL'::character varying NOT NULL,
    CONSTRAINT coverage_mapping_ssot_source_check CHECK (((source)::text = ANY ((ARRAY['MANUAL'::character varying, 'DERIVED'::character varying, 'API'::character varying])::text[]))),
    CONSTRAINT coverage_mapping_ssot_status_check CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'DEPRECATED'::character varying])::text[])))
);


ALTER TABLE public.coverage_mapping_ssot OWNER TO postgres;

--
-- Name: TABLE coverage_mapping_ssot; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.coverage_mapping_ssot IS '보험사별 담보 매핑 SSOT - 모든 pipeline의 기준';


--
-- Name: COLUMN coverage_mapping_ssot.ins_cd; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.ins_cd IS '보험사 코드';


--
-- Name: COLUMN coverage_mapping_ssot.coverage_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.coverage_code IS '담보 코드';


--
-- Name: COLUMN coverage_mapping_ssot.insurer_coverage_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.insurer_coverage_name IS '보험사별 담보명 원문 (약관상 표기)';


--
-- Name: COLUMN coverage_mapping_ssot.as_of_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.as_of_date IS '매핑 기준일 (PK 포함 - 시간에 따른 변경 이력 관리)';


--
-- Name: COLUMN coverage_mapping_ssot.status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.status IS 'ACTIVE: 현행 / DEPRECATED: 구버전';


--
-- Name: COLUMN coverage_mapping_ssot.source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_mapping_ssot.source IS 'MANUAL: 수동입력 / DERIVED: 파생 / API: API 수집';


--
-- Name: coverage_premium_quote; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coverage_premium_quote (
    ins_cd character varying(10) NOT NULL,
    product_id character varying(255) NOT NULL,
    coverage_code character varying(50) NOT NULL,
    plan_variant character varying(50) DEFAULT 'NO_REFUND'::character varying NOT NULL,
    age integer NOT NULL,
    sex character varying(1) NOT NULL,
    premium_monthly_coverage integer,
    coverage_amount bigint,
    as_of_date date NOT NULL,
    coverage_name character varying(500),
    source character varying(50) DEFAULT 'API'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    coverage_title_raw text,
    coverage_name_normalized character varying(500),
    coverage_amount_raw text,
    coverage_amount_value bigint,
    multiplier_percent integer DEFAULT 100,
    source_table_id character varying(100),
    source_row_id character varying(100),
    smoke character varying(2) DEFAULT 'NA'::character varying,
    pay_term_years integer,
    ins_term_years integer
);


ALTER TABLE public.coverage_premium_quote OWNER TO postgres;

--
-- Name: TABLE coverage_premium_quote; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.coverage_premium_quote IS 'Coverage-level premium breakdown (from prDetail.cvrAmtArrLst)';


--
-- Name: COLUMN coverage_premium_quote.coverage_code; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.coverage_code IS 'Normalized coverage code (e.g., A4200_1)';


--
-- Name: COLUMN coverage_premium_quote.premium_monthly_coverage; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.premium_monthly_coverage IS 'Monthly premium for this coverage (from cvrAmtArrLst[*].monthlyPrem)';


--
-- Name: COLUMN coverage_premium_quote.coverage_title_raw; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.coverage_title_raw IS 'Raw coverage name from API (cvrNm)';


--
-- Name: COLUMN coverage_premium_quote.coverage_amount_raw; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.coverage_amount_raw IS 'Raw coverage amount string (accAmt)';


--
-- Name: COLUMN coverage_premium_quote.coverage_amount_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.coverage_amount_value IS 'Parsed coverage amount as integer';


--
-- Name: COLUMN coverage_premium_quote.multiplier_percent; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.coverage_premium_quote.multiplier_percent IS 'Plan variant multiplier (100 for NO_REFUND, varies for GENERAL)';


--
-- Name: evidence_slot; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.evidence_slot (
    evidence_id bigint NOT NULL,
    ins_cd character varying(10) NOT NULL,
    coverage_code character varying(20) NOT NULL,
    as_of_date date DEFAULT '2025-11-26'::date NOT NULL,
    slot_key text NOT NULL,
    status character varying(20) NOT NULL,
    doc_type character varying(20),
    source_pdf text,
    page_range character varying(20),
    excerpt text,
    excerpt_length integer GENERATED ALWAYS AS (length(excerpt)) STORED,
    gate_version text DEFAULT 'GATE_SSOT_V1'::text NOT NULL,
    gate_passed jsonb,
    rejected_candidates integer DEFAULT 0 NOT NULL,
    resolved_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    pipeline_version character varying(20) DEFAULT 'V2'::character varying,
    CONSTRAINT evidence_slot_check CHECK (((((status)::text = 'FOUND'::text) AND (doc_type IS NOT NULL) AND (page_range IS NOT NULL) AND (excerpt IS NOT NULL)) OR ((status)::text = 'NOT_FOUND'::text))),
    CONSTRAINT evidence_slot_status_check CHECK (((status)::text = ANY ((ARRAY['FOUND'::character varying, 'NOT_FOUND'::character varying])::text[])))
);


ALTER TABLE public.evidence_slot OWNER TO postgres;

--
-- Name: TABLE evidence_slot; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.evidence_slot IS 'Step3 결과: Evidence resolver 출력 (Gate 검증 포함, SSOT FK 강제)';


--
-- Name: evidence_slot_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.evidence_slot_evidence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.evidence_slot_evidence_id_seq OWNER TO postgres;

--
-- Name: evidence_slot_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.evidence_slot_evidence_id_seq OWNED BY public.evidence_slot.evidence_id;


--
-- Name: insurer; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.insurer (
    ins_cd character varying(10) NOT NULL,
    insurer_name_ko character varying(100) NOT NULL,
    insurer_name_en character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.insurer OWNER TO postgres;

--
-- Name: TABLE insurer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.insurer IS '보험사 마스터 테이블';


--
-- Name: COLUMN insurer.ins_cd; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.insurer.ins_cd IS '보험사 코드 (e.g., N01, N02)';


--
-- Name: COLUMN insurer.insurer_name_ko; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.insurer.insurer_name_ko IS '보험사명 한글';


--
-- Name: product; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product (
    product_id character varying(50) NOT NULL,
    ins_cd character varying(10) NOT NULL,
    product_full_name text NOT NULL,
    as_of_date date NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    product_name_base text,
    version text,
    effective_date date
);


ALTER TABLE public.product OWNER TO postgres;

--
-- Name: TABLE product; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product IS '상품 마스터 (Q12/Q14/보험료 UI용) - SSOT는 premium_raw(prInfo).prNm';


--
-- Name: COLUMN product.product_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.product_id IS '상품 식별자';


--
-- Name: COLUMN product.product_full_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.product_full_name IS '상품 전체명 (prInfo.prNm 원문 - 납입조건 포함)';


--
-- Name: COLUMN product.as_of_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.as_of_date IS '데이터 스냅샷 적재 기준일 (effective_date와 다름)';


--
-- Name: COLUMN product.product_name_base; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.product_name_base IS '상품 기본명 (약관 메타데이터용)';


--
-- Name: COLUMN product.version; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.version IS '상품 버전 (예: 2508)';


--
-- Name: COLUMN product.effective_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product.effective_date IS '상품 시행일 (약관 발효일)';


--
-- Name: product_id_map; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_id_map (
    ins_cd character varying(10) NOT NULL,
    compare_product_id character varying(255) NOT NULL,
    premium_product_id character varying(255) NOT NULL,
    as_of_date date NOT NULL,
    source character varying(50) DEFAULT 'API'::character varying,
    evidence_ref text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.product_id_map OWNER TO postgres;

--
-- Name: TABLE product_id_map; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_id_map IS 'Mapping between compare product IDs and premium API product IDs (temporal versioning)';


--
-- Name: COLUMN product_id_map.compare_product_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_id_map.compare_product_id IS 'Product ID used in coverage comparison (A-level canonical)';


--
-- Name: COLUMN product_id_map.premium_product_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_id_map.premium_product_id IS 'Product ID from premium API response (prCd)';


--
-- Name: COLUMN product_id_map.evidence_ref; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_id_map.evidence_ref IS 'JSON reference to source (e.g., prInfo file path)';


--
-- Name: product_premium_quote_v2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_premium_quote_v2 (
    ins_cd character varying(10) NOT NULL,
    product_id character varying(255) NOT NULL,
    plan_variant character varying(50) DEFAULT 'NO_REFUND'::character varying NOT NULL,
    age integer NOT NULL,
    sex character varying(1) NOT NULL,
    pay_term_years integer,
    ins_term_years integer,
    premium_monthly_total integer,
    premium_total_total bigint,
    as_of_date date NOT NULL,
    product_full_name character varying(500),
    source character varying(50) DEFAULT 'API'::character varying,
    api_response_hash character varying(64),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    calculated_monthly_sum integer,
    sum_match_status character varying(20),
    source_table_id character varying(100),
    source_row_id character varying(100),
    smoke character varying(2) DEFAULT 'NA'::character varying,
    CONSTRAINT chk_product_premium_v2_sum_match_status CHECK (((sum_match_status)::text = ANY ((ARRAY['MATCH'::character varying, 'MISMATCH'::character varying, 'UNKNOWN'::character varying, NULL::character varying])::text[])))
);


ALTER TABLE public.product_premium_quote_v2 OWNER TO postgres;

--
-- Name: TABLE product_premium_quote_v2; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_premium_quote_v2 IS 'Product-level premium quotes (SSOT from API prDetail)';


--
-- Name: COLUMN product_premium_quote_v2.premium_monthly_total; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_quote_v2.premium_monthly_total IS 'SSOT: prDetail.monthlyPremSum (total monthly premium)';


--
-- Name: COLUMN product_premium_quote_v2.premium_total_total; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_quote_v2.premium_total_total IS 'SSOT: prDetail.totalPremSum (total premium over payment period)';


--
-- Name: COLUMN product_premium_quote_v2.api_response_hash; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_quote_v2.api_response_hash IS 'SHA256 hash of API response for audit trail';


--
-- Name: COLUMN product_premium_quote_v2.calculated_monthly_sum; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_quote_v2.calculated_monthly_sum IS 'Sum of coverage_premium_quote.premium_monthly_coverage';


--
-- Name: COLUMN product_premium_quote_v2.sum_match_status; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_quote_v2.sum_match_status IS 'MATCH if calculated_monthly_sum = premium_monthly_total, MISMATCH otherwise';


--
-- Name: product_premium_ssot; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_premium_ssot (
    id integer NOT NULL,
    as_of_date date NOT NULL,
    ins_cd character varying(10) NOT NULL,
    age integer NOT NULL,
    sex character varying(1) NOT NULL,
    plan_variant character varying(50),
    pay_term_years integer,
    ins_term_years integer,
    monthly_premium_total integer NOT NULL,
    source character varying(50) DEFAULT 'premium_raw'::character varying NOT NULL,
    raw_ref text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT product_premium_ssot_sex_check CHECK (((sex)::text = ANY ((ARRAY['M'::character varying, 'F'::character varying])::text[])))
);


ALTER TABLE public.product_premium_ssot OWNER TO postgres;

--
-- Name: TABLE product_premium_ssot; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_premium_ssot IS 'Premium SSOT - migrated from premium_raw JSON';


--
-- Name: COLUMN product_premium_ssot.source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_ssot.source IS 'Source of premium data (premium_raw, etc.)';


--
-- Name: COLUMN product_premium_ssot.raw_ref; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_premium_ssot.raw_ref IS 'Reference to raw JSON file path';


--
-- Name: product_premium_ssot_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.product_premium_ssot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_premium_ssot_id_seq OWNER TO postgres;

--
-- Name: product_premium_ssot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.product_premium_ssot_id_seq OWNED BY public.product_premium_ssot.id;


--
-- Name: product_variant; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_variant (
    variant_id character varying(100) NOT NULL,
    product_id character varying(50) NOT NULL,
    variant_key character varying(50) NOT NULL,
    pay_term_years integer,
    ins_term_years integer,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    plan_variant character varying(20),
    age integer,
    sex character varying(10),
    as_of_date date,
    CONSTRAINT product_variant_plan_variant_check CHECK (((plan_variant)::text = ANY ((ARRAY['GENERAL'::character varying, 'NO_REFUND'::character varying])::text[]))),
    CONSTRAINT product_variant_sex_check CHECK (((sex)::text = ANY ((ARRAY['M'::character varying, 'F'::character varying, 'UNISEX'::character varying])::text[])))
);


ALTER TABLE public.product_variant OWNER TO postgres;

--
-- Name: TABLE product_variant; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_variant IS '상품 변형 (일반/무해지, 납입/만기, 나이/성별) - Q12/Q13/Q14 비교 키';


--
-- Name: COLUMN product_variant.variant_key; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_variant.variant_key IS 'DEPRECATED - use plan_variant';


--
-- Name: COLUMN product_variant.pay_term_years; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_variant.pay_term_years IS '납입 기간 (년)';


--
-- Name: COLUMN product_variant.ins_term_years; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_variant.ins_term_years IS '보험 기간 (년)';


--
-- Name: COLUMN product_variant.plan_variant; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.product_variant.plan_variant IS '플랜 변형 (GENERAL: 일반, NO_REFUND: 무해지)';


--
-- Name: compare_table_v2 table_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.compare_table_v2 ALTER COLUMN table_id SET DEFAULT nextval('public.compare_table_v2_table_id_seq'::regclass);


--
-- Name: coverage_chunk chunk_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_chunk ALTER COLUMN chunk_id SET DEFAULT nextval('public.coverage_chunk_chunk_id_seq'::regclass);


--
-- Name: evidence_slot evidence_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evidence_slot ALTER COLUMN evidence_id SET DEFAULT nextval('public.evidence_slot_evidence_id_seq'::regclass);


--
-- Name: product_premium_ssot id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_premium_ssot ALTER COLUMN id SET DEFAULT nextval('public.product_premium_ssot_id_seq'::regclass);


--
-- Name: compare_table_v2 compare_table_v2_as_of_date_coverage_code_insurer_set_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.compare_table_v2
    ADD CONSTRAINT compare_table_v2_as_of_date_coverage_code_insurer_set_key UNIQUE (as_of_date, coverage_code, insurer_set);


--
-- Name: compare_table_v2 compare_table_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.compare_table_v2
    ADD CONSTRAINT compare_table_v2_pkey PRIMARY KEY (table_id);


--
-- Name: coverage_canonical coverage_canonical_canonical_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_canonical
    ADD CONSTRAINT coverage_canonical_canonical_name_key UNIQUE (canonical_name);


--
-- Name: coverage_canonical coverage_canonical_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_canonical
    ADD CONSTRAINT coverage_canonical_pkey PRIMARY KEY (coverage_code);


--
-- Name: coverage_chunk coverage_chunk_ins_cd_coverage_code_as_of_date_doc_type_sou_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_chunk
    ADD CONSTRAINT coverage_chunk_ins_cd_coverage_code_as_of_date_doc_type_sou_key UNIQUE (ins_cd, coverage_code, as_of_date, doc_type, source_pdf, page_start, page_end, content_hash);


--
-- Name: coverage_chunk coverage_chunk_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_chunk
    ADD CONSTRAINT coverage_chunk_pkey PRIMARY KEY (chunk_id);


--
-- Name: coverage_mapping_ssot coverage_mapping_ssot_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_mapping_ssot
    ADD CONSTRAINT coverage_mapping_ssot_pkey PRIMARY KEY (ins_cd, coverage_code, as_of_date);


--
-- Name: coverage_premium_quote coverage_premium_quote_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_premium_quote
    ADD CONSTRAINT coverage_premium_quote_pkey PRIMARY KEY (ins_cd, product_id, coverage_code, plan_variant, age, sex, as_of_date);


--
-- Name: evidence_slot evidence_slot_ins_cd_coverage_code_as_of_date_slot_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evidence_slot
    ADD CONSTRAINT evidence_slot_ins_cd_coverage_code_as_of_date_slot_key_key UNIQUE (ins_cd, coverage_code, as_of_date, slot_key);


--
-- Name: evidence_slot evidence_slot_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evidence_slot
    ADD CONSTRAINT evidence_slot_pkey PRIMARY KEY (evidence_id);


--
-- Name: insurer insurer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.insurer
    ADD CONSTRAINT insurer_pkey PRIMARY KEY (ins_cd);


--
-- Name: product_id_map pk_product_id_map; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_id_map
    ADD CONSTRAINT pk_product_id_map PRIMARY KEY (ins_cd, compare_product_id, as_of_date);


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (product_id);


--
-- Name: product_premium_quote_v2 product_premium_quote_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_premium_quote_v2
    ADD CONSTRAINT product_premium_quote_v2_pkey PRIMARY KEY (ins_cd, product_id, plan_variant, age, sex, as_of_date);


--
-- Name: product_premium_ssot product_premium_ssot_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_premium_ssot
    ADD CONSTRAINT product_premium_ssot_pkey PRIMARY KEY (id);


--
-- Name: product_variant product_variant_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variant
    ADD CONSTRAINT product_variant_pkey PRIMARY KEY (variant_id);


--
-- Name: product_variant product_variant_unique_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variant
    ADD CONSTRAINT product_variant_unique_key UNIQUE (product_id, plan_variant, pay_term_years, ins_term_years, age, sex, as_of_date);


--
-- Name: idx_compare_v2_as_of_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_compare_v2_as_of_date ON public.compare_table_v2 USING btree (as_of_date);


--
-- Name: idx_compare_v2_coverage; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_compare_v2_coverage ON public.compare_table_v2 USING btree (coverage_code);


--
-- Name: idx_compare_v2_insurer_set; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_compare_v2_insurer_set ON public.compare_table_v2 USING gin (insurer_set);


--
-- Name: idx_compare_v2_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_compare_v2_lookup ON public.compare_table_v2 USING btree (as_of_date, coverage_code);


--
-- Name: idx_coverage_chunk_doc_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_chunk_doc_type ON public.coverage_chunk USING btree (doc_type);


--
-- Name: idx_coverage_chunk_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_chunk_hash ON public.coverage_chunk USING btree (content_hash) WHERE (content_hash IS NOT NULL);


--
-- Name: idx_coverage_chunk_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_chunk_lookup ON public.coverage_chunk USING btree (ins_cd, coverage_code, as_of_date);


--
-- Name: idx_coverage_chunk_page; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_chunk_page ON public.coverage_chunk USING btree (page_start, page_end);


--
-- Name: idx_coverage_mapping_ssot_as_of_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_mapping_ssot_as_of_date ON public.coverage_mapping_ssot USING btree (as_of_date);


--
-- Name: idx_coverage_mapping_ssot_lock_2025_11_26; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_coverage_mapping_ssot_lock_2025_11_26 ON public.coverage_mapping_ssot USING btree (ins_cd, coverage_code) WHERE (as_of_date = '2025-11-26'::date);


--
-- Name: INDEX idx_coverage_mapping_ssot_lock_2025_11_26; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON INDEX public.idx_coverage_mapping_ssot_lock_2025_11_26 IS 'LOCK 기준일(2025-11-26) 스냅샷 UNIQUE 제약 - FK 참조 타깃';


--
-- Name: idx_coverage_mapping_ssot_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_mapping_ssot_status ON public.coverage_mapping_ssot USING btree (status);


--
-- Name: idx_coverage_premium_as_of_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_premium_as_of_date ON public.coverage_premium_quote USING btree (as_of_date);


--
-- Name: idx_coverage_premium_coverage_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_premium_coverage_code ON public.coverage_premium_quote USING btree (coverage_code, as_of_date);


--
-- Name: idx_coverage_premium_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_premium_lookup ON public.coverage_premium_quote USING btree (ins_cd, product_id, plan_variant, age, sex, coverage_code);


--
-- Name: idx_coverage_premium_quote_coverage; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_premium_quote_coverage ON public.coverage_premium_quote USING btree (coverage_code, as_of_date);


--
-- Name: idx_coverage_premium_quote_scenario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coverage_premium_quote_scenario ON public.coverage_premium_quote USING btree (ins_cd, age, sex, as_of_date);


--
-- Name: idx_evidence_slot_gate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_evidence_slot_gate ON public.evidence_slot USING btree (gate_version);


--
-- Name: idx_evidence_slot_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_evidence_slot_key ON public.evidence_slot USING btree (slot_key);


--
-- Name: idx_evidence_slot_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_evidence_slot_lookup ON public.evidence_slot USING btree (ins_cd, coverage_code, as_of_date);


--
-- Name: idx_evidence_slot_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_evidence_slot_status ON public.evidence_slot USING btree (status);


--
-- Name: idx_product_id_map_premium_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_id_map_premium_id ON public.product_id_map USING btree (ins_cd, premium_product_id, as_of_date);


--
-- Name: idx_product_ins_cd; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_ins_cd ON public.product USING btree (ins_cd);


--
-- Name: idx_product_premium_quote_v2_scenario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_premium_quote_v2_scenario ON public.product_premium_quote_v2 USING btree (ins_cd, age, sex, as_of_date);


--
-- Name: idx_product_premium_ssot_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_premium_ssot_lookup ON public.product_premium_ssot USING btree (as_of_date, ins_cd, age, sex);


--
-- Name: idx_product_premium_ssot_unique; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_product_premium_ssot_unique ON public.product_premium_ssot USING btree (as_of_date, ins_cd, age, sex, plan_variant, pay_term_years, ins_term_years) WHERE (plan_variant IS NOT NULL);


--
-- Name: idx_product_premium_ssot_unique_null; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_product_premium_ssot_unique_null ON public.product_premium_ssot USING btree (as_of_date, ins_cd, age, sex) WHERE (plan_variant IS NULL);


--
-- Name: idx_product_premium_v2_as_of_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_premium_v2_as_of_date ON public.product_premium_quote_v2 USING btree (as_of_date);


--
-- Name: idx_product_premium_v2_lookup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_premium_v2_lookup ON public.product_premium_quote_v2 USING btree (ins_cd, product_id, plan_variant, age, sex, as_of_date);


--
-- Name: idx_product_variant_product_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_variant_product_id ON public.product_variant USING btree (product_id);


--
-- Name: compare_table_v2 compare_table_v2_coverage_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.compare_table_v2
    ADD CONSTRAINT compare_table_v2_coverage_code_fkey FOREIGN KEY (coverage_code) REFERENCES public.coverage_canonical(coverage_code);


--
-- Name: coverage_chunk coverage_chunk_ins_cd_coverage_code_as_of_date_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_chunk
    ADD CONSTRAINT coverage_chunk_ins_cd_coverage_code_as_of_date_fkey FOREIGN KEY (ins_cd, coverage_code, as_of_date) REFERENCES public.coverage_mapping_ssot(ins_cd, coverage_code, as_of_date);


--
-- Name: coverage_mapping_ssot coverage_mapping_ssot_coverage_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_mapping_ssot
    ADD CONSTRAINT coverage_mapping_ssot_coverage_code_fkey FOREIGN KEY (coverage_code) REFERENCES public.coverage_canonical(coverage_code);


--
-- Name: coverage_mapping_ssot coverage_mapping_ssot_ins_cd_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_mapping_ssot
    ADD CONSTRAINT coverage_mapping_ssot_ins_cd_fkey FOREIGN KEY (ins_cd) REFERENCES public.insurer(ins_cd);


--
-- Name: coverage_premium_quote coverage_premium_quote_ins_cd_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_premium_quote
    ADD CONSTRAINT coverage_premium_quote_ins_cd_fkey FOREIGN KEY (ins_cd) REFERENCES public.insurer(ins_cd);


--
-- Name: coverage_premium_quote coverage_premium_quote_ins_cd_product_id_plan_variant_age__fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coverage_premium_quote
    ADD CONSTRAINT coverage_premium_quote_ins_cd_product_id_plan_variant_age__fkey FOREIGN KEY (ins_cd, product_id, plan_variant, age, sex, as_of_date) REFERENCES public.product_premium_quote_v2(ins_cd, product_id, plan_variant, age, sex, as_of_date) ON DELETE CASCADE;


--
-- Name: evidence_slot evidence_slot_ins_cd_coverage_code_as_of_date_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.evidence_slot
    ADD CONSTRAINT evidence_slot_ins_cd_coverage_code_as_of_date_fkey FOREIGN KEY (ins_cd, coverage_code, as_of_date) REFERENCES public.coverage_mapping_ssot(ins_cd, coverage_code, as_of_date);


--
-- Name: product_id_map fk_product_id_map_insurer; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_id_map
    ADD CONSTRAINT fk_product_id_map_insurer FOREIGN KEY (ins_cd) REFERENCES public.insurer(ins_cd) ON DELETE CASCADE;


--
-- Name: product product_ins_cd_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_ins_cd_fkey FOREIGN KEY (ins_cd) REFERENCES public.insurer(ins_cd);


--
-- Name: product_premium_quote_v2 product_premium_quote_v2_ins_cd_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_premium_quote_v2
    ADD CONSTRAINT product_premium_quote_v2_ins_cd_fkey FOREIGN KEY (ins_cd) REFERENCES public.insurer(ins_cd);


--
-- Name: product_variant product_variant_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variant
    ADD CONSTRAINT product_variant_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(product_id);


--
-- PostgreSQL database dump complete
--

\unrestrict havpIup4bIFQlgDSWQihdSiWBcbPRnWjpfP1aBmQOrCDi2eKa4L195shZcNYbbX

