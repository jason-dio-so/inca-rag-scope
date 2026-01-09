# Customer Question Coverage Matrix (LOCK)

**Version:** 1.1
**Date:** 2026-01-08
**Status:** 🔒 LOCKED
**Basis:** STEP NEXT-76, STEP NEXT-77, STEP NEXT-79 실증 결과

---

## 0. 문서 목적

고객 질문 유형(1~14)에 대해 시스템이 **어디까지 답변 가능한지를 실증 기반으로 고정(Lock)**한다.

- ❌ 기능 확장 제안 금지
- ❌ 추론/해석 추가 금지
- ✅ 현재 파이프라인 실증 결과만 기록

---

## 1. 요약 테이블 (필수)

| 질문 번호 | 질문 요약 | 상태 | 사용 슬롯 | Evidence 출처 | 비고 |
|---------|---------|------|----------|-------------|------|
| Q1 | 보장 금액/한도는? | ✅ 가능 | `payout_limit` | 가입설계서, 약관 | STEP 1-5 active |
| Q2 | 유병자(고혈압/당뇨) 가입 가능? | ✅ 가능 | `underwriting_condition` | 상품요약서, 사업방법서 | STEP NEXT-77 실증 (100% KB) |
| Q3 | 특약 단독 가입 가능? | ✅ 가능 | `mandatory_dependency` | 상품요약서, 사업방법서, 약관 | STEP NEXT-77 실증 (100% KB) |
| Q4 | 재발/재진단 시에도 지급? | ✅ 가능 | `payout_frequency` | 가입설계서, 약관 | STEP NEXT-77 실증 (100% KB) |
| Q5 | 면책기간/대기기간은? | ✅ 가능 | `waiting_period` | 가입설계서, 상품요약서 | STEP 1-5 active |
| Q6 | 감액기간/비율은? | ✅ 가능 | `reduction` | 약관 | STEP 1-5 active |
| Q7 | 가입 나이 제한은? | ✅ 가능 | `entry_age` | 가입설계서, 약관 | STEP 1-5 active |
| Q8 | 타사 가입도 영향? (업계 누적) | ✅ 가능 | `industry_aggregate_limit` | 약관 | STEP NEXT-77 실증 (100% FOUND_GLOBAL KB) |
| Q9 | 보장 개시일은? | ✅ 가능 | `start_date` | 가입설계서, 약관 | STEP 1-5 active |
| Q10 | 어떤 경우 제외? (면책사항) | ✅ 가능 | `exclusions` | 가입설계서, 약관 | STEP 1-5 active |
| Q11 | 암직접입원비 보장한도(일수구간) | ✅ 가능 | `benefit_day_range` | 가입설계서, 상품요약서, 약관 | STEP NEXT-80 완료 (KB 100% coverage) |
| Q12 | 삼성 vs 메리츠 암진단비 비교 + 추천 | ✅ 가능 | 기존 슬롯 조합 + Rule | 가입설계서, 약관 | STEP NEXT-74/75 Rule 사용 |
| Q13 | 제자리암/경계성종양 O/X 비교 | ✅ 가능 | `subtype_coverage_map` | 가입설계서, 약관 | STEP NEXT-81 완료 (KB 100% + Meritz) |
| Q14 | 보험료 가성비 Top 4 비교 | ⚠️ 조건부 | 외부 테이블 결합 | premium_table, rate_example.xlsx | 외부 데이터 필수 (YELLOW) |

**상태 범례:**
- ✅ 가능 (증명 완료): Evidence 기반 답변 가능
- ⚠️ 조건부: 추가 데이터/고객 정보/슬롯 필요
- ❌ 불가: 의도적 제외 (마케팅/저축 영역)

---

## 2. 질문별 판정 근거 (1~10 전부)

### Q1. 보장 금액/한도는?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `payout_limit`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - KB 43 coverages: FOUND rate 높음
  - 예: "3천만원", "1천만원", "연간 5회" 등 deterministic value 추출

---

