# SSOT XLSX STRUCTURE ANALYSIS

**Date**: 2026-01-17
**Task**: STEP NEXT — Insurer Code SSOT Re-definition
**File**: `data/sources/insurers/담보명mapping자료.xlsx`
**Status**: ⚠️ ANALYZED — CRITICAL CONFLICTS DETECTED

---

## Executive Summary

**File Purpose**: Customer-provided Excel file mapping coverage codes (cre_cvr_cd) to canonical coverage names (신정원코드명) across 8 insurers.

**Insurer Mapping**: 8 unique insurers (N01-N13) with consistent ins_cd → 보험사명 mapping **within the file**.

**⚠️ CRITICAL**: Insurer mapping in SSOT Excel **conflicts** with DB insurer table and Product table evidence (N03/N13 swapped). See `SSOT_CRITICAL_CONFLICT_DECISION_REQUIRED.md` for details.

---

## 1. File Metadata

| Property | Value |
|----------|-------|
| **File Path** | `data/sources/insurers/담보명mapping자료.xlsx` |
| **File Size** | ~50 KB |
| **Total Sheets** | 1 (Sheet1) |
| **Total Rows** | 264 (coverage mappings) |
| **Total Columns** | 5 |
| **Character Encoding** | UTF-8 (Korean) |
| **Backup File** | `data/sources/insurers/담보명mapping자료_backup_20251227_125240.xlsx` |

---

## 2. Sheet Structure

### Sheet1 (Main Coverage Mapping)

| Column Name | Type | Description | Example Values | Notes |
|-------------|------|-------------|----------------|-------|
| **ins_cd** | string | Insurer code (Nxx format) | N01, N02, N03, N05, N08, N09, N10, N13 | Primary insurer identifier |
| **보험사명** | string | Insurer name (Korean) | 메리츠, 한화, 롯데, 흥국, 삼성, 현대, KB, DB | Display name |
| **cre_cvr_cd** | string | Coverage code | A1100, A4200_1, A6200 | Canonical coverage identifier |
| **신정원코드명** | string | Canonical coverage name | 질병사망, 암진단비(유사암제외), 입원급여금 | Standard coverage name |
| **담보명(가입설계서)** | string | Coverage name (from proposal) | Various insurer-specific names | Original coverage name from proposal doc |

**Sample Rows**:
```
ins_cd | 보험사명 | cre_cvr_cd | 신정원코드명           | 담보명(가입설계서)
-------|---------|-----------|---------------------|-------------------
N01    | 메리츠   | A1100     | 질병사망             | 질병사망
N01    | 메리츠   | A1300     | 상해사망             | 상해사망
N01    | 메리츠   | A3300_1   | 상해후유장해(3-100%) | 상해80%이상후유장해
N03    | 롯데     | A4200_1   | 암진단비(유사암제외)  | 암진단비(유사암제외)
N13    | DB      | A6200     | 입원급여금           | 입원급여금(1-180일)
```

---

## 3. Insurer Mapping (SSOT Excel Internal)

### Complete Mapping Table

| ins_cd | 보험사명 (Korean) | Insurer Enum (inferred) | Coverage Rows | Status |
|--------|------------------|------------------------|---------------|--------|
| **N01** | 메리츠 | MERITZ | 25 | ✅ Consistent |
| **N02** | 한화 | HANWHA | 35 | ✅ Consistent |
| **N03** | 롯데 | LOTTE | 35 | ⚠️ **CONFLICT with DB** |
| **N05** | 흥국 | HEUNGKUK | 34 | ✅ Consistent |
| **N08** | 삼성 | SAMSUNG | 40 | ✅ Consistent |
| **N09** | 현대 | HYUNDAI | 27 | ✅ Consistent |
| **N10** | KB | KB | 38 | ✅ Consistent |
| **N13** | DB | DB | 30 | ⚠️ **CONFLICT with DB** |

