# Type Map Patch Notes - STEP NEXT-17C

**Date**: 2025-12-30
**Config File**: `config/amount_lineage_type_map.json`
**Changes**: 2 insurers reclassified (hyundai, kb)

---

## Change Summary

| Insurer | Before | After | Status |
|---------|--------|-------|--------|
| hyundai | C | A | ✅ Applied |
| kb | C | A | ✅ Applied |
| hanwha | C | C | ⚠️ No change (insufficient evidence) |

---

## Change Details

### 1. Hyundai (현대해상): C → A

**Evidence Source**: `docs/audit/TYPE_REVIEW_STEP17C.md` Section 1

**Document Structure Pattern**:
- Page 4 shows clear table: `담보명 | 납기/만기 | 가입금액 | 보험료(원)`
- Each coverage has individual amount (1천만원, 1천만원, etc.)
- **Type A/B pattern confirmed** - coverage-specific amounts in table

**Impact**:
- Current CONFIRMED rate: 21.6% (8/37 coverages)
- Expected improvement after Step11 re-extraction: ~90%+

**Rationale**:
- Type C extraction looks for single 보험가입금액 reference
- Hyundai PDF has Type A structure (individual amounts per coverage)
- Mismatch caused extraction failures

---

### 2. KB (KB손해보험): C → A

**Evidence Source**: `docs/audit/TYPE_REVIEW_STEP17C.md` Section 2

**Document Structure Pattern**:
- Page 3 shows clear table: `보장명 | 가입금액 | 보험료(원) | 납입|보험기간`
- Each coverage has individual amount (5백만원, 10만원, 3백만원, etc.)
- **Type A/B pattern confirmed** - varying amounts across coverages

**Impact**:
- Current CONFIRMED rate: 22.2% (10/45 coverages)
- Expected improvement after Step11 re-extraction: ~90%+

**Rationale**:
- Same as hyundai - Type C extraction logic incompatible with Type A PDF structure
- Amounts vary widely (10만원 ~ 5백만원), indicating coverage-specific pricing

---

### 3. Hanwha (한화손해보험): No Change

**Evidence Source**: `docs/audit/TYPE_REVIEW_STEP17C.md` Section 3

**Status**: UNKNOWN - insufficient evidence

**Reason**:
- First 10 pages of PDF did not yield table structure evidence
- May be image-based PDF requiring OCR
- Table may appear after page 10
- Different column header pattern not matching current regex

**Action**: Keep as Type C until further investigation

**Next Steps**: Separate investigation task (STEP NEXT-17D or manual review)

---

## Verification - Before/After Diff

### Before Patch (2025-12-30 pre-patch)

**TYPE_MAP_DIFF_REPORT.md**:
```
| Insurer | Config Type | Evidence Type | Match? | Action Recommended |
|---------|-------------|---------------|--------|-------------------|
| hyundai | C | A/B | ❌ | Consider update |
| kb | C | A/B | ❌ | Consider update |
| hanwha | C | UNKNOWN | ❓ | Review evidence |
```

**Discrepancies**: 2 (hyundai, kb)

---

### After Patch (2025-12-30 post-patch)

**TYPE_MAP_DIFF_REPORT.md** (re-generated):
```
| Insurer | Config Type | Evidence Type | Match? | Action Recommended |
|---------|-------------|---------------|--------|-------------------|
| hyundai | A | A/B | ✅ | None |
| kb | A | A/B | ✅ | None |
| hanwha | C | UNKNOWN | ❓ | Review evidence |
```

**Discrepancies**: 0 (all aligned where evidence available)

**Result**: ✅ All evidence-based mismatches resolved

---

## Impact on Amount Status Dashboard

### Before Patch

**AMOUNT_STATUS_DASHBOARD.md** excerpt:
```
| Insurer | CONFIRMED | UNCONFIRMED | Total | CONFIRMED % |
|---------|-----------|-------------|-------|-------------|
| hyundai | 8 | 29 | 37 | 21.6% |
| kb | 10 | 35 | 45 | 22.2% |
| hanwha | 4 | 33 | 37 | 10.8% |
```

### After Patch

**AMOUNT_STATUS_DASHBOARD.md** (no change yet - requires Step11 re-extraction):
```
| Insurer | CONFIRMED | UNCONFIRMED | Total | CONFIRMED % |
|---------|-----------|-------------|-------|-------------|
| hyundai | 8 | 29 | 37 | 21.6% |
| kb | 10 | 35 | 45 | 22.2% |
| hanwha | 4 | 33 | 37 | 10.8% |
```

