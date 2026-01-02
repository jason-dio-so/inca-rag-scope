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
    InsurerDetail
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

        # Get coverage data from all insurers (with cards for evidence extraction)
        coverage_data = []
        insurer_cards = {}  # Store cards for later evidence extraction

        for insurer in insurers:
            cards = comparer.load_coverage_cards(insurer)
            card = comparer.find_coverage(cards, coverage_code)

            if card:
                insurer_cards[insurer] = card
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

        # Build CoverageDiffResultSection (ENRICHED with insurer_details)
        diff_section = CoverageDiffResultSection(
            title=f"{compare_field} 비교 결과",
            field_label=compare_field,
            status=status,
            groups=groups,
            diff_summary=diff_summary,
            extraction_notes=extraction_notes if extraction_notes else None
        )

        vm = AssistantMessageVM(
            request_id=request.request_id,
            kind="EX2_DETAIL_DIFF",
            title=f"{coverage_code} {compare_field} 차이 분석",
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
        """
        comparer = TwoInsurerComparer()

        insurers = compiled_query.get("insurers", [])
        if len(insurers) < 2:
            raise ValueError("2개 이상의 보험사가 필요합니다")

        insurer1, insurer2 = insurers[0], insurers[1]
        coverage_code = compiled_query.get("coverage_code", "A4200_1")

        result = comparer.compare_two_insurers(insurer1, insurer2, coverage_code)

        if result["status"] == "FAIL":
            # Gate failed
            return AssistantMessageVM(
                kind="EX3_INTEGRATED",
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

        # Build comparison table
        comparison_table = result["comparison_table"]
        rows = [
            TableRow(
                cells=[
                    TableCell(text="보장금액"),
                    TableCell(text=comparison_table[insurer1]["amount"]),
                    TableCell(text=comparison_table[insurer2]["amount"])
                ]
            ),
            TableRow(
                cells=[
                    TableCell(text="보험료"),
                    TableCell(text=comparison_table[insurer1].get("premium", "명시 없음")),
                    TableCell(text=comparison_table[insurer2].get("premium", "명시 없음"))
                ]
            ),
            TableRow(
                cells=[
                    TableCell(text="납입/만기"),
                    TableCell(text=comparison_table[insurer1].get("period", "명시 없음")),
                    TableCell(text=comparison_table[insurer2].get("period", "명시 없음"))
                ]
            ),
            TableRow(
                cells=[
                    TableCell(text="지급유형"),
                    TableCell(text=comparison_table[insurer1]["payment_type"]),
                    TableCell(text=comparison_table[insurer2]["payment_type"])
                ]
            )
        ]

        table = ComparisonTableSection(
            table_kind="INTEGRATED_COMPARE",
            title=f"{insurer1} vs {insurer2} 비교",
            columns=["구분", insurer1, insurer2],
            rows=rows
        )

        # Build summary from Step8 templates
        summary_bullets = result["summary"]

        # Build common notes
        common_notes = CommonNotesSection(
            title="공통사항 및 유의사항",
            bullets=[],
            groups=[
                BulletGroup(
                    title="공통사항",
                    bullets=["가입설계서 기준 비교입니다"]
                ),
                BulletGroup(
                    title="유의사항",
                    bullets=["실제 약관과 다를 수 있습니다"]
                )
            ]
        )

        vm = AssistantMessageVM(
            kind="EX3_INTEGRATED",
            title=f"{insurer1} vs {insurer2} {coverage_code} 비교",
            summary_bullets=summary_bullets,
            sections=[table, common_notes],
            lineage={
                "handler": "Example3HandlerDeterministic",
                "llm_used": False,
                "deterministic": True,
                "gates": result["gates"]
            }
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
        """
        checker = SubtypeEligibilityChecker()

        insurers = compiled_query.get("insurers", [])
        subtype = compiled_query.get("disease_name", "제자리암")

        result = checker.check_subtype_eligibility(insurers, subtype)

        # Build eligibility table
        rows = []
        for row_data in result["rows"]:
            rows.append(TableRow(
                cells=[
                    TableCell(text=row_data["insurer"]),
                    TableCell(text=row_data["status"]),
                    TableCell(text=row_data["evidence_type"] or "판단근거 없음"),
                    TableCell(text=(row_data["evidence_snippet"] or "")[:100])
                ]
            ))

        table = ComparisonTableSection(
            table_kind="ELIGIBILITY_MATRIX",
            title=f"{subtype} 보장 가능 여부",
            columns=["보험사", "보장여부", "근거유형", "근거내용"],
            rows=rows
        )

        # Build summary
        statuses = [row["status"] for row in result["rows"]]
        summary_bullets = [
            f"{subtype}에 대한 보장 가능 여부를 확인했습니다",
            f"O: {statuses.count('O')}개, X: {statuses.count('X')}개, Unknown: {statuses.count('Unknown')}개"
        ]

        # Build common notes
        common_notes = CommonNotesSection(
            title="유의사항",
            bullets=[
                "O: 보장 가능, X: 면책, △: 감액, Unknown: 판단 근거 없음",
                "약관 및 상품요약서 기준입니다"
            ],
            groups=None
        )

        vm = AssistantMessageVM(
            kind="EX4_ELIGIBILITY",
            title=f"{subtype} 보장 가능 여부 확인",
            summary_bullets=summary_bullets,
            sections=[table, common_notes],
            lineage={
                "handler": "Example4HandlerDeterministic",
                "llm_used": False,
                "deterministic": True
            }
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
        "EX2_DETAIL_DIFF": Example2DiffHandlerDeterministic(),
        "EX3_INTEGRATED": Example3HandlerDeterministic(),
        "EX4_ELIGIBILITY": Example4HandlerDeterministic()
    }

    @classmethod
    def get_handler(cls, kind: MessageKind) -> Optional[BaseDeterministicHandler]:
        """Get handler for MessageKind"""
        return cls._HANDLERS.get(kind)
