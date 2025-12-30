# Type Classification Review - STEP NEXT-17C

**Generated**: 2025-12-30
**Purpose**: Evidence-based Type classification confirmation for hyundai/kb/hanwha
**Scope**: Document structure analysis to resolve Config vs Evidence discrepancies

---

## Executive Summary

**Type Reclassification Required**: 2 insurers (hyundai, kb)
**Further Investigation Required**: 1 insurer (hanwha)

| Insurer | Current Config | Evidence Type | Verdict | Action |
|---------|----------------|---------------|---------|--------|
| hyundai | C | A/B | ✅ CONFIRMED | Change C → A/B |
| kb | C | A/B | ✅ CONFIRMED | Change C → A/B |
| hanwha | C | UNKNOWN | ⚠️ INCONCLUSIVE | Investigate |

---

## 1. Hyundai (현대해상) — Type C → A/B ✅

### Current Config
- `config/amount_lineage_type_map.json`: **Type C** (보험가입금액 참조형)

### Evidence Type
- **Type A/B** (담보별 개별 금액 명시형)

### Document Structure Evidence

#### Page 4 - Coverage Table with Individual Amounts
```
담보명 및 보장내용 납기/만기 가입금액 보험료(원)
1.기본계약(상해사망) 20년납100세만기 1천만원 448
상해로 사망시 가입금액 지급

2.기본계약(상해후유장해) 20년납100세만기 1천만원 550
상해로 장해지급률이 3% 이상에 해당하는 장해상태가 된 경우 <가입금...
```

**Pattern Match**: `(담보명|보장명) ... (가입금액) ... (보험료)`

**Analysis**:
- Clear table structure with 4 columns: 담보명, 납기/만기, 가입금액, 보험료
- **Each coverage has its own individual amount** (1천만원, 1천만원, etc.)
- This is the canonical **Type A/B pattern** where amounts are coverage-specific
- **NO single 보험가입금액 reference** that all coverages refer to

### Conclusion
**CONFIRMED Type A/B** - Config misclassification detected

---

## 2. KB (KB손해보험) — Type C → A/B ✅

### Current Config
- `config/amount_lineage_type_map.json`: **Type C** (보험가입금액 참조형)

### Evidence Type
- **Type A/B** (담보별 개별 금액 명시형)

### Document Structure Evidence

#### Page 3 - Coverage Table with Individual Amounts
```
보장명 가입금액 보험료(원) 납입|보험기간
뇌혈관질환수술비 5백만원 885 20년/100세
허혈성심장질환수술비 5백만원 1,760 20년/100세
상해수술비 10만원 420 20년/100세
항암방사선치료비 3백만원 1,587 20년/100세
```

**Pattern Match**: `(보장명) ... (가입금액) ... (보험료)`

**Analysis**:
- Clear table structure with 4 columns: 보장명, 가입금액, 보험료, 납입|보험기간
- **Each coverage has its own individual amount** (5백만원, 10만원, 3백만원, etc.)
- Amounts vary widely across coverages (10만원 ~ 5백만원)
- This is the canonical **Type A/B pattern** where amounts are coverage-specific
- **NO single 보험가입금액 reference**

### Conclusion
**CONFIRMED Type A/B** - Config misclassification detected

---

## 3. Hanwha (한화손해보험) — UNKNOWN ⚠️

### Current Config
- `config/amount_lineage_type_map.json`: **Type C** (보험가입금액 참조형)

### Evidence Type
- **UNKNOWN** (문서 구조 증거 부족)

### Investigation: Why UNKNOWN?

#### Evidence Extraction Result
```
- Page 0: NO_EVIDENCE_FOUND
  - Pattern: N/A
```

#### Possible Causes

1. **PDF Structure Issue (Most Likely)**
   - Coverage table may be located **after page 10** (audit script only scans first 10 pages)
   - Table may be in different section (e.g., page 15+)

2. **Image-based PDF (OCR Required)**
   - Table rendered as image/scan rather than text
   - PyPDF2 text extraction returns empty/garbled text
   - Requires OCR preprocessing

3. **Different Table Pattern (Pattern Mismatch)**
   - Hanwha may use different column headers/structure
   - Current regex patterns don't match their format
   - Example: "담보" instead of "담보명", "금액" instead of "가입금액"

4. **Different Document Type**
   - May not have traditional 가입설계서 table
   - Could use summary format or different layout

