# Q12/Q13 Customer Copy SSOT

**Purpose**: Single Source of Truth for customer-facing UI text templates
**Date**: 2026-01-15
**Rules**: UI components MUST use these templates (NO arbitrary text generation)

---

## Q12: 암진단비 비교 리포트

### 페이지 제목
```
{보험사1} vs {보험사2} 암진단비 비교
```

### 시나리오 설명
```
{age}세 {sex}, {pay_term_years}년납 / {ins_term_years}세만기 기준
as_of_date: {as_of_date}
```

### 비교표 행 (고정)
1. **월보험료**
   - 값: `{premium:,}원`
   - 출처 라벨: `premium_raw JSON (20251126)`

2. **총납입보험료**
   - 값: `{total_premium:,}원`
   - 출처 라벨: `{pay_term_years}년 납입 기준`

3. **보장개시일(면책/감액)**
   - FOUND: `{customer_sentence}` (derived_semantics에서)
   - NOT_FOUND: `약관에서 명시 근거를 찾지 못했습니다 (정보 없음)`
   - 근거: `{doc_type} | {page_range}`

4. **유사암 제외 항목**
   - FOUND: `{customer_sentence}` (제자리암, 경계성종양 등 키워드 나열)
   - NOT_FOUND: `약관에서 명시 근거를 찾지 못했습니다 (정보 없음)`
   - 근거: `{doc_type} | {page_range}`

5. **보장 제외 사항**
   - FOUND: `{customer_sentence}` (핵심 제외 조건 요약)
   - NOT_FOUND: `약관에서 명시 근거를 찾지 못했습니다 (정보 없음)`
   - 근거: `{doc_type} | {page_range}`

### 종합판단 (Rule-based)

**장점/단점 Bullets**:
```
✅ 장점:
• {장점1}
• {장점2}

⚠️ 단점:
• {단점1}
• {단점2}
```

**장점 Rule**:
- R1: 월보험료가 상대적으로 저렴
- R2: 보장개시일이 빠름 (예: 90일 vs 1년)
- R3: 유사암 제외 범위가 좁음
- R4: 보장제외 조건이 적음

**단점 Rule**:
- R1: 월보험료가 상대적으로 높음
- R2: 보장개시일이 늦음 (예: 1년 vs 90일)
- R3: 유사암 제외 범위가 넓음
- R4: 보장제외 조건이 많음

**추천 문구**:
```
✅ 추천: {winner_insurer_name}
종합 점수: {score}점
• {reason_bullet1}
• {reason_bullet2}
```

**판단 보류 문구**:
```
판단 보류 (정보 부족)
• 비교 근거가 충분하지 않습니다.
• 보장개시일 또는 제외 항목 정보가 없습니다.
```

### Footer (고객용)
```
본 리포트는 약관 근거 기반으로 정리되며, 근거 미확인 항목은 "정보 없음"으로 표기됩니다.
보험료: premium_raw JSON (2025-11-26)
기준일: {as_of_date}
```

**금지**: "DB SSOT", "LLM 사용 안 함", "NO JSON reads" 등 기술적 용어 노출

### Evidence Toggle ("근거 보기")

**Rule (MUST)**:
- Default state: OFF (evidence hidden)
- Toggle button per table row that has evidence_ref
- Show doc_type, page_range, excerpt (truncated to 200 chars) when ON

**Evidence Refs Mapping**:
```
비교표 행                → insurer.items[{key}].evidence_ref
-------------------------------------------------------------
보장개시일(면책/감액)    → items["보장개시일(면책/감액)"].evidence_ref
유사암 제외 항목         → items["유사암 제외 항목"].evidence_ref
보장 제외 사항           → items["보장 제외 사항"].evidence_ref
```

**Display format when toggle ON**:
```
📄 {doc_type} | {page_range}
{excerpt[:200]}...
```

---

## Q13: 제자리암/경계성종양 보장 가능 여부

### 페이지 제목
```
제자리암/경계성종양 보장 가능 여부
```

### 서브타이틀
```
O: 보장 가능, X: 보장 불가, -: 정보 없음
```

### 매트릭스 구조
- Rows: 보장 항목 (진단비, 수술비, 항암약물, 표적항암, 다빈치치료)
- Columns: 보험사 (N01, N08 등)
- Sections: 암 유형 (제자리암, 경계성종양)

