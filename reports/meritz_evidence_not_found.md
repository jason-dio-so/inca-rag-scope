# Meritz Evidence Not Found Analysis

## Overview

- **Total Evidence Not Found**: 7
- **Analysis Date**: 2025-12-27
- **All 7 cases are unmatched** (no canonical mapping)

## Search Failure Details

### 1. 일반상해80%이상후유장해[기본계약]

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "일반상해80%이상후유장해[기본계약]"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Unmatched → only raw name searched; special chars "[기본계약]" may not appear verbatim

### 2. (20년갱신)갱신형중증질환자(뇌혈관질환) 산정특례대상진단비(연간1회한)

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "(20년갱신)갱신형중증질환자(뇌혈관질환) 산정특례대상진단비(연간1회한)"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Full complex string not found; "산정특례" may use different formatting in docs

### 3. (20년갱신)갱신형중증질환자(심장질환) 산정특례대상진단비(연간1회한)

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "(20년갱신)갱신형중증질환자(심장질환) 산정특례대상진단비(연간1회한)"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Full complex string not found; "산정특례" may use different formatting in docs

### 4. (10년갱신)갱신형다빈치로봇암수술비(암(특정암제외))

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "(10년갱신)갱신형다빈치로봇암수술비(암(특정암제외))"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Renewal period prefix + nested parentheses not found verbatim

### 5. (10년갱신)갱신형다빈치로봇암수술비(특정암)

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "(10년갱신)갱신형다빈치로봇암수술비(특정암)"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Renewal period prefix not found verbatim

### 6. 신화상치료비(중증화상및부식진단비)

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "신화상치료비(중증화상및부식진단비)"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: "신화상치료비" prefix not found in documents

### 7. (10년갱신)갱신형표적항암약물허가치료비Ⅱ

- **Coverage Code**: N/A (unmatched)
- **Canonical Name**: N/A
- **Search Keywords Used**: "(10년갱신)갱신형표적항암약물허가치료비Ⅱ"
- **Documents Searched**:
  - 약관: 0 hits
  - 사업방법서: 0 hits
  - 상품요약서: 0 hits
- **Root Cause**: Renewal period prefix + Roman numeral "Ⅱ" encoding not found

## Document Type Hit Summary

| Document Type | 0-hit Count |
|---|---|
| 약관 | 7 |
| 사업방법서 | 7 |
| 상품요약서 | 7 |

**All 7 coverages**: Zero hits across all document types

## Root Cause Pattern (Fact-Only)

**Common pattern**: All 7 are **unmatched** coverages
- Unmatched → only `coverage_name_raw` is used for search
- No canonical fallback keywords available
- Complex strings with:
  - Renewal period prefixes: (10년갱신), (20년갱신)
  - Special characters: [], (), Ⅱ
  - Long compound names

## Recommendation (Fact-Based)

To improve evidence discovery:
1. **First priority**: Map these 7 to canonical codes
   - Once mapped, search will use canonical name as primary keyword
   - Increases hit probability significantly
2. **Search enhancement**: Add fuzzy keyword extraction
   - Strip renewal prefixes: (N년갱신)갱신형
   - Extract core coverage name
   - Search with multiple keyword variants
3. **Verify PDF extraction**: Ensure special chars ([], Ⅱ) are correctly extracted from PDFs

**Note**: Current deterministic search requires exact substring match. Zero hits indicate coverage names in 가입설계서 differ significantly from terms used in 약관/사업방법서/상품요약서.
