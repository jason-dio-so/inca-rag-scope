#!/usr/bin/env python3
"""
EX4_ELIGIBILITY Response Composer — STEP NEXT-130: O/X Table Lock

STEP NEXT-130: Customer Self-Test Flow — O/X Eligibility Table

PURPOSE:
Show disease subtype (제자리암/경계성종양) eligibility as simple O/X table
for 2 insurers (samsung, meritz) across 5 fixed categories.

DESIGN:
1. Fixed 5 rows: 진단비 / 수술비 / 항암약물 / 표적항암 / 다빈치수술
2. O/X only (NO △/Unknown/조건부/부분지급)
3. Deterministic keyword matching (NO LLM)
4. Left bubble: 2-4 sentences (short guidance)
5. Right panel: O/X table + notes

CONSTITUTIONAL RULES (STEP NEXT-129R):
- ❌ NO LLM usage
- ❌ NO recommendation/judgment/superiority claims
- ❌ NO △/Unknown in cells (O or X only)
- ❌ NO auto-complete/forced routing
- ❌ NO coverage_code UI exposure
- ✅ View layer ONLY (no pipeline/data/search changes)
- ✅ Deterministic keyword matching ONLY
- ✅ Display names ONLY (삼성화재, 메리츠화재)
- ✅ Evidence refs attached to cells/rows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from apps.api.response_composers.utils import (
    display_coverage_name,
    sanitize_no_coverage_code,
    format_insurer_name
)


class EX4EligibilityComposer:
    """
    Compose EX4_ELIGIBILITY response with fixed O/X table

    SSOT Schema: STEP NEXT-130 specification
    """

    # Fixed 5 categories (locked)
    FIXED_CATEGORIES = [
        "진단비",
        "수술비",
        "항암약물",
        "표적항암",
        "다빈치수술"
    ]

    # Category keyword mappings (deterministic)
    CATEGORY_KEYWORDS = {
        "진단비": ["진단", "진단비"],
        "수술비": ["수술", "수술비"],
        "항암약물": ["항암", "약물", "항암약물", "화학", "화학요법"],
        "표적항암": ["표적", "표적항암", "표적치료"],
        "다빈치수술": ["다빈치", "로봇", "로봇수술"]
    }

    @staticmethod
    def compose(
        insurers: List[str],
        subtype_keyword: str,
        coverage_cards: List[Dict[str, Any]],
        query_focus_terms: Optional[List[str]] = None,
        coverage_name: Optional[str] = None,
        coverage_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compose EX4_ELIGIBILITY response with O/X table

        Args:
            insurers: List of insurer codes (e.g., ["samsung", "meritz"])
            subtype_keyword: Disease subtype (e.g., "제자리암", "경계성종양")
            coverage_cards: List of coverage card dicts (from coverage_cards.jsonl)
            query_focus_terms: Optional list of focus terms from user query
            coverage_name: Optional coverage name for context
            coverage_code: Optional coverage code (used for display_coverage_name, NEVER exposed)

        Returns:
            EX4_ELIGIBILITY message dict
        """
        # STEP NEXT-130: Fixed 2 insurers (samsung, meritz)
        # If different insurers provided, use first 2 only
        if not insurers or len(insurers) < 2:
            insurers = ["samsung", "meritz"]
        else:
            insurers = insurers[:2]

        # Get display-safe coverage name (NO code exposure)
        display_name = display_coverage_name(
            coverage_name=coverage_name,
            coverage_code=coverage_code
        ) if (coverage_name or coverage_code) else None

        # Build title
        title = f"{subtype_keyword} 보장 가능 여부"

        # Build summary bullets
        summary_bullets = [
            f"{subtype_keyword}에 대한 보장 가능 여부를 확인했습니다",
            "표에서 O/X로 확인하세요"
        ]

        # Build sections
        sections = []

        # Section 1: O/X Eligibility Table (required)
        table_section = EX4EligibilityComposer._build_ox_table_section(
            insurers, subtype_keyword, coverage_cards
        )
        sections.append(table_section)

        # Section 2: Notes (guidance-only)
        notes_section = EX4EligibilityComposer._build_notes_section(subtype_keyword)
        sections.append(notes_section)

        # Build bubble markdown (2-4 sentences)
        bubble_markdown = EX4EligibilityComposer._build_bubble_markdown(
            subtype_keyword, display_name
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
            "bubble_markdown": bubble_markdown,
            "lineage": {
                "handler": "EX4EligibilityComposer",
                "llm_used": False,
                "deterministic": True,
                "step_next": "130"
            }
        }

        # Final sanitization pass (constitutional enforcement)
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
    def _build_ox_table_section(
        insurers: List[str],
        subtype_keyword: str,
        coverage_cards: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build O/X eligibility table section

        Fixed structure:
        - Columns: ["비교 항목", "{Insurer1 Display Name}", "{Insurer2 Display Name}"]
        - Rows: 5 fixed categories (진단비, 수술비, 항암약물, 표적항암, 다빈치수술)
        - Cell values: "O" or "X" only (NO △/Unknown)

        Args:
            insurers: List of 2 insurer codes
            subtype_keyword: Disease subtype (e.g., "제자리암")
            coverage_cards: List of coverage card dicts

        Returns:
            comparison_table section dict
        """
        # Build column headers (use display names)
        insurer_display_names = [format_insurer_name(ins) for ins in insurers]
        columns = ["비교 항목"] + insurer_display_names

        rows = []

        # Build 5 fixed rows
        for category in EX4EligibilityComposer.FIXED_CATEGORIES:
            # Determine O/X for each insurer
            cells = [{"text": category}]  # First cell: category label
            row_refs = []

            for insurer in insurers:
                ox_status, refs = EX4EligibilityComposer._determine_ox_status(
                    insurer, category, subtype_keyword, coverage_cards
                )
                cells.append({"text": ox_status})
                row_refs.extend(refs)

            # Build row with meta
            row = {
                "cells": cells,
                "is_header": False,
                "meta": {
                    "evidence_refs": row_refs if row_refs else None
                }
            }
            rows.append(row)

        return {
            "kind": "comparison_table",
            "table_kind": "ELIGIBILITY_OX_TABLE",
            "title": f"{subtype_keyword} 보장 가능 여부",
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def _determine_ox_status(
        insurer: str,
        category: str,
        subtype_keyword: str,
        coverage_cards: List[Dict[str, Any]]
    ) -> tuple[str, List[str]]:
        """
        Determine O/X status for a specific insurer + category + subtype

        Rules:
        - O: Found 1+ coverage card matching category keywords + subtype_keyword
        - X: No matching coverage card
        - NO △/Unknown allowed (simplification for self-test)

        Args:
            insurer: Insurer code (e.g., "samsung")
            category: Category name (e.g., "진단비")
            subtype_keyword: Disease subtype (e.g., "제자리암")
            coverage_cards: List of coverage card dicts

        Returns:
            (status, refs) where status ∈ {"O", "X"}, refs = List of PD: refs
        """
        category_keywords = EX4EligibilityComposer.CATEGORY_KEYWORDS.get(category, [])

        # Filter cards: match insurer + category keywords
        matching_cards = []
        for card in coverage_cards:
            if card.get("insurer") != insurer:
                continue

            # Check if coverage_name_raw contains category keywords
            coverage_name_raw = card.get("coverage_name_raw", "").lower()
            coverage_code = card.get("coverage_code", "")

            # Match category keywords
            category_match = any(kw in coverage_name_raw for kw in category_keywords)
            if not category_match:
                continue

            # Check if subtype_keyword appears in evidences
            # (simplified: check proposal_facts or evidences)
            evidences = card.get("evidences", [])
            proposal_facts = card.get("proposal_facts", {})

            subtype_match = False

            # Check proposal_facts evidence
            proposal_evidences = proposal_facts.get("evidences", [])
            for ev in proposal_evidences:
                snippet = ev.get("snippet", "")
                if subtype_keyword in snippet:
                    subtype_match = True
                    break

            # Check main evidences
            if not subtype_match:
                for ev in evidences:
                    snippet = ev.get("snippet", "")
                    if subtype_keyword in snippet:
                        subtype_match = True
                        break

            if category_match and subtype_match:
                matching_cards.append(card)

        # Determine status
        if len(matching_cards) > 0:
            # Extract refs (PD: format)
            refs = []
            for card in matching_cards[:3]:  # Limit to 3 refs
                insurer_code = card.get("insurer", "")
                coverage_code = card.get("coverage_code", "")
                if insurer_code and coverage_code:
                    refs.append(f"PD:{insurer_code}:{coverage_code}")

            return ("O", refs)
        else:
            return ("X", [])

    @staticmethod
    def _build_notes_section(subtype_keyword: str) -> Dict[str, Any]:
        """
        Build notes section (guidance-only)

        Rules:
        - NO recommendation
        - NO judgment
        - Simple clarification bullets (2-3)
        """
        return {
            "kind": "common_notes",
            "title": "유의사항",
            "bullets": [
                "O: 보장 가능, X: 보장 제외",
                "가입설계서 및 약관 기준입니다",
                "실제 보장 여부는 약관을 직접 확인하시기 바랍니다"
            ],
            "groups": None
        }

    @staticmethod
    def _build_bubble_markdown(
        subtype_keyword: str,
        coverage_display_name: Optional[str] = None
    ) -> str:
        """
        Build bubble_markdown for central chat bubble (2-4 sentences)

        Rules (Constitutional):
        - NO LLM usage (deterministic only)
        - NO recommendation/judgment
        - NO raw text (refs only)
        - NO coverage_code exposure
        - 2-4 sentences ONLY

        Format (LOCKED):
        1. Query intent (1 sentence)
        2. Guidance to check table (1 sentence)
        3. Optional: clarification (1 sentence)

        Args:
            subtype_keyword: Disease subtype (e.g., "제자리암")
            coverage_display_name: Optional coverage name for context (NO code exposure)
        """
        lines = []

        # Sentence 1: Query intent
        if coverage_display_name:
            lines.append(f"{coverage_display_name} 중 **{subtype_keyword}** 보장 가능 여부를 확인했습니다.")
        else:
            lines.append(f"**{subtype_keyword}** 보장 가능 여부를 확인했습니다.")

        lines.append("")

        # Sentence 2: Guidance
        lines.append("표에서 **O/X**로 확인하세요.")
        lines.append("O는 보장 가능, X는 보장 제외입니다.")

        return "\n".join(lines)
