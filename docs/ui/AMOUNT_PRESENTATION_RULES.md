# Amount Presentation Rules (UI/Frontend)

**Version**: 1.1.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29 (Updated: STEP NEXT-17)
**Applies To**: All UI/Frontend implementations

---

## 🎯 Purpose

This document defines **IMMUTABLE presentation rules** for displaying amount data in user interfaces.

**CRITICAL**: These rules ensure:
1. **Factual presentation** (no interpretation)
2. **Status-based display** (CONFIRMED | UNCONFIRMED | NOT_AVAILABLE)
3. **No comparisons** (no ranking, no recommendations)

---

## 📋 Core Principles

### P1. Status-Based Presentation
- Display logic is **LOCKED** to `status` field
- Each status has **fixed** presentation rules
- **NO custom styling** based on amount value

### P2. Factual Display Only
- Show `value_text` **as-is** for CONFIRMED
- Show **fixed text** for UNCONFIRMED/NOT_AVAILABLE
- **NO** parsing, formatting, or conversion

### P3. No Comparisons
- **NO** color coding for "better/worse"
- **NO** sorting by amount value
- **NO** highlighting max/min
- **NO** calculations (average, total, etc.)
- **NO** charts or visualizations comparing amounts

### P4. Accessibility
- Status must be **semantically marked** (not just color)
- Screen readers must announce status
- Tooltips provide context

---

## 🎨 Status Presentation Rules (LOCKED)

### CONFIRMED

**Meaning**: Amount explicitly stated in proposal document + evidence exists

**Display** (STEP NEXT-17 Updated):
```
Display Text: Unified format (e.g., "1,000만원")
Font Weight: Normal (400)
Color: Inherit (default text color)
Background: None
Icon: None
```

**Format Unification (STEP NEXT-17)**:
- "3천만원" → "3,000만원"
- "6백만원" → "600만원"
- "3000만원" → "3,000만원"
- Commas REQUIRED for thousands

**Tooltip/Help**:
```
"가입설계서에 명시된 금액입니다"
```

**HTML Example**:
```html
<td class="amount-confirmed">
  <span class="amount-value">1천만원</span>
  <span class="amount-tooltip" aria-label="가입설계서에 명시된 금액입니다">
    ⓘ
  </span>
</td>
```

**CSS Example**:
```css
.amount-confirmed {
  font-weight: 400;
  color: inherit;  /* NO special coloring */
}

.amount-value {
  display: inline-block;
}
```

**Forbidden**:
- ❌ Green color (implies "good")
- ❌ Bold font (implies "highlight")
- ❌ Checkmark icon (implies "recommended")

---

### UNCONFIRMED

**Meaning**: Coverage exists but amount not stated in documents

**Display** (STEP NEXT-17 Updated):

**Type A/B Insurers (Samsung, Lotte, Heungkuk, Meritz, DB)**:
```
Display Text: "금액 명시 없음" (FIXED)
Font Weight: Normal (400)
Color: #666666 (gray)
Font Style: Italic
Background: None
Icon: None or ⚠️
```

**Type C Insurers (Hanwha, Hyundai, KB)**:
```
Display Text: "보험가입금액 기준" (FIXED)
Font Weight: Normal (400)
Color: #666666 (gray)
Font Style: Italic
Background: None
Icon: None
```

**Tooltip/Help**:

Type A/B:
```
"문서상 금액이 명시되지 않았습니다.
해당 담보는 존재하나 금액 정보를 확인할 수 없습니다."
```

Type C:
```
"이 보험사는 담보별 금액을 별도로 표시하지 않고
보험가입금액을 기준으로 보장을 제공합니다."
```

**HTML Example**:
```html
<td class="amount-unconfirmed">
  <span class="amount-placeholder">금액 명시 없음</span>
  <span class="amount-tooltip" aria-label="문서상 금액이 명시되지 않았습니다">
    ⚠️
  </span>
</td>
```

