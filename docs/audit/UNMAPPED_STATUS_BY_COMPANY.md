# Company-by-Company Unmapped Status Report

**Generated**: STEP NEXT-59 (SSOT Separated: Step2-a dropped vs Step2-b unmapped)

## Overview

| Company | Total | Mapped | Unmapped | Rate | Dropped (Step2-a) |
|---------|-------|--------|----------|------|-------------------|
| SAMSUNG | 31 | 27 | 4 | 87.1% | 0 |
| db_over41 | 30 | 29 | 1 | 96.7% | 0 |
| db_under40 | 30 | 29 | 1 | 96.7% | 0 |
| hanwha | 32 | 28 | 4 | 87.5% | 0 |
| heungkuk | 35 | 32 | 3 | 91.4% | 0 |
| hyundai | 36 | 25 | 11 | 69.4% | 10 |
| kb | 42 | 30 | 12 | 71.4% | 20 |
| lotte_female | 30 | 25 | 5 | 83.3% | 0 |
| lotte_male | 30 | 25 | 5 | 83.3% | 0 |
| meritz | 37 | 28 | 9 | 75.7% | 0 |

**SSOT Definition**:
- **Total/Mapped/Unmapped/Rate**: From Step2-b `*_step2_mapping_report.jsonl` (canonical mapping results)
- **Dropped**: From Step2-a `*_step2_dropped.jsonl` (sanitize phase noise/fragments)

---

## SAMSUNG

**Total Coverage Items**: 31
**Mapped**: 27 (87.1%)
**Unmapped**: 4
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 4
**Unique Items**: 4

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `간병/사망`
- `골절 진단비(치아파절(깨짐, 부러짐) 제외)`
- `수술`
- `장해/장애`

---

## DB_OVER41

**Total Coverage Items**: 30
**Mapped**: 29 (96.7%)
**Unmapped**: 1
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 1
**Unique Items**: 1

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `1. 상해사망·후유장해(20-100%)`

---

## DB_UNDER40

**Total Coverage Items**: 30
**Mapped**: 29 (96.7%)
**Unmapped**: 1
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 1
**Unique Items**: 1

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `1. 상해사망·후유장해(20-100%)`

---

## HANWHA

**Total Coverage Items**: 32
**Mapped**: 28 (87.5%)
**Unmapped**: 4
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 4
**Unique Items**: 4

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `10. 질병사망 1,`
- `4대유사암진단비`
- `상해후유장해(3-100%)`
- `암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)`

---

## HEUNGKUK

**Total Coverage Items**: 35
**Mapped**: 32 (91.4%)
**Unmapped**: 3
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 3
**Unique Items**: 3

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `[갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년)`
- `일반상해후유장해(80%이상)`
- `질병후유장해(80%이상)(감액없음)`

---

## HYUNDAI

**Total Coverage Items**: 36
**Mapped**: 25 (69.4%)
**Unmapped**: 11
**Dropped (Step2-a)**: 10

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 11
**Unique Items**: 11

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `10. 유사암진단Ⅱ담보`
- `17. 심혈관질환(특정Ⅰ,I49제외)진단담보`
- `18. 심혈관질환(I49)진단담보`
- `19. 심혈관질환(주요심장염증)진단담보`
- `21. 심혈관질환(특정2대)진단담보`
- `22. 심혈관질환(대동맥판막협착증)진단담보`
- `23. 심혈관질환(심근병증)진단담보`
- `24. 항암약물치료Ⅱ담보`
- `28. 질병입원일당(1-180일)담보`
- `37. 혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보`
- `로봇암수술(다빈치및레보아이
)(갑상선암및전립선암)(최초
1회한)(갱신형)담보`

### Group A: Step2-a Dropped (Fragments/Noise)

**Count (SSOT lines)**: 10
**Unique Items**: 10

**Description**: Items removed by Step2-a sanitization (deterministic pattern matching).

**Drop Reasons**:
- `FRAGMENTED_HANGUL`: 2
- `DUPLICATE_VARIANT`: 2
- `BROKEN_RENEWAL_담보`: 1
- `BROKEN_SUFFIX`: 1
- `ADMIN_FIELD_갱신차수`: 1
- `COLUMN_HEADER_담보명`: 1
- `PARENTHESES_ONLY`: 1
- `STANDALONE_NUMBER`: 1

**All Unique Items**:
- `(갱신형)담보`
- `(기준: 100세만기 20년납, 40세, 상해1급)`
- `91.5`
- `갱신차수`
- `남 자`
- `담보명`
- `보 험 가 격 지 수 (%)`
- `신형)담보`
- `카티(CAR-T)항암약물허가치료(연간1회한)(갱신형)담보`
- `표적항암약물허가치료(갱신형)담보`

---

## KB

