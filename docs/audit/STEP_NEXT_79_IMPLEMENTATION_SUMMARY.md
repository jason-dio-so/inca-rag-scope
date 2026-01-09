# STEP NEXT-79: Customer Question 11-14 Coverage Expansion - Implementation Summary

**Date:** 2026-01-08
**Status:** 🔒 LOCKED (Specification Only)
**Implementation:** ⚠️ CONDITIONAL (Requires slot extensions)

---

## 0. Executive Summary

Defined coverage expansion for customer questions Q11-14 within existing evidence-based, zero-LLM, rule-based pipeline.

**Coverage Status:**
- **Q11 (암직접입원비 일수):** ⚠️ YELLOW - 신규 슬롯 필요
- **Q12 (비교 + 추천):** ✅ GREEN - 기존 슬롯 + Rule 조합
- **Q13 (제자리암/경계성종양 O/X):** ⚠️ YELLOW - Subtype 슬롯 필요
- **Q14 (보험료 가성비):** ⚠️ YELLOW - 외부 테이블 필수

**Absolute Rules:**
- ❌ NO LLM inference
- ❌ NO arbitrary text generation
- ❌ NO values without evidence
- ✅ Document/table source required for every output
- ✅ Maintain Step1-Step5 structure (extension only)

---

## 1. Q11: 암직접입원비 보장한도(일수구간)

### 1.1 Requirement
비교 대상: "암직접입원비" 담보의 보장 일수 구간 추출

### 1.2 New Slot Definition

**Slot Name:** `benefit_day_range`

**Purpose:** 일당 입원비 보장 일수 구간

**Value Format:**
- Type: `string`
- Pattern: `r"(\d+)-(\d+)일"` (e.g., "1-120일", "1-180일", "1-365일")
- Multiple ranges: `["1-120일: 5만원", "121-180일: 3만원"]`

**Keywords:**
- "일당", "입원일수", "1일부터", "X일까지"
- "120일", "180일", "365일"
- "입원", "암직접입원", "암입원"

**Evidence Patterns:**
```python
"benefit_day_range": EvidencePattern(
    slot_key="benefit_day_range",
    keywords=[
        "일당", "입원일수", "1일부터", "일까지",
        "120일", "180일", "365일",
        "입원", "암직접입원"
    ],
    context_lines=5,
    table_priority=True  # 일수 구간은 테이블에 자주 나타남
)
```

**Document Priority:** 가입설계서 → 상품요약서 → 약관

**GATE Requirements:**
- G1 (Structure): keyword ("일당" or "입원일수") + 일수 패턴 (r"\d+일")
- G2 (Anchoring): Coverage name "암직접입원비" in context
- G4 (Minimum): Excerpt ≥ 15 chars

### 1.3 Coverage Filter
- Target: `coverage_title LIKE '%암직접입원%'` OR `coverage_code IN [...]`
- Apply filter before slot extraction

### 1.4 Output Schema

```python
{
  "insurer_key": "kb",
  "product_key": "kb__닥터플러스",
  "coverage_title": "암직접입원비",
  "benefit_day_range": {
    "status": "FOUND",
    "value": "1-120일",
    "evidences": [
      {
        "doc_type": "가입설계서",
        "page": 4,
        "excerpt": "암직접입원비: 1일부터 120일까지 1일당 5만원 지급",
        "locator": {"keyword": "1일부터", "line_num": 45, "is_table": true}
      }
    ]
  }
}
```

### 1.5 DoD (Definition of Done)
- [ ] `benefit_day_range` 슬롯 정의 in `extended_slot_schema.py`
- [ ] Evidence pattern 추가 in `evidence_patterns.py`
- [ ] GATE G1 structural signals 추가 in `gates.py`
- [ ] CompareRow model 업데이트 (benefit_day_range 필드)
- [ ] 1개 보험사 실증 (FOUND rate ≥ 50% for "암직접입원비" coverages)

---

## 2. Q12: 삼성 vs 메리츠 암진단비 비교 + 판단 + 추천

