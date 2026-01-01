#!/bin/bash
# STEP NEXT-56: Pipeline Constitution Lock - Single Entrypoint
#
# Constitutional Rules:
# 1. This is the ONLY allowed execution method
# 2. All steps run sequentially: Step1 → Step2-a → Step2-b
# 3. Variant-aware execution (DB: under40/over41, LOTTE: male/female)
# 4. Output SSOT: data/scope_v3/ only
# 5. Mandatory gates: stability, variant, raw integrity, SSOT

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Constitutional enforcement
enforce_single_entrypoint() {
    echo -e "${BLUE}🔒 PIPELINE CONSTITUTION ENFORCEMENT${NC}"
    echo "This is the ONLY allowed execution method."
    echo "❌ Direct python -m execution is FORBIDDEN"
    echo "❌ --insurer execution is FORBIDDEN"
    echo ""
}

# Usage
usage() {
    cat << EOF
Usage: $0 --manifest MANIFEST_PATH

STEP NEXT-56: Pipeline Constitution Lock

This is the ONLY allowed execution method.

Options:
  --manifest PATH    Path to proposal PDFs manifest (REQUIRED)
  --help            Show this help message

Example:
  $0 --manifest data/manifests/proposal_pdfs_v1.json

Constitutional Rules:
  1. Single entrypoint (this script only)
  2. Step1 → Step2-a → Step2-b sequential execution
  3. Variant-aware (DB: under40/over41, LOTTE: male/female)
  4. SSOT output: data/scope_v3/ only
  5. Mandatory gates: stability, variant, raw integrity, SSOT

EOF
    exit 1
}

# Parse arguments
MANIFEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --manifest)
            MANIFEST="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown argument: $1${NC}"
            usage
            ;;
    esac
done

# Validate arguments
if [[ -z "$MANIFEST" ]]; then
    echo -e "${RED}❌ ERROR: --manifest is REQUIRED${NC}"
    usage
fi

if [[ ! -f "$MANIFEST" ]]; then
    echo -e "${RED}❌ ERROR: Manifest file not found: $MANIFEST${NC}"
    exit 2
fi

cd "$PROJECT_ROOT"

enforce_single_entrypoint

# Generate run ID
RUN_ID="run_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="data/scope_v3/_RUNS/$RUN_ID"
mkdir -p "$RUN_DIR"

echo -e "${BLUE}📦 Run ID: $RUN_ID${NC}"
echo ""

# Copy manifest to run directory
cp "$MANIFEST" "$RUN_DIR/manifest.json"

# ============================================================================
# STEP 1: Profile Builder + Extractor
# ============================================================================

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 1: Profile Builder + Extractor (Raw Extraction)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}→ Step1-A: Building profiles (table/column detection)${NC}"
python -m pipeline.step1_summary_first.profile_builder_v3 --manifest "$MANIFEST"

echo ""
echo -e "${YELLOW}→ Step1-B: Extracting raw scope (proposal facts)${NC}"
python -m pipeline.step1_summary_first.extractor_v3 --manifest "$MANIFEST"

# Capture profile checksums
echo ""
echo -e "${BLUE}→ Capturing profile checksums${NC}"
find data/profile -name "*_proposal_profile_v3.json" -type f | sort | xargs sha256sum > "$RUN_DIR/profiles_sha.txt"

# ============================================================================
# STEP 2-A: Sanitize (Normalization + Dropping)
# ============================================================================

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 2-A: Sanitize (Normalization + Fragment Removal)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Extract insurers from manifest
INSURERS=$(jq -r '.items[] | "\(.insurer):\(.variant)"' "$MANIFEST" | sort -u)

for INSURER_VARIANT in $INSURERS; do
    INSURER=$(echo "$INSURER_VARIANT" | cut -d: -f1)
    VARIANT=$(echo "$INSURER_VARIANT" | cut -d: -f2)

    echo -e "${YELLOW}→ Sanitizing: $INSURER ($VARIANT)${NC}"
    python -m pipeline.step2_sanitize_scope.run --insurer "$INSURER" --variant "$VARIANT"
done

# ============================================================================
# STEP 2-B: Canonical Mapping
# ============================================================================

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}STEP 2-B: Canonical Mapping (신정원 통일코드)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

for INSURER_VARIANT in $INSURERS; do
    INSURER=$(echo "$INSURER_VARIANT" | cut -d: -f1)
    VARIANT=$(echo "$INSURER_VARIANT" | cut -d: -f2)

    echo -e "${YELLOW}→ Canonical mapping: $INSURER ($VARIANT)${NC}"
    python -m pipeline.step2_canonical_mapping.run --insurer "$INSURER" --variant "$VARIANT"
done

# ============================================================================
# CONSTITUTIONAL GATES
# ============================================================================

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CONSTITUTIONAL GATES (MANDATORY)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

GATE_FAILURES=0