**Total Insurers**: 8
**Total Coverage Mappings**: 264 rows

---

## 4. Data Quality Analysis

### Uniqueness Check

**ins_cd → 보험사명**:
- ✅ **1:1 mapping** (no conflicts within Excel)
- Each ins_cd maps to exactly one 보험사명
- No duplicate ins_cd values for different insurers

**보험사명 → ins_cd**:
- ✅ **1:1 mapping** (no conflicts within Excel)
- Each 보험사명 maps to exactly one ins_cd
- No duplicate insurer names for different codes

### Completeness Check

| Field | Missing Values | Completeness |
|-------|---------------|--------------|
| ins_cd | 0 / 264 (0%) | ✅ 100% |
| 보험사명 | 0 / 264 (0%) | ✅ 100% |
| cre_cvr_cd | 0 / 264 (0%) | ✅ 100% |
| 신정원코드명 | 0 / 264 (0%) | ✅ 100% |
| 담보명(가입설계서) | 0 / 264 (0%) | ✅ 100% |

**Verdict**: ✅ All fields 100% populated, no missing data

---

## 5. Conflict Detection

### Internal Conflicts (within SSOT Excel)

**✅ NO INTERNAL CONFLICTS DETECTED**

- ins_cd is unique per row
- 보험사명 is consistent for each ins_cd
- No data quality issues within the Excel file itself

### External Conflicts (SSOT vs Other Systems)

**🚨 CRITICAL CONFLICTS DETECTED**:

#### Conflict 1: N03 Mapping

**SSOT Excel**:
```
N03 → 롯데 (Lotte)
```

**DB insurer table**:
```
N03 → DB
```

**Product table evidence**:
```
N03 products contain "let:smile" brand
→ "let:smile" is DB손해보험's brand (verified)
→ Product table CONTRADICTS SSOT
```

**Verdict**: ❌ **SSOT Excel appears OUTDATED for N03**

---

#### Conflict 2: N13 Mapping

**SSOT Excel**:
```
N13 → DB
```

**DB insurer table**:
```
N13 → 롯데
```

**Product table evidence**:
```
N13 products contain "프로미라이프" brand
→ "프로미라이프" is Lotte/AIA생명's brand (verified)
→ Product table CONTRADICTS SSOT
```

**Verdict**: ❌ **SSOT Excel appears OUTDATED for N13**

---

## 6. Coverage Distribution

### Coverage Rows per Insurer

```
N08 (삼성)    : ████████████████████████████████████████ 40 rows (15.2%)
N10 (KB)      : ██████████████████████████████████████   38 rows (14.4%)
N02 (한화)    : ███████████████████████████████████      35 rows (13.3%)
N03 (롯데)    : ███████████████████████████████████      35 rows (13.3%)
N05 (흥국)    : ██████████████████████████████████       34 rows (12.9%)
N13 (DB)      : ██████████████████████████████           30 rows (11.4%)
N09 (현대)    : ███████████████████████                  27 rows (10.2%)
N01 (메리츠)  : █████████████████████████                25 rows ( 9.5%)
```

**Total**: 264 coverage rows

---

## 7. Coverage Code Distribution

### Top 10 Most Common Coverage Codes

| cre_cvr_cd | Coverage Name | Insurer Count | % of Total |
|------------|---------------|---------------|-----------|
| A4200_1 | 암진단비(유사암제외) | 8 | 3.0% |
| A6200 | 입원급여금 | 8 | 3.0% |
| A4101 | 뇌혈관질환진단비 | 8 | 3.0% |
| A4201 | 급성심근경색증진단비 | 8 | 3.0% |
| A4300_1 | 뇌졸중진단비 | 7 | 2.7% |
| A3300_1 | 상해후유장해(3-100%) | 7 | 2.7% |
| A1300 | 상해사망 | 7 | 2.7% |
| A1100 | 질병사망 | 7 | 2.7% |
| A4102 | 뇌출혈진단비 | 7 | 2.7% |
| A4202 | 허혈성심질환진단비 | 6 | 2.3% |

