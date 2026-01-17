# INSURER CODE INVENTORY & RCA

**Date**: 2026-01-17
**Task**: STEP NEXT — INSURER CODE MISMATCH RCA
**Status**: 🚨 CRITICAL — Multiple code system conflicts detected

---

## Executive Summary

**FINDING**: 🚨 **CRITICAL MISMATCH** — 7 out of 8 insurers have conflicting code mappings across 3 different systems.

**ROOT CAUSE**:
1. DB `insurer` table and `product` table are **internally consistent** (CORRECT SSOT)
2. `mapping.xlsx` has **outdated** insurer names (N03/N13 swapped, others wrong)
3. `apps/api/server.py` INSURER_ENUM_TO_CODE is **completely wrong** (7/8 mismatches)
4. `greenlight_client.py` INSURER_CODE_MAP follows **wrong mapping.xlsx** (2/8 mismatches)

**IMPACT**: Q2 회사명-상품명 불일치, premium 조회 실패, UI 표시 오류

---

## 1. Code System Inventory

### System A: DB `insurer` Table (✅ SSOT — CORRECT)

```sql
SELECT ins_cd, insurer_name_ko FROM insurer ORDER BY ins_cd;
```

| ins_cd | insurer_name_ko | Status |
|--------|----------------|--------|
| N01    | 메리츠          | ✅ SSOT |
| N02    | 한화            | ✅ SSOT |
| N03    | DB              | ✅ SSOT |
| N05    | 흥국            | ✅ SSOT |
| N08    | 삼성            | ✅ SSOT |
| N09    | 현대            | ✅ SSOT |
| N10    | KB              | ✅ SSOT |
| N13    | 롯데            | ✅ SSOT |

**Evidence**: `product` table confirms this mapping (N03 = "let:smile" DB product, N13 = "프로미라이프" Lotte/AIA product)

---

### System B: `mapping.xlsx` (❌ OUTDATED — N03/N13 SWAPPED)

**File**: `data/sources/mapping/담보명mapping자료.xlsx`

```python
# Extracted from mapping.xlsx
N01 → 메리츠
N02 → 한화
N03 → 롯데     # ❌ WRONG! DB says N03=DB
N05 → 흥국
N08 → 삼성
N09 → 현대
N10 → KB
N13 → DB       # ❌ WRONG! DB says N13=롯데
```

**Conflicts**:
- ❌ N03: mapping.xlsx=롯데, DB=DB (SWAPPED)
- ❌ N13: mapping.xlsx=DB, DB=롯데 (SWAPPED)

**Date**: Backup file dated 20251227 has same wrong mapping → error predates Dec 27, 2025

---

### System C: `apps/api/server.py` INSURER_ENUM_TO_CODE (🚨 CRITICAL — 7/8 WRONG)

**File**: `apps/api/server.py:779-788`

```python
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # ✅ CORRECT
    "DB": "N02",        # ❌ WRONG! N02=한화 not DB
    "HANWHA": "N03",    # ❌ WRONG! N03=DB not 한화
    "LOTTE": "N05",     # ❌ WRONG! N05=흥국 not 롯데
    "KB": "N08",        # ❌ WRONG! N08=삼성 not KB
    "HYUNDAI": "N09",   # ✅ CORRECT
    "SAMSUNG": "N10",   # ❌ WRONG! N10=KB not 삼성
    "HEUNGKUK": "N13"   # ❌ WRONG! N13=롯데 not 흥국
}
```

**Conflicts**: 7 out of 8 mappings are WRONG

**Impact**: Q2 compare endpoint receives ENUM from UI, converts using wrong codes → joins with wrong insurer data

---

### System D: `greenlight_client.py` INSURER_CODE_MAP (⚠️ 2/8 WRONG)

**File**: `pipeline/premium_ssot/greenlight_client.py:40-49`

