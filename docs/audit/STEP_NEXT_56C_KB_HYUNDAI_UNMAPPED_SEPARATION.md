# STEP NEXT-56-C: KB/HYUNDAI Unmapped Separation + Common Normalization

**Date**: 2026-01-07
**Purpose**: Separate KB/HYUNDAI unmapped into fragments vs legit variants, improve mapping via common normalization rules

---

## 🎯 Goals

1. **Diagnostic Separation**: Classify unmapped into GROUP-1 (fragments to drop) and GROUP-2 (legit variants needing Excel/normalization)
2. **Common Normalization**: Improve `normalize_coverage_name()` with insurer-agnostic rules
3. **Mapping Rate Improvement**: Target 80%+ for KB/HYUNDAI (from baseline 69%)

---

## ✅ Results Summary

### Mapping Rate Improvement

| Insurer | Before (STEP NEXT-55) | After (STEP NEXT-56-C) | Unmapped Reduction |
|---------|------------------------|-------------------------|-------------------|
| **KB** | 69.0% (13 unmapped) | **71.4% (12 unmapped)** | -1 item (-7.7%) |
| **HYUNDAI** | 69.4% (11 unmapped) | 69.4% (11 unmapped) | 0 (no change) |

**Note**: Target 80% not reached yet - remaining unmapped are primarily **Excel coverage gaps** (not normalization issues).

---

## 📊 Unmapped Diagnostic Results

### KB Unmapped (12 items total)

#### GROUP-1: Fragment/Scrap (3 items, 25%)
**Should be dropped/normalized in Step2-a:**

1. `최초1회` - STANDALONE_CLAUSE
2. `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(` - UNBALANCED_PARENS (open=2, close=1)
3. `다빈치로봇 갑상선암 및 전립선암수술비(` - UNBALANCED_PARENS (open=1, close=0)

#### GROUP-2: Legit Variant (9 items, 75%)
**Meaningful coverages needing Excel entries or normalization:**

1. `일반상해후유장해(20~100%)(기본)` - **Excel gap** (only has 3~100% variant)
2. `부정맥질환(Ⅰ49)진단비` - Excel gap
3. `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)` - Excel gap
4. `다빈치로봇 갑상선암 및 전립선암수술비(최초1회한)(갱신형)` - Excel gap
5. `표적항암약물허가치료비(3대특정암)(최초1회한)Ⅱ(갱신형)` - Excel gap
6. `표적항암약물허가치료비(림프종·백혈병 관련암)(최초1회한)Ⅱ(갱신형)` - Excel gap
7. `표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한)Ⅱ(갱신형)` - Excel gap
8. `특정항암호르몬약물허가치료비(최초1회한)Ⅱ(갱신형)` - Excel gap
9. `카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형)` - Excel gap

### HYUNDAI Unmapped (11 items total)

#### GROUP-1: Fragment/Scrap (1 item, 9.1%)
**Should be dropped/normalized in Step2-a:**

1. `로봇암수술(다빈치및레보아이\n)(갑상선암및전립선암)(최초\n1회한)(갱신형)담보` - MALFORMED_SUFFIX_1 (newline breaks)

#### GROUP-2: Legit Variant (10 items, 90.9%)
**Meaningful coverages needing Excel entries:**

1. `유사암진단Ⅱ담보` - Excel gap
2. `심혈관질환(특정Ⅰ,I49제외)진단담보` - Excel gap
3. `심혈관질환(I49)진단담보` - Excel gap
4. `심혈관질환(주요심장염증)진단담보` - Excel gap
5. `심혈관질환(특정2대)진단담보` - Excel gap
6. `심혈관질환(대동맥판막협착증)진단담보` - Excel gap
7. `심혈관질환(심근병증)진단담보` - Excel gap
8. `항암약물치료Ⅱ담보` - Excel gap
9. `질병입원일당(1-180일)담보` - Excel gap
10. `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보` - Excel gap

---

## 🛠️ Implementation

### 1. Diagnostic Tool (`tools/audit/diagnose_unmapped.py`)

**Features**:
- Deterministic fragment detection (no LLM)
- Per-insurer unmapped categorization
- JSON output for programmatic use

**Fragment Detection Rules**:
- Unclosed parentheses: `(` count != `)` count
- Standalone clauses: `최초1회`, `갱신형`, `기본` (without coverage name)
- Malformed structure: `)(갱신형)담보`, `신형)담보`
- Too short: < 3 characters
- Multi-line breaks: newlines in coverage name

**Usage**:
```bash
python tools/audit/diagnose_unmapped.py
# Output: data/scope_v3/{insurer}_step2_unmapped_diagnosis.json
```

### 2. Enhanced `normalize_coverage_name()` (canonical_mapper.py)

**New Common Rules (STEP NEXT-56-C)**:

#### Rule 1: Bracket Prefix Removal
```python
# [기본계약], [갱신형] → removed
name = re.sub(r'^\[[^\]]+\]\s*', '', name)
```

#### Rule 2: (기본) Suffix Removal
```python
# 일반상해후유장해(20~100%)(기본) → 일반상해후유장해(20~100%)
name = re.sub(r'\)\s*\(기본\)\s*$', ')', name)
name = re.sub(r'\s*\(기본\)\s*$', '', name)
```

#### Rule 3: Percent Sign Normalization
```python
# 3%~100% / 3~100% / 3~100 % / 3-100 → 3~100%
# Step 1: Normalize tilde/hyphen
name = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1~\2', name)
# Step 2: Remove spaces around %
name = re.sub(r'\s*%\s*', '%', name)
# Step 3: Remove % from first number in range
name = re.sub(r'(\d+)%~(\d+)', r'\1~\2', name)
# Step 4: Ensure % after range end
name = re.sub(r'(\d+~\d+)(?!%)\b', r'\1%', name)
```

