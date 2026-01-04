# STEP NEXT-130: EX4 O/X Eligibility Table — Customer Self-Test Lock

**Date**: 2026-01-04
**Status**: ✅ LOCKED
**SSOT**: This document is the canonical reference for EX4_ELIGIBILITY O/X table implementation
**Constitutional Basis**: STEP NEXT-129R (Customer Self-Test Flow)

---

## 0. Purpose

Enable customer self-test for disease subtype eligibility (제자리암/경계성종양) by showing a **simple O/X table** that answers:
- "Which coverage types support this subtype?"
- Fixed 2 insurers (samsung, meritz)
- Fixed 5 categories (진단비, 수술비, 항암약물, 표적항암, 다빈치수술)
- O/X only (NO △/Unknown/조건부)

**Definition of Success**:
> "고객이 표를 10초 안에 읽고 'O는 지원, X는 미지원'을 즉시 이해하면 성공"

---

## 1. Constitutional Rules (ABSOLUTE)

From STEP NEXT-129R:

### 1.1 Forbidden (ZERO TOLERANCE)
- ❌ **NO LLM usage** (deterministic keyword matching ONLY)
- ❌ **NO recommendation/judgment** ("유리", "불리", "좋", "나쁨", "추천")
- ❌ **NO △/Unknown** in cells (O or X ONLY)
- ❌ **NO auto-complete/forced routing** (user action required)
- ❌ **NO coverage_code UI exposure** (A4200 등 금지)
- ❌ **NO pipeline/data/search changes** (view layer ONLY)

### 1.2 Required (MANDATORY)
- ✅ **Fixed 5 rows** (진단비, 수술비, 항암약물, 표적항암, 다빈치수술)
- ✅ **Fixed 2 insurers** (samsung, meritz) — hardcoded for demo
- ✅ **O/X only** (binary eligibility)
- ✅ **Display names ONLY** (삼성화재, 메리츠화재)
- ✅ **Deterministic keyword matching** (NO LLM, NO inference)
- ✅ **Evidence refs attached** (PD: format)
- ✅ **Left bubble: 2-4 sentences** (short guidance)

---

## 2. Implementation Specification

### 2.1 Data Structure

**Input**:
- `insurers`: List[str] — default ["samsung", "meritz"] if not provided
- `subtype_keyword`: str — e.g., "제자리암", "경계성종양"
- `coverage_cards`: List[Dict] — from `data/compare/*_coverage_cards.jsonl`

**Output**:
```json
{
  "kind": "EX4_ELIGIBILITY",
  "title": "{subtype_keyword} 보장 가능 여부",
  "summary_bullets": [
    "{subtype_keyword}에 대한 보장 가능 여부를 확인했습니다",
    "표에서 O/X로 확인하세요"
  ],
  "sections": [
    {
      "kind": "comparison_table",
      "table_kind": "ELIGIBILITY_OX_TABLE",
      "title": "{subtype_keyword} 보장 가능 여부",
      "columns": ["비교 항목", "삼성화재", "메리츠화재"],
      "rows": [
        {
          "cells": [
            {"text": "진단비"},
            {"text": "O"},
            {"text": "O"}
          ],
          "meta": {
            "evidence_refs": ["PD:samsung:A4200", "PD:meritz:A5200"]
          }
        },
        ...
      ]
    },
    {
      "kind": "common_notes",
      "title": "유의사항",
      "bullets": [
        "O: 보장 가능, X: 보장 제외",
        "가입설계서 및 약관 기준입니다",
        "실제 보장 여부는 약관을 직접 확인하시기 바랍니다"
      ]
    }
  ],
  "bubble_markdown": "**제자리암** 보장 가능 여부를 확인했습니다.\n\n표에서 **O/X**로 확인하세요.\nO는 보장 가능, X는 보장 제외입니다.",
  "lineage": {
    "handler": "EX4EligibilityComposer",
    "llm_used": false,
    "deterministic": true,
    "step_next": "130"
  }
}
```

### 2.2 Fixed 5 Categories (LOCKED)

