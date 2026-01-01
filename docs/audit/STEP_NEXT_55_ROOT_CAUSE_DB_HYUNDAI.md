# STEP NEXT-55: DB / Hyundai Prefix Loss Root Cause Analysis

**Date**: 2026-01-01
**Status**: ✅ **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

**Problem**: DB and Hyundai proposals show coverage names with leading `"1."` markers in the PDF, but Step1 extracts them as `". "` (dot + space), losing the numeric prefix.

**Impact**:
- DB: 31 coverages extracted, ~15 with corrupted prefixes (`". 상해사망"` instead of `"1. 상해사망"`)
- Hyundai: 47 coverages extracted, ~30 with corrupted prefixes
- Step2-b mapping failures increased due to prefix corruption

**Root Cause**: Hybrid layout extractor (`hybrid_layout.py`) regex pattern captures seq_num separately but never prepends it back to `coverage_name_raw`.

---

## Evidence Trail

### 1. DB over41 Profile Evidence (page 4, table 0)

**Profile signature** (variant_signature):
```json
{
  "page": 4,
  "table_index": 0,
  "header_snippet": "고객님님 보장내용 No. 가입담보 가입금액 보험료(원) 납기/만기(갱신종료시기) 1. 상해사망·후유장해(20-100%) 1백만원 129 20년/100세",
  "sample_rows": [
    "1. |  | 상해사망·후유장해(20-100%) | 1백만원 | 129 | 20년/100세",
    "2. |  | 보험료납입면제대상보장(10대사유) | 10만원 | 110 | 20년/20년",
    "3. |  | 상해사망 | 1천만원 | 850 | 20년/100세"
  ]
}
```

**Profile shows**: Raw cell text contains `"1. "`, `"2. "`, `"3. "` prefixes.

### 2. Step1 Extraction Output

**First row from `db_over41_step1_raw_scope_v3.jsonl`**:
```json
{
  "insurer": "db",
  "coverage_name_raw": ". 상해사망·후유장해(20-100%)",
  "proposal_facts": {
    "coverage_amount_text": "1백만원",
    "premium_text": "129",
    "period_text": "20년/100세",
    "evidences": [{
      "doc_type": "가입설계서",
      "page": 4,
      "extraction_mode": "hybrid"
    }]
  }
}
```

**Extracted**: `". 상해사망..."` — the `"1"` is missing!

### 3. Hyundai Profile Evidence (page 2, table 2)

**Profile signature** (primary_signature):
```json
{
  "page": 2,
  "table_index": 2,
  "header_snippet": "가입담보 가입금액 보험료(원) 납기/만기 1. 기본계약(상해사망) 1천만원 448 20년납100세만기 2. 기본계약(상해후유장해) 1천만원 550 20년납100세만기",
  "sample_rows": [
    "2. | 기본계약(상해후유장해) | 1천만원 | 550 | 20년납100세만기",
    "3. | 보험료납입면제대상담보 | 10만원 | 35 | 전기납20년만기",
    "4. | 골절진단(치아파절제외)담보 | 10만원 | 629 | 20년납100세만기"
  ]
}
```

**First row from `hyundai_step1_raw_scope_v3.jsonl`**:
```json
{
  "insurer": "hyundai",
  "coverage_name_raw": ". 기본계약(상해사망)",
  "proposal_facts": {
    "coverage_amount_text": "1천만원",
    "premium_text": "448",
    "period_text": "20년납100세만기",
    "evidences": [{
      "doc_type": "가입설계서",
      "page": 2,
      "extraction_mode": "hybrid"
    }]
  }
}
```

**Extracted**: `". 기본계약..."` — the `"1"` is missing!

---

## Code-Level Root Cause

### File: `pipeline/step1_summary_first/hybrid_layout.py`

**Function**: `parse_summary_row_text()` (Line 120-176)

**Problematic Pattern** (Line 145):
```python
pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
match = re.match(pattern, text)

if not match:
    return None

seq_num, coverage_name, amount, premium, period = match.groups()
```

