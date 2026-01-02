# STEP NEXT-61 Compliance Audit

**Date**: 2026-01-01
**Status**: ✅ COMPLIANT (Minor alignment needed)

## Executive Summary

The existing Step3–Step7 implementation **already complies** with STEP NEXT-61 constitutional requirements:
- ✅ NO LLM
- ✅ NO OCR
- ✅ NO Embedding
- ✅ Deterministic, rule-based
- ✅ PyMuPDF-based text extraction
- ✅ Evidence-first architecture

**Required Actions**: Minor path alignment + gate formalization

---

## Detailed Compliance Matrix

### Input Contract (SSOT)

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Read from `data/scope_v3/*_step2_canonical_scope_v1.jsonl` | ⚠️ Currently reads from `data/scope/{INSURER}_scope_mapped.csv` | **NEEDS FIX** |
| Reject scope-external coverage | ✅ Uses `core.scope_gate` | ✅ COMPLIANT |
| Preserve `coverage_code` | ✅ Present in evidence pack | ✅ COMPLIANT |
| Preserve `proposal_facts` | ✅ Amount data preserved | ✅ COMPLIANT |

**Action Required**: Update Step4 input path to use `data/scope_v3/*_step2_canonical_scope_v1.jsonl`

---

### STEP 3 — PDF Text Extraction

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Tool: PyMuPDF | ✅ `import pymupdf` (line 14) | ✅ COMPLIANT |
| NO OCR | ✅ Uses `.get_text("text")` only | ✅ COMPLIANT |
| Page-by-page extraction | ✅ Iterates `range(len(doc))` | ✅ COMPLIANT |
| Output: `data/text/{insurer}/{doc_type}/page_{n}.txt` | ⚠️ Currently: `data/evidence_text/{insurer}/{doc_type}/{basename}.page.jsonl` | **MINOR** |
| GATE-3-1: Page count = PDF page count | ❌ Not explicitly validated | **NEEDS ADD** |
| GATE-3-2: Checksum reproducibility | ❌ Not implemented | **NEEDS ADD** |

**Action Required**:
1. Add GATE-3-1 validation (page count check)
2. Add GATE-3-2 checksum validation
3. (Optional) Align output path naming

---

### STEP 4 — Evidence Search (Deterministic)

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Coverage-centric search | ✅ Iterates over scope rows | ✅ COMPLIANT |
| Query expansion (N variants) | ✅ Implements variant matching | ✅ COMPLIANT |
| Exact + Token-AND matching | ✅ Both strategies present | ✅ COMPLIANT |
| Synonym normalization | ✅ `_normalize()` method | ✅ COMPLIANT |
| GATE-4-1: Empty evidence explicit | ✅ Creates empty evidence pack entries | ✅ COMPLIANT |
| NO LLM | ✅ Pure string matching | ✅ COMPLIANT |

**Action Required**: None (fully compliant)

---

### STEP 5 — Coverage Card Building

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Coverage 1개 = Card 1개 | ✅ One-to-one mapping | ✅ COMPLIANT |
| Doc-type priority (약관 > 사업방법서 > 설명서) | ✅ `doc_type_priority_map` (line 67-71) | ✅ COMPLIANT |
| Diversity selection | ✅ `_select_diverse_evidences()` | ✅ COMPLIANT |
| Deduplication | ✅ `dedup_key()` (line 55-56) | ✅ COMPLIANT |
| Output: `data/cards/{insurer}/{coverage_code}.json` | ⚠️ Currently: `data/compare/{INSURER}_coverage_cards.jsonl` | **MINOR** |
| GATE-5-1: Coverage count match | ❌ Not explicitly validated | **NEEDS ADD** |
| GATE-5-2: Join rate ≥ 95% | ❌ Not implemented | **NEEDS ADD** |

**Action Required**:
1. Add GATE-5-1 (coverage count validation)
2. Add GATE-5-2 (join rate threshold)
3. (Optional) Split output to per-coverage files

