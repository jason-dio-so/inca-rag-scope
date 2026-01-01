# STEP NEXT-61C — Evidence Fill Rate Analysis

## GATE-4-2: Evidence Quality Validation

### Purpose
Prevent "hollow 100% join rates" where Step5 join succeeds but evidence arrays are empty.

### Methodology
```
fill_rate = (# coverages with evidence snippets > 0) / (total coverages)
```

### Thresholds
| Level | Range | Action |
|-------|-------|--------|
| ❌ Hard Fail | < 0.60 | Execution stops |
| ⚠️  Warn | 0.60 - 0.79 | Log warning, continue |
| ✅ Pass | ≥ 0.80 | Proceed normally |

---

## Results Summary

**All 10 axes achieved 100% fill_rate** — Perfect evidence coverage

---

## Detailed Fill Rate Table

| # | Axis | Total Coverages | With Evidence | Without Evidence | Fill Rate | GATE-4-2 Status |
|---|------|-----------------|---------------|------------------|-----------|-----------------|
| 1 | samsung | 32 | 32 | 0 | **1.00** | ✅ PASS |
| 2 | meritz | 30 | 30 | 0 | **1.00** | ✅ PASS |
| 3 | hanwha | 33 | 33 | 0 | **1.00** | ✅ PASS |
| 4 | heungkuk | 36 | 36 | 0 | **1.00** | ✅ PASS |
| 5 | hyundai | 37 | 37 | 0 | **1.00** | ✅ PASS |
| 6 | kb | 43 | 43 | 0 | **1.00** | ✅ PASS |
| 7 | lotte_male | 31 | 31 | 0 | **1.00** | ✅ PASS |
| 8 | lotte_female | 31 | 31 | 0 | **1.00** | ✅ PASS |
| 9 | db_under40 | 31 | 31 | 0 | **1.00** | ✅ PASS |
| 10 | db_over41 | 31 | 31 | 0 | **1.00** | ✅ PASS |

**Aggregate**: 335/335 coverages have evidence (100%)

---

## Evidence Source Distribution

Evidence found across 3 document types per coverage:
- 약관 (policy terms)
- 사업방법서 (business methods)
- 상품요약서 (product summary)

### Typical Evidence Pattern (per coverage)
```json
{
  "evidences": [
    {"doc_type": "약관", "snippet": "...", "page": 123},
    {"doc_type": "사업방법서", "snippet": "...", "page": 45},
    {"doc_type": "상품요약서", "snippet": "...", "page": 6}
  ],
  "hits_by_doc_type": {
    "약관": 3,
    "사업방법서": 3,
    "상품요약서": 3
  }
}
```

---

## Interpretation

### ✅ Key Findings
1. **Zero hollow joins**: Every coverage has supporting evidence
2. **Multi-source validation**: Evidence sourced from 약관, 사업방법서, 상품요약서
3. **Deterministic search**: No LLM/embedding — pure keyword matching
4. **Reproducible**: Same inputs → same fill_rate

### 🔍 Unmapped vs. Fill Rate
- **Unmapped** (from mapping_status): Coverage name didn't match canonical code
- **Fill Rate** (from evidence search): Evidence snippets found/not found

**Result**: Even unmapped coverages can have evidence (from raw name matching in PDFs)

---

## GATE-4-2 vs. GATE-5-2 Relationship

| Gate | What It Measures | Failure Mode Prevented |
|------|------------------|------------------------|
| **GATE-4-2** (fill_rate) | Evidence quality per coverage | Empty evidence arrays (hollow joins) |
| **GATE-5-2** (join_rate) | Join completeness Step2↔Step4 | Missing rows after join |

**Both gates passed** → High-quality evidence-backed coverage cards

---

## Historical Context

### Before GATE-4-2 (STEP NEXT-61A)
- Only GATE-5-2 (join_rate ≥ 95%) enforced
- Risk: 100% join with empty evidence arrays would pass undetected

### After GATE-4-2 (STEP NEXT-61C)
- **Two-layer validation**: join completeness + evidence substance
- **100% fill_rate** proves evidence search is working correctly

---

## Next Actions

### ✅ No Action Needed (This STEP)
All axes passed GATE-4-2 with perfect scores.

### 🔜 Future Considerations (Separate STEPs)
If future axes show fill_rate < 0.80:
1. Check evidence_text extraction (Step3 GATE-3-1)
2. Review search keyword logic (Step4 search_evidence.py)
3. Verify PDF quality (OCR/digitized text availability)

**Do NOT modify Step2 canonical scope in response to low fill_rate** — evidence issue is separate from mapping issue.

---

## Execution Evidence

**Logs**: `data/scope_v3/_RUNS/run_20260101_160000/*_step4.log`

**Verification Command**:
```bash
grep "fill_rate" data/scope_v3/_RUNS/run_20260101_160000/SUMMARY.log
```

**Output**:
```
  Evidence pack: 32 rows, 32 with evidence, fill_rate=1.00
  Evidence pack: 30 rows, 30 with evidence, fill_rate=1.00
  Evidence pack: 33 rows, 33 with evidence, fill_rate=1.00
  Evidence pack: 36 rows, 36 with evidence, fill_rate=1.00
  Evidence pack: 37 rows, 37 with evidence, fill_rate=1.00
  Evidence pack: 43 rows, 43 with evidence, fill_rate=1.00
  Evidence pack: 31 rows, 31 with evidence, fill_rate=1.00
  Evidence pack: 31 rows, 31 with evidence, fill_rate=1.00
  Evidence pack: 31 rows, 31 with evidence, fill_rate=1.00
  Evidence pack: 31 rows, 31 with evidence, fill_rate=1.00
```

**Result**: 10/10 axes at 100% fill_rate ✅
