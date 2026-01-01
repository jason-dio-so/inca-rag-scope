# STEP NEXT-47: Step2-b Canonical Mapping

## Summary

**Status**: ✅ COMPLETE

**Purpose**: Map sanitized coverage names to 신정원 unified coverage codes (deterministic only).

---

## Constitutional Rules (Enforced)

### 1. 신정원 통일코드 is Absolute Reference
- **Source**: `data/sources/mapping/담보명mapping자료.xlsx` (신정원 v2024.12)
- **Coverage codes**: ONLY from this file
- **NO arbitrary generation / inference / expansion**

### 2. Deterministic Only
- ✅ Exact match
- ✅ Normalized match (suffix/prefix/whitespace removal)
- ✅ Alias table (if defined)
- ❌ LLM / embedding / similarity scoring
- ❌ "Looks similar" guessing

### 3. Unmapped When Ambiguous
- If no clear match → `unmapped`
- Confidence thresholds:
  - exact: 1.0
  - normalized: 0.9
  - unmapped: 0.0

### 4. NO Row Reduction (Anti-Contamination Gate)
- Input count MUST equal output count
- Hard gate: RuntimeError if rows are lost
- Sanitization is Step2-a's job, NOT Step2-b's

---

## Implementation

### Files Created
```
pipeline/step2_canonical_mapping/
├── __init__.py          # Module docstring
├── canonical_mapper.py  # Core mapping logic
└── run.py               # CLI runner
```

### Mapping Methods

**Method 1: Exact Match** (confidence: 1.0)
```python
if coverage_name_raw == canonical_name:
    return canonical_code
```

**Method 2: Normalized Match** (confidence: 0.9)
```python
normalized = normalize_coverage_name(coverage_name_raw)
# Removes:
# - Whitespace variations
# - Suffix markers: Ⅱ, (갱신형), (1년50%), (1회한), etc
# - Prefix markers: [갱신형]
# - Trailing keywords: 담보, 보장
# - Parentheses content variations
```

**Method 3: Unmapped** (confidence: 0.0)
```python
if no_match_found:
    return None, None, 'unmapped', 0.0
```

---

## Execution Results (All Insurers)

### Global Statistics
```
Total input: 335 entries
Total mapped: 173 entries (51.6%)
Total unmapped: 162 entries (48.4%)

Mapping methods:
  - unmapped: 162 (48.4%)
  - exact: 141 (42.1%)
  - normalized: 32 (9.6%)
```

### Per-Insurer Mapping Rates
| Insurer  | Input | Mapped | Unmapped | Rate  | Note |
|----------|-------|--------|----------|-------|------|
| heungkuk | 22    | 20     | 2        | 90.9% | ✅ High coverage |
| samsung  | 61    | 52     | 9        | 85.2% | ✅ High coverage |
| hanwha   | 34    | 27     | 7        | 79.4% | ✅ Good coverage |
| hyundai  | 34    | 23     | 11       | 67.6% | ⚠️ Moderate |
| kb       | 36    | 24     | 12       | 66.7% | ⚠️ Moderate |
| lotte    | 64    | 21     | 43       | 32.8% | ⚠️ Low (gender variants) |
| meritz   | 36    | 6      | 30       | 16.7% | ⚠️ Low |
| db       | 48    | 0      | 48       | 0.0%  | ❌ No canonical mapping (ins_cd='N11' has 0 entries) |

---

## Unmapped Coverage Analysis

### Samsung (9 unmapped)
- `골절 진단비(치아파절(깨짐, 부러짐) 제외)` → Not in canonical
- `2대주요기관질병 관혈수술비Ⅱ(1년50%)` → Not in canonical
- `2대주요기관질병 비관혈수술비Ⅱ(1년50%)` → Not in canonical
- `장해/장애` → Not in canonical
- `간병/사망` → Not in canonical

### Lotte (43 unmapped)
- High unmapped rate due to **gender-specific variants** (male/female)
- Many coverage names not in canonical mapping
- Examples:
  - `일반암수술비(1회한)`
  - `다빈치로봇암수술비(갑상선암및전립선암제외)(최초1회 한)(갱신형)`
  - `표적항암약물허가치료비(유방암및비뇨생식기암)(1회 한)(갱신형)`

### Hyundai (11 unmapped)
- Fragment patterns from Step1 (to be handled in Step2-a sanitization)
- Coverage names not in canonical mapping

### DB (48 unmapped - 100%)
- **Root cause**: `ins_cd='N11'` has 0 entries in canonical mapping Excel
- **Action required**: Add DB canonical mapping to `담보명mapping자료.xlsx`

---

## Gates (All Passed ✅)

### Gate 1: Reproducibility
- ✅ Deterministic mapping (no randomness)
- ✅ Same input → Same output

### Gate 2: Anti-Reduction (NO row loss)
- ✅ All insurers: input count == output count
- ✅ No rows dropped during mapping

### Gate 3: Unmapped Visibility
- ✅ Unmapped rate reported per insurer
- ✅ Unmapped entries preserved in output JSONL
- ✅ Mapping reports generated (`*_step2_mapping_report.jsonl`)

---

## Output Schema

### Canonical Scope JSONL
```jsonl
{
  "insurer": "samsung",
  "coverage_name_raw": "암 진단비(유사암 제외)",
  "coverage_code": "A4200_1",
  "canonical_name": "암진단비(유사암제외)",
  "mapping_method": "normalized",
  "mapping_confidence": 0.9,
  "evidence": {
    "source": "신정원_v2024.12",
    "matched_term": "암진단비(유사암제외)"
  },
  "sanitized": true,
  "drop_reason": null,
  "proposal_facts": { ... }
}
```

### Unmapped Entry
```jsonl
{
  "insurer": "samsung",
  "coverage_name_raw": "장해/장애",
  "coverage_code": null,
  "canonical_name": null,
  "mapping_method": "unmapped",
  "mapping_confidence": 0.0,
  "evidence": {
    "source": "신정원_v2024.12"
  },
  ...
}
```

---

## Usage

### Single Insurer
```bash
python -m pipeline.step2_canonical_mapping.run --insurer samsung
```

### All Insurers
```bash
python -m pipeline.step2_canonical_mapping.run --all
```

### Output Files
- Canonical scope: `data/scope/{insurer}_step2_canonical_scope_v1.jsonl`
- Mapping report: `data/scope/{insurer}_step2_mapping_report.jsonl`

---

## Next Steps

### Immediate Actions
1. **DB Canonical Mapping**: Add DB (ins_cd='N11') entries to `담보명mapping자료.xlsx`
2. **Lotte Canonical Mapping**: Add gender-specific coverage variants to canonical mapping
3. **Meritz Canonical Mapping**: Review and add missing Meritz coverages

### Future Enhancements
1. **Alias Table**: Add known aliases for common coverage name variations
2. **Normalization Rules**: Expand normalization patterns based on unmapped analysis
3. **Mapping Audit**: Create dashboard for unmapped coverage trends

---

## 금지 사항 (Enforced)

- ❌ Step1 / Step2-a modification
- ❌ pdfplumber / PyMuPDF usage
- ❌ LLM / embedding / similarity scoring
- ❌ Arbitrary code generation
- ❌ "개수 맞추기" (forcing mappings to match counts)

---

## Definition of Done (✅ ALL COMPLETE)

- ✅ `step2_canonical_scope_v1.jsonl` generated for all insurers
- ✅ All rows have `coverage_code` or `unmapped` status
- ✅ Samsung/Hyundai/Lotte counts preserved (no reduction)
- ✅ Unmapped list clear and documented
- ✅ Documentation complete (this file)
- ✅ All gates passed
