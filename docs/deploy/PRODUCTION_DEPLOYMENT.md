# Production Deployment Guide

**Version**: 1.0.0
**Status**: 🔒 **LOCKED**
**Lock Date**: 2025-12-29
**STEP**: NEXT-13

---

## 🎯 Purpose

This document defines the **production deployment procedure** for inca-rag-scope system.

**CRITICAL**: This is a **deployment guide**, NOT a development guide.
- NO new feature development
- NO pipeline modifications
- NO schema changes
- NO amount/explanation logic changes

---

## 📋 System Architecture (LOCKED)

### Component Stack

```
┌─────────────────────────────────────────────────┐
│               Frontend (UI)                      │
│  - React/Vue/HTML (user choice)                 │
│  - Follows COMPARISON_EXPLANATION_RULES.md      │
└─────────────────────────────────────────────────┘
                      ▼ HTTP
┌─────────────────────────────────────────────────┐
│          API Server (FastAPI)                    │
│  - apps/api/server.py                           │
│  - Read-only amount_fact access                 │
│  - Explanation layer integration                │
└─────────────────────────────────────────────────┘
                      ▼ SQL
┌─────────────────────────────────────────────────┐
│       PostgreSQL Database (pgvector)             │
│  - amount_fact (LOCKED, read-only)              │
│  - audit_runs (LOCKED, read-only)               │
│  - coverage_canonical, evidence_ref             │
└─────────────────────────────────────────────────┘
```

**CRITICAL**: All components are READ-ONLY in production (NO writes to amount_fact).

---

## 🐳 Docker Deployment

### Deployment Modes

| Mode | Compose File | Purpose | Database |
|------|-------------|---------|----------|
| **Development** | `docker/compose.yml` | Local testing, API dev | Local DB (volume) |
| **Production** | `docker/docker-compose.production.yml` | Live service | Production DB |

**CRITICAL**: `docker-compose.demo.yml` is DEPRECATED (from old project, DO NOT USE)

---

## 🚀 Development Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB+ available RAM
- 5GB+ available disk

### Step 1: Environment Configuration

```bash
cd /Users/cheollee/inca-rag-scope/docker
cp .env .env.local  # Optional: override for local testing
```

**Default `.env`**:
```ini
POSTGRES_DB=inca_rag_scope
POSTGRES_USER=inca_admin
POSTGRES_PASSWORD=inca_secure_prod_2025_db_key
POSTGRES_PORT=5432
```

**CRITICAL**: NEVER commit `.env` with production passwords.

---

### Step 2: Start Development Environment

```bash
# From project root
docker compose -f docker/compose.yml up -d --build
```

**Services Started**:
- PostgreSQL 15 Alpine
- Port: 5432 (host) → 5432 (container)
- Volume: `postgres_data` (persistent)

**Healthcheck**:
```bash
docker compose -f docker/compose.yml ps
# Expected: postgres service "healthy"
```

---

### Step 3: Verify Database

```bash
# Connect to DB
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope

# Check amount_fact table
SELECT COUNT(*) FROM amount_fact;
-- Expected: 297 rows (from STEP NEXT-10B-FINAL)

# Check audit_runs
SELECT audit_name, audit_status, freeze_tag FROM audit_runs;
-- Expected: step7_amount_gt_audit, PASS, freeze/pre-10b2g2-*
```

**CRITICAL**: If counts differ, DB may not be loaded. See `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md`.

---

### Step 4: Stop Development Environment

```bash
docker compose -f docker/compose.yml down
# Use `down -v` to remove volumes (DESTRUCTIVE)
```

---

## 🏭 Production Deployment

### Prerequisites

- Production server (Linux recommended)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk (for DB growth)
- SSL certificate (for HTTPS)

---

### Step 1: Production Environment Setup

```bash
cd /Users/cheollee/inca-rag-scope/docker

# Create production .env (CRITICAL: secure credentials)
vim .env
```

**Production `.env` Template**:
```ini
# Database credentials (CHANGE THESE!)
POSTGRES_DB=inca_rag_scope
POSTGRES_USER=inca_admin
POSTGRES_PASSWORD=<STRONG_RANDOM_PASSWORD>

# Port (default: 5432)
POSTGRES_PORT=5432

# Optional: Custom timezone
TZ=Asia/Seoul
```

**Password Requirements**:
- Minimum 20 characters
- Mix of letters, numbers, symbols
- NO dictionary words
- Use password generator

