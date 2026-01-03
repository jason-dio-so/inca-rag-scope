# STEP NEXT-112: EX3_COMPARE Comparison-First UX Lock

**Status**: ✅ LOCKED
**Date**: 2026-01-04
**Supersedes**: STEP NEXT-82 (deprecated bubble format)

---

## Executive Summary

EX3_COMPARE bubble_markdown has been **structurally redesigned** to address critical UX failures in comparison presentation.

### Problem Statement

Before STEP NEXT-112, EX3_COMPARE had the following critical issues:

1. **Abstract/Evasive Summary** ❌
   - "일부 보험사는 보장 '한도/횟수', 일부는 '보장금액' 기준으로 제공됩니다"
   - This repeats what's already visible in the table
   - Does NOT answer the customer's actual question: **"그래서 뭐가 다른데?"**
   - Feels like the system is **avoiding responsibility**

2. **Vertical Card Layout** ❌
   - 2 cards stacked vertically
   - Each card shows 1 insurer
   - Customer must:
     1. Read Meritz card
     2. Read Samsung card
     3. **Mentally compare** the two
   - This transfers **cognitive load to the customer**

3. **Key Differences Not Highlighted** ❌
   - Actual difference: Meritz (3천만원 정액) vs. Samsung (보험기간 중 1회)
   - But cards look similar → difference not visually salient
   - Customer can't see "what matters" at a glance

4. **No Conclusion/Interpretation** ❌
   - Customer's inevitable question: **"그럼 어느 쪽이 더 유리한 거예요?"**
   - We can't recommend ❌
   - We can't judge superiority ❌
   - But we MUST provide **structural interpretation** ✅
   - Current state: just lists facts, feels "cold and irresponsible"

### Solution (LOCKED)

**Definition of Success**:
> "Comparison is visually immediate, structural differences are explicit, and the system feels like it's thinking—without making judgments."

**3-Section Structure** (LOCKED):
1. **구조적 차이 요약** — Explicit structural comparison (NOT abstract)
2. **보장 기준 비교** — Side-by-side table (comparison-first design)
3. **해석 보조** — Neutral interpretation guide (NOT judgment)

---

## Constitutional Rules (LOCKED)

### Forbidden ❌

1. **Abstract/Evasive Summaries**
   - ❌ "일부 보험사는..." (some insurers...)
   - ❌ Generic patterns that avoid specifics
   - ❌ Repeating table contents without insight

2. **Vertical Card Layout**
   - ❌ Separate cards per insurer
   - ❌ Forcing customer to mentally compare
   - ❌ "1개 보험사" labels

3. **Recommendations / Superiority Judgments**
   - ❌ "더 좋다" / "더 유리하다"
   - ❌ "추천합니다" / "선택하세요"
   - ❌ Ranking / scoring

### Required ✅

1. **Explicit Structural Comparison**
   - ✅ Insurer names in summary
   - ✅ HOW coverage is defined (NOT which is better)
   - ✅ Structural basis: 정액 지급 / 한도 기준 / 횟수 기준

2. **Side-by-Side Comparison Table**
   - ✅ Same row = direct comparison
   - ✅ Markdown table format: `| 비교 항목 | Insurer1 | Insurer2 |`
   - ✅ At least 3 cells per row (item + 2 insurers)

3. **Neutral Interpretation Guide**
   - ✅ Structural implications (e.g., "정액 지급 → 지급액 명확")
   - ✅ Contextual to structure types
   - ✅ NO judgments, ONLY facts

---

## Format Specification (LOCKED)

### Section 1: 구조적 차이 요약 (Structural Difference Summary)

**Purpose**: Answer "그래서 뭐가 다른데?" explicitly

**Pattern (Different Basis)**:
```markdown
## 구조적 차이 요약

메리츠화재는 **정액 지급 방식**으로 보장이 정의되고,
삼성화재는 **지급 한도 기준**으로 보장이 정의됩니다.
```

**Pattern (Same Basis)**:
```markdown
## 구조적 차이 요약

삼성화재와 메리츠화재는 모두 **정액 지급 방식**으로 보장이 정의됩니다.
```

**Rules**:
- ❌ NO "일부 보험사는..."
- ✅ Explicit insurer names (display names ONLY)
- ✅ Structural basis: 정액 지급 방식 / 지급 한도 기준 / [payment_type] 방식 / 기본 보장 방식
- ✅ Deterministic priority: amount → limit → payment_type → fallback

**Structural Basis Priority**:
1. `amount != "명시 없음"` → **정액 지급 방식**
2. `limit_summary exists` → **지급 한도 기준**
3. `payment_type != "UNKNOWN"` → **{payment_type} 방식**
4. Fallback → **기본 보장 방식**

