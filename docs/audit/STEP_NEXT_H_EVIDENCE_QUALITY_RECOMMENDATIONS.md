# STEP NEXT-H: Evidence Quality Improvement Recommendations

## Executive Summary

STEP NEXT-G revealed that **64.5% of diagnosis slots have UNKNOWN_SEARCH_FAIL** status, meaning evidence EXISTS in source documents but fails G5 Coverage Attribution Gate. This is an **evidence quality issue**, NOT a document gap.

**Root Cause Analysis:**
- Step3 extracts large context windows (5-10 lines) around slot keywords
- These excerpts often contain MULTIPLE coverages (cross-coverage mixing)
- G5 gate correctly blocks these mixed excerpts to prevent contamination
- Result: Low FOUND rate (17.3%) but contamination=0 maintained

**Current State (LOCKED):**
- ✅ G5 gate working correctly (309 demotions, contamination=0)
- ✅ System is SAFE (no incorrect values exposed)
- ❌ System has low completeness (17.3% FOUND for diagnosis slots)

**This Document:**
- Analyzes root causes of SEARCH_FAIL
- Proposes Step3 evidence extraction improvements
- **Does NOT implement changes** (would require full pipeline re-run)
- Serves as roadmap for future evidence quality work

---

## Problem Analysis

### Root Cause: Step3 Chunk Extraction Strategy

**Current Behavior:**
```python
# pipeline/step3_evidence_resolver/evidence_patterns.py
"waiting_period": EvidencePattern(
    slot_key="waiting_period",
    keywords=["면책기간", "면책 기간", ...],
    context_lines=5,  # ← Captures 5 lines around match
    table_priority=False
)
```

**Result:**
Evidence excerpt contains 5+ lines, often including multiple coverages:

```
Evidence excerpt (waiting_period for 암진단비):
보장명
최초보험가입 또는 부활(효력회복) 후 면책기간
최초 보험가입후 50% 감액 지급 기간
[갱신형] 암 요양병원 입원일당Ⅱ (1일이상, 90일한도),  ← ❌ 다른 담보 (입원일당)
암 직접치료 통원일당  ← ❌ 다른 담보 (통원일당)
```

**G5 Gate Decision:**
- Detects "입원일당" (exclusion keyword)
- **REJECTS** → status=UNKNOWN, reason="다른 담보 값 혼입"
- **Correct behavior** (prevents contamination)

---

### Failure Pattern Breakdown (STEP NEXT-G Data)

| Failure Reason | Count | % | Root Cause |
|----------------|-------|---|------------|
| **G5: 다른 담보 값 혼입** | 40 | 56.3% | Chunk contains excluded coverage keywords |
| **G5: 담보 귀속 확인 불가** | 31 | 43.7% | Chunk doesn't mention target coverage name |
| **Total SEARCH_FAIL** | 71 | 100% | |

---

## Proposed Solutions (NOT IMPLEMENTED)

### Solution 1: Coverage-Anchored Chunk Extraction

**Problem:**
Current Step3 extracts chunks based on SLOT keywords only ("면책기간", "감액", etc.).
No requirement that target COVERAGE name appears in the chunk.

**Proposed Fix:**
```python
# NEW: Coverage-anchored evidence extraction
def extract_evidence_with_coverage_anchor(
    text: str,
    coverage_name: str,
    slot_keyword: str,
    context_lines: int = 3
) -> List[str]:
    """
    Extract evidence chunks that contain BOTH:
    1. Slot keyword (e.g., "면책기간")
    2. Coverage name (e.g., "암진단비(유사암 제외)")

    This ensures excerpts are coverage-specific.
    """
    excerpts = []

    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Check if line contains slot keyword
        if not re.search(slot_keyword, line, re.IGNORECASE):
            continue

        # Extract context window
        start = max(0, i - context_lines)
        end = min(len(lines), i + context_lines + 1)
        chunk = '\n'.join(lines[start:end])

        # ANCHOR CHECK: Chunk must contain target coverage name
        if not re.search(coverage_name, chunk, re.IGNORECASE):
            continue  # ← Skip chunks without coverage mention

        excerpts.append(chunk)

    return excerpts
```

