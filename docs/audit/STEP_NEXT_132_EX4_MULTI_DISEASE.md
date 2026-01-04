# STEP NEXT-132: EX4 Multi-Disease Support

**Date**: 2026-01-04
**Status**: ✅ LOCKED
**Supersedes**: STEP NEXT-130/131 (signature only)
**SSOT**: This document

---

## Purpose

Support multiple diseases in a single EX4 query to prevent "제자리암, 경계성종양..." being reduced to single disease.

**Problem**:
- User input: "제자리암, 경계성종양 비교해줘"
- System response: Only "제자리암" (single disease)
- Follow-up: User asks "경계성종양은?" → Falls back to EX2 (UX break)

**Solution**:
- EX4 accepts `List[str]` of diseases
- Each disease gets its own O/X table section
- NO fallback to EX2, NO clarification UI

---

## Changes

### 1. Composer Signature
**Before**:
```python
def compose(insurers, subtype_keyword: str, ...)
```

**After**:
```python
def compose(insurers, subtype_keywords: List[str], ...)  # STEP NEXT-132
```

### 2. Response Structure
**Single disease** (`["제자리암"]`):
- 1 table section: "제자리암 보장 가능 여부"
- Bubble: "**제자리암** 보장 가능 여부를 확인했습니다."

**Multi disease** (`["제자리암", "경계성종양"]`):
- 2 table sections:
  - "제자리암 보장 가능 여부"
  - "경계성종양 보장 가능 여부"
- Bubble: "**제자리암**, **경계성종양** 보장 가능 여부를 각각 확인했습니다."

### 3. Handler Update
```python
# STEP NEXT-132: Extract disease list
disease_names = compiled_query.get("disease_names")  # List
if disease_names and isinstance(disease_names, list):
    subtypes = disease_names
else:
    # Fallback to single
    subtype = compiled_query.get("disease_name", "제자리암")
    subtypes = [subtype]
```

---

## Modified Files
- `apps/api/response_composers/ex4_eligibility_composer.py`:
  - `compose()`: `subtype_keyword` → `subtype_keywords: List[str]`
  - `_build_notes_section()`: Multi-disease text support
  - `_build_bubble_markdown()`: Multi-disease text support
- `apps/api/chat_handlers_deterministic.py`:
  - `Example4HandlerDeterministic`: Extract `disease_names` list
- `tests/test_step_next_130_ex4_ox_table.py`:
  - Updated all calls: `subtype_keyword="..."` → `subtype_keywords=["..."]`

---

## Tests
- 8/8 PASS (backward compatible with single-disease)
- Multi-disease: Manual verification pending

---

## Git Commit
```
feat(ex4): support multi-disease queries (step-next-132)
```

---

## DoD
- [x] Signature changed to `List[str]`
- [x] Multi-disease bubble/notes text
- [x] Handler extracts `disease_names` list
- [x] 8/8 tests PASS
- [ ] Manual test with "제자리암, 경계성종양" query
- [ ] CLAUDE.md updated
