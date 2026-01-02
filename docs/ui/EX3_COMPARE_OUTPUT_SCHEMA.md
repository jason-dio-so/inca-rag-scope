# EX3_COMPARE Output Schema SSOT

**STEP NEXT-77: EX3_COMPARE Response Format Lock**

## Purpose

Defines the **canonical response format** for Example 3 (Two-Insurer Integrated Comparison) in ChatGPT-style UI.

- **Scope**: `/chat` endpoint responses for Example 3 scenarios
- **SSOT Status**: This document defines the **exact JSON schema** that all EX3_COMPARE responses MUST follow
- **Anti-Contamination**: No raw text (DETAIL/EVIDENCE) in response body—**refs only**

---

## Schema Definition

### Message Kind

```json
{
  "kind": "EX3_COMPARE"
}
```

### Top-Level Structure

```typescript
interface EX3_CompareMessage {
  message_id: string;          // UUID
  request_id: string;          // From /chat request
  kind: "EX3_COMPARE";
  timestamp: string;           // ISO 8601

  title: string;               // e.g., "삼성화재 vs 메리츠화재 암진단비 비교"
  summary_bullets: string[];   // 2-4 bullets (fact-only)

  sections: Section[];         // [kpi, table, footnotes]

  lineage?: any;               // Audit metadata (optional)
}
```

---

## Section Types

### 1. KPI Section (Optional)

**Purpose**: Display KPI summary (payment type, limit, conditions) at the top of the comparison.

```typescript
interface KPISection {
  kind: "kpi_summary";
  title: string;                    // e.g., "주요 지표"

  kpi: {
    payment_type: string;           // "정액형" | "일당형" | "건별" | "실손" | "UNKNOWN"
    limit_summary: string | null;   // e.g., "1회당 3천만원 한도" | null
    conditions: {
      waiting_period?: string;      // e.g., "90일"
      reduction_condition?: string; // e.g., "1년 50%"
      exclusion_condition?: string; // e.g., "제자리암 제외"
      renewal_type?: string;        // e.g., "비갱신형"
    };
    refs: {
      kpi_evidence_refs: string[];          // KPI summary refs (EV:...)
      condition_evidence_refs: string[];    // Condition refs (EV:...)
    };
  };
}
```

**Display Rules**:
- `payment_type == "UNKNOWN"` → Display "표현 없음"
- `limit_summary == null` → Display "한도 표현 없음"
- `conditions` → Only show fields with values (skip if null/empty)
- `refs` → Enable "ⓘ 근거 보기" button only if refs exist

---

### 2. Comparison Table Section (Required)

**Purpose**: Show coverage comparison table (담보 × 보험사).

```typescript
interface ComparisonTableSection {
  kind: "comparison_table";
  table_kind: "INTEGRATED_COMPARE";
  title: string;                    // e.g., "암진단비 비교표"
  columns: string[];                // ["담보명", "삼성화재", "메리츠화재"]
  rows: TableRow[];
}

interface TableRow {
  cells: TableCell[];
  is_header: boolean;               // true for header row
  meta?: TableRowMeta;              // Row-level metadata
}

interface TableCell {
  text: string;                     // Display text (e.g., "3000만원", "명시 없음")
  meta?: CellMeta;                  // Cell-level metadata (optional)
}

interface CellMeta {
  status?: string;                  // "CONFIRMED" | "UNCONFIRMED" | "NOT_AVAILABLE"
  doc_ref?: string;                 // DEPRECATED (use row.meta instead)
}

interface TableRowMeta {
  proposal_detail_ref?: string;     // PD:{insurer}:{coverage_code}
  evidence_refs?: string[];         // [EV:{insurer}:{coverage_code}:01, ...]
  kpi_summary?: KPISummaryMeta;     // STEP NEXT-75
  kpi_condition?: KPIConditionMeta; // STEP NEXT-76
}
```

**Display Rules**:
- Headers (`is_header: true`) → **Bold** styling
- Cell status → Background color (gray for UNCONFIRMED, red for NOT_AVAILABLE)
- NO color-based superiority (❌ red=better, blue=worse)
- NO automatic sorting by amount

**refs Rules**:
- `row.meta.proposal_detail_ref` → "보장내용 보기" button (lazy load via `/store/proposal-detail/{ref}`)
- `row.meta.evidence_refs` → "근거 보기" toggle (lazy load via `/store/evidence/batch`)
- If refs are missing or empty → buttons disabled

---

### 3. Footnotes Section (Optional)

**Purpose**: Display common notes, caveats, or disclaimers.

