#!/usr/bin/env bash
# STEP NEXT-61C: Execute Step3-5 for all insurers with GATE validation
set -euo pipefail

# Run ID
RUN_ID="run_20260101_160000"
RUN_DIR="data/scope_v3/_RUNS/$RUN_ID"
mkdir -p "$RUN_DIR"

# Axes list
AXES=(samsung meritz hanwha heungkuk hyundai kb lotte_male lotte_female db_under40 db_over41)

# Axis to base insurer mapping (for Step3)
get_base_insurer() {
  case "$1" in
    lotte_male|lotte_female) echo "lotte" ;;
    db_under40|db_over41) echo "db" ;;
    *) echo "$1" ;;
  esac
}

echo "=== STEP NEXT-61C: All-Insurer Execution ===" | tee "$RUN_DIR/SUMMARY.log"
echo "Run ID: $RUN_ID" | tee -a "$RUN_DIR/SUMMARY.log"
echo "Start: $(date)" | tee -a "$RUN_DIR/SUMMARY.log"
echo "" | tee -a "$RUN_DIR/SUMMARY.log"

# Track results
PASS_COUNT=0
FAIL_COUNT=0
declare -a FAILED_AXES

for axis in "${AXES[@]}"; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RUN_DIR/SUMMARY.log"
  echo "Processing: $axis" | tee -a "$RUN_DIR/SUMMARY.log"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RUN_DIR/SUMMARY.log"

  # Check Step2 canonical input exists
  INPUT_CANONICAL="data/scope_v3/${axis}_step2_canonical_scope_v1.jsonl"
  if [ ! -f "$INPUT_CANONICAL" ]; then
    echo "❌ SKIP: No Step2 canonical input for $axis" | tee -a "$RUN_DIR/SUMMARY.log"
    FAILED_AXES+=("$axis (no Step2 input)")
    FAIL_COUNT=$((FAIL_COUNT + 1))
    continue
  fi

  # Get base insurer for Step3
  INSURER=$(get_base_insurer "$axis")

  # Step3: PDF Text Extraction
  echo "[Step3] Extracting PDF text for $INSURER..." | tee -a "$RUN_DIR/SUMMARY.log"
  if python -m pipeline.step3_extract_text.extract_pdf_text --insurer "$INSURER" 2>&1 | tee "$RUN_DIR/${axis}_step3.log"; then
    if grep -q "GATE-3-1 passed" "$RUN_DIR/${axis}_step3.log"; then
      echo "✓ Step3 GATE-3-1 PASS" | tee -a "$RUN_DIR/SUMMARY.log"
    else
      echo "❌ Step3 GATE-3-1 FAIL" | tee -a "$RUN_DIR/SUMMARY.log"
      FAILED_AXES+=("$axis (GATE-3-1)")
      FAIL_COUNT=$((FAIL_COUNT + 1))
      continue
    fi
  else
    echo "❌ Step3 execution failed" | tee -a "$RUN_DIR/SUMMARY.log"
    FAILED_AXES+=("$axis (Step3 exec)")
    FAIL_COUNT=$((FAIL_COUNT + 1))
    continue
  fi

  # Step4: Evidence Search
  echo "[Step4] Searching evidence for $axis..." | tee -a "$RUN_DIR/SUMMARY.log"
  if python -m pipeline.step4_evidence_search.search_evidence --insurer "$axis" 2>&1 | tee "$RUN_DIR/${axis}_step4.log"; then
    # Verify SSOT input
    if grep -q "scope_v3/${axis}_step2_canonical_scope_v1.jsonl" "$RUN_DIR/${axis}_step4.log"; then
      echo "✓ Step4 SSOT input verified" | tee -a "$RUN_DIR/SUMMARY.log"
    else
      echo "❌ Step4 SSOT input violation" | tee -a "$RUN_DIR/SUMMARY.log"
      FAILED_AXES+=("$axis (SSOT violation)")
      FAIL_COUNT=$((FAIL_COUNT + 1))
      continue
    fi

    # GATE-4-2: Evidence Fill Rate
    EVIDENCE_PACK="data/evidence_pack/${axis}_evidence_pack.jsonl"
    if [ -f "$EVIDENCE_PACK" ]; then
      TOTAL=$(wc -l < "$EVIDENCE_PACK" | xargs)
      # Count rows with non-empty evidences array (heuristic: check for "evidences":[])
      WITH_EVIDENCE=$(grep -v '"evidences":\[\]' "$EVIDENCE_PACK" | wc -l | xargs)
      FILL_RATE=$(awk "BEGIN {printf \"%.2f\", $WITH_EVIDENCE / $TOTAL}")

      echo "  Evidence pack: $TOTAL rows, $WITH_EVIDENCE with evidence, fill_rate=$FILL_RATE" | tee -a "$RUN_DIR/SUMMARY.log"

      # GATE-4-2 thresholds
      if awk "BEGIN {exit !($FILL_RATE < 0.60)}"; then
        echo "❌ GATE-4-2 FAIL: fill_rate $FILL_RATE < 0.60" | tee -a "$RUN_DIR/SUMMARY.log"
        FAILED_AXES+=("$axis (GATE-4-2)")
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
      elif awk "BEGIN {exit !($FILL_RATE < 0.80)}"; then
        echo "⚠️  GATE-4-2 WARN: fill_rate $FILL_RATE < 0.80" | tee -a "$RUN_DIR/SUMMARY.log"
      else
        echo "✓ GATE-4-2 PASS: fill_rate $FILL_RATE ≥ 0.80" | tee -a "$RUN_DIR/SUMMARY.log"
      fi
    else
      echo "❌ Evidence pack not found" | tee -a "$RUN_DIR/SUMMARY.log"
      FAILED_AXES+=("$axis (no evidence pack)")
      FAIL_COUNT=$((FAIL_COUNT + 1))
      continue
    fi
  else
    echo "❌ Step4 execution failed" | tee -a "$RUN_DIR/SUMMARY.log"
    FAILED_AXES+=("$axis (Step4 exec)")
    FAIL_COUNT=$((FAIL_COUNT + 1))
    continue
  fi

  # Step5: Coverage Cards
  echo "[Step5] Building coverage cards for $axis..." | tee -a "$RUN_DIR/SUMMARY.log"
  if python -m pipeline.step5_build_cards.build_cards --insurer "$axis" 2>&1 | tee "$RUN_DIR/${axis}_step5.log"; then
    # GATE-5-2: Join Rate
    if grep -q "GATE-5-2 passed" "$RUN_DIR/${axis}_step5.log"; then
      JOIN_RATE=$(grep "Join rate:" "$RUN_DIR/${axis}_step5.log" | sed -E 's/.*Join rate: ([0-9.]+).*/\1/' | head -1)
      echo "✓ GATE-5-2 PASS: join_rate $JOIN_RATE%" | tee -a "$RUN_DIR/SUMMARY.log"
    else
      echo "❌ GATE-5-2 FAIL" | tee -a "$RUN_DIR/SUMMARY.log"
      FAILED_AXES+=("$axis (GATE-5-2)")
      FAIL_COUNT=$((FAIL_COUNT + 1))
      continue
    fi
  else
    echo "❌ Step5 execution failed" | tee -a "$RUN_DIR/SUMMARY.log"
    FAILED_AXES+=("$axis (Step5 exec)")
    FAIL_COUNT=$((FAIL_COUNT + 1))
    continue
  fi

  # Success
  echo "✅ $axis completed successfully" | tee -a "$RUN_DIR/SUMMARY.log"
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "" | tee -a "$RUN_DIR/SUMMARY.log"
done

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RUN_DIR/SUMMARY.log"
echo "FINAL RESULTS" | tee -a "$RUN_DIR/SUMMARY.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$RUN_DIR/SUMMARY.log"
echo "Total axes: ${#AXES[@]}" | tee -a "$RUN_DIR/SUMMARY.log"
echo "Passed: $PASS_COUNT" | tee -a "$RUN_DIR/SUMMARY.log"
echo "Failed: $FAIL_COUNT" | tee -a "$RUN_DIR/SUMMARY.log"

if [ $FAIL_COUNT -gt 0 ]; then
  echo "" | tee -a "$RUN_DIR/SUMMARY.log"
  echo "Failed axes:" | tee -a "$RUN_DIR/SUMMARY.log"
  for failed in "${FAILED_AXES[@]}"; do
    echo "  - $failed" | tee -a "$RUN_DIR/SUMMARY.log"
  done
fi

echo "" | tee -a "$RUN_DIR/SUMMARY.log"
echo "End: $(date)" | tee -a "$RUN_DIR/SUMMARY.log"

# Exit code
if [ $FAIL_COUNT -gt 0 ]; then
  exit 1
else
  exit 0
fi
