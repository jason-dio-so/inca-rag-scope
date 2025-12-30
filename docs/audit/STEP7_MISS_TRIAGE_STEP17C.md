# Step7 Miss Candidates Triage - STEP NEXT-17C

**Date**: 2025-12-30
**Scope**: Top 15 candidates (5 per insurer: hyundai, kb, lotte)
**Method**: Manual review of PDF snippets + evidence classification

---

## Triage Labels

| Label | Description | Action Required |
|-------|-------------|-----------------|
| **TRUE_MISS_TABLE** | Coverage name + amount clearly in table, but UNCONFIRMED | Fix Step7 extraction |
| **FALSE_POSITIVE_OTHER_AMOUNT** | Amount found but unrelated (premium/other coverage) | No action - expected |
| **NEEDS_OCR** | Image/scan PDF, text garbled | OCR preprocessing needed |
| **NAME_MISMATCH** | Coverage name normalization/mapping issue | Fix mapping or extraction pattern |

---

## Hyundai (현대해상) - Top 5 Candidates

### Candidate 1: 질병사망 (Page 2)

**Snippet**:
```
가입담보 가입금액 보험료(원) 납기/만기
1.기본계약(상해사망) 1천만원 448 20년납100세만기
2.기본계약(상해후유장해) 1천만원 550 20년납100세만기
3.보험료납입면제대상담보 10만원 35 전기납20년만기
4.골절진단(치아파절제외)...
```

**Analysis**:
- Looking for "질병사망" but snippet shows "상해사망"
- "질병사망" is NOT in this snippet (these are other coverages)
- The amount "1천만원" belongs to "상해사망", not "질병사망"

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Coverage name mismatch - detected amount belongs to different coverage (상해사망)

---

### Candidate 3: 상해사망 (Page 2)

**Snippet**:
```
가입담보 가입금액 보험료(원) 납기/만기
1.기본계약(상해사망) 1천만원 448 20년납100세만기
2.기본계약(상해후유장해) 1천만원 550 20년납100세만기
```

**Analysis**:
- "1.기본계약(상해사망)" clearly shows "1천만원"
- Table structure: 담보명 + 가입금액 + 보험료 + 납기/만기
- This is EXACTLY what Step7 should extract

**Label**: **TRUE_MISS_TABLE**
**Reason**: Coverage name "기본계약(상해사망)" + amount "1천만원" clearly in table, should be extracted

**Target**: YES - add to Step7 fix targets

---

### Candidate 5: 표적항암약물허가치료비(최초1회한) (Page 2)

**Snippet**:
```
가입담보 가입금액 보험료(원) 납기/만기
1.기본계약(상해사망) 1천만원 448 20년납100세만기
2.기본계약(상해후유장해) 1천만원 550 20년납100세만기
3.보험료납입면제대상담보 10만원 35 전기납20년만기
4.골절진단(치아파절제외)...
```

**Analysis**:
- Looking for "표적항암약물허가치료비" but snippet only shows "상해사망/상해후유장해/보험료납입면제"
- Coverage name NOT in snippet
- False positive - page has table but wrong coverages

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Coverage "표적항암약물허가치료비" not in this snippet (different part of table)

---

### Candidate 10: 카티(CAR-T)항암약물허가치료비 (Page 7)

**Snippet**:
```
담보명 및 보장내용 납기/만기 가입금액 보험료(원)
27.카티(CAR-T)항암약물허가치료(연간1회한)(갱신형)담보 전기납10년만기갱신(최대100세) 1천만원 37
보장개시일 이후 '카티(CAR-T)항암약물허가치료 적응증'으로 진단확정되고, 그 치료를 직접적인 목적으로 '카티(CAR-T)항암약물허가치료'를 받은 경우 가입금액 지...
```

**Analysis**:
- Coverage name: "카티(CAR-T)항암약물허가치료(연간1회한)(갱신형)담보"
- Amount: "1천만원"
- Table structure clear
- **Canonical name issue**: DB has "카티(CAR-T)항암약물허가치료비" but PDF shows "카티(CAR-T)항암약물허가치료...담보"
- Name normalization may cause miss

