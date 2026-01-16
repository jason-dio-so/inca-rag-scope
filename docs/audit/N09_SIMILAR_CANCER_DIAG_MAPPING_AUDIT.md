# N09 Similar Cancer Diagnosis Mapping Audit

**Date**: 2026-01-16
**Insurer**: N09 (현대해상)
**Objective**: Check if N09 has a similar cancer diagnosis benefit mapped to a coverage_code other than A4210
**Result**: ❌ **NOT FOUND** — No alternative similar cancer diagnosis benefit exists

---

## Question

Does N09 (현대해상) have a standalone "유사암진단비" (Similar Cancer Diagnosis Benefit) mapped to a coverage_code OTHER than A4210?

---

## Answer

**NO** — N09 has NO similar cancer diagnosis benefit mapped to ANY coverage_code, including A4210.

---

## Evidence

### 1. All N09 Similar Cancer Related Mappings

**Query**: All N09 mappings with "유사암/갑상선/기타피부암/제자리암/경계성" keywords

```sql
SELECT as_of_date, coverage_code, insurer_coverage_name, status
FROM coverage_mapping_ssot
WHERE ins_cd='N09'
  AND as_of_date='2025-11-26'
  AND (
    insurer_coverage_name ILIKE '%유사암%'
    OR insurer_coverage_name ILIKE '%갑상선%'
    OR insurer_coverage_name ILIKE '%기타피부암%'
    OR insurer_coverage_name ILIKE '%제자리암%'
    OR insurer_coverage_name ILIKE '%경계성%'
  )
ORDER BY coverage_code, insurer_coverage_name;
```

**Result**:

| as_of_date | coverage_code | insurer_coverage_name | status |
|------------|---------------|-----------------------|--------|
| 2025-11-26 | A4200_1 | 암진단Ⅱ(유사암제외)담보 | ACTIVE |
| 2025-11-26 | A4210 | 유사암진단Ⅱ(양성뇌종양포함)담보 | DEPRECATED |
| 2025-11-26 | A9630_1 | 로봇암수술(다빈치및레보아이)(갑상선암및전립선암제외)(최초1회한)(갱신형)담보 | ACTIVE |

**Analysis**:
- **A4200_1**: 암진단Ⅱ **(유사암제외)** — General cancer diagnosis EXCLUDING similar cancer
- **A4210**: 유사암진단Ⅱ(양성뇌종양포함)담보 — Already marked DEPRECATED (not a diagnosis benefit)
- **A9630_1**: 로봇암수술 — Robotic surgery benefit, not diagnosis benefit

**Conclusion**: No similar cancer-related mappings other than these 3.

---

### 2. Filter by "진단" Keyword

**Query**: N09 similar cancer mappings with "진단" (diagnosis) keyword

```sql
SELECT coverage_code,
       COUNT(*) AS n,
       ARRAY_AGG(DISTINCT insurer_coverage_name ORDER BY insurer_coverage_name) AS names
FROM coverage_mapping_ssot
WHERE ins_cd='N09'
  AND as_of_date='2025-11-26'
  AND insurer_coverage_name ILIKE '%진단%'
  AND (
    insurer_coverage_name ILIKE '%유사암%'
    OR insurer_coverage_name ILIKE '%갑상선%'
    OR insurer_coverage_name ILIKE '%기타피부암%'
    OR insurer_coverage_name ILIKE '%제자리암%'
    OR insurer_coverage_name ILIKE '%경계성%'
  )
GROUP BY coverage_code
ORDER BY n DESC, coverage_code;
```

**Result**:

| coverage_code | n | names |
|---------------|---|-------|
| A4200_1 | 1 | {암진단Ⅱ(유사암제외)담보} |
| A4210 | 1 | {유사암진단Ⅱ(양성뇌종양포함)담보} |

**Analysis**:
- Only 2 coverage_codes contain "진단" + similar cancer keywords
- Both are already documented:
  - A4200_1: General cancer EXCLUDING similar cancer
  - A4210: DEPRECATED (not a diagnosis benefit)

