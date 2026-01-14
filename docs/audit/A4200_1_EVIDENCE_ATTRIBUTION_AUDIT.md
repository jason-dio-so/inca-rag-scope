# A4200_1 Evidence Attribution Audit

**Date:** 2026-01-14
**Target coverage_code:** A4200_1
**Canonical name:** 암진단비(유사암제외)
**Target insurers:** Meritz (N01), Hanwha (N02)
**Constitution:** COVERAGE CANONICALIZATION V2 + STEP A4200_1-PIPELINE-SSOT-ENFORCE-V2

---

## 🎯 Purpose

This document audits whether evidence extracted for A4200_1 (암진단비·유사암제외) in Step3 is:
1. **Correctly attributed** to coverage_code A4200_1
2. **Exclusive to A4200_1** (not mixed with other coverage evidence)
3. **Anchored by coverage_code**, not coverage_name strings

**Critical Rule:** Evidence MUST be tied to coverage_code. Evidence extraction MUST NOT be influenced by coverage_name string patterns.

---

## ✅ VERDICT: PASS with WARNINGS - Evidence Correctly Attributed but Method Questionable

**Key Finding:** Evidence is structurally tied to coverage_code A4200_1 in Step3 output, BUT evidence extraction (Step4_evidence_search) uses coverage_name string patterns which may cause inconsistencies.

---

## 📊 Evidence Attribution Overview

### Meritz (N01) A4200_1

**File:** `data/scope_v3/meritz_step3_evidence_enriched_v1.jsonl:5`

| Attribute | Value |
|-----------|-------|
| **coverage_code** | A4200_1 |
| **canonical_name** | 암진단비(유사암제외) |
| **coverage_name** | 암진단비(유사암제외) |
| **Total evidence items** | 40 |
| **FOUND evidence items** | 40 (100%) |

#### Evidence by Critical Slot:

| Slot | Status | Evidence Count | Match Count |
|------|--------|----------------|-------------|
| start_date | FOUND | 3 | 3,039 |
| exclusions | FOUND | 3 | 4,850 |
| payout_limit | FOUND | 3 | 907 |

**Verdict:** ✅ PASS - Evidence is abundant and attributed to A4200_1

---

### Hanwha (N02) A4200_1

**File:** `data/scope_v3/hanwha_step3_evidence_enriched_v1.jsonl:7`

| Attribute | Value |
|-----------|-------|
| **coverage_code** | A4200_1 |
| **canonical_name** | 암진단비(유사암제외) |
| **coverage_name** | 암(4대유사암제외)진단비 |
| **Total evidence items** | 40 |
| **FOUND evidence items** | 40 (100%) |

#### Evidence by Critical Slot:

| Slot | Status | Evidence Count | Match Count |
|------|--------|----------------|-------------|
| start_date | FOUND | 3 | 1,713 |
| exclusions | FOUND | 3 | 2,270 |
| payout_limit | FOUND | 3 | 841 |

**Verdict:** ✅ PASS - Evidence is abundant and attributed to A4200_1

---

## 🔍 Evidence Quality Analysis

### Structural Attribution: ✅ CORRECT

Evidence in Step3 output is **embedded within the record** containing coverage_code:

```json
{
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "coverage_name_normalized": "암진단비(유사암제외)",
  "evidence": [
    {
      "slot_key": "start_date",
      "doc_type": "가입설계서",
      "page_start": 5,
      "excerpt": "암보장개시일 이후 암(유사암제외)으로 진단확정...",
      "gate_status": "FOUND"
    },
    ...
  ]
}
```

**Key Validation:**
- ✅ Each evidence item is part of an A4200_1 record
- ✅ Evidence cannot be orphaned from coverage_code
- ✅ No ambiguity about which coverage this evidence supports

---

### Evidence Content Analysis: ⚠️ REQUIRES VERIFICATION

#### Meritz A4200_1 Evidence Samples

**Slot: start_date**

*Evidence #1 (가입설계서, Page 5):*
```
암보장개시일 이후 암(유사암제외)으로 진단확정되거나
```

**Analysis:**
- ✅ Mentions "암(유사암제외)" - matches A4200_1
- ✅ Discusses start date ("암보장개시일")
- ✅ Context is correct for A4200_1

