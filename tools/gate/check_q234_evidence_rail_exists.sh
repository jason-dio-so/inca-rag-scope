#!/bin/bash
# Q2-Q4 Evidence Rail Existence Gate Check
# Ensures Evidence Rails are implemented for Q2-Q4

set -e

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
WEB_ROOT="$REPO_ROOT/apps/web"

echo "========================================="
echo "Q2-Q4 EVIDENCE RAIL EXISTENCE GATE"
echo "========================================="

FAIL=0

# Check 1: EvidenceRailBase component exists
echo "[CHECK 1] EvidenceRailBase component must exist..."
RAIL_BASE="$WEB_ROOT/components/evidence/EvidenceRailBase.tsx"
if [ -f "$RAIL_BASE" ]; then
  echo "✅ PASS: EvidenceRailBase exists"
else
  echo "❌ FAIL: EvidenceRailBase not found"
  FAIL=1
fi

# Check 2: Q2EvidenceRail component exists
echo "[CHECK 2] Q2EvidenceRail component must exist..."
Q2_RAIL="$WEB_ROOT/components/q2/Q2EvidenceRail.tsx"
if [ -f "$Q2_RAIL" ]; then
  echo "✅ PASS: Q2EvidenceRail exists"
else
  echo "❌ FAIL: Q2EvidenceRail not found"
  FAIL=1
fi

# Check 3: Q3EvidenceRail component exists
echo "[CHECK 3] Q3EvidenceRail component must exist..."
Q3_RAIL="$WEB_ROOT/components/q3/Q3EvidenceRail.tsx"
if [ -f "$Q3_RAIL" ]; then
  echo "✅ PASS: Q3EvidenceRail exists"
else
  echo "❌ FAIL: Q3EvidenceRail not found"
  FAIL=1
fi

# Check 4: Q4EvidenceRail component exists
echo "[CHECK 4] Q4EvidenceRail component must exist..."
Q4_RAIL="$WEB_ROOT/components/q4/Q4EvidenceRail.tsx"
if [ -f "$Q4_RAIL" ]; then
  echo "✅ PASS: Q4EvidenceRail exists"
else
  echo "❌ FAIL: Q4EvidenceRail not found"
  FAIL=1
fi

# Check 5: Q2LimitDiffView exports Q2Row interface
echo "[CHECK 5] Q2LimitDiffView must export Q2Row interface..."
Q2_VIEW="$WEB_ROOT/components/chat/Q2LimitDiffView.tsx"
if [ -f "$Q2_VIEW" ]; then
  if grep -q "export interface Q2Row" "$Q2_VIEW"; then
    echo "✅ PASS: Q2Row interface exported"
  else
    echo "❌ FAIL: Q2Row interface not exported"
    FAIL=1
  fi
else
  echo "❌ FAIL: Q2LimitDiffView not found"
  FAIL=1
fi

# Check 6: Q2LimitDiffView has onRowClick prop
echo "[CHECK 6] Q2LimitDiffView must have onRowClick prop..."
if [ -f "$Q2_VIEW" ]; then
  if grep -q "onRowClick" "$Q2_VIEW"; then
    echo "✅ PASS: Q2LimitDiffView has onRowClick support"
  else
    echo "❌ FAIL: Q2LimitDiffView missing onRowClick"
    FAIL=1
  fi
fi

# Check 7: Evidence Rail components use EvidenceRailBase
echo "[CHECK 7] Evidence Rails must use EvidenceRailBase..."
RAIL_CHECKS=0
for RAIL_FILE in "$Q2_RAIL" "$Q3_RAIL" "$Q4_RAIL"; do
  if [ -f "$RAIL_FILE" ]; then
    if grep -q "EvidenceRailBase" "$RAIL_FILE"; then
      RAIL_CHECKS=$((RAIL_CHECKS + 1))
    fi
  fi
done
if [ $RAIL_CHECKS -eq 3 ]; then
  echo "✅ PASS: All Evidence Rails use EvidenceRailBase"
else
  echo "❌ FAIL: Not all Evidence Rails use EvidenceRailBase ($RAIL_CHECKS/3)"
  FAIL=1
fi

echo "========================================="
if [ $FAIL -eq 0 ]; then
  echo "✅ Q2-Q4 EVIDENCE RAIL EXISTENCE GATE: ALL CHECKS PASSED"
  echo "========================================="
  exit 0
else
  echo "❌ Q2-Q4 EVIDENCE RAIL EXISTENCE GATE: FAILED"
  echo "========================================="
  exit 1
fi
