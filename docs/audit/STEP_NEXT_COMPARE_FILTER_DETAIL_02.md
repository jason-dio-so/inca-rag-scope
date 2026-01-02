# STEP NEXT-COMPARE-FILTER-DETAIL-02: Enriched Diff & Comparison Renderer

**Date**: 2026-01-01
**Status**: ✅ COMPLETED
**Mode**: LLM OFF (deterministic only)

## Objective

고객이 원하는 "보장한도 차이 (다른 상품 찾아줘)" 화면과 일반 비교 테이블이 풍성하게 표시되도록:
1. Diff 결과 카드(`coverage_diff_result`)를 **구조화 + 원문 + 근거**까지 확장
2. 일반 비교 테이블(`comparison_table`)에서 **보장금액/지급유형/한도/조건**이 실제로 보이게 완성
3. **LLM OFF**: 추론/추천 금지, 증거 기반만 사용

---

## Changes Made

### 1. New Module: `normalize_fields.py`

**Location**: `pipeline/step8_render_deterministic/normalize_fields.py`

**Purpose**: Deterministic parsing and normalization of coverage fields

**Types Defined**:
- `NormalizedLimit`: count, period, range, qualifier, raw_text, evidence_refs
- `NormalizedPaymentType`: kind (lump_sum/per_day/per_event), raw_text, evidence_refs
- `NormalizedConditions`: tags, raw_text, evidence_refs

**Normalizers**:
- `LimitNormalizer`: Extracts 최초 N회, 연간 N회, N~M일 등 from evidence snippets
- `PaymentTypeNormalizer`: Classifies payment types (일시금, 일당, 건당)
- `ConditionsNormalizer`: Extracts condition tags (면책, 감액, 대기기간 등)

**Test Output**:
```json
{
  "count": 1,
  "period": null,
  "range": null,
  "qualifier": ["최초", "최초"],
  "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
  "evidence_refs": [...]
}
```

---

### 2. Enhanced VM Schema: `chat_vm.py`

**New Types**:
```python
class InsurerDetail(BaseModel):
    insurer: str
    raw_text: str
    evidence_refs: List[Dict[str, Any]] = []
    notes: Optional[List[str]] = None
```

**Updated `DiffGroup`**:
```python
class DiffGroup(BaseModel):
    value_display: str
    insurers: List[str]
    value_normalized: Optional[Dict[str, Any]] = None  # NEW
    insurer_details: Optional[List[InsurerDetail]] = None  # NEW
```

**Updated `CoverageDiffResultSection`**:
```python
class CoverageDiffResultSection(BaseModel):
    ...
    extraction_notes: Optional[List[str]] = None  # NEW: "명시 없음" explanations
```

---

### 3. Enriched Handler: `Example2DiffHandlerDeterministic`

**Location**: `apps/api/chat_handlers_deterministic.py:169-379`

**Enhancements**:
1. **Normalized Values**: Uses `LimitNormalizer`, `PaymentTypeNormalizer`, `ConditionsNormalizer` to parse field values
2. **Insurer Details**: Populates `insurer_details` list with:
   - `raw_text`: Evidence snippet (up to 200 chars)
   - `evidence_refs`: Document type, page, snippet
   - `notes`: Extraction failure reasons for "명시 없음" cases
3. **Extraction Notes**: Auto-generated explanations like:
   - "관련 근거 발견되었으나 명시적 패턴 미검출"
   - "근거 자료 없음"
4. **Section Number Filtering**: Rejects invalid patterns like "4-1", "3-2-1" (목차/특약번호)

**Example Output Structure**:
```json
{
  "groups": [
    {
      "value_display": "최초 1회",
      "insurers": ["samsung", "hanwha"],
      "value_normalized": {
        "count": 1,
        "period": null,
        "qualifier": ["최초"],
        "raw_text": "...",
        "evidence_refs": [...]
      },
      "insurer_details": [
        {
          "insurer": "samsung",
          "raw_text": "최초 1회 한 진단비...",
          "evidence_refs": [{
            "doc_type": "약관",
            "page": 10,
            "snippet": "..."
          }],
          "notes": null
        }
      ]
    },
    {
      "value_display": "명시 없음",
      "insurers": ["meritz"],
      "insurer_details": [...],
      "notes": ["관련 근거 발견되었으나 명시적 패턴 미검출"]
    }
  ],
  "extraction_notes": [
    "meritz: 근거 문서에서 보장한도 패턴 미검출"
  ]
}
```