**Note**: Dashboard unchanged because:
- Config change only affects **future** Step11 extractions
- Current coverage_cards.jsonl still contains old extraction results (Type C logic)
- **Next STEP required**: Re-run Step11 for hyundai/kb with Type A logic

**Expected After Step11 Re-extraction**:
```
| Insurer | CONFIRMED | UNCONFIRMED | Total | CONFIRMED % |
|---------|-----------|-------------|-------|-------------|
| hyundai | ~34 | ~3 | 37 | ~90%+ |
| kb | ~41 | ~4 | 45 | ~90%+ |
```

---

## Audit Script Re-run Log

```bash
$ python tools/audit/run_step_next_17b_audit.py

=== STEP NEXT-17B Audit Runner ===

1. Scanning insurers...
   Found 8 insurers: db, hanwha, heungkuk, hyundai, kb, lotte, meritz, samsung

2. Generating Amount Status Dashboard...
   ✅ /Users/cheollee/inca-rag-scope/docs/audit/AMOUNT_STATUS_DASHBOARD.md

3. Generating Type Classification Report...
   ✅ /Users/cheollee/inca-rag-scope/docs/audit/INSURER_TYPE_BY_EVIDENCE.md

4. Generating Type Map Diff Report...
   ✅ /Users/cheollee/inca-rag-scope/docs/audit/TYPE_MAP_DIFF_REPORT.md

5. Detecting Step7 Miss Candidates...
   ✅ /Users/cheollee/inca-rag-scope/docs/audit/STEP7_MISS_CANDIDATES.md
   Found 57 miss candidates

=== Audit Complete ===
```

**Result**: All reports regenerated successfully, TYPE_MAP_DIFF_REPORT now shows 0 discrepancies ✅

---

## Git Commit Info

**Branch**: feat/step-next-14-chat-ui (current)
**Files Changed**:
- `config/amount_lineage_type_map.json` (2 lines modified)

**Diff**:
```diff
{
  "samsung": "A",
  "lotte": "A",
  "heungkuk": "A",
  "meritz": "B",
  "db": "B",
  "hanwha": "C",
- "hyundai": "C",
- "kb": "C"
+ "hyundai": "A",
+ "kb": "A"
}
```

---

## Validation Checklist

- [x] Evidence reviewed for hyundai (Page 4 table structure)
- [x] Evidence reviewed for kb (Page 3 table structure)
- [x] Evidence inconclusive for hanwha (kept as Type C)
- [x] Config file updated (hyundai C→A, kb C→A)
- [x] Audit script re-run successfully
- [x] TYPE_MAP_DIFF_REPORT shows 0 discrepancies
- [x] Documentation complete (TYPE_REVIEW_STEP17C.md)
- [ ] Step11 re-extraction (next STEP - not in scope for 17C)
- [ ] Hanwha investigation (next STEP - not in scope for 17C)

---

## Next Actions

### Immediate (This STEP - 17C)
1. ✅ Type map patch complete
2. ⏭️ Step7 miss triage (15 candidates)
3. ⏭️ Regression test refinement

### Future (Next STEP - 17D or 18)
1. **Step11 Re-extraction** for hyundai/kb with Type A logic
   - Command: `python -m apps.loader.step11_amount_extractor --insurer hyundai --force-reload`
   - Command: `python -m apps.loader.step11_amount_extractor --insurer kb --force-reload`
   - Validate CONFIRMED rate improvement
   - Update coverage_cards.jsonl

2. **Hanwha Deep Dive**
   - Extend PDF page scan range (max_pages=20+)
   - Manual PDF inspection
   - OCR preprocessing if needed
   - Pattern extension for different table headers

---

## References

- Evidence Document: `docs/audit/TYPE_REVIEW_STEP17C.md`
- Config File: `config/amount_lineage_type_map.json`
- Diff Report (after): `docs/audit/TYPE_MAP_DIFF_REPORT.md`
- Dashboard (unchanged): `docs/audit/AMOUNT_STATUS_DASHBOARD.md`

---

**Conclusion**: Type map successfully patched with evidence-based corrections. Hyundai and KB now correctly classified as Type A, aligning with document structure evidence. Next STEP should re-extract amounts using correct Type logic.
