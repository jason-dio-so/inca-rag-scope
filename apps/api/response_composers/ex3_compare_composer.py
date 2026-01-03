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

from apps.api.response_composers.utils import (
    display_coverage_name,
    sanitize_no_coverage_code,
    format_insurer_name
)


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
        display_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        )

        # Build title (STEP NEXT-110A: Use display names, NOT codes)
        insurer1, insurer2 = insurers[0], insurers[1]
        insurer1_display = format_insurer_name(insurer1)
        insurer2_display = format_insurer_name(insurer2)
        title = f"{insurer1_display} vs {insurer2_display} {display_name} 비교"

        # STEP NEXT-112: Build structural difference summary (NOT abstract)
        # Extract data for structural basis detection
        data1 = comparison_data.get(insurer1, {})
        data2 = comparison_data.get(insurer2, {})

        amount1 = data1.get("amount", "명시 없음")
        amount2 = data2.get("amount", "명시 없음")
        kpi1 = data1.get("kpi_summary", {}) or {}
        kpi2 = data2.get("kpi_summary", {}) or {}
        limit1 = kpi1.get("limit_summary")
        limit2 = kpi2.get("limit_summary")
        payment1 = data1.get("payment_type", "UNKNOWN")
        payment2 = data2.get("payment_type", "UNKNOWN")

        # Helper function to determine structural basis
        def get_definition_basis(amount, limit, payment):
            if amount != "명시 없음":
                return "정액 지급 방식"
            elif limit:
                return "지급 한도 기준"
            elif payment != "UNKNOWN":
                return f"{payment} 방식"
            else:
                return "기본 보장 방식"

        basis1 = get_definition_basis(amount1, limit1, payment1)
        basis2 = get_definition_basis(amount2, limit2, payment2)

        # STEP NEXT-116: Build structural comparison summary (top-level summary for right panel)
        # This provides a framework before users see the detailed table
        if basis1 == basis2:
            structural_summary_panel = f"이 비교에서는 {insurer1_display}와 {insurer2_display} 모두 {basis1}으로 보장이 정의된 구조입니다."
            structural_summary_bullet = f"{insurer1_display}와 {insurer2_display}는 모두 {basis1}으로 보장이 정의됩니다"
        else:
            # Deterministic: Describe each insurer's structure separately
            structural_summary_panel = (
                f"이 비교에서는 {insurer1_display}는 '{basis1}'이고, "
                f"{insurer2_display}는 '{basis2}'입니다."
            )
            structural_summary_bullet = (
                f"{insurer1_display}는 {basis1}으로 보장이 정의되고, "
                f"{insurer2_display}는 {basis2}으로 보장이 정의됩니다"
            )

        summary_bullets = [
            structural_summary_bullet,
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

        # STEP NEXT-128: Build bubble markdown from TABLE (SSOT)
        # Bubble MUST match table structure (no hardcoded assumptions)
        insurer_display_names = [format_insurer_name(ins) for ins in insurers]
        bubble_markdown = EX3CompareComposer._build_bubble_markdown(
            insurers, insurer_display_names, display_name, comparison_data, table_section
        )

        # Build response
        response = {
            "message_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),  # Should be passed from caller
            "kind": "EX3_COMPARE",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "summary_bullets": summary_bullets,
            "structural_summary": structural_summary_panel,  # STEP NEXT-116: Top-level structural comparison
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
                insurer_cond = comparison_data.get(insurer, {}).get("kpi_condition")
                if insurer_cond:  # Handle None case
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
        Build comparison table section (STEP NEXT-127: Per-Insurer Cells + Meta)

        STEP NEXT-127 FIXES:
        - Per-insurer cells: Show limit vs amount correctly per insurer
        - Per-insurer meta: Each cell carries its own insurer's refs (NOT shared)
        - Structural basis: Reflect limit vs amount difference in "보장 정의 기준" row

        Rules:
        - Columns: ["비교 항목", insurer1_display, insurer2_display]
        - Rows: 보장 정의 기준, 핵심 보장 내용, 지급유형
        - Side-by-side comparison (same row = direct comparison)
        """
        # Build columns with display names
        insurer1, insurer2 = insurers[0], insurers[1]
        insurer1_display = format_insurer_name(insurer1)
        insurer2_display = format_insurer_name(insurer2)
        columns = ["비교 항목", insurer1_display, insurer2_display]

        # Extract data
        data1 = comparison_data.get(insurer1, {})
        data2 = comparison_data.get(insurer2, {})

        amount1 = data1.get("amount", "명시 없음")
        amount2 = data2.get("amount", "명시 없음")
        kpi1 = data1.get("kpi_summary", {}) or {}
        kpi2 = data2.get("kpi_summary", {}) or {}
        limit1 = kpi1.get("limit_summary")
        limit2 = kpi2.get("limit_summary")
        payment1 = data1.get("payment_type", "UNKNOWN")
        payment2 = data2.get("payment_type", "UNKNOWN")

        # STEP NEXT-127: Build per-insurer meta
        meta1 = EX3CompareComposer._build_row_meta(data1)
        meta2 = EX3CompareComposer._build_row_meta(data2)

        # STEP NEXT-127: Helper function to determine structural basis + detail
        def get_definition_basis_and_detail(amount, limit, payment):
            """
            Determine structural basis and what to show in detail row

            Priority (STEP NEXT-127 CONTRACT):
            1. If limit exists → basis = "지급 한도/횟수 기준", detail = limit
            2. Elif amount != "명시 없음" → basis = "보장금액(정액) 기준", detail = amount
            3. Else → basis = "표현 없음", detail = None
            """
            if limit:
                return "지급 한도/횟수 기준", limit
            elif amount != "명시 없음":
                return "보장금액(정액) 기준", amount
            else:
                return "표현 없음", None

        basis1, detail1 = get_definition_basis_and_detail(amount1, limit1, payment1)
        basis2, detail2 = get_definition_basis_and_detail(amount2, limit2, payment2)

        # Build rows
        rows = []

        # Row 1: 보장 정의 기준 (ALWAYS - STEP NEXT-127: Per-insurer basis)
        rows.append({
            "cells": [
                {"text": "보장 정의 기준"},
                {"text": basis1, "meta": meta1},  # STEP NEXT-127: Per-cell meta
                {"text": basis2, "meta": meta2}   # STEP NEXT-127: Per-cell meta
            ],
            "is_header": False
        })

        # Row 2: 핵심 보장 내용 (STEP NEXT-127: Show limit or amount per insurer)
        rows.append({
            "cells": [
                {"text": "핵심 보장 내용"},
                {"text": detail1 if detail1 else "표현 없음", "meta": meta1},
                {"text": detail2 if detail2 else "표현 없음", "meta": meta2}
            ],
            "is_header": False
        })

        # Row 3: 지급유형 (ALWAYS)
        payment1_display = "표현 없음" if payment1 == "UNKNOWN" else payment1
        payment2_display = "표현 없음" if payment2 == "UNKNOWN" else payment2
        rows.append({
            "cells": [
                {"text": "지급유형"},
                {"text": payment1_display, "meta": meta1},
                {"text": payment2_display, "meta": meta2}
            ],
            "is_header": False
        })

        return {
            "kind": "comparison_table",
            "table_kind": "INTEGRATED_COMPARE",
            "title": f"{coverage_name} 보장 기준 비교",
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
        insurer_display_names: List[str],
        display_name: str,
        comparison_data: Dict[str, Any],
        table_section: Dict[str, Any]
    ) -> str:
        """
        Build bubble_markdown for central chat bubble (STEP NEXT-128: TABLE-DRIVEN)

        STEP NEXT-128 ABSOLUTE LOCK:
        - ❌ FORBIDDEN: Hardcoded insurer order assumptions
        - ❌ FORBIDDEN: "일부 보험사는..." (ABSOLUTE FORBIDDEN)
        - ❌ FORBIDDEN: Any abstract/vague language
        - ✅ REQUIRED: Read structure from TABLE (SSOT)
        - ✅ REQUIRED: Bubble MUST match table structure 100%
        - ✅ REQUIRED: 6 lines EXACTLY (format preserved from STEP NEXT-126)

        CORE PRINCIPLE (STEP NEXT-128):
        "Bubble is NOT an explanation - it RE-READS the table in natural language"

        Structure Detection (DETERMINISTIC):
        - LIMIT structure: cells.text contains ["보험기간 중", "지급 한도", "횟수", "회"]
        - AMOUNT structure: cells.text contains ["만원", "천만원", "원"]
        - Priority: LIMIT > AMOUNT (if both exist)

        LOCKED FORMAT (6 lines):
        Line 1: "{LIMIT insurer}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,"
        Line 2: "{AMOUNT insurer}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다."
        Line 3: (blank)
        Line 4: "**즉,**"
        Line 5: "- {LIMIT insurer}: 지급 조건·횟수(한도) 기준"
        Line 6: "- {AMOUNT insurer}: 지급 금액이 명확한 정액(보장금액) 기준"

        Args:
            insurers: List of insurer codes (for indexing)
            insurer_display_names: List of insurer display names (for UI output)
            display_name: Display-safe coverage name (NOT used in bubble)
            comparison_data: Dict with insurer comparison data (NOT used - table is SSOT)
            table_section: comparison_table section (SSOT for structure detection)
        """
        insurer1_display, insurer2_display = insurer_display_names[0], insurer_display_names[1]

        # STEP NEXT-128: Detect structure from TABLE (SSOT)
        # Extract "핵심 보장 내용" row (contains limit or amount)
        rows = table_section.get("rows", [])

        # Find "핵심 보장 내용" row
        detail_row = None
        for row in rows:
            cells = row.get("cells", [])
            if cells and cells[0].get("text") == "핵심 보장 내용":
                detail_row = row
                break

        # Determine structure for each insurer
        def detect_structure(cell_text: str) -> str:
            """Detect LIMIT or AMOUNT structure from cell text"""
            if not cell_text:
                return "UNKNOWN"

            text = cell_text.strip()

            # LIMIT indicators (priority)
            limit_keywords = ["보험기간 중", "지급 한도", "횟수", "회"]
            if any(kw in text for kw in limit_keywords):
                return "LIMIT"

            # AMOUNT indicators
            amount_keywords = ["만원", "천만원", "원"]
            if any(kw in text for kw in amount_keywords):
                return "AMOUNT"

            return "UNKNOWN"

        # Default to hardcoded if table detection fails (fallback)
        insurer1_structure = "AMOUNT"
        insurer2_structure = "LIMIT"

        if detail_row and len(detail_row.get("cells", [])) >= 3:
            # cells[0] = label, cells[1] = insurer1, cells[2] = insurer2
            insurer1_text = detail_row["cells"][1].get("text", "")
            insurer2_text = detail_row["cells"][2].get("text", "")

            insurer1_structure = detect_structure(insurer1_text)
            insurer2_structure = detect_structure(insurer2_text)

        # Build bubble based on detected structure
        if insurer1_structure == "LIMIT" and insurer2_structure == "AMOUNT":
            # Insurer1 = LIMIT, Insurer2 = AMOUNT
            lines = [
                f"{insurer1_display}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의되고,",
                f"{insurer2_display}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의됩니다.",
                "",
                "**즉,**",
                f"- {insurer1_display}: 지급 조건·횟수(한도) 기준",
                f"- {insurer2_display}: 지급 금액이 명확한 정액(보장금액) 기준"
            ]
        elif insurer1_structure == "AMOUNT" and insurer2_structure == "LIMIT":
            # Insurer1 = AMOUNT, Insurer2 = LIMIT
            lines = [
                f"{insurer1_display}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의되고,",
                f"{insurer2_display}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의됩니다.",
                "",
                "**즉,**",
                f"- {insurer1_display}: 지급 금액이 명확한 정액(보장금액) 기준",
                f"- {insurer2_display}: 지급 조건·횟수(한도) 기준"
            ]
        else:
            # Fallback: Both same structure or unknown (use original hardcoded)
            # This should rarely happen with proper data
            lines = [
                f"{insurer1_display}는 진단 시 정해진 금액(보장금액) 기준으로 보장이 정의되고,",
                f"{insurer2_display}는 보험기간 중 지급 횟수/한도 기준으로 보장이 정의됩니다.",
                "",
                "**즉,**",
                f"- {insurer1_display}: 지급 금액이 명확한 정액(보장금액) 기준",
                f"- {insurer2_display}: 지급 조건·횟수(한도) 기준"
            ]

        return "\n".join(lines)
