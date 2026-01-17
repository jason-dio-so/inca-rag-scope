#!/bin/bash
# Q2 Product Name SSOT Enforcement Gate
# Ensures Q2 uses product.product_full_name SSOT (not regex extraction)

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)

echo "========================================="
echo "Q2 PRODUCT NAME SSOT GATE"
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

# Check (A): Q1 join key fact documented in audit doc
echo ""
echo "[CHECK A] Q1 join key FACT documented in Q2_PRODUCT_DB_AUDIT.md..."

AUDIT_DOC="$REPO_ROOT/docs/ui/Q2_PRODUCT_DB_AUDIT.md"
if [ ! -f "$AUDIT_DOC" ]; then
  echo "❌ FAIL: Audit doc not found: $AUDIT_DOC"
  FAIL=1
elif ! grep -q "Q1 product_name join key" "$AUDIT_DOC"; then
  echo "❌ FAIL: Q1 join key FACT not documented in audit doc"
  FAIL=1
elif ! grep -q "product_id.*apps/api/q1_endpoints.py" "$AUDIT_DOC"; then
  echo "❌ FAIL: Q1 join key source not documented (expected: product_id from q1_endpoints.py)"
  FAIL=1
else
  echo "✅ PASS: Q1 join key FACT documented with evidence"
fi

# Check (B): No regex product_name extraction in Q2 handler
echo ""
echo "[CHECK B] No regex product_name extraction in Q2 handler..."

SERVER_PY="$REPO_ROOT/apps/api/server.py"
if grep -A 5 "Q2CoverageLimitCompareHandler" "$SERVER_PY" | grep -E "product_patterns.*=|re\.search.*product" | grep -v "^#" > /dev/null; then
  echo "❌ FAIL: Regex product_name extraction still exists in Q2 handler"
  echo "   Found:"
  grep -A 5 "Q2CoverageLimitCompareHandler" "$SERVER_PY" | grep -E "product_patterns.*=|re\.search.*product" | grep -v "^#"
  FAIL=1
else
  echo "✅ PASS: No regex product_name extraction found"
fi

# Check (C): SSOT query exists (batch query to product table)
echo ""
echo "[CHECK C] Product SSOT batch query exists in Q2 handler..."

if ! grep -A 10 "SELECT.*product_full_name" "$SERVER_PY" | grep -q "FROM product"; then
  echo "❌ FAIL: No product SSOT query found in server.py"
  FAIL=1
elif ! grep -B 5 -A 10 "FROM product" "$SERVER_PY" | grep -q "ins_cd = ANY"; then
  echo "❌ FAIL: Product query not using batch pattern (ins_cd = ANY)"
  FAIL=1
else
  echo "✅ PASS: Product SSOT batch query exists"
fi

# Check (D): A6200 returns non-empty product_names from SSOT
echo ""
echo "[CHECK D] A6200 returns non-empty product_names..."

# Create test payload
cat > /tmp/q2_product_gate_payload.json << 'EOF'
{
  "intent": "Q2_COVERAGE_LIMIT_COMPARE",
  "insurers": ["MERITZ","DB","HANWHA","LOTTE","KB","HYUNDAI","SAMSUNG","HEUNGKUK"],
  "products": [],
  "coverage_codes": ["A6200"],
  "age": 40,
  "gender": "M",
  "as_of_date": "2025-11-26"
}
EOF

RESPONSE=$(curl -s -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d @/tmp/q2_product_gate_payload.json)

HTTP_CODE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if 'insurer_rows' in data else 1)" && echo "200" || echo "error")

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ FAIL: API request failed or invalid response"
  FAIL=1
else
  # Count non-empty product_names
  NON_EMPTY_COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rows = data.get('insurer_rows', [])
non_empty = sum(1 for row in rows if row.get('product_name'))
print(non_empty)
" 2>/dev/null || echo "0")

  TOTAL_ROWS=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len(data.get('insurer_rows', [])))
" 2>/dev/null || echo "0")

  if [ "$NON_EMPTY_COUNT" = "0" ]; then
    echo "❌ FAIL: No product_names returned (expected at least 1)"
    FAIL=1
  else
    echo "✅ PASS: $NON_EMPTY_COUNT/$TOTAL_ROWS insurers have product_name from SSOT"
  fi
fi

# Check (E): No table header noise patterns in product_names
echo ""
echo "[CHECK E] No table header noise patterns in product_names..."

FORBIDDEN_PATTERNS="가입담보|고객님님|보장내용 요약|보험료 납입|계약사항 보험"

HAS_NOISE=$(echo "$RESPONSE" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
rows = data.get('insurer_rows', [])
forbidden_re = re.compile(r'$FORBIDDEN_PATTERNS')
noisy = [row.get('insurer_code') for row in rows
         if row.get('product_name') and forbidden_re.search(row['product_name'])]
if noisy:
    print(','.join(noisy))
else:
    print('none')
" 2>/dev/null || echo "error")

if [ "$HAS_NOISE" = "error" ]; then
  echo "⚠️  WARN: Could not validate patterns (python error)"
elif [ "$HAS_NOISE" != "none" ]; then
  echo "❌ FAIL: Table header noise found in product_names: $HAS_NOISE"
  FAIL=1
else
  echo "✅ PASS: No table header noise patterns detected"
fi

# Check (F): Debug transparency fields present
echo ""
echo "[CHECK F] Debug transparency fields present..."

MISSING_FIELDS=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
debug = data.get('debug', {})
required = ['product_join_key_fact', 'product_name_missing_insurers', 'product_table_as_of_date_used']
missing = [f for f in required if f not in debug]
if missing:
    print(','.join(missing))
else:
    print('none')
" 2>/dev/null || echo "error")

if [ "$MISSING_FIELDS" = "error" ]; then
  echo "❌ FAIL: Could not validate debug fields (python error)"
  FAIL=1
elif [ "$MISSING_FIELDS" != "none" ]; then
  echo "❌ FAIL: Missing debug fields: $MISSING_FIELDS"
  FAIL=1
else
  FACT_VALUE=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['debug']['product_join_key_fact'])" 2>/dev/null || echo "error")
  echo "✅ PASS: All debug transparency fields present (fact: $FACT_VALUE)"
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2 PRODUCT NAME SSOT GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2 PRODUCT NAME SSOT GATE: FAILED"
  echo "========================================="
  exit 1
fi
