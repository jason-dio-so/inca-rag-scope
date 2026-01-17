# PRODUCT BRAND EVIDENCE PROOF

**Date**: 2026-01-17
**Task**: STEP NEXT — Insurer Code SSOT Re-definition (Evidence-Based)
**Status**: ✅ EVIDENCE CONFIRMED — DB insurer table has N03/N13 SWAPPED

---

## Executive Summary

**CRITICAL FINDING**: DB `insurer` table has **N03/N13 swapped** compared to source files and SSOT Excel.

**Evidence Method**: Traced product brands (let:smile, 프로미라이프) back to source JSONL files in `data/scope_v3/`, which are named by insurer (lotte_*, db_*).

**Conclusion**:
- ✅ **SSOT Excel is CORRECT** (N03=롯데, N13=DB)
- ❌ **DB insurer table is WRONG** (N03=DB, N13=롯데)

---

## 1. Evidence Chain Overview

```
Source Files (Ground Truth)
    ↓
Product Extraction (scope_v3 JSONL)
    ↓
SSOT Excel (담보명mapping자료.xlsx) ✅ CORRECT
    ↓
DB insurer table ❌ N03/N13 SWAPPED
    ↓
Product table (inherits wrong ins_cd)
    ↓
Q2 API (company-product mismatch)
```

---

## 2. Evidence Table: let:smile Products

### Product Table Query Result

```sql
SELECT product_id, ins_cd, product_full_name, as_of_date
FROM product
WHERE product_full_name LIKE '%let:smile%'
ORDER BY product_id;
```

| product_id | ins_cd | product_full_name | as_of_date |
|------------|--------|-------------------|------------|
| LA0772E002 | **N03** | 무배당 let:smile 종합건강보험(더끌림 포맨)(2506)(무해지형)_납입면제적용형 | 2025-11-26 |
| LA0762E002 | **N03** | 무배당 let:smile 종합건강보험(더끌림 포우먼)(2506)(무해지형)_납입면제적용형 | 2025-11-26 |

**Product table says**: N03 = let:smile products

---

### Source File Evidence (Ground Truth)

**File**: `data/scope_v3/lotte_male_step1_raw_scope_v3.jsonl`

**Line 1**:
```json
{
  "product_name": "무배당 let:smile 종합건강보험(더끌림 포맨)(2506)(무해지형)_납입면제적용형",
  ...
}
```

**File**: `data/scope_v3/lotte_female_step1_raw_scope_v3.jsonl`

**Line 1**:
```json
{
  "product_name": "무배당 let:smile 종합건강보험(더끌림 포우먼)(2506)(무해지형)_납입면제적용형",
  ...
}
```

**Source files say**: let:smile products are in **lotte_*** files

---

### SSOT Excel Mapping

From `data/derived/insurer_map_ssot.json` (generated from 담보명mapping자료.xlsx):

```json
{
  "ins_cd": "N03",
  "insurer_name_ko": "롯데",
  "insurer_enum": "LOTTE",
  "premium_code": "lotte"
}
```

**SSOT Excel says**: N03 = 롯데 (Lotte)

---

### Evidence Analysis: let:smile

| Evidence Source | N03 = ? | Verification |
|----------------|---------|--------------|
| **Source files** (lotte_*) | 롯데 | ✅ File naming is ground truth |
| **SSOT Excel** | 롯데 | ✅ Matches source files |
| **DB insurer table** | DB | ❌ **WRONG** (contradicts source files) |
| **Product table** | (uses N03 from DB) | ❌ Inherits wrong ins_cd |

**Verdict**: N03 = 롯데 (Lotte) ← **Source files + SSOT Excel are CORRECT**

---

## 3. Evidence Table: 프로미라이프 Products

### Product Table Query Result

```sql
SELECT product_id, ins_cd, product_full_name, as_of_date
FROM product
WHERE product_full_name LIKE '%프로미라이프%'
ORDER BY product_id;
```

| product_id | ins_cd | product_full_name | as_of_date |
|------------|--------|-------------------|------------|
| 30633 | **N13** | 무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508_무해지납중0%/납후50% 납면적용B 세만기 | 2025-11-26 |

**Product table says**: N13 = 프로미라이프 products

---

### Source File Evidence (Ground Truth)

**File**: `data/scope_v3/db_over41_step1_raw_scope_v3.jsonl`

**Line 1**:
```json
{
  "product_name": "무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508_무해지납중0%/납후50% 납면적용B 세만기",
  ...
}
```

**File**: `data/scope_v3/db_under40_step1_raw_scope_v3.jsonl`