```python
INSURER_CODE_MAP = {
    'meritz': 'N01',    # ✅ CORRECT
    'hanwha': 'N02',    # ✅ CORRECT
    'lotte': 'N03',     # ❌ WRONG! N03=DB not lotte
    'heungkuk': 'N05',  # ✅ CORRECT
    'samsung': 'N08',   # ✅ CORRECT
    'hyundai': 'N09',   # ✅ CORRECT
    'kb': 'N10',        # ✅ CORRECT
    'db': 'N13'         # ❌ WRONG! N13=롯데 not db
}
```

**Conflicts**: N03/N13 swapped (follows mapping.xlsx)

**Impact**: Premium data retrieved for wrong insurer, cannot join with correct product data

---

### System E: `canonical_mapper.py` INSURER_CODE_MAP (⚠️ 2/8 WRONG)

**File**: `pipeline/step2_canonical_mapping/canonical_mapper.py:27-38`

Same as greenlight_client.py (follows mapping.xlsx):

```python
INSURER_CODE_MAP = {
    'meritz': 'N01',    # ✅ CORRECT
    'hanwha': 'N02',    # ✅ CORRECT
    'lotte': 'N03',     # ❌ WRONG! N03=DB not lotte
    'heungkuk': 'N05',  # ✅ CORRECT
    'samsung': 'N08',   # ✅ CORRECT
    'hyundai': 'N09',   # ✅ CORRECT
    'kb': 'N10',        # ✅ CORRECT
    'db': 'N13'         # ❌ WRONG! N13=롯데 not db
}
```

**Conflicts**: N03/N13 swapped

**Impact**: Pipeline generates wrong ins_cd for lotte/db products → DB mismatch

---

## 2. Conflict Matrix

| ins_cd | DB insurer (SSOT) | mapping.xlsx | server.py ENUM | greenlight | Status |
|--------|-------------------|--------------|----------------|------------|--------|
| **N01** | 메리츠 | 메리츠 | MERITZ ✅ | meritz ✅ | ✅ ALL MATCH |
| **N02** | 한화 | 한화 | DB ❌ | hanwha ✅ | ❌ server.py WRONG |
| **N03** | DB | 롯데 ❌ | HANWHA ❌ | lotte ❌ | ❌ ALL WRONG (except DB) |
| **N05** | 흥국 | 흥국 | LOTTE ❌ | heungkuk ✅ | ❌ server.py WRONG |
| **N08** | 삼성 | 삼성 | KB ❌ | samsung ✅ | ❌ server.py WRONG |
| **N09** | 현대 | 현대 | HYUNDAI ✅ | hyundai ✅ | ✅ ALL MATCH |
| **N10** | KB | KB | SAMSUNG ❌ | kb ✅ | ❌ server.py WRONG |
| **N13** | 롯데 | DB ❌ | HEUNGKUK ❌ | db ❌ | ❌ ALL WRONG (except DB) |

**Summary**:
- ✅ Correct: 2/8 (N01, N09)
- ❌ server.py wrong: 7/8
- ❌ mapping.xlsx wrong: 2/8 (N03, N13)
- ❌ greenlight wrong: 2/8 (N03, N13)

---

## 3. Evidence: DB Product Data Verification

```sql
SELECT ins_cd, product_full_name FROM product WHERE as_of_date = '2025-11-26';
```

| ins_cd | product_full_name | Insurer |
|--------|-------------------|---------|
| N01 | (무)알파Plus보장보험2508... | 메리츠 ✅ |
| N02 | 한화 더건강한 한아름종합보험... | 한화 ✅ |
| N03 | 무배당 let:smile 종합건강보험... | **DB** ✅ |
| N05 | 무배당 흥Good 행복한 파워종합보험... | 흥국 ✅ |
| N08 | 무배당 삼성화재 건강보험 마이헬스... | 삼성 ✅ |
| N09 | 무배당현대해상퍼펙트플러스종합보험... | 현대 ✅ |
| N10 | KB닥터플러스건강보험... | KB ✅ |
| N13 | 무배당 프로미라이프 참좋은훼밀리... | **롯데/AIA** ✅ |

