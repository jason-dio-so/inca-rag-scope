# A4200_1 SSOT Row Snapshot

**Date:** 2026-01-14
**SSOT File:** `data/sources/insurers/담보명mapping자료.xlsx`
**Sheet:** Sheet1
**Target coverage_code:** A4200_1
**Canonical name:** 암진단비(유사암제외)

---

## 🎯 Purpose

This document records the **exact Excel rows** from the SSOT that define A4200_1 (암진단비·유사암제외) across all insurers. This is the **absolute baseline** for all pipeline processing.

**Critical Principle:** The pipeline MUST NOT discover, infer, or generate coverages. It MUST ONLY process coverages explicitly listed in this SSOT.

---

## 📄 SSOT File Metadata

| Property | Value |
|----------|-------|
| File Path | `data/sources/insurers/담보명mapping자료.xlsx` |
| Sheet Name | Sheet1 |
| File Size | 24,412 bytes |
| Last Modified | 2026-01-14 21:41:55 |
| Total Rows | 264 (header + data) |

---

## 📊 Complete A4200_1 Coverage Definition (All Insurers)

A4200_1 is defined for **8 insurers** in the SSOT:

| Excel Row | ins_cd | Insurer | coverage_code | canonical_name | insurer_display_name |
|-----------|--------|---------|---------------|----------------|----------------------|
| **9** | N01 | 메리츠 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| **39** | N02 | 한화 | A4200_1 | 암진단비(유사암제외) | 암(4대유사암제외)진단비 |
| **69** | N03 | 롯데 | A4200_1 | 암진단비(유사암제외) | 일반암진단비Ⅱ |
| **109** | N05 | 흥국 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| **140** | N08 | 삼성 | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| **179** | N09 | 현대 | A4200_1 | 암진단비(유사암제외) | 암진단Ⅱ(유사암제외)담보 |
| **210** | N10 | KB | A4200_1 | 암진단비(유사암제외) | 암진단비(유사암제외) |
| **246** | N13 | DB | A4200_1 | 암진단비(유사암제외) | 암진단비Ⅱ(유사암제외) |

---

## 🔍 Target Insurers (Meritz, Hanwha) - Detailed View

This audit focuses on **Meritz** and **Hanwha** as representative cases demonstrating the Coverage Code First principle.

### Meritz (N01) - Excel Row 9

```
ins_cd: N01
보험사명: 메리츠
cre_cvr_cd: A4200_1
신정원코드명: 암진단비(유사암제외)
담보명(가입설계서): 암진단비(유사암제외)
```

**Key Fact:**
- Meritz uses the display name "암진단비(유사암제외)"
- This name **matches** the canonical name
- PDF documents (가입설계서, 약관, 사업방법서, 상품요약서) for Meritz should use this exact string

---

### Hanwha (N02) - Excel Row 39

```
ins_cd: N02
보험사명: 한화
cre_cvr_cd: A4200_1
신정원코드명: 암진단비(유사암제외)
담보명(가입설계서): 암(4대유사암제외)진단비
```

**Key Fact:**
- Hanwha uses the display name "암(4대유사암제외)진단비"
- This name **differs** from the canonical name
- PDF documents for Hanwha should use this exact string
- **CRITICAL:** String matching "암(4대유사암제외)진단비" vs "암진단비(유사암제외)" would FAIL
- **ONLY** coverage_code A4200_1 correctly identifies these as the same coverage

---

## ⚠️ Coverage Name Diversity Analysis

### Why String Matching FAILS

A4200_1 has **8 different display names** across insurers:

1. **메리츠**: "암진단비(유사암제외)"
2. **한화**: "암(4대유사암제외)진단비"  ← DIFFERENT
3. **롯데**: "일반암진단비Ⅱ"  ← VERY DIFFERENT
4. **흥국**: "암진단비(유사암제외)"
5. **삼성**: "암진단비(유사암제외)"
6. **현대**: "암진단Ⅱ(유사암제외)담보"  ← DIFFERENT
7. **KB**: "암진단비(유사암제외)"
8. **DB**: "암진단비Ⅱ(유사암제외)"  ← DIFFERENT

### String Matching Would Require:

- Exact match: ❌ Only 4/8 insurers match
- Fuzzy match: ❌ "일반암진단비Ⅱ" vs "암(4대유사암제외)진단비" have no overlap
- Regex/pattern: ❌ Would match wrong coverages (A4200_2, A4209, etc.)
- Semantic inference: ❌ FORBIDDEN by constitution

### Only coverage_code A4200_1 Works:

- ✅ Exact identifier across all insurers
- ✅ No ambiguity
- ✅ Requires no inference
- ✅ Maps directly to SSOT