### Q2. 유병자(고혈압/당뇨) 가입 가능?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `underwriting_condition`
- **Evidence 상태:** FOUND (69.8%) + FOUND_GLOBAL (30.2%)
- **근거 문서:** 상품요약서, 사업방법서
- **제약 사항:** 없음 (100% evidence coverage)
- **실증 근거:**
  - STEP NEXT-77 실증: KB 43 coverages 100% (30 FOUND + 13 FOUND_GLOBAL)
  - Evidence 예시: "가입나이 및 건강상태직무 등에 따라 보험가입금액이 제한되거나 가입이 불가능할 수 있음"
  - Keywords: "유병자", "고혈압", "당뇨", "건강상태", "건강고지"
  - Gate validation: G1-G4 통과

**진단비 비교 범위 안내:**
```
📌 본 시스템에서 비교 가능한 진단비:
- 암진단비 (유사암 제외)
- 고액암진단비
- 유사암진단비
- 재진단암진단비
- 뇌졸중진단비
- 허혈성심장질환진단비

급성심근경색은 단독 진단비 상품이 없어
본 시스템의 진단비 비교 대상에 포함되지 않습니다.
```

**답변 예시 (근거 포함):**
```
일반상해사망(기본) 담보의 경우:
- 건강상태에 따라 보험가입금액이 제한되거나 가입이 불가능할 수 있습니다
- 근거: 상품요약서 p.15 "회사가 정하는 기준에 따라 가입나이 및 건강상태직무 등에
  따라 보험가입금액이 제한되거나 가입이 불가능할 수 있음"
```

---

### Q3. 특약 단독 가입 가능?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `mandatory_dependency`
- **Evidence 상태:** FOUND (11.6%) + FOUND_GLOBAL (88.4%)
- **근거 문서:** 상품요약서, 사업방법서, 약관
- **제약 사항:** 없음 (100% evidence coverage)
- **실증 근거:**
  - STEP NEXT-77 실증: KB 43 coverages 100% (5 FOUND + 38 FOUND_GLOBAL)
  - Evidence 예시: "의무가입 특별약관... 보험료납입면제대상보장대기본(8)"
  - Keywords: "주계약 필수", "필수 가입", "의무가입", "단독가입"
  - Mostly product-level rules (88.4% FOUND_GLOBAL) - expected for contract structure

**답변 예시 (근거 포함):**
```
일반상해사망(기본) 담보의 경우:
- 보험료납입면제대상보장(8대기본)은 의무가입 특별약관입니다
- 근거: 상품요약서 p.35 "보험종목에 따른 의무부가 특별약관은 다음과 같음...
  의무부가 특별약관 보험료납입면제대상보장대기본(8"
```

---

### Q4. 재발/재진단 시에도 지급?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `payout_frequency`
- **Evidence 상태:** FOUND (97.7%) + FOUND_GLOBAL (2.3%)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음 (100% evidence coverage)
- **실증 근거:**
  - STEP NEXT-77 실증: KB 43 coverages 100% (42 FOUND + 1 FOUND_GLOBAL)
  - Evidence 예시: "최초1회한", "연간 5회", "평생", "재진단암보장개시일 이후"
  - Keywords: "1회한", "최초 1회한", "연간", "재발", "재진단", "반복지급"
  - Highly coverage-specific (97.7% FOUND)

**답변 예시 (근거 포함):**
```
다빈치로봇 암수술비 담보의 경우:
- 최초 1회한 지급됩니다 (재발 시 지급 안 됨)
- 근거: 가입설계서 p.2 "206 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
- 근거: 약관 p.38 "표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ"
```

---

### Q5. 면책기간/대기기간은?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `waiting_period`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 가입설계서, 상품요약서, 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - Keywords: "면책기간", "대기기간", "보장제외기간", "일 경과"
  - Deterministic value 추출: "90일", "30일", "1년" 등

---

### Q6. 감액기간/비율은?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `reduction`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - Keywords: "감액", "지급률", "지급비율", "삭감", "경과기간"
  - Often in tables (table_priority=True)
  - Deterministic value: "50%", "1년", "3년" 등

---

