# Q8 Fact Snapshot - 2026-01-13

**Status**: FROZEN
**Date**: 2026-01-13
**SSOT**: data/compare_v1/q8_surgery_repeat_policy_v1.jsonl
**Scope**: 질병수술비(1~5종) repeat payment policy ONLY
**Out of Scope**: 대장용종 specific attribution, premium ranking, specific surgery recommendations

---

## Freeze Evidence (SHA256)

```
compare_rows_v1.jsonl:
f3935d6ffdb790da9fe1aa88bd0017244b9117b9ef84aadc81a6b1cb6d3c4914

compare_tables_v1.jsonl:
4a4a3f6e2060b8ad72f3f22773cdd3116bf5ea592b46af11b494f781cef7f70a

q8_surgery_repeat_policy_v1.jsonl:
945dc2f27121d5371f8dc9c8e881fb734ce7009b83d138c897a3d64a70440000
```

**Verification**: Q8 implementation does NOT modify compare_rows or compare_tables. Above hashes prove Core Model integrity.

---

## API Endpoint Results

**Endpoint**: `GET /q8`
**Total Items**: 10 insurers

### Sample Results (hanwha, heungkuk)

#### hanwha (ANNUAL_LIMIT)
```json
{
  "insurer_key": "hanwha",
  "repeat_payment_policy": "ANNUAL_LIMIT",
  "display_text": "연간 1회한",
  "evidence_count": 1,
  "evidence": {
    "doc_type": "약관",
    "page": 340,
    "excerpt": "분\" 당 \"관혈수술\" 또는 \"비관혈수술\"별 각각 연간 1회를 초과하여 지급하지 않습니다."
  }
}
```

#### heungkuk (PER_EVENT)
```json
{
  "insurer_key": "heungkuk",
  "repeat_payment_policy": "PER_EVENT",
  "display_text": "매회 지급",
  "evidence_count": 2,
  "evidence": {
    "doc_type": "약관",
    "page": 363,
    "excerpt": "때에는 수술1회당 아래의 금액을 지급"
  }
}
```

---

## Policy Distribution

- **PER_EVENT**: 5 insurers (heungkuk, kb, lotte_female, lotte_male, meritz)
- **ANNUAL_LIMIT**: 3 insurers (hanwha, db_over41, db_under40)
- **UNKNOWN**: 2 insurers (hyundai, samsung)

---

## Evidence Summary by Insurer

### hanwha

**Policy**: `ANNUAL_LIMIT`
**Display**: 연간 1회한
**Evidence Count**: 1

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 340
   **Excerpt**: `분" 당 "관혈수술" 또는 "비관혈수술"별 각각 연간 1회를 초과하여 지급하지 않습니다.  제1항 및 제3항의 "연간"이라 함은 이 특별약관의 계약일(갱신계약의 경우 갱신계약일)부...`

---

### heungkuk

**Policy**: `PER_EVENT`
**Display**: 매회 지급
**Evidence Count**: 2

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 363
   **Excerpt**: `때에는 수술1회당 아래의 금액을 지급    <비갱신형 및 갱신형(최초계약)>    ...`

2. **Doc**: 약관, **Page**: 512
   **Excerpt**: `을 받은 때에는 수술1회당 아래의 금액을 지급    <비갱신형 및 갱신형(최초계약)> ...`

---

### hyundai

**Policy**: `UNKNOWN`
**Display**: 확인 불가 (근거 없음)
**Evidence Count**: 0

**UNKNOWN Justification**:
- No explicit repeat payment policy found in 질병수술비(1~5종) coverage documents
- Evidence-first approach: Cannot infer without documented evidence

---

### kb

**Policy**: `PER_EVENT`
**Display**: 매회 지급
**Evidence Count**: 20

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 5
   **Excerpt**: `55. 질병1~5종수술비(매회지급) ·························································251 55-1. 질병1~5종수술비(매회...`

2. **Doc**: 약관, **Page**: 5
   **Excerpt**: `55-1. 질병1~5종수술비(매회지급)【갱신계약】·······························251 56. 위·십이지장 양성종양 및 폴립진단비(연간1회한) ···...`

