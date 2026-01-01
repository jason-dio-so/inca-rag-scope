# INSURER CODE AUDIT

**STEP NEXT-50-A / Audit A**
**Date**: 2026-01-01
**Purpose**: Verify 100% consistency between canonical_mapper.py insurer codes and 담보명mapping자료.xlsx

---

## 1. Executive Summary

✅ **PASS**: All 8 insurer codes are **100% consistent** between code and Excel.

**Finding**: Zero discrepancies detected.

---

## 2. Methodology

1. Extract `INSURER_CODE_MAP` from `pipeline/step2_canonical_mapping/canonical_mapper.py`
2. Extract `ins_cd` column from `data/sources/mapping/담보명mapping자료.xlsx`
3. Perform 1:1 mapping verification
4. Check for:
   - Missing insurers (in code but not in Excel)
   - Extra insurers (in Excel but not in code)
   - Code mismatches (same insurer, different code)

---

## 3. Verification Table

| Insurer (English) | Code in canonical_mapper.py | Code in Excel | Excel Name | Rows in Excel | Status |
|-------------------|----------------------------|---------------|------------|---------------|--------|
| meritz            | N01                        | N01           | 메리츠       | 31            | ✅ MATCH |
| hanwha            | N02                        | N02           | 한화        | 52            | ✅ MATCH |
| lotte             | N03                        | N03           | 롯데        | 35            | ✅ MATCH |
| heungkuk          | N05                        | N05           | 흥국        | 34            | ✅ MATCH |
| samsung           | N08                        | N08           | 삼성        | 40            | ✅ MATCH |
| hyundai           | N09                        | N09           | 현대        | 27            | ✅ MATCH |
| kb                | N10                        | N10           | KB         | 38            | ✅ MATCH |
| db                | N13                        | N13           | DB         | 30            | ✅ MATCH |

**Total**: 8/8 matched (100%)

---

## 4. Code Extraction

### canonical_mapper.py (lines 27-38)

```python
INSURER_CODE_MAP = {
    'meritz': 'N01',
    'hanwha': 'N02',
    'lotte': 'N03',
    'heungkuk': 'N05',
    'samsung': 'N08',
    'hyundai': 'N09',
    'kb': 'N10',
    'db': 'N13'  # Fixed: DB uses N13, not N11
}
```

### Excel ins_cd Distribution

```
N01: 메리츠 (31 rows)
N02: 한화 (52 rows)
N03: 롯데 (35 rows)
N05: 흥국 (34 rows)
N08: 삼성 (40 rows)
N09: 현대 (27 rows)
N10: KB (38 rows)
N13: DB (30 rows)
```

---

## 5. Anomaly Detection

**Missing codes in Excel**: None
**Missing codes in Python**: None
**Mismatches**: None

**Note**: DB code was corrected from N11 → N13 in STEP NEXT-50. This audit confirms the fix is properly aligned with Excel.

---

## 6. Conclusion

**Verdict**: ✅ **PASS**

All insurer codes are correctly synchronized between:
- `pipeline/step2_canonical_mapping/canonical_mapper.py` (INSURER_CODE_MAP)
- `data/sources/mapping/담보명mapping자료.xlsx` (ins_cd column)

**No infrastructure-level code mismatches detected.**

The DB mapping issue identified in STEP NEXT-50 was an isolated incident (N11 → N13 typo), now corrected and verified.

---

## 7. Recommendation

- ✅ Proceed to Audit B (Core Coverage Smoke Test)
- No remediation required