### Q7. 가입 나이 제한은?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `entry_age`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - Keywords: "가입연령", "가입나이", "피보험자 나이", "만 X세"
  - Regex pattern: r"만\s*(\d+)\s*세"
  - Deterministic value: "15세 ~ 65세" 등

---

### Q8. 타사 가입도 영향? (업계 누적 한도)
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `industry_aggregate_limit`
- **Evidence 상태:** FOUND_GLOBAL (100%)
- **근거 문서:** 약관
- **제약 사항:** 고객의 기존 가입 정보 입력 시 정확한 계산 가능
- **실증 근거:**
  - STEP NEXT-77 실증: KB 43 coverages 100% FOUND_GLOBAL (0 FOUND)
  - Evidence 예시: "보험사간 치료비 분담 지급", "비례보상원칙을 적용하여 보험계약별로 보험금을 분할"
  - Keywords: "업계 누적", "타사 가입", "타 보험사", "합산", "통산한도"
  - 100% FOUND_GLOBAL expected: 업계 누적 한도는 product-level/industry-level rule

**답변 예시 (근거 포함):**
```
KB 상품의 경우:
- 다른 보험사에 가입한 실비 상품이 있으면 비례보상 적용됩니다
- 근거: 약관 p.70 "상해·질병으로 인한 의료비 실비를 보상하는 상품에 복수로 가입한 경우
  보험약관에 따라 비례보상원칙을 적용하여 보험계약별로 보험금을 분할하여 지급할 수 있습니다"

※ 정확한 계산을 위해서는 고객님의 기존 가입 정보가 필요합니다.
```

---

### Q9. 보장 개시일은?
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `start_date`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - Keywords: "보장개시일", "보장 개시일", "계약일", "책임개시", "보험개시일"
  - Deterministic value: "계약일", "계약일로부터 90일 경과 후" 등

**진단비 비교 범위 안내:**
```
📌 본 시스템에서 비교 가능한 진단비:
- 암진단비 (유사암 제외)
- 고액암진단비
- 유사암진단비
- 재진단암진단비
- 뇌졸중진단비
- 허혈성심장질환진단비

급성심근경색은 단독 진단비 상품이 없어
본 시스템의 진단비 비교 대상에 포함되지 않습니다.
```

---

### Q10. 어떤 경우 제외? (면책사항)
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `exclusions`
- **Evidence 상태:** FOUND (coverage-specific)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음
- **실증 근거:**
  - STEP 1-5 active (core slot)
  - Keywords: "면책사항", "면책 사항", "보장제외", "보장 제외", "보상하지 않는", "지급하지 않는"
  - Context lines: 10 (넓은 context로 면책 조건 전체 추출)

---

## 2-B. 질문별 판정 근거 (Q11~14 확장)

### Q11. 암직접입원비 보장한도(일수구간)
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `benefit_day_range` (신규 - STEP NEXT-80)
- **Evidence 상태:** FOUND (KB 100% coverage)
- **근거 문서:** 가입설계서, 상품요약서, 약관
- **제약 사항:** 없음 (deterministic pattern 추출 완료)
- **구현 완료 (STEP NEXT-80):**
  - ✅ 대상 담보: "암직접치료입원일당" (A6200)
  - ✅ 신규 슬롯: `benefit_day_range`
    - Value format: "1-120일", "1-180일", "1-365일"
    - Keywords: "입원일당", "입원일수", "최대", "120일", "180일", "365일"
    - Doc priority: 가입설계서 → 상품요약서 → 약관
  - ✅ GATE 적용: G1 (keyword + 일수 패턴), G2 (coverage anchoring), G4 (evidence minimum)
  - ✅ KB 실증: 1/1 coverages (100%)

**출력 형식 (Evidence 필수) - STEP NEXT-80 실증:**
```
보험사 | 상품명 | 담보명 | 보장한도(일수) | 근거(문서/페이지)
-----|------|------|------------|-------------
KB   | 닥터플러스 건강보험 | 암직접치료입원일당 | ✅ 1-180일 | 가입설계서 p.8
Meritz | 알파Plus보장보험 | 암직접치료입원일당(Ⅱ) | ✅ 1-180일 | 가입설계서 p.8
Hyundai | 퍼펙트플러스종합보험 | 암직접치료입원일당 | ⚠️ NEEDS_REVIEW | 사업방법서 p.104
```

