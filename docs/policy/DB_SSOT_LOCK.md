# DB SSOT LOCK — Global Database Configuration Policy

**Status**: ✅ ACTIVE (MANDATORY)
**Enforcement**: ALL work (ingest / compare / premium / ui / tools / audit)
**Last Updated**: 2026-01-17

---

## 1. Purpose

This policy enforces a **single source of truth (SSOT)** for database connections across the entire project to prevent:
- Accidental connections to legacy/wrong databases
- Port confusion (5432 vs 5433)
- Database name confusion (inca_rag_scope vs inca_ssot)
- Regression to deprecated infrastructure

---

## 2. GLOBAL HARD RULES

### ✅ ALLOWED (ONLY)

**Database**: `inca_ssot`
**Port**: `5433`
**Connection String**:
```
postgresql://postgres:postgres@localhost:5433/inca_ssot
```

**Environment Variables** (see `.env.ssot`):
```bash
SSOT_DB_URL=postgresql://postgres:postgres@localhost:5433/inca_ssot
SSOT_DB_HOST=localhost
SSOT_DB_PORT=5433
SSOT_DB_NAME=inca_ssot
SSOT_DB_USER=postgres
SSOT_DB_PASSWORD=postgres
```

### ❌ FORBIDDEN

- ❌ `postgresql://*:*@localhost:5432/inca_rag_scope` (legacy DB)
- ❌ Any connection to port `5432`
- ❌ Any connection to database `inca_rag_scope`
- ❌ Hardcoded DB URLs in code/scripts
- ❌ "Temporary" connections to other databases for "quick checks"
- ❌ Environment variables other than `SSOT_DB_*` for primary connections

---

## 3. DB ID CHECK — Preflight Validation (MANDATORY)

**All database entry points MUST perform DB ID CHECK before proceeding.**

### Validation Rules

**Two-stage validation**:

1. **Database Name Check** (SQL):
   ```sql
   SELECT current_database() AS db;
   ```
   - **Expected**: `inca_ssot`
   - **Mandatory**: MUST match exactly

2. **Port Check** (Client-side):
   - Parse `SSOT_DB_URL` environment variable
   - Extract port from connection string
   - **Expected**: `5433` (host port)
   - **Mandatory**: MUST match exactly

### Important: NAT Port Mapping

⚠️ **DO NOT validate port using `inet_server_port()`**

`inet_server_port()` returns the container's **internal listening port** (typically 5432), which may differ from the **host port** (5433) due to Docker port mapping (NAT).

Example:
```sql
SELECT current_database(), inet_server_port();
-- Result: inca_ssot | 5432  ← Container internal port
```

This is **correct behavior** for Docker containers. The SSOT validation must check:
- Database name = `inca_ssot` (from SQL)
- Host port = `5433` (from SSOT_DB_URL)

### Failure Behavior:
- **Immediate exit** with `exit 1`
- **Error message**: `SSOT_DB_MISMATCH: expected inca_ssot@5433 (host port), got {actual_db}@{actual_port}`

### Entry Points Requiring DB ID CHECK:
1. `apps/api/server.py` — FastAPI startup (1 check at boot)
2. `pipeline/**/*` — All pipeline entry scripts
3. `tools/**/*` — All tool/audit scripts
4. Any script that connects to database

---

## 4. Grep Gate — Regression Detection (MANDATORY)

### Script: `tools/gate/check_db_ssot_lock.sh`

**Purpose**: Detect forbidden patterns in codebase to prevent regression.

### Forbidden Patterns:
- `inca_rag_scope`
- `:5432/`
- `localhost:5432`
- `inca_admin:inca_secure_prod_2025_db_key`

### Whitelist Exceptions:
- `docs/policy/PREMIUM_LEGACY_DO_NOT_USE.md` (documentation of forbidden patterns)
- `docs/policy/DB_SSOT_LOCK.md` (this file)
- `.env.ssot` (contains forbidden patterns in comments for documentation)

### Execution:
```bash
bash tools/gate/check_db_ssot_lock.sh
```

**Exit Codes**:
- `0` — PASS (no forbidden patterns found)
- `1` — FAIL (forbidden patterns detected, must be fixed)

---

## 5. Code Implementation Requirements

### 5.1 Load SSOT Configuration

