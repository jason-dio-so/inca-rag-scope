# Chat Layout Specification (Screen Structure)

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-16

---

## 🎯 Purpose

This document defines the **screen layout structure** for the Chat UI.

**Critical**: This spec describes ONLY the structural layout (frame hierarchy, spacing, alignment). Visual styling (colors, fonts, shadows) is intentionally minimal to focus on **information architecture**.

**ChatGPT-Style Caveat**: We borrow the **conversational layout rhythm** from ChatGPT (speech bubble alternation, vertical flow), but NOT the meaning (our system is deterministic, not LLM-based).

---

## 🔒 Layout Principles (Absolute Rules)

### P1. Vertical Information Flow
- Messages stack top-to-bottom (chronological order)
- Newest message at bottom
- Scroll to bottom on new message

### P2. Message Alternation
- User messages: Right-aligned
- System/Assistant messages: Left-aligned
- Visual rhythm: user ↔ assistant alternation

### P3. Section Ordering (LOCKED)
- Assistant message sections MUST render in ViewModel order
- NO re-ordering based on "importance"
- NO collapsing sections (except Evidence accordion)

### P4. No Comparative Layout
- Insurer blocks MUST be vertically stacked (NOT side-by-side comparison)
- NO visual hierarchy suggesting "better/worse"
- NO spatial arrangement implying ranking

---

## 📐 Screen Structure (Hierarchy)

```
┌──────────────────────────────────────────────────────┐
│ Header (Fixed, Top)                                  │ ← 60px height
├──────────────────────────────────────────────────────┤
│                                                      │
│ MessageScrollArea (Scrollable)                       │
│                                                      │
│   ┌──────────────────────────────────────┐          │
│   │ UserMessage (Right-aligned)          │          │
│   └──────────────────────────────────────┘          │
│                                                      │
│   ┌────────────────────────────────────────────┐    │
│   │ AssistantMessage (Left-aligned, full-width)│    │
│   │                                            │    │
│   │  [SummaryBulletBlock]                      │    │
│   │  [ComparisonTableSection]                  │    │
│   │  [InsurerExplanationSection]               │    │
│   │  [CommonNotesSection]                      │    │
│   │  [EvidenceAccordionSection]                │    │
│   │                                            │    │
│   └────────────────────────────────────────────┘    │
│                                                      │
│   ┌──────────────────────────────────────┐          │
│   │ UserMessage (Right-aligned)          │          │
│   └──────────────────────────────────────┘          │
│                                                      │
│   ┌────────────────────────────────────────────┐    │
│   │ SystemMessage (Centered or Left)           │    │
│   └────────────────────────────────────────────┘    │
│                                                      │
├──────────────────────────────────────────────────────┤
│ InputArea (Fixed, Bottom)                            │ ← 80px height
│ [Text Input] [Send Button]                          │
└──────────────────────────────────────────────────────┘
```

---

## 1. Header (Fixed Top)

### Layout Spec

```
┌──────────────────────────────────────────────────────┐
│ [Logo/Icon]  Service Name           [User Menu ▼]   │
└──────────────────────────────────────────────────────┘
```

**Dimensions**:
- Height: `60px` (fixed)
- Padding: `0 20px`
- Alignment: Space-between (logo left, menu right)

**Content**:
- Service branding (logo + name)
- User menu (optional, right-aligned)