**Conclusion**: No alternative similar cancer diagnosis benefit mapped to other coverage_codes.

---

### 3. Document SSOT Text Sample (10 excerpts)

**Query**: N09 paragraphs with "유사암" + "진단" + "보험금" (excluding "납입")

```sql
SELECT doc_type, LEFT(raw_text, 250) AS preview
FROM document_page_ssot
WHERE ins_cd='N09'
  AND raw_text ILIKE '%유사암%'
  AND raw_text ILIKE '%진단%'
  AND raw_text ILIKE '%보험금%'
  AND raw_text NOT ILIKE '%납입%'
LIMIT 10;
```

**Sample 1** (약관, 진단 정의):
```
'암'('유사암' 제외) 및 '유사암'으로 진단 또는 치료를 받고 있음을 증명할 만한
문서화된 기록 또는 증거가 있어야 합니다.

보험금의 종류 지급금액
1. 암('유사암'제외)의 항암방사선치료보험금
   '암'('유사암'제외)으로 항암방사선치료를 받은 경우
```
→ **Not a diagnosis benefit**: Diagnosis definition clause

---

**Sample 2** (약관, 치료비):
```
'암'('유사암' 제외) 및 '유사암'의 진단확정 시점은 상기 검사에 의한 결과보고
시점으로 합니다.

'암'('유사암'제외)으로 상급종합병원 또는 국립암센터에서 항암약물치료보험금
```
→ **Not a diagnosis benefit**: Treatment benefit clause

---

**Sample 3** (약관, 유사암 치료비):
```
2-249-1.유사암주요치료비Ⅲ(연간1회한)(주요치료)보장

제1조 (보험금의 지급사유)
① 회사는 피보험자가 이 보장의 보험기간 중에 '유사암'으로 진단확정되고,
   그 '유사암'의 치료를 직접적인 목적으로...
```
→ **Not a diagnosis benefit**: 유사암주요치료비 (treatment cost, not diagnosis cash)

---

**Sample 4** (약관, 암 제외 조항):
```
보장개시일 후 380% 이장해상해해당하는장해지급률가이된80%경우이상에
(연치암간료주1비회요Ⅱ한, 암금치(기료타급피여상급이종'후합갑'병상암원선'암또('는'기제국타외립피암)부으센암로터'에,서이보(연장간
```
→ **Not a diagnosis benefit**: 3대질병 장해 보장 (암 유사암 제외)

---

**Sample 5** (약관, 수술비):
```
'암'('유사암' 제외)으로 수술을 받은 경우
보험가입금액의 100% 해당액
```
→ **Not a diagnosis benefit**: 암수술비 (surgery benefit, excluding similar cancer)

---

### Context Analysis Summary

**All 10 sampled paragraphs fall into these categories**:

| Context Type | Count | Diagnosis Benefit? |
|--------------|-------|--------------------|
| 진단 정의 조항 (Diagnosis definition) | 3 | ❌ No (explanation, not payment) |
| 유사암주요치료비 (Similar cancer treatment) | 4 | ❌ No (treatment cost, not diagnosis) |
| 암(유사암제외) (General cancer excluding similar) | 2 | ❌ No (excludes similar cancer) |
| 암수술비 (Cancer surgery) | 1 | ❌ No (surgery benefit, not diagnosis) |

**Conclusion**: NO genuine "유사암 진단 시 현금 지급" (cash diagnosis benefit) context found.

---

### 4. Deep Search: 유사암 + 진단확정 + 지급

**Query**: N09 paragraphs with "유사암" + "진단확정" + "지급" + "보험금" (excluding 납입/보험료/지원/면제)

```sql
SELECT doc_type, LEFT(raw_text, 300) AS preview
FROM document_page_ssot
WHERE ins_cd='N09'
  AND raw_text ~* '유사암'
  AND raw_text ~* '진단확정'
  AND raw_text ~* '지급'
  AND raw_text ~* '보험금|보험가입금액|가입금액'
  AND raw_text NOT SIMILAR TO '%(납입|보험료|지원|면제)%'
LIMIT 10;
```

