# STEP NEXT-95 — Coverage Grouping Runtime Proof & EX3 확장 검증 (LOCK)

**Status**: ✅ LOCKED (2026-01-03)

---

## 목적 (WHY)

STEP NEXT-94에서 구현된 **Coverage Grouping UX(담보 군집화)**가:
- EX4_ELIGIBILITY에 실제로 적용되었는지
- Runtime 기준으로 문제 없이 동작하는지
- EX3_COMPARE 적용 여부가 명시적으로 문서화되었는지

를 **증적(documented proof)**으로 확정한다.

⚠️ **이번 STEP은 기능 추가가 아니라 "검증 + 락" 단계**

---

## 범위 (SCOPE)

### ✅ 포함

1. **EX4_ELIGIBILITY**: Coverage Grouping runtime 검증
2. **EX3_COMPARE**: Grouping 적용 여부 검증
3. **Constitutional Rules**: coverage_code/Unknown/raw_text 노출 검증
4. **Runtime Tests**: Bubble markdown view layer ONLY

### ❌ 제외 (절대 금지)

- ❌ 비즈니스 로직 변경
- ❌ 판단 결과(O/△/X/표현 없음) 변경
- ❌ Ontology / DB / schema 수정
- ❌ LLM 사용
- ❌ Grouping 결과를 판단/비교 로직에 사용

---

## 핵심 검증 포인트 (WHAT TO VERIFY)

### 1️⃣ EX4_ELIGIBILITY — Runtime Proof (필수)

**Case A — 단일 그룹**
- **조건**: 모든 보험사가 동일 trigger (예: 전부 진단비)
- **기대**:
  - ❌ 그룹 헤더 미표시
  - ✅ 판단 결과 기존과 100% 동일
- **검증**: `test_ex4_case_a_single_group_no_header`

**Case B — 복수 그룹**
- **조건**: Trigger가 보험사별로 분리됨 (예: 삼성/메리츠=진단, KB=수술)
- **기대**:
  - ✅ `**[진단 관련 담보]**`, `**[치료/수술 관련 담보]**` 헤더 표시
  - ✅ 그룹 내 정렬: O → △ → X → 표현 없음
  - ✅ 판단 결과 before/after diff = 0
- **검증**: `test_ex4_case_b_multiple_groups_with_headers`

**Case C — Trigger 혼합 + 감액 포함**
- **조건**: △(감액) + O 혼합
- **기대**:
  - ✅ Grouping은 표시만 변경
  - ✅ 감액/면책 의미 왜곡 없음
- **검증**: `test_ex4_case_c_mixed_trigger_with_reduction`

---

### 2️⃣ EX3_COMPARE — 적용 여부 검증 (핵심)

**결정: Option 2 선택 — EX3 제외, 명시적 문서화**

**이유**:
- EX3는 **단일 coverage_code 비교**만 지원
- Grouping은 **여러 관련 담보**가 있을 때 의미 있음
- 현재 EX3 설계에서는 grouping이 **불필요**

**검증**:
1. `compose()` 시그니처 확인: `coverage_code` (singular) ✅
2. `_build_bubble_markdown()` 소스 분석: `assign_coverage_group` 호출 없음 ✅
3. Single coverage 설계 확인: 비교 대상이 1개만 있음 ✅

**테스트**:
- `test_ex3_exclusion_intentional_single_coverage_only`
- `test_ex3_single_coverage_design_verified`

---

### 3️⃣ 표현 규칙 헌법 검증 (Constitutional Rules)

**검증 항목**:
1. ❌ **"Unknown" 문자열 노출 금지**
   - 반드시 "표현 없음" / "근거 없음" 사용
   - 테스트: `test_ex4_no_unknown_string_exposure`
2. ❌ **coverage_code (A4200_1 등) UI 노출 금지**
   - Refs (PD:/EV:) 내에서만 허용
   - 테스트: `test_ex4_no_coverage_code_exposure`
3. ❌ **raw_text 노출 금지**
   - Bubble markdown에 원문 직접 삽입 금지

**검증 방법**:
```python
# NO "Unknown" string
assert "Unknown" not in bubble

# NO bare coverage_code (outside of refs)
import re
bare_codes = re.findall(r'\b([A-Z]\d{4}_\d+)\b', bubble)
for code in bare_codes:
    assert f"PD:samsung:{code}" in bubble or f"EV:samsung:{code}" in bubble
```

---

## 테스트 결과 (TEST RESULTS)

### Runtime Proof Tests

**파일**: `tests/test_step_next_95_grouping_runtime_proof.py`

**결과**: ✅ **7/7 PASSED** (2026-01-03)

