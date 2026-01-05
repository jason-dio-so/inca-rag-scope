# STEP NEXT-134: EXAM2 "찾아줘" Query Routing Lock — SSOT

**Date**: 2026-01-04
**Status**: FINAL LOCK
**Constitutional Basis**: EXAM2 = 탐색/발굴 전용 (NO context carryover)

---

## 0. Purpose (목적)

EXAM2 질문 중 **"~담보 중 보장한도가 다른 상품 찾아줘"** 유형이 잘못된 intent (EX2_DETAIL_DIFF)로 라우팅되고, **이전 EX3/EX4 컨텍스트(coverage_code=A4200_1 등)를 재사용**하는 버그를 완전히 차단한다.

### 문제 재현 증거

**Input**: "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"

**Before STEP NEXT-134**:
- ❌ `kind = EX2_DETAIL_DIFF` (comparison mode, NOT search)
- ❌ Response refs: `PD:samsung:A4200_1`, `PD:meritz:A4200_1` (암진단비)
- ❌ Coverage mismatch: Query asks for "암직접입원일당", but system uses "암진단비" (A4200_1)
- ❌ Root cause: Context carryover from previous EX3 question

**After STEP NEXT-134**:
- ✅ `kind = EX2_LIMIT_FIND` (search/discovery mode)
- ✅ Response refs: `PD:samsung:A6200`, `PD:meritz:A6200` (암직접입원일당)
- ✅ Coverage match: Query and response both use "암직접입원일당"
- ✅ NO context carryover

---

## 1. EXAM2 Constitutional Rules (ABSOLUTE)

### EXAM2 Principles

1. **EXAM2 = 탐색(발굴) + 비교**, NOT "비교 전용"
2. **"찾아줘/발굴/다른 상품" 키워드 → 무조건 EX2_LIMIT_FIND**
3. **EX2_DETAIL_DIFF는 사용자가 보험사 2개 명시 + 비교 의도 명확할 때만**
4. **EXAM2는 이전 메시지의 coverage_code / proposal_detail_ref / insurers를 절대 carry-over 하지 않음**

### Forbidden (금지)

- ❌ EX2_LIMIT_FIND에서 보험사 2개 선택 강요
- ❌ EXAM2에서 이전 message의 coverage_code / PD ref / insurers 재사용
- ❌ "삼성/메리츠 보장한도 차이" 같은 EX2_DETAIL_DIFF 결과를 "찾아줘" 질문에 반환

---

## 2. Intent Detection Logic (Deterministic)

### EX2_LIMIT_FIND Detection (ABSOLUTE PRIORITY)

**Gate 2 (STEP NEXT-134)**: "찾아줘" (discovery/search) patterns

```python
# Priority 3 - Anti-confusion gates (BEFORE pattern matching)
search_patterns = [
    r"찾아줘",
    r"찾아주세요",
    r"찾아주",
    r"다른\s*상품",
    r"있는\s*상품",
    r"발굴",
    r"보장한도가?\s*다른",
    r"차이가?\s*나는\s*상품"
]
for pattern in search_patterns:
    if re.search(pattern, message_lower):
        return ("EX2_LIMIT_FIND", 1.0)  # 100% confidence
```

**Examples**:
- "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" → `EX2_LIMIT_FIND`
- "보장한도 차이가 나는 상품 있나요?" → `EX2_LIMIT_FIND`
- "다른 상품 발굴해줘" → `EX2_LIMIT_FIND`

### EX2_DETAIL_DIFF Conditions (Strict)

**Allowed ONLY when ALL of**:
1. 보험사 2개 명시됨 (또는 UI에서 2개 선택됨)
2. "비교/차이/어느게/더 큰" 류 비교 의도
3. "찾아줘/다른 상품" 류 발굴 의도 **없음**

**Example**:
- "삼성화재와 메리츠화재 암진단비 보장한도 비교해줘" → `EX2_DETAIL_DIFF` (OK)

---

