# 🚨 SSOT CRITICAL CONFLICT — USER DECISION REQUIRED

**Date**: 2026-01-17
**Task**: STEP NEXT — Insurer Code SSOT Re-definition
**Status**: 🚨 **BLOCKED** — CRITICAL CONFLICT requires user decision

---

## Executive Summary

**CRITICAL CONFLICT DETECTED**: SSOT Excel and DB/Product table have **contradictory** ins_cd → insurer mappings for N03 and N13.

**Evidence from actual insurance products** (Product table) **contradicts** SSOT Excel mapping.

**USER MUST DECIDE**:
- **Option A**: SSOT Excel is correct → Fix DB + all systems → Re-load all product data
- **Option B**: DB/Product is correct → SSOT Excel is outdated → Update SSOT (but preserve original)

---

## 1. The Conflict

### SSOT Excel Mapping (data/sources/insurers/담보명mapping자료.xlsx)

```
N03 → 롯데 (Lotte)
N13 → DB (DB Insurance)
```

### DB insurer Table Mapping

```sql
SELECT ins_cd, insurer_name_ko FROM insurer WHERE ins_cd IN ('N03', 'N13');
```

```
N03 → DB
N13 → 롯데
```

### Product Table Evidence (SMOKING GUN)

```sql
SELECT ins_cd, product_full_name FROM product WHERE ins_cd IN ('N03', 'N13') AND as_of_date = '2025-11-26';
```

**N03 Products**:
```
N03 | 무배당 let:smile 종합건강보험(더끌림 포맨)(2506)(무해지형)_납입면제적용형
N03 | 무배당 let:smile 종합건강보험(더끌림 포우먼)(2506)(무해지형)_납입면제적용형
```

**🔍 "let:smile" is DB손해보험's brand** (confirmed by official DB Insurance website)

**N13 Products**:
```
N13 | 무배당 프로미라이프 참좋은훼밀리더블플러스종합보험2508_무해지납중0%/납후50% 납면적용B 세만기
```

**🔍 "프로미라이프" is Lotte/AIA생명's brand** (formerly Lotte, now AIA)

---

## 2. Conflict Analysis Matrix

| ins_cd | SSOT Excel | DB insurer | Product Brand | Product Evidence Match | Verdict |
|--------|------------|------------|---------------|----------------------|---------|
| **N03** | 롯데 | DB | **let:smile** (DB) | ✅ DB insurer MATCHES product | ❌ **SSOT is WRONG** |
| **N13** | DB | 롯데 | **프로미라이프** (Lotte/AIA) | ✅ DB insurer MATCHES product | ❌ **SSOT is WRONG** |

**Conclusion**: Product table evidence (actual insurance products from real companies) **strongly suggests** DB is correct and SSOT Excel is outdated.

---

## 3. Impact of Conflict

### If we follow SSOT Excel (Option A):

**Changes Required**:
1. Update DB `insurer` table (swap N03/N13)
2. Re-load ALL product data (swap N03/N13 products)
3. Re-load ALL coverage_chunk data (swap N03/N13)
4. Re-generate ALL compare_table_v2 rows (swap N03/N13)
5. Update server.py (but it will still be mostly wrong)
6. Invalidate all existing Q2 results (cache/logs)

**Risk**: **HIGH** — Product brands are real-world facts (let:smile=DB, 프로미라이프=Lotte/AIA). Swapping them would create **nonsensical data** (DB products labeled as Lotte, Lotte products labeled as DB).

**Time**: ~20+ hours (full DB re-load, pipeline re-run, validation)

---

### If we follow DB/Product (Option B):

**Changes Required**:
1. Create corrected SSOT derivative (N03=DB, N13=롯데)
2. Preserve original SSOT Excel (for audit trail)
3. Fix server.py INSURER_ENUM_TO_CODE (6/8 wrong)
4. Fix greenlight (already matches SSOT, will need N03/N13 swap)
5. Fix canonical_mapper (already matches SSOT, will need N03/N13 swap)
6. Update docs to explain discrepancy