---

### Section 2: 보장 기준 비교 (Comparison Table)

**Purpose**: Enable direct side-by-side comparison (reduce cognitive load)

**Format** (LOCKED):
```markdown
## 보장 기준 비교

| 비교 항목 | 삼성화재 | 메리츠화재 |
|----------|---------|-----------|
| 보장 정의 기준 | 정액 지급 방식 | 지급 한도 기준 |
| 구체 내용 | 3천만원 | 보험기간 중 1회 |
| 지급유형 | 정액형 | 정액형 |
```

**Rules**:
- ✅ Markdown table format
- ✅ Columns: `비교 항목 | Insurer1 | Insurer2`
- ✅ Rows (minimum):
  - 보장 정의 기준 (ALWAYS)
  - 구체 내용 (if details exist)
  - 보장금액 (if not in 구체 내용)
  - 지급유형 (ALWAYS)
- ✅ Same row = direct comparison (NO vertical separation)
- ✅ Display names ONLY (NO insurer codes)

**Conditional Rows**:
- If `detail1` or `detail2` exists → show "구체 내용" row
- If NO details → show "보장금액" row instead
- "지급유형" always shown (use "표현 없음" for UNKNOWN)

---

### Section 3: 해석 보조 (Interpretation Guide)

**Purpose**: Help customer understand structural implications (NOT judge)

**Format** (Contextual to Structure Types):

**Mixed (Amount vs. Limit)**:
```markdown
## 해석 보조

- **정액 지급 방식**: 지급액이 명확하며, 조건 충족 시 확정된 금액을 받습니다.
- **한도 기준 방식**: 지급 조건(횟수, 기간 등)에 따라 실제 지급액이 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Both Amount-Based**:
```markdown
## 해석 보조

- 정액 지급 방식 상품은 지급액이 명확하며, 조건 충족 시 확정된 금액을 받습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Both Limit-Based**:
```markdown
## 해석 보조

- 한도 기준 상품은 지급 횟수, 기간 등 세부 조건 확인이 중요합니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Generic Fallback**:
```markdown
## 해석 보조

- 보장 정의 방식이 다르므로, 각 보험사의 지급 조건을 개별적으로 확인하시기 바랍니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Rules**:
- ❌ NO "더 좋다" / "추천" / "유리"
- ✅ Structural implications ONLY
- ✅ Contextual to detected structure types
- ✅ Neutral language ("명확하다", "확인이 중요하다", "달라질 수 있다")
- ✅ Always end with "아래 표에서 상세 비교 및 근거 문서를 확인하세요"

---

## Implementation

**File**: `apps/api/response_composers/ex3_compare_composer.py`

**Function**: `_build_bubble_markdown()`

**Logic**:

1. **Extract Data**:
   ```python
   amount1 = data1.get("amount", "명시 없음")
   limit1 = data1.get("kpi_summary", {}).get("limit_summary")
   payment1 = data1.get("payment_type", "UNKNOWN")
   ```

2. **Determine Structural Basis** (deterministic priority):
   ```python
   def get_definition_basis(amount, limit, payment):
       if amount != "명시 없음":
           return "정액 지급 방식", amount
       elif limit:
           return "지급 한도 기준", limit
       elif payment != "UNKNOWN":
           return f"{payment} 방식", None
       else:
           return "기본 보장 방식", None
   ```

3. **Build Section 1** (구조적 차이 요약):
   ```python
   if basis1 == basis2:
       lines.append(f"{insurer1_display}와 {insurer2_display}는 모두 **{basis1}**으로 보장이 정의됩니다.")
   else:
       lines.append(
           f"{insurer1_display}는 **{basis1}**으로 보장이 정의되고, "
           f"{insurer2_display}는 **{basis2}**으로 보장이 정의됩니다."
       )
   ```

4. **Build Section 2** (보장 기준 비교):
   ```python
   lines.append(f"| 비교 항목 | {insurer1_display} | {insurer2_display} |")
   lines.append("|----------|-------------------|-------------------|")
   lines.append(f"| 보장 정의 기준 | {basis1} | {basis2} |")
   if detail1 or detail2:
       lines.append(f"| 구체 내용 | {detail1 or '-'} | {detail2 or '-'} |")
   # ... (continue with conditional rows)
   ```

5. **Build Section 3** (해석 보조):
   ```python
   if "정액 지급" in basis1 or "정액 지급" in basis2:
       if "한도" in basis1 or "한도" in basis2:
           # Mixed case
           lines.append("- **정액 지급 방식**: 지급액이 명확하며...")
           lines.append("- **한도 기준 방식**: 지급 조건에 따라...")
       else:
           # Both amount-based
           lines.append("- 정액 지급 방식 상품은...")
   elif "한도" in basis1 and "한도" in basis2:
       # Both limit-based
       lines.append("- 한도 기준 상품은...")
   else:
       # Fallback
       lines.append("- 보장 정의 방식이 다르므로...")
   ```

