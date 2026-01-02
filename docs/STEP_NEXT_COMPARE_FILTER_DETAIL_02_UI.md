# STEP NEXT-COMPARE-FILTER-DETAIL-02: Frontend UI Implementation

**Date**: 2026-01-01
**Status**: ✅ COMPLETED
**Mode**: LLM OFF (client-side rendering only)

## Objective

고객이 원하는 "보장한도가 다른 상품 찾아줘" 화면이 빈약하지 않도록:
- 그룹 요약 + 보험사별 근거/원문/정규화 값을 UI에서 충분히 펼쳐 보여준다
- "명시 없음", "절번호(4-1)" 같은 케이스를 설명 가능한 형태로 표시
- 런타임 에러(undefined/map/join/[object Object]) **0건**

---

## Changes Made

### 1. Updated Types (`apps/web/lib/types.ts`)

**New Types**:
```typescript
export interface EvidenceRef {
  doc_type: string;
  page: number;
  file_path?: string;
  snippet?: string;
}

export interface InsurerDetail {
  insurer: string;
  raw_text?: string;
  evidence_refs?: EvidenceRef[];
  notes?: string[];
}

export interface DiffGroup {
  value_display: string;
  insurers: string[];
  value_normalized?: Record<string, any>;  // NEW
  insurer_details?: InsurerDetail[];        // NEW
}

export interface CoverageDiffResultSection {
  kind: "coverage_diff_result";
  title: string;
  field_label: string;
  status: "DIFF" | "ALL_SAME";
  groups: DiffGroup[];
  diff_summary?: string;
  extraction_notes?: string[];  // NEW
}
```

---

### 2. Enriched Component (`apps/web/components/cards/CoverageDiffCard.tsx`)

**Features**:
1. **Summary Section**: Diff summary banner or "ALL_SAME" message
2. **Group Cards** (3-tier structure):
   - Header: value_display + insurer count
   - Normalized Summary: Structured limit/payment/condition display
   - Insurer Badges: Color-coded (yellow for "명시 없음")
3. **Insurer Details Accordion** (collapsible per group):
   - Per-insurer sections with:
     - Insurer name (mapped from code to display)
     - Raw text (evidence snippet)
     - Notes (extraction failure reasons)
     - Evidence refs (doc_type + page + snippet)
4. **Extraction Notes**: Global notes at bottom (e.g., "4-1 같은 절 번호는 제외")

**Component Structure**:
```
CoverageDiffCard
├─ Summary (diff_summary or ALL_SAME banner)
├─ Groups (map)
│  └─ GroupCard
│     ├─ Header (value_display + count)
│     ├─ Normalized Summary (optional)
│     ├─ Insurer Badges
│     └─ InsurerDetailsAccordion (collapsible)
│        └─ Per-insurer details
│           ├─ Raw text
│           ├─ Notes
│           └─ EvidenceList
└─ Extraction Notes (global)
```

---

## UI Elements

### Summary Section
- **DIFF mode**: Amber banner with diff_summary
- **ALL_SAME mode**: Blue banner with common value

### Group Cards
- **Normal**: White background, gray border
- **명시 없음**: Yellow background (`bg-yellow-50 border-yellow-300`)

### Normalized Summary
- Blue box with structured fields:
  - `횟수=1회 | 조건=최초`
  - `유형=일시금`
  - `태그=면책, 감액`

### Insurer Details Accordion
- Toggle button: "▶ 보험사별 근거 보기 (3개)"
- Expanded state:
  - Per-insurer gray boxes
  - Raw text in white bordered box
  - Notes in amber text
  - Evidence refs (max 3 shown, with "더보기" note)

### Extraction Notes
- Gray box at bottom
- Bullet list format
- Explains filtering/extraction decisions

---

## Safety Guards

All rendering is defensive:
```typescript
// Array guards
const groups = Array.isArray(section.groups) ? section.groups : [];
Array.isArray(group.insurers) ? group.insurers.map(...) : null

// String guards
String(value ?? "")
String(detail.raw_text).trim()

// Null checks
{detail.raw_text && String(detail.raw_text).trim() && (...)}
{Array.isArray(refs) && refs.length > 0 && (...)}
```

**No [object Object]**:
- All non-string values are converted with `String()`
- Objects are never directly rendered in JSX

---

## Insurer Name Mapping

```typescript
const INSURER_NAMES: Record<string, string> = {
  samsung: '삼성화재',
  meritz: '메리츠화재',
  db: 'DB손해보험',
  kb: 'KB손해보험',
  hanwha: '한화손해보험',
  hyundai: '현대해상',
  lotte: '롯데손해보험',
  heungkuk: '흥국화재',
};

function getInsurerDisplay(code: string): string {
  return INSURER_NAMES[code] || code;
}
```

---

## Before/After Comparison

