#!/bin/bash
# Q2-Q4 Result/Evidence Separation Gate Check
# Prevents explanation terms in result components (global terminology lock)

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q2-Q4 RESULT/EVIDENCE SEPARATION GATE"
echo "========================================="

FAIL=0

# Forbidden terms that should ONLY appear in Evidence Rail components
FORBIDDEN_TERMS='근거|출처|사유|기준|산출|공식|배수|multiplier|formula'

# Check 1: Q2 Result components must NOT contain forbidden terms
echo "[CHECK 1] Q2 Result components must NOT contain forbidden terms..."
Q2_CHAT_VIEW="$WEB_ROOT/components/chat/Q2LimitDiffView.tsx"
if [ -f "$Q2_CHAT_VIEW" ]; then
  Q2_VIOLATIONS=$(grep -E "$FORBIDDEN_TERMS" "$Q2_CHAT_VIEW" | grep -v "//.*\(근거\|출처\|사유\)" || true)
  if [ -n "$Q2_VIOLATIONS" ]; then
    echo "❌ FAIL: Q2LimitDiffView contains forbidden explanation terms"
    echo "$Q2_VIOLATIONS" | head -10
    FAIL=1
  else
    echo "✅ PASS: Q2LimitDiffView has no forbidden terms"
  fi
else
  echo "⚠️  SKIP: Q2LimitDiffView not found"
fi

# Check 2: Q3 Result components must NOT contain forbidden terms
echo "[CHECK 2] Q3 Result components must NOT contain forbidden terms..."
Q3_CHAT_VIEW="$WEB_ROOT/components/chat/Q3ThreePartView.tsx"
if [ -f "$Q3_CHAT_VIEW" ]; then
  Q3_VIOLATIONS=$(grep -E "$FORBIDDEN_TERMS" "$Q3_CHAT_VIEW" | grep -v "//.*\(근거\|출처\|사유\)" || true)
  if [ -n "$Q3_VIOLATIONS" ]; then
    echo "❌ FAIL: Q3ThreePartView contains forbidden explanation terms"
    echo "$Q3_VIOLATIONS" | head -10
    FAIL=1
  else
    echo "✅ PASS: Q3ThreePartView has no forbidden terms"
  fi
else
  echo "⚠️  SKIP: Q3ThreePartView not found"
fi

# Check 3: Q4 Result components must NOT contain forbidden terms
echo "[CHECK 3] Q4 Result components must NOT contain forbidden terms..."
Q4_CHAT_VIEW="$WEB_ROOT/components/chat/Q4SupportMatrixView.tsx"
if [ -f "$Q4_CHAT_VIEW" ]; then
  Q4_VIOLATIONS=$(grep -E "$FORBIDDEN_TERMS" "$Q4_CHAT_VIEW" | grep -v "//.*\(근거\|출처\|사유\)" || true)
  if [ -n "$Q4_VIOLATIONS" ]; then
    echo "❌ FAIL: Q4SupportMatrixView contains forbidden explanation terms"
    echo "$Q4_VIOLATIONS" | head -10
    FAIL=1
  else
    echo "✅ PASS: Q4SupportMatrixView has no forbidden terms"
  fi
else
  echo "⚠️  SKIP: Q4SupportMatrixView not found"
fi

# Check 4: Q2-Q4 pages must NOT contain forbidden terms (except imports/evidence rail usage)
echo "[CHECK 4] Q2-Q4 pages must NOT contain forbidden terms in result areas..."
for Q_NUM in 2 3 4; do
  Q_PAGE="$WEB_ROOT/app/q${Q_NUM}/page.tsx"
  if [ -f "$Q_PAGE" ]; then
    # Exclude import lines and EvidenceRail component references
    PAGE_VIOLATIONS=$(grep -E "$FORBIDDEN_TERMS" "$Q_PAGE" | grep -v "import.*EvidenceRail" | grep -v "EvidenceRail" | grep -v "//.*\(근거\|출처\|사유\)" || true)
    if [ -n "$PAGE_VIOLATIONS" ]; then
      echo "❌ FAIL: Q${Q_NUM} page contains forbidden terms in result area"
      echo "$PAGE_VIOLATIONS" | head -10
      FAIL=1
    else
      echo "✅ PASS: Q${Q_NUM} page has no forbidden terms in result area"
    fi
  else
    echo "⚠️  SKIP: Q${Q_NUM} page not found yet"
  fi
done

# Check 5: Forbidden percentage symbols in result tables
echo "[CHECK 5] Q2-Q4 must NOT contain % symbols in result components..."
PERCENT_CHECK_PASS=1
for VIEW_FILE in "$WEB_ROOT/components/chat/Q2LimitDiffView.tsx" "$WEB_ROOT/components/chat/Q3ThreePartView.tsx" "$WEB_ROOT/components/chat/Q4SupportMatrixView.tsx"; do
  if [ -f "$VIEW_FILE" ]; then
    # Check for % symbols (exclude comments and allow 100% as context word)
    PERCENT_VIOLATIONS=$(grep "%" "$VIEW_FILE" | grep -v "//.*%" | grep -v "100%" | grep -v "/\*.*%.*\*/" || true)
    if [ -n "$PERCENT_VIOLATIONS" ]; then
      echo "❌ FAIL: $(basename $VIEW_FILE) contains % symbols"
      echo "$PERCENT_VIOLATIONS" | head -5
      PERCENT_CHECK_PASS=0
      FAIL=1
    fi
  fi
done
if [ $PERCENT_CHECK_PASS -eq 1 ]; then
  echo "✅ PASS: No percentage symbols found in result components"
fi

# Check 6: Evidence Rail components must exist for complete Q implementations
echo "[CHECK 6] Evidence Rail components should exist for Q2-Q4..."
RAIL_FOUND=0
for Q_NUM in 2 3 4; do
  Q_RAIL="$WEB_ROOT/components/q${Q_NUM}/Q${Q_NUM}EvidenceRail.tsx"
  if [ -f "$Q_RAIL" ]; then
    echo "✅ PASS: Q${Q_NUM}EvidenceRail exists"
    RAIL_FOUND=$((RAIL_FOUND + 1))
  else
    echo "⚠️  INFO: Q${Q_NUM}EvidenceRail not found (implementation may be incomplete)"
  fi
done

# Check 7: Approved terminology in footer/helper text
echo "[CHECK 7] Q2-Q4 must use approved neutral terminology..."
FORBIDDEN_FOOTER_TERMS='근거를 확인|출처 보기|기준 확인|산출식 확인'
FOOTER_CHECK_PASS=1
for VIEW_FILE in "$WEB_ROOT/components/chat/Q2LimitDiffView.tsx" "$WEB_ROOT/components/chat/Q3ThreePartView.tsx" "$WEB_ROOT/components/chat/Q4SupportMatrixView.tsx"; do
  if [ -f "$VIEW_FILE" ]; then
    FOOTER_VIOLATIONS=$(grep -E "$FORBIDDEN_FOOTER_TERMS" "$VIEW_FILE" || true)
    if [ -n "$FOOTER_VIOLATIONS" ]; then
      echo "❌ FAIL: $(basename $VIEW_FILE) uses forbidden footer terminology"
      echo "$FOOTER_VIOLATIONS" | head -5
      FOOTER_CHECK_PASS=0
      FAIL=1
    fi
  fi
done
if [ $FOOTER_CHECK_PASS -eq 1 ]; then
  echo "✅ PASS: Approved terminology in use"
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2-Q4 RESULT/EVIDENCE GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2-Q4 RESULT/EVIDENCE GATE: FAILED"
  echo "========================================="
  exit 1
fi