**No LLM Usage**: All logic is deterministic pattern matching.

---

## Testing

**Contract Tests**: `tests/test_step_next_112_ex3_comparison_first.py`

**Test Coverage** (12 tests, 100% PASS):

### TestEX3ComparisonFirstStructure (4 tests)
1. ✅ `test_no_abstract_evasive_summary` — Forbids "일부 보험사는..."
2. ✅ `test_side_by_side_comparison_table_exists` — Table format validated
3. ✅ `test_same_row_comparison_not_vertical_cards` — At least 3 cells per row
4. ✅ `test_no_recommendation_or_superiority_judgment` — No "추천" / "유리"

### TestEX3StructuralDifferenceSummary (2 tests)
5. ✅ `test_structural_difference_when_different_basis` — Explicit insurer names + basis
6. ✅ `test_structural_summary_when_same_basis` — "모두" pattern

### TestEX3InterpretationGuide (3 tests)
7. ✅ `test_interpretation_guide_exists` — Section present, non-empty
8. ✅ `test_interpretation_guide_is_neutral` — No judgment keywords
9. ✅ `test_interpretation_guide_contextual_to_structure` — Adapts to structure types

### TestEX3RegressionProtection (3 tests)
10. ✅ `test_no_coverage_code_exposure` — NO A4200_1 in bubble
11. ✅ `test_no_insurer_code_exposure` — NO samsung/meritz in bubble (outside refs)
12. ✅ `test_response_kind_is_ex3_compare` — kind == "EX3_COMPARE"

**Regression Tests**: `tests/test_ex3_compare_schema_contract.py` (9 tests, 100% PASS)

**Deprecated**: `tests/test_ex3_bubble_markdown_step_next_82_DEPRECATED.py` (old format)

---

## Definition of Done (DoD)

### Functional Requirements ✅

- [x] "그래서 뭐가 다른지" is explicitly stated (NOT abstract)
- [x] Customer can compare two insurers on the same row
- [x] Comparison results are visually immediate (table-first design)
- [x] Structural differences are highlighted (보장 정의 기준)
- [x] Neutral interpretation helps customer judgment (NO recommendations)

### Technical Requirements ✅

- [x] NO LLM usage (deterministic only)
- [x] NO coverage_code in bubble_markdown (refs OK)
- [x] NO insurer codes in bubble_markdown (refs OK)
- [x] Display names ONLY (삼성화재, 메리츠화재, etc.)
- [x] All refs use `PD:` or `EV:` prefix
- [x] Response kind == "EX3_COMPARE"

### Test Requirements ✅

- [x] 12 new contract tests (STEP NEXT-112) — PASS
- [x] 9 schema contract tests (STEP NEXT-77) — PASS
- [x] ZERO coverage_code / insurer_code exposure
- [x] ZERO recommendation / judgment keywords

### UX Requirements ✅

- [x] Comparison table is the **visual center** (NOT buried below summary)
- [x] Customer doesn't need to "mentally compare" (table does it)
- [x] Structural difference is **discovered** (NOT hidden in generic text)
- [x] System feels like it's "thinking" (NOT just listing facts)
- [x] NO judgments, but interpretation feels helpful

---

## Before/After Comparison

### Before (STEP NEXT-82, DEPRECATED)

**구조 (Structure)**:
1. 핵심 요약 (선택 보험사, 비교 담보, 기준)
2. 한눈에 보는 결론 (보장금액 공통/상이, 지급유형, 주요 차이 있음/없음)
3. 세부 비교 포인트 (보험사별 1줄 요약 — **VERTICAL CARDS**)
4. 유의사항

**문제점**:
- ❌ Section 2 ("한눈에 보는 결론") is abstract: "보장금액: 상이"
  - Does NOT show the actual values side-by-side
  - Customer still has to scroll down to see details
- ❌ Section 3 ("세부 비교 포인트") lists insurers vertically:
  - "- **삼성화재**: 보장금액 3천만원, 정액형"
  - "- **메리츠화재**: 보장금액 5천만원, 정액형"
  - Customer must mentally compare bullet points
- ❌ NO explicit structural comparison
  - Just lists features, no insight into "HOW coverage is defined"
- ❌ Section 2 summary is vague:
  - "주요 차이: 있음 (대기기간 차이 확인)"
  - What about it? Why does it matter?

