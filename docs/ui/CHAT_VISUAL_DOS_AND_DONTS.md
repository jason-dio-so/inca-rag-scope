# Chat Visual Dos and Don'ts (Financial/Insurance UX Safety)

**Version**: 1.1.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-16 (Updated: NEXT-17)

---

## 🎯 Purpose

This document defines **visual design constraints** to prevent financial/insurance UX risks.

**Audience**:
- Visual Designers (Figma/Sketch)
- UI/UX Designers
- Frontend Developers (CSS/styling decisions)
- QA Engineers (visual acceptance testing)

**Critical**: Financial/insurance services have **strict UX compliance requirements**. Visual elements that suggest "recommendation", "ranking", or "AI judgment" can create legal/regulatory risks.

---

## 🔒 Core Safety Principles

### P1. Factual Presentation Only
- UI must present data "as-is" (no interpretation layer)
- Visual hierarchy must NOT imply superiority/inferiority
- Status-based styling ONLY (data availability, NOT value judgment)

### P2. No Recommendation Signals
- NO color coding for "better/worse"
- NO icons suggesting "best choice" (⭐, ✓, 👍)
- NO spatial arrangement implying ranking

### P3. No LLM Inference Hints
- NO "AI thinking" animations
- NO anthropomorphic UI (robot avatars, "smart assistant" branding)
- NO dynamic content generation hints

### P4. Deterministic UX
- All UI states must be deterministic (no randomness)
- Animation/transition must be predictable
- User must understand system is rule-based (NOT AI-judging)

---

## 📋 Visual Risk Categories

---

## Category 1: Color Coding (High Risk)

### ❌ DON'T: Use Green/Red for Amount Comparison

**FORBIDDEN**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │ ← Green background (implies "good")
│ 메리츠화재     │ 2천만원      │ ← Yellow (implies "medium")
│ KB손해보험     │ 1천만원      │ ← Red background (implies "bad")
└────────────────┴──────────────┘
```

**Visual Risk**: User perceives green = "better choice" → Recommendation

---

### ✅ DO: Use Status-Based Neutral Colors

**CORRECT**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │ ← Normal text (CONFIRMED)
│ 메리츠화재     │ 금액 명시 없음   │ ← Gray + italic (UNCONFIRMED)
│ KB손해보험     │ 해당 담보 없음   │ ← Strikethrough + gray (NOT_AVAILABLE)
└────────────────┴──────────────────┘
```

**Justification**: Colors reflect DATA STATUS (confirmed vs unconfirmed), NOT value judgment.

**Allowed Palette**:
```css
/* CONFIRMED (default) */
color: #333;  /* Inherit from text */

/* UNCONFIRMED (data incomplete) */
color: #666666;  /* Gray, neutral */
font-style: italic;

/* NOT_AVAILABLE (data absent) */
color: #999999;  /* Light gray, neutral */
text-decoration: line-through;
background: #F5F5F5;
```

**FORBIDDEN Colors**:
```css
/* NEVER use these for amount values */
❌ color: #00C853;  /* Green - implies "good" */
❌ color: #FF0000;  /* Red - implies "bad" */
❌ color: #FFC107;  /* Yellow - implies "warning" */
❌ color: #007BFF;  /* Blue - implies "recommended" */
```

---

### ❌ DON'T: Use Color Gradients for Ranking

**FORBIDDEN**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │ ← background: rgba(0, 200, 83, 0.3)  (dark green)
│ 메리츠화재     │ 2천만원      │ ← background: rgba(0, 200, 83, 0.2)  (medium green)
│ KB손해보험     │ 1천만원      │ ← background: rgba(0, 200, 83, 0.1)  (light green)
└────────────────┴──────────────┘
```

**Visual Risk**: Gradient intensity = value ranking → Recommendation

---

### ✅ DO: Use Uniform Neutral Background

**CORRECT**:
```css
.comparison-table td {
  background: #FFF;  /* Uniform white */
  color: #333;       /* Uniform text color */
}

.comparison-table .label-cell {
  background: #FAFAFA;  /* Slightly different for label column ONLY */
}
```

---

## Category 1B: Type C Insurer Display (High Risk - STEP NEXT-17)

### ❌ DON'T: Show Inferred Amounts for Type C Insurers

**FORBIDDEN**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 한화손해보험   │ 5,000만원        │ ← FORBIDDEN: Inferred from "보험가입금액"
│                │ (보험가입금액)    │
└────────────────┴──────────────────┘
```

**Visual Risk**: User perceives "5,000만원" as confirmed amount → False comparison

