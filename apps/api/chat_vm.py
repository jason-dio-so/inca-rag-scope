#!/usr/bin/env python3
"""
Chat View Model Schema for ChatGPT-style UI
STEP NEXT-14: Chat UI Integration

DESIGN PRINCIPLES:
1. Frontend renders VM JSON ONLY (NO LLM text parsing)
2. All sections are typed (TableSection, ExplanationSection, etc.)
3. Evidence is collapsible
4. NO forbidden words in any text fields
5. Deterministic compiler generates VM (NO LLM inference)

MESSAGE KINDS:
- EX2_DETAIL_DIFF: Coverage diff comparison (담보 조건 차이 탐색)
- EX3_INTEGRATED: Integrated comparison (통합 비교표 + 공통사항 + 유의사항)
- EX4_ELIGIBILITY: Eligibility matrix (질병 경계조건 기반 보장 가능 여부)
- EX1_PREMIUM_DISABLED: Premium comparison disabled (보험료 데이터 소스 미연동)
"""

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid

from apps.api.dto import AmountAuditDTO


# ============================================================================
# Section Types (Union Discriminator) - MINIMIZED TO 5 CORE TYPES
# ============================================================================

SectionKind = Literal[
    "summary",              # Summary bullets (always first)
    "comparison_table",     # Comparison table (all table types unified)
    "insurer_explanations", # Insurer-by-insurer parallel explanations
    "common_notes",         # Common notes/notices (unified)
    "evidence_accordion",   # Evidence (collapsible accordion)
    "coverage_diff_result"  # STEP NEXT-COMPARE-FILTER: Diff grouping result
]

# Legacy mapping (backward compat - to be removed)
_LEGACY_SECTION_KINDS = {
    "table": "comparison_table",
    "explanation": "insurer_explanations",
    "notices": "common_notes",
    "evidence": "evidence_accordion"
}


# ============================================================================
# Table Section (for EX2/EX3/EX4)
# ============================================================================

TableKind = Literal[
    "COVERAGE_DETAIL",      # 예시2: 담보 상세 비교 (보장개시/면책/감액 등)
    "INTEGRATED_COMPARE",   # 예시3: 통합 비교표
    "ELIGIBILITY_MATRIX"    # 예시4: 보장 가능 여부 매트릭스
]


class CellMeta(BaseModel):
    """Cell metadata for status-based styling"""
    status: Optional[str] = None  # CONFIRMED | UNCONFIRMED | NOT_AVAILABLE
    doc_ref: Optional[str] = None  # Evidence reference (optional)


class TableCell(BaseModel):
    """Single table cell with optional metadata"""
    text: str
    meta: Optional[CellMeta] = None


class KPISummaryMeta(BaseModel):
    """STEP NEXT-75: KPI Summary for row-level display"""
    payment_type: str
    limit_summary: Optional[str] = None
    kpi_evidence_refs: List[str] = []
    extraction_notes: str = ""


class KPIConditionMeta(BaseModel):
    """STEP NEXT-76: KPI Condition Summary for row-level display"""
    waiting_period: Optional[str] = None
    reduction_condition: Optional[str] = None
    exclusion_condition: Optional[str] = None
    renewal_condition: Optional[str] = None
    condition_evidence_refs: List[str] = []
    extraction_notes: str = ""


class TableRowMeta(BaseModel):
    """STEP NEXT-73R: Row-level metadata for refs"""
    proposal_detail_ref: Optional[str] = None
    evidence_refs: Optional[List[str]] = None
    kpi_summary: Optional[KPISummaryMeta] = None  # STEP NEXT-75
    kpi_condition: Optional[KPIConditionMeta] = None  # STEP NEXT-76


class TableRow(BaseModel):
    """Table row (header or data)"""
    cells: List[TableCell]
    is_header: bool = False
    meta: Optional[TableRowMeta] = None  # STEP NEXT-73R: Row-level refs


class ComparisonTableSection(BaseModel):
    """
    Comparison table section (UNIFIED)

    Replaces: TableSection (all table_kind variants)

    PRESENTATION RULES:
    - Headers are bolded
    - Cell styling is based on meta.status
    - NO color-based superiority (금지: 빨강=좋음, 파랑=나쁨)
    - NO sorting by amount

    USAGE:
    - Example 2: Coverage detail (보장개시/면책/감액/보장한도)
    - Example 3: Integrated comparison (담보 × 보험사)
    - Example 4: Eligibility matrix (하위개념 × 보험사, O/X)
    """
    kind: Literal["comparison_table"] = "comparison_table"
    table_kind: TableKind  # For semantic context (not for rendering)
    title: Optional[str] = None
    columns: List[str]  # Column headers
    rows: List[TableRow]


