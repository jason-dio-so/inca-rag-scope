# Meritz Unmatched Root Causes Analysis

## Overview

- **Total Unmatched**: 12
- **Analysis Date**: 2025-12-27
- **Method**: Deterministic string pattern analysis (no inference)

## Root Cause Classification

| raw_name | reason_type | note |
|---|---|---|
| 일반상해80%이상후유장해[기본계약] | PREFIX_SUFFIX | Prefix "일반" + square brackets "[기본계약]" not in Excel |
| 재진단암진단비(1년대기형) | TOKEN_VARIANT | "1년대기형" vs "1년 대기형" (spacing difference) |
| (20년갱신)갱신형중증질환자(뇌혈관질환) 산정특례대상진단비(연간1회한) | NOT_IN_EXCEL | Full string with prefix "(20년갱신)" not in Excel |
| (20년갱신)갱신형중증질환자(심장질환) 산정특례대상진단비(연간1회한) | NOT_IN_EXCEL | Full string with prefix "(20년갱신)" not in Excel |
| 암직접치료입원일당(Ⅱ)(요양병원제외, 1일이상) | TOKEN_VARIANT | Roman numeral "Ⅱ" + comma spacing variation |
| 일반상해중환자실입원일당(1일이상) | PREFIX_SUFFIX | Prefix "일반" + "중환자실" vs standard "상해입원일당" |
| (10년갱신)갱신형다빈치로봇암수술비(암(특정암제외)) | PREFIX_SUFFIX | Prefix "(10년갱신)갱신형" not in Excel |
| (10년갱신)갱신형다빈치로봇암수술비(특정암) | PREFIX_SUFFIX | Prefix "(10년갱신)갱신형" not in Excel |
| 신화상치료비(화상수술비) | NOT_IN_EXCEL | "신화상치료비" prefix not in Excel |
| 신화상치료비(화상진단비) | NOT_IN_EXCEL | "신화상치료비" prefix not in Excel |
| 신화상치료비(중증화상및부식진단비) | NOT_IN_EXCEL | "신화상치료비" prefix not in Excel |
| (10년갱신)갱신형표적항암약물허가치료비Ⅱ | PREFIX_SUFFIX | Prefix "(10년갱신)갱신형" + Roman numeral "Ⅱ" |

## Reason Type Distribution

| reason_type | count |
|---|---|
| PREFIX_SUFFIX | 5 |
| TOKEN_VARIANT | 2 |
| NOT_IN_EXCEL | 5 |

## Patterns Observed (Fact-Only)

### PREFIX_SUFFIX (5 cases)
- Galjenable renewal prefix: "(10년갱신)갱신형", "(20년갱신)갱신형"
- Product variant prefix: "일반", "신"
- Bracketed suffix: "[기본계약]"

### TOKEN_VARIANT (2 cases)
- Spacing differences: "1년대기형" vs "1년 대기형"
- Roman numeral variations: "Ⅱ" character encoding
- Comma spacing: "제외, 1일" vs "제외,1일"

### NOT_IN_EXCEL (5 cases)
- Full coverage names not present in mapping Excel
- Includes specialized variants (중증질환자, 신화상치료비)

## Recommendation (Fact-Based)

To improve match rate:
1. Add exact strings to Excel mapping file
2. Enhance normalization to handle:
   - Renewal period prefixes: (N년갱신)
   - Product variant prefixes: 일반, 신
   - Spacing in parentheses
   - Roman numeral normalization

**Note**: No new canonical codes should be created. Only add aliases to existing codes if semantically identical.