```typescript
interface FootnotesSection {
  kind: "common_notes";
  title: string;                    // e.g., "공통사항 및 유의사항"
  bullets?: string[];               // Legacy flat list
  groups?: BulletGroup[];           // Grouped bullets (preferred)
}

interface BulletGroup {
  title: string;                    // e.g., "공통사항"
  bullets: string[];                // ["가입설계서 기준", ...]
}
```

**Display Rules**:
- Render `groups` if exists (preferred)
- Fallback to `bullets` if `groups` is null/empty
- Bullets MUST NOT contain forbidden phrases (validated by policy module)

---

## Example Response (Complete)

```json
{
  "message_id": "a1b2c3d4-...",
  "request_id": "req-12345",
  "kind": "EX3_COMPARE",
  "timestamp": "2026-01-02T10:00:00Z",

  "title": "삼성화재 vs 메리츠화재 암진단비 비교",
  "summary_bullets": [
    "2개 보험사의 암진단비를 비교했습니다",
    "가입설계서 기준 금액입니다"
  ],

  "sections": [
    {
      "kind": "kpi_summary",
      "title": "주요 지표",
      "kpi": {
        "payment_type": "정액형",
        "limit_summary": null,
        "conditions": {
          "waiting_period": "90일",
          "exclusion_condition": "유사암 제외"
        },
        "refs": {
          "kpi_evidence_refs": ["EV:samsung:A4200_1:01", "EV:meritz:A4200_1:02"],
          "condition_evidence_refs": ["EV:samsung:A4200_1:03"]
        }
      }
    },
    {
      "kind": "comparison_table",
      "table_kind": "INTEGRATED_COMPARE",
      "title": "암진단비 비교표",
      "columns": ["담보명", "삼성화재", "메리츠화재"],
      "rows": [
        {
          "cells": [
            {"text": "암진단비(유사암 제외)"},
            {"text": "3000만원"},
            {"text": "5000만원"}
          ],
          "is_header": false,
          "meta": {
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"],
            "kpi_summary": {
              "payment_type": "정액형",
              "limit_summary": null,
              "kpi_evidence_refs": ["EV:samsung:A4200_1:01"],
              "extraction_notes": ""
            }
          }
        }
      ]
    },
    {
      "kind": "common_notes",
      "title": "공통사항 및 유의사항",
      "groups": [
        {
          "title": "공통사항",
          "bullets": ["가입설계서 기준 비교입니다"]
        },
        {
          "title": "유의사항",
          "bullets": ["실제 약관과 다를 수 있습니다"]
        }
      ]
    }
  ],

  "lineage": {
    "handler": "EX3CompareComposer",
    "llm_used": false,
    "deterministic": true
  }
}
```

---

## Display Rules Summary

### KPI Display
1. **payment_type**:
   - `UNKNOWN` → "표현 없음"
   - Otherwise → Display value as-is
2. **limit_summary**:
   - `null` → "한도 표현 없음"
   - Otherwise → Display value as-is
3. **conditions**:
   - Show only non-null fields
   - Empty/null fields → Do not display
4. **"명시 없음"**:
   - Use ONLY when DETAIL/EVIDENCE structurally does not exist
   - If evidence found but pattern not detected → `extraction_notes` only (value stays null/"명시 없음")

### Table Display
1. **Headers** → Bold
2. **Cell status** → Background color (neutral, NO superiority implication)
3. **refs** → Enable buttons/toggles only if refs exist
4. **NO text in response body** → All DETAIL/EVIDENCE via lazy load

### Footnotes Display
1. **groups** (preferred) → Render as grouped bullets
2. **bullets** (fallback) → Render as flat list

---

## Constitutional Rules (Hard Stop)

1. ❌ **NO LLM usage** (deterministic only)
2. ❌ **NO raw text in response body** (refs only)
3. ✅ **refs MUST use PD:/EV: prefix** (validation required)
4. ✅ **"명시 없음" ONLY when structurally missing** (not for pattern mismatch)
5. ✅ **Forbidden phrase validation** (all text fields)

---

## Validation Checklist (DoD)

- [ ] Response has `kind: "EX3_COMPARE"`
- [ ] `title` and `summary_bullets` are present
- [ ] All refs use `PD:` or `EV:` prefix
- [ ] NO `raw_text`, `benefit_description_text`, or large text fields in response body
- [ ] KPI section (if present) has `refs.kpi_evidence_refs` or `refs.condition_evidence_refs`
- [ ] Table rows have `meta.proposal_detail_ref` or `meta.evidence_refs` (if evidence exists)
- [ ] Forbidden phrase validation passes

---

**Version**: STEP NEXT-77
**Date**: 2026-01-02
**Status**: SSOT (Single Source of Truth)