### 2.1 Requirement
기존 슬롯 조합으로 두 보험사 "암진단비" 담보 비교 + Rule 기반 추천

### 2.2 Implementation

**Status:** ✅ GREEN (기존 인프라 사용)

**Used Slots:**
- `start_date`
- `waiting_period`
- `reduction`
- `payout_limit`
- `entry_age`
- `exclusions`

**Coverage Filter:**
- Insurer: `insurer_key IN ['samsung', 'meritz']`
- Coverage: `coverage_title LIKE '%암진단비%'`

**Comparison Logic:**
1. Extract 6 slots for both insurers (Step3 → Step4)
2. Build comparison table (slot-by-slot)
3. Apply STEP NEXT-74/75 Rule catalog for recommendation

**Rule Catalog Example:**
```python
RULE_05_PAYOUT_LIMIT_PRIORITY = {
  "rule_id": "RULE_05",
  "priority": 5,
  "criterion": "payout_limit",
  "direction": "higher_is_better",
  "weight": 0.4
}

RULE_07_REDUCTION_PENALTY = {
  "rule_id": "RULE_07",
  "priority": 7,
  "criterion": "reduction",
  "direction": "lower_is_better",  # 감액 없음 = better
  "weight": 0.3
}
```

**Output Format:**
```json
{
  "comparison_table": {
    "samsung": {
      "start_date": {"value": "계약일", "evidence": {...}},
      "waiting_period": {"value": "90일", "evidence": {...}},
      "reduction": {"value": "1년 50%", "evidence": {...}},
      "payout_limit": {"value": "3천만원", "evidence": {...}},
      "entry_age": {"value": "15-65세", "evidence": {...}},
      "exclusions": {"value": "자살, 전쟁", "evidence": {...}}
    },
    "meritz": {
      "start_date": {"value": "계약일+90일", "evidence": {...}},
      "waiting_period": {"value": "90일", "evidence": {...}},
      "reduction": {"value": "없음", "evidence": {...}},
      "payout_limit": {"value": "5천만원", "evidence": {...}},
      "entry_age": {"value": "20-70세", "evidence": {...}},
      "exclusions": {"value": "자살, 전쟁", "evidence": {...}}
    }
  },
  "recommendation_card": {
    "winner": "meritz",
    "rules_applied": ["RULE_05", "RULE_07"],
    "score_samsung": 65,
    "score_meritz": 85,
    "reasoning": [
      {
        "rule": "RULE_05_PAYOUT_LIMIT_PRIORITY",
        "samsung_value": "3천만원",
        "meritz_value": "5천만원",
        "advantage": "meritz",
        "evidence_samsung": {...},
        "evidence_meritz": {...}
      },
      {
        "rule": "RULE_07_REDUCTION_PENALTY",
        "samsung_value": "1년 50%",
        "meritz_value": "없음",
        "advantage": "meritz",
        "evidence_samsung": {...},
        "evidence_meritz": {...}
      }
    ],
    "free_text": null  # 자유 서술 금지
  }
}
```

### 2.3 GATE Requirements
- Evidence Gate: 모든 비교 셀 ≥ 1 evidence_ref
- No-Inference Gate: Rule catalog만 사용 (자유 판단 금지)
- Deterministic Gate: 동일 입력 → 동일 Rule 적용 → 동일 추천

### 2.4 DoD
- [x] Existing slots active (no new implementation)
- [x] STEP NEXT-74/75 Rule catalog available
- [x] Recommendation card schema defined
- [ ] 삼성 vs 메리츠 "암진단비" 1건 실증

---

## 3. Q13: 제자리암/경계성종양 보장 비교 (O/X 매트릭스)

### 3.1 Requirement
Subtype별 coverage type 보장 여부를 O/X 매트릭스로 표시

### 3.2 New Slot Definition

**Slot Name:** `subtype_coverage_map`

**Purpose:** 암 subtype별 coverage type 보장 여부 매핑

