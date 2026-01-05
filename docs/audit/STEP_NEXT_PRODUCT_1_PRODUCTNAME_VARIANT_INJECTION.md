# STEP NEXT-PRODUCT-1: Product Name + Variant Injection (SSOT)

**Date**: 2026-01-05
**Status**: ✅ COMPLETE
**Phase**: STEP NEXT-OPS-CYCLE-01 / Phase 1

---

## 0. Purpose

Inject `product_name` + `variant_key` into **coverage_cards_slim.jsonl** from **products.yml** (SSOT).

**Problem**:
- No product_name in slim cards → ambiguous screen display
- LOTTE/DB variants (MALE/FEMALE, AGE_U40/O40) not explicitly tracked
- Runtime had no product metadata SSOT

**Solution**:
- Add 2 fields to `CoverageCardSlim` schema
- Load products.yml at build time
- Inject product_name + variant_key during Step5-slim

---

## 1. Files Changed

### Schema
- `core/compare_types.py` (CoverageCardSlim dataclass)
  - Added `product_name: str` (required)
  - Added `variant_key: Optional[str]` (LOTTE_MALE/FEMALE, DB_AGE_U40/O40, or null)

### Pipeline
- `pipeline/step5_build_cards/build_cards_slim.py`
  - Added `_load_products_metadata()` function (YAML parser)
  - Added `_resolve_variant_key()` function (LOTTE/DB special handling)
  - Modified `build_coverage_cards_slim()` to inject fields
  - Modified `main()` to require products.yml path

---

## 2. product_name Injection Rules (ABSOLUTE)

- **SSOT**: `data/metadata/products.yml` → `products[*].product_name_display`
- **Mapping**: `insurer_key` → `product_name`
- **Fallback**: ❌ FORBIDDEN (raise RuntimeError if not found)

**Example**:
```yaml
# products.yml
products:
  - product_key: samsung_health_v1
    insurer_key: samsung
    product_name_display: 삼성생명 건강보험
```

**Slim Card**:
```json
{
  "insurer": "samsung",
  "product_name": "삼성생명 건강보험",
  ...
}
```

---

## 3. variant_key Resolution Rules (ABSOLUTE)

### No-Variant Insurers (6)
- **samsung, meritz, hanwha, kb, hyundai, heungkuk**: `variant_key = null`

### LOTTE (Gender Variants)
- **Rule**: Must determine `LOTTE_MALE` or `LOTTE_FEMALE`
- **Default (Phase 1)**: `LOTTE_MALE` (first variant)
- **Future**: File path detection (e.g., `롯데_약관(남).page.jsonl`)

### DB (Age Variants)
- **Rule**: Must determine `DB_AGE_U40` (40세이하) or `DB_AGE_O40` (41세이상)
- **Default (Phase 1)**: `DB_AGE_U40` (first variant)
- **Future**: File path detection (e.g., `DB_가입설계서(40세이하)_2511.page.jsonl`)

**Failure Mode**:
- If variant required but cannot be determined → raise RuntimeError

---

## 4. Slim Card Schema (FINAL)

```python
@dataclass
class CoverageCardSlim:
    insurer: str
    coverage_code: Optional[str]
    coverage_name_canonical: Optional[str]
    coverage_name_raw: str
    mapping_status: str
    product_name: str                 # NEW (STEP NEXT-PRODUCT-1)
    variant_key: Optional[str] = None # NEW (STEP NEXT-PRODUCT-1)
    proposal_facts: Optional[dict] = None
    customer_view: Optional[CustomerView] = None
    refs: dict = field(default_factory=dict)
    kpi_summary: Optional[KPISummary] = None
    kpi_condition: Optional[KPIConditionSummary] = None
```

---

## 5. Execution Commands

### Single Insurer (Standard)
```bash
python -m pipeline.step5_build_cards.build_cards_slim --insurer samsung
```

### All 8 Insurers
```bash
for insurer in samsung meritz hanwha kb hyundai heungkuk; do
  python -m pipeline.step5_build_cards.build_cards_slim --insurer $insurer
done

# LOTTE/DB (variant-specific - Phase 1 workaround)
# Processed manually with direct file paths (see implementation notes)
```

---

## 6. Verification Results

