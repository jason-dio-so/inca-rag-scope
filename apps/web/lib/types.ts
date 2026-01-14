/**
 * STEP NEXT-UI-02: Type Definitions
 * Based on FastAPI chat_vm.py contract
 */

export type LlmMode = "OFF" | "ON";

export type MessageKind =
  | "PREMIUM_COMPARE"
  | "EX1_PREMIUM_DISABLED"
  | "EX2_DETAIL"           // STEP NEXT-86: 단일 담보 설명
  | "EX2_DETAIL_DIFF"
  | "EX2_LIMIT_FIND"      // STEP NEXT-78
  | "EX3_INTEGRATED"
  | "EX3_COMPARE"          // STEP NEXT-77
  | "EX4_ELIGIBILITY"
  | "KNOWLEDGE_BASE"
  | "Q11_OVERLAY"         // STEP DEMO-LAUNCHER-FIX-01: Overlay adapters
  | "Q13_OVERLAY"
  | "Q5_OVERLAY"
  | "Q7_OVERLAY"
  | "Q8_OVERLAY"
  | "OVERLAY_GENERIC";

// EXAM ISOLATION: Explicit exam type for cross-contamination prevention
export type ExamType = "EXAM1" | "EXAM2" | "EXAM3" | "EXAM4";

export interface ChatRequest {
  message: string;
  kind?: MessageKind;  // STEP NEXT-79-FE: Explicit kind (Priority 1)
  selected_category?: string;
  insurers?: string[];
  coverage_names?: string[];
  compare_field?: string;
  llm_mode?: LlmMode;
}

export interface CellMeta {
  evidence_ref_id?: string;
  highlight?: boolean;
  evidences?: any[];  // STEP DEMO-EVIDENCE-RELEVANCE-01: Slot-specific evidence
  slotName?: string;  // STEP DEMO-EVIDENCE-RELEVANCE-01: Slot identifier (e.g., "duration_limit_days")
}

export interface TableCell {
  value_text?: string;  // Legacy
  text?: string;        // STEP NEXT-73R: Backend uses 'text'
  meta?: CellMeta;
}

// STEP NEXT-75: KPI Summary for UI display
export interface KPISummaryMeta {
  payment_type: string;
  limit_summary?: string | null;
  kpi_evidence_refs?: string[];
  extraction_notes?: string;
}

// STEP NEXT-76: KPI Condition Summary for UI display
export interface KPIConditionMeta {
  waiting_period?: string | null;
  reduction_condition?: string | null;
  exclusion_condition?: string | null;
  renewal_condition?: string | null;
  condition_evidence_refs?: string[];
  extraction_notes?: string;
}

// STEP NEXT-73R: Row-level metadata for refs
export interface TableRowMeta {
  proposal_detail_ref?: string;
  evidence_refs?: string[];
  evidences?: any[];  // STEP DEMO-EVIDENCE-VIS-01: Direct evidence objects for overlay responses
  productName?: string;  // STEP DEMO-Q11-POLISH-01: Product name for insurer
  note?: string;  // STEP DEMO-Q11-POLISH-01: Reference note
  kpi_summary?: KPISummaryMeta;  // STEP NEXT-75
  kpi_condition?: KPIConditionMeta;  // STEP NEXT-76
}

export interface TableRow {
  label?: string;       // Legacy
  values?: TableCell[]; // Legacy
  cells?: TableCell[];  // STEP NEXT-73R: Backend uses 'cells'
  is_header?: boolean;
  meta?: TableRowMeta;  // STEP NEXT-73R
}

export interface ComparisonTableSection {
  kind: "comparison_table";
  table_kind: string;
  title: string;
  columns?: string[];
  rows?: TableRow[];
}

export interface BulletGroup {
  title: string;
  bullets?: string[];
}

export interface CommonNotesSection {
  kind: "common_notes";
  title: string;
  bullets?: string[];
  groups?: BulletGroup[];
}

export interface EvidenceItem {
  evidence_ref_id: string;
  insurer: string;
  coverage_name: string;
  doc_type: string;
  page?: number;
  snippet?: string;
}

