# STEP NEXT-60 — Excel Patch List (Dictionary Gap Only)

**Date**: 2026-01-01
**Purpose**: Minimal canonical dictionary enhancement for DB/Hyundai/KB
**Scope**: Focus insurers only (DoD targets)
**Method**: Manual Excel edit (`data/sources/mapping/담보명mapping자료.xlsx`)

---

## Summary

- **Total patches**: 3 entries
- **Scope**: DB (1), Hyundai (0), KB (2)
- **Impact**:
  - DB: 96.7% → **100%** (29/30 → 30/30)
  - KB: 69.0% → **73.8%** (29/42 → 31/42)
  - Hyundai: 59.1% (no patches - broken fragments only)

---

## Constitutional Compliance Check

✅ **PASS** - All patches meet strict criteria:
1. Clear coverage concept (not fragments)
2. Core coverage used across multiple insurers
3. Already normalized by Step2-a
4. Classified as dictionary gap (not extraction error)

❌ **REJECTED**:
- Broken fragments: `(갱신형)담보`, `담보명`, `5`, `남 자`, `한)(갱신형)`, etc.
- Conditional phrases: `최초1회한`, `연간1회한`, `요양병원제외`, etc.
- Table headers/noise: `보험료 비교(예시)`, `대표계약 기준 : ...`
- Product-specific complex terms: `다빈치로봇`, `CAR-T`, `표적항암약물...`

---

## Patches

### DB (N13) — 1 entry

**Purpose**: Close 3.3% gap (1/30 unmapped) → **100% DoD target**

| coverage_name_normalized | canonical_code | canonical_name | 근거 |
|---|---|---|---|
| 상해사망·후유장해(20-100%) | A3399 | 상해사망·후유장해 | DB over41/under40 공통 unmapped, combined death/disability coverage |

**Rationale**:
- Both DB variants (over41, under40) have same unmapped coverage
- Combined death/disability benefit with percentage range
- Not a fragment - legitimate core coverage
- Use A3399 (combined category) or map to A1300+A3300_1 combination

**Expected Impact**:
- DB over41: 29/30 → **30/30 (100%)**
- DB under40: 29/30 → **30/30 (100%)**

---

### Hyundai (N09) — 0 entries

**Decision**: **NO patches for Hyundai in this STEP**

**Rationale**:
- Unmapped analysis (18 total):
  - **11 broken fragments** (61%): `(갱신형)담보`, `담보명`, `5`, `남 자`, `)담보`, `표적항암약물허가치료(갱신형` (truncated), etc.
  - **4 too specific** (22%): `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보`, conditional cardiovascular variants
  - **2 legitimate** (11%): `유사암진단Ⅱ담보`, `질병입원일당(1-180일)담보`
  - **1 noise**: `보 험 가 격 지 수 (%)`

**Why no patches**:
1. Hyundai already has **기본계약(상해사망)** and **기본계약(상해후유장해)** mapped in Excel (confirmed above)
2. The 2 legitimate candidates (`유사암진단Ⅱ담보`, `질병입원일당(1-180일)담보`) are:
   - Version variants (Ⅱ) - requires business validation
   - Conditional (1-180일) - borderline for minimal patch criteria
3. **61% of gap is broken fragments** → this is a **Step1 extraction quality issue**, not dictionary gap
4. Adding 2 patches would only improve to 63.6% (26→28/44), still far from 75% DoD target

**Conclusion**:
- Hyundai gap is **NOT a dictionary problem**
- Defer to future STEP for Step1 extraction quality improvement
- Accept 59.1% mapping rate for this STEP

---

### KB (N10) — 2 entries

**Purpose**: Improve from 69.0% to 73.8% (29/42 → 31/42)

| coverage_name_normalized | canonical_code | canonical_name | 근거 |
|---|---|---|---|
| 일반상해후유장해(3%~100%) | A3300_1 | 상해후유장해(3-100%) | KB core disability coverage, standard 3-100% range |
| 일반상해후유장해(20~100%)(기본) | A3300_1 | 상해후유장해(20-100%) | KB basic contract disability, standard 20-100% range |

**Rationale**:
- Both are core general accident disability coverages
- Excel already has `[기본계약]일반상해후유장해(3~100%)` mapped to A3300_1
- These are coverage name variants (different percentage ranges)
- NOT fragments, NOT conditional (percentage range is coverage specification, not payment condition)
- KB already has `일반상해사망(기본)` mapped in Excel → no need to add