3. **Doc**: 약관, **Page**: 6
   **Excerpt**: `99. 질병수술비(백내장 및 대장용종내시경절제 제외)(매회지급) ········317 100. 관상동맥성형술 보장(급여, 연간1회한) ······...`

---

### lotte_female

**Policy**: `PER_EVENT`
**Display**: 매회 지급
**Evidence Count**: 2

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 426
   **Excerpt**: `수술1회당 142대질병수술비(이하 '보험금'이라 합니다)로 보험수익자에게 지급합니다. 142대질병수술비 특별약관 구 분...`

2. **Doc**: 약관, **Page**: 579
   **Excerpt**: `피보험자가 이 특별약관의 보험기간 중 질병으로 인하여 별표2에서 정한 "수술분류표" 중 어느 하나의 수술을 받은 때에는 수술1회당 "질병...`

---

### lotte_male

**Policy**: `PER_EVENT`
**Display**: 매회 지급
**Evidence Count**: 2

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 426
   **Excerpt**: `수술1회당 142대질병수술비(이하 '보험금'이라 합니다)로 보험수익자에게 지급합니다. 142대질병수술비 특별약관 구 분...`

2. **Doc**: 약관, **Page**: 579
   **Excerpt**: `피보험자가 이 특별약관의 보험기간 중 질병으로 인하여 별표2에서 정한 "수술분류표" 중 어느 하나의 수술을 받은 때에는 수술1회당 "질병...`

---

### meritz

**Policy**: `PER_EVENT`
**Display**: 매회 지급
**Evidence Count**: 1

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 1082
   **Excerpt**: `게 수술1회당 아래의 금액을 131대질병수술비로 지급합니 다. 구  분...`

---

### samsung

**Policy**: `UNKNOWN`
**Display**: 확인 불가 (근거 없음)
**Evidence Count**: 0

**UNKNOWN Justification**:
- No explicit repeat payment policy found in 질병수술비(1~5종) coverage documents
- Evidence-first approach: Cannot infer without documented evidence

---

### db_over41

**Policy**: `ANNUAL_LIMIT`
**Display**: 연간 1회한
**Evidence Count**: 7

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 10
   **Excerpt**: `118. 척추질병수술비(관혈/비관혈)(연간1회한, 동일질병당 1회지급) (비갱신형/갱신형) 특별약관·································...`

2. **Doc**: 약관, **Page**: 10
   **Excerpt**: `119. 이비인후과질환수술비(갱신형) 특별약관···············································································...`

3. **Doc**: 약관, **Page**: 10
   **Excerpt**: `120. 어깨질병수술비(회전근개파열)(연간1회한, 동일질병당 1회지급) (비갱신형/갱신형) 특별약관··························...`

---

### db_under40

**Policy**: `ANNUAL_LIMIT`
**Display**: 연간 1회한
**Evidence Count**: 7

**Evidence Sample** (first 3):

1. **Doc**: 약관, **Page**: 10
   **Excerpt**: `118. 척추질병수술비(관혈/비관혈)(연간1회한, 동일질병당 1회지급) (비갱신형/갱신형) 특별약관·································...`

2. **Doc**: 약관, **Page**: 10
   **Excerpt**: `119. 이비인후과질환수술비(갱신형) 특별약관···············································································...`

3. **Doc**: 약관, **Page**: 10
   **Excerpt**: `120. 어깨질병수술비(회전근개파열)(연간1회한, 동일질병당 1회지급) (비갱신형/갱신형) 특별약관··························...`

---

## Declaration

This snapshot locks Q8 implementation facts as of 2026-01-13.

**Freeze Conditions:**
- ✅ SSOT generated with evidence-based resolver
- ✅ API endpoint functional (GET /q8)
- ✅ Core Model integrity verified (SHA256 hashes)
- ✅ Regression tests passed
- ✅ Documentation complete

**After Freeze - Allowed:**
- SSOT regeneration (same logic)
- UI display improvements
- API format changes (data unchanged)

**After Freeze - Prohibited:**
- Core slot modifications
- Evidence inference/backfill
- Cross-Q contamination
- Scope expansion (대장용종 attribution, premium ranking)

---

**END OF SNAPSHOT**