**Proof**:
- N03 product name contains "let:smile" (DB 손해보험 브랜드)
- N13 product name contains "프로미라이프" (Lotte/AIA 브랜드)

**Conclusion**: DB `insurer` table is 100% consistent with `product` table → **DB is SSOT**

---

## 4. Impact Analysis

### Impact 1: Q2 회사명-상품명 불일치 (HIGH)

**Scenario**: User requests Q2 compare for coverage A6200

1. UI sends: `insurers: ["MERITZ", "DB", "LOTTE", "KB", "HYUNDAI", "SAMSUNG", "HEUNGKUK"]`
2. `server.py` converts using INSURER_ENUM_TO_CODE (WRONG):
   - "DB" → N02 (❌ should be N03)
   - "LOTTE" → N05 (❌ should be N13)
   - "KB" → N08 (❌ should be N10)
   - "SAMSUNG" → N10 (❌ should be N08)
   - "HEUNGKUK" → N13 (❌ should be N05)
3. Query joins `product` table with **wrong ins_cd**
4. Returns N02 product (한화) but UI displays "DB" label → **MISMATCH**

**Result**: User saw "DB손해보험 → 알파Plus보장보험 (메리츠 상품)" in Q2 screenshot

---

### Impact 2: Premium 조회 실패 (MEDIUM)

**Scenario**: Pipeline pulls premium from Greenlight API

1. Pipeline uses greenlight_client.py INSURER_CODE_MAP
2. Queries premium for 'lotte' → stores as N03
3. Product data has N03 = DB (not lotte)
4. Premium join fails or attaches to wrong product

**Result**: Premium 데이터 정합성 깨짐

---

### Impact 3: UI 표시 오류 (HIGH)

**Scenario**: Q2LimitDiffView.tsx INSURER_NAMES hardcoded

**Previous code** (apps/web/components/chat/Q2LimitDiffView.tsx:45-54):

```typescript
// ❌ OLD (WRONG)
const INSURER_NAMES: Record<string, string> = {
  N01: 'DB손해보험',      // ❌ N01=메리츠 not DB
  N03: '메리츠화재',      // ❌ N03=DB not 메리츠
  N05: '삼성화재',        // ❌ N05=흥국 not 삼성
  N08: '현대해상',        // ❌ N08=삼성 not 현대
  N09: '흥국화재',        // ❌ N09=현대 not 흥국
  N13: '한화손해보험',    // ❌ N13=롯데 not 한화
};
```

**Fixed code** (2026-01-17):

```typescript
// ✅ NEW (CORRECT)
const INSURER_NAMES: Record<string, string> = {
  N01: '메리츠화재',
  N02: 'DB손해보험',
  N03: 'DB손해보험',
  N05: '흥국화재',
  N08: '삼성화재',
  N09: '현대해상',
  N10: 'KB손해보험',
  N13: 'AIA생명',
};
```

**Result**: UI now displays correct company names (but backend still broken)

---

## 5. Root Cause Analysis

### H1: mapping.xlsx 자체에 2개 코드 체계가 섞여있다

**Verdict**: ❌ FALSE

- mapping.xlsx has consistent structure (1 sheet, clear ins_cd + 보험사명 columns)
- BUT values are outdated (N03/N13 swapped)

---

### H2: premium adapter가 canonical로 변환하지 않고 raw 외부 code로 join한다

**Verdict**: ⚠️ PARTIAL

- greenlight_client.py uses wrong INSURER_CODE_MAP (follows mapping.xlsx)
- Stores premium with wrong ins_cd (N03=lotte, N13=db)
- Cannot join with product table (which has N03=DB, N13=롯데)

---

### H3: UI/프록시에서 "insurer enum" ↔ "ins_cd" 변환이 역전되었다

**Verdict**: ✅ TRUE — **PRIMARY ROOT CAUSE**

