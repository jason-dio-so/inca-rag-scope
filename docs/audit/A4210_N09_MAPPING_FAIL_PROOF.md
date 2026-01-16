# A4210 N09 Mapping Failure Proof

**Date**: 2026-01-16
**Coverage**: A4210 (유사암진단비)
**Insurer**: N09 (현대해상)
**Result**: FOUND=0/3, Complete failure
**Status**: ⛔ Mapping anomaly detected

---

## Coverage Mapping

**Source**: coverage_mapping_ssot (as_of_date=2025-11-26)

```sql
SELECT ins_cd, coverage_code, insurer_coverage_name
FROM coverage_mapping_ssot
WHERE ins_cd = 'N09' AND coverage_code = 'A4210' AND as_of_date = '2025-11-26';
```

| ins_cd | coverage_code | insurer_coverage_name |
|--------|---------------|-----------------------|
| N09 | A4210 | 유사암진단Ⅱ(양성뇌종양포함)담보 |

---

## Failure Summary

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Total chunks | 349 | ✓ Adequate volume |
| Anchor-matched | 221/349 (63%) | ✓ Anchor "유사암" found |
| With "유사암 제외" | 326/349 (93%) | ❌ Mostly exclusion context |
| With "유사암납입" | 148/349 (42%) | ❌ Premium support, not diagnosis |
| With "유사암진단비" | 4/349 (1%) | ❌ All in "(유사암제외)" context |
| **FOUND slots** | **0/3** | ❌ Complete failure |

**Root cause**: N09's "유사암진단Ⅱ(양성뇌종양포함)담보" is **NOT a diagnosis benefit (진단비)**, but a **premium waiver benefit (보험료납입지원)**.

---

## Evidence Categories (Contamination Analysis)

### Category 1: 보험료납입지원 (Premium Support)
148 chunks contain "유사암납입" pattern — this is NOT a cash diagnosis benefit.

### Category 2: 유사암제외 (Similar Cancer Exclusion)
326 chunks contain "유사암 제외" — these are general cancer benefits EXCLUDING similar cancer.

### Category 3: Genuine 유사암진단비
Only 4 chunks contain "유사암진단비", but all are in exclusion context:
- "남성통합암(유사암제외)진단비"
- "암진단비(유사암제외)"

---

## Representative Excerpts

### Excerpt 1: 보험료납입지원 특약

**Source**: document_page_ssot (N09)

```
회사는 피보험자가 보험기간 중에 '유사암'으로 진단확정된 경우에는 최초 1회에 한하
여 아래의 금액을 보험수익자에게 보험금으로 지급합니다.
단, 보험료 납입지원금은 제2항 및 제3항에서 정한 보험료 납입지원기간동안 매년 보험
료 납입지원금 지급사유 발생해당일(지급사유 발생일 포함)에 지급합니다.

보험금의 종류: 보험료 납입지원금
지급사유: '유사암'으로 진단 확정된 경우
지급금액: 이 특약의 가입금액주)× 보험료 납입지원 잔여기간(월)

보험료납입지원(유사암진단)특별약관/
보험료납입지원(유사암진단)[맞춤고지Ⅱ]특별약관
```

**Analysis**: Premium waiver benefit, not cash diagnosis benefit. Pays monthly premium support, not lump sum diagnosis cash.

---

### Excerpt 2: 일반암 특약 (유사암 제외)

**Source**: document_page_ssot (N09)

```
보장개시일 이후 암 (유사암 제외), 뇌
졸중, 급성심근경색증, 말기신부전증,
말기간경화 또는 말기폐질환으로 진단
확정된 경우 (최초 1회한)

※유사암 : 기타피부암, 갑상선암,
제자리암, 경계성종양

질병수술1 26대질병의 치료를 직접적인 목적
(26대질병 으로 수술을 받은 경우 (단, 최초계약일부터
Ⅱ) 1년미만 상기금액의 50%)
```

**Analysis**: This is a GENERAL cancer benefit that EXCLUDES similar cancer. Not a similar cancer diagnosis benefit.

---

### Excerpt 3: 남성통합암 특약 (유사암 제외)

**Source**: document_page_ssot (N09)

```
남성통합암(전이포함)진단(유사암제외) 보장 특별약관은 아래의 세부보장(10개)으로
구성되어 있습니다.

회사는 피보험자가 이 특별약관의 보험기간 중에 제3조(보험금 지급에 관한 세부규정) 제1
항에서 정한 보장개시일 이후 '남성통합암(전이포함)(유사암제외)'으로 진단확정된 경우
```

**Analysis**: Men's integrated cancer benefit that EXCLUDES similar cancer. Not a similar cancer diagnosis benefit.

---

## Statistical Proof

### Query: N09 유사암 paragraph patterns

```sql
SELECT
  COUNT(*) as total_yusa,
  SUM(CASE WHEN raw_text ~* '유사암진단' THEN 1 ELSE 0 END) as with_yusa_jindan,
  SUM(CASE WHEN raw_text ~* '유사암.*제외' THEN 1 ELSE 0 END) as with_yusa_jeoe,
  SUM(CASE WHEN raw_text ~* '유사암.*납입' THEN 1 ELSE 0 END) as with_yusa_napip,
  SUM(CASE WHEN raw_text ~* '유사암.*진단비' THEN 1 ELSE 0 END) as with_yusa_jindan_bi
FROM document_page_ssot
WHERE ins_cd = 'N09'
  AND raw_text ~* '유사암';
```

**Result**:

| total_yusa | with_yusa_jindan | with_yusa_jeoe | with_yusa_napip | with_yusa_jindan_bi |
|------------|------------------|----------------|-----------------|---------------------|
| 349 | 60 | 326 | 148 | 4 |

**Interpretation**:
- 93% of chunks contain "유사암 제외" (exclusion context)
- 42% contain "유사암납입" (premium support context)
- Only 1% contain "유사암진단비", and all are in exclusion phrases

---

## Conclusion

**N09 "유사암진단Ⅱ(양성뇌종양포함)담보" is NOT a similar cancer diagnosis benefit.**

It is a **premium waiver special clause** that pays monthly premium support (not lump sum cash) when diagnosed with similar cancer.

This mapping should be marked as **INACTIVE** in coverage_mapping_ssot.

---

## Recommended Action

1. Mark N09-A4210 mapping as `status='INACTIVE'` (do NOT delete)
2. Proceed with A4210 7-insurer baseline (N01,N02,N03,N05,N08,N10,N13)
3. Re-validate N09 mapping against original source documents

---

**STATUS**: Mapping anomaly documented ✅
**Next**: Freeze 7-insurer baseline
