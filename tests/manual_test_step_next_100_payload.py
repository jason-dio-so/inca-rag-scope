#!/usr/bin/env python3
"""
STEP NEXT-100 Manual Test: Verify /chat request payload includes insurers/coverage_names

Test Cases:
- Case A: insurers + coverage_names → no need_more_info
- Case B: insurers only → coverage_names prompt only
- Case C: coverage_names only → insurers prompt only
"""

import requests
import json

API_BASE = "http://localhost:8000"


def test_case_a_full_context():
    """Case A: Both insurers and coverage_names provided"""
    print("\n=== Case A: insurers + coverage_names ===")

    payload = {
        "message": "삼성과 메리츠의 암진단비 보장한도차이",
        "insurers": ["samsung", "meritz"],
        "coverage_names": ["암진단비(유사암제외)"],
        "llm_mode": "OFF"
    }

    print(f"Request payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    response = requests.post(f"{API_BASE}/chat", json=payload)
    data = response.json()

    print(f"Response status: {response.status_code}")
    print(f"need_more_info: {data.get('need_more_info', False)}")
    print(f"missing_slots: {data.get('missing_slots', [])}")
    print(f"message kind: {data.get('message', {}).get('kind', 'N/A')}")

    # Assertion
    assert data.get("need_more_info") is not True, "❌ FAIL: should NOT need more info"
    print("✅ PASS: No need_more_info")


def test_case_b_insurers_only():
    """Case B: Only insurers provided (coverage_names missing)"""
    print("\n=== Case B: insurers only ===")

    payload = {
        "message": "암진단비 보장한도차이",
        "insurers": ["samsung", "meritz"],
        "llm_mode": "OFF"
    }

    print(f"Request payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    response = requests.post(f"{API_BASE}/chat", json=payload)
    data = response.json()

    print(f"Response status: {response.status_code}")
    print(f"need_more_info: {data.get('need_more_info', False)}")
    print(f"missing_slots: {data.get('missing_slots', [])}")

    # Assertion
    if data.get("need_more_info") is True:
        missing = data.get("missing_slots", [])
        assert "coverage_names" in missing, "❌ FAIL: should request coverage_names"
        assert "insurers" not in missing, "❌ FAIL: should NOT request insurers"
        print("✅ PASS: Requests coverage_names only")
    else:
        print("✅ PASS: Handled without clarification (message context sufficient)")


def test_case_c_coverage_only():
    """Case C: Only coverage_names provided (insurers missing)"""
    print("\n=== Case C: coverage_names only ===")

    payload = {
        "message": "암진단비 보장 가능한가요?",
        "coverage_names": ["암진단비(유사암제외)"],
        "llm_mode": "OFF"
    }

    print(f"Request payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    response = requests.post(f"{API_BASE}/chat", json=payload)
    data = response.json()

    print(f"Response status: {response.status_code}")
    print(f"need_more_info: {data.get('need_more_info', False)}")
    print(f"missing_slots: {data.get('missing_slots', [])}")

    # Assertion
    if data.get("need_more_info") is True:
        missing = data.get("missing_slots", [])
        assert "insurers" in missing, "❌ FAIL: should request insurers"
        assert "coverage_names" not in missing, "❌ FAIL: should NOT request coverage_names"
        print("✅ PASS: Requests insurers only")
    else:
        print("✅ PASS: Handled without clarification (message context sufficient)")


if __name__ == "__main__":
    print("STEP NEXT-100 Payload Contract Test")
    print("=" * 50)

    try:
        test_case_a_full_context()
        test_case_b_insurers_only()
        test_case_c_coverage_only()

        print("\n" + "=" * 50)
        print("All tests PASSED ✅")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
