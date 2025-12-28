# inca-rag-scope Production Database

**Version**: 1.0
**Purpose**: Single operational PostgreSQL database for inca-rag-scope project

---

## Overview

This Docker Compose configuration provides a **production-grade PostgreSQL database** with pgvector extension for the inca-rag-scope project.

**IMPORTANT NOTES**:
- ✅ **Database ONLY**: This compose file manages the database container exclusively
- ❌ **No application logic**: No API, worker, loader, or ETL containers included
- ❌ **No schema scripts**: Schema creation/migration handled separately (see STEP 9)
- ❌ **No business logic**: Database is a storage layer ONLY (no calculations, inferences, or decisions)

---

## Purpose

This database stores results from **STEP 1-9** of the inca-rag-scope pipeline:

1. Coverage metadata (insurers, products, variants)
2. Document metadata (약관, 사업방법서, 상품요약서, 가입설계서)
3. Coverage canonical definitions (from 담보명mapping자료.xlsx)
4. Coverage instances (from scope CSV)
5. Evidence references (from evidence_pack JSONL)
6. Amount facts (from coverage_cards JSONL)

**Database Role**: Storage and retrieval ONLY. All business logic resides in pipeline/loader code.

---

## Architecture

### Components

- **Image**: `pgvector/pgvector:pg16` (PostgreSQL 16 + pgvector extension)
- **Container**: `inca_rag_scope_db`
- **Volume**: `inca_rag_scope_postgres_data` (single volume for all data)
- **Network**: `inca_rag_scope_net` (isolated bridge network)
- **Port**: 5432 (configurable via POSTGRES_PORT)

### Database Configuration

- **DB Name**: `inca_rag_scope`
- **User**: `inca_admin` (configurable)
- **Locale**: ko_KR.UTF-8
- **Timezone**: Asia/Seoul
- **Max Connections**: 100
- **Shared Buffers**: 256MB

---

## Getting Started

### 1. Initial Setup

```bash
# Navigate to docker directory
cd docker

# Copy environment template
cp .env.example .env

# Edit .env and set secure password
nano .env  # or vim/code/etc.
```

**IMPORTANT**: Change `POSTGRES_PASSWORD` in `.env` before first run!

### 2. Start Database

```bash
# Start database in detached mode
docker compose -f docker-compose.production.yml up -d

# Check status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f postgres
```

### 3. Verify Health

```bash
# Check healthcheck status
docker inspect inca_rag_scope_db --format='{{.State.Health.Status}}'
# Expected: healthy

# Test connection
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c '\l'
```

---

## Database Access

### From Host Machine

```bash
# Using psql (if installed locally)
psql -h localhost -p 5432 -U inca_admin -d inca_rag_scope

# Using Docker exec
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope
```

### From Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="inca_rag_scope",
    user="inca_admin",
    password="YOUR_PASSWORD"
)
```

### From Application Container

If running application containers in the same Docker network:

```python
# Use container name as hostname
conn = psycopg2.connect(
    host="inca_rag_scope_db",  # Container name
    port=5432,
    database="inca_rag_scope",
    user="inca_admin",
    password="YOUR_PASSWORD"
)
```

---

## Common Operations

### Stop Database

```bash
docker compose -f docker-compose.production.yml down
```

**NOTE**: Volume persists after `down`. Data is NOT deleted.

### Restart Database

```bash
docker compose -f docker-compose.production.yml restart
```

### View Logs

```bash
# All logs
docker compose -f docker-compose.production.yml logs

# Follow logs
docker compose -f docker-compose.production.yml logs -f

# Last 100 lines
docker compose -f docker-compose.production.yml logs --tail=100
```

---

## Backup and Restore

### Backup (pg_dump)

```bash
# Full database backup
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Custom format (recommended for large databases)
docker exec inca_rag_scope_db pg_dump -U inca_admin -d inca_rag_scope -F c > backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restore (pg_restore)