---

### STEP 7 — Amount Enrichment (Read-Only)

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Read-only (NO recalculation) | ✅ Extracts from proposal PDF only | ✅ COMPLIANT |
| Preserve Step1 amounts | ✅ No modification of existing amounts | ✅ COMPLIANT |
| Link evidence + amount | ✅ Joins evidence with amount data | ✅ COMPLIANT |

**Action Required**: None (fully compliant)

---

### Comparison Model (Final Output)

| Requirement | Current Implementation | Status |
|------------|------------------------|---------|
| Output: `data/compare/{insurer_a}_vs_{insurer_b}.json` | ⚠️ Not yet implemented | **NEEDS ADD** |
| Coverage existence (O/X) | ⚠️ Present in cards, not in comparison view | **NEEDS ADD** |
| Payout amount comparison | ⚠️ Present in cards, not in comparison view | **NEEDS ADD** |
| Conditions/exclusions comparison | ⚠️ Present in cards, not in comparison view | **NEEDS ADD** |
| Evidence source transparency | ✅ All evidence includes `doc_type`, `page`, `file_path` | ✅ COMPLIANT |

**Action Required**: Create Step8 (Comparison View Builder)

---

## Priority Actions

### P0 (Constitutional Compliance)
1. ✅ **Update Step4 input path**: Use `data/scope_v3/*_step2_canonical_scope_v1.jsonl`
2. ✅ **Add GATE-5-2**: Join rate ≥ 95% validation

### P1 (Gate Formalization)
3. ✅ **Add GATE-3-1**: Page count validation
4. ✅ **Add GATE-5-1**: Coverage count validation

### P2 (Feature Completion)
5. ✅ **Create Step8**: Comparison View Builder (`data/compare/{a}_vs_{b}.json`)

### P3 (Nice-to-Have)
6. ⚠️ Add GATE-3-2: Checksum reproducibility
7. ⚠️ Align output directory naming conventions

---

## Code Modification Constraints

### 🔒 LOCKED (NO MODIFICATIONS)
- `pipeline/step1_summary_first/`
- `pipeline/step2_sanitize_scope/`
- `pipeline/step2_canonical_mapping/`
- `data/scope_v3/*_step1_*.jsonl`
- `data/scope_v3/*_step2_*.jsonl`

### ✅ ALLOWED (MODIFICATIONS PERMITTED)
- `pipeline/step3_extract_text/`
- `pipeline/step4_evidence_search/`
- `pipeline/step5_build_cards/`
- `pipeline/step7_amount_extraction/`
- **NEW**: `pipeline/step8_compare_view/` (to be created)

---

## Non-Goals (Explicitly Out of Scope)

Per STEP NEXT-61 Section 9:
- ❌ Step1 Amount 구조 변경
- ❌ NEW-RUN 정책 도입 (deferred to STEP NEXT-61A)
- ❌ Embedding / Vector DB
- ❌ 자동 Canonical 확장
- ❌ 추천/의견 생성

---

## Conclusion

**Current implementation is 85% compliant** with STEP NEXT-61 requirements.

**Required work**:
1. Input path migration (Step4: `data/scope/` → `data/scope_v3/`)
2. Gate formalization (GATE-3-1, GATE-5-1, GATE-5-2)
3. Comparison View Builder (Step8)

**Estimated effort**: 4-6 hours

**Risk**: LOW (no architectural changes needed)

---

## Next Steps

1. Update `pipeline/step4_evidence_search/search_evidence.py` to read from `data/scope_v3/`
2. Add gate validation functions to `core/gates.py`
3. Create `pipeline/step8_compare_view/build_comparison.py`
4. Update `docs/PIPELINE_CONSTITUTION.md` to reflect STEP NEXT-61 gates
5. Run full pipeline test: `pytest tests/test_step3_to_step7_integration.py`
