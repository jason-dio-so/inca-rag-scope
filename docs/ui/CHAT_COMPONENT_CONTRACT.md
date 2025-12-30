# Chat Component Contract (Design & Implementation Specification)

**Version**: 1.1.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-16 (Updated: NEXT-17)

---

## 🎯 Purpose

This document defines the **design contract** for all Chat UI components.

**Audience**:
- Figma Designers (component structure + variants)
- Frontend Developers (React/Vue/HTML implementation)
- QA Engineers (acceptance testing)

**Contract Principle**: This is NOT a visual design guide. This is a **behavioral specification** that defines:
- What each component DOES
- What data it receives
- What states it can be in
- What is FORBIDDEN

---

## 🔒 Absolute Constraints (All Components)

| Constraint | Enforcement | Reference |
|------------|-------------|-----------|
| ❌ NO recommendation UI | Visual design must NOT imply superiority | `CHAT_UX_SCENARIOS.md` |
| ❌ NO amount-based ranking | Color/sorting must NOT rank by value | `AMOUNT_PRESENTATION_RULES.md` |
| ❌ NO comparative emphasis | Cross-component visual links FORBIDDEN | `COMPARISON_EXPLANATION_RULES.md` |
| ❌ NO LLM inference hints | UI must NOT suggest "AI judgment" | `FORBIDDEN_LANGUAGE_POLICY_SCOPE.md` |
| ✅ Status-based styling ONLY | CONFIRMED/UNCONFIRMED/NOT_AVAILABLE | `AMOUNT_PRESENTATION_RULES.md` |
| ✅ ViewModel as-is rendering | NO parsing, NO transformation | `CUSTOMER_EXAMPLE_SCREEN_MAPPING.md` |

---

## 📋 Component Hierarchy

```
ChatScreen
├── Header (service branding, static)
├── MessageScrollArea
│   ├── UserMessageBubble (C1)
│   ├── SystemMessageBubble (C2)
│   └── AssistantMessageCard (C3)
│       ├── SummaryBulletBlock (C4)
│       ├── ComparisonTableSection (C5)
│       ├── InsurerExplanationSection (C6)
│       ├── CommonNotesSection (C7)
│       └── EvidenceAccordionSection (C8)
└── InputArea (user text input, static)
```

---

## Component Specifications

---

## C1: UserMessageBubble

### Role
Displays user's text input in chat format (ChatGPT-style appearance).

### ViewModel Source
```typescript
interface UserMessageVM {
  role: "user";
  content: string;  // Plain text only
}
```

### Visual Rules

