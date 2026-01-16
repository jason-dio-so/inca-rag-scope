#!/usr/bin/env bash
# ========================================
# DB SSOT LOCK — Grep Gate
# ========================================
#
# Purpose: Detect forbidden DB patterns in codebase to prevent regression
# Exit 0: PASS (no violations)
# Exit 1: FAIL (violations found, must be fixed)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Forbidden patterns
PATTERNS=(
  "inca_rag_scope"
  ":5432/"
  "localhost:5432"
  "inca_admin:inca_secure_prod_2025_db_key"
)

# Whitelist: Files/directories allowed to contain forbidden patterns
# (documentation, docker configs, archived files, backup files)
WHITELIST=(
  "docs/policy/PREMIUM_LEGACY_DO_NOT_USE.md"
  "docs/policy/DB_SSOT_LOCK.md"
  "docs/audit"
  "docs/archive"
  "docs/deploy"
  "docs/ui/FINAL_VIEWMODEL_LOCK.md"
  "STEP_NEXT_10_COMPLETION_REPORT.md"
  "STEP_NEXT_13_COMPLETION.md"
  "STATUS.md"
  ".env.ssot"
  "tools/gate/check_db_ssot_lock.sh"
  "docker"
  ".git"
  "node_modules"
  ".next"
  "__pycache__"
  ".venv"
  "venv"
  "*.bak"
  "*.backup"
)

# Build grep exclude arguments
EXCLUDE_ARGS=""
for item in "${WHITELIST[@]}"; do
  EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude-dir=$item --exclude=$item"
done

# Also explicitly exclude backup files
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=*.bak --exclude=*.backup"

echo "========================================="
echo "DB SSOT LOCK — Grep Gate"
echo "========================================="
echo ""
echo "Searching for forbidden DB patterns..."
echo ""

VIOLATIONS_FOUND=0

for pattern in "${PATTERNS[@]}"; do
  echo "Checking pattern: '$pattern'"

  # Search with grep
  # -r: recursive
  # -n: line numbers
  # -I: ignore binary files
  # --color=always: colorize output
  if grep -r -n -I --color=always $EXCLUDE_ARGS "$pattern" . 2>/dev/null; then
    echo "  ❌ VIOLATION: Pattern '$pattern' found"
    VIOLATIONS_FOUND=1
  else
    echo "  ✓ OK: Pattern '$pattern' not found"
  fi
  echo ""
done

echo "========================================="

if [ $VIOLATIONS_FOUND -eq 1 ]; then
  echo "❌ GREP GATE FAILED"
  echo ""
  echo "Forbidden DB patterns detected in codebase."
  echo "Action required:"
  echo "  1. Replace with SSOT_DB_URL from .env.ssot"
  echo "  2. Or add file to whitelist in tools/gate/check_db_ssot_lock.sh"
  echo ""
  echo "See: docs/policy/DB_SSOT_LOCK.md"
  exit 1
else
  echo "✅ GREP GATE PASSED"
  echo ""
  echo "No forbidden DB patterns found."
  echo "SSOT enforcement: inca_ssot@5433 only"
  exit 0
fi
