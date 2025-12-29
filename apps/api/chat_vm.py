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
- EX2_DETAIL: Coverage detail comparison (보장한도/면책/감액 등)
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
# Section Types (Union Discriminator)
# ============================================================================

SectionKind = Literal[
    "table",
    "explanation",
    "common_notes",
    "notices",
    "evidence",
    "disabled_notice"
]


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


class TableRow(BaseModel):
    """Table row (header or data)"""
    cells: List[TableCell]
    is_header: bool = False


class TableSection(BaseModel):
    """
    Table section for comparison data

    PRESENTATION RULES:
    - Headers are bolded
    - Cell styling is based on meta.status
    - NO color-based superiority (금지: 빨강=좋음, 파랑=나쁨)
    - NO sorting by amount
    """
    kind: Literal["table"] = "table"
    table_kind: TableKind
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


class ExplanationSection(BaseModel):
    """
    Explanation section (parallel, fact-only)

    RULES:
    - Each insurer explanation is INDEPENDENT
    - NO comparative sentences (e.g., "A는 B보다")
    - NO forbidden words (더/보다/유리/불리/높다/낮다)
    """
    kind: Literal["explanation"] = "explanation"
    title: Optional[str] = None
    explanations: List[InsurerExplanation]


# ============================================================================
# Common Notes Section (예시3: 공통사항)
# ============================================================================

class CommonNotesSection(BaseModel):
    """
    Common notes section (fact-only, NO comparisons)

    USAGE: 예시3 "공통사항" (모든 보험사 공통 특징)
    RULES:
    - Bullet list format
    - NO comparisons (e.g., "모든 보험사가 동일")
    - Factual observations only
    """
    kind: Literal["common_notes"] = "common_notes"
    title: str = "공통사항"
    bullets: List[str]


# ============================================================================
# Notices Section (예시3: 유의사항)
# ============================================================================

class NoticesSection(BaseModel):
    """
    Notices section (fact-based caveats)

    USAGE: 예시3 "유의사항" (근거 기반 seeing)
    RULES:
    - Bullet list format
    - Based on evidence (NOT inference)
    - NO recommendations (e.g., "선택 시 고려")
    """
    kind: Literal["notices"] = "notices"
    title: str = "유의사항"
    bullets: List[str]


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


class EvidenceSection(BaseModel):
    """
    Evidence section (collapsible)

    PRESENTATION:
    - Collapsed by default
    - Expand on click
    - Grouped by insurer
    """
    kind: Literal["evidence"] = "evidence"
    title: str = "근거 자료"
    items: List[EvidenceItem]


# ============================================================================
# Disabled Notice Section (예시1: 보험료 비교 불가)
# ============================================================================

class DisabledNoticeSection(BaseModel):
    """
    Disabled notice section

    USAGE: 예시1 "보험료 비교" 요청 시 안내
    RULES:
    - NO estimation (추정 금지)
    - NO calculation (계산 금지)
    - Clear reason for disabled state
    """
    kind: Literal["disabled_notice"] = "disabled_notice"
    title: str
    message: str
    reason: str  # e.g., "보험료 데이터 소스 미연동"
    suggested_action: Optional[str] = None


# ============================================================================
# Section Union Type
# ============================================================================

Section = (
    TableSection |
    ExplanationSection |
    CommonNotesSection |
    NoticesSection |
    EvidenceSection |
    DisabledNoticeSection
)


# ============================================================================
# Assistant Message View Model (Top-level)
# ============================================================================

MessageKind = Literal[
    "EX2_DETAIL",           # 예시2: 상품/담보 설명
    "EX3_INTEGRATED",       # 예시3: 통합 비교
    "EX4_ELIGIBILITY",      # 예시4: 보장 가능 여부
    "EX1_PREMIUM_DISABLED"  # 예시1: 보험료 비교 불가
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

    lineage: Optional[AmountAuditDTO] = None  # Audit metadata (collapsible)

    class Config:
        frozen = True

    @field_validator('summary_bullets')
    @classmethod
    def validate_no_forbidden_words_in_summary(cls, v: List[str]) -> List[str]:
        """
        Enforce forbidden word policy in summary bullets

        ALLOWED: "비교합니다", "확인합니다" (factual statements)
        FORBIDDEN: "A가 B보다", "더 높다", "유리하다" (evaluative comparisons)
        """
        # Strict forbidden patterns (evaluative/comparative language)
        FORBIDDEN_PATTERNS = [
            r'(?<!을\s)(?<!를\s)더(?!\s*확인)',  # "더" (but allow "더 확인")
            r'보다(?!\s*자세)',  # "보다" (but allow "보다 자세")
            '반면', '그러나', '하지만',
            '유리', '불리', '높다', '낮다', '많다', '적다',
            r'차이(?!를\\s*확인)',  # "차이" (but allow "차이를 확인")
            '우수', '열등', '좋', '나쁜',
            '가장', '최고', '최저', '평균', '합계',
            '추천', '제안', '권장', '선택', '판단'
        ]

        import re
        for bullet in v:
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, bullet):
                    raise ValueError(
                        f"FORBIDDEN word in summary: pattern '{pattern}' matches in '{bullet}'"
                    )

        return v


# ============================================================================
# Chat Request/Response DTOs
# ============================================================================

class ChatRequest(BaseModel):
    """
    Chat request from frontend

    FLOW:
    1. User input (natural language or FAQ template)
    2. Intent router → determine kind (EX2/EX3/EX4/EX1_DISABLED)
    3. Slot validator → check required fields
    4. Compiler → generate CompareRequest
    5. Handler → execute query + build VM
    """
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    message: str  # User input text
    faq_template_id: Optional[str] = None  # If clicked from FAQ

    # Optional slots (filled by user or FAQ template)
    coverage_names: Optional[List[str]] = None
    insurers: Optional[List[str]] = None
    disease_name: Optional[str] = None

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
            example_kind="EX2_DETAIL"
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
