# STEP 9: DB POPULATION SPECIFICATION – inca-rag-scope

**Version**: 1.0
**Date**: 2025-12-28
**Status**: DESIGN SPECIFICATION (No Implementation)

---

## 0. PURPOSE

Define how existing JSONL/CSV/Excel outputs (from STEP 1-7) are loaded into the DB.

**Scope**: Load sequence, idempotency, failure recovery, validation.
**Out of Scope**: Code implementation, database creation, migration execution.

---

## 1. OVERVIEW

### 1.1 Objective

Load all data from **file-based pipeline outputs** (STEP 1-7) into **DB tables** (9 tables).

### 1.2 Input Sources

| Source File | Table(s) Populated | STEP Origin |
|-------------|-------------------|-------------|
| metadata.json (manual) | insurer, product, product_variant, doc_structure_profile | MANUAL |
| data/sources/insurers/{insurer}/{doc_type}/*.pdf | document | STEP 2-α |
| data/sources/mapping/담보명mapping자료.xlsx | coverage_canonical | MANUAL |
| data/scope/{insurer}_scope_mapped.csv | coverage_instance | STEP 2 |
| data/evidence_pack/{insurer}_pack.jsonl | evidence_ref | STEP 3 |
| data/compare/{insurer}_coverage_cards.jsonl | amount_fact | STEP 5 |

### 1.3 Output

**Database**: Fully populated 9 tables with all FK relationships intact.

**Validation**: Row counts, FK integrity, constraint checks.

---

## 2. STEP 9 LOAD SEQUENCE

### 2.1 Dependency Order

```
STEP 9.1: Load Metadata (insurer, product, product_variant, doc_structure_profile)
    ↓
STEP 9.2: Load Documents (document)
    ↓
STEP 9.3: Load Coverage Canonical (coverage_canonical)
    ↓
STEP 9.4: Load Coverage Instances (coverage_instance)
    ↓
STEP 9.5: Load Evidence (evidence_ref)
    ↓
STEP 9.6: Load Amounts (amount_fact)
    ↓
STEP 9.7: Validation
```

**Rationale**: Load parents before children (FK constraint satisfaction).

---

## 3. STEP 9.1: Load Metadata

### 3.1 Input

**File**: `data/metadata/metadata.json` (MANUAL ENTRY)

**Schema**:
```json
{
  "insurers": [
    {
      "insurer_id": "samsung",
      "insurer_name_kr": "삼성화재",
      "insurer_type": "손해보험"
    }
  ],
  "products": [
    {
      "product_id": "samsung_product_001",
      "insurer_id": "samsung",
      "product_name": "Samsung Health Insurance 2024",
      "doc_structure_profile_id": "standard_profile_001"
    }
  ],
  "product_variants": [
    {
      "variant_id": "lotte_male",
      "product_id": "lotte_product_001",
      "variant_key": "MALE",
      "variant_display_name": "남",
      "doc_structure_profile_id": "lotte_profile_001"
    }
  ],
  "doc_structure_profiles": [
    {
      "profile_id": "standard_profile_001",
      "profile_name": "Standard Document Profile",
      "scope_table_location": "page_2_table_1",
      "amount_table_location": "page_3_table_1",
      "metadata": {
        "scope_keywords": ["보장내용", "담보"],
        "amount_keywords": ["가입금액", "보험가입금액"]
      }
    }
  ]
}
```

### 3.2 Load Logic

```sql
-- Load doc_structure_profiles FIRST (no FK dependencies)
INSERT INTO doc_structure_profile (profile_id, profile_name, scope_table_location, amount_table_location, metadata)
SELECT
  profile_id,
  profile_name,
  scope_table_location,
  amount_table_location,
  metadata::jsonb
FROM metadata_json.doc_structure_profiles;

-- Load insurers
INSERT INTO insurer (insurer_id, insurer_name_kr, insurer_type)
SELECT
  insurer_id,
  insurer_name_kr,
  insurer_type
FROM metadata_json.insurers;

-- Load products (references insurer + doc_structure_profile)
INSERT INTO product (product_id, insurer_id, product_name, doc_structure_profile_id)
SELECT
  product_id,
  insurer_id,
  product_name,
  doc_structure_profile_id
FROM metadata_json.products;

-- Load product_variants (references product + doc_structure_profile)
INSERT INTO product_variant (variant_id, product_id, variant_key, variant_display_name, doc_structure_profile_id)
SELECT
  variant_id,
  product_id,
  variant_key,
  variant_display_name,
  doc_structure_profile_id
FROM metadata_json.product_variants;
```

### 3.3 Idempotency

**Strategy**: UPSERT (INSERT ON CONFLICT DO UPDATE)

```sql
INSERT INTO insurer (insurer_id, insurer_name_kr, insurer_type)
VALUES (?, ?, ?)
ON CONFLICT (insurer_id) DO UPDATE
SET insurer_name_kr = EXCLUDED.insurer_name_kr,
    insurer_type = EXCLUDED.insurer_type;
```

**Rationale**: Allow re-running STEP 9.1 without duplicate errors.

### 3.4 Validation

```sql
-- Check row counts
SELECT COUNT(*) AS insurer_count FROM insurer;
SELECT COUNT(*) AS product_count FROM product;
SELECT COUNT(*) AS variant_count FROM product_variant;
SELECT COUNT(*) AS profile_count FROM doc_structure_profile;

-- Check FK integrity
SELECT * FROM product WHERE insurer_id NOT IN (SELECT insurer_id FROM insurer);
-- Expected: 0 rows
```

---

## 4. STEP 9.2: Load Documents

### 4.1 Input

**Files**: `data/evidence_text/{insurer}/{doc_type}/*.page.jsonl`

**Example**:
```
data/evidence_text/samsung/약관/삼성화재_약관.page.jsonl
data/evidence_text/samsung/사업방법서/삼성화재_사업방법서.page.jsonl
data/evidence_text/samsung/상품요약서/삼성화재_상품요약서.page.jsonl
data/evidence_text/samsung/가입설계서/삼성화재_가입설계서.page.jsonl
```

### 4.2 Load Logic

```python
# Pseudocode
for insurer in insurers:
    for doc_type in ['약관', '사업방법서', '상품요약서', '가입설계서']:
        page_jsonl_files = glob(f"data/evidence_text/{insurer}/{doc_type}/*.page.jsonl")
        for file_path in page_jsonl_files:
            page_count = count_lines(file_path)  # Number of pages

            # Get product_id for this insurer
            product_id = db.query("SELECT product_id FROM product WHERE insurer_id = ?", insurer)

            # Insert document
            db.execute("""
                INSERT INTO document (insurer_id, product_id, doc_type, file_path, page_count, extracted_at)
                VALUES (?, ?, ?, ?, ?, NOW())
                ON CONFLICT (file_path) DO UPDATE
                SET page_count = EXCLUDED.page_count
            """, insurer, product_id, doc_type, file_path, page_count)
```

### 4.3 Idempotency

**Strategy**: UPSERT on `file_path` (unique constraint)

```sql
INSERT INTO document (insurer_id, product_id, doc_type, file_path, page_count, extracted_at)
VALUES (?, ?, ?, ?, ?, NOW())
ON CONFLICT (file_path) DO UPDATE
SET page_count = EXCLUDED.page_count,
    extracted_at = NOW();
```

### 4.4 Validation

```sql
-- Check document counts per insurer
SELECT insurer_id, doc_type, COUNT(*) AS doc_count
FROM document
GROUP BY insurer_id, doc_type;

-- Expected: 4 doc_types per insurer (약관, 사업방법서, 상품요약서, 가입설계서)

-- Check FK integrity
SELECT * FROM document WHERE product_id NOT IN (SELECT product_id FROM product);
-- Expected: 0 rows
```

---

## 5. STEP 9.3: Load Coverage Canonical

### 5.1 Input

**File**: `data/sources/mapping/담보명mapping자료.xlsx`

**Sheet**: "담보명mapping" (or similar)

**Columns**:
- `coverage_code` (A4200_1)
- `coverage_name_canonical` (암진단비(유사암제외))
- `coverage_category` (진단)
- `payment_event` (암 진단 확정 시)

### 5.2 Load Logic

```python
# Pseudocode
import openpyxl

# Read Excel
wb = openpyxl.load_workbook("data/sources/mapping/담보명mapping자료.xlsx")
ws = wb["담보명mapping"]

# Extract rows
for row in ws.iter_rows(min_row=2, values_only=True):
    coverage_code = row[0]
    coverage_name_canonical = row[1]
    coverage_category = row[2]
    payment_event = row[3]

    # Insert into DB
    db.execute("""
        INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical, coverage_category, payment_event)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (coverage_code) DO UPDATE
        SET coverage_name_canonical = EXCLUDED.coverage_name_canonical,
            coverage_category = EXCLUDED.coverage_category,
            payment_event = EXCLUDED.payment_event
    """, coverage_code, coverage_name_canonical, coverage_category, payment_event)
```

### 5.3 Idempotency

**Strategy**: UPSERT on `coverage_code` (PK)

```sql
INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical, coverage_category, payment_event)
VALUES (?, ?, ?, ?)
ON CONFLICT (coverage_code) DO UPDATE
SET coverage_name_canonical = EXCLUDED.coverage_name_canonical,
    coverage_category = EXCLUDED.coverage_category,
    payment_event = EXCLUDED.payment_event;
```

### 5.4 Validation

```sql
-- Check row count
SELECT COUNT(*) AS canonical_count FROM coverage_canonical;
-- Expected: ~100-200 rows (depends on mapping Excel)

-- Check coverage_code format
SELECT coverage_code FROM coverage_canonical WHERE coverage_code !~ '^[A-Z]\d{4}(_\d+)?$';
-- Expected: 0 rows (all codes match format)
```

---

## 6. STEP 9.4: Load Coverage Instances

### 6.1 Input

**File**: `data/scope/{insurer}_scope_mapped.csv`

**Schema**:
```csv
coverage_name_raw,coverage_code,coverage_name_canonical,mapping_status,match_type,source_page
암 진단비(유사암 제외),A4200_1,암진단비(유사암제외),matched,normalized_alias,3
```

### 6.2 Load Logic

```python
# Pseudocode
import csv

for insurer in insurers:
    scope_file = f"data/scope/{insurer}_scope_mapped.csv"

    # Get product_id and variant_id for this insurer
    product_id = db.query("SELECT product_id FROM product WHERE insurer_id = ?", insurer)

    # Check if product has variants
    variants = db.query("SELECT variant_id, variant_key FROM product_variant WHERE product_id = ?", product_id)

    with open(scope_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coverage_name_raw = row['coverage_name_raw']
            coverage_code = row.get('coverage_code')  # May be NULL if unmatched
            mapping_status = row['mapping_status']
            match_type = row.get('match_type')
            source_page = row.get('source_page')

            # Determine variant_id (if applicable)
            if variants:
                # Multi-variant product (e.g., LOTTE, DB)
                # Need to determine which variant this coverage belongs to
                # Strategy: Use metadata or filename parsing
                # Example: LOTTE uses "(남)" / "(여)" in filename
                variant_id = determine_variant(insurer, coverage_name_raw, source_page)
            else:
                variant_id = None

            # Insert coverage_instance
            db.execute("""
                INSERT INTO coverage_instance (
                    insurer_id, product_id, variant_id, coverage_code,
                    coverage_name_raw, source_page, mapping_status, match_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (product_id, variant_id, coverage_code) DO UPDATE
                SET coverage_name_raw = EXCLUDED.coverage_name_raw,
                    source_page = EXCLUDED.source_page,
                    mapping_status = EXCLUDED.mapping_status,
                    match_type = EXCLUDED.match_type
            """, insurer, product_id, variant_id, coverage_code,
                coverage_name_raw, source_page, mapping_status, match_type)
```

### 6.3 Variant Determination Strategy

**LOTTE (Gender Variants)**:
```python
def determine_variant_lotte(coverage_name_raw, source_page, metadata):
    # Strategy 1: Filename contains "(남)" or "(여)"
    if "(남)" in metadata.get('filename', ''):
        return 'lotte_male'
    elif "(여)" in metadata.get('filename', ''):
        return 'lotte_female'

    # Strategy 2: Source page range
    # Male: pages 2-5, Female: pages 6-9 (hypothetical)
    if 2 <= source_page <= 5:
        return 'lotte_male'
    elif 6 <= source_page <= 9:
        return 'lotte_female'

    raise ValueError(f"Cannot determine variant for LOTTE: {coverage_name_raw}")
```

**DB (Age Variants)**:
```python
def determine_variant_db(coverage_name_raw, source_page, metadata):
    # Strategy: Source page range
    # Age 20-39: pages 3-5
    # Age 40-59: pages 6-8
    # Age 60-79: pages 9-11
    if 3 <= source_page <= 5:
        return 'db_age_20_39'
    elif 6 <= source_page <= 8:
        return 'db_age_40_59'
    elif 9 <= source_page <= 11:
        return 'db_age_60_79'

    raise ValueError(f"Cannot determine variant for DB: {coverage_name_raw}")
```

**KB/Meritz (No Variants)**:
```python
def determine_variant_kb_meritz(coverage_name_raw, source_page, metadata):
    return None  # No variants
```

### 6.4 Idempotency

**Strategy**: UPSERT on `(product_id, variant_id, coverage_code)`

```sql
INSERT INTO coverage_instance (
    insurer_id, product_id, variant_id, coverage_code,
    coverage_name_raw, source_page, mapping_status, match_type
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (product_id, variant_id, coverage_code) DO UPDATE
SET coverage_name_raw = EXCLUDED.coverage_name_raw,
    source_page = EXCLUDED.source_page,
    mapping_status = EXCLUDED.mapping_status,
    match_type = EXCLUDED.match_type;
```

### 6.5 Validation

```sql
-- Check coverage_instance counts per insurer
SELECT insurer_id, mapping_status, COUNT(*) AS instance_count
FROM coverage_instance
GROUP BY insurer_id, mapping_status;

-- Check FK integrity (coverage_code references coverage_canonical)
SELECT * FROM coverage_instance
WHERE mapping_status = 'matched'
  AND coverage_code NOT IN (SELECT coverage_code FROM coverage_canonical);
-- Expected: 0 rows

-- Check FK integrity (variant_id references product_variant)
SELECT * FROM coverage_instance
WHERE variant_id IS NOT NULL
  AND variant_id NOT IN (SELECT variant_id FROM product_variant);
-- Expected: 0 rows
```

---

## 7. STEP 9.5: Load Evidence

### 7.1 Input

**File**: `data/evidence_pack/{insurer}_pack.jsonl`

**Schema** (per line):
```json
{
  "insurer": "samsung",
  "coverage_name_raw": "암 진단비(유사암 제외)",
  "coverage_code": "A4200_1",
  "evidences": [
    {
      "doc_type": "약관",
      "file_path": "/path/to/약관.page.jsonl",
      "page": 7,
      "snippet": "제1조(보험금의 지급사유) ...",
      "match_keyword": "암진단비(유사암제외)"
    }
  ]
}
```

### 7.2 Load Logic

```python
# Pseudocode
import json

for insurer in insurers:
    evidence_file = f"data/evidence_pack/{insurer}_pack.jsonl"

    with open(evidence_file, 'r') as f:
        for line in f:
            pack = json.loads(line)

            coverage_code = pack['coverage_code']
            coverage_name_raw = pack['coverage_name_raw']

            # Get coverage_instance_id
            # Match on (insurer_id, coverage_code, coverage_name_raw)
            coverage_instance_id = db.query("""
                SELECT instance_id FROM coverage_instance
                WHERE insurer_id = ? AND coverage_code = ? AND coverage_name_raw = ?
            """, insurer, coverage_code, coverage_name_raw)

            if not coverage_instance_id:
                # Coverage instance not found (should not happen if STEP 9.4 succeeded)
                raise ValueError(f"Coverage instance not found: {insurer}, {coverage_code}")

            # Process evidences
            for rank, evidence in enumerate(pack['evidences'], start=1):
                doc_type = evidence['doc_type']
                file_path = evidence['file_path']
                page = evidence['page']
                snippet = evidence['snippet']
                match_keyword = evidence.get('match_keyword')

                # Get document_id
                document_id = db.query("SELECT document_id FROM document WHERE file_path = ?", file_path)

                if not document_id:
                    # Document not found (should not happen if STEP 9.2 succeeded)
                    raise ValueError(f"Document not found: {file_path}")

                # Insert evidence_ref
                db.execute("""
                    INSERT INTO evidence_ref (
                        coverage_instance_id, document_id, doc_type, page, snippet, match_keyword, rank
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (coverage_instance_id, document_id, page, snippet) DO UPDATE
                    SET rank = EXCLUDED.rank,
                        match_keyword = EXCLUDED.match_keyword
                """, coverage_instance_id, document_id, doc_type, page, snippet, match_keyword, rank)
```

### 7.3 Idempotency

**Strategy**: UPSERT on `(coverage_instance_id, document_id, page, snippet)`

**Rationale**: Same snippet on same page = same evidence (no duplicates)

```sql
INSERT INTO evidence_ref (
    coverage_instance_id, document_id, doc_type, page, snippet, match_keyword, rank
)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (coverage_instance_id, document_id, page, snippet) DO UPDATE
SET rank = EXCLUDED.rank,
    match_keyword = EXCLUDED.match_keyword;
```

**Note**: This requires adding a UNIQUE constraint:
```sql
ALTER TABLE evidence_ref
ADD CONSTRAINT unique_evidence_snippet UNIQUE (coverage_instance_id, document_id, page, snippet);
```

### 7.4 Validation

```sql
-- Check evidence counts per insurer
SELECT ci.insurer_id, er.doc_type, COUNT(*) AS evidence_count
FROM evidence_ref er
JOIN coverage_instance ci ON er.coverage_instance_id = ci.instance_id
GROUP BY ci.insurer_id, er.doc_type;

-- Check FK integrity (coverage_instance_id)
SELECT * FROM evidence_ref
WHERE coverage_instance_id NOT IN (SELECT instance_id FROM coverage_instance);
-- Expected: 0 rows

-- Check FK integrity (document_id)
SELECT * FROM evidence_ref
WHERE document_id NOT IN (SELECT document_id FROM document);
-- Expected: 0 rows

-- Check non-empty snippets
SELECT * FROM evidence_ref WHERE length(snippet) = 0;
-- Expected: 0 rows
```

---

## 8. STEP 9.6: Load Amounts

### 8.1 Input

**File**: `data/compare/{insurer}_coverage_cards.jsonl`

**Schema** (per line, focusing on `amount` field):
```json
{
  "insurer": "samsung",
  "coverage_code": "A4200_1",
  "coverage_name_raw": "암 진단비(유사암 제외)",
  "amount": {
    "status": "CONFIRMED",
    "value_text": "3000만원",
    "source_doc_type": "가입설계서",
    "source_priority": "PRIMARY",
    "evidence": {
      "file_path": "/path/to/가입설계서.page.jsonl",
      "page": 2,
      "snippet": "암진단비(유사암제외) 보험가입금액: 3,000만원"
    },
    "notes": ["계산금지", "가입설계서우선"]
  }
}
```

### 8.2 Load Logic

```python
# Pseudocode
import json

for insurer in insurers:
    cards_file = f"data/compare/{insurer}_coverage_cards.jsonl"

    with open(cards_file, 'r') as f:
        for line in f:
            card = json.loads(line)

            coverage_code = card['coverage_code']
            coverage_name_raw = card['coverage_name_raw']
            amount = card.get('amount')

            if not amount:
                # No amount field (should not happen if STEP 5 ran)
                continue

            # Get coverage_instance_id
            coverage_instance_id = db.query("""
                SELECT instance_id FROM coverage_instance
                WHERE insurer_id = ? AND coverage_code = ? AND coverage_name_raw = ?
            """, insurer, coverage_code, coverage_name_raw)

            if not coverage_instance_id:
                raise ValueError(f"Coverage instance not found: {insurer}, {coverage_code}")

            # Extract amount fields
            status = amount['status']
            value_text = amount.get('value_text')
            source_doc_type = amount.get('source_doc_type')
            source_priority = amount.get('source_priority')
            notes = amount.get('notes', [])

            # Get evidence_id (if CONFIRMED)
            evidence_id = None
            if status == 'CONFIRMED' and amount.get('evidence'):
                evidence_snippet = amount['evidence']['snippet']
                evidence_page = amount['evidence']['page']
                evidence_file_path = amount['evidence']['file_path']

                # Find matching evidence_ref
                evidence_id = db.query("""
                    SELECT er.evidence_id
                    FROM evidence_ref er
                    JOIN document d ON er.document_id = d.document_id
                    WHERE er.coverage_instance_id = ?
                      AND er.page = ?
                      AND er.snippet = ?
                      AND d.file_path = ?
                """, coverage_instance_id, evidence_page, evidence_snippet, evidence_file_path)

                if not evidence_id:
                    # Evidence not found - create it
                    document_id = db.query("SELECT document_id FROM document WHERE file_path = ?", evidence_file_path)
                    evidence_id = db.execute("""
                        INSERT INTO evidence_ref (
                            coverage_instance_id, document_id, doc_type, page, snippet, match_keyword, rank
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        RETURNING evidence_id
                    """, coverage_instance_id, document_id, source_doc_type, evidence_page, evidence_snippet, None, 99)

            # Insert amount_fact
            db.execute("""
                INSERT INTO amount_fact (
                    coverage_instance_id, evidence_id, status, value_text,
                    source_doc_type, source_priority, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (coverage_instance_id) DO UPDATE
                SET evidence_id = EXCLUDED.evidence_id,
                    status = EXCLUDED.status,
                    value_text = EXCLUDED.value_text,
                    source_doc_type = EXCLUDED.source_doc_type,
                    source_priority = EXCLUDED.source_priority,
                    notes = EXCLUDED.notes
            """, coverage_instance_id, evidence_id, status, value_text,
                source_doc_type, source_priority, json.dumps(notes))
```

### 8.3 Idempotency

**Strategy**: UPSERT on `coverage_instance_id` (1:1 relationship)

```sql
INSERT INTO amount_fact (
    coverage_instance_id, evidence_id, status, value_text,
    source_doc_type, source_priority, notes
)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (coverage_instance_id) DO UPDATE
SET evidence_id = EXCLUDED.evidence_id,
    status = EXCLUDED.status,
    value_text = EXCLUDED.value_text,
    source_doc_type = EXCLUDED.source_doc_type,
    source_priority = EXCLUDED.source_priority,
    notes = EXCLUDED.notes;
```

### 8.4 Validation

```sql
-- Check amount counts per insurer
SELECT ci.insurer_id, af.status, COUNT(*) AS amount_count
FROM amount_fact af
JOIN coverage_instance ci ON af.coverage_instance_id = ci.instance_id
GROUP BY ci.insurer_id, af.status;

-- Check CONFIRMED amounts have evidence
SELECT * FROM amount_fact
WHERE status = 'CONFIRMED' AND evidence_id IS NULL;
-- Expected: 0 rows

-- Check PRIMARY source is 가입설계서
SELECT * FROM amount_fact
WHERE source_priority = 'PRIMARY' AND source_doc_type != '가입설계서';
-- Expected: 0 rows

-- Check FK integrity (coverage_instance_id)
SELECT * FROM amount_fact
WHERE coverage_instance_id NOT IN (SELECT instance_id FROM coverage_instance);
-- Expected: 0 rows

-- Check FK integrity (evidence_id, if not NULL)
SELECT * FROM amount_fact
WHERE evidence_id IS NOT NULL
  AND evidence_id NOT IN (SELECT evidence_id FROM evidence_ref);
-- Expected: 0 rows
```

---

## 9. STEP 9.7: Validation

### 9.1 Row Count Validation

```sql
-- Insurer count (expected: 8)
SELECT COUNT(*) AS insurer_count FROM insurer;

-- Product count (expected: 8, one per insurer)
SELECT COUNT(*) AS product_count FROM product;

-- Variant count (expected: 0 for KB/Meritz, 2+ for LOTTE/DB)
SELECT COUNT(*) AS variant_count FROM product_variant;

-- Coverage canonical count (expected: ~100-200)
SELECT COUNT(*) AS canonical_count FROM coverage_canonical;

-- Coverage instance count (expected: ~300-400, 30-40 per insurer)
SELECT COUNT(*) AS instance_count FROM coverage_instance;

-- Evidence count (expected: ~1000-2000, 3-6 per coverage instance)
SELECT COUNT(*) AS evidence_count FROM evidence_ref;

-- Amount count (expected: equal to coverage_instance count)
SELECT COUNT(*) AS amount_count FROM amount_fact;
```

### 9.2 FK Integrity Validation

```sql
-- Run all FK checks
SELECT 'product.insurer_id' AS fk_check, COUNT(*) AS violation_count
FROM product WHERE insurer_id NOT IN (SELECT insurer_id FROM insurer)
UNION ALL
SELECT 'coverage_instance.coverage_code', COUNT(*)
FROM coverage_instance
WHERE mapping_status = 'matched'
  AND coverage_code NOT IN (SELECT coverage_code FROM coverage_canonical)
UNION ALL
SELECT 'evidence_ref.coverage_instance_id', COUNT(*)
FROM evidence_ref
WHERE coverage_instance_id NOT IN (SELECT instance_id FROM coverage_instance)
UNION ALL
SELECT 'amount_fact.evidence_id', COUNT(*)
FROM amount_fact
WHERE status = 'CONFIRMED'
  AND evidence_id NOT IN (SELECT evidence_id FROM evidence_ref);

-- Expected: All violation_count = 0
```

### 9.3 Business Logic Validation

```sql
-- Check CONFIRMED amounts have evidence
SELECT 'amount_confirmed_without_evidence' AS check_name, COUNT(*) AS violation_count
FROM amount_fact
WHERE status = 'CONFIRMED' AND evidence_id IS NULL

UNION ALL

-- Check PRIMARY source is 가입설계서
SELECT 'primary_not_from_proposal', COUNT(*)
FROM amount_fact
WHERE source_priority = 'PRIMARY' AND source_doc_type != '가입설계서'

UNION ALL

-- Check non-empty snippets
SELECT 'empty_snippet', COUNT(*)
FROM evidence_ref
WHERE length(snippet) = 0

UNION ALL

-- Check coverage_code format
SELECT 'invalid_coverage_code_format', COUNT(*)
FROM coverage_canonical
WHERE coverage_code !~ '^[A-Z]\d{4}(_\d+)?$';

-- Expected: All violation_count = 0
```

---

## 10. FAILURE RECOVERY

### 10.1 Partial Load Failure

**Scenario**: STEP 9.4 fails midway (e.g., variant determination error)

**Recovery**:
1. Rollback transaction (if using transactional load)
2. Fix variant determination logic
3. Re-run STEP 9.4 (idempotent UPSERT will update existing rows)

**Idempotency Guarantee**: UPSERT ensures no duplicates

### 10.2 FK Violation Failure

**Scenario**: STEP 9.5 fails due to missing coverage_instance_id

**Diagnosis**:
```sql
-- Find missing coverage_instances
SELECT DISTINCT coverage_code, coverage_name_raw
FROM evidence_pack_jsonl
WHERE (insurer_id, coverage_code, coverage_name_raw) NOT IN (
  SELECT insurer_id, coverage_code, coverage_name_raw
  FROM coverage_instance
);
```

**Recovery**:
1. Re-run STEP 9.4 to ensure all coverage_instances loaded
2. Re-run STEP 9.5

### 10.3 Constraint Violation Failure

**Scenario**: STEP 9.6 fails due to CHECK constraint (CONFIRMED without evidence)

**Diagnosis**:
```sql
-- Find CONFIRMED amounts without evidence
SELECT * FROM amount_fact_staging
WHERE status = 'CONFIRMED' AND evidence_id IS NULL;
```

**Recovery**:
1. Fix data in coverage_cards.jsonl (re-run STEP 5 if needed)
2. Re-run STEP 9.6

---

## 11. RE-RUN POLICY

### 11.1 Full Re-Run (Clean Slate)

**When**: Major schema change, data quality issue

**Steps**:
```sql
-- Drop all data (preserve schema)
TRUNCATE TABLE amount_fact CASCADE;
TRUNCATE TABLE evidence_ref CASCADE;
TRUNCATE TABLE coverage_instance CASCADE;
TRUNCATE TABLE coverage_canonical CASCADE;
TRUNCATE TABLE document CASCADE;
TRUNCATE TABLE product_variant CASCADE;
TRUNCATE TABLE product CASCADE;
TRUNCATE TABLE insurer CASCADE;
TRUNCATE TABLE doc_structure_profile CASCADE;

-- Re-run STEP 9.1 → 9.7
```

### 11.2 Incremental Re-Run (Partial Update)

**When**: Add new insurer, update amounts for one insurer

**Steps**:
```sql
-- Delete data for specific insurer
DELETE FROM amount_fact WHERE coverage_instance_id IN (
  SELECT instance_id FROM coverage_instance WHERE insurer_id = 'samsung'
);
DELETE FROM evidence_ref WHERE coverage_instance_id IN (
  SELECT instance_id FROM coverage_instance WHERE insurer_id = 'samsung'
);
DELETE FROM coverage_instance WHERE insurer_id = 'samsung';

-- Re-run STEP 9.4 → 9.6 for 'samsung' ONLY
```

### 11.3 Re-Run Decision Matrix

| Change Type | Re-Run Steps | Strategy |
|------------|-------------|----------|
| Add new insurer | 9.1, 9.2, 9.3, 9.4, 9.5, 9.6 | Incremental (UPSERT) |
| Update mapping Excel | 9.3, 9.4 | Incremental (UPSERT) |
| Update amounts for one insurer | 9.6 | Incremental (UPSERT) |
| Major schema change | ALL | Full re-run (TRUNCATE) |
| Fix variant determination | 9.4, 9.5, 9.6 | Incremental (UPSERT) |

---

## 12. CHECKPOINTS

### 12.1 Checkpoint Definition

**Checkpoint**: STEP 9.X completion marker

**Storage**: `load_checkpoints` table

```sql
CREATE TABLE load_checkpoints (
  checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  insurer_id TEXT NOT NULL,
  step_number TEXT NOT NULL,  -- '9.1', '9.2', etc.
  status TEXT NOT NULL CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED')),
  row_count INT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  error_message TEXT
);
```

### 12.2 Checkpoint Usage

```python
# Pseudocode
def run_step_9_4(insurer):
    # Record start
    db.execute("""
        INSERT INTO load_checkpoints (insurer_id, step_number, status)
        VALUES (?, '9.4', 'STARTED')
    """, insurer)

    try:
        # Load coverage instances
        load_coverage_instances(insurer)

        # Record completion
        db.execute("""
            UPDATE load_checkpoints
            SET status = 'COMPLETED',
                completed_at = NOW(),
                row_count = (SELECT COUNT(*) FROM coverage_instance WHERE insurer_id = ?)
            WHERE insurer_id = ? AND step_number = '9.4' AND status = 'STARTED'
        """, insurer, insurer)

    except Exception as e:
        # Record failure
        db.execute("""
            UPDATE load_checkpoints
            SET status = 'FAILED',
                completed_at = NOW(),
                error_message = ?
            WHERE insurer_id = ? AND step_number = '9.4' AND status = 'STARTED'
        """, str(e), insurer)
        raise
```

### 12.3 Checkpoint Queries

```sql
-- Check latest status for all insurers
SELECT
  insurer_id,
  step_number,
  status,
  row_count,
  completed_at
FROM load_checkpoints
WHERE (insurer_id, step_number, started_at) IN (
  SELECT insurer_id, step_number, MAX(started_at)
  FROM load_checkpoints
  GROUP BY insurer_id, step_number
)
ORDER BY insurer_id, step_number;
```

---

## 13. EXECUTION PLAN (PRODUCTION)

### 13.1 Pre-Execution Checklist

- [ ] Metadata.json prepared (all insurers, products, variants, profiles)
- [ ] Mapping Excel up-to-date (coverage_canonical rows)
- [ ] All STEP 1-7 outputs present (scope CSV, evidence_pack JSONL, coverage_cards JSONL)
- [ ] DB schema created (DDL scripts executed)
- [ ] Validation queries prepared

### 13.2 Execution Sequence

```bash
# STEP 9.1: Load Metadata
python -m pipeline.step9_load_metadata.load_all --metadata data/metadata/metadata.json

# STEP 9.2: Load Documents
python -m pipeline.step9_load_documents.load_all

# STEP 9.3: Load Coverage Canonical
python -m pipeline.step9_load_coverage_canonical.load_from_excel --excel data/sources/mapping/담보명mapping자료.xlsx

# STEP 9.4: Load Coverage Instances
for insurer in samsung meritz db kb lotte hanwha hyundai; do
  python -m pipeline.step9_load_coverage_instance.load --insurer $insurer
done

# STEP 9.5: Load Evidence
for insurer in samsung meritz db kb lotte hanwha hyundai; do
  python -m pipeline.step9_load_evidence.load --insurer $insurer
done

# STEP 9.6: Load Amounts
for insurer in samsung meritz db kb lotte hanwha hyundai; do
  python -m pipeline.step9_load_amounts.load --insurer $insurer
done

# STEP 9.7: Validation
python -m pipeline.step9_validate.validate_all
```

### 13.3 Post-Execution Validation

```sql
-- Run all validation queries (Section 9)
\i tests/validate_step9_row_counts.sql
\i tests/validate_step9_fk_integrity.sql
\i tests/validate_step9_business_logic.sql

-- Expected: All violation_count = 0
```

---

## 14. DB IS NOT GENERATOR (REITERATION)

### 14.1 Prohibited Operations

```sql
-- ❌ WRONG: Generate coverage_code in DB
INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical)
SELECT
  'A' || LPAD(ROW_NUMBER() OVER ()::TEXT, 4, '0'),
  coverage_name
FROM temp_coverage_list;

-- ✅ RIGHT: Load from Excel ONLY
INSERT INTO coverage_canonical (coverage_code, coverage_name_canonical)
SELECT coverage_code, coverage_name_canonical
FROM excel_import;
```

### 14.2 DB Role

**DB = Storage Layer**:
- ✅ Store facts from files
- ✅ Enforce FK constraints
- ✅ Enforce CHECK constraints
- ✅ Enable fast queries

**DB ≠ Generator**:
- ❌ Generate canonical codes
- ❌ Infer missing amounts
- ❌ Calculate amounts from rates
- ❌ Summarize evidence snippets

---

## CONCLUSION

This STEP 9 specification defines:

1. **Load Sequence**: 9.1 → 9.7 (dependency-ordered)
2. **Idempotency**: UPSERT on all tables (re-runnable)
3. **Variant Handling**: Data-driven (metadata.json)
4. **Validation**: Row counts, FK integrity, business logic
5. **Failure Recovery**: Checkpoints, partial re-run, full re-run
6. **DB Role**: Storage ONLY (no generation)

**Status**: DESIGN LOCKED. No code implementation in this document.

**Next**: Code implementation (STEP 9 loader scripts)