# ============================================================================
# Explanation Section (Step12 output)
# ============================================================================

class InsurerExplanation(BaseModel):
    """Single insurer's fact-only explanation"""
    insurer: str
    text: str  # From ExplanationTemplateRegistry (NO forbidden words)


class InsurerExplanationsSection(BaseModel):
    """
    Insurer explanations section (RENAMED for clarity)

    Replaces: ExplanationSection

    RULES:
    - Each insurer explanation is INDEPENDENT (parallel blocks)
    - NO comparative sentences (e.g., "A는 B보다")
    - NO forbidden words (validated by policy module)

    FRONTEND COMPONENT: InsurerExplanationBlocks
    """
    kind: Literal["insurer_explanations"] = "insurer_explanations"
    title: Optional[str] = None
    explanations: List[InsurerExplanation]


# ============================================================================
# Common Notes Section (예시3: 공통사항)
# ============================================================================

class BulletGroup(BaseModel):
    """
    Bullet group for visual separation (NEW in STEP NEXT-14-β)

    USAGE: 예시3에서 공통사항/유의사항을 시각적으로 분리 렌더
    """
    title: str  # e.g., "공통사항", "유의사항"
    bullets: List[str]

    @field_validator('bullets')
    @classmethod
    def validate_no_forbidden_words_in_bullets(cls, v: List[str]) -> List[str]:
        from apps.api.policy.forbidden_language import validate_text_list
        try:
            validate_text_list(v)
        except ValueError as e:
            raise ValueError(f"Forbidden language in group bullets: {e}")
        return v


class CommonNotesSection(BaseModel):
    """
    Common notes section (UNIFIED with notices)

    Replaces: CommonNotesSection + NoticesSection

    USAGE:
    - 공통사항 (모든 보험사 공통 특징)
    - 유의사항 (근거 기반 caveats)

    RULES:
    - Bullet list format
    - NO comparisons (e.g., "A가 B보다 우수")
    - Factual observations only (validated by policy module)

    FRONTEND COMPONENT: CommonNotes

    STEP NEXT-14-β EXTENSION:
    - groups: Optional[List[BulletGroup]] for visual separation (예시3)
    - Rendering priority: groups (if exists) > bullets (fallback)
    """
    kind: Literal["common_notes"] = "common_notes"
    title: str = "공통사항 및 유의사항"  # Unified title
    bullets: List[str] = []  # LEGACY (flat bullets, 호환성 유지)
    groups: Optional[List[BulletGroup]] = None  # NEW (grouped bullets for 예시3)


# ============================================================================
# Evidence Section (collapsible)
# ============================================================================

class EvidenceItem(BaseModel):
    """Single evidence item with source reference"""
    evidence_ref_id: str  # Unique ID for evidence
    insurer: str
    coverage_name: str
    doc_type: str  # e.g., "가입설계서"
    page: Optional[int] = None
    snippet: Optional[str] = None  # Max 400 chars


class EvidenceAccordionSection(BaseModel):
    """
    Evidence accordion section (RENAMED for UI clarity)

    Replaces: EvidenceSection

    PRESENTATION:
    - Accordion/collapsible (collapsed by default)
    - Expand on click
    - Grouped by insurer

    FRONTEND COMPONENT: EvidenceAccordion
    """
    kind: Literal["evidence_accordion"] = "evidence_accordion"
    title: str = "근거 자료"
    items: List[EvidenceItem]


# ============================================================================
# Coverage Diff Result Section (STEP NEXT-COMPARE-FILTER)
# ============================================================================

class InsurerDetail(BaseModel):
    """Detailed insurer data for diff group"""
    insurer: str
    raw_text: str
    evidence_refs: List[Dict[str, Any]] = []
    notes: Optional[List[str]] = None


class DiffGroup(BaseModel):
    """Group of insurers with same value (STEP NEXT-COMPARE-FILTER-DETAIL-02 enriched)"""
    value_display: str
    insurers: List[str]
    value_normalized: Optional[Dict[str, Any]] = None
    insurer_details: Optional[List[InsurerDetail]] = None


class CoverageDiffResultSection(BaseModel):
    """
    Coverage difference result section

    STEP NEXT-COMPARE-FILTER: Dedicated section for diff queries
    STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched with normalized values and evidence

    USAGE:
    - Query: "보장한도가 다른 상품 찾아줘"
    - Response: Groups insurers by field value

    PRESENTATION:
    - If status="ALL_SAME": Show single message
    - If status="DIFF": Show groups with diff_summary
    - insurer_details: expandable accordion with raw_text + evidence_refs

    FRONTEND COMPONENT: CoverageDiffCard
    """
    kind: Literal["coverage_diff_result"] = "coverage_diff_result"
    title: str
    field_label: str
    status: Literal["DIFF", "ALL_SAME"]
    groups: List[DiffGroup]
    diff_summary: Optional[str] = None
    extraction_notes: Optional[List[str]] = None  # For "명시 없음" explanations


