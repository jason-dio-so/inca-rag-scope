# STEP NEXT — Chat UI v2 Specification

## 1. Component Tree & Responsibilities

```
ChatPage (app/chat/page.tsx)
│   Responsibility: State management, API calls, routing to views
│
├── ChatHeader
│   Responsibility: Display branding, back navigation
│
├── InsurerSelector
│   Responsibility: Multiselect (2~8), presets (2/4/8), validation
│   State: selectedInsurers: string[]
│
├── FilterPanel (collapsible)
│   Responsibility: Sort/type/age/gender inputs, validation
│   State: filters: { sort_by, product_type, age, gender }
│
├── QueryInput
│   Responsibility: Text input, submit button, validation hints
│   State: query: string, loading: boolean
│
└── ResultRenderer
    │   Responsibility: Route to Q1/Q2/Q3/Q4 views based on result.kind
    │
    ├── Q1PremiumView
    │   Responsibility: Render Top 4 premium table
    │
    ├── Q2LimitDiffView
    │   Responsibility: Render limit difference comparison table
    │
    ├── Q3ThreePartView
    │   Responsibility: Render 3-part report (table + summary + recommendation)
    │
    └── Q4MatrixView
        Responsibility: Render support matrix (O/X/—)
```

---

## 2. ViewModel Schemas (TypeScript)

```typescript
// Q1: Premium Ranking
interface Q1ViewModel {
  top4: Array<{
    rank: number;
    insurer_code: string;
    insurer_name: string;
    premium_monthly: number;
    premium_total: number;
    product_name?: string;
  }>;
  error?: string;
  note?: string; // "Premium data not yet implemented"
}

// Q2: Limit Difference Comparison
interface Q2ViewModel {
  coverage_code: string;
  canonical_name: string;
  insurer_rows: Array<{
    ins_cd: string;
    product_name?: string;
    slots: {
      duration_limit_days?: { value: number | null; status: string; evidences: any[] };
      daily_benefit_amount_won?: { value: number | null; status: string; evidences: any[] };
      [key: string]: any;
    };
  }>;
  error?: string;
  suggestions?: string[]; // Coverage code suggestions if not found
}

// Q3: Three-Part Comparison
interface Q3ViewModel {
  coverage_code: string;
  canonical_name: string;
  insurer_rows: Array<{
    ins_cd: string;
    product_name?: string;
    slots: Record<string, any>;
  }>;
  overall_assessment: string[] | null; // LLM-generated bullet points
  recommendation: {
    winner: string | null; // ins_cd or "TIE" or "UNKNOWN"
    reasons: string[];
  } | null;
  missing_info?: string[]; // LLM identified missing data
  error?: string;
}

// Q4: Support Matrix
interface Q4ViewModel {
  query_id: string;
  matrix: Array<{
    insurer_key: string;
    in_situ: {
      status_icon: '✅' | '❌' | '—' | '⚠️';
      display: string;
      color: 'green' | 'red' | 'gray' | 'orange';
      coverage_kind?: 'diagnosis_benefit' | 'treatment_trigger' | 'definition_only' | 'excluded';
      evidence_refs?: any[];
    };
    borderline: {
      status_icon: '✅' | '❌' | '—' | '⚠️';
      display: string;
      color: 'green' | 'red' | 'gray' | 'orange';
      coverage_kind?: 'diagnosis_benefit' | 'treatment_trigger' | 'definition_only' | 'excluded';
      evidence_refs?: any[];
    };
  }>;
  error?: string;
}

// Unified Response
interface ChatQueryResponse {
  kind: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'UNKNOWN';
  viewModel: Q1ViewModel | Q2ViewModel | Q3ViewModel | Q4ViewModel;
  error?: string;
}
```

---

## 3. /api/chat_query Contract

### Request
```typescript
POST /api/chat_query
Content-Type: application/json

{
  query_text: string;      // Required, min 3 chars
  ins_cds: string[];       // Required, 2~8 items
  filters: {
    sort_by: 'total' | 'monthly';           // Default: 'total'
    product_type: 'all' | 'standard' | 'no_refund'; // Default: 'all'
    age: number;                            // Default: 40, range: 20~80
    gender: 'M' | 'F';                      // Default: 'M'
  };
}
```

