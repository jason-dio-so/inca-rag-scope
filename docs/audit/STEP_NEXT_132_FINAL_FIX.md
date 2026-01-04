# STEP NEXT-132 FINAL FIX: Multi-Disease Extraction

**Date**: 2026-01-04
**Status**: ✅ COMPLETE
**Commit**: `6ad1482`

---

## Problem

STEP NEXT-132 implemented multi-disease support in the **composer layer** (EX4EligibilityComposer accepts `List[str]`), but the **extraction layer** (IntentDispatcher) was still extracting only a single disease.

**User Query**:
```
"제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘"
```

**Expected Behavior**:
- Extract both diseases: `["제자리암", "경계성종양"]`
- Create 2 O/X table sections (one per disease)

**Actual Behavior** (before fix):
- Extracted only first disease: `["제자리암"]`
- Only one O/X table section shown
- User asks "경계성종양은?" → Falls back to EX2 (UX break)

**Root Cause**:
`_extract_disease_name_from_message()` returned on **first match** (single disease only)

---

## Solution

### 1. Add `disease_names` field to ChatRequest
**File**: `apps/api/chat_vm.py`

```python
class ChatRequest(BaseModel):
    disease_name: Optional[str] = None  # Legacy (single)
    disease_names: Optional[List[str]] = None  # STEP NEXT-132: Multi-disease
```

### 2. Create multi-disease extraction method
**File**: `apps/api/chat_intent.py`

```python
@staticmethod
def _extract_disease_names_from_message(message: str) -> List[str]:
    """
    STEP NEXT-132: Extract ALL disease names from message

    Returns:
        List of extracted disease names (may be empty)
    """
    disease_keywords = ["제자리암", "경계성종양", "유사암", ...]
    message_lower = message.lower()
    found_diseases = []

    for keyword in disease_keywords:
        if keyword in message_lower:
            found_diseases.append(keyword)

    return found_diseases
```

### 3. Update IntentDispatcher auto-fill
**File**: `apps/api/chat_intent.py`

```python
# STEP NEXT-132: Auto-fill disease_names for EX4_ELIGIBILITY
if kind == "EX4_ELIGIBILITY" and not request.disease_names:
    auto_filled = QueryCompiler._extract_disease_names_from_message(request.message)
    if auto_filled:
        request = ChatRequest(
            ...
            disease_names=auto_filled,  # Multi-disease list
            disease_name=auto_filled[0] if auto_filled else None,  # Legacy
            ...
        )
```

### 4. Update QueryCompiler
**File**: `apps/api/chat_intent.py`

```python
elif kind == "EX4_ELIGIBILITY":
    # STEP NEXT-132: Prefer disease_names (list) over disease_name (single)
    if request.disease_names:
        query["disease_names"] = request.disease_names
    elif request.disease_name:
        query["disease_names"] = [request.disease_name]
    else:
        query["disease_names"] = []
```

---

## Flow After Fix

**User Query**:
```
"제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘"
```

**Step 1**: IntentRouter detects `EX4_ELIGIBILITY` (disease subtype keywords found)

**Step 2**: IntentDispatcher auto-fills:
```python
disease_names = ["제자리암", "경계성종양"]  # Both extracted
```

**Step 3**: QueryCompiler compiles:
```python
compiled_query = {
    "disease_names": ["제자리암", "경계성종양"],
    "insurers": ["samsung", "meritz"]
}
```

**Step 4**: Example4HandlerDeterministic calls composer:
```python
response = EX4EligibilityComposer.compose(
    insurers=["samsung", "meritz"],
    subtype_keywords=["제자리암", "경계성종양"],  # List passed
    coverage_cards=all_coverage_cards
)
```

**Step 5**: Composer creates 2 table sections:
- Section 1: "제자리암 보장 가능 여부" (5-row O/X table)
- Section 2: "경계성종양 보장 가능 여부" (5-row O/X table)

**Step 6**: Bubble markdown:
```
**제자리암**, **경계성종양** 보장 가능 여부를 각각 확인했습니다.

표에서 **O/X**로 확인하세요.
O는 보장 가능, X는 보장 제외입니다.
```

---

## Tests

**Contract Tests**: 8/8 PASS (backward compatible)
```bash
pytest tests/test_step_next_130_ex4_ox_table.py -v
```

**Manual Extraction Test**:
```python
from apps.api.chat_intent import QueryCompiler

message = "제자리암, 경계성종양 보장내용에 따라 삼성화재, 메리츠화재 비교해줘"
diseases = QueryCompiler._extract_disease_names_from_message(message)

# Output: ['제자리암', '경계성종양']
```

---

## Definition of Done

- [x] `disease_names` field added to ChatRequest
- [x] `_extract_disease_names_from_message()` implemented
- [x] IntentDispatcher auto-fill updated
- [x] QueryCompiler handles `disease_names` priority
- [x] Tests: 8/8 PASS (backward compatible)
- [x] Manual extraction test verified
- [x] Documentation updated
- [x] Git committed

---

## Regression Prevention

### Anti-Pattern (FORBIDDEN):
```python
# ❌ FORBIDDEN: First-match extraction (single disease only)
for keyword in disease_keywords:
    if keyword in message_lower:
        return keyword  # WRONG: Returns immediately
```

### Valid Pattern (ALLOWED):
```python
# ✅ ALLOWED: Extract ALL diseases found
found_diseases = []
for keyword in disease_keywords:
    if keyword in message_lower:
        found_diseases.append(keyword)  # Collect all
return found_diseases
```

---

## LOCKED

**Date**: 2026-01-04
**Next Step**: Manual UI testing with actual multi-disease query

The multi-disease extraction is now complete at all layers:
1. ✅ Extraction layer (IntentDispatcher)
2. ✅ Compilation layer (QueryCompiler)
3. ✅ Handler layer (Example4HandlerDeterministic)
4. ✅ Composer layer (EX4EligibilityComposer)

All layers now support `List[str]` for diseases.
