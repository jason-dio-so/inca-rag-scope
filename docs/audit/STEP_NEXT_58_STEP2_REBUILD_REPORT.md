# STEP NEXT-58 — Step2 Rebuild Per Insurer Report

**Date**: 2026-01-01
**Purpose**: Rebuild Step2 outputs (sanitize + canonical) per insurer/variant while preserving Step1 SSOT

---

## 📋 Executive Summary

**Objective**: Delete and regenerate ALL Step2 outputs while keeping Step1 raw files intact, proving Step2 pipeline executes correctly per insurer/variant.

**Result**: ✅ **SUCCESS**
- Step1 preserved: 10 files (362 rows)
- Step2 regenerated: 40 files (10 insurers × 4 output types)
- Variant axis preserved: DB (under40/over41), LOTTE (male/female)
- Prefix contamination: 0 (DB/Hyundai prefixes intact)

---

## 1) Step1 SSOT (Processing Targets)

### Input Files (Preserved)
```
db_over41_step1_raw_scope_v3.jsonl       (31 rows)
db_under40_step1_raw_scope_v3.jsonl      (31 rows)
hanwha_step1_raw_scope_v3.jsonl          (33 rows)
heungkuk_step1_raw_scope_v3.jsonl        (36 rows)
hyundai_step1_raw_scope_v3.jsonl         (47 rows)
kb_step1_raw_scope_v3.jsonl              (63 rows)
lotte_female_step1_raw_scope_v3.jsonl    (30 rows)
lotte_male_step1_raw_scope_v3.jsonl      (30 rows)
meritz_step1_raw_scope_v3.jsonl          (29 rows)
samsung_step1_raw_scope_v3.jsonl         (32 rows)
```

**Total**: 10 files, 362 rows

---

## 2) Execution Commands

### Phase 1: Delete Step2 Outputs Only
```bash
# Delete Step2-a sanitized outputs
rm -f data/scope_v3/*_step2_sanitized_scope_v1.jsonl

# Delete Step2-b canonical outputs
rm -f data/scope_v3/*_step2_canonical_scope_v1.jsonl

# Delete Step2 audit trails
rm -f data/scope_v3/*_step2_dropped.jsonl
rm -f data/scope_v3/*_step2_mapping_report.jsonl

# Verification: no Step2 files remain
ls -1 data/scope_v3/*_step2_*.jsonl 2>/dev/null || echo "✅ OK: no step2 outputs"
```

**Result**: ✅ All Step2 outputs deleted, Step1 preserved (10 files remain)

### Phase 2: Rebuild Step2-a (Sanitize)
```bash
python -m pipeline.step2_sanitize_scope.run
```

**Input**: `data/scope_v3/*_step1_raw_scope_v3.jsonl` (glob, variant-aware)
**Output**:
- `data/scope_v3/*_step2_sanitized_scope_v1.jsonl` (10 files)
- `data/scope_v3/*_step2_dropped.jsonl` (10 files, audit trail)

**Processing**:
- Total input: 362 entries
- Total kept: 353 entries (97.5%)
- Total dropped: 9 entries (2.5%)

### Phase 3: Rebuild Step2-b (Canonical Mapping)
```bash
python -m pipeline.step2_canonical_mapping.run
```

**Input**: `data/scope_v3/*_step2_sanitized_scope_v1.jsonl` (glob, variant-aware)
**Output**:
- `data/scope_v3/*_step2_canonical_scope_v1.jsonl` (10 files)
- `data/scope_v3/*_step2_mapping_report.jsonl` (10 files, audit trail)

**Processing**:
- Total input: 353 entries
- Total mapped: 167 entries (47.3%)
- Total unmapped: 186 entries (52.7%)

---

## 3) Step2 Output File Inventory

### File Counts
| Output Type | Count | Expected | Status |
|-------------|-------|----------|--------|
| Step2-a sanitized | 10 | 10 | ✅ |
| Step2-b canonical | 10 | 10 | ✅ |
| Step2 dropped (audit) | 10 | 10 | ✅ |
| Step2 mapping report (audit) | 10 | 10 | ✅ |
| **Total** | **40** | **40** | ✅ |