**Example Output** (Before):
```markdown
## 핵심 요약
- 선택한 보험사: 삼성화재, 메리츠화재
- 비교 대상 담보: 암진단비(유사암 제외)
- 기준 문서: 가입설계서

## 한눈에 보는 결론

- 보장금액: 상이 (삼성화재 3천만원, 메리츠화재 5천만원)
- 지급유형: 정액형
- 주요 차이: 없음 (동일 조건)

## 세부 비교 포인트

- **삼성화재**: 보장금액 3천만원, 정액형
- **메리츠화재**: 보장금액 5천만원, 정액형

## 유의사항

- 실제 지급 조건은 상품별 약관 및 가입 조건에 따라 달라질 수 있습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Cognitive Load**:
- Customer sees "상이" but must scroll to Section 3 to see actual values
- Values are in bullet points (not side-by-side)
- No explanation of structural implications

---

### After (STEP NEXT-112, LOCKED)

**구조 (Structure)**:
1. 구조적 차이 요약 (보장 정의 방식 — EXPLICIT)
2. 보장 기준 비교 (side-by-side table — COMPARISON-FIRST)
3. 해석 보조 (neutral interpretation — STRUCTURAL IMPLICATIONS)

**개선점**:
- ✅ Section 1: Explicit structural comparison
  - "삼성화재와 메리츠화재는 모두 **정액 지급 방식**으로 보장이 정의됩니다."
  - Customer immediately knows HOW coverage is defined
- ✅ Section 2: Side-by-side table (comparison-first design)
  - Values on the SAME ROW
  - Direct visual comparison (NO mental effort)
- ✅ Section 3: Neutral interpretation
  - "정액 지급 방식 상품은 지급액이 명확하며..."
  - Helps customer understand implications (NOT judgments)

**Example Output** (After):
```markdown
## 구조적 차이 요약

삼성화재와 메리츠화재는 모두 **정액 지급 방식**으로 보장이 정의됩니다.

## 보장 기준 비교

| 비교 항목 | 삼성화재 | 메리츠화재 |
|----------|---------|-----------|
| 보장 정의 기준 | 정액 지급 방식 | 정액 지급 방식 |
| 구체 내용 | 3천만원 | 5천만원 |
| 지급유형 | 정액형 | 정액형 |

## 해석 보조

- 정액 지급 방식 상품은 지급액이 명확하며, 조건 충족 시 확정된 금액을 받습니다.
- 아래 표에서 상세 비교 및 근거 문서를 확인하세요.
```

**Cognitive Load Reduction**:
- Customer sees structural basis FIRST
- Comparison table shows values side-by-side (SAME ROW)
- Interpretation explains structural implications

---

## Impact Analysis

**User Experience**:
- Before: "뭔가 분석은 했는데, 말은 안 해주는 시스템"
- After: "아, 이 시스템 생각하고 있네"

**Comparison Clarity**:
- Before: Comparison buried in vertical bullets
- After: Comparison visually immediate (table-first)

**Insight Depth**:
- Before: "보장금액 상이" (what)
- After: "정액 지급 방식으로 정의" (how)

**Actionability**:
- Before: Just facts, no guidance
- After: Structural interpretation helps decision-making

---

## Migration Notes

**STEP NEXT-82 → STEP NEXT-112**:
- Old format: 4 sections (핵심 요약, 한눈에 보는 결론, 세부 비교 포인트, 유의사항)
- New format: 3 sections (구조적 차이 요약, 보장 기준 비교, 해석 보조)
- Breaking change: Old tests deprecated (`test_ex3_bubble_markdown_step_next_82_DEPRECATED.py`)
- Schema contract preserved: `test_ex3_compare_schema_contract.py` still passes

**No Backend Changes** (View Layer Only):
- Data structure unchanged
- API endpoint unchanged
- Only bubble_markdown format redesigned

---

## Future Enhancements (Out of Scope)

1. **3+ Insurer Comparison** (current implementation: 2 insurers only)
   - Requires table column expansion
   - Pattern: `| 비교 항목 | Ins1 | Ins2 | Ins3 |`

2. **Interactive Table Sorting** (frontend)
   - Allow customer to sort by 보장금액, 지급유형, etc.
   - Requires frontend state management

3. **Difference Highlighting** (visual styling)
   - Highlight cells where values differ
   - Requires frontend CSS styling

---

## References

- **Schema SSOT**: `docs/ui/EX3_COMPARE_OUTPUT_SCHEMA.md`
- **Composer**: `apps/api/response_composers/ex3_compare_composer.py`
- **Tests**: `tests/test_step_next_112_ex3_comparison_first.py`
- **Frontend**: `apps/web/components/ChatPanel.tsx` (markdown rendering)

---

**Version**: STEP NEXT-112
**Lock Status**: ✅ LOCKED
**Next Review**: When expanding to 3+ insurer comparison
