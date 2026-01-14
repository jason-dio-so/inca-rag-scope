# METADATA GOVERNANCE – inca-rag-scope

**Version**: 1.0
**Date**: 2025-12-28
**Status**: GOVERNANCE POLICY (Enforcement Rules)

---

## 0. PURPOSE

Define operational rules for maintaining `data/metadata/products.yaml` as the **Single Source of Truth (SSOT)** for product/variant/document metadata.

**Scope**: Change control, validation, rollback, access control.
**Out of Scope**: Metadata schema (see `PRODUCT_VARIANT_METADATA_SPEC.md`).

---

## 1. SSOT DECLARATION

### 1.1 Canonical Source

**Location**: `data/metadata/products.yaml` (in `main`/`master` branch)

**Status**: SSOT for all product/variant/document relationships

**Forbidden Alternatives**:
- ❌ Hardcoded logic in Python/SQL
- ❌ Filename-based inference
- ❌ Environment variables
- ❌ Configuration files outside Git
- ❌ Database-generated metadata

### 1.2 SSOT Hierarchy

```
products.yaml (Git main branch)
    ↓ (highest authority)
Pipeline code (MUST read from products.yaml)
    ↓
Scope CSV (tagged with variant_key from products.yaml)
    ↓
DB tables (populated from scope CSV)
    ↓
Reports (query DB)
```

**Conflict Resolution**: If discrepancy exists, `products.yaml` in `main` branch is authoritative.

---

## 2. CHANGE CONTROL PROCESS

### 2.1 Pull Request (PR) Workflow

**All changes** to `products.yaml` MUST follow this process:

```
1. Create feature branch from main
   git checkout main
   git pull --rebase origin main
   git checkout -b metadata/add-{insurer}-{product}

2. Edit products.yaml
   - Add/modify insurer/product/variant/document entries
   - Follow schema in PRODUCT_VARIANT_METADATA_SPEC.md

3. Validate changes locally
   python -m tools.validate_metadata data/metadata/products.yaml

4. Commit changes
   git add data/metadata/products.yaml
   git commit -m "metadata: add {insurer} {product} with {variant_count} variants"

5. Push and create PR
   git push origin metadata/add-{insurer}-{product}
   gh pr create --title "Add {insurer} product metadata" --body "..."

6. Review and merge
   - Reviewer validates schema compliance
   - Automated CI runs validation
   - Merge to main after approval
```

### 2.2 Commit Message Convention

**Format**: `metadata: <action> <entity> <details>`

**Examples**:
- `metadata: add lotte product with male/female variants`
- `metadata: update db proposal file paths for u40/o40`
- `metadata: fix kb structure_type to kb_profile`
- `metadata: remove deprecated samsung_old product`

### 2.3 Prohibited Direct Changes

**❌ FORBIDDEN**:
- Direct commits to `main` branch
- Editing `products.yaml` without PR
- Bypassing validation checks
- Merging without review

**✅ REQUIRED**:
- All changes via PR
- At least 1 reviewer approval
- Passing CI validation
- Clear commit messages

---

## 3. VALIDATION REQUIREMENTS

### 3.1 Pre-Commit Validation

**Before committing**, run local validation:

```bash
python -m tools.validate_metadata data/metadata/products.yaml
```

**Checks**:
1. YAML syntax valid
2. All required fields present
3. Uniqueness constraints satisfied (insurer_key, product_key, file_path)
4. Referential integrity (variant_key references exist)
5. Completeness (every product has 가입설계서)
6. No prohibited patterns (filename inference, null variant for multi-variant products)

**Exit codes**:
- `0`: Validation passed
- `1`: Validation failed (must fix before committing)

### 3.2 CI/CD Validation

**GitHub Actions** (or equivalent) MUST run on every PR:

```yaml
# .github/workflows/validate-metadata.yml
name: Validate Metadata
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate products.yaml
        run: python -m tools.validate_metadata data/metadata/products.yaml
```

**PR merge blocked** if validation fails.

### 3.3 Validation Rules (Summary)

See `PRODUCT_VARIANT_METADATA_SPEC.md` Section 4 for full list.

