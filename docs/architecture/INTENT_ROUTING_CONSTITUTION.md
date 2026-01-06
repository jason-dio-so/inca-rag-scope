# INTENT ROUTING CONSTITUTION

**목적**: inca-rag-scope Intent Routing + need_more_info 규칙을 헌법 수준으로 동결
**기준 시점**: STEP NEXT-OPS-CYCLE-03B/C (2026-01-06)
**SSOT**: 이 문서는 이후 정리/리팩토링(STEP B-2/B-3)의 ABSOLUTE 기준이 된다
**금지**: 이 문서와 다른 동작은 **버그**로 간주한다

---

## 1. 용어 / 엔티티

### 1.1 ChatRequest 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| `message` | `str` | 사용자 입력 텍스트 (필수) |
| `kind` | `Optional[MessageKind]` | 명시적 intent (UI 버튼 등) |
| `selected_category` | `Optional[str]` | 카테고리 선택 (UI) |
| `insurers` | `List[str]` | 보험사 코드 리스트 (예: `["samsung", "meritz"]`) |
| `coverage_names` | `List[str]` | 담보명 리스트 (예: `["암진단비"]`) |
| `disease_names` | `List[str]` | 질병명 리스트 (EX4용, 예: `["제자리암", "경계성종양"]`) |
| `disease_name` | `Optional[str]` | 단일 질병명 (레거시 필드) |
| `llm_mode` | `str` | `"OFF"` (deterministic) / `"ON"` (LLM refinement) |
| `compare_field` | `Optional[str]` | 비교 필드 (EX2_LIMIT_FIND용, 기본값: `"보장한도"`) |

### 1.2 MessageKind 목록
| MessageKind | 설명 | 상태 |
|-------------|------|------|
| `EX1_PREMIUM_DISABLED` | 보험료 비교 (disabled 응답) | 활성 |
| `EX2_DETAIL` | 단일 보험사 담보 설명 | 활성 |
| `EX2_LIMIT_FIND` | 보장한도/조건 차이 탐색 | 활성 |
| `EX3_COMPARE` | 다중 보험사 담보 비교 | 활성 |
| `EX4_ELIGIBILITY` | 질병 하위 개념 보장 여부 (O/X) | 활성 |
| `EX2_DETAIL_DIFF` | (레거시 - backward compat only) | 레거시 |
| `EX3_INTEGRATED` | (레거시 - backward compat only) | 레거시 |

---

## 2. 라우팅 우선순위 (Priority 규칙)

### 2.1 IntentRouter.route() 우선순위 (LOCKED)

```
Priority 1 (ABSOLUTE):
  if request.kind is not None:
    return request.kind

Priority 2 (insurers count gate):
  if len(insurers) == 1:
    return "EX2_DETAIL"

Priority 2.5 (EX3 comparison gate - STEP NEXT-OPS-CYCLE-03B):
  if len(insurers) >= 2 AND ("비교" OR "vs" OR "차이" OR "대조" OR "비교해줘" OR "compare" in message):
    return "EX3_COMPARE"

Priority 3 (detect_intent()):
  return IntentRouter.detect_intent(request)
```

### 2.2 IntentRouter.detect_intent() 우선순위 (LOCKED)

```
Priority 1 (Category):
  if request.selected_category:
    return CATEGORY_MAPPING[selected_category]

Priority 2 (FAQ template):
  if request.faq_template_id:
    return template.example_kind

Priority 3 (Anti-confusion gates):
  Gate 1 (Disease subtype → EX4_ELIGIBILITY):
    if ANY disease_subtype in message:
      return "EX4_ELIGIBILITY"
    Disease subtypes: ["제자리암", "경계성종양", "유사암", "갑상선암", "기타피부암",
                       "대장점막내암", "전립선암", "방광암"]

  Gate 2 (Search pattern → EX2_LIMIT_FIND):
    if ANY search_pattern in message:
      return "EX2_LIMIT_FIND"
    Search patterns: ["찾아줘", "찾아주세요", "찾아주", "다른\s*상품", "있는\s*상품",
                      "발굴", "보장한도가?\s*다른", "차이가?\s*나는\s*상품"]

  Gate 3 (Limit/condition pattern → EX2_LIMIT_FIND):
    if ANY limit_pattern in message:
      return "EX2_LIMIT_FIND"
    Limit patterns: ["보장한도.*다른", "한도.*다른", "한도.*차이", "조건.*다른",
                     "면책.*다른", "감액.*다른"]

Priority 4 (Keyword pattern matching):
  - Score = (matched patterns / total patterns) per kind
  - Threshold: 0.3
  - Return highest scoring kind if >= 0.3

Priority 5 (Unknown fallback):
  return "EX2_LIMIT_FIND"  # Default fallback
```