**Expected Impact:**
- SEARCH_FAIL ("담보 귀속 확인 불가"): 43.7% → ~10%
- FOUND: 17.3% → ~40%+

**Implementation Cost:**
- Modify `pipeline/step3_evidence_resolver/resolver.py`
- Re-run Step3 for ALL insurers (~10 products)
- Re-run Step4 comparison
- Re-validate G5 gate (ensure contamination=0 maintained)

---

### Solution 2: Smart Chunk Splitting (Table-Aware)

**Problem:**
Many excerpts are from comparison tables that list MULTIPLE coverages in rows.
Current extraction doesn't split by table rows.

**Example Table:**
```
보장명                     면책기간
암진단비(유사암 제외)      90일
유사암진단비               없음      ← Mixed in same chunk!
```

**Proposed Fix:**
```python
def split_table_by_coverage(table_text: str) -> Dict[str, str]:
    """
    Split table rows by coverage name.

    Returns: {coverage_name: row_text}
    """
    rows = {}

    for line in table_text.split('\n'):
        # Detect coverage name in line
        for coverage_pattern in DIAGNOSIS_COVERAGE_PATTERNS:
            match = re.search(coverage_pattern, line)
            if match:
                coverage_name = match.group(0)
                rows[coverage_name] = line
                break

    return rows
```

**Expected Impact:**
- SEARCH_FAIL ("다른 담보 값 혼입"): 56.3% → ~20%
- FOUND: 17.3% → ~50%+

**Implementation Cost:**
- Add table detection logic to `document_reader.py`
- Modify chunk extraction in `resolver.py`
- Re-run Step3 + Step4

---

### Solution 3: Product-Level Slot Relaxation (LOW RISK)

**Problem:**
Some slots are naturally product-level, not coverage-specific:
- **entry_age**: Often applies to entire product (all coverages share same age range)
- **start_date**: Often product-level or global

**Current G5 Result:**
- entry_age: **0.0% FOUND** (100% blocked)
- start_date: 45.5% FOUND

**Proposed Fix:**
```python
# In SlotGateValidator
PRODUCT_LEVEL_SLOTS = ["entry_age"]

def validate_slot(self, slot_key, ...):
    if slot_key in PRODUCT_LEVEL_SLOTS:
        # Relaxed G5: Only check exclusion keywords
        # NO target coverage mention requirement
        attribution = self.validator.validate_attribution_relaxed(...)
    else:
        # Strict G5: Check both target + exclusions
        attribution = self.validator.validate_attribution(...)
```

**Expected Impact:**
- entry_age FOUND: 0.0% → ~60% (product-level values allowed)
- Overall FOUND: 17.3% → ~23%
- **Risk:** Low (still blocks exclusion keywords, just relaxes target mention requirement)

**Implementation Cost:**
- Add `validate_attribution_relaxed()` method to `CoverageAttributionValidator`
- Modify `SlotGateValidator.validate_slot()`
- Re-run Step4 only (NO Step3 re-run needed)
- Validate contamination=0 maintained

**Recommendation:** ✅ **IMPLEMENT THIS** (low risk, immediate 6% improvement)

---

## Impact Simulation

### Conservative Estimate (Solution 3 Only)

| Metric | Before | After (Solution 3) | Change |
|--------|--------|-------------------|---------|
| FOUND | 17.3% | ~23% | +5.7% |
| SEARCH_FAIL | 64.5% | ~58% | -6.5% |
| MISSING | 18.2% | 18.2% | 0% |
| **Contamination** | **0** | **0** | **✅ MAINTAINED** |

### Optimistic Estimate (Solutions 1+2+3)

| Metric | Before | After (All Solutions) | Change |
|--------|--------|-----------------------|---------|
| FOUND | 17.3% | ~55% | +37.7% |
| SEARCH_FAIL | 64.5% | ~27% | -37.5% |
| MISSING | 18.2% | 18.2% | 0% |
| **Contamination** | **0** | **0** | **✅ MAINTAINED** |

---

## Implementation Priority

### Phase 1: Low-Hanging Fruit (Immediate)

**Solution 3: Product-Level Slot Relaxation**
- ✅ No Step3 re-run needed
- ✅ Low contamination risk
- ✅ Immediate +6% FOUND improvement
- ✅ Can implement in 1 hour