**ALLOWED**:
- Single background color (neutral, e.g., #F0F0F0)
- Plain text rendering
- Standard font (inherit from design system)
- Right-aligned bubble (user side)

**FORBIDDEN**:
- ❌ Parsing content (e.g., detecting insurer names)
- ❌ Highlighting keywords
- ❌ Icons or badges
- ❌ Multi-line splitting logic (just wrap text)

### States / Variants
- **Default**: Normal text display

### Figma Component Structure
```
Component: UserMessageBubble
├── Frame (auto-layout, right-aligned)
│   └── Text (content)
```

### Implementation Notes
```tsx
// React example
const UserMessageBubble: React.FC<{ content: string }> = ({ content }) => (
  <div className="user-message-bubble">
    {content}
  </div>
);
```

**CSS Rules**:
```css
.user-message-bubble {
  background: #F0F0F0;
  border-radius: 12px;
  padding: 12px 16px;
  margin-left: auto;  /* Right-align */
  max-width: 70%;
  text-align: left;
  word-wrap: break-word;
}
```

### QA Validation
- [ ] Text wraps correctly
- [ ] No keyword highlighting
- [ ] Right-aligned on all screen sizes

---

## C2: SystemMessageBubble

### Role
Displays system messages (e.g., loading, constraint explanations).

### ViewModel Source
```typescript
interface SystemMessageVM {
  role: "system";
  content: string;  // Factual statement only
  message_type?: "loading" | "constraint" | "clarification";
}
```

### Visual Rules

**ALLOWED**:
- Centered or left-aligned
- Neutral background color (e.g., #FFF9E6 for warnings, #F5F5F5 for info)
- Icon ONLY for message_type (e.g., ⏳ for loading, ⚠️ for constraint)

**FORBIDDEN**:
- ❌ Apologetic tone (enforced by `forbidden_language.py`)
- ❌ "AI is thinking" animations (no LLM inference hints)
- ❌ Color coding for "error" vs "success" (use neutral tones)

### States / Variants
- **Loading**: "확인 중입니다..." (with spinner/icon)
- **Constraint**: "해당 요청은 제공 범위를 벗어납니다" (neutral tone)
- **Clarification**: "보험사 정보가 필요합니다" (request for input)

### Figma Component Structure
```
Component: SystemMessageBubble
├── Variant: message_type (loading | constraint | clarification)
│   ├── Icon (conditional)
│   └── Text (content)
```

### Implementation Notes
```tsx
const SystemMessageBubble: React.FC<{
  content: string;
  message_type?: "loading" | "constraint" | "clarification";
}> = ({ content, message_type }) => (
  <div className={`system-message ${message_type || "info"}`}>
    {message_type === "loading" && <Spinner />}
    {message_type === "constraint" && <Icon>⚠️</Icon>}
    <span>{content}</span>
  </div>
);
```

**CSS Rules**:
```css
.system-message {
  background: #F5F5F5;
  border-radius: 8px;
  padding: 10px 14px;
  margin: 0 auto;
  max-width: 80%;
  text-align: center;
  color: #666;
}

.system-message.constraint {
  background: #FFF9E6;
  border-left: 3px solid #FFA500;
}
```

### QA Validation
- [ ] No apologetic language ("죄송합니다")
- [ ] No "AI thinking" animations
- [ ] Neutral color scheme

---

## C3: AssistantMessageCard

### Role
Container for all assistant response sections (S1 Happy Path response).

### ViewModel Source
```typescript
interface AssistantMessageVM {
  role: "assistant";
  title?: string;
  summary_bullets?: string[];
  sections: Section[];  // Ordered array
}
```

### Visual Rules

**ALLOWED**:
- White background card
- Vertical section stacking (top → bottom order preserved)
- Consistent spacing between sections

**FORBIDDEN**:
- ❌ Re-ordering sections (must follow ViewModel order)
- ❌ Hiding sections based on content (render all sections)
- ❌ Collapsing sections by default (except Evidence)

### States / Variants
- **Default**: Full response with all sections
- **Partial**: Some sections may be empty (render placeholder or skip)

### Figma Component Structure
```
Component: AssistantMessageCard
├── Frame (auto-layout, vertical, left-aligned)
│   ├── Title (optional, H3)
│   ├── SummaryBulletBlock (C4)
│   ├── Section[] (C5-C8, rendered in order)
```

### Implementation Notes
```tsx
const AssistantMessageCard: React.FC<{ message: AssistantMessageVM }> = ({ message }) => (
  <div className="assistant-message-card">
    {message.title && <h3>{message.title}</h3>}
    {message.summary_bullets && <SummaryBulletBlock bullets={message.summary_bullets} />}
    {message.sections.map((section, idx) => (
      <SectionRenderer key={idx} section={section} />
    ))}
  </div>
);
```

**Section Routing** (deterministic):
```tsx
const SectionRenderer: React.FC<{ section: Section }> = ({ section }) => {
  switch (section.kind) {
    case "comparison_table":
      return <ComparisonTableSection {...section} />;
    case "insurer_explanations":
      return <InsurerExplanationSection {...section} />;
    case "common_notes":
      return <CommonNotesSection {...section} />;
    case "evidence_accordion":
      return <EvidenceAccordionSection {...section} />;
    default:
      return null;
  }
};
```

### QA Validation
- [ ] Sections render in ViewModel order
- [ ] No sections hidden
- [ ] All section types handled

---

## C4: SummaryBulletBlock

### Role
Displays 3-5 factual summary bullets (top of assistant response).

### ViewModel Source
```typescript
interface SummaryBulletBlock {
  bullets: string[];  // 3-5 items, validated by forbidden_language.py
}
```

### Visual Rules

**ALLOWED**:
- Bullet list (• or numbered)
- Normal text weight
- Neutral color (#333)

**FORBIDDEN**:
- ❌ Bold for "important" bullets (all equal weight)
- ❌ Color coding (green for "good", red for "bad")
- ❌ Icons or badges

### States / Variants
- **Default**: Bullet list rendering

### Figma Component Structure
```
Component: SummaryBulletBlock
├── Frame (auto-layout, vertical)
│   └── BulletItem[] (repeated)
│       ├── Bullet (•)
│       └── Text
```

### Implementation Notes
```tsx
const SummaryBulletBlock: React.FC<{ bullets: string[] }> = ({ bullets }) => (
  <ul className="summary-bullets">
    {bullets.map((text, idx) => (
      <li key={idx}>{text}</li>
    ))}
  </ul>
);
```

**CSS Rules**:
```css
.summary-bullets {
  list-style: disc;
  padding-left: 20px;
  margin: 12px 0;
  color: #333;
}

.summary-bullets li {
  margin-bottom: 6px;
  line-height: 1.5;
}
```

### QA Validation
- [ ] All bullets rendered
- [ ] No bold/color emphasis
- [ ] Text passes `forbidden_language.py`

---

## C5: ComparisonTableSection

### Role
Displays comparison table (insurers × coverages or other matrices).

### ViewModel Source
```typescript
interface ComparisonTableSection {
  kind: "comparison_table";
  table_kind: "COVERAGE_DETAIL" | "INTEGRATED_COMPARE" | "ELIGIBILITY_MATRIX";
  title?: string;
  columns: string[];  // Header row
  rows: ComparisonRow[];
}

interface ComparisonRow {
  label: string;  // First column (e.g., coverage name, condition)
  values: string[];  // Subsequent columns (e.g., insurer amounts, statuses)
}
```

### Visual Rules

**ALLOWED**:
- Table layout (HTML `<table>` or CSS Grid)
- Header row styling (e.g., background #F5F5F5)
- Status-based cell styling (CONFIRMED/UNCONFIRMED/NOT_AVAILABLE)

**FORBIDDEN**:
- ❌ Sorting by amount value (preserve ViewModel order)
- ❌ Color coding for "best value" (green) or "worst value" (red)
- ❌ Bold for max/min values
- ❌ Icons for ranking (⭐, ✓, ✗)
- ❌ Charts or bar graphs

### Status-Based Cell Styling (LOCKED)

From `AMOUNT_PRESENTATION_RULES.md` (Updated: STEP NEXT-17):

| Status | Text | Style |
|--------|------|-------|
| **CONFIRMED** | `value_text` (e.g., "3천만원") | Normal text, inherit color |
| **UNCONFIRMED (Type A/B)** | "금액 명시 없음" | Italic, gray (#666666) |
| **UNCONFIRMED (Type C)** | "금액 미기재<br>(보험가입금액 기준)" | Italic, gray (#666666), two-line display |
| **NOT_AVAILABLE** | "해당 담보 없음" | Strikethrough, light gray (#999999), background #F5F5F5 |

**CRITICAL (Type C insurers)**:
- Type C insurers (Hanwha, Hyundai, KB) use "보험가입금액" structure
- UNCONFIRMED status is NORMAL for Type C (70-90% expected)
- Display "금액 미기재 (보험가입금액 기준)" to explain product structure
- ❌ NEVER show inferred amounts (e.g., "5,000만원")

### States / Variants
- **COVERAGE_DETAIL**: Single coverage, multiple insurers
- **INTEGRATED_COMPARE**: Multiple coverages, multiple insurers
- **ELIGIBILITY_MATRIX**: Conditions × insurers (O/X/△)

### Figma Component Structure
```
Component: ComparisonTableSection
├── Variant: table_kind
│   ├── Title (optional)
│   ├── Table
│   │   ├── HeaderRow (columns[])
│   │   └── DataRow[] (rows[])
│   │       ├── LabelCell (row.label)
│   │       └── ValueCell[] (row.values[], status-based styling)
```

### Implementation Notes
```tsx
const ComparisonTableSection: React.FC<ComparisonTableSection> = ({
  title,
  columns,
  rows
}) => (
  <div className="comparison-table-section">
    {title && <h4>{title}</h4>}
    <table className="comparison-table">
      <thead>
        <tr>
          {columns.map((col, idx) => (
            <th key={idx}>{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIdx) => (
          <tr key={rowIdx}>
            <td className="label-cell">{row.label}</td>
            {row.values.map((value, valIdx) => (
              <td key={valIdx} className={getCellClassName(value)}>
                {value}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// Status detection (based on fixed text)
const getCellClassName = (value: string): string => {
  // Type C insurer pattern (STEP NEXT-17)
  if (value.includes("금액 미기재") || value.includes("보험가입금액 기준")) {
    return "amount-unconfirmed-type-c";
  }
  // Type A/B insurer pattern
  if (value === "금액 명시 없음") return "amount-unconfirmed";
  if (value === "해당 담보 없음") return "amount-not-available";
  return "amount-confirmed";
};
```

**CSS Rules**:
```css
.comparison-table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.comparison-table th {
  background: #F5F5F5;
  padding: 10px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #DDD;
}

.comparison-table td {
  padding: 10px;
  border-bottom: 1px solid #EEE;
}

.comparison-table .label-cell {
  font-weight: 500;
  background: #FAFAFA;
}

/* Status-based styling (LOCKED) */
.amount-confirmed {
  color: inherit;
  font-weight: normal;
}

.amount-unconfirmed {
  color: #666666;
  font-style: italic;
}

/* Type C insurer - two-line display (STEP NEXT-17) */
.amount-unconfirmed-type-c {
  color: #666666;
  font-style: italic;
  font-size: 13px;
  line-height: 1.4;
}

.amount-not-available {
  color: #999999;
  text-decoration: line-through;
  background: #F5F5F5;
}
```

### QA Validation
- [ ] Table order matches ViewModel (NO sorting)
- [ ] Status-based styling applied correctly
- [ ] No color coding for "best value"
- [ ] No sorting UI controls

---

## C6: InsurerExplanationSection

### Role
Displays parallel (independent) explanation blocks for each insurer.

### ViewModel Source
```typescript
interface InsurerExplanationSection {
  kind: "insurer_explanations";
  title?: string;
  explanations: InsurerExplanation[];
}

interface InsurerExplanation {
  insurer: string;
  status: "CONFIRMED" | "UNCONFIRMED" | "NOT_AVAILABLE";
  explanation: string;  // Template-based, validated
  value_text?: string;  // For CONFIRMED only
}
```

### Visual Rules

**ALLOWED**:
- Section title: "보험사별 설명"
- Each insurer as independent block
- Status badge (optional, minimal)

**FORBIDDEN**:
- ❌ Visual connectors between insurers (no arrows, lines)
- ❌ Highlighting "best" insurer
- ❌ Comparative layout (e.g., side-by-side with emphasis)
- ❌ Bold for "important" insurer

### Template-Based Explanations (LOCKED)

From `COMPARISON_EXPLANATION_RULES.md`:

```
CONFIRMED: "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."
UNCONFIRMED: "{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."
NOT_AVAILABLE: "{insurer}에는 해당 담보가 존재하지 않습니다."
```

### States / Variants
- **Default**: All insurers rendered as parallel blocks

### Figma Component Structure
```
Component: InsurerExplanationSection
├── Title ("보험사별 설명")
├── ExplanationBlock[] (repeated per insurer)
│   ├── InsurerName (H5, e.g., "삼성화재")
│   ├── StatusBadge (optional, minimal)
│   └── ExplanationText (1-3 lines)
```

### Implementation Notes
```tsx
const InsurerExplanationSection: React.FC<InsurerExplanationSection> = ({
  title,
  explanations
}) => (
  <div className="insurer-explanation-section">
    {title && <h4>{title}</h4>}
    {explanations.map((exp, idx) => (
      <div key={idx} className="explanation-block">
        <h5>{exp.insurer}</h5>
        {exp.value_text && <span className="value-text">{exp.value_text}</span>}
        <p className={`explanation ${exp.status.toLowerCase()}`}>
          {exp.explanation}
        </p>
      </div>
    ))}
  </div>
);
```

**CSS Rules**:
```css
.insurer-explanation-section {
  margin: 20px 0;
}

.explanation-block {
  margin-bottom: 16px;
  padding: 12px;
  background: #FAFAFA;
  border-radius: 8px;
}

.explanation-block h5 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.explanation-block .value-text {
  display: block;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #000;
}

.explanation-block p {
  margin: 0;
  line-height: 1.5;
  color: #555;
}

/* Status-based text styling */
.explanation.unconfirmed {
  color: #666;
  font-style: italic;
}

.explanation.not_available {
  color: #999;
}
```

### QA Validation
- [ ] Each insurer is independent block (no visual links)
- [ ] Explanations pass `forbidden_language.py`
- [ ] No comparative language ("더", "보다")
- [ ] Order preserved from ViewModel

---

## C7: CommonNotesSection

### Role
Displays common notes / disclaimers (flat bullets OR grouped).

### ViewModel Source
```typescript
interface CommonNotesSection {
  kind: "common_notes";
  title: string;  // e.g., "유의사항" or "공통사항 및 유의사항"

  // Option 1: Flat bullets (예시2, 예시4)
  bullets?: string[];

  // Option 2: Grouped bullets (예시3)
  groups?: CommonNoteGroup[];
}

interface CommonNoteGroup {
  title: string;  // e.g., "공통사항" or "유의사항"
  bullets: string[];
}
```

### Visual Rules

**ALLOWED**:
- Bullet list rendering
- Grouped sections (when `groups` exists)
- Neutral background (#F9F9F9)

**FORBIDDEN**:
- ❌ Hiding groups (render all)
- ❌ Collapsing by default
- ❌ Color coding for "warning" vs "info"

### States / Variants
- **Flat**: Single bullet list (`bullets` array)
- **Grouped**: Multiple subsections (`groups` array)

### Figma Component Structure
```
Component: CommonNotesSection
├── Variant: layout (flat | grouped)
│   ├── Title
│   ├── [If flat] BulletList (bullets[])
│   ├── [If grouped] GroupBlock[]
│   │   ├── GroupTitle
│   │   └── BulletList (group.bullets[])
```

### Implementation Notes
```tsx
const CommonNotesSection: React.FC<CommonNotesSection> = ({
  title,
  bullets,
  groups
}) => (
  <div className="common-notes-section">
    <h4>{title}</h4>
    {bullets && (
      <ul className="notes-list">
        {bullets.map((text, idx) => (
          <li key={idx}>{text}</li>
        ))}
      </ul>
    )}
    {groups && groups.map((group, gIdx) => (
      <div key={gIdx} className="note-group">
        <h5>{group.title}</h5>
        <ul className="notes-list">
          {group.bullets.map((text, bIdx) => (
            <li key={bIdx}>{text}</li>
          ))}
        </ul>
      </div>
    ))}
  </div>
);
```

**CSS Rules**:
```css
.common-notes-section {
  margin: 20px 0;
  padding: 16px;
  background: #F9F9F9;
  border-radius: 8px;
}

.common-notes-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.note-group {
  margin-bottom: 16px;
}

.note-group h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.notes-list {
  list-style: disc;
  padding-left: 20px;
  margin: 0;
}

.notes-list li {
  margin-bottom: 6px;
  line-height: 1.5;
  color: #666;
}
```

### QA Validation
- [ ] Flat layout works (bullets[])
- [ ] Grouped layout works (groups[])
- [ ] All groups rendered
- [ ] Text passes `forbidden_language.py`

---

## C8: EvidenceAccordionSection

### Role
Displays evidence snippets (collapsed by default, user can expand).

### ViewModel Source
```typescript
interface EvidenceAccordionSection {
  kind: "evidence_accordion";
  title: string;  // e.g., "근거 자료"
  items: EvidenceItem[];
}

interface EvidenceItem {
  insurer: string;
  doc_type: string;  // e.g., "가입설계서", "약관"
  page_number?: number;
  snippet: string;  // Verbatim excerpt (NO summarization)
}
```

### Visual Rules

**ALLOWED**:
- Accordion component (collapsed by default)
- Expand/collapse icon (▼/▶)
- Verbatim snippet rendering
- Source metadata (doc_type, page_number)

**FORBIDDEN**:
- ❌ Summarizing snippet
- ❌ Highlighting keywords in snippet
- ❌ Parsing snippet for "important" phrases
- ❌ Re-ordering items by "relevance"

### States / Variants
- **Collapsed** (default): Title + expand icon visible
- **Expanded**: All evidence items visible

### Figma Component Structure
```
Component: EvidenceAccordionSection
├── AccordionHeader (clickable)
│   ├── Title ("근거 자료")
│   └── Icon (▼ collapsed, ▶ expanded)
├── AccordionBody (conditional)
│   └── EvidenceItem[] (repeated)
│       ├── InsurerName
│       ├── SourceMetadata (doc_type, page_number)
│       └── Snippet (verbatim, monospace optional)
```

### Implementation Notes
```tsx
const EvidenceAccordionSection: React.FC<EvidenceAccordionSection> = ({
  title,
  items
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="evidence-accordion-section">
      <div
        className="accordion-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h4>{title}</h4>
        <span className="icon">{isExpanded ? "▼" : "▶"}</span>
      </div>
      {isExpanded && (
        <div className="accordion-body">
          {items.map((item, idx) => (
            <div key={idx} className="evidence-item">
              <strong>{item.insurer}</strong>
              <div className="metadata">
                출처: {item.doc_type}
                {item.page_number && ` ${item.page_number}페이지`}
              </div>
              <pre className="snippet">{item.snippet}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

**CSS Rules**:
```css
.evidence-accordion-section {
  margin: 20px 0;
  border: 1px solid #DDD;
  border-radius: 8px;
}

.accordion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background: #F5F5F5;
  border-radius: 8px 8px 0 0;
}

.accordion-header:hover {
  background: #EBEBEB;
}

.accordion-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.accordion-body {
  padding: 16px;
  background: #FAFAFA;
}

.evidence-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #EEE;
}

.evidence-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.evidence-item strong {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  color: #333;
}

.evidence-item .metadata {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.evidence-item .snippet {
  background: #FFF;
  border: 1px solid #DDD;
  border-radius: 4px;
  padding: 10px;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
  color: #555;
}
```

### QA Validation
- [ ] Default state: Collapsed
- [ ] Expand/collapse works
- [ ] Snippet is verbatim (NO summarization)
- [ ] Order preserved from ViewModel

---

## 🧪 Component Testing Matrix

| Component | Input Validation | State Handling | Forbidden Pattern Check |
|-----------|------------------|----------------|-------------------------|
| C1: UserMessageBubble | Plain text only | Default only | No keyword highlighting |
| C2: SystemMessageBubble | No apology tone | Loading/Constraint/Clarification | No "AI thinking" |
| C3: AssistantMessageCard | Section order preserved | Default/Partial | No section re-ordering |
| C4: SummaryBulletBlock | `forbidden_language.py` | Default only | No bold/color emphasis |
| C5: ComparisonTableSection | Status-based styling | 3 table_kinds | No sorting, no ranking colors |
| C6: InsurerExplanationSection | Template-based text | Default only | No comparative language |
| C7: CommonNotesSection | `forbidden_language.py` | Flat/Grouped | No color coding |
| C8: EvidenceAccordionSection | Verbatim snippet | Collapsed/Expanded | No summarization |

---

## 🎨 Design System Integration

### Typography
- **Headings**: System font stack (e.g., -apple-system, BlinkMacSystemFont, "Segoe UI")
- **Body**: Inherit from design system
- **Monospace** (snippets only): Consolas, Monaco, "Courier New"

### Color Palette (Neutral Financial Tone)

```css
/* Primary */
--color-text: #333;
--color-text-secondary: #666;
--color-text-muted: #999;

/* Backgrounds */
--color-bg-white: #FFF;
--color-bg-light: #F5F5F5;
--color-bg-lighter: #FAFAFA;
--color-bg-lightest: #F9F9F9;

/* Status-based (LOCKED) */
--color-confirmed: inherit;  /* No special color */
--color-unconfirmed: #666666;
--color-not-available: #999999;
--color-not-available-bg: #F5F5F5;

/* Borders */
--color-border: #DDD;
--color-border-light: #EEE;

/* Accents (minimal) */
--color-accent-warning: #FFA500;  /* For constraint messages only */
```

**FORBIDDEN Colors**:
- ❌ Green (#00C853) - Implies "good/better"
- ❌ Red (#FF0000) - Implies "bad/worse"
- ❌ Blue (#007BFF) - Implies "recommended"

### Spacing Scale
```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 12px;
--spacing-lg: 16px;
--spacing-xl: 20px;
```

### Border Radius
```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
```

---

## 🚫 Forbidden Patterns (Visual Design)

### ❌ Pattern 1: Amount-Based Ranking

**FORBIDDEN**:
```html
<!-- Color coding by value -->
<td style="background: green">3천만원</td>  ← Max
<td>2천만원</td>
<td style="background: red">1천만원</td>  ← Min
```

**CORRECT**:
```html
<!-- Status-based styling ONLY -->
<td class="amount-confirmed">3천만원</td>
<td class="amount-confirmed">2천만원</td>
<td class="amount-confirmed">1천만원</td>
```

---

### ❌ Pattern 2: Comparative Visual Links

**FORBIDDEN**:
```
┌─ 삼성화재 ─┐
│ 3천만원 ✓  │ ← "Best"
└────────────┘
      ↓ (arrow suggesting comparison)
┌─ 메리츠화재 ─┐
│ 2천만원     │
└────────────┘
```

**CORRECT**:
```
┌─ 삼성화재 ─────┐
│ 3천만원       │
└───────────────┘

┌─ 메리츠화재 ───┐
│ 2천만원       │
└───────────────┘
```
(Independent blocks, no visual hierarchy)

---

### ❌ Pattern 3: "AI Judgment" UI

**FORBIDDEN**:
```
[Assistant is analyzing...] ← "AI thinking" hint
[🤖 Based on your profile, I recommend...] ← AI persona
```

**CORRECT**:
```
[확인 중입니다...] ← Neutral system message
[2개 보험사의 암진단비를 비교합니다] ← Factual statement
```

---

## 📚 Related Documents

| Document | Purpose | Reference |
|----------|---------|-----------|
| `CHAT_UX_SCENARIOS.md` | UX scenario specifications (S1-S5) | STEP NEXT-15 |
| `CHAT_UX_DOS_AND_DONTS.md` | UX anti-patterns | STEP NEXT-15 |
| `COMPARISON_EXPLANATION_RULES.md` | Explanation templates | STEP NEXT-12 |
| `AMOUNT_PRESENTATION_RULES.md` | Status-based styling | STEP NEXT-11 |
| `CUSTOMER_EXAMPLE_SCREEN_MAPPING.md` | ViewModel → UI mapping | STEP NEXT-14-β |
| `FORBIDDEN_LANGUAGE_POLICY_SCOPE.md` | Language validation | STEP NEXT-14-β |

---

## 🔐 Contract Lock

**This component contract is LOCKED as of STEP NEXT-16.**

Any changes to:
- Component structure
- ViewModel field mapping
- Status-based styling
- Forbidden patterns

Require **version bump** and **documentation update**.

**Enforcement**:
- Figma components MUST follow this spec
- Frontend implementation MUST pass QA validation matrix
- Visual design MUST avoid forbidden patterns

---

**Lock Owner**: Product Team + Design Team + Frontend Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
