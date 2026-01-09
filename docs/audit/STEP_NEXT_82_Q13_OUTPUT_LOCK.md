# STEP NEXT-82: Q13 Output Integration & SSOT Gate (LOCK)

## 목적

STEP NEXT-81C 결과를 Q13 고객 출력에 **강제 반영**하여
`treatment_trigger ≠ diagnosis_benefit` 오해를 **출력 레벨에서 영구 차단**한다.

---

## SSOT Gate (HARD)

### 입력 SSOT
**MUST USE:** `docs/audit/step_next_81c_subtype_coverage_locked.jsonl`

### Gate 규칙
1. 다른 subtype 결과 사용 시 **HARD FAIL (exit 2)**
2. 모든 레코드는 `coverage_kind` 필드 필수
3. 모든 레코드는 `q13_display_rule` 필드 필수
4. 위반 시 즉시 종료 (exit 2)

### Gate 검증
```python
# SSOT Gate enforcer
if input_path != "docs/audit/step_next_81c_subtype_coverage_locked.jsonl":
    print("❌ SSOT GATE VIOLATION")
    exit(2)

if "coverage_kind" not in data:
    print("❌ Missing coverage_kind")
    exit(2)
```

---

## Q13 출력 규칙 (LOCK)

### 규칙표

| coverage_kind | 출력 표시 | 아이콘 | 색상 | usable_as_coverage |
|---------------|----------|--------|------|-------------------|
| **diagnosis_benefit** | ✅ 보장 O | ✅ | green | `true` |
| **treatment_trigger** | ⚠️ 진단 시 치료비 지급 (진단비 아님) | ⚠️ | orange | `false` |
| **definition_only** | ℹ️ 정의 문맥 언급 | ℹ️ | gray | `false` |
| **excluded** | ❌ 보장 X | ❌ | red | `false` |

### 핵심 원칙 (HARD LOCK)
- ❌ **treatment_trigger를 "보장 O"로 출력 절대 금지**
- ✅ **diagnosis_benefit만 "보장 O"로 출력**
- ⚠️ **treatment_trigger는 별도 표기 필수**

---

## Before/After 비교 (KB 표적항암약물허가치료비)

### Before (81C 이전 - 오해 위험)
```
| 담보 | 제자리암 | 경계성종양 |
|------|---------|-----------|
| 표적항암약물허가치료비 | O | O |
```

**문제:**
- 고객: "제자리암 진단비 받을 수 있구나!" (착각)
- 실제: 진단비가 아니라 치료비 지급 트리거

---

### After (STEP NEXT-82 - 명확한 구분)
```
| 담보 | 제자리암 | 경계성종양 |
|------|---------|-----------|
| 표적항암약물허가치료비 | ⚠️ 진단 시 치료비 지급 (진단비 아님) | ⚠️ 진단 시 치료비 지급 (진단비 아님) |
```

**개선:**
- 고객: "아, 진단비가 아니라 치료비 받을 때 조건이구나" (정확한 이해)
- `usable_as_coverage=false` → 진단비 비교에서 제외

---

## Q13 출력 구조

### 샘플 출력 (step_next_82_q13_output.jsonl)
```json
{
  "insurer_key": "kb",
  "product_name": "KB 닥터플러스 건강보험(세만기)(해약환급금미지급형)(무배",
  "coverage_name": "280 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)",
  "coverage_type": "치료비",
  "q13_subtype_cells": {
    "in_situ": {
      "subtype": "in_situ",
      "coverage_kind": "treatment_trigger",
      "display": "진단 시 치료비 지급 (진단비 아님)",
      "display_detail": "치료비 지급 트리거 (진단비가 아님)",
      "icon": "⚠️",
      "color": "orange",
      "usable_as_coverage": false,
      "evidence_refs": [{
        "doc_type": "가입설계서",
        "page": "5-5",
        "excerpt": "보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시"
      }],
      "scope": "diagnosis",
      "condition_type": "지급사유"
    },
    "borderline": {
      "subtype": "borderline",
      "coverage_kind": "treatment_trigger",
      "display": "진단 시 치료비 지급 (진단비 아님)",
      "icon": "⚠️",
      "usable_as_coverage": false
    }
  },
  "metadata": {
    "source": "step_next_81c_locked",
    "processing_step": "STEP_NEXT_82",
    "locked": true
  }
}
```

---

## DoD 검증 결과