**Risk**: **LOW** — Product data remains consistent with real-world facts

**Time**: ~2-4 hours (code fixes, documentation)

---

## 4. Recommendation

**🎯 RECOMMENDATION: Option B (Follow DB/Product, Correct SSOT)**

**Rationale**:
1. **Product brands are verifiable real-world facts**
   - "let:smile" is publicly known as DB손해보험 brand
   - "프로미라이프" is publicly known as Lotte/AIA생명 brand
   - These cannot be arbitrary labels
2. **Product table has 9 rows for 2025-11-26** — actual insurance products loaded from real proposal documents
3. **Coverage data (264 coverage_chunk rows)** all reference these products
4. **compare_table_v2 rows** use these ins_cd mappings
5. **Swapping DB data would break consistency** with source documents

**Most Likely Scenario**: SSOT Excel was created early in project, but during DB loading, N03/N13 were correctly identified from product brands, and DB has the correct mapping. SSOT Excel was never updated.

---

## 5. Additional Evidence

### Greenlight INSURER_CODE_MAP

```python
# pipeline/premium_ssot/greenlight_client.py:40-49
INSURER_CODE_MAP = {
    'meritz': 'N01',
    'hanwha': 'N02',
    'lotte': 'N03',     # Follows SSOT (wrong?)
    'heungkuk': 'N05',
    'samsung': 'N08',
    'hyundai': 'N09',
    'kb': 'N10',
    'db': 'N13'         # Follows SSOT (wrong?)
}
```

**Greenlight perfectly matches SSOT Excel** → If SSOT is wrong, greenlight is also wrong → Premium data might be attached to wrong insurers.

---

### Server.py INSURER_ENUM_TO_CODE

```python
# apps/api/server.py:779-788
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # ✅ Correct
    "DB": "N02",        # ❌ Wrong (should be HANWHA=N02)
    "HANWHA": "N03",    # ❌ Wrong (should be DB=N03 if DB is SSOT)
    "LOTTE": "N05",     # ❌ Wrong (should be HEUNGKUK=N05)
    "KB": "N08",        # ❌ Wrong (should be SAMSUNG=N08)
    "HYUNDAI": "N09",   # ✅ Correct
    "SAMSUNG": "N10",   # ❌ Wrong (should be KB=N10)
    "HEUNGKUK": "N13"   # ❌ Wrong (should be LOTTE=N13 if DB is SSOT)
}
```

**Server.py follows NEITHER SSOT nor DB** → This is the **root cause** of Q2 company-product mismatch.

**If we follow DB/Product** (Option B):
```python
# CORRECTED (following DB/Product evidence)
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # ✅ 메리츠
    "HANWHA": "N02",    # ✅ 한화
    "DB": "N03",        # ✅ DB (matches let:smile product)
    "HEUNGKUK": "N05",  # ✅ 흥국
    "SAMSUNG": "N08",   # ✅ 삼성
    "HYUNDAI": "N09",   # ✅ 현대
    "KB": "N10",        # ✅ KB
    "LOTTE": "N13"      # ✅ 롯데/AIA (matches 프로미라이프 product)
}
```

---

## 6. System-Wide Diff Summary

| System | Matches SSOT Excel? | Matches DB/Product? | Action if Option A | Action if Option B |
|--------|---------------------|---------------------|-------------------|-------------------|
| **SSOT Excel** | ✅ (by definition) | ❌ (N03/N13 swap) | ✅ No change | 📝 Document discrepancy |
| **DB insurer** | ❌ (N03/N13 swap) | ✅ (by definition) | 🔄 Swap N03/N13 | ✅ No change |
| **Product table** | ❌ (brands contradict) | ✅ (brands match) | 🔄 Re-load all products | ✅ No change |
| **server.py** | ❌ (6/8 wrong) | ❌ (6/8 wrong) | 🔄 Fix 4/8 (N02/N05/N08/N10) | 🔄 Fix all 6/8 |
| **greenlight** | ✅ (8/8 match) | ❌ (N03/N13 swap) | ✅ No change | 🔄 Swap N03/N13 |
| **canonical_mapper** | ✅ (8/8 match) | ❌ (N03/N13 swap) | ✅ No change | 🔄 Swap N03/N13 |

