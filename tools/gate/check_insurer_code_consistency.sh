#!/bin/bash

# CHECK INSURER CODE CONSISTENCY GATE
# Purpose: Verify ins_cd → insurer mapping consistency across all systems
# Usage: ./tools/gate/check_insurer_code_consistency.sh
# Exit codes: 0 (all pass), 1 (at least one failure)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AUDIT_DIR="$PROJECT_ROOT/docs/audit"

echo "========================================="
echo "INSURER CODE CONSISTENCY GATE"
echo "========================================="
echo ""

EXIT_CODE=0

# Database connection
DB_URL="${SSOT_DB_URL:-postgresql://postgres:postgres@localhost:5433/inca_ssot}"
export PGPASSWORD=postgres

# CHECK 1: insurer table vs SSOT Excel
echo "[CHECK 1] insurer table vs SSOT Excel"
echo "--------------------------------------"

INSURER_SNAPSHOT=$(psql "$DB_URL" -t -c "
SELECT ins_cd, insurer_name_ko
FROM insurer
ORDER BY ins_cd;
" | grep -v '^$')

# Expected from SSOT
EXPECTED_N03=$(echo "$INSURER_SNAPSHOT" | grep "N03" | awk '{print $3}')
EXPECTED_N13=$(echo "$INSURER_SNAPSHOT" | grep "N13" | awk '{print $3}')

if [ "$EXPECTED_N03" = "롯데" ] && [ "$EXPECTED_N13" = "DB" ]; then
  echo "✅ PASS: insurer table matches SSOT (N03=롯데, N13=DB)"
else
  echo "❌ FAIL: insurer table mismatch (N03=$EXPECTED_N03, N13=$EXPECTED_N13)"
  EXIT_CODE=1
fi
echo ""

# CHECK 2: Product brand consistency
echo "[CHECK 2] Product brand consistency (N03/N13)"
echo "--------------------------------------"

N03_BRANDS=$(psql "$DB_URL" -t -c "
SELECT product_full_name
FROM product
WHERE ins_cd = 'N03';
" | grep -i "let:smile" | wc -l | tr -d ' ')

N13_BRANDS=$(psql "$DB_URL" -t -c "
SELECT product_full_name
FROM product
WHERE ins_cd = 'N13';
" | grep -i "프로미라이프" | wc -l | tr -d ' ')

if [ "$N03_BRANDS" -ge 1 ] && [ "$N13_BRANDS" -ge 1 ]; then
  echo "✅ PASS: N03 has let:smile ($N03_BRANDS products), N13 has 프로미라이프 ($N13_BRANDS products)"
else
  echo "❌ FAIL: Brand mismatch (N03 let:smile=$N03_BRANDS, N13 프로미라이프=$N13_BRANDS)"
  EXIT_CODE=1
fi
echo ""

# CHECK 3: Cross-contamination check
echo "[CHECK 3] Cross-contamination check"
echo "--------------------------------------"

N03_CONTAMINATION=$(psql "$DB_URL" -t -c "
SELECT COUNT(*)
FROM product
WHERE ins_cd = 'N03'
  AND (product_full_name LIKE '%프로미라이프%' OR product_full_name LIKE '%DB%');
" | tr -d ' ')

N13_CONTAMINATION=$(psql "$DB_URL" -t -c "
SELECT COUNT(*)
FROM product
WHERE ins_cd = 'N13'
  AND (product_full_name LIKE '%let:smile%' OR product_full_name LIKE '%롯데%');
" | tr -d ' ')

if [ "$N03_CONTAMINATION" -eq 0 ] && [ "$N13_CONTAMINATION" -eq 0 ]; then
  echo "✅ PASS: No cross-contamination detected"
else
  echo "❌ FAIL: Contamination found (N03 DB brands=$N03_CONTAMINATION, N13 롯데 brands=$N13_CONTAMINATION)"
  EXIT_CODE=1
fi
echo ""

# CHECK 4: compare_table_v2 insurer_set format
echo "[CHECK 4] compare_table_v2 insurer_set"
echo "--------------------------------------"

COMPARE_TABLE_COUNT=$(psql "$DB_URL" -t -c "
SELECT COUNT(*)
FROM compare_table_v2
WHERE coverage_code IN ('A6200', 'A4200_1');
" | tr -d ' ')

if [ "$COMPARE_TABLE_COUNT" -ge 1 ]; then
  echo "✅ PASS: compare_table_v2 has $COMPARE_TABLE_COUNT rows for test coverages"
else
  echo "⚠️  WARNING: compare_table_v2 is empty or missing test coverages"
fi
echo ""

# CHECK 5: server.py INSURER_ENUM_TO_CODE (code inspection)
echo "[CHECK 5] server.py INSURER_ENUM_TO_CODE"
echo "--------------------------------------"

SERVER_PY="$PROJECT_ROOT/apps/api/server.py"

if grep -q '"LOTTE": "N03"' "$SERVER_PY" && grep -q '"DB": "N13"' "$SERVER_PY"; then
  echo "✅ PASS: server.py INSURER_ENUM_TO_CODE matches SSOT"
else
  echo "❌ FAIL: server.py INSURER_ENUM_TO_CODE does not match SSOT"
  EXIT_CODE=1
fi
echo ""

# CHECK 6: UI INSURER_NAMES (code inspection)
echo "[CHECK 6] UI INSURER_NAMES"
echo "--------------------------------------"

UI_FILE="$PROJECT_ROOT/apps/web/components/chat/Q2LimitDiffView.tsx"

if grep -q "N03.*롯데" "$UI_FILE" && grep -q "N13.*DB" "$UI_FILE"; then
  echo "✅ PASS: UI INSURER_NAMES matches SSOT"
else
  echo "❌ FAIL: UI INSURER_NAMES does not match SSOT"
  EXIT_CODE=1
fi
echo ""

# SUMMARY
echo "========================================="
echo "GATE SUMMARY"
echo "========================================="

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ ALL CHECKS PASSED"
  echo ""
  echo "Insurer code consistency is verified."
  echo "Safe to merge/deploy."
else
  echo "❌ ONE OR MORE CHECKS FAILED"
  echo ""
  echo "DO NOT MERGE until all checks pass."
  echo "Review docs/audit/INSURER_TABLE_SNAPSHOT.md and related documents."
fi
echo ""

exit $EXIT_CODE