**Line 1**:
```json
{
  "product_name": "무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508_무해지납중0%/납후50% 납면적용B 세만기",
  ...
}
```

**Source files say**: 프로미라이프 products are in **db_*** files

---

### SSOT Excel Mapping

From `data/derived/insurer_map_ssot.json` (generated from 담보명mapping자료.xlsx):

```json
{
  "ins_cd": "N13",
  "insurer_name_ko": "DB",
  "insurer_enum": "DB",
  "premium_code": "db"
}
```

**SSOT Excel says**: N13 = DB

---

### User-Provided Cover Evidence

**User Correction** (2026-01-17):
```
"너의 주장 '프로미라이프 = Lotte/AIA 브랜드'는 **거짓**이다."
"증거: 사용자 제공 표지 이미지에서 좌상단 로고가 **DB손해보험**,
 제목이 **'무배당 프로미라이프 …'**로 명시됨."
```

**Cover Evidence**:
- Logo: DB손해보험
- Product Title: 무배당 프로미라이프

**Verified**: 프로미라이프 is DB Insurance's product brand

---

### Evidence Analysis: 프로미라이프

| Evidence Source | N13 = ? | Verification |
|----------------|---------|--------------|
| **Source files** (db_*) | DB | ✅ File naming is ground truth |
| **SSOT Excel** | DB | ✅ Matches source files |
| **User PDF cover** | DB | ✅ Logo + brand confirm DB |
| **DB insurer table** | 롯데 | ❌ **WRONG** (contradicts source files) |
| **Product table** | (uses N13 from DB) | ❌ Inherits wrong ins_cd |

**Verdict**: N13 = DB ← **Source files + SSOT Excel + Cover evidence are CORRECT**

---

## 4. Conflict Matrix: N03 and N13

| ins_cd | Source Files | SSOT Excel | DB insurer table | Product Table | Status |
|--------|--------------|------------|------------------|---------------|--------|
| **N03** | 롯데 (lotte_*) | 롯데 | **DB** ❌ | let:smile (from N03) | **SWAPPED** |
| **N13** | DB (db_*) | DB | **롯데** ❌ | 프로미라이프 (from N13) | **SWAPPED** |

**Diagnosis**: DB `insurer` table has N03 and N13 **swapped** compared to source files and SSOT Excel.

---

## 5. Root Cause Analysis

### Timeline Hypothesis

**Phase 1: Source Document Processing (Correct)**
- Source PDFs processed into scope_v3 JSONL files
- Files named by insurer: lotte_male, lotte_female, db_over41, db_under40
- File naming is CORRECT (matches PDF covers)

**Phase 2: SSOT Excel Creation (Correct)**
- Customer provided 담보명mapping자료.xlsx
- Mapping: N03=롯데, N13=DB
- SSOT Excel is CORRECT (matches source files)

**Phase 3: DB Loading (ERROR INTRODUCED)**
- DB `insurer` table loaded with N03/N13 swapped
- Possible causes:
  - Manual entry error
  - Copy-paste mistake
  - Incorrect migration script
- **This is where the error was introduced**

**Phase 4: Product Table Loading (Inherits Error)**
- Product table loaded with ins_cd from DB insurer table
- let:smile products assigned N03 (but DB insurer says N03=DB, WRONG)
- 프로미라이프 products assigned N13 (but DB insurer says N13=롯데, WRONG)
- Product table is **internally consistent** with DB insurer table (both wrong)

**Phase 5: Q2 API (Manifests as Bug)**
- Q2 uses server.py INSURER_ENUM_TO_CODE (also wrong)
- Company-product mismatch appears in UI
- User reports bug

---

## 6. System-Wide Impact

### Affected Systems

| System | N03 Mapping | N13 Mapping | Action Required |
|--------|-------------|-------------|-----------------|
| **Source files** (lotte_*, db_*) | ✅ 롯데 | ✅ DB | ✅ No change (correct) |
| **SSOT Excel** | ✅ 롯데 | ✅ DB | ✅ No change (correct) |
| **DB insurer table** | ❌ DB | ❌ 롯데 | 🔄 **SWAP N03/N13** |
| **Product table** | N03 (wrong label) | N13 (wrong label) | 🔄 **UPDATE ins_cd** |
| **server.py** | Many wrong | Many wrong | 🔄 **FIX ALL 6/8** |
| **greenlight** | ✅ N03=lotte | ✅ N13=db | ✅ No change (correct) |
| **canonical_mapper** | ✅ N03=lotte | ✅ N13=db | ✅ No change (correct) |