**Total Coverage Items**: 42
**Mapped**: 30 (71.4%)
**Unmapped**: 12
**Dropped (Step2-a)**: 20

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 12
**Unique Items**: 12

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `105. 부정맥질환(Ⅰ49)진단비`
- `2. 일반상해후유장해(20~100%)(기본)`
- `206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)`
- `207. 다빈치로봇 갑상선암 및 전립선암수술비(최초1회한)(갱신형)`
- `278. 표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ(갱신형)`
- `279. 표적항암약물허가치료비(림프종·백혈병 관련암)(최초1회한)Ⅱ(갱신형)`
- `280  표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)`
- `283. 특정항암호르몬약물허가치료비(최초1회한)Ⅱ(갱신형)`
- `291. 카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형)`
- `다빈치로봇 갑상선암 및 전립선암수술비(`
- `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(`
- `최초1회`

### Group A: Step2-a Dropped (Fragments/Noise)

**Count (SSOT lines)**: 20
**Unique Items**: 20

**Description**: Items removed by Step2-a sanitization (deterministic pattern matching).

**Drop Reasons**:
- `DUPLICATE_VARIANT`: 20

**All Unique Items**:
- `골절진단비Ⅱ(치아파절제외)`
- `뇌졸중진단비`
- `뇌출혈진단비`
- `뇌혈관질환수술비`
- `뇌혈관질환진단비`
- `부정맥질환(Ⅰ49)진단비`
- `상해수술비`
- `심근병증진단비`
- `심장질환(특정Ⅰ) 진단비`
- `심장질환(특정Ⅱ) 진단비`
- `심장판막협착증(대동맥판막)진단비`
- `암수술비(유사암제외)`
- `유사암수술비`
- `유사암진단비`
- `재진단암진단비`
- `질병수술비`
- `항암방사선치료비`
- `허혈성심장질환수술비`
- `허혈성심장질환진단비`
- `화상진단비`

---

## LOTTE_FEMALE

**Total Coverage Items**: 30
**Mapped**: 25 (83.3%)
**Unmapped**: 5
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 5
**Unique Items**: 5

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `급성심근경색증(I21) 혈전용해치료비`
- `뇌경색증(I63) 혈전용해치료비`
- `암직접입원비(요양병원제외)(1일-120일)`
- `일반암수술비(1회한)`
- `허혈성심장질환진단비`

---

## LOTTE_MALE

**Total Coverage Items**: 30
**Mapped**: 25 (83.3%)
**Unmapped**: 5
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 5
**Unique Items**: 5

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `급성심근경색증(I21) 혈전용해치료비`
- `뇌경색증(I63) 혈전용해치료비`
- `암직접입원비(요양병원제외)(1일-120일)`
- `일반암수술비(1회한)`
- `허혈성심장질환진단비`

---

## MERITZ

**Total Coverage Items**: 37
**Mapped**: 28 (75.7%)
**Unmapped**: 9
**Dropped (Step2-a)**: 0

### Group B: Step2-b Unmapped (Legitimate Unmapped)

**Count (SSOT lines)**: 9
**Unique Items**: 9

**Description**: Items that passed Step2-a sanitization but failed canonical mapping in Step2-b.

**All Unique Items**:
- `대표계약 기준 : 남자40세,20년납,100세만기,월납,일반상해80%이상후유장해[기본계약] 5,000만원, 일반상해사망 5,000만원, 질병사망 5,000만원`
- `보험료 비교(예시)`
- `신화상치료비(중증화상및부식진단비)`
- `신화상치료비(화상수술비)`
- `신화상치료비(화상진단비)`
- `일반상해80%이상후유장해[기본계약]`
- `일반상해사망`
- `일반상해중환자실입원일당(1일이상)`
- `자동갱신특약`

---

## Summary Statistics

- **Total Coverage Items (Step2-b)**: 333
- **Mapped**: 278 (83.5%)
- **Unmapped (Group B)**: 55
- **Dropped (Group A, Step2-a)**: 30

## Constitutional Rules (STEP NEXT-59-FIX)

1. ✅ **SSOT Separation**: Group A (Step2-a dropped) ≠ Group B (Step2-b unmapped)
2. ✅ **SSOT Line-Based Counts**: Count = raw line count (NOT unique deduplicated)
3. ✅ **SSOT Gates Enforced**: summary['unmapped'] == group_b['raw_count'], dropped lines == group_a['raw_count']
4. ✅ **Unique Items for Display**: Show unique_count separately, but count = SSOT lines
5. ✅ **No Fragment Logic on Step2-b**: Step2-b unmapped items are NOT re-classified as fragments
6. ✅ **Field Priority**: `coverage_name_normalized` > `coverage_name_raw` > `coverage_name`
7. ✅ **Overview = Step2-b SSOT**: Total/Mapped/Unmapped from mapping_report.jsonl only
8. ❌ **No LLM**: Deterministic only
9. ❌ **No Logic Change**: Step2-a/Step2-b unchanged

## Action Items

1. **Group A (Dropped)**: Already handled by Step2-a (no action needed)
2. **Group B (Unmapped)**: Require manual review and Excel mapping additions
   - Add missing canonical names to `data/sources/mapping/담보명mapping자료.xlsx`
   - Re-run Step2-b canonical mapping
