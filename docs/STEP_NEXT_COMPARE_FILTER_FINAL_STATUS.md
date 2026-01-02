# STEP NEXT-COMPARE-FILTER-FINAL: Implementation Status

## ✅ Completed (Backend)

### 1. Coverage Diff Result Section Type
**File**: `apps/api/chat_vm.py`

Added new section type:
```python
class CoverageDiffResultSection(BaseModel):
    kind: Literal["coverage_diff_result"] = "coverage_diff_result"
    title: str
    field_label: str
    status: Literal["DIFF", "ALL_SAME"]
    groups: List[DiffGroup]
    diff_summary: Optional[str] = None
```

### 2. Example2DiffHandler Updated
**File**: `apps/api/chat_handlers_deterministic.py`

Now returns `CoverageDiffResultSection` instead of `InsurerExplanationsSection`:

**Response Structure**:
```json
{
  "kind": "EX2_DETAIL_DIFF",
  "title": "A4200_1 보장한도 차이 분석",
  "summary_bullets": ["db가 다릅니다 (최초1회)"],
  "sections": [{
    "kind": "coverage_diff_result",
    "title": "보장한도 비교 결과",
    "field_label": "보장한도",
    "status": "DIFF",
    "groups": [
      {"value_display": "최초1회", "insurers": ["db"]},
      {"value_display": "명시 없음", "insurers": ["samsung", "meritz", "hanwha"]}
    ],
    "diff_summary": "db가 다릅니다 (최초1회)"
  }]
}
```

### 3. Test Results
```
✅ Handler executed successfully
✅ Title: "A4200_1 보장한도 차이 분석"
✅ Summary: "db가 다릅니다 (최초1회)"
✅ Sections: 1 (CoverageDiffResultSection)
✅ ALL_SAME scenario working
```

---

## 🔧 TODO (Frontend - Required for End-to-End)

### 1. Add compare_field Extraction Logic
**File**: `apps/api/chat_intent.py` (QueryCompiler)

Add field detection from query text:

```python
@staticmethod
def extract_compare_field(message: str) -> str:
    """Extract compare field from query text"""
    field_patterns = {
        "보장한도": [r"보장한도", r"한도", r"입원한도"],
        "지급유형": [r"지급유형", r"지급방식", r"지급조건"],
        "보장금액": [r"보장금액", r"가입금액", r"금액"],
        "조건": [r"조건", r"면책", r"감액"]
    }

    for field, patterns in field_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message):
                return field

    return "보장한도"  # Default
```

Then in `QueryCompiler.compile()`:
```python
if kind == "EX2_DETAIL_DIFF":
    if not request.compare_field:
        # Auto-detect from message
        query["compare_field"] = QueryCompiler.extract_compare_field(request.message)
    else:
        query["compare_field"] = request.compare_field
```

### 2. Implement CoverageDiffCard UI Component
**File**: `apps/web/components/CoverageDiffCard.tsx` (NEW)

```typescript
import React from 'react';

interface DiffGroup {
  value_display: string;
  insurers: string[];
}

interface CoverageDiffResultSection {
  kind: 'coverage_diff_result';
  title: string;
  field_label: string;
  status: 'DIFF' | 'ALL_SAME';
  groups: DiffGroup[];
  diff_summary?: string;
}

export function CoverageDiffCard({ section }: { section: CoverageDiffResultSection }) {
  if (section.status === 'ALL_SAME') {
    return (
      <div className="diff-card all-same">
        <h3>{section.title}</h3>
        <p>선택한 보험사의 {section.field_label}는 모두 동일합니다</p>
        {section.groups[0] && (
          <div className="common-value">
            공통 값: <strong>{section.groups[0].value_display}</strong>
          </div>
        )}
      </div>
    );
  }

  // DIFF mode
  return (
    <div className="diff-card diff-mode">
      <h3>{section.title}</h3>
      {section.diff_summary && (
        <div className="diff-summary">
          <strong>{section.diff_summary}</strong>
        </div>
      )}
      <div className="diff-groups">
        {section.groups.map((group, idx) => (
          <div key={idx} className="diff-group">
            <div className="value-label">{group.value_display}</div>
            <div className="insurers-list">
              {group.insurers.map((insurer, i) => (
                <span key={i} className="insurer-badge">
                  {insurer}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3. Update ResultDock to Route coverage_diff_result
**File**: `apps/web/components/ResultDock.tsx`

Add to section router:
```typescript
switch (section.kind) {
  case "coverage_diff_result":
    return <CoverageDiffCard key={idx} section={section} />;
  // ... existing cases
}
```

### 4. Add TypeScript Types
**File**: `apps/web/lib/types.ts`

```typescript
export interface DiffGroup {
  value_display: string;
  insurers: string[];
}

