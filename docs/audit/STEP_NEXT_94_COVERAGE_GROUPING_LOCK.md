# STEP NEXT-94 — Coverage Grouping UX (담보 군집화) LOCK

**Status**: ✅ LOCKED (2026-01-03)

---

## 목적 (WHY)

현재 시스템은 정확성·검증·헌법 준수는 완성 단계이나,
고객 관점에서는 다음과 같은 **인지 부담**이 남아 있음:

- **문제**: 암진단비 / 유사암진단비 / 제자리암진단비 / 경계성종양진단비 / 유사암수술비가
  서로 어떤 관계인지 즉시 이해되지 않음
- **원인**: "같은 암인가, 다른 암인가?"에 대한 구조적 힌트 부족
- **해결**: 비교·판단 로직은 그대로 유지하면서, **인지 단위만 한 단계 상향**

---

## 적용 범위 (SCOPE)

### ✅ 적용

- **EX4_ELIGIBILITY**: 보장 가능 여부 비교 (O/X/△/Unknown)
  - 여러 관련 담보가 함께 표시되므로 grouping 효과 큼
  - 예: 제자리암진단비, 유사암진단비, 유사암수술비 → 그룹으로 묶어 표시

### ❌ 미적용

- **EX2_DETAIL**: 단일 담보 설명 전용 (grouping 불필요)
- **EX2_LIMIT_FIND**: 단일 담보 차이 탐색 (grouping 불필요)
- **EX3_COMPARE**: 단일 담보 비교 (현재는 단일 coverage_code 비교만 지원)

---

## 핵심 원칙 (CONSTITUTION)

### ❌ 금지 사항

1. **비즈니스 로직 변경 금지**
   - coverage_code, 판단 결과, 비교 결과 절대 변경 금지
   - 그룹 라벨은 판단·집계·통계에 **사용 금지**
2. **Ontology 투입 금지**
   - DB / schema / canonical mapping 변경 금지
3. **LLM 사용 금지**
   - 그룹 할당은 deterministic keyword matching ONLY

### ✅ 허용 사항

1. **View Layer 전용**
   - 그룹 라벨은 UI 표시 전용 (bubble_markdown, section header)
2. **Deterministic only**
   - 키워드 기반 규칙 (명시적, 재현 가능)
3. **Coverage Group은 "표시용 라벨"**
   - 판단·집계·통계에 절대 사용 금지

---

## 구현 개념 (WHAT)

### 1️⃣ Coverage Group Label 도입 (View-only)

각 담보에 **상위 인지 그룹(label)**을 부여한다.

**예시**:

```
**[진단 관련 담보]**
  - 암진단비
  - 유사암진단비
  - 제자리암진단비
  - 경계성종양진단비

**[치료/수술 관련 담보]**
  - 유사암수술비
  - 암입원비
```

- 그룹은 **UI 섹션 헤더** 용도
- 개별 담보 row / 판단 / 비교는 **그대로 유지**

---

### 2️⃣ Grouping 기준 (RULE)

**기준 필드** (Slim Card 기준):
- `coverage_name` (normalized, STEP NEXT-93 결과)
- `coverage_trigger` (DIAGNOSIS / SURGERY / TREATMENT)

**그룹 정의** (최대 3개):

| Group Label | 포함 조건 |
|------------|---------|
| **진단 관련 담보** | `coverage_trigger == "DIAGNOSIS"` OR `coverage_name` contains "진단비", "진단급여" |
| **치료/수술 관련 담보** | `coverage_trigger in ["SURGERY", "TREATMENT"]` OR `coverage_name` contains "수술비", "치료비", "입원", "통원", "항암", "방사선" |
| **기타 담보** | Fallback (위 조건 불충족 시) |

**우선순위 규칙**:
1. **Name keyword 우선**: 담보명에 명시적 키워드가 있으면 trigger보다 우선
   - 예: `coverage_name="암진단비"` + `coverage_trigger="SURGERY"` → **진단 관련 담보** (name 우선)
2. **Trigger 보조**: 담보명에 키워드 없으면 trigger 사용
   - 예: `coverage_name="기타담보"` + `coverage_trigger="DIAGNOSIS"` → **진단 관련 담보**
3. **Fallback**: 둘 다 없으면 "기타 담보"

⚠️ **그룹 수는 최대 3개로 제한** (UX 과밀 방지)

---

### 3️⃣ 화면 반영 규칙 (HOW)

#### EX4_ELIGIBILITY

**변경 전**:
```markdown
## 보험사별 판단 요약

- **삼성**: ○ 진단비 지급
- **메리츠**: △ 진단비 지급 (1년 미만 50% 감액)
- **KB**: ○ 수술 시 지급
```

**변경 후**:
```markdown
## 보험사별 판단 요약

**[진단 관련 담보]**

- **삼성**: ○ 진단비 지급
- **메리츠**: △ 진단비 지급 (1년 미만 50% 감액)

**[치료/수술 관련 담보]**

- **KB**: ○ 수술 시 지급
```

**표시 규칙**:
- **단일 그룹만 존재** → 그룹 헤더 **표시 안 함** (불필요)
- **복수 그룹 존재** → 그룹 헤더 **표시** (구조 명확화)
- 그룹 내에서는 **status 우선순위 정렬** (O → △ → X → Unknown)
- 판단 아이콘(O/△/X/?) 및 설명은 **그대로 유지**

---

## 기술 구현 지점 (WHERE)

### Backend

**신규 함수** (`apps/api/response_composers/utils.py`):
```python
def assign_coverage_group(
    coverage_name: str,
    coverage_trigger: Optional[str] = None
) -> str:
    """
    Assign coverage group label for UX grouping (STEP NEXT-94)

    Returns: "진단 관련 담보" | "치료/수술 관련 담보" | "기타 담보"
    """
```

