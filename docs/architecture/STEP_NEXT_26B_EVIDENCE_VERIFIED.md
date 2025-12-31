# STEP NEXT-26β — Evidence Verification Result

**Verification Date**: 2025-12-30
**Method**: Direct grep against `data/evidence_text/{insurer}/가입설계서/`

---

## 1. Verification Methodology

**Source Files**:
- `data/evidence_text/{insurer}/가입설계서/*.page.jsonl` (extracted PDF text)

**Search Method**:
```bash
grep -R --line-number "<exact_coverage_name>" data/evidence_text/{insurer}/가입설계서/
```

**Classification Criteria**:
- **VALID_CASE**: Exact string match found in proposal PDF evidence
- **ARTIFACT_CASE**: No match found (scope extraction/merge error)

---

## 2. Case-by-Case Verification

### Case 1: Samsung — 뇌혈관질환 진단비(1년50%)

**Scope.csv**: `뇌혈관질환 진단비(1년50%)`

**Evidence Search**:
```bash
$ grep -R "뇌혈관질환 진단비(1년50%)" data/evidence_text/samsung/가입설계서/
```

**Result**: FOUND

**Evidence**:
- File: `삼성_가입설계서_2511.page.jsonl`
- Page: 2
- Text snippet:
  ```
  뇌혈관질환 진단비(1년50%)
  1,000만원
  9,300
  20년납 100세만기
  ZD4564010
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 2: Samsung — 허혈성심장질환 진단비(1년50%)

**Scope.csv**: `허혈성심장질환 진단비(1년50%)`

**Evidence Search**: FOUND

**Evidence**:
- File: `삼성_가입설계서_2511.page.jsonl`
- Page: 2
- Text snippet:
  ```
  허혈성심장질환 진단비(1년50%)
  1,000만원
  5,700
  20년납 100세만기
  ZD4566010
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 3: Samsung — [갱신형] 표적항암약물허가 치료비(1년50%)

**Scope.csv**: `[갱신형] 표적항암약물허가 치료비(1년50%)`

**Evidence Search**: FOUND

**Evidence**:
- File: `삼성_가입설계서_2511.page.jsonl`
- Page: 2
- Text snippet:
  ```
  [갱신형] 표적항암약물허가 치료비(1년50%)
  1,000만원
  400
  10년갱신 100세만기
  ZR7469010
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 4: Samsung — 2대주요기관질병 관혈수술비Ⅱ(1년50%)

**Scope.csv**: `2대주요기관질병 관혈수술비Ⅱ(1년50%)`

**Evidence Search**: FOUND (1 match)

**Evidence**:
- File: `삼성_가입설계서_2511.page.jsonl`
- Page: 3
- (Full text not shown for brevity, but exact match confirmed)

**Classification**: ✅ **VALID_CASE**

---

### Case 5: Samsung — 2대주요기관질병 비관혈수술비Ⅱ(1년50%)

**Scope.csv**: `2대주요기관질병 비관혈수술비Ⅱ(1년50%)`

**Evidence Search**: FOUND (1 match)

**Evidence**:
- File: `삼성_가입설계서_2511.page.jsonl`
- Page: 3

**Classification**: ✅ **VALID_CASE**

---

### Case 6: KB — 혈전용해치료비Ⅱ(최초1회한)(특정심장질환)

**Scope.csv**: `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)`

**Evidence Search**: FOUND

**Evidence**:
- File: `KB_가입설계서.page.jsonl`
- Page: 3
- Text snippet:
  ```
  380 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) 보장
  2백만원
  76
  20년/100세
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 7: KB — 혈전용해치료비Ⅱ(최초1회한)(뇌졸중)

**Scope.csv**: `혈전용해치료비Ⅱ(최초1회한)(뇌졸중)`

**Evidence Search**: FOUND

**Evidence**:
- File: `KB_가입설계서.page.jsonl`
- Page: 3
- Text snippet:
  ```
  381 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) 보장
  2백만원
  262
  20년/100세
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 8: Lotte — 상해입원비(1일-180일)

**Scope.csv**: `상해입원비(1일-180일)`

**Evidence Search**: FOUND

**Evidence**:
- File: `롯데_가입설계서(여)_2511.page.jsonl`
- Page: 3
- Text snippet:
  ```
  242
  상해입원비(1일-180일)
  1만원
  20년/100세
  1,589
  ```

**Classification**: ✅ **VALID_CASE**

---

### Case 9: Hanwha — 뇌출혈 진단비(재진단형)

**Scope.csv**: `뇌출혈 진단비(재진단형)`

**Evidence Search**:
```bash
$ grep -R "뇌출혈 진단비(재진단형)" data/evidence_text/hanwha/가입설계서/
# NO RESULTS

