# Frontend Integration Guide (STEP NEXT-14-β Production Hardening)

**Version**: 1.1.0-beta
**Status**: 🔒 **LOCKED** (Production Hardened)
**Lock Date**: 2025-12-29
**STEP**: NEXT-14-β

---

## 🚨 CRITICAL CHANGES IN 14-β (Production Hardening)

### 1. **Deterministic Kind Routing** (ALWAYS use this in production)

**PRODUCTION FLOW** (100% deterministic):
```typescript
POST /chat {
  "message": "암진단비 상세 비교",
  "kind": "EX2_DETAIL",  // <-- Set from FAQ button (REQUIRED)
  "coverage_names": ["암진단비"],
  "insurers": ["삼성화재", "메리츠화재"]
}
```

**Kind Values**:
- `EX2_DETAIL` - Coverage detail comparison
- `EX3_INTEGRATED` - Integrated comparison
- `EX4_ELIGIBILITY` - Eligibility matrix
- `EX1_PREMIUM_DISABLED` - Premium disabled notice

**FALLBACK** (keyword-based, NOT recommended):
```typescript
POST /chat {
  "kind": null,  // Will use keyword router (accuracy not guaranteed)
  ...
}
```

### 2. **Minimized Section Types** (5 CORE TYPES - Maps to Figma components)

| API Section Kind | Figma Component | Description |
|------------------|-----------------|-------------|
| `comparison_table` | `ComparisonTable` | All comparison tables (detail/integrated/eligibility) |
| `insurer_explanations` | `InsurerExplanationBlocks` | Parallel insurer explanations (independent blocks) |
| `common_notes` | `CommonNotes` | Common notes + notices (unified bullet list) |
| `evidence_accordion` | `EvidenceAccordion` | Collapsible evidence (collapsed by default) |

**Note**: `summary_bullets` is part of `AssistantMessageVM` top-level (not a section).

### 3. **Forbidden Language Policy** (Single Source of Truth)

All text validation uses `apps/api/policy/forbidden_language.py`.

**ALLOWED** (Factual statements):
- "비교합니다", "확인합니다", "표시합니다", "명시되어 있습니다"
- "차이를 확인", "보다 자세"

**FORBIDDEN** (Evaluative/Comparative):
- "A가 B보다", "더 높다", "유리하다", "추천합니다", "가장 좋다", "평균"

**Frontend Rule**: NEVER parse/interpret text. Render `value_text` and `explanation` as-is.

---

## 🎨 Figma Component Mapping

### Top-Level Structure
```
AssistantMessageCard
├─ SummaryCard (summary_bullets)
├─ ComparisonTable (section[0] if kind=comparison_table)
├─ InsurerExplanationBlocks (section[1] if kind=insurer_explanations)
├─ CommonNotes (section[2] if kind=common_notes)
└─ EvidenceAccordion (section[3] if kind=evidence_accordion)
```

### Component Specs

**1. SummaryCard**
```typescript
interface SummaryCardProps {
  bullets: string[]  // from AssistantMessageVM.summary_bullets
}
```

**2. ComparisonTable**
```typescript
interface ComparisonTableProps {
  columns: string[]
  rows: TableRow[]
  table_kind: "COVERAGE_DETAIL" | "INTEGRATED_COMPARE" | "ELIGIBILITY_MATRIX"
}
```

**3. InsurerExplanationBlocks**
```typescript
interface InsurerExplanationBlocksProps {
  explanations: Array<{
    insurer: string
    text: string  // Render as-is (NO parsing)
  }>
}
```

**4. CommonNotes**
```typescript
interface CommonNotesProps {
  title: string  // e.g., "공통사항 및 유의사항"
  bullets: string[]
}
```

**5. EvidenceAccordion**
```typescript
interface EvidenceAccordionProps {
  items: Array<{
    evidence_ref_id: string
    insurer: string
    coverage_name: string
    doc_type: string
    page: number | null
    snippet: string | null
  }>
  defaultCollapsed: true
}
```

---

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-13

---

## 🎯 Purpose

This document defines **frontend integration contract** for inca-rag-scope UI.

**CRITICAL**: This is a **UI integration guide**, NOT a design guide.
- NO custom interpretation of API responses
- NO client-side calculations or comparisons
- NO deviation from presentation rules

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            User Browser (Frontend)               │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │   UI Components (React/Vue/HTML)       │     │
│  │   - AmountDisplay                      │     │
│  │   - ExplanationDisplay                 │     │
│  │   - ComparisonTable                    │     │
│  └────────────────────────────────────────┘     │
│                    ▼                             │
│  ┌────────────────────────────────────────┐     │
│  │   API Client (Fetch/Axios)             │     │
│  │   - POST /compare                      │     │
│  │   - GET /explanation (future)          │     │
│  └────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
                      ▼ HTTPS
