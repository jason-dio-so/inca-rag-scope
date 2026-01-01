# MAPPING RATE OUTLIERS

**STEP NEXT-50-A / Audit C**
**Date**: 2026-01-01
**Purpose**: Detect and explain mapping rate outliers across insurers

---

## 1. Executive Summary

✅ **PASS (outliers explained)**

**Outliers Detected**: 2 insurers (MERITZ, LOTTE)

**Key Findings**:
1. **MERITZ (16.7%)**: Number-prefix alias gap (systematic but explainable)
2. **LOTTE (32.8%)**: Step1 extraction noise (benefit descriptions as coverage names)

**Critical Conclusion**:
Both outliers are **data quality issues**, NOT infrastructure errors.
No insurer exhibits the DB-class bug (wrong insurer code).

---

## 2. Overall Statistics

| Metric              | Value  |
|---------------------|--------|
| Mean mapping rate   | 65.3%  |
| Median mapping rate | 73.5%  |
| Std deviation       | 26.7%  |

**Distribution**:
- Excellent (>85%): 3 insurers (HEUNGKUK, SAMSUNG, DB)
- Good (70-85%): 1 insurer (HANWHA)
- Moderate (60-70%): 2 insurers (HYUNDAI, KB)
- Poor (<60%): 2 insurers (LOTTE, MERITZ) ← **Outliers**

---

## 3. Mapping Rates by Insurer

| Rank | Insurer  | Total | Mapped | Exact | Normalized | Unmapped | Rate   | Status |
|------|----------|-------|--------|-------|------------|----------|--------|--------|
| 1    | HEUNGKUK | 22    | 20     | 18    | 2          | 2        | 90.9%  | ✅ Excellent |
| 2    | SAMSUNG  | 61    | 52     | 25    | 27         | 9        | 85.2%  | ✅ Excellent |
| 3    | DB       | 48    | 40     | 29    | 11         | 8        | 83.3%  | ✅ Excellent |
| 4    | HANWHA   | 34    | 27     | 27    | 0          | 7        | 79.4%  | ✅ Good |
| 5    | HYUNDAI  | 34    | 23     | 22    | 1          | 11       | 67.6%  | ⚠️ Moderate |
| 6    | KB       | 36    | 24     | 24    | 0          | 12       | 66.7%  | ⚠️ Moderate |
| 7    | LOTTE    | 64    | 21     | 20    | 1          | 43       | 32.8%  | ❌ Outlier |
| 8    | MERITZ   | 36    | 6      | 5     | 1          | 30       | 16.7%  | ❌ Outlier |

**Median**: 73.5%

---

## 4. Outlier Detection (±30% Deviation from Median)

### 4.1 MERITZ (16.7%)

**Deviation**: -56.9% (77.3% from median)

**Root Cause**: Number-prefix coverage naming pattern

**Evidence**:
- Meritz proposal uses numbered coverage names: "155 뇌졸중진단비", "163 허혈성심장질환진단비"
- Excel mapping table has "뇌졸중진단비" (without number prefix)
- Current normalization rules do NOT strip leading numbers

**Example Unmapped Entries**:
```
155 뇌졸중진단비                 → UNMAPPED (Excel has: 뇌졸중진단비)
163 허혈성심장질환진단비         → UNMAPPED (Excel has: 허혈성심장질환진단비)
365 신화상치료비(화상진단비)     → UNMAPPED (Excel has: 화상진단비)
```

**Impact**:
- Total: 36 entries
- Unmapped: 30 entries (83.3%)
- **Actual coverage names exist in Excel**, but with different formatting

**Is This an Infrastructure Error?**
❌ **NO**

**Explanation**:
- This is an **alias gap** (known naming variant not covered by normalization rules)
- NOT a code mismatch (insurer code is correct: N01)
- NOT a missing coverage (Excel has the coverages, just without number prefixes)

**Remediation Options** (optional, NOT required):
1. Add number-prefix stripping in Step2-a normalization
2. Add numbered aliases to Excel mapping table
3. Accept current state and document pattern

**Recommended**: Option 3 (document and accept)

**Rationale**: Number prefixes are Meritz-specific. Adding global normalization may cause false matches in other insurers.

---

### 4.2 LOTTE (32.8%)

**Deviation**: -40.7% (55.4% from median)

**Root Cause**: Step1 extraction quality (benefit descriptions extracted as coverage names)

**Evidence**:
- Lotte has 64 total entries (highest among all insurers)
- 43 unmapped (67.2%)
- Many unmapped entries are **benefit descriptions**, not coverage names

**Example Unmapped Entries**:
```
상해사고로 사망한 경우 보험가입금액 지급                    → Benefit description
일반암 진단시 가입금액 지급                               → Benefit description
뇌출혈·뇌경색 진단시 가입금액 지급                        → Benefit description
```