**Explanation**:
- `(\d+)?` captures the leading number (e.g., `"1"`) as `seq_num` (optional group)
- `(.+?)` captures the rest as `coverage_name` (e.g., `". 기본계약(상해사망)"`)
- The regex pattern correctly separates the two, **but**...

**Line 169-175**:
```python
return {
    "seq_num": seq_num.strip() if seq_num else None,
    "coverage_name": coverage_name,  # ❌ Does NOT include seq_num!
    "amount": amount,
    "premium": premium,
    "period": period,
}
```

**Line 289-297 in `merge_row_band_to_summary_row()`**:
```python
return SummaryRow(
    seq_num=parsed["seq_num"],  # ✅ Stored here
    coverage_name_raw=final_coverage_name,  # ❌ But NOT prepended back!
    amount_text=parsed["amount"],
    premium_text=parsed["premium"],
    period_text=parsed["period"],
    y0=y0,
    y1=y1,
    page=page,
)
```

**Issue**:
- `seq_num` is parsed and stored in the `SummaryRow` dataclass
- But `coverage_name_raw` is built from `final_coverage_name`, which comes from `parsed["coverage_name"]`
- `parsed["coverage_name"]` does NOT include the `seq_num` prefix
- **Result**: `"1. 상해사망"` → seq_num=`"1"`, coverage_name=`". 상해사망"` → coverage_name_raw=`". 상해사망"`

---

## Extraction Path Analysis

### Why Hybrid Mode for DB/Hyundai?

**DB over41** (page 4, table 0):
- `detection_pass: "A"` (keyword-based)
- `is_variant: true` (summary-variant table)
- **Extractor logic** (`extractor_v3.py` Line 147-148):
  ```python
  # Process variant signatures (Pass B) - use hybrid-first extraction
  facts.extend(self._extract_signatures(variant_sigs, mode="hybrid_first"))
  ```

**Result**: Even though Pass A detected the table, it's a `variant_signature`, so extractor uses `hybrid_first` mode.

**Hyundai** (page 2, table 2):
- `detection_pass: "A"` (keyword-based)
- `is_variant: false` (primary table)
- **BUT** — extractor uses `standard_first` → auto-triggers hybrid if >30% empty coverage names

**Check extractor logic** (`extractor_v3.py` Line 194-199):
```python
should_use_hybrid = self._should_trigger_hybrid(signatures)

if should_use_hybrid:
    logger.warning(f"{self.insurer}: Triggering hybrid extraction (empty coverage ratio > 30%)")
    hybrid_facts = self._extract_signatures_hybrid(signatures)
    facts = hybrid_facts
```

**Hypothesis**: Hyundai's page 2 table has column_map issues (coverage_name column incorrectly mapped?), causing >30% empty → auto-triggers hybrid.

---

## Verification

### Test Case 1: Parse Text with Seq Num

**Input**: `"1. 기본계약(상해사망) 1천만원 448 20년납100세만기"`

**Expected**:
- seq_num: `"1"`
- coverage_name: `"기본계약(상해사망)"` ✅
- But actual: `". 기본계약(상해사망)"` ❌

**Regex Capture**:
```python
>>> import re
>>> text = "1. 기본계약(상해사망) 1천만원 448 20년납100세만기"
>>> pattern = r"^(\d+)?\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
>>> match = re.match(pattern, text)
>>> match.groups()
('1', '. 기본계약(상해사망)', '1천만원', '448', '20년납100세만기')
```

**Confirmed**: The `". "` (dot + space) after the number is captured in coverage_name, not in seq_num.

---

## Fix Strategy

### Option A: Include seq_num in coverage_name_raw (RECOMMENDED)