### BEFORE (Basic diff card)
- ❌ Just value + insurer badges
- ❌ No evidence/sources
- ❌ No explanation for "명시 없음"
- ❌ No normalized structure display
- ❌ **Looks empty/sparse**

### AFTER (Enriched diff card)
- ✅ Value + normalized summary
- ✅ Accordion with per-insurer evidence
- ✅ Notes explaining "명시 없음" cases
- ✅ Evidence refs (doc_type, page, snippet)
- ✅ **Rich, professional UI**

---

## Testing Checklist

### ✅ Completed
- [x] Types updated with enriched schema
- [x] CoverageDiffCard component rewritten
- [x] Defensive array/null guards in place
- [x] String conversions for all renders
- [x] Insurer name mapping functional
- [x] Accordion state management (useState)
- [x] TypeScript compiles without errors
- [x] Next.js dev server running without errors

### 🔄 Manual Testing Required (User to verify)
- [ ] DIFF query: "암직접입원비 보장한도가 다른 상품 찾아줘"
  - Diff banner shows
  - Groups display with normalized summaries
  - Accordion expands to show per-insurer details
  - Evidence refs visible
- [ ] ALL_SAME case
  - Blue banner with common value
  - No diff summary
- [ ] "명시 없음" case
  - Yellow background
  - Notes explaining extraction failure
  - extraction_notes at bottom

### Expected Console Output
- ✅ No `undefined.map` errors
- ✅ No `[object Object]` in UI
- ✅ No TypeScript errors

---

## Files Modified

1. **apps/web/lib/types.ts**
   - Added `EvidenceRef`, `InsurerDetail` interfaces
   - Updated `DiffGroup` with `value_normalized` and `insurer_details`
   - Updated `CoverageDiffResultSection` with `extraction_notes`

2. **apps/web/components/cards/CoverageDiffCard.tsx**
   - Complete rewrite (307 lines)
   - Added helper functions:
     - `getInsurerDisplay()`
     - `renderNormalizedSummary()`
     - `EvidenceList` component
     - `InsurerDetailsAccordion` component
     - `GroupCard` component
   - Main component with ALL_SAME/DIFF modes

---

## Example API Response Structure

```json
{
  "kind": "coverage_diff_result",
  "title": "보장한도 비교 결과",
  "field_label": "보장한도",
  "status": "DIFF",
  "diff_summary": "메리츠화재가 다릅니다 (명시 없음)",
  "groups": [
    {
      "value_display": "최초 1회",
      "insurers": ["samsung", "hanwha"],
      "value_normalized": {
        "count": 1,
        "qualifier": ["최초"],
        "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
        "evidence_refs": [...]
      },
      "insurer_details": [
        {
          "insurer": "samsung",
          "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
          "evidence_refs": [
            {
              "doc_type": "약관",
              "page": 10,
              "snippet": "최초 1회 한 진단비를 보험가입금액으로 지급합니다"
            }
          ]
        }
      ]
    },
    {
      "value_display": "명시 없음",
      "insurers": ["meritz"],
      "insurer_details": [
        {
          "insurer": "meritz",
          "raw_text": "암직접입원비에 대한 보장",
          "notes": ["관련 근거 발견되었으나 명시적 패턴 미검출"],
          "evidence_refs": [...]
        }
      ]
    }
  ],
  "extraction_notes": [
    "meritz: 근거 문서에서 보장한도 패턴 미검출"
  ]
}
```

---

## Styling Notes

**Colors**:
- DIFF banner: Amber (`bg-amber-50 border-amber-200 text-amber-900`)
- ALL_SAME banner: Blue (`bg-blue-50 border-blue-200 text-blue-900`)
- 명시 없음 card: Yellow (`bg-yellow-50 border-yellow-300`)
- Normal card: White (`bg-white border-gray-200`)
- Normalized summary: Light blue (`bg-blue-50 border-blue-200`)
- Evidence refs: Gray (`bg-gray-50 border-gray-200`)

**Typography**:
- Title: `text-lg font-semibold`
- Value display: `text-lg font-semibold`
- Normalized summary: `text-xs text-gray-600`
- Insurer badges: `text-sm font-medium`
- Evidence: `text-xs`

---

## Next Steps (Optional)

**Future Enhancements**:
- Add "더보기" modal for evidence refs > 3
- Add copy-to-clipboard for raw_text
- Add hover tooltips for doc_type/file_path
- Add evidence filtering by doc_type

**Performance**:
- Memoize `renderNormalizedSummary` if groups > 10
- Lazy load accordion content (only render when opened)

---

## Summary

✅ **Frontend UI for STEP NEXT-COMPARE-FILTER-DETAIL-02 is complete**

- Rich 3-tier card structure (summary → groups → insurer details)
- Accordion-based evidence display
- Defensive rendering (no runtime errors)
- Professional UX with color-coding and structured data
- LLM OFF compliant (pure rendering)

**Ready for user testing** at `http://localhost:3000`
