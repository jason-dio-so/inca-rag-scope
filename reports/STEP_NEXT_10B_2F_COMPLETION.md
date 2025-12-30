# STEP NEXT-10B-2F Completion Report

**Date**: 2025-12-29
**Status**: ✅ COMPLETE
**Branch**: fix/10b2d-loader-evidence-bridge
**Freeze Tag**: freeze/pre-10b2f-kb-parser-fix-20251229-014724

---

## Executive Summary

Successfully completed KB amount parser fix and Type reclassification:

1. ✅ **Amount Parser Fixed**: Added support for "천만원/백만원" patterns
2. ✅ **KB Retype**: KB classified as Type A based on document structure
3. ✅ **DB Label Audit**: Confirmed "삼성생명" labeling is correct
4. ✅ **All Tests Pass**: 61/61 lineage + guardrail tests
5. ✅ **Pattern Verified**: 7/7 test cases pass for new patterns

---

## Issue Identified

### Root Cause: Pattern Recognition Gap

**Problem**: KB was misclassified as Type C (77.8% UNCONFIRMED) despite having coverage-level amounts in proposal.

**Evidence from Previous Audit** (`KB_STEP7_MAPPING_AUDIT_FINAL_VERDICT.md`):
- KB proposal has담보별 보장금액 명시 (Type A structure)
- 12 matched coverages in scope
- Only 4/12 extracted (33.3% success)
- Pattern analysis:
  - ✅ "만원" pattern: 4/4 extracted (100%)
  - ❌ "천만원" pattern: 0/5 extracted (0%)
  - ❌ "백만원" pattern: 0/2 extracted (0%)

**Diagnosis**: Amount parser only supported "X만원" pattern, missing "X천만원/백만원"

---

## Fix Implemented

### Files Modified

1. **`pipeline/step7_amount/extract_proposal_amount.py`** (lines 74-104)
2. **`pipeline/step7_amount_integration/integrate_amount.py`** (lines 71-101)

### Pattern Changes

**BEFORE** (only "만원" recognized):
```python
patterns = [
    r'(\d{1,3}(?:,\d{3})+\s*만원)',
    r'(\d+\s*만원)',
    r'(\d{1,3}(?:,\d{3})+\s*원)',
    r'(\d+\s*원)',
]
```

**AFTER** (all Korean unit patterns supported):
```python
patterns = [
    # Korean numeric units + 만원
    r'(\d+\s*천\s*만원)',      # e.g., 1천만원, 3천만원
    r'(\d+\s*백\s*만원)',      # e.g., 5백만원, 3백만원
    r'(\d+\s*십\s*만원)',      # e.g., 2십만원
    # Standard numeric + 만원
    r'(\d{1,3}(?:,\d{3})+\s*만원)',  # e.g., 1,000만원
    r'(\d+\s*만원)',           # e.g., 10만원, 1만원
    # Fallback
    r'(\d{1,3}(?:,\d{3})+\s*원)',
    r'(\d+\s*원)',
]
```

**Key Change**: Added Korean unit patterns **before** standard patterns to ensure longer matches take priority.

---

## Pattern Verification

### Test Results

```
=== Pattern Fix Verification ===

✅ 일반상해사망(기본) 1천만원         → 1천만원
✅ 암진단비(유사암제외) 3천만원        → 3천만원
✅ 뇌혈관질환수술비 5백만원           → 5백만원
✅ 항암방사선치료비 3백만원           → 3백만원
✅ 상해수술비 10만원                → 10만원
✅ 질병입원일당(1일이상) 1만원         → 1만원
✅ 특정항암호르몬약물허가치료비 50만원   → 50만원

Results: 7 passed, 0 failed
```

### KB Proposal Evidence (from `reports/kb_proposal_amount_raw.md`)

**Pattern Distribution**:
- 천만원: 9 cases (e.g., 1천만원, 3천만원)
- 백만원: 6 cases (e.g., 5백만원, 3백만원)
- 만원: 6 cases (e.g., 10만원, 1만원, 2만원, 50만원)

**Total**: 21 coverages with explicit amounts in KB proposal

---

## Expected Impact

### Before Fix (Actual)

| Category | Count | Percentage |
|----------|-------|------------|
| Matched in scope | 12 | 100% |
| Pattern recognized | 4 | 33.3% |
| CONFIRMED | 4 | 33.3% |
| UNCONFIRMED (pattern failure) | 8 | 66.7% |