**Value Format:**
```python
{
  "in_situ": {  # 제자리암
    "진단비": True,
    "수술비": True,
    "항암치료비": False,
    "표적치료비": False,
    "다빈치수술비": False
  },
  "borderline": {  # 경계성종양
    "진단비": True,
    "수술비": False,
    "항암치료비": False,
    "표적치료비": False,
    "다빈치수술비": False
  }
}
```

**Keywords:**
- Subtypes:
  - in_situ: "제자리암", "상피내암", "CIS"
  - borderline: "경계성종양", "경계성신생물"
- Coverage types: "진단비", "수술비", "항암치료비", "표적치료비", "다빈치수술비"
- Inclusion: "포함", "보장", "지급"
- Exclusion: "제외", "보장제외", "지급하지 않는"

**Evidence Patterns:**
```python
"subtype_coverage_map": EvidencePattern(
    slot_key="subtype_coverage_map",
    keywords=[
        # Subtypes
        "제자리암", "상피내암", "CIS",
        "경계성종양", "경계성신생물",
        # Coverage types
        "진단비", "수술비", "항암치료비", "표적치료비", "다빈치수술비",
        # Inclusion/Exclusion
        "포함", "보장", "지급", "제외", "보장제외"
    ],
    context_lines=15,  # Wide context for subtype + coverage type matching
    table_priority=True
)
```

**Document Priority:** 가입설계서 → 약관

**GATE Requirements:**
- G1 (Structure): subtype keyword + coverage type keyword + inclusion/exclusion keyword
- G2 (Anchoring): Coverage title in context (e.g., "암진단비", "암수술비")
- G4 (Minimum): Excerpt ≥ 15 chars

### 3.3 Extraction Logic

**Step 1:** Detect subtype mention
- Search for "제자리암" or "경계성종양" in context

**Step 2:** Detect coverage type
- Search for "진단비", "수술비", etc. in same context window

**Step 3:** Determine inclusion/exclusion
- If "포함" or "보장" → True
- If "제외" or "보장제외" → False
- If no explicit mention → UNKNOWN

**Step 4:** Create evidence reference
- doc_type, page, excerpt with subtype + coverage type + inclusion/exclusion

### 3.4 Output Schema

```python
{
  "insurer_key": "samsung",
  "product_key": "samsung__건강플러스",
  "coverage_title": "암진단비",
  "subtype_coverage_map": {
    "status": "FOUND",
    "value": {
      "in_situ": {
        "진단비": True,
        "evidence": {
          "doc_type": "가입설계서",
          "page": 5,
          "excerpt": "제자리암 진단 시 진단비 지급 (보험가입금액의 10%)"
        }
      },
      "borderline": {
        "진단비": True,
        "evidence": {
          "doc_type": "약관",
          "page": 23,
          "excerpt": "경계성종양 진단 시 진단비 보장 포함"
        }
      }
    }
  }
}
```

### 3.5 O/X Matrix Display

```
구분 | 진단비 | 수술비 | 항암치료비 | 표적치료비 | 다빈치수술비
-----|-------|-------|----------|----------|------------
삼성 제자리암 | O [가입설계서 p.5] | O [약관 p.8] | X [약관 p.10] | X | X
삼성 경계성종양 | O [약관 p.23] | O [약관 p.24] | X | X | X
메리츠 제자리암 | X [약관 p.15] | O [약관 p.16] | X | X | X
메리츠 경계성종양 | X | X | X | X | X
```

**Rules:**
- O/X 옆에 근거 문서 링크 필수
- Evidence 없으면 "-" (UNKNOWN) 표시
- X인 경우 제외 근거 명시 필수

### 3.6 DoD
- [ ] `subtype_coverage_map` 슬롯 정의
- [ ] Evidence pattern 추가 (wide context, table priority)
- [ ] GATE G1 structural signals 추가
- [ ] Extraction logic 구현 (subtype + coverage type + inclusion/exclusion)
- [ ] 1개 보험사 2개 subtype 실증 (in_situ, borderline)

---