**CSS Example**:
```css
.amount-unconfirmed {
  color: #666666;
  font-style: italic;
}

.amount-placeholder {
  opacity: 0.7;
}
```

**Forbidden**:
- ❌ Red color (implies "error")
- ❌ "N/A" or "-" (ambiguous)
- ❌ Empty cell (loses information)

---

### NOT_AVAILABLE

**Meaning**: Coverage itself does not exist for this insurer/product

**Display**:
```
Display Text: "해당 담보 없음" (FIXED)
Font Weight: Normal (400)
Color: #999999 (light gray)
Text Decoration: Strikethrough
Background: #f5f5f5 (light gray)
Icon: None or ⊘
```

**Tooltip/Help**:
```
"해당 보험사/상품에 이 담보가 없습니다"
```

**HTML Example**:
```html
<td class="amount-not-available">
  <span class="amount-unavailable">해당 담보 없음</span>
</td>
```

**CSS Example**:
```css
.amount-not-available {
  color: #999999;
  background-color: #f5f5f5;
  text-decoration: line-through;
}

.amount-unavailable {
  font-style: italic;
  opacity: 0.6;
}
```

**Forbidden**:
- ❌ Hiding the cell (loses information)
- ❌ Showing "0원" (implies $0 coverage)
- ❌ Showing "-" (ambiguous with UNCONFIRMED)

---

## 📊 Comparison Table Layout

### Example: Product Summary Table

```
┌────────────────┬──────────┬──────────┬──────────┐
│ 담보명          │ 삼성     │ 한화     │ 현대     │
├────────────────┼──────────┼──────────┼──────────┤
│ 암진단비        │ 3천만원  │ 2천만원  │ 3천만원  │  <- CONFIRMED
│ 질병사망        │ 1천만원  │ 금액명시없음 │ 5백만원  │  <- UNCONFIRMED (한화)
│ 상해후유장해    │ 1천만원  │ 해당담보없음 │ 1천만원  │  <- NOT_AVAILABLE (한화)
└────────────────┴──────────┴──────────┴──────────┘
```

**Rules**:
- Each cell follows status-based presentation
- NO column sorting by amount
- NO color gradients across rows
- NO highlighting "best value"

---

## 🚫 Forbidden Presentations

### ❌ Comparison Coloring

**FORBIDDEN**:
```html
<!-- ❌ WRONG: Color coding implies ranking -->
<td class="amount-high" style="color: green">3천만원</td>
<td class="amount-medium" style="color: orange">2천만원</td>
<td class="amount-low" style="color: red">1천만원</td>
```

**CORRECT**:
```html
<!-- ✅ CORRECT: Neutral presentation -->
<td class="amount-confirmed">3천만원</td>
<td class="amount-confirmed">2천만원</td>
<td class="amount-confirmed">1천만원</td>
```

---

### ❌ Highlighting Max/Min

**FORBIDDEN**:
```html
<!-- ❌ WRONG: Highlighting implies recommendation -->
<td class="amount-best" style="font-weight: bold; background: yellow">
  3천만원 ⭐ 최고
</td>
```

**CORRECT**:
```html
<!-- ✅ CORRECT: All amounts shown equally -->
<td class="amount-confirmed">3천만원</td>
```

---

### ❌ Sorting by Amount

**FORBIDDEN**:
```javascript
// ❌ WRONG: Sorting by amount implies ranking
rows.sort((a, b) => b.amount_numeric - a.amount_numeric);
```

**CORRECT**:
```javascript
// ✅ CORRECT: Sort by coverage_code or name only
rows.sort((a, b) => a.coverage_code.localeCompare(b.coverage_code));
```

---

### ❌ Calculated Fields

**FORBIDDEN**:
```javascript
// ❌ WRONG: Calculations imply comparison
const average = amounts.reduce((sum, amt) => sum + amt.numeric, 0) / amounts.length;
const max = Math.max(...amounts.map(a => a.numeric));
```

