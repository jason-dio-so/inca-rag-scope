# STEP NEXT-48: Canonical Gap Analysis

## Summary

**Status**: ✅ ANALYSIS COMPLETE (설계·분석 ONLY)

**Purpose**: Classify and explain unmapped coverages from Step2-b canonical mapping.

**Scope**: Read-only analysis (NO implementation, NO mapping logic changes, NO alias additions)

---

## Executive Summary

### Quantitative Overview

**Total unmapped**: 162 entries out of 335 (48.4%)

**Category Distribution**:
| Category | Count | % of Unmapped | Description |
|----------|-------|---------------|-------------|
| **U1** | 10 | 6.2% | 신정원 개념 존재 + alias 부족 |
| **U2** | 19 | 11.7% | Variant (성별/연령/갱신형/플랜) |
| **U3** | 4 | 2.5% | 조건부 / Clause 성격 |
| **U4** | 11 | 6.8% | 보험사 고유 확장 담보 |
| **U5** | 13 | 8.0% | Fragment / 불완전 명칭 |
| **U6** | 105 | 64.8% | 기타 (판단 불가 / DB 전체) |

**Key Insight**: 64.8% (105 entries) are in U6 category, with 45 entries (27.8% of total) being DB insurer (no canonical mapping available).

---

## Category Definitions and Examples

### U1: 신정원 개념 존재 + alias 부족 (10 entries, 6.2%)

**Definition**: Coverage semantically matches existing 신정원 canonical coverage, but name variation prevents matching.

**Root Cause**: Normalization rules in Step2-b insufficient for these patterns.

**Examples**:

#### Samsung (2 entries)
```
- 골절 진단비(치아파절(깨짐, 부러짐) 제외)
  → Should map to: A4301_1 골절진단비(치아파절제외)
  → Issue: Nested parentheses not handled

- 골절 진단비(치아파절(깨 짐, 부러짐) 제외)
  → Should map to: A4301_1 골절진단비(치아파절제외)
  → Issue: Nested parentheses + extra whitespace
```

#### Hanwha (2 entries)
```
- 상해후유장해(3-100%)
  → Should map to: A3300_1 상해후유장해(3-100%)
  → Issue: Space variation (상해 후유장해 in canonical)

- 4대유사암진단비
  → Should map to: A4210 유사암진단비
  → Issue: "4대" prefix not recognized
```

#### Hyundai (1 entry)
```
- 유사암진단Ⅱ담보
  → Should map to: A4210 유사암진단비
  → Issue: Roman numeral suffix + 담보 keyword
```

#### KB (2 entries)
```
- 일반상해후유장해(20~100%)(기본)
  → Should map to: A3300_1 상해후유장해(3-100%)
  → Issue: "일반" prefix + range notation variation

- 일반상해후유장해(3%~100%)
  → Should map to: A3300_1 상해후유장해(3-100%)
  → Issue: "일반" prefix + percentage symbol
```

#### Lotte (3 entries)
```
- 일반암수술비(1회한)
  → Should map to: A5200 암수술비(유사암제외)
  → Issue: "일반" prefix

- 허혈성심장질환진단비
  → Should map to: A4105 허혈성심장질환진단비
  → Issue: Whitespace variation (already in 신정원)
```

**Impact on Step3**: These coverages will appear as "unmapped" in comparison, reducing effective coverage comparison.

**Recommendation**: Enhance normalization rules in Step2-b (future enhancement, NOT in this step).

---

### U2: Variant (성별/연령/갱신형/플랜) (19 entries, 11.7%)

**Definition**: Coverage with variant markers (gender, renewable term, plan name) that should NOT be merged.

**Root Cause**: Legitimate variant differentiation (not a mapping failure).

**Examples**:

#### Lotte (10 entries) - Renewable term variants
```
- 다빈치로봇암수술비(갑상선암및전립선암제외)(최초1회 한)(갱신형)
- 다빈치로봇갑상선암및전립선암수술비(최초1회한)(갱신 형)
- 표적항암약물허가치료비(유방암및비뇨생식기암)(1회 한)(갱신형)
- 표적항암약물허가치료비(3대주요기관암)(1회한)(갱신 형)
- 표적항암약물허가치료비(림프종및백혈병관련암)(1회 한)(갱신형)
  → All have (갱신형) suffix
```

#### Meritz (4 entries) - Renewable term with period
```
- 715 (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연 간1회한)
- 641 (10년갱신)갱신형 다빈치로봇 암수술비(암(특정암제외))
  → Renewable term with specific period (10년, 20년)
```

