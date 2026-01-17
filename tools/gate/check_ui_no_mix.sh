#!/bin/bash
# UI Mixing Prevention Gate
# Prevents legacy UI and Chat UI v2 from mixing

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "UI NO-MIX GATE CHECK"
echo "========================================="

FAIL=0

# Check 1: /chat MUST NOT have legacy UI components
echo "[CHECK 1] /chat must not import legacy UI components..."
CHAT_PAGE="$WEB_ROOT/app/chat/page.tsx"
if [ -f "$CHAT_PAGE" ]; then
  if grep -q "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|EX3ReportView\|보험 상품 비교 도우미\|옵션 숨기기\|LLM: OFF" "$CHAT_PAGE"; then
    echo "❌ FAIL: /chat page contains legacy UI elements"
    grep -n "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|EX3ReportView\|보험 상품 비교 도우미\|옵션 숨기기\|LLM: OFF" "$CHAT_PAGE"
    FAIL=1
  else
    echo "✅ PASS: /chat has no legacy UI elements"
  fi
else
  echo "❌ FAIL: /chat/page.tsx not found"
  FAIL=1
fi

# Check 2: root (/) MUST NOT have Chat UI v2 components
echo "[CHECK 2] root (/) must not import Chat UI v2 components..."
ROOT_PAGE="$WEB_ROOT/app/page.tsx"
if [ -f "$ROOT_PAGE" ]; then
  if grep -q "Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView\|Evidence Rail\|kind === 'Q1'\|비교 조건 설정" "$ROOT_PAGE"; then
    echo "❌ FAIL: root (/) page contains Chat UI v2 elements"
    grep -n "Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView\|Evidence Rail\|kind === 'Q1'\|비교 조건 설정" "$ROOT_PAGE"
    FAIL=1
  else
    echo "✅ PASS: root (/) has no Chat UI v2 elements"
  fi
else
  echo "❌ FAIL: root page.tsx not found"
  FAIL=1
fi

# Check 3: Chat UI v2 components must be in @/components/chat
echo "[CHECK 3] Chat UI v2 components in correct directory..."
if [ -d "$WEB_ROOT/components/chat" ]; then
  V2_COMPONENTS=$(ls "$WEB_ROOT/components/chat" | grep -c "View.tsx" || true)
  if [ "$V2_COMPONENTS" -ge 4 ]; then
    echo "✅ PASS: Found $V2_COMPONENTS Chat UI v2 view components"
  else
    echo "❌ FAIL: Expected 4+ Chat UI v2 views, found $V2_COMPONENTS"
    FAIL=1
  fi
else
  echo "❌ FAIL: @/components/chat directory not found"
  FAIL=1
fi

# Check 4: API route exists
echo "[CHECK 4] /api/chat_query route exists..."
API_ROUTE="$WEB_ROOT/app/api/chat_query/route.ts"
if [ -f "$API_ROUTE" ]; then
  echo "✅ PASS: /api/chat_query/route.ts exists"
else
  echo "❌ FAIL: /api/chat_query/route.ts not found"
  FAIL=1
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ UI NO-MIX GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ UI NO-MIX GATE: FAILED"
  echo "========================================="
  exit 1
fi