### Response (Success)
```typescript
200 OK
Content-Type: application/json

{
  kind: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'UNKNOWN';
  viewModel: Q1ViewModel | Q2ViewModel | Q3ViewModel | Q4ViewModel;
}
```

### Response (Error)
```typescript
400 Bad Request
{
  error: string; // "query_text required" | "ins_cds must have 2~8 items"
}

500 Internal Server Error
{
  kind: 'UNKNOWN';
  viewModel: {
    error: string; // User-friendly Korean message
    suggestions?: string[]; // Fallback suggestions
  };
}
```

### Validation Rules
1. `query_text`: Required, min 3 chars, max 500 chars
2. `ins_cds`: Required, array length 2~8, each item must match /^N\d{2}$/
3. `filters.age`: Optional, if provided must be 20~80
4. `filters.sort_by`: Optional, if provided must be 'total' | 'monthly'
5. `filters.product_type`: Optional, if provided must be 'all' | 'standard' | 'no_refund'
6. `filters.gender`: Optional, if provided must be 'M' | 'F'

---

## 4. Client-Side Query Classification Rules

### Classification Logic (Deterministic)
```typescript
function classifyQuery(query: string): 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'UNKNOWN' {
  const q = query.toLowerCase();

  // Q1: Premium ranking
  if (q.includes('보험료') && (q.includes('저렴') || q.includes('정렬') || q.includes('top') || q.includes('순'))) {
    return 'Q1';
  }

  // Q2: Limit difference
  if ((q.includes('보장한도') || q.includes('한도')) && (q.includes('다른') || q.includes('차이'))) {
    return 'Q2';
  }

  // Q3: 3-part comparison
  if ((q.includes('비교') || q.includes('종합')) && (q.includes('진단') || q.includes('암'))) {
    return 'Q3';
  }

  // Q4: Support matrix
  if (q.includes('제자리암') || q.includes('경계성종양') || (q.includes('지원') && q.includes('여부'))) {
    return 'Q4';
  }

  return 'UNKNOWN';
}
```

### Classification Examples
```typescript
// Q1
"가장 저렴한 보험료 순서대로 4개만 비교"
→ kind: 'Q1', reason: '보험료 + 저렴'

// Q2
"암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
→ kind: 'Q2', reason: '보장한도 + 다른'

// Q3
"삼성 메리츠 암진단비 비교"
→ kind: 'Q3', reason: '비교 + 진단'

// Q4
"제자리암과 경계성종양 지원 여부 비교"
→ kind: 'Q4', reason: '제자리암 + 경계성종양'
```

---

## 5. Insurer Selection Rules

### Constraints
- **Minimum**: 2 insurers must be selected
- **Maximum**: 8 insurers can be selected
- **Validation**: Prevent submit if < 2 selected
- **UI Feedback**: Display count "({selectedInsurers.length}개 선택)"

### Presets
```typescript
const PRESETS = [
  { id: '2-insurer', label: '2개', codes: ['N01', 'N08'] },
  { id: '4-insurer', label: '4개', codes: ['N01', 'N02', 'N08', 'N10'] },
  { id: '8-insurer', label: '8개 (전체)', codes: ['N01', 'N02', 'N03', 'N05', 'N08', 'N09', 'N10', 'N13'] },
];
```

### Default Selection
- **On page load**: Fetch available insurers from `/coverage_status?coverage_code=A4200_1&as_of_date=2025-11-26`
- **Fallback**: If API fails, use all 8 insurers from preset
- **Initial state**: Select all available insurers (default to 8)

### Available Insurers (Reference)
```typescript
const INSURER_NAMES: Record<string, string> = {
  'N01': 'DB손해보험',
  'N02': '롯데손해보험',
  'N03': '메리츠화재',
  'N05': '삼성화재',
  'N08': '현대해상',
  'N09': '흥국화재',
  'N10': 'KB손해보험',
  'N13': '한화손해보험',
};
```

---

## 6. Filter Rules (Q1 Focus)