---

### ❌ DON'T: Use Ambiguous "보험가입금액" Label

**FORBIDDEN**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원          │
│ 한화손해보험   │ 보험가입금액      │ ← Ambiguous - what does this mean?
└────────────────┴──────────────────┘
```

**Visual Risk**: User does not understand what "보험가입금액" means

---

### ✅ DO: Use Two-Line Structure Display (Type C UNCONFIRMED)

**CORRECT**:
```
┌────────────────┬──────────────────────────┐
│ 보험사         │ 암진단비                  │
├────────────────┼──────────────────────────┤
│ 삼성화재       │ 3천만원                  │
│ 한화손해보험   │ 금액 미기재              │
│                │ (보험가입금액 기준)      │ ← Italic, gray, two-line
└────────────────┴──────────────────────────┘
```

**Justification**:
- "금액 미기재" = states the fact (no amount in proposal)
- "(보험가입금액 기준)" = explains product structure
- NO numbers = NO inference

**CSS Example**:
```css
.amount-unconfirmed-type-c {
  color: #666666;
  font-style: italic;
  font-size: 13px;
  line-height: 1.4;
  display: block;
}

.amount-unconfirmed-type-c::after {
  content: '\A(보험가입금액 기준)';
  white-space: pre;
}
```

---

### ❌ DON'T: Place Number in Parentheses

**FORBIDDEN**:
```
한화손해보험: (5,000만원)
한화손해보험: 금액 미기재 (5,000만원)
```

**Visual Risk**: Parentheses suggest "implied" or "calculated" amount → Inference

---

### ✅ DO: Add Structure Explanation in Common Notes

**CORRECT**:
```markdown
**유의사항**
- 한화손해보험의 경우 '보험가입금액' 구조를 사용합니다.
- 이 경우 담보별 금액이 개별적으로 명시되지 않으며, 가입설계서에는 '보험가입금액 지급' 형태로만 표기됩니다.
- 정확한 보장 금액은 약관 또는 담당자를 통해 확인하시기 바랍니다.
```

**Justification**: Explains WHY amount is not shown (product structure, not data missing)

---

## Category 2: Icons & Badges (High Risk)

### ❌ DON'T: Use Icons for Value Ranking

**FORBIDDEN**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원 ⭐   │ ← Star icon (implies "best")
│ 메리츠화재     │ 2천만원 ✓    │ ← Checkmark (implies "good")
│ KB손해보험     │ 1천만원 ✗    │ ← X mark (implies "bad")
└────────────────┴──────────────┘
```

**Visual Risk**: Icons create ranking hierarchy.

---

### ✅ DO: Use Icons for Status ONLY (Minimal)

**CORRECT**:
```
┌────────────────┬──────────────────┐
│ 보험사         │ 암진단비          │
├────────────────┼──────────────────┤
│ 삼성화재       │ 3천만원 ⓘ        │ ← Info icon (tooltip: "가입설계서 명시")
│ 메리츠화재     │ 금액 명시 없음 ⚠️│ ← Warning icon (tooltip: "문서 확인 필요")
│ KB손해보험     │ 해당 담보 없음 ⊘ │ ← Null icon (tooltip: "담보 없음")
└────────────────┴──────────────────┘
```

**Justification**: Icons indicate DATA STATUS (not value judgment).

**Allowed Icons**:
- ⓘ (info) - For CONFIRMED with tooltip
- ⚠️ (warning) - For UNCONFIRMED (neutral warning, not error)
- ⊘ (null) - For NOT_AVAILABLE
- ▼/▶ (expand/collapse) - For accordion

**FORBIDDEN Icons**:
- ❌ ⭐ (star) - Implies "recommended"
- ❌ ✓ (checkmark) - Implies "approved"
- ❌ ✗ (x-mark) - Implies "rejected"
- ❌ 👍/👎 (thumbs) - Implies judgment
- ❌ 🏆 (trophy) - Implies "winner"

---

### ❌ DON'T: Use Badges for "Best Value"

**FORBIDDEN**:
```
┌─────────────────────────────┐
│ 삼성화재                    │
│ 3천만원  [BEST VALUE]       │ ← Badge implies recommendation
└─────────────────────────────┘
```

**Visual Risk**: Badge = system endorsement.

---

### ✅ DO: Use Badges for Status ONLY

**CORRECT**:
```
┌─────────────────────────────┐
│ 삼성화재                    │
│ 3천만원  [CONFIRMED]        │ ← Status badge (factual)
└─────────────────────────────┘

┌─────────────────────────────┐
│ 메리츠화재                  │
│ 금액 명시 없음  [UNCONFIRMED]│ ← Status badge
└─────────────────────────────┘
```