```bash
# From SQL backup
docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope < backup_20251228.sql

# From compressed SQL backup
gunzip -c backup_20251228.sql.gz | docker exec -i inca_rag_scope_db psql -U inca_admin -d inca_rag_scope

# From custom format
docker exec -i inca_rag_scope_db pg_restore -U inca_admin -d inca_rag_scope -F c < backup_20251228.dump
```

### Volume Backup (Docker volume)

```bash
# Stop database first
docker compose -f docker-compose.production.yml down

# Backup volume to tar
docker run --rm \
  -v inca_rag_scope_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/volume_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restart database
docker compose -f docker-compose.production.yml up -d
```

### Volume Restore (Docker volume)

```bash
# CAUTION: This will OVERWRITE all data in the volume

# Stop database
docker compose -f docker-compose.production.yml down

# Remove old volume
docker volume rm inca_rag_scope_postgres_data

# Recreate volume
docker volume create inca_rag_scope_postgres_data

# Restore from tar
docker run --rm \
  -v inca_rag_scope_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/volume_backup_20251228.tar.gz -C /data

# Restart database
docker compose -f docker-compose.production.yml up -d
```

---

## Volume Management

### Inspect Volume

```bash
# List volumes
docker volume ls | grep inca_rag_scope

# Inspect volume details
docker volume inspect inca_rag_scope_postgres_data

# Check volume size
docker system df -v | grep inca_rag_scope_postgres_data
```

### DANGER: Delete Volume

```bash
# CAUTION: This will PERMANENTLY DELETE all data

# Stop database first
docker compose -f docker-compose.production.yml down

# Delete volume
docker volume rm inca_rag_scope_postgres_data
```

**IMPORTANT**: Always backup before deleting volume!

---

## Network Management

### Inspect Network

```bash
# List networks
docker network ls | grep inca_rag_scope

# Inspect network details
docker network inspect inca_rag_scope_net

# List containers on network
docker network inspect inca_rag_scope_net --format='{{range .Containers}}{{.Name}} {{end}}'
```

---

## Troubleshooting

### Database Won't Start

**Check logs**:
```bash
docker compose -f docker-compose.production.yml logs postgres
```

**Common issues**:
- Port 5432 already in use → Change `POSTGRES_PORT` in `.env`
- Volume permission errors → Check Docker volume permissions
- Memory limits → Adjust `shared_buffers` in compose file

### Connection Refused

**Check container status**:
```bash
docker ps -a | grep inca_rag_scope_db
```

**Check healthcheck**:
```bash
docker inspect inca_rag_scope_db --format='{{json .State.Health}}'
```

**Test connection from inside container**:
```bash
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c 'SELECT version();'
```

### Slow Queries

**Enable query logging**:
```bash
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker compose -f docker-compose.production.yml restart
```

**Check slow query log**:
```bash
docker exec -it inca_rag_scope_db tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

---

## Security Recommendations

### Production Checklist

- [ ] Change default `POSTGRES_PASSWORD` to strong password (20+ chars)
- [ ] Restrict `POSTGRES_PORT` to localhost only (change to `127.0.0.1:5432:5432`)
- [ ] Enable SSL/TLS for encrypted connections
- [ ] Set up regular automated backups
- [ ] Implement backup retention policy
- [ ] Test restore procedure regularly
- [ ] Monitor disk usage on volume
- [ ] Set up alerting for database health

### Restrict to Localhost

Edit `docker-compose.production.yml`:
```yaml
ports:
  - "127.0.0.1:5432:5432"  # Only accessible from host
```

---

## Integration with STEP 9 (DB Population)

This database is populated by **STEP 9 loaders** (see `docs/foundation/STEP9_DB_POPULATION_SPEC.md`).

**Workflow**:
```
1. Start database (this compose file)
2. Run STEP 9.1: Load Metadata (insurer, product, variant)
3. Run STEP 9.2: Load Documents
4. Run STEP 9.3: Load Coverage Canonical
5. Run STEP 9.4: Load Coverage Instances
6. Run STEP 9.5: Load Evidence
7. Run STEP 9.6: Load Amounts
8. Run STEP 9.7: Validation
```

**Database remains running** throughout pipeline execution.

---

## Monitoring

### Check Database Size

```bash
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "SELECT pg_size_pretty(pg_database_size('inca_rag_scope'));"
```

### Check Table Sizes

```bash
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Check Connection Count