**Label**: **NAME_MISMATCH**
**Reason**: Coverage name variation - "...치료비" vs "...치료...담보" suffix difference

**Target**: MAYBE - check if name normalization handles "담보" suffix removal

---

### Candidate 12: 혈전용해치료비 (Page 3)

**Snippet**:
```
가입담보 가입금액 보험료(원) 납기/만기
28.질병입원일당(1-180일)담보 1만원 5,052 20년납100세만기
29.암직접치료입원일당(1-180일,요양병원제외)담보 2만원 1,730 20년납100세만기
30.질병수술담보 10만원 2,561 20년납100세...
```

**Analysis**:
- Looking for "혈전용해치료비" but snippet shows "질병입원일당/암직접치료입원일당/질병수술"
- Coverage name NOT in snippet

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Coverage not in snippet (wrong part of table)

---

## KB (KB손해보험) - Top 5 Candidates

### Candidate 14: 질병사망 (Page 2)

**Snippet**:
```
KB 닥터플러스 건강보험(세만기)(해약환급금미지급형)(무배당)(25.08)(24882)
계약사항 20년납 100세만기 | 세만기 | 8대납입면제기본 | 납입후50%지급형 | 기본플랜
1회 보험료 130,188원 납입형태 월납 통합고객님 피보...
```

**Analysis**:
- Snippet shows premium summary section (130,188원 is **total premium**, not coverage amount)
- No coverage table in this snippet
- No "질병사망" coverage name visible

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Detected "130,188원" is total premium, not coverage-specific amount

---

### Candidate 16: 상해사망 (Page 2)

**Snippet**: (Same as Candidate 14)

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Same - premium summary, not coverage table

---

### Candidate 19: 뇌혈관질환진단비 (Page 5)

**Snippet**:
```
보장명 및 보장내용 가입금액 보험료(원) 납입|보험기간
74 유사암진단비 6백만원 870 20년/100세
보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시
(각각 최초1회 한, 계약일로부터 1년미만시 보험가입금액의 50%지급)
85...
```

**Analysis**:
- Looking for "뇌혈관질환진단비" but snippet shows "유사암진단비"
- Coverage name NOT in snippet (wrong part of table)

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Different coverage shown ("유사암진단비" not "뇌혈관질환진단비")

---

### Candidate 36: 뇌혈관질환수술비 (Page 3)

**Snippet**:
```
보장명 가입금액 보험료(원) 납입|보험기간
209 뇌혈관질환수술비 5백만원 885 20년/100세
213 허혈성심장질환수술비 5백만원 1,760 20년/100세
227 상해수술비 10만원 420 20년/100세
256 항암방사선치료비 3백만원 1,587...
```

**Analysis**:
- Coverage name: "209 뇌혈관질환수술비"
- Amount: "5백만원"
- Table structure clear
- **Perfect table match**

**Label**: **TRUE_MISS_TABLE**
**Reason**: Coverage name + amount clearly in table, exact match

**Target**: YES - add to Step7 fix targets

---

### Candidate 38: 허혈성심장질환수술비 (Page 3)

**Snippet**:
```
보장명 가입금액 보험료(원) 납입|보험기간
209 뇌혈관질환수술비 5백만원 885 20년/100세
213 허혈성심장질환수술비 5백만원 1,760 20년/100세
227 상해수술비 10만원 420 20년/100세
```

**Analysis**:
- Coverage name: "213 허혈성심장질환수술비"
- Amount: "5백만원"
- Table structure clear
- **Perfect table match**

**Label**: **TRUE_MISS_TABLE**
**Reason**: Coverage name + amount clearly in table, exact match

**Target**: YES - add to Step7 fix targets

---

## Lotte (롯데손해보험) - Top 5 Candidates

### Candidate 42: 표적항암약물허가치료비(최초1회한) (Page 2)