**Critical Rules**:
- ✅ `(insurer_key, product_key)` unique
- ✅ `(insurer_key, product_key, doc_type, variant_key)` unique
- ✅ `file_path` unique across all documents
- ✅ `has_variants=true` → `variants` list not empty
- ✅ `has_variants=false` → all documents have `variant_key: null`
- ✅ Every `document.variant_key` (if not null) exists in `variants` list
- ✅ Every product has at least 1 `가입설계서` document

---

## 4. ROLLBACK PROCEDURES

### 4.1 Rollback via Git Revert

**Scenario**: Merged PR introduces error (e.g., breaks pipeline)

**Steps**:
```bash
# 1. Identify problematic commit
git log --oneline data/metadata/products.yaml

# 2. Revert commit
git revert <commit_hash>

# 3. Push to main
git push origin main
```

**Result**: `products.yaml` restored to pre-change state, pipeline continues working.

### 4.2 Rollback via New PR

**Scenario**: Complex change requires manual fix

**Steps**:
```bash
# 1. Create fix branch
git checkout -b metadata/fix-{issue}

# 2. Edit products.yaml to correct state
# (e.g., remove broken entry, restore old values)

# 3. Validate
python -m tools.validate_metadata data/metadata/products.yaml

# 4. Commit and PR
git add data/metadata/products.yaml
git commit -m "metadata: fix {issue} in {insurer} product"
git push origin metadata/fix-{issue}
gh pr create --title "Fix metadata: {issue}"
```

### 4.3 Emergency Rollback

**Scenario**: Production pipeline broken, immediate fix needed

**Authorization**: Repository maintainer only

**Steps**:
```bash
# 1. Create emergency branch from last known good commit
git checkout <last_good_commit>
git checkout -b metadata/emergency-rollback

# 2. Force push to main (ONLY in emergency)
git push origin metadata/emergency-rollback:main --force

# 3. Create post-mortem PR with proper fix
# (Follow standard PR workflow)
```

**Usage**: Extremely rare, requires incident report.

---

## 5. ACCESS CONTROL

### 5.1 Repository Permissions

**Write Access** (can create PRs):
- All team members

**Merge Access** (can approve/merge PRs):
- Repository maintainers
- Designated reviewers

**Force Push** (emergency only):
- Repository owner only

### 5.2 Branch Protection Rules

**main branch** MUST have:
- ✅ Require PR before merging
- ✅ Require at least 1 approval
- ✅ Require status checks (CI validation)
- ✅ No force push (except emergency)
- ✅ No direct commits

---

## 6. REVIEW CHECKLIST

### 6.1 Reviewer Responsibilities

Before approving PR, reviewer MUST verify:

- [ ] PR changes only `data/metadata/products.yaml` (no code changes)
- [ ] All required fields present (insurer_key, product_key, documents, etc.)
- [ ] Uniqueness constraints satisfied (no duplicate keys, file_paths)
- [ ] LOTTE/DB variants follow canonical examples in spec
- [ ] No filename-based inference logic introduced
- [ ] No insurer-specific if-else patterns suggested
- [ ] Commit message follows convention
- [ ] CI validation passed
- [ ] LOTTE example (if changed) includes all 4 doc types for MALE/FEMALE
- [ ] DB example (if changed) shows shared docs with `variant_key: null`

### 6.2 Automated Checks (CI)

CI MUST verify:

- [ ] YAML syntax valid
- [ ] Schema validation passed
- [ ] Uniqueness constraints passed
- [ ] Referential integrity passed
- [ ] Completeness checks passed
- [ ] No prohibited patterns detected

---

## 7. ADDING NEW INSURERS

### 7.1 Checklist for New Insurer

When adding a new insurer to `products.yaml`:

1. **Determine variant strategy**:
   - Does insurer have variants? (gender, age, etc.)
   - Which doc types are separated? (all or subset)

2. **Create metadata entry**:
   ```yaml
   - insurer_key: {new_insurer}
     insurer_name_kr: {name}
     insurer_type: {type}
     products:
       - product_key: {product_id}
         has_variants: {true|false}
         variants: [...]
         documents: [...]
   ```

3. **Validate file paths**:
   - All `file_path` values must exist or be planned
   - No duplicate `file_path` across all insurers

4. **Add structure_type** (if custom):
   - If document structure differs from standard, define custom profile
   - Example: `kb_profile`, `meritz_profile`

5. **Test with validation script**:
   ```bash
   python -m tools.validate_metadata data/metadata/products.yaml
   ```

6. **Create PR** following Section 2.1