**Rejected KB candidates**:
- `부정맥질환(Ⅰ49)진단비`: Too specific (ICD code), requires business validation
- `최초1회`: Fragment (incomplete)
- `다빈치로봇 ...`: Product-specific (robotic surgery), too specialized
- `표적항암약물허가치료비...`: Multiple conditions chained (최초1회한)(갱신형)
- `카티(CAR-T)항암약물허가치료비`: Experimental therapy (CAR-T), too specialized

**Expected Impact**:
- KB: 29/42 → **31/42 (73.8%)**
- ⚠️ Still short of 75% DoD target by 1.2% (need 1 more mapping)

---

## Exclusions (Intentional Non-Patches)

### Broken Fragments (Step1 Extraction Issue)
**Total**: ~42 coverages across all insurers

Examples:
- `(갱신형)담보` (Hyundai, 4 occurrences)
- `담보명` (Hyundai, 2)
- `한)(갱신형)` (Lotte f/m, 3 each)
- `형)` (Lotte f/m, 2 each)
- `수술` (Meritz, 3)
- `골절/화상` (Meritz, 2)
- `장해/장애` (Samsung, 2)
- `5`, `남 자`, `보 험 가 격 지 수 (%)` (Hyundai table headers/noise)

**Reason**: These are extraction errors, not dictionary gaps. Requires Step1 quality improvement.

---

### Conditional/Too Specific Phrases
**Total**: ~21 coverages

Examples:
- `암(갑상선암및전립선암제외)다빈치로봇수술비(1회한)(갱신형)` (Hanwha)
- `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보` (Hyundai)
- `카티(CAR-T)항암약물허가치료비(연간1회한)(갱신형)` (KB)
- `표적항암약물허가치료비(3대특정암 및 림프종·백혈병 관련암 제외)(최초1회한) Ⅱ(갱신형)` (KB)
- `다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)` (KB)
- `[갱신형]표적항암약물허가치료비Ⅱ(갱신형_10년)` (Heungkuk)

**Reason**: Product design complexity. Too many conditions chained together. Not core coverage.

---

### Table Headers / Noise
Examples:
- `보험료 비교(예시)` (Meritz)
- `대표계약 기준 : 남자40세,20년납,100세만기,월납,일반상해80%이상후유장해[기본계약] 5,000만원, 일반상해사망 5,000만원, 질병사망 5,000만원` (Meritz, 67 chars)
- `질병사망 1,` (Hanwha - fragment with trailing comma)

**Reason**: Not coverage names - extraction noise from proposal PDF layout.

---

### Borderline Cases (Business Validation Required)

Legitimate but excluded for "minimal patch" criteria:

1. **Hanwha**:
   - `4대유사암진단비`: Quasi-cancer (4 types) - requires validation
   - `상해후유장해(3-100%)`: Already covered by normalized mapping

2. **Heungkuk**:
   - `일반상해후유장해(80%이상)`: Threshold variant - requires validation

3. **Lotte** (f/m):
   - `뇌경색증(I63) 혈전용해치료비`: Specific treatment (thrombolysis) - requires validation
   - `급성심근경색증(I21) 혈전용해치료비`: Specific treatment - requires validation
   - `허혈성심장질환진단비`: Ischemic heart disease - already in some insurers

4. **Meritz**:
   - `일반상해80%이상후유장해[기본계약]`: Already covered by normalized mapping

5. **Samsung**:
   - `골절 진단비(치아파절(깨짐, 부러짐) 제외)`: Nested exclusions - complex

**Reason**: These require business validation to confirm they map to existing canonical codes vs. need new codes. Defer to future STEP after business review.

---

## Implementation Instructions

### Step 1: Open Excel File
```bash
open data/sources/mapping/담보명mapping자료.xlsx
```

### Step 2: Add Patches Manually

**Navigate to ins_cd tabs and add rows:**

#### DB (N13) Tab:
| ins_cd | 보험사명 | cre_cvr_cd | 신정원코드명 | 담보명(가입설계서) |
|--------|----------|------------|--------------|-------------------|
| N13 | DB손해보험 | A3399 | 상해사망·후유장해 | 상해사망·후유장해(20-100%) |

**Note**: If A3399 doesn't exist in canonical code table, use A1300 (상해사망) as alternative.

