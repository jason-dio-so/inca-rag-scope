#!/usr/bin/env python3
"""
EX2_LIMIT_FIND Response Composer

STEP NEXT-78: Limit/Condition Difference Finder

PURPOSE:
Find differences in coverage limits/conditions across insurers.
Output is a **diff table** (NO O/X/△ matrix).

DESIGN:
1. Input: Coverage cards (slim), KPI summary, compare_field
2. Output: EX2_LIMIT_FIND message dict (SSOT schema)
3. NO eligibility judgment (O/X/△)
4. NO raw text in response body (refs only)
5. Deterministic only (NO LLM)

CONSTITUTIONAL RULES:
- ❌ NO LLM usage
- ❌ NO O/X/△ in output
- ❌ NO raw text in response body
- ✅ Value comparison ONLY
- ✅ refs MUST use PD:/EV: prefix
- ✅ Deterministic only
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class EX2LimitFindComposer:
    """
    Compose EX2_LIMIT_FIND response for limit/condition difference finding

    SSOT Schema: docs/ui/INTENT_ROUTER_RULES.md (EX2_LIMIT_FIND section)
    """

    @staticmethod
    def compose(
        insurers: List[str],
        coverage_code: str,
        compare_field: str,
        comparison_data: Dict[str, Any],
        coverage_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose EX2_LIMIT_FIND response

        Args:
            insurers: List of insurer codes (e.g., ["samsung", "meritz"])
            coverage_code: Coverage code (e.g., "A4200_1")
            compare_field: Field to compare (e.g., "보장한도", "지급유형")
            comparison_data: Dict with insurer data
                {
                    "samsung": {
                        "limit_summary": "1일 1회, 최대 120일",
                        "payment_type": "정액형",
                        "proposal_detail_ref": "PD:samsung:A4200_1",
                        "evidence_refs": ["EV:samsung:A4200_1:01"],
                        "kpi_summary": {...},
                        "kpi_condition": {...}
                    },
                    "meritz": {...}
                }
            coverage_name: Coverage name (e.g., "암진단비(유사암 제외)")

        Returns:
            EX2_LIMIT_FIND message dict
        """
        # Build title
        title = f"{coverage_name or coverage_code} {compare_field} 차이 비교"

        # Extract field values for diff analysis
        field_values = {}
        for insurer in insurers:
            insurer_data = comparison_data.get(insurer, {})

            # Extract value based on compare_field
            if compare_field == "보장한도":
                value = insurer_data.get("limit_summary") or "명시 없음"
            elif compare_field == "지급유형":
                value = insurer_data.get("payment_type", "UNKNOWN")
                # Display "표현 없음" for UNKNOWN
                value = "표현 없음" if value == "UNKNOWN" else value
            elif compare_field == "조건":
                # Extract conditions from kpi_condition
                kpi_cond = insurer_data.get("kpi_condition", {})
                conditions = []
                if kpi_cond.get("waiting_period"):
                    conditions.append(f"대기: {kpi_cond['waiting_period']}")
                if kpi_cond.get("reduction_condition"):
                    conditions.append(f"감액: {kpi_cond['reduction_condition']}")
                if kpi_cond.get("exclusion_condition"):
                    conditions.append(f"면책: {kpi_cond['exclusion_condition']}")
                value = ", ".join(conditions) if conditions else "명시 없음"
            else:
                value = "명시 없음"

            field_values[insurer] = value

        # Build diff summary
        unique_values = set(field_values.values())
        if len(unique_values) == 1:
            # All same
            diff_status = "ALL_SAME"
            summary_bullets = [
                f"선택한 보험사의 {compare_field}는 모두 동일합니다",
                f"공통 값: {list(unique_values)[0]}"
            ]
        else:
            # Different
            diff_status = "DIFF"
            # Find minority group (different insurers)
            value_groups = {}
            for insurer, value in field_values.items():
                if value not in value_groups:
                    value_groups[value] = []
                value_groups[value].append(insurer)

            # Sort by group size
            sorted_groups = sorted(value_groups.items(), key=lambda x: len(x[1]))
            minority_value, minority_insurers = sorted_groups[0]

            summary_bullets = [
                f"{', '.join(minority_insurers)}의 {compare_field}가 다릅니다",
                f"다른 값: {minority_value}"
            ]

        # Build sections
        sections = []

        # Section 1: Diff table
        table_section = EX2LimitFindComposer._build_diff_table(
            insurers, comparison_data, compare_field, coverage_name or coverage_code
        )
        sections.append(table_section)

        # Section 2: Common notes
        footnotes_section = {
            "kind": "common_notes",
            "title": "유의사항",
            "bullets": [
                "값 차이 비교는 KPI Summary/Condition 기준입니다",
                "세부 근거는 각 항목의 '보장내용 보기' 또는 '근거 보기' 버튼에서 확인하세요"
            ]
        }
        sections.append(footnotes_section)

        # Build response
        return {
            "message_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),  # Should be passed from caller
            "kind": "EX2_LIMIT_FIND",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "summary_bullets": summary_bullets,
            "sections": sections,
            "lineage": {
                "handler": "EX2LimitFindComposer",
                "llm_used": False,
                "deterministic": True,
                "diff_status": diff_status
            }
        }

    @staticmethod
    def _build_diff_table(
        insurers: List[str],
        comparison_data: Dict[str, Any],
        compare_field: str,
        coverage_name: str
    ) -> Dict[str, Any]:
        """
        Build diff comparison table

        Rules:
        - Columns: ["보험사", compare_field, "근거"]
        - Rows: One per insurer
        - Each row has meta with refs
        - NO O/X/△
        """
        # Build columns
        columns = ["보험사", compare_field, "근거"]

        # Build rows
        rows = []
        for insurer in insurers:
            insurer_data = comparison_data.get(insurer, {})

            # Extract value
            if compare_field == "보장한도":
                value = insurer_data.get("limit_summary") or "명시 없음"
                refs = insurer_data.get("kpi_summary", {}).get("kpi_evidence_refs", [])
            elif compare_field == "지급유형":
                value = insurer_data.get("payment_type", "UNKNOWN")
                value = "표현 없음" if value == "UNKNOWN" else value
                refs = insurer_data.get("kpi_summary", {}).get("kpi_evidence_refs", [])
            elif compare_field == "조건":
                kpi_cond = insurer_data.get("kpi_condition", {})
                conditions = []
                if kpi_cond.get("waiting_period"):
                    conditions.append(f"대기: {kpi_cond['waiting_period']}")
                if kpi_cond.get("reduction_condition"):
                    conditions.append(f"감액: {kpi_cond['reduction_condition']}")
                if kpi_cond.get("exclusion_condition"):
                    conditions.append(f"면책: {kpi_cond['exclusion_condition']}")
                value = ", ".join(conditions) if conditions else "명시 없음"
                refs = kpi_cond.get("condition_evidence_refs", [])
            else:
                value = "명시 없음"
                refs = []

            # Build evidence cell text
            evidence_text = f"{len(refs)}건" if refs else "없음"

            # Build row
            row_cells = [
                {"text": insurer},
                {"text": value},
                {"text": evidence_text}
            ]

            # Build meta
            meta = {
                "proposal_detail_ref": insurer_data.get("proposal_detail_ref"),
                "evidence_refs": refs if refs else insurer_data.get("evidence_refs", [])
            }

            # Add kpi_summary/kpi_condition if available
            if insurer_data.get("kpi_summary"):
                meta["kpi_summary"] = insurer_data["kpi_summary"]
            if insurer_data.get("kpi_condition"):
                meta["kpi_condition"] = insurer_data["kpi_condition"]

            rows.append({
                "cells": row_cells,
                "is_header": False,
                "meta": meta
            })

        return {
            "kind": "comparison_table",
            "table_kind": "COVERAGE_DETAIL",  # Reuse existing table type
            "title": f"{coverage_name} {compare_field} 비교",
            "columns": columns,
            "rows": rows
        }
