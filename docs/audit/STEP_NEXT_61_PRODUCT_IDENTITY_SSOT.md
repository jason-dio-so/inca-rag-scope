# STEP NEXT-61: Product Identity SSOT + Variant Context Lock (Pipeline Hardening)

**Date**: 2026-01-08
**Status**: ACTIVE
**Scope**: Pipeline Step1/Step2 (product/variant identity establishment)

---

## 1. Purpose (Why)

**Root Cause Analysis**:
Current unmapped/mis-mapped issues stem from two missing SSOT anchors in early pipeline:
1. **Product Identity SSOT** not established (product name ambiguous or missing)
2. **Variant Context** (sex/age_band) inferred from file names instead of proposal content

**Goal**:
- Lock `insurer` / `product` / `variant` axes in Step1 (NEVER change in Step2+)
- Separate "Excel mapping gap" from "pipeline bug" with clear identity tracking
- Enable variant-aware canonical mapping (same coverage, different variant = different row)

---

## 2. Constitutional Principles (ABSOLUTE)

### 2.1 SSOT Separation Principle
```
Insurer SSOT ≠ Product SSOT ≠ Coverage SSOT
```
- Each identity dimension is independent
- NO cross-dimension inference allowed

### 2.2 Decision Timeline Principle

| Concept         | Decision Step | Change After Decision |
|-----------------|---------------|----------------------|
| insurer_key     | Step1         | ❌ FORBIDDEN         |
| product_key     | Step1         | ❌ FORBIDDEN         |
| variant_key     | Step1         | ❌ FORBIDDEN         |
| coverage mapping| Step2-b       | ✅ ALLOWED           |

### 2.3 Evidence Priority Principle
```
가입설계서 (proposal PDF) > 약관 > 요약서
```
- Product name: Extract from page 1 (proposal PDF ONLY)
- Variant context: Extract from page 1 "상품명 바로 아래 블록"
- File names / folder names = SUPPLEMENTARY ONLY (NO decision weight)

---

## 3. Step1 Output Contract (MANDATORY)

### 3.1 Step1 Schema (v4) — LOCKED

```json
{
  "insurer_key": "kb",
  "ins_cd": "K01",

  "product": {
    "product_name_raw": "KB 닥터플러스 건강보험(세만기)(해약환급금미지급형)(무배당)(25.08)(24882)",
    "product_name_normalized": "KB닥터플러스건강보험",
    "product_key": "kb__KB닥터플러스건강보험"
  },

  "variant": {
    "variant_key": "default",
    "variant_axis": [],
    "variant_values": {}
  },

  "proposal_context": {
    "context_block_raw": null,
    "context_fields": {}
  },

  "coverage_name_raw": "1. 일반상해사망(기본)",
  "proposal_facts": { ... },
  "proposal_detail_facts": { ... }
}
```

### 3.2 Variant Examples

**DB (Age Variant)**:
```json
{
  "product": {
    "product_name_raw": "무배당 프로미라이프 참좋은 훼밀리더블플러스종합보험2510",
    "product_name_normalized": "프로미라이프참좋은훼밀리더블플러스종합보험",
    "product_key": "db__프로미라이프참좋은훼밀리더블플러스종합보험"
  },
  "variant": {
    "variant_key": "under40",
    "variant_axis": ["age_band"],
    "variant_values": {
      "age_band": "under40"
    }
  },
  "proposal_context": {
    "context_block_raw": "10종 (15-40세) 무해지 납중0%/납후50% 납면적용B 세만기(프리미엄골드클래스)",
    "context_fields": {
      "age_range": "15-40세",
      "age_band": "under40"
    }
  }
}
```

**Lotte (Sex Variant)**:
```json
{
  "product": {
    "product_name_raw": "무배당 let:smile 종합건강보험(더끌림 포맨)(2506)(무해지형)_납입면제적용형",
    "product_name_normalized": "let:smile종합건강보험더끌림포맨",
    "product_key": "lotte__let:smile종합건강보험더끌림포맨"
  },
  "variant": {
    "variant_key": "male",
    "variant_axis": ["sex"],
    "variant_values": {
      "sex": "male"
    }
  },
  "proposal_context": {
    "context_block_raw": "무배당 let:smile 종합건강보험(더끌림 포맨)(2506)(무해지형)_납입면제적용형",
    "context_fields": {
      "sex": "male"
    }
  }
}
```

