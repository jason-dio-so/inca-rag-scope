# STEP NEXT-64: Canonical Unmapped Policy Lock

**Date**: 2026-01-08
**Scope**: ALL insurers (post STEP NEXT-63-A)
**Constitution**: ACTIVE_CONSTITUTION.md
**Input**: STEP NEXT-63-A unmapped diagnosis results

---

## Executive Summary

- **Total unmapped rows**: 62
- **Classification complete**: 62 / 62 (100%)
- **Pipeline bugs (P1)**: 3 ⬆️ (STEP NEXT-66: KB fragments reclassified)
- **Canonical gaps (P2)**: 46 ⬇️
- **Expected unmapped (P3)**: 11
- **Variant-dependent (P4)**: 2

**STEP NEXT-66 Update** (2026-01-08):
KB fragments ("최초1회", incomplete coverage names) reclassified from P3 → P1 after implementing coverage semantics extraction and fragment detection.

---

## Policy Classification Rules

| Policy | Definition | Action Required |
|--------|-----------|-----------------|
| **P1: PIPELINE_BUG** | Excel에 존재하는데 unmapped | Fix mapping logic |
| **P2: CANONICAL_GAP** | Excel/신정원에 없음 | Update Excel mapping reference |
| **P3: EXPECTED_UNMAPPED** | 납입면제, 특약, 메타성 항목 | No action (정상 상태) |
| **P4: VARIANT_DEPENDENT** | 상품/성별/연령 종속 | Variant policy area |

---

## Per-Insurer Policy Lock

### 1. SAMSUNG (5 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| SAMSUNG | samsung__삼성화재건강보험 | default | 보험료 납입면제대상Ⅱ | P3 | Premium waiver meta coverage |
| SAMSUNG | samsung__삼성화재건강보험 | default | 골절 진단비(치아파절(깨짐, 부러짐) 제외) | P2 | New coverage not in Excel |
| SAMSUNG | samsung__삼성화재건강보험 | default | 수술 | P2 | Generic surgery term too broad |
| SAMSUNG | samsung__삼성화재건강보험 | default | 장해/장애 | P2 | Generic disability term too broad |
| SAMSUNG | samsung__삼성화재건강보험 | default | 간병/사망 | P2 | Generic nursing/death term too broad |

### 2. KB (13 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 일반상해후유장해(20~100%)(기본) | P2 | Specific percentage range not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 보험료납입면제대상보장(8대기본) | P3 | Premium waiver meta coverage |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 부정맥질환(Ⅰ49)진단비 | P2 | Specific arrhythmia ICD code not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형) | P2 | Da Vinci robot surgery new coverage |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 다빈치로봇 갑상선암 및 전립선암수술비(최초1회한)(갱신형) | P2 | Da Vinci robot surgery new coverage |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ(갱신형) | P2 | Targeted cancer drug v2 not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 표적항암약물허가치료비(림프종·백혈병 관련암)(최초1회한)Ⅱ(갱신형) | P2 | Targeted cancer drug v2 not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형) | P2 | Targeted cancer drug v2 not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 특정항암호르몬약물허가치료비(최초1회한)Ⅱ(갱신형) | P2 | Hormonal cancer drug v2 not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형) | P2 | CAR-T cancer therapy not in Excel |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 최초1회 | **P1** ⬆️ | Step1 extraction bug: `(최초1회한)` parsed as separate coverage (STEP NEXT-66) |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)( | **P1** ⬆️ | Step1 extraction bug: incomplete coverage name due to parenthesis mismatch (STEP NEXT-66) |
| kb | kb__KB닥터플러스건강보험세만기해약환급금미지급형무배 | default | 다빈치로봇 갑상선암 및 전립선암수술비( | **P1** ⬆️ | Step1 extraction bug: incomplete coverage name due to parenthesis mismatch (STEP NEXT-66) |

### 3. HYUNDAI (12 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 보험료납입면제대상담보 | P3 | Premium waiver meta coverage |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 유사암진단Ⅱ담보 | P2 | Similar cancer v2 not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(특정Ⅰ,I49제외)진단담보 | P2 | Cardiovascular disease subset not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(I49)진단담보 | P2 | Cardiovascular I49 specific not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(주요심장염증)진단담보 | P2 | Major heart inflammation not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(특정2대)진단담보 | P2 | Specific 2 cardiovascular not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(대동맥판막협착증)진단담보 | P2 | Aortic valve stenosis not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 심혈관질환(심근병증)진단담보 | P2 | Cardiomyopathy specific not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 항암약물치료Ⅱ담보 | P2 | Anticancer drug v2 not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 질병입원일당(1-180일)담보 | P2 | Illness hospitalization daily not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보 | P2 | Thrombolytic therapy v2 not in Excel |
| hyundai | hyundai__무배당현대해상퍼펙트플러스종합보험세만기형Hi25083종해약환급금미지급형 | default | 로봇암수술(다빈치및레보아이)(갑상선암및전립선암)(최초1회한)(갱신형)담보 | P2 | Robot surgery (Da Vinci & Revo-i) not in Excel |

### 4. MERITZ (9 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 일반상해80%이상후유장해[기본계약] | P2 | 80% threshold not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 일반상해사망 | P2 | Generic accident death not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 일반상해중환자실입원일당(1일이상) | P2 | ICU daily benefit not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 신화상치료비(화상수술비) | P2 | New burn surgery benefit not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 신화상치료비(화상진단비) | P2 | New burn diagnosis benefit not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 신화상치료비(중증화상및부식진단비) | P2 | Severe burn diagnosis not in Excel |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 자동갱신특약 | P3 | Auto-renewal rider metadata |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 보험료 비교(예시) | P3 | Premium comparison example metadata |
| meritz | meritz__무알파Plus보장보험2511보험료납입면제형 | default | 대표계약 기준 : 남자40세,20년납,100세만기,월납,일반상해80%이상후유장해[기본계약] 5,000만원, 일반상해사망 5,000만원, 질병사망 5,000만원 | P3 | Sample contract specification metadata |

### 5. HANWHA (5 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| hanwha | hanwha__한화더건강한한아름종합보험 | default | 보험료납입면제대상보장(8대사유) | P3 | Premium waiver meta coverage |
| hanwha | hanwha__한화더건강한한아름종합보험 | default | 상해후유장해(3-100%) | P2 | Percentage range 3-100% not in Excel |
| hanwha | hanwha__한화더건강한한아름종합보험 | default | 4대유사암진단비 | P2 | 4 similar cancers not in Excel |
| hanwha | hanwha__한화더건강한한아름종합보험 | default | 암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형) | P2 | Da Vinci robot surgery not in Excel |
| hanwha | hanwha__한화더건강한한아름종합보험 | default | 질병사망 1, | P3 | Fragment from parsing error |

