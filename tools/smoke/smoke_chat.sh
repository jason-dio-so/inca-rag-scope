#!/bin/bash
# STEP B-3: Routing Lock Smoke Test
# 3 routing cases: EX3_COMPARE, EX2_LIMIT_FIND, EX4_ELIGIBILITY

set -e

BASE_URL="http://localhost:8000"

echo "=== SMOKE TEST 1: EX3_COMPARE ==="
echo "Query: 삼성화재와 메리츠화재 암진단비 비교해줘"
echo "Expected: kind=EX3_COMPARE, need_more_info=false"
echo ""

curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "삼성화재와 메리츠화재 암진단비 비교해줘",
    "insurers": ["samsung", "meritz"],
    "coverage_names": ["암진단비"]
  }' | python3 -m json.tool | head -60

echo ""
echo "=== SMOKE TEST 2: EX2_LIMIT_FIND (missing insurers) ==="
echo "Query: 암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"
echo "Expected: need_more_info=true, missing_slots contains insurers"
echo ""

curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
    "insurers": [],
    "coverage_names": []
  }' | python3 -m json.tool | head -60

echo ""
echo "=== SMOKE TEST 3: EX4_ELIGIBILITY ==="
echo "Query: 경계성종양 보장돼?"
echo "Expected: kind=EX4_ELIGIBILITY, need_more_info=false"
echo ""

curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "경계성종양 보장돼?",
    "insurers": ["samsung", "meritz"],
    "coverage_names": []
  }' | python3 -m json.tool | head -60

echo ""
echo "=== SMOKE TEST COMPLETE ==="
