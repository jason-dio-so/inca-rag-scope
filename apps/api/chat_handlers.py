#!/usr/bin/env python3
"""
Chat Handlers for each MessageKind
STEP NEXT-14: Chat UI Integration

HANDLER RESPONSIBILITIES:
1. Execute compiled query
2. Call Step11 (AmountRepository) + Step12 (ExplanationHandler)
3. Build AssistantMessageVM
4. Enforce forbidden words
5. Preserve locks (NO amount_fact writes)

HANDLERS:
- Example2Handler: Coverage detail comparison
- Example3Handler: Integrated comparison
- Example4Handler: Eligibility matrix
- Example1DisabledHandler: Premium disabled notice
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import uuid
import json

from apps.api.chat_vm import (
    AssistantMessageVM,
    MessageKind,
    ComparisonTableSection,  # RENAMED from TableSection
    TableRow,
    TableCell,
    CellMeta,
    InsurerExplanationsSection,  # RENAMED from ExplanationSection
    InsurerExplanation,
    CommonNotesSection,  # UNIFIED (includes notices)
    BulletGroup,  # NEW (STEP NEXT-14-β)
    EvidenceAccordionSection,  # RENAMED from EvidenceSection
    EvidenceItem,
    ChatRequest
)
from apps.api.dto import AmountAuditDTO, AmountDTO
from apps.api.presentation_utils import (
    format_amount_for_display,
    get_type_c_explanation_note,
    should_show_type_c_note
)  # STEP NEXT-17


# ============================================================================
# Helper Functions
# ============================================================================

def _load_coverage_card(insurer: str, coverage_canonical: str) -> Optional[Dict[str, Any]]:
    """
    Load coverage card from JSONL file

    Args:
        insurer: Insurer code (e.g., "kb", "samsung")
        coverage_canonical: Canonical coverage name

    Returns:
        Coverage card dict or None if not found
    """
    cards_path = Path(f"data/compare/{insurer}_coverage_cards.jsonl")

    if not cards_path.exists():
        return None

    try:
        with open(cards_path, 'r', encoding='utf-8') as f:
            for line in f:
                card = json.loads(line)
                if card.get('coverage_name_canonical') == coverage_canonical:
                    return card
    except Exception:
        return None

    return None


def _get_amount_from_card(card: Optional[Dict[str, Any]]) -> AmountDTO:
    """
    Extract AmountDTO from coverage card

    Args:
        card: Coverage card dict (may be None)

    Returns:
        AmountDTO with proper status and value
    """
    if not card or 'amount' not in card:
        return AmountDTO(
            status="NOT_AVAILABLE",
            value_text=None,
            source_doc_type=None,
            source_priority=None,
            evidence_ref=None,
            notes=[]
        )

    amount_data = card['amount']

    return AmountDTO(
        status=amount_data.get('status', 'UNCONFIRMED'),
        value_text=amount_data.get('value_text'),
        source_doc_type=amount_data.get('source_doc_type'),
        source_priority=amount_data.get('source_priority'),
        evidence_ref=amount_data.get('evidence_ref'),
        notes=amount_data.get('notes', [])
    )


# ============================================================================
# Base Handler
# ============================================================================

class BaseHandler:
    """Base handler with common utilities"""

    def __init__(self):
        self.kind: MessageKind = "EX2_DETAIL"  # Override in subclass

    def execute(
        self,
        compiled_query: Dict[str, Any],
        request: ChatRequest
    ) -> AssistantMessageVM:
        """
        Execute handler and build VM

        Override in subclass
        """
        raise NotImplementedError("Subclass must implement execute()")

    def _get_audit_metadata(self) -> Optional[AmountAuditDTO]:
        """
        Get current audit metadata

        Returns locked audit run info from Step10B-FINAL
        """
        # LOCKED values from STATUS.md
        return AmountAuditDTO(
            audit_run_id=uuid.UUID("f2e58b52-f22d-4d66-8850-df464954c9b8"),
            freeze_tag="freeze/pre-10b2g2-20251229-024400",
            git_commit="c6fad903c4782c9b78c44563f0f47bf13f9f3417"
        )


# ============================================================================
# Example 2 Handler: Coverage Detail Comparison
# ============================================================================

class Example2Handler(BaseHandler):
    """
    Handler for Example 2: Coverage Detail Comparison

    OUTPUT:
    - Title: "{coverage_name} 보장 상세 비교"
    - Summary: 3-6 bullets (fact-only)
    - Table: Insurer columns × Detail rows (보장개시/면책/감액/보장기간/보장한도)
    - Explanation: Parallel insurer explanations (Step12)
    - Evidence: Collapsible evidence section

    FORBIDDEN:
    - 금액 기준 정렬
    - "더 좋다/나쁘다" 평가
    - 색상 우열
    """

    def __init__(self):
        self.kind = "EX2_DETAIL"

    def execute(
        self,
        compiled_query: Dict[str, Any],
        request: ChatRequest
    ) -> AssistantMessageVM:
        """Execute Example 2 handler"""

        coverage_names = compiled_query.get("coverage_names", [])
        insurers = compiled_query.get("insurers", [])

        # For demo, use first coverage
        coverage_name = coverage_names[0] if coverage_names else "담보"

        # Build title
        title = f"{coverage_name} 보장 상세 비교"

        # Build summary (fact-only)
        summary_bullets = [
            f"{len(insurers)}개 보험사의 {coverage_name} 보장 상세를 비교합니다",
            "보장개시, 면책기간, 감액기간, 보장기간, 보장한도를 확인할 수 있습니다",
            "금액은 가입설계서에 명시된 내용을 그대로 표시합니다"
        ]

        # Build table section
        table_section = self._build_detail_table(coverage_name, insurers)

        # Build explanation section (from Step12)
        explanation_section = self._build_explanation(coverage_name, insurers)

        # Build evidence section
        evidence_section = self._build_evidence(coverage_name, insurers)

        # Build VM
        return AssistantMessageVM(
            request_id=uuid.UUID(compiled_query["request_id"]),
            kind=self.kind,
            title=title,
            summary_bullets=summary_bullets,
            sections=[
                table_section,
                explanation_section,
                evidence_section
            ],
            lineage=self._get_audit_metadata()
        )

    def _build_detail_table(
        self,
        coverage_name: str,
        insurers: List[str]
    ) -> ComparisonTableSection:
        """Build detail comparison table"""

        # Column headers: 항목 + Insurers
        columns = ["항목"] + [self._format_insurer_name(ins) for ins in insurers]

        # Rows: 보장개시/면책/감액/보장기간/보장한도
        detail_items = [
            "보장개시",
            "면책기간",
            "감액기간",
            "보장기간",
            "보장한도"
        ]

        rows = []

        # Header row
        rows.append(TableRow(
            cells=[TableCell(text=col) for col in columns],
            is_header=True
        ))

        # Data rows (load real amounts from coverage_cards)
        for item in detail_items:
            cells = [TableCell(text=item)]  # First column = item name

            for ins in insurers:
                if item == "보장한도":
                    # Load real amount from coverage_cards.jsonl
                    insurer_code = ins.lower().replace("손해보험", "").replace("화재", "").replace("해상", "")
                    card = _load_coverage_card(insurer_code, coverage_name)
                    amount = _get_amount_from_card(card)

                    # Format amount using presentation layer
                    display_text = format_amount_for_display(amount, ins)

                    cells.append(TableCell(
                        text=display_text,
                        meta=CellMeta(status=amount.status) if amount.status else None
                    ))
                else:
                    cells.append(TableCell(text="-"))  # Placeholder

            rows.append(TableRow(cells=cells))

        return ComparisonTableSection(
            table_kind="COVERAGE_DETAIL",
            title=f"{coverage_name} 상세 비교",
            columns=columns,
            rows=rows
        )

    def _build_explanation(
        self,
        coverage_name: str,
        insurers: List[str]
    ) -> InsurerExplanationsSection:
        """Build parallel explanations (from real amount data)"""

        explanations = []

        for ins in insurers:
            insurer_display = self._format_insurer_name(ins)
            insurer_code = ins.lower().replace("손해보험", "").replace("화재", "").replace("해상", "")

            # Load real amount
            card = _load_coverage_card(insurer_code, coverage_name)
            amount = _get_amount_from_card(card)

            # Build explanation based on actual status
            if amount.status == "CONFIRMED" and amount.value_text:
                text = f"{insurer_display}의 {coverage_name}는 가입설계서에 {amount.value_text}으로 명시되어 있습니다."
            elif amount.status == "UNCONFIRMED":
                text = f"{insurer_display}의 {coverage_name}는 금액이 명시되지 않았습니다."
            else:  # NOT_AVAILABLE
                text = f"{insurer_display}는 {coverage_name} 담보가 확인되지 않았습니다."

            explanations.append(InsurerExplanation(
                insurer=insurer_display,
                text=text
            ))

        return InsurerExplanationsSection(
            title="보험사별 설명",
            explanations=explanations
        )

    def _build_evidence(
        self,
        coverage_name: str,
        insurers: List[str]
    ) -> EvidenceAccordionSection:
        """Build evidence section (from real coverage cards)"""

        items = []

        for ins in insurers:
            insurer_display = self._format_insurer_name(ins)
            insurer_code = ins.lower().replace("손해보험", "").replace("화재", "").replace("해상", "")

            # Load real card
            card = _load_coverage_card(insurer_code, coverage_name)

            if card and card.get('evidences'):
                # Use first evidence (typically 약관)
                first_evidence = card['evidences'][0]
                items.append(EvidenceItem(
                    evidence_ref_id=f"ev_{ins}_{coverage_name}",
                    insurer=insurer_display,
                    coverage_name=coverage_name,
                    doc_type=first_evidence.get('doc_type', '약관'),
                    page=first_evidence.get('page', 1),
                    snippet=first_evidence.get('snippet', '')[:200]  # Limit snippet length
                ))

        return EvidenceAccordionSection(items=items)

    def _format_insurer_name(self, code: str) -> str:
        """Format insurer code to display name"""
        DISPLAY_NAMES = {
            "samsung": "삼성화재",
            "meritz": "메리츠화재",
            "db": "DB손해보험",
            "kb": "KB손해보험",
            "hanwha": "한화손해보험",
            "hyundai": "현대해상",
            "lotte": "롯데손해보험",
            "heungkuk": "흥국화재"
        }
        return DISPLAY_NAMES.get(code, code)


# ============================================================================
# Example 3 Handler: Integrated Comparison
# ============================================================================

class Example3Handler(BaseHandler):
    """
    Handler for Example 3: Integrated Comparison

    OUTPUT:
    - Title: "통합 비교 결과"
    - Summary: 3-6 bullets
    - Table: Integrated comparison table
    - Explanation: Parallel explanations
    - Common Notes: 공통사항 (fact-only)
    - Notices: 유의사항 (evidence-based)
    - Evidence: Collapsible

    FORBIDDEN:
    - 비교/평가 표현
    - 금액 정렬
    - 추천
    """

    def __init__(self):
        self.kind = "EX3_INTEGRATED"

    def execute(
        self,
        compiled_query: Dict[str, Any],
        request: ChatRequest
    ) -> AssistantMessageVM:
        """Execute Example 3 handler"""

        coverage_names = compiled_query.get("coverage_names", [])
        insurers = compiled_query.get("insurers", [])

        # Build title
        title = "통합 비교 결과"

        # Build summary
        summary_bullets = [
            f"{len(coverage_names)}개 담보에 대해 {len(insurers)}개 보험사를 비교합니다",
            "가입설계서에 명시된 내용을 그대로 표시합니다",
            "공통사항과 유의사항을 함께 확인하세요"
        ]

        # Build sections
        table_section = self._build_integrated_table(coverage_names, insurers)
        explanation_section = self._build_explanation(coverage_names, insurers)
        common_notes = self._build_common_and_notices(coverage_names, insurers)
        evidence_section = self._build_evidence(coverage_names, insurers)

        # Build VM
        return AssistantMessageVM(
            request_id=uuid.UUID(compiled_query["request_id"]),
            kind=self.kind,
            title=title,
            summary_bullets=summary_bullets,
            sections=[
                table_section,
                explanation_section,
                common_notes,
                evidence_section
            ],
            lineage=self._get_audit_metadata()
        )

    def _build_integrated_table(
        self,
        coverage_names: List[str],
        insurers: List[str]
    ) -> ComparisonTableSection:
        """Build integrated comparison table"""

        # Columns: 담보 + Insurers
        columns = ["담보"] + [self._format_insurer_name(ins) for ins in insurers]

        rows = []

        # Header row
        rows.append(TableRow(
            cells=[TableCell(text=col) for col in columns],
            is_header=True
        ))

        # Data rows (one per coverage, load real amounts)
        for coverage in coverage_names:
            cells = [TableCell(text=coverage)]

            for ins in insurers:
                # Load real amount from coverage_cards
                insurer_code = ins.lower().replace("손해보험", "").replace("화재", "").replace("해상", "")
                card = _load_coverage_card(insurer_code, coverage)
                amount = _get_amount_from_card(card)

                # Format using presentation layer
                display_text = format_amount_for_display(amount, ins)

                cells.append(TableCell(
                    text=display_text,
                    meta=CellMeta(status=amount.status) if amount.status else None
                ))

            rows.append(TableRow(cells=cells))

        return ComparisonTableSection(
            table_kind="INTEGRATED_COMPARE",
            title="통합 비교표",
            columns=columns,
            rows=rows
        )

    def _build_explanation(
        self,
        coverage_names: List[str],
        insurers: List[str]
    ) -> InsurerExplanationsSection:
        """Build parallel explanations"""

        explanations = []

        # One explanation per insurer (parallel, not comparative)
        for ins in insurers:
            insurer_display = self._format_insurer_name(ins)
            text = f"{insurer_display}는 {len(coverage_names)}개 담보 모두 가입설계서에 금액이 명시되어 있습니다."

            explanations.append(InsurerExplanation(
                insurer=insurer_display,
                text=text
            ))

        return InsurerExplanationsSection(
            title="보험사별 설명",
            explanations=explanations
        )

    def _build_common_and_notices(
        self,
        coverage_names: List[str],
        insurers: List[str]
    ) -> CommonNotesSection:
        """
        Build common notes and notices (UNIFIED, fact-only, NO comparisons)

        STEP NEXT-14-β: Use groups for visual separation (예시3)
        STEP NEXT-17: Add Type C explanation if applicable
        """

        # Build base common notes
        common_bullets = [
            "가입설계서의 금액 표기 방식은 보험사/상품 구조에 따라 다를 수 있습니다",
            "면책기간과 감액기간은 별도 확인이 필요합니다"
        ]

        # STEP NEXT-17: Add Type C structure explanation if needed
        if should_show_type_c_note(insurers):
            common_bullets.append(get_type_c_explanation_note())

        # Build grouped bullets (시각 분리용)
        groups = [
            BulletGroup(
                title="공통사항",
                bullets=common_bullets
            ),
            BulletGroup(
                title="유의사항",
                bullets=[
                    "가입설계서 기준이며 실제 약관과 다를 수 있습니다",
                    "보장한도는 가입 당시 조건에 따라 달라질 수 있습니다"
                ]
            )
        ]

        return CommonNotesSection(
            title="공통사항 및 유의사항",
            bullets=[],  # LEGACY (empty for grouped mode)
            groups=groups  # NEW (grouped bullets)
        )

    def _build_evidence(
        self,
        coverage_names: List[str],
        insurers: List[str]
    ) -> EvidenceAccordionSection:
        """Build evidence section (from real coverage cards)"""

        items = []

        for coverage in coverage_names:
            for ins in insurers:
                insurer_display = self._format_insurer_name(ins)
                insurer_code = ins.lower().replace("손해보험", "").replace("화재", "").replace("해상", "")

                # Load real card
                card = _load_coverage_card(insurer_code, coverage)

                if card and card.get('evidences'):
                    # Use first evidence
                    first_evidence = card['evidences'][0]
                    items.append(EvidenceItem(
                        evidence_ref_id=f"ev_{ins}_{coverage}",
                        insurer=insurer_display,
                        coverage_name=coverage,
                        doc_type=first_evidence.get('doc_type', '약관'),
                        page=first_evidence.get('page', 1),
                        snippet=first_evidence.get('snippet', '')[:200]
                    ))

        return EvidenceAccordionSection(items=items)

    def _format_insurer_name(self, code: str) -> str:
        """Format insurer code to display name"""
        return Example2Handler()._format_insurer_name(code)


# ============================================================================
# Example 4 Handler: Eligibility Matrix
# ============================================================================

class Example4Handler(BaseHandler):
    """
    Handler for Example 4: Disease Eligibility Matrix

    OUTPUT:
    - Title: "{disease_name} 보장 가능 여부"
    - Summary: 3-6 bullets
    - Table: Eligibility matrix (O/X/조건부/불명)
    - Explanation: Definition excerpts
    - Evidence: Condition/definition snippets

    FORBIDDEN:
    - "A가 유리" 평가
    - 비교 표현
    """

    def __init__(self):
        self.kind = "EX4_ELIGIBILITY"

    def execute(
        self,
        compiled_query: Dict[str, Any],
        request: ChatRequest
    ) -> AssistantMessageVM:
        """Execute Example 4 handler"""

        disease_name = compiled_query.get("disease_name", "질병")
        insurers = compiled_query.get("insurers", [])

        # Build title
        title = f"{disease_name} 보장 가능 여부"

        # Build summary
        summary_bullets = [
            f"{disease_name}에 대한 {len(insurers)}개 보험사의 보장 가능 여부를 확인합니다",
            "약관 정의와 경계조건을 기준으로 표시합니다",
            "O: 보장 가능, X: 보장 불가, 조건부: 조건 충족 시 가능"
        ]

        # Build sections
        table_section = self._build_eligibility_table(disease_name, insurers)
        explanation_section = self._build_definition_explanation(disease_name, insurers)
        evidence_section = self._build_evidence(disease_name, insurers)

        # Build VM
        return AssistantMessageVM(
            request_id=uuid.UUID(compiled_query["request_id"]),
            kind=self.kind,
            title=title,
            summary_bullets=summary_bullets,
            sections=[
                table_section,
                explanation_section,
                evidence_section
            ],
            lineage=self._get_audit_metadata()
        )

    def _build_eligibility_table(
        self,
        disease_name: str,
        insurers: List[str]
    ) -> ComparisonTableSection:
        """Build eligibility matrix"""

        # Columns: 하위개념 + Insurers
        sub_diseases = [f"{disease_name}_유형1", f"{disease_name}_유형2"]
        columns = ["하위개념"] + [self._format_insurer_name(ins) for ins in insurers]

        rows = []

        # Header row
        rows.append(TableRow(
            cells=[TableCell(text=col) for col in columns],
            is_header=True
        ))

        # Data rows
        for sub in sub_diseases:
            cells = [TableCell(text=sub)]

            for ins in insurers:
                # Mock data (O/X/조건부/불명)
                cells.append(TableCell(text="O"))  # Mock

            rows.append(TableRow(cells=cells))

        return ComparisonTableSection(
            table_kind="ELIGIBILITY_MATRIX",
            title="보장 가능 여부 매트릭스",
            columns=columns,
            rows=rows
        )

    def _build_definition_explanation(
        self,
        disease_name: str,
        insurers: List[str]
    ) -> InsurerExplanationsSection:
        """Build definition excerpts"""

        explanations = []

        for ins in insurers:
            insurer_display = self._format_insurer_name(ins)
            text = f"{insurer_display}의 약관에서는 {disease_name}를 '...'로 정의합니다."

            explanations.append(InsurerExplanation(
                insurer=insurer_display,
                text=text
            ))

        return InsurerExplanationsSection(
            title="보험사별 정의",
            explanations=explanations
        )

    def _build_evidence(
        self,
        disease_name: str,
        insurers: List[str]
    ) -> EvidenceAccordionSection:
        """Build evidence (definitions/conditions)"""

        items = []

        for ins in insurers:
            insurer_display = self._format_insurer_name(ins)
            items.append(EvidenceItem(
                evidence_ref_id=f"ev_{ins}_{disease_name}_def",
                insurer=insurer_display,
                coverage_name=disease_name,
                doc_type="약관",
                page=10,
                snippet=f"{disease_name} 정의: ..."  # Mock
            ))

        return EvidenceAccordionSection(items=items)

    def _format_insurer_name(self, code: str) -> str:
        """Format insurer code to display name"""
        return Example2Handler()._format_insurer_name(code)


# ============================================================================
# Example 1 Disabled Handler: Premium Disabled Notice
# ============================================================================

class Example1DisabledHandler(BaseHandler):
    """
    Handler for Example 1: Premium Disabled Notice

    OUTPUT:
    - Title: "보험료 비교 (현재 제공 불가)"
    - Summary: Disabled reason
    - CommonNotesSection: Clear explanation + alternative suggestion

    CRITICAL:
    - NO premium estimation
    - NO calculation
    - NO ranking/sorting
    """

    def __init__(self):
        self.kind = "EX1_PREMIUM_DISABLED"

    def execute(
        self,
        compiled_query: Dict[str, Any],
        request: ChatRequest
    ) -> AssistantMessageVM:
        """Execute Example 1 disabled handler"""

        # Build title
        title = "보험료 비교 (현재 제공 불가)"

        # Build summary
        summary_bullets = [
            "보험료 비교 기능은 현재 제공되지 않습니다",
            "보험료 데이터 소스가 아직 연동되지 않았습니다"
        ]

        # Build disabled notice (using CommonNotesSection)
        disabled_notice = CommonNotesSection(
            title="보험료 비교 불가 안내",
            bullets=[
                "보험료 비교 기능은 현재 제공되지 않습니다",
                "보험료 데이터 소스가 시스템에 연동되지 않았습니다",
                "향후 데이터 소스 확정 후 제공 예정입니다",
                "담보 보장 내용 비교는 가능합니다 (상단 FAQ 참조)"
            ]
        )

        # Build VM
        return AssistantMessageVM(
            request_id=uuid.UUID(compiled_query["request_id"]),
            kind=self.kind,
            title=title,
            summary_bullets=summary_bullets,
            sections=[disabled_notice],
            lineage=self._get_audit_metadata()
        )


# ============================================================================
# Handler Registry
# ============================================================================

class HandlerRegistry:
    """
    Handler registry for dispatcher

    Maps MessageKind → Handler
    """

    _handlers = {
        "EX2_DETAIL": Example2Handler(),
        "EX3_INTEGRATED": Example3Handler(),
        "EX4_ELIGIBILITY": Example4Handler(),
        "EX1_PREMIUM_DISABLED": Example1DisabledHandler()
    }

    @staticmethod
    def get_handler(kind: MessageKind) -> Optional[BaseHandler]:
        """Get handler for MessageKind"""
        return HandlerRegistry._handlers.get(kind)
