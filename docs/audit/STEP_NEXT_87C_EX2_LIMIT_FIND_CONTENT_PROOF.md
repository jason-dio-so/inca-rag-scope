# STEP NEXT-87C — EX2_LIMIT_FIND Content Contract Proof

**Date**: 2026-01-03
**Status**: ✅ COMPLETE (All tests PASS)

---

## 1. Purpose

Validate that **EX2_LIMIT_FIND** responses follow constitutional rules:

- ✅ Deterministic only (NO LLM)
- ✅ EX2_LIMIT_FIND is for "finding/filtering/difference exploration" ONLY
- ❌ NO recommendation/superiority/value judgement
- ❌ NO EX4 contamination (O/X/△ eligibility judgement)
- ❌ NO EX3 contamination (comprehensive comparison table)
- ✅ 0% coverage_code exposure in UI-facing text
- ✅ refs must use PD:/EV: format

---

## 2. Contract Checks

### 2.1 Forbidden Words (Judgement Leakage)

**Forbidden words** in user-facing text:
- "추천", "비추천", "유리", "불리", "낫", "좋", "나쁘"
- "권장", "비권장", "선택", "최적", "베스트"
- "가입하세요", "가입 권장", "피하세요"

**Checked fields**:
- `.message.title`
- `.message.summary_bullets[*]`
- `.message.bubble_markdown`
- `.message.sections[*].title`
- `.message.sections[*].bullets[*]`
- `.message.sections[*].rows[*].cells[*].text`

### 2.2 Coverage Code Exposure

**Pattern**: `[A-Z]\d{4}_\d` (e.g., A4200_1)

**Rule**: MUST NOT appear in any user-facing text.

### 2.3 EX4 Contamination

**EX4 patterns** (eligibility judgement):
- "보장 가능 여부"
- "보장 가능:"
- "보장 불가"
- O/X/△ as eligibility judgement
- "Unknown.*보장"

**Note**: Mentioning "면책" or "감액" as part of condition explanation is OK.

### 2.4 EX3 Contamination

**EX3 patterns** (comprehensive comparison):
- "비교표" section
- "공통사항 및 유의사항" section
- Comprehensive 2+ insurer comparison table structure

---

## 3. Test Scenarios

### Scenario 1: 보장한도가 다른 상품
**Query**: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"

**Response**:
- Title: "암직접입원비 보장한도 차이 비교"
- Summary: ["samsung의 보장한도가 다릅니다", "다른 값: 1일 1회, 최대 120일"]

**Result**: ✅ PASS

---

### Scenario 2: 대기기간이 다른 보험사
**Query**: "암진단비 담보 중 대기기간이 다른 보험사 찾아줘"

**Response**:
- Title: "암진단비(유사암 제외) 조건 차이 비교"
- Summary: ["samsung의 조건가 다릅니다", "다른 값: 대기: 2년, 면책: 유사암 제외"]

**Result**: ✅ PASS

---

### Scenario 3: 조건이 다른 회사
**Query**: "암진단비 담보 조건이 다른 회사 찾아줘"

**Response**:
- Title: "암진단비(유사암 제외) 조건 차이 비교"
- Summary: ["hanwha의 조건가 다릅니다", "다른 값: 대기: 90일, 면책: 유사암 제외"]

**Result**: ✅ PASS

---

### Scenario 4: 보장한도 차이 (3사)
**Query**: "보장한도 차이 알려줘" (3+ insurers)

**Response**:
- Title: "암진단비(유사암 제외) 보장한도 차이 비교"
- Summary: ["samsung의 보장한도가 다릅니다", "다른 값: 1회한 5000만원"]

**Result**: ✅ PASS

---

### Scenario 5: 감액 조건 필터
**Query**: "유사암진단비에서 감액 조건이 있는 회사만"

**Response**:
- Title: "유사암진단비 조건 차이 비교"
- Summary: ["hanwha의 조건가 다릅니다", "다른 값: 대기: 90일, 감액: 1년 50%"]

**Result**: ✅ PASS

**Note**: "감액" mentioned as condition explanation (NOT eligibility judgement) - OK.