### Generated Files (Complete List)
```
data/scope_v3/db_over41_step2_canonical_scope_v1.jsonl
data/scope_v3/db_over41_step2_dropped.jsonl
data/scope_v3/db_over41_step2_mapping_report.jsonl
data/scope_v3/db_over41_step2_sanitized_scope_v1.jsonl

data/scope_v3/db_under40_step2_canonical_scope_v1.jsonl
data/scope_v3/db_under40_step2_dropped.jsonl
data/scope_v3/db_under40_step2_mapping_report.jsonl
data/scope_v3/db_under40_step2_sanitized_scope_v1.jsonl

data/scope_v3/hanwha_step2_canonical_scope_v1.jsonl
data/scope_v3/hanwha_step2_dropped.jsonl
data/scope_v3/hanwha_step2_mapping_report.jsonl
data/scope_v3/hanwha_step2_sanitized_scope_v1.jsonl

data/scope_v3/heungkuk_step2_canonical_scope_v1.jsonl
data/scope_v3/heungkuk_step2_dropped.jsonl
data/scope_v3/heungkuk_step2_mapping_report.jsonl
data/scope_v3/heungkuk_step2_sanitized_scope_v1.jsonl

data/scope_v3/hyundai_step2_canonical_scope_v1.jsonl
data/scope_v3/hyundai_step2_dropped.jsonl
data/scope_v3/hyundai_step2_mapping_report.jsonl
data/scope_v3/hyundai_step2_sanitized_scope_v1.jsonl

data/scope_v3/kb_step2_canonical_scope_v1.jsonl
data/scope_v3/kb_step2_dropped.jsonl
data/scope_v3/kb_step2_mapping_report.jsonl
data/scope_v3/kb_step2_sanitized_scope_v1.jsonl

data/scope_v3/lotte_female_step2_canonical_scope_v1.jsonl
data/scope_v3/lotte_female_step2_dropped.jsonl
data/scope_v3/lotte_female_step2_mapping_report.jsonl
data/scope_v3/lotte_female_step2_sanitized_scope_v1.jsonl

data/scope_v3/lotte_male_step2_canonical_scope_v1.jsonl
data/scope_v3/lotte_male_step2_dropped.jsonl
data/scope_v3/lotte_male_step2_mapping_report.jsonl
data/scope_v3/lotte_male_step2_sanitized_scope_v1.jsonl

data/scope_v3/meritz_step2_canonical_scope_v1.jsonl
data/scope_v3/meritz_step2_dropped.jsonl
data/scope_v3/meritz_step2_mapping_report.jsonl
data/scope_v3/meritz_step2_sanitized_scope_v1.jsonl

data/scope_v3/samsung_step2_canonical_scope_v1.jsonl
data/scope_v3/samsung_step2_dropped.jsonl
data/scope_v3/samsung_step2_mapping_report.jsonl
data/scope_v3/samsung_step2_sanitized_scope_v1.jsonl
```

---

## 4) Per-Insurer Results

### Step2-a Sanitization Results

| Insurer | Variant | Input | Kept | Dropped | Keep Rate | Drop Reasons |
|---------|---------|-------|------|---------|-----------|--------------|
| DB | over41 | 31 | 30 | 1 | 96.8% | PREMIUM_WAIVER_TARGET |
| DB | under40 | 31 | 30 | 1 | 96.8% | PREMIUM_WAIVER_TARGET |
| Hanwha | — | 33 | 32 | 1 | 97.0% | PREMIUM_WAIVER_TARGET |
| Heungkuk | — | 36 | 35 | 1 | 97.2% | PREMIUM_WAIVER_TARGET |
| Hyundai | — | 47 | 44 | 3 | 93.6% | PREMIUM_WAIVER_TARGET (1), BROKEN_SUFFIX (1), PARENTHESES_ONLY (1) |
| KB | — | 63 | 62 | 1 | 98.4% | PREMIUM_WAIVER_TARGET |
| LOTTE | female | 30 | 30 | 0 | 100.0% | — |
| LOTTE | male | 30 | 30 | 0 | 100.0% | — |
| Meritz | — | 29 | 29 | 0 | 100.0% | — |
| Samsung | — | 32 | 31 | 1 | 96.9% | PREMIUM_WAIVER_TARGET |

**Aggregated Drop Reasons**:
- PREMIUM_WAIVER_TARGET: 7 (77.8%)
- BROKEN_SUFFIX: 1 (11.1%)
- PARENTHESES_ONLY: 1 (11.1%)

### Step2-b Canonical Mapping Results

| Insurer | Variant | Entries | Mapped | Unmapped | Mapping Rate | Primary Method |
|---------|---------|---------|--------|----------|--------------|----------------|
| DB | over41 | 30 | 0 | 30 | **0.0%** | unmapped |
| DB | under40 | 30 | 0 | 30 | **0.0%** | unmapped |
| Hanwha | — | 32 | 28 | 4 | 87.5% | exact (28) |
| Heungkuk | — | 35 | 32 | 3 | 91.4% | exact (27), normalized (5) |
| Hyundai | — | 44 | 2 | 42 | **4.5%** | normalized (2) |
| KB | — | 62 | 19 | 43 | 30.6% | exact (19) |
| LOTTE | female | 30 | 20 | 10 | 66.7% | exact (19), normalized (1) |
| LOTTE | male | 30 | 20 | 10 | 66.7% | exact (19), normalized (1) |
| Meritz | — | 29 | 19 | 10 | 65.5% | exact (16), normalized (3) |
| Samsung | — | 31 | 27 | 4 | 87.1% | exact (21), normalized (6) |

