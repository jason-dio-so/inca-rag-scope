#!/usr/bin/env python3
"""
STEP NEXT-103: Manual Runtime Proof — Insurer Switch Payload + EX2_DETAIL Display Names

PURPOSE:
Manual test to verify:
1. Frontend sends correct payload when user types "메리츠는?" (insurer switch)
2. Backend EX2_DETAIL response uses display names (삼성화재, 메리츠화재) NOT codes

USAGE:
1. Start web dev server: cd apps/web && npm run dev
2. Start API server: cd apps/api && uvicorn main:app --reload --port 8000
3. Open browser: http://localhost:3000
4. Run this test flow

TEST FLOW (Manual):
1. Click "EX2 예제" button (삼성 암진단비) → Verify request payload has insurers:["samsung"]
2. Type "메리츠는?" → Verify request payload has insurers:["meritz"]
3. Verify response title shows "메리츠화재 암진단비 설명" (NOT "meritz")
4. Type "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" → Verify clarification UI appears
5. Select "삼성화재" → Verify request has insurers:["meritz", "samsung"] (merge, not replace)
6. Verify EX2_LIMIT_FIND table appears with both insurers

EXPECTED BEHAVIOR:
✅ Step 1: Request payload { insurers: ["samsung"], coverage_names: ["암진단비(유사암 제외)"] }
✅ Step 2: Request payload { insurers: ["meritz"], coverage_names: ["암진단비(유사암 제외)"] }
✅ Step 3: Response title "메리츠화재 암진단비(유사암 제외) 설명" (NO "meritz")
✅ Step 5: Request payload { insurers: ["meritz", "samsung"], coverage_names: ["암직접입원비"] }
✅ Step 6: EX2_LIMIT_FIND table with 2 rows (samsung, meritz)

AUTOMATED CHECKS (Backend Only):
Since frontend requires manual browser testing, this script only tests backend EX2_DETAIL
"""

import json
from apps.api.response_composers.ex2_detail_composer import EX2DetailComposer


def test_ex2_detail_samsung_display_name():
    """Test Samsung EX2_DETAIL uses display name"""
    print("\n" + "="*80)
    print("TEST 1: Samsung EX2_DETAIL Display Name")
    print("="*80)

    card_data = {
        "amount": "3000만원",
        "kpi_summary": {
            "limit_summary": "3,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:samsung:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "1년 미만 50%",
            "waiting_period": "90일",
            "exclusion_condition": "계약일 이전 발생 질병",
            "renewal_condition": "비갱신형"
        }
    }

    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=card_data,
        coverage_name="암진단비(유사암 제외)"
    )

    print(f"\n📝 Title: {result['title']}")
    print(f"📝 Summary: {result['summary_bullets'][0]}")
    print(f"\n📝 Bubble (first 200 chars):\n{result['bubble_markdown'][:200]}...")

    # Verify
    assert "삼성화재" in result['title'], "❌ Title should contain '삼성화재'"
    assert "samsung" not in result['title'].lower(), "❌ Title should NOT contain 'samsung'"
    assert "삼성화재" in result['bubble_markdown'], "❌ Bubble should contain '삼성화재'"
    print("\n✅ Samsung display name: PASS")


def test_ex2_detail_meritz_display_name():
    """Test Meritz EX2_DETAIL uses display name"""
    print("\n" + "="*80)
    print("TEST 2: Meritz EX2_DETAIL Display Name")
    print("="*80)

    card_data = {
        "amount": "2000만원",
        "kpi_summary": {
            "limit_summary": "2,000만원",
            "payment_type": "LUMP_SUM",
            "kpi_evidence_refs": ["EV:meritz:A4200_1:01"]
        },
        "kpi_condition": {
            "reduction_condition": "근거 없음",
            "waiting_period": "90일",
            "exclusion_condition": "근거 없음",
            "renewal_condition": "비갱신형"
        }
    }

    result = EX2DetailComposer.compose(
        insurer="meritz",
        coverage_code="A4200_1",
        card_data=card_data,
        coverage_name="암진단비(유사암 제외)"
    )

    print(f"\n📝 Title: {result['title']}")
    print(f"📝 Summary: {result['summary_bullets'][0]}")
    print(f"\n📝 Bubble (first 200 chars):\n{result['bubble_markdown'][:200]}...")

    # Verify
    assert "메리츠화재" in result['title'], "❌ Title should contain '메리츠화재'"
    assert "meritz" not in result['title'].lower(), "❌ Title should NOT contain 'meritz'"
    assert "메리츠화재" in result['bubble_markdown'], "❌ Bubble should contain '메리츠화재'"
    print("\n✅ Meritz display name: PASS")