# ============================================================================
# Overall Evaluation Section (STEP NEXT-79)
# ============================================================================

OverallDecision = Literal["RECOMMEND", "NOT_RECOMMEND", "NEUTRAL"]


class OverallEvaluationReason(BaseModel):
    """Single reason in overall evaluation"""
    type: str
    description: str
    refs: List[str]


class OverallEvaluation(BaseModel):
    """Overall evaluation data structure"""
    decision: OverallDecision
    summary: str
    reasons: List[OverallEvaluationReason]
    notes: str


class OverallEvaluationSection(BaseModel):
    """
    Overall evaluation section (STEP NEXT-79)

    EX4_ELIGIBILITY 전용 종합평가 섹션

    RULES:
    - MANDATORY for EX4_ELIGIBILITY (not optional)
    - decision ∈ {RECOMMEND, NOT_RECOMMEND, NEUTRAL}
    - Deterministic only (NO LLM)
    - All reasons MUST have refs (except Unknown status)

    FRONTEND COMPONENT: OverallEvaluationCard
    """
    kind: Literal["overall_evaluation"] = "overall_evaluation"
    title: str
    overall_evaluation: OverallEvaluation


# ============================================================================
# Section Union Type (7 CORE TYPES)
# ============================================================================

Section = (
    ComparisonTableSection |
    InsurerExplanationsSection |
    CommonNotesSection |
    EvidenceAccordionSection |
    CoverageDiffResultSection |
    OverallEvaluationSection
)

# Note: summary is part of AssistantMessageVM.summary_bullets (not a section)
# Note: DisabledNoticeSection removed (use CommonNotesSection with appropriate bullets)


# ============================================================================
# Assistant Message View Model (Top-level)
# ============================================================================

MessageKind = Literal[
    "EX2_DETAIL_DIFF",      # 예시2: 담보 조건 차이 탐색 (LEGACY - use EX2_LIMIT_FIND)
    "EX2_LIMIT_FIND",       # STEP NEXT-78: 보장한도/조건 값 차이 비교 (NO O/X)
    "EX3_INTEGRATED",       # 예시3: 통합 비교 (LEGACY - use EX3_COMPARE)
    "EX3_COMPARE",          # STEP NEXT-77: EX3 with locked schema (composer-based)
    "EX4_ELIGIBILITY",      # 예시4: 보장 가능 여부 (O/X/△ matrix)
    "EX1_PREMIUM_DISABLED", # 예시1: 보험료 비교 불가
    "PREMIUM_COMPARE"       # 예시1: 보험료 비교 (활성)
]


class AssistantMessageVM(BaseModel):
    """
    Top-level View Model for chat assistant response

    CRITICAL RULES:
    1. Frontend renders this JSON ONLY (NO text parsing)
    2. All text fields are forbidden-word validated
    3. Sections are typed (union discriminator)
    4. Lineage metadata is REQUIRED
    5. NO LLM-generated text (compiler output only)

    PRESENTATION:
    - ChatGPT-style card layout
    - Title + Summary + Sections
    - Evidence is collapsible
    - Lineage is collapsible
    """
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    request_id: uuid.UUID  # From /chat request
    kind: MessageKind
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    title: str  # Short header (e.g., "암진단비 비교 결과")
    summary_bullets: List[str]  # 3-6 bullets (fact-only)

    sections: List[Section]  # Typed sections (table/explanation/etc.)

    # STEP NEXT-81B: Bubble markdown (deterministic summary for central chat bubble)
    bubble_markdown: Optional[str] = None  # Markdown summary (NO raw text, refs only)

    lineage: Optional[AmountAuditDTO] = None  # Audit metadata (collapsible)

    class Config:
        frozen = True

    @field_validator('summary_bullets')
    @classmethod
    def validate_no_forbidden_words_in_summary(cls, v: List[str]) -> List[str]:
        """
        Enforce forbidden language policy in summary bullets

        DELEGATES to: apps.api.policy.forbidden_language (SINGLE SOURCE)
        """
        from apps.api.policy.forbidden_language import validate_text_list

        try:
            validate_text_list(v)
        except ValueError as e:
            raise ValueError(f"Forbidden language in summary_bullets: {e}")

        return v


# ============================================================================
# Chat Request/Response DTOs
# ============================================================================

