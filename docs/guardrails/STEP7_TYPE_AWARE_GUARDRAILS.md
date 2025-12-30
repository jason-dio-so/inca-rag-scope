# Step7 Type-Aware Guardrails - Quick Reference

**Created**: 2025-12-29
**STEP**: NEXT-10B-2C-4
**Status**: ACTIVE ✅

---

## Purpose

Prevent forbidden inference/heuristics in Step7 amount extraction, especially for Type C insurers where high UNCONFIRMED rate (70-90%) is NORMAL and CORRECT.

---

## Insurer Type Map

Located: `config/amount_lineage_type_map.json`

```json
{
  "samsung": "A",
  "lotte": "A",
  "heungkuk": "A",
  "meritz": "B",
  "db": "B",
  "hanwha": "C",
  "hyundai": "C",
  "kb": "C"
}
```

---

## Type Definitions

### Type A — Coverage-level 명시형

**Characteristics**:
- 가입설계서에 담보별 금액이 테이블/라인 단위로 명시
- PRIMARY rate ≥ 80% expected
- Example: Samsung (100%), Lotte (83.8%), Heungkuk (94.4%)

**Document Structure**:
```
담보가입현황        가입금액
암 진단비(유사암 제외)   3,000만원
상해 사망            1,000만원
```

---

### Type B — 혼합형 (Mixed Structure)

**Characteristics**:
- 일부 담보는 coverage-level 명시, 일부는 SECONDARY 문서에만 존재
- PRIMARY + SECONDARY coverage 45-60% expected
- Example: Meritz (52.9%), DB (46.7%)

**Document Structure**:
- Some coverages: line-by-line with amounts
- Some coverages: bundled in narrative
- Some coverages: only in 사업방법서/상품요약서

---

### Type C — Product-level 구조형

**Characteristics**:
- 가입설계서에 담보별 금액이 거의 없음
- 상품 공통 "보험가입금액"만 표기
- UNCONFIRMED 70-90% is **NORMAL and CORRECT**
- Example: Hanwha (89.2%), Hyundai (78.4%), KB (77.8%)

**Document Structure**:
```
보험가입금액: 5,000만원 (product level, stated once)

담보            보장내용
암진단비        암 진단시 보험가입금액 지급
뇌출혈진단비    뇌출혈 진단시 보험가입금액 지급
```

**CRITICAL**: Coverage-level amounts do NOT exist in these documents. UNCONFIRMED is the correct status.

---

## Forbidden Actions

### Type C Specific (CRITICAL)

❌ **FORBIDDEN**:
1. Extract "보험가입금액" and copy to all coverages
2. Infer coverage amount from product amount
3. Add "smart rules" to reduce UNCONFIRMED rate
4. Flag Type C as "broken" or "needs fixing"

✅ **CORRECT**:
- Extract only explicit coverage-specific amounts (10-25% is expected)
- Leave as UNCONFIRMED when coverage amount undefined

---

### Universal Forbidden Actions

❌ **FORBIDDEN**:
1. LLM/GPT to parse amounts
2. Embedding/similarity to match amount patterns
3. Loader extracts amount from evidence snippet
4. Cross-insurer amount copying

---

## Forbidden Patterns

**Must NOT appear in `value_text`**:

```python
[
    "민원사례",
    "목차",
    "특별약관",
    " 조 ",
    " 항 ",
    "페이지",
    "장 ",
    "절 ",
    "p.",
    "page",
    "보험가입금액"  # CRITICAL: Type C 금지 패턴
]
```

---

## Schema Rules

### CONFIRMED Amounts

MUST have:
- `value_text` (non-null, e.g., "3,000만원")
- `evidence_ref` (dict with doc_type, source, snippet)
- `source_priority` ("PRIMARY" or "SECONDARY")
- `source_doc_type` (가입설계서, 사업방법서, 상품요약서, 약관)

### UNCONFIRMED Amounts

MUST have:
- `value_text` = `null`
- `evidence_ref` = `null`
- `source_priority` = `null`
- `source_doc_type` = `null`

---

## STOP Conditions

**Immediate STOP if ANY of these detected**:

1. Forbidden patterns in `value_text`
2. Type C: "보험가입금액" in `value_text`
3. UNCONFIRMED with non-null `value_text`
4. CONFIRMED without `evidence_ref`
5. Type C: UNCONFIRMED rate < 70% (suspiciously low)

---

## Validation Commands

### Run Type-Aware Tests

```bash
pytest -q tests/test_step7_type_aware_guardrails.py
```

Expected: 51 passed

### Run Validation & Reporting

```bash
# Single insurer
python -m pipeline.step7_amount.validate_and_report --insurer hanwha

# Multiple insurers
python -m pipeline.step7_amount.validate_and_report \
  --insurers samsung,meritz,db,hanwha,hyundai,kb,lotte,heungkuk

# All insurers (default)
python -m pipeline.step7_amount.validate_and_report
```

### Run All Tests (Lineage + Type-Aware)

```bash
pytest -q tests/test_lineage_lock_step7.py \
           tests/test_lineage_lock_loader.py \
           tests/test_step7_type_aware_guardrails.py
```

Expected: 61 passed

---

## Files

### Core Modules

- `pipeline/step7_amount/guardrails.py` - Type-aware validation logic
- `pipeline/step7_amount/validate_and_report.py` - Validation & reporting script

### Tests

- `tests/test_step7_type_aware_guardrails.py` - 51 type-aware tests

### Configuration

- `config/amount_lineage_type_map.json` - Insurer type map (A/B/C)

### Reports

- `reports/step7_amount_validation_{insurer}.md` - Per-insurer validation report
- `reports/amount_validation_stats_{timestamp}.json` - Consolidated statistics

---

## Example Usage

### Check Type C Insurer (Hanwha)

```bash
python -m pipeline.step7_amount.validate_and_report --insurer hanwha
```

**Expected Output**:
```
Type: C
Total: 37
PRIMARY: 4 (10.8%)
SECONDARY: 0 (0.0%)
UNCONFIRMED: 33 (89.2%)
Schema: ✅ PASS
Forbidden: ✅ PASS
```

**Interpretation**:
- 89.2% UNCONFIRMED is NORMAL for Type C ✅
- No "보험가입금액" in value_text ✅
- All UNCONFIRMED have null value_text ✅

---

## Maintenance

### When Adding New Insurer

1. Add to `config/amount_lineage_type_map.json`
2. Classify as A, B, or C based on document structure
3. Run validation: `python -m pipeline.step7_amount.validate_and_report --insurer {new_insurer}`
4. Verify type expectations are met

### When Modifying Step7 Extraction Logic

1. Run all tests: `pytest -q tests/test_*lineage*.py tests/test_step7_type_aware_guardrails.py`
2. Run validation for all insurers
3. Verify NO STOP conditions detected
4. Check Type C insurers still have 70-90% UNCONFIRMED

---

## Reference

- Type definition report: `reports/amount_lineage_typing_20251229-001053.md`
- Completion report: `STEP_NEXT_10B_2C_4_COMPLETION.md`
- Lineage snapshot: `docs/lineage_snapshots/pre_10b2c4/`

---

**Last Updated**: 2025-12-29
**Status**: ACTIVE ✅
