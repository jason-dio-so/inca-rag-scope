# PRODUCT VARIANT METADATA SPECIFICATION – inca-rag-scope

**Version**: 1.0
**Date**: 2025-12-28
**Status**: DESIGN SPECIFICATION (SSOT Definition)

---

## 0. PURPOSE

Define the **Single Source of Truth (SSOT)** for product, variant, and document metadata, eliminating all filename-based inference and insurer-specific if-else logic from pipelines.

**Scope**: Metadata schema, examples (LOTTE, DB), validation rules.
**Out of Scope**: Code implementation, database creation, data population scripts.

---

## 1. PROBLEM STATEMENT

### 1.1 Current Issues

**Issue 1**: Variant determination uses filename parsing:
```python
# ❌ PROHIBITED
if "(남)" in filename:
    variant_id = 'lotte_male'
elif "(여)" in filename:
    variant_id = 'lotte_female'
```

**Issue 2**: Insurer-specific branching:
```python
# ❌ PROHIBITED
if insurer == 'lotte':
    # Gender-based logic
elif insurer == 'db':
    # Age-based logic
```

**Issue 3**: Document structure assumptions:
```python
# ❌ PROHIBITED
if insurer == 'kb':
    scope_table_location = 'page_3_table_2'
```

### 1.2 Required Solution

**Single metadata file** (`products.yaml`) that declares:
- Which documents belong to which variant
- Document structure profiles
- Insurer/product/variant relationships

**Zero inference**: All pipeline/loader code reads metadata ONLY, no parsing/guessing.

---

## 2. METADATA SCHEMA

### 2.1 Top-Level Structure

```yaml
insurers:
  - insurer_key: STRING           # Unique identifier (e.g., 'lotte', 'db', 'kb')
    insurer_name_kr: STRING       # Korean name (e.g., '롯데손해보험')
    insurer_type: STRING          # Type (e.g., '손해보험', '생명보험')
    products: [Product]           # List of products

Product:
  product_key: STRING             # Unique identifier (e.g., 'lotte_health_2024')
  product_name_raw: STRING        # Product name from documents
  product_name_display: STRING    # Display name for reports
  has_variants: BOOLEAN           # TRUE if product has variants, FALSE otherwise
  variants: [Variant]             # List of variants (empty if has_variants=FALSE)
  documents: [Document]           # List of documents

Variant:
  variant_key: STRING             # Unique identifier (e.g., 'MALE', 'FEMALE', 'U40', 'O40')
  variant_display_name: STRING   # Display name (e.g., '남', '여', '40세이하', '40세이상')
  variant_attrs: MAP              # Additional attributes (e.g., {"gender": "M", "age_range": "20-39"})

Document:
  doc_type: STRING                # Document type ('약관', '사업방법서', '상품요약서', '가입설계서')
  file_path: STRING               # Absolute or relative path to document
  variant_key: STRING|NULL        # Variant this document belongs to (NULL if no variant)
  structure_type: STRING          # Document structure profile (e.g., 'standard', 'kb_profile', 'meritz_profile')
```

### 2.2 Minimal Required Fields

**Insurer**:
- `insurer_key` (PK)
- `insurer_name_kr`
- `products[]`

**Product**:
- `product_key` (PK within insurer)
- `product_name_display`
- `has_variants`
- `variants[]` (required if `has_variants=TRUE`)
- `documents[]`

**Variant**:
- `variant_key` (PK within product)
- `variant_display_name`

**Document**:
- `doc_type`
- `file_path`
- `variant_key` (required if product `has_variants=TRUE`)

---

## 3. CANONICAL EXAMPLES

### 3.1 LOTTE (Gender Variants - ALL Documents Separated)

**Requirement**: LOTTE has separate PDFs for Male/Female across ALL doc types.