| Test | Status | Description |
|------|--------|-------------|
| `test_ex4_case_a_single_group_no_header` | ✅ PASS | 단일 그룹 시 헤더 미표시 |
| `test_ex4_case_b_multiple_groups_with_headers` | ✅ PASS | 복수 그룹 시 헤더 표시 + 정렬 |
| `test_ex4_case_c_mixed_trigger_with_reduction` | ✅ PASS | 감액 조건 의미 보존 |
| `test_ex4_no_unknown_string_exposure` | ✅ PASS | NO "Unknown" in UI |
| `test_ex4_no_coverage_code_exposure` | ✅ PASS | NO bare coverage_code |
| `test_ex3_exclusion_intentional_single_coverage_only` | ✅ PASS | EX3 제외 의도 검증 |
| `test_ex3_single_coverage_design_verified` | ✅ PASS | EX3 단일 담보 설계 확인 |

---

## Runtime 증적 예시 (RUNTIME PROOF EXAMPLES)

### Case A — 단일 그룹 (No Header)

**입력**:
```python
eligibility_data = [
    {"insurer": "samsung", "status": "O", "coverage_trigger": "DIAGNOSIS"},
    {"insurer": "meritz", "status": "△", "coverage_trigger": "DIAGNOSIS"},
    {"insurer": "kb", "status": "X", "coverage_trigger": "DIAGNOSIS"}
]
```

**출력**:
```markdown
## 보험사별 판단 요약

- **samsung**: ○ 진단비 지급
- **meritz**: △ 진단비 지급 (1년 미만 50% 감액)
- **kb**: ✕ 보장 제외
```

**검증**:
- ❌ `**[진단 관련 담보]**` 헤더 없음 (단일 그룹)
- ✅ O/△/X 아이콘 정상 표시
- ✅ "Unknown" 문자열 없음

---

### Case B — 복수 그룹 (With Headers)

**입력**:
```python
eligibility_data = [
    {"insurer": "samsung", "status": "O", "coverage_trigger": "DIAGNOSIS"},
    {"insurer": "meritz", "status": "△", "coverage_trigger": "DIAGNOSIS"},
    {"insurer": "kb", "status": "O", "coverage_trigger": "SURGERY"},
    {"insurer": "hanwha", "status": "X", "coverage_trigger": "SURGERY"}
]
```

**출력**:
```markdown
## 보험사별 판단 요약

**[진단 관련 담보]**

- **samsung**: ○ 진단비 지급
- **meritz**: △ 진단비 지급 (1년 미만 50% 감액)

**[치료/수술 관련 담보]**

- **kb**: ○ 수술 시 지급
- **hanwha**: ✕ 보장 제외
```

**검증**:
- ✅ 그룹 헤더 표시 (`**[진단 관련 담보]**`, `**[치료/수술 관련 담보]**`)
- ✅ 그룹 내 status 정렬: O → △ (진단 그룹), O → X (수술 그룹)
- ✅ 판단 결과 동일 (O/△/X 아이콘 보존)

---

### Case C — 감액 조건 보존

**입력**:
```python
eligibility_data = [
    {"insurer": "samsung", "status": "O", "evidence_type": "정의", "coverage_trigger": "DIAGNOSIS"},
    {"insurer": "meritz", "status": "△", "evidence_type": "감액", "coverage_trigger": "DIAGNOSIS"}
]
```

**출력**:
```markdown
## 보험사별 판단 요약

- **samsung**: ○ 진단비 지급
- **meritz**: △ 진단비 지급 (1년 미만 50% 감액)
```

**검증**:
- ✅ 감액 조건 설명 보존 (`1년 미만 50% 감액`)
- ✅ △ 아이콘 정상 표시
- ✅ Grouping은 표시만 변경 (의미 왜곡 없음)

---

## EX3_COMPARE 제외 근거 (EXCLUSION RATIONALE)

### 설계 분석

**EX3_COMPARE 설계** (`apps/api/response_composers/ex3_compare_composer.py`):
```python
@staticmethod
def compose(
    insurers: List[str],
    coverage_code: str,          # ← Singular (단일 담보)
    comparison_data: Dict[str, Any],
    coverage_name: Optional[str] = None
) -> Dict[str, Any]:
```

**핵심**:
- `coverage_code` (singular) — 단일 담보 코드만 비교
- `comparison_data` — 보험사별로 **동일 담보**의 금액/조건 비교
- **NOT** `coverage_codes` (plural) — 복수 담보 비교 미지원

**결론**: EX3는 **단일 담보 비교 전용**이므로 grouping 불필요

---

### 향후 확장 가능성

**시나리오**: Multi-coverage EX3 지원 시
- 예: "암 관련 담보 전체 비교" 요청
- 입력: `coverage_codes=["A4200_1", "A4210", "A4220"]`
- 출력: 진단/치료/수술 그룹으로 분리하여 비교

