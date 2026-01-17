#!/bin/bash
# Q2 Data Subset Matching Gate
# Ensures Q2 handler correctly handles subset matching when DB has fewer insurers than requested

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)

echo "========================================="
echo "Q2 DATA SUBSET MATCHING GATE"
echo "========================================="

FAIL=0

# Prerequisites: Backend must be running on port 8000
echo "[CHECK 0] Backend health check..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
  echo "❌ FAIL: Backend not running on port 8000"
  echo "   Run: export SSOT_DB_URL=... && python -m uvicorn apps.api.server:app --host 0.0.0.0 --port 8000"
  exit 1
fi
echo "✅ PASS: Backend is running"

# Test 1: A6200 with 8 insurers (DB has 7) → Should return 200 with 7 insurers
echo ""
echo "[CHECK 1] A6200 with 8 insurers (DB has 7) → HTTP 200..."

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Q2_COVERAGE_LIMIT_COMPARE",
    "insurers": ["MERITZ","DB","HANWHA","LOTTE","KB","HYUNDAI","SAMSUNG","HEUNGKUK"],
    "products": [],
    "coverage_codes": ["A6200"],
    "age": 40,
    "gender": "M",
    "as_of_date": "2025-11-26"
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAIL: Expected HTTP 200, got $HTTP_CODE"
  echo "   Response: $BODY"
  FAIL=1
else
  echo "✅ PASS: HTTP 200 returned"
fi

# Test 2: Verify returned_insurer_set has 7 insurers
echo ""
echo "[CHECK 2] Verify returned_insurer_set has 7 insurers..."

RETURNED_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['debug']['returned_insurer_set']))" 2>/dev/null || echo "0")

if [ "$RETURNED_COUNT" != "7" ]; then
  echo "❌ FAIL: Expected 7 insurers in returned_insurer_set, got $RETURNED_COUNT"
  FAIL=1
else
  echo "✅ PASS: returned_insurer_set has 7 insurers"
fi

# Test 3: Verify missing_insurers contains N02
echo ""
echo "[CHECK 3] Verify missing_insurers contains N02..."

MISSING_INSURERS=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['debug']['missing_insurers'])" 2>/dev/null || echo "[]")

if echo "$MISSING_INSURERS" | grep -q "N02"; then
  echo "✅ PASS: missing_insurers contains N02"
else
  echo "❌ FAIL: missing_insurers does not contain N02"
  echo "   Got: $MISSING_INSURERS"
  FAIL=1
fi

# Test 4: Verify insurer_rows has 7 elements
echo ""
echo "[CHECK 4] Verify insurer_rows has 7 elements..."

ROWS_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['insurer_rows']))" 2>/dev/null || echo "0")

if [ "$ROWS_COUNT" != "7" ]; then
  echo "❌ FAIL: Expected 7 rows in insurer_rows, got $ROWS_COUNT"
  FAIL=1
else
  echo "✅ PASS: insurer_rows has 7 elements"
fi

# Test 5: Verify each insurer_row has insurer_code field
echo ""
echo "[CHECK 5] Verify each insurer_row has insurer_code field..."

HAS_INSURER_CODE=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
all_have_code = all('insurer_code' in row for row in data['insurer_rows'])
print('1' if all_have_code else '0')
" 2>/dev/null || echo "0")

if [ "$HAS_INSURER_CODE" != "1" ]; then
  echo "❌ FAIL: Not all insurer_rows have insurer_code field"
  FAIL=1
else
  echo "✅ PASS: All insurer_rows have insurer_code field"
fi

# Test 6: Verify insurer_codes match returned_insurer_set
echo ""
echo "[CHECK 6] Verify insurer_codes match returned_insurer_set..."

CODES_MATCH=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
row_codes = sorted([row['insurer_code'] for row in data['insurer_rows']])
returned_set = sorted(data['debug']['returned_insurer_set'])
print('1' if row_codes == returned_set else '0')
" 2>/dev/null || echo "0")

if [ "$CODES_MATCH" != "1" ]; then
  echo "❌ FAIL: insurer_codes in rows don't match returned_insurer_set"
  FAIL=1
else
  echo "✅ PASS: insurer_codes match returned_insurer_set"
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2 DATA SUBSET MATCHING GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2 DATA SUBSET MATCHING GATE: FAILED"
  echo "========================================="
  exit 1
fi