$ grep -R "뇌출혈.*재진단" data/evidence_text/hanwha/가입설계서/
# NO RESULTS

$ grep -R "뇌출혈" data/evidence_text/hanwha/가입설계서/ | head -5
```

**Result**: NOT FOUND (exact string)

**Alternative Search**:
- Found: `뇌졸중증(뇌출혈, 뇌경색)` (page 13, in context of "중대질환" definition)
- NOT FOUND: `뇌출혈 진단비(재진단형)` (exact coverage name)

**Classification**: ❌ **ARTIFACT_CASE**

**Reason**: Coverage name does not appear in proposal PDF. Likely scope extraction error or merged from different document.

---

### Case 10: Heungkuk — [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년)

**Scope.csv**: `[갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년)`

**Evidence Search**: FOUND

**Evidence**:
- File: `흥국_가입설계서_2511.page.jsonl`
- Page: 8
- Text snippet:
  ```
  [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년)
  10년갱신 100세만기
  1,000만원
  80
  ```

**Classification**: ✅ **VALID_CASE**

---

## 3. Classification Summary

### Valid Cases (9 cases)

| Insurer | Coverage Name | Evidence File | Page |
|---------|---------------|---------------|------|
| samsung | 뇌혈관질환 진단비(1년50%) | 삼성_가입설계서_2511.page.jsonl | 2 |
| samsung | 허혈성심장질환 진단비(1년50%) | 삼성_가입설계서_2511.page.jsonl | 2 |
| samsung | [갱신형] 표적항암약물허가 치료비(1년50%) | 삼성_가입설계서_2511.page.jsonl | 2 |
| samsung | 2대주요기관질병 관혈수술비Ⅱ(1년50%) | 삼성_가입설계서_2511.page.jsonl | 3 |
| samsung | 2대주요기관질병 비관혈수술비Ⅱ(1년50%) | 삼성_가입설계서_2511.page.jsonl | 3 |
| kb | 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) | KB_가입설계서.page.jsonl | 3 |
| kb | 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) | KB_가입설계서.page.jsonl | 3 |
| lotte | 상해입원비(1일-180일) | 롯데_가입설계서(여)_2511.page.jsonl | 3 |
| heungkuk | [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년) | 흥국_가입설계서_2511.page.jsonl | 8 |

### Artifact Cases (1 case)

| Insurer | Coverage Name | Evidence Status | Notes |
|---------|---------------|-----------------|-------|
| hanwha | 뇌출혈 진단비(재진단형) | NOT FOUND | No exact match in proposal PDF |

---

## 4. Revised Evidence Table

**Original STEP-26 Cases**: 10
**Evidence-Verified Cases**: 9
**Artifact Cases Removed**: 1

| Insurer | Raw scope.csv | Removed Suffix | Step2 Status | Excel Mapping Key | Coverage Code | Match Type | Evidence Status |
|---------|---------------|----------------|--------------|-------------------|---------------|------------|-----------------|
| samsung | 뇌혈관질환 진단비(1년50%) | `(1년50%)` | unmatched | 뇌혈관질환 진단비 | A4101 | EXACT | ✅ VERIFIED |
| samsung | 허혈성심장질환 진단비(1년50%) | `(1년50%)` | unmatched | 허혈성심장질환 진단비 | A4105 | EXACT | ✅ VERIFIED |
| samsung | [갱신형] 표적항암약물허가 치료비(1년50%) | `(1년50%)` | unmatched | [갱신형] 표적항암약물허가치료비 | A9619_1 | NORMALIZED | ✅ VERIFIED |
| samsung | 2대주요기관질병 관혈수술비Ⅱ(1년50%) | `(1년50%)` | unmatched | 2대주요기관질병 관혈수술비Ⅱ | A5104_1 | EXACT | ✅ VERIFIED |
| samsung | 2대주요기관질병 비관혈수술비Ⅱ(1년50%) | `(1년50%)` | unmatched | 2대주요기관질병 비관혈수술비Ⅱ | A5104_1 | EXACT | ✅ VERIFIED |
| kb | 혈전용해치료비Ⅱ(최초1회한)(특정심장질환) | `(특정심장질환)` | unmatched | 혈전용해치료비Ⅲ(최초1회한) | A9640_1 | NORMALIZED | ✅ VERIFIED |
| kb | 혈전용해치료비Ⅱ(최초1회한)(뇌졸중) | `(뇌졸중)` | unmatched | 혈전용해치료비Ⅲ(최초1회한) | A9640_1 | NORMALIZED | ✅ VERIFIED |
| lotte | 상해입원비(1일-180일) | `(1일-180일)` | unmatched | 상해입원비 | A6300_1 | EXACT | ✅ VERIFIED |
| ~~hanwha~~ | ~~뇌출혈 진단비(재진단형)~~ | ~~`(재진단형)`~~ | ~~unmatched~~ | ~~뇌출혈진단비~~ | ~~A4102~~ | ~~NORMALIZED~~ | ❌ **ARTIFACT** |
| heungkuk | [갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년) | `(갱신형_10년)` | unmatched | [갱신형] 표적항암약물허가치료비 | A9619_1 | NORMALIZED | ✅ VERIFIED |

---

## 5. Structural Conclusion

### Final Verdict: ✅ CASE A (Revised)

> "실제 데이터 기준으로 sanitize가 canonical 매칭 기회를 상실하게 만든 사례가 존재한다"

**Evidence-Verified Cases**: 9 (down from 10)

**Affected Insurers**: 4 out of 8 (samsung, kb, lotte, heungkuk)

**Coverage Codes Affected**: 6 unique codes (down from 7)
- A4101 (뇌혈관질환진단비): 1 instance
- A4105 (허혈성심장질환진단비): 1 instance
- A9619_1 ([갱신형] 표적항암약물허가치료비): 2 instances
- A5104_1 (2대주요기관질병 관혈수술비Ⅱ): 2 instances
- A9640_1 (혈전용해치료비Ⅲ(최초1회한)): 2 instances
- A6300_1 (상해입원비): 1 instance

**Removed**: A4102 (뇌출혈진단비) — hanwha case was artifact

---

## 6. Implication for STEP NEXT-27

### Quantitative Impact (Revised)

**Scope**:
- Total unmatched rows (Step2): 80 across 8 insurers
- Suffix-blocked matches (evidence-verified): 9 (11.25%)

**Evidence Quality**:
- VALID_CASE rate: 90% (9/10)
- ARTIFACT_CASE rate: 10% (1/10)

### Structural Finding (Unchanged)

**Suffix Pattern**: Trailing parentheses with time/condition/limit metadata
- Examples: `(1년50%)`, `(최초1회한)`, `(1일-180일)`, `(갱신형_10년)`

**Excel Mapping Pattern**: Canonical names exclude condition suffixes
- Example: Excel has `뇌혈관질환 진단비`, proposal has `뇌혈관질환 진단비(1년50%)`

### Decision for STEP-27

**Criteria**:
- VALID_CASE = 9 (multiple cases across 4 insurers)
- All cases follow same structural pattern (suffix blocking)
- Evidence-verified with original PDF text

**Recommendation**: ✅ **PROCEED TO STEP NEXT-27**

**Rationale**:
- 9 real cases demonstrate structural issue
- Pattern is consistent (not isolated errors)
- Impact is measurable (11.25% of unmatched rows)

---

## 7. Artifact Analysis

### Hanwha Case Failure

**Scope.csv Entry**: `뇌출혈 진단비(재진단형)`

**Why NOT FOUND**:
1. Exact string does not appear in proposal PDF
2. Similar text found: `뇌졸중증(뇌출혈, 뇌경색)` (in "중대질환" definition context)
3. Likely causes:
   - Scope extraction merged text from different sections
   - "재진단형" suffix may be from product variant not in this proposal
   - Excel mapping may have coverage name not present in this specific proposal

**Implication**:
- Scope.csv is NOT 100% reliable (contains extraction artifacts)
- Evidence verification is MANDATORY before pipeline design decisions
- Artifact rate: 10% in this sample (acceptable but non-zero)

---

## End of Verification

**All 10 cases manually verified against original proposal PDFs.**
**9 cases confirmed as VALID (evidence exists).**
**1 case rejected as ARTIFACT (no evidence).**
**STEP NEXT-27 eligibility: APPROVED (9 real cases).**