## 3. Coverage Name Extraction (NEW)

**File**: `apps/api/chat_intent.py`

**Function**: `QueryCompiler.extract_coverage_name_from_message()`

```python
@staticmethod
def extract_coverage_name_from_message(message: str) -> str | None:
    """
    STEP NEXT-134: Extract coverage name from message (deterministic)

    Rules:
    - NO LLM
    - Extract common coverage keywords from message
    - Priority order (first match wins)
    """
    coverage_keywords = [
        "암진단비",
        "암직접입원비",
        "암직접입원일당",  # STEP NEXT-134: Added
        "뇌출혈진단비",
        "급성심근경색진단비",
        "상해사망",
        "질병사망",
        "수술비",
        "입원비",
        "통원비"
    ]

    message_lower = message.lower()
    for keyword in coverage_keywords:
        if keyword in message_lower:
            return keyword

    return None
```

**Coverage Code Mapping** (STEP NEXT-134):
```python
COVERAGE_NAME_TO_CODE = {
    "암진단비": "A4200_1",
    "암직접입원일당": "A6200",  # STEP NEXT-134: Added
    "암직접입원비": "A6200",    # Map to same code
    "입원일당": "A6100_1",
    # ... etc
}
```

---

## 4. Processing Flow (EX2_LIMIT_FIND)

### Flow Steps

1. **Coverage Name**: 현재 query에서만 추출/정규화 (이전 상태 사용 금지)
   ```python
   coverage_name = extract_coverage_name_from_message(request.message)
   # "암직접입원일당" extracted from current message ONLY
   ```

2. **Insurers**:
   - 사용자 미지정 → 전체 insurers (auto-expand to 8)
   - 사용자 일부 지정 → 그 집합만 탐색

3. **Result ViewModel**:
   - `kind = "EX2_LIMIT_FIND"`
   - 표 형태: 상품명 / 담보명 / 보장한도 / 보험사
   - "A사/B사" 고정 금지 (회사 수는 확장 가능)

4. **Empty State**:
   - "해당 담보를 찾지 못했습니다(탐색 범위: N개 보험사). 담보명/표현을 바꿔보세요."

---

## 5. Verification Scenarios

### Scenario A (핵심)
**Input**: "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘"

**Expected**:
- ✅ `kind = EX2_LIMIT_FIND`
- ✅ 삼성/메리츠 2개로 좁혀지지 않음 (보험사 선택 UI 없음)
- ✅ A4200_1/암진단비 refs가 응답에 0개
- ✅ A6200/암직접입원일당 refs만 사용

### Scenario B
**Input**: "삼성화재와 메리츠화재 암직접입원일당 보장한도 비교해줘"

**Expected**:
- ✅ (비교 의도 명확) `kind = EX2_DETAIL_DIFF` 가능
- ✅ 단, coverage_code는 암직접입원일당으로 resolve (A6200)
- ✅ A4200_1 금지

### Scenario C (Context Carryover Prevention)
**Input**:
1. "삼성화재 암진단비 비교해줘" (EX3, A4200_1 사용)
2. "암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘" (EXAM2)

**Expected**:
- ✅ Step 2: `kind = EX2_LIMIT_FIND`
- ✅ Step 2: A4200_1 carry-over 0%
- ✅ Step 2: A6200/암직접입원일당만 사용

---

## 6. Implementation Changes

### Modified Files

1. **`apps/api/chat_intent.py`**:
   - Added Gate 2 (STEP NEXT-134): "찾아줘" search patterns → EX2_LIMIT_FIND
   - Added `extract_coverage_name_from_message()` function
   - Added coverage code mappings for 입원 related coverages
   - Updated STEP NEXT-133 auto-extraction to use proper coverage name extraction

2. **`apps/api/chat_handlers_deterministic.py`**:
   - Fixed `Example2DiffHandlerDeterministic` to use dynamic `kind` from `compiled_query`
   - Previously hardcoded `kind="EX2_DETAIL_DIFF"` (ignored routing decision)
   - Now respects routed intent (`EX2_LIMIT_FIND` or `EX2_DETAIL_DIFF`)