export interface EvidenceAccordionSection {
  kind: "evidence_accordion";
  title: string;
  items?: EvidenceItem[];
  defaultCollapsed?: boolean;
}

// STEP NEXT-79-FE: Overall Evaluation for EX4_ELIGIBILITY
export type OverallDecision = "RECOMMEND" | "NOT_RECOMMEND" | "NEUTRAL";

export interface OverallEvaluationReason {
  type: string;
  description: string;
  refs: string[];
}

export interface OverallEvaluationSection {
  kind: "overall_evaluation";
  title: string;
  overall_evaluation: {
    decision: OverallDecision;
    summary: string;
    reasons: OverallEvaluationReason[];
    notes: string;
  };
}

export type Section =
  | ComparisonTableSection
  | CommonNotesSection
  | EvidenceAccordionSection
  | CoverageDiffResultSection
  | OverallEvaluationSection;

export interface Lineage {
  handler?: string;
  llm_used?: boolean;
  deterministic?: boolean;
  gate_failed?: boolean;
  gates?: Record<string, number>;
}

export interface AssistantMessageVM {
  kind: MessageKind;
  exam_type?: ExamType;  // EXAM ISOLATION: Explicit exam type (OPTIONAL for overlays)
  title?: string;
  summary_bullets?: string[];
  sections?: Section[];
  bubble_markdown?: string;  // STEP NEXT-81B: Deterministic markdown summary
  lineage?: Lineage;
}

// STEP NEXT-73R: Store API types
export interface ProposalDetailStoreItem {
  proposal_detail_ref: string;
  insurer: string;
  coverage_code: string;
  doc_type: string;
  page: number;
  benefit_description_text: string;
  hash: string;
}

export interface EvidenceStoreItem {
  evidence_ref: string;
  insurer: string;
  coverage_code: string;
  doc_type: string;
  page: number;
  snippet: string;
  match_keyword: string;
  hash: string;
}

export interface ChatResponse {
  // Success case - matches backend ChatResponse
  request_id?: string;
  timestamp?: string;
  need_more_info?: boolean;
  missing_slots?: string[];
  clarification_options?: Record<string, string[]>;
  message?: AssistantMessageVM;

  // Error case - added by frontend wrapper
  ok?: boolean;
  error?: {
    message: string;
    detail?: string;
  };
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  vm?: AssistantMessageVM;
}

export interface Category {
  id: string;
  label: string;
  description: string;
  example_kind: string;
  default_prompt: string;
  requires_slots: string[];
  status?: string;
}

export interface Insurer {
  code: string;
  display: string;
}

// STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched Diff Result Types
export interface EvidenceRef {
  doc_type: string;
  page: number;
  file_path?: string;
  snippet?: string;
}

export interface InsurerDetail {
  insurer: string;
  raw_text?: string;
  evidence_refs?: EvidenceRef[];
  notes?: string[];
}

export interface DiffGroup {
  value_display: string;
  insurers: string[];
  value_normalized?: Record<string, any>;
  insurer_details?: InsurerDetail[];
}

export interface CoverageDiffResultSection {
  kind: "coverage_diff_result";
  title: string;
  field_label: string;
  status: "DIFF" | "ALL_SAME";
  groups: DiffGroup[];
  diff_summary?: string;
  extraction_notes?: string[];
}

export interface UIConfig {
  categories: Category[];
  available_insurers: Insurer[];
  common_coverages: string[];
  ui_settings: {
    default_llm_mode: LlmMode;
    evidence_collapsed_by_default: boolean;
    max_insurers_per_query: number;
    enable_forbidden_phrase_check: boolean;
  };
}

// STEP NEXT-P2-Q11-REF-β: Q11 Reference Block Types
export interface Q11ReferenceEvidence {
  doc_type: string;
  page: number;
  excerpt: string;
}

export interface Q11ReferenceItem {
  insurer_key: string;
  coverage_title: string;
  duration_limit_days: number | null;
  daily_benefit_amount_won: number | null;
  evidence: Q11ReferenceEvidence;
  badge: string;
  note: string;
}