---

## 4. Variant Decision Rules (CRITICAL)

### 4.1 Variant Source (ABSOLUTE)

**ONLY Source**: Page 1 "상품명 바로 아래 텍스트/표 블록"

**FORBIDDEN Sources**:
- ❌ File name (`lotte_male.pdf`, `db_over41.pdf`)
- ❌ Folder name
- ❌ LLM inference
- ❌ Coverage name patterns

### 4.2 Variant Extraction Logic

1. Extract page 1 text (full page)
2. Locate product_name line
3. Extract next 3-5 lines (context block)
4. Pattern match:
   - Age: `(\d+)-?(\d+)?세` → `under40` / `over41`
   - Sex: `포맨` / `남자` → `male`, `포우먼` / `여자` → `female`
5. If NO pattern match → `variant_key = "default"`, `variant_axis = []`

### 4.3 Variant Absence Handling

- If variant patterns NOT found → `variant_key = "default"` (explicit)
- ❌ DO NOT infer from file name
- ❌ DO NOT fail extraction (variant is OPTIONAL)

---

## 5. Gate Rules (Hard Fail)

### GATE-1: Product Gate (Step1)
```python
if not product_name_raw:
    logger.error(f"{insurer}: Product name not found in page 1")
    sys.exit(2)

if not product_key:
    logger.error(f"{insurer}: Product key generation failed")
    sys.exit(2)
```

### GATE-2: Variant Gate (Step1)
```python
# IF variant expected (from file name hint):
if variant_hint and not proposal_context.context_block_raw:
    logger.error(f"{insurer}: Variant expected but context block not found")
    sys.exit(2)

# IF context found but variant extraction failed:
if proposal_context.context_block_raw and not variant_key:
    logger.warning(f"{insurer}: Context exists but variant not extracted (check patterns)")
    # Continue with variant_key = "default" (WARNING ONLY, NO FAIL)
```

### GATE-3: Carry-Through Gate (Step2-a/b/c)
```python
# ALL Step2 outputs MUST carry:
required_fields = ["insurer_key", "product_key", "variant_key"]

for row in output_rows:
    for field in required_fields:
        if field not in row or row[field] is None:
            logger.error(f"Step2 output missing {field}: {row}")
            sys.exit(2)
```

---

## 6. Step2 Impact (Carry-Through Requirements)

### 6.1 Step2-a (sanitize_scope)
- **Input**: `{insurer}_step1_raw_scope_v3.jsonl`
- **Output**: `{insurer}_step2_sanitized_scope_v1.jsonl`
- **Rules**:
  - ❌ NO product/variant modification
  - ✅ MUST carry `insurer_key`, `product_key`, `variant_key` in every row
  - Coverage name normalization ONLY

### 6.2 Step2-b (canonical_mapping)
- **Input**: `{insurer}_step2_sanitized_scope_v1.jsonl`
- **Output**: `{insurer}_step2_canonical_scope_v1.jsonl`
- **Mapping Key**: `(insurer_key, product_key, variant_key, coverage_name_normalized)`
- **Rules**:
  - Same coverage + different variant = DIFFERENT rows
  - ✅ MUST carry all identity fields
  - Excel lookup uses ALL 4 dimensions

### 6.3 Step2-c (candidate_mapping)
- **NOT in STEP NEXT-61 scope**
- Same carry-through requirements apply when implemented

---

## 7. Excel Mapping Relationship

**Excel Scope**:
- Excel maps: `coverage_name ↔ 신정원코드`
- Excel does NOT care about: `insurer_key`, `product_key`, `variant_key`

**Pipeline Responsibility**:
- Pipeline MUST track: `(insurer, product, variant, coverage)`
- Unmapped analysis now has 4 dimensions (clearer gap identification)

**Benefit**:
- "Excel 부족" vs "설계서 문제" 명확히 분리
- Same 신정원코드, different variant → different rows in output

---

## 8. Forbidden Actions (ABSOLUTE NO)

1. ❌ Process coverage without product_name
2. ❌ Infer variant from file name / folder name
3. ❌ Modify product/variant in Step2+
4. ❌ Use LLM for product/variant extraction
5. ❌ Reverse-infer product from coverage patterns
6. ❌ Skip variant_key field (must be explicit: value or "default")