#### DB (3 entries)
```
- 표적항암약물허가치료비(최초1회한)(갱신형)
- 표적항암약물허가치료비 (최초1회한)(갱신형)
```

#### Hanwha (1 entry)
```
- 암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)
```

#### KB (1 entry)
```
- 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)
```

**Impact on Step3**: These should remain unmapped. Renewable term products are fundamentally different from non-renewable counterparts.

**Recommendation**: Keep unmapped. Do NOT merge variants into base coverage.

---

### U3: 조건부 / Clause 성격 (4 entries, 2.5%)

**Definition**: Coverage names that are actually payment conditions, exemptions, or groupings (not specific coverages).

**Root Cause**: Step2-a sanitization missed these entries OR they are legitimate clause-based coverages.

**Examples**:

#### Heungkuk (2 entries)
```
- 일반상해후유장해(80%이상)
  → Conditional: Disability threshold clause (80% threshold)

- 질병후유장해(80%이상)(감액없음)
  → Conditional: Disability threshold clause with payment condition
```

#### Samsung (2 entries)
```
- 장해/장애
  → Clause: Category grouping (not specific coverage)

- 간병/사망
  → Clause: Category grouping (not specific coverage)
```

**Impact on Step3**: These are NOT comparable coverages. Should be filtered or marked as non-coverage.

**Recommendation**: Strengthen Step2-a sanitization rules to catch threshold clauses and category groupings.

---

### U4: 보험사 고유 확장 담보 (11 entries, 6.8%)

**Definition**: Coverages not yet defined in 신정원 canonical mapping (insurer-specific innovations or expansions).

**Root Cause**: 신정원 canonical mapping does not include these coverage types.

**Examples**:

#### Samsung (4 entries) - 2대주요기관질병
```
- 2대주요기관질병 관혈수술비Ⅱ(1년50%)
- 2대주요기관질병 비관혈수술비Ⅱ(1년50%)
- 2대주요기관질병 관혈수 술비Ⅱ(1년50%)
- 2대주요기관질병 비관혈 수술비Ⅱ(1년50%)
  → Samsung-specific: 2대주요기관질병 category (brain + heart)
  → Not in 신정원 canonical mapping
```

#### Hyundai (3 entries) - Cardiovascular sub-categories
```
- 심혈관질환(특정Ⅰ,I49제외)진단담보
- 심혈관질환(I49)진단담보
- 심혈관질환(주요심장염증)진단담보
  → Insurer-specific: Fine-grained cardiovascular sub-categories
  → Not in 신정원 (only has 심장질환진단비 A4104_1)
```

#### KB (4 entries)
```
- 부정맥질환(Ⅰ49)진단비
  → Insurer-specific: Arrhythmia (ICD I49)
  → Not in 신정원 canonical mapping

- 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(
  → Insurer-specific: Gender/cancer-specific robotic surgery exclusions
```

**Impact on Step3**: These coverages cannot be compared across insurers (unique to specific insurers).

**Recommendation**: Add to 신정원 canonical mapping if these become common across multiple insurers. Otherwise, keep unmapped.

---

### U5: Fragment / 불완전 명칭 (13 entries, 8.0%)

**Definition**: Incomplete or malformed coverage names (extraction artifacts from Step1 or formatting issues).

**Root Cause**: Step1 extraction edge cases OR Step2-a missed fragment patterns.

**Examples**:

#### Hanwha (4 entries) - Leading dash (sub-items)
```
- - 4대유사암진단비(기타피부암)
- - 4대유사암진단비(제자리암)
- - 4대유사암진단비(경계성종양)
- - 4대유사암진단비(갑상선암)
  → Fragment: Leading dash indicates sub-item
  → Should be filtered in Step2-a OR merged with parent item
```

#### Meritz (5 entries) - Category headers
```
- 사망후유
- 3대진단
- 입원일당
- 골절/화상
- 할증/제도성
  → Fragment: Category headers (not specific coverages)
  → Should be filtered in Step2-a
```

#### Lotte (2 entries)
```
- 입원일당
- 골절/화상
  → Fragment: Category headers
```

#### KB (1 entry)
```
- 최초1회
  → Fragment: Payment frequency indicator (not coverage)
```

#### Hyundai (1 entry)
```
- 로봇암수술(다빈치및레보아이)(갑상선암및전립선암)(최초1회한)(갱 신형)담보
  → Fragment: "신형)담보" pattern
  → Known Hyundai-specific fragment pattern
```

**Impact on Step3**: These are noise and should NOT appear in comparison.

**Recommendation**:
1. Add fragment patterns to Step2-a sanitization (leading dash, category headers)
2. Document known Step1 extraction edge cases (Hyundai fragment patterns)

