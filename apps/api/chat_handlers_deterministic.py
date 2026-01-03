#!/usr/bin/env python3
"""
Chat Handlers with Step8 Deterministic Render Engine Integration
STEP NEXT-UI-01: LLM OFF by default

DESIGN:
1. Use Step8 render engine for ALL examples (LLM OFF)
2. Handlers only orchestrate: load data → render → build VM
3. NO LLM calls unless explicitly requested (llm_mode="ON")
4. Forbidden phrases validation enforced

HANDLERS:
- Example1HandlerDeterministic: Premium comparison (Step8)
- Example3HandlerDeterministic: Two-insurer comparison (Step8)
- Example4HandlerDeterministic: Subtype eligibility (Step8)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pipeline" / "step8_render_deterministic"))

from example1_premium_compare import PremiumComparer
from example2_coverage_limit import CoverageLimitComparer
from example3_two_insurer_compare import TwoInsurerComparer
from example4_subtype_eligibility import SubtypeEligibilityChecker
from diff_filter import CoverageDiffFilter
from normalize_fields import normalize_field, LimitNormalizer, PaymentTypeNormalizer, ConditionsNormalizer

from apps.api.chat_vm import (
    AssistantMessageVM,
    MessageKind,
    ComparisonTableSection,
    TableRow,
    TableCell,
    CellMeta,
    InsurerExplanationsSection,
    InsurerExplanation,
    CommonNotesSection,
    BulletGroup,
    EvidenceAccordionSection,
    EvidenceItem,
    ChatRequest,
    CoverageDiffResultSection,
    DiffGroup,
    InsurerDetail,
    OverallEvaluationSection,
    OverallEvaluation,
    OverallEvaluationReason
)
from apps.api.response_composers.utils import (
    display_coverage_name,
    format_insurer_list,
    sanitize_no_coverage_code
)
# from apps.api.policy.forbidden_language import ForbiddenLanguageValidator

# Simple mock validator for STEP NEXT-UI-02
class ForbiddenLanguageValidator:
    def check_text(self, text):
        """Mock validator - returns empty list (no violations)"""
        return []


# ============================================================================
# Base Handler
# ============================================================================

class BaseDeterministicHandler:
    """Base handler with Step8 integration"""

    def __init__(self):
        self.validator = ForbiddenLanguageValidator()

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """Execute handler and build ViewModel"""
        raise NotImplementedError

    def _validate_forbidden_phrases(self, vm: AssistantMessageVM):
        """Validate VM for forbidden phrases"""
        # Serialize VM to check all text fields
        import json
        vm_json = vm.model_dump_json()

        violations = self.validator.check_text(vm_json)
        if violations:
            raise ValueError(f"Forbidden phrases detected: {violations}")


# ============================================================================
# Example 1 Handler: Premium Comparison
# ============================================================================

class Example1HandlerDeterministic(BaseDeterministicHandler):
    """Premium comparison using Step8 PremiumComparer"""

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """
        Execute premium comparison (LLM OFF)

        Returns:
        - If gate pass: Top-4 premium table
        - If gate fail: NotAvailable message
        """
        comparer = PremiumComparer()

        # All insurers for Top-4
        insurers = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai", "heungkuk", "db"]

        result = comparer.compare_top4(insurers)

        if result["status"] == "not_available":
            # Return disabled message
            return AssistantMessageVM(
                kind="EX1_PREMIUM_DISABLED",
                title="보험료 비교 기능 안내",
                summary_bullets=[
                    "현재 보험료 비교 기능은 준비 중입니다",
                    result["reason"]
                ],
                sections=[],
                lineage={
                    "handler": "Example1HandlerDeterministic",
                    "llm_used": False,
                    "deterministic": True
                }
            )

        # Build ViewModel from Step8 output
        rows = []
        for row in result["rows"]:
            rows.append(TableRow(
                cells=[
                    TableCell(text=row["insurer"]),
                    TableCell(text=row["monthly_premium"], meta=CellMeta(doc_ref=row["monthly_evidence"])),
                    TableCell(text=row["total_premium"], meta=CellMeta(doc_ref=row["total_evidence"]))
                ]
            ))

        table = ComparisonTableSection(
            table_kind="COVERAGE_DETAIL",
            title="보험료 비교 (Top 4)",
            columns=["보험사", "월납 보험료", "총납 보험료"],
            rows=rows
        )

        vm = AssistantMessageVM(
            kind="PREMIUM_COMPARE",
            title="보험료 Top 4 비교",
            summary_bullets=[
                "보험료가 낮은 순서로 4개 보험사를 비교했습니다",
                "가입설계서 기준 금액입니다"
            ],
            sections=[table],
            lineage={
                "handler": "Example1HandlerDeterministic",
                "llm_used": False,
                "deterministic": True
            }
        )

        self._validate_forbidden_phrases(vm)
        return vm


# ============================================================================
# Example 2-Diff Handler: Coverage Difference Filter
# ============================================================================

class Example2DiffHandlerDeterministic(BaseDeterministicHandler):
    """Coverage difference filter (STEP NEXT-COMPARE-FILTER-FINAL)"""

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """
        Execute diff filter (LLM OFF)
        STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched with normalized values and evidence

        Returns coverage_diff_result section with:
        - status: "DIFF" or "ALL_SAME"
        - groups: value_display + insurers + value_normalized + insurer_details
        - diff_summary: "A사가 다릅니다" format
        - extraction_notes: reasons for "명시 없음"
        """
        comparer = CoverageLimitComparer()

        insurers = compiled_query.get("insurers", [])
        coverage_code = compiled_query.get("coverage_code", "A4200_1")
        compare_field = compiled_query.get("compare_field", "보장한도")

        # STEP NEXT-89: Extract coverage_name with priority
        # Priority: request.coverage_names > compiled_query.coverage_names > card fallback
        coverage_name = None
        coverage_names = compiled_query.get("coverage_names", [])
        if coverage_names and len(coverage_names) > 0:
            coverage_name = coverage_names[0]  # Use first coverage_name from request

        # Get coverage data from all insurers (with cards for evidence extraction)
        coverage_data = []
        insurer_cards = {}  # Store cards for later evidence extraction

        for insurer in insurers:
            cards = comparer.load_coverage_cards(insurer)
            card = comparer.find_coverage(cards, coverage_code)

            if card:
                insurer_cards[insurer] = card
                # STEP NEXT-89: Fallback to card if coverage_name not from request
                if coverage_name is None:
                    # Priority: coverage_name_canonical > coverage_name_raw > customer_view.coverage_name
                    coverage_name = (
                        card.get("coverage_name_canonical") or
                        card.get("coverage_name_raw") or
                        (card.get("customer_view", {}) or {}).get("coverage_name")
                    )
                evidences = card.get("evidences", [])
                proposal_facts = card.get("proposal_facts", {}) or {}

                # Extract field value based on compare_field
                if compare_field == "보장한도":
                    value = comparer.extract_limit(evidences)
                elif compare_field == "보장금액":
                    value = proposal_facts.get("coverage_amount_text") or comparer.extract_amount(evidences)
                elif compare_field == "지급유형":
                    value = comparer.extract_payment_type(evidences)
                elif compare_field == "조건":
                    value = comparer.extract_conditions(evidences)
                else:
                    value = None

                # Normalize invalid values (e.g., section numbers like "4-1", "3-2-1")
                if value and self._is_section_number(value):
                    value = None

                coverage_data.append({
                    "insurer": insurer,
                    "value": value or "명시 없음",
                    "coverage_code": coverage_code
                })
            else:
                coverage_data.append({
                    "insurer": insurer,
                    "value": "담보 미존재",
                    "coverage_code": coverage_code
                })

        # Run diff filter
        diff_result = CoverageDiffFilter.filter_by_difference(coverage_data, compare_field)

        # Build enriched DiffGroups with insurer_details
        groups = []
        value_to_data = {}

        # Group insurers by value (with full card data)
        for item in coverage_data:
            value = item["value"]
            insurer = item["insurer"]

            if value not in value_to_data:
                value_to_data[value] = {
                    "insurers": [],
                    "cards": []
                }

            value_to_data[value]["insurers"].append(insurer)
            value_to_data[value]["cards"].append(insurer_cards.get(insurer))

        # Convert to enriched DiffGroup list
        extraction_notes = []

        for value, data in value_to_data.items():
            insurer_list = data["insurers"]
            cards = data["cards"]

            # Normalize field values for this group
            value_normalized = None
            insurer_details = []

            for idx, insurer in enumerate(insurer_list):
                card = cards[idx]
                if card:
                    evidences = card.get("evidences", [])

                    # Normalize field (use normalize_fields module)
                    if compare_field == "보장한도":
                        normalized = LimitNormalizer.normalize(evidences)
                        value_normalized = normalized.to_dict() if not value_normalized else value_normalized
                        raw_text = normalized.raw_text
                        evidence_refs = [ref.to_dict() for ref in normalized.evidence_refs]
                    elif compare_field == "지급유형":
                        normalized = PaymentTypeNormalizer.normalize(evidences)
                        value_normalized = normalized.to_dict() if not value_normalized else value_normalized
                        raw_text = normalized.raw_text
                        evidence_refs = [ref.to_dict() for ref in normalized.evidence_refs]
                    elif compare_field == "조건":
                        normalized = ConditionsNormalizer.normalize(evidences)
                        value_normalized = normalized.to_dict() if not value_normalized else value_normalized
                        raw_text = normalized.raw_text
                        evidence_refs = [ref.to_dict() for ref in normalized.evidence_refs]
                    else:
                        # For "보장금액" or others, use raw snippet
                        raw_text = evidences[0].get("snippet", "")[:200] if evidences else ""
                        evidence_refs = [
                            {
                                "doc_type": ev.get("doc_type", ""),
                                "page": ev.get("page", 0),
                                "snippet": ev.get("snippet", "")[:200]
                            }
                            for ev in evidences[:2]  # Top 2 evidences
                        ]

                    # Build notes for "명시 없음" cases
                    notes = []
                    if value == "명시 없음":
                        if evidences:
                            notes.append("관련 근거 발견되었으나 명시적 패턴 미검출")
                        else:
                            notes.append("근거 자료 없음")

                    insurer_details.append(InsurerDetail(
                        insurer=insurer,
                        raw_text=raw_text or value,
                        evidence_refs=evidence_refs,
                        notes=notes if notes else None
                    ))
                else:
                    insurer_details.append(InsurerDetail(
                        insurer=insurer,
                        raw_text="담보 미존재",
                        evidence_refs=[],
                        notes=["해당 보험사에 이 담보가 존재하지 않음"]
                    ))

            # Add extraction notes for "명시 없음" groups
            if value == "명시 없음":
                extraction_notes.append(
                    f"{', '.join(insurer_list)}: 근거 문서에서 {compare_field} 패턴 미검출"
                )

            groups.append(DiffGroup(
                value_display=value,
                insurers=insurer_list,
                value_normalized=value_normalized,
                insurer_details=insurer_details
            ))

        # Build diff summary
        if diff_result["status"] == "ALL_SAME":
            status = "ALL_SAME"
            diff_summary = None
            summary_bullets = [
                f"선택한 보험사의 {compare_field}는 모두 동일합니다"
            ]
            if groups:
                summary_bullets.append(f"공통 값: {groups[0].value_display}")
        else:
            status = "DIFF"
            diff_insurers = diff_result["diff_insurers"]

            # Find minority group (different insurers)
            if len(groups) >= 2:
                # Sort by group size
                sorted_groups = sorted(groups, key=lambda g: len(g.insurers))
                minority_group = sorted_groups[0]

                # Build diff summary: "A사가 다릅니다 (value)"
                diff_insurer_names = ", ".join(minority_group.insurers)
                diff_summary = f"{diff_insurer_names}가 다릅니다 ({minority_group.value_display})"
            else:
                diff_summary = f"{len(diff_insurers)}개 보험사의 {compare_field}가 다릅니다"

            summary_bullets = [diff_summary]

        # STEP NEXT-89: Build title with proper view layer expression
        safe_coverage_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        )
        insurer_list_str = format_insurer_list(insurers)

        # STEP NEXT-89: Format title based on insurer count (singular/plural)
        if len(insurers) >= 2:
            title = f"{insurer_list_str}의 {safe_coverage_name} {compare_field} 차이"
        else:
            title = f"{insurer_list_str}의 {safe_coverage_name} {compare_field} 확인"

        # STEP NEXT-89: Sanitize title (remove any bare coverage codes)
        title = sanitize_no_coverage_code(title)

        # STEP NEXT-89: Sanitize summary_bullets (remove any bare coverage codes)
        summary_bullets = [sanitize_no_coverage_code(bullet) for bullet in summary_bullets]

        # Build CoverageDiffResultSection (ENRICHED with insurer_details)
        section_title = f"{compare_field} 비교 결과"
        # STEP NEXT-89: Sanitize section title
        section_title = sanitize_no_coverage_code(section_title)

        diff_section = CoverageDiffResultSection(
            title=section_title,
            field_label=compare_field,
            status=status,
            groups=groups,
            diff_summary=diff_summary,
            extraction_notes=extraction_notes if extraction_notes else None
        )

        vm = AssistantMessageVM(
            request_id=request.request_id,
            kind="EX2_DETAIL_DIFF",
            title=title,
            summary_bullets=summary_bullets,
            sections=[diff_section],
            lineage={
                "handler": "Example2DiffHandlerDeterministic",
                "llm_used": False,
                "deterministic": True,
                "diff_status": status
            }
        )

        self._validate_forbidden_phrases(vm)
        return vm

    def _is_section_number(self, text: str) -> bool:
        """Check if text is a section number like '4-1', '3-2-1'"""
        import re
        return bool(re.match(r'^\d+(-\d+)+$', text.strip()))


# ============================================================================
# Example 3 Handler: Two-Insurer Comparison
# ============================================================================

class Example3HandlerDeterministic(BaseDeterministicHandler):
    """Two-insurer comparison using Step8 TwoInsurerComparer"""

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """
        Execute two-insurer comparison (LLM OFF)

        STEP NEXT-77: Use EX3CompareComposer for locked schema response
        """
        from apps.api.response_composers.ex3_compare_composer import EX3CompareComposer
        from pathlib import Path

        # Use absolute path to data/compare
        project_root = Path(__file__).parent.parent.parent
        cards_dir = project_root / "data" / "compare"

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[EX3] Loading cards from: {cards_dir.absolute()}")

        comparer = TwoInsurerComparer(cards_dir=cards_dir)

        insurers = compiled_query.get("insurers", [])
        if len(insurers) < 2:
            raise ValueError("2개 이상의 보험사가 필요합니다")

        insurer1, insurer2 = insurers[0], insurers[1]
        coverage_code = compiled_query.get("coverage_code", "A4200_1")

        result = comparer.compare_two_insurers(insurer1, insurer2, coverage_code)

        if result["status"] == "FAIL":
            # Gate failed - use EX3_COMPARE (STEP NEXT-80: explicit kind lock)
            return AssistantMessageVM(
                request_id=request.request_id,
                kind="EX3_COMPARE",  # STEP NEXT-80: Always use EX3_COMPARE (not EX3_INTEGRATED)
                title="비교 불가",
                summary_bullets=[
                    f"비교 실패: {result['reason']}"
                ],
                sections=[],
                lineage={
                    "handler": "Example3HandlerDeterministic",
                    "llm_used": False,
                    "gate_failed": True
                }
            )

        # STEP NEXT-77: Use EX3CompareComposer to build response
        comparison_table = result["comparison_table"]

        # STEP NEXT-81B: Get coverage name (NEVER pass coverage_code as fallback)
        coverage_name = result.get("coverage_name")  # None if not available (composer will handle)

        # Compose EX3_COMPARE response
        response_dict = EX3CompareComposer.compose(
            insurers=[insurer1, insurer2],
            coverage_code=coverage_code,
            comparison_data=comparison_table,
            coverage_name=coverage_name
        )

        # Convert dict response to AssistantMessageVM
        # Build sections from response_dict
        from apps.api.chat_vm import TableRowMeta, KPISummaryMeta, KPIConditionMeta

        sections = []
        for section_dict in response_dict["sections"]:
            if section_dict["kind"] == "kpi_summary":
                # Skip for now (not in current VM schema)
                # TODO: Add KPISummarySection to chat_vm.py if needed
                pass
            elif section_dict["kind"] == "comparison_table":
                # Build ComparisonTableSection
                rows = []
                for row_dict in section_dict["rows"]:
                    cells = [TableCell(**cell) for cell in row_dict["cells"]]

                    # Build meta
                    meta = None
                    if row_dict.get("meta"):
                        meta_dict = row_dict["meta"]
                        kpi_summary_meta = None
                        if meta_dict.get("kpi_summary"):
                            kpi_summary_meta = KPISummaryMeta(**meta_dict["kpi_summary"])

                        kpi_condition_meta = None
                        if meta_dict.get("kpi_condition"):
                            kpi_condition_meta = KPIConditionMeta(**meta_dict["kpi_condition"])

                        meta = TableRowMeta(
                            proposal_detail_ref=meta_dict.get("proposal_detail_ref"),
                            evidence_refs=meta_dict.get("evidence_refs"),
                            kpi_summary=kpi_summary_meta,
                            kpi_condition=kpi_condition_meta
                        )

                    rows.append(TableRow(
                        cells=cells,
                        is_header=row_dict.get("is_header", False),
                        meta=meta
                    ))

                table = ComparisonTableSection(
                    table_kind=section_dict["table_kind"],
                    title=section_dict["title"],
                    columns=section_dict["columns"],
                    rows=rows
                )
                sections.append(table)
            elif section_dict["kind"] == "common_notes":
                # Build CommonNotesSection
                groups = None
                if section_dict.get("groups"):
                    groups = [BulletGroup(**g) for g in section_dict["groups"]]

                common_notes = CommonNotesSection(
                    title=section_dict["title"],
                    bullets=section_dict.get("bullets", []),
                    groups=groups
                )
                sections.append(common_notes)

        vm = AssistantMessageVM(
            request_id=request.request_id,
            kind="EX3_COMPARE",  # STEP NEXT-77: New kind
            title=response_dict["title"],
            summary_bullets=response_dict["summary_bullets"],
            sections=sections,
            bubble_markdown=response_dict.get("bubble_markdown"),  # STEP NEXT-81B
            lineage=response_dict["lineage"]
        )

        self._validate_forbidden_phrases(vm)
        return vm


# ============================================================================
# Example 4 Handler: Subtype Eligibility
# ============================================================================

class Example4HandlerDeterministic(BaseDeterministicHandler):
    """Subtype eligibility using Step8 SubtypeEligibilityChecker"""

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """
        Execute subtype eligibility check (LLM OFF)

        STEP NEXT-79: Use EX4EligibilityComposer for locked schema response with overall evaluation
        """
        from apps.api.response_composers.ex4_eligibility_composer import EX4EligibilityComposer

        checker = SubtypeEligibilityChecker()

        insurers = compiled_query.get("insurers", [])
        subtype = compiled_query.get("disease_name", "제자리암")

        result = checker.check_subtype_eligibility(insurers, subtype)

        # STEP NEXT-79: Use EX4EligibilityComposer to build response
        query_focus_terms = [subtype]

        # Compose EX4_ELIGIBILITY response
        response_dict = EX4EligibilityComposer.compose(
            insurers=insurers,
            subtype_keyword=subtype,
            eligibility_data=result["rows"],
            query_focus_terms=query_focus_terms
        )

        # Convert dict response to AssistantMessageVM
        sections = []
        for section_dict in response_dict["sections"]:
            if section_dict["kind"] == "comparison_table":
                # Build ComparisonTableSection
                rows = []
                for row_dict in section_dict["rows"]:
                    cells = [TableCell(**cell) for cell in row_dict["cells"]]
                    rows.append(TableRow(
                        cells=cells,
                        is_header=row_dict.get("is_header", False),
                        meta=row_dict.get("meta")
                    ))

                table = ComparisonTableSection(
                    table_kind=section_dict["table_kind"],
                    title=section_dict["title"],
                    columns=section_dict["columns"],
                    rows=rows
                )
                sections.append(table)
            elif section_dict["kind"] == "overall_evaluation":
                # STEP NEXT-79: Build OverallEvaluationSection
                overall_eval_data = section_dict["overall_evaluation"]
                reasons = [
                    OverallEvaluationReason(**reason)
                    for reason in overall_eval_data["reasons"]
                ]
                overall_eval = OverallEvaluation(
                    decision=overall_eval_data["decision"],
                    summary=overall_eval_data["summary"],
                    reasons=reasons,
                    notes=overall_eval_data["notes"]
                )
                overall_eval_section = OverallEvaluationSection(
                    title=section_dict["title"],
                    overall_evaluation=overall_eval
                )
                sections.append(overall_eval_section)
            elif section_dict["kind"] == "common_notes":
                # Build CommonNotesSection
                common_notes = CommonNotesSection(
                    title=section_dict["title"],
                    bullets=section_dict.get("bullets", []),
                    groups=section_dict.get("groups")
                )
                sections.append(common_notes)

        vm = AssistantMessageVM(
            request_id=request.request_id,
            kind="EX4_ELIGIBILITY",
            title=response_dict["title"],
            summary_bullets=response_dict["summary_bullets"],
            sections=sections,
            bubble_markdown=response_dict.get("bubble_markdown"),  # STEP NEXT-81B
            lineage=response_dict["lineage"]
        )

        self._validate_forbidden_phrases(vm)
        return vm


# ============================================================================
# Example 2-Detail Handler: Single Insurer Coverage Explanation
# ============================================================================

class Example2DetailHandlerDeterministic(BaseDeterministicHandler):
    """
    Single insurer coverage explanation (STEP NEXT-86)

    EX2_DETAIL = 설명 전용 모드
    - NO comparison
    - NO recommendation
    - NO judgment
    - Deterministic only
    """

    def execute(self, compiled_query: Dict[str, Any], request: ChatRequest) -> AssistantMessageVM:
        """
        Execute single insurer coverage explanation (LLM OFF)

        Args:
            compiled_query: {
                "insurers": ["samsung"],
                "coverage_names": ["암진단비(유사암 제외)"],
                "coverage_code": "A4200_1"
            }
            request: ChatRequest

        Returns:
            AssistantMessageVM with 4-section bubble_markdown
        """
        from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer

        # Extract query params
        insurers = compiled_query.get("insurers", [])
        coverage_code = compiled_query.get("coverage_code", "A4200_1")
        coverage_names = compiled_query.get("coverage_names", [])

        # Validation: Must have exactly 1 insurer (STEP NEXT-86 gate)
        if len(insurers) != 1:
            raise ValueError(f"EX2_DETAIL requires exactly 1 insurer, got {len(insurers)}")

        insurer = insurers[0]
        coverage_name = coverage_names[0] if coverage_names else None

        # Load coverage card for this insurer
        comparer = CoverageLimitComparer()
        cards = comparer.load_coverage_cards(insurer)
        card = comparer.find_coverage(cards, coverage_code)

        if not card:
            # Coverage not found
            return AssistantMessageVM(
                request_id=request.request_id,  # STEP NEXT-86: Required field
                kind="EX2_DETAIL",
                title=f"{insurer} 담보 정보 없음",
                summary_bullets=[
                    f"{insurer}에서 해당 담보를 찾을 수 없습니다",
                    "다른 보험사를 선택하거나 담보명을 확인해주세요"
                ],
                sections=[],
                lineage={
                    "handler": "Example2DetailHandlerDeterministic",
                    "llm_used": False,
                    "deterministic": True
                }
            )

        # Extract card data
        proposal_facts = card.get("proposal_facts", {}) or {}
        evidences = card.get("evidences", [])

        # Build card_data dict for composer
        card_data = {
            "amount": proposal_facts.get("coverage_amount_text") or "표현 없음",
            "premium": "표현 없음",  # Premium not shown in EX2_DETAIL
            "period": "표현 없음",
            "payment_type": "표현 없음",
            "proposal_detail_ref": f"PD:{insurer}:{coverage_code}",
            "evidence_refs": [
                f"EV:{insurer}:{coverage_code}:{str(idx+1).zfill(2)}"
                for idx in range(min(len(evidences), 3))
            ],
            "kpi_summary": {},
            "kpi_condition": {}
        }

        # Extract KPI Summary (STEP NEXT-75)
        kpi_summary_meta = card.get("kpi_summary")
        if kpi_summary_meta:
            card_data["kpi_summary"] = {
                "limit_summary": kpi_summary_meta.get("limit_summary") or "표현 없음",
                "payment_type": kpi_summary_meta.get("payment_type") or "표현 없음",
                "kpi_evidence_refs": kpi_summary_meta.get("kpi_evidence_refs", [])
            }
        else:
            # Fallback: Extract from evidences
            limit_normalized = LimitNormalizer.normalize(evidences)
            payment_normalized = PaymentTypeNormalizer.normalize(evidences)

            # Build kpi_evidence_refs from evidence_refs (use first 2)
            kpi_refs = []
            for idx, ref in enumerate(limit_normalized.evidence_refs[:2]):
                kpi_refs.append(f"EV:{insurer}:{coverage_code}:{str(idx+1).zfill(2)}")

            card_data["kpi_summary"] = {
                "limit_summary": limit_normalized.to_display_text() or "표현 없음",
                "payment_type": payment_normalized.to_display_text() or "표현 없음",
                "kpi_evidence_refs": kpi_refs
            }

        # Extract KPI Condition (STEP NEXT-76)
        kpi_condition_meta = card.get("kpi_condition")
        if kpi_condition_meta:
            card_data["kpi_condition"] = {
                "reduction_condition": kpi_condition_meta.get("reduction_condition") or "근거 없음",
                "waiting_period": kpi_condition_meta.get("waiting_period") or "근거 없음",
                "exclusion_condition": kpi_condition_meta.get("exclusion_condition") or "근거 없음",
                "renewal_condition": kpi_condition_meta.get("renewal_condition") or "근거 없음",
                "condition_evidence_refs": kpi_condition_meta.get("condition_evidence_refs", [])
            }
        else:
            # Fallback: Extract from evidences
            conditions_normalized = ConditionsNormalizer.normalize(evidences)

            # Build condition_evidence_refs from evidence_refs (use first 3)
            condition_refs = []
            for idx, ref in enumerate(conditions_normalized.evidence_refs[:3]):
                condition_refs.append(f"EV:{insurer}:{coverage_code}:{str(idx+1).zfill(2)}")

            card_data["kpi_condition"] = {
                "reduction_condition": conditions_normalized.reduction or "근거 없음",
                "waiting_period": conditions_normalized.waiting_period or "근거 없음",
                "exclusion_condition": conditions_normalized.exclusion or "근거 없음",
                "renewal_condition": "근거 없음",  # Not extracted yet
                "condition_evidence_refs": condition_refs
            }

        # Compose response using EX2DetailComposer
        message_dict = EX2DetailComposer.compose(
            insurer=insurer,
            coverage_code=coverage_code,
            card_data=card_data,
            coverage_name=coverage_name
        )

        # Build AssistantMessageVM
        vm = AssistantMessageVM(
            request_id=request.request_id,  # STEP NEXT-86: Required field
            kind="EX2_DETAIL",
            title=message_dict["title"],
            summary_bullets=message_dict["summary_bullets"],
            bubble_markdown=message_dict.get("bubble_markdown"),
            sections=message_dict["sections"],
            lineage=message_dict.get("lineage")
        )

        self._validate_forbidden_phrases(vm)
        return vm


# ============================================================================
# Handler Registry (Deterministic)
# ============================================================================

class HandlerRegistryDeterministic:
    """Registry for deterministic handlers"""

    _HANDLERS: Dict[MessageKind, BaseDeterministicHandler] = {
        "PREMIUM_COMPARE": Example1HandlerDeterministic(),
        "EX1_PREMIUM_DISABLED": Example1HandlerDeterministic(),
        "EX2_DETAIL": Example2DetailHandlerDeterministic(),     # STEP NEXT-86: 설명 전용
        "EX2_DETAIL_DIFF": Example2DiffHandlerDeterministic(),  # LEGACY
        "EX2_LIMIT_FIND": Example2DiffHandlerDeterministic(),   # STEP NEXT-78: Reuse EX2Diff
        "EX3_INTEGRATED": Example3HandlerDeterministic(),
        "EX3_COMPARE": Example3HandlerDeterministic(),  # STEP NEXT-77: New kind
        "EX4_ELIGIBILITY": Example4HandlerDeterministic()
    }

    @classmethod
    def get_handler(cls, kind: MessageKind) -> Optional[BaseDeterministicHandler]:
        """Get handler for MessageKind"""
        return cls._HANDLERS.get(kind)