---

## 7. Correction Plan

### Priority 1: Fix DB insurer Table (CRITICAL)

**Current (WRONG)**:
```sql
SELECT ins_cd, insurer_name_ko, insurer_enum FROM insurer WHERE ins_cd IN ('N03', 'N13');
```
```
N03 | DB       | DB
N13 | 롯데     | LOTTE
```

**Required Fix**:
```sql
-- Swap N03 and N13
BEGIN;

UPDATE insurer
SET insurer_name_ko = '롯데', insurer_enum = 'LOTTE'
WHERE ins_cd = 'N03';

UPDATE insurer
SET insurer_name_ko = 'DB', insurer_enum = 'DB'
WHERE ins_cd = 'N13';

COMMIT;
```

**After Fix**:
```
N03 | 롯데     | LOTTE  ✅
N13 | DB       | DB     ✅
```

---

### Priority 2: Fix Product Table ins_cd (CRITICAL)

**Issue**: Product table has correct brands but wrong ins_cd labels

**Current State**:
```
N03 + let:smile → Should be LOTTE but labeled as N03 (which DB insurer says = DB)
N13 + 프로미라이프 → Should be DB but labeled as N13 (which DB insurer says = 롯데)
```

**After DB insurer fix**: Products will automatically be correctly labeled
- N03 + let:smile → LOTTE ✅
- N13 + 프로미라이프 → DB ✅

**Action**: No direct product table update needed. Product table is correct once DB insurer table is fixed.

---

### Priority 3: Fix server.py INSURER_ENUM_TO_CODE

**File**: `apps/api/server.py:779-788`

**Current (6/8 WRONG)**:
```python
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # ✅ Correct
    "DB": "N02",        # ❌ Wrong (should be HANWHA)
    "HANWHA": "N03",    # ❌ Wrong (should be DB)
    "LOTTE": "N05",     # ❌ Wrong (should be HEUNGKUK)
    "KB": "N08",        # ❌ Wrong (should be SAMSUNG)
    "HYUNDAI": "N09",   # ✅ Correct
    "SAMSUNG": "N10",   # ❌ Wrong (should be KB)
    "HEUNGKUK": "N13"   # ❌ Wrong (should be LOTTE)
}
```

**Required Fix (8/8 CORRECT)**:
```python
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # ✅ 메리츠
    "HANWHA": "N02",    # ✅ 한화
    "LOTTE": "N03",     # ✅ 롯데 (matches SSOT + source files)
    "HEUNGKUK": "N05",  # ✅ 흥국
    "SAMSUNG": "N08",   # ✅ 삼성
    "HYUNDAI": "N09",   # ✅ 현대
    "KB": "N10",        # ✅ KB
    "DB": "N13"         # ✅ DB (matches SSOT + source files)
}
```

---

### Priority 4: Fix UI INSURER_NAMES

**File**: `apps/web/components/chat/Q2LimitDiffView.tsx:45-54`

**Current (3/8 WRONG)**:
```typescript
const INSURER_NAMES: Record<string, string> = {
  N01: '메리츠화재',
  N02: 'DB손해보험',        // ❌ Wrong (should be 한화)
  N03: 'DB손해보험',        // ❌ Wrong (should be 롯데)
  N05: '흥국화재',
  N08: '삼성화재',
  N09: '현대해상',
  N10: 'KB손해보험',
  N13: 'AIA생명',           // ❌ Wrong (should be DB)
};
```

**Required Fix (8/8 CORRECT)**:
```typescript
const INSURER_NAMES: Record<string, string> = {
  N01: '메리츠화재',
  N02: '한화손해보험',      // ✅ Fixed
  N03: '롯데손해보험',      // ✅ Fixed (matches SSOT + source files)
  N05: '흥국화재',
  N08: '삼성화재',
  N09: '현대해상',
  N10: 'KB손해보험',
  N13: 'DB손해보험',        // ✅ Fixed (matches SSOT + source files)
};
```

---

### Priority 5: Verify greenlight and canonical_mapper (NO CHANGE NEEDED)

**greenlight_client.py** (ALREADY CORRECT):
```python
INSURER_CODE_MAP = {
    'lotte': 'N03',     # ✅ Matches SSOT
    'db': 'N13'         # ✅ Matches SSOT
}
```

**canonical_mapper.py** (ALREADY CORRECT):
```python
# Already matches SSOT Excel
```

**Action**: No changes needed. These components are already correct.

---

## 8. Verification Test Plan

