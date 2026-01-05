# STEP NEXT-141-θ: EX4 Subtype-Driven Rows Lock (REJECTED)

**Date**: 2026-01-05
**Status**: ❌ REJECTED (customer requirements clarified)
**Rejection Date**: 2026-01-05

---

## REJECTION REASON

**Customer Requirement (Confirmed)**:
- EX4 = **Coverage Matrix Compare** (customer/sales screen)
- **Rows = Coverage types** (진단비, 수술비, 항암약물, 표적항암, 다빈치수술) ✅
- **Columns = Insurers** (삼성화재, 메리츠화재)
- **Condition = Disease subtypes** (제자리암, 경계성종양) as filter

**What Customer Wants to See**:
> "For 제자리암/경계성종양 condition, which insurers cover which coverage types?"

**NOT** (what STEP NEXT-141-θ tried to do):
> "For each disease subtype, which insurers cover it?"

**Why STEP NEXT-130 is Correct**:
- Customer interest: "이 상품은 무엇을 보장해주나?" (What coverages?)
- NOT: "이 질병은 보장되나?" (Is this disease covered?)
- Coverage types (진단비/수술비) are the **primary comparison dimension**
- Disease subtypes (제자리암/경계성종양) are the **filter/condition**

**Design Confirmed**:
- STEP NEXT-130/131/132 = ✅ CORRECT (customer-facing design)
- STEP NEXT-141-θ = ❌ WRONG (misunderstood customer need)

---

## ORIGINAL DOCUMENT (REJECTED DESIGN)

**Supersedes**: STEP NEXT-130/131/132 (EX4 coverage-type rows design)
**Status**: LOCKED (NOW REJECTED)

---

## Purpose

Fix EX4 table structure to **use disease subtypes as rows** instead of coverage types, matching user expectation when clicking EX4 preset button "제자리암, 경계성종양 보장여부 비교해줘".

**Core Question EX4 Answers**:
> "Does this insurer cover 제자리암/경계성종양?"

**NOT** (previous design):
> "Does this insurer have 진단비/수술비/항암약물 coverage for cancer?"

---

## Final Decision (No Further Discussion)

✅ **Option B confirmed**: Subtype-driven rows (disease subtypes = table rows)

❌ **Option A rejected**: Coverage-type rows (진단비/수술비/항암약물 = table rows)

**Rationale**:
- EX4 preset query: "제자리암, 경계성종양 보장여부 비교해줘"
- User mental model: "Which insurers cover each subtype?"
- Coverage types (진단비/수술비 etc.) are orthogonal to disease subtypes

---

## Core Rules (ABSOLUTE)

### Table Structure (LOCKED)

| Element | Rule |
|---------|------|
| **Table count** | 1 table ONLY (NOT one per subtype) |
| **Rows** | `request.disease_subtypes` (e.g., ["제자리암", "경계성종양"]) |
| **Columns** | "질병 구분" + insurer display names |
| **Cell values** | O / X / UNKNOWN (deterministic keyword match) |
| **Inference** | ❌ FORBIDDEN (근거 없으면 UNKNOWN) |

### Forbidden Output (ABSOLUTE)

❌ **Coverage-type rows**:
- 진단비
- 수술비
- 항암약물
- 표적항암
- 다빈치수술

❌ **Generic cancer text**:
- "암 보장 가능 여부"
- "암진단비 보장 여부"

❌ **Multiple tables**:
- One table per subtype (STEP NEXT-132 design) → REMOVED
- MUST be single table with multiple rows

### Semantic Rules

**EX4 Question** (LOCKED):
> "이 보험사는 제자리암 / 경계성종양을 보장하는가?"

**NOT EX4 Questions**:
- "암에 어떤 담보들이 있나?" → Different exam type
- "수술비/항암약물 보장 여부?" → Different exam type

---

## Implementation

### Modified Files

**1. `apps/api/response_composers/ex4_eligibility_composer.py`**

**Header Changes** (lines 1-30):
- Updated docstring to reflect STEP NEXT-141-θ design
- Removed STEP NEXT-130/131/132 references
- Added FORBIDDEN OUTPUT list

**Class Changes** (lines 43-59):
- **REMOVED**: `FIXED_CATEGORIES` constant (5 coverage types)
- **REMOVED**: `CATEGORY_KEYWORDS` dict (coverage type keyword mappings)
- **ADDED**: `SUBTYPE_KEYWORDS_MAP` dict (disease subtype keyword mappings)