### Key Code Changes

**Gate 2 (Anti-confusion for "찾아줘")**:
```python
# STEP NEXT-134: Gate 2 - "찾아줘" (discovery/search) patterns → EX2_LIMIT_FIND
search_patterns = [
    r"찾아줘", r"찾아주세요", r"찾아주",
    r"다른\s*상품", r"있는\s*상품", r"발굴",
    r"보장한도가?\s*다른", r"차이가?\s*나는\s*상품"
]
for pattern in search_patterns:
    if re.search(pattern, message_lower):
        return ("EX2_LIMIT_FIND", 1.0)
```

**Auto-extraction Fix (STEP NEXT-133 → STEP NEXT-134)**:
```python
# STEP NEXT-134: Use proper coverage name extraction (NOT compare_field)
if not request.coverage_names or len(request.coverage_names) == 0:
    coverage_from_message = QueryCompiler.extract_coverage_name_from_message(request.message)
    if coverage_from_message:
        request.coverage_names = [coverage_from_message]
```

**Handler Kind Lock (STEP NEXT-134)**:
```python
# apps/api/chat_handlers_deterministic.py::Example2DiffHandlerDeterministic.execute()

# STEP NEXT-134: Use kind from compiled_query (EX2_LIMIT_FIND or EX2_DETAIL_DIFF)
message_kind = compiled_query.get("kind", "EX2_DETAIL_DIFF")

vm = AssistantMessageVM(
    request_id=request.request_id,
    kind=message_kind,  # STEP NEXT-134: Use dynamic kind (NOT hardcoded)
    exam_type=get_exam_type_from_kind(message_kind),
    # ...
    lineage={
        "handler": "Example2DiffHandlerDeterministic",
        "llm_used": False,
        "deterministic": True,
        "diff_status": status,
        "intent": message_kind  # STEP NEXT-134: Track intent in lineage
    }
)
```

---

## 7. Forbidden Behaviors (금지)

❌ **ABSOLUTE FORBIDDEN**:
1. EX2_LIMIT_FIND에서 보험사 2개 선택 강요
2. EXAM2에서 이전 message의 coverage_code / PD ref / insurers 재사용
3. "삼성/메리츠 보장한도 차이" 같은 EX2_DETAIL_DIFF 결과를 "찾아줘" 질문에 반환
4. "보장한도" (field name)를 coverage_name으로 사용

---

## 8. Git Reflection

**Commit Message**:
```
fix(step-next-134): route EXAM2 finder queries to EX2_LIMIT_FIND and block context carryover

EXAM2 "찾아줘" query 처리:
- Gate 2: "찾아줘/다른 상품/발굴" → EX2_LIMIT_FIND (ABSOLUTE)
- Coverage extraction: extract_coverage_name_from_message() (NEW)
- Coverage code mapping: A6200 (암직접입원일당) added
- Context carryover prevention: NO previous coverage_code reuse

Fixes: EXAM2 queries using wrong coverage_code from previous context
SSOT: docs/audit/STEP_NEXT_134_EXAM2_LIMIT_FIND_ROUTING_LOCK.md

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 9. Definition of Success

> **"'암직접입원일당 담보 중 보장한도가 다른 상품 찾아줘'를 10번 반복해도 A4200_1 refs가 1번도 안 나오고, 매번 A6200 refs만 나오면 성공"**

---

## 10. EXAM CONSTITUTION Compliance

| EXAM Rule | Compliance |
|-----------|------------|
| EXAM2 = 탐색/발굴 + 비교 | ✅ "찾아줘" → EX2_LIMIT_FIND |
| EXAM2 context isolation | ✅ NO carryover from EX3/EX4 |
| Intent clarity | ✅ "찾아줘" = search (NOT comparison) |
| Coverage extraction | ✅ Current message ONLY |

---

**END OF SSOT**
