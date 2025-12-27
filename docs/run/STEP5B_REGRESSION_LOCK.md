# STEP 5-β — Regression Lock vs STEP5-α

## Overview

Comparison of coverage cards generation between STEP5-α (baseline) and STEP5-β (current).

**Note**: STEP5-α baseline data not available. This serves as the **initial lock** for future regression testing.

## Current State (STEP5-β)

| Insurer | Cards Generated | With Evidence | Empty Evidence |
|---------|-----------------|---------------|----------------|
| samsung |              41 |            40 |              1 |
| meritz  |              34 |            27 |              7 |
| db      |              30 |            30 |              0 |
| hanwha  |              37 |            20 |             17 |
| lotte   |              37 |            35 |              2 |
| kb      |              45 |            37 |              8 |
| hyundai |              37 |            33 |              4 |
| heungkuk |              36 |            32 |              4 |

## Known Changes Since Previous Steps

### Hanwha Evidence Improvement (STEP4-λ)

- **Before STEP4-λ**: 13 nonempty (from evidence_pack)
- **After STEP4-λ**: 20 nonempty (from evidence_pack)
- **Current cards**: 20 with evidence (matches evidence_pack)
- **Delta**: +7 evidences

### Cards Regeneration

- **Hanwha cards**: Regenerated in STEP5-β to sync with STEP4-λ evidence_pack
- **Other insurers**: No changes detected

## Regression Analysis

Since STEP5-α baseline is not available, regression cannot be computed.

**This report serves as the baseline for future STEP5 iterations.**

## Verification

### Check Evidence Pack vs Cards Consistency

```bash
# For each insurer, verify evidence_pack nonempty count matches cards with_evidence count
python3 << 'PYSCRIPT'
import json
for insurer in ['samsung', 'meritz', 'db', 'hanwha', 'lotte', 'kb', 'hyundai', 'heungkuk']:
    # Evidence pack
    with open(f'data/evidence_pack/{insurer}_evidence_pack.jsonl') as f:
        pack = [json.loads(line) for line in f if line.strip()]
    pack_nonempty = sum(1 for r in pack if len(r['evidences']) > 0)
    
    # Cards
    with open(f'data/compare/{insurer}_coverage_cards.jsonl') as f:
        cards = [json.loads(line) for line in f if line.strip()]
    cards_found = sum(1 for c in cards if c.get('evidence_status') == 'found')
    
    match = '✅' if pack_nonempty == cards_found else '❌'
    print(f"{match} {insurer}: pack={pack_nonempty}, cards={cards_found}")
PYSCRIPT
```

---

**Date**: 2025-12-27
**Status**: ✅ Initial lock established