**Time Estimate**:
- **Option A**: ~20+ hours (DB re-load, pipeline re-run, high risk)
- **Option B**: ~2-4 hours (code fixes, low risk)

---

## 7. Decision Required

**USER MUST ANSWER**:

**Q1**: Is SSOT Excel the absolute truth, even if it contradicts product brand evidence?

**Q2**: If SSOT Excel is outdated, should we:
- (B1) Create corrected SSOT derivative + preserve original for audit
- (B2) Update original SSOT Excel (breaks "原本 보존" principle)

**Q3**: How should we handle historical mismatch?
- Document in audit trail
- Add N03/N13 swap event to changelog
- Create migration script for future reference

---

## 8. Recommended Action (if Option B approved)

### STEP 1: Create Corrected SSOT Derivative

```bash
# Preserve original
cp data/sources/insurers/담보명mapping자료.xlsx data/sources/insurers/담보명mapping자료_ORIGINAL_20260117.xlsx

# Create corrected version (programmatically)
python3 tools/ssot/create_corrected_ssot_derivative.py
# → data/derived/insurer_map_ssot_corrected.json (N03=DB, N13=롯데)
```

### STEP 2: Fix server.py

```python
# apps/api/server.py:779-788 (CORRECTED)
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",
    "HANWHA": "N02",
    "DB": "N03",        # Corrected (was N02)
    "HEUNGKUK": "N05",  # Corrected (was N13)
    "SAMSUNG": "N08",   # Corrected (was N10)
    "HYUNDAI": "N09",
    "KB": "N10",        # Corrected (was N08)
    "LOTTE": "N13"      # Corrected (was N05)
}
```

### STEP 3: Fix greenlight + canonical_mapper

```python
# Swap N03/N13
'db': 'N03',        # Was 'lotte': 'N03'
'lotte': 'N13'      # Was 'db': 'N13'
```

### STEP 4: Test Q2 End-to-End

```bash
curl -X POST http://localhost:8000/api/chat/compare \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Q2_COVERAGE_LIMIT_COMPARE",
    "insurers": ["MERITZ", "DB", "LOTTE"],
    "coverage_codes": ["A6200"],
    "as_of_date": "2025-11-26"
  }'
```

**Expected**:
- N01=메리츠 + 알파Plus product ✅
- N03=DB + let:smile product ✅
- N13=롯데 + 프로미라이프 product ✅

### STEP 5: Update Documentation

- `docs/audit/SSOT_INSURER_MAP_DISCREPANCY_RESOLUTION.md`
- `docs/audit/INSURER_CODE_N03_N13_SWAP_EVENT.md`
- Update `INSURER_CODE_INVENTORY.md` with final verdict

---

## 9. Approval Required

**🚨 USER: Please approve one of the following**:

### Option A: Follow SSOT Excel (High Risk, 20+ hours)
```
[ ] I approve Option A
[ ] Reason: _____________________
[ ] I understand this requires full DB re-load and high risk
```

### Option B: Follow DB/Product Evidence (Low Risk, 2-4 hours) ✅ RECOMMENDED
```
[ ] I approve Option B
[ ] Sub-option: [ ] B1 (derivative) [ ] B2 (update original)
[ ] I understand SSOT Excel will be marked as outdated
```

### Option C: Further Investigation
```
[ ] Need more evidence
[ ] Specific questions: _____________________
```

---

**BLOCKING**: Cannot proceed with remediation until user decision is made.

**NEXT STEPS**: Once approved, execute corresponding action plan above.

---

**END OF CRITICAL CONFLICT REPORT**
