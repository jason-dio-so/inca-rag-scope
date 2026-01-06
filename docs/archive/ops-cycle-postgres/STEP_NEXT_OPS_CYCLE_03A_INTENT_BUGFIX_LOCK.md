# STEP NEXT-OPS-CYCLE-03-A: Intent Routing & Clarification Bugfix (FINAL)

**Date**: 2026-01-05
**Status**: ✅ LOCKED
**Scope**: Intent Router + Clarification Logic (NO data/DB changes)

---

## Purpose

Fix Intent Router and Handler bugs to complete Postgres SSOT migration:
- ✅ S3: `insurers >= 2` + "비교" → `EX3_COMPARE` (routing bug)
- ✅ S0: Coverage NOT_FOUND → `need_more_info=true` (clarification bug)

---

## Problem Summary (Evidence-Based)

### S3 Routing Bug

**Input**: `"삼성화재와 메리츠화재 암진단비 비교해줘"`
- **Expected**: `kind=EX3_COMPARE`
- **Actual**: `kind=EX2_LIMIT_FIND` (wrong routing)
- **Root Cause**: Intent Router had no rule for `insurers >= 2` + "비교" keywords

### S0 Clarification Bug

**Input**: `"삼성화재 알수없는담보명 설명해줘"`
- **Expected**: `need_more_info=true`, `missing_slots=["coverage_names"]`
- **Actual**: `need_more_info=false` (handler executed with `coverage_code=None`)
- **Root Cause**: Dispatcher called handler even when `coverage_code` missing (NOT_FOUND)

---

## Solution (Intent Router Logic ONLY)

### Fix 1: S3 Routing Rule (ABSOLUTE LOCK)

**Rule** (lines 218-226 of `apps/api/chat_intent.py`):
```python
if len(insurers) >= 2:
    comparison_keywords = ["비교", "차이"]
    if any(keyword in message_lower for keyword in comparison_keywords):
        return "EX3_COMPARE"
```

**Priority**:
1. Explicit `kind` from request (100%)
2. **insurers >= 2 + "비교" → EX3_COMPARE** (NEW - 100%)
3. insurers == 1 → EX2_DETAIL (100%)
4. detect_intent() fallback

**Constitutional Rule** (ABSOLUTE):
> `insurers.length >= 2` → ALWAYS `EX3_COMPARE` (IF "비교" keyword present)

### Fix 2: S0 Clarification Gate (BEFORE handler)

**Rule** (lines 861-873 of `apps/api/chat_intent.py`):
```python
# STEP NEXT-OPS-CYCLE-03-A: Coverage NOT_FOUND → Clarification (BEFORE handler)
if kind in ["EX2_DETAIL", "EX2_DETAIL_DIFF", "EX2_LIMIT_FIND", "EX3_COMPARE"]:
    coverage_code = compiled_query.get("coverage_code")
    if not coverage_code:
        return ChatResponse(
            request_id=request.request_id,
            need_more_info=True,
            missing_slots=["coverage_names"],
            clarification_options=None,
            message=None
        )
```

**Effect**:
- Coverage NOT_FOUND → return clarification BEFORE calling handler
- ❌ NO handler execution with `coverage_code=None`
- ❌ NO ValueError
- ✅ Clean clarification response

---

## Modified Files

1. **apps/api/chat_intent.py** (2 changes):
   - Lines 196-234: Intent Router with S3 routing rule
   - Lines 861-873: Clarification gate for S0

---

## Test Results (100% PASS)

**Test Suite**: `test_runtime_verification.py`

```
✓ PASS: S1_EX2_DETAIL (DB resolve works)
✓ PASS: S3_EX3_COMPARE (insurers >= 2 + "비교" → EX3_COMPARE)
✓ PASS: S0_NOT_FOUND (coverage NOT_FOUND → clarification)
✓ PASS: LOG_NO_FALLBACK (NO active JSONL fallback)
```

---

## Evidence (Runtime Logs)

### S3: EX3_COMPARE Routing (FIXED)

**Input**: `"삼성화재와 메리츠화재 암진단비 비교해줘"`