**Snippet**:
```
담보명 가입금액 납기/만기 보험료(원)
1 상해후유장해(3~100%) 3,000만원 20년/100세 1,800
2 상해사망 1,000만원 20년/100세 290
21 질병사망 1,000만원 20년/80세 4,800
30 일반암진단비Ⅱ 3,000만원 20년...
```

**Analysis**:
- Looking for "표적항암약물허가치료비" but snippet shows "상해후유장해/상해사망/질병사망/일반암진단비"
- Coverage NOT in this snippet (wrong part of table)

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Coverage not in snippet

---

### Candidate 43: 표적항암약물허가치료비(최초1회한) (Page 6)

**Snippet**:
```
담보유형 담보명 가입금액 납기/만기 보험료(원) 보장내용
암관련 88 다빈치로봇갑상선암및전립선암수술비(최초1회한)(갱신형) 200만원 10년/10년갱신 108
보장개시일 이후에 갑상선암 또는 전립선암으로 진단확정되고...
```

**Analysis**:
- Looking for "표적항암약물허가치료비" but snippet shows "다빈치로봇갑상선암및전립선암수술비"
- Different coverage

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Different coverage in snippet

---

### Candidate 44: 표적항암약물허가치료비(최초1회한) (Page 7)

**Snippet**:
```
담보유형 담보명 가입금액 납기/만기 보험료(원) 보장내용
암관련 91 표적항암약물허가치료비(림프종및백혈병관련암)(1회한)(갱신형) 1,000만원 10년/10년갱신 200
보장개시일 이후에 '림프종및백혈병관련암'으로 진단확정되고 그 암의 직접적인 치료를 목적으로 표적항암약물허가치료를 받은 경우...
```

**Analysis**:
- Coverage name: "표적항암약물허가치료비(림프종및백혈병관련암)(1회한)(갱신형)"
- Amount: "1,000만원"
- Table structure clear
- **Name variation issue**: Canonical is "표적항암약물허가치료비(최초1회한)" but PDF has "표적항암약물허가치료비(림프종및백혈병관련암)(1회한)"
- Different specific type

**Label**: **NAME_MISMATCH**
**Reason**: Coverage name variation - specific cancer type included in PDF name

**Target**: MAYBE - check if this is actually a different coverage or same coverage with different name

---

### Candidate 54: 다빈치로봇암수술비 (Page 2)

**Snippet**:
```
담보명 가입금액 납기/만기 보험료(원)
1 상해후유장해(3~100%) 3,000만원 20년/100세 1,800
2 상해사망 1,000만원 20년/100세 290
21 질병사망 1,000만원 20년/80세 4,800
30 일반암진단비Ⅱ 3,000만원 20년...
```

**Analysis**:
- Looking for "다빈치로봇암수술비" but snippet shows different coverages
- Coverage NOT in snippet

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Coverage not in snippet

---

### Candidate 55: 다빈치로봇암수술비 (Page 5)

**Snippet**:
```
담보유형 담보명 가입금액 납기/만기 보험료(원) 보장내용
암관련 64 일반암수술비(1회한) 500만원 20년/100세 5,700
보장개시일 이후에 일반암으로 진단확정되고 그 일반암의 직접적인 치료를 목적으로 수술시...
```

**Analysis**:
- Looking for "다빈치로봇암수술비" but snippet shows "일반암수술비"
- Different coverage

**Label**: **FALSE_POSITIVE_OTHER_AMOUNT**
**Reason**: Different coverage shown

---

## Triage Summary

### By Label

| Label | Count | Percentage |
|-------|-------|------------|
| TRUE_MISS_TABLE | 3 | 20% |
| FALSE_POSITIVE_OTHER_AMOUNT | 10 | 67% |
| NAME_MISMATCH | 2 | 13% |
| NEEDS_OCR | 0 | 0% |
| **TOTAL** | **15** | **100%** |

### By Insurer

| Insurer | TRUE_MISS | FALSE_POS | NAME_MISMATCH | NEEDS_OCR |
|---------|-----------|-----------|---------------|-----------|
| hyundai | 1 | 3 | 1 | 0 |
| kb | 2 | 3 | 0 | 0 |
| lotte | 0 | 4 | 1 | 0 |
| **TOTAL** | **3** | **10** | **2** | **0** |