┌─────────────────────────────────────────────────┐
│          API Server (FastAPI)                    │
│  - Amount Read Contract (LOCKED)                │
│  - Explanation Layer (LOCKED)                   │
└─────────────────────────────────────────────────┘
```

---

## 🔌 API Integration

### Base URL

```javascript
// Development
const API_BASE_URL = "http://localhost:8000";

// Production
const API_BASE_URL = "https://api.inca-rag-scope.example.com";
```

**CORS**: API server allows `localhost:8000`, `localhost:9000` (dev mode)

---

### API Contract Reference

| Endpoint | Purpose | Contract Document |
|----------|---------|-------------------|
| `POST /compare` | Compare insurance products | `docs/api/AMOUNT_READ_CONTRACT.md` |
| `GET /explanation` | Get comparison explanations (future) | `docs/ui/COMPARISON_EXPLANATION_RULES.md` |
| `GET /health` | API healthcheck | N/A |

**CRITICAL**: API contracts are **IMMUTABLE**. UI must adapt to API, NOT vice versa.

---

## 📝 Request Format

### Compare Request

```javascript
// POST /compare
const request = {
  products: [
    {
      insurer: "삼성화재",
      product_name: "다이렉트 암보험"
    },
    {
      insurer: "KB손해보험",
      product_name: "KB 암보험"
    }
  ],
  target_coverages: [
    {
      coverage_code: "A4200_1"  // Preferred: canonical code
    },
    {
      coverage_name_raw: "암진단비"  // Fallback: raw name
    }
  ],
  options: {
    include_notes: true,
    include_evidence: true,
    premium_reference_only: false
  }
};

fetch(`${API_BASE_URL}/compare`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(request)
})
.then(res => res.json())
.then(data => {
  // Handle response (see below)
});
```

---

## 📊 Response Format

### Compare Response Structure

```typescript
interface CompareResponse {
  query_id: string;          // UUID
  timestamp: string;         // ISO 8601
  request: {
    products: ProductInfo[];
    target_coverages: TargetCoverage[];
  };
  results: CoverageComparison[];
  audit?: {
    audit_run_id: string;    // UUID
    freeze_tag: string;      // e.g., "freeze/pre-10b2g2-20251229-024400"
    git_commit: string;      // Frozen commit hash
  };
}

interface CoverageComparison {
  coverage_code: string;     // e.g., "A4200_1"
  coverage_name: string;     // e.g., "암진단비"
  values: {
    [insurer: string]: {
      value_text: string | null;
      evidence?: {
        status: "found" | "not_found";
        source?: string;
        snippet?: string;
      };
    }
  };
}
```

**Example Response**:

```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-29T10:30:00Z",
  "results": [
    {
      "coverage_code": "A4200_1",
      "coverage_name": "암진단비",
      "values": {
        "삼성화재": {
          "value_text": "3천만원",
          "evidence": {
            "status": "found",
            "source": "가입설계서 p.4",
            "snippet": "암진단비: 3천만원"
          }
        },
        "KB손해보험": {
          "value_text": null,
          "evidence": {
            "status": "not_found"
          }
        }
      }
    }
  ],
  "audit": {
    "audit_run_id": "f2e58b52-f22d-4d66-8850-df464954c9b8",
    "freeze_tag": "freeze/pre-10b2g2-20251229-024400"
  }
}
```

---

## 🎨 Presentation Rules (LOCKED)

### Status-Based Display Logic

**Rule 1: value_text determines display**

```javascript
function getDisplayValue(insurerData) {
  if (insurerData.value_text) {
    // CONFIRMED: Show value_text as-is
    return {
      text: insurerData.value_text,
      style: "normal",
      color: "inherit"
    };
  } else {
    // UNCONFIRMED or NOT_AVAILABLE
    return {
      text: "금액 명시 없음",
      style: "italic",
      color: "#666666"
    };
  }
}
```

**CRITICAL**: DO NOT interpret or calculate from `value_text`. Display as-is.

---

### Presentation Table (LOCKED)

| value_text | Display Text | Style | Color | Tooltip |
|-----------|--------------|-------|-------|---------|
| **Present** (e.g., "3천만원") | `value_text` | Normal | Inherit | "가입설계서에 명시된 금액입니다" |
| **null** | "금액 명시 없음" | Italic | #666666 | "문서상 금액이 명시되지 않았습니다" |

**Additional Styling** (Optional):

```css
/* CONFIRMED style */
.amount-confirmed {
  font-weight: normal;
  color: inherit;
}

