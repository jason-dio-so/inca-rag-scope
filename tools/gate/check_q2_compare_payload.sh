#!/bin/bash
# Q2 Compare Payload Gate Check
# Ensures Q2 compare proxy transforms payload to CompareRequest schema correctly

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q2 COMPARE PAYLOAD GATE"
echo "========================================="

FAIL=0

Q2_COMPARE_ROUTE="$WEB_ROOT/app/api/q2/compare/route.ts"

# Check 1: MUST NOT pass through ins_cds to backend
echo "[CHECK 1] /api/q2/compare MUST NOT send ins_cds to backend..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "ins_cds.*body\|body.*ins_cds\|JSON.stringify(body)" "$Q2_COMPARE_ROUTE"; then
    echo "❌ FAIL: Q2 compare route contains passthrough pattern (REGRESSION)"
    FAIL=1
  else
    echo "✅ PASS: Q2 compare route does NOT passthrough ins_cds"
  fi
else
  echo "❌ FAIL: Q2 compare route not found"
  FAIL=1
fi

# Check 2: MUST have insurers field in payload
echo "[CHECK 2] /api/q2/compare MUST have 'insurers' field..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "insurers" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route has 'insurers' field"
  else
    echo "❌ FAIL: Q2 compare route missing 'insurers' field"
    FAIL=1
  fi
fi

# Check 3: MUST have INSURER_CODE_TO_ENUM mapping
echo "[CHECK 3] /api/q2/compare MUST have INSURER_CODE_TO_ENUM mapping..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "INSURER_CODE_TO_ENUM" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route has INSURER_CODE_TO_ENUM"
  else
    echo "❌ FAIL: Q2 compare route missing INSURER_CODE_TO_ENUM"
    FAIL=1
  fi
fi

# Check 4: MUST have all CompareRequest required fields
echo "[CHECK 4] /api/q2/compare MUST include all CompareRequest fields..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  REQUIRED_FIELDS=("query" "insurers" "age" "gender" "coverage_codes")
  MISSING_FIELDS=()

  for field in "${REQUIRED_FIELDS[@]}"; do
    # Check for both "field": and field: and field, (property shorthand)
    if ! grep -qE "\"$field\":|$field:|$field," "$Q2_COMPARE_ROUTE"; then
      MISSING_FIELDS+=("$field")
    fi
  done

  if [ ${#MISSING_FIELDS[@]} -eq 0 ]; then
    echo "✅ PASS: All required CompareRequest fields present"
  else
    echo "❌ FAIL: Missing required fields: ${MISSING_FIELDS[*]}"
    FAIL=1
  fi
fi

# Check 5: MUST construct comparePayload directly (NO PASSTHROUGH)
echo "[CHECK 5] /api/q2/compare MUST construct comparePayload directly..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "comparePayload" "$Q2_COMPARE_ROUTE" && grep -q "JSON.stringify(comparePayload)" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route constructs comparePayload directly"
  else
    echo "❌ FAIL: Q2 compare route does NOT construct comparePayload"
    FAIL=1
  fi
fi

# Check 6: MUST have debug logs (TEMP)
echo "[CHECK 6] /api/q2/compare MUST have debug logs..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "console.log.*\[Q2\]\[compare\]" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route has debug logs"
  else
    echo "❌ FAIL: Q2 compare route missing debug logs"
    FAIL=1
  fi
fi

# Check 7: MUST have 'intent' field in payload
echo "[CHECK 7] /api/q2/compare MUST include 'intent' in payload..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -qE "intent.*:.*\"Q2_COVERAGE_LIMIT_COMPARE\"|intent.*:.*'Q2_COVERAGE_LIMIT_COMPARE'" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route has 'intent' field (Q2_COVERAGE_LIMIT_COMPARE)"
  else
    echo "❌ FAIL: Q2 compare route missing or incorrect 'intent' field"
    FAIL=1
  fi
fi

# Check 8: MUST have 'products' field in payload
echo "[CHECK 8] /api/q2/compare MUST include 'products' in payload..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -qE "products.*:" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route has 'products' field"
  else
    echo "❌ FAIL: Q2 compare route missing 'products' field"
    FAIL=1
  fi
fi

# Check 9: MUST NOT have 'coverage_code:undefined' pattern (REGRESSION)
echo "[CHECK 9] /api/q2/compare MUST NOT have 'coverage_code:undefined' pattern..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "coverage_code:\${coverage_code}" "$Q2_COMPARE_ROUTE"; then
    echo "❌ FAIL: Q2 compare route has 'coverage_code:\${coverage_code}' pattern (REGRESSION)"
    FAIL=1
  else
    echo "✅ PASS: Q2 compare route has NO 'coverage_code:undefined' pattern"
  fi
fi

# Check 10: MUST support coverage_codes array input
echo "[CHECK 10] /api/q2/compare MUST support coverage_codes array input..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "coverage_codes" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route supports coverage_codes array"
  else
    echo "❌ FAIL: Q2 compare route missing coverage_codes array support"
    FAIL=1
  fi
fi

# Check 11: MUST validate coverage_code (return 400 if missing)
echo "[CHECK 11] /api/q2/compare MUST validate coverage_code..."
if [ -f "$Q2_COMPARE_ROUTE" ]; then
  if grep -q "Missing coverage_code" "$Q2_COMPARE_ROUTE" && grep -q "status: 400" "$Q2_COMPARE_ROUTE"; then
    echo "✅ PASS: Q2 compare route validates coverage_code"
  else
    echo "❌ FAIL: Q2 compare route missing coverage_code validation"
    FAIL=1
  fi
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2 COMPARE PAYLOAD GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2 COMPARE PAYLOAD GATE: FAILED"
  echo "========================================="
  exit 1
fi