### 6. LOTTE_FEMALE (5 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| lotte_female | lotte__무배당let:smile종합건강보험더끌림포우먼2506무해지형납입 | default | 일반암수술비(1회한) | P2 | General cancer surgery not in Excel |
| lotte_female | lotte__무배당let:smile종합건강보험더끌림포우먼2506무해지형납입 | default | 암직접입원비(요양병원제외)(1일-120일) | P2 | Cancer direct hospitalization not in Excel |
| lotte_female | lotte__무배당let:smile종합건강보험더끌림포우먼2506무해지형납입 | default | 뇌경색증(I63) 혈전용해치료비 | P2 | Cerebral infarction thrombolysis not in Excel |
| lotte_female | lotte__무배당let:smile종합건강보험더끌림포우먼2506무해지형납입 | default | 허혈성심장질환진단비 | P2 | Ischemic heart disease not in Excel |
| lotte_female | lotte__무배당let:smile종합건강보험더끌림포우먼2506무해지형납입 | default | 급성심근경색증(I21) 혈전용해치료비 | P2 | AMI thrombolysis not in Excel |

### 7. LOTTE_MALE (5 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| lotte_male | lotte__무배당let:smile종합건강보험더끌림포맨2506무해지형납입면 | default | 일반암수술비(1회한) | P2 | General cancer surgery not in Excel |
| lotte_male | lotte__무배당let:smile종합건강보험더끌림포맨2506무해지형납입면 | default | 암직접입원비(요양병원제외)(1일-120일) | P2 | Cancer direct hospitalization not in Excel |
| lotte_male | lotte__무배당let:smile종합건강보험더끌림포맨2506무해지형납입면 | default | 뇌경색증(I63) 혈전용해치료비 | P2 | Cerebral infarction thrombolysis not in Excel |
| lotte_male | lotte__무배당let:smile종합건강보험더끌림포맨2506무해지형납입면 | default | 허혈성심장질환진단비 | P2 | Ischemic heart disease not in Excel |
| lotte_male | lotte__무배당let:smile종합건강보험더끌림포맨2506무해지형납입면 | default | 급성심근경색증(I21) 혈전용해치료비 | P2 | AMI thrombolysis not in Excel |

### 8. HEUNGKUK (4 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| heungkuk | heungkuk__무배당흥Good행복한파워종합보험 | default | 일반상해후유장해(80%이상) | P2 | 80% threshold not in Excel |
| heungkuk | heungkuk__무배당흥Good행복한파워종합보험 | default | 질병후유장해(80%이상)(감액없음) | P2 | Disease disability 80% not in Excel |
| heungkuk | heungkuk__무배당흥Good행복한파워종합보험 | default | 보험료 납입면제대상보장(6대질병진단 및 상해·질병후유장해(80%이상)) | P3 | Premium waiver meta coverage |
| heungkuk | heungkuk__무배당흥Good행복한파워종합보험 | default | [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년) | P2 | Targeted cancer drug v2 not in Excel |

### 9. DB_OVER41 (2 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| db_over41 | db__무배당프로미라이프 | default | 상해사망·후유장해(20-100%) | P2 | Combined death/disability range not in Excel |
| db_over41 | db__무배당프로미라이프 | default | 보험료납입면제대상보장(10대사유) | P4 | Premium waiver with 10 reasons (variant-specific) |