/* UNCONFIRMED style */
.amount-unconfirmed {
  font-style: italic;
  color: #666666;
}

/* NOT_AVAILABLE style (if distinguishable) */
.amount-not-available {
  text-decoration: line-through;
  color: #999999;
}
```

---

## ❌ Forbidden Operations (CRITICAL)

### Forbidden UI Operations

| Operation | Example | Why Forbidden |
|-----------|---------|---------------|
| **Color Coding for Comparison** | Green for max, red for min | Implies better/worse |
| **Sorting by Amount** | Sort table by value_text | Creates ranking |
| **Highlighting Max/Min** | Bold highest amount | Creates comparison |
| **Calculations** | Show average, total | NOT in API contract |
| **Charts/Graphs** | Bar chart by amount | Visual comparison |
| **Recommendations** | "Best choice: ..." | Evaluation |
| **Value Extraction** | Parse "3천만원" → 30000000 | Amount inference |

**Enforcement**: Code review + UI testing

---

### Forbidden Words in UI

DO NOT display these words in comparison context:

```
더, 보다, 반면, 그러나, 하지만
유리, 불리, 높다, 낮다, 많다, 적다
차이, 비교, 우수, 열등, 좋, 나쁜
가장, 최고, 최저, 평균, 합계
추천, 제안, 권장, 선택, 판단
```

**Example Violations**:

```html
<!-- ❌ WRONG -->
<div>삼성화재가 KB손해보험보다 더 높습니다</div>
<div>가장 유리한 상품은 삼성화재입니다</div>
<div>평균 보장금액: 2천5백만원</div>

<!-- ✅ CORRECT -->
<div>삼성화재: 3천만원</div>
<div>KB손해보험: 금액 명시 없음</div>
```

---

## 🧩 UI Component Examples

### React Component (Recommended)

```tsx
import React from 'react';

interface AmountDisplayProps {
  insurer: string;
  coverageName: string;
  valueText: string | null;
  evidence?: {
    status: "found" | "not_found";
    source?: string;
    snippet?: string;
  };
}

const AmountDisplay: React.FC<AmountDisplayProps> = ({
  insurer,
  coverageName,
  valueText,
  evidence
}) => {
  // Determine display based on value_text presence
  const displayValue = valueText || "금액 명시 없음";
  const styleClass = valueText ? "amount-confirmed" : "amount-unconfirmed";
  const tooltip = valueText
    ? "가입설계서에 명시된 금액입니다"
    : "문서상 금액이 명시되지 않았습니다";

  return (
    <div className={`amount-display ${styleClass}`} title={tooltip}>
      <div className="insurer-name">{insurer}</div>
      <div className="amount-value">{displayValue}</div>
      {evidence?.status === "found" && (
        <div className="evidence-source">{evidence.source}</div>
      )}
    </div>
  );
};

export default AmountDisplay;
```

---

### Vue Component

```vue
<template>
  <div :class="['amount-display', styleClass]" :title="tooltip">
    <div class="insurer-name">{{ insurer }}</div>
    <div class="amount-value">{{ displayValue }}</div>
    <div v-if="evidence?.status === 'found'" class="evidence-source">
      {{ evidence.source }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  insurer: String,
  coverageName: String,
  valueText: String,
  evidence: Object
});

const displayValue = computed(() => {
  return props.valueText || "금액 명시 없음";
});

const styleClass = computed(() => {
  return props.valueText ? "amount-confirmed" : "amount-unconfirmed";
});

const tooltip = computed(() => {
  return props.valueText
    ? "가입설계서에 명시된 금액입니다"
    : "문서상 금액이 명시되지 않았습니다";
});
</script>
```

---

### Plain HTML/JavaScript

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .amount-confirmed {
      font-weight: normal;
      color: inherit;
    }
    .amount-unconfirmed {
      font-style: italic;
      color: #666666;
    }
  </style>
</head>
<body>
  <div id="comparison-table"></div>

  <script>
    async function loadComparison() {
      const response = await fetch('http://localhost:8000/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          products: [
            { insurer: "삼성화재", product_name: "다이렉트 암보험" }
          ],
          target_coverages: [
            { coverage_code: "A4200_1" }
          ]
        })
      });

      const data = await response.json();
      const tableDiv = document.getElementById('comparison-table');

      data.results.forEach(coverage => {
        const coverageDiv = document.createElement('div');
        coverageDiv.innerHTML = `<h3>${coverage.coverage_name}</h3>`;

        Object.entries(coverage.values).forEach(([insurer, data]) => {
          const displayValue = data.value_text || "금액 명시 없음";
          const styleClass = data.value_text ? "amount-confirmed" : "amount-unconfirmed";

          const amountDiv = document.createElement('div');
          amountDiv.className = styleClass;
          amountDiv.textContent = `${insurer}: ${displayValue}`;
          coverageDiv.appendChild(amountDiv);
        });

        tableDiv.appendChild(coverageDiv);
      });
    }

    loadComparison();
  </script>
</body>
</html>
```