**CORRECT**:
```javascript
// ✅ CORRECT: Display only, no calculations
amounts.forEach(amt => {
  display(amt.value_text);  // Show as-is
});
```

---

### ❌ Visual Comparisons

**FORBIDDEN**:
```html
<!-- ❌ WRONG: Bar chart implies ranking -->
<div class="amount-bar" style="width: 80%">3천만원</div>
<div class="amount-bar" style="width: 60%">2천만원</div>
<div class="amount-bar" style="width: 40%">1천만원</div>
```

**CORRECT**:
```html
<!-- ✅ CORRECT: Table layout, no visual comparison -->
<td>3천만원</td>
<td>2천만원</td>
<td>1천만원</td>
```

---

## 🎯 Presentation Checklist

Before deploying UI changes, verify:

- [ ] **Status-based styling only** (not value-based)
- [ ] **Fixed text** for UNCONFIRMED/NOT_AVAILABLE
- [ ] **No color coding** for amount comparison
- [ ] **No sorting** by amount value
- [ ] **No highlighting** of max/min
- [ ] **No calculations** (average, total, etc.)
- [ ] **No charts** comparing amounts
- [ ] **Tooltips** provide context for each status
- [ ] **Screen reader** support for status
- [ ] **No "recommend"** or "best" labels

---

## 📱 Responsive Design

### Desktop

```
┌────────────────┬──────────┬──────────┬──────────┐
│ 담보명          │ 삼성     │ 한화     │ 현대     │
├────────────────┼──────────┼──────────┼──────────┤
│ 암진단비        │ 3천만원  │ 2천만원  │ 3천만원  │
└────────────────┴──────────┴──────────┴──────────┘
```

### Mobile (Stacked)

```
┌────────────────────────────┐
│ 암진단비                   │
├────────────────────────────┤
│ 삼성: 3천만원              │
│ 한화: 2천만원              │
│ 현대: 3천만원              │
└────────────────────────────┘
```

**Rules for mobile**:
- Status classes still apply
- No reordering by amount
- Maintain status tooltips

---

## ♿ Accessibility

### Screen Reader Support

```html
<td class="amount-confirmed">
  <span aria-label="확정된 금액">1천만원</span>
  <span class="sr-only">가입설계서에 명시된 금액입니다</span>
</td>

<td class="amount-unconfirmed">
  <span aria-label="금액 미확인">금액 명시 없음</span>
  <span class="sr-only">문서상 금액이 명시되지 않았습니다</span>
</td>

<td class="amount-not-available">
  <span aria-label="담보 없음">해당 담보 없음</span>
  <span class="sr-only">해당 보험사에 이 담보가 없습니다</span>
</td>
```

### Keyboard Navigation

- Tab through cells normally
- No special focus styling for "best value"
- Tooltips accessible via focus

---

## 🧪 Testing

### Visual Regression Tests

Test each status renders correctly:

```javascript
describe('Amount Presentation', () => {
  it('CONFIRMED shows value_text', () => {
    expect(cell.text()).toBe('1천만원');
    expect(cell).not.toHaveClass('amount-highlight');
  });

  it('UNCONFIRMED shows fixed text', () => {
    expect(cell.text()).toBe('금액 명시 없음');
    expect(cell).toHaveClass('amount-unconfirmed');
  });

  it('NOT_AVAILABLE shows fixed text', () => {
    expect(cell.text()).toBe('해당 담보 없음');
    expect(cell).toHaveClass('amount-not-available');
  });

  it('does not sort by amount value', () => {
    const amounts = table.getColumnValues('amount');
    // Should match original order (coverage_code order)
    expect(amounts).not.toBeSorted();
  });
});
```

---

## 📚 Implementation Examples

### React Component

