# STEP NEXT-51: Excel Patch Instructions

**Date**: 2026-01-01
**Purpose**: Manual patching guide for adding alias rows to 담보명mapping자료.xlsx

---

## 1. Overview

**What**: Add 41 new alias rows to Excel mapping table
**Why**: Resolve 60% of MERITZ unmapped and 48.8% of LOTTE unmapped entries
**How**: Manual copy-paste from generated Excel file

---

## 2. Files Required

**Source (generated)**:
- `docs/audit/STEP_NEXT_51_ALIAS_ROWS_TO_ADD.xlsx`

**Target (SSOT)**:
- `data/sources/mapping/담보명mapping자료.xlsx`

---

## 3. Pre-Flight Checks

Before starting:

1. ✅ Backup current Excel file:
   ```bash
   cp data/sources/mapping/담보명mapping자료.xlsx \
      data/sources/mapping/담보명mapping자료.xlsx.backup_$(date +%Y%m%d)
   ```

2. ✅ Verify current Excel row count:
   ```bash
   python3 -c "import pandas as pd; print(f'Current rows: {len(pd.read_excel(\"data/sources/mapping/담보명mapping자료.xlsx\"))}')"
   ```

   Expected: **287 rows**

3. ✅ Open both files in Excel/Numbers/LibreOffice

---

## 4. Patching Steps

### Step 1: Open Source File

Open `docs/audit/STEP_NEXT_51_ALIAS_ROWS_TO_ADD.xlsx`

**Expected columns**:
- `ins_cd`
- `보험사명`
- `cre_cvr_cd`
- `신정원코드명`
- `담보명(가입설계서)`
- `reason` (for reference only, DO NOT copy to target)
- `confidence` (for reference only, DO NOT copy to target)
- `source` (for reference only, DO NOT copy to target)

**Expected rows**: 41 (excluding header)

---

### Step 2: Open Target File

Open `data/sources/mapping/담보명mapping자료.xlsx`

**Current structure**:
- Row 1: Header (`ins_cd`, `보험사명`, `cre_cvr_cd`, `신정원코드명`, `담보명(가입설계서)`)
- Rows 2-288: Existing mapping data (287 rows)

**Target structure after patch**:
- Rows 2-328: Existing + new rows (287 + 41 = **328 rows**)

---

### Step 3: Copy Rows

**Important**: Only copy the first 5 columns (`ins_cd` through `담보명(가입설계서)`).

**DO NOT copy**: `reason`, `confidence`, `source` columns.

#### Method A: Select and Copy

1. In source file, select columns A-E (rows 2-42, excluding header)
2. Copy (Cmd+C / Ctrl+C)
3. In target file, go to row 289 (first empty row after existing data)
4. Paste (Cmd+V / Ctrl+V)

#### Method B: Individual Insurer Blocks

If you prefer to add by insurer:

**MERITZ (N01)**: 18 rows
- Source rows: 2-19
- Target starting row: 289

**HANWHA (N02)**: 1 row
- Source row: 20
- Target starting row: 307

**LOTTE (N03)**: 21 rows
- Source rows: 21-41
- Target starting row: 308

**HYUNDAI (N09)**: 1 row
- Source row: 42
- Target starting row: 329

---

### Step 4: Verify Patch

After pasting:

1. ✅ Check total row count: Should be **288** (header + 287 existing + 41 new)
2. ✅ Check last row content:
   - Should be a HYUNDAI (N09) entry
   - `담보명(가입설계서)` should contain "혈전용해치료비Ⅱ(최초1회한)(특정심장질환)담보"

3. ✅ Verify no formatting corruption:
   - All `ins_cd` values are valid (N01, N02, N03, N05, N08, N09, N10, N13)
   - No blank rows inserted
   - No header row duplicated

4. ✅ Spot-check sample rows:

| ins_cd | 보험사명 | cre_cvr_cd | 신정원코드명 | 담보명(가입설계서) |
|--------|----------|------------|--------------|-------------------|
| N01    | 메리츠   | A1100      | 질병사망     | 3 질병사망        |
| N01    | 메리츠   | A4103      | 뇌졸중진단비 | 155 뇌졸중진단비  |
| N03    | 롯데     | A1300      | 상해사망     | 상해사고로 사망한 경우 보험가입금액 지급 |

---

### Step 5: Save Target File

1. Save `data/sources/mapping/담보명mapping자료.xlsx`
2. Close Excel (ensure file is not locked)

---

## 5. Post-Patch Verification

Run verification script:

```bash
python3 << 'EOF'
import pandas as pd

# Load patched Excel
df = pd.read_excel('data/sources/mapping/담보명mapping자료.xlsx')

print(f'Total rows: {len(df)}')
print(f'Expected: 328')
print(f'Match: {"✅" if len(df) == 328 else "❌"}')

# Check insurer distribution
print('\nRow count by insurer:')
for ins_cd in sorted(df['ins_cd'].unique()):
    count = len(df[df['ins_cd'] == ins_cd])
    print(f'  {ins_cd}: {count} rows')

# Check for duplicates
duplicates = df[df.duplicated(subset=['ins_cd', '담보명(가입설계서)'], keep=False)]
if len(duplicates) > 0:
    print(f'\n❌ WARNING: {len(duplicates)} duplicate entries found!')
    print(duplicates[['ins_cd', '담보명(가입설계서)']])
else:
    print('\n✅ No duplicates found')

EOF
```

**Expected output**:
```
Total rows: 328
Expected: 328
Match: ✅

Row count by insurer:
  N01: 49 rows  (was 31, added 18)
  N02: 53 rows  (was 52, added 1)
  N03: 56 rows  (was 35, added 21)
  N05: 34 rows  (no change)
  N08: 40 rows  (no change)
  N09: 28 rows  (was 27, added 1)
  N10: 38 rows  (no change)
  N13: 30 rows  (no change)

✅ No duplicates found
```

---

## 6. Re-Run Step2-b Mapping

After Excel patching, re-run canonical mapping for all insurers:

```bash
# Re-run Step2-b for all insurers
for insurer in samsung hyundai kb meritz hanwha lotte heungkuk db; do
    echo "Running Step2-b for $insurer..."
    python -m pipeline.step2_canonical_mapping.run --insurer $insurer
done
```

---

## 7. Verify Improvement

Check before/after mapping rates:

```bash
python3 << 'EOF'
import json
from pathlib import Path

INSURERS = ['samsung', 'hyundai', 'kb', 'meritz', 'hanwha', 'lotte', 'heungkuk', 'db']

print('Mapping Rate Improvement:')
print('='*60)

for insurer in INSURERS:
    canonical_file = Path(f'data/scope_v3/{insurer}_step2_canonical_scope_v1.jsonl')

    if not canonical_file.exists():
        continue

    entries = []
    with open(canonical_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    total = len(entries)
    mapped = sum(1 for e in entries if e.get('mapping_method') in ['exact', 'normalized'])
    unmapped = total - mapped

    rate = (mapped / total * 100) if total > 0 else 0

    print(f'{insurer.upper():10s}: {mapped:2d}/{total:2d} mapped ({rate:5.1f}%) | unmapped: {unmapped:2d}')

EOF
```

**Expected improvement**:
- MERITZ: 16.7% → ~76.7% (60% of 30 unmapped resolved = +60%p)
- LOTTE: 32.8% → ~61.6% (48.8% of 43 unmapped resolved = +28.8%p)

---

## 8. Commit Changes

If verification passes:

```bash
git add data/sources/mapping/담보명mapping자료.xlsx
git commit -m "feat(step-next-51): add 41 alias rows to canonical mapping

- MERITZ: +18 rows (number-prefix aliases)
- LOTTE: +21 rows (benefit description aliases)
- HYUNDAI: +1 row
- HANWHA: +1 row

Expected improvement:
- MERITZ unmapped: 30 → 12 (-60%)
- LOTTE unmapped: 43 → 22 (-48.8%)

STEP NEXT-51 Excel SSOT alias expansion"
```

---

## 9. Rollback Procedure

If anything goes wrong:

```bash
# Restore from backup
cp data/sources/mapping/담보명mapping자료.xlsx.backup_YYYYMMDD \
   data/sources/mapping/담보명mapping자료.xlsx

# Re-run Step2-b
for insurer in samsung hyundai kb meritz hanwha lotte heungkuk db; do
    python -m pipeline.step2_canonical_mapping.run --insurer $insurer
done
```

---

## 10. Troubleshooting

### Issue: "Total rows is 329, not 328"

**Cause**: Header row duplicated
**Fix**: Delete duplicate header row in Excel

### Issue: "Duplicate entries found"

**Cause**: Same (ins_cd, 담보명) pair already exists in Excel
**Fix**: Remove duplicates from source file before patching

### Issue: "Mapping rate didn't improve"

**Cause**: Excel not saved, or Step2-b not re-run
**Fix**:
1. Verify Excel file was saved
2. Check file modification timestamp: `ls -l data/sources/mapping/담보명mapping자료.xlsx`
3. Re-run Step2-b for affected insurers

---

## 11. Success Criteria

✅ Excel row count: 328 (287 + 41)
✅ No duplicate entries
✅ MERITZ mapping rate: ≥70%
✅ LOTTE mapping rate: ≥60%
✅ No regression in other insurers
✅ Committed to git

---

**Next**: After successful patching, proceed to STEP 51-5 (Regression Testing)