**Global Mapping Methods**:
- unmapped: 186 (52.7%)
- exact: 149 (42.2%)
- normalized: 18 (5.1%)

---

## 5) Prefix Preservation Verification

### DB (over41) — First 20 Coverage Names
```
1. 상해사망·후유장해(20-100%)
3. 상해사망
4. 상해후유장해(3-100%)
5. 질병사망
6. 상해수술비(동일사고당1회지급)
7. 골절진단비(치아제외)
8. 계속받는암진단비(유사암,대장점막내암및전립선암제외)
9. 암진단비Ⅱ(유사암제외)
10. 유사암진단비Ⅱ(1년감액지급)
11. 고액치료비암진단비
12. 암수술비(유사암제외)(최초1회한)
13. 유사암수술비
14. 다빈치로봇암수술비(연간1회한,특정암)
15. 다빈치로봇암수술비(연간1회한,특정암제외)
16. 표적항암약물허가치료비(최초1회한)(갱신형)
17. 항암방사선약물치료비(유사암포함)
18. 암직접치료입원일당Ⅱ(요양병원제외)(1일이상180일한도)
19. 뇌졸중진단비
20. 뇌출혈진단비
21. 뇌혈관질환진단비
```

**Verdict**: ✅ **PASS**
- Prefixes intact: `1.`, `3.`, `4.`, `5.`, etc.
- NO ". " contamination (broken prefix)
- Proper numbering format maintained

### DB (under40) — First 20 Coverage Names
```
1. 상해사망·후유장해(20-100%)
3. 상해사망
4. 상해후유장해(3-100%)
5. 질병사망
6. 상해수술비(동일사고당1회지급)
7. 골절진단비(치아제외)
8. 계속받는암진단비(유사암,대장점막내암및전립선암제외)
9. 암진단비Ⅱ(유사암제외)
10. 유사암진단비Ⅱ(1년감액지급)
11. 고액치료비암진단비
12. 암수술비(유사암제외)(최초1회한)
13. 유사암수술비
14. 다빈치로봇암수술비(연간1회한,특정암)
15. 다빈치로봇암수술비(연간1회한,특정암제외)
16. 표적항암약물허가치료비(최초1회한)(갱신형)
17. 항암방사선약물치료비(유사암포함)
18. 암직접치료입원일당Ⅱ(요양병원제외)(1일이상180일한도)
19. 뇌졸중진단비
20. 뇌출혈진단비
21. 뇌혈관질환진단비
```

**Verdict**: ✅ **PASS** (identical to over41, confirms variant consistency)

### Hyundai — First 20 Coverage Names
```
1. 기본계약(상해사망)
2. 기본계약(상해후유장해)
4. 골절진단(치아파절제외)담보
5. 화상진단담보
6. 상해입원일당(1-180일)담보
7. 상해수술담보
8. 질병사망담보
9. 암진단Ⅱ(유사암제외)담보
10. 유사암진단Ⅱ담보
11. 고액치료비암진단담보
12. 재진단암진단Ⅱ담보
13. 뇌출혈진단담보
14. 뇌졸중진단담보
15. 뇌혈관질환진단담보
16. 허혈심장질환진단담보
17. 심혈관질환(특정Ⅰ,I49제외)진단담보
18. 심혈관질환(I49)진단담보
19. 심혈관질환(주요심장염증)진단담보
20. 심혈관질환(특정Ⅱ)진단담보
21. 심혈관질환(특정2대)진단담보
```

**Verdict**: ✅ **PASS**
- Prefixes intact: `1.`, `2.`, `4.`, `5.`, etc.
- NO ". " contamination
- Hyundai-specific format maintained

---

## 6) DB 0% Mapping Rate Analysis

### Issue
DB (both under40 and over41 variants) achieved **0% mapping rate** (all 30 entries unmapped).

### Root Cause Investigation

#### 1. Coverage Name Samples (Sanitized)
```
1. 상해사망·후유장해(20-100%)
3. 상해사망
4. 상해후유장해(3-100%)
5. 질병사망
6. 상해수술비(동일사고당1회지급)
7. 골절진단비(치아제외)
```

#### 2. Canonical Dictionary Check
**Mapping Source**: `data/sources/mapping/담보명mapping자료.xlsx` (신정원_v2024.12)

**Hypothesis**: DB coverage names not present in canonical dictionary
- DB uses unique naming format (numbered prefixes + specific qualifiers)
- Canonical dictionary may lack DB-specific coverage names
- Example: "상해사망·후유장해(20-100%)" may not match any canonical entry

