# STEP NEXT-96 — EX2_DETAIL 고객 질문 정렬 (Customer-First KPI Ordering) LOCK

**Status**: ✅ LOCKED (2026-01-03)

---

## 목적 (WHY)

EX2_DETAIL(담보 설명 전용 모드)의 표현 순서를 **고객 질문 기준**으로 재정렬하여
**"정확하지만 답이 안 되는 화면"** 문제를 해결한다.

### 문제 정의

**고객 질문**:
> "삼성화재 암진단비 보장금액이 얼마인가요?"

**BEFORE (STEP NEXT-86)**:
```markdown
## 보장 요약
- **보장한도**: 보험기간 중 1회
- **지급유형**: 정액형 (일시금)
- **근거**: [근거 보기](EV:samsung:A4200_1:01)
```

**문제점**:
- 보장금액(3,000만원)이 표시되지 않음
- 고객의 1차 질문("얼마 받나요?")에 즉시 답하지 못함

**AFTER (STEP NEXT-96)**:
```markdown
## 보장 요약
- **보장금액**: 3,000만원
  · 지급 조건: 암진단비(유사암 제외) 해당 시
- **보장한도**: 보험기간 중 1회
- **지급유형**: 정액형 (일시금)
- **근거**: [근거 보기](EV:samsung:A4200_1:01)
```

**해결**:
- ✅ 보장금액이 첫 번째 KPI로 노출
- ✅ "얼마 받는지" 3초 내 인지 가능

---

## 설계 원칙 (CONSTITUTION)

### 🚫 금지 사항

- ❌ **비즈니스 로직 변경 금지**
  - Handler 로직 변경 금지
  - 데이터 로딩 로직 변경 금지
  - KPI 추출 규칙 변경 금지
- ❌ **판단/추천/우열 표현 금지**
  - EX2_DETAIL = 설명 전용 (NO 비교/판단)
- ❌ **금액 계산 또는 추론 금지**
  - 표시된 금액은 `card_data.amount` 원본만
- ❌ **coverage_code UI 노출 금지**
  - Refs (PD:/EV:) 내에서만 허용
- ❌ **EX3/EX4 로직 차용 금지**
  - EX2는 EX2 헌법만 준수

### ✅ 허용 사항

- ✅ **View Layer ONLY 변경**
  - Bubble markdown 내 섹션 순서 변경
  - 보장 요약 내부 KPI 노출 순서 변경
- ✅ **Deterministic ONLY**
  - NO LLM usage
- ✅ **Refs (PD:/EV:) 기반**
  - STEP NEXT-90/91/92 정책 유지

---

## 구현 내용 (WHAT)

### 1️⃣ 보장 요약 KPI 순서 재정렬

**BEFORE**:
1. 보장한도 (횟수/기간)
2. 지급유형

**AFTER (Customer-First)**:
1. **보장금액** ← NEW (있을 경우 최우선)
2. 보장한도 (횟수/기간)
3. 지급유형

**조건**:
- 보장금액이 있을 경우 (`amount` field exists and != "명시 없음")
- 보장금액이 없으면 기존 순서 유지 (한도부터)

---

### 2️⃣ 보장금액 표시 규칙

**Data Source**:
```python
amount = card_data.get("amount")  # e.g., "3,000만원"
```

**표현 형식**:
```markdown
- **보장금액**: 3,000만원
  · 지급 조건: {coverage_name} 해당 시
```

**조건**:
- `amount` field가 존재하고
- `amount != "명시 없음"` 일 때만 표시

**Fallback**:
- `amount` 없음 → **보장금액 항목 미표시**
- 기존 EX2_DETAIL과 동일 (보장한도부터 시작)

---

### 3️⃣ 섹션 순서 (전체)

**BEFORE/AFTER 모두 동일** (섹션 자체는 변경 없음):
1. 핵심 요약
2. 보장 요약 (내부 KPI 순서만 변경)
3. 조건 요약
4. 근거 자료

---

## 구현 위치 (WHERE)

**파일**: `apps/api/response_composers/ex2_detail_composer.py`

**수정 범위**:
- `_build_bubble_markdown()` method ONLY
- Lines 181-209 (보장 요약 section)

**변경 사항**:
```python
# STEP NEXT-96: Extract 보장금액 from card_data.amount (proposal_facts)
amount = card_data.get("amount")  # e.g., "3000만원"

# STEP NEXT-96: 보장금액 우선 표시 (있을 경우)
if amount and amount != "명시 없음":
    lines.append(f"- **보장금액**: {amount}")
    lines.append(f"  · 지급 조건: {display_name} 해당 시")

# 보장한도 (횟수/기간 제한)
lines.append(f"- **보장한도**: {limit_summary}")

# 지급유형
lines.append(f"- **지급유형**: {payment_type}")
```