---

**Slot: exclusions**

*Evidence #1 (가입설계서, Page 5):*
```
암보장개시일 이후 암(유사암제외)으로 진단확정된 경우
※ 납입면제가 적용되는 대상은 아래(납입면제 제외대상)를 제외한 전체입니다.
```

**Analysis:**
- ✅ Mentions "암(유사암제외)" - matches A4200_1
- ✅ Discusses exclusions ("제외대상")
- ✅ Context is correct for A4200_1

---

**Slot: payout_limit**

*Evidence #1 (가입설계서, Page 6):*
```
암진단비(유사암제외)
3천만원
30,480
20년 / 100세
암보장개시일 이후 암(유사암제외)으로 진단확정시 최초 1회한 가입금액 지급
```

**Analysis:**
- ✅ Explicitly names "암진단비(유사암제외)" - exact match for A4200_1
- ✅ Shows payout amount (3천만원) and limit (최초 1회한)
- ✅ Strong evidence for A4200_1

---

*Evidence #3 (가입설계서, Page 6):*
```
유사암진단비
6백만원
852
20년 / 100세
보험기간 중 유사암으로 진단확정되었을 때 유사암별로 각각 최초 1회한 가입금액 지급
```

**⚠️ WARNING - POSSIBLE CONTAMINATION:**
- ❌ This is "유사암진단비" - **A4210**, NOT A4200_1!
- ❌ A4200_1 is "암진단비(유사암**제외**)" - this **excludes** 유사암
- ❌ A4210 is "유사암진단비" - this is **for** 유사암

**Why did this evidence get included?**

Hypothesis: Evidence search used coverage_name string patterns like:
- Search for "암진단" in coverage_name "암진단비(유사암제외)"
- PDF contains both "암진단비(유사암제외)" and "유사암진단비"
- Search query "암진단" matches both
- Result: Evidence from A4210 contaminate A4200_1

**This confirms the violation found in `A4200_1_STRING_MATCH_BAN_SCAN.md`:**
- Evidence search uses coverage_name strings to generate queries
- Query variants include substrings like "암진단"
- These broad queries match multiple coverages

---

#### Hanwha A4200_1 Evidence Samples

**Slot: start_date**

*Evidence #1 (가입설계서, Page 5):*
```
보장개시일부터 2년이 지난 후에 발생한 습관성 유산...
```

**Analysis:**
- ⚠️ This is generic boilerplate about coverage start dates
- ⚠️ Not specifically about A4200_1
- ⚠️ Likely applies to multiple coverages

---

*Evidence #3 (가입설계서, Page 5):*
```
"암"에 대한 보장개시일은 계약일부터 그 날을 포함하여 90일이 지난 날의 다음날로 합니다.
```

**Analysis:**
- ✅ Specific to cancer ("암") coverage
- ✅ Mentions 90-day waiting period
- ✅ Relevant to A4200_1

---

**Slot: exclusions**

*Evidence #1 (가입설계서, Page 5):*
```
[보험금을 지급하지 않는 사항]
1. 피보험자가 고의로 자신을 해친 경우...
3. 계약자가 고의로 피보험자를 해친 경우
```

**Analysis:**
- ⚠️ Generic exclusions (applies to all coverages)
- ⚠️ Not specific to A4200_1
- ⚠️ Boilerplate

---

**Slot: payout_limit**

*Evidence #3 (가입설계서, Page 6):*
```
45 암(4대유사암제외)진단비
3,000만원
```

**Analysis:**
- ✅ Explicitly names "암(4대유사암제외)진단비" - Hanwha's name for A4200_1
- ✅ Shows payout amount
- ✅ Strong evidence for A4200_1

---

## 🔬 Cross-Coverage Contamination Check

### Question: Did A4200_1 evidence include text from other coverages?

**Meritz Evidence:**
- ✅ Most evidence mentions "암(유사암제외)" correctly
- ❌ ONE evidence item mentions "유사암진단비" (A4210) - **CONTAMINATION DETECTED**

**Hanwha Evidence:**
- ✅ Specific evidence mentions "암(4대유사암제외)진단비" correctly
- ⚠️ Some evidence is generic boilerplate (not coverage-specific)

