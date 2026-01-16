/**
 * Q1 Premium Ranking Types
 *
 * Evidence-Mandatory + Rail-Only Design
 * per STEP_NEXT_CHAT_UI_V2_SPEC.md Section 2a
 */

// ========================================
// Evidence Types
// ========================================

export interface BasePremiumEvidence {
  source_table: 'product_premium_quote_v2';
  ins_cd: string;
  product_id: string;
  age: number;
  sex: 'M' | 'F';
  plan_variant: 'NO_REFUND' | 'GENERAL';
  as_of_date: string;
  premium_monthly_total: number;
  premium_total_total?: number;
  raw_ref?: string;
}

export interface RateMultiplierEvidence {
  source_table: 'coverage_premium_quote';
  ins_cd: string;
  product_id: string;
  multiplier_percent: number;
  as_of_date: string;
  coverage_code?: string;
  raw_ref?: string;
}

export interface PremiumRowEvidence {
  base_premium: BasePremiumEvidence;
  rate_multiplier?: RateMultiplierEvidence; // Only for GENERAL variant
}

// ========================================
// Q1 ViewModel
// ========================================

export interface Q1PremiumRow {
  rank: number;
  ins_cd: string;
  insurer_name: string;
  product_id: string;
  product_name?: string;

  // NO_REFUND premiums (always present if row is valid)
  premium_monthly_no_refund?: number;
  premium_total_no_refund?: number;

  // GENERAL premiums (optional, depends on plan_variant request)
  premium_monthly_general?: number;
  premium_total_general?: number;

  // Evidence references (Rail-only, not displayed in main table)
  evidence: PremiumRowEvidence;
}

export interface Q1ViewModel {
  kind: 'Q1';

  // Query metadata
  query_params: {
    age: number;
    sex: 'M' | 'F';
    plan_variant: 'NO_REFUND' | 'GENERAL' | 'BOTH';
    sort_by: 'monthly_total' | 'total';
    top_n: number;
    as_of_date: string;
  };

  // Top-N results
  rows: Q1PremiumRow[];

  // Error handling
  error?: string;
  note?: string;
}

// ========================================
// API Request/Response
// ========================================

export interface PremiumRankingRequest {
  age: number;
  sex: 'M' | 'F';
  plan_variant?: 'NO_REFUND' | 'GENERAL' | 'BOTH';
  sort_by?: 'monthly_total' | 'total';
  top_n?: number;
  as_of_date?: string;
}

export interface PremiumRankingResponse {
  success: boolean;
  data?: Q1ViewModel;
  error?: string;
}
