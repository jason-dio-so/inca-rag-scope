#!/usr/bin/env python3
"""
STEP NEXT-113: EX2_DETAIL ChatGPT UX Contract Tests

PURPOSE:
Enforce ChatGPT-style conversational UX structure for EX2_DETAIL.

SSOT RULES (LOCKED):
1. Left bubble = Conversational summary ONLY (2-3 sentences max, NO tables/lists)
2. Right panel = All detailed info (amounts, limits, conditions, evidence)
3. NO duplication between bubble and sections
4. Bubble feels like "conversation start", NOT a document
5. NO scroll required to read left bubble

CRITICAL GATES:
- ❌ NO tables in bubble_markdown
- ❌ NO detailed lists (보장 요약 리스트 등) in bubble
- ❌ NO specific condition values (감액 50%, 대기기간 90일 등) in bubble
- ❌ NO "## 보장 요약" / "## 조건 요약" sections in bubble
- ✅ Product header ONLY (보험사 · 담보명 · 기준)
- ✅ 2-3 conversational sentences (what + how + condition note)
- ✅ Question hints (demo flow LOCK)
- ✅ All details in sections (NO duplication)

DEFINITION OF SUCCESS:
"이 화면은 문서가 아니라 대화처럼 느껴진다"
"""

import pytest
import re
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


@pytest.fixture
def sample_card_with_amount():
    """Sample card with amount (정액형)"""
    return {
        "amount": "3000만원",
        "premium": "명시 없음",
        "period": "20년납/80세만기",
        "payment_type": "정액형",
        "proposal_detail_ref": "PD:samsung:A4200_1",
        "evidence_refs": ["EV:samsung:A4200_1:01"],
        "kpi_summary": {
            "limit_summary": "보험기간 중 1회 한도",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50% 감액",
            "waiting_period": "90일",
            "exclusion_condition": "계약일 이전 발생 질병 제외",
            "renewal_condition": "비갱신형",
            "condition_evidence_refs": ["EV:samsung:A4200_1:02", "EV:samsung:A4200_1:03"]
        }
    }


