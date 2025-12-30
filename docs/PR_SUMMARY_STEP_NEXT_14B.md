# PR Summary: STEP NEXT-14-β Chat UI Production Hardening

## Branch
`feat/step-next-14-chat-ui`

## Scope
Chat UI (STEP NEXT-14) + Production Hardening (STEP NEXT-14-β)

## Changes

### 1. Forbidden Language Policy (Single Source)
- **File**: `apps/api/policy/forbidden_language.py` (new)
- **Purpose**: Centralized validation for all text output
- **Approach**: Allowlist-first, context-aware pattern matching
- **Coverage**: title, summary_bullets, table cells, explanations, common notes, groups

### 2. Deterministic Intent Routing
- **File**: `apps/api/chat_vm.py`
- **Change**: Added `kind: Optional[MessageKind]` to `ChatRequest`
- **Purpose**: 100% deterministic routing when `kind` is explicitly set (from FAQ buttons)
- **Fallback**: Keyword-based routing when `kind=null` (not recommended for production)

### 3. VM Section Minimization (5 Core Types)
- **Purpose**: 1:1 mapping to Figma components
- **Section Types**:
  1. `comparison_table` (all table variants unified)
  2. `insurer_explanations` (parallel, no cross-reference)
  3. `common_notes` (unified with notices)
  4. `evidence_accordion` (collapsible, default collapsed)
  5. `summary` (top-level bullets, not a section)

### 4. Groups Extension (예시3 Visual Separation)
- **File**: `apps/api/chat_vm.py`
- **Change**: Added `BulletGroup` class and `CommonNotesSection.groups: Optional[List[BulletGroup]]`
- **Purpose**: Allow visual separation of "공통사항" and "유의사항" in Example 3
- **Backward Compatible**: `bullets` field retained for Examples 2/4

## Test Results

**Command**: `python -m pytest -q`
```
178 passed, 3 skipped, 15 warnings in 0.61s
```

## Test Execution Standard

**All tests must be executed using `python -m pytest`.**

Direct `pytest` execution is not supported due to current package layout. This is an **intentional decision** for STEP NEXT-14-β scope control. Import structure changes (e.g., pyproject.toml, editable install, sys.path manipulation) are **out-of-scope** for this Chat UI PR.

## Documentation

1. **`docs/ui/CUSTOMER_EXAMPLE_SCREEN_MAPPING.md`**
   - Customer example screen → ViewModel mapping specification
   - Example 2/3/4 block order and field mapping tables

2. **`docs/policy/FORBIDDEN_LANGUAGE_POLICY_SCOPE.md`**
   - Forbidden language policy application scope
   - Allowlist/forbidden patterns documentation
   - Evidence snippet exception handling

3. **`docs/STEP_NEXT_14B_PRODUCTION_GATE_REPORT.md`**
   - Production gate verification report
   - Test results, lock preservation verification
   - Step7 cleanup note

## Out-of-Scope (Intentional)

- ❌ Step7 pipeline changes (handled in dedicated PR)
- ❌ Import structure / package layout changes
- ❌ PYTHONPATH / sys.path manipulation
- ❌ pyproject.toml / editable install setup

## Lock Preservation

- ✅ Step7: No amount_fact writes
- ✅ Step11: AmountDTO status values unchanged
- ✅ Step12: Templates LOCKED, validator delegation only
- ✅ Step13: Frontend contract preserved (value_text display rules)

## Modified Files (Chat UI Scope Only)

```
M apps/api/chat_handlers.py      # BulletGroup import + groups usage
M apps/api/chat_vm.py             # BulletGroup class + groups field
M apps/api/policy/forbidden_language.py  # Pattern fix
M tests/test_chat_integration.py # Example3 groups validation
M tests/test_comparison_explanation.py  # Context-based pattern tests
```

## Next Steps

🎨 **Figma Component Implementation** (Frontend Integration)

The ViewModel structure is now production-ready with:
- 5 core section types mapped 1:1 to Figma components
- Deterministic routing capability
- Single-source forbidden language policy
- Visual separation support for Example 3

---

**PR Author**: Claude Code (STEP NEXT-14-β)
**Date**: 2025-12-29
**Status**: ✅ READY FOR REVIEW
