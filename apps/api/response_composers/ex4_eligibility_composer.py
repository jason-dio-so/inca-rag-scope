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
        query_focus_terms: Optional[List[str]] = None
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

        Returns:
            EX4_ELIGIBILITY message dict
        """
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

        # STEP NEXT-81B: Build bubble markdown
        bubble_markdown = EX4EligibilityComposer._build_bubble_markdown(
            subtype_keyword, eligibility_data, evaluation_section
        )

        # Build response
        return {
            "message_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),  # Should be passed from caller
            "kind": "EX4_ELIGIBILITY",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "summary_bullets": summary_bullets,
            "sections": sections,
            "bubble_markdown": bubble_markdown,  # STEP NEXT-81B
            "lineage": {
                "handler": "EX4EligibilityComposer",
                "llm_used": False,
                "deterministic": True
            }
        }

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
        Extract evidence refs from eligibility data for target insurers

        Args:
            eligibility_data: Full eligibility data
            target_insurers: List of insurers to extract refs from

        Returns:
            List of evidence refs (e.g., ["약관 p.12", "상품요약서 p.3"])
        """
        refs = []
        for row in eligibility_data:
            if row["insurer"] in target_insurers:
                if row.get("evidence_ref"):
                    refs.append(row["evidence_ref"])

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
        evaluation_section: Dict[str, Any]
    ) -> str:
        """
        Build bubble_markdown for central chat bubble (STEP NEXT-81B)

        Rules (Constitutional):
        - NO LLM usage (deterministic only)
        - NO raw text (refs only)
        - Extract from evaluation section and eligibility data

        Format:
        1. 제목 (질병 subtype)
        2. 종합평가 결론 (RECOMMEND/NOT_RECOMMEND/NEUTRAL)
        3. O/X/△ 분포 요약
        4. 근거 안내
        5. 주의사항
        """
        # Extract overall evaluation
        overall_eval = evaluation_section.get("overall_evaluation", {})
        decision = overall_eval.get("decision", "NEUTRAL")
        decision_display = {
            "RECOMMEND": "✅ 추천",
            "NOT_RECOMMEND": "❌ 비추천",
            "NEUTRAL": "⚠️ 유보"
        }.get(decision, "판단 보류")

        # Section 1: Title
        lines = [
            f"# {subtype_keyword} 보장 가능 여부 요약",
            ""
        ]

        # Section 2: Overall evaluation
        lines.append("## 종합 평가")
        lines.append("")
        lines.append(f"**{decision_display}**")
        lines.append("")

        # Extract reasons from evaluation
        reasons = overall_eval.get("reasons", [])
        if reasons:
            lines.append("**판단 근거:**")
            for reason in reasons[:3]:  # Limit to 3 reasons
                reason_text = reason.get("reason_text", "")
                lines.append(f"- {reason_text}")
            lines.append("")

        # Section 3: O/X/△ distribution
        statuses = [row["status"] for row in eligibility_data]
        o_count = statuses.count("O")
        x_count = statuses.count("X")
        delta_count = statuses.count("△")
        unknown_count = statuses.count("Unknown")

        lines.append("## 보험사별 분포")
        lines.append("")
        lines.append(f"- ✅ **보장 가능(O)**: {o_count}개 보험사")
        lines.append(f"- ❌ **면책(X)**: {x_count}개 보험사")
        lines.append(f"- ⚠️ **감액(△)**: {delta_count}개 보험사")
        if unknown_count > 0:
            lines.append(f"- ❓ **판단 불가(Unknown)**: {unknown_count}개 보험사")
        lines.append("")

        # Section 4: Evidence guide
        lines.append("## 근거 확인")
        lines.append("")
        lines.append("상세 근거는 **ⓘ 아이콘** 및 비교표에서 확인하실 수 있습니다.")
        lines.append("")

        # Section 5: Caution
        lines.append("## 유의사항")
        lines.append("")
        lines.append("- O: 보장 가능, X: 면책, △: 감액, Unknown: 판단 근거 없음")
        lines.append("- 본 비교는 약관 및 상품요약서 기준이며, 실제 보장 여부는 원문 확인이 필요합니다.")

        return "\n".join(lines)