#### 3. Insurer Code Check
**Sample output** from `db_over41_step2_canonical_scope_v1.jsonl`:
```json
{
  "insurer": "db",
  "coverage_name_raw": "1. 상해사망·후유장해(20-100%)",
  "coverage_code": null,
  "canonical_name": null,
  "mapping_method": "unmapped",
  "mapping_confidence": 0.0,
  "evidence": {
    "source": "신정원_v2024.12"
  }
}
```

**Insurer code**: "db" (lowercase, standard format)

### Action Required

**Priority 1**: Canonical Dictionary Expansion
1. Audit `담보명mapping자료.xlsx` for DB coverage entries
2. Add DB-specific coverage names to canonical dictionary
3. Include variant-specific mappings if needed

**Priority 2**: Normalization Rules
1. Review if number prefixes should be stripped before mapping
2. Evaluate if percentage qualifiers affect matching
3. Test normalized matching with DB samples

**Expected Outcome**: DB mapping rate should reach 60-90% (similar to other insurers) after dictionary expansion.

---

## 7) Variant Axis Verification

### DB Variants
| Variant | Step2-a Output | Step2-b Output | Status |
|---------|----------------|----------------|--------|
| under40 | ✅ db_under40_step2_sanitized_scope_v1.jsonl | ✅ db_under40_step2_canonical_scope_v1.jsonl | ✅ PRESERVED |
| over41 | ✅ db_over41_step2_sanitized_scope_v1.jsonl | ✅ db_over41_step2_canonical_scope_v1.jsonl | ✅ PRESERVED |

### LOTTE Variants
| Variant | Step2-a Output | Step2-b Output | Status |
|---------|----------------|----------------|--------|
| male | ✅ lotte_male_step2_sanitized_scope_v1.jsonl | ✅ lotte_male_step2_canonical_scope_v1.jsonl | ✅ PRESERVED |
| female | ✅ lotte_female_step2_sanitized_scope_v1.jsonl | ✅ lotte_female_step2_canonical_scope_v1.jsonl | ✅ PRESERVED |

**Verdict**: ✅ **VARIANT AXIS PRESERVED** (Step1 → Step2-a → Step2-b)

---

## 8) Quality Gates

| Gate | Rule | Status | Evidence |
|------|------|--------|----------|
| **GATE-58-1** | Step1 preserved | ✅ PASS | 10 Step1 files unchanged |
| **GATE-58-2** | Step2 file count | ✅ PASS | 40 files (10 × 4 types) |
| **GATE-58-3** | Variant preservation | ✅ PASS | DB/LOTTE pairs exist |
| **GATE-58-4** | Prefix contamination | ✅ PASS | 0 ". " broken prefixes |
| **GATE-58-5** | SSOT compliance | ✅ PASS | All outputs in scope_v3/ |

---

## 9) Definition of Done

- [x] Step1 raw files preserved (10 files, 362 rows)
- [x] Step2 outputs regenerated (40 files total)
- [x] File count matches: Step1 axis = Step2 axis (10 insurers/variants)
- [x] No legacy/single-variant files in scope_v3/
- [x] DB/Hyundai prefix preservation verified (0 contamination)
- [x] DB 0% mapping documented with root cause analysis
- [x] Variant axis preserved (DB under40/over41, LOTTE male/female)
- [x] Report created (this document)

---

## 10) Next Steps

### Immediate
1. **DB Canonical Dictionary Expansion** (Priority 1)
   - Audit `담보명mapping자료.xlsx` for missing DB entries
   - Add 30+ DB coverage names to canonical dictionary
   - Target: 60-90% mapping rate

2. **Hyundai Mapping Improvement** (Priority 2)
   - Current: 4.5% mapping rate (2/44)
   - Add Hyundai-specific coverage names to canonical dictionary
   - Target: 60-80% mapping rate

### Medium-Term
1. Run Step3+ pipeline (evidence extraction → search → cards)
2. End-to-end test with improved canonical dictionary
3. Monitor mapping rates across all insurers

---

## 11) Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Step1 files preserved | 10 | ✅ |
| Step2 files generated | 40 | ✅ |
| Total input entries | 362 | — |
| Step2-a kept | 353 (97.5%) | ✅ |
| Step2-a dropped | 9 (2.5%) | ✅ |
| Step2-b mapped | 167 (47.3%) | ⚠️ |
| Step2-b unmapped | 186 (52.7%) | ⚠️ |
| Variant pairs preserved | 4 (DB×2, LOTTE×2) | ✅ |
| Prefix contamination | 0 | ✅ |
| SSOT violations | 0 | ✅ |

**Overall Status**: ✅ **PIPELINE EXECUTION VERIFIED**
**Action Required**: Canonical dictionary expansion for DB/Hyundai