### Recommended Actions

1. **Extend Page Scan Range**
   - Re-run extraction with `max_pages=20` or `max_pages=None` (full PDF)
   - Check if table appears in later pages

2. **Manual PDF Inspection**
   - Open `data/sources/insurers/hanwha/가입설계서/*.pdf` manually
   - Identify actual page number where coverage table appears
   - Note exact column headers and structure

3. **OCR Verification**
   - If table is image-based, check text extraction quality
   - May need OCR preprocessing or different extraction method

4. **Pattern Extension**
   - If table uses different headers, add Hanwha-specific patterns to audit script

### Current Status
- **INCONCLUSIVE** - Cannot confirm Type without evidence
- **Keep Config as Type C** until evidence available
- **No action on amount_lineage_type_map.json** for Hanwha at this time

### Next STEP Recommendation
- Create separate investigation task: "STEP NEXT-17D: Hanwha Document Structure Analysis"
- Manual review + extended page scan + OCR if needed

---

## 4. Impact Analysis

### Hyundai - CONFIRMED Rate Correlation

**Current State**:
- Config Type: C
- CONFIRMED rate: **21.6%** (8/37)
- Evidence Type: A/B

**Expected Improvement After Type Correction**:
- If re-extracted with Type A/B logic: CONFIRMED rate should increase to ~90%+
- Similar to other Type A/B insurers (samsung: 100%, meritz: 97.1%)

**Root Cause**:
- Type C extraction logic looks for single 보험가입금액 reference
- Hyundai PDF has coverage-specific amounts (Type A/B structure)
- Mismatch causes extraction failures → low CONFIRMED rate

### KB - CONFIRMED Rate Correlation

**Current State**:
- Config Type: C
- CONFIRMED rate: **22.2%** (10/45)
- Evidence Type: A/B

**Expected Improvement After Type Correction**:
- If re-extracted with Type A/B logic: CONFIRMED rate should increase to ~90%+
- Similar to other Type A/B insurers

**Root Cause**:
- Same as Hyundai - Type mismatch causing extraction logic failure

---

## 5. Validation Criteria Met

### Evidence Quality Checklist

✅ **Hyundai**:
- [x] Page/line evidence extracted
- [x] Table structure pattern matched
- [x] Column headers confirmed (담보명, 가입금액, 보험료)
- [x] Individual amounts per coverage confirmed
- [x] No 보험가입금액 reference pattern found
- [x] Conclusion: Type A/B deterministic

✅ **KB**:
- [x] Page/line evidence extracted
- [x] Table structure pattern matched
- [x] Column headers confirmed (보장명, 가입금액, 보험료)
- [x] Individual amounts per coverage confirmed (varying amounts)
- [x] No 보험가입금액 reference pattern found
- [x] Conclusion: Type A/B deterministic

⚠️ **Hanwha**:
- [ ] Page/line evidence extracted (FAILED)
- [ ] Table structure pattern matched (NOT FOUND)
- [ ] Requires further investigation
- [ ] Conclusion: UNKNOWN (cannot determine)

---

## 6. Recommendations

### Immediate Actions (This STEP)

1. **Update `config/amount_lineage_type_map.json`**:
   ```json
   {
     "hyundai": "A",  // Changed from C
     "kb": "A",       // Changed from C
     "hanwha": "C"    // Keep as-is until evidence available
   }
   ```

2. **Document Patch Notes** (TYPE_MAP_PATCH_NOTES.md)

3. **Re-run Audit Script** to validate impact

### Future Actions (Next STEP)

1. **Step11 Re-extraction for hyundai/kb**
   - Use Type A extraction logic
   - Validate CONFIRMED rate improvement
   - Update coverage_cards.jsonl

2. **Hanwha Deep Dive** (separate STEP)
   - Manual PDF review
   - Extended page scan
   - OCR if needed
   - Pattern extension

---

## 7. References

- Evidence Source: `docs/audit/INSURER_TYPE_BY_EVIDENCE.md`
- Config File: `config/amount_lineage_type_map.json`
- Dashboard: `docs/audit/AMOUNT_STATUS_DASHBOARD.md`
- Diff Report: `docs/audit/TYPE_MAP_DIFF_REPORT.md`

---

**Conclusion**: Hyundai and KB Type reclassification from C to A/B is **evidence-based and deterministic**. Hanwha requires further investigation before Type can be confirmed.