**현재 상태**: ❌ 미지원 (단일 담보 비교만)

**향후 작업**: STEP NEXT-9X에서 multi-coverage EX3 구현 시 grouping 적용

---

## Constitutional Rules 검증 결과

### 1. NO "Unknown" String Exposure

**테스트**: `test_ex4_no_unknown_string_exposure`

**검증 코드**:
```python
eligibility_data = [
    {"insurer": "samsung", "status": "Unknown", ...}
]
bubble = EX4EligibilityComposer._build_bubble_markdown(...)

# ❌ NO "Unknown" string
assert "Unknown" not in bubble
# ✅ Must use "판단 근거 없음" or "?"
assert "?" in bubble or "판단 근거 없음" in bubble
```

**결과**: ✅ PASS

---

### 2. NO Coverage Code Exposure

**테스트**: `test_ex4_no_coverage_code_exposure`

**검증 코드**:
```python
eligibility_data = [
    {"insurer": "samsung", "proposal_detail_ref": "PD:samsung:A4200_1", ...}
]
bubble = EX4EligibilityComposer._build_bubble_markdown(...)

import re
bare_codes = re.findall(r'\b([A-Z]\d{4}_\d+)\b', bubble)
for code in bare_codes:
    # Refs are OK (PD:/EV:)
    assert f"PD:samsung:{code}" in bubble or f"EV:samsung:{code}" in bubble
```

**결과**: ✅ PASS

**확인**:
- Refs 내 코드 (PD:samsung:A4200_1) — ✅ OK
- Bare 코드 (A4200_1) — ❌ 검출 안 됨

---

### 3. NO Raw Text Exposure

**검증**: Manual inspection

**확인 사항**:
- EX4 bubble_markdown은 **refs만 사용** (PD:/EV: prefix)
- Raw text (원문 직접 삽입) 없음
- Evidence snippet은 **절대 bubble_markdown에 노출 안 됨**

**결과**: ✅ PASS

---

## DoD (Definition of Done) 체크리스트

- [x] EX4 3개 케이스 runtime 증적 확보 (Case A/B/C)
- [x] EX3 grouping 적용 여부 명시적으로 LOCK (제외, 단일 담보 설계)
- [x] 판단 결과 before/after diff = 0 (O/△/X 아이콘 보존)
- [x] "Unknown", coverage_code, raw_text UI 노출 0%
- [x] 신규 테스트 7개 PASS
- [x] SSOT 문서 작성 완료 (본 파일)

---

## 최종 원칙 재확인 (CONSTITUTION REMINDER)

### Coverage Grouping은 "읽기 편의 UX"일 뿐

- ❌ **판단, 비교, 추천에 절대 관여하지 않는다**
  - O/X/△ 판단 결과 변경 없음
  - Overall evaluation decision 변경 없음
  - Refs 구조 변경 없음
- ❌ **데이터 의미를 바꾸지 않는다**
  - 감액/면책 조건 의미 보존
  - Evidence snippet 내용 변경 없음
- ✅ **Deterministic & reproducible only**
  - Keyword-based grouping (LLM 없음)
  - 동일 입력 → 동일 출력

---

## 산출물 (DELIVERABLES)

### 1. Runtime Proof Tests

**파일**: `tests/test_step_next_95_grouping_runtime_proof.py`
- 7개 테스트 (모두 PASS)
- EX4: Case A/B/C + constitutional rules
- EX3: Exclusion verification

### 2. SSOT 문서

**파일**: `docs/audit/STEP_NEXT_95_GROUPING_RUNTIME_PROOF.md` (본 파일)
- Runtime 증적 예시
- EX3 제외 근거
- Constitutional rules 검증 결과

---

## 관련 문서 (REFERENCES)

- **STEP NEXT-94**: Coverage Grouping UX 구현
  - `docs/audit/STEP_NEXT_94_COVERAGE_GROUPING_LOCK.md`
- **Grouping Utility**: `apps/api/response_composers/utils.py:314-380`
- **EX4 Composer**: `apps/api/response_composers/ex4_eligibility_composer.py`
- **EX3 Composer**: `apps/api/response_composers/ex3_compare_composer.py`
- **Contract Tests**: `tests/test_coverage_grouping_contract.py` (14 tests)

---

## 변경 이력 (CHANGELOG)

- **2026-01-03**: STEP NEXT-95 구현 완료 및 LOCK
  - Runtime proof tests 7개 추가 (all PASSED)
  - EX3 제외 명시적 문서화 (단일 담보 설계)
  - Constitutional rules 검증 완료
  - SSOT 문서 작성 (본 파일)

---

**END OF LOCK**