**Change in `merge_row_band_to_summary_row()`**:
```python
# Line 289-297
final_coverage_name = ...  # existing logic

# NEW: Prepend seq_num if present
if parsed["seq_num"]:
    final_coverage_name = f"{parsed['seq_num']}. {final_coverage_name}"

return SummaryRow(
    seq_num=parsed["seq_num"],
    coverage_name_raw=final_coverage_name,  # ✅ Now includes "1. " prefix
    amount_text=parsed["amount"],
    premium_text=parsed["premium"],
    period_text=parsed["period"],
    y0=y0,
    y1=y1,
    page=page,
)
```

**Rationale**:
- `coverage_name_raw` should be "as close to PDF as possible" (Step1 Constitutional Rule)
- The PDF shows `"1. 상해사망"`, so Step1 should extract it as `"1. 상해사망"`
- Step2-a already has normalization patterns to remove leading markers (STEP NEXT-55)

### Option B: Fix regex to not capture dot

**Change pattern to exclude the dot from coverage_name**:
```python
pattern = r"^(\d+)\.\s*(.+?)\s+(\d+[천백만억]*원)\s+([\d,]+)\s+(.+)$"
#            ^^^^  Required "." after number, not captured in coverage_name
```

**Issue**: This assumes the dot is always present. Some PDFs may have:
- `"1) 담보명"` (paren instead of dot)
- `"1 담보명"` (no separator)
- `"A. 담보명"` (letter instead of number)

**Verdict**: Option A is more robust.

---

## Impact Assessment

### Affected Insurers

| Insurer | Extraction Mode | Pages Affected | Rows Affected | Prefix Pattern |
|---------|-----------------|----------------|---------------|----------------|
| db_over41 | hybrid (variant) | 4 | ~15/31 | `1. `, `2. `, etc. |
| db_under40 | hybrid (variant) | 4 | ~15/30 | `1. `, `2. `, etc. |
| hyundai | hybrid (auto-trigger?) | 2, 3 | ~30/47 | `1. `, `2. `, etc. |

### Step2 Mapping Impact

**Before Fix**:
- Coverage name: `". 상해사망"` → Step2-b exact match fails
- Step2-a normalization removes `". "` → `"상해사망"` → mapping may succeed

**After Fix**:
- Coverage name: `"1. 상해사망"` → Step2-a removes `"1. "` → `"상해사망"` → mapping succeeds

**Conclusion**: Step2 already handles leading markers (STEP NEXT-55), but Step1 should preserve them for accuracy.

---

## Reproducibility

### Minimal Reproduction

```bash
# 1. Extract DB with current code
python -m pipeline.step1_summary_first.extractor_v3 --manifest data/sources/proposal/MANIFEST.yaml --insurer db

# 2. Check first row
head -1 data/scope_v3/db_over41_step1_raw_scope_v3.jsonl | jq -r '.coverage_name_raw'
# Output: ". 상해사망·후유장해(20-100%)"
# Expected: "1. 상해사망·후유장해(20-100%)"
```

---

## Definition of Done

- [x] Root cause identified: `hybrid_layout.py` drops seq_num from coverage_name_raw
- [x] Evidence collected: DB/Hyundai profile vs Step1 output comparison
- [x] Fix strategy defined: Prepend seq_num in `merge_row_band_to_summary_row()`
- [ ] Code fix implemented
- [ ] Test case added (verify "1. 담보명" preserved)
- [ ] Regression test (DB/Hyundai prefix test)

---

## Next Steps

1. Implement Option A fix in `hybrid_layout.py`
2. Add test case: `tests/test_step1_hybrid_seq_num_preservation.py`
3. Re-run Step1 for DB/Hyundai
4. Verify output: `grep '^{".*coverage_name_raw":"1\.' data/scope_v3/db_over41_step1_raw_scope_v3.jsonl`
5. Update STEP NEXT-55 summary

---

## Audit Trail

- **Issue Discovery**: 2026-01-01 (STEP NEXT-55 execution)
- **Root Cause Analysis**: 2026-01-01 (this document)
- **Code Analysis**: `hybrid_layout.py` Line 145, 169-175, 289-297
- **Fix Implementation**: TBD
