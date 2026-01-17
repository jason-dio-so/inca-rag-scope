#!/bin/bash
# Q1 Chat Gate Check
# Prevents Q1 chat from importing legacy UI or using LLM

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q1 CHAT GATE CHECK"
echo "========================================="

FAIL=0

# Check 1: Q1 page must not import legacy ChatPanel
echo "[CHECK 1] Q1 page must not import legacy ChatPanel..."
Q1_PAGE="$WEB_ROOT/app/q1/page.tsx"
if [ -f "$Q1_PAGE" ]; then
  if grep -q "from '@/components/chat/ChatPanel'" "$Q1_PAGE"; then
    echo "❌ FAIL: Q1 page imports legacy ChatPanel"
    grep -n "from '@/components/chat/ChatPanel'" "$Q1_PAGE"
    FAIL=1
  else
    echo "✅ PASS: Q1 page does not import legacy ChatPanel"
  fi
else
  echo "❌ FAIL: Q1 page not found"
  FAIL=1
fi

# Check 2: Q1ChatPanel must exist
echo "[CHECK 2] Q1ChatPanel component must exist..."
Q1_CHAT_PANEL="$WEB_ROOT/components/q1/Q1ChatPanel.tsx"
if [ -f "$Q1_CHAT_PANEL" ]; then
  echo "✅ PASS: Q1ChatPanel exists"
else
  echo "❌ FAIL: Q1ChatPanel not found"
  FAIL=1
fi

# Check 3: slotParser must exist
echo "[CHECK 3] slotParser utility must exist..."
SLOT_PARSER="$WEB_ROOT/lib/q1/slotParser.ts"
if [ -f "$SLOT_PARSER" ]; then
  echo "✅ PASS: slotParser exists"
else
  echo "❌ FAIL: slotParser not found"
  FAIL=1
fi

# Check 4: slotParser must not have LLM imports or API calls
echo "[CHECK 4] slotParser must not have LLM imports or API calls..."
if [ -f "$SLOT_PARSER" ]; then
  if grep -q "from.*openai\|from.*anthropic\|import.*openai\|import.*anthropic\|fetch.*openai\|fetch.*anthropic" "$SLOT_PARSER"; then
    echo "❌ FAIL: slotParser contains LLM imports or API calls"
    grep -n "from.*openai\|from.*anthropic\|import.*openai\|import.*anthropic\|fetch.*openai\|fetch.*anthropic" "$SLOT_PARSER"
    FAIL=1
  else
    echo "✅ PASS: slotParser has no LLM imports or API calls"
  fi
fi

# Check 5: Q1ChatPanel must not import legacy UI
echo "[CHECK 5] Q1ChatPanel must not import legacy UI..."
if [ -f "$Q1_CHAT_PANEL" ]; then
  if grep -q "from '@/components/chat/\|from '@/components/sidebar/\|from '@/components/result_dock/" "$Q1_CHAT_PANEL"; then
    echo "❌ FAIL: Q1ChatPanel imports legacy UI"
    grep -n "from '@/components/chat/\|from '@/components/sidebar/\|from '@/components/result_dock/" "$Q1_CHAT_PANEL"
    FAIL=1
  else
    echo "✅ PASS: Q1ChatPanel does not import legacy UI"
  fi
fi

# Check 6: Q1 page must import Q1ChatPanel (not legacy ChatPanel)
echo "[CHECK 6] Q1 page must import Q1ChatPanel..."
if [ -f "$Q1_PAGE" ]; then
  if grep -q "from '@/components/q1/Q1ChatPanel'" "$Q1_PAGE"; then
    echo "✅ PASS: Q1 page imports Q1ChatPanel"
  else
    echo "❌ FAIL: Q1 page does not import Q1ChatPanel"
    FAIL=1
  fi
fi

# Check 7: Q1 page must use parseSlots
echo "[CHECK 7] Q1 page must use parseSlots from slotParser..."
if [ -f "$Q1_PAGE" ]; then
  if grep -q "parseSlots\|from '@/lib/q1/slotParser'" "$Q1_PAGE"; then
    echo "✅ PASS: Q1 page uses parseSlots"
  else
    echo "❌ FAIL: Q1 page does not use parseSlots"
    FAIL=1
  fi
fi

# Check 8: Q1 page must not have preset buttons (2/4/8)
echo "[CHECK 8] Q1 page must not have preset buttons..."
if [ -f "$Q1_PAGE" ]; then
  if grep -B2 -A2 "onClick.*preset\|onClick.*setSelectedInsurers.*2\|onClick.*setSelectedInsurers.*4\|onClick.*setSelectedInsurers.*8" "$Q1_PAGE" | grep -q "2개\|4개\|8개"; then
    echo "❌ FAIL: Q1 page contains preset button UI"
    grep -n "onClick.*preset\|onClick.*setSelectedInsurers" "$Q1_PAGE"
    FAIL=1
  else
    echo "✅ PASS: Q1 page has no preset buttons"
  fi
fi

# Check 9: BY_COVERAGE proxy route must exist
echo "[CHECK 9] BY_COVERAGE proxy route must exist..."
COVERAGE_ROUTE="$WEB_ROOT/app/api/q1/coverage_ranking/route.ts"
if [ -f "$COVERAGE_ROUTE" ]; then
  echo "✅ PASS: BY_COVERAGE proxy route exists"
else
  echo "❌ FAIL: BY_COVERAGE proxy route not found"
  FAIL=1
fi

# Check 10: Q1 page must call coverage_ranking endpoint
echo "[CHECK 10] Q1 page must call coverage_ranking endpoint..."
if [ -f "$Q1_PAGE" ]; then
  if grep -q "/api/q1/coverage_ranking\|executeCoverageRanking" "$Q1_PAGE"; then
    echo "✅ PASS: Q1 page calls coverage_ranking"
  else
    echo "❌ FAIL: Q1 page does not call coverage_ranking"
    FAIL=1
  fi
fi

# Check 11: coverage_candidates proxy route must exist
echo "[CHECK 11] coverage_candidates proxy route must exist..."
CANDIDATES_ROUTE="$WEB_ROOT/app/api/q1/coverage_candidates/route.ts"
if [ -f "$CANDIDATES_ROUTE" ]; then
  echo "✅ PASS: coverage_candidates proxy route exists"
else
  echo "❌ FAIL: coverage_candidates proxy route not found"
  FAIL=1
fi

# Check 12: Q1 page must call coverage_candidates endpoint
echo "[CHECK 12] Q1 page must call coverage_candidates endpoint..."
if [ -f "$Q1_PAGE" ]; then
  if grep -q "/api/q1/coverage_candidates" "$Q1_PAGE"; then
    echo "✅ PASS: Q1 page calls coverage_candidates"
  else
    echo "❌ FAIL: Q1 page does not call coverage_candidates"
    FAIL=1
  fi
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q1 CHAT GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q1 CHAT GATE: FAILED"
  echo "========================================="
  exit 1
fi
