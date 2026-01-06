#!/bin/bash
# STEP C: Safe Cleanup Script
# Baseline: HEAD=3a31976
# WARNING: Review STEP_C_CLEANUP_INVENTORY.md before executing

set -e

echo "=== STEP C: Cleanup Script ==="
echo "Baseline: HEAD=$(git log -1 --oneline)"
echo ""

# Safety check
read -p "Have you reviewed docs/audit/STEP_C_CLEANUP_INVENTORY.md? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Cleanup aborted. Please review inventory first."
    exit 1
fi

echo ""
echo "=== Pre-cleanup Verification ==="
git status -sb
echo ""

# Phase 1: Archive completion reports
echo "Phase 1: Archiving STEP_NEXT completion reports..."
mkdir -p archive/step_completion_reports
git mv STEP_NEXT_*_COMPLETION*.md archive/step_completion_reports/ 2>/dev/null || echo "No completion reports to move"
echo "✅ Phase 1 complete"
echo ""

# Phase 2: Root-level cleanup
echo "Phase 2: Removing root-level backups and ad-hoc files..."
rm -f STATUS.md.backup
rm -f simple_test.html test_api.html
echo "✅ Phase 2 complete"
echo ""

# Phase 3: Recovery artifacts
echo "Phase 3: Removing recovery artifacts..."
rm -rf _recovery_snapshots _triage_logs
echo "✅ Phase 3 complete"
echo ""

# Phase 4: Backup files
echo "Phase 4: Removing backup files..."
rm -f apps/api/server_v1.py.bak
rm -f data/sources/mapping/담보명mapping자료_backup_*.xlsx
echo "✅ Phase 4 complete"
echo ""

# Phase 5: Archive output directory
echo "Phase 5: Archiving output directory..."
if [ -d "output" ]; then
    mkdir -p archive/output_legacy
    mv output/* archive/output_legacy/ 2>/dev/null || echo "output/ empty or already moved"
    rmdir output 2>/dev/null || echo "output/ not empty, skipping rmdir"
fi
echo "✅ Phase 5 complete"
echo ""

# Verification
echo "=== Post-cleanup Verification ==="
echo "Git status:"
git status -sb
echo ""

echo "Running routing lock tests..."
PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py

echo ""
echo "Running smoke tests..."
bash tools/smoke/smoke_chat.sh | grep -E "^(===|Query:|Expected:)" | head -10

echo ""
echo "=== Cleanup Complete ==="
echo "Next step: Review git status and commit changes"
echo "Suggested commit message: See docs/audit/STEP_C_CLEANUP_INVENTORY.md Section 9"