**수정된 Composer**:
- `apps/api/response_composers/ex4_eligibility_composer.py`
  - `_build_bubble_markdown()`: 그룹별로 보험사 정렬
  - **변경 범위**: bubble_markdown 생성 로직 ONLY
  - **불변**: `_build_overall_evaluation()` (판단 로직 절대 변경 없음)

### Frontend

- ❌ **수정 없음** (section 구조만 활용)

---

## 테스트 / 검증 (TEST)

### 계약 테스트 (필수)

**파일**: `tests/test_coverage_grouping_contract.py`

**검증 항목**:
1. ✅ Group label이 판단 결과에 **영향 없음**
2. ✅ 동일 입력 → grouping on/off 시 결과 **동일**
3. ✅ coverage_code UI 노출 **0%**
4. ✅ refs 구조 **변경 없음**
5. ✅ 그룹 없는 담보도 **정상 표시**
6. ✅ 단일 그룹 시 헤더 **미표시**
7. ✅ 복수 그룹 시 헤더 **표시**
8. ✅ Status 아이콘 (O/△/X/?) **보존**

**결과**: ✅ **14 tests PASSED** (2026-01-03)

### 기존 테스트 (회귀 검증)

- `tests/test_ex3_bubble_markdown_step_next_82.py`: ✅ **10 tests PASSED**
- `tests/test_ex4_bubble_markdown_step_next_83.py`: ✅ **12 tests PASSED**

**결론**: ✅ **기존 기능 100% 보존** (no regression)

---

## DoD (완료 기준)

- [x] EX4_ELIGIBILITY 응답에 Coverage Group Label 표시
- [x] 판단/비교 결과 100% 동일 (before/after diff = 0)
- [x] Group label은 UI text only (business logic 분리)
- [x] 신규 테스트 PASS (14 tests)
- [x] 기존 테스트 PASS (22 tests, no regression)
- [x] SSOT 문서 작성 (본 파일)

---

## 구현 상태 (IMPLEMENTATION STATUS)

### ✅ 완료 (2026-01-03)

1. **Grouping Utility** (`apps/api/response_composers/utils.py:314-380`)
   - `assign_coverage_group()`: Deterministic keyword-based grouping
   - Priority: Name keyword > trigger > fallback
2. **EX4 Composer Update** (`apps/api/response_composers/ex4_eligibility_composer.py`)
   - `_build_bubble_markdown()`: Group-aware output (lines 401-522)
   - Single group → no header
   - Multiple groups → show headers
   - Status sorting within groups: O → △ → X → Unknown
3. **Contract Tests** (`tests/test_coverage_grouping_contract.py`)
   - 14 tests: grouping rules, view-only contract, no judgment change
4. **Bug Fixes**
   - None evidence_snippet handling (line 527: null check before `in` operation)
   - Name keyword priority over trigger (utils.py: reordered conditions)

### 🔒 헌법 준수 검증

- ❌ NO business logic change (✅ verified by tests)
- ❌ NO LLM usage (✅ deterministic only)
- ❌ NO ontology change (✅ no DB/schema modification)
- ✅ View layer only (✅ bubble_markdown ONLY)
- ✅ Deterministic (✅ keyword matching ONLY)

---

## 예시 출력 (EXAMPLE OUTPUT)

### Before (STEP NEXT-83)

```markdown
## 보험사별 판단 요약

- **삼성**: ○ 진단비 지급
- **메리츠**: △ 진단비 지급 (1년 미만 50% 감액)
- **KB**: ○ 수술 시 지급
- **한화**: ✕ 보장 제외
```

### After (STEP NEXT-94)

```markdown
## 보험사별 판단 요약

**[진단 관련 담보]**

- **삼성**: ○ 진단비 지급
- **메리츠**: △ 진단비 지급 (1년 미만 50% 감액)
- **한화**: ✕ 보장 제외

**[치료/수술 관련 담보]**

- **KB**: ○ 수술 시 지급
```

**차이점**:
- 그룹 헤더 추가 (`**[그룹명]**`)
- 그룹 내 status 정렬 (O → △ → X)
- **판단 결과 (O/△/X/?) 및 설명 동일 유지**

---

## 향후 확장 가능성 (FUTURE)

### EX3_COMPARE 적용 (현재 미적용)

**이유**: EX3는 현재 **단일 coverage_code 비교**만 지원
- 예: "암진단비(A4200_1)" 삼성 vs 메리츠
- 단일 담보이므로 grouping 불필요

**확장 시나리오**:
- 향후 **multi-coverage EX3** 지원 시 grouping 적용 가능
- 예: "암 관련 담보 전체 비교" → 진단/치료/수술 그룹으로 분리

---

## 변경 이력 (CHANGELOG)

- **2026-01-03**: STEP NEXT-94 구현 완료 및 LOCK
  - `assign_coverage_group()` 추가 (utils.py)
  - EX4_ELIGIBILITY bubble_markdown grouping 적용
  - Contract tests 14개 추가 (all PASSED)
  - 기존 tests 22개 회귀 검증 (all PASSED)
  - SSOT 문서 작성 (본 파일)

---

## 참조 (REFERENCES)

- **Constitutional Rules**: `CLAUDE.md` (STEP NEXT-94 section)
- **Grouping Utility**: `apps/api/response_composers/utils.py:314-380`
- **EX4 Composer**: `apps/api/response_composers/ex4_eligibility_composer.py`
- **Contract Tests**: `tests/test_coverage_grouping_contract.py`
- **Related Steps**:
  - STEP NEXT-82: EX3 Bubble Markdown
  - STEP NEXT-83: EX4 Bubble Markdown
  - STEP NEXT-93: Coverage Name Display Normalization

---

**END OF LOCK**