**GATE 적용:**
- Evidence Gate: 모든 "보장한도(일수)" 셀 ≥ 1 evidence_ref
- No-Inference Gate: 일수는 문서에서 추출만 (계산 금지)
- Schema Gate: benefit_day_range 슬롯 정의 필수

---

### Q12. 삼성 vs 메리츠 암진단비 비교 + 판단 + 추천
- **판정:** ✅ 가능 (기존 슬롯 + Rule 조합)
- **사용 슬롯:**
  - `start_date` (보장개시일)
  - `waiting_period` (면책기간)
  - `reduction` (감액)
  - `payout_limit` (지급한도)
  - `entry_age` (가입나이)
  - `exclusions` (면책사항)
- **Evidence 상태:** FOUND (core slots active)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** Rule 기반 판단만 허용 (자유 문장 금지)
- **구현 요구사항:**
  - 비교 대상: coverage_title = "암진단비" (유사암 제외 등 포함)
  - Insurer filter: samsung, meritz
  - 슬롯 조합: 위 6개 슬롯 전체 비교
  - 판단/추천: STEP NEXT-74/75 Recommendation Card 형식만 사용

**진단비 비교 범위 안내:**
```
📌 본 시스템에서 비교 가능한 진단비:
- 암진단비 (유사암 제외)
- 고액암진단비
- 유사암진단비
- 재진단암진단비
- 뇌졸중진단비
- 허혈성심장질환진단비

급성심근경색은 단독 진단비 상품이 없어
본 시스템의 진단비 비교 대상에 포함되지 않습니다.
```

**출력 형식 (Evidence 필수):**

**비교 테이블:**
```
항목 | 삼성 | 메리츠 | 근거
----|-----|-------|-----
보장개시일 | 계약일 | 계약일+90일 | [가입설계서 p.X], [약관 p.Y]
면책기간 | 90일 | 90일 | [약관 p.A], [약관 p.B]
감액 | 1년 50% | 없음 | [약관 p.C], [약관 p.D]
지급한도 | 3천만원 | 5천만원 | [가입설계서 p.E], [가입설계서 p.F]
가입나이 | 15-65세 | 20-70세 | [약관 p.G], [약관 p.H]
면책사항 | 자살, 전쟁 | 자살, 전쟁 | [약관 p.I], [약관 p.J]
```

**종합판단 (Rule 기반만):**
```json
{
  "recommendation_card": {
    "winner": "meritz",
    "rule_applied": "RULE_05_PAYOUT_LIMIT_PRIORITY",
    "reasoning": [
      {
        "criterion": "payout_limit",
        "samsung_value": "3천만원",
        "meritz_value": "5천만원",
        "evidence_samsung": {"doc_type": "가입설계서", "page": "E"},
        "evidence_meritz": {"doc_type": "가입설계서", "page": "F"}
      },
      {
        "criterion": "reduction",
        "samsung_value": "1년 50%",
        "meritz_value": "없음",
        "evidence_samsung": {"doc_type": "약관", "page": "C"},
        "evidence_meritz": {"doc_type": "약관", "page": "D"}
      }
    ],
    "free_text": null
  }
}
```

**GATE 적용:**
- Evidence Gate: 모든 비교 셀 ≥ 1 evidence_ref
- No-Inference Gate: Rule catalog만 사용 (자유 판단 금지)
- Deterministic Gate: 동일 입력 → 동일 Rule 적용 → 동일 추천

---

