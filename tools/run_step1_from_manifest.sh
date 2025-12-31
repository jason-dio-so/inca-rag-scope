#!/bin/bash
# STEP NEXT-45-D: Manifest-based Step1 Pipeline Runner (v3 ONLY)
#
# Purpose:
#   Run profile_builder_v3 + extractor_v3 using manifest as SSOT
#
# Usage:
#   ./tools/run_step1_from_manifest.sh [manifest_path]
#
# Default manifest: data/manifests/proposal_pdfs_v1.json

set -euo pipefail

MANIFEST="${1:-data/manifests/proposal_pdfs_v1.json}"

echo "================================================================================================"
echo "STEP NEXT-45-D: Manifest-Based Step1 Reproducible Runner (V3 ONLY)"
echo "================================================================================================"
echo ""
echo "Manifest: $MANIFEST"
echo ""

# Step 1: Profile Builder V3
echo "Step 1/2: Running profile_builder_v3 (generates profile with fingerprint)..."
python -m pipeline.step1_summary_first.profile_builder_v3 --manifest "$MANIFEST"

echo ""
echo "Step 2/2: Running extractor_v3 (with fingerprint gate)..."
python -m pipeline.step1_summary_first.extractor_v3 --manifest "$MANIFEST"

echo ""
echo "================================================================================================"
echo "✅ Step1 V3 pipeline complete (REPRODUCIBLE, FINGERPRINT-GATED)"
echo "================================================================================================"