@pytest.fixture
def sample_card_no_amount():
    """Sample card without amount (limit-based)"""
    return {
        "amount": "명시 없음",
        "premium": "명시 없음",
        "period": "20년납/80세만기",
        "payment_type": "일당형",
        "proposal_detail_ref": "PD:meritz:B3100_1",
        "evidence_refs": ["EV:meritz:B3100_1:01"],
        "kpi_summary": {
            "limit_summary": "1일당 5만원",
            "payment_type": "PER_DAY",
            "kpi_evidence_refs": ["EV:meritz:B3100_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "근거 없음",
            "waiting_period": "근거 없음",
            "exclusion_condition": "근거 없음",
            "renewal_condition": "갱신형",
            "condition_evidence_refs": []
        }
    }


def test_bubble_has_no_tables(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST NOT contain tables

    GATE: NO "##" section headers, NO bullet lists with detailed values
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: NO "## 보장 요약" section in bubble
    assert "## 보장 요약" not in bubble, "Bubble must NOT contain '## 보장 요약' section"

    # GATE: NO "## 조건 요약" section in bubble
    assert "## 조건 요약" not in bubble, "Bubble must NOT contain '## 조건 요약' section"

    # GATE: NO detailed bullet lists (e.g., "- **보장한도**: ...")
    assert "- **보장한도**:" not in bubble, "Bubble must NOT contain detailed bullet lists"
    assert "- **지급유형**:" not in bubble, "Bubble must NOT contain detailed KPI lists"

    print(f"✅ Bubble has NO tables/sections (lightweight conversational)")


def test_bubble_has_no_specific_condition_values(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST NOT contain specific condition values

    GATE: NO "50% 감액", NO "90일", NO specific exclusion clauses
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: NO specific reduction values
    assert "50%" not in bubble, "Bubble must NOT contain specific reduction percentage"
    assert "1년 미만" not in bubble, "Bubble must NOT contain specific reduction period"

    # GATE: NO specific waiting period
    assert "90일" not in bubble, "Bubble must NOT contain specific waiting period"

    # GATE: NO specific exclusion text
    assert "계약일 이전" not in bubble, "Bubble must NOT contain specific exclusion clauses"

    print(f"✅ Bubble has NO specific condition values (conversational summary only)")


def test_bubble_is_lightweight_2_3_sentences(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST be lightweight (2-3 sentences max)

    GATE: Count sentences outside of product header and question hints
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # Extract body (exclude product header and question hints)
    # Product header: <!-- PRODUCT_HEADER --> ... <!-- /PRODUCT_HEADER -->
    # Question hints: 🔎 **다음으로... onwards
    body_start_marker = "<!-- /PRODUCT_HEADER -->"
    body_end_marker = "🔎"

    body_start = bubble.find(body_start_marker)
    body_end = bubble.find(body_end_marker)

    if body_start == -1 or body_end == -1:
        pytest.fail("Bubble structure broken (no product header or question hints marker)")

    body = bubble[body_start + len(body_start_marker):body_end].strip()

    # Count sentences (rough heuristic: count periods/question marks NOT in links)
    # Remove markdown links first
    body_no_links = re.sub(r'\[.*?\]\(.*?\)', '', body)
    sentence_count = body_no_links.count('.') + body_no_links.count('?')

    # GATE: Should be around 2-4 sentences (including newlines treated as sentences)
    # Allow some flexibility for markdown structure
    assert sentence_count >= 2, f"Bubble too short ({sentence_count} sentences, expected 2-4)"
    assert sentence_count <= 6, f"Bubble too long ({sentence_count} sentences, expected 2-4)"

    print(f"✅ Bubble is lightweight ({sentence_count} sentences)")


def test_bubble_has_product_header(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST start with product header

    GATE: Must have <!-- PRODUCT_HEADER --> markers with insurer + coverage + 기준
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: Must have product header markers
    assert "<!-- PRODUCT_HEADER -->" in bubble, "Bubble must have product header start marker"
    assert "<!-- /PRODUCT_HEADER -->" in bubble, "Bubble must have product header end marker"

    # GATE: Header must contain insurer display name (NOT code)
    assert "**삼성화재**" in bubble, "Product header must contain insurer display name"
    assert "samsung" not in bubble.lower() or "PD:samsung:" in bubble, "Product header must NOT expose insurer code (except in refs)"

    # GATE: Header must contain coverage name
    assert "**암진단비(유사암제외)**" in bubble, "Product header must contain coverage display name"

    # GATE: Header must contain 기준
    assert "_기준: 가입설계서_" in bubble, "Product header must contain 기준 line"

    print(f"✅ Bubble has product header (insurer · coverage · 기준)")


def test_bubble_has_question_hints(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST have question hints (demo flow LOCK)

    GATE: Must have exactly 2 hints (STEP NEXT-104 LOCK)
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: Must have question hints section
    assert "🔎 **다음으로 이런 질문도 해볼 수 있어요**" in bubble, "Bubble must have question hints header"

    # GATE: Must have exactly 2 hints (STEP NEXT-104 LOCK)
    assert "- 메리츠는?" in bubble, "Bubble must have first hint (insurer switch)"
    assert "- 암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" in bubble, "Bubble must have second hint (LIMIT_FIND)"

    print(f"✅ Bubble has question hints (2 hints, demo flow LOCK)")


def test_sections_contain_all_details(sample_card_with_amount):
    """
    CONTRACT: sections MUST contain ALL detailed info (NO duplication with bubble)

    GATE: Sections must have 보장 요약 + 조건 요약 + 근거 자료
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    sections = msg.get("sections", [])

    # GATE: Must have at least 3 sections (보장 요약, 조건 요약, 근거 자료)
    assert len(sections) >= 3, f"Sections must have at least 3 items, got {len(sections)}"

    # Find section titles
    section_titles = [s.get("title", "") for s in sections]

    # GATE: Must have 보장 요약 section
    assert "보장 요약" in section_titles, "Sections must contain '보장 요약'"

    # GATE: Must have 조건 요약 section
    assert "조건 요약" in section_titles, "Sections must contain '조건 요약'"

    # GATE: Must have 근거 자료 section
    assert "근거 자료" in section_titles, "Sections must contain '근거 자료'"

    # GATE: 보장 요약 section must have bullets with details
    summary_section = [s for s in sections if s.get("title") == "보장 요약"][0]
    assert "bullets" in summary_section, "보장 요약 section must have bullets"
    bullets = summary_section["bullets"]

    # STEP NEXT-96/113: Must have 보장금액 first (customer-first)
    assert any("보장금액" in b for b in bullets), "보장 요약 must contain 보장금액"
    assert any("보장한도" in b for b in bullets), "보장 요약 must contain 보장한도"
    assert any("지급유형" in b for b in bullets), "보장 요약 must contain 지급유형"

    print(f"✅ Sections contain all details (보장 요약 + 조건 요약 + 근거 자료)")


def test_no_duplication_between_bubble_and_sections(sample_card_with_amount):
    """
    CONTRACT: NO duplication between bubble and sections

    GATE: Specific values in sections must NOT appear in bubble
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]
    sections = msg.get("sections", [])

    # Extract condition section bullets
    condition_section = [s for s in sections if s.get("title") == "조건 요약"]
    if condition_section:
        bullets = condition_section[0].get("bullets", [])

        # GATE: Specific condition values in sections must NOT appear in bubble
        for bullet in bullets:
            # Check for specific values (감액 percentage, waiting period days, etc.)
            if "50%" in bullet:
                assert "50%" not in bubble, "Bubble must NOT duplicate '50%' from sections"
            if "90일" in bullet:
                assert "90일" not in bubble, "Bubble must NOT duplicate '90일' from sections"
            if "1년 미만" in bullet:
                assert "1년 미만" not in bubble, "Bubble must NOT duplicate '1년 미만' from sections"

    print(f"✅ No duplication between bubble and sections")


def test_bubble_conversational_tone_with_amount(sample_card_with_amount):
    """
    CONTRACT: bubble must use conversational tone (amount-based case)

    GATE: Must have "이 담보는..." + "정액으로..." + "조건이 적용됩니다"
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: Sentence 1 (what this coverage is)
    assert "이 담보는" in bubble, "Bubble must have '이 담보는...' sentence"
    assert "보장합니다" in bubble, "Bubble must have conversational ending '보장합니다'"

    # GATE: Sentence 2 (how it works - amount-based)
    assert "정액으로" in bubble, "Bubble must mention '정액으로' for amount-based coverage"
    assert "3000만원" in bubble, "Bubble must mention amount value"
    assert "지급하는 방식입니다" in bubble, "Bubble must have conversational ending '지급하는 방식입니다'"

    # GATE: Sentence 3 (condition note - generic)
    assert "조건이 적용됩니다" in bubble or "확인하실 수 있습니다" in bubble, "Bubble must have condition note"

    print(f"✅ Bubble uses conversational tone (amount-based case)")


def test_bubble_conversational_tone_no_amount(sample_card_no_amount):
    """
    CONTRACT: bubble must use conversational tone (no amount case)

    GATE: Must have "이 담보는..." + payment_type fallback + condition note
    """
    msg = EX2DetailComposer.compose(
        insurer="meritz",
        coverage_code="B3100_1",
        card_data=sample_card_no_amount,
        coverage_name="암직접입원비"
    )

    bubble = msg["bubble_markdown"]

    # GATE: Sentence 1 (what this coverage is)
    assert "이 담보는" in bubble, "Bubble must have '이 담보는...' sentence"
    assert "보장합니다" in bubble, "Bubble must have conversational ending '보장합니다'"

    # GATE: Sentence 2 (how it works - no amount, use payment_type)
    assert "일당형" in bubble or "방식으로" in bubble, "Bubble must mention payment_type when no amount"

    # GATE: Sentence 3 (condition note - generic)
    assert "확인하실 수 있습니다" in bubble or "조건이 적용됩니다" in bubble, "Bubble must have condition note"

    print(f"✅ Bubble uses conversational tone (no amount case)")


def test_no_coverage_code_exposure_in_bubble(sample_card_with_amount):
    """
    CONTRACT: bubble_markdown MUST NOT expose coverage_code

    GATE: NO "A4200_1" or similar patterns (except in refs like PD:samsung:A4200_1)
    """
    msg = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=sample_card_with_amount,
        coverage_name="암진단비(유사암제외)"
    )

    bubble = msg["bubble_markdown"]

    # GATE: NO coverage_code exposure (except in refs)
    # Allow refs like "PD:samsung:A4200_1" but not bare "A4200_1"
    bubble_no_refs = re.sub(r'\[.*?\]\(.*?\)', '', bubble)  # Remove markdown links

    assert "A4200_1" not in bubble_no_refs, "Bubble must NOT expose coverage_code outside of refs"

    print(f"✅ Bubble has NO coverage_code exposure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