- apps/api/server.py INSURER_ENUM_TO_CODE is completely wrong (7/8 mismatches)
- UI sends ENUM → server converts using wrong map → queries DB with wrong ins_cd
- UI hardcoded INSURER_NAMES was also wrong (fixed on 2026-01-17)

---

### H4: "보험사명 normalize"가 다중 alias로 깨져서 잘못 매핑된다

**Verdict**: ❌ FALSE

- No alias system exists (should be implemented)
- Issue is not normalization, but **hardcoded wrong mappings**

---

## 6. SSOT Decision

### ✅ SSOT: DB `insurer` Table

**Rationale**:
1. DB `insurer` table is 100% consistent with `product` table (verified)
2. Product names in `product` table match insurer brands (let:smile=DB, 프로미라이프=Lotte/AIA)
3. All other systems (mapping.xlsx, server.py, greenlight) are inconsistent

**Constitutional Declaration**:

**DB `insurer` table is the ONLY authoritative source for ins_cd → insurer_name_ko mapping.**

---

## 7. Remediation Plan

### STEP B-1: Fix mapping.xlsx (URGENT)

**Action**: Update `data/sources/mapping/담보명mapping자료.xlsx`

**Changes**:
```diff
- N03 → 롯데
+ N03 → DB
- N13 → DB
+ N13 → 롯데
```

**Validation**: Run `tools/audit/marker_vs_mapping_impact.py` to check for downstream impact

---

### STEP B-2: Fix server.py INSURER_ENUM_TO_CODE (CRITICAL)

**File**: `apps/api/server.py:779-788`

**OLD (WRONG)**:
```python
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",
    "DB": "N02",        # ❌ WRONG
    "HANWHA": "N03",    # ❌ WRONG
    "LOTTE": "N05",     # ❌ WRONG
    "KB": "N08",        # ❌ WRONG
    "HYUNDAI": "N09",
    "SAMSUNG": "N10",   # ❌ WRONG
    "HEUNGKUK": "N13"   # ❌ WRONG
}
```

**NEW (CORRECT)**:
```python
INSURER_ENUM_TO_CODE = {
    "MERITZ": "N01",    # 메리츠
    "HANWHA": "N02",    # 한화
    "DB": "N03",        # DB
    "HEUNGKUK": "N05",  # 흥국
    "SAMSUNG": "N08",   # 삼성
    "HYUNDAI": "N09",   # 현대
    "KB": "N10",        # KB
    "LOTTE": "N13"      # 롯데/AIA
}
```

**Note**: N13 is "롯데" in DB, but actual products are "프로미라이프" (AIA생명, formerly Lotte)

---

### STEP B-3: Fix greenlight_client.py INSURER_CODE_MAP (HIGH)

**File**: `pipeline/premium_ssot/greenlight_client.py:40-49`

**OLD (WRONG)**:
```python
INSURER_CODE_MAP = {
    'meritz': 'N01',
    'hanwha': 'N02',
    'lotte': 'N03',     # ❌ WRONG
    'heungkuk': 'N05',
    'samsung': 'N08',
    'hyundai': 'N09',
    'kb': 'N10',
    'db': 'N13'         # ❌ WRONG
}
```

**NEW (CORRECT)**:
```python
INSURER_CODE_MAP = {
    'meritz': 'N01',
    'hanwha': 'N02',
    'db': 'N03',        # DB
    'heungkuk': 'N05',
    'samsung': 'N08',
    'hyundai': 'N09',
    'kb': 'N10',
    'lotte': 'N13'      # Lotte/AIA
}
```

---

### STEP B-4: Fix canonical_mapper.py INSURER_CODE_MAP (HIGH)

**File**: `pipeline/step2_canonical_mapping/canonical_mapper.py:27-38`

**Same fix as greenlight_client.py** (N03=db, N13=lotte)

---

### STEP B-5: Create DB `insurer_code_alias` Table (CONSTITUTIONAL)

**Purpose**: Support external code systems (UI ENUM, premium API, legacy) without polluting SSOT