### 2.3 핵심 라우팅 규칙 (3대 원칙)

#### 규칙 1: Single Insurer → EX2_DETAIL (ABSOLUTE)
```
if len(insurers) == 1:
  return "EX2_DETAIL"
```
- 보험사 1개 = 설명 전용 모드
- 다른 키워드("비교", "찾아줘") 무시
- Priority 2에서 처리 (detect_intent 호출 전)

#### 규칙 2: Multi Insurer + Comparison Keywords → EX3_COMPARE (ABSOLUTE)
```
if len(insurers) >= 2 AND comparison_keyword in message:
  return "EX3_COMPARE"
```
- Comparison keywords: `["비교", "vs", "차이", "대조", "비교해줘", "compare"]`
- STEP NEXT-OPS-CYCLE-03B에서 복구 (이전에 dead 상태였음)
- Priority 2.5에서 처리 (detect_intent 호출 전)

#### 규칙 3: Disease Subtype → EX4_ELIGIBILITY (ABSOLUTE)
```
if disease_subtype in message:
  return "EX4_ELIGIBILITY"
```
- Disease subtypes: 8개 하드코딩 리스트 (DISEASE_SUBTYPES)
- EX2/EX3보다 우선 (Priority 3 - Gate 1)
- detect_intent() 내부에서 처리 (insurers count gate 이후)

---

## 3. IntentDispatcher.dispatch() Validation 규칙

### 3.1 Validation Flow (LOCKED)

```
Step 1: Auto-fill disease_names (EX4 only)
  if kind == "EX4_ELIGIBILITY" AND disease_names empty:
    disease_names = extract disease subtypes from message
    (Note: disease_name 단수형도 auto-fill)

Step 2: EX2_LIMIT_FIND coverage auto-extract (STEP NEXT-OPS-CYCLE-03C)
  if kind == "EX2_LIMIT_FIND" AND coverage_names empty:
    coverage_names = extract_coverage_name_from_message(message)
    ⚠️ CRITICAL: insurers는 절대 수정 금지 (NO auto-expand)

Step 3: SlotValidator.validate(request, kind)
  → (is_valid, missing_slots)

Step 4: if not is_valid:
    return ChatResponse(need_more_info=True, missing_slots, clarification_options)

Step 5: Compile query + Dispatch to handler
```

### 3.2 EX2_LIMIT_FIND 특수 규칙 (ABSOLUTE)

#### ✅ 허용: Coverage Auto-Extract
```python
# STEP NEXT-OPS-CYCLE-03C
if kind == "EX2_LIMIT_FIND" and not request.coverage_names:
    coverage_from_message = QueryCompiler.extract_coverage_name_from_message(request.message)
    if coverage_from_message:
        request.coverage_names = [coverage_from_message]
```

#### ❌ 금지: Insurers Auto-Expand (ABSOLUTE FORBIDDEN)
```python
# STEP NEXT-OPS-CYCLE-03B: 아래 코드는 삭제됨 (42 lines deleted)
# if kind == "EX2_LIMIT_FIND" and not request.insurers:
#     request.insurers = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai", "heungkuk", "db"]  # ❌ FORBIDDEN
```
- Insurers는 사용자가 **반드시 선택**해야 함
- Auto-expand 시도 시 **헌법 위반**으로 간주

---

## 4. Slot 요구사항 표 (LOCKED)

### 4.1 Required Slots per MessageKind

