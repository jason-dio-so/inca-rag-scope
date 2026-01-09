# STEP NEXT-G: Diagnosis Slot Completeness Validation (Samsung + KB)

## 목표

Registry에 등재된 **전 진단비** (암·뇌졸중·허혈성)에 대해 Samsung + KB 보험사의 **슬롯 채움률**을 검증하고, UNKNOWN 사유를 분류한다.

### Validation Scope

- **Coverage Types:** 6 types (A4200_1, A4209, A4210, A4299_1, A4103, A4105)
- **Insurers:** Samsung, KB
- **Slots:** 10 slots (6 core + 4 extended)
  - **Core:** start_date, waiting_period, reduction, payout_limit, entry_age, exclusions
  - **Extended:** underwriting_condition, mandatory_dependency, payout_frequency, industry_aggregate_limit

### UNKNOWN Classification

Each UNKNOWN slot is classified into:

1. **UNKNOWN_MISSING** (❓)
   - Evidence does NOT exist in source documents
   - Document gap (약관/요약서/사업방법서에 정보 없음)
   - **Action:** 문서 보완 요청 or 고객 안내 "정보 없음"

2. **UNKNOWN_SEARCH_FAIL** (🔍)
   - Evidence EXISTS but extraction/attribution failed
   - Causes:
     - **G5 Attribution Gate:** Cross-coverage contamination blocked
     - **Normalization failure:** Pattern matching failed
     - **Schema violation:** Value doesn't match expected schema
   - **Action:** Evidence quality 개선 (STEP NEXT-H)

---

## Overall Results

### Statistics

| Category | Count | Percentage |
|----------|-------|-----------|
| **Total Slots Checked** | 110 | 100.0% |
| ✅ **FOUND** | 19 | 17.3% |
| ❓ **UNKNOWN_MISSING** | 20 | 18.2% |
| 🔍 **UNKNOWN_SEARCH_FAIL** | 71 | **64.5%** |

### Key Findings

1. **Low FOUND rate (17.3%)**
   - Most diagnosis slots have evidence but fail G5 attribution gate
   - Strong evidence quality issue, NOT document gap

2. **High SEARCH_FAIL rate (64.5%)**
   - 71 slots have evidence in Step3 but demoted in Step4
   - Primary cause: **G5 Attribution Gate blocking cross-coverage contamination**
   - Secondary cause: Target coverage not explicitly mentioned

3. **Moderate MISSING rate (18.2%)**
   - 20 slots genuinely lack evidence in source docs
   - Mostly extended slots (underwriting_condition, mandatory_dependency, etc.)

---

## Completeness by Insurer

### Samsung

| Status | Count | Percentage | Notes |
|--------|-------|-----------|-------|
| ✅ FOUND | 9 / 50 | 18.0% | Slightly better than KB |
| ❓ MISSING | 20 / 50 | 40.0% | All missing in extended slots |
| 🔍 SEARCH_FAIL | 21 / 50 | 42.0% | G5 gate blocks most |

**Samsung Characteristics:**
- Extended slots completely missing (underwriting_condition, mandatory_dependency, etc.)
- Core slots mostly have evidence but fail attribution

### KB

| Status | Count | Percentage | Notes |
|--------|-------|-----------|-------|
| ✅ FOUND | 10 / 60 | 16.7% | Slightly worse than Samsung |
| ❓ MISSING | 0 / 60 | **0.0%** | No missing! All have evidence |
| 🔍 SEARCH_FAIL | 50 / 60 | **83.3%** | Very high G5 block rate |

**KB Characteristics:**
- **Zero MISSING:** All slots have evidence in docs
- **Massive SEARCH_FAIL:** G5 gate blocks 83.3% of slots
- Evidence quality issue: Cross-coverage contamination widespread

---

## Completeness by Coverage

| Coverage Code | Canonical Name | FOUND | MISSING | SEARCH_FAIL | Total | FOUND % |
|---------------|----------------|-------|---------|-------------|-------|---------|
| **A4103** | 뇌졸중진단비 | 7 | 4 | 9 | 20 | **35.0%** ✅ |
| **A4105** | 허혈성심장질환진단비 | 6 | 4 | 10 | 20 | **30.0%** |
| **A4299_1** | 재진단암진단비 | 3 | 4 | 13 | 20 | 15.0% |
| **A4210** | 유사암진단비 | 2 | 4 | 14 | 20 | 10.0% |
| **A4200_1** | 암진단비(유사암제외) | 1 | 4 | 15 | 20 | **5.0%** ❌ |
| **A4209** | 고액암진단비 | 0 | 0 | 10 | 10 | **0.0%** ❌❌ |

### Best Performers

1. **뇌졸중진단비 (35.0%)** - Non-cancer diagnosis, cleaner evidence
2. **허혈성심장질환진단비 (30.0%)** - Non-cancer diagnosis

### Worst Performers

1. **고액암진단비 (0.0%)** - 100% search fail (G5 gate blocks all)
2. **암진단비(유사암제외) (5.0%)** - Severe cross-coverage contamination