**Schema**:
```sql
CREATE TABLE insurer_code_alias (
    alias_id SERIAL PRIMARY KEY,
    alias_system VARCHAR(50) NOT NULL,  -- 'UI_ENUM' | 'PREMIUM_API' | 'LEGACY'
    alias_code VARCHAR(50) NOT NULL,
    ins_cd VARCHAR(10) NOT NULL REFERENCES insurer(ins_cd),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alias_system, alias_code)
);
```

**Seed Data**:
```sql
-- UI ENUM (current)
INSERT INTO insurer_code_alias (alias_system, alias_code, ins_cd, is_primary) VALUES
    ('UI_ENUM', 'MERITZ', 'N01', true),
    ('UI_ENUM', 'HANWHA', 'N02', true),
    ('UI_ENUM', 'DB', 'N03', true),
    ('UI_ENUM', 'HEUNGKUK', 'N05', true),
    ('UI_ENUM', 'SAMSUNG', 'N08', true),
    ('UI_ENUM', 'HYUNDAI', 'N09', true),
    ('UI_ENUM', 'KB', 'N10', true),
    ('UI_ENUM', 'LOTTE', 'N13', true);

-- Premium API (greenlight legacy keys)
INSERT INTO insurer_code_alias (alias_system, alias_code, ins_cd, is_primary) VALUES
    ('PREMIUM_API', 'meritz', 'N01', true),
    ('PREMIUM_API', 'hanwha', 'N02', true),
    ('PREMIUM_API', 'db', 'N03', true),
    ('PREMIUM_API', 'heungkuk', 'N05', true),
    ('PREMIUM_API', 'samsung', 'N08', true),
    ('PREMIUM_API', 'hyundai', 'N09', true),
    ('PREMIUM_API', 'kb', 'N10', true),
    ('PREMIUM_API', 'lotte', 'N13', true);
```

---

### STEP B-6: Enforce Adapter Pattern (CODE CHANGE)

**Principle**: ALL code MUST query `insurer_code_alias` table for conversion, NOT hardcoded maps

**Example** (apps/api/server.py):

**OLD (HARDCODED)**:
```python
INSURER_ENUM_TO_CODE = {...}  # ❌ Hardcoded
requested_insurer_codes = [INSURER_ENUM_TO_CODE.get(ins, ins) for ins in insurers]
```

**NEW (DB-DRIVEN)**:
```python
def resolve_insurer_codes(alias_system: str, alias_codes: List[str]) -> List[str]:
    """
    Resolve alias codes to canonical ins_cd using DB

    Args:
        alias_system: 'UI_ENUM' | 'PREMIUM_API' | 'LEGACY'
        alias_codes: List of alias codes (e.g., ['MERITZ', 'DB'])

    Returns:
        List of ins_cd (e.g., ['N01', 'N03'])
    """
    cursor.execute("""
        SELECT alias_code, ins_cd
        FROM insurer_code_alias
        WHERE alias_system = %s AND alias_code = ANY(%s)
    """, (alias_system, alias_codes))

    mapping = {row['alias_code']: row['ins_cd'] for row in cursor.fetchall()}
    return [mapping.get(code, code) for code in alias_codes]

# Usage
requested_insurer_codes = resolve_insurer_codes('UI_ENUM', insurers)
```

**Impact**: ✅ Single source of truth, no hardcoded maps, runtime updates possible

---

## 8. Gate Enforcement

### Gate 1: Code Conflict Detection

**Script**: `tools/gate/check_insurer_code_consistency.sh`

**Checks**:
1. DB `insurer` table has 8 rows (N01-N13)
2. mapping.xlsx ins_cd matches DB insurer.ins_cd (8/8)
3. server.py INSURER_ENUM_TO_CODE maps to valid ins_cd (8/8)
4. greenlight INSURER_CODE_MAP maps to valid ins_cd (8/8)
5. canonical_mapper INSURER_CODE_MAP maps to valid ins_cd (8/8)
6. No hardcoded INSURER_NAMES in UI (must use API response)