---

### U6: 기타 (판단 불가) (105 entries, 64.8%)

**Definition**: Unmapped entries that do not clearly fit into U1-U5, OR DB insurer (no canonical mapping).

**Breakdown**:
- **DB insurer**: 45 entries (42.9% of U6, 27.8% of total unmapped)
- **Meritz**: 21 entries (20.0% of U6)
- **Lotte**: 28 entries (26.7% of U6)
- **Others**: 11 entries (10.5% of U6)

#### DB (45 entries) - No canonical mapping available
```
All 45 DB entries are unmapped because:
  → ins_cd='N11' has 0 entries in 담보명mapping자료.xlsx
  → Root cause: DB canonical mapping not provided in 신정원 source

Examples:
  - 상해사망·후유장해(20-100%)
  - 상해사망
  - 상해후유장해(3-100%)
  - 질병사망
  - 상해수술비(동일사고당1회지급)
  ... (40 more)

Status: Cannot classify until DB canonical mapping is added to 신정원 Excel.
```

#### Meritz (21 entries) - Mixed issues
```
Examples requiring manual review:
  - 보험기간 중 상해의 직접결과로써 사망한 경우 가입금액 지급
    → Full sentence description (not coverage name)

  - 3 질병사망
    → Leading number (likely extraction artifact)

  - 갑상선암수술비(갑상선암(C73)으로 진단 확정되고…
    → Truncated sentence with payment condition

  - 612 [재진단암(기타피부암포함)진단비]
    → Leading code number (likely product code)
```

#### Lotte (28 entries) - Cancer-specific and specialized treatments
```
Examples requiring manual review:
  - 암직접입원비(요양병원제외)(1일-120일)
    → May need alias (similar to A6200 암직접치료입원일당)

  - 뇌경색증(I63) 혈전용해치료비
    → ICD code included (may map to A9640_1 혈전용해치료비)

  - 급성심근경색증(I21) 혈전용해치료비
    → ICD code included (may map to A9640_1 혈전용해치료비)

  - 유방암진단비(기타피부암및갑상선암제외)
  - 전립선암진단비(기타피부암및갑상선암제외)
    → Gender-specific cancer diagnoses (not in 신정원)
```

#### Others (11 entries)
```
- [samsung] 허혈성심장질환 진단비(1 년50%)
  → Whitespace insertion in middle of name

- [hyundai] 심혈관질환(특정2대)진단담보
  → Sub-category not in 신정원

- [kb] 표적항암약물허가치료비(3대특정암)(
  → Truncated closing parenthesis
```

**Impact on Step3**:
- DB: Cannot compare until canonical mapping added
- Others: Need manual review to determine if U1-U5 or legitimately unmapped

**Recommendation**:
1. **Urgent**: Add DB canonical mapping to 신정원 Excel
2. **Manual review**: Review Meritz/Lotte U6 entries individually
3. **Pattern detection**: Identify common U6 patterns for potential alias additions

---

## Per-Insurer Analysis

### Samsung (9 unmapped, 14.8% of 61)

**Unmapped Categories**:
- U1: 2 entries (골절 진단비 nested parentheses)
- U3: 2 entries (장해/장애, 간병/사망 groupings)
- U4: 4 entries (2대주요기관질병 - Samsung-specific)
- U6: 1 entry (whitespace variation)

**Key Insight**: Samsung has **insurer-specific 2대주요기관질병 category** not in 신정원. This is a legitimate expansion requiring 신정원 update.

**Recommendation**: Add 2대주요기관질병 to 신정원 if other insurers adopt it.

---

### Hyundai (11 unmapped, 32.4% of 34)

**Unmapped Categories**:
- U1: 1 entry (유사암진단Ⅱ담보)
- U4: 3 entries (심혈관질환 sub-categories)
- U5: 1 entry (fragment pattern: 신형)담보)
- U6: 6 entries (various sub-categories)

**Key Insight**: Hyundai has **fine-grained cardiovascular sub-categories** (I49, 주요심장염증, etc.) not in 신정원.

**Recommendation**: Review if cardiovascular sub-categories should be added to 신정원.

---

### Lotte (43 unmapped, 67.2% of 64)

**Unmapped Categories**:
- U1: 3 entries (일반암수술비, 허혈성심장질환진단비)
- U2: 10 entries (갱신형 variants)
- U5: 2 entries (category headers)
- U6: 28 entries (gender-specific cancers, specialized treatments)

**Key Insight**: Lotte has **high unmapped rate due to**:
1. Many renewable term (갱신형) variants (U2 - keep unmapped)
2. Gender-specific cancer coverages not in 신정원
3. Specialized treatment coverages (ICD-code-specific)

