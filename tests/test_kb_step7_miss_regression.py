#!/usr/bin/env python3
"""
KB Step7 Extraction - Regression Gate
STEP NEXT-18X-FIX: ✅ FIXED - KB amount extraction now working

PURPOSE:
Regression test to ensure KB 암진단비(유사암제외) amount extraction continues to work.

EVIDENCE:
- Document: data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf
- Page 2, Line 16: "70 암진단비(유사암제외) 3천만원 36,420 20년/100세"
- Current Step7 result: status=CONFIRMED, value_text="3천만원" ✅
- Expected Step7 result: status=CONFIRMED, value_text="3천만원" ✅

USAGE:
This test serves as a regression gate to ensure KB extraction continues to work.

Current state: ✅ PASS (fixed in STEP NEXT-18X-FIX)
"""

import json
import pytest
from pathlib import Path


def test_kb_cancer_diagnosis_amount_extraction():
    """
    REGRESSION GATE: KB 암진단비(유사암제외) should extract "3천만원"

    EVIDENCE:
    - KB 가입설계서 Page 2: "70 암진단비(유사암제외) 3천만원"
    - This is an EXPLICIT coverage-specific amount
    - Type A/B structure (coverage amount table exists)

    EXPECTED (after Step7 fix):
    - status: "CONFIRMED"
    - value_text: "3천만원" (or normalized "3000만원")
    - source_doc_type: "가입설계서"
    - evidence_ref: Not None

    CURRENT (Step7 miss):
    - status: "UNCONFIRMED"
    - value_text: None
    - source_doc_type: None
    - evidence_ref: None

    This test is marked xfail because Step7 modification is prohibited
    in STEP NEXT-17-KB (verification-only phase).

    When Step7 is fixed, remove xfail and this test should PASS.
    """

    coverage_cards_path = Path("data/compare/kb_coverage_cards.jsonl")

    if not coverage_cards_path.exists():
        pytest.skip("KB coverage cards not found")

    # Find KB 암진단비(유사암제외)
    kb_cancer_amount = None

    with open(coverage_cards_path, 'r', encoding='utf-8') as f:
        for line in f:
            card = json.loads(line)
            canonical = card.get('coverage_name_canonical', '')

            if '암진단비' in canonical and '유사암제외' in canonical:
                kb_cancer_amount = card.get('amount', {})
                break

    assert kb_cancer_amount is not None, "KB 암진단비(유사암제외) not found in coverage_cards"

    # EXPECTED VALUES (after Step7 fix)
    assert kb_cancer_amount.get('status') == 'CONFIRMED', (
        f"Expected CONFIRMED, got {kb_cancer_amount.get('status')}. "
        f"Document shows '3천만원' on page 2."
    )

    assert kb_cancer_amount.get('value_text') is not None, (
        "Expected value_text to be '3천만원' or similar, got None. "
        "Document explicitly shows '3천만원'."
    )

    # Normalized amount should be 3000 (만원 unit) or "3천만원"
    value_text = kb_cancer_amount.get('value_text', '')
    assert any([
        '3천만원' in value_text,
        '3,000만원' in value_text,
        '3000만원' in value_text,
    ]), f"Expected '3천만원' format, got: {value_text}"

    assert kb_cancer_amount.get('source_doc_type') is not None, (
        "Expected source_doc_type (e.g., '가입설계서'), got None"
    )

    assert kb_cancer_amount.get('evidence_ref') is not None, (
        "Expected evidence_ref (page/snippet), got None"
    )


def test_kb_document_structure_evidence_exists():
    """
    VERIFICATION: Ensure KB document structure evidence is documented

    This test confirms that the manual verification (document structure analysis)
    has been completed and evidence file exists.

    This test should PASS immediately (no xfail).
    """

    evidence_file = Path("docs/audit/KB_AMOUNT_STRUCTURE_EVIDENCE.md")

    assert evidence_file.exists(), (
        "KB amount structure evidence document not found. "
        "Expected: docs/audit/KB_AMOUNT_STRUCTURE_EVIDENCE.md"
    )

    content = evidence_file.read_text(encoding='utf-8')

    # Verify key evidence is documented
    assert '3천만원' in content, "Evidence should mention '3천만원'"
    assert 'Type A/B' in content or 'Type A' in content, "Evidence should conclude Type A/B"
    assert 'Page 2' in content or 'p.2' in content or '페이지 2' in content, (
        "Evidence should reference Page 2"
    )
    assert '암진단비(유사암제외)' in content, "Evidence should reference cancer diagnosis coverage"


def test_kb_type_classification_guardrail_exists():
    """
    VERIFICATION: Ensure KB type classification guardrail is documented

    This test confirms that the type classification override policy
    (document structure > config map) has been documented.

    This test should PASS immediately (no xfail).
    """

    guardrail_file = Path("docs/guardrails/KB_TYPE_CLASSIFICATION_RULE.md")

    assert guardrail_file.exists(), (
        "KB type classification guardrail document not found. "
        "Expected: docs/guardrails/KB_TYPE_CLASSIFICATION_RULE.md"
    )

    content = guardrail_file.read_text(encoding='utf-8')

    # Verify key policies are documented
    assert '문서 구조' in content, "Guardrail should mention document structure priority"
    assert '보험사 고정' in content and '금지' in content, "Guardrail should prohibit fixed insurer typing"
    assert 'override' in content.lower(), "Guardrail should mention override mechanism"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
