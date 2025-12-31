# STEP NEXT-44-γ-2: Global Quality Report — Step1 Safety Sweep

**Date**: 2025-12-31
**Scope**: All 8 insurers (Samsung, Meritz, KB, Hanwha, Hyundai, Lotte, Heungkuk, DB)
**Baseline**: `backups/step1_44g2_baseline/` (pre-44-γ-2)
**Current**: `data/scope/*_step1_raw_scope.jsonl` (post-44-γ-2)

---

## Executive Summary

**✅ ALL GATES PASSED** — No over-filtering detected.

**Key Findings**:
1. **Hanwha-specific filters successfully scoped**: Lines 132-146 in `proposal_fact_extractor_v2.py` now guarded by `if self.insurer == "hanwha"`
2. **Zero coverage count changes** across all 8 insurers (before/after identical)
3. **100% evidence completeness**: All records have `evidences.length >= 1`
4. **KB/Hyundai rejection pattern gates**: 0 violations (existing hard gates maintained)

---

## 1. Over-Filtering Verification (Hard Gates)

### 1.1 Coverage Count Stability

| Insurer  | Before | After | Delta | Δ%    | Tolerance         | Gate Status |
|----------|--------|-------|-------|-------|-------------------|-------------|
| Samsung  | 62     | 62    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| Meritz   | 36     | 36    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| KB       | 37     | 37    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| **Hanwha** | **35** | **35** | **0** | **0.00%** | **30-40 range** | ✅ **PASS** |
| Hyundai  | 35     | 35    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| Lotte    | 65     | 65    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| Heungkuk | 23     | 23    | 0     | 0.00% | max drop 10       | ✅ PASS     |
| DB       | 50     | 50    | 0     | 0.00% | max drop 10       | ✅ PASS     |

**Gate Rules**:
- Non-Hanwha (7 insurers): `delta >= -max(10, round(before * 0.10))`
- Hanwha: `30 <= count <= 40` (existing regression test)

**Result**: ✅ **All 8 insurers passed** (zero delta across all)

### 1.2 Evidence Completeness

| Insurer  | Total Records | Missing Evidences | Status  |
|----------|---------------|-------------------|---------|
| Samsung  | 62            | 0                 | ✅ PASS |
| Meritz   | 36            | 0                 | ✅ PASS |
| KB       | 37            | 0                 | ✅ PASS |
| Hanwha   | 35            | 0                 | ✅ PASS |
| Hyundai  | 35            | 0                 | ✅ PASS |
| Lotte    | 65            | 0                 | ✅ PASS |
| Heungkuk | 23            | 0                 | ✅ PASS |
| DB       | 50            | 0                 | ✅ PASS |

**Gate Rule**: `evidences.length >= 1` for all records
**Result**: ✅ **100% compliance**

---

## 2. Fact Completeness (Data Quality)

### 2.1 Proposal Facts Fill Rates

| Insurer  | Total | Amount | Premium | Period | Method | Renewal |
|----------|-------|--------|---------|--------|--------|---------|
| Samsung  | 62    | 61     | 47      | 47     | 0      | 0       |
| Meritz   | 36    | 33     | 33      | 33     | 0      | 0       |
| KB       | 37    | 36     | 36      | 0      | 0      | 0       |
| Hanwha   | 35    | 35     | 34      | 31     | 0      | 0       |
| Hyundai  | 35    | 35     | 35      | 35     | 0      | 0       |
| Lotte    | 65    | 61     | 61      | 61     | 0      | 0       |
| Heungkuk | 23    | 23     | 23      | 0      | 0      | 0       |
| DB       | 50    | 44     | 44      | 32     | 0      | 0       |

**Notes**:
- `coverage_amount_text`: High fill rate (88-100% across insurers)
- `premium_amount_text`: High fill rate for most (0-100%)
- `payment_period_text`: Variable (0-100%, depends on PDF structure)
- `payment_method_text`, `renewal_terms_text`: 0% (expected, rarely present in 가입설계서)

### 2.2 Hanwha-Specific Improvement Verification

**Hanwha Before (44-γ baseline)**: 35 coverages
**Hanwha After (44-γ-2)**: 35 coverages

**Filter Scope Verification** (lines 132-146 in `proposal_fact_extractor_v2.py`):
```python
# 2. Hanwha-only filters (STEP NEXT-44-γ improvement, scoped to Hanwha only)
if self.insurer == "hanwha":
    # Filter out benefit description texts (not coverage names)
    # These are typically long sentences describing payment conditions
    if any(x in coverage_name_raw for x in ['보험가입금액 지급', '보험금을 지급하지 않는', '보험금 지급', '진단확정', '치료를 목적으로', '직접 결과로', '보험기간 중']):
        continue

    # Filter out standalone bracket texts (section markers)
    if re.match(r'^\[.*\]$', coverage_name_raw):
        continue

    # Filter out overly long texts (likely descriptions, not coverage names)
    # Typical coverage name: 10-50 chars, descriptions: 50+ chars
    if len(coverage_name_raw) > 100:
        continue
```

**Status**: ✅ **Confirmed** — Hanwha filters now guarded by `if self.insurer == "hanwha"`, ensuring no cross-contamination.

---

## 3. Rejected Pattern Gate (KB/Hyundai Regression Prevention)

**Hard Gate Patterns** (lines 26-33):
```python
REJECT_PATTERNS = [
    r'^\d+\.?$',              # "10.", "11."
    r'^\d+\)$',               # "10)", "11)"
    r'^\d+(,\d{3})*(원|만원)?$',  # "3,000원", "3,000만원"
    r'^\d+만(원)?$',          # "10만", "10만원"
    r'^\d+[천백십](만)?원?$',  # "1천만원", "5백만원", "10만원"
    r'^[천백십만억]+원?$',    # "천원", "만원", "억원"
]
```

**Verification**: ✅ **0 violations** detected across all 8 insurers (existing regression test confirms)

---

## 4. Over-Filtering Suspect Analysis

**Query**: "Were any coverages removed in 44-γ-2 re-run?"
**Result**: **No** — All insurers show `delta = 0` (before == after)

**Conclusion**: Zero over-filtering occurred. Hanwha-specific filters (44-γ) successfully isolated to Hanwha insurer only.

---

## 5. Recommendations

### 5.1 Immediate
- ✅ **COMPLETED**: Hanwha filters scoped to Hanwha-only (lines 132-146)
- ✅ **COMPLETED**: Global over-filtering verification script (`tools/audit/verify_step1_44g2_overfiltering.py`)

### 5.2 Ongoing Monitoring
- Add regression test for non-Hanwha coverage count stability (see Section 6)
- Monitor future filter additions to ensure insurer-specific scoping

---

## 6. Next Steps

1. **Add Regression Test**: Update `tests/test_step1_proposal_fact_regression.py` with over-filtering guard
2. **Commit**: `fix(step-next-44g2): global re-run + over-filtering guards + quality report`
3. **Update STATUS.md**: Mark STEP NEXT-44-γ-2 complete

---

## Appendix: Verification Command

```bash
# Re-run verification
python tools/audit/verify_step1_44g2_overfiltering.py

# Expected output:
# ✅ ALL GATES PASSED - No over-filtering detected
```

---

**Sign-off**: All gates passed. Hanwha-specific filters (44-γ) successfully scoped without global impact.