**Badge Styling** (Minimal):
```css
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-badge.confirmed {
  background: #E8F5E9;  /* Light green (not bright) */
  color: #2E7D32;       /* Dark green text */
}

.status-badge.unconfirmed {
  background: #FFF9E6;  /* Light yellow */
  color: #F57C00;       /* Orange text */
}

.status-badge.not-available {
  background: #F5F5F5;  /* Gray */
  color: #999;
}
```

**Important**: These colors are ONLY for status badges (not for amount cells).

---

## Category 3: Typography (Medium Risk)

### ❌ DON'T: Use Bold for "Best" Values

**FORBIDDEN**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ **3천만원**  │ ← Bold (implies "best")
│ 메리츠화재     │ 2천만원      │ ← Normal
│ KB손해보험     │ 1천만원      │ ← Normal
└────────────────┴──────────────┘
```

**Visual Risk**: Bold = emphasis = "this is better".

---

### ✅ DO: Use Uniform Font Weight

**CORRECT**:
```css
.comparison-table td {
  font-weight: 400;  /* Normal weight for all values */
  font-size: 15px;
}

.comparison-table .label-cell {
  font-weight: 500;  /* Slightly bolder for label ONLY */
}
```

**Exception**: Section titles can be bold (H4/H5), but NOT data values.

---

### ❌ DON'T: Use Font Size for Ranking

**FORBIDDEN**:
```
삼성화재: 3천만원  ← 24px (largest)
메리츠화재: 2천만원  ← 18px (medium)
KB손해보험: 1천만원  ← 14px (smallest)
```

**Visual Risk**: Larger font = more important.

---

### ✅ DO: Use Uniform Font Size

**CORRECT**:
```css
.explanation-block .value-text {
  font-size: 18px;  /* Same for all insurers */
  font-weight: 600;
}
```

---

## Category 4: Layout & Spacing (Medium Risk)

### ❌ DON'T: Use Spatial Hierarchy for Ranking

**FORBIDDEN**:
```
┌─────────────────────────────────┐
│ ┌───────────────────────────┐   │  ← Larger card
│ │ 삼성화재 (3천만원) ⭐     │   │
│ │ ...                       │   │
│ └───────────────────────────┘   │
│                                 │
│ ┌─────────────────┐             │  ← Smaller card (implies "worse")
│ │ 메리츠화재       │             │
│ │ (2천만원)        │             │
│ └─────────────────┘             │
└─────────────────────────────────┘
```

**Visual Risk**: Size difference = value hierarchy.

---

### ✅ DO: Use Equal Card Sizes

**CORRECT**:
```css
.explanation-block {
  width: 100%;  /* Equal width */
  padding: 12px;  /* Equal padding */
  margin-bottom: 16px;  /* Equal spacing */
}
```

---

### ❌ DON'T: Use Side-by-Side for Comparison

**FORBIDDEN**:
```
┌───────────────────────────────────────┐
│ ┌─────────────┐   ┌─────────────┐    │
│ │ 삼성화재    │   │ 메리츠화재  │    │  ← Side-by-side
│ │ 3천만원     │   │ 2천만원     │    │    invites comparison
│ └─────────────┘   └─────────────┘    │
└───────────────────────────────────────┘
```

**Visual Risk**: Side-by-side layout = "compare these two".

---

### ✅ DO: Use Vertical Stack

**CORRECT**:
```
┌───────────────────────────────────────┐
│ ┌─────────────────────────────────┐   │
│ │ 삼성화재: 3천만원               │   │
│ └─────────────────────────────────┘   │
│                                       │
│ ┌─────────────────────────────────┐   │  ← Vertical stack
│ │ 메리츠화재: 2천만원             │   │    (neutral)
│ └─────────────────────────────────┘   │
└───────────────────────────────────────┘
```

**Exception**: ComparisonTableSection can use table layout (columns), but NO visual emphasis on specific cells.

---

## Category 5: Charts & Visualizations (High Risk)

### ❌ DON'T: Use Bar Charts for Amount Comparison

**FORBIDDEN**:
```
삼성화재   ████████████ 3천만원
메리츠화재 ████████ 2천만원
KB손해보험 ████ 1천만원
```

**Visual Risk**: Bar length = visual ranking.

---

### ❌ DON'T: Use Pie Charts for Market Share

**FORBIDDEN**:
```
[Pie chart showing % breakdown of amounts by insurer]
```

**Visual Risk**: Pie chart implies "share" or "proportion" → value judgment.

---

### ✅ DO: Use Table Layout ONLY

**CORRECT**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비      │
├────────────────┼──────────────┤
│ 삼성화재       │ 3천만원      │
│ 메리츠화재     │ 2천만원      │
│ KB손해보험     │ 1천만원      │
└────────────────┴──────────────┘
```