**Is This an Infrastructure Error?**
❌ **NO**

**Explanation**:
- This is a **Step1 extraction quality issue** (over-extraction from Lotte proposal PDF)
- Benefit descriptions should NOT be extracted as coverage names
- Excel mapping table is correct (has actual coverage names)

**Remediation Options** (optional, NOT required):
1. Improve Lotte Step1 extraction profile (reduce over-extraction)
2. Add sentence-like pattern filter in Step2-a (drop entries with "경우", "진단시", etc.)
3. Accept current state and filter during Step4 evidence search

**Recommended**: Option 2 (add Step2-a sentence filter)

**Rationale**: Benefit descriptions leak through to downstream steps, polluting evidence search.

---

## 5. Non-Outlier Insurers (Within ±30% of Median)

### 5.1 HEUNGKUK (90.9%) — Best Performer

**Why High Rate?**:
- Clean proposal PDF (minimal extraction noise)
- Coverage names align well with Excel
- Only 2 unmapped entries (9.1%)

**Unmapped Examples**:
- "일반상해사망" → Excel has "상해사망" (prefix variant)
- "질병사망(감액없음)" → Excel has "질병사망" (suffix variant)

**Both are expected naming variants, not errors.**

---

### 5.2 SAMSUNG (85.2%)

**Why High Rate?**:
- Good exact match coverage (25 entries)
- Good normalized match coverage (27 entries)
- Low unmapped rate (14.8%)

**Unmapped Examples**:
- "암 진단비(유사암 제외)" → Spacing variant (Excel has "암진단비(유사암제외)")
- "뇌졸중 진단비(1년50%)" → Spacing variant

**Spacing differences are cosmetic, not infrastructure errors.**

---

### 5.3 DB (83.3%)

**Why High Rate?**:
- Good exact match coverage (29 entries)
- Good normalized match coverage (11 entries)
- Low unmapped rate (16.7%)

**Unmapped Examples**:
- "상해사망·후유장해(20-100%)" → Combined coverage (Excel has separate entries)

**Multi-coverage bundling is expected in DB proposals.**

---

### 5.4 HANWHA (79.4%)

**Why Moderate Rate?**:
- Excellent exact match coverage (27 entries, 79.4%)
- Zero normalized matches (normalization not needed)
- Low unmapped rate (20.6%)

**Unmapped Examples**:
- "- 4대유사암진단비(기타피부암)" → Sub-item marker ("- ") not stripped

**Sub-item markers should be stripped in Step2-a (minor quality issue).**

---

### 5.5 HYUNDAI (67.6%)

**Why Moderate Rate?**:
- Good exact match coverage (22 entries)
- Minimal normalized matches (1 entry)
- Moderate unmapped rate (32.4%)

**Unmapped Examples**:
- "골절진단(치아파절제외)담보" → Excel has "골절진단비(치아파절제외)" ("담보" suffix + "진단" vs "진단비")

**"담보" suffix is Hyundai-specific. Excel already accounts for this (exact matches work).**

---

### 5.6 KB (66.7%)

**Why Moderate Rate?**:
- Good exact match coverage (24 entries)
- Zero normalized matches
- Moderate unmapped rate (33.3%)

**Unmapped Examples**:
- "최초1회" → Clause fragment (should be dropped by Step2-a)

**This is a Step2-a quality issue (fragment leak).**

---

## 6. Cross-Insurer Patterns

### 6.1 Naming Variant Patterns (Expected)

| Pattern              | Example                       | Insurers      | Status |
|----------------------|-------------------------------|---------------|--------|
| Prefix variants      | "일반상해사망" vs "상해사망"     | KB, HEUNGKUK  | ✅ Expected |
| Suffix variants      | "질병사망담보" vs "질병사망"     | HYUNDAI       | ✅ Expected |
| Spacing variants     | "암 진단비" vs "암진단비"       | SAMSUNG       | ✅ Expected |
| Condition variants   | "질병사망(감액없음)" vs "질병사망" | HEUNGKUK      | ✅ Expected |
| Combined coverages   | "상해사망·후유장해" vs separate | DB            | ✅ Expected |

**Conclusion**: These are **insurance industry naming conventions**, not bugs.

---

### 6.2 Systematic Alias Gaps (Fixable, but NOT Bugs)

| Pattern              | Example                       | Insurer | Impact | Fix Priority |
|----------------------|-------------------------------|---------|--------|--------------|
| Number prefixes      | "155 뇌졸중진단비"             | MERITZ  | 83.3% unmapped | Low (insurer-specific) |
| Sub-item markers     | "- 4대유사암진단비"            | HANWHA  | Minor  | Low |
| Benefit descriptions | "상해사고로 사망한 경우..."     | LOTTE   | 67.2% unmapped | Medium (noise pollution) |