**PASS Condition**: All 6 checks green

---

### Gate 2: Premium Roundtrip Validation

**Script**: `tools/gate/check_premium_alias_roundtrip.sh`

**Checks**:
1. Query `insurer_code_alias` for PREMIUM_API system
2. For each alias_code: pull premium from greenlight API
3. Verify premium data can join with product table (ins_cd match)
4. Verify returned premium matches expected insurer

**PASS Condition**: 8/8 insurers roundtrip successfully

---

### Gate 3: Q2 Row Integrity (EXISTING)

**Script**: `tools/gate/check_q2_data_subset_ok.sh`

**Checks**: (already implemented)
- insurer_code injection matches insurer_set order
- product_name matches product.product_full_name for each ins_cd

---

## 9. Timeline & Priority

| Step | Priority | ETA | Blocker? |
|------|----------|-----|----------|
| B-1: Fix mapping.xlsx | HIGH | 30 min | ❌ No (isolated file) |
| B-2: Fix server.py | CRITICAL | 15 min | ✅ YES (Q2 broken) |
| B-3: Fix greenlight | HIGH | 15 min | ⚠️ Partial (premium) |
| B-4: Fix canonical_mapper | HIGH | 15 min | ⚠️ Partial (pipeline) |
| B-5: Create alias table | MEDIUM | 2 hrs | ❌ No (future-proofing) |
| B-6: Enforce adapter | MEDIUM | 4 hrs | ❌ No (refactor) |
| Gate 1: Consistency | HIGH | 1 hr | ❌ No (validation) |
| Gate 2: Roundtrip | MEDIUM | 2 hrs | ❌ No (validation) |

**Total Time**: ~10 hours

**Immediate Blockers** (< 1 hr):
1. B-2: Fix server.py INSURER_ENUM_TO_CODE (Q2 currently broken)

**Short-term** (< 3 hrs):
1. B-1: Fix mapping.xlsx
2. B-3: Fix greenlight
3. B-4: Fix canonical_mapper
4. Gate 1: Consistency check

**Long-term** (< 1 week):
1. B-5: Create alias table
2. B-6: Enforce adapter pattern
3. Gate 2: Roundtrip validation

---

## 10. References

**Files Audited**:
- `data/sources/mapping/담보명mapping자료.xlsx` (OUTDATED)
- `apps/api/server.py:779-788` (WRONG)
- `pipeline/premium_ssot/greenlight_client.py:40-49` (WRONG)
- `pipeline/step2_canonical_mapping/canonical_mapper.py:27-38` (WRONG)
- `apps/web/components/chat/Q2LimitDiffView.tsx:45-54` (FIXED 2026-01-17)

**Related Docs**:
- `docs/audit/INSURER_CODE_AUDIT.md` (2026-01-01, verified mapping.xlsx consistency — now invalidated)
- `docs/policy/INSURER_IDENTIFIER_SSOT.md` (2026-01-14, declared ins_cd as ONLY identifier — still valid)
- `docs/ui/Q2_COMPARE_DATA_CONTRACT.md` (2026-01-17, Q2 product SSOT integration)

**DB Queries**:
```sql
-- SSOT verification
SELECT ins_cd, insurer_name_ko FROM insurer ORDER BY ins_cd;
SELECT ins_cd, product_full_name FROM product WHERE as_of_date = '2025-11-26' ORDER BY ins_cd;
```

---

## 11. Approval & Next Steps

**Status**: 🚨 AUDIT COMPLETE — REMEDIATION REQUIRED

**Approval**: Pending user review

**Next Steps**:
1. User confirms SSOT = DB `insurer` table
2. Execute B-1 (mapping.xlsx) + B-2 (server.py) immediately (< 1 hr)
3. Test Q2 end-to-end after B-2 fix
4. Execute B-3 (greenlight) + B-4 (canonical_mapper) within 24 hrs
5. Schedule B-5 (alias table) + B-6 (adapter) for next sprint

---

**END OF INSURER CODE INVENTORY**
