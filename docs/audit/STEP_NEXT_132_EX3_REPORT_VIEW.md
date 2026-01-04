# STEP NEXT-132: EX3 Report View (EXAM3 Report View v0)

**Date**: 2026-01-04
**Status**: ✅ COMPLETE
**Commit**: `dcdd968`

---

## Purpose

Customer-requested "1-page report" view for EX3_COMPARE results only.

**Problem**:
- Customer wants printable/shareable comparison report
- Current view shows detailed sections (good for browsing, not for sharing)
- Customer needs clean, professional 1-page format

**Solution**:
- Add "보고서 보기" toggle in right panel
- Generate 1-page report from latest EX3_COMPARE message only
- EX3 SSOT (NO EX4/EX2 mixing)
- Deterministic composition (NO LLM)

---

## Constitutional Rules

1. ✅ **EX3 SSOT ONLY**: Report uses kind === "EX3_COMPARE" messages only
2. ❌ **NO LLM usage**: Deterministic extraction and fixed templates only
3. ❌ **NO recommendation/judgment**: "더 좋다", "추천", "유리" forbidden
4. ✅ **Structural explanations allowed**: "보장 정의 기준 차이" is factual
5. ✅ **Report wording**: Verifiable from data + fixed templates only
6. ✅ **Extensible**: Model supports 2+ insurers (column-array based)

---

## Implementation

### 1. Report Types

**File**: `apps/web/lib/report/ex3ReportTypes.ts`

```typescript
export interface EX3ReportDoc {
  title: string;          // "{coverage_display} 비교 요약"
  subtitle: string[];     // ["삼성화재 vs 메리츠화재", "가입설계서 기준 비교입니다"]
  summary_lines: string[]; // Max 3 lines (deterministic template + data)
  table: ComparisonTableSection; // Direct copy from EX3 comparison_table
  notes: string[];        // Direct copy from EX3 common_notes
}
```

### 2. Report Composer

**File**: `apps/web/lib/report/composeEx3Report.ts`

**Logic**:
1. Find latest EX3_COMPARE message (iterate backwards)
2. Extract comparison_table section (required)
3. Extract insurer names from table columns (skip first column)
4. Build title: `{coverage_name} 비교 요약`
5. Build subtitle:
   - Line 1: `{insurer1} vs {insurer2}` (from columns)
   - Line 2: Source note from common_notes (e.g., "가입설계서 기준")
6. Build summary_lines (max 3, omit missing):
   - Line 1: Fixed template `{A}와 {B}의 {coverage} 보장 정의 기준 차이를 정리했습니다.`
   - Line 2: "보장 정의 기준" row (if exists) → `{A}: {cellA} / {B}: {cellB}`
   - Line 3: "핵심 보장 내용" row (if exists) → `{A}: {cellA} / {B}: {cellB}`
7. Copy table and notes directly

**Rules**:
- NO creation (only extraction)
- NO LLM usage
- If no EX3_COMPARE → return null
- Deterministic row finding (by first cell text match)

### 3. Report View Component

**File**: `apps/web/components/report/EX3ReportView.tsx`

**Layout (1-page)**:
1. **Header**: Title + subtitle (dark border-bottom separator)
2. **Summary Box**: Blue background, 3 lines max
3. **Comparison Table**: Standard HTML table (print-friendly)
4. **Notes**: Yellow background, bullet list
5. **Footer**: Small disclaimer text

**Styling**:
- Print/capture-friendly (max-w-4xl, white background)
- Professional borders and spacing
- First column (category) has gray background
- Hover effect on table rows

**Empty State**:
If no EX3_COMPARE exists:
```
"보고서는 비교(EXAM3) 결과가 있을 때만 생성됩니다."
```

### 4. Toggle UI

**File**: `apps/web/app/page.tsx`

**Changes**:
1. Added imports:
   ```typescript
   import { EX3ReportView } from "@/components/report/EX3ReportView";
   import { composeEx3Report } from "@/lib/report/composeEx3Report";
   ```

2. Added state:
   ```typescript
   const [viewMode, setViewMode] = useState<"comparison" | "report">("comparison");
   ```

3. Modified right panel structure:
   ```tsx
   {latestResponse && messages.length > 0 && (
     <div className="w-1/2 border-l flex flex-col">
       {/* Toggle header */}
       <div className="border-b px-4 py-2 flex gap-2">
         <button onClick={() => setViewMode("comparison")}>비교 보기</button>
         <button onClick={() => setViewMode("report")}>보고서 보기</button>
       </div>

       {/* Content area */}
       <div className="flex-1 overflow-y-auto p-4">
         {viewMode === "comparison" ? (
           <ResultDock response={latestResponse} />
         ) : (
           <EX3ReportView report={composeEx3Report(
             messages.filter(m => m.role === "assistant").map(m => m.content)
           )} />
         )}
       </div>
     </div>
   )}
   ```

**Rules**:
- Report mode ALWAYS uses latest EX3 (ignores current screen/EX4)
- Toggle visible when any response exists (not just EX3)
- Empty state shown when clicking "보고서 보기" with no EX3

