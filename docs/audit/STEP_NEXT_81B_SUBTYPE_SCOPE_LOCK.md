# STEP NEXT-81B: Subtype Coverage Scope Refinement (LOCK)

## 변경 이유

STEP NEXT-81에서 `covered=true` 판정은 "문구에 subtype(제자리암/경계성종양)이 등장"을 기준으로 했으나,
그 문구가 **지급사유**인지 **정의/예시**인지 구분하지 않았음.

→ 고객이 "제자리암 O"를 보고 "보장된다"고 오해할 위험이 있음.
→ 실제로는 "유사암 정의에 제자리암이 포함된다"는 설명일 뿐, 해당 담보는 지급 대상이 아닐 수 있음.

**변경 목표:**
- `O` 정의를 **지급사유(diagnosis/treatment) 문맥에서 명시 포함**으로 좁힘
- `definition/example` scope는 보장 판단에 사용 금지

---

## O 정의 (Before → After)

### Before (STEP NEXT-81)
- `covered=true`: 문구에 subtype 등장 = O

### After (STEP NEXT-81B)
- `decision=O`: **지급사유(diagnosis/treatment) 문맥**에서 subtype 명시 포함
- `scope` 필드 추가:
  - `diagnosis`: 진단확정 시 지급
  - `treatment`: 치료/수술/약물허가치료 시 지급
  - `definition`: 유사암/정의/분류 설명 문맥 (보장 판단 금지)
  - `example`: 예시/참고 문맥 (보장 판단 금지)
  - `unknown`: 판정 불가 (보장 판단 금지)

---

## Scope 정의표

| Scope | 설명 | UI/비교 사용 | 키워드 예시 |
|-------|------|-------------|------------|
| **diagnosis** | 진단확정 시 지급사유 | ✅ 사용 가능 | "진단확정시", "진단받은 때", "진단 시 지급" |
| **treatment** | 치료/수술 시 지급사유 | ✅ 사용 가능 | "치료", "수술", "항암", "약물허가치료", "방사선" |
| **definition** | 정의/범위 설명 문맥 | ❌ 사용 금지 | "유사암", "정의", "분류", "해당하는", "기타피부암/갑상선암/제자리암/경계성종양" |
| **example** | 예시/참고 문맥 | ❌ 사용 금지 | "예를 들어", "예시", "참고", "예)", "다음과 같음" |
| **unknown** | 판정 불가 | ❌ 사용 금지 | - |

---

## LOCK 선언

**절대 규칙 (GATE-81B-2):**
- `scope in {definition, example, unknown}` 인 항목은
  - `usable_as_coverage=false` 필드를 반드시 포함
  - UI/추천/비교 화면에서 "보장 O"로 표시 금지
  - 표기: "정의/설명 문맥에서 언급" 또는 "예시로 언급"으로만 표시

---

## Before/After 예시 (KB 표적항암약물허가치료비)

### Before (STEP NEXT-81)
```json
{
  "coverage_name": "280 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)",
  "subtype_coverage": {
    "in_situ": {
      "covered": true,
      "confidence": "EXPLICIT_INCLUSION"
    },
    "borderline": {
      "covered": true,
      "confidence": "EXPLICIT_INCLUSION"
    }
  }
}
```

**문제점:**
- `covered=true`만 보면 "제자리암/경계성종양이 보장된다"고 오해 가능
- 실제 문구: "유사암진단비 ... 제자리암 또는 경계성종양으로 진단확정시"
  - 이것은 **다른 담보(유사암진단비)**의 지급사유
  - 표적항암약물허가치료비 자체의 지급사유가 아님

### After (STEP NEXT-81B)
```json
{
  "coverage_name": "280 표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)",
  "subtype_coverage_refined": {
    "in_situ": {
      "decision": "O",
      "scope": "diagnosis",
      "condition_type": "지급사유",
      "usable_as_coverage": true,
      "evidence_refs": [{
        "doc_type": "가입설계서",
        "page": "5-5",
        "excerpt": "보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시"
      }]
    },
    "borderline": {
      "decision": "O",
      "scope": "diagnosis",
      "condition_type": "지급사유",
      "usable_as_coverage": true,
      "evidence_refs": [{
        "doc_type": "가입설계서",
        "page": "5-5",
        "excerpt": "보험기간 중 기타피부암, 갑상선암, 제자리암 또는 경계성종양으로 진단확정시"
      }]
    }
  }
}
```

**개선점:**
- `scope=diagnosis` + `condition_type=지급사유` → 명확히 "지급사유 문맥"임을 표시
- `usable_as_coverage=true` → UI에서 "보장 O"로 사용 가능
- `evidence_refs`에 실제 문구 포함 → 사용자가 직접 확인 가능

---

## Definition 케이스 예시 (가상)

만약 다음과 같은 문구가 있다면:

**문구:**
> "유사암이란 기타피부암, 갑상선암, 제자리암 및 경계성종양을 말합니다."

**분류:**
```json
{
  "in_situ": {
    "decision": "X",
    "original_decision": "O",
    "scope": "definition",
    "condition_type": "정의",
    "usable_as_coverage": false,
    "notes": "정의 문맥에서 언급, 지급사유 아님"
  }
}
```

**UI 표기:**
- ❌ "제자리암 보장 O"
- ✅ "정의 문맥에서 언급" 또는 "해당 담보는 제자리암을 유사암 범위로 정의"

---

## 산출물

1. **Refined JSONL:**
   `docs/audit/step_next_81b_subtype_scope_refined.jsonl`

2. **Validation 결과:**
   `docs/audit/step_next_81b_validation.json`

3. **LOCK 문서 (본 문서):**
   `docs/audit/STEP_NEXT_81B_SUBTYPE_SCOPE_LOCK.md`

---

## 검증 결과 (GATE-81B)

- **GATE-81B-1** (All O items have scope): ✅ PASS
- **GATE-81B-2** (definition/example/unknown not usable): ✅ PASS
- **GATE-81B-3** (Sample consistency): ✅ PASS

총 1개 담보(KB 표적항암약물허가치료비) 처리 완료.

---

## 다음 단계

- UI/추천 시스템에서 `scope` 및 `usable_as_coverage` 필드 활용
- `definition/example` scope는 "정의 문맥 언급"으로만 표시
- `diagnosis/treatment` scope만 "보장 O" 판정에 사용