```yaml
insurers:
  - insurer_key: lotte
    insurer_name_kr: 롯데손해보험
    insurer_type: 손해보험
    products:
      - product_key: lotte_health_2024
        product_name_raw: 롯데 Super Health 보험
        product_name_display: 롯데 슈퍼헬스
        has_variants: true

        variants:
          - variant_key: MALE
            variant_display_name: 남
            variant_attrs:
              gender: M

          - variant_key: FEMALE
            variant_display_name: 여
            variant_attrs:
              gender: F

        documents:
          # Male documents
          - doc_type: 약관
            file_path: data/sources/insurers/lotte/policy/lotte_policy_male.pdf
            variant_key: MALE
            structure_type: standard

          - doc_type: 사업방법서
            file_path: data/sources/insurers/lotte/business/lotte_business_male.pdf
            variant_key: MALE
            structure_type: standard

          - doc_type: 상품요약서
            file_path: data/sources/insurers/lotte/summary/lotte_summary_male.pdf
            variant_key: MALE
            structure_type: standard

          - doc_type: 가입설계서
            file_path: data/sources/insurers/lotte/proposal/lotte_proposal_male.pdf
            variant_key: MALE
            structure_type: standard

          # Female documents
          - doc_type: 약관
            file_path: data/sources/insurers/lotte/policy/lotte_policy_female.pdf
            variant_key: FEMALE
            structure_type: standard

          - doc_type: 사업방법서
            file_path: data/sources/insurers/lotte/business/lotte_business_female.pdf
            variant_key: FEMALE
            structure_type: standard

          - doc_type: 상품요약서
            file_path: data/sources/insurers/lotte/summary/lotte_summary_female.pdf
            variant_key: FEMALE
            structure_type: standard

          - doc_type: 가입설계서
            file_path: data/sources/insurers/lotte/proposal/lotte_proposal_female.pdf
            variant_key: FEMALE
            structure_type: standard
```

**Key Points**:
- ✅ All 4 doc types have separate files for MALE/FEMALE
- ✅ `variant_key` explicitly set for every document
- ✅ No filename parsing required
- ✅ Pipeline reads `variant_key` directly from metadata

---

### 3.2 DB (Age Variants - Partial Separation)

**Requirement**: DB has age-based variants (U40/O40) for 가입설계서 ONLY. Other doc types are shared.

```yaml
insurers:
  - insurer_key: db
    insurer_name_kr: DB손해보험
    insurer_type: 손해보험
    products:
      - product_key: db_life_2024
        product_name_raw: DB 무배당 실속건강보험
        product_name_display: DB 실속건강
        has_variants: true

        variants:
          - variant_key: U40
            variant_display_name: 40세이하
            variant_attrs:
              age_range: "20-39"

          - variant_key: O40
            variant_display_name: 40세이상
            variant_attrs:
              age_range: "40-79"

        documents:
          # Shared documents (no variant)
          - doc_type: 약관
            file_path: data/sources/insurers/db/policy/db_policy.pdf
            variant_key: null
            structure_type: standard

          - doc_type: 사업방법서
            file_path: data/sources/insurers/db/business/db_business.pdf
            variant_key: null
            structure_type: standard

          - doc_type: 상품요약서
            file_path: data/sources/insurers/db/summary/db_summary.pdf
            variant_key: null
            structure_type: standard

          # Age-specific proposals
          - doc_type: 가입설계서
            file_path: data/sources/insurers/db/proposal/db_proposal_u40.pdf
            variant_key: U40
            structure_type: standard

          - doc_type: 가입설계서
            file_path: data/sources/insurers/db/proposal/db_proposal_o40.pdf
            variant_key: O40
            structure_type: standard
```

**Key Points**:
- ✅ 약관/사업방법서/상품요약서 have `variant_key: null` (shared)
- ✅ 가입설계서 has separate files for U40/O40
- ✅ No page-range-based inference required
- ✅ Pipeline knows which document belongs to which variant from metadata

---

### 3.3 KB/Meritz (No Variants)

**Requirement**: Single product, no variants, all documents shared.

```yaml
insurers:
  - insurer_key: kb
    insurer_name_kr: KB손해보험
    insurer_type: 손해보험
    products:
      - product_key: kb_health_2024
        product_name_raw: KB 무배당 건강보험
        product_name_display: KB 건강보험
        has_variants: false
        variants: []

        documents:
          - doc_type: 약관
            file_path: data/sources/insurers/kb/policy/kb_policy.pdf
            variant_key: null
            structure_type: kb_profile

          - doc_type: 사업방법서
            file_path: data/sources/insurers/kb/business/kb_business.pdf
            variant_key: null
            structure_type: kb_profile

          - doc_type: 상품요약서
            file_path: data/sources/insurers/kb/summary/kb_summary.pdf
            variant_key: null
            structure_type: kb_profile

          - doc_type: 가입설계서
            file_path: data/sources/insurers/kb/proposal/kb_proposal.pdf
            variant_key: null
            structure_type: kb_profile
```

**Key Points**:
- ✅ `has_variants: false`
- ✅ `variants: []` (empty list)
- ✅ All documents have `variant_key: null`
- ✅ `structure_type: kb_profile` (document structure profile)

