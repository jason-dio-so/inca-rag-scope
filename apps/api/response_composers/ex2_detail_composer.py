#!/usr/bin/env python3
"""
EX2_DETAIL Response Composer

STEP NEXT-86: Lock EX2_DETAIL response schema (담보 설명 전용 모드)

DESIGN:
1. Input: Single insurer slim card with KPI summary/condition
2. Output: EX2_DETAIL message dict with 4-section bubble_markdown
3. NO raw text in bubble (refs only)
4. Deterministic only (NO LLM)

CONSTITUTIONAL RULES:
- ❌ NO LLM usage
- ❌ NO comparison / recommendation / judgment
- ❌ NO coverage_code exposure (e.g., "A4200_1")
- ❌ NO raw text in bubble_markdown (DETAIL/EVIDENCE)
- ✅ refs MUST use PD:/EV: prefix
- ✅ "표현 없음" / "근거 없음" ONLY when structurally missing
- ✅ 4-section bubble_markdown (핵심요약, 보장요약, 조건요약, 근거안내)
"""

from typing import Dict, Any, List, Optional

from apps.api.response_composers.utils import (
    display_coverage_name,
    sanitize_no_coverage_code,
    format_insurer_name  # STEP NEXT-103
)


class EX2DetailComposer:
    """
    Compose EX2_DETAIL response from single insurer coverage data

    SSOT Schema: docs/ui/STEP_NEXT_86_EX2_LOCK.md
    """

    @staticmethod
    def compose(
        insurer: str,
        coverage_code: str,
        card_data: Dict[str, Any],
        coverage_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose EX2_DETAIL response (설명 전용, NO 비교/판단)

        Args:
            insurer: Insurer code (e.g., "samsung")
            coverage_code: Coverage code (e.g., "A4200_1")
            card_data: Single insurer card data
                {
                    "amount": "3000만원",
                    "premium": "명시 없음",
                    "period": "20년납/80세만기",
                    "payment_type": "정액형",
                    "proposal_detail_ref": "PD:samsung:A4200_1",
                    "evidence_refs": ["EV:samsung:A4200_1:01"],
                    "kpi_summary": {
                        "limit_summary": "3,000만원",
                        "payment_type": "정액형",
                        "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
                    },
                    "kpi_condition": {
                        "reduction_condition": "1년 미만 50%",
                        "waiting_period": "90일",
                        "exclusion_condition": "계약일 이전 발생 질병",
                        "renewal_condition": "비갱신형",
                        "condition_evidence_refs": ["EV:samsung:A4200_1:02"]
                    }
                }
            coverage_name: Coverage name (e.g., "암진단비(유사암 제외)")

        Returns:
            EX2_DETAIL message dict
        """
        # STEP NEXT-86: Get display-safe coverage name (NO code exposure)
        display_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        )

        # STEP NEXT-103: Get display-safe insurer name (NO code exposure)
        insurer_display = format_insurer_name(insurer)

        # Build title
        title = f"{insurer_display} {display_name} 설명"

        # Build summary bullets
        summary_bullets = [
            f"{insurer_display}의 {display_name}를 설명합니다",
            "가입설계서 기준 자료입니다"
        ]

        # Build bubble_markdown (4-section)
        # STEP NEXT-103: Pass insurer_display instead of code
        bubble_markdown = EX2DetailComposer._build_bubble_markdown(
            insurer_display, display_name, card_data
        )

        # Build sections
        sections = []

        # Section 1: KPI Summary (보장 요약)
        kpi_section = EX2DetailComposer._build_kpi_summary_section(card_data)
        if kpi_section:
            sections.append(kpi_section)

        # Section 2: KPI Condition (조건 요약)
        condition_section = EX2DetailComposer._build_kpi_condition_section(card_data)
        if condition_section:
            sections.append(condition_section)

        # Section 3: Evidence (근거 자료)
        evidence_section = EX2DetailComposer._build_evidence_section(
            insurer, display_name, card_data
        )
        if evidence_section:
            sections.append(evidence_section)

        # Build message dict
        message = {
            "kind": "EX2_DETAIL",
            "title": title,
            "summary_bullets": summary_bullets,
            "bubble_markdown": bubble_markdown,
            "sections": sections,
            "lineage": {
                "composer": "EX2DetailComposer",
                "deterministic": True,
                "llm_used": False
            }
        }

        return message

    @staticmethod
    def _translate_payment_type(payment_type: str) -> str:
        """
        Translate payment_type to Korean (STEP NEXT-86)

        Args:
            payment_type: English payment type (e.g., "LUMP_SUM")

        Returns:
            Korean payment type (e.g., "일시금")
        """
        type_map = {
            "LUMP_SUM": "정액형 (일시금)",
            "lump_sum": "정액형 (일시금)",
            "PER_DAY": "일당형",
            "per_day": "일당형",
            "PER_EVENT": "건별형",
            "per_event": "건별형",
            "ACTUAL_EXPENSE": "실손형",
            "actual_expense": "실손형",
            "UNKNOWN": "표현 없음",
            "unknown": "표현 없음"
        }
        return type_map.get(payment_type, payment_type)

    @staticmethod
    def _build_bubble_markdown(
        insurer_display: str,  # STEP NEXT-103: Changed from insurer code to display name
        display_name: str,
        card_data: Dict[str, Any]
    ) -> str:
        """
        Build 4-section bubble_markdown (STEP NEXT-86, STEP NEXT-103)

        Sections:
        1. 핵심 요약
        2. 보장 요약 (KPI Summary)
        3. 조건 요약 (KPI Condition)
        4. 근거 안내

        STEP NEXT-103: insurer_display is display name (e.g., "삼성화재"), NOT code

        Returns:
            Markdown string (NO raw text, refs only)
        """
        lines = []

        # Section 1: 핵심 요약
        lines.append("## 핵심 요약\n")
        lines.append(f"- **보험사**: {insurer_display}")
        lines.append(f"- **담보명**: {display_name}")
        lines.append("- **데이터 기준**: 가입설계서\n")

        # Section 2: 보장 요약 (KPI Summary)
        # STEP NEXT-96: Customer-first ordering (보장금액 최우선)
        lines.append("## 보장 요약\n")
        kpi_summary = card_data.get("kpi_summary", {})

        # STEP NEXT-96: Extract 보장금액 from card_data.amount (proposal_facts)
        amount = card_data.get("amount")  # e.g., "3000만원"

        limit_summary = kpi_summary.get("limit_summary") or "표현 없음"
        payment_type_raw = kpi_summary.get("payment_type") or "표현 없음"
        payment_type = EX2DetailComposer._translate_payment_type(payment_type_raw)
        kpi_refs = kpi_summary.get("kpi_evidence_refs", [])

        # STEP NEXT-96: 보장금액 우선 표시 (있을 경우)
        if amount and amount != "명시 없음":
            lines.append(f"- **보장금액**: {amount}")
            lines.append(f"  · 지급 조건: {display_name} 해당 시")

        # 보장한도 (횟수/기간 제한)
        lines.append(f"- **보장한도**: {limit_summary}")

        # 지급유형
        lines.append(f"- **지급유형**: {payment_type}")

        if kpi_refs:
            ref_str = kpi_refs[0]  # Use first ref
            lines.append(f"- **근거**: [근거 보기]({ref_str})\n")
        else:
            lines.append("- **근거**: 표현 없음\n")

        # Section 3: 조건 요약 (KPI Condition)
        lines.append("## 조건 요약\n")
        kpi_condition = card_data.get("kpi_condition", {})

        reduction = kpi_condition.get("reduction_condition") or "근거 없음"
        waiting = kpi_condition.get("waiting_period") or "근거 없음"
        exclusion = kpi_condition.get("exclusion_condition") or "근거 없음"
        renewal = kpi_condition.get("renewal_condition") or "근거 없음"
        condition_refs = kpi_condition.get("condition_evidence_refs", [])

        lines.append(f"- **감액**: {reduction}")
        if condition_refs and len(condition_refs) > 0:
            lines[-1] += f" ([근거 보기]({condition_refs[0]}))"

        lines.append(f"- **대기기간**: {waiting}")
        if condition_refs and len(condition_refs) > 1:
            lines[-1] += f" ([근거 보기]({condition_refs[1]}))"

        lines.append(f"- **면책**: {exclusion}")
        if condition_refs and len(condition_refs) > 2:
            lines[-1] += f" ([근거 보기]({condition_refs[2]}))"

        lines.append(f"- **갱신**: {renewal}\n")

        # Section 4: 근거 안내
        lines.append("## 근거 자료\n")
        lines.append("상세 근거는 \"근거 보기\" 링크를 클릭하시면 확인하실 수 있습니다.\n")

        # STEP NEXT-98/104: Question Continuity Hints (Demo Flow LOCK)
        # STEP NEXT-104: Fixed demo flow hints (NO dynamic text)
        # Flow: EX2_DETAIL (설명) → 메리츠는? (전환) → LIMIT_FIND (탐색)
        lines.append("---")
        lines.append("🔎 **다음으로 이런 질문도 해볼 수 있어요**\n")
        lines.append("- 메리츠는?")
        lines.append("- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘")

        markdown = "\n".join(lines)

        # STEP NEXT-86: Sanitize to remove any coverage_code exposure
        markdown = sanitize_no_coverage_code(markdown)

        return markdown

    @staticmethod
    def _build_kpi_summary_section(card_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build KPI Summary section (보장 요약)

        Returns:
            CommonNotesSection dict or None
        """
        kpi_summary = card_data.get("kpi_summary")
        if not kpi_summary:
            return None

        bullets = []

        limit_summary = kpi_summary.get("limit_summary")
        if limit_summary:
            bullets.append(f"보장한도: {limit_summary}")

        payment_type_raw = kpi_summary.get("payment_type")
        if payment_type_raw:
            payment_type = EX2DetailComposer._translate_payment_type(payment_type_raw)
            bullets.append(f"지급유형: {payment_type}")

        kpi_refs = kpi_summary.get("kpi_evidence_refs", [])
        if kpi_refs:
            ref_str = ", ".join(kpi_refs)
            bullets.append(f"근거: {ref_str}")

        if not bullets:
            return None

        return {
            "kind": "common_notes",
            "title": "보장 요약",
            "bullets": bullets
        }

    @staticmethod
    def _build_kpi_condition_section(card_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build KPI Condition section (조건 요약)

        Returns:
            CommonNotesSection dict or None
        """
        kpi_condition = card_data.get("kpi_condition")
        if not kpi_condition:
            return None

        bullets = []
        condition_refs = kpi_condition.get("condition_evidence_refs", [])
        ref_idx = 0

        reduction = kpi_condition.get("reduction_condition")
        if reduction:
            ref_str = f" ({condition_refs[ref_idx]})" if ref_idx < len(condition_refs) else ""
            bullets.append(f"감액: {reduction}{ref_str}")
            if ref_idx < len(condition_refs):
                ref_idx += 1

        waiting = kpi_condition.get("waiting_period")
        if waiting:
            ref_str = f" ({condition_refs[ref_idx]})" if ref_idx < len(condition_refs) else ""
            bullets.append(f"대기기간: {waiting}{ref_str}")
            if ref_idx < len(condition_refs):
                ref_idx += 1

        exclusion = kpi_condition.get("exclusion_condition")
        if exclusion:
            ref_str = f" ({condition_refs[ref_idx]})" if ref_idx < len(condition_refs) else ""
            bullets.append(f"면책: {exclusion}{ref_str}")
            if ref_idx < len(condition_refs):
                ref_idx += 1

        renewal = kpi_condition.get("renewal_condition")
        if renewal:
            bullets.append(f"갱신: {renewal}")

        if not bullets:
            return None

        return {
            "kind": "common_notes",
            "title": "조건 요약",
            "bullets": bullets
        }

    @staticmethod
    def _build_evidence_section(
        insurer: str,
        display_name: str,
        card_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build Evidence section (근거 자료, lazy-load)

        Returns:
            EvidenceAccordionSection dict or None
        """
        proposal_detail_ref = card_data.get("proposal_detail_ref")
        evidence_refs = card_data.get("evidence_refs", [])

        items = []

        # Add proposal detail ref as first item
        if proposal_detail_ref:
            items.append({
                "evidence_ref_id": proposal_detail_ref,
                "insurer": insurer,
                "coverage_name": display_name,
                "doc_type": "가입설계서",
                "page": None,  # Unknown at this stage
                "snippet": None  # Lazy-load
            })

        # Add evidence refs
        for idx, ref in enumerate(evidence_refs):
            items.append({
                "evidence_ref_id": ref,
                "insurer": insurer,
                "coverage_name": display_name,
                "doc_type": "약관/사업방법서",  # Generic
                "page": None,
                "snippet": None  # Lazy-load
            })

        if not items:
            return None

        return {
            "kind": "evidence_accordion",
            "title": "근거 자료",
            "items": items
        }