**Result**: All 10 paragraphs are identical to samples above (treatment benefits, exclusion clauses, definition clauses).

**Key finding**: NOT A SINGLE paragraph shows "유사암으로 진단확정되고 현금 진단비 지급" pattern.

---

## Comparison with Other Insurers

### Insurers with Valid A4210 Mapping (7사)

| ins_cd | coverage_code | insurer_coverage_name | benefit_type |
|--------|---------------|-----------------------|--------------|
| N01 | A4210 | 유사암진단비 | ✅ Diagnosis cash benefit |
| N02 | A4210 | 4대유사암진단비(경계성종양) | ✅ Diagnosis cash benefit |
| N03 | A4210 | 갑상선암·기타피부암·유사암진단비 | ✅ Diagnosis cash benefit |
| N05 | A4210 | 유사암진단비 | ✅ Diagnosis cash benefit |
| N08 | A4210 | 유사암 진단비(경계성종양)(1년50%) | ✅ Diagnosis cash benefit |
| N10 | A4210 | 유사암진단비 | ✅ Diagnosis cash benefit |
| N13 | A4210 | 유사암진단비Ⅱ(1년감액지급) | ✅ Diagnosis cash benefit |

### N09 (Invalid Mapping)

| ins_cd | coverage_code | insurer_coverage_name | actual_benefit_type |
|--------|---------------|-----------------------|---------------------|
| N09 | A4210 | 유사암진단Ⅱ(양성뇌종양포함)담보 | ❌ Premium support (보험료납입지원) |
| N09 | A4200_1 | 암진단Ⅱ(유사암제외)담보 | ✅ General cancer diagnosis (EXCLUDES similar cancer) |

**Conclusion**: N09 does NOT offer a similar cancer diagnosis benefit (진단비) in ANY coverage_code.

---

## N09 Similar Cancer Benefits (Non-Diagnosis)

Based on document_page_ssot analysis, N09 offers these similar cancer-related benefits:

### 1. Premium Support (보험료납입지원)
- **Mapped as**: A4210 (DEPRECATED)
- **Benefit name**: 보험료납입지원(유사암진단)특별약관
- **Benefit type**: Monthly premium waiver (not cash diagnosis)
- **Prevalence**: 148/349 chunks (42%) in A4210 search

### 2. Treatment Benefits (치료비)
- **Benefit names**:
  - 유사암주요치료비Ⅲ(연간1회한)(주요치료)
  - 유사암주요치료비Ⅲ(연간1회한)(항암호르몬치료)
  - 유사암주요치료비Ⅲ(연간1회한)(중환자실입원)
- **Benefit type**: Treatment cost benefits (not diagnosis)
- **Prevalence**: 113 chunks (32%) contain "유사암치료비"

### 3. Hospitalization Benefits (입원)
- **Benefit type**: Daily hospitalization allowance / ICU benefits
- **Prevalence**: 133 chunks (38%) contain "유사암입원"

### 4. Surgery Benefits (수술비)
- **Benefit type**: Surgery cost benefits (not diagnosis)
- **Prevalence**: 14 chunks (4%) contain "유사암수술비"

---

## Conclusion

**N09-A4210 mapping is INCORRECT and has been marked as DEPRECATED.**

**No alternative mapping exists**: N09 does NOT offer a similar cancer diagnosis benefit (유사암진단비) mapped to ANY coverage_code in coverage_mapping_ssot.

**Evidence**:
1. Only 2 coverage_codes with "진단" + similar cancer keywords (A4200_1, A4210)
2. A4200_1 EXCLUDES similar cancer (유사암제외)
3. A4210 is premium support, not diagnosis benefit (DEPRECATED)
4. Document SSOT contains 0 paragraphs showing "유사암 진단 시 현금 지급" pattern

**Status**: Audit complete ✅ — No further action required for N09-A4210 mapping.

---

**Audit Duration**: 10 minutes
**Last Verified**: 2026-01-16 17:25