**DoD:**
- entry_age FOUND: 0% → 60%+
- Contamination check: PASS (still 0)
- Overall FOUND: 17.3% → 23%

### Phase 2: Evidence Quality Overhaul (Future)

**Solutions 1+2: Coverage-Anchored + Smart Splitting**
- ⚠️ Requires Step3 re-run (expensive)
- ⚠️ Needs careful G5 revalidation
- ✅ Major improvement (+38% FOUND)
- ⏱️ Estimated 1-2 days work

**DoD:**
- FOUND: 23% → 55%+
- SEARCH_FAIL: 58% → 27%
- Contamination check: PASS (still 0)
- All customer questions (Q1-Q13) regression test

---

## Constraints Analysis

### Why NOT Implemented in STEP NEXT-H?

1. **Step3 Re-Run Cost**
   - Solutions 1+2 require modifying Step3 evidence extraction
   - Must re-run Step3 for 10 insurers (~30 min each = 5 hours)
   - Must re-validate ALL gates (G1-G5)
   - High risk of breaking existing pipeline

2. **Contamination=0 Requirement**
   - Current state: **309 demotions, 0 contaminations** ✅
   - Any G5 relaxation must maintain this
   - Need extensive validation before deployment

3. **Time vs. Value Tradeoff**
   - Solution 3 (product-level relaxation): 1 hour, +6% FOUND
   - Solutions 1+2 (evidence overhaul): 2 days, +38% FOUND
   - Current system is SAFE (just low completeness)

### Decision: Document Only (No Implementation)

This document serves as:
- ✅ Root cause analysis
- ✅ Solution design
- ✅ Impact simulation
- ✅ Implementation roadmap

**Actual implementation deferred** to future work when:
- Time budget allows Step3 re-run
- Full regression testing capacity available
- Business value justifies 2-day effort for +38% improvement

---

## Validation Checklist (For Future Implementation)

When implementing Solutions 1+2, validate:

### Pre-Implementation
- [ ] Backup current Step3 outputs
- [ ] Backup current Step4 compare_rows
- [ ] Save current completeness baseline (STEP NEXT-G report)

### Post-Implementation
- [ ] Run contamination check (`step_next_f_contamination_check.py`)
  - **Must be 0** (no false values exposed)
- [ ] Run completeness analysis (`step_next_g_slot_completeness.py`)
  - Target: FOUND >50%, SEARCH_FAIL <30%
- [ ] Compare before/after demotion reports
  - Ensure demotions are JUSTIFIED (not false negatives)
- [ ] Regression test customer questions Q1-Q13
  - No incorrect values
  - UNKNOWN allowed
  - No misleading outputs

### Rollback Criteria
If ANY of these fail:
- ❌ Contamination >0
- ❌ FOUND <40% (worse than expected)
- ❌ Customer question regression failures

→ **ROLLBACK** to current Step3/Step4 outputs

---

## Conclusion

**Current State (STEP NEXT-F + STEP NEXT-G):**
- ✅ System is SAFE (contamination=0)
- ❌ System has low completeness (17.3% FOUND)
- ✅ G5 gate working correctly (blocks cross-coverage mixing)

**Root Cause:**
- Step3 evidence extraction captures multi-coverage chunks
- G5 gate correctly rejects these to prevent contamination
- Result: Safe but incomplete

**Proposed Path Forward:**

1. **Immediate (Phase 1):**
   - Implement Solution 3 (product-level relaxation)
   - Low risk, +6% improvement
   - Maintain contamination=0

2. **Future (Phase 2):**
   - Implement Solutions 1+2 (evidence overhaul)
   - Requires Step3 re-run
   - Target: +38% improvement
   - Full regression testing

**Status:**
- This document: ✅ COMPLETE
- Phase 1 implementation: ⏸️ DEFERRED (time constraints)
- Phase 2 implementation: 📅 FUTURE WORK

**Recommendation:**
Accept current 17.3% FOUND rate as baseline.
System is SAFE and correct (contamination=0).
Improvement to 55%+ FOUND is valuable but not critical for initial deployment.