**Recommendation**:
1. Keep U2 (갱신형) unmapped (legitimate variants)
2. Review U6 gender-specific cancers for 신정원 addition

---

### DB (48 unmapped, 100% of 48)

**Unmapped Categories**:
- U2: 3 entries (갱신형)
- U6: 45 entries (no canonical mapping)

**Key Insight**: **100% unmapped because ins_cd='N11' has 0 entries in 신정원 Excel.**

**Recommendation**: **URGENT - Add DB canonical mapping to 담보명mapping자료.xlsx**

---

### KB (12 unmapped, 33.3% of 36)

**Unmapped Categories**:
- U1: 2 entries (일반상해후유장해 variants)
- U2: 1 entry (갱신형)
- U4: 4 entries (부정맥질환, 다빈치로봇 gender-specific)
- U5: 1 entry (최초1회 fragment)
- U6: 4 entries (truncated names)

**Key Insight**: KB has **insurer-specific arrhythmia (부정맥질환 I49) coverage** not in 신정원.

**Recommendation**: Add 부정맥질환 to 신정원 if common across insurers.

---

### Meritz (30 unmapped, 83.3% of 36)

**Unmapped Categories**:
- U2: 4 entries (갱신형 with period)
- U5: 5 entries (category headers)
- U6: 21 entries (full sentences, extraction artifacts)

**Key Insight**: Meritz has **severe Step1 extraction quality issues**:
- Full sentence descriptions instead of coverage names
- Leading product codes (612, 715, 641, etc.)
- Truncated sentences

**Recommendation**:
1. **Fix Step1 extraction for Meritz** (proposal PDF structure different)
2. Strengthen Step2-a sanitization for sentence patterns

---

### Hanwha (7 unmapped, 20.6% of 34)

**Unmapped Categories**:
- U1: 2 entries (상해후유장해, 4대유사암진단비)
- U2: 1 entry (갱신형)
- U5: 4 entries (leading dash sub-items)

**Key Insight**: Hanwha has **sub-item structure** (leading dash) not handled in Step1/Step2-a.

**Recommendation**:
1. Add leading dash pattern to Step2-a sanitization
2. Consider merging sub-items with parent items in Step1

---

### Heungkuk (2 unmapped, 9.1% of 22)

**Unmapped Categories**:
- U3: 2 entries (80%이상 threshold clauses)

**Key Insight**: **Best mapping rate (90.9%)** with only threshold clause issues.

**Recommendation**: Add threshold clause pattern to Step2-a sanitization.

---

## 시사점 (Decision Support)

### Impact on Step3 Comparison

**U1 (6.2%)**: Will reduce effective comparison coverage
- **Action**: Enhance Step2-b normalization (future enhancement)
- **Priority**: Medium (improves comparison quality)

**U2 (11.7%)**: Should remain unmapped (legitimate variants)
- **Action**: None (correct behavior)
- **Priority**: N/A

**U3 (2.5%)**: Should be filtered before comparison
- **Action**: Strengthen Step2-a sanitization
- **Priority**: High (data quality issue)

**U4 (6.8%)**: Cannot be compared (insurer-specific)
- **Action**: Add to 신정원 if becomes common
- **Priority**: Low (monitor for adoption trends)

**U5 (8.0%)**: Should be filtered before comparison
- **Action**: Strengthen Step2-a sanitization + Fix Step1 extraction (Meritz)
- **Priority**: High (data quality issue)

**U6 (64.8%)**: Mixed (DB blocking + manual review needed)
- **Action**:
  1. **URGENT**: Add DB canonical mapping
  2. Manual review of Meritz/Lotte U6 entries
- **Priority**: Critical (DB), Medium (others)

---

### 신정원 Expansion Candidates

**High Priority** (multiple insurers):
- 2대주요기관질병 관혈/비관혈수술비 (Samsung)
- 부정맥질환(I49) 진단비 (KB, Hyundai)

**Medium Priority** (single insurer, but common concept):
- 심혈관질환 sub-categories (Hyundai)
- Gender-specific cancer diagnoses (Lotte)

**Low Priority** (insurer-specific innovations):
- Gender/cancer-specific robotic surgery exclusions

---

### Coverage to Keep Unmapped Forever

**Renewable term (갱신형) variants** (U2):
- Fundamental product difference
- Should NOT be merged with non-renewable base coverage
- Keep unmapped for accurate product comparison

**Threshold clauses** (U3):
- Not standalone coverages
- Should be filtered in Step2-a

