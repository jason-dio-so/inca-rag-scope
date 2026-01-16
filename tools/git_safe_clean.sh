#!/usr/bin/env bash
set -euo pipefail
echo "[SAFE CLEAN] Backing up git state..."
mkdir -p /tmp/inca_git_rescue
git status --porcelain=v1 > /tmp/inca_git_rescue/git_status.txt || true
git diff > /tmp/inca_git_rescue/git_diff.patch || true
git ls-files -o --exclude-standard > /tmp/inca_git_rescue/untracked_files.txt || true
echo "Backup saved to /tmp/inca_git_rescue"
echo "If you REALLY want to clean, run: git clean -fdx"
