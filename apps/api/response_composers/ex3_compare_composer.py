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

from apps.api.utils.amount_formatter import format_amount_korean  # STEP NEXT-139D
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

        # STEP NEXT-138-γ: Section 2.5: 보장 한도 (LIMIT info - separate from main table)
        limit_section = EX3CompareComposer._build_limit_section(insurers, comparison_data, display_name)
        if limit_section:
            sections.append(limit_section)

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
    def _tag_dimension(amount: str, limit: Optional[str]) -> str:
        """
        STEP NEXT-138-γ: Tag dimension (AMOUNT/LIMIT/MIXED)

        This is for EXAM3 dimension separation ONLY.
        DO NOT use in EXAM2 (탐색 전용).

        Rules:
        - AMOUNT: Has amount, NO limit
        - LIMIT: Has limit, NO amount
        - MIXED: Has both amount AND limit

        Returns:
            "AMOUNT" | "LIMIT" | "MIXED"
        """
        has_amount = amount and amount != "명시 없음"
        has_limit = limit and limit.strip()

        if has_amount and has_limit:
            return "MIXED"
        elif has_amount:
            return "AMOUNT"
        elif has_limit:
            return "LIMIT"
        else:
            return "AMOUNT"  # Default to AMOUNT dimension (fallback)

    @staticmethod
    def _build_table_section(
        insurers: List[str],
        comparison_data: Dict[str, Any],
        coverage_name: str
    ) -> Dict[str, Any]:
        """
        Build comparison table section

        STEP NEXT-138-γ: AMOUNT/LIMIT Dimension Separation (EXAM3 ONLY)
        - Main table shows ONLY AMOUNT (핵심 보장 내용 = 정액금액)
        - LIMIT goes to separate section (보장 한도)
        - NO mixing AMOUNT and LIMIT in same row

        STEP NEXT-127: Per-Insurer Cells + Meta (preserved)
        - Per-insurer cells: Each insurer has own meta
        - NO shared refs across insurers

        Rules:
        - Columns: ["비교 항목", insurer1_display, insurer2_display]
        - Rows: 보장 정의 기준, 핵심 보장 내용 (AMOUNT ONLY), 지급유형
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

        # STEP NEXT-138-γ: Dimension tagging (EXAM3 ONLY)
        dim1 = EX3CompareComposer._tag_dimension(amount1, limit1)
        dim2 = EX3CompareComposer._tag_dimension(amount2, limit2)

        # STEP NEXT-138-γ: Determine structural basis (AMOUNT-first)
        def get_definition_basis(dim: str) -> str:
            """
            Get structural basis from dimension tag

            STEP NEXT-138-γ: AMOUNT-first rule
            - AMOUNT or MIXED → "보장금액(정액) 기준"
            - LIMIT → "지급 한도/횟수 기준"
            """
            if dim in ("AMOUNT", "MIXED"):
                return "보장금액(정액) 기준"
            elif dim == "LIMIT":
                return "지급 한도/횟수 기준"
            else:
                return "표현 없음"

        basis1 = get_definition_basis(dim1)
        basis2 = get_definition_basis(dim2)

        # Build rows
        rows = []

        # Row 1: 보장 정의 기준 (ALWAYS - STEP NEXT-138-γ: AMOUNT-first)
        rows.append({
            "cells": [
                {"text": "보장 정의 기준"},
                {"text": basis1, "meta": meta1},  # STEP NEXT-127: Per-cell meta
                {"text": basis2, "meta": meta2}   # STEP NEXT-127: Per-cell meta
            ],
            "is_header": False
        })

        # STEP NEXT-139D: Format amount display (unified Korean formatter)
        def format_amount_display(amount: str, payment_type: str) -> str:
            """
            Format amount display text (STEP NEXT-139D)

            Rules:
            - ALL amounts → Korean abbreviated format (3천만원, 2만원)
            - 일당형: "일당 {amount}"
            - 정액형: "{amount}"
            - Uses unified formatter (NO individual logic)
            """
            if amount == "명시 없음":
                return "명시 없음"

            # STEP NEXT-139D: Use unified Korean formatter
            korean_amount = format_amount_korean(amount)

            # Add prefix for 일당형
            if payment_type == "일당형":
                if not korean_amount.startswith("일당"):
                    return f"일당 {korean_amount}"
                return korean_amount

            # Default: return formatted amount (정액형 or other types)
            return korean_amount

        # Row 2: 핵심 보장 내용 (STEP NEXT-138-γ: AMOUNT ONLY)
        # RULE: Show AMOUNT, NOT limit (limit goes to separate section)
        # Exception: If NO amount exists for ALL insurers, fallback to limit
        has_any_amount = (amount1 != "명시 없음") or (amount2 != "명시 없음")

        if has_any_amount:
            # STEP NEXT-139D: Apply unified Korean amount formatting
            amount1_display = format_amount_display(amount1, payment1)
            amount2_display = format_amount_display(amount2, payment2)

            # AMOUNT-first: Show amount (even if "명시 없음" for some insurers)
            rows.append({
                "cells": [
                    {"text": "핵심 보장 내용"},
                    {"text": amount1_display, "meta": meta1},
                    {"text": amount2_display, "meta": meta2}
                ],
                "is_header": False
            })
        else:
            # Fallback: NO amount exists → show limit as핵심 보장 내용
            # This case triggers summary bullet warning
            limit1_display = limit1 if limit1 else "표현 없음"
            limit2_display = limit2 if limit2 else "표현 없음"
            rows.append({
                "cells": [
                    {"text": "핵심 보장 내용"},
                    {"text": limit1_display, "meta": meta1},
                    {"text": limit2_display, "meta": meta2}
                ],
                "is_header": False
            })

        # Row 3: 지급유형 (ALWAYS)
        # STEP NEXT-139C: Format payment_type for display (NO raw enum values)
        def format_payment_type(payment_type: str) -> str:
            """
            Format payment_type for EX3 display
            Maps raw enum values to Korean labels
            """
            label_map = {
                "LUMP_SUM": "정액 지급",
                "일당형": "일당 지급",
                "건별형": "건별 지급",
                "실손형": "실손 지급",
                "UNKNOWN": "표현 없음"
            }
            return label_map.get(payment_type, payment_type)  # Fallback to original if not in map

        payment1_display = format_payment_type(payment1)
        payment2_display = format_payment_type(payment2)

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
    def _build_limit_section(
        insurers: List[str],
        comparison_data: Dict[str, Any],
        coverage_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        STEP NEXT-138-γ: Build separate LIMIT section (보장 한도)

        This section shows LIMIT info that was separated from main table.
        Only shown if AT LEAST ONE insurer has limit info.

        Rules:
        - Show limit_summary from kpi_summary
        - Same side-by-side format as main table
        - NO mixing with AMOUNT (already in main table)

        Returns:
            Section dict or None (if no limit info exists)
        """
        insurer1, insurer2 = insurers[0], insurers[1]
        insurer1_display = format_insurer_name(insurer1)
        insurer2_display = format_insurer_name(insurer2)

        # Extract limit info
        data1 = comparison_data.get(insurer1, {})
        data2 = comparison_data.get(insurer2, {})

        kpi1 = data1.get("kpi_summary", {}) or {}
        kpi2 = data2.get("kpi_summary", {}) or {}

        limit1 = kpi1.get("limit_summary")
        limit2 = kpi2.get("limit_summary")
        amount1 = data1.get("amount", "명시 없음")
        amount2 = data2.get("amount", "명시 없음")
        payment1 = data1.get("payment_type", "UNKNOWN")  # STEP NEXT-139B
        payment2 = data2.get("payment_type", "UNKNOWN")  # STEP NEXT-139B

        # CRITICAL SEMANTIC FIX: LIMIT section visibility logic
        # RULE: LIMIT section should ONLY show when LIMIT is PRIMARY structural definition
        #
        # DON'T show if:
        # 1. NO limits exist (both insurers AMOUNT-DRIVEN or no data)
        # 2. Coverage is AMOUNT-DRIVEN (both insurers use amount as primary structure)
        #
        # Current heuristic: If both insurers have NO meaningful limit, don't show section
        # "Meaningful limit" = NOT just frequency constraint like "최초 1회한"
        #
        # TODO: This is a HEURISTIC. True semantic classification requires
        # understanding whether limit is PRIMARY vs SECONDARY definition.
        if not limit1 and not limit2:
            return None

        # CRITICAL SEMANTIC FIX (STEP NEXT-140-γ):
        # If one insurer is AMOUNT-DRIVEN (no limit) and other has ONLY frequency constraint,
        # DON'T show LIMIT section (it's not a structural difference)
        #
        # Frequency constraint patterns: "최초 1회", "보험기간 중 1회", "1회한"
        # These are SECONDARY constraints, not PRIMARY structural definitions
        def is_frequency_constraint_only(limit_text: Optional[str]) -> bool:
            """Check if limit is just a frequency constraint (not primary structure)"""
            if not limit_text:
                return False
            # Frequency patterns (Korean)
            freq_patterns = ["최초", "회한", "회 한", "보험기간 중", "1회", "2회", "3회"]
            return any(pattern in limit_text for pattern in freq_patterns)

        limit1_is_freq = is_frequency_constraint_only(limit1)
        limit2_is_freq = is_frequency_constraint_only(limit2)

        # If BOTH have ONLY frequency constraints (no amount difference),
        # LIMIT section adds no value → DON'T SHOW
        # Example: Samsung "최초 1회", Meritz "최초 1회" → NO LIMIT section
        if limit1_is_freq and limit2_is_freq:
            # Check if they're the SAME constraint (no difference)
            if limit1 == limit2:
                return None  # Same frequency = no structural difference

        # If ONE has ONLY frequency constraint and OTHER has NO limit,
        # this suggests AMOUNT-DRIVEN coverage → DON'T SHOW LIMIT section
        # Example: Samsung "최초 1회", Meritz None → Both are AMOUNT-DRIVEN (암진단비 case)
        if (limit1_is_freq and not limit2) or (limit2_is_freq and not limit1):
            return None  # Frequency + None = AMOUNT-DRIVEN structure, NO LIMIT section

        # Build row meta
        meta1 = EX3CompareComposer._build_row_meta(data1)
        meta2 = EX3CompareComposer._build_row_meta(data2)

        # CRITICAL FIX: Format limit display (LIMIT ONLY, NO AMOUNT FALLBACK)
        def format_limit_display(limit: Optional[str]) -> str:
            """
            Format limit display text (CRITICAL FIX)

            ABSOLUTE RULES:
            1. LIMIT exists → show limit
            2. LIMIT missing → "한도: 명시 없음"
            3. ❌ FORBIDDEN: Show AMOUNT in LIMIT cells
            4. ❌ FORBIDDEN: "(보장금액: ...)" in LIMIT section
            5. LIMIT = LIMIT ONLY (NO dimension mixing)
            """
            if limit and limit.strip():
                return limit
            else:
                return "한도: 명시 없음"

        # Build table
        columns = ["항목", insurer1_display, insurer2_display]
        limit1_display = format_limit_display(limit1)
        limit2_display = format_limit_display(limit2)

        rows = [{
            "cells": [
                {"text": "보장 한도"},
                {"text": limit1_display, "meta": meta1},
                {"text": limit2_display, "meta": meta2}
            ],
            "is_header": False
        }]

        return {
            "kind": "comparison_table",
            "table_kind": "LIMIT_INFO",
            "title": f"{coverage_name} 보장 한도",
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
        Build bubble_markdown for central chat bubble

        CRITICAL FIX (STEP NEXT-141):
        EX3 bubble = STRUCTURE CONFIRMATION (NOT comparison)

        ABSOLUTE RULES:
        - ❌ FORBIDDEN: "삼성은 A, 메리츠는 B" (comparison format)
        - ❌ FORBIDDEN: Insurer-specific differences in bubble
        - ❌ FORBIDDEN: EXAM2 exploration-style comparison logic
        - ✅ REQUIRED: "두 보험사는 모두 [구조] 입니다" (unified structure)
        - ✅ REQUIRED: PRIMARY structure confirmation ONLY

        EX3 Purpose:
        - Confirm the PRIMARY structural basis that applies to ALL insurers
        - Table shows detailed differences, bubble shows CONFIRMED structure

        Args:
            insurers: List of insurer codes (for indexing)
            insurer_display_names: List of insurer display names (for UI output)
            display_name: Display-safe coverage name (NOT used in bubble)
            comparison_data: Dict with insurer comparison data (NOT used - table is SSOT)
            table_section: comparison_table section (SSOT for structure detection)
        """
        # STEP NEXT-141: Detect PRIMARY structure from TABLE
        # Extract "보장 정의 기준" row (PRIMARY structural basis)
        rows = table_section.get("rows", [])

        # Find "보장 정의 기준" row
        basis_row = None
        for row in rows:
            cells = row.get("cells", [])
            if cells and cells[0].get("text") == "보장 정의 기준":
                basis_row = row
                break

        # Determine PRIMARY structure (AMOUNT-DRIVEN or LIMIT-DRIVEN)
        def determine_primary_structure(basis_text: str) -> str:
            """Determine if PRIMARY structure is AMOUNT or LIMIT"""
            if not basis_text:
                return "UNKNOWN"

            # AMOUNT-DRIVEN keywords
            if "보장금액" in basis_text or "정액" in basis_text:
                return "AMOUNT"
            # LIMIT-DRIVEN keywords
            elif "한도" in basis_text or "횟수" in basis_text:
                return "LIMIT"
            else:
                return "UNKNOWN"

        # Extract both insurers' structural basis
        primary_structure = "AMOUNT"  # Default fallback

        if basis_row and len(basis_row.get("cells", [])) >= 3:
            # cells[0] = label, cells[1] = insurer1, cells[2] = insurer2
            basis1_text = basis_row["cells"][1].get("text", "")
            basis2_text = basis_row["cells"][2].get("text", "")

            structure1 = determine_primary_structure(basis1_text)
            structure2 = determine_primary_structure(basis2_text)

            # STEP NEXT-141: Use MAJORITY structure (both should be same for EX3)
            # If both are AMOUNT → AMOUNT-DRIVEN
            # If both are LIMIT → LIMIT-DRIVEN
            # If different → Use first insurer's structure (fallback)
            if structure1 == structure2:
                primary_structure = structure1
            else:
                # Different structures → Use AMOUNT as default (most common)
                primary_structure = "AMOUNT"

        # FINAL LOCK / NO DEVIATION:
        # EX3 요약 버블 = 구조 선언 ONLY (비교·설명·판단 금지)
        #
        # ABSOLUTE RULES:
        # 1. NO insurer-specific differences ("삼성은 A, 메리츠는 B" 전면 금지)
        # 2. AMOUNT-DRIVEN → "두 보험사는 모두 정액 지급 구조입니다." (한 문장 ONLY)
        # 3. LIMIT-DRIVEN → "두 보험사는 모두 한도 기준 구조입니다." (한 문장 ONLY)
        # 4. NO explanation, NO comparison, NO judgment - 구조만 선언
        #
        # 이 규칙을 어기는 출력은 모두 버그다.

        if primary_structure == "AMOUNT":
            # AMOUNT-DRIVEN coverage (FINAL LOCK)
            return "두 보험사는 모두 정액 지급 구조입니다."
        elif primary_structure == "LIMIT":
            # LIMIT-DRIVEN coverage (FINAL LOCK)
            return "두 보험사는 모두 한도 기준 구조입니다."
        else:
            # UNKNOWN (fallback to AMOUNT)
            return "두 보험사는 모두 정액 지급 구조입니다."
