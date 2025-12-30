# STEP NEXT-17A Completion Report
**Date**: 2025-12-30
**Task**: Remove mock amounts from chat handlers and wire to real data sources
**Status**: ✅ COMPLETED

---

## Executive Summary

Successfully removed all hardcoded mock amounts from `apps/api/chat_handlers.py` and connected handlers to real amount data from `coverage_cards.jsonl` files. All E2E test outputs now reflect actual data extraction results.

**Impact**: E2E testing is now valid - handlers display real CONFIRMED/UNCONFIRMED status instead of hardcoded "1천만원" mocks.

---

## Git Status

### Modified Files
```
M  apps/api/chat_handlers.py  (PRIMARY - mock removal + real data integration)
```

### Unchanged (as required)
- ✅ Step7 logic: NO changes
- ✅ amount_fact DB: NO regeneration
- ✅ DTO schemas: NO modifications
- ✅ Data layer files: NO modifications

---

## Gate Results

### Gate 1: Mock Blocker Test
```bash
python -m pytest tests/test_no_mock_amounts_in_chat_handlers.py -v
```
**Result**: ✅ **PASS** (2/2 tests passed)
- `test_no_mock_amounts_in_chat_handlers`: PASS (was FAIL before, now fixed)
- `test_mock_comments_are_documented`: PASS

**Before**: FAIL - detected 4 mock amount violations
**After**: PASS - all hardcoded amounts removed

### Gate 2: Chat Integration Tests
```bash
python -m pytest tests/test_chat_integration.py -q
python -m pytest tests/test_comparison_explanation.py -q
```
**Result**: ✅ **PASS**
- `test_chat_integration.py`: 19 passed, 9 warnings
- `test_comparison_explanation.py`: 38 passed, 10 warnings

No regressions introduced.

### Gate 3: Full Test Suite
```bash
python -m pytest -q
```
**Result**: ✅ **PASS**
- **202 passed**
- 3 skipped
- 1 xfailed (test_kb_step7_miss_regression - expected)
- 15 warnings

**Before**: 201 passed, 1 failed (mock blocker), 1 xfailed
**After**: 202 passed, 0 failed, 1 xfailed

Net improvement: +1 passed (mock blocker now passing)

---

## Removed Mock Locations

### Example2Handler (`apps/api/chat_handlers.py`)
| Line (Before) | Mock Pattern | Status |
|---------------|-------------|--------|
| 189 | `text="1천만원"  # Mock` | ✅ REMOVED |
| 216 | `f"...1천만원으로 명시..."` | ✅ REMOVED |
| 246 | `snippet="암진단비: 1천만원"  # Mock` | ✅ REMOVED |

**Replaced with**:
- Load `coverage_cards.jsonl` → extract `AmountDTO`
- Format via `format_amount_for_display(amount, insurer)`

### Example3Handler (`apps/api/chat_handlers.py`)
| Line (Before) | Mock Pattern | Status |
|---------------|-------------|--------|
| 448 | `text="1천만원"  # Mock` | ✅ REMOVED |
| 553 | `snippet=f"{coverage}: 1천만원"  # Mock` | ✅ REMOVED |

**Replaced with**: Same real data integration as Example2

### Example4Handler (Eligibility)
| Item | Status |
|------|--------|
| Line 658: `text="O"` | ✅ KEPT (eligibility O/X, not amount) |
| Line 709: `snippet="...정의..."` | ✅ KEPT (definition text, not amount) |

**Rationale**: Example4 is for eligibility (O/X/조건부), not amounts. Mock data is acceptable for demo.

---

## Real Data Integration

### Data Flow
```
coverage_cards.jsonl (data/compare/{insurer}_coverage_cards.jsonl)
    ↓
_load_coverage_card(insurer, coverage_canonical)
    ↓
_get_amount_from_card(card) → AmountDTO
    ↓
format_amount_for_display(amount, insurer) → display text
    ↓
TableCell(text=display_text, meta=CellMeta(status=amount.status))
```

### Helper Functions Added
1. **`_load_coverage_card(insurer, coverage_canonical)`**
   - Reads JSONL file for specified insurer
   - Returns coverage card dict or None

2. **`_get_amount_from_card(card)`**
   - Extracts AmountDTO from card['amount']
   - Handles None/missing gracefully (returns NOT_AVAILABLE)

### Integration Points
- **Example2Handler**: `_build_detail_table`, `_build_explanation`, `_build_evidence`
- **Example3Handler**: `_build_integrated_table`, `_build_evidence`