class ChatRequest(BaseModel):
    """
    Chat request from frontend

    FLOW (Production - STEP NEXT-UI-01):
    1. Frontend specifies `selected_category` (sidebar click) → category-based routing
    2. OR Frontend specifies `kind` (from FAQ button) → 100% deterministic
    3. If both None, fallback to intent router (keyword-based, lower accuracy)
    4. Slot validator → check required fields
    5. Compiler → generate CompareRequest
    6. Handler → execute query + build VM

    CRITICAL: For production UI, set `selected_category` from sidebar selection.
    """
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    message: str  # User input text (for display/logging)

    # STEP NEXT-UI-01: Category-based routing (highest priority)
    selected_category: Optional[str] = None  # "단순보험료 비교", "상품/담보 설명", etc.

    # PRODUCTION: Set this from FAQ button click (deterministic)
    kind: Optional[MessageKind] = None  # If set, skip intent router

    faq_template_id: Optional[str] = None  # Legacy (use `kind` instead)

    # Optional slots (filled by user or FAQ template)
    coverage_names: Optional[List[str]] = None
    insurers: Optional[List[str]] = None
    disease_name: Optional[str] = None
    compare_field: Optional[str] = None  # STEP NEXT-COMPARE-FILTER-01: "보장한도", "보장금액", etc.

    # STEP NEXT-UI-01: LLM mode toggle
    llm_mode: Literal["OFF", "ON"] = "OFF"  # Default: LLM OFF

    # User profile (from top form)
    user_profile: Optional[Dict[str, Any]] = None  # birth_date, gender, etc.


class ChatResponse(BaseModel):
    """
    Chat response to frontend

    Two modes:
    1. need_more_info=True → ask for slots (1-2 questions max)
    2. need_more_info=False → full VM response
    """
    request_id: uuid.UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Mode 1: Need more info
    need_more_info: bool = False
    missing_slots: Optional[List[str]] = None  # e.g., ["coverage_names", "insurers"]
    clarification_options: Optional[Dict[str, List[str]]] = None  # UI selection options

    # Mode 2: Full response
    message: Optional[AssistantMessageVM] = None

    class Config:
        frozen = True


# ============================================================================
# FAQ Template Registry
# ============================================================================

class FAQTemplate(BaseModel):
    """FAQ template for quick queries"""
    template_id: str
    category: str  # e.g., "상품비교", "보장범위", "보험료"
    title: str
    prompt_template: str  # Template with {placeholders}
    required_slots: List[str]  # e.g., ["coverage_names", "insurers"]
    example_kind: MessageKind  # Target response kind


class FAQTemplateRegistry:
    """
    LOCKED FAQ templates

    CRITICAL RULES:
    1. Templates are deterministic (NO LLM generation)
    2. Templates map 1:1 to MessageKind
    3. Required slots are validated before execution
    4. NO templates for prohibited queries (e.g., premium estimation)
    """

    TEMPLATES = [
        FAQTemplate(
            template_id="ex2_coverage_detail",
            category="상품비교",
            title="담보 상세 비교 (보장한도/면책/감액)",
            prompt_template="{coverage_names}에 대해 {insurers} 간 보장 상세를 비교해주세요",
            required_slots=["coverage_names", "insurers"],
            example_kind="EX2_DETAIL_DIFF"
        ),
        FAQTemplate(
            template_id="ex3_integrated_compare",
            category="상품비교",
            title="통합 비교 (여러 담보)",
            prompt_template="{coverage_names} 담보들에 대해 {insurers} 간 통합 비교해주세요",
            required_slots=["coverage_names", "insurers"],
            example_kind="EX3_INTEGRATED"
        ),
        FAQTemplate(
            template_id="ex4_disease_eligibility",
            category="보장범위",
            title="질병 하위개념 보장 여부",
            prompt_template="{disease_name}에 대해 {insurers}의 보장 가능 여부를 알려주세요",
            required_slots=["disease_name", "insurers"],
            example_kind="EX4_ELIGIBILITY"
        ),
        FAQTemplate(
            template_id="ex1_premium_disabled",
            category="보험료",
            title="보험료 비교 (현재 제공 불가)",
            prompt_template="보험료 비교를 요청하셨습니다",
            required_slots=[],
            example_kind="EX1_PREMIUM_DISABLED"
        )
    ]

    @staticmethod
    def get_template(template_id: str) -> Optional[FAQTemplate]:
        """Get FAQ template by ID"""
        for template in FAQTemplateRegistry.TEMPLATES:
            if template.template_id == template_id:
                return template
        return None

    @staticmethod
    def get_by_category(category: str) -> List[FAQTemplate]:
        """Get all templates in category"""
        return [
            t for t in FAQTemplateRegistry.TEMPLATES
            if t.category == category
        ]