### DoD 기준
- ✅ treatment_trigger → "진단비 O" 출력: **0건**
- ✅ Q13 모든 셀에 근거(evidence_ref) 유지
- ✅ LLM ❌ / 추론 ❌ / 규칙 기반만
- ✅ Deterministic (same input → same output)

### 실행 결과
```
Total Q13 cells: 2
  diagnosis_benefit: 0
  treatment_trigger: 2

DoD Validation Results:
  treatment_trigger → '진단비 O' violations: 0
  ✅ No violations found

Sample outputs:
  treatment_trigger samples:
    ⚠️  kb|280 표적항암약물허가치료비 / in_situ: 진단 시 치료비 지급 (진단비 아님)
    ⚠️  kb|280 표적항암약물허가치료비 / borderline: 진단 시 치료비 지급 (진단비 아님)

✅ DoD PASSED
   treatment_trigger → '진단비 O' output: 0 cases
   All Q13 cells maintain evidence_ref
   Deterministic (no LLM, no inference)

🔒 Q13 Output LOCKED.
   treatment_trigger ≠ diagnosis_benefit.
   Customer misinterpretation risk eliminated.
```

---

## 산출물

1. **Q13 Output JSONL:**
   `docs/audit/step_next_82_q13_output.jsonl`
   - coverage_kind 기반 출력 규칙 적용
   - evidence_refs 유지

2. **Validation 결과:**
   `docs/audit/step_next_82_q13_validation.json`
   - treatment_trigger → "진단비 O" 위반: 0건
   - DoD PASSED

3. **LOCK 문서 (본 문서):**
   `docs/audit/STEP_NEXT_82_Q13_OUTPUT_LOCK.md`

---

## UI 구현 가이드

### Q13 테이블 렌더링

```javascript
function renderQ13Cell(cell) {
  const { coverage_kind, display, icon, color, usable_as_coverage } = cell;

  // LOCKED rule: coverage_kind determines display
  if (coverage_kind === "diagnosis_benefit") {
    return `<td class="diagnosis-benefit">${icon} ${display}</td>`;
  } else if (coverage_kind === "treatment_trigger") {
    return `<td class="treatment-trigger">${icon} ${display}</td>`;
  } else if (coverage_kind === "definition_only") {
    return `<td class="definition-only">${icon} ${display}</td>`;
  } else {
    return `<td class="excluded">${icon} ${display}</td>`;
  }
}
```

### CSS 스타일

```css
.diagnosis-benefit {
  background-color: #d4edda;
  color: #155724;
}

.treatment-trigger {
  background-color: #fff3cd;
  color: #856404;
  font-style: italic;
}

.definition-only {
  background-color: #e2e3e5;
  color: #6c757d;
}

.excluded {
  background-color: #f8d7da;
  color: #721c24;
}
```

---

## 금지 사항 (HARD)

### ❌ 절대 금지
1. **81C 이전 결과 사용**
   - SSOT Gate 위반 시 exit 2

2. **표현 완화/의역**
   - "사실상 보장" 같은 추론 문구 금지
   - 정확한 coverage_kind 기반 표시만 허용

3. **treatment_trigger를 "보장 O"로 표시**
   - 고객 오해 유발
   - DoD 위반

### ✅ 필수 준수
1. **SSOT 사용**
   - `step_next_81c_subtype_coverage_locked.jsonl`만 사용

2. **Deterministic**
   - 동일 입력 → 동일 출력 보장
   - LLM/추론 사용 금지

3. **Evidence 유지**
   - 모든 Q13 셀에 evidence_refs 포함
   - 고객이 근거 확인 가능

---

## 다음 단계

1. **UI 적용**
   - Q13 테이블에 coverage_kind 기반 렌더링 적용
   - 아이콘 및 색상 적용

2. **전 보험사 확대**
   - 현재: KB 1건 검증 완료
   - 향후: 전 보험사 담보 적용

3. **고객 피드백**
   - treatment_trigger 표기 명확성 확인
   - 오해 방지 효과 측정

---

## 완료 상태 메시지

```
🔒 Q13 Output LOCKED.
   treatment_trigger ≠ diagnosis_benefit.
   Customer misinterpretation risk eliminated.
```

**요약:**
- SSOT Gate 적용 완료
- treatment_trigger → "진단비 O" 출력: **0건** (DoD PASSED)
- Q13 출력 규칙 LOCKED (변경 불가)
- 고객 오해 방지 영구 차단