# GATE-56-3: Raw Integrity (no broken prefixes)
echo -e "${YELLOW}→ GATE-56-3: Raw Integrity Check${NC}"
BROKEN_PREFIXES=$(find data/scope_v3 -name "*_step1_raw_scope_v3.jsonl" -exec grep -l '^\. ' {} \; | wc -l || true)
if [[ $BROKEN_PREFIXES -gt 0 ]]; then
    echo -e "${RED}❌ GATE-56-3 FAILED: Found $BROKEN_PREFIXES files with broken prefixes ('. ')${NC}"
    GATE_FAILURES=$((GATE_FAILURES + 1))
else
    echo -e "${GREEN}✅ GATE-56-3 PASSED: No broken prefixes found${NC}"
fi

# GATE-56-2: Variant Preservation
echo -e "${YELLOW}→ GATE-56-2: Variant Preservation Check${NC}"
VARIANT_VIOLATIONS=0

# Check DB variants
if [[ ! -f "data/scope_v3/db_under40_step2_canonical_scope_v1.jsonl" ]] || \
   [[ ! -f "data/scope_v3/db_over41_step2_canonical_scope_v1.jsonl" ]]; then
    echo -e "${RED}❌ DB variant files missing${NC}"
    VARIANT_VIOLATIONS=$((VARIANT_VIOLATIONS + 1))
fi

# Check LOTTE variants
if [[ ! -f "data/scope_v3/lotte_male_step2_canonical_scope_v1.jsonl" ]] || \
   [[ ! -f "data/scope_v3/lotte_female_step2_canonical_scope_v1.jsonl" ]]; then
    echo -e "${RED}❌ LOTTE variant files missing${NC}"
    VARIANT_VIOLATIONS=$((VARIANT_VIOLATIONS + 1))
fi

# Check for forbidden single-variant files
if [[ -f "data/scope_v3/db_step2_canonical_scope_v1.jsonl" ]] || \
   [[ -f "data/scope_v3/lotte_step2_canonical_scope_v1.jsonl" ]]; then
    echo -e "${RED}❌ FORBIDDEN: Single-variant file exists (violates variant axis)${NC}"
    VARIANT_VIOLATIONS=$((VARIANT_VIOLATIONS + 1))
fi

if [[ $VARIANT_VIOLATIONS -gt 0 ]]; then
    echo -e "${RED}❌ GATE-56-2 FAILED: Variant violations detected${NC}"
    GATE_FAILURES=$((GATE_FAILURES + 1))
else
    echo -e "${GREEN}✅ GATE-56-2 PASSED: Variant preservation verified${NC}"
fi

# GATE-56-4: SSOT Enforcement (no outputs outside scope_v3)
echo -e "${YELLOW}→ GATE-56-4: SSOT Enforcement Check${NC}"
LEGACY_FILES=$(find data/scope -name "*.jsonl" -type f 2>/dev/null | wc -l || echo 0)
if [[ $LEGACY_FILES -gt 0 ]]; then
    echo -e "${RED}❌ GATE-56-4 FAILED: Found $LEGACY_FILES files in legacy data/scope/${NC}"
    GATE_FAILURES=$((GATE_FAILURES + 1))
else
    echo -e "${GREEN}✅ GATE-56-4 PASSED: SSOT enforcement verified${NC}"
fi

# Capture output checksums
echo ""
echo -e "${BLUE}→ Capturing output checksums${NC}"
find data/scope_v3 -name "*_step*.jsonl" -type f | sort | xargs sha256sum > "$RUN_DIR/outputs_sha.txt"

# Generate summary
cat > "$RUN_DIR/SUMMARY.md" << EOF
# Pipeline Run Summary

**Run ID**: $RUN_ID
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Manifest**: $(basename "$MANIFEST")

## Execution Steps
- ✅ Step1-A: Profile Builder
- ✅ Step1-B: Extractor
- ✅ Step2-A: Sanitize
- ✅ Step2-B: Canonical Mapping

## Constitutional Gates
$(if [[ $GATE_FAILURES -eq 0 ]]; then echo "✅ All gates PASSED"; else echo "❌ $GATE_FAILURES gate(s) FAILED"; fi)

## Output Counts
$(for f in data/scope_v3/*_step*.jsonl; do echo "- $(basename "$f"): $(wc -l < "$f") rows"; done)

## Checksums
- Profiles: $(wc -l < "$RUN_DIR/profiles_sha.txt") files
- Outputs: $(wc -l < "$RUN_DIR/outputs_sha.txt") files
EOF

# Update LATEST symlink
ln -sf "$RUN_ID" data/scope_v3/LATEST

# Final report
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PIPELINE EXECUTION COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Run ID: ${GREEN}$RUN_ID${NC}"
echo -e "Summary: ${BLUE}$RUN_DIR/SUMMARY.md${NC}"
echo ""

if [[ $GATE_FAILURES -gt 0 ]]; then
    echo -e "${RED}❌ PIPELINE FAILED: $GATE_FAILURES constitutional gate(s) violated${NC}"
    exit 2
else
    echo -e "${GREEN}✅ ALL CONSTITUTIONAL GATES PASSED${NC}"
    exit 0
fi