---

## 📋 Comparison Table Layout

### Recommended Layout

```
┌─────────────────────────────────────────────────┐
│  Coverage: 암진단비 (A4200_1)                    │
├─────────────────────────────────────────────────┤
│  보험사         │  금액          │  출처          │
├─────────────────┼────────────────┼───────────────┤
│  삼성화재       │  3천만원       │  가입설계서 p.4│
│  KB손해보험     │  금액 명시 없음│  -             │
│  현대해상       │  2천만원       │  가입설계서 p.5│
└─────────────────────────────────────────────────┘
```

**Layout Rules**:
- ✅ Independent rows per insurer
- ✅ Input order preserved (NO sorting by amount)
- ✅ Consistent column widths
- ❌ NO color coding by amount
- ❌ NO highlighting max/min
- ❌ NO calculated fields (average, total)

---

## 🔍 Evidence Display

### Evidence Tooltip (Optional)

```javascript
function formatEvidenceTooltip(evidence) {
  if (!evidence || evidence.status === "not_found") {
    return "증거 없음";
  }

  return `
출처: ${evidence.source}

원문:
${evidence.snippet}
  `.trim();
}
```

**Display Options**:
- ✅ Tooltip on hover
- ✅ Expandable section
- ✅ Modal dialog
- ❌ Inline long snippets (breaks layout)

---

## 🧪 Testing Requirements

### UI Contract Tests

```javascript
describe('Amount Display Component', () => {
  test('CONFIRMED: displays value_text as-is', () => {
    const component = render(
      <AmountDisplay
        insurer="삼성화재"
        valueText="3천만원"
      />
    );
    expect(component.text()).toContain("3천만원");
    expect(component.hasClass("amount-confirmed")).toBe(true);
  });

  test('UNCONFIRMED: displays fixed text', () => {
    const component = render(
      <AmountDisplay
        insurer="KB손해보험"
        valueText={null}
      />
    );
    expect(component.text()).toContain("금액 명시 없음");
    expect(component.hasClass("amount-unconfirmed")).toBe(true);
  });

  test('NO forbidden words in output', () => {
    const component = render(
      <ComparisonTable
        insurers={["삼성화재", "KB손해보험"]}
        amounts={["3천만원", null]}
      />
    );
    const html = component.html();
    const forbiddenWords = ["더", "보다", "유리", "불리", "높다"];
    forbiddenWords.forEach(word => {
      expect(html).not.toContain(word);
    });
  });
});
```

---

## 🚨 Error Handling

### API Error Responses

```javascript
async function fetchComparison(request) {
  try {
    const response = await fetch(`${API_BASE_URL}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "API request failed");
    }

    return await response.json();

  } catch (error) {
    console.error("Comparison fetch failed:", error);

    // Display user-friendly error
    return {
      error: true,
      message: "보험 비교 조회에 실패했습니다. 잠시 후 다시 시도해주세요."
    };
  }
}
```

**User-Facing Error Messages**:

| Error Type | Display Message |
|-----------|-----------------|
| Network Error | "네트워크 연결을 확인해주세요" |
| 400 Bad Request | "입력 정보를 확인해주세요" |
| 404 Not Found | "해당 상품 정보를 찾을 수 없습니다" |
| 500 Server Error | "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요" |

---

## 📞 Support

| Issue Type | Contact | Reference |
|------------|---------|-----------|
| API Integration | Backend Team | `docs/api/AMOUNT_READ_CONTRACT.md` |
| Presentation Rules | UI Team | `docs/ui/AMOUNT_PRESENTATION_RULES.md` |
| Explanation Display | UI Team | `docs/ui/COMPARISON_EXPLANATION_RULES.md` |
| Deployment | DevOps Team | `docs/deploy/PRODUCTION_DEPLOYMENT.md` |

---

## 🎯 Frontend Integration Checklist

- ✅ API client configured (`POST /compare`)
- ✅ Response parsing follows contract
- ✅ value_text displayed as-is (NO parsing)
- ✅ Status-based styling applied
- ✅ NO forbidden words in UI
- ✅ NO color coding for comparison
- ✅ NO sorting by amount
- ✅ NO calculations (average, total)
- ✅ Evidence display optional
- ✅ Error handling implemented
- ✅ Unit tests for contract compliance

---

**Lock Owner**: Frontend Team + API Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