```bash
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Configuration Tuning

### Memory Settings

Default settings in compose file are conservative. Adjust based on host resources:

- **shared_buffers**: 25% of system RAM (max 8GB)
- **effective_cache_size**: 50-75% of system RAM
- **work_mem**: total RAM / max_connections / 2
- **maintenance_work_mem**: 5% of system RAM (max 2GB)

**Example for 16GB RAM**:
```yaml
command:
  - -c
  - shared_buffers=4GB
  - -c
  - effective_cache_size=12GB
  - -c
  - work_mem=50MB
  - -c
  - maintenance_work_mem=1GB
```

### Connection Pooling

For high-concurrency applications, consider adding **PgBouncer** in front of PostgreSQL.

---

## Maintenance

### Vacuum

```bash
# Manual vacuum
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "VACUUM ANALYZE;"

# Vacuum specific table
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "VACUUM ANALYZE coverage_instance;"
```

### Reindex

```bash
# Reindex specific table
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "REINDEX TABLE coverage_instance;"

# Reindex database (requires exclusive lock)
docker exec -it inca_rag_scope_db psql -U inca_admin -d inca_rag_scope -c "REINDEX DATABASE inca_rag_scope;"
```

---

## Upgrade Strategy

### PostgreSQL Version Upgrade

**IMPORTANT**: Always backup before upgrading!

```bash
# 1. Backup current database
docker exec inca_rag_scope_db pg_dumpall -U inca_admin > full_backup_pre_upgrade.sql

# 2. Stop current database
docker compose -f docker-compose.production.yml down

# 3. Update image version in docker-compose.production.yml
#    Example: pgvector/pgvector:pg16 → pgvector/pgvector:pg17

# 4. Remove old volume (if incompatible)
docker volume rm inca_rag_scope_postgres_data

# 5. Recreate volume
docker volume create inca_rag_scope_postgres_data

# 6. Start new database
docker compose -f docker-compose.production.yml up -d

# 7. Restore from backup
docker exec -i inca_rag_scope_db psql -U inca_admin < full_backup_pre_upgrade.sql
```

---

## FAQ

### Q: Can I run multiple instances of this database?

**A**: No. This compose file is designed for **single database instance** only. Multiple instances would require separate volumes and ports.

### Q: Can I add application containers to this compose file?

**A**: No. This compose file is **database-only**. Application containers should use a separate compose file and connect via the `inca_rag_scope_net` network.

### Q: How do I migrate from old inca-rag containers?

**A**: Use `pg_dump` from old container and `pg_restore` to new container. See Backup/Restore section.

### Q: Where are database schemas defined?

**A**: Schemas are defined in `docs/foundation/DB_PHYSICAL_MODEL_EXTENDED.md` and applied via STEP 9 loaders. This compose file does NOT include schema scripts.

### Q: Can I use this for development?

**A**: Yes, but consider lowering memory settings and removing production tuning parameters for development environments.

---

## Related Documentation

- **Database Schema**: `docs/foundation/DB_PHYSICAL_MODEL_EXTENDED.md`
- **ERD**: `docs/foundation/ERD_PHYSICAL.md`
- **STEP 9 Population**: `docs/foundation/STEP9_DB_POPULATION_SPEC.md`
- **Metadata Spec**: `docs/foundation/PRODUCT_VARIANT_METADATA_SPEC.md`

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/jason-dio-so/inca-rag-scope/issues
- See `CLAUDE.md` for project context

---

## Version History

- **1.0** (2025-12-28): Initial production database configuration
  - Single PostgreSQL container with pgvector
  - Production tuning parameters
  - Healthcheck and restart policies
  - Volume and network isolation