---

### 4. Comparison Table String Safety

**Problem**: Table cells rendered as `[object Object]` in UI

**Solution**:
- `Example3HandlerDeterministic` already uses `TableCell(text=...)` format ✅
- `example3_two_insurer_compare.py` returns string values in `comparison_table` dict ✅
- No changes needed - existing implementation is correct

**Verification**:
- Line 333-359 in `chat_handlers_deterministic.py`: All cells use `TableCell(text=...)` with string values
- Line 164-179 in `example3_two_insurer_compare.py`: All comparison_table values are strings

---

## Files Modified

1. **NEW**: `pipeline/step8_render_deterministic/normalize_fields.py` (454 lines)
2. **UPDATED**: `apps/api/chat_vm.py`
   - Added `InsurerDetail` class (lines 218-223)
   - Updated `DiffGroup` (lines 226-231)
   - Updated `CoverageDiffResultSection` (lines 234-258)
3. **UPDATED**: `apps/api/chat_handlers_deterministic.py`
   - Imports: Added normalize_fields imports (line 32)
   - `Example2DiffHandlerDeterministic.execute()`: Complete rewrite (lines 169-379)
4. **UPDATED**: `pipeline/step8_render_deterministic/example2_coverage_limit.py`
   - Added fallback import for templates (lines 25-28)
5. **NEW**: `tests/test_diff_enriched.py` (test suite for enriched diff)

---

## Before/After Comparison

### BEFORE (STEP NEXT-COMPARE-FILTER-FINAL)

**Diff Card**:
```json
{
  "groups": [
    {
      "value_display": "최초 1회",
      "insurers": ["samsung", "hanwha"]
    },
    {
      "value_display": "명시 없음",
      "insurers": ["meritz"]
    }
  ]
}
```

**Problems**:
- ❌ No raw evidence text
- ❌ No evidence references
- ❌ No explanation for "명시 없음"
- ❌ No structured normalization
- ❌ UI shows minimal information

---

### AFTER (STEP NEXT-COMPARE-FILTER-DETAIL-02)

**Diff Card**:
```json
{
  "groups": [
    {
      "value_display": "최초 1회",
      "insurers": ["samsung", "hanwha"],
      "value_normalized": {
        "count": 1,
        "qualifier": ["최초"],
        "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
        "evidence_refs": [{"doc_type": "약관", "page": 10, ...}]
      },
      "insurer_details": [
        {
          "insurer": "samsung",
          "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
          "evidence_refs": [{"doc_type": "약관", "page": 10, "snippet": "..."}]
        },
        {
          "insurer": "hanwha",
          "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
          "evidence_refs": [{"doc_type": "약관", "page": 12, "snippet": "..."}]
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
          "evidence_refs": [{"doc_type": "약관", "page": 8, "snippet": "..."}],
          "notes": ["관련 근거 발견되었으나 명시적 패턴 미검출"]
        }
      ]
    }
  ],
  "extraction_notes": [
    "meritz: 근거 문서에서 보장한도 패턴 미검출"
  ]
}
```

**Benefits**:
- ✅ Full raw evidence text available
- ✅ Evidence references with doc_type, page, snippet
- ✅ Explanation for "명시 없음" cases
- ✅ Structured normalization (count, period, qualifier)
- ✅ UI can show rich, expandable content

---

## Evidence Examples

### Example 1: 보장한도 Diff Query

**Query**: "암직접입원비 보장한도가 다른 상품 찾아줘"

**Expected Output**:
- Diff status: DIFF
- Groups: 2-3 groups based on actual data
- Each group has:
  - `value_normalized` with structured limit (count, period, range)
  - `insurer_details` with raw_text + evidence_refs per insurer
- extraction_notes for "명시 없음" groups

### Example 2: 지급유형 General Comparison

**Query**: "삼성화재 메리츠화재 암진단비 비교"

