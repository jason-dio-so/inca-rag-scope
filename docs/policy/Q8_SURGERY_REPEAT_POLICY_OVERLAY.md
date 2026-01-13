# Q8: Surgery Repeat Payment Policy Overlay

**Status**: FROZEN
**Type**: TYPE B - Overlay (Evidence-First)
**Date**: 2026-01-13

---

## 1. Problem Definition (Fixed)

### Q8-A (Demo Query, Fact-Only)

"질병 수술비(1~5종) 담보에서 '연간 1회 지급'인지, '매회(회당) 반복 지급'인지가 문서에 어떻게 명시되어 있는지를 보험사별로 비교해준다."

### Prohibited Actions ❌

- "대장용종 제거" 등 특정 수술 귀속 해석
- "가장 큰 곳" 랭킹/추천
- 금액 비교
- 추론/관행 해석

### Allowed Actions ✅

- 문서에 명시된 반복 지급 조건 문구만 추출
- 근거 없으면 UNKNOWN 유지

---

## 2. Type Classification

- **TYPE B**: Overlay
- **Core Slot / Step3 / compare_rows_v1.jsonl**: 절대 수정 금지
- **Pattern**: Q5/Q7/Q11과 동일한 Overlay 패턴 사용

---

## 3. Output SSOT Definition

### File Path
```
data/compare_v1/q8_surgery_repeat_policy_v1.jsonl
```

### Record Schema (Fixed)
```json
{
  "insurer_key": "samsung",
  "repeat_payment_policy": "PER_EVENT | ANNUAL_LIMIT | UNKNOWN",
  "display_text": "매회 지급 | 연간 1회한 | 확인 불가 (근거 없음)",
  "evidence_refs": [
    {
      "doc_type": "약관",
      "page": 32,
      "excerpt": "질병수술비는 수술 1회당 지급합니다."
    }
  ]
}
```

### Enum Values

- **PER_EVENT**: "매회", "회당", "수술 1회당"
- **ANNUAL_LIMIT**: "연간 1회", "연 1회한"
- **UNKNOWN**: 문서에 명시 없음

---

## 4. Evidence Extraction Rules (Strict)

### Document Search Priority (Fixed Order)
1. 약관
2. 사업방법서
3. 상품요약서
4. 가입설계서

### Allowed Keywords

**PER_EVENT Candidates:**
- "매회"
- "회당"
- "수술 1회당"

**ANNUAL_LIMIT Candidates:**
- "연간 1회"
- "연 1회한"
- "1년 1회"

### Important Constraints

⚠️ **질병명/수술명 포함 여부는 무시**
→ "대장용종" 단어가 있어도 귀속 판단 금지

---

## 5. Decision Rules (Evidence-First)

- **문서 + 페이지 + 원문 인용 없으면 무조건 UNKNOWN**
- **한 보험사에 상충 문구 존재 시**:
  - 더 제한적인 조건 선택
  - evidence_refs에 모두 기록
- **추론 / 보정 / 관행 해석 ❌**

---

## 6. API Implementation

### Endpoint
```
GET /q8
```

### Response Format
```json
{
  "query_id": "Q8",
  "items": [
    {
      "insurer_key": "samsung",
      "repeat_payment_policy": "PER_EVENT",
      "display_text": "매회 지급",
      "evidence_count": 2,
      "evidence": {
        "doc_type": "약관",
        "page": 32,
        "excerpt": "질병수술비는 수술 1회당 지급합니다."
      }
    }
  ]
}
```

---

## 7. Regression Prevention Checklist

The following items must remain **UNCHANGED**:

- [ ] compare_rows_v1.jsonl (line count identical)
- [ ] Q5 endpoint results
- [ ] Q7 endpoint results
- [ ] Q11 endpoint results
- [ ] Q13 matrix results

---

## 8. Required Documentation

### Policy Document
- **This file**: `docs/policy/Q8_SURGERY_REPEAT_POLICY_OVERLAY.md`
  - Q8 scope definition
  - Prohibited actions declared
  - "대장용종/최대금액 미포함" declaration

### Audit Document
- `docs/audit/Q8_FACT_SNAPSHOT_YYYY-MM-DD.md`
  - Evidence extraction log
  - UNKNOWN justification

---

## 9. Freeze Condition

### Q8 = FROZEN when:
✅ SSOT generated + API functional

### After Freeze - Allowed:
- SSOT regeneration (when documents added)
- UI expression improvement

### After Freeze - Prohibited:
- Adding premium ranking
- Specific surgery attribution decision

---

---

## Core Model Integrity (SHA256 Verification)

Q8 is an **Overlay-only** implementation. The following Core Model files remain **UNCHANGED**:

```
compare_rows_v1.jsonl:
f3935d6ffdb790da9fe1aa88bd0017244b9117b9ef84aadc81a6b1cb6d3c4914

compare_tables_v1.jsonl:
4a4a3f6e2060b8ad72f3f22773cdd3116bf5ea592b46af11b494f781cef7f70a
```

**Verification Command**:
```bash
sha256sum data/compare_v1/compare_rows_v1.jsonl data/compare_v1/compare_tables_v1.jsonl
```

If hashes differ, Q8 implementation has **violated** the Overlay principle.

---

## Summary (For Claude)

**Q8 implements "질병수술비 반복 지급 조건 문구 비교" ONLY as an Overlay.**

**In Scope**:
- ✅ 질병수술비(1~5종) coverage: Extracting repeat payment frequency policy from documents
- ✅ Pattern matching: "매회"/"회당" vs "연간 1회한"
- ✅ Evidence-based only: Document + Page + Excerpt required
- ✅ UNKNOWN when no explicit evidence

**Out of Scope (Prohibited)**:
- ❌ "대장용종 제거" specific surgery attribution
- ❌ "가장 큰 금액" premium ranking/recommendation
- ❌ Specific surgery name interpretation
- ❌ Cross-coverage inference
- ❌ LLM estimation or backfill
- ❌ Core slot creation/modification