---

## TRUE_MISS_TABLE Targets (Confirmed Misses)

### Target 1: Hyundai - 상해사망
- **Page**: 2
- **Snippet**: "1.기본계약(상해사망) 1천만원 448 20년납100세만기"
- **Pattern**: Clear table row with coverage name + amount
- **Issue**: Step7 likely missed "기본계약(상해사망)" pattern (parentheses in name)

### Target 2: KB - 뇌혈관질환수술비
- **Page**: 3
- **Snippet**: "209 뇌혈관질환수술비 5백만원 885 20년/100세"
- **Pattern**: Clear table row with number prefix + coverage name + amount
- **Issue**: Step7 may not handle number prefixes (209, 213, etc.)

### Target 3: KB - 허혈성심장질환수술비
- **Page**: 3
- **Snippet**: "213 허혈성심장질환수술비 5백만원 1,760 20년/100세"
- **Pattern**: Clear table row with number prefix + coverage name + amount
- **Issue**: Same as Target 2 - number prefix handling

---

## NAME_MISMATCH Analysis

### Case 1: Hyundai - 카티(CAR-T)항암약물허가치료비
- **DB Canonical**: "카티(CAR-T)항암약물허가치료비"
- **PDF Text**: "카티(CAR-T)항암약물허가치료(연간1회한)(갱신형)담보"
- **Issue**: "비" suffix vs "담보" suffix
- **Recommendation**: Add "담보" suffix removal to normalization logic

### Case 2: Lotte - 표적항암약물허가치료비(최초1회한)
- **DB Canonical**: "표적항암약물허가치료비(최초1회한)"
- **PDF Text**: "표적항암약물허가치료비(림프종및백혈병관련암)(1회한)(갱신형)"
- **Issue**: Specific cancer type variation - may be different coverage or subtype
- **Recommendation**: Check mapping file to see if these are same or different coverages

---

## Step7 Extraction Issues Identified

### 1. Number Prefix Handling (KB)
- **Pattern**: `209 뇌혈관질환수술비`, `213 허혈성심장질환수술비`
- **Issue**: Step7 may not strip number prefixes before matching coverage names
- **Fix**: Add regex to remove leading `\d+\s+` from coverage names in table rows

### 2. Parenthesized Coverage Names (Hyundai)
- **Pattern**: `기본계약(상해사망)`
- **Issue**: Parentheses may break name matching
- **Fix**: Improve name normalization to handle parentheses

### 3. Suffix Variations
- **Pattern**: "...치료비" vs "...치료...담보"
- **Issue**: Different document style suffixes
- **Fix**: Add common suffix removal/normalization

---

## Recommendations

### Immediate (This STEP)
1. ✅ Document 3 TRUE_MISS_TABLE targets for Step7 fix
2. ✅ Document 2 NAME_MISMATCH cases for mapping/normalization review
3. ✅ Update regression tests with specific XFAIL reasons

### Next STEP (Step7 Improvement)
1. Implement number prefix removal in Step7 table parsing
2. Improve coverage name normalization:
   - Handle parentheses in coverage names
   - Remove common suffixes ("담보", "비", etc.)
3. Test fixes against 3 confirmed TRUE_MISS targets
4. Re-run extraction for hyundai/kb/lotte

### Future
1. Reduce false positive rate (67% currently)
   - Improve context window for amount detection
   - Verify coverage name appears near detected amount (within N chars)
2. Add coverage name proximity check to miss detection algorithm

---

## References

- Source: `docs/audit/STEP7_MISS_CANDIDATES.md`
- Targets: `docs/audit/STEP7_MISS_TARGETS.md` (to be created)
- Regression Tests: `tests/test_step7_miss_candidates_regression.py`

---

**Conclusion**: Out of 15 triaged candidates, only 3 (20%) are TRUE MISSES requiring Step7 fixes. Most (67%) are false positives where amount belongs to different coverage. 2 cases (13%) require name normalization improvements.
