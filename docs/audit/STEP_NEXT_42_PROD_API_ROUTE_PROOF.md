# STEP NEXT-42: Production API Route Proof (Code Evidence)

## Source File
`apps/api/server.py`

---

## Production API Routes (From Code)

### 1. Root Endpoint
- **Path**: `/`
- **Method**: `GET`
- **Line**: 795-815
- **Handler**: `root()`
- **Response**: API info (name, version, endpoints list)

### 2. Health Check
- **Path**: `/health`
- **Method**: `GET`
- **Line**: 648-667
- **Handler**: `health_check()`
- **Response**: Health status + DB connection check

### 3. Compare Endpoint (Main)
- **Path**: `/compare`
- **Method**: `POST`
- **Line**: 669-730
- **Handler**: `compare(request: CompareRequest)`
- **Contract**: `CompareRequest` (line 101-107) → Response View Model (5-block)
- **Features**:
  - Product Validation Gate (line 695-697)
  - Fact-First value_text (line 554-564)
  - Evidence Quality Filter (line 227-278)

### 4. Chat Endpoint
- **Path**: `/chat`
- **Method**: `POST`
- **Line**: 732-770
- **Handler**: `chat(request_dict: dict)`
- **Note**: STEP NEXT-14 feature (ChatGPT-style UI)

### 5. FAQ Templates
- **Path**: `/faq/templates`
- **Method**: `GET`
- **Line**: 773-792
- **Handler**: `get_faq_templates()`
- **Note**: STEP NEXT-14 feature

---

## Execution Method (From Code)

**No `if __name__ == "__main__"` block found in server.py**

### Standard uvicorn execution:
```bash
# apps/api/server.py line 817 comment:
# Run with: uvicorn apps.api.server_v2:app --host 0.0.0.1 --port 8001 --reload
```

**Corrected command** (file is `server.py`, not `server_v2.py`):
```bash
cd /Users/cheollee/inca-rag-scope
uvicorn apps.api.server:app --host 127.0.0.1 --port 8002 --log-level info
```

**Port choice**: 8002 (avoiding 8000=static HTML, 8001=mock API)

---

## FastAPI App Object
- **Variable**: `app`
- **Line**: 43-47
- **Title**: "Insurance Comparison Production API"
- **Version**: "1.1.0-beta"
- **CORS**: Enabled for localhost:8000/9000

---

## Database Connection
- **DB URL**: `postgresql://inca_admin:inca_secure_prod_2025_db_key@localhost:5432/inca_rag_scope`
- **Line**: 64-67
- **Connection Manager**: `DBConnection.get_connection()` (line 117-124)

---

## Next: Execute Production API on port 8002