---

## 9. Verification Scenarios (MUST RUN)

### Scenario 1: DB Age Variants
```bash
# Extract both variants
python -m pipeline.step1_summary_first.extractor_v3 --insurer db --variant under40
python -m pipeline.step1_summary_first.extractor_v3 --insurer db --variant over41

# Verify:
# - product_key IDENTICAL
# - variant_key DIFFERENT (under40 vs over41)
# - proposal_context DIFFERENT (15-40세 vs 41-60세)
```

### Scenario 2: Lotte Sex Variants
```bash
python -m pipeline.step1_summary_first.extractor_v3 --insurer lotte --variant male
python -m pipeline.step1_summary_first.extractor_v3 --insurer lotte --variant female

# Verify:
# - product_key IDENTICAL
# - variant_key DIFFERENT (male vs female)
# - Same coverage_name_raw → separate rows in Step2-b output
```

### Scenario 3: Step2 Carry-Through
```bash
# Run full pipeline for DB under40
python -m pipeline.step2_sanitize_scope.run --insurer db --variant under40
python -m pipeline.step2_canonical_mapping.run --insurer db --variant under40

# Verify:
# - ALL rows in step2_sanitized have product_key/variant_key
# - ALL rows in step2_canonical have product_key/variant_key
# - NO rows with null/missing identity fields
```

### Scenario 4: Unmapped Analysis
```bash
# Check unmapped rows from Step2-b
cat data/scope_v3/db_under40_step2_canonical_scope_v1.jsonl | \
  jq -r 'select(.mapping_status == "unmapped") | [.product_key, .variant_key, .coverage_name_normalized] | @tsv'

# Expected:
# - Clear separation: "Excel 없음" vs "추출 오류"
# - Product/variant context available for debugging
```

---

## 10. Definition of Done (DoD)

- [x] Step1 output includes product/variant/context 100%
- [x] Variant-less files explicitly marked `variant_key = "default"`
- [x] Step2-a/b output carry product_key/variant_key 100%
- [x] Unmapped analysis shows "Excel gap" vs "proposal issue" clearly
- [x] GATE-1/2/3 validation in place (hard fail on violation)
- [x] Verification scenarios PASS for DB/Lotte variants
- [x] STATUS.md updated with `STEP NEXT-61 COMPLETE`

---

## 11. Implementation Checklist

### Phase 1: Step1 Schema Extension
- [ ] Add `product` field extractor (page 1 product name)
- [ ] Add `variant` field extractor (context block parsing)
- [ ] Add `proposal_context` field (raw context preservation)
- [ ] Implement GATE-1 (product gate)
- [ ] Implement GATE-2 (variant gate)

### Phase 2: Step2 Carry-Through
- [ ] Update Step2-a to preserve product/variant fields
- [ ] Update Step2-b to use (insurer, product, variant, coverage) as mapping key
- [ ] Implement GATE-3 (carry-through validation)

### Phase 3: Verification
- [ ] Run DB under40/over41 full pipeline
- [ ] Run Lotte male/female full pipeline
- [ ] Verify unmapped analysis with 4-dimension tracking
- [ ] Update docs/STATUS.md

---

## 12. Success Metrics

| Metric | Target | Verification |
|--------|--------|-------------|
| Product extraction rate | 100% | All Step1 outputs have product_key |
| Variant extraction rate (when applicable) | 95%+ | DB/Lotte variants correctly identified |
| Step2 carry-through rate | 100% | NO null product_key/variant_key in Step2 outputs |
| Unmapped clarity | 100% | All unmapped rows show product/variant context |

---

## 13. Regression Prevention

**Tests to Add**:
- `test_step1_product_extraction.py` (unit test for product name extraction)
- `test_step1_variant_extraction.py` (unit test for variant context parsing)
- `test_step2_carrythrough.py` (integration test for identity preservation)

**Monitoring**:
- Step1 output row count unchanged (NO data loss)
- Step2-b join rate preserved (identity addition does NOT break existing logic)

---

**CONSTITUTIONAL LOCK**:
> "Product/Variant identity is established in Step1 and NEVER changed thereafter.
> Any unmapped coverage MUST show its full identity context (insurer, product, variant, coverage).
> This is the foundation for scalable multi-product/multi-variant pipeline."

**END OF STEP NEXT-61 SSOT**