| MessageKind | Required Slots | need_more_info Trigger |
|-------------|----------------|------------------------|
| `EX1_PREMIUM_DISABLED` | (none) | Never (immediate disabled response) |
| `EX2_DETAIL` | `coverage_names`, `insurers` | Any slot missing |
| `EX2_LIMIT_FIND` | `coverage_names`, `insurers`, `compare_field` | `insurers` missing (coverage auto-extracted) |
| `EX3_COMPARE` | `coverage_names`, `insurers` | Any slot missing |
| `EX4_ELIGIBILITY` | `disease_name`, `insurers` | `insurers` missing (disease auto-filled) |

### 4.2 Special Handling (LOCKED)

| Slot | Kind | Auto-Fill Rule |
|------|------|----------------|
| `compare_field` | `EX2_LIMIT_FIND` | Default to `"보장한도"` if missing |
| `coverage_names` | `EX2_LIMIT_FIND` | Auto-extract from message (STEP NEXT-OPS-CYCLE-03C) |
| `disease_names` | `EX4_ELIGIBILITY` | Auto-extract disease subtypes from message |
| `disease_name` | `EX4_ELIGIBILITY` | Auto-fill from `disease_names[0]` (legacy compat) |
| `insurers` | **ALL** | ❌ **NEVER auto-fill** (user selection required) |

---

## 5. 대표 시나리오 6개 (현재 동작 기준)

### Scenario 1: EX3_COMPARE (Multi-insurer comparison)
**Input**:
```json
{
  "message": "삼성화재와 메리츠화재 암진단비 비교해줘",
  "insurers": ["samsung", "meritz"],
  "coverage_names": ["암진단비"],
  "llm_mode": "OFF"
}
```
**Expected**:
- `kind`: `"EX3_COMPARE"`
- `need_more_info`: `false`
- `message`: Comparison table with 2 insurers

**Routing Logic**:
- Priority 2.5: `insurers >= 2` + `"비교해줘"` in message → `EX3_COMPARE`

---

### Scenario 2: EX2_LIMIT_FIND (Coverage auto-extract + insurers required)
**Input**:
```json
{
  "message": "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘",
  "insurers": [],
  "coverage_names": [],
  "llm_mode": "OFF"
}
```
**Expected**:
- `kind`: `"EX2_LIMIT_FIND"`
- `need_more_info`: `true`
- `missing_slots`: `["insurers"]` (NOT `["coverage_names", "insurers"]`)

**Current Behavior** (STEP NEXT-OPS-CYCLE-03C):
- Step 1: Route to `EX2_LIMIT_FIND` (via "찾아줘" gate)
- Step 2: Coverage auto-extract → `coverage_names = ["암직접입원일당"]`
- Step 3: Validate → `insurers` missing
- Step 4: Return `need_more_info=true`, `missing_slots=["insurers"]`

**CRITICAL**: `missing_slots`에 `coverage_names` 포함 안 됨 (auto-extract 성공)

---

### Scenario 3: EX2_DETAIL (Single insurer explanation)
**Input**:
```json
{
  "message": "삼성화재 암진단비 설명해줘",
  "insurers": ["samsung"],
  "coverage_names": ["암진단비"],
  "llm_mode": "OFF"
}
```
**Expected**:
- `kind`: `"EX2_DETAIL"`
- `need_more_info`: `false`
- `message`: Explanation bubble + detail sections

**Routing Logic**:
- Priority 2: `insurers == 1` → `EX2_DETAIL` (ignore "설명해줘" keyword)

---

### Scenario 4: EX4_ELIGIBILITY (Disease subtype auto-fill)
**Input**:
```json
{
  "message": "경계성종양 보장돼?",
  "insurers": ["samsung", "meritz"],
  "coverage_names": [],
  "llm_mode": "OFF"
}
```
**Expected**:
- `kind`: `"EX4_ELIGIBILITY"`
- `need_more_info`: `false` (if disease auto-filled successfully)
- `message`: O/X eligibility table

**Current Behavior**:
- Step 1: Route to `EX4_ELIGIBILITY` (via disease subtype gate - "경계성종양")
- Step 2: Auto-fill `disease_names = ["경계성종양"]`, `disease_name = "경계성종양"`
- Step 3: Validate → all slots filled
- Step 4: Return EX4 table