### Filter Fields
```typescript
interface Filters {
  sort_by: 'total' | 'monthly';                    // 정렬 기준
  product_type: 'all' | 'standard' | 'no_refund'; // 보험 종류
  age: number;                                     // 연령 (20~80)
  gender: 'M' | 'F';                               // 성별
}
```

### Defaults (If Missing)
- `sort_by`: 'total' (총납입보험료)
- `product_type`: 'all' (전체)
- `age`: 40
- `gender`: 'M'

### Validation
- `age`: Must be integer in range [20, 80], otherwise use default 40
- `sort_by`: Must be 'total' or 'monthly', otherwise use 'total'
- `product_type`: Must be 'all' | 'standard' | 'no_refund', otherwise use 'all'
- `gender`: Must be 'M' or 'F', otherwise use 'M'

### Filter Panel Behavior
- **Initial State**: Collapsed (hidden)
- **Toggle**: User can expand/collapse via button
- **Persistence**: Filters persist across queries (not reset on submit)

### Q1-Specific Usage
- Filters are **only used for Q1** (Premium ranking)
- Q2/Q3/Q4 ignore filters (backend does not require them)
- Frontend always sends filters, backend decides whether to use them

---

## 7. Rendering Rules (Fixed Order)

### Q2 Rendering (Limit Difference)
**Order (Fixed)**:
1. **Header Block**: Coverage name + code (blue background)
2. **Comparison Table**: Rank | 보험사 | 상품명 | 보장한도 | 일일보장금액
3. **Note Block**: 안내문구 (gray background, 약관 기반)

**Required Fields**:
- `coverage_code`, `canonical_name`, `insurer_rows`
- Each row: `ins_cd`, `slots.duration_limit_days.value`, `slots.daily_benefit_amount_won.value`
- Missing values: Display "—"

**No Reordering**: Table rows follow API order (do NOT client-side sort)

---

### Q3 Rendering (Three-Part)
**Order (Fixed)**:
1. **Header Block**: Coverage name + code
2. **Part 1 - Comparison Table**: 보험사 | 상품명 | 보장금액
3. **Part 2 - Overall Assessment**: (Only if `overall_assessment` exists)
   - Title: "2. 종합 판단"
   - Bullet list of LLM-generated points
   - If missing: Show yellow warning "LLM 요약 준비 중"
4. **Part 3 - Recommendation**: (Only if `recommendation` exists)
   - Title: "3. 최종 추천"
   - Winner badge + reasons as bullet list
   - If missing: Show yellow warning "추천 정보 준비 중"
5. **Note Block**: 안내문구

**Conditional Blocks**:
- If `overall_assessment` is null: Skip Part 2 or show placeholder
- If `recommendation` is null: Skip Part 3 or show placeholder
- Table (Part 1) is **always required**

---

### Q4 Rendering (Support Matrix)
**Order (Fixed)**:
1. **Header Block**: Title "제자리암/경계성종양 보장 여부 매트릭스" + legend
2. **Matrix Table**: 보험사 (row) × 제자리암/경계성종양 (col)
   - Cell: O/X/— icon + color badge
   - If `coverage_kind === 'treatment_trigger'`: Add warning text "진단비 아님"
3. **Legend Block**: Icon meanings (O/X/—/⚠️)
4. **Note Block**: 안내문구

**Required Fields**:
- `matrix`: Array of insurers with `in_situ` and `borderline` cells
- Each cell: `status_icon`, `color`, `display`

**Icon Mapping**:
- `✅` → "O"
- `❌` → "X"
- `—` → "—"
- `⚠️` → "⚠️"

---

## 8. Non-Goals

### Do NOT Implement
1. ❌ Premium data source (Q1 backend connection)
2. ❌ Reuse demo-q12 components (Q12ReportView, etc.)
3. ❌ Touch legacy UI routes (/q11, /q13, /demo-q12)
4. ❌ LLM generation in frontend (only render pre-generated LLM output)
5. ❌ PDF re-parsing or gate relaxation
6. ❌ Coverage code auto-completion UI (use simple fuzzy matching)
7. ❌ Insurer logo images
8. ❌ Export/download features
9. ❌ URL state persistence (query params)
10. ❌ Multi-language support