| Category    | Keywords                                    |
|-------------|---------------------------------------------|
| 진단비      | `["진단", "진단비"]`                        |
| 수술비      | `["수술", "수술비"]`                        |
| 항암약물    | `["항암", "약물", "항암약물", "화학", "화학요법"]` |
| 표적항암    | `["표적", "표적항암", "표적치료"]`           |
| 다빈치수술  | `["다빈치", "로봇", "로봇수술"]`             |

**Row order is FIXED** (no reordering, no dynamic filtering)

### 2.3 O/X Determination Logic (Deterministic)

For each `(insurer, category, subtype_keyword)` cell:

1. **Filter coverage cards**:
   - `card.insurer == insurer`
   - `any(keyword in card.coverage_name_raw.lower() for keyword in category_keywords)`

2. **Check subtype match**:
   - Search in `card.evidences[].snippet`
   - Search in `card.proposal_facts.evidences[].snippet`
   - If `subtype_keyword in snippet` → subtype_match = True

3. **Determine O/X**:
   - If `category_match AND subtype_match` → **O**
   - Else → **X**

4. **Extract refs** (for O cells):
   - Format: `PD:{insurer}:{coverage_code}`
   - Limit: 3 refs per row

**NO exceptions, NO fallback to LLM, NO △/Unknown allowed**

### 2.4 Left Bubble (2-4 Sentences)

Template (LOCKED):
```markdown
{coverage_display_name 중 }**{subtype_keyword}** 보장 가능 여부를 확인했습니다.

표에서 **O/X**로 확인하세요.
O는 보장 가능, X는 보장 제외입니다.
```

**Character limit**: < 300 chars
**Sentence count**: 2-4 sentences
**Forbidden**: recommendation, judgment, tables, lists, sections

---

## 3. Contract Tests

**File**: `tests/test_step_next_130_ex4_ox_table.py`
**Status**: 8/8 PASS

| Test | Requirement                                          | Status |
|------|------------------------------------------------------|--------|
| 1    | Fixed 5 rows (진단비, 수술비, 항암약물, 표적항암, 다빈치수술) | ✅ PASS |
| 2    | O/X only (NO △/Unknown)                              | ✅ PASS |
| 3    | Display names only (NO insurer code)                 | ✅ PASS |
| 4    | Bubble length 2-4 sentences                          | ✅ PASS |
| 5    | NO recommendation in bubble                          | ✅ PASS |
| 6    | NO coverage_code exposure                            | ✅ PASS |
| 7    | Evidence refs attached to O cells                    | ✅ PASS |
| 8    | Deterministic O/X logic (keyword matching)           | ✅ PASS |

---

## 4. Modified Files

### 4.1 Code Changes
- `apps/api/response_composers/ex4_eligibility_composer.py` (REPLACED)
  - New: `_build_ox_table_section()` — fixed 5 rows, O/X only
  - New: `_determine_ox_status()` — deterministic keyword matching
  - New: `_build_bubble_markdown()` — 2-4 sentences
  - Removed: Overall evaluation section (judgment/recommendation)
  - Removed: Eligibility matrix (△/Unknown support)

### 4.2 Tests Added
- `tests/test_step_next_130_ex4_ox_table.py` (NEW, 8 tests)

### 4.3 Documentation
- `docs/audit/STEP_NEXT_130_EX4_OX_TABLE_LOCK.md` (this file)

---

## 5. Example Scenarios

### Scenario 1: "제자리암 보장되나요?"
**Input**:
- insurers: `["samsung", "meritz"]`
- subtype_keyword: `"제자리암"`
- coverage_cards: (loaded from data/compare/)

**Output**:
- Table with 5 rows × 3 columns
- O/X values based on coverage_cards matching
- Bubble: "**제자리암** 보장 가능 여부를 확인했습니다..."

### Scenario 2: "경계성종양 기준으로 항암약물/표적항암/다빈치수술?"
**Input**:
- insurers: `["samsung", "meritz"]`
- subtype_keyword: `"경계성종양"`
- coverage_cards: (loaded from data/compare/)