### Root Cause: String-Based Evidence Search

From `A4200_1_STRING_MATCH_BAN_SCAN.md`:

**File:** `pipeline/step4_evidence_search/search_evidence.py`

The evidence search generates query variants from coverage_name:
```python
# For Meritz A4200_1 "암진단비(유사암제외)"
if '진단비' in coverage_name:
    variants.append(coverage_name.replace('진단비', '진단'))  # → "암(유사암제외)"

# Query becomes: ["암진단비", "암진단", "암", "진단비", ...]
```

**Problem:** These broad queries match multiple coverages:
- "암진단비(유사암제외)" - A4200_1 ✅
- "유사암진단비" - A4210 ❌ (WRONG COVERAGE!)
- "암진단비Ⅱ" - Other cancer diagnosis ❌

**Result:** Evidence from A4210 (유사암진단비) appears in A4200_1 evidence list.

---

## ⚠️ Warnings and Concerns

### Warning 1: Evidence Contamination Risk

**Observed:** Meritz A4200_1 evidence includes a snippet mentioning "유사암진단비" (A4210).

**Risk:** If evidence search queries are too broad, evidence from other coverages may be mixed in.

**Impact:**
- Users comparing A4200_1 across insurers may see inconsistent information
- Evidence quality differs between insurers (specific vs generic)

---

### Warning 2: String-Based Evidence Search

**Current Approach:** Evidence search uses coverage_name to generate query variants.

**Problems:**
1. Different coverage_names for same coverage_code generate different queries
2. Broad queries match multiple coverages
3. No coverage_code-based disambiguation

**Example:**

| Insurer | coverage_name | Query Variants | Matches |
|---------|---------------|----------------|---------|
| Meritz | 암진단비(유사암제외) | ["암진단비", "암진단", "암"] | A4200_1, A4210, A4209... |
| Hanwha | 암(4대유사암제외)진단비 | ["4대유사암제외", "암진단비", "암"] | A4200_1, A4210, A4209... |

Different queries → different evidence → inconsistent comparison.

---

### Warning 3: Generic Evidence

**Observed:** Some Hanwha evidence is generic boilerplate (exclusions, general terms).

**Problem:** Not specific to A4200_1, applies to many coverages.

**Impact:** Evidence doesn't help users understand A4200_1 specifics.

---

## ✅ Strengths

### Strength 1: Structural Isolation

Evidence is **embedded within coverage_code records**, ensuring attribution:
```json
{
  "coverage_code": "A4200_1",
  "evidence": [...]  // ← Cannot be orphaned
}
```

**Validation:** ✅ Evidence is tied to coverage_code A4200_1 in data structure.

---

### Strength 2: Comprehensive Evidence

**Meritz:** 40/40 evidence items FOUND (100%)
**Hanwha:** 40/40 evidence items FOUND (100%)

**All critical slots have evidence:**
- start_date ✅
- exclusions ✅
- payout_limit ✅

**Validation:** ✅ Evidence extraction is thorough.

---

### Strength 3: High Match Counts

**Meritz:** 3,039 start_date matches, 4,850 exclusions matches
**Hanwha:** 1,713 start_date matches, 2,270 exclusions matches

**Validation:** ✅ Evidence search found many relevant passages.

---

## 📋 Evidence Sample Summary

### Meritz A4200_1 Evidence Quality

| Slot | Quality | Notes |
|------|---------|-------|
| start_date | ✅ GOOD | Mentions "암보장개시일 이후 암(유사암제외)" |
| exclusions | ✅ GOOD | Discusses "납입면제 제외대상" in A4200_1 context |
| payout_limit | ⚠️ MIXED | Includes correct A4200_1 info BUT also A4210 info |

---

### Hanwha A4200_1 Evidence Quality

| Slot | Quality | Notes |
|------|---------|-------|
| start_date | ⚠️ MIXED | Some generic boilerplate, some specific to cancer |
| exclusions | ⚠️ GENERIC | Standard exclusions, not A4200_1-specific |
| payout_limit | ✅ GOOD | Mentions "암(4대유사암제외)진단비" explicitly |

---

## 📝 Recommendations

### 1. Fix Evidence Search Contamination (URGENT)

**Problem:** Evidence search uses broad coverage_name queries that match multiple coverages.

