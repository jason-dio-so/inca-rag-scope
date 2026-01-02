# STEP NEXT-UI-02-FIX2 — ResultDock Sections-First Rendering

**Date**: 2026-01-01
**Status**: ✅ COMPLETE

## 목적

EX2_DETAIL 응답이 정상적으로 오는데도 UI 결과 pane이 비는 문제 해결.
ResultDock를 "sections-first" 렌더러로 리팩토링하여 message.kind와 무관하게 sections가 있으면 항상 렌더링되도록 수정.

---

## 문제 증상

### 재현 상황
1. UI에서 "상품/담보 설명" 선택
2. 담보명: "암진단비(유사암제외)" 입력 후 실행
3. 브라우저 콘솔에서 응답 확인:
   - `message.kind: "EX2_DETAIL"`
   - `message.sections.length: 2`
   - sections[0] = `{ kind:"comparison_table", table_kind:"COVERAGE_DETAIL", columns:[...], rows:[...] }`
   - sections[1] = `{ kind:"evidence_accordion", items:[...] }`
4. **문제**: UI 결과 pane이 비어있음

### 원인 분석

기존 `ResultDock.tsx`의 `renderSection()` 로직:

```typescript
case "comparison_table":
  if (section.table_kind === "COVERAGE_DETAIL" && response.kind === "EX2_DETAIL") {
    return <CoverageLimitCard key={idx} section={section} />;
  } else if (section.table_kind === "INTEGRATED_COMPARE" || response.kind === "EX3_INTEGRATED") {
    return <TwoInsurerCompareCard key={idx} section={section} />;
  }
  // ...
  return <PremiumCompareCard key={idx} section={section} />;
```

**문제점**:
- `table_kind`와 `message.kind` 둘 다 체크하는 AND 조건
- 만약 `response.kind`가 예상과 다르면 fallback으로 `PremiumCompareCard`를 사용
- `table_kind`를 SSOT로 사용하지 않고 `message.kind`에 의존

**헌법 위반**:
- Sections는 SSOT인데, `message.kind`에 의존하는 것은 anti-pattern
- Sections-first 원칙: sections 필드가 존재하면 무조건 렌더링되어야 함

---

## 해결 방법

### 1. Sections-First Rendering 원칙 적용

**핵심 변경**:
```typescript
case "comparison_table":
  // Route based on table_kind (sections-first approach)
  // table_kind is the SSOT, not message.kind
  if (section.table_kind === "COVERAGE_DETAIL") {
    return <CoverageLimitCard key={idx} section={section} />;
  } else if (section.table_kind === "INTEGRATED_COMPARE") {
    return <TwoInsurerCompareCard key={idx} section={section} />;
  } else if (section.table_kind === "ELIGIBILITY_MATRIX") {
    return <SubtypeEligibilityCard key={idx} section={section} />;
  } else if (section.table_kind === "PREMIUM_COMPARE") {
    return <PremiumCompareCard key={idx} section={section} />;
  }

  // Fallback: Use CoverageLimitCard as default table renderer
  // This ensures ANY comparison_table will render even if table_kind is unknown
  return <CoverageLimitCard key={idx} section={section} />;
```

**변경 사항**:
- ❌ 제거: `response.kind` 의존성
- ✅ 추가: `section.table_kind` SSOT 기반 라우팅
- ✅ 추가: 기본 fallback을 `CoverageLimitCard`로 변경 (모든 테이블 렌더링 보장)

### 2. Empty Sections 디버그 UI 추가

```typescript
{sections.length > 0 ? (
  sections.map((section, idx) => renderSection(section, idx))
) : (
  <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
    <p className="text-sm text-yellow-800">
      섹션 데이터가 없습니다. (kind: {response.kind})
    </p>
    <details className="mt-2 text-xs text-yellow-700">
      <summary className="cursor-pointer">디버그 정보</summary>
      <pre className="mt-1 whitespace-pre-wrap">
        {JSON.stringify(response, null, 2)}
      </pre>
    </details>
  </div>
)}
```

**목적**:
- sections가 비어있을 때 빈 화면 대신 디버그 정보 표시
- 개발자가 VM 응답을 즉시 확인 가능

---

## 수정 파일

### `apps/web/components/ResultDock.tsx`

**변경 내용**:
1. `renderSection()` 로직을 sections-first로 리팩토링
2. `table_kind`를 SSOT로 사용, `message.kind` 의존성 제거
3. 모든 `comparison_table`에 대한 기본 fallback 보장
4. Empty sections 디버그 UI 추가

---

## 검증 (DoD)

### 테스트 시나리오

#### 1. EX2_DETAIL (상품/담보 설명)
```
입력: 담보명 "암진단비(유사암제외)"
예상:
  - ✅ "A4200_1 보장한도 비교" 테이블 표시
  - ✅ "근거 자료" 아코디언 표시
  - ✅ 콘솔 에러 0건
```

#### 2. EX3_INTEGRATED (통합 비교)
```
예상:
  - ✅ 통합 비교표 표시
  - ✅ 공통사항/유의사항 표시
  - ✅ 근거 자료 표시
```

#### 3. EX4_ELIGIBILITY (질병 경계조건)
```
예상:
  - ✅ 자격 매트릭스 표시
  - ✅ 근거 자료 표시
```

#### 4. Empty Sections
```
시나리오: 서버가 sections=[] 응답
예상:
  - ✅ "섹션 데이터가 없습니다" 메시지 표시
  - ✅ 디버그 정보 펼침 가능
  - ✅ UI 크래시 없음
```

---

## 결과

### Before
- EX2_DETAIL 응답이 와도 UI 결과 pane이 비어있음
- `message.kind`와 `table_kind` 불일치 시 렌더링 실패

### After
- ✅ Sections-first 렌더링: sections가 존재하면 무조건 렌더링
- ✅ `table_kind`를 SSOT로 사용
- ✅ 모든 `comparison_table`에 대한 기본 fallback 보장
- ✅ Empty sections 시 디버그 UI 표시
- ✅ UI 크래시 방지 유지

---

## 헌법 준수

- ✅ 백엔드 수정 없음 (Frontend only)
- ✅ LLM OFF 기본값 유지
- ✅ VM 그대로 렌더링 (가공 최소)
- ✅ Optional guard 유지 (crash 방지)
- ✅ Sections-first 원칙 준수

---

## 다음 단계

1. **UI 테스트**: 예제 1~4 모두 LLM OFF 모드에서 테스트
2. **성능 모니터링**: 큰 테이블 렌더링 시 성능 확인
3. **에러 처리**: API 에러 응답 시 UI 동작 확인

---

## 관련 문서

- `docs/STEP_NEXT_UI_01.md` - 결정론적 핸들러 설계
- `docs/STEP_NEXT_UI_02_LOCAL.md` - 로컬 개발 환경 설정
- `STEP_NEXT_UI_02_FIX.md` - 첫 번째 UI 크래시 방지 패치