**Justification**: Table presents facts without visual interpretation.

---

## Category 6: Sorting & Filtering (High Risk)

### ❌ DON'T: Add Sort Controls by Amount

**FORBIDDEN**:
```
┌────────────────┬──────────────┐
│ 보험사         │ 암진단비 ▼▲ │ ← Sort arrows
├────────────────┼──────────────┤
│ ...            │ ...          │
└────────────────┴──────────────┘
```

**Visual Risk**: Sortable column = "you can rank these".

---

### ✅ DO: Preserve ViewModel Order (No Sorting)

**CORRECT**:
```css
/* NO sort event handlers */
.comparison-table th {
  cursor: default;  /* NOT pointer */
}

/* NO sort icons */
.comparison-table th::after {
  content: "";  /* No ▼▲ */
}
```

**Exception**: Sorting by coverage_code or insurer name (alphabetical) is ALLOWED, but NOT by amount value.

---

## Category 7: Animation & Interaction (Medium Risk)

### ❌ DON'T: Use "AI Thinking" Animations

**FORBIDDEN**:
```
[🤖 Analyzing your options...]  ← Robot icon + "analyzing"
[💭 Thinking...]                ← Thought bubble
[⚡ Processing with AI...]       ← "AI" branding
```

**Visual Risk**: User perceives "AI is making a judgment for me".

---

### ✅ DO: Use Neutral Loading States

**CORRECT**:
```
[⏳ 확인 중입니다...]  ← Hourglass + factual text
[Loading...]         ← Generic spinner
```

**Spinner Styling**:
```css
.spinner {
  border: 3px solid #F3F3F3;
  border-top: 3px solid #666;  /* Neutral gray */
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}
```