**Visual Rules**:
- Background: White (#FFF) or light gray (#F5F5F5)
- Border-bottom: 1px solid #DDD
- Position: Fixed (sticky on scroll)

**Figma Frame**:
```
Frame: Header
├── Auto-layout: Horizontal
├── Padding: 0 20px
├── Height: 60px (fixed)
├── Items:
│   ├── Logo (Image, 32x32)
│   ├── ServiceName (Text, H5)
│   └── UserMenu (Dropdown, right-aligned)
```

---

## 2. MessageScrollArea (Scrollable Body)

### Layout Spec

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   [Message 1]                                        │
│                                                      │
│   [Message 2]                                        │
│                                                      │
│   [Message 3]                                        │
│                                                      │
│   ... (scrollable)                                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Dimensions**:
- Height: `calc(100vh - 140px)` (viewport minus header/input)
- Padding: `20px 40px` (desktop), `16px` (mobile)
- Max-width: `1024px` (centered on wide screens)

**Scroll Behavior**:
- Auto-scroll to bottom on new message
- Scroll indicator (optional)
- Smooth scroll animation

**Visual Rules**:
- Background: White (#FFF) or light gray (#FAFAFA)
- Overflow-y: Auto

**Figma Frame**:
```
Frame: MessageScrollArea
├── Auto-layout: Vertical
├── Padding: 20px 40px (desktop), 16px (mobile)
├── Gap: 20px (between messages)
├── Max-width: 1024px
├── Overflow: Scroll
```

---

## 3. Message Alignment Rules

### 3A. UserMessage (Right-Aligned)

```
                   ┌───────────────────────────┐
                   │ UserMessageBubble         │
                   │ "삼성화재랑 메리츠 비교" │
                   └───────────────────────────┘
```

**Alignment**:
- Margin-left: Auto (pushes right)
- Max-width: 70% of container
- Align-self: Flex-end

**Spacing**:
- Margin-bottom: 16px

**Figma Frame**:
```
Frame: UserMessage
├── Auto-layout: Horizontal, align-right
├── Max-width: 70%
├── Margin-left: Auto
```

---

### 3B. AssistantMessage (Left-Aligned, Full-Width)

```
┌──────────────────────────────────────────────────┐
│ AssistantMessageCard                             │
│                                                  │
│ [SummaryBulletBlock]                             │
│ [ComparisonTableSection]                         │
│ [InsurerExplanationSection]                      │
│ [CommonNotesSection]                             │
│ [EvidenceAccordionSection]                       │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Alignment**:
- Full-width (100% of container, max 1024px)
- Align-self: Flex-start (left-aligned)

**Spacing**:
- Margin-bottom: 24px (larger than user messages)

**Visual Container**:
- Background: White (#FFF)
- Border: 1px solid #EEE (optional)
- Border-radius: 12px
- Padding: 20px

**Figma Frame**:
```
Frame: AssistantMessageCard
├── Auto-layout: Vertical
├── Width: Fill container (max 1024px)
├── Padding: 20px
├── Background: #FFF
├── Border: 1px solid #EEE
├── Border-radius: 12px
├── Gap: 16px (between sections)
```

---

### 3C. SystemMessage (Centered or Left)

```
          ┌─────────────────────────────┐
          │ SystemMessageBubble         │
          │ "확인 중입니다..."          │
          └─────────────────────────────┘
```

**Alignment**:
- Centered (margin: 0 auto) for info/loading
- Left-aligned for clarification requests

**Spacing**:
- Margin-bottom: 12px

**Figma Frame**:
```
Frame: SystemMessage
├── Auto-layout: Horizontal, align-center
├── Max-width: 80%
├── Margin: 0 auto (centered)
```

---

## 4. Section Stacking (Inside AssistantMessage)

### Vertical Order (LOCKED)

**Order MUST follow ViewModel `sections[]` array**:

```
AssistantMessageCard
├── 1. SummaryBulletBlock (if exists)
├── 2. Section[0] (e.g., ComparisonTableSection)
├── 3. Section[1] (e.g., InsurerExplanationSection)
├── 4. Section[2] (e.g., CommonNotesSection)
├── 5. Section[N] (e.g., EvidenceAccordionSection)
```

**Spacing Between Sections**:
- Gap: 16px (vertical spacing)

**NO Re-ordering**:
- ❌ DO NOT move Evidence to top
- ❌ DO NOT group similar sections
- ✅ Render in exact ViewModel order

---

### Section Width

All sections are **full-width** within AssistantMessageCard:

```css
.section {
  width: 100%;
  margin-bottom: 16px;
}
```

**Exception**: ComparisonTableSection may have horizontal scroll on mobile if table is wide.

---

## 5. Input Area (Fixed Bottom)

### Layout Spec

```
┌──────────────────────────────────────────────────────┐
│ [────────── Text Input ──────────] [Send Button]     │
└──────────────────────────────────────────────────────┘
```

**Dimensions**:
- Height: 80px (fixed)
- Padding: 16px 20px

**Components**:
- Text Input (multi-line, max 3 rows)
- Send Button (primary action)

**Visual Rules**:
- Background: White (#FFF)
- Border-top: 1px solid #DDD
- Position: Fixed bottom
- Box-shadow: 0 -2px 10px rgba(0,0,0,0.05) (optional)

**Figma Frame**:
```
Frame: InputArea
├── Auto-layout: Horizontal
├── Height: 80px (fixed)
├── Padding: 16px 20px
├── Gap: 12px
├── Items:
│   ├── TextInput (flex: 1, multi-line)
│   └── SendButton (width: 80px, height: 48px)
```

---

## 6. Responsive Breakpoints

### Desktop (≥ 1024px)

```
┌──────────────────────────────────────────────────────┐
│ Header (Full-width)                                  │
├──────────────────────────────────────────────────────┤
│ MessageScrollArea (Max-width: 1024px, centered)      │
│                                                      │
│         ┌──────────────────────────┐                 │
│         │ AssistantMessage         │                 │
│         │ (Full-width, max 1024px) │                 │
│         └──────────────────────────┘                 │
│                                                      │
├──────────────────────────────────────────────────────┤
│ InputArea (Full-width)                               │
└──────────────────────────────────────────────────────┘
```

**Settings**:
- Container max-width: 1024px
- Padding: 20px 40px
- Table: Full-width within container

---

### Tablet (768px - 1023px)

```
┌────────────────────────────────────────┐
│ Header                                 │
├────────────────────────────────────────┤
│ MessageScrollArea (Padding reduced)    │
│                                        │
│   ┌──────────────────────────────┐    │
│   │ AssistantMessage             │    │
│   │ (Full-width)                 │    │
│   └──────────────────────────────┘    │
│                                        │
├────────────────────────────────────────┤
│ InputArea                              │
└────────────────────────────────────────┘
```

**Settings**:
- Container: Full-width
- Padding: 16px 24px
- Table: May require horizontal scroll

---

### Mobile (< 768px)

```
┌──────────────────────┐
│ Header (Compact)     │
├──────────────────────┤
│ MessageScrollArea    │
│                      │
│ ┌──────────────────┐ │
│ │ AssistantMessage │ │
│ │ (Full-width)     │ │
│ └──────────────────┘ │
│                      │
├──────────────────────┤
│ InputArea (Compact)  │
└──────────────────────┘
```

**Settings**:
- Container: Full-width
- Padding: 12px 16px
- UserMessage max-width: 80% (wider on mobile)
- Table: Horizontal scroll enabled

**Table Handling** (Mobile-Specific):

Option 1: Horizontal scroll
```css
.comparison-table-section {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

Option 2: Stacked layout (if table_kind allows)
```
담보명: 암진단비
├── 삼성화재: 3천만원
├── 메리츠화재: 2천만원
└── KB손해보험: 해당 담보 없음
```

---

## 7. Spacing Scale (Locked Values)

```css
/* Vertical Spacing */
--message-gap: 20px;  /* Between messages */
--section-gap: 16px;  /* Between sections within AssistantMessage */
--block-gap: 12px;    /* Within sections (e.g., bullet items) */

/* Horizontal Padding */
--container-padding-desktop: 40px;
--container-padding-tablet: 24px;
--container-padding-mobile: 16px;

/* Component Padding */
--card-padding: 20px;  /* AssistantMessageCard */
--section-padding: 16px;  /* Sections with background */
```

---

## 8. Scroll Behavior

### Auto-Scroll on New Message

```javascript
// Scroll to bottom when new message arrives
const scrollToBottom = () => {
  const scrollArea = document.querySelector('.message-scroll-area');
  scrollArea.scrollTop = scrollArea.scrollHeight;
};

// Trigger on new message
useEffect(() => {
  scrollToBottom();
}, [messages]);
```

### Smooth Scroll

```css
.message-scroll-area {
  scroll-behavior: smooth;
}
```

### Scroll Indicator (Optional)

When user scrolls up and new message arrives, show indicator:

```
                              ┌─────────────────┐
                              │ New message ↓   │
                              └─────────────────┘
```

---

## 9. Forbidden Layout Patterns

### ❌ Pattern 1: Side-by-Side Insurer Comparison

**FORBIDDEN**:
```
┌─────────────────────────────────────────┐
│ AssistantMessage                        │
│                                         │
│ ┌────────────┐    ┌────────────┐       │
│ │ 삼성화재   │    │ 메리츠화재 │       │  ← Side-by-side
│ │ 3천만원    │    │ 2천만원    │       │    implies comparison
│ └────────────┘    └────────────┘       │
│                                         │
└─────────────────────────────────────────┘
```

**CORRECT**:
```
┌─────────────────────────────────────────┐
│ AssistantMessage                        │
│                                         │
│ ┌──────────────────────────────────┐   │
│ │ 삼성화재                         │   │
│ │ 3천만원                          │   │
│ └──────────────────────────────────┘   │
│                                         │
│ ┌──────────────────────────────────┐   │
│ │ 메리츠화재                       │   │  ← Vertical stack
│ │ 2천만원                          │   │    (neutral)
│ └──────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Reason**: Side-by-side layout suggests visual comparison → ranking.

---

### ❌ Pattern 2: Spatial Ranking

**FORBIDDEN**:
```
┌─────────────────────────────────────────┐
│ AssistantMessage                        │
│                                         │
│ ┌──────────────────────────────────┐   │  ← Larger card
│ │ 삼성화재 (3천만원) ⭐             │   │    implies "better"
│ │ ...                              │   │
│ └──────────────────────────────────┘   │
│                                         │
│ ┌────────────────────┐                 │  ← Smaller card
│ │ 메리츠화재 (2천만원) │                 │    implies "worse"
│ └────────────────────┘                 │
│                                         │
└─────────────────────────────────────────┘
```

**CORRECT**:
```
┌─────────────────────────────────────────┐
│ AssistantMessage                        │
│                                         │
│ ┌──────────────────────────────────┐   │  ← Equal size
│ │ 삼성화재 (3천만원)               │   │
│ └──────────────────────────────────┘   │
│                                         │
│ ┌──────────────────────────────────┐   │  ← Equal size
│ │ 메리츠화재 (2천만원)             │   │
│ └──────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Reason**: All insurers must have equal visual weight (no hierarchy).

---

### ❌ Pattern 3: Section Re-ordering

**FORBIDDEN**:
```
AssistantMessage
├── 1. Evidence (moved to top)  ← Re-ordered
├── 2. SummaryBulletBlock
├── 3. ComparisonTableSection
```

**CORRECT**:
```
AssistantMessage
├── 1. SummaryBulletBlock  ← ViewModel order
├── 2. ComparisonTableSection
├── 3. Evidence (at bottom)
```

**Reason**: Section order is locked by ViewModel (deterministic).

---

## 10. Grid Specification (Optional)

For precise alignment, use 8px grid:

```css
/* 8px Grid System */
--grid-unit: 8px;

/* Spacing derived from grid */
--spacing-1: 8px;   /* 1 unit */
--spacing-2: 16px;  /* 2 units */
--spacing-3: 24px;  /* 3 units */
--spacing-4: 32px;  /* 4 units */
--spacing-5: 40px;  /* 5 units */
```

**Application**:
- Component padding: Multiples of 8px
- Margin/gap: Multiples of 8px
- Component heights: Multiples of 8px

---

## 11. Z-Index Layering

```css
/* Z-Index Scale */
--z-base: 0;         /* Message content */
--z-header: 100;     /* Fixed header */
--z-input: 100;      /* Fixed input area */
--z-accordion: 10;   /* Expanded accordion (above content) */
--z-modal: 1000;     /* Modal overlays (if any) */
```

**Usage**:
- Header and InputArea: `z-index: 100` (fixed above scrolling content)
- Accordion expanded state: `z-index: 10` (above sibling sections)

---

## 12. Animation Principles

### Message Entry Animation

**New message appears**:
```css
@keyframes slide-in-bottom {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message {
  animation: slide-in-bottom 0.3s ease-out;
}
```

### Accordion Expand/Collapse

```css
@keyframes expand {
  from {
    max-height: 0;
    opacity: 0;
  }
  to {
    max-height: 1000px;  /* Adjust based on content */
    opacity: 1;
  }
}

.accordion-body {
  animation: expand 0.3s ease-out;
  overflow: hidden;
}
```

**Constraint**: Animations must be subtle (no "flashy" effects that distract from content).

---

## 📚 Related Documents

| Document | Purpose | Reference |
|----------|---------|-----------|
| `CHAT_COMPONENT_CONTRACT.md` | Component specifications | STEP NEXT-16 |
| `CHAT_UX_SCENARIOS.md` | UX scenario flows | STEP NEXT-15 |
| `CUSTOMER_EXAMPLE_SCREEN_MAPPING.md` | ViewModel → UI mapping | STEP NEXT-14-β |
| `AMOUNT_PRESENTATION_RULES.md` | Status-based styling | STEP NEXT-11 |

---

## 🔐 Layout Lock

**This layout specification is LOCKED as of STEP NEXT-16.**

Any changes to:
- Screen structure (header/body/input)
- Message alignment rules
- Section stacking order
- Spacing scale

Require **version bump** and **documentation update**.

**Enforcement**:
- Figma frames MUST follow this hierarchy
- Frontend implementation MUST preserve section order
- QA tests validate responsive breakpoints

---

**Lock Owner**: Product Team + Design Team + Frontend Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