### Q13. 제자리암/경계성종양 보장 비교 (O/X 매트릭스)
- **판정:** ✅ 가능 (증명 완료)
- **사용 슬롯:** `subtype_coverage_map` (신규 - STEP NEXT-81)
- **Evidence 상태:** O/X 명시적 판정 (KB 100%, Meritz 100%)
- **근거 문서:** 가입설계서, 약관
- **제약 사항:** 없음 (명시적 O/X 판정 완료)
- **구현 완료 (STEP NEXT-81):**
  - ✅ 신규 슬롯: `subtype_coverage_map`
    - Structure: `{subtype: {coverage_type: bool}}`
    - Subtypes: "in_situ" (제자리암), "borderline" (경계성종양)
    - Coverage types: "진단비", "수술비", "치료비"
    - Keywords:
      - in_situ: "제자리암", "상피내암", "CIS"
      - borderline: "경계성종양", "경계성신생물"
      - Inclusion: "포함", "보장", "지급"
      - Exclusion: "제외", "보장제외", "지급하지 않는"
    - Doc priority: 가입설계서 → 약관
  - ✅ O/X 판정 규칙: 명시적 보장 문구만 O, 나머지 X (보수적 기준)
  - ✅ KB 실증: 34/34 coverages (100%), 1 O케이스
  - ✅ Meritz 실증: 26/26 coverages (100%), 0 O케이스

**출력 형식 (Evidence 필수):**
```
구분 | 진단비 | 수술비 | 항암치료비 | 표적치료비 | 다빈치수술비
-----|-------|-------|----------|----------|------------
삼성 제자리암 | O [가입설계서 p.X] | O [약관 p.Y] | X [약관 p.Z] | X | X
삼성 경계성종양 | O [약관 p.A] | O [약관 p.B] | X | X | X
메리츠 제자리암 | X [약관 p.C] | O [약관 p.D] | X | X | X
메리츠 경계성종양 | X | X | X | X | X
```

**GATE 적용:**
- Evidence Gate: 모든 O/X 옆에 근거 문서 링크 필수
- No-Inference Gate: O/X는 문서 근거로만 판단 (추론 금지)
- Schema Gate: subtype_coverage_map 슬롯 정의 필수

---

### Q14. 보험료 가성비 Top 4 비교 (정렬)
- **판정:** ⚠️ 조건부 (외부 테이블 필수)
- **사용 슬롯:** 외부 데이터 결합 (문서 슬롯 아님)
- **Evidence 상태:** 외부 테이블 (premium_table, rate_example.xlsx)
- **근거 문서:** premium_table (총보험료/월납), rate_example.xlsx (일반/무해지 비율)
- **제약 사항:** 외부 데이터 연계 필수, 계산식 코드로 고정
- **구현 요구사항:**
  - 외부 테이블:
    - `premium_table`: {insurer, product, variant, coverage, monthly_premium, total_premium}
    - `rate_example.xlsx`: {insurer, product, general_rate, no_refund_rate}
  - 계산 규칙 (고정):
    - 일반형 총납입 = total_premium × general_rate
    - 무해지형 총납입 = total_premium × no_refund_rate (= total_premium if 100%)
    - 월납 동일 비율 적용
  - 정렬: 총납입(무해지형) 오름차순
  - Evidence: 계산식/버전/출처를 evidence_ref로 기록

**출력 형식 (Evidence 필수):**
```
순위 | 보험사 | 상품명 | 총납입(일반) | 총납입(무해지) | 월납(일반) | 월납(무해지) | 근거
----|------|------|----------|-----------|---------|----------|-----
1 | KB | 닥터플러스 | 3,000만원 | 2,500만원 | 25만원 | 20만원 | [premium_table v1.0], [rate_example.xlsx]
2 | 메리츠 | 실속건강 | 3,200만원 | 2,700만원 | 27만원 | 22만원 | [premium_table v1.0], [rate_example.xlsx]
3 | 삼성 | 건강플러스 | 3,500만원 | 3,000만원 | 29만원 | 25만원 | [premium_table v1.0], [rate_example.xlsx]
4 | 한화 | 라이프케어 | 3,800만원 | 3,200만원 | 32만원 | 27만원 | [premium_table v1.0], [rate_example.xlsx]
```