**Analysis:**
- **Non-cancer diagnosis** (stroke, ischemic) perform BETTER than cancer
- **Cancer diagnosis** suffers from severe cross-coverage mixing
- G5 gate is working correctly but reveals poor evidence separation

---

## Completeness by Slot

### Core Slots

| Slot | FOUND | MISSING | SEARCH_FAIL | Total | FOUND % |
|------|-------|---------|-------------|-------|---------|
| **start_date** | 5 | 0 | 6 | 11 | **45.5%** ✅ |
| **reduction** | 5 | 0 | 6 | 11 | **45.5%** ✅ |
| **payout_limit** | 3 | 0 | 8 | 11 | 27.3% |
| **exclusions** | 2 | 0 | 9 | 11 | 18.2% |
| **waiting_period** | 1 | 0 | 10 | 11 | 9.1% |
| **entry_age** | 0 | 0 | 11 | 11 | **0.0%** ❌ |

**Core Slot Findings:**
- **start_date** and **reduction** perform best (45.5%)
- **entry_age** worst (0.0%) - All blocked by G5 gate
- **Zero MISSING** for all core slots → Evidence exists, attribution fails

### Extended Slots

| Slot | FOUND | MISSING | SEARCH_FAIL | Total | FOUND % |
|------|-------|---------|-------------|-------|---------|
| **payout_frequency** | 3 | 5 | 3 | 11 | **27.3%** ✅ |
| **underwriting_condition** | 0 | 5 | 6 | 11 | 0.0% |
| **mandatory_dependency** | 0 | 5 | 6 | 11 | 0.0% |
| **industry_aggregate_limit** | 0 | 5 | 6 | 11 | 0.0% |

**Extended Slot Findings:**
- **payout_frequency** only slot with FOUND (27.3%)
- Other 3 slots: 50% MISSING (Samsung docs lack these)
- KB has evidence but G5 blocks attribution

---

## Search-Fail Backlog (71 items)

### By Failure Reason

| Reason | Count | Percentage | Notes |
|--------|-------|-----------|-------|
| **G5: 다른 담보 값 혼입** | 40 | 56.3% | Cross-coverage contamination |
| **G5: 담보 귀속 확인 불가** | 31 | 43.7% | Target coverage not mentioned |

### Top Search-Fail Cases

#### Case 1: 암진단비(유사암제외) - 다른 담보 값 혼입

**Coverage:** A4200_1 (Samsung)
**Affected Slots:** start_date, waiting_period, reduction, payout_limit, exclusions
**Reason:** Evidence mentions 유사암진단비, 치료비, 입원일당 (excluded keywords)

**Example Evidence:**
```
[갱신형] 암 요양병원 입원일당Ⅱ (1일이상, 90일한도), 암 직접치료 통원일당
```

**Analysis:**
- Step3 found evidence (FOUND status)
- Evidence contains "입원일당" → matches exclusion keyword
- G5 gate → **REJECTED** (cross-coverage contamination)

---

#### Case 2: 고액암진단비 - 100% Search Fail

**Coverage:** A4209 (KB only)
**Affected Slots:** ALL 10 slots
**Reason:** 담보 귀속 확인 불가 + 다른 담보 값 혼입

**Analysis:**
- KB has evidence for all slots
- But evidence does NOT explicitly mention "고액암진단비"
- Evidence likely mixed with A4200_1 (일반암진단비) or treatment benefits
- G5 gate → **100% REJECT**

**Recommendation:**
- Need to strengthen "고액암진단비" anchor keywords
- OR accept that this coverage may not have dedicated sections in docs

---

#### Case 3: entry_age - 100% Search Fail (All Coverages)

**Slot:** entry_age
**Affected:** ALL 11 diagnosis coverages (Samsung + KB)
**Reason:** 담보 귀속 확인 불가

**Analysis:**
- Step3 finds entry_age evidence (e.g., "15세~90세")
- But evidence excerpts do NOT mention target coverage name
- Likely from product-level or table-level sections
- G5 gate → **100% REJECT** (cannot confirm attribution to specific diagnosis benefit)

**Recommendation:**
- entry_age may be product-level, not coverage-level
- Consider relaxing G5 gate for entry_age slot
- OR improve chunk splitting to capture coverage-specific age ranges

---

## Completeness Matrix

See: `docs/audit/step_next_g_completeness_matrix.md`

### Sample Matrix (뇌졸중진단비)

| Slot | KB | SAMSUNG |
|------|------|------|
| start_date | ✅ | ✅ |
| waiting_period | 🔍 | 🔍 |
| reduction | ✅ | ✅ |
| payout_limit | 🔍 | ✅ |
| entry_age | 🔍 | 🔍 |
| exclusions | 🔍 | ✅ |
| underwriting_condition | 🔍 | ❓ |
| mandatory_dependency | 🔍 | ❓ |
| payout_frequency | ✅ | ❓ |
| industry_aggregate_limit | 🔍 | ❓ |

