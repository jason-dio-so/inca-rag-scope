#!/bin/bash
# Q2 Chat Mode Gate Check
# Ensures Q2 chat mode is properly implemented

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q2 CHAT MODE GATE"
echo "========================================="

FAIL=0

# Check 1: Q2ChatPanel component exists
echo "[CHECK 1] Q2ChatPanel component must exist..."
Q2_CHAT_PANEL="$WEB_ROOT/components/q2/Q2ChatPanel.tsx"
if [ -f "$Q2_CHAT_PANEL" ]; then
  echo "✅ PASS: Q2ChatPanel exists"
else
  echo "❌ FAIL: Q2ChatPanel not found"
  FAIL=1
fi

# Check 2: slotParser exists + NO LLM imports
echo "[CHECK 2] slotParser must exist with NO LLM imports..."
SLOT_PARSER="$WEB_ROOT/lib/q2/slotParser.ts"
if [ -f "$SLOT_PARSER" ]; then
  echo "✅ PASS: slotParser exists"

  # Check for LLM imports
  if grep -q "import.*openai\|import.*anthropic\|from.*llm\|import.*gpt" "$SLOT_PARSER"; then
    echo "❌ FAIL: slotParser contains LLM imports"
    FAIL=1
  else
    echo "✅ PASS: slotParser has NO LLM imports"
  fi
else
  echo "❌ FAIL: slotParser not found"
  FAIL=1
fi

# Check 3: /api/q2/coverage_candidates route exists
echo "[CHECK 3] /api/q2/coverage_candidates route must exist..."
COV_CAND_ROUTE="$WEB_ROOT/app/api/q2/coverage_candidates/route.ts"
if [ -f "$COV_CAND_ROUTE" ]; then
  echo "✅ PASS: /api/q2/coverage_candidates route exists"
else
  echo "❌ FAIL: /api/q2/coverage_candidates route not found"
  FAIL=1
fi

# Check 4: /api/q2/compare route exists
echo "[CHECK 4] /api/q2/compare route must exist..."
COMPARE_ROUTE="$WEB_ROOT/app/api/q2/compare/route.ts"
if [ -f "$COMPARE_ROUTE" ]; then
  echo "✅ PASS: /api/q2/compare route exists"
else
  echo "❌ FAIL: /api/q2/compare route not found"
  FAIL=1
fi

# Check 5: q2/page.tsx renders Q2ChatPanel
echo "[CHECK 5] q2/page.tsx must render Q2ChatPanel..."
Q2_PAGE="$WEB_ROOT/app/q2/page.tsx"
if [ -f "$Q2_PAGE" ]; then
  if grep -q "Q2ChatPanel" "$Q2_PAGE"; then
    echo "✅ PASS: q2/page.tsx renders Q2ChatPanel"
  else
    echo "❌ FAIL: q2/page.tsx does not render Q2ChatPanel"
    FAIL=1
  fi
else
  echo "❌ FAIL: q2/page.tsx not found"
  FAIL=1
fi

# Check 6: Q2 result components have NO forbidden terms (reuse existing gate)
echo "[CHECK 6] Q2 result components must have NO forbidden terms..."
FORBIDDEN_TERMS='근거|출처|사유|기준|산출|공식|배수|multiplier|formula'
Q2_LIMIT_VIEW="$WEB_ROOT/components/chat/Q2LimitDiffView.tsx"

if [ -f "$Q2_LIMIT_VIEW" ]; then
  if grep -E "$FORBIDDEN_TERMS" "$Q2_LIMIT_VIEW" > /dev/null 2>&1; then
    echo "❌ FAIL: Q2LimitDiffView contains forbidden terms"
    FAIL=1
  else
    echo "✅ PASS: Q2LimitDiffView has NO forbidden terms"
  fi
else
  echo "❌ FAIL: Q2LimitDiffView not found"
  FAIL=1
fi

# Check 7: NO preset buttons/text in Q2 page
echo "[CHECK 7] Q2 page must have NO preset buttons..."
if [ -f "$Q2_PAGE" ]; then
  # Look for actual preset UI patterns (not comments about NO preset)
  if grep -E "preset.*label|PRESETS.*=|2개.*label|4개.*label|8개 전체.*button" "$Q2_PAGE" > /dev/null 2>&1; then
    echo "❌ FAIL: Q2 page contains preset button UI"
    FAIL=1
  else
    echo "✅ PASS: Q2 page has NO preset buttons"
  fi
fi

# Check 8: NO legacy UI imports in Q2 page
echo "[CHECK 8] Q2 page must have NO legacy UI imports..."
if [ -f "$Q2_PAGE" ]; then
  if grep -E "demo-q12|Q12ReportView|CustomerHub.*legacy" "$Q2_PAGE" > /dev/null 2>&1; then
    echo "❌ FAIL: Q2 page contains legacy UI imports"
    FAIL=1
  else
    echo "✅ PASS: Q2 page has NO legacy UI imports"
  fi
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2 CHAT MODE GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2 CHAT MODE GATE: FAILED"
  echo "========================================="
  exit 1
fi