#### KB (N10) Tab:
| ins_cd | 보험사명 | cre_cvr_cd | 신정원코드명 | 담보명(가입설계서) |
|--------|----------|------------|--------------|-------------------|
| N10 | KB손해보험 | A3300_1 | 상해후유장해(3-100%) | 일반상해후유장해(3%~100%) |
| N10 | KB손해보험 | A3300_1 | 상해후유장해(20-100%) | 일반상해후유장해(20~100%)(기본) |

### Step 3: Save Excel File

### Step 4: Verify Checksum Changed
```bash
shasum data/sources/mapping/담보명mapping자료.xlsx
```
(Record new checksum for reproducibility)

---

## Verification Commands (After Excel Patch + Step2 Rebuild)

### Regenerate Step2 (Required)
```bash
# Delete Step2 outputs
rm -f data/scope_v3/*_step2_*.jsonl

# Rebuild Step2-a (sanitization)
python -m pipeline.step2_sanitize_scope.run

# Rebuild Step2-b (canonical mapping)
python -m pipeline.step2_canonical_mapping.run
```

### Verify Mapping Rates
```bash
# DB over41 (expect 30/30 = 100%)
echo "DB over41: $(jq -r 'select(.coverage_code!=null) | .coverage_name_raw' data/scope_v3/db_over41_step2_canonical_scope_v1.jsonl | wc -l | tr -d ' ')/30"

# DB under40 (expect 30/30 = 100%)
echo "DB under40: $(jq -r 'select(.coverage_code!=null) | .coverage_name_raw' data/scope_v3/db_under40_step2_canonical_scope_v1.jsonl | wc -l | tr -d ' ')/30"

# KB (expect 31/42 = 73.8%)
echo "KB: $(jq -r 'select(.coverage_code!=null) | .coverage_name_raw' data/scope_v3/kb_step2_canonical_scope_v1.jsonl | wc -l | tr -d ' ')/42"

# Hyundai (expect unchanged 26/44 = 59.1%)
echo "Hyundai: $(jq -r 'select(.coverage_code!=null) | .coverage_name_raw' data/scope_v3/hyundai_step2_canonical_scope_v1.jsonl | wc -l | tr -d ' ')/44"
```

---

## DoD Status (Projected After Patches)

| Metric | Target | Current | Projected | Status |
|--------|--------|---------|-----------|--------|
| DB mapping rate | ≥ 99% | 96.7% | **100%** | ✅ PASS |
| Hyundai mapping rate | ≥ 75% | 59.1% | **59.1%** | ❌ FAIL (broken fragments) |
| KB mapping rate | ≥ 75% | 69.0% | **73.8%** | ⚠️ SHORT (1.2% gap) |
| Step1 files unchanged | Yes | — | Yes | ✅ PASS |
| SSOT enforcement | scope_v3 only | — | Yes | ✅ PASS |
| Minimal patches only | Yes | — | 3 entries | ✅ PASS |

**Notes**:
1. **DB**: ✅ DoD met (100%)
2. **Hyundai**: ❌ 61% of gap is broken fragments (Step1 extraction issue) → Accept 59.1%
3. **KB**: ⚠️ 1.2% short of 75% target (need 1 more mapping from borderline candidates)

---

## Alternative: KB Gap Closure (Optional)

If KB must reach 75% DoD threshold, consider adding 1 borderline candidate:

**Candidate**: `부정맥질환(Ⅰ49)진단비`
- **Reason**: ICD code-based (I49), similar to existing cardiovascular diagnoses
- **Canonical code**: A4407 or create new
- **Impact**: 73.8% → **76.2%** (31→32/42) ✅ DoD met

**Trade-off**: Requires business validation that I49 (arrhythmia) diagnosis coverage is standard enough for canonical dictionary.

**Recommendation**:
- If DoD threshold is strict requirement → add this 4th patch
- If 73.8% is acceptable → stay with 3 patches (minimal approach)

---

## Next Steps

1. **Human**: Manually apply 3 patches to Excel (DB 1, KB 2)
2. **Human**: Save Excel and record new checksum
3. **Claude**: Regenerate Step2 outputs (delete + rebuild)
4. **Claude**: Verify mapping rates against DoD thresholds
5. **Claude**: Create result summary document
6. **Claude**: Commit changes with audit trail

---

**Status**: Patch list ready for manual Excel application
**Total patches**: 3 (DB: 1, Hyundai: 0, KB: 2)
**Expected DoD**: DB ✅ 100%, Hyundai ❌ 59.1%, KB ⚠️ 73.8%
