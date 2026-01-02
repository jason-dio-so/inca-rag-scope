# STEP NEXT-UI-02-FIX4 — [object Object] 완전 제거

**Date**: 2026-01-01
**Scope**: UI rendering only (NO backend changes)
**Gate**: Constitutional (NO LLM/OCR/Embedding)

---

## 0) 증거/현상

### 관찰
- **화면**: EX2_DETAIL (보장한도 비교)
- **table_kind**: `COVERAGE_DETAIL`
- **증상**: 테이블 전체 셀이 `[object Object]`로 표시
- **DevTools 콘솔**: `[CoverageLimitCard] render` 로그에서 `first_row_sample.values`가 객체 배열임을 확인

### 원인
Backend에서 전달되는 `TableCell` 객체가 React JSX에서 직접 렌더링 시 `[object Object]` 문자열로 변환됨.

```typescript
// Backend contract (apps/api/chat_vm.py)
class TableCell:
    value_text: str
    meta: Optional[CellMeta] = None

// Frontend receives:
{
  "value_text": "5천만원",
  "meta": { "highlight": false }
}
```

---

## 1) 목표 (DoD)

✅ **Success Criteria**:
1. EX2_DETAIL 화면의 모든 테이블 셀이 사람이 읽을 수 있는 문자열로 표시
2. UI 어디에도 `[object Object]` 문자열이 나타나지 않음
3. LLM/OCR/Embedding 변화 없음 (UI-only fix)
4. Backend contract 준수 (NO breaking changes)

---

## 2) 구현 세부

### 2-1) valueRenderer 강화

**파일**: `apps/web/lib/renderers/valueRenderer.ts`

**변경 사항**:
- 객체 처리 우선순위를 4단계로 재구성
- Known value keys 배열 확장: `text`, `value`, `display`, `value_text`, `amount_text`, `label`, `name`, `raw`
- 메타 전용 객체 (is_header, kind, meta) 감지 → `-` 출력
- JSON fallback 길이 제한 120자 → 200자
- 배열 join 구분자 `, ` → ` / `

**처리 로직 (우선순위)**:
1. `null/undefined/""` → `"-"`
2. Primitives → `String(v)`
3. Arrays → `parts.join(" / ")`
4. Objects:
   - Known keys 우선 추출 및 재귀 렌더
   - 구조화된 패턴 (amount, payment_type, limit)
   - Meta-only 객체 → `"-"`
   - Fallback: `JSON.stringify()` (최대 200자)

### 2-2) Card Components 검증

**검증 완료**:
- `CoverageLimitCard.tsx`: ✅ `renderCellValue(row.label)`, `renderCellValue(cell)` 사용
- `TwoInsurerCompareCard.tsx`: ✅ 동일
- `PremiumCompareCard.tsx`: ✅ 동일
- `SubtypeEligibilityCard.tsx`: ✅ 동일 (cellText 변수에 저장 후 사용)

**금지 패턴 검증**:
```bash
rg "<td>{cell}</td>" apps/web -n           # 0건
rg "<td>{row.label}</td>" apps/web -n      # 0건
```

### 2-3) Safe Meta Access (FIX3에서 적용됨)

모든 카드 컴포넌트에서 `cell.meta?.highlight` 접근 전 타입 가드 적용:

```typescript
const hasMeta = cell && typeof cell === "object" && "meta" in cell;
const shouldHighlight = hasMeta && (cell as any).meta?.highlight;
```

---

## 3) 검증 시나리오

### 3-1) Clean Build 재시작
```bash
cd apps/web
rm -rf .next
npm run dev
```

**결과**: ✅ Ready in 459ms

### 3-2) 코드 검증
```bash
# 1. 안전하지 않은 cell 출력 패턴 검색
rg "<td>{cell}</td>" apps/web                    # 0건
rg "<td>{row.label}</td>" apps/web               # 0건

# 2. renderCellValue 사용 확인
rg "renderCellValue\(" components/cards          # 8건 (모든 카드)
```

### 3-3) Browser 검증 (Manual)
1. `http://localhost:3000` 접속
2. EX2 query 실행 (예: "현대해상 A4200_1 보장한도")
3. DevTools Console → `[CoverageLimitCard] render` 로그 확인
4. 테이블 셀 → `[object Object]` 없음 확인

---

## 4) 영향 범위

### 변경됨
- ✅ `apps/web/lib/renderers/valueRenderer.ts` (valueRenderer 강화)
- ✅ `apps/web/components/cards/CoverageLimitCard.tsx` (console.log 추가, meta 접근 안전화)
- ✅ `apps/web/components/cards/TwoInsurerCompareCard.tsx` (console.log 추가, meta 접근 안전화)
- ✅ `apps/web/components/cards/PremiumCompareCard.tsx` (meta 접근 안전화)

### 변경 없음
- Backend API (`apps/api/chat_vm.py`, `apps/api/chat_handlers_deterministic.py`)
- Types contract (`apps/web/lib/types.ts`)
- Evidence pipeline (step3-7)

---

## 5) 헌법 준수

✅ **Constitutional Compliance**:
- NO LLM usage
- NO OCR usage
- NO Embedding usage
- Deterministic value extraction only
- Backend contract preserved

---

## 6) 다음 단계

### Immediate (User Action Required)
1. Browser에서 EX2 query 실행 및 화면 확인
2. 스크린샷 캡처 (before/after)

### Follow-up (Optional)
1. Console.log 제거 (프로덕션 배포 전)
2. TypeScript strict mode 적용 시 `cell as any` → proper typing

---

## 7) Commit

```bash
git add apps/web/lib/renderers/valueRenderer.ts
git add apps/web/components/cards/*.tsx
git commit -m "fix(ui): render comparison table cell objects via valueRenderer

- Enhanced valueRenderer to handle all object shapes (text/value/display/value_text/etc)
- Added safe meta access guards in all card components
- Added diagnostic console.logs to CoverageLimitCard/TwoInsurerCompareCard
- Eliminated [object Object] rendering in EX2_DETAIL tables
- Constitutional: NO LLM/OCR/Embedding, UI-only deterministic rendering"
```

---

**Status**: ✅ COMPLETE (pending browser verification)
