#!/bin/bash
# Customer Hub Gate Check
# Prevents customer hub from importing legacy/chat UI

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "CUSTOMER HUB GATE CHECK"
echo "========================================="

FAIL=0

# Check 1: Root page MUST NOT have legacy UI imports
echo "[CHECK 1] Root page must not import legacy UI..."
ROOT_PAGE="$WEB_ROOT/app/page.tsx"
if [ -f "$ROOT_PAGE" ]; then
  if grep -q "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|EX3ReportView\|보험 상품 비교 도우미\|옵션 숨기기\|LLM: OFF" "$ROOT_PAGE"; then
    echo "❌ FAIL: Root page contains legacy UI elements"
    grep -n "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|EX3ReportView\|보험 상품 비교 도우미\|옵션 숨기기\|LLM: OFF" "$ROOT_PAGE"
    FAIL=1
  else
    echo "✅ PASS: Root page has no legacy UI elements"
  fi
else
  echo "❌ FAIL: Root page.tsx not found"
  FAIL=1
fi

# Check 2: Root page MUST NOT have Chat UI v2 imports
echo "[CHECK 2] Root page must not import Chat UI v2..."
if grep -q "Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView\|Evidence Rail\|kind === 'Q1'\|비교 조건 설정" "$ROOT_PAGE"; then
  echo "❌ FAIL: Root page contains Chat UI v2 elements"
  grep -n "Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView\|Evidence Rail\|kind === 'Q1'\|비교 조건 설정" "$ROOT_PAGE"
  FAIL=1
else
  echo "✅ PASS: Root page has no Chat UI v2 elements"
fi

# Check 3: Q1~Q4 routes must exist
echo "[CHECK 3] Q1~Q4 routes must exist..."
Q_ROUTES_MISSING=0
for i in 1 2 3 4; do
  Q_PAGE="$WEB_ROOT/app/q$i/page.tsx"
  if [ ! -f "$Q_PAGE" ]; then
    echo "❌ FAIL: /q$i route not found"
    Q_ROUTES_MISSING=1
  fi
done

if [ $Q_ROUTES_MISSING -eq 0 ]; then
  echo "✅ PASS: All Q1~Q4 routes exist"
else
  FAIL=1
fi

# Check 4: CustomerHub components exist
echo "[CHECK 4] CustomerHub components must exist..."
CUSTOMER_HUB="$WEB_ROOT/components/customer_hub/CustomerHub.tsx"
Q_CARD="$WEB_ROOT/components/customer_hub/QCard.tsx"

if [ -f "$CUSTOMER_HUB" ] && [ -f "$Q_CARD" ]; then
  echo "✅ PASS: CustomerHub components exist"
else
  echo "❌ FAIL: CustomerHub components not found"
  FAIL=1
fi

# Check 5: Q routes must not import legacy/chat UI
echo "[CHECK 5] Q routes must not import legacy/chat UI..."
Q_ROUTES_CLEAN=1
for i in 1 2 3 4; do
  Q_PAGE="$WEB_ROOT/app/q$i/page.tsx"
  if [ -f "$Q_PAGE" ]; then
    if grep -q "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView" "$Q_PAGE"; then
      echo "❌ FAIL: /q$i imports legacy/chat UI"
      grep -n "SidebarCategories\|ChatPanel\|ResultDock\|LlmModeToggle\|Q1PremiumView\|Q2LimitDiffView\|Q3ThreePartView\|Q4SupportMatrixView" "$Q_PAGE"
      Q_ROUTES_CLEAN=0
    fi
  fi
done

if [ $Q_ROUTES_CLEAN -eq 1 ]; then
  echo "✅ PASS: All Q routes are clean"
else
  FAIL=1
fi

# Check 6: NO preset button UI (검사: button/onClick와 함께 나오는 2개/4개/8개 패턴)
echo "[CHECK 6] Customer hub must not have preset button UI..."
PRESET_FOUND=0
CUSTOMER_HUB_FILES=$(find "$WEB_ROOT/components/customer_hub" "$WEB_ROOT/app/q1" "$WEB_ROOT/app/q2" "$WEB_ROOT/app/q3" "$WEB_ROOT/app/q4" -name "*.tsx" 2>/dev/null || true)

for file in $CUSTOMER_HUB_FILES; do
  # Look for preset button patterns (button text with 2개/4개/8개)
  if grep -B2 -A2 "onClick.*preset\|onClick.*setSelectedInsurers.*2\|onClick.*setSelectedInsurers.*4\|onClick.*setSelectedInsurers.*8" "$file" | grep -q "2개\|4개\|8개"; then
    echo "❌ FAIL: Preset button UI found in $(basename $file)"
    grep -n "onClick.*preset\|onClick.*setSelectedInsurers" "$file"
    PRESET_FOUND=1
  fi
done

if [ $PRESET_FOUND -eq 0 ]; then
  echo "✅ PASS: No preset button UI found"
else
  FAIL=1
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ CUSTOMER HUB GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ CUSTOMER HUB GATE: FAILED"
  echo "========================================="
  exit 1
fi