export interface CoverageDiffResultSection {
  kind: "coverage_diff_result";
  title: string;
  field_label: string;
  status: "DIFF" | "ALL_SAME";
  groups: DiffGroup[];
  diff_summary?: string;
}

// Add to Section union
export type Section =
  | ComparisonTableSection
  | InsurerExplanationsSection
  | CommonNotesSection
  | EvidenceAccordionSection
  | CoverageDiffResultSection;
```

---

## 🎯 DoD (Definition of Done)

| Requirement | Status |
|------------|--------|
| ❌ LLM usage | ✅ NO LLM (deterministic) |
| ❌ New data extraction | ✅ Uses existing coverage_cards |
| ❌ Step1-5 re-execution | ✅ Only reads SSOT |
| Backend: CoverageDiffResultSection | ✅ DONE |
| Backend: Example2DiffHandler | ✅ DONE |
| Backend: compare_field auto-detect | ⏳ TODO |
| Frontend: CoverageDiffCard component | ⏳ TODO |
| Frontend: ResultDock routing | ⏳ TODO |
| Frontend: TypeScript types | ⏳ TODO |
| End-to-end: "다른 상품 찾아줘" works | ⏳ TODO |

---

## 📋 Quick Start for Frontend Dev

1. **Add compare_field extraction** (5 min):
   - Edit `apps/api/chat_intent.py`
   - Add `extract_compare_field()` method
   - Call it in `QueryCompiler.compile()`

2. **Create CoverageDiffCard** (15 min):
   - Create `apps/web/components/CoverageDiffCard.tsx`
   - Copy template from above
   - Add CSS for diff-card, diff-groups, insurer-badge

3. **Update ResultDock** (2 min):
   - Add `case "coverage_diff_result"` to switch
   - Import CoverageDiffCard

4. **Add types** (2 min):
   - Edit `apps/web/lib/types.ts`
   - Add DiffGroup, CoverageDiffResultSection

5. **Test**:
   - Query: "암직접입원비 보장한도가 다른 상품 찾아줘"
   - Expected: CoverageDiffCard renders with groups
   - Expected: "db가 다릅니다 (최초1회)" shows prominently

---

## 🔍 Backend API Example

**Request**:
```json
{
  "message": "암직접입원비 보장한도가 다른 상품 찾아줘",
  "kind": "EX2_DETAIL_DIFF",
  "coverage_names": ["A4200_1"],
  "insurers": ["samsung", "meritz", "db", "hanwha"],
  "compare_field": "보장한도",
  "llm_mode": "OFF"
}
```

**Response** (actual test output):
```json
{
  "request_id": "...",
  "kind": "EX2_DETAIL_DIFF",
  "title": "A4200_1 보장한도 차이 분석",
  "summary_bullets": ["db가 다릅니다 (최초1회)"],
  "sections": [{
    "kind": "coverage_diff_result",
    "title": "보장한도 비교 결과",
    "field_label": "보장한도",
    "status": "DIFF",
    "groups": [
      {"value_display": "최초1회", "insurers": ["db"]},
      {"value_display": "명시 없음", "insurers": ["samsung", "meritz", "hanwha"]}
    ],
    "diff_summary": "db가 다릅니다 (최초1회)"
  }]
}
```

---

## 📦 Files Modified

**Backend**:
- ✅ `apps/api/chat_vm.py` - Added CoverageDiffResultSection
- ✅ `apps/api/chat_handlers_deterministic.py` - Updated Example2DiffHandler
- ✅ `pipeline/step8_render_deterministic/diff_filter.py` - Created
- ✅ `tests/test_diff_filter.py` - Created

**Frontend** (TODO):
- ⏳ `apps/api/chat_intent.py` - Add compare_field extraction
- ⏳ `apps/web/components/CoverageDiffCard.tsx` - Create
- ⏳ `apps/web/components/ResultDock.tsx` - Add routing
- ⏳ `apps/web/lib/types.ts` - Add types

---

## 🎯 Next Steps

1. **Immediate** (Backend polish):
   - Add compare_field auto-detection from query text
   - Test with various queries

2. **Frontend** (30 min total):
   - Implement CoverageDiffCard component
   - Wire up routing in ResultDock
   - Add TypeScript types

3. **E2E Test**:
   - Query: "암직접입원비 보장한도가 다른 상품 찾아줘"
   - Verify: UI shows diff groups correctly
   - Verify: "db가 다릅니다" message prominent

4. **Optional Enhancements**:
   - Add field selector dropdown in UI (보장한도 / 지급유형 / 조건)
   - Color-code majority vs minority groups
   - Add tooltips for value explanations

---

**Status**: Backend complete ✅ | Frontend implementation ready to start ⏳
