"""
STEP NEXT-66: Test Vector Search

Quick test of vector search functionality.
"""

from core.vector_search_file import search_chunks
from core.customer_view_builder_v2 import build_customer_view_v2


def test_search():
    """Test vector search on A4200_1 (암진단비)"""
    print("=== Testing Vector Search ===\n")

    # Test case: A4200_1 암진단비(유사암 제외)
    axis = "samsung"
    query = "암진단비"

    print(f"Axis: {axis}")
    print(f"Query: {query}\n")

    # Search
    hits = search_chunks(axis, query, doc_types=['약관', '사업방법서', '상품요약서'], top_k=10)

    print(f"Found {len(hits)} hits:\n")

    for i, hit in enumerate(hits[:5]):  # Show top 5
        print(f"{i+1}. [{hit.doc_type}] p.{hit.page} (score={hit.score:.3f})")
        print(f"   Chunk ID: {hit.chunk_id}")
        print(f"   Text: {hit.text[:150]}...")
        print()


def test_customer_view():
    """Test customer_view builder with vector search"""
    print("\n=== Testing Customer View Builder v2 ===\n")

    # Test case: A4200_1
    axis = "samsung"
    coverage_code = "A4200_1"
    coverage_name = "암진단비"

    print(f"Axis: {axis}")
    print(f"Coverage: {coverage_code} - {coverage_name}\n")

    # Build customer view
    customer_view = build_customer_view_v2(axis, coverage_code, coverage_name)

    print("Customer View:")
    print(f"  Benefit Description: {customer_view['benefit_description']}")
    print(f"  Payment Type: {customer_view['payment_type']}")
    print(f"  Limit Conditions: {customer_view['limit_conditions']}")
    print(f"  Exclusion Notes: {customer_view['exclusion_notes']}")
    print(f"  Evidence Refs: {len(customer_view['evidence_refs'])} refs")
    print(f"  Extraction Notes: {customer_view['extraction_notes']}")


if __name__ == "__main__":
    test_search()
    test_customer_view()