---

## 🔒 Absolute Contract: SSOT as Pipeline Input

### What This Means for Step1

Step1 **MUST**:
1. Load this SSOT Excel file FIRST
2. Create a "target plan" containing:
   - For Meritz: `(insurer_key="meritz", coverage_code="A4200_1", allowed_name="암진단비(유사암제외)")`
   - For Hanwha: `(insurer_key="hanwha", coverage_code="A4200_1", allowed_name="암(4대유사암제외)진단비")`
3. When processing PDFs:
   - Search for the **allowed_name** in the PDF
   - Tag extracted data with **coverage_code** from the plan
   - NEVER determine coverage_code from coverage_name

Step1 **MUST NOT**:
- ❌ Scan PDF to discover coverage names
- ❌ Use coverage_name to infer coverage_code
- ❌ Process coverages not in the target plan
- ❌ String-match coverage names across insurers

---

## 📋 Pipeline Enforcement Rules

### Rule 1: SSOT-First Loading

```python
# ✅ CORRECT
def create_target_plan():
    ssot = pd.read_excel('data/sources/insurers/담보명mapping자료.xlsx')
    plan = []
    for _, row in ssot.iterrows():
        plan.append({
            'insurer_key': normalize_insurer(row['ins_cd']),
            'coverage_code': row['cre_cvr_cd'],
            'canonical_name': row['신정원코드명'],
            'allowed_display_name': row['담보명(가입설계서)']
        })
    return plan

# ❌ WRONG
def discover_coverages_from_pdf(pdf):
    coverage_names = extract_coverage_list(pdf)
    return coverage_names  # NO coverage_code!
```

### Rule 2: Coverage Name for Lookup Only

```python
# ✅ CORRECT
def extract_coverage_data(pdf, target_plan):
    for target in target_plan:
        # Look up by allowed name
        section = find_coverage_section(pdf, target['allowed_display_name'])
        if section:
            # Tag with coverage_code from plan
            return {
                'coverage_code': target['coverage_code'],  # From SSOT
                'coverage_name': target['allowed_display_name'],  # For display
                'data': extract_data(section)
            }

# ❌ WRONG
def extract_coverage_data(pdf):
    coverage_name = extract_coverage_name(pdf)
    # Try to map name to code...
    coverage_code = guess_code_from_name(coverage_name)  # FORBIDDEN!
```

### Rule 3: No Coverage Name Comparison

```python
# ✅ CORRECT
def compare_coverages(cov1, cov2):
    return cov1['coverage_code'] == cov2['coverage_code']

# ❌ WRONG
def compare_coverages(cov1, cov2):
    return similar(cov1['coverage_name'], cov2['coverage_name'])  # FAIL!
```

---

## 🧪 Verification Checklist

For A4200_1 to pass SSOT enforcement:

- [x] A4200_1 exists in SSOT for target insurers (Meritz, Hanwha)
- [x] Excel row numbers documented (Row 9 for Meritz, Row 39 for Hanwha)
- [x] Display names extracted (different for Meritz vs Hanwha)
- [x] coverage_code is the canonical key (A4200_1)
- [ ] Step1 loads SSOT before processing PDFs
- [ ] Step1 creates target plan from SSOT
- [ ] Step1 uses allowed_display_name for PDF lookup only
- [ ] Step1 tags all extracted data with coverage_code from plan
- [ ] Step2-4 never re-determine coverage_code from coverage_name

---

## 📦 Artifact

**Snapshot JSON:** `a4200_1_ssot_snapshot.json`

This file contains the structured data for all 8 insurers' A4200_1 definitions, including Excel row numbers.

---

## 🔗 Related Documents

- `COVERAGE_CANONICALIZATION_V2.md` - Coverage Code First constitution
- `COVERAGE_MAPPING_SSOT.md` - SSOT definition
- `A4200_1_PIPELINE_CONSISTENCY_REPORT.md` - Pipeline audit results
- `A4200_1_STEP1_TARGET_PLAN_TRACE.md` - Step1 enforcement trace (next)

---

## 📝 Summary

**SSOT declares:**
- A4200_1 exists for 8 insurers
- Display names vary significantly (8 different strings)
- coverage_code A4200_1 is the ONLY reliable identifier
- Meritz Row 9: "암진단비(유사암제외)"
- Hanwha Row 39: "암(4대유사암제외)진단비"

**Pipeline MUST:**
- Load SSOT first
- Use coverage_code as primary key
- Use display_name for lookup only
- NEVER infer coverage_code from coverage_name

**String matching of coverage names is FORBIDDEN.**

---

**END OF SSOT SNAPSHOT**