**Security Checklist**:
- ✅ `.env` in `.gitignore`
- ✅ `.env` file permissions: `chmod 600 .env`
- ✅ NO `.env` in version control
- ✅ Backup `.env` in secure vault

---

### Step 2: Start Production Database

```bash
# From project root
docker compose -f docker/docker-compose.production.yml up -d
```

**Services Started**:
- PostgreSQL 16 with pgvector extension
- Container: `inca_rag_scope_db`
- Network: `inca_rag_scope_net` (bridge)
- Volume: `inca_rag_scope_postgres_data` (persistent)

**Production Tuning** (from compose file):
```ini
max_connections=100
shared_buffers=256MB
effective_cache_size=1GB
work_mem=4MB
```

**CRITICAL**: These are baseline settings. Adjust for your server specs.

---

### Step 3: Load Production Data

**First-Time Setup Only**:

```bash
# 1. Load DB schema
docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope < pipeline/db_schema/create_tables.sql

# 2. Load amount_fact data (from STEP NEXT-10B-FINAL)
docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope < pipeline/step10_audit/load_amount_fact.sql

# 3. Load audit_runs metadata
python -m pipeline.step10_audit.preserve_audit_run

# 4. Verify
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "SELECT COUNT(*) FROM amount_fact;"
# Expected: 297
```

**CRITICAL**: This is a ONE-TIME operation. DO NOT reload in production.

---

### Step 4: Production Healthcheck

```bash
# Check container status
docker compose -f docker/docker-compose.production.yml ps

# Expected output:
# NAME                 STATUS
# inca_rag_scope_db    Up (healthy)

# Check logs
docker logs inca_rag_scope_db --tail 50

# Check database connectivity
docker exec -it inca_rag_scope_db pg_isready -U inca_admin
# Expected: accepting connections
```

---

### Step 5: API Server Deployment (Manual)

**CRITICAL**: API server is NOT included in docker-compose (by design).

**Option A: Python Virtual Environment**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://inca_admin:<PASSWORD>@localhost:5432/inca_rag_scope"

# Run API server
uvicorn apps.api.server:app --host 0.0.0.0 --port 8000
```

**Option B: Systemd Service** (Recommended for Linux)

```ini
# /etc/systemd/system/inca-api.service
[Unit]
Description=INCA RAG Scope API Server
After=network.target docker.service

[Service]
Type=simple
User=inca
WorkingDirectory=/opt/inca-rag-scope
Environment="DATABASE_URL=postgresql://inca_admin:<PASSWORD>@localhost:5432/inca_rag_scope"
ExecStart=/opt/inca-rag-scope/venv/bin/uvicorn apps.api.server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable inca-api
sudo systemctl start inca-api
sudo systemctl status inca-api
```

**Option C: Docker Container** (Custom)

```dockerfile
# Dockerfile.api (create if needed)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/ apps/
COPY pipeline/ pipeline/
CMD ["uvicorn", "apps.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -f Dockerfile.api -t inca-api:latest .
docker run -d \
  --name inca_api \
  --network inca_rag_scope_net \
  -e DATABASE_URL="postgresql://inca_admin:<PASSWORD>@inca_rag_scope_db:5432/inca_rag_scope" \
  -p 8000:8000 \
  inca-api:latest
```

---

### Step 6: Production Verification

**Database Verification**:
```bash
# Row counts
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "
  SELECT
    (SELECT COUNT(*) FROM amount_fact) as amount_fact_count,
    (SELECT COUNT(*) FROM audit_runs) as audit_runs_count,
    (SELECT COUNT(*) FROM coverage_canonical) as coverage_count;
"
# Expected: 297, 1+, 50+
```

**API Verification**:
```bash
# Healthcheck endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Example compare request
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"insurer": "삼성화재", "product_name": "다이렉트 암보험"},
      {"insurer": "KB손해보험", "product_name": "KB 암보험"}
    ],
    "target_coverages": [
      {"coverage_code": "A4200_1"}
    ]
  }'
```

**Lock Verification**:
```bash
# Verify audit PASS status
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "
  SELECT audit_status, freeze_tag FROM audit_runs
  WHERE audit_name = 'step7_amount_gt_audit';
