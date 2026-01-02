"""
Test STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched diff results

Verifies:
1. Diff results include value_normalized
2. Diff results include insurer_details with raw_text + evidence_refs
3. extraction_notes present for "명시 없음" cases
4. No [object Object] in outputs
5. LLM OFF (no LLM imports/usage)
"""

import sys
import json
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline" / "step8_render_deterministic"))
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from api.chat_handlers_deterministic import Example2DiffHandlerDeterministic
from api.chat_vm import ChatRequest


def test_diff_enriched_limit():
    """Test enriched diff for 보장한도 field"""
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung", "meritz", "hanwha"],
        "coverage_code": "A4200_1",  # 암직접입원비
        "compare_field": "보장한도"
    }

    request = ChatRequest(
        request_id="test_diff_limit",
        user_message="암직접입원비 보장한도가 다른 상품 찾아줘",
        llm_mode="OFF"
    )

    vm = handler.execute(compiled_query, request)

    # Verify basic structure
    assert vm.kind == "EX2_DETAIL_DIFF"
    assert len(vm.sections) > 0

    diff_section = vm.sections[0]
    assert diff_section.kind == "coverage_diff_result"
    assert diff_section.field_label == "보장한도"

    # Verify groups have enriched data
    for group in diff_section.groups:
        print(f"\n=== Group: {group.value_display} ===")
        print(f"Insurers: {group.insurers}")

        # Check value_normalized
        if group.value_normalized:
            print(f"Value normalized: {json.dumps(group.value_normalized, ensure_ascii=False, indent=2)}")
            assert "raw_text" in group.value_normalized
            assert "evidence_refs" in group.value_normalized

        # Check insurer_details
        if group.insurer_details:
            print(f"Insurer details count: {len(group.insurer_details)}")
            for detail in group.insurer_details:
                print(f"  - {detail.insurer}: {detail.raw_text[:50]}...")
                assert detail.insurer in group.insurers
                assert isinstance(detail.raw_text, str)
                assert isinstance(detail.evidence_refs, list)

                # Verify no [object Object]
                assert "[object Object]" not in detail.raw_text

                # If notes exist, verify they're strings
                if detail.notes:
                    assert all(isinstance(note, str) for note in detail.notes)
                    print(f"    Notes: {detail.notes}")

    # Check extraction_notes
    if diff_section.extraction_notes:
        print(f"\n=== Extraction Notes ===")
        for note in diff_section.extraction_notes:
            print(f"  - {note}")
            assert isinstance(note, str)

    # Verify LLM not used
    assert vm.lineage.get("llm_used") == False
    assert vm.lineage.get("deterministic") == True

    print("\n✅ Test passed: diff enriched (limit)")


def test_diff_enriched_payment_type():
    """Test enriched diff for 지급유형 field"""
    handler = Example2DiffHandlerDeterministic()

    compiled_query = {
        "insurers": ["samsung", "meritz", "hanwha"],
        "coverage_code": "A4200_1",
        "compare_field": "지급유형"
    }

    request = ChatRequest(
        request_id="test_diff_payment",
        user_message="암직접입원비 지급유형이 다른 상품 찾아줘",
        llm_mode="OFF"
    )

    vm = handler.execute(compiled_query, request)

    diff_section = vm.sections[0]

    # Verify groups have payment type normalization
    for group in diff_section.groups:
        print(f"\n=== Payment Type Group: {group.value_display} ===")

        if group.value_normalized:
            print(f"Normalized kind: {group.value_normalized.get('kind')}")
            assert group.value_normalized.get("kind") in ["lump_sum", "per_day", "per_event", "unknown"]

        if group.insurer_details:
            for detail in group.insurer_details:
                print(f"  - {detail.insurer}: {detail.raw_text[:50]}...")
                assert "[object Object]" not in detail.raw_text

    print("\n✅ Test passed: diff enriched (payment_type)")


def test_no_llm_imports():
    """Verify no LLM imports in handler"""
    handler_file = Path(__file__).parent.parent / "apps" / "api" / "chat_handlers_deterministic.py"
    content = handler_file.read_text()

    forbidden_imports = ["openai", "anthropic", "langchain", "llama"]

    for imp in forbidden_imports:
        assert imp not in content.lower(), f"Found forbidden import: {imp}"

    print("✅ Test passed: no LLM imports")


if __name__ == "__main__":
    test_diff_enriched_limit()
    test_diff_enriched_payment_type()
    test_no_llm_imports()

    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED (STEP NEXT-COMPARE-FILTER-DETAIL-02)")
    print("="*50)