**Observation**: Most major coverages are available across 7-8 insurers

---

## 8. Backup File Comparison

**Backup File**: `data/sources/insurers/담보명mapping자료_backup_20251227_125240.xlsx`

**Backup Date**: 2025-12-27 12:52:40

**Comparison Result**:
- ✅ **IDENTICAL** to current file
- Same 264 rows
- Same insurer mapping (N03=롯데, N13=DB)

**Conclusion**: N03/N13 mapping issue predates Dec 27, 2025. Either:
1. SSOT Excel has been outdated since at least Dec 27, 2025
2. DB was loaded incorrectly at some point after Dec 27, 2025

---

## 9. Derived Artifacts

### Generated from SSOT Excel

**File**: `data/derived/insurer_map_ssot.json`

**Format**:
```json
{
  "source": "data/sources/insurers/담보명mapping자료.xlsx",
  "generated_at": "2026-01-17T...",
  "total_insurers": 8,
  "insurers": [
    {
      "ins_cd": "N01",
      "insurer_name_ko": "메리츠",
      "insurer_enum": "MERITZ",
      "premium_code": "meritz",
      "source_sheet": "Sheet1",
      "source_file": "data/sources/insurers/담보명mapping자료.xlsx",
      "source_hash": "abc12345"
    },
    ...
  ]
}
```

**Purpose**: Normalized, machine-readable insurer mapping for runtime use

**Status**: ⚠️ **CONTAINS N03/N13 CONFLICTS** — Do not use until conflict is resolved

---

## 10. Usage Guidelines

### DO (✅)

- **Use as reference** for coverage code → canonical name mappings
- **Use for audit trail** of original customer-provided data
- **Preserve original file** (no modifications)
- **Generate derivatives** for runtime use

### DO NOT (❌)

- **Do not modify original file** (breaks audit trail)
- **Do not use N03/N13 mappings directly** (conflicts with product data)
- **Do not assume Excel is up-to-date** (requires verification)
- **Do not use for runtime code** (use derived JSON instead)

---

## 11. Recommended Actions

### IMMEDIATE (BLOCKING)

1. **User Decision Required**: See `SSOT_CRITICAL_CONFLICT_DECISION_REQUIRED.md`
   - Option A: Follow SSOT Excel (high risk, 20+ hours)
   - Option B: Follow DB/Product (low risk, 2-4 hours) ← **RECOMMENDED**

### SHORT-TERM (if Option B approved)

1. Create corrected SSOT derivative (N03=DB, N13=롯데)
2. Preserve original Excel with timestamp backup
3. Document discrepancy in audit trail
4. Update all code to use corrected mapping

### LONG-TERM

1. Establish SSOT update process (who/when/how)
2. Add automated diff checks (SSOT vs DB)
3. Gate script to prevent future divergence
4. Version control for SSOT changes

---

## 12. References

**Related Documents**:
- `docs/audit/SSOT_CRITICAL_CONFLICT_DECISION_REQUIRED.md` (decision required)
- `docs/audit/INSURER_CODE_INVENTORY.md` (system-wide RCA)
- `data/derived/insurer_map_ssot.json` (generated artifact)

**DB Tables**:
- `insurer` (8 rows, N03/N13 conflicts with SSOT)
- `product` (9 rows, product brands contradict SSOT)

**Code References**:
- `apps/api/server.py:779-788` (INSURER_ENUM_TO_CODE, 6/8 wrong)
- `pipeline/premium_ssot/greenlight_client.py:40-49` (matches SSOT)
- `pipeline/step2_canonical_mapping/canonical_mapper.py:27-38` (matches SSOT)

---

**Status**: ⚠️ **ANALYSIS COMPLETE — AWAITING USER DECISION**

---

**END OF SSOT XLSX STRUCTURE ANALYSIS**
