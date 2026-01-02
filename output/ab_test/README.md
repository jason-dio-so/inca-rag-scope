# STEP NEXT-V-01: Vector DB Proof of Value - A/B Test Results

## Quick Summary

**Final Verdict: NO-GO**

Vector DB does not provide sufficient value compared to cost and complexity in the current setup.

## Key Findings

| Insurer | Coverage Count | Winner | Notes |
|---------|---------------|--------|-------|
| **Samsung** | 31 | ❌ Baseline | Vector: 0% benefit_description (vs 58.1% baseline) |
| **Meritz** | 29 | ❌ Vector (low quality) | Vector: 100% fill rate but filled with irrelevant medical procedure codes |

## Files

### Input
- `data/compare/samsung_coverage_cards.jsonl` (31 coverages)
- `data/compare/meritz_coverage_cards.jsonl` (29 coverages)

### Output
- `A_samsung_customer_view.jsonl` - Baseline results (Samsung)
- `B_samsung_customer_view.jsonl` - Vector results (Samsung)
- `A_meritz_customer_view.jsonl` - Baseline results (Meritz)
- `B_meritz_customer_view.jsonl` - Vector results (Meritz)
- `metrics_samsung_summary.json` - Comparison metrics (Samsung)
- `metrics_meritz_summary.json` - Comparison metrics (Meritz)

### Tools
- `tools/ab_test_run_baseline.py` - Run baseline (A) test
- `tools/ab_test_run_vector.py` - Run vector (B) test
- `tools/ab_test_metrics.py` - Calculate comparison metrics

### Full Report
- **`docs/audit/STEP_NEXT_V01_VECTOR_POV_REPORT.md`** - Complete analysis with Go/No-Go decision

## How to Reproduce

```bash
# Run baseline tests
python -m tools.ab_test_run_baseline samsung
python -m tools.ab_test_run_baseline meritz

# Run vector tests
python -m tools.ab_test_run_vector samsung
python -m tools.ab_test_run_vector meritz

# Calculate metrics
python -m tools.ab_test_metrics samsung
python -m tools.ab_test_metrics meritz
```

## Decision Criteria Results

| Criterion | Samsung | Meritz | Overall |
|-----------|---------|--------|---------|
| Coverage improvement (≥ +20%p) | ❌ -58.1% | ✅ +41.4% | ❌ FAIL (quality issue) |
| TOC ratio reduction | ✅ -100% | ❌ 0% | ❌ FAIL |
| Explanatory ratio increase | ❌ 0% | ❌ 0% | ❌ FAIL |

## Recommendations

**Short-term** (instead of Vector DB):
1. Improve Step4 evidence_search (filter TOC pages, add quality scoring)
2. Enhance baseline customer_view_builder (add medical code filters, paragraph extraction)
3. Prioritize 사업방법서/상품요약서 over 약관

**Long-term** (reconsider Vector DB only if):
1. Semantic chunking implemented (paragraph/clause-level)
2. Document type separation enforced
3. Hybrid search (keyword + vector) implemented
4. Estimated timeline: 4-6 weeks

---

**Generated**: 2026-01-02
**Experiment**: STEP NEXT-V-01
**Constitutional Compliance**: ✅ NO LLM, NO Step1/2 changes, NO Excel changes