**불변 영역**:
- `compose()` method
- `_build_kpi_summary_section()` method
- `_build_kpi_condition_section()` method
- `_build_evidence_section()` method
- Handler logic (NO changes)

---

## 검증 시나리오 (TEST)

### Case A — 고객 질문 중심 (보장금액 있음)

**입력**:
```python
card_data = {
    "amount": "3,000만원",  # 보장금액 존재
    "kpi_summary": {"limit_summary": "보험기간 중 1회", "payment_type": "정액형"}
}
```

**기대**:
- ✅ 보장금액이 보장 요약의 **첫 번째 항목**으로 노출
- ✅ "얼마 받는지" 즉시 인지 가능
- ✅ Ordering: 보장금액 → 보장한도 → 지급유형

**테스트**: `test_case_a_amount_first_in_kpi_summary` ✅ PASS

---

### Case B — 금액 없는 담보

**입력**:
```python
card_data = {
    "amount": "명시 없음",  # No amount
    "kpi_summary": {"limit_summary": "보험기간 중 1회", "payment_type": "정액형"}
}
```

**기대**:
- ❌ 보장금액 항목 **미표시**
- ✅ 기존 EX2_DETAIL와 동일 (보장한도부터 시작)

**테스트**: `test_case_b_no_amount_fallback_to_original` ✅ PASS

---

### Case C — 기존 계약 테스트 (NO Regression)

**검증 항목**:
1. ❌ NO coverage_code exposure (A4200_1)
2. ❌ NO raw text in bubble
3. ✅ Deterministic ONLY (same input → same output)
4. ✅ Payment type translation (LUMP_SUM → "정액형 (일시금)")

**테스트**:
- `test_case_c_no_coverage_code_exposure` ✅ PASS
- `test_case_c_no_raw_text_in_bubble` ✅ PASS
- `test_case_c_deterministic_only_no_llm` ✅ PASS
- `test_case_c_payment_type_translation` ✅ PASS

---

## 테스트 결과 (RESULTS)

### 신규 테스트 (STEP NEXT-96)

**파일**: `tests/test_step_next_96_customer_first_order.py`

**결과**: ✅ **8/8 PASSED** (2026-01-03)

| Test | Status | Description |
|------|--------|-------------|
| `test_case_a_amount_first_in_kpi_summary` | ✅ PASS | 보장금액 최우선 표시 |
| `test_case_b_no_amount_fallback_to_original` | ✅ PASS | 금액 없을 시 fallback |
| `test_case_b_none_amount_fallback` | ✅ PASS | amount=None 처리 |
| `test_case_c_no_coverage_code_exposure` | ✅ PASS | NO coverage_code |
| `test_case_c_no_raw_text_in_bubble` | ✅ PASS | NO raw text |
| `test_case_c_deterministic_only_no_llm` | ✅ PASS | Deterministic |
| `test_case_c_payment_type_translation` | ✅ PASS | Payment type 번역 |
| `test_full_compose_with_amount_first` | ✅ PASS | Full integration |

---

### 기존 테스트 (Regression Check)

**파일**: `tests/test_ex2_bubble_contract.py`

**결과**: ✅ **7/7 PASSED** (2026-01-03, NO regression)

| Test | Status | Description |
|------|--------|-------------|
| `test_no_coverage_code_exposure_in_bubble` | ✅ PASS | NO coverage_code |
| `test_bubble_has_4_sections` | ✅ PASS | 4-section structure |
| `test_refs_use_pd_ev_prefix` | ✅ PASS | PD:/EV: refs |
| `test_표현_없음_when_missing_kpi_summary` | ✅ PASS | "표현 없음" usage |
| `test_근거_없음_when_missing_kpi_condition` | ✅ PASS | "근거 없음" usage |
| `test_no_raw_text_in_bubble` | ✅ PASS | NO raw text |
| `test_sanitize_no_coverage_code_util` | ✅ PASS | Sanitization |

**결론**: ✅ **NO REGRESSION** (기존 계약 100% 유지)

---

## DoD (Definition of Done) 체크리스트

- [x] EX2_DETAIL 화면에서 고객 질문 "얼마 받나요?"에 **3초 내 답 가능**
- [x] 헌법 위반 **0건** (NO comparison/judgment/coverage_code exposure)
- [x] 기존 테스트 **전부 PASS** (7/7 기존 + 8/8 신규 = 15/15 ALL PASS)
- [x] EX3/EX4 출력 변화 **0건** (EX2 ONLY 변경)
- [x] Handler/data logic 변경 **0건** (View layer ONLY)
- [x] SSOT 문서 작성 완료 (본 파일)