"
# Expected: PASS, freeze/pre-10b2g2-20251229-024400
```

---

## 🔒 Production Lock Checklist

Before declaring production ready:

- ✅ **Database**: amount_fact = 297 rows (no changes)
- ✅ **Audit**: audit_runs status = PASS
- ✅ **API**: Healthcheck returns 200 OK
- ✅ **Explanation**: Templates LOCKED (no LLM)
- ✅ **Forbidden Words**: Validation active (25+ patterns)
- ✅ **Read-Only**: NO writes to amount_fact
- ✅ **Credentials**: Production `.env` secured
- ✅ **Backups**: Database backup strategy in place

---

## 🔄 Maintenance Operations

### Backup Database

```bash
# Full database backup
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope > backup_$(date +%Y%m%d).sql

# Compressed backup
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Backup Schedule** (Recommended):
- Daily: Full DB backup
- Weekly: Archive to remote storage
- Monthly: Verification restore test

---

### Restore Database

```bash
# Stop API server first
sudo systemctl stop inca-api

# Restore from backup
docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope < backup_20251229.sql

# Restart API server
sudo systemctl start inca-api
```

---

### Monitor Logs

```bash
# Database logs
docker logs inca_rag_scope_db --follow

# API logs (if using systemd)
sudo journalctl -u inca-api -f

# API logs (if using docker)
docker logs inca_api --follow
```

---

### Update Application Code

**CRITICAL**: Only deployment/config updates allowed (NO pipeline changes).

```bash
# Pull latest code (deployment updates only)
git pull origin fix/10b2g2-amount-audit-hardening

# Restart API server
sudo systemctl restart inca-api

# Verify
curl http://localhost:8000/health
```

**Forbidden Updates**:
- ❌ amount_fact schema changes
- ❌ Step7 pipeline modifications
- ❌ Explanation templates changes
- ❌ Forbidden words removal
- ❌ Status semantics changes

---

## 🚨 Troubleshooting

### Issue: Database Container Won't Start

**Symptoms**:
```bash
docker compose ps
# inca_rag_scope_db: Restarting
```

**Solutions**:
```bash
# Check logs
docker logs inca_rag_scope_db

# Common causes:
# 1. Port 5432 already in use
sudo lsof -i :5432
# Kill conflicting process or change POSTGRES_PORT in .env

# 2. Volume permission issues
docker volume inspect inca_rag_scope_postgres_data
# Check mount point permissions

# 3. Corrupt volume (LAST RESORT)
docker compose down -v  # DESTRUCTIVE: removes data
docker compose up -d
```

---

### Issue: API Cannot Connect to Database

**Symptoms**:
```bash
curl http://localhost:8000/health
# {"status": "unhealthy", "error": "database connection failed"}
```

**Solutions**:
```bash
# 1. Check DATABASE_URL
echo $DATABASE_URL
# Should match postgres container credentials

# 2. Check network connectivity
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "SELECT 1;"

# 3. Verify API server network mode
# If API in Docker: use container name "inca_rag_scope_db"
# If API on host: use "localhost" or "127.0.0.1"
```

---

### Issue: amount_fact Row Count Mismatch

**Symptoms**:
```sql
SELECT COUNT(*) FROM amount_fact;
-- Returns != 297
```

**Solutions**:
```bash
# DO NOT reload in production without approval!
# Contact pipeline team for guidance

# Check audit status
SELECT audit_status FROM audit_runs WHERE audit_name = 'step7_amount_gt_audit';
# If not PASS, data integrity compromised
```

**Escalation Path**:
1. Document current state (row counts, audit status)
2. Create backup immediately
3. Contact pipeline team
4. DO NOT modify amount_fact manually

---

## 📞 Support

| Issue Type | Contact | Reference |
|------------|---------|-----------|
| Deployment | DevOps Team | This document |
| Database | DBA Team | `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md` |
| API | Backend Team | `docs/api/AMOUNT_READ_CONTRACT.md` |
| UI Integration | Frontend Team | `docs/ui/FRONTEND_INTEGRATION_GUIDE.md` |
| Lock Policy | Pipeline Team | `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` |

---

## 🎯 Production Readiness Checklist

- ✅ Docker compose files verified (`compose.yml`, `docker-compose.production.yml`)
- ✅ Environment variables secured (`.env` with strong password)
- ✅ Database deployed and healthy
- ✅ amount_fact = 297 rows (LOCKED)
- ✅ audit_runs status = PASS
- ✅ API server deployed and accessible
- ✅ Healthcheck endpoint returns 200 OK
- ✅ Backup strategy in place
- ✅ Monitoring configured
- ✅ Support contacts documented

---

**Lock Owner**: DevOps Team + Pipeline Team
**Last Updated**: 2025-12-29
**Status**: 🔒 **LOCKED**