**계산식 Evidence:**
```json
{
  "calculation_formula": {
    "total_premium_general": "total_premium × general_rate",
    "total_premium_no_refund": "total_premium × no_refund_rate",
    "monthly_premium_general": "monthly_premium × general_rate",
    "monthly_premium_no_refund": "monthly_premium × no_refund_rate"
  },
  "data_source": {
    "premium_table": "v1.0",
    "rate_example": "rate_example.xlsx (2026-01)"
  },
  "deterministic_hash": "sha256:abc123..."
}
```

**GATE 적용:**
- Evidence Gate: 모든 금액 셀 + 계산식/출처 명시
- No-Inference Gate: 계산식은 코드로 고정 (임의 계산 금지)
- Schema Gate: 외부 테이블 스키마 정의 필수
- Deterministic Gate: 동일 입력 → 동일 계산 → 동일 해시

**제약 사항:**
- ❌ 보험료 테이블 없으면 답변 불가
- ❌ 임의 할인/할증 적용 금지
- ❌ "예상" 금액 표시 금지
- ✅ 외부 테이블 버전/출처 명시 필수

---

## 3. Capability Boundary 재확인 (요약)

### 🟢 GREEN: 즉시 대응 가능 (11개 질문)

| 질문 | 슬롯 | KB 실증 결과 |
|-----|------|------------|
| Q1 (보장금액) | `payout_limit` | Core slot active |
| Q2 (유병자) | `underwriting_condition` | 100% (30 FOUND + 13 FOUND_GLOBAL) |
| Q3 (단독가입) | `mandatory_dependency` | 100% (5 FOUND + 38 FOUND_GLOBAL) |
| Q4 (재발지급) | `payout_frequency` | 100% (42 FOUND + 1 FOUND_GLOBAL) |
| Q5 (면책기간) | `waiting_period` | Core slot active |
| Q6 (감액) | `reduction` | Core slot active |
| Q7 (가입나이) | `entry_age` | Core slot active |
| Q8 (업계누적) | `industry_aggregate_limit` | 100% (43 FOUND_GLOBAL) |
| Q9 (보장개시) | `start_date` | Core slot active |
| Q10 (면책사항) | `exclusions` | Core slot active |
| Q12 (비교+추천) | Core slots + Rule catalog | Rule-based recommendation |

**즉시 대응 조건:**
- Evidence FOUND or FOUND_GLOBAL
- Gate validation 통과 (G1-G4)
- 약관/요약서/사업방법서 근거 1개 이상

---

### 🟡 YELLOW: 조건부 대응 가능 (1개 질문)

| 질문 | 조건 | 필요 구현 |
|-----|------|----------|
| Q14 (보험료 가성비) | 외부 테이블 필수 | premium_table + rate_example.xlsx 연계 |

**조건부 대응 요구사항:**
- Q14: 외부 데이터 연계 + 계산식 코드화 + Deterministic hash

**완료된 슬롯:**
- ~~Q11 (암직접입원비 일수)~~: ✅ `benefit_day_range` 슬롯 구현 완료 (STEP NEXT-80)
- ~~Q13 (제자리암/경계성종양 O/X)~~: ✅ `subtype_coverage_map` 슬롯 구현 완료 (STEP NEXT-81)

---

### 🔴 RED: 의도적 비대상

아래 질문은 **시스템 범위를 벗어나므로 답변 불가**:

| 질문 유형 | 예시 | 사유 |
|---------|------|------|
| 할인 | "결합 할인 받을 수 있나?" | 마케팅 정책 (약관 근거 없음) |
| 할인 | "가족 할인 있나?" | 마케팅 정책 (약관 근거 없음) |
| 환급/저축 | "만기 환급금은?" | 보장 조건 아님 (금융 상품 설계 요소) |
| 환급/저축 | "해약 환급금은?" | 보장 조건 아님 (금융 상품 설계 요소) |
| 환급/저축 | "저축 효과는?" | 보장 조건 아님 (금융 상품 설계 요소) |
| 마케팅 | "어느 회사가 더 유명?" | 주관적 평가 (약관 근거 없음) |
| 마케팅 | "고객 평가는?" | 주관적 평가 (약관 근거 없음) |
| 보험료 계산 | "내 나이로 보험료는?" | 보험료 테이블 미연계 (향후 확장 가능) |