**Log**:
```
[INFO] [apps.api.chat_intent] Resolving coverage_code: kind=EX3_COMPARE, insurer=samsung, coverage_name=암진단비
[INFO] [core.db_lookup] [CoverageCodeLookup] Using Postgres backend
[INFO] [apps.api.chat_intent] Lookup result: status=LookupStatus.RESOLVED, coverage_code=A4200_1
[INFO] [apps.api.chat_handlers_deterministic] [EX3] Loading cards from: /Users/cheollee/inca-rag-scope/data/compare
[INFO] [example3_two_insurer_compare] [EX3] Loaded 31 cards for samsung
[INFO] [example3_two_insurer_compare] [EX3] Loaded 37 cards for meritz
```

**Result**: ✅ `kind=EX3_COMPARE` (NOT `EX2_LIMIT_FIND`)

### S0: NOT_FOUND → Clarification (FIXED)

**Input**: `"삼성화재 알수없는담보명 설명해줘"`

**Log**:
```
[INFO] [apps.api.chat_intent] Resolving coverage_code: kind=EX2_DETAIL, insurer=samsung, coverage_name=알수없는담보명
[INFO] [core.db_lookup] [CoverageCodeLookup] Using Postgres backend
[INFO] [apps.api.chat_intent] Lookup result: status=LookupStatus.NOT_FOUND, coverage_code=None, reason=No matches for '알수없는담보명' in samsung
[WARNING] [apps.api.chat_intent] Coverage code NOT_FOUND: No matches for '알수없는담보명' in samsung
```

**Response**:
```json
{
  "need_more_info": true,
  "missing_slots": ["coverage_names"],
  "message": null
}
```

**Result**: ✅ Clarification returned (NO handler execution, NO ValueError)

---

## Constitutional Rules (LOCKED)

### S3 Routing Rule (ABSOLUTE)

```
IF insurers.length >= 2 AND ("비교" OR "차이" in message):
  → kind = EX3_COMPARE

PRIORITY:
  1. Explicit kind (request.kind)
  2. insurers >= 2 + comparison keywords
  3. insurers == 1
  4. detect_intent() fallback
```

### S0 Clarification Rule (ABSOLUTE)

```
IF kind in [EX2_DETAIL, EX2_DETAIL_DIFF, EX2_LIMIT_FIND, EX3_COMPARE]
   AND coverage_code is None:
  → Return ChatResponse(need_more_info=true, missing_slots=["coverage_names"])

NO handler execution
NO ValueError
NO JSONL fallback
```

---

## Forbidden Changes (STRICT)

- ❌ PostgreSQL schema modification
- ❌ JSONL data modification
- ❌ DB migration
- ❌ EXAM type addition
- ❌ Business logic change (comparers, composers)
- ✅ Intent Router logic ONLY
- ✅ Clarification gate logic ONLY

---

## Verification Commands

### S3 Routing Test
```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"삼성화재와 메리츠화재 암진단비 비교해줘","insurers":["samsung","meritz"],"coverage_names":["암진단비"]}' \
  | python3 -m json.tool | grep '"kind"'

# Expected: "kind": "EX3_COMPARE"
```

### S0 Clarification Test
```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"삼성화재 알수없는담보명 설명해줘","insurers":["samsung"],"coverage_names":["알수없는담보명"]}' \
  | python3 -m json.tool | grep 'need_more_info\|missing_slots'

# Expected: "need_more_info": true, "missing_slots": ["coverage_names"]
```

### Full Test Suite
```bash
python3 test_runtime_verification.py

# Expected: ALL TESTS PASSED
```

---

## Definition of Success

> "보험사 2개 이상이면 무조건 EX3_COMPARE. Coverage NOT_FOUND면 무조건 clarification. DB/데이터는 건들지 말고 로직만 고쳐라."

**Acceptance Criteria**:
- ✅ S3: `insurers >= 2` + "비교" → `kind=EX3_COMPARE` (100%)
- ✅ S0: Coverage NOT_FOUND → `need_more_info=true` (100%)
- ✅ NO ValueError in logs (100%)
- ✅ NO JSONL fallback in logs (100%)

---

## SSOT Document

**This document is the canonical reference for Intent Routing & Clarification fixes.**

All future intent routing MUST:
1. Respect `insurers >= 2` + "비교" → `EX3_COMPARE` rule (ABSOLUTE)
2. Check `coverage_code` BEFORE calling handler
3. Return clarification when `coverage_code=None`
4. NO handler execution with missing required fields

**Status**: FINAL LOCK ✅
