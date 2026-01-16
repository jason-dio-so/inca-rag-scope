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
        Build bubble_markdown (STEP NEXT-113: ChatGPT conversational UX)

        STEP NEXT-113 REDESIGN:
        - Left bubble = Conversational summary ONLY (lightweight, 2-3 sentences max)
        - Right panel = All detailed info (tables, conditions, evidence)
        - NO duplication between bubble and sections
        - NO tables/lists/conditions in bubble
        - Feels like "conversation start", NOT a document

        Structure (LOCKED):
        - Product Header (보험사 · 담보명 · 기준)
        - Core explanation (1-2 sentences, what this coverage is)
        - Key characteristic (1 sentence, how it works)
        - Condition note (1 sentence, "조건이 적용됩니다" - NO specifics)
        - Question hints (demo flow LOCK)

        STEP NEXT-103: insurer_display is display name (e.g., "삼성화재"), NOT code
        STEP NEXT-110A: Product header at top (without product_name data)

        Returns:
            Markdown string (NO raw text, refs only)
        """
        lines = []

        # STEP NEXT-110A: Product Header (fixed at top, marked for frontend styling)
        lines.append("<!-- PRODUCT_HEADER -->")
        lines.append(f"**{insurer_display}**")
        lines.append(f"**{display_name}**")
        lines.append("_기준: 가입설계서_\n")
        lines.append("---")
        lines.append("<!-- /PRODUCT_HEADER -->\n")

        # STEP NEXT-113: Conversational summary (lightweight ONLY)
        # Build 2-3 sentence summary based on available data
        kpi_summary = card_data.get("kpi_summary", {})
        kpi_condition = card_data.get("kpi_condition", {})

        # Extract key info for conversational summary
        amount = card_data.get("amount")  # e.g., "3000만원"
        payment_type_raw = kpi_summary.get("payment_type") or "UNKNOWN"
        payment_type_kr = EX2DetailComposer._translate_payment_type(payment_type_raw)

        # Sentence 1: What this coverage is (보장 정의)
        lines.append(f"이 담보는 {display_name}에 해당할 때 보장합니다.\n")

        # Sentence 2: How it works (핵심 특징)
        if amount and amount != "명시 없음":
            lines.append(f"정액으로 {amount}을 지급하는 방식입니다.\n")
        elif payment_type_kr != "표현 없음":
            lines.append(f"{payment_type_kr} 방식으로 보장이 이루어집니다.\n")
        else:
            lines.append("보장 방식은 가입설계서를 참고하시면 됩니다.\n")

        # Sentence 3: Condition note (일반적 안내, NO specifics)
        has_reduction = kpi_condition.get("reduction_condition") and kpi_condition.get("reduction_condition") != "근거 없음"
        has_waiting = kpi_condition.get("waiting_period") and kpi_condition.get("waiting_period") != "근거 없음"
        has_exclusion = kpi_condition.get("exclusion_condition") and kpi_condition.get("exclusion_condition") != "근거 없음"

        if has_reduction or has_waiting or has_exclusion:
            lines.append("→ 감액, 대기기간 등 주요 조건이 적용됩니다.\n")
        else:
            lines.append("→ 상세 조건은 오른쪽 패널에서 확인하실 수 있습니다.\n")

        # STEP NEXT-115: Comparison transition line (EX2 → EX3 flow)
        # This line naturally guides users toward comparison without recommendation
        lines.append(f"같은 {display_name}라도 보험사마다 '보장을 정의하는 기준'이 달라,")
        lines.append("비교해 보면 구조 차이가 더 분명해집니다.\n")

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

        STEP NEXT-113: Right panel = drill-down ONLY
        - All detailed info (amounts, limits, payment types)
        - STEP NEXT-96: Customer-first ordering (보장금액 first)

        Returns:
            CommonNotesSection dict or None
        """
        kpi_summary = card_data.get("kpi_summary")
        if not kpi_summary:
            return None

        bullets = []

        # STEP NEXT-96/113: 보장금액 최우선 (customer-first)
        amount = card_data.get("amount")  # e.g., "3000만원"
        if amount and amount != "명시 없음":
            bullets.append(f"보장금액: {amount}")

        # 보장한도 (횟수/기간 제한)
        limit_summary = kpi_summary.get("limit_summary")
        if limit_summary:
            bullets.append(f"보장한도: {limit_summary}")

        # 지급유형
        payment_type_raw = kpi_summary.get("payment_type")
        if payment_type_raw:
            payment_type = EX2DetailComposer._translate_payment_type(payment_type_raw)
            bullets.append(f"지급유형: {payment_type}")

        # 근거 (for drill-down)
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