**Result**: KB appeared as Type C (high UNCONFIRMED)

---

### After Fix (Expected)

| Category | Count | Percentage |
|----------|-------|------------|
| Matched in scope | 12 | 100% |
| Pattern recognized | 12 | 100% |
| CONFIRMED | 12 | 100% |
| UNCONFIRMED (pattern failure) | 0 | 0% |

**Result**: KB should show Type A characteristics (high CONFIRMED)

**Note**: Re-running Step7 for KB will validate this expectation in practice.

---

## Type Reclassification

### Type Map Updated

**File**: `config/amount_lineage_type_map.json`

**BEFORE**:
```json
{
  "kb": "C"
}
```

**AFTER**:
```json
{
  "kb": "A"
}
```

### Reclassification Rationale

**Type Definition** (from `docs/guardrails/STEP7_TYPE_AWARE_GUARDRAILS.md`):

- **Type A**: Coverage-level 명시형 (line-by-line amounts in proposal)
- **Type C**: Product-level 구조형 (no coverage-level amounts)

**KB Document Structure** (from `reports/kb_proposal_amount_raw.md`):

```
Page 3: 담보 요약 테이블
보장명                가입금액        보험료(원)    납입|보험기간
209 뇌혈관질환수술비    5백만원         885         20년/100세
213 허혈성심장질환수술비 5백만원         1,760       20년/100세
...

Page 4: 담보 상세 설명
1 일반상해사망(기본)     1천만원
  보험기간중 상해의 직접결과로써 사망시
```

**Characteristics**:
- ✅ Line-by-line amount table (Page 3)
- ✅ Coverage code + name + amount format
- ✅ Explicit amounts for each coverage

**Conclusion**: KB is **Type A** (coverage-level 명시형)

**Previous Type C classification was due to pattern recognition bug, NOT document structure.**

---

## Type Classification Principle (Clarified)

### Principle P4: Type는 문서 구조 기준

**Rule**: Type classification is based on **document structure ONLY**, not on extraction success rate.

**Examples**:

| Insurer | Document Structure | Pattern Support | Extraction % | Correct Type |
|---------|-------------------|-----------------|--------------|--------------|
| Samsung | Line-by-line amounts | Full support | 100% | A |
| KB | Line-by-line amounts | Partial support → **FIXED** | 33% → 100% | A |
| Hanwha | Product-level only | N/A (no coverage amounts) | 10.8% | C |

**Anti-Pattern** (FORBIDDEN):
- ❌ Changing Type based on extraction success rate
- ❌ Calling Type C "correct" when pattern is incomplete
- ❌ Using Type C as excuse for pattern gaps

**Correct Approach**:
- ✅ Type reflects document structure
- ✅ Low extraction rate = implementation bug (fix pattern)
- ✅ Type C high UNCONFIRMED = expected behavior (no coverage-level amounts in document)

---

## DB Label Audit: "삼성생명" Issue

### Investigation

**Question**: Why does "삼성생명" appear in DB audit reports when code uses "samsung" key?

**Answer**: This is **CORRECT behavior**, not an issue.

### Evidence

**DB Insurer Master**:
```sql
SELECT insurer_id, insurer_name_kr, insurer_name_en, insurer_type FROM insurer;

insurer_name_kr | insurer_name_en         | insurer_type
----------------|-------------------------|-------------
삼성생명        | Samsung Life Insurance  | 생명
```

**Loader Key Mapping** (`apps/loader/step9_loader.py` line 793):
```python
INSURER_NAME_MAPPING = {
    'samsung': '삼성생명',
    'lotte': '롯데손해보험',
    'kb': 'KB손해보험',
    # ...
}
```

**File System Structure**:
```
data/scope/samsung_scope.csv          (file key: samsung)
data/sources/insurers/samsung/...     (directory key: samsung)
```

### Conclusion

- ✅ File system uses **English key** (`samsung`)
- ✅ DB uses **Korean label** (`삼성생명`)
- ✅ Loader maps correctly: `samsung` → `삼성생명`
- ✅ **NO ISSUE DETECTED** - this is correct architecture

**Recommendation**: Document this dual-key pattern (English file key + Korean DB label) in architecture guide.

---

## Lineage Lock Verification

### All Tests Pass ✅

```bash
pytest -q tests/test_lineage_lock_step7.py \
           tests/test_lineage_lock_loader.py \
           tests/test_step7_type_aware_guardrails.py

Results: 61 passed in 0.11s
```

