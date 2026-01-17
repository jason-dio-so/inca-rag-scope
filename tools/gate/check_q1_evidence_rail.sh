#!/bin/bash
# Q1 Evidence Rail Gate Check
# Prevents formulas/explanations in main table (rail-only rule)

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q1 EVIDENCE RAIL GATE CHECK"
echo "========================================="

FAIL=0

# Check 1: Q1PremiumTable must NOT contain forbidden tokens
echo "[CHECK 1] Q1PremiumTable must NOT contain forbidden tokens..."
Q1_TABLE="$WEB_ROOT/components/q1/Q1PremiumTable.tsx"
if [ -f "$Q1_TABLE" ]; then
  # Check for forbidden strings (formulas, percentages, multipliers, explanations)
  FORBIDDEN_PATTERNS='%|×|multiplier|공식|배수|130|산출|계산'
  if grep -E "$FORBIDDEN_PATTERNS" "$Q1_TABLE" | grep -v "//.*$FORBIDDEN_PATTERNS" | grep -q .; then
    echo "❌ FAIL: Q1PremiumTable contains forbidden tokens"
    grep -n -E "$FORBIDDEN_PATTERNS" "$Q1_TABLE" | head -10
    FAIL=1
  else
    echo "✅ PASS: Q1PremiumTable has no forbidden tokens"
  fi
else
  echo "❌ FAIL: Q1PremiumTable not found"
  FAIL=1
fi

# Check 2: Main table cells must NOT contain explanation keywords (footer is OK)
echo "[CHECK 2] Main table cells must NOT contain explanation keywords..."
if [ -f "$Q1_TABLE" ]; then
  # Only check table cells (td/th), not footer note
  EXPLANATION_IN_CELLS=$(grep -E '<td|<th' "$Q1_TABLE" | grep -E '근거|출처|사유|기준일' || true)
  if [ -n "$EXPLANATION_IN_CELLS" ]; then
    echo "❌ FAIL: Q1PremiumTable cells contain explanation keywords (should be rail-only)"
    echo "$EXPLANATION_IN_CELLS" | head -10
    FAIL=1
  else
    echo "✅ PASS: Q1PremiumTable cells have no explanation keywords"
  fi
fi

# Check 3: Evidence Rail component must exist
echo "[CHECK 3] Evidence Rail component must exist..."
Q1_EVIDENCE_RAIL="$WEB_ROOT/components/q1/Q1EvidenceRail.tsx"
if [ -f "$Q1_EVIDENCE_RAIL" ]; then
  echo "✅ PASS: Q1EvidenceRail exists"
else
  echo "❌ FAIL: Q1EvidenceRail not found"
  FAIL=1
fi

# Check 4: Q1 page must reference Evidence Rail
echo "[CHECK 4] Q1 page must reference Evidence Rail..."
Q1_PAGE="$WEB_ROOT/app/q1/page.tsx"
if [ -f "$Q1_PAGE" ]; then
  if grep -q "Q1EvidenceRail" "$Q1_PAGE"; then
    echo "✅ PASS: Q1 page imports/uses Q1EvidenceRail"
  else
    echo "❌ FAIL: Q1 page does not reference Q1EvidenceRail"
    FAIL=1
  fi
else
  echo "❌ FAIL: Q1 page not found"
  FAIL=1
fi

# Check 5: No UI-side math in Q1 components
echo "[CHECK 5] No UI-side math in Q1 components..."
MATH_PATTERNS='Math\.round|Math\.floor|Math\.ceil|\*\s*130|\/\s*100'
Q1_COMPONENTS="$WEB_ROOT/components/q1 $WEB_ROOT/app/q1"
MATH_MATCHES=$(grep -r -E "$MATH_PATTERNS" $Q1_COMPONENTS 2>/dev/null | grep -v "\.map\|\.filter\|\.reduce" | head -20 || true)
if [ -n "$MATH_MATCHES" ]; then
  echo "⚠️  WARNING: Found potential math operations (verify if legitimate):"
  echo "$MATH_MATCHES"
  # Not failing this check since some legitimate array operations might match
else
  echo "✅ PASS: No suspicious math operations found"
fi

# Check 6: Evidence Rail must have fixed copy for null GENERAL
echo "[CHECK 6] Evidence Rail must have fixed copy for null GENERAL..."
if [ -f "$Q1_EVIDENCE_RAIL" ]; then
  if grep -q "데이터 없음" "$Q1_EVIDENCE_RAIL" && grep -q "해당 기준일" "$Q1_EVIDENCE_RAIL"; then
    echo "✅ PASS: Evidence Rail has fixed copy for null GENERAL data"
  else
    echo "❌ FAIL: Evidence Rail missing fixed copy for null GENERAL data"
    FAIL=1
  fi
fi

# Check 7: Table must have row click handler
echo "[CHECK 7] Table must have row click handler..."
if [ -f "$Q1_TABLE" ]; then
  if grep -q "onRowClick" "$Q1_TABLE" && grep -q "onClick.*onRowClick" "$Q1_TABLE"; then
    echo "✅ PASS: Table has row click handler"
  else
    echo "❌ FAIL: Table missing row click handler"
    FAIL=1
  fi
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q1 EVIDENCE RAIL GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q1 EVIDENCE RAIL GATE: FAILED"
  echo "========================================="
  exit 1
fi