**compose() Method** (lines 61-132):
- Changed from "one table per subtype" to "single table with subtype rows"
- Removed loop: `for subtype_keyword in subtype_keywords:`
- Single call: `_build_subtype_ox_table(insurers, subtype_keywords, coverage_cards)`

**New Method**: `_build_subtype_ox_table()` (lines 173-230)
```python
def _build_subtype_ox_table(
    insurers: List[str],
    subtype_keywords: List[str],
    coverage_cards: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build O/X eligibility table with disease subtypes as rows

    Columns: ["질병 구분"] + insurer display names
    Rows: subtype_keywords (e.g., ["제자리암", "경계성종양"])
    Cell values: "O" or "X" or "UNKNOWN"
    """
```

**Replaced Method**: `_determine_subtype_ox_status()` (lines 232-287)
- **OLD**: `_determine_ox_status(insurer, category, subtype_keyword, coverage_cards)`
- **NEW**: `_determine_subtype_ox_status(insurer, subtype_keyword, coverage_cards)`
- Logic: Match `subtype_keyword` in `coverage_name_raw` (NOT category keywords)
- O: Subtype keyword found in coverage
- X: Subtype keyword NOT found (NO inference)

**Updated**: `_build_notes_section()` (lines 289-321)
- Simplified bullets (removed coverage-type explanation)
- "O: 보장 가능, X: 보장 제외"
- Subtype-focused guidance

**Updated**: `_build_bubble_markdown()` (lines 323-367)
- **REMOVED**: Coverage-type mentions
- **REMOVED**: "암 보장 가능 여부" generic text
- **ADDED**: Subtype-specific confirmation ("제자리암 및 경계성종양의 보장 가능 여부를 확인했습니다")

---

## Logic Changes

### STEP NEXT-130/131/132 (OLD - DEPRECATED)

**Table structure**:
- 2 tables (one per subtype: 제자리암, 경계성종양)
- Each table: 5 rows (진단비/수술비/항암약물/표적항암/다빈치수술)
- O/X logic: Category keyword match (e.g., "진단" in coverage_name_raw)

**Title**:
- "제자리암 보장 가능 여부" (first table)
- "경계성종양 보장 가능 여부" (second table)

**Bubble**:
- "제자리암, 경계성종양 보장 가능 여부를 각각 확인했습니다"
- "표에서 O/X로 확인하세요"

---

### STEP NEXT-141-θ (NEW - CURRENT)

**Table structure**:
- **1 table** (single table for all subtypes)
- Rows: ["제자리암", "경계성종양"] (subtype keywords)
- Columns: ["질병 구분", "삼성화재", "메리츠화재"]
- O/X logic: Subtype keyword match (e.g., "제자리암" in coverage_name_raw)

**Title**:
- "제자리암, 경계성종양 보장 가능 여부" (single title)
- OR "보장 가능 여부" (generic, for multi-subtype case)

**Bubble**:
- "제자리암 및 경계성종양의 보장 가능 여부를 확인했습니다"
- "표에서 보험사별 보장 여부를 확인하세요"

---

## Verification Scenarios

### S1: EX4 Preset → Insurer Selection → Table Display (CRITICAL)

**Steps**:
1. Click EX4 preset: "제자리암, 경계성종양 보장여부 비교해줘"
2. Send message
3. Select 2 insurers (e.g., samsung, meritz)
4. Click confirm

**Expected** ✅:
- **Left bubble**:
  - "제자리암 및 경계성종양의 보장 가능 여부를 확인했습니다"
  - NO "진단비", NO "수술비", NO "암 보장 가능 여부"

- **Right panel table**:
  - Title: "보장 가능 여부"
  - Columns: ["질병 구분", "삼성화재", "메리츠화재"]
  - Rows: **2 rows exactly** (제자리암, 경계성종양)
  - NO 진단비/수술비/항암약물/표적항암/다빈치수술 rows

- **Table cells**:
  - O / X values (deterministic keyword match)
  - Evidence refs attached (PD:samsung:*, PD:meritz:*)

**Forbidden** ❌:
- Coverage-type rows (진단비, 수술비 etc.)
- Multiple tables (one per subtype)
- Generic "암 보장 가능 여부" text
- 5-row table format

**Status**: [ ] PASS / [ ] FAIL

---

### S2: Coverage-Type Contamination Check (CRITICAL)

**Steps**:
1. Complete S1
2. Search response for forbidden keywords

**Expected** ✅:
- Search results: **0 matches** for:
  - "진단비"
  - "수술비"
  - "항암약물"
  - "표적항암"
  - "다빈치수술"
  - "암 보장 가능 여부"

