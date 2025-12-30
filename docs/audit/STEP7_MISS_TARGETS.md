# Step7 Miss Targets (Confirmed) - STEP NEXT-17C

**Date**: 2025-12-30
**Source**: STEP7_MISS_TRIAGE_STEP17C.md
**Status**: TRUE_MISS_TABLE only (confirmed extraction misses)

---

## Purpose

This document tracks **CONFIRMED** Step7 extraction misses where:
1. Coverage name + amount clearly appear in proposal PDF table
2. amount.status == UNCONFIRMED in coverage_cards.jsonl
3. Manual review confirms this is a true miss (not false positive)

These are **targets for Step7 extraction improvement**.

---

## Summary

**Total Confirmed Targets**: 3
- Hyundai: 1
- KB: 2
- Lotte: 0

**Success Criteria**: After Step7 fix, these 3 should transition from UNCONFIRMED → CONFIRMED

---

## Target List

### Target 1: Hyundai - 상해사망

**Insurer**: hyundai
**Coverage Canonical**: 상해사망
**Current Status**: UNCONFIRMED
**PDF Page**: 2

**Evidence**:
```
가입담보 가입금액 보험료(원) 납기/만기
1.기본계약(상해사망) 1천만원 448 20년납100세만기
2.기본계약(상해후유장해) 1천만원 550 20년납100세만기
```

**Expected Amount**: 1천만원 (10,000,000원)

**Issue**:
- Coverage name in PDF: "1.기본계약(상해사망)"
- Canonical name: "상해사망"
- Step7 likely fails to match due to:
  1. Number prefix "1."
  2. Parent coverage wrapper "기본계약(...)"

**Fix Required**:
- Strip number prefixes from table rows: `^\d+\.`
- Extract coverage name from parentheses: `기본계약\(([^)]+)\)` → capture group 1
- OR normalize both canonical and PDF names to handle "기본계약" wrapper

---

### Target 2: KB - 뇌혈관질환수술비

**Insurer**: kb
**Coverage Canonical**: 뇌혈관질환수술비
**Current Status**: UNCONFIRMED
**PDF Page**: 3

**Evidence**:
```
보장명 가입금액 보험료(원) 납입|보험기간
209 뇌혈관질환수술비 5백만원 885 20년/100세
213 허혈성심장질환수술비 5백만원 1,760 20년/100세
227 상해수술비 10만원 420 20년/100세
```

**Expected Amount**: 5백만원 (5,000,000원)

**Issue**:
- Coverage name in PDF: "209 뇌혈관질환수술비"
- Canonical name: "뇌혈관질환수술비"
- Step7 likely fails to match due to number prefix "209 "

**Fix Required**:
- Strip leading number + space from table rows: `^\d+\s+`
- After stripping: "뇌혈관질환수술비" should match canonical exactly

---

### Target 3: KB - 허혈성심장질환수술비

**Insurer**: kb
**Coverage Canonical**: 허혈성심장질환수술비
**Current Status**: UNCONFIRMED
**PDF Page**: 3

**Evidence**: (Same table as Target 2)
```
보장명 가입금액 보험료(원) 납입|보험기간
209 뇌혈관질환수술비 5백만원 885 20년/100세
213 허혈성심장질환수술비 5백만원 1,760 20년/100세
227 상해수술비 10만원 420 20년/100세
```

**Expected Amount**: 5백만원 (5,000,000원)

**Issue**: Same as Target 2 - number prefix "213 "

**Fix Required**: Same as Target 2 - strip `^\d+\s+`

---

## Pattern Analysis

### Issue Pattern 1: Number Prefixes (KB)

**Affected Targets**: 2/3 (Target 2, Target 3)

**Pattern**: `\d+\s+{coverage_name}`

**Examples**:
- `209 뇌혈관질환수술비`
- `213 허혈성심장질환수술비`
- `227 상해수술비`

**Extraction Logic Fix**:
```python
# Before matching coverage name, strip number prefix
cleaned_name = re.sub(r'^\d+\s+', '', raw_table_cell)
# Then match against canonical coverage names
```

**Impact**: Should fix ~40% of KB UNCONFIRMED cases (estimated)

---