### 7.2 Variant Decision Matrix

| Insurer | Variant Strategy | Doc Types Separated | Example variant_key |
|---------|-----------------|---------------------|---------------------|
| LOTTE | Gender (M/F) | All (약관/사업방법서/상품요약서/가입설계서) | MALE, FEMALE |
| DB | Age (U40/O40) | Only 가입설계서 | U40, O40 |
| KB/Meritz/Samsung | None | None | null |

**New insurer**: Choose closest matching strategy, or define new variant_key pattern.

---

## 8. UPDATING EXISTING PRODUCTS

### 8.1 File Path Changes

**Scenario**: Document file moved or renamed

**Steps**:
1. Update `file_path` in `products.yaml`
2. Ensure new path is unique
3. Validate with `validate_metadata`
4. Create PR with clear description

**Example**:
```yaml
# Before
file_path: data/sources/insurers/lotte/proposal/old_path.pdf

# After
file_path: data/sources/insurers/lotte/proposal/lotte_proposal_male.pdf
```

### 8.2 Adding New Variants

**Scenario**: Insurer introduces new variant (e.g., age group 60+)

**Steps**:
1. Add variant to `variants` list:
   ```yaml
   variants:
     - variant_key: U40
     - variant_key: O40
     - variant_key: O60  # NEW
       variant_display_name: 60세이상
       variant_attrs:
         age_range: "60-79"
   ```

2. Add documents for new variant:
   ```yaml
   documents:
     - doc_type: 가입설계서
       file_path: data/sources/insurers/db/proposal/db_proposal_o60.pdf
       variant_key: O60
   ```

3. Validate and PR

### 8.3 Removing Deprecated Products

**Scenario**: Product discontinued, no longer in scope

**Steps**:
1. Remove product entry from `products.yaml`
2. Archive documents (move to `data/archive/`)
3. Update pipeline to skip archived products
4. Create PR with deprecation note

**Example commit**:
```
metadata: remove deprecated samsung_old product

Product discontinued as of 2024-12. Documents archived to data/archive/.
```

---

## 9. CONFLICT RESOLUTION

### 9.1 Merge Conflicts in products.yaml

**Scenario**: Two PRs modify same insurer/product

**Resolution**:
1. Rebase feature branch on latest main
2. Manually resolve conflicts in `products.yaml`
3. Re-run validation
4. Force push to feature branch
5. Re-request review

**Example**:
```bash
git checkout metadata/add-lotte-variant
git fetch origin
git rebase origin/main
# Resolve conflicts in products.yaml
python -m tools.validate_metadata data/metadata/products.yaml
git add data/metadata/products.yaml
git rebase --continue
git push origin metadata/add-lotte-variant --force
```

### 9.2 Validation Failures After Merge

**Scenario**: PR merged despite validation failure (CI bypass)

**Immediate Actions**:
1. Revert merge commit (Section 4.1)
2. Create incident report
3. Re-submit corrected PR
4. Review CI configuration to prevent bypass

---

## 10. DOCUMENTATION UPDATES

### 10.1 When to Update Spec

Update `PRODUCT_VARIANT_METADATA_SPEC.md` when:
- New schema fields introduced
- New validation rules added
- New variant patterns emerge (beyond LOTTE/DB examples)

**Process**: Separate PR for spec changes, merge before metadata changes.

### 10.2 Changelog

Maintain `CHANGELOG.md` in `data/metadata/`:

```markdown
# Metadata Changelog

## 2025-12-28
- Added LOTTE product with MALE/FEMALE variants (all doc types separated)
- Added DB product with U40/O40 variants (only 가입설계서 separated)
- Added KB/Meritz/Samsung with no variants

## 2025-12-15
- Initial metadata schema defined
```

---

## 11. PROHIBITED PATTERNS (ENFORCEMENT)

### 11.1 Code Review Red Flags

**Reject PR** if any of these patterns appear in pipeline/loader code:

❌ **Filename-based variant inference**:
```python
if "(남)" in filename:
    variant_key = 'MALE'
```

❌ **Page-range-based variant inference**:
```python
if 3 <= page <= 5:
    variant_key = 'U40'
```

❌ **Insurer-specific if-else branching**:
```python
if insurer == 'lotte':
    variant_logic()
elif insurer == 'db':
    different_variant_logic()
```

