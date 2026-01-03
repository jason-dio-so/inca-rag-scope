#!/usr/bin/env python3
"""
EX4_ELIGIBILITY Response Composer

STEP NEXT-79: Lock EX4_ELIGIBILITY response schema + overall evaluation

DESIGN:
1. Input: Eligibility matrix (O/X/△ data), query focus terms
2. Output: EX4_ELIGIBILITY message dict with MANDATORY overall_evaluation
3. Deterministic decision rules (NO LLM)
4. Overall evaluation is ALWAYS present (not optional)

CONSTITUTIONAL RULES:
- ❌ NO LLM usage
- ❌ NO scoring/weighting/inference
- ❌ NO emotional phrases ("좋아 보임", "합리적")
- ✅ Deterministic decision rules ONLY
- ✅ overall_evaluation section ALWAYS present
- ✅ decision ∈ {RECOMMEND, NOT_RECOMMEND, NEUTRAL}
- ✅ All reasons MUST have refs (no refs = no reason)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from collections import defaultdict

from apps.api.response_composers.utils import (
    display_coverage_name,
    sanitize_no_coverage_code,
    assign_coverage_group  # STEP NEXT-94
)


class EX4EligibilityComposer:
    """
    Compose EX4_ELIGIBILITY response from eligibility matrix data

    SSOT Schema: STEP NEXT-79 specification
    """

    # Decision types (locked enum)
    DECISION_RECOMMEND = "RECOMMEND"
    DECISION_NOT_RECOMMEND = "NOT_RECOMMEND"
    DECISION_NEUTRAL = "NEUTRAL"

    # Reason types (locked enum)
    REASON_COVERAGE_SUPERIOR = "COVERAGE_SUPERIOR"
    REASON_COVERAGE_MISSING = "COVERAGE_MISSING"
    REASON_CONDITION_UNFAVORABLE = "CONDITION_UNFAVORABLE"

    @staticmethod
    def compose(
        insurers: List[str],
        subtype_keyword: str,
        eligibility_data: List[Dict[str, Any]],
        query_focus_terms: Optional[List[str]] = None,
        coverage_name: Optional[str] = None,
        coverage_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose EX4_ELIGIBILITY response with overall evaluation

        Args:
            insurers: List of insurer codes (e.g., ["samsung", "meritz"])
            subtype_keyword: Disease subtype (e.g., "제자리암", "경계성종양")
            eligibility_data: List of eligibility rows
                [
                    {
                        "insurer": "samsung",
                        "status": "O" | "X" | "△" | "Unknown",
                        "evidence_type": "정의" | "면책" | "감액" | None,
                        "evidence_snippet": "...",
                        "evidence_ref": "..."
                    },
                    ...
                ]
            query_focus_terms: Optional list of focus terms from user query
            coverage_name: Optional coverage name for context (STEP NEXT-83)
            coverage_code: Optional coverage code (used for display_coverage_name, NEVER exposed)

        Returns:
            EX4_ELIGIBILITY message dict
        """
        # STEP NEXT-83: Get display-safe coverage name (NO code exposure)
        display_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        ) if (coverage_name or coverage_code) else None

        # Build title
        title = f"{subtype_keyword} 보장 가능 여부 비교"

        # Build summary bullets
        statuses = [row["status"] for row in eligibility_data]
        summary_bullets = [
            f"{subtype_keyword}에 대한 보장 가능 여부를 확인했습니다",
            f"O: {statuses.count('O')}개, X: {statuses.count('X')}개, "
            f"△: {statuses.count('△')}개, Unknown: {statuses.count('Unknown')}개"
        ]

        # Build sections
        sections = []

        # Section 1: Eligibility Matrix (required)
        matrix_section = EX4EligibilityComposer._build_matrix_section(
            insurers, subtype_keyword, eligibility_data
        )
        sections.append(matrix_section)

        # Section 2: Overall Evaluation (MANDATORY)
        evaluation_section = EX4EligibilityComposer._build_overall_evaluation(
            eligibility_data, query_focus_terms or [subtype_keyword]
        )
        # Add as dict-based section (not in chat_vm.py schema yet)
        sections.append(evaluation_section)

        # Section 3: Common Notes
        notes_section = EX4EligibilityComposer._build_notes_section()
        sections.append(notes_section)

        # STEP NEXT-83: Build bubble markdown with coverage context
        bubble_markdown = EX4EligibilityComposer._build_bubble_markdown(
            subtype_keyword, eligibility_data, evaluation_section,
            coverage_display_name=display_name
        )

        # Build response
        response = {
            "message_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),  # Should be passed from caller
            "kind": "EX4_ELIGIBILITY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "summary_bullets": summary_bullets,
            "sections": sections,
            "bubble_markdown": bubble_markdown,  # STEP NEXT-83
            "lineage": {
                "handler": "EX4EligibilityComposer",
                "llm_used": False,
                "deterministic": True
            }
        }

        # STEP NEXT-83: Final sanitization pass (constitutional enforcement)
        # Ensure NO coverage_code leaks anywhere in response
        response["title"] = sanitize_no_coverage_code(response["title"])
        response["summary_bullets"] = [
            sanitize_no_coverage_code(bullet) for bullet in response["summary_bullets"]
        ]
        if response["bubble_markdown"]:
            response["bubble_markdown"] = sanitize_no_coverage_code(response["bubble_markdown"])

        # Sanitize section titles
        for section in response["sections"]:
            if "title" in section and section["title"]:
                section["title"] = sanitize_no_coverage_code(section["title"])

        return response

    @staticmethod
    def _build_matrix_section(
        insurers: List[str],
        subtype_keyword: str,
        eligibility_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build eligibility matrix table section

        Columns: ["보험사", "보장여부", "근거유형", "근거내용"]
        """
        columns = ["보험사", "보장여부", "근거유형", "근거내용"]
        rows = []

        for row_data in eligibility_data:
            cells = [
                {"text": row_data["insurer"]},
                {"text": row_data["status"]},
                {"text": row_data["evidence_type"] or "판단근거 없음"},
                {"text": (row_data["evidence_snippet"] or "")[:100]}
            ]
            rows.append({
                "cells": cells,
                "is_header": False,
                "meta": None
            })

        return {
            "kind": "comparison_table",
            "table_kind": "ELIGIBILITY_MATRIX",
            "title": f"{subtype_keyword} 보장 가능 여부",
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def _build_overall_evaluation(
        eligibility_data: List[Dict[str, Any]],
        query_focus_terms: List[str]
    ) -> Dict[str, Any]:
        """
        Build overall evaluation section (MANDATORY)

        Deterministic Rules:
        - Rule A (RECOMMEND): One insurer has O, others have X
        - Rule B (NOT_RECOMMEND): Focus coverage has X
        - Rule C (NEUTRAL): Mixed O/X/△ or △-dominant

        Args:
            eligibility_data: List of eligibility rows
            query_focus_terms: Focus terms from user query

        Returns:
            overall_evaluation section dict
        """
        # Count statuses
        status_counts = {}
        insurer_status = {}
        for row in eligibility_data:
            insurer = row["insurer"]
            status = row["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            insurer_status[insurer] = status

        # Extract insurer lists by status
        o_insurers = [ins for ins, st in insurer_status.items() if st == "O"]
        x_insurers = [ins for ins, st in insurer_status.items() if st == "X"]
        delta_insurers = [ins for ins, st in insurer_status.items() if st == "△"]
        unknown_insurers = [ins for ins, st in insurer_status.items() if st == "Unknown"]

        # Apply decision rules
        decision, summary, reasons = EX4EligibilityComposer._apply_decision_rules(
            o_insurers, x_insurers, delta_insurers, unknown_insurers,
            eligibility_data, query_focus_terms
        )

        # Build evaluation section
        return {
            "kind": "overall_evaluation",
            "title": "종합 평가",
            "overall_evaluation": {
                "decision": decision,
                "summary": summary,
                "reasons": reasons,
                "notes": "판단 기준: 보장 가능(O), 면책(X), 감액(△), 판단불가(Unknown) 분포를 기반으로 한 사실 비교입니다"
            }
        }

    @staticmethod
    def _apply_decision_rules(
        o_insurers: List[str],
        x_insurers: List[str],
        delta_insurers: List[str],
        unknown_insurers: List[str],
        eligibility_data: List[Dict[str, Any]],
        query_focus_terms: List[str]
    ) -> tuple[str, str, List[Dict[str, Any]]]:
        """
        Apply deterministic decision rules

        Returns: (decision, summary, reasons)
        """
        # Rule B: NOT_RECOMMEND if majority X
        if len(x_insurers) > len(o_insurers) and len(x_insurers) > 0:
            return (
                EX4EligibilityComposer.DECISION_NOT_RECOMMEND,
                "보장 제외(X) 항목이 다수입니다",
                [
                    {
                        "type": EX4EligibilityComposer.REASON_COVERAGE_MISSING,
                        "description": f"{', '.join(x_insurers)}에서 면책 조건 확인됨",
                        "refs": EX4EligibilityComposer._extract_refs(eligibility_data, x_insurers)
                    }
                ]
            )

        # Rule A: RECOMMEND if clear O majority
        if len(o_insurers) > len(x_insurers) and len(o_insurers) > 0:
            return (
                EX4EligibilityComposer.DECISION_RECOMMEND,
                "보장 가능(O) 항목이 다수입니다",
                [
                    {
                        "type": EX4EligibilityComposer.REASON_COVERAGE_SUPERIOR,
                        "description": f"{', '.join(o_insurers)}에서 보장 가능 확인됨",
                        "refs": EX4EligibilityComposer._extract_refs(eligibility_data, o_insurers)
                    }
                ]
            )

        # Rule C: NEUTRAL (mixed or △-dominant)
        neutral_reasons = []

        if len(delta_insurers) > 0:
            neutral_reasons.append({
                "type": EX4EligibilityComposer.REASON_CONDITION_UNFAVORABLE,
                "description": f"{', '.join(delta_insurers)}에서 감액 조건 확인됨",
                "refs": EX4EligibilityComposer._extract_refs(eligibility_data, delta_insurers)
            })

        if len(unknown_insurers) > 0:
            neutral_reasons.append({
                "type": EX4EligibilityComposer.REASON_COVERAGE_MISSING,
                "description": f"{', '.join(unknown_insurers)}에서 판단 근거 없음",
                "refs": []  # No refs for Unknown
            })

        # If no specific reasons, add generic mixed status reason
        if not neutral_reasons:
            neutral_reasons.append({
                "type": EX4EligibilityComposer.REASON_COVERAGE_SUPERIOR,
                "description": "보장 상태가 혼재되어 우열 판단 불가",
                "refs": EX4EligibilityComposer._extract_refs(eligibility_data, o_insurers + x_insurers)
            })

        return (
            EX4EligibilityComposer.DECISION_NEUTRAL,
            "장단점 혼재로 우열 판단이 어렵습니다",
            neutral_reasons
        )

    @staticmethod
    def _extract_refs(
        eligibility_data: List[Dict[str, Any]],
        target_insurers: List[str]
    ) -> List[str]:
        """
        STEP NEXT-85: Extract PD:/EV: refs from eligibility data

        Args:
            eligibility_data: Full eligibility data
            target_insurers: List of insurers to extract refs from

        Returns:
            List of PD:/EV: refs (e.g., ["PD:samsung:A4210", "PD:meritz:A5298_001"])
        """
        refs = []
        for row in eligibility_data:
            if row["insurer"] in target_insurers:
                # STEP NEXT-85: Use proposal_detail_ref (PD: format)
                pd_ref = row.get("proposal_detail_ref")
                if pd_ref and pd_ref.startswith("PD:"):
                    refs.append(pd_ref)

        return refs[:5]  # Limit to top 5 refs

    @staticmethod
    def _build_notes_section() -> Dict[str, Any]:
        """
        Build common notes section

        Rules:
        - Explain O/X/△/Unknown meanings
        - NO forbidden phrases
        """
        return {
            "kind": "common_notes",
            "title": "유의사항",
            "bullets": [
                "O: 보장 가능, X: 면책, △: 감액, Unknown: 판단 근거 없음",
                "약관 및 상품요약서 기준입니다",
                "실제 보장 여부는 약관을 직접 확인하시기 바랍니다"
            ],
            "groups": None
        }

    @staticmethod
    def _build_bubble_markdown(
        subtype_keyword: str,
        eligibility_data: List[Dict[str, Any]],
        evaluation_section: Dict[str, Any],
        coverage_display_name: Optional[str] = None
    ) -> str:
        """
        Build bubble_markdown for central chat bubble (STEP NEXT-83)

        Rules (Constitutional):
        - NO LLM usage (deterministic only)
        - NO raw text (refs only)
        - NO coverage_code exposure
        - NO scoring/weighting/inference
        - Extract from evaluation section and eligibility data ONLY

        Format (LOCKED - aligned with EX3):
        1. 핵심 요약 (context: subtype, insurer count, data source)
        2. 한눈에 보는 결론 (decision summary in natural language)
        3. 보험사별 판단 요약 (O/△/X grouping by insurers)
        4. 유의사항 (disclaimers)

        Args:
            subtype_keyword: Disease subtype (e.g., "제자리암")
            eligibility_data: List of eligibility rows
            evaluation_section: Overall evaluation section
            coverage_display_name: Optional coverage name for context (NO code exposure)
        """
        # Extract overall evaluation
        overall_eval = evaluation_section.get("overall_evaluation", {})
        decision = overall_eval.get("decision", "NEUTRAL")
        summary = overall_eval.get("summary", "")

        # STEP NEXT-84: Group insurers by status WITH trigger info
        # STEP NEXT-94: Add coverage group info for grouping related coverages
        insurer_groups = {"O": [], "△": [], "X": [], "Unknown": []}
        insurer_trigger_map = {}  # insurer -> (status, trigger, evidence_type, coverage_group)

        for row in eligibility_data:
            status = row.get("status", "Unknown")
            insurer = row.get("insurer", "")
            trigger = row.get("coverage_trigger")
            evidence_type = row.get("evidence_type")

            # STEP NEXT-94: Get coverage group (view-only label)
            coverage_name_raw = row.get("coverage_name_raw", "")
            coverage_group = assign_coverage_group(coverage_name_raw, trigger)

            if status in insurer_groups:
                insurer_groups[status].append(insurer)
            else:
                insurer_groups["Unknown"].append(insurer)

            insurer_trigger_map[insurer] = (status, trigger, evidence_type, coverage_group)

        total_insurers = len(eligibility_data)

        lines = []

        # Section 1: 핵심 요약
        lines.append("## 핵심 요약")
        lines.append("")

        # Build context sentence with optional coverage name
        context_parts = [f"{total_insurers}개 보험사"]
        if coverage_display_name:
            context_parts.append(f"**{coverage_display_name}**")
        context_parts.append(f"**{subtype_keyword}**")

        lines.append(f"이 비교는 {' '.join(context_parts)}에 대해")
        lines.append("가입설계서 및 약관 기준으로 보장 가능 여부를 확인한 결과입니다.")
        lines.append("")

        # Section 2: 한눈에 보는 결론
        lines.append("## 한눈에 보는 결론")
        lines.append("")

        # Convert decision to customer-friendly summary
        if decision == "RECOMMEND":
            conclusion = "보장 가능한 보험사가 다수입니다"
        elif decision == "NOT_RECOMMEND":
            conclusion = "보장되지 않는 보험사가 다수입니다"
        else:  # NEUTRAL
            conclusion = "보험사별 보장 여부가 갈립니다"

        lines.append(f"- {conclusion}")
        lines.append(f"- {summary}")
        lines.append("")

        # Section 3: 보험사별 판단 요약 (STEP NEXT-84: WITH TRIGGER)
        # STEP NEXT-94: Group by coverage group, then by status
        lines.append("## 보험사별 판단 요약")
        lines.append("")

        # Helper to format trigger in Korean
        def format_trigger(trigger: Optional[str], evidence_type: Optional[str]) -> str:
            if not trigger:
                return ""
            trigger_map = {
                "DIAGNOSIS": "진단비 지급",
                "SURGERY": "수술 시 지급",
                "TREATMENT": "치료 시 지급",
                "MIXED": "복합 조건"
            }
            base = trigger_map.get(trigger, "")
            # Add evidence_type detail if △
            if evidence_type == "감액":
                return f"{base} (1년 미만 50% 감액)" if base else "(감액 조건)"
            return base

        # STEP NEXT-94: Group insurers by coverage_group
        # Create group_name -> [(insurer, status, trigger, evidence_type), ...]
        grouped_by_coverage = defaultdict(list)
        for insurer, (status, trigger, evidence_type, coverage_group) in insurer_trigger_map.items():
            grouped_by_coverage[coverage_group].append((insurer, status, trigger, evidence_type))

        # Define group order (진단 → 치료/수술 → 기타)
        group_order = ["진단 관련 담보", "치료/수술 관련 담보", "기타 담보"]

        # Output grouped by coverage_group
        for group_name in group_order:
            if group_name not in grouped_by_coverage:
                continue

            # STEP NEXT-94: Only show group header if multiple groups exist
            if len(grouped_by_coverage) > 1:
                lines.append(f"**[{group_name}]**")
                lines.append("")

            # Sort by status priority: O → △ → X → Unknown
            status_priority = {"O": 0, "△": 1, "X": 2, "Unknown": 3}
            insurers_in_group = sorted(
                grouped_by_coverage[group_name],
                key=lambda x: (status_priority.get(x[1], 4), x[0])  # status, then insurer name
            )

            for insurer, status, trigger, evidence_type in insurers_in_group:
                trigger_text = format_trigger(trigger, evidence_type)

                if status == "O":
                    if trigger_text:
                        lines.append(f"- **{insurer}**: ○ {trigger_text}")
                    else:
                        lines.append(f"- **{insurer}**: ○ 보장 가능")
                elif status == "△":
                    if trigger_text:
                        lines.append(f"- **{insurer}**: △ {trigger_text}")
                    else:
                        lines.append(f"- **{insurer}**: △ 감액 조건 존재")
                elif status == "X":
                    lines.append(f"- **{insurer}**: ✕ 보장 제외")
                else:  # Unknown
                    lines.append(f"- **{insurer}**: ? 판단 근거 없음")

            lines.append("")

        # STEP NEXT-85: Disambiguation note (if applicable)
        # Check if any evidence mentions "유사암" bundling
        has_subtype_bundling = any(
            row.get("evidence_snippet") and
            "유사암" in row.get("evidence_snippet", "") and
            any(keyword in row.get("evidence_snippet", "") for keyword in ["제자리암", "경계성종양", "갑상선암", "기타피부암"])
            for row in eligibility_data
        )

        if has_subtype_bundling:
            lines.append("※ **질병 범주 참고**: 제자리암은 일부 상품에서 '유사암' 범주로 함께 정의되어")
            lines.append("문구에 다른 하위항목(경계성종양, 갑상선암 등)이 포함될 수 있습니다.")
            lines.append("")

        # Section 4: 유의사항
        lines.append("## 유의사항")
        lines.append("")
        lines.append("※ 본 결과는 가입설계서 기준 요약이며,")
        lines.append("세부 조건(감액·면책·대기기간)은 상품 약관에 따라 달라질 수 있습니다.")
        lines.append("")

        # STEP NEXT-98: Question Continuity Hints (판단 → 조건 확장 비교 연결)
        lines.append("---")
        lines.append("")
        lines.append("## 📌 참고")
        lines.append("")
        lines.append(f"{subtype_keyword}은(는) 일부 상품에서")
        lines.append("**경계성종양·유사암**과 함께 정의되어")
        lines.append("보험사별 보장 기준이 달라질 수 있습니다.")
        lines.append("")
        lines.append("👉 **이런 비교도 가능합니다**")
        lines.append(f"- {subtype_keyword}·경계성종양 기준으로 **보험사별 상품 비교**")
        if coverage_display_name:
            lines.append(f"- {coverage_display_name} 중 **보장한도가 다른 상품 찾기**")

        return "\n".join(lines)