**FORBIDDEN Spinner Colors**:
- ❌ Blue (#007BFF) - Implies "smart"
- ❌ Rainbow gradient - Implies "creative AI"

---

### ❌ DON'T: Use Highlighting on Hover for "Best Value"

**FORBIDDEN**:
```css
.comparison-table tr:hover td:nth-child(2) {
  background: #00C853;  /* Green highlight on hover */
  color: #FFF;
}
```

**Visual Risk**: Hover state = "this is special".

---

### ✅ DO: Use Subtle Uniform Hover

**CORRECT**:
```css
.comparison-table tr:hover {
  background: #F9F9F9;  /* Light gray, uniform across row */
}
```

---

## Category 8: Messaging & Copy (High Risk)

### ❌ DON'T: Use Recommendation Language

**FORBIDDEN**:
```
"Based on your profile, we recommend 삼성화재"
"삼성화재 is the best choice for you"
"You should choose 메리츠화재"
```

**Enforcement**: `forbidden_language.py` blocks these at runtime.

---

### ✅ DO: Use Factual Statements

**CORRECT**:
```
"2개 보험사의 암진단비를 비교합니다"
"삼성화재의 암진단비는 가입설계서에 3천만원으로 명시되어 있습니다"
```

**Reference**: `COMPARISON_EXPLANATION_RULES.md`

---

### ❌ DON'T: Use Apologetic Tone

**FORBIDDEN**:
```
"죄송하지만 추천 기능은 제공하지 않습니다"
"아직 지원하지 않는 기능입니다"
```

**Visual Risk**: Apologetic tone = defensive = "we're limited".

---

### ✅ DO: Use Neutral Constraint Explanation

**CORRECT**:
```
"보험 상품의 추천 및 우열 비교는 제공하지 않습니다"

대신 다음 정보를 확인하실 수 있습니다:
- 보험사별 보장금액 비교
- 담보별 가입설계서 명시 내용
```

**Reference**: `CHAT_UX_SCENARIOS.md` (S4)

---

## Category 9: Branding & Persona (Medium Risk)

### ❌ DON'T: Use "AI Assistant" Persona

**FORBIDDEN**:
```
[Avatar: 🤖 Smart Insurance AI]
"Hi! I'm your AI insurance advisor..."
```

**Visual Risk**: AI branding = user expects "smart recommendations".

---

### ✅ DO: Use Neutral Service Branding

**CORRECT**:
```
[Service Name: 보험 비교 정보]
[Tagline: 가입설계서 기준 사실 비교]
```

**NO Avatar**: If avatar is required, use abstract icon (NOT robot/person).

---

### ❌ DON'T: Use Conversational Tone Suggesting Intelligence

**FORBIDDEN**:
```
"I've analyzed 10 policies and found that..."
"In my opinion, 삼성화재 offers better coverage..."
```

**Visual Risk**: "I" = persona = judgment.

---

### ✅ DO: Use System Tone (No Persona)

**CORRECT**:
```
"가입설계서 기준으로 2개 보험사를 비교합니다"
"삼성화재의 암진단비는 3천만원으로 명시되어 있습니다"
```

**Voice**: Third-person factual (NOT first-person "I").

---

## Category 10: Accessibility (Low Risk, Best Practice)

### ❌ DON'T: Rely on Color Alone for Status

**FORBIDDEN**:
```css
.amount-confirmed { color: green; }  ← Color ONLY
.amount-unconfirmed { color: red; }
```

**Accessibility Risk**: Color-blind users cannot distinguish.

---

### ✅ DO: Combine Color + Icon + Text

**CORRECT**:
```html
<td class="amount-unconfirmed">
  <span aria-label="금액 미확인">⚠️</span>
  <span>금액 명시 없음</span>
</td>
```

**CSS**:
```css
.amount-unconfirmed {
  color: #666;  /* Color */
  font-style: italic;  /* Style */
}
```

**ARIA Labels**:
```html
<td aria-label="Confirmed: 3천만원">3천만원</td>
<td aria-label="Unconfirmed: 금액 명시 없음">금액 명시 없음</td>
```

---

## 🧪 Visual QA Checklist

Use this checklist during design review:

### Color
- [ ] No green/red for amount values
- [ ] No color gradients for ranking
- [ ] Status-based colors only (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)
- [ ] Neutral palette (#333, #666, #999)

### Icons & Badges
- [ ] No ⭐, ✓, ✗ for value judgment
- [ ] Status icons only (ⓘ, ⚠️, ⊘)
- [ ] Badge text is factual ("CONFIRMED", NOT "BEST")

### Typography
- [ ] Uniform font weight (no bold for "best" values)
- [ ] Uniform font size (no larger text for "best" values)
- [ ] Headings (H4/H5) can be bold, but NOT data values

### Layout
- [ ] Equal card sizes (no spatial hierarchy)
- [ ] Vertical stacking (NO side-by-side comparison)
- [ ] Section order preserved from ViewModel

### Charts & Visualizations
- [ ] No bar charts, pie charts, or graphs
- [ ] Table layout ONLY

### Sorting & Filtering
- [ ] No sort controls by amount value
- [ ] Alphabetical sort (coverage_code/insurer name) ONLY

### Animation & Interaction
- [ ] No "AI thinking" animations
- [ ] Neutral loading spinner (gray, not blue/rainbow)
- [ ] Subtle hover states (uniform across row)

### Messaging & Copy
- [ ] All text passes `forbidden_language.py`
- [ ] No recommendation language
- [ ] No apologetic tone

### Branding & Persona
- [ ] No "AI Assistant" persona
- [ ] Neutral service branding
- [ ] Third-person factual voice (NOT "I")

### Accessibility
- [ ] Color + icon + text (NOT color alone)
- [ ] ARIA labels for screen readers
- [ ] Keyboard navigation support

---

## 📚 Related Documents

| Document | Purpose | Reference |
|----------|---------|-----------|
| `CHAT_COMPONENT_CONTRACT.md` | Component specifications | STEP NEXT-16 |
| `CHAT_LAYOUT_SPEC.md` | Layout structure | STEP NEXT-16 |
| `COMPARISON_EXPLANATION_RULES.md` | Explanation templates | STEP NEXT-12 |
| `AMOUNT_PRESENTATION_RULES.md` | Status-based styling | STEP NEXT-11 |
| `FORBIDDEN_LANGUAGE_POLICY_SCOPE.md` | Language validation | STEP NEXT-14-β |
| `CHAT_UX_SCENARIOS.md` | UX scenarios | STEP NEXT-15 |

---

## 🔐 Visual Safety Lock

**This visual constraint spec is LOCKED as of STEP NEXT-16.**

Any violations of these patterns in production design are **rejected** via:
- Design review (manual inspection)
- Visual regression tests (automated screenshots)
- QA checklist (acceptance testing)

**Enforcement Owner**: Product Team + Design Team + QA Team

---

**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