❌ **Hardcoded file paths**:
```python
file_path = f"data/sources/insurers/{insurer}/proposal.pdf"
```

✅ **Correct pattern**:
```python
metadata = load_yaml('data/metadata/products.yaml')
for doc in metadata.get_documents(insurer, product):
    variant_key = doc.variant_key  # Direct read from metadata
    file_path = doc.file_path       # Direct read from metadata
```

### 11.2 Metadata Review Red Flags

**Reject metadata PR** if:

❌ Variant key missing for multi-variant product:
```yaml
has_variants: true
documents:
  - doc_type: 가입설계서
    variant_key: null  # WRONG! Must be MALE or FEMALE for LOTTE
```

❌ Duplicate file paths:
```yaml
# Product A
documents:
  - file_path: data/sources/insurers/lotte/proposal.pdf

# Product B (DUPLICATE!)
documents:
  - file_path: data/sources/insurers/lotte/proposal.pdf
```

❌ Non-existent variant reference:
```yaml
variants:
  - variant_key: MALE
documents:
  - variant_key: FEMALE  # WRONG! FEMALE not in variants list
```

---

## 12. TRAINING AND ONBOARDING

### 12.1 New Team Member Checklist

- [ ] Read `PRODUCT_VARIANT_METADATA_SPEC.md`
- [ ] Read `METADATA_GOVERNANCE.md` (this document)
- [ ] Review example PRs (LOTTE/DB additions)
- [ ] Run validation script locally
- [ ] Create test PR (add dummy insurer, then close PR)
- [ ] Shadow a metadata review session

### 12.2 Reference PRs

**Example PRs** to review:
- PR#X: "Add LOTTE product with gender variants"
- PR#Y: "Add DB product with age variants"
- PR#Z: "Update KB file paths after document reorganization"

---

## 13. MONITORING AND AUDITING

### 13.1 Metadata Health Metrics

**Monthly Report** (automated):
- Total insurers: {count}
- Total products: {count}
- Products with variants: {count}
- Products without variants: {count}
- Total documents: {count}
- Unique file paths: {count}
- Validation pass rate: {percentage}

### 13.2 Audit Log

**Git log** serves as audit trail:
```bash
# View all metadata changes
git log --oneline -- data/metadata/products.yaml

# View changes by author
git log --author="user@example.com" -- data/metadata/products.yaml

# View changes in date range
git log --since="2025-01-01" --until="2025-12-31" -- data/metadata/products.yaml
```

---

## 14. INCIDENT RESPONSE

### 14.1 Incident Classification

**Severity 1** (Production broken):
- Pipeline cannot run due to metadata error
- Response: Emergency rollback (Section 4.3)

**Severity 2** (Incorrect results):
- Pipeline runs but produces wrong variant assignments
- Response: Rollback via PR (Section 4.2)

**Severity 3** (Validation failure):
- PR blocked by CI, no production impact
- Response: Fix and re-submit PR

### 14.2 Post-Incident Review

After Severity 1/2 incidents:
1. Create incident report in `docs/incidents/`
2. Root cause analysis (why validation missed error)
3. Update validation rules to catch similar errors
4. Update governance policy if needed
5. Share learnings with team

---

## 15. FUTURE ENHANCEMENTS

### 15.1 Planned Improvements

- **Automated file path validation**: Check if `file_path` exists in repo
- **Diff visualization**: Show metadata changes in PR as table
- **Variant coverage report**: Ensure all variants have required doc types
- **Schema versioning**: Support backward-compatible schema evolution

### 15.2 Feedback Loop

Submit governance improvement suggestions via:
- GitHub Issues (label: `metadata-governance`)
- Team meetings
- Post-incident reviews

---

## CONCLUSION

This governance policy ensures `products.yaml` remains the **Single Source of Truth** with:

1. **Change Control**: All changes via PR with validation
2. **Rollback**: Clear procedures for reverting bad changes
3. **Validation**: Automated checks enforce schema compliance
4. **Access Control**: Branch protection prevents unauthorized changes
5. **Enforcement**: Code/metadata reviews catch prohibited patterns

**Compliance**: Mandatory for all team members.

**Status**: ACTIVE. Violations subject to PR rejection.

**Next Steps**:
1. Set up CI validation pipeline
2. Enable branch protection on main
3. Train team on PR workflow
4. Monitor first 10 PRs for compliance