**Conclusion**: These are **data quality issues**, addressable in Step1/Step2-a. NOT infrastructure errors.

---

### 6.3 Step2-a Sanitization Leaks (Quality Issues)

| Type                 | Example           | Insurers     | Fix Priority |
|----------------------|-------------------|--------------|--------------|
| Clause fragments     | "최초1회"          | KB           | Medium |
| Sub-item markers     | "- ..."           | HANWHA       | Low |
| Benefit descriptions | Full sentences    | LOTTE        | Medium |

**Conclusion**: Step2-a should be improved to catch these, but they do NOT constitute infrastructure errors.

---

## 7. Infrastructure Error Check

**Question**: Do any insurers exhibit the DB-class bug (wrong insurer code)?

**Answer**: ❌ **NO**

**DB-Class Bug Characteristics**:
1. Wrong insurer code in `INSURER_CODE_MAP` (e.g., N11 instead of N13)
2. Results in **0% mapping** (total Excel lookup failure)
3. Affects ALL coverages uniformly

**Current Outliers**:
- **MERITZ** (16.7%): Partial mapping (5 exact + 1 normalized = 6 mapped out of 36)
- **LOTTE** (32.8%): Partial mapping (20 exact + 1 normalized = 21 mapped out of 64)

**Both have SOME successful mappings → insurer codes are CORRECT → NO infrastructure error.**

---

## 8. Deviation Analysis

| Insurer  | Rate  | Deviation from Median | % Deviation | Outlier? | Reason |
|----------|-------|-----------------------|-------------|----------|--------|
| HEUNGKUK | 90.9% | +17.4%                | +23.6%      | ❌ No    | Within ±30% |
| SAMSUNG  | 85.2% | +11.7%                | +15.9%      | ❌ No    | Within ±30% |
| DB       | 83.3% | +9.8%                 | +13.4%      | ❌ No    | Within ±30% |
| HANWHA   | 79.4% | +5.9%                 | +8.0%       | ❌ No    | Within ±30% |
| HYUNDAI  | 67.6% | -5.9%                 | -8.0%       | ❌ No    | Within ±30% |
| KB       | 66.7% | -6.8%                 | -9.3%       | ❌ No    | Within ±30% |
| LOTTE    | 32.8% | -40.7%                | -55.4%      | ✅ YES   | Extraction noise |
| MERITZ   | 16.7% | -56.9%                | -77.3%      | ✅ YES   | Number prefix alias gap |

**Threshold**: ±30% from median (73.5%)

---

## 9. Recommendations

### 9.1 Immediate (No Action Required)
1. ✅ Accept MERITZ and LOTTE outlier status as **explained**
2. ✅ Document patterns in this report
3. ✅ Proceed with current infrastructure (no bugs detected)

### 9.2 Future Quality Improvements (Optional)

**Priority 1 (Medium Impact)**:
1. Add Step2-a sentence filter for Lotte benefit descriptions
2. Add Step2-a clause fragment filter for KB "최초1회" style

**Priority 2 (Low Impact)**:
1. Add Meritz number-prefix normalization rule
2. Add sub-item marker stripping ("- ") in Step2-a

**Priority 3 (Cosmetic)**:
1. Review Lotte Step1 extraction profile to reduce over-extraction
2. Add spacing normalization for Samsung (cosmetic only)

### 9.3 DO NOT DO
- ❌ Add LLM-based fuzzy matching
- ❌ Lower mapping thresholds to "fix" outliers
- ❌ Auto-generate missing aliases

---

## 10. Conclusion

**Verdict**: ✅ **PASS**

**Summary**:
1. **2 outliers detected** (MERITZ 16.7%, LOTTE 32.8%)
2. **Both outliers are fully explained**:
   - MERITZ: Number-prefix alias gap (systematic but not a bug)
   - LOTTE: Step1 extraction noise (quality issue)
3. **Zero infrastructure-level errors** (no wrong insurer codes, no Excel mismatches)
4. **All other insurers within acceptable range** (66.7%–90.9%)

**Contrast with DB Case**:
- DB bug: Wrong code (N11→N13) → 0% mapping → **infrastructure error** ✅ **FIXED**
- MERITZ: Correct code (N01) → 16.7% mapping → **alias gap** → **NOT a bug**
- LOTTE: Correct code (N03) → 32.8% mapping → **extraction noise** → **NOT a bug**

**Key Insight**:
Low mapping rates do NOT automatically indicate bugs.
They indicate **data quality issues** (aliases, extraction, formatting).

**Audit C Conclusion**: No infrastructure-level errors detected. Proceed to Final Summary.