---

### Scenario 6: 납입면제 조건 차이
**Query**: "납입면제 조건이 다른 회사 찾아줘"

**Response**:
- Title: "암진단비(유사암 제외) 조건 차이 비교"
- Summary: ["hanwha의 조건가 다릅니다", "다른 값: 대기: 90일, 면책: 유사암 제외"]

**Result**: ✅ PASS

---

## 4. Test Results

### Overall Summary
```
✅ PASS scenario_1: 보장한도가 다른 상품
✅ PASS scenario_2: 대기기간이 다른 보험사
✅ PASS scenario_3: 조건이 다른 회사
✅ PASS scenario_4: 보장한도 차이 (3사)
✅ PASS scenario_5: 감액 조건 필터
✅ PASS scenario_6: 납입면제 조건 차이

🎉 All scenarios PASSED contract validation
```

### Pytest Output
```bash
$ python -m pytest tests/test_ex2_limit_find_content_contract.py -v

tests/test_ex2_limit_find_content_contract.py::test_ex2_limit_find_contract_validation_function PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_1_limit_difference PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_2_waiting_period_difference PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_3_condition_difference PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_4_limit_difference_multi_insurer PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_5_reduction_condition_filter PASSED
tests/test_ex2_limit_find_content_contract.py::test_scenario_6_waiver_condition_difference PASSED

============================== 7 passed in 0.02s
```

---

## 5. Violations Found

### None

**All 6 scenarios passed with 0 violations.**

No composer changes were needed - EX2_LIMIT_FIND composer already follows constitutional rules.

---

## 6. Constitutional Compliance

### ✅ Confirmed Rules

1. **Deterministic only**: All responses generated without LLM
2. **No judgement**: No forbidden words detected in any scenario
3. **No coverage_code exposure**: 0% coverage code leakage to UI
4. **No EX4 contamination**: No O/X/△ eligibility judgement
5. **No EX3 contamination**: No comprehensive comparison structure
6. **Refs format**: All refs use PD:/EV: prefix (when applicable)

### Response Structure

EX2_LIMIT_FIND responses follow this structure:

1. **Title**: `{coverage_name} {compare_field} 차이 비교`
2. **Summary bullets**: Factual difference summary (NO judgement)
   - Example: "samsung의 보장한도가 다릅니다"
   - Example: "다른 값: 1일 1회, 최대 120일"
3. **Sections**:
   - Section 1: Diff comparison table (보험사, field, 근거)
   - Section 2: Common notes (유의사항)

---

## 7. Definition of Done (DoD)

✅ **All DoD items completed:**

- [x] 6개 시나리오 모두 EX2_LIMIT_FIND 응답이 계약 테스트 PASS
- [x] user-facing text에서 추천/우열/판단 문구 0%
- [x] EX3/EX4 혼입 0%
- [x] coverage_code 노출 0%
- [x] docs/audit 증적 문서 생성
- [x] pytest green

---

## 8. Files Modified/Created

### Created
- `tests/test_ex2_limit_find_content_contract.py` - Contract validation tests
- `tests/manual_test_ex2_limit_find_samples.py` - Sample response generator
- `tests/ex2_limit_find_samples.json` - Response samples (JSON)
- `docs/audit/STEP_NEXT_87C_EX2_LIMIT_FIND_CONTENT_PROOF.md` - This document

### Modified
- None (no composer changes needed)

---

## 9. Next Steps

None required - EX2_LIMIT_FIND content contract is **LOCKED** and verified.

Future changes to `apps/api/response_composers/ex2_limit_find_composer.py` MUST pass these contract tests.

---

## 10. References

- **SSOT**: `docs/ui/INTENT_ROUTER_RULES.md` (EX2_LIMIT_FIND section)
- **Composer**: `apps/api/response_composers/ex2_limit_find_composer.py`
- **Handler**: `apps/api/chat_handlers_deterministic.py`
- **Test**: `tests/test_ex2_limit_find_content_contract.py`
- **Samples**: `tests/manual_test_ex2_limit_find_samples.py`

---

**STEP NEXT-87C COMPLETE** ✅