**Forbidden** ❌:
- Any coverage-type keyword in bubble / title / table rows

**Status**: [ ] PASS / [ ] FAIL

---

### S3: Table Row Count Check (CRITICAL)

**Steps**:
1. Complete S1
2. Count table rows in response

**Expected** ✅:
- Row count: **2** (제자리암, 경계성종양)
- NOT 5 rows (coverage types)
- NOT 10 rows (2 tables × 5 rows)

**Status**: [ ] PASS / [ ] FAIL

---

### S4 (Regression): Single Subtype Query

**Steps**:
1. Type: "제자리암 보장여부 비교해줘"
2. Send
3. Select 2 insurers
4. Confirm

**Expected** ✅:
- Table: **1 row** (제자리암)
- Title: "제자리암 보장 가능 여부"
- Bubble: "제자리암 보장 가능 여부를 확인했습니다"
- NO coverage-type rows

**Status**: [ ] PASS / [ ] FAIL

---

## Constitutional Basis

**STEP NEXT-129R**: Customer Self-Test Flow
- ✅ NO auto-send / auto-route
- ✅ Predictable UX (same input → same output)

**STEP NEXT-133**: Slot-Driven Clarification
- ✅ Missing slot → clarification UI shown
- ✅ Resolved slot → NO UI exposure

**STEP NEXT-141**: EX4 Preset Routing Lock
- ✅ Preset button → explicit intent (100% confidence)

**STEP NEXT-141-δ**: EX4 Context Isolation
- ✅ EX4 NO context fallback for insurers

**STEP NEXT-141-ζζ**: EX4 Coverage Gating Fix
- ✅ EX4 coverage gating bypassed at UI level

**STEP NEXT-141-θ**: EX4 Subtype-Driven Rows (THIS STEP)
- ✅ EX4 table rows = disease_subtypes (ABSOLUTE)
- ❌ NO coverage-type rows for EX4 (ABSOLUTE)

---

## Regression Prevention

- ✅ STEP NEXT-129R preserved (NO auto-send, NO silent correction)
- ✅ STEP NEXT-133 preserved (Slot-driven clarification)
- ✅ STEP NEXT-138 preserved (Single-insurer explanation guard)
- ✅ STEP NEXT-141 preserved (EX4 preset routing lock)
- ✅ STEP NEXT-141-δ preserved (EX4 context isolation)
- ✅ STEP NEXT-141-ζζ preserved (EX4 coverage gating fix)
- ✅ **EX2/EX3 unchanged** (NO impact on other exam types)

---

## Build Status

✅ **Backend syntax check**: PASSED (`python3 -m py_compile`)

---

## Definition of Success

> "EX4 프리셋 → 보험사 선택 → 확인. 표에 제자리암/경계성종양 행 2개만 표시. 진단비/수술비/항암약물 등 coverage-type 문자열 0%."

---

## Key Insight

**Design Evolution**:
1. **STEP NEXT-130**: Fixed 5 coverage-type rows (진단비/수술비/항암약물/표적항암/다빈치수술)
2. **STEP NEXT-131**: Relaxed O/X logic (category ONLY, NOT category + subtype)
3. **STEP NEXT-132**: Multi-disease support (one table per subtype)
4. **STEP NEXT-141-θ**: **Subtype-driven rows** (disease subtypes = rows, NOT coverage types)

**Why Change**:
- User clicks EX4 preset: "제자리암, 경계성종양 보장여부 비교해줘"
- User expects: "Which insurers cover 제자리암? Which cover 경계성종양?"
- NOT: "What coverage types exist for cancer?"
- **Coverage types (진단비/수술비) are orthogonal to disease subtypes (제자리암/경계성종양)**

**Trade-off**:
- **Gain**: User mental model match (100%)
- **Loss**: Coverage-type overview (moved to different exam type)
- **Decision**: User expectation > internal design preference

---

## STEP NEXT-130/131/132 Status

**DEPRECATED** (replaced by STEP NEXT-141-θ):
- Coverage-type row design is NO LONGER ACTIVE for EX4
- Can be repurposed for different exam type (e.g., EX5) if needed
- Tests for STEP NEXT-130/131/132 MUST be updated or removed

---

## Next Steps

1. **User Testing**: Verify S1-S4 scenarios
2. **Regression Testing**: Confirm EX2/EX3 unchanged
3. **Test Update**: Modify/remove tests expecting coverage-type rows
4. **Documentation**: Update CLAUDE.md with STEP NEXT-141-θ section

---

**LOCKED**: This is the final EX4 table structure. No further design changes allowed without new STEP NEXT number.