**Python** (apps/api, pipeline, tools):
```python
import os
from dotenv import load_dotenv

# Load .env.ssot
load_dotenv('.env.ssot')

SSOT_DB_URL = os.getenv('SSOT_DB_URL')
if not SSOT_DB_URL:
    raise RuntimeError("SSOT_DB_URL not set. Load .env.ssot first.")
```

**Node.js** (apps/web/app/api):
```typescript
// Load .env.ssot
const SSOT_DB_URL = process.env.SSOT_DB_URL ||
  'postgresql://postgres:postgres@localhost:5433/inca_ssot';
```

### 5.2 DB ID CHECK Implementation

**Python**:
```python
import psycopg2
from urllib.parse import urlparse

def check_db_identity(db_url: str):
    """Validate we're connected to the correct SSOT database."""
    # Parse URL to get host port (client perspective)
    parsed = urlparse(db_url)
    expected_port = parsed.port or 5432

    # Connect and check database name
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT current_database()")
    actual_db = cursor.fetchone()[0]

    # Validate database name and host port
    if actual_db != 'inca_ssot':
        raise RuntimeError(
            f"SSOT_DB_MISMATCH: expected inca_ssot@{expected_port} (host port), "
            f"got {actual_db}@{expected_port}"
        )

    if expected_port != 5433:
        raise RuntimeError(
            f"SSOT_DB_MISMATCH: expected host port 5433, got {expected_port}"
        )

    cursor.close()
    conn.close()
    print(f"✓ DB ID CHECK PASS: {actual_db}@{expected_port} (host port)")
```

**Usage**:
```python
# At entry point (before any work)
check_db_identity(SSOT_DB_URL)
```

---

## 6. Developer Convenience

### 6.1 psql Alias

Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias psql_ssot='psql "postgresql://postgres:postgres@localhost:5433/inca_ssot"'
```

### 6.2 Docker Container

**Container name**: `inca_pg_ssot`
**Start command**:
```bash
docker start inca_pg_ssot
```

**Verify**:
```bash
docker ps | grep inca_pg_ssot
lsof -i :5433
nc -zv localhost 5433
```

---

## 7. Enforcement Checklist (DoD)

- [ ] `.env.ssot` exists at repo root
- [ ] `apps/api/server.py` performs DB ID CHECK at startup
- [ ] All pipeline entry scripts perform DB ID CHECK
- [ ] All tool/audit scripts perform DB ID CHECK
- [ ] `tools/gate/check_db_ssot_lock.sh` exists and passes
- [ ] No code references `inca_rag_scope` (except whitelisted docs)
- [ ] No code references `:5432/` or `localhost:5432` (except whitelisted docs)
- [ ] All DB connections use `SSOT_DB_URL` from `.env.ssot`
- [ ] Documentation updated (README/guides point to inca_ssot only)

---

## 8. Violations and Remediation

### Violation: Code references forbidden DB
**Detection**: `bash tools/gate/check_db_ssot_lock.sh` fails
**Remediation**: Replace with `SSOT_DB_URL` or add to whitelist (if documentation)

### Violation: DB ID CHECK fails
**Detection**: Script exits with `SSOT_DB_MISMATCH` error
**Remediation**:
1. Check `inca_pg_ssot` container is running
2. Verify `.env.ssot` is loaded correctly
3. Confirm connection string points to port 5433

### Violation: Hardcoded DB URL
**Detection**: Code review / grep gate
**Remediation**: Replace with environment variable from `.env.ssot`

---

## 9. Related Policies

- `docs/policy/PREMIUM_LEGACY_DO_NOT_USE.md` — Premium table deprecation
- `docs/active_constitution.md` — Pipeline rules and gates
- `docs/ui/STEP_NEXT_CHAT_UI_V2_SPEC.md` — UI Evidence requirements

---

## 10. Rationale

**Problem**: Multiple database instances (inca_rag_scope on 5432, inca_ssot on 5433) caused:
- Confusion about which DB contains canonical data
- Accidental queries to wrong DB
- Data inconsistency and debugging overhead

**Solution**: Lock entire project to single SSOT with:
1. Declarative config (`.env.ssot`)
2. Runtime validation (DB ID CHECK)
3. Static validation (grep gate)

**Result**:
- Zero ambiguity about data source
- No regression to legacy infrastructure
- Clear error messages when misconfigured