**Excluded Slots (영구 제외):**
- `discount` (할인)
- `refund_rate` (환급률)
- `family_discount` (가족결합)
- `marketing_phrases` (홍보 문구)

**이유:** 약관 근거 없음, 마케팅/저축 영역, 시스템 정체성과 충돌

---

## 4. Evidence 품질 기준

모든 질문 답변은 아래 기준을 충족:

### 4.1 Evidence 최소 요구사항 (Gate G4)
- ✅ Excerpt length ≥ 15 chars
- ✅ Context는 keyword만 아니라 실제 내용 포함 (≥ 10 chars excluding keyword)
- ✅ Required fields: slot_key, keyword, context, page

### 4.2 Structural Validation (Gate G1)
- ✅ Keyword + structural pattern 동시 충족
- ✅ Min 2 patterns matched for extended slots
- 예: underwriting_condition → "유병자" + "가능"

### 4.3 Coverage Anchoring (Gate G2)
- ✅ FOUND: Coverage-specific evidence (coverage name/code in context)
- ✅ FOUND_GLOBAL: Product-level/global evidence (valid but not coverage-specific)
- ❌ UNKNOWN: Gate 실패 또는 no evidence

### 4.4 Conflict Detection (Gate G3)
- ✅ CONFLICT: 문서 간 값 불일치 → 양쪽 근거 모두 표시
- ✅ Transparency: 고객에게 확인 요청

---

## 5. Document Priority (Evidence 탐색 순서)

각 질문별 우선순위:

| 질문 | 1순위 | 2순위 | 3순위 | 4순위 |
|-----|------|------|------|------|
| Q1 (보장금액) | 가입설계서 | 약관 | 상품요약서 | 사업방법서 |
| Q2 (유병자) | 상품요약서 | 사업방법서 | 가입설계서 | 약관 |
| Q3 (단독가입) | 약관 | 상품요약서 | 사업방법서 | 가입설계서 |
| Q4 (재발지급) | 약관 | 가입설계서 | 상품요약서 | 사업방법서 |
| Q5 (면책기간) | 가입설계서 | 상품요약서 | 약관 | 사업방법서 |
| Q6 (감액) | 약관 | 가입설계서 | 상품요약서 | 사업방법서 |
| Q7 (가입나이) | 가입설계서 | 약관 | 상품요약서 | 사업방법서 |
| Q8 (업계누적) | 약관 | 사업방법서 | 상품요약서 | 가입설계서 |
| Q9 (보장개시) | 가입설계서 | 약관 | 상품요약서 | 사업방법서 |
| Q10 (면책사항) | 약관 | 가입설계서 | 상품요약서 | 사업방법서 |

**우선순위 절대 규칙:**
- 가입설계서 → 상품요약서 → 사업방법서 → 약관 (일반 원칙)
- 단, 질문 유형별로 최적 문서 우선 탐색
- 모든 문서를 순차 탐색하며 evidence 수집

---

## 6. 실증 데이터 요약

### STEP NEXT-77 실증 결과 (KB Only)
- **Insurer:** KB
- **Coverages:** 43
- **Extended Slots:**
  - underwriting_condition: 100% (30 FOUND + 13 FOUND_GLOBAL)
  - mandatory_dependency: 100% (5 FOUND + 38 FOUND_GLOBAL)
  - payout_frequency: 100% (42 FOUND + 1 FOUND_GLOBAL)
  - industry_aggregate_limit: 100% (43 FOUND_GLOBAL)
- **Core Slots:** Step 1-5 active (6 slots)
- **Zero UNKNOWN:** 모든 extended slot에 evidence 존재

### 대표 Coverage 실증 (1건)
- **Coverage:** 일반상해사망(기본) (A1300)
- **Product:** KB닥터플러스건강보험세만기해약환급금미지급형무배
- **Extended Slot Evidences:**
  - underwriting_condition: 3 evidences (상품요약서)
  - mandatory_dependency: 3 evidences (상품요약서 + 사업방법서)
  - payout_frequency: 3 evidences (가입설계서 + 약관)
  - industry_aggregate_limit: 2 evidences (약관)