**NOTE**: If disease auto-fill fails, `need_more_info=true` with `missing_slots=["disease_name"]`

---

### Scenario 5: Explicit kind override (UI button contract)
**Input**:
```json
{
  "message": "암진단비",
  "insurers": ["samsung"],
  "coverage_names": ["암진단비"],
  "kind": "EX3_COMPARE",  ← Explicit kind from UI button
  "llm_mode": "OFF"
}
```
**Expected**:
- `kind`: `"EX3_COMPARE"` (NOT `"EX2_DETAIL"`)
- `need_more_info`: `true` (EX3 requires insurers >= 2)
- `missing_slots`: `["insurers"]`

**Routing Logic**:
- Priority 1 (ABSOLUTE): `request.kind` is provided → return `"EX3_COMPARE"`
- Priority 2 (`insurers == 1`) is **skipped**
- Validation fails → `need_more_info`

**Constitutional Rule**: Explicit `kind` bypasses **ALL** routing logic (insurers count, keywords, etc.)

---

### Scenario 6: Ambiguous query (comparison vs search confusion)
**Input**:
```json
{
  "message": "암진단비 보장한도가 다른 상품 비교해줘",
  "insurers": [],
  "coverage_names": [],
  "llm_mode": "OFF"
}
```
**Expected** (Current behavior as of STEP NEXT-OPS-CYCLE-03B/C):
- `kind`: `"EX2_LIMIT_FIND"` (NOT `"EX3_COMPARE"`)
- `need_more_info`: `true`
- `missing_slots`: `["insurers"]`

**Routing Logic** (Priority order matters):
- Priority 2.5 (EX3 gate): **FAILS** (`insurers.length == 0`, not >= 2)
- Priority 3 - Gate 2 (Search pattern): **MATCH** ("다른 상품" pattern)
- Result: `EX2_LIMIT_FIND` wins

**Key Insight**: EX3 gate requires `insurers >= 2` **before** checking keywords

---

## 6. 금지 사항 (Constitutional Violations)

### 6.1 ABSOLUTE 금지 (위반 시 헌법 위반)

#### ❌ ValueError로 500 만들기 금지
```python
# ❌ FORBIDDEN
if not insurers:
    raise ValueError("Insurers required")  # 500 error

# ✅ CORRECT
if not insurers:
    return ChatResponse(need_more_info=True, missing_slots=["insurers"])  # 200 OK
```
- 라우팅/슬롯 미충족은 **반드시** `need_more_info` 패턴으로 처리
- 500 에러는 **시스템 장애**로만 사용

#### ❌ EX2_LIMIT_FIND insurers auto-expand 금지
```python
# ❌ FORBIDDEN (STEP NEXT-OPS-CYCLE-03B에서 삭제됨)
if kind == "EX2_LIMIT_FIND" and not insurers:
    insurers = ["samsung", "meritz", "hanwha", "lotte", "kb", "hyundai", "heungkuk", "db"]

# ✅ CORRECT (STEP NEXT-OPS-CYCLE-03C)
if kind == "EX2_LIMIT_FIND" and not insurers:
    # Coverage auto-extract 허용, insurers는 절대 수정 금지
    pass  # SlotValidator will catch missing insurers
```

#### ❌ EX3_COMPARE multi-coverage 금지 (단일 담보 lock)
```python
# ❌ FORBIDDEN
request.coverage_names = ["암진단비", "수술비"]  # EX3는 단일 담보만

# ✅ CORRECT
request.coverage_names = ["암진단비"]  # Single coverage only
```
- EX3_COMPARE는 **1개 담보 × N개 보험사** 비교만 허용
- Multi-coverage comparison은 EX3_INTEGRATED (deprecated)로 분류

### 6.2 추가 금지 사항

