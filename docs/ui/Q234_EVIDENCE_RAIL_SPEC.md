# Q2-Q4 Evidence Rail Specification

**Date**: 2026-01-17

**Purpose**: Apply Q1's Result/Evidence separation principle globally to Q2, Q3, and Q4

---

## 🎯 Global Principle (Result vs Evidence)

Following Q1's established pattern:

- **Result Area** = Numbers, conclusions, O/X/△ status ONLY
- **Evidence Rail** = Explanations, sources, reasons, formulas ONLY

This principle is **absolute** and applies to ALL question types (Q1-Q4).

---

## 📋 Current Q2-Q4 Components

### Q2: Coverage Limit Comparison
**Component**: `apps/web/components/chat/Q2LimitDiffView.tsx`

**Current State**: ✅ CLEAN
- Displays rank, insurer, product, limit values
- NO forbidden terms found
- Footer uses neutral "안내" term

**Future Requirements**:
- Evidence Rail: Q2EvidenceRail.tsx (not yet implemented)
- Rail should show:
  - Coverage definition source
  - Limit calculation methodology
  - Data source timestamp
  - Slot extraction evidence

---

### Q3: Comprehensive Comparison Report
**Component**: `apps/web/components/chat/Q3ThreePartView.tsx`

**Current State**: ✅ CLEAN
- Displays comparison table with amounts
- Delegates to Q12ReportView for full reports
- NO forbidden terms found

**Future Requirements**:
- Evidence Rail: Q3EvidenceRail.tsx (not yet implemented)
- Rail should show:
  - Overall assessment methodology
  - Recommendation reasoning
  - Data aggregation sources
  - LLM prompt/reasoning trace (if applicable)

---

### Q4: Support Matrix (O/X/△)
**Component**: `apps/web/components/chat/Q4SupportMatrixView.tsx`

**Current State**: ✅ CLEAN (after fix)
- Displays O/X/— matrix for coverage support
- Legend shows status icons
- Fixed: Changed "약관에서 근거를 찾지 못함" → "약관에서 확인되지 않음"

**Future Requirements**:
- Evidence Rail: Q4EvidenceRail.tsx (not yet implemented)
- Rail should show:
  - Coverage rule extraction evidence
  - Clause references from policy documents
  - Support status reasoning
  - Edge case handling notes

---

## 🚫 Forbidden Terms in Result Areas

These terms must NEVER appear in Q2-Q4 result components:

| Korean | English |
|--------|---------|
| 근거 | Evidence |
| 출처 | Source |
| 사유 | Reason |
| 기준 | Basis/Standard |
| 산출 | Calculation |
| 공식 | Formula |
| 배수 | Multiplier |
| % (except as context like "100%") | Percentage |

---

## ✅ Allowed Terms in Result Areas

| Korean | English | Context |
|--------|---------|---------|
| 정보 | Information | "상세 정보를 확인" |
| 안내 | Guidance | "안내: 모든 데이터는..." |
| 보기 | View | "상세 보기" |
| 확인 | Check | "약관에서 확인되지 않음" |

---

## 🛡️ Gate Enforcement

**Script**: `tools/gate/check_q234_result_no_evidence.sh`

**Checks**:
1. ✅ Q2LimitDiffView: No forbidden terms
2. ✅ Q3ThreePartView: No forbidden terms
3. ✅ Q4SupportMatrixView: No forbidden terms
4. ✅ Q2-Q4 pages: No forbidden terms (except EvidenceRail imports)
5. ✅ No percentage symbols in result components
6. ⚠️  Evidence Rails exist (currently none implemented)
7. ✅ Approved neutral terminology in use

**Current Status**: ALL CHECKS PASSED (7/7)

---

## 📐 Evidence Rail Design Guidelines

When implementing Q2-Q4 Evidence Rails, follow Q1's pattern:

### Structure
```tsx
export function Q{N}EvidenceRail({ selectedRow, onClose }: Props) {
  if (!selectedRow) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l shadow-xl">
      {/* Header: Rank badge + Name + Close button */}

      {/* Section 1: Primary Evidence */}
      <section>
        <h3>1. [Primary Data]</h3>
        {/* Show source, timestamp, methodology */}
      </section>

      {/* Section 2: Secondary Evidence */}
      <section>
        <h3>2. [Secondary Data]</h3>
        {/* Show additional context, calculations */}
      </section>

      {/* Section 3: Principles/Notes */}
      <section>
        <h3>3. 산출 원칙</h3>
        {/* Fixed bullets about SSOT principles */}
      </section>
    </div>
  );
}
```

### Visual Style
- Fixed position: `fixed right-0 top-0 h-full w-96`
- Z-index: `z-50` (above main content)
- Blue header: `bg-blue-600 text-white`
- Scrollable content: `overflow-y-auto`
- Close button: X icon in header

### Interaction
- Opens on row click in main table
- Selected row gets visual highlight (ring-2, bg-blue-50)
- Close button or clicking outside closes rail
- Only one row selected at a time

---

## 📝 Implementation Checklist

When implementing Evidence Rails for Q2-Q4:

- [ ] Create Q{N}EvidenceRail.tsx component
- [ ] Add selectedRow state to Q{N} page
- [ ] Pass onRowClick handler to result view
- [ ] Add visual highlight for selected rows
- [ ] Import and render EvidenceRail in page
- [ ] Define evidence sections based on data structure
- [ ] Add fixed "산출 원칙" section
- [ ] Test row click → rail open → close interaction
- [ ] Verify gate checks still pass
- [ ] Create smoke test documentation

---

## 🔒 Final Declaration

**Q1-Q4 全画面に適用される絶対原則:**

```
Result Area  = 結論のみ (数字/O/X/順位)
Evidence Rail = 説明のみ (근거/출처/기준/공식)
```

任何 "説明が混ざったテーブル" は明白な回帰とみなす。

---

## 📚 Reference

- Q1 Evidence Rail: `apps/web/components/q1/Q1EvidenceRail.tsx`
- Q1 Gate Script: `tools/gate/check_q1_evidence_rail.sh`
- Q1 Smoke Tests: `docs/ui/Q1_EVIDENCE_RAIL_SMOKE.md`
- Q1 Premium Table: `apps/web/components/q1/Q1PremiumTable.tsx`
