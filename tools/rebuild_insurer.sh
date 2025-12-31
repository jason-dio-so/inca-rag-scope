#!/usr/bin/env bash
#
# STEP NEXT-31-P3: Atomic Rebuild Script for Single Insurer
#
# Usage: ./tools/rebuild_insurer.sh <insurer>
# Example: ./tools/rebuild_insurer.sh hanwha
#
# This script performs atomic rebuild of pipeline artifacts for a single insurer:
# 1. Removes all generated files (scope, evidence_pack, coverage_cards)
# 2. Re-runs canonical pipeline steps (step1 → step2 → sanitize → step3 → step4 → step5)
# 3. Ensures content-hash consistency (STEP NEXT-31-P3)
#

set -euo pipefail  # Exit on error, undefined var, pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory (assume run from project root or tools/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Insurer from argument
if [ $# -ne 1 ]; then
    echo -e "${RED}Error: Missing insurer argument${NC}"
    echo "Usage: $0 <insurer>"
    echo "Example: $0 hanwha"
    exit 1
fi

INSURER="$1"

echo -e "${GREEN}[STEP NEXT-31-P3 Atomic Rebuild]${NC}"
echo -e "Insurer: ${YELLOW}${INSURER}${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Remove generated files (insurer-specific)
echo -e "${YELLOW}[1/7] Removing generated files for ${INSURER}...${NC}"

# Scope files
rm -f "data/scope/${INSURER}_scope.csv"
rm -f "data/scope/${INSURER}_scope_mapped.csv"
rm -f "data/scope/${INSURER}_scope_mapped.sanitized.csv"
rm -f "data/scope/${INSURER}_scope_filtered_out.jsonl"
rm -f "data/scope/${INSURER}_unmatched_review.csv"

# Evidence pack
rm -f "data/evidence_pack/${INSURER}_evidence_pack.jsonl"

# Coverage cards (SSOT)
rm -f "data/compare/${INSURER}_coverage_cards.jsonl"

echo -e "${GREEN}✓ Removed generated files${NC}"

# Step 2: Extract scope from proposal PDF
echo -e "${YELLOW}[2/7] Extracting scope (step1_extract_scope)...${NC}"
python -m pipeline.step1_extract_scope.run --insurer "$INSURER"
echo -e "${GREEN}✓ step1_extract_scope complete${NC}"

# Step 3: Canonical mapping
echo -e "${YELLOW}[3/7] Canonical mapping (step2_canonical_mapping)...${NC}"
python -m pipeline.step2_canonical_mapping.map_to_canonical --insurer "$INSURER"
echo -e "${GREEN}✓ step2_canonical_mapping complete${NC}"

# Step 4: Sanitize scope
echo -e "${YELLOW}[4/7] Sanitizing scope (step1_sanitize_scope)...${NC}"
python -m pipeline.step1_sanitize_scope.run --insurer "$INSURER"
echo -e "${GREEN}✓ step1_sanitize_scope complete${NC}"

# Step 5: Extract text from PDFs (if needed, can be skipped if evidence_text already exists)
echo -e "${YELLOW}[5/7] Extracting evidence text (step3_extract_text)...${NC}"
if [ -d "data/evidence_text/${INSURER}" ]; then
    echo -e "${GREEN}✓ evidence_text already exists, skipping step3_extract_text${NC}"
else
    python -m pipeline.step3_extract_text.run --insurer "$INSURER"
    echo -e "${GREEN}✓ step3_extract_text complete${NC}"
fi

# Step 6: Search evidence (with content-hash)
echo -e "${YELLOW}[6/7] Searching evidence (step4_evidence_search)...${NC}"
python -m pipeline.step4_evidence_search.search_evidence --insurer "$INSURER"
echo -e "${GREEN}✓ step4_evidence_search complete (meta record + content-hash)${NC}"

# Step 7: Build coverage cards (SSOT)
echo -e "${YELLOW}[7/7] Building coverage cards (step5_build_cards)...${NC}"
python -m pipeline.step5_build_cards.build_cards --insurer "$INSURER"
echo -e "${GREEN}✓ step5_build_cards complete (SSOT)${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Atomic rebuild complete for ${INSURER}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Verification:"
echo "  - Scope: data/scope/${INSURER}_scope_mapped.sanitized.csv"
echo "  - Evidence pack (with meta): data/evidence_pack/${INSURER}_evidence_pack.jsonl"
echo "  - Coverage cards (SSOT): data/compare/${INSURER}_coverage_cards.jsonl"
echo ""
echo "Check evidence_status:"
echo "  jq -r '.evidence_status' data/compare/${INSURER}_coverage_cards.jsonl | sort | uniq -c"