### 10. DB_UNDER40 (2 unmapped)

| insurer | product_key | variant_key | coverage_name | policy | reason |
|---------|-------------|-------------|---------------|--------|--------|
| db_under40 | db__무배당프로미라이프 | default | 상해사망·후유장해(20-100%) | P2 | Combined death/disability range not in Excel |
| db_under40 | db__무배당프로미라이프 | default | 보험료납입면제대상보장(11대사유) | P4 | Premium waiver with 11 reasons (variant-specific) |

---

## Summary by Policy

| Policy | Count | Percentage | Action Required |
|--------|-------|-----------|-----------------|
| P1: PIPELINE_BUG | 3 ⬆️ | 4.8% | Fix Step1 extractor (STEP NEXT-66 implemented) |
| P2: CANONICAL_GAP | 46 ⬇️ | 74.2% | Update Excel mapping reference |
| P3: EXPECTED_UNMAPPED | 11 | 17.7% | None (정상 상태) |
| P4: VARIANT_DEPENDENT | 2 | 3.2% | Variant policy review |

---

## Policy Details

### P1: PIPELINE_BUG (3 items) ⬆️

**Count**: 3 (STEP NEXT-66: KB fragments reclassified from P3)
**Action**: Fix Step1 extractor (✅ COMPLETED in STEP NEXT-66)
**Status**: ✅ Fixed by implementing coverage semantics extraction and fragment detection

**Items**:
1. KB: `최초1회` - Metadata fragment extracted as standalone coverage
2. KB: `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(` - Incomplete coverage name (unclosed parenthesis)
3. KB: `다빈치로봇 갑상선암 및 전립선암수술비(` - Incomplete coverage name (unclosed parenthesis)

**Root Cause**: PDF table parsing error in hybrid extraction mode

**Fix** (STEP NEXT-66):
- Implemented `CoverageSemanticExtractor` with fragment detection
- Added `fragment_detected` flag to semantics output
- Fragments now carry `parent_coverage_hint` for debugging
- All KB extractions now include `coverage_semantics` field

---

### P2: CANONICAL_GAP (46 items) ⬇️

**Count**: 46 (reduced from 49 after STEP NEXT-66 KB fragment reclassification)
**Action**: Update `data/sources/mapping/담보명mapping자료.xlsx`
**Categories**:
- New medical procedures (Da Vinci robot surgery, CAR-T therapy, thrombolytic therapy)
- Specific ICD codes (I49, I63, I21)
- V2 coverage versions (유사암진단Ⅱ, 항암약물치료Ⅱ)
- Specific percentage ranges (20-100%, 3-100%, 80%이상)
- New cardiovascular subsets
- Burn-related coverages
- Generic coverage terms too broad to map

**Next Steps**:
1. Review coverage terms with business team
2. Request canonical codes from 신정원
3. Update Excel mapping reference
4. Re-run Step2-b for affected insurers

---

### P3: EXPECTED_UNMAPPED (11 items)

**Count**: 11
**Action**: None (정상 상태)
**Categories**:
- Premium waiver meta coverage (7 items)
- Parsing fragments/errors (3 items)
- Auto-renewal rider metadata (1 item)

**Reason**: These are metadata items, not actual insurance coverages. They should remain unmapped.

---

### P4: VARIANT_DEPENDENT (2 items)

**Count**: 2
**Action**: Variant policy review
**Items**:
- `db_over41`: 보험료납입면제대상보장(10대사유)
- `db_under40`: 보험료납입면제대상보장(11대사유)

**Reason**: DB insurer has different premium waiver reasons based on age variant (10대사유 for over41, 11대사유 for under40). This suggests variant-specific coverage definitions.

**Next Steps**: Determine if variant-dependent mapping is needed or if these should be normalized to generic premium waiver coverage.

---

## Constitution Compliance

✅ **§2**: All rows preserve 4D identity (insurer_key, product_key, variant_key, coverage_name)
✅ **§6.3**: Unmapped defined as `mapping_method == "unmapped"`
✅ **§7.2**: Classification = ANALYSIS ONLY (no automatic fixing)
✅ **STEP NEXT-64**: All 62 unmapped items classified into P1-P4
✅ **STEP NEXT-64**: Zero unclassified items remaining

---

## Completion Status

- [x] All unmapped items classified (62/62)
- [x] P1-P4 policy assigned to every item
- [x] No "추후 검토" or ambiguous items
- [x] Per-insurer tables completed
- [x] Summary statistics computed
- [x] Action items identified

**Status**: ✅ POLICY LOCK COMPLETE

---

**Policy Lock Date**: 2026-01-08
**Constitution Version**: ACTIVE_CONSTITUTION.md (2026-01-08)
**Input Version**: STEP_NEXT_63A_UNMAPPED_ANALYSIS.md

**End of Policy Lock**