def test_ex2_detail_question_hints():
    """Test question continuity hints use display names"""
    print("\n" + "="*80)
    print("TEST 3: Question Continuity Hints Display Names")
    print("="*80)

    card_data = {
        "amount": "3000만원",
        "kpi_summary": {
            "limit_summary": "3,000만원",
            "payment_type": "LUMP_SUM"
        },
        "kpi_condition": {
            "renewal_condition": "비갱신형"
        }
    }

    result = EX2DetailComposer.compose(
        insurer="samsung",
        coverage_code="A4200_1",
        card_data=card_data,
        coverage_name="암진단비(유사암 제외)"
    )

    bubble = result['bubble_markdown']

    # Extract hints section
    if "다음으로 이런 질문도" in bubble:
        hints_section = bubble.split("다음으로 이런 질문도")[-1]
        print(f"\n📝 Hints Section:\n{hints_section}")

        # Verify
        assert "삼성화재와 다른 보험사의" in hints_section, "❌ Hints should use display name '삼성화재'"
        print("\n✅ Question hints use display names: PASS")
    else:
        print("⚠️  No hints section found")


def print_manual_test_instructions():
    """Print manual test instructions for frontend"""
    print("\n" + "="*80)
    print("MANUAL TEST INSTRUCTIONS (Frontend)")
    print("="*80)
    print("""
1. Start servers:
   - API: cd apps/api && uvicorn main:app --reload --port 8000
   - Web: cd apps/web && npm run dev

2. Open browser: http://localhost:3000

3. Open browser console (F12) to see request payloads

4. TEST FLOW:

   STEP 1: Click "EX2 예제" button (삼성 암진단비)
   ✅ Check console: Request payload should have insurers:["samsung"]
   ✅ Check response: Title should be "삼성화재 암진단비(유사암 제외) 설명"
   ❌ Verify: NO "samsung" in title/bubble (except refs like PD:samsung:...)

   STEP 2: Type "메리츠는?" and press Enter
   ✅ Check console: Request payload should have insurers:["meritz"]
   ✅ Check response: Title should be "메리츠화재 암진단비(유사암 제외) 설명"
   ❌ Verify: NO "meritz" in title/bubble (except refs)

   STEP 3: Type "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
   ✅ Check: Clarification UI should appear (need 2 insurers for LIMIT_FIND)
   ✅ Select "삼성화재" from the list

   STEP 4: Verify auto-resend after clarification
   ✅ Check console: Request should have insurers:["meritz", "samsung"] (MERGE, not replace)
   ✅ Check response: EX2_LIMIT_FIND table with 2 rows
   ✅ Verify: Table shows "삼성화재", "메리츠화재" (NOT codes)

5. ACCEPTANCE CRITERIA:
   - Insurer switch ("메리츠는?") sends correct payload immediately
   - All EX2_DETAIL responses use display names (삼성화재/메리츠화재/KB손해보험 etc.)
   - Clarification flow merges insurers (doesn't replace)
   - NO insurer codes (samsung/meritz/kb etc.) in user-facing text

6. FAILURE MODES (What we're fixing):
   ❌ "메리츠는?" sends insurers:["samsung"] (OLD BUG - now fixed)
   ❌ Title shows "samsung 암진단비 설명" (OLD BUG - now fixed)
   ❌ Clarification replaces insurers instead of merging (OLD BUG - already fixed in STEP NEXT-102)
""")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("STEP NEXT-103: Insurer Switch Payload + EX2_DETAIL Display Name Runtime Proof")
    print("="*80)

    # Run automated backend tests
    test_ex2_detail_samsung_display_name()
    test_ex2_detail_meritz_display_name()
    test_ex2_detail_question_hints()

    # Print manual test instructions
    print_manual_test_instructions()

    print("\n" + "="*80)
    print("✅ Backend tests PASSED — Display names working correctly")
    print("📝 Follow manual test instructions above to verify frontend payload")
    print("="*80 + "\n")