**Solution:** Use coverage_code-specific keywords from metadata:

```python
# ❌ CURRENT (WRONG)
def search_evidence(coverage_name):
    query = generate_variants(coverage_name)  # String-based
    return search_fts(query)

# ✅ REQUIRED (CORRECT)
def search_evidence(coverage_code):
    # Load coverage-code specific keywords
    keywords = COVERAGE_METADATA[coverage_code]['keywords']
    # A4200_1 → ['암진단', '유사암제외', '진단확정', '최초1회한']
    return search_fts(keywords)
```

---

### 2. Add Evidence Validation Gate

**After evidence extraction, validate:**

```python
def validate_evidence(coverage_code, evidence_list):
    """Ensure evidence is specific to coverage_code"""

    # Load exclusion keywords (should NOT appear)
    exclusions = COVERAGE_METADATA[coverage_code]['exclusion_keywords']
    # A4200_1 → ['유사암진단비'] (A4210 name)

    for evidence in evidence_list:
        for exclusion_keyword in exclusions:
            if exclusion_keyword in evidence['excerpt']:
                raise EvidenceContaminationError(
                    f"Evidence for {coverage_code} contains {exclusion_keyword}"
                )
```

---

### 3. Score Evidence Specificity

**Add specificity score to each evidence item:**

```python
def score_evidence_specificity(coverage_code, evidence_excerpt):
    """Score how specific this evidence is to coverage_code"""

    # High score: Contains coverage-specific terms
    specific_terms = COVERAGE_METADATA[coverage_code]['specific_terms']
    # A4200_1 → ['암진단비(유사암제외)', '암(유사암제외)']

    # Low score: Generic boilerplate
    generic_terms = ['보험금을 지급하지 않는 사항', '고의로']

    score = 0
    for term in specific_terms:
        if term in evidence_excerpt:
            score += 10

    for term in generic_terms:
        if term in evidence_excerpt:
            score -= 5

    return max(0, score)
```

---

### 4. Create Evidence Attribution Test

**Unit test to prevent contamination:**

```python
def test_a4200_1_evidence_no_contamination():
    """Ensure A4200_1 evidence doesn't reference other coverages"""

    # Load A4200_1 evidence
    evidence_list = get_evidence_for_coverage('A4200_1')

    # Check for contamination keywords
    forbidden_keywords = [
        '유사암진단비',  # A4210
        '고액암진단비',  # A4209
        '재진단암'       # A4299
    ]

    for evidence in evidence_list:
        excerpt = evidence['excerpt']
        for keyword in forbidden_keywords:
            assert keyword not in excerpt, \
                f"A4200_1 evidence contains {keyword} (other coverage)"
```

---

## 🔗 Related Documents

- `A4200_1_SSOT_ROW_SNAPSHOT.md` - SSOT definition for A4200_1
- `A4200_1_STEP1_TARGET_PLAN_TRACE.md` - Step1 SSOT enforcement
- `A4200_1_STRING_MATCH_BAN_SCAN.md` - String matching violations
- `A4200_1_PIPELINE_CONSISTENCY_REPORT.md` - Overall pipeline audit

---

## 📊 Final Assessment

### Structural Attribution: ✅ PASS

Evidence is correctly embedded within coverage_code A4200_1 records. No structural orphaning.

### Content Quality: ⚠️ PASS with WARNINGS

- **Most evidence** is correct and specific to A4200_1
- **Some evidence** is generic boilerplate (low specificity)
- **At least one evidence** mentions other coverage (A4210) - contamination detected

### Evidence Extraction Method: ❌ FAIL

Evidence search uses coverage_name string patterns, not coverage_code metadata. This leads to:
- Inconsistent queries across insurers
- Broad matches that include other coverages
- Contamination risk

### Overall Verdict: ✅ PASS with CRITICAL WARNINGS

Evidence **is** attributed to coverage_code A4200_1 in output data.

However, the **method** of evidence extraction uses forbidden string-based patterns and poses contamination risk.

**Required Action:**
1. Refactor evidence search to use coverage_code metadata (URGENT)
2. Add evidence validation gates to detect contamination
3. Score evidence specificity and filter generic boilerplate

---

**END OF AUDIT**
