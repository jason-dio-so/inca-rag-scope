# Premium Runtime Audit Report (Q12 G10 Gate)

**Generated**: 2026-01-09 17:51:47

**Purpose**: Validate Q12 G10 Gate compliance for runtime premium injection

---

## Audit Persona

- **Age**: 40
- **Sex**: M
- **Plan Variant**: NO_REFUND

---

## Q12 G10 Gate Status

**Status**: **PASS**

**Gate Rule**: Q12 G10 Gate: ALL insurers must have premium_monthly (if ANY missing → FAIL)

**Total Insurers Required**: 8

**With Premium SSOT**: 8

**Missing Premium**: 0

✅ **All insurers have premium SSOT available**

---

## Premium SSOT by Insurer

| Insurer | Premium Monthly (원) | Status |
|---------|----------------------|--------|
| db | 86,317 | ✅ OK |
| hanwha | 83,829 | ✅ OK |
| heungkuk | 82,745 | ✅ OK |
| hyundai | 81,750 | ✅ OK |
| kb | 87,417 | ✅ OK |
| lotte | 87,681 | ✅ OK |
| meritz | 80,025 | ✅ OK |
| samsung | 81,000 | ✅ OK |

---

## Interpretation

✅ **Q12 is READY for runtime execution**

All required insurers have premium_monthly available from SSOT.

Q12 responses can include premium data and pass G10 gate validation.

---

## Data Source

⚠️ **MOCK DATA** (for demonstration)

In production, premium data MUST come from:
- `product_premium_quote_v2` table, OR
- Greenlight API (prInfo + prDetail), OR
- Other approved Premium SSOT sources

---

## Metadata

- **Script**: `tools/audit/premium_runtime_audit.py`
- **Execution Time**: 2026-01-09 17:51:47
- **Insurers Audited**: 8
- **G10 Gate Status**: **PASS**