- **Total:** 10개 슬롯 모두 evidence 포함 (6 core + 4 extended)

---

## 7. 제약 사항 (명시적)

### 7.1 LLM 추론 금지
- ❌ "추정됩니다" / "일반적으로" 표현 금지
- ✅ 모든 답변은 약관/요약서 근거 필수
- ✅ Evidence 0개 = "근거 없음" 명시

### 7.2 근거 제시 필수
- ✅ 답변마다 (문서 타입, 페이지, 문구) 표시
- ✅ Evidence excerpt 최대 200자 (truncate with "...")
- ✅ Keyword + line_num + is_table 정보 포함

### 7.3 CONFLICT 투명화
- ✅ 문서 간 상충 시 양쪽 근거 모두 표시
- ✅ 고객에게 확인 요청
- ✅ 최종 판단은 고객/설계사에게

### 7.4 데이터 범위
- ✅ 현재 실증: KB only (43 coverages)
- ⚠️ 다른 보험사 확대 시 재검증 필요
- ✅ 슬롯 정의는 insurer-agnostic (확장 가능)

---

## 8. Lock 선언

본 문서는 2026-01 기준 보험 비교 시스템의 고객 질문 대응 범위를 고정(Lock)한다.

**적용 범위:**
- 고객 질문 1~10: 모두 ✅ 가능 (증명 완료)
- 할인/환급/마케팅: 모두 ❌ 불가 (의도적 제외)
- 증거 기준: FOUND/FOUND_GLOBAL (GATE G1-G4 통과)

**금지 사항:**
- 본 문서에 포함되지 않은 해석, 추천, 계산, 할인, 환급 관련 응답은 시스템 범위를 벗어난다.
- LLM 추론/보완/생성 금지
- 약관 근거 없는 답변 금지

**변경 조건:**
- 본 문서 변경 시 STEP NEXT-XX 단계로 실증 재수행 필요
- 새로운 슬롯 추가 시 ACTIVE_CONSTITUTION.md Section 10 업데이트 필수
- Evidence 패턴 변경 시 GATE 재검증 필수

---

## 9. Version History

- **1.0** (2026-01-08): Initial lock
  - Based on STEP NEXT-76 (extended slots)
  - Based on STEP NEXT-77 (KB proof of concept)
  - 10 customer questions → 10 ✅ (all GREEN)
  - 0 UNKNOWN for extended slots (KB)

- **1.1** (2026-01-08): STEP NEXT-79 expansion
  - Added Q11-14 (extended coverage)
  - Q11: ✅ 가능 (benefit_day_range 슬롯 완료 - STEP NEXT-80)
  - Q12: ✅ 가능 (기존 슬롯 + Rule)
  - Q13: ✅ 가능 (subtype_coverage_map 슬롯 완료 - STEP NEXT-81)
  - Q14: ⚠️ 조건부 (외부 테이블 필수)
  - Total: 13 ✅ GREEN, 1 ⚠️ YELLOW, 0 ❌ RED

---

## 10. 참조 문서 (SSOT)

1. `docs/ACTIVE_CONSTITUTION.md` - Section 10 (Coverage Slot Extensions)
2. `docs/CAPABILITY_BOUNDARY.md` - GREEN/YELLOW/RED categories
3. `docs/audit/STEP_NEXT_76_COVERAGE_SLOT_EXTENSION.md` - Slot extension spec
4. `docs/audit/STEP_NEXT_77_EXTENDED_SLOT_PROOF.md` - KB proof (100% evidence)
5. `docs/audit/STEP_NEXT_79_IMPLEMENTATION_SUMMARY.md` - Q11-14 expansion spec
6. `data/compare_v1/compare_rows_v1.jsonl` - KB 43 coverages with extended slots

---

**이 문서는 고객·영업·기획 간 기대치 불일치를 차단하기 위한 공식 Lock 문서입니다.**

**마지막 업데이트:** 2026-01-08
**다음 검토일:** 슬롯 추가 또는 보험사 확대 시