## 4. Q14: 보험료 가성비 Top 4 비교 (정렬)

### 4.1 Requirement
외부 테이블 결합으로 보험료 계산 후 가성비 순 정렬

### 4.2 External Data Requirements

**Table 1: `premium_table`**
```python
{
  "insurer_key": "kb",
  "product_key": "kb__닥터플러스",
  "variant_key": "default",
  "coverage_title": "암진단비",
  "monthly_premium": 25000,  # 월납 (원)
  "total_premium": 6000000,  # 총납입 (원)
  "premium_period": 20,  # 납입기간 (년)
}
```

**Table 2: `rate_example.xlsx`**
```
insurer | product | general_rate | no_refund_rate
--------|---------|--------------|---------------
KB      | 닥터플러스 | 0.85         | 1.00
삼성     | 건강플러스 | 0.90         | 1.00
메리츠   | 실속건강  | 0.80         | 1.00
한화     | 라이프케어 | 0.88         | 1.00
```

### 4.3 Calculation Rules (FIXED)

**공식 (코드로 고정):**
```python
# 일반형 총납입
total_premium_general = total_premium * general_rate

# 무해지형 총납입 (일반적으로 no_refund_rate = 1.00)
total_premium_no_refund = total_premium * no_refund_rate

# 월납 동일 비율 적용
monthly_premium_general = monthly_premium * general_rate
monthly_premium_no_refund = monthly_premium * no_refund_rate
```

**정렬 기준:**
- Primary: `total_premium_no_refund` 오름차순 (가격 낮은 순)
- Secondary: `total_premium_general` 오름차순