**Example Transformations**:
```
[기본계약]일반상해후유장해(3~100%)     → 일반상해후유장해(3~100%)
일반상해후유장해(3%~100%)            → 일반상해후유장해(3~100%)
일반상해후유장해(20~100%)(기본)       → 일반상해후유장해(20~100%)
일반상해후유장해(3-100)              → 일반상해후유장해(3~100%)
```

**Mapping Success Example**:
- **KB proposal**: `5. 일반상해후유장해(3%~100%)`
- **Step2-a normalized**: `일반상해후유장해(3%~100%)`
- **Step2-b normalized**: `일반상해후유장해(3~100%)`
- **Excel N10**: `[기본계약]일반상해후유장해(3~100%)`
- **Excel normalized**: `일반상해후유장해(3~100%)`
- **Result**: ✅ **MATCHED** via `normalized` method (confidence 0.9)

---

## 🔒 Constitutional Compliance

### ✅ Enforced Rules

1. **NO insurer-specific branching**: All normalization rules apply to ALL insurers
2. **NO LLM usage**: Deterministic pattern matching only
3. **NO SSOT violation**: Excel remains single source of truth (no arbitrary mappings)
4. **NO Step1 manual editing**: Fragment issues addressed in Step2-a/Step2-b only

### ❌ Forbidden Actions

- ❌ Adding `if insurer == 'KB':` branches
- ❌ Using LLM to "guess" canonical codes
- ❌ Manually editing Step1 output files
- ❌ Hardcoding coverage code mappings outside Excel

---

## 📈 Success Metrics

### DoD Verification

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| GROUP-1 (fragments) in unmapped | 0% | KB: 25%, HYUNDAI: 9.1% | ⚠️ **Partial** (Step2-a needs fragment drops) |
| Mapping rate (KB) | 80%+ | 71.4% | ⚠️ **Partial** (Excel gaps remain) |
| Mapping rate (HYUNDAI) | 80%+ | 69.4% | ⚠️ **Partial** (Excel gaps remain) |
| Insurer-specific branching | 0 | 0 | ✅ **PASS** |
| LLM usage | 0 | 0 | ✅ **PASS** |

### Key Insights

1. **Normalization worked**: KB item #5 `일반상해후유장해(3%~100%)` now maps successfully
2. **Fragment detection accurate**: KB has 3 fragments (25%), HYUNDAI has 1 fragment (9.1%)
3. **Excel is bottleneck**: Most GROUP-2 unmapped are legitimate coverages missing from Excel
4. **Common rules sufficient**: NO insurer-specific rules needed

---

## 🚀 Next Steps (Outside Scope)

### Step2-a Enhancement (Fragment Removal)
Target: Eliminate GROUP-1 fragments BEFORE Step2-b

**Candidates for Step2-a Drop**:
- Standalone clauses: `최초1회`, `갱신형`
- Unclosed parentheses: `...(갑상선암...제외)(`
- Malformed suffix: `...)(갱신형)담보`

### Excel Coverage Addition (Manual)
Target: Add GROUP-2 legit variants to Excel

**KB High-Priority Additions** (신정원 approval required):
- `일반상해후유장해(20~100%)` (variant of existing 3~100%)
- `부정맥질환(Ⅰ49)진단비`
- `다빈치로봇 암수술비...` (2 variants)
- `표적항암약물허가치료비...` (3 variants)
- `카티(CAR-T)항암약물허가치료비`

**HYUNDAI High-Priority Additions**:
- `유사암진단Ⅱ담보`
- `심혈관질환...` (6 variants)
- `항암약물치료Ⅱ담보`
- `질병입원일당(1-180일)담보`

---

## 📎 Artifacts

### Code Changes
- `pipeline/step2_canonical_mapping/canonical_mapper.py` (lines 160-193): Enhanced normalization
- `tools/audit/diagnose_unmapped.py` (NEW): Diagnostic tool

### Output Files
- `data/scope_v3/kb_step2_unmapped_diagnosis.json`: KB diagnostic results
- `data/scope_v3/hyundai_step2_unmapped_diagnosis.json`: HYUNDAI diagnostic results

### Test Evidence
```bash
# Before STEP NEXT-56-C
KB: 69.0% mapped (13 unmapped)
HYUNDAI: 69.4% mapped (11 unmapped)

# After STEP NEXT-56-C
KB: 71.4% mapped (12 unmapped)  # +2.4% improvement
HYUNDAI: 69.4% mapped (11 unmapped)  # No change (Excel gaps)
```

---

## 🔍 Verification Commands

```bash
# Run diagnostic
python tools/audit/diagnose_unmapped.py

# Re-run Step2-b
python -m pipeline.step2_canonical_mapping.run

# Check mapping rates
grep "mapped" data/scope_v3/kb_step2_mapping_report.jsonl | wc -l
grep "unmapped" data/scope_v3/kb_step2_mapping_report.jsonl | wc -l

# Verify no insurer branching
grep -E "if.*insurer.*==" pipeline/step2_canonical_mapping/canonical_mapper.py
# (Should return NO matches)
```

---

## ✅ Conclusion

STEP NEXT-56-C successfully:
1. ✅ Separated fragments (GROUP-1) from legit variants (GROUP-2)
2. ✅ Improved KB mapping rate (+2.4%, from 69.0% to 71.4%)
3. ✅ Added common normalization rules (NO insurer branching)
4. ✅ Created diagnostic tool for future debugging

**Remaining Work** (outside scope):
- Step2-a fragment drop logic (eliminate GROUP-1 before Step2-b)
- Excel coverage additions (신정원 approval required for GROUP-2)

**80% mapping target NOT reached** - root cause is Excel coverage gaps, not normalization issues.