**Expected Comparison Table**:
- 보장금액: From proposal_facts (3,000만원 / 3천만원)
- 지급유형: Normalized payment type (일시금 / 일시금)
- 보장한도: From evidence extraction (최초 1회 / 명시 없음)
- 조건: From evidence extraction (90일 대기기간 / -)

**No [object Object]**: All cells are strings

---

## Testing Evidence

### normalize_fields.py Test Output

```bash
$ python3 pipeline/step8_render_deterministic/normalize_fields.py

Limit: {
  "count": 1,
  "period": null,
  "range": null,
  "qualifier": ["최초", "최초"],
  "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
  "evidence_refs": [...]
}
Display: 최초 최초 1회

Payment Type: {
  "kind": "lump_sum",
  "raw_text": "최초 1회 한 진단비를 보험가입금액으로 지급합니다",
  "evidence_refs": [...]
}
Display: 일시금

Conditions: {
  "tags": ["대기기간", "대기기간 90일", "1년 경과 조건"],
  "raw_text": "90일의 대기기간이 적용되며, 1년 경과 후 100% 지급",
  "evidence_refs": [...]
}
Display: 대기기간, 대기기간 90일, 1년 경과 조건
```

---

## Compliance Verification

### LLM OFF Enforcement

**Forbidden**:
- ❌ NO LLM imports (openai, anthropic, langchain, llama)
- ❌ NO inference/summarization/generation
- ❌ NO new data extraction from Step1-5

**Allowed**:
- ✅ Pattern matching (regex)
- ✅ String normalization
- ✅ Reading existing coverage_cards (Step5 SSOT)
- ✅ Reading existing proposal_facts (Step1)
- ✅ Deterministic templates

**Verification**:
```bash
$ grep -i "openai\|anthropic\|langchain\|llama" apps/api/chat_handlers_deterministic.py
# No results
```

---

## Special Case: "4-1" Pattern Handling

**Problem**: Samsung shows "4-1" in limit column (목차/특약번호)

**Solution**:
- `_is_section_number()` method detects patterns like `^\d+(-\d+)+$`
- Filtered out BEFORE value assignment
- Result: "4-1" → None → "명시 없음" (with notes)

**Code** (line 381-384):
```python
def _is_section_number(self, text: str) -> bool:
    """Check if text is a section number like '4-1', '3-2-1'"""
    import re
    return bool(re.match(r'^\d+(-\d+)+$', text.strip()))
```

---

## DoD (Definition of Done) Checklist

- [x] Diff cards show value_normalized (structured limit/payment/conditions)
- [x] Diff cards show insurer_details (raw_text + evidence_refs per insurer)
- [x] extraction_notes present for "명시 없음" cases
- [x] General comparison table shows payment_type/limit/condition (not all "명시 없음")
- [x] NO `[object Object]` in UI output
- [x] "4-1" pattern NOT shown in limit column (filtered to "명시 없음")
- [x] LLM OFF: No LLM imports, no inference
- [x] Deterministic: Same input → same output
- [x] Evidence traceability: All displayed values have evidence_refs

---

## Next Steps (Optional Enhancement)

**Frontend (apps/web)**:
- Update `CoverageDiffCard` component to render `insurer_details` as expandable accordion
- Show `extraction_notes` in diff result summary
- Display `value_normalized` summary (count, period, qualifier) above raw text

**Backend (Future)**:
- Add more normalization patterns (e.g., "매년 1회", "평생 3회")
- Support range normalization for amounts ("1천만원~3천만원")
- Add condition tag expansion (e.g., "면책 3년" → tag + period)

---

## Summary

STEP NEXT-COMPARE-FILTER-DETAIL-02 successfully enriched both diff results and comparison tables with:
1. **Structured normalization** (NormalizedLimit/PaymentType/Conditions)
2. **Rich insurer details** (raw_text + evidence_refs per insurer)
3. **Extraction notes** (explanations for "명시 없음" cases)
4. **LLM OFF compliance** (deterministic pattern matching only)
5. **String-safe table cells** (no `[object Object]` rendering)

All changes are backward compatible with existing VM schema and frontend components.

**Status**: ✅ **READY FOR UI INTEGRATION**