### Issue Pattern 2: Parenthesized Wrappers (Hyundai)

**Affected Targets**: 1/3 (Target 1)

**Pattern**: `{parent}({actual_coverage})`

**Examples**:
- `기본계약(상해사망)`
- `기본계약(상해후유장해)`

**Extraction Logic Fix - Option A** (Preferred):
```python
# Extract from parentheses if pattern matches
match = re.match(r'.*\(([^)]+)\)', raw_table_cell)
if match:
    coverage_name = match.group(1)  # "상해사망"
```

**Extraction Logic Fix - Option B**:
```python
# Normalize canonical names to include wrapper
# e.g., add "기본계약(상해사망)" as alias for "상해사망"
```

**Impact**: Should fix ~30% of Hyundai UNCONFIRMED cases (estimated)

---

## Validation Plan

### Test Case 1: Hyundai - 상해사망
```bash
# After Step7 fix:
python -m apps.loader.step11_amount_extractor --insurer hyundai --force-reload

# Verify:
# 1. amount.status == CONFIRMED
# 2. amount.value_text == "1천만원" or "10,000,000"
# 3. coverage_name_canonical == "상해사망"
```

### Test Case 2-3: KB - 뇌혈관질환수술비, 허혈성심장질환수술비
```bash
# After Step7 fix:
python -m apps.loader.step11_amount_extractor --insurer kb --force-reload

# Verify:
# 1. amount.status == CONFIRMED (both coverages)
# 2. 뇌혈관질환수술비: value_text == "5백만원" or "5,000,000"
# 3. 허혈성심장질환수술비: value_text == "5백만원" or "5,000,000"
```

---

## Regression Test Integration

Current test file: `tests/test_step7_miss_candidates_regression.py`

**Before Fix**: All 3 targets are XFAIL
```python
@pytest.mark.xfail(reason="Known Step7 miss - number prefix not handled")
def test_kb_뇌혈관질환수술비():
    ...  # Currently FAILS (UNCONFIRMED)
```

**After Fix**: All 3 targets should PASS (XPASS → PASS)
```python
# Same test, but now PASSES because:
# - Step7 strips number prefix
# - Extraction succeeds
# - amount.status == CONFIRMED
```

**Monitoring**: When tests transition from XFAIL → XPASS, this signals fix success

---

## Priority & Impact

| Target | Priority | Impact | Complexity |
|--------|----------|--------|------------|
| Target 2-3 (KB number prefix) | HIGH | Medium (fixes ~10 KB cases) | LOW |
| Target 1 (Hyundai parentheses) | MEDIUM | Medium (fixes ~10 Hyundai cases) | MEDIUM |

**Recommended Order**:
1. Fix number prefix issue first (LOW complexity, HIGH priority)
2. Validate on KB targets 2-3
3. Then fix parentheses issue
4. Validate on Hyundai target 1

---

## Next Steps

### This STEP (17C)
- [x] Document 3 confirmed targets
- [ ] Update regression test XFAIL reasons with specific issue patterns

### Next STEP (Step7 Improvement - 17D or 18)
1. **Implement fixes**:
   - Add number prefix stripping to Step7 table parser
   - Add parentheses extraction logic
2. **Test**:
   - Run Step11 re-extraction for hyundai/kb
   - Verify 3 targets transition UNCONFIRMED → CONFIRMED
3. **Validate**:
   - Check regression tests: XFAIL → XPASS → PASS
   - Review overall CONFIRMED rate improvement

### Future
- Expand triage to remaining 42 candidates (57 total - 15 triaged = 42)
- Apply same patterns to identify more TRUE_MISS cases
- Build comprehensive Step7 improvement roadmap

---

## References

- Triage Source: `docs/audit/STEP7_MISS_TRIAGE_STEP17C.md`
- All Candidates: `docs/audit/STEP7_MISS_CANDIDATES.md`
- Regression Tests: `tests/test_step7_miss_candidates_regression.py`
- Type Review: `docs/audit/TYPE_REVIEW_STEP17C.md`

---

**Conclusion**: 3 confirmed Step7 extraction misses identified with clear fix patterns. Number prefix stripping and parentheses handling should resolve all 3 targets.