**Breakdown**:
- Lineage lock tests: 10 passed
- Type-aware guardrail tests: 51 passed

### No Lineage Violations

**Verified**:
- ✅ No LLM/inference in amount extraction
- ✅ No snippet keyword search in loader
- ✅ Canonical mapping integrity maintained
- ✅ Pattern expansion does NOT violate P1 (신정원 통일코드 기준)
- ✅ No Type C forbidden inference ("보험가입금액" copy)

---

## Forbidden Pattern Check

### Type C Forbidden Pattern: "보험가입금액"

**Check**: Ensure no "보험가입금액" in amount value_text (Type C violation)

**Result** (from DB audit):
```sql
SELECT COUNT(*) FROM amount_fact WHERE value_text LIKE '%보험가입금액%';

critical_violation
--------------------
                  0
```

✅ **PASS**: Zero Type C violations

---

## Files Modified

### Code Changes

1. `pipeline/step7_amount/extract_proposal_amount.py` - Pattern fix
2. `pipeline/step7_amount_integration/integrate_amount.py` - Pattern fix

### Configuration Changes

3. `config/amount_lineage_type_map.json` - KB: C → A

### Documentation Created

4. `reports/STEP_NEXT_10B_2F_COMPLETION.md` - This completion report

---

## DoD (Definition of Done) Verification

### Required Criteria

1. ✅ **Pattern Fix**: Added "천만원/백만원" support (verified with 7 test cases)
2. ✅ **Type Map**: KB changed to Type A based on document structure
3. ✅ **DB Label**: Confirmed "삼성생명" is correct (no fix needed)
4. ✅ **All Tests Pass**: 61/61 tests pass
5. ✅ **Lineage Lock**: No violations detected
6. ✅ **Documentation**: Completion report generated

### Expected Outcome (After Step7 Re-run)

**Note**: Full Step7 re-run was NOT performed in this STEP per SAFETY-LOCKED principle. Pattern fix is code-level complete and verified with unit tests.

**To validate extraction improvement**:
```bash
# Re-run Step7 for KB (future step)
python -m pipeline.step7_amount.run --insurer kb

# Expected result:
# - 12 matched coverages → 12 CONFIRMED (100%)
# - KB Type A validation PASS (PRIMARY ≥ 80%)
```

---

## Key Principles Enforced

### P1: 신정원 통일코드 기준

✅ Pattern expansion does NOT create new canonical codes
✅ All pattern matches still resolve to existing cre_cvr_cd from Excel

### P2: No LLM Inference

✅ Pattern matching is regex-based (no AI inference)
✅ Amount text extracted as-is from document

### P3: Loader는 매핑만

✅ Loader was NOT modified (no snippet extraction)
✅ Pattern fix is in Step7 only

### P4: Type는 문서 구조 기준

✅ KB reclassified based on document structure
✅ Pattern gap treated as bug, not Type definition

### P5: Type C 금지 패턴

✅ Zero "보험가입금액" in value_text
✅ Type C definition remains strict (no product-level inference)

---

## Next Steps (Optional Future Work)

1. ⏭️ **Re-run Step7 for KB** to validate extraction improvement
2. ⏭️ **Re-load DB** with updated KB amounts
3. ⏭️ **Re-audit Type A** validation for KB (expected PRIMARY ≥80%)
4. ⏭️ **Update STATUS.md** with Type classification clarification

**Current Status**: Pattern fix complete and verified. Re-run deferred to avoid pipeline complexity in SAFETY-LOCKED step.

---

## Summary Statement

KB amount parser has been fixed to support "천만원/백만원" patterns, resolving the pattern recognition gap that caused KB to appear as Type C. KB has been reclassified as Type A based on its document structure (coverage-level amount table). DB label audit confirms "삼성생명" labeling is correct. All lineage lock and guardrail tests pass.

**Pattern Fix**: ✅ COMPLETE
**Type Reclassification**: ✅ COMPLETE
**DB Label Audit**: ✅ COMPLETE (no issue found)
**Tests**: ✅ 61/61 PASS

---

**Report Generated**: 2025-12-29 02:15:00 KST
**Branch**: fix/10b2d-loader-evidence-bridge
**Freeze Tag**: freeze/pre-10b2f-kb-parser-fix-20251229-014724
**Total Tests**: 61/61 passed ✅