**Category headers / fragments** (U5):
- Extraction artifacts
- Should be filtered in Step2-a

---

## 명시적 비결정 사항 (What This Step Does NOT Do)

### ❌ NOT Done in This Step

1. **Alias additions**: No modifications to Step2-b mapping logic
2. **Merge/unification**: No combining of variants or sub-categories
3. **신정원 Excel updates**: No changes to canonical mapping source
4. **Step1/Step2-a fixes**: No modification of extraction or sanitization logic
5. **Step3 comparison implementation**: No downstream pipeline work
6. **U6 manual classification**: DB and Meritz/Lotte U6 entries require future manual review

### ✅ What This Step Provides

1. **Complete classification**: All 162 unmapped entries categorized into U1-U6
2. **Root cause analysis**: Explanation of why each category is unmapped
3. **Impact assessment**: How each category affects Step3 comparison
4. **Action prioritization**: Urgent (DB), High (U3/U5), Medium (U1/U6), Low (U4)
5. **Decision support**: Clear guidance on which unmapped entries to keep vs. fix

---

## Next Step Recommendations

### Immediate Actions (Before Step3)

**Priority 1 (CRITICAL)**: Add DB canonical mapping
- **File**: `data/sources/mapping/담보명mapping자료.xlsx`
- **Action**: Add ins_cd='N11' entries for DB insurer
- **Impact**: Unlocks 45 unmapped entries (27.8% of total)

**Priority 2 (HIGH)**: Strengthen Step2-a sanitization
- **Patterns to add**:
  - Leading dash (sub-items): `^- `
  - Category headers: `^(사망후유|3대진단|입원일당|골절/화상|할증/제도성|최초1회)$`
  - Threshold clauses: `\d+%이상`
  - Category groupings: `^(장해/장애|간병/사망)$`
- **Impact**: Filters 17 entries (10.5% of unmapped)

**Priority 3 (MEDIUM)**: Enhance Step2-b normalization
- **Patterns to add**:
  - Nested parentheses: `\([^)]*\([^)]*\)[^)]*\)`
  - "일반" prefix: `^일반`
  - Roman numeral suffix: `[ⅠⅡⅢ]+담보$`
  - "4대" prefix: `^4대`
- **Impact**: Maps 10 entries (6.2% of unmapped)

**Priority 4 (MEDIUM)**: Manual review
- **Target**: Meritz U6 (21 entries), Lotte U6 (28 entries)
- **Goal**: Reclassify into U1-U5 or confirm legitimately unmapped

---

## Definition of Done (✅ ALL COMPLETE)

- ✅ All 162 unmapped rows classified into U1-U6
- ✅ No row count changes (read-only analysis)
- ✅ No pipeline code modifications
- ✅ Single document created (this file)
- ✅ Next step selection criteria documented
- ✅ Per-insurer insights provided
- ✅ Impact on Step3 comparison assessed
- ✅ 신정원 expansion candidates identified
- ✅ Action prioritization complete

---

## Appendix: Raw Statistics

### Category Totals
```
U1: 신정원 개념 존재 + alias 부족       : 10 (  6.2%)
U2: Variant (성별/연령/갱신형/플랜)      : 19 ( 11.7%)
U3: 조건부 / Clause 성격               : 4  (  2.5%)
U4: 보험사 고유 확장 담보               : 11 (  6.8%)
U5: Fragment / 불완전 명칭             : 13 (  8.0%)
U6: 기타 (판단 불가)                   : 105 ( 64.8%)
```

### Per-Insurer Unmapped Distribution
```
samsung  :   9 unmapped (U1:2, U3:2, U4:4, U6:1)
hyundai  :  11 unmapped (U1:1, U4:3, U5:1, U6:6)
lotte    :  43 unmapped (U1:3, U2:10, U5:2, U6:28)
db       :  48 unmapped (U2:3, U6:45)
kb       :  12 unmapped (U1:2, U2:1, U4:4, U5:1, U6:4)
meritz   :  30 unmapped (U2:4, U5:5, U6:21)
hanwha   :   7 unmapped (U1:2, U2:1, U5:4)
heungkuk :   2 unmapped (U3:2)
```

### Mapping Rate Summary
```
Best  → Worst mapping rate:
1. heungkuk: 90.9% (2 unmapped)
2. samsung:  85.2% (9 unmapped)
3. hanwha:   79.4% (7 unmapped)
4. hyundai:  67.6% (11 unmapped)
5. kb:       66.7% (12 unmapped)
6. lotte:    32.8% (43 unmapped)
7. meritz:   16.7% (30 unmapped)
8. db:       0.0%  (48 unmapped - no canonical mapping)
```