- ❌ `IntentRouter.route()` 내부에서 LLM 호출 금지 (deterministic only)
- ❌ `SlotValidator.validate()` 내부에서 슬롯 값 수정 금지 (validation only)
- ❌ Explicit `kind`가 제공되었을 때 routing override 금지 (Priority 1 ABSOLUTE)
- ❌ Disease subtype 리스트를 동적으로 변경 금지 (8개 하드코딩 유지)

---

## 7. 검증 (실행 로그)

### 7.1 테스트 실행

#### A. Contract Tests (STEP NEXT-OPS-CYCLE-03B/C)
```bash
# Intent routing contract tests
PYTHONPATH=. pytest -q tests/test_intent_routing_lock.py

# Result: 10/10 PASS
# - test_ex3_compare_routing ✅
# - test_ex3_compare_missing_coverage ✅
# - test_ex2_limit_find_coverage_auto_extract ✅
# - test_ex2_limit_find_no_insurers_auto_expand ✅
# - test_ex2_detail_single_insurer ✅
# - test_ex2_detail_missing_coverage ✅
# - test_ex4_eligibility_disease_subtype ✅
# - test_ex4_eligibility_missing_insurers ✅
# - test_ex3_routing_not_dead ✅
# - test_ex2_no_auto_expand_insurers ✅
```

#### B. Smoke Tests (STEP B-3)
```bash
# Routing smoke test (requires server running on localhost:8000)
bash tools/smoke/smoke_chat.sh

# 3 test cases:
# 1. EX3_COMPARE (multi-insurer comparison)
# 2. EX2_LIMIT_FIND (missing insurers → need_more_info)
# 3. EX4_ELIGIBILITY (disease subtype routing)
```

### 7.2 수동 검증 (curl)
```bash
# Scenario 1: EX3_COMPARE
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"삼성화재와 메리츠화재 암진단비 비교해줘","insurers":["samsung","meritz"],"coverage_names":["암진단비"],"llm_mode":"OFF"}' \
  | jq '{kind: .message.kind, need_more_info}'
# Result: {"kind": "EX3_COMPARE", "need_more_info": false}

# Scenario 2: EX2_LIMIT_FIND
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘","insurers":[],"coverage_names":[],"llm_mode":"OFF"}' \
  | jq '{need_more_info, missing_slots}'
# Result: {"need_more_info": true, "missing_slots": ["insurers"]}
```

---

## 8. 변경 이력

| Date | Step | Change | Rationale |
|------|------|--------|-----------|
| 2026-01-06 | STEP NEXT-OPS-CYCLE-03B | EX3 routing 복구 (`insurers >= 2` + comparison keywords) | EX3 was dead (0% routing) |
| 2026-01-06 | STEP NEXT-OPS-CYCLE-03B | EX2_LIMIT_FIND insurers auto-expand 제거 (42 lines deleted) | Insurers must be user-selected |
| 2026-01-06 | STEP NEXT-OPS-CYCLE-03C | EX2_LIMIT_FIND coverage auto-extract 복구 | Coverage extraction OK, insurers FORBIDDEN |

---

## 9. 후속 작업 (STEP B-2/B-3)

이 문서는 **SSOT**이며, 이후 작업 시 반드시 준수해야 한다:

### STEP B-2 (Refactoring)
- 목표: 코드 구조 정리 (기능 변경 없음)
- 금지: 이 문서의 우선순위/규칙/시나리오 변경
- 허용: 함수 분리, 네이밍 개선, 중복 제거 (동작 동일)

### STEP B-3 (Optimization)
- 목표: 성능 개선 (기능 변경 없음)
- 금지: 라우팅 우선순위 변경, 슬롯 요구사항 변경
- 허용: 캐싱, 조기 종료, 알고리즘 최적화 (결과 동일)

### Future Enhancements (헌법 수정 필요)
- Multi-coverage EX3 지원 → 헌법 수정 필요 (Section 6.1 update)
- Dynamic disease subtype list → 헌법 수정 필요 (Section 2.2 update)
- LLM-based routing → 헌법 재작성 필요 (Section 2 complete rewrite)

---

**Constitutional Notice**: 이 문서와 다른 동작은 버그로 간주한다. 변경 시 반드시 헌법 개정(Constitutional Amendment) 절차를 거쳐야 한다.