**File Counts** (8×3 = 24 files):
- Slim cards: 8 ✅
- Proposal detail stores: 8 ✅
- Evidence stores: 8 ✅

**Product Metadata Verification**:
- **Samsung**: product_name="삼성생명 건강보험", variant_key=null ✅
- **Meritz**: product_name="메리츠화재 건강보험", variant_key=null ✅
- **Hanwha**: product_name="한화생명 건강보험", variant_key=null ✅
- **KB**: product_name="KB손해보험 건강보험", variant_key=null ✅
- **Hyundai**: product_name="현대해상 건강보험", variant_key=null ✅
- **Heungkuk**: product_name="흥국생명 건강보험", variant_key=null ✅
- **LOTTE**: product_name="롯데손해보험 건강보험", variant_key="LOTTE_MALE" ✅
- **DB**: product_name="DB손해보험 건강보험", variant_key="DB_AGE_U40" ✅

**Coverage Counts**:
- Samsung: 31 coverages
- Meritz: 37 coverages
- Hanwha: 32 coverages
- KB: 42 coverages
- Hyundai: 36 coverages
- Heungkuk: 35 coverages
- LOTTE: 30 coverages (MALE variant)
- DB: 30 coverages (U40 variant)

---

## 7. Known Limitations (Phase 1)

### LOTTE/DB Variant Handling
- **Current**: Default to first variant (LOTTE_MALE, DB_AGE_U40)
- **Issue**: CLI doesn't support `--variant` flag
- **Workaround**: Direct function call with variant-specific file paths
- **Future (Phase 2)**: Add `--variant` CLI argument + auto-detection from file paths

**Rationale**: Phase 1 focuses on SSOT establishment. Full variant switching is a Phase 2 operational enhancement.

---

## 8. SSOT Contract

**Input SSOT**:
```
data/metadata/products.yml
```

**Output SSOT** (product_name + variant_key in ALL cards):
```
data/compare/{insurer}_coverage_cards_slim.jsonl
```

**Loading SSOT** (runtime):
```python
# apps/api/store_loader.py (already exists)
# Reads product_name + variant_key from slim cards
```

**Display SSOT** (future - Phase 1 wiring TBD):
```
# EX2/EX3/EX4 composers can now access:
# card_slim.product_name
# card_slim.variant_key
```

---

## 9. Regression Prevention

**Schema Changes**:
- `CoverageCardSlim.product_name` is REQUIRED (no default)
- `CoverageCardSlim.variant_key` is OPTIONAL (null allowed)

**Backward Compatibility**:
- Old slim cards (without product_name) will fail to load → INTENTIONAL (forces regeneration)
- `from_dict()` requires `product_name` in data

**Future Changes**:
- ❌ NO product_name guessing/inference
- ❌ NO variant_key modification after generation
- ❌ NO products.yml edits without regenerating slim cards

---

## 10. Definition of Done

- [x] Slim card schema includes product_name + variant_key
- [x] products.yml loader implemented
- [x] 8 insurers all have product_name in slim cards
- [x] LOTTE has variant_key="LOTTE_MALE"
- [x] DB has variant_key="DB_AGE_U40"
- [x] 8×3 = 24 files generated successfully
- [x] No hardcoded product names in pipeline code
- [x] RuntimeError on products.yml mapping failure
- [x] Documentation complete

---

## 11. Next Steps (Phase 2+)

**Immediate (Phase 2 - Data Loading)**:
- Verify runtime loading (apps/api/store_loader.py) handles new fields
- Add product_name to EX2/EX3/EX4 responses (minimal wiring)
- Customer test scenarios (4 scenarios - see OPS-CYCLE-01)

**Future (Phase 3 - Variant Expansion)**:
- Add `--variant` CLI flag to build_cards_slim.py
- Auto-detect variant from file paths
- Support multi-variant output (e.g., lotte_male_coverage_cards_slim.jsonl)

**Future (Phase 4 - Product Family)**:
- Add product version tracking (v1, v2)
- Handle product deprecation/replacement
- Support cross-product comparison

---

**LOCK STATUS**: ✅ FINAL (Schema + Injection Logic)
**NEXT PHASE**: Phase 2 (Runtime Loading + Display Wiring)