---

## Expected Behavior Changes

### Before (Mock Data)
```python
# All insurers showed same mock
KB: "1천만원" (CONFIRMED)
삼성: "1천만원" (CONFIRMED)
한화: "1천만원" (CONFIRMED)
```

### After (Real Data)
```python
# Shows actual extraction results
KB: "금액 미표기" (UNCONFIRMED)  # Step7 miss - documented in KB verification
삼성: "X,XXX만원" (CONFIRMED)   # If extracted
한화: "보험가입금액 기준" (UNCONFIRMED, Type C)
```

**Note**: KB showing UNCONFIRMED is correct given Step7 extraction failure (documented in STEP NEXT-17-KB verification).

---

## Verification Commands

### Mock Detection (should be clean)
```bash
rg -n 'Mock|# Mock|text="[^"]*만원"|snippet="[^"]*만원"' apps/api/chat_handlers.py
```
**Result**: Only Example4 placeholder text remains (acceptable - not amounts)

### E2E Test with Real Data
```bash
python -c "
from apps.api.chat_vm import ChatRequest
from apps.api.chat_intent import IntentDispatcher

req = ChatRequest(
    message='KB 암진단비',
    kind='EX2_DETAIL',
    coverage_names=['암진단비(유사암제외)'],
    insurers=['KB손해보험']
)
resp = IntentDispatcher.dispatch(req)
# Will show real UNCONFIRMED status, not mock '1천만원'
"
```

---

## Compliance Checklist

### ✅ Completed
- [x] All mock amounts removed from Example2/Example3 handlers
- [x] Real data wired via coverage_cards.jsonl
- [x] `format_amount_for_display()` used for all amount text
- [x] Gate 1 (mock blocker): PASS
- [x] Gate 2 (chat integration): PASS
- [x] Gate 3 (full suite): PASS
- [x] Zero Step7/amount_fact/DB changes
- [x] Zero DTO schema changes

### ❌ Not Done (Out of Scope)
- [ ] Step7 extraction fix (separate STEP required)
- [ ] KB Type C → A/B reclassification (STEP 2 planned)
- [ ] Handler integration with AmountRepository (DB-backed, future)

---

## Known Issues / Next Steps

### Issue 1: KB Still Shows UNCONFIRMED
**Root Cause**: Step7 extraction miss (documented in KB verification)
**Impact**: KB amounts display as "금액 미표기" despite document showing "3천만원"
**Fix Required**: Step7 modification (separate STEP)
**Status**: Tracked by `test_kb_step7_miss_regression.py` (xfail)

### Issue 2: Currently Using File-Based Data
**Current**: Loads from `coverage_cards.jsonl` files
**Future**: Integrate with AmountRepository (DB-backed)
**Benefit**: Would support dynamic queries, not just pre-loaded cards
**Priority**: Medium (file-based works for current scope)

---

## Testing Recommendations

### Regression Gate (Mandatory)
```bash
# Must pass before any PR merge
python -m pytest tests/test_no_mock_amounts_in_chat_handlers.py -v
```

### E2E Validation
```bash
# Test real amount display
python -m pytest tests/test_chat_integration.py::test_ex2_coverage_detail -v
```

### Full Suite
```bash
# Standard command (always use python -m pytest)
python -m pytest -q
```

---

## Completion Criteria (DoD)

| Criteria | Status |
|----------|--------|
| No hardcoded amounts in handlers | ✅ DONE |
| `test_no_mock_amounts_in_chat_handlers.py` PASS | ✅ DONE |
| All amounts use `format_amount_for_display()` | ✅ DONE |
| Full pytest suite passes (202+ passed) | ✅ DONE |
| No Step7/amount_fact/DTO changes | ✅ DONE |
| Documentation updated | ✅ DONE |

---

## Summary for Stakeholders

**What Changed**: Removed fake "1천만원" displays from chat UI, connected to real data

**Impact**: E2E tests now valid - you'll see actual CONFIRMED/UNCONFIRMED results

**What Didn't Change**: No data extraction logic modified, no DB changes

**Next Steps**:
1. Fix Step7 KB extraction (separate STEP)
2. Reclassify KB Type C → A/B (STEP 2)
3. Consider AmountRepository integration (future)

---

**Completion Date**: 2025-12-30
**Verified By**: Automated tests (202 passed)
**Status**: READY FOR MERGE