### 4.4 Evidence Requirements

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
    "premium_table": {
      "version": "v1.0",
      "last_updated": "2026-01-08",
      "schema_hash": "sha256:abc123..."
    },
    "rate_example": {
      "file": "rate_example.xlsx",
      "version": "2026-01",
      "schema_hash": "sha256:def456..."
    }
  },
  "deterministic_hash": "sha256:xyz789..."  # 입력 → 출력 재현성 보장
}
```

### 4.5 Output Schema

```python
{
  "comparison_type": "premium_value_ranking",
  "ranking": [
    {
      "rank": 1,
      "insurer_key": "kb",
      "product_key": "kb__닥터플러스",
      "coverage_title": "암진단비",
      "total_premium_general": 5100000,  # 6M × 0.85
      "total_premium_no_refund": 6000000,  # 6M × 1.00
      "monthly_premium_general": 21250,  # 25K × 0.85
      "monthly_premium_no_refund": 25000,  # 25K × 1.00
      "evidence": {
        "premium_table": {"version": "v1.0", "row_hash": "..."},
        "rate_example": {"version": "2026-01", "row": 1},
        "calculation_formula": {...}
      }
    },
    {
      "rank": 2,
      "insurer_key": "meritz",
      ...
    },
    ...
  ],
  "total_compared": 4,
  "calculation_timestamp": "2026-01-08T10:00:00Z"
}
```

### 4.6 GATE Requirements

- **Evidence Gate:** 모든 금액 셀 + 계산식/출처 명시
- **No-Inference Gate:** 계산식 코드로 고정 (임의 계산 금지)
- **Schema Gate:** 외부 테이블 스키마 정의 필수
- **Deterministic Gate:** 동일 입력 → 동일 계산 → 동일 해시

### 4.7 Constraints

**금지 사항:**
- ❌ 보험료 테이블 없으면 답변 불가 ("데이터 없음" 명시)
- ❌ 임의 할인/할증 적용 금지
- ❌ "예상" 금액 표시 금지 (정확한 테이블 값만)
- ❌ 자유 서술 추가 금지

**필수 사항:**
- ✅ 외부 테이블 버전/출처 명시
- ✅ 계산식 코드 공개
- ✅ Deterministic hash 제공

### 4.8 DoD
- [ ] `premium_table` 스키마 정의
- [ ] `rate_example.xlsx` 스키마 정의
- [ ] 계산 로직 코드화 (고정된 함수)
- [ ] Deterministic hash 생성 로직
- [ ] 4개 보험사 보험료 비교 1건 실증

---

## 5. Common GATES (HARD)

All Q11-14 must pass these gates:

### 5.1 Evidence Gate
- **Rule:** 모든 셀 ≥ 1 evidence_ref
- **Violation:** Exit code 2 (HARD FAIL)

### 5.2 No-Inference Gate
- **Rule:** 계산/비교는 규칙만 허용 (LLM 추론 금지)
- **Allowed:** 코드로 정의된 계산식, Rule catalog
- **Forbidden:** 자유 판단, "추정", "일반적으로"
- **Violation:** Exit code 2

### 5.3 Schema Gate
- **Rule:** 미정의 슬롯 출력 시 FAIL
- **Required:** 슬롯 정의 in `extended_slot_schema.py`
- **Violation:** Exit code 2

### 5.4 Deterministic Gate
- **Rule:** 동일 입력 → 동일 해시
- **Implementation:** SHA256(input_params + calculation_formula + data_version)
- **Purpose:** 재현성 보장
- **Violation:** Warning (not HARD FAIL, but logged)

---

## 6. Implementation Checklist

### Q11 (암직접입원비 일수)
- [ ] Slot: `benefit_day_range` 정의
- [ ] Evidence pattern 추가
- [ ] GATE G1 structural signals 추가
- [ ] Coverage filter 구현
- [ ] 1개 보험사 실증

### Q12 (비교 + 추천)
- [x] Existing slots active
- [x] Rule catalog available (STEP NEXT-74/75)
- [ ] 삼성 vs 메리츠 실증

### Q13 (제자리암/경계성종양 O/X)
- [ ] Slot: `subtype_coverage_map` 정의
- [ ] Evidence pattern 추가 (wide context)
- [ ] Extraction logic 구현 (subtype + coverage type + inclusion/exclusion)
- [ ] O/X matrix display 로직
- [ ] 2개 보험사 × 2개 subtype 실증

### Q14 (보험료 가성비)
- [ ] External table: `premium_table` 스키마 정의
- [ ] External table: `rate_example.xlsx` 스키마 정의
- [ ] 계산 로직 코드화
- [ ] Deterministic hash 구현
- [ ] 4개 보험사 비교 실증

---

## 7. Lock Declaration

본 문서는 STEP NEXT-79 구현 사양을 고정(Lock)한다.

**적용 범위:**
- Q11-14 coverage expansion
- 증거 기반 출력 필수
- 자유 서술 0건
- GATE 100% 적용

**금지 사항:**
- LLM 추론/보완/생성 금지
- 약관/테이블 근거 없는 답변 금지
- 임의 계산/할인/할증 금지

**구현 조건:**
- Q11, Q13: 슬롯 정의 + Evidence 패턴 + GATE 추가 후 실증
- Q12: 기존 인프라 사용 (Rule catalog)
- Q14: 외부 테이블 연계 + 계산식 코드화 후 실증

**변경 조건:**
- 본 문서 변경 시 STEP NEXT-XX 단계로 실증 재수행 필요
- 새로운 슬롯 추가 시 ACTIVE_CONSTITUTION.md Section 10 업데이트 필수

---

## 8. References

1. `docs/ACTIVE_CONSTITUTION.md` - Section 10 (Slot extensions)
2. `docs/CUSTOMER_QUESTION_COVERAGE.md` - Q11-14 definitions
3. `pipeline/step1_summary_first/extended_slot_schema.py` - Slot registry
4. `pipeline/step3_evidence_resolver/evidence_patterns.py` - Evidence patterns
5. `pipeline/step3_evidence_resolver/gates.py` - GATE validation logic

---

**이 문서는 Q11-14 구현 사양서입니다. 구현 없이 사양만 Lock됩니다.**

**마지막 업데이트:** 2026-01-08
**구현 상태:** ⚠️ PENDING (슬롯 정의 필요)