### 셀 값 결정 Rule (HARD)
```
IF subtype_coverage_map.status == "FOUND":
    IF excerpt contains "{subtype}" AND excerpt contains "제외":
        value = "X"
        reason = "A4200_1 정의에서 제외"
        evidence_ref = {doc_type, page_range, excerpt[:100]}
    ELIF excerpt contains "{subtype}" AND excerpt contains "포함":
        value = "O"
        reason = "A4200_1 정의에 포함"
        evidence_ref = {doc_type, page_range, excerpt[:100]}
    ELSE:
        value = "-"
        reason = "약관에서 명시 근거를 찾지 못했습니다"
ELSE (NOT_FOUND):
    value = "-"
    reason = "약관에서 명시 근거를 찾지 못했습니다"
```

### 종합 평가 Bullets
```
• 제자리암: {O_count}/{total_count}개 항목에서 보장 가능
• 경계성종양: {O_count}/{total_count}개 항목에서 보장 가능
• 진단비 보장: {O_insurers_count}개 보험사
```

### 추천 문구
```
✅ 추천: {winner_insurer_name}
종합 점수: {score}점
• R1: {ins_cd} has most O's ({count}개)
• R2: {ins_cd} has O for both subtypes in 진단비
```

**판단 보류 문구**:
```
동점으로 판단 보류 ({tied_insurers})
또는
판단 보류 (정보 부족)
```

### Footer
```
ℹ️ O/X 판정: coverage_mapping_ssot + evidence_slot (A4200_1 exclusion override)
ℹ️ 추천은 rule-based 결정적 로직 (LLM 사용 안 함)
Source: compare_table_v2.payload.q13_report
```

---

## Derived Semantics 생성 규칙

### waiting_period → customer_sentence
```
IF status == "FOUND":
    # Pattern 1: X일 후
    IF excerpt matches r'(\d+)일\s*(이후|후|경과)':
        customer_sentence = "{days}일 후 100% 지급"

    # Pattern 2: X년 (감액)
    ELIF excerpt matches r'(\d+)년.*(\d+)%.*감액':
        customer_sentence = "최초 {years}년 {percent}% 감액, 이후 100% 지급"

    # Pattern 3: X년 후
    ELIF excerpt matches r'(\d+)년\s*(이후|후|경과)':
        customer_sentence = "{years}년 후 100% 지급"

    # Fallback
    ELSE:
        customer_sentence = excerpt[:60] + "..."
ELSE:
    customer_sentence = "약관에서 명시 근거를 찾지 못했습니다 (정보 없음)"
    customer_badge = "정보없음"
```

### subtype_coverage_map → customer_sentence
```
IF status == "FOUND":
    found_subtypes = []
    FOR keyword IN ['제자리암', '경계성종양', '갑상선암', '기타피부암', '소액암']:
        IF keyword in excerpt:
            found_subtypes.append(keyword)

    IF found_subtypes:
        customer_sentence = ", ".join(found_subtypes) + " 제외"
    ELSE:
        customer_sentence = "유사암 제외 항목 확인 필요"
ELSE:
    customer_sentence = "약관에서 명시 근거를 찾지 못했습니다 (정보 없음)"
```

### exclusions → customer_sentence
```
IF status == "FOUND":
    # Extract key sentences with "제외/미지급/면책"
    key_sentences = extract_sentences_with_keywords(excerpt, ["제외", "미지급", "면책"])

    IF key_sentences:
        customer_sentence = key_sentences[0][:80] + "..."
    ELSE:
        customer_sentence = "보장제외 조항 존재 (상세 내용은 약관 참조)"
ELSE:
    customer_sentence = "약관에서 명시 근거를 찾지 못했습니다 (정보 없음)"
```

---

## Premium 라벨 (LOCK)

**현재 상태** (MUST use):
```
Premium SSOT DB (2025-11-26)
```

**DoD**:
- UI에 정확히 `Premium SSOT DB (2025-11-26)` 표시
- JSON 읽기 금지, DB ONLY
- Footer에 "NO JSON reads" 명시

---

## NOT_FOUND 고정 문구

**모든 slots에서 NOT_FOUND인 경우**:
```
약관에서 명시 근거를 찾지 못했습니다 (정보 없음)
```

**이유 추가 (선택적)**:
```
{not_found_reason}
예: "NO_CANDIDATE", "GATE_FAIL", "EMPTY_EXCERPT"
```

---

## 금지 사항 (NEVER)

❌ UI에서 임의 해석/계산
❌ "DB SSOT"라고만 쓰기 (premium 출처 불명확)
❌ LLM 호출
❌ Vector 검색
❌ Step3 evidence 재해석

✅ ONLY:
- Rule-based transformation
- Template substitution
- compare_table_v2.payload 소비