---

## 예시 출력 (EXAMPLE OUTPUT)

### Before (STEP NEXT-86)

```markdown
## 핵심 요약

- **보험사**: samsung
- **담보명**: 암진단비(유사암 제외)
- **데이터 기준**: 가입설계서

## 보장 요약

- **보장한도**: 보험기간 중 1회
- **지급유형**: 정액형 (일시금)
- **근거**: [근거 보기](EV:samsung:A4200_1:01)

## 조건 요약

- **감액**: 1년 미만 50% ([근거 보기](EV:samsung:A4200_1:02))
- **대기기간**: 90일
- **면책**: 계약일 이전 발생 질병
- **갱신**: 비갱신형

## 근거 자료

상세 근거는 "근거 보기" 링크를 클릭하시면 확인하실 수 있습니다.
```

**문제점**: 고객이 가장 궁금한 "보장금액 3,000만원"이 표시 안 됨

---

### After (STEP NEXT-96)

```markdown
## 핵심 요약

- **보험사**: samsung
- **담보명**: 암진단비(유사암 제외)
- **데이터 기준**: 가입설계서

## 보장 요약

- **보장금액**: 3,000만원
  · 지급 조건: 암진단비(유사암 제외) 해당 시
- **보장한도**: 보험기간 중 1회
- **지급유형**: 정액형 (일시금)
- **근거**: [근거 보기](EV:samsung:A4200_1:01)

## 조건 요약

- **감액**: 1년 미만 50% ([근거 보기](EV:samsung:A4200_1:02))
- **대기기간**: 90일
- **면책**: 계약일 이전 발생 질병
- **갱신**: 비갱신형

## 근거 자료

상세 근거는 "근거 보기" 링크를 클릭하시면 확인하실 수 있습니다.
```

**해결**: ✅ 보장금액이 첫 번째 항목으로 표시 (고객 질문에 즉시 답)

---

## Constitutional Guarantees (헌법 준수 검증)

### 1. NO Business Logic Change

**검증**:
- ✅ Handler logic unchanged (NO changes to `compose()` parameters)
- ✅ Data loading unchanged (NO changes to `card_data` structure)
- ✅ KPI extraction unchanged (NO changes to `kpi_summary`/`kpi_condition` extraction)

**증거**: Git diff shows ONLY `_build_bubble_markdown()` method changes

---

### 2. NO Comparison/Recommendation/Judgment

**검증**:
- ❌ NO "더 좋다", "추천", "우월" 표현
- ❌ NO 보험사 간 비교
- ❌ NO 금액 계산/추론

**증거**:
- Bubble markdown contains ONLY factual KPI display
- NO comparative language in output
- NO value judgment

---

### 3. NO Coverage Code Exposure

**검증**:
- ❌ NO bare coverage_code (A4200_1) outside of refs
- ✅ Refs (PD:/EV:) preserved

**증거**: `test_case_c_no_coverage_code_exposure` PASS

---

### 4. View Layer ONLY

**검증**:
- ✅ ONLY bubble_markdown ordering changed
- ✅ NO handler method signature changes
- ✅ NO data model changes

**증거**:
- Git diff: 30 lines changed (all in `_build_bubble_markdown()`)
- NO changes to `apps/api/chat_handlers_deterministic.py`
- NO changes to `core/compare_types.py`

---

## 관련 문서 (REFERENCES)

- **STEP NEXT-86**: EX2_DETAIL Lock (담보 설명 전용 모드)
  - `docs/ui/STEP_NEXT_86_EX2_LOCK.md`
- **STEP NEXT-90/91/92**: Amount/Filter/Display Policies
  - Refs 기반 표시 정책
- **EX2_DETAIL Composer**: `apps/api/response_composers/ex2_detail_composer.py`
- **Contract Tests**: `tests/test_ex2_bubble_contract.py` (7 tests)

---

## 변경 이력 (CHANGELOG)

- **2026-01-03**: STEP NEXT-96 구현 완료 및 LOCK
  - 보장금액 customer-first ordering 적용
  - 신규 테스트 8개 추가 (ALL PASS)
  - 기존 테스트 7개 회귀 검증 (ALL PASS, NO regression)
  - View layer ONLY 변경 (NO business logic change)
  - SSOT 문서 작성 (본 파일)

---

**END OF LOCK**