**Output**:
- Same 5-row table (ALL 5 categories shown, not just 3)
- O/X based on "경계성종양" keyword match
- Bullet: "표에서 O/X로 확인하세요"

---

## 6. Limitations & Trade-offs

### 6.1 Current Limitations
1. **Fixed 2 insurers** (samsung, meritz) — hardcoded for demo
2. **Keyword matching only** — may have false positives (e.g., "표적항암" matches "항암약물")
3. **Binary O/X** — no nuance for "감액" or "조건부"
4. **NO dynamic filtering** — always shows all 5 rows (even if all X)

### 6.2 Why These Trade-offs?
- **Customer self-test priority**: Simple, reproducible, scannable at-a-glance
- **NO LLM constitutional lock**: Deterministic only for STEP NEXT-129R
- **Fixed format**: Consistent UX for demo/testing flow

### 6.3 Future Enhancements (NOT NOW)
- Support N insurers (dynamic columns)
- Add "감액" indicator (O*)
- Dynamic category filtering (hide all-X rows)
- **Pre-condition**: Requires NEW STEP, NOT in STEP NEXT-130

---

## 7. Regression Prevention

### 7.1 Anti-patterns (FORBIDDEN)
```python
# ❌ FORBIDDEN: LLM inference
eligibility_status = call_llm("Is 제자리암 covered?")

# ❌ FORBIDDEN: △/Unknown in cells
cell_value = "△" if has_condition else "O"

# ❌ FORBIDDEN: Dynamic row filtering
if all_x:
    rows = [row for row in rows if has_o(row)]

# ❌ FORBIDDEN: Recommendation
bubble += "삼성화재가 유리합니다"
```

### 7.2 Valid Patterns (ALLOWED)
```python
# ✅ ALLOWED: Deterministic keyword matching
category_match = any(kw in coverage_name.lower() for kw in keywords)

# ✅ ALLOWED: Binary O/X
status = "O" if (category_match and subtype_match) else "X"

# ✅ ALLOWED: Fixed 5 rows
for category in FIXED_CATEGORIES:
    build_row(category)

# ✅ ALLOWED: Evidence refs
refs = [f"PD:{insurer}:{code}" for card in matching_cards]
```

---

## 8. Git Commit Message

```
feat(ex4): add OX eligibility table for subtype self-test (step-next-130)

STEP NEXT-130: EX4 O/X Eligibility Table — Customer Self-Test Lock

Changes:
- Replace EX4_ELIGIBILITY composer with fixed 5-row O/X table
- Fixed categories: 진단비, 수술비, 항암약물, 표적항암, 다빈치수술
- O/X only (NO △/Unknown/조건부)
- Deterministic keyword matching (NO LLM)
- Left bubble: 2-4 sentences (short guidance)
- Fixed 2 insurers: samsung, meritz (demo mode)

Tests: 8/8 PASS (test_step_next_130_ex4_ox_table.py)

Constitutional basis: STEP NEXT-129R (Customer Self-Test Flow)
- NO LLM usage
- NO recommendation/judgment
- NO auto-complete
- View layer ONLY

Files:
- Modified: apps/api/response_composers/ex4_eligibility_composer.py
- Added: tests/test_step_next_130_ex4_ox_table.py
- Added: docs/audit/STEP_NEXT_130_EX4_OX_TABLE_LOCK.md
```

---

## 9. Definition of Done (DoD)

- [x] Fixed 5 rows table implemented
- [x] O/X only (NO △/Unknown)
- [x] Display names only (NO code exposure)
- [x] Deterministic keyword matching
- [x] Left bubble 2-4 sentences
- [x] Evidence refs attached
- [x] 8/8 contract tests PASS
- [x] NO recommendation/judgment
- [x] SSOT documentation complete
- [ ] CLAUDE.md updated
- [ ] Git committed with proper message

---

**LOCKED**: 2026-01-04
**Next Step**: CLAUDE.md update → Git commit → Manual verification
