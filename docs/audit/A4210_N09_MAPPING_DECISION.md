# A4210 N09 Mapping Decision

**Date**: 2026-01-16
**Coverage**: A4210 (유사암진단비)
**Insurer**: N09 (현대해상)
**Decision**: ❌ **Mapping INACTIVE** (NOT delete, status change only)

---

## Question

Does N09 (현대해상) have a standalone "유사암진단비" (Similar Cancer Diagnosis Benefit) that qualifies for A4210 mapping?

---

## Answer

**NO** — N09 does NOT have a similar cancer diagnosis benefit (진단비).

---

## Evidence Summary

### Document Search Results

**Query**: All N09 paragraphs containing "유사암" (349 total)

| Benefit Type | Count | % | Qualification for A4210 |
|--------------|-------|---|-------------------------|
| 진단비 (Diagnosis) | 4 | 1% | ❌ All in "(유사암제외)" exclusion context |
| 납입지원 (Premium Support) | 148 | 42% | ❌ Not cash diagnosis benefit |
| 입원 (Hospitalization) | 133 | 38% | ❌ Not diagnosis benefit |
| 치료비 (Treatment) | 113 | 32% | ❌ Not diagnosis benefit |
| 수술비 (Surgery) | 14 | 4% | ❌ Not diagnosis benefit |

---

## Detailed Findings

### 1. Premium Support (NOT Diagnosis Benefit)

N09's most prominent "유사암" benefit is **보험료납입지원(유사암진단)특별약관** (Premium Waiver for Similar Cancer Diagnosis):

**Benefit Type**: Monthly premium support (NOT lump-sum cash)

**Evidence**:
```
회사는 피보험자가 보험기간 중에 '유사암'으로 진단확정된 경우에는 최초 1회에 한하
여 아래의 금액을 보험수익자에게 보험금으로 지급합니다.
단, 보험료 납입지원금은 제2항 및 제3항에서 정한 보험료 납입지원기간동안 매년 보험
료 납입지원금 지급사유 발생해당일(지급사유 발생일 포함)에 지급합니다.

보험금의 종류: 보험료 납입지원금
지급금액: 이 특약의 가입금액 × 보험료 납입지원 잔여기간(월)

보험료납입지원(유사암진단)특별약관
```

**Analysis**: This pays future premiums, not a lump-sum diagnosis cash benefit.

---

### 2. "유사암진단비" Mentions (All Exclusions)

Only 4 paragraphs mention "유사암진단비" or "유사암...진단비", and ALL are in exclusion contexts:

**Excerpt 1**: 남성통합암(전이포함)진단(유사암제외)
```
남성통합암(전이포함)진단(유사암제외) 보장 특별약관은 아래의 세부보장(10개)으로
구성되어 있습니다.

• 남성통합암(전이포함)진단비(두경부암)
• 남성통합암(전이포함)진단비(위암및식도암)
• 남성통합암(전이포함)진단비(소장·대장·항문암 및 기타암)
```
→ Men's integrated cancer benefit **EXCLUDING similar cancer**

**Excerpt 2**: 여성통합암(전이포함)진단(유사암제외)
```
여성통합암(전이포함)진단(유사암제외)보장특별약관/
여성통합암(전이포함)진단(유사암제외)[맞춤고지Ⅱ]보장
```
→ Women's integrated cancer benefit **EXCLUDING similar cancer**

**Conclusion**: These are general cancer benefits that explicitly EXCLUDE similar cancer. Not a similar cancer diagnosis benefit.

---

### 3. Other Similar Cancer Benefits (NOT A4210)

N09 offers multiple similar cancer-related benefits, but NONE qualify as A4210 (진단비):

**Surgery Benefits** (14 mentions):
- "유사암수술비" — Pays for surgery, not diagnosis

**Hospitalization Benefits** (133 mentions):
- "유사암입원일당" — Daily hospitalization allowance
- "유사암중환자실입원" — ICU hospitalization benefit

**Treatment Benefits** (113 mentions):
- "유사암주요치료비" — Major treatment cost benefit
- "유사암항암방사선치료" — Radiation therapy benefit

**Analysis**: All are treatment-stage benefits, not upfront diagnosis benefits.

---

## Comparison with Other Insurers

### Insurers with Valid A4210 Mapping

| ins_cd | insurer_coverage_name | Evidence |
|--------|-----------------------|----------|
| N01 | 유사암진단비 | ✅ Standalone diagnosis benefit |
| N02 | 4대유사암진단비(경계성종양) | ✅ Diagnosis benefit for 4 similar cancers |
| N03 | 갑상선암·기타피부암·유사암진단비 | ✅ Diagnosis benefit (combined) |
| N05 | 유사암진단비 | ✅ Standalone diagnosis benefit |
| N08 | 유사암 진단비(경계성종양)(1년50%) | ✅ Diagnosis benefit with reduction |
| N10 | 유사암진단비 | ✅ Standalone diagnosis benefit |
| N13 | 유사암진단비Ⅱ(1년감액지급) | ✅ Diagnosis benefit with reduction |

### N09 (Invalid Mapping)

| ins_cd | mapped_coverage_name | Actual Benefit Type |
|--------|----------------------|---------------------|
| N09 | 유사암진단Ⅱ(양성뇌종양포함)담보 | ❌ Premium Support (보험료납입지원) |

**Key difference**: N09's "유사암진단Ⅱ" is NOT a diagnosis benefit (진단비), but a premium waiver benefit (납입지원).

---

## Recommended Action

### SQL to Mark Mapping as INACTIVE

```sql
UPDATE coverage_mapping_ssot
SET status = 'DEPRECATED',
    updated_at = CURRENT_TIMESTAMP
WHERE ins_cd = 'N09'
  AND coverage_code = 'A4210'
  AND as_of_date = '2025-11-26';
```

**Reason**: N09 does not offer a similar cancer diagnosis benefit (A4210). The mapped coverage name "유사암진단Ⅱ(양성뇌종양포함)담보" is a premium support benefit, not a diagnosis benefit.

**Note**: Do NOT delete the row. Mark as DEPRECATED to preserve audit trail.

---

## Verification Query

```sql
SELECT ins_cd, coverage_code, insurer_coverage_name, status
FROM coverage_mapping_ssot
WHERE ins_cd = 'N09' AND coverage_code = 'A4210' AND as_of_date = '2025-11-26';
```

**Expected After Update**:

| ins_cd | coverage_code | insurer_coverage_name | status |
|--------|---------------|-----------------------|--------|
| N09 | A4210 | 유사암진단Ⅱ(양성뇌종양포함)담보 | DEPRECATED |

---

## Conclusion

**N09-A4210 mapping is INCORRECT and should be marked as DEPRECATED.**

Proceed with A4210 7-insurer baseline (N01, N02, N03, N05, N08, N10, N13).

---

**STATUS**: Decision documented ✅
**Next**: Update coverage_mapping_ssot status