---

## 4. VALIDATION RULES

### 4.1 Uniqueness Constraints

**Rule 1**: `(insurer_key, product_key)` MUST be unique.

**Rule 2**: `(insurer_key, product_key, variant_key)` MUST be unique.

**Rule 3**: `(insurer_key, product_key, doc_type, variant_key)` MUST be unique.

**Rule 4**: `file_path` MUST be unique across all documents.

### 4.2 Referential Integrity

**Rule 5**: If `has_variants = true`, `variants` list MUST NOT be empty.

**Rule 6**: If `has_variants = false`, all documents MUST have `variant_key: null`.

**Rule 7**: If `has_variants = true`, all documents MUST have a valid `variant_key` (exists in `variants` list) OR `null` (shared document).

**Rule 8**: Every `document.variant_key` (if not null) MUST exist in the product's `variants` list.

### 4.3 Completeness Constraints

**Rule 9**: Every product MUST have at least 1 document of type `가입설계서`.

**Rule 10**: Every insurer MUST have at least 1 product.

**Rule 11**: If a product has variants, at least 1 variant MUST have a `가입설계서` document.

### 4.4 Prohibited Patterns

**❌ FORBIDDEN: Filename-based inference**
```yaml
# WRONG: variant_key determined by filename
documents:
  - doc_type: 가입설계서
    file_path: lotte_proposal_(남).pdf
    variant_key: null  # WRONG! Must explicitly set variant_key
```

**❌ FORBIDDEN: Variant missing for multi-variant product**
```yaml
# WRONG: has_variants=true but document has no variant_key
products:
  - product_key: lotte_health_2024
    has_variants: true
    variants: [MALE, FEMALE]
    documents:
      - doc_type: 가입설계서
        file_path: lotte_proposal.pdf
        variant_key: null  # WRONG! Must be MALE or FEMALE
```

**✅ CORRECT: Explicit variant assignment**
```yaml
documents:
  - doc_type: 가입설계서
    file_path: data/sources/insurers/lotte/proposal/lotte_proposal_male.pdf
    variant_key: MALE  # Explicit assignment
```

---

## 5. METADATA LOADING STRATEGY

### 5.1 Pipeline Integration

**STEP 1-7 (File-based pipeline)**:
1. Read `products.yaml`
2. For each insurer/product/document, extract PDF
3. Tag extracted data with `(insurer_key, product_key, variant_key)` from metadata
4. Write to scope CSV, evidence_pack JSONL with variant_key column

**STEP 9 (DB loader)**:
1. Read `products.yaml`
2. Populate `insurer`, `product`, `product_variant` tables
3. Read scope CSV with `variant_key` column
4. Match `variant_key` from CSV to `product_variant.variant_key` in DB
5. No filename parsing, no if-else branching

### 5.2 Metadata-Driven Workflow

```
products.yaml (SSOT)
    ↓
Pipeline reads metadata
    ↓
Extract PDF → Tag with (insurer_key, product_key, variant_key)
    ↓
Write to scope CSV with variant_key column
    ↓
DB loader reads scope CSV → Lookup variant_id from product_variant table
    ↓
Insert into coverage_instance with variant_id (FK)
```

**Zero inference required**.

---

## 6. STRUCTURE_TYPE (OPTIONAL)

### 6.1 Purpose

`structure_type` allows metadata to pre-declare document structure profiles (e.g., KB/Meritz have different table layouts).

### 6.2 Usage

**Option 1**: Pre-define structure types in metadata
```yaml
documents:
  - doc_type: 약관
    file_path: kb_policy.pdf
    structure_type: kb_profile  # Predefined
```

**Option 2**: Auto-detect structure type, store in `doc_structure_profile` table
- Metadata MAY omit `structure_type`
- Pipeline auto-detects and writes to DB
- STEP 9 loader reads from DB

**Recommendation**: Use Option 1 for known insurers (KB, Meritz), Option 2 for future insurers.

---

## 7. EXAMPLE QUERIES (CONCEPTUAL)

### 7.1 Query: Find all documents for LOTTE MALE variant

```python
# Pseudocode
products = load_yaml('products.yaml')
lotte = products.insurers['lotte']
lotte_health = lotte.products['lotte_health_2024']
male_docs = [
    doc for doc in lotte_health.documents
    if doc.variant_key == 'MALE'
]
```