**Legend:**
- ✅ FOUND (evidence extracted successfully)
- ❓ UNKNOWN_MISSING (no evidence in source documents)
- 🔍 UNKNOWN_SEARCH_FAIL (evidence exists but extraction/attribution failed)

---

## Actionable Insights

### 1. G5 Attribution Gate is Working ✅

- **71 slots blocked** by G5 gate
- **Zero false positives** (contamination=0 validated in STEP NEXT-F)
- G5 correctly prevents cross-coverage contamination

### 2. Evidence Quality Issue (NOT Document Gap) ⚠️

- **Only 18.2% genuinely missing** from docs
- **64.5% have evidence but fail attribution**
- Problem: Evidence excerpts lack target coverage mention

### 3. Improvement Opportunities (STEP NEXT-H)

#### A. Strengthen Anchor Keywords

**Current Issue:**
- Evidence found but target coverage not explicitly mentioned
- Generic keywords like "암", "뇌졸중" not sufficient

**Solution:**
- Add coverage-specific anchors:
  - "암진단비(유사암 제외)" → require full phrase, not just "암"
  - "뇌졸중진단비" → require "진단비", not just "뇌졸중"

#### B. Improve Chunk Splitting

**Current Issue:**
- Chunks mix multiple coverages
- Single chunk contains: 암진단비 + 유사암진단비 + 치료비

**Solution:**
- Split by coverage sections more aggressively
- Detect coverage name headers and split there
- Avoid cross-coverage chunks

#### C. Consider Slot-Specific Attribution Rules

**Current Issue:**
- entry_age 100% fail (likely product-level, not coverage-level)
- start_date often generic

**Solution:**
- **entry_age:** Allow product-level attribution (relax G5)
- **start_date:** Allow global attribution (already has FOUND_GLOBAL)
- **Core benefit slots** (payout_limit, reduction): Keep strict G5

---

## DoD Validation ✅

### Original Requirements (STEP NEXT-G)

- ✅ **Validate all diagnosis types:** 6 coverage types validated
- ✅ **Samsung + KB only:** Filtered to these insurers
- ✅ **Classify UNKNOWN slots:** MISSING vs SEARCH_FAIL taxonomy
- ✅ **Completeness matrix:** Generated (step_next_g_completeness_matrix.md)
- ✅ **Search-fail backlog:** 71 items identified with reasons
- ✅ **No Step1-3 changes:** Analysis only (no pipeline changes)
- ✅ **No LLM:** Pure deterministic classification

### Deliverables

1. **Analysis Tool:** `tools/step_next_g_slot_completeness.py`
2. **Completeness Matrix:** `docs/audit/step_next_g_completeness_matrix.md`
3. **JSON Report:** `docs/audit/step_next_g_slot_completeness.json`
4. **Audit Doc:** `docs/audit/STEP_NEXT_G_DIAGNOSIS_SLOT_COMPLETENESS.md` (THIS FILE)

---

## Next Steps

### STEP NEXT-H: Evidence Quality 개선 (Recommended)

**Goal:** Reduce SEARCH_FAIL from 64.5% to <30%

**Actions:**

1. **Anchor Keyword Strengthening**
   - Require full coverage name mention in evidence excerpts
   - Add coverage-code-specific patterns

2. **Chunk Splitting Enhancement**
   - Detect coverage section boundaries
   - Prevent cross-coverage chunks

3. **Slot-Specific Attribution Rules**
   - entry_age: Allow product-level attribution
   - start_date: Keep FOUND_GLOBAL support
   - Core slots: Maintain strict G5 gate

**Expected Impact:**
- SEARCH_FAIL: 64.5% → 30%
- FOUND: 17.3% → 50%+
- MISSING: 18.2% → unchanged (genuine doc gaps)

### STEP NEXT-I: Customer Question Regression (After STEP NEXT-H)

Re-run Q1, Q2, Q9, Q12 with improved evidence quality.

**Passing Criteria:**
- ✅ Zero incorrect values
- ✅ UNKNOWN allowed (with proper "정보 없음" messaging)
- ✅ No misleading outputs

---

## 완료 상태 메시지

```
✅ STEP NEXT-G 완료

Diagnosis Slot Completeness Results (Samsung + KB):
- Total slots checked: 110 (6 coverages × 2 insurers × ~10 slots)
- FOUND: 19 (17.3%)
- UNKNOWN_MISSING: 20 (18.2%) - genuine doc gaps
- UNKNOWN_SEARCH_FAIL: 71 (64.5%) - G5 attribution failures

Search-Fail Breakdown:
- G5: 다른 담보 값 혼입: 40 cases
- G5: 담보 귀속 확인 불가: 31 cases

Best Coverage: 뇌졸중진단비 (35.0% FOUND)
Worst Coverage: 고액암진단비 (0.0% FOUND)

Best Slot: start_date, reduction (45.5% FOUND)
Worst Slot: entry_age (0.0% FOUND)

Recommendation: Proceed to STEP NEXT-H (Evidence Quality 개선)
```