### Test 1: DB Insurer Table Integrity

```sql
SELECT ins_cd, insurer_name_ko, insurer_enum
FROM insurer
WHERE ins_cd IN ('N03', 'N13');
```

**Expected**:
```
N03 | 롯데 | LOTTE
N13 | DB   | DB
```

---

### Test 2: Product Brand Consistency

```sql
SELECT p.ins_cd, i.insurer_name_ko, p.product_full_name
FROM product p
JOIN insurer i ON p.ins_cd = i.ins_cd
WHERE p.product_full_name LIKE '%let:smile%'
   OR p.product_full_name LIKE '%프로미라이프%'
ORDER BY p.ins_cd;
```

**Expected**:
```
N03 | 롯데 | 무배당 let:smile 종합건강보험(더끌림 포맨)
N03 | 롯데 | 무배당 let:smile 종합건강보험(더끌림 포우먼)
N13 | DB   | 무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508
```

---

### Test 3: Q2 API End-to-End

```bash
curl -X POST http://localhost:8000/api/chat/compare \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Q2_COVERAGE_LIMIT_COMPARE",
    "insurers": ["LOTTE", "DB"],
    "coverage_codes": ["A6200"],
    "as_of_date": "2025-11-26"
  }'
```

**Expected**:
```json
{
  "rows": [
    {
      "insurer_code": "N03",
      "insurer_name": "롯데",
      "product_name": "무배당 let:smile 종합건강보험(더끌림 포맨)",
      ...
    },
    {
      "insurer_code": "N13",
      "insurer_name": "DB",
      "product_name": "무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508",
      ...
    }
  ]
}
```

**Verify**: Company name matches product brand in each row

---

## 9. Documentation Updates Required

### Files to Update

1. ❌ **DELETE or MARK INVALID**: `docs/audit/INSURER_CODE_INVENTORY.md`
   - Contains incorrect conclusion (claimed DB insurer table was correct)

2. ❌ **DELETE or MARK INVALID**: `docs/audit/SSOT_CRITICAL_CONFLICT_DECISION_REQUIRED.md`
   - Based on false premise (assumed 프로미라이프=Lotte/AIA)

3. ✅ **UPDATE**: `docs/audit/SSOT_XLSX_STRUCTURE.md`
   - Remove conflict warnings
   - Add note that SSOT Excel is confirmed correct

4. ✅ **CREATE**: `docs/audit/DB_INSURER_N03_N13_SWAP_FIX.md`
   - Document the correction event
   - Include before/after states
   - Record fix timestamp

---

## 10. Lessons Learned

### What Went Wrong

1. **Assumed brand ownership without evidence**
   - Claimed "프로미라이프 = Lotte/AIA" based on assumed public knowledge
   - Should have traced source files first

2. **Trusted DB over source files**
   - Concluded DB insurer table was correct because product table matched it
   - Failed to recognize both could be consistently wrong

3. **Created false conflict**
   - Generated decision request document asking user to choose
   - Should have investigated evidence first

### Correct Methodology

1. ✅ **Trace to source files** (scope_v3 JSONL file naming)
2. ✅ **Verify SSOT Excel** matches source files
3. ✅ **Identify discrepancy** in DB tables
4. ✅ **Fix DB tables** to match source evidence

---

## 11. Approval for Execution

**RECOMMENDATION**: Proceed with correction plan immediately

**Risk**: **LOW** — All evidence confirms SSOT Excel is correct

**Impact**:
- DB insurer table: 2 rows updated
- server.py: 6 lines changed
- UI: 3 constants changed
- Testing: ~30 minutes

**Time Estimate**: 1-2 hours total

---

## 12. Conclusion

**FINAL VERDICT**:

| Component | N03 = ? | N13 = ? | Status |
|-----------|---------|---------|--------|
| **Source files** | 롯데 (lotte_*) | DB (db_*) | ✅ GROUND TRUTH |
| **SSOT Excel** | 롯데 | DB | ✅ CORRECT |
| **DB insurer** | DB | 롯데 | ❌ **SWAPPED** (fix required) |

**Evidence Quality**: 🟢 **DEFINITIVE**
- Source file naming (lotte_*, db_*) is irrefutable ground truth
- SSOT Excel matches source files
- User-provided PDF cover confirms 프로미라이프=DB

**Action Required**: Fix DB insurer table (swap N03/N13), then cascade to server.py and UI

---

**Status**: ✅ **EVIDENCE COMPLETE — READY FOR EXECUTION**

---

**END OF PRODUCT BRAND EVIDENCE PROOF**