---

## Verification Scenarios

### Scenario 1: EX3 실행 후 "보고서 보기" 클릭
**Expected**:
- Title/subtitle/summary/table/notes 표시
- 1-page clean layout
- NO EX4 content mixing

### Scenario 2: EX4 화면을 본 뒤 "보고서 보기" 클릭
**Expected**:
- EX4 content NOT shown
- Latest EX3 report shown (ignores current EX4 screen)
- NO cross-contamination

### Scenario 3: EX3를 여러 번 수행 후 "보고서 보기"
**Expected**:
- Latest EX3 used (NOT first/oldest)
- Report updates with most recent comparison

### Scenario 4: EX3가 없는 상태에서 "보고서 보기"
**Expected**:
- Empty state message shown
- NO crash/error
- Clear guidance: "보고서는 비교(EXAM3) 결과가 있을 때만 생성됩니다"

---

## Contract Tests

**File**: `apps/web/lib/report/__tests__/composeEx3Report.test.ts`

**6 Tests** (per DoD requirement):

1. **No EX3 → returns null**
   - Input: EX2_DETAIL, EX4_ELIGIBILITY messages
   - Output: null

2. **Latest EX3 selected**
   - Input: EX3 (old) + EX4 + EX3 (new)
   - Output: Report from newest EX3 (NOT first)

3. **Summary lines composition (3 lines max)**
   - Input: EX3 with "보장 정의 기준" + "핵심 보장 내용" rows
   - Output: 3 lines (template + basis + content)

4. **Omit missing rows (no blank lines)**
   - Input: EX3 with only "보장 정의 기준" row (NO "핵심 보장 내용")
   - Output: 2 lines (template + basis), NO blank line

5. **Notes copied from common_notes**
   - Input: EX3 with common_notes section
   - Output: report.notes === EX3 bullets (direct copy)

6. **Insurer names from table columns**
   - Input: Columns = ["비교 항목", "KB손해보험", "한화손해보험"]
   - Output: subtitle = "KB손해보험 vs 한화손해보험"

**Test Status**: Written (frontend has no Jest setup, manual verification required)

---

## Forbidden Patterns

### ❌ FORBIDDEN (ABSOLUTE):

```typescript
// ❌ Mix EX4 content in report
if (message.kind === "EX4_ELIGIBILITY") {
  report.summary_lines.push("EX4 데이터");
}

// ❌ LLM-based composition
const summary = await callLLM("Summarize this comparison");

// ❌ Recommendation/judgment
summary_lines.push("메리츠화재가 더 좋습니다"); // FORBIDDEN

// ❌ Create notes (only copy)
notes.push("새로운 유의사항"); // FORBIDDEN
```

### ✅ ALLOWED:

```typescript
// ✅ EX3 SSOT only
if (message.kind === "EX3_COMPARE") {
  const table = message.sections.find(s => s.kind === "comparison_table");
}

// ✅ Deterministic extraction
const insurers = table.columns.slice(1); // Skip first column

// ✅ Fixed template
summary_lines.push(`${A}와 ${B}의 ${coverage} 보장 정의 기준 차이를 정리했습니다.`);

// ✅ Structural explanation
summary_lines.push("삼성화재: 지급 한도/횟수 기준 / 메리츠화재: 보장금액(정액) 기준");

// ✅ Direct copy
notes = commonNotesSection.bullets;
```

---

## Definition of Done

- [x] EX3ReportTypes defined (title, subtitle, summary_lines, table, notes)
- [x] composeEx3Report() implemented (deterministic, latest EX3 selection)
- [x] EX3ReportView component created (1-page layout, print-friendly)
- [x] Toggle UI added to right panel ("비교 보기" / "보고서 보기")
- [x] Report mode always uses latest EX3 (ignores current screen)
- [x] Empty state shown when no EX3 exists
- [x] 6 contract tests written
- [x] Git committed
- [ ] **Manual UI verification** (4 scenarios)

---

## Next Steps

**Manual Verification Required**:
1. Run EX3 comparison → Click "보고서 보기" → Verify 1-page report
2. Navigate to EX4 → Click "보고서 보기" → Verify EX3 report shown (NOT EX4)
3. Run multiple EX3 comparisons → Verify latest EX3 used
4. Start fresh (no EX3) → Click "보고서 보기" → Verify empty state message

**If any scenario fails**:
- Check browser console for errors
- Verify composeEx3Report() returns correct data
- Check EX3 message structure in conversation

---

## LOCKED

**Date**: 2026-01-04
**Branch**: `feat/step-next-132-ex3-report`
**Commit**: `dcdd968`

**Definition of Success**:
> "고객이 '보고서 보기'를 눌렀을 때 EX3 비교 결과가 1페이지로 깔끔하게 표시되고, 캡처/인쇄가 가능하며, EX4 화면과 섞이지 않으면 성공"

All code changes complete. Manual UI verification pending.