### Out of Scope (Future)
- Q1 premium data integration (requires Premium SSOT)
- LLM real-time generation (requires backend LLM service)
- Advanced coverage code search (requires NLP)

---

## 9. DoD (Definition of Done)

### Checklist
- [ ] `/chat` route renders without errors
- [ ] Insurer selector: 2~8 validation works
- [ ] Filter panel: Collapse/expand works
- [ ] Query input: Submit disabled when invalid
- [ ] Q2 query: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘" → Shows table
- [ ] Q3 query: "삼성 메리츠 암진단비 비교" → Shows 3-part (or table + warning)
- [ ] Q4 query: "제자리암 경계성종양 지원 여부" → Shows O/X/— matrix
- [ ] Q1 query: "보험료 저렴한 순" → Shows "준비 중" placeholder
- [ ] UNKNOWN query: "이것저것" → Shows error + suggestions
- [ ] All views: "—" displays for missing data (not blank or error)
- [ ] No console errors (strict mode)
- [ ] No legacy component imports (Q12ReportView, etc.)
- [ ] Git clean (no uncommitted files)
- [ ] Documentation: This spec file committed

---

## 10. Manual Test Script

### Setup
```bash
# 1. Ensure servers running
cd /Users/cheollee/inca-rag-scope
python3 -m uvicorn apps.api.server:app --host 0.0.0.0 --port 8000 &
cd apps/web && npm run dev &

# 2. Wait for startup
sleep 5
```

### Browser Tests
```
1. Open: http://localhost:3000/chat

2. Test Insurer Selection:
   - Click "2개" preset → Should select 2 insurers
   - Uncheck all but 1 → Submit button should be disabled
   - Select 2+ → Submit button enabled

3. Test Filter Panel:
   - Click "필터 옵션 보기" → Panel expands
   - Change age to 30 → Value persists after submit
   - Click "필터 옵션 숨기기" → Panel collapses

4. Test Q2 Query:
   - Input: "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘"
   - Submit
   - Expected: Blue header + table with 보장한도/일일보장금액 columns
   - Badge: "보장한도 차이 비교"

5. Test Q3 Query:
   - Input: "삼성 메리츠 암진단비 비교"
   - Submit
   - Expected: Table + (종합판단 or warning) + (추천 or warning)
   - Badge: "3파트 비교"

6. Test Q4 Query:
   - Input: "제자리암 경계성종양 지원 여부"
   - Submit
   - Expected: Matrix with O/X/— icons
   - Badge: "지원여부 매트릭스"

7. Test Q1 Query:
   - Input: "보험료 저렴한 순서대로"
   - Submit
   - Expected: Yellow placeholder "보험료 비교는 준비 중입니다"
   - Badge: "보험료 비교"

8. Test UNKNOWN Query:
   - Input: "이것저것 알려줘"
   - Submit
   - Expected: Red error box + suggestions list
   - Badge: "알 수 없는 질문"

9. Test Missing Data:
   - Q2 result with null values → Should display "—" (not blank)
   - Q3 without LLM parts → Should show yellow warning blocks
```

### API Tests (curl)
```bash
# Test Q2
curl -X POST http://localhost:3000/api/chat_query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "암직접입원비 담보 중 보장한도가 다른 상품 찾아줘",
    "ins_cds": ["N01", "N03", "N08", "N10"],
    "filters": {"sort_by": "total", "product_type": "all", "age": 40, "gender": "M"}
  }' | jq '.kind'

# Expected: "Q2"

# Test Q4
curl -X POST http://localhost:3000/api/chat_query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "제자리암 경계성종양 지원 여부",
    "ins_cds": ["N01", "N03", "N05", "N08"],
    "filters": {"sort_by": "total", "product_type": "all", "age": 40, "gender": "M"}
  }' | jq '.kind'

# Expected: "Q4"

# Test Validation (should fail)
curl -X POST http://localhost:3000/api/chat_query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "암진단비",
    "ins_cds": ["N01"],
    "filters": {}
  }' | jq '.error'

# Expected: "ins_cds must have 2~8 items" (400 error)
```

---

## Revision History
- v1.0 (2026-01-16): Initial spec