```tsx
interface AmountCellProps {
  amount: AmountDTO;
}

const AmountCell: React.FC<AmountCellProps> = ({ amount }) => {
  const getDisplayText = () => {
    switch (amount.status) {
      case 'CONFIRMED':
        return amount.value_text || '확인 불가';
      case 'UNCONFIRMED':
        return '금액 명시 없음';
      case 'NOT_AVAILABLE':
        return '해당 담보 없음';
      default:
        return '확인 불가';
    }
  };

  const getClassName = () => `amount-${amount.status.toLowerCase()}`;

  return (
    <td className={getClassName()}>
      <span className="amount-value">{getDisplayText()}</span>
      {amount.evidence && (
        <span className="amount-tooltip" title={amount.evidence.snippet}>
          ⓘ
        </span>
      )}
    </td>
  );
};
```

### Vue Component

```vue
<template>
  <td :class="amountClass">
    <span class="amount-value">{{ displayText }}</span>
    <span v-if="amount.evidence" class="amount-tooltip" :title="amount.evidence.snippet">
      ⓘ
    </span>
  </td>
</template>

<script>
export default {
  props: ['amount'],
  computed: {
    displayText() {
      switch (this.amount.status) {
        case 'CONFIRMED':
          return this.amount.value_text || '확인 불가';
        case 'UNCONFIRMED':
          return '금액 명시 없음';
        case 'NOT_AVAILABLE':
          return '해당 담보 없음';
        default:
          return '확인 불가';
      }
    },
    amountClass() {
      return `amount-${this.amount.status.toLowerCase()}`;
    }
  }
};
</script>
```

---

## 🔒 Presentation Lock

**These rules are LOCKED as of STEP NEXT-11.**

Any UI changes that violate these rules are **rejected**.

**Enforcement**:
- Code review checklist includes presentation rules
- Visual regression tests fail on violations
- Accessibility audits check status semantics

---

## 📞 Support

**Questions**: Refer to `docs/api/AMOUNT_READ_CONTRACT.md` for API contract
**Issues**: Check `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` for lock policy

**Lock Owner**: Pipeline Team + UI Team
**Last Updated**: 2025-12-29 (STEP NEXT-17)

---

## 📝 STEP NEXT-17 Updates (2025-12-29)

### What Changed

**1. Number Format Unification**:
- All CONFIRMED amounts now use comma format: "3,000만원" (NOT "3천만원")
- Provides consistent, professional presentation
- Frontend presentation layer only (NO data changes)

**2. Type C Insurer Distinction**:
- Type C insurers (Hanwha, Hyundai, KB) use "보험가입금액 기준" for UNCONFIRMED
- Type A/B insurers continue to use "금액 명시 없음" for UNCONFIRMED
- Prevents customer misunderstanding about product structure

**3. Common Notes Explanation**:
- Added note explaining Type C structure (shown once per comparison)
- "※ 일부 보험사는 담보별 금액을 별도로 표시하지 않고 상품 공통 '보험가입금액'을 기준으로 보장을 제공합니다."
- Appears in CommonNotesSection when any Type C insurer is present

### Implementation

**Presentation Utilities**: `apps/api/presentation_utils.py`
- `format_amount_for_display()`: Main formatting function
- `get_type_c_explanation_note()`: Returns explanation text
- `should_show_type_c_note()`: Checks if note needed

**Integration Points**:
- Chat handlers use presentation utilities for display
- NO changes to Step7/11/12/13 extraction logic
- NO database schema changes
- NO API contract changes

### Validation

**DoD Checklist**:
- ✅ NO "3천만원" format in UI
- ✅ Type C insurers show "보험가입금액 기준" (NO amounts)
- ✅ Type A/B insurers show unified "3,000만원" format
- ✅ Common note appears once per comparison
- ✅ NO Step7/11/12/13 logic changes
- ✅ pytest passes with no regressions

### References

- Type Map: `config/amount_lineage_type_map.json`
- Guardrails: `docs/guardrails/STEP7_TYPE_AWARE_GUARDRAILS.md`
- Completion Report: `STEP_NEXT_17_COMPLETION.md`
