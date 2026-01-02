#!/usr/bin/env python3
"""
EX3_COMPARE Response Composer

STEP NEXT-77: Lock EX3_COMPARE response schema + composer

DESIGN:
1. Input: Compare result (slim cards), KPI summary/condition, refs
2. Output: EX3_COMPARE message dict (SSOT schema)
3. NO raw text in response body (refs only)
4. Deterministic only (NO LLM)

CONSTITUTIONAL RULES:
- ❌ NO LLM usage
- ❌ NO raw text in response body (DETAIL/EVIDENCE)
- ✅ refs MUST use PD:/EV: prefix
- ✅ "명시 없음" ONLY when structurally missing
- ✅ Forbidden phrase validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from apps.api.response_composers.utils import display_coverage_name, sanitize_no_coverage_code


class EX3CompareComposer:
    """
    Compose EX3_COMPARE response from coverage comparison data

    SSOT Schema: docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md
    """

    @staticmethod
    def compose(
        insurers: List[str],
        coverage_code: str,
        comparison_data: Dict[str, Any],
        coverage_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose EX3_COMPARE response

        Args:
            insurers: List of insurer codes (e.g., ["samsung", "meritz"])
            coverage_code: Coverage code (e.g., "A4200_1")
            comparison_data: Dict with insurer data
                {
                    "samsung": {
                        "amount": "3000만원",
                        "premium": "명시 없음",
                        "period": "20년납/80세만기",
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
            EX3_COMPARE message dict
        """
        # STEP NEXT-81B: Get display-safe coverage name (NO code exposure)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[EX3_COMPOSE] coverage_name={coverage_name}, coverage_code={coverage_code}")

        display_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        )
        logger.info(f"[EX3_COMPOSE] display_name={display_name}")

        # Build title
        insurer1, insurer2 = insurers[0], insurers[1]
        title = f"{insurer1} vs {insurer2} {display_name} 비교"

        # Build summary bullets
        summary_bullets = [
            f"{len(insurers)}개 보험사의 {display_name}를 비교했습니다",
            "가입설계서 기준 비교입니다"
        ]

        # Build sections
        sections = []

        # Section 1: KPI Summary (optional)
        kpi_section = EX3CompareComposer._build_kpi_section(insurers, comparison_data)
        if kpi_section:
            sections.append(kpi_section)

        # Section 2: Comparison Table (required)
        table_section = EX3CompareComposer._build_table_section(
            insurers, comparison_data, display_name
        )
        sections.append(table_section)

        # Section 3: Footnotes (optional)
        footnotes_section = EX3CompareComposer._build_footnotes_section()
        sections.append(footnotes_section)

        # STEP NEXT-81B: Build bubble markdown
        bubble_markdown = EX3CompareComposer._build_bubble_markdown(
            insurers, display_name, comparison_data
        )

        # Build response
        response = {
            "message_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),  # Should be passed from caller
            "kind": "EX3_COMPARE",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "summary_bullets": summary_bullets,
            "sections": sections,
            "bubble_markdown": bubble_markdown,  # STEP NEXT-81B
            "lineage": {
                "handler": "EX3CompareComposer",
                "llm_used": False,
                "deterministic": True
            }
        }

        # STEP NEXT-81B: Final sanitization pass (constitutional enforcement)
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
    def _build_kpi_section(
        insurers: List[str],
        comparison_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build KPI summary section

        Rules:
        - Extract KPI from first insurer (if available)
        - Aggregate refs from all insurers
        - Return None if no KPI data
        """
        # Get first insurer's KPI
        first_insurer = insurers[0]
        kpi_summary = comparison_data.get(first_insurer, {}).get("kpi_summary")
        kpi_condition = comparison_data.get(first_insurer, {}).get("kpi_condition")

        if not kpi_summary and not kpi_condition:
            return None

        # Build KPI dict
        kpi = {
            "payment_type": "UNKNOWN",
            "limit_summary": None,
            "conditions": {},
            "refs": {
                "kpi_evidence_refs": [],
                "condition_evidence_refs": []
            }
        }

        # Extract payment_type and limit_summary
        if kpi_summary:
            kpi["payment_type"] = kpi_summary.get("payment_type", "UNKNOWN")
            kpi["limit_summary"] = kpi_summary.get("limit_summary")

            # Aggregate kpi_evidence_refs from all insurers
            for insurer in insurers:
                insurer_kpi = comparison_data.get(insurer, {}).get("kpi_summary", {})
                refs = insurer_kpi.get("kpi_evidence_refs", [])
                kpi["refs"]["kpi_evidence_refs"].extend(refs)

        # Extract conditions
        if kpi_condition:
            conditions = {}
            if kpi_condition.get("waiting_period"):
                conditions["waiting_period"] = kpi_condition["waiting_period"]
            if kpi_condition.get("reduction_condition"):
                conditions["reduction_condition"] = kpi_condition["reduction_condition"]
            if kpi_condition.get("exclusion_condition"):
                conditions["exclusion_condition"] = kpi_condition["exclusion_condition"]
            if kpi_condition.get("renewal_type"):
                conditions["renewal_type"] = kpi_condition["renewal_type"]

            kpi["conditions"] = conditions

            # Aggregate condition_evidence_refs from all insurers
            for insurer in insurers:
                insurer_cond = comparison_data.get(insurer, {}).get("kpi_condition", {})
                refs = insurer_cond.get("condition_evidence_refs", [])
                kpi["refs"]["condition_evidence_refs"].extend(refs)

        return {
            "kind": "kpi_summary",
            "title": "주요 지표",
            "kpi": kpi
        }

    @staticmethod
    def _build_table_section(
        insurers: List[str],
        comparison_data: Dict[str, Any],
        coverage_name: str
    ) -> Dict[str, Any]:
        """
        Build comparison table section

        Rules:
        - Columns: ["구분", insurer1, insurer2, ...]
        - Rows: 보장금액, 보험료, 납입/만기, 지급유형
        - Each row has meta with refs
        """
        # Build columns
        columns = ["구분"] + insurers

        # Build rows
        rows = []

        # Row 1: 보장금액
        row1_cells = [{"text": "보장금액"}]
        for insurer in insurers:
            amount = comparison_data.get(insurer, {}).get("amount", "명시 없음")
            row1_cells.append({"text": amount})

        # Get meta from first insurer
        first_insurer = insurers[0]
        meta1 = EX3CompareComposer._build_row_meta(comparison_data.get(first_insurer, {}))

        rows.append({
            "cells": row1_cells,
            "is_header": False,
            "meta": meta1
        })

        # Row 2: 보험료
        row2_cells = [{"text": "보험료"}]
        for insurer in insurers:
            premium = comparison_data.get(insurer, {}).get("premium", "명시 없음")
            row2_cells.append({"text": premium})

        rows.append({
            "cells": row2_cells,
            "is_header": False,
            "meta": meta1  # Reuse meta (same coverage)
        })

        # Row 3: 납입/만기
        row3_cells = [{"text": "납입/만기"}]
        for insurer in insurers:
            period = comparison_data.get(insurer, {}).get("period", "명시 없음")
            row3_cells.append({"text": period})

        rows.append({
            "cells": row3_cells,
            "is_header": False,
            "meta": meta1  # Reuse meta
        })

        # Row 4: 지급유형
        row4_cells = [{"text": "지급유형"}]
        for insurer in insurers:
            payment_type = comparison_data.get(insurer, {}).get("payment_type", "UNKNOWN")
            # Display "표현 없음" for UNKNOWN
            display_text = "표현 없음" if payment_type == "UNKNOWN" else payment_type
            row4_cells.append({"text": display_text})

        rows.append({
            "cells": row4_cells,
            "is_header": False,
            "meta": meta1  # Reuse meta
        })

        return {
            "kind": "comparison_table",
            "table_kind": "INTEGRATED_COMPARE",
            "title": f"{coverage_name} 비교표",
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def _build_row_meta(insurer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build TableRowMeta from insurer data

        Args:
            insurer_data: Dict with proposal_detail_ref, evidence_refs, kpi_summary, kpi_condition

        Returns:
            TableRowMeta dict (without Pydantic model)
        """
        meta = {}

        if insurer_data.get("proposal_detail_ref"):
            meta["proposal_detail_ref"] = insurer_data["proposal_detail_ref"]

        if insurer_data.get("evidence_refs"):
            meta["evidence_refs"] = insurer_data["evidence_refs"]

        if insurer_data.get("kpi_summary"):
            # Convert dict to KPISummaryMeta-compatible dict
            kpi_summary = insurer_data["kpi_summary"]
            meta["kpi_summary"] = {
                "payment_type": kpi_summary.get("payment_type", "UNKNOWN"),
                "limit_summary": kpi_summary.get("limit_summary"),
                "kpi_evidence_refs": kpi_summary.get("kpi_evidence_refs", []),
                "extraction_notes": kpi_summary.get("extraction_notes", "")
            }

        if insurer_data.get("kpi_condition"):
            # Convert dict to KPIConditionMeta-compatible dict
            kpi_condition = insurer_data["kpi_condition"]
            meta["kpi_condition"] = {
                "waiting_period": kpi_condition.get("waiting_period"),
                "reduction_condition": kpi_condition.get("reduction_condition"),
                "exclusion_condition": kpi_condition.get("exclusion_condition"),
                "renewal_condition": kpi_condition.get("renewal_condition"),
                "condition_evidence_refs": kpi_condition.get("condition_evidence_refs", []),
                "extraction_notes": kpi_condition.get("extraction_notes", "")
            }

        return meta if meta else None

    @staticmethod
    def _build_footnotes_section() -> Dict[str, Any]:
        """
        Build footnotes section (common notes)

        Rules:
        - Use grouped bullets (preferred)
        - NO forbidden phrases
        """
        return {
            "kind": "common_notes",
            "title": "공통사항 및 유의사항",
            "groups": [
                {
                    "title": "공통사항",
                    "bullets": ["가입설계서 기준 비교입니다"]
                },
                {
                    "title": "유의사항",
                    "bullets": [
                        "실제 약관과 다를 수 있습니다",
                        "대기기간, 감액기간, 면책사항 등 세부 조건은 약관을 직접 확인하시기 바랍니다"
                    ]
                }
            ]
        }

    @staticmethod
    def _build_bubble_markdown(
        insurers: List[str],
        display_name: str,
        comparison_data: Dict[str, Any]
    ) -> str:
        """
        Build bubble_markdown for central chat bubble (STEP NEXT-81B)

        Rules (Constitutional):
        - NO LLM usage (deterministic only)
        - NO raw text (refs only)
        - NO coverage_code exposure (display_name is pre-sanitized)
        - Extract from KPI/comparison data only

        Format:
        1. 제목 (담보명, NO code)
        2. 핵심 결론 (금액/지급유형/한도)
        3. 주요 차이 (KPI condition)
        4. 근거 안내
        5. 주의사항

        Args:
            insurers: List of insurer codes
            display_name: Display-safe coverage name (NO coverage_code)
            comparison_data: Dict with insurer comparison data
        """
        insurer1, insurer2 = insurers[0], insurers[1]
        data1 = comparison_data.get(insurer1, {})
        data2 = comparison_data.get(insurer2, {})

        # Section 1: Title
        lines = [
            f"# {insurer1} vs {insurer2} {display_name} 비교",
            ""
        ]

        # Section 2: Core conclusion (amount, payment type, limit)
        amount1 = data1.get("amount", "명시 없음")
        amount2 = data2.get("amount", "명시 없음")
        payment1 = data1.get("payment_type", "UNKNOWN")
        payment2 = data2.get("payment_type", "UNKNOWN")

        kpi1 = data1.get("kpi_summary", {}) or {}
        kpi2 = data2.get("kpi_summary", {}) or {}
        limit1 = kpi1.get("limit_summary", "명시 없음")
        limit2 = kpi2.get("limit_summary", "명시 없음")

        lines.append("## 핵심 결론")
        lines.append("")

        # Amount comparison
        if amount1 == amount2:
            lines.append(f"- **보장금액**: 동일 ({amount1})")
        else:
            lines.append(f"- **보장금액**: 차이 있음 ({insurer1}: {amount1}, {insurer2}: {amount2})")

        # Payment type
        payment1_display = "표현 없음" if payment1 == "UNKNOWN" else payment1
        payment2_display = "표현 없음" if payment2 == "UNKNOWN" else payment2
        if payment1 == payment2:
            lines.append(f"- **지급유형**: 동일 ({payment1_display})")
        else:
            lines.append(f"- **지급유형**: 차이 있음 ({insurer1}: {payment1_display}, {insurer2}: {payment2_display})")

        # Limit summary
        if limit1 == limit2:
            lines.append(f"- **지급한도**: 동일 ({limit1})")
        else:
            lines.append(f"- **지급한도**: 차이 있음 ({insurer1}: {limit1}, {insurer2}: {limit2})")

        lines.append("")

        # Section 3: Major differences (KPI condition)
        cond1 = data1.get("kpi_condition", {}) or {}
        cond2 = data2.get("kpi_condition", {}) or {}

        lines.append("## 주요 차이")
        lines.append("")

        differences = []

        # Waiting period
        wait1 = cond1.get("waiting_period")
        wait2 = cond2.get("waiting_period")
        if wait1 != wait2:
            differences.append(f"- 대기기간: {insurer1} {wait1 or '명시 없음'}, {insurer2} {wait2 or '명시 없음'}")

        # Reduction condition
        red1 = cond1.get("reduction_condition")
        red2 = cond2.get("reduction_condition")
        if red1 != red2:
            differences.append(f"- 감액조건: {insurer1} {red1 or '명시 없음'}, {insurer2} {red2 or '명시 없음'}")

        # Exclusion condition
        exc1 = cond1.get("exclusion_condition")
        exc2 = cond2.get("exclusion_condition")
        if exc1 != exc2:
            differences.append(f"- 면책조건: {insurer1} {exc1 or '명시 없음'}, {insurer2} {exc2 or '명시 없음'}")

        if differences:
            lines.extend(differences)
        else:
            lines.append("주요 조건 차이: 확인된 차이 없음")

        lines.append("")

        # Section 4: Evidence guide
        lines.append("## 근거 확인")
        lines.append("")
        lines.append("상세 근거는 **[보장내용 보기]** 버튼 및 **ⓘ 아이콘**에서 확인하실 수 있습니다.")
        lines.append("")

        # Section 5: Caution
        lines.append("## 주의사항")
        lines.append("")
        lines.append("본 비교는 가입설계서 및 근거 문서의 표현을 기준으로 하며, 정확한 보장 내용은 원문 확인이 필요합니다.")

        return "\n".join(lines)