**Result**:
```
약관: data/sources/insurers/lotte/policy/lotte_policy_male.pdf
사업방법서: data/sources/insurers/lotte/business/lotte_business_male.pdf
상품요약서: data/sources/insurers/lotte/summary/lotte_summary_male.pdf
가입설계서: data/sources/insurers/lotte/proposal/lotte_proposal_male.pdf
```

### 7.2 Query: Find all shared documents for DB product

```python
db = products.insurers['db']
db_life = db.products['db_life_2024']
shared_docs = [
    doc for doc in db_life.documents
    if doc.variant_key is None
]
```

**Result**:
```
약관: data/sources/insurers/db/policy/db_policy.pdf
사업방법서: data/sources/insurers/db/business/db_business.pdf
상품요약서: data/sources/insurers/db/summary/db_summary.pdf
```

---

## 8. MIGRATION FROM CURRENT STATE

### 8.1 Current State (Filename-based)

```
data/sources/insurers/lotte/가입설계서/
  롯데_가입설계서(남).pdf
  롯데_가입설계서(여).pdf
```

**Code**:
```python
# ❌ Current approach
if "(남)" in filename:
    variant = 'male'
```

### 8.2 New State (Metadata-driven)

```yaml
# products.yaml
documents:
  - doc_type: 가입설계서
    file_path: data/sources/insurers/lotte/proposal/lotte_proposal_male.pdf
    variant_key: MALE

  - doc_type: 가입설계서
    file_path: data/sources/insurers/lotte/proposal/lotte_proposal_female.pdf
    variant_key: FEMALE
```

**Code**:
```python
# ✅ New approach
metadata = load_yaml('products.yaml')
for doc in metadata.get_documents(insurer='lotte', product='lotte_health_2024'):
    variant_key = doc.variant_key  # Direct read from metadata
```

### 8.3 Migration Steps

1. Create `products.yaml` with all existing insurers
2. Update pipeline to read `products.yaml` instead of scanning directories
3. Add `variant_key` column to scope CSV output
4. Update STEP 9 loader to read `variant_key` from CSV
5. Remove all filename parsing code
6. Remove all insurer-specific if-else branches

---

## 9. VALIDATION CHECKLIST

### 9.1 Pre-Merge Checklist

Before merging `products.yaml` changes:

- [ ] All `(insurer_key, product_key)` combinations are unique
- [ ] All `(insurer_key, product_key, variant_key)` combinations are unique
- [ ] All `file_path` values are unique
- [ ] All `variant_key` references exist in `variants` list
- [ ] Products with `has_variants=true` have at least 1 variant
- [ ] Products with `has_variants=false` have all documents with `variant_key: null`
- [ ] Every product has at least 1 `가입설계서` document
- [ ] No filename-based inference logic in metadata
- [ ] LOTTE example includes all 4 doc types for MALE/FEMALE
- [ ] DB example shows shared docs with `variant_key: null`

### 9.2 Automated Validation Script (Future)

```python
# Pseudocode for validation script
def validate_metadata(yaml_path):
    metadata = load_yaml(yaml_path)

    # Rule 1-4: Uniqueness
    check_unique_insurers()
    check_unique_products()
    check_unique_variants()
    check_unique_file_paths()

    # Rule 5-8: Referential integrity
    check_variants_not_empty_if_has_variants()
    check_all_variant_keys_valid()

    # Rule 9-11: Completeness
    check_every_product_has_proposal()
    check_every_insurer_has_product()

    # Prohibited patterns
    check_no_null_variant_for_multi_variant_product()

    return validation_report
```

---

## 10. GOVERNANCE (CROSS-REFERENCE)

See `docs/foundation/METADATA_GOVERNANCE.md` for:
- Change control process (PR-based)
- Review/approval workflow
- Rollback procedures
- SSOT enforcement rules

---

## CONCLUSION

This specification defines the **Single Source of Truth** for product/variant/document metadata.

**Key Principles**:
1. **Zero inference**: No filename parsing, no page-range guessing
2. **Data-driven**: All variant assignments come from metadata
3. **SSOT**: `products.yaml` is the canonical source
4. **Validation**: Automated checks enforce integrity rules

**Next Steps**:
1. Create `data/metadata/products.yaml` with LOTTE/DB examples
2. Define governance rules in `METADATA_GOVERNANCE.md`
3. Update pipeline to read metadata
4. Update STEP 9 loader to use metadata-driven variant assignment

**Status**: DESIGN LOCKED. Ready for implementation.
