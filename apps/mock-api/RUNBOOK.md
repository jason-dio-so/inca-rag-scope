# Mock API Server - Runbook

STEP NEXT-9: Mock API + UI Integration

## Current Status

✅ **Completed**:
1. API Contract documentation (`docs/api/STEP_NEXT_9_API_CONTRACT.md`)
2. JSON Schemas (`docs/api/schema/*.json`)
3. Mock API server (`apps/mock-api/server.py`)
4. UI converted to API calls (`apps/web-prototype/index.html`)
5. Request schema validation (8/8 tests pass)

⚠️ **Known Issue**:
- Existing fixtures (from STEP NEXT-5) use different Response View Model structure
- Tests expect schema from STEP NEXT-9 contract
- 13/21 tests fail due to schema mismatch

## Quick Start (Current State)

### 1. Install Dependencies

```bash
cd apps/mock-api
pip install -r requirements.txt
```

### 2. Start Mock API Server

```bash
# From apps/mock-api directory
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Server running at: `http://localhost:8001`

### 3. Test Health Endpoint

```bash
curl http://localhost:8001/health
```

Expected output:
```json
{
  "status": "ok",
  "version": "mock-0.1.0",
  "timestamp": "2025-12-28T..."
}
```

### 4. Start UI (Separate Terminal)

```bash
cd apps/web-prototype
python3 -m http.server 8000
```

Open browser: `http://localhost:8000`

### 5. Test Integration

1. Click any example button (예제 1~4)
2. **Expected**: API call to `http://localhost:8001/compare`
3. **Current**: Returns fixture JSON (works, but schema mismatch)

## Testing

### Request Schema Tests (✅ PASS)

```bash
pytest tests/test_api_contract.py::TestRequestSchemaValidation -v
```

All 6 tests pass - request schema is correct.

### Response Schema Tests (⚠️ FAIL)

```bash
pytest tests/test_api_contract.py::TestResponseSchemaValidation -v
```

4/4 tests fail - fixtures don't match new contract schema.

## Schema Mismatch Details

### Current Fixtures Structure (STEP NEXT-5)

```json
{
  "meta": {
    "response_type": "comparison",
    "confidence_level": "document-based",
    "premium_notice": false,
    "generated_at": "2025-12-28T10:00:00+09:00"
  },
  "query_summary": {
    "original_query": "...",
    "interpreted_intent": "...",
    "target_insurers": [...],
    "target_products": [...]
  },
  "comparison": {
    "dimensions": [...],
    "values": [...]
  },
  "notes": "...",
  "limitations": {...}
}
```

### Expected Schema (STEP NEXT-9 Contract)

```json
{
  "meta": {
    "query_id": "uuid",
    "timestamp": "iso8601",
    "intent": "PRODUCT_SUMMARY",
    "compiler_version": "v1.0.0"
  },
  "query_summary": {
    "targets": [...],
    "coverage_scope": {...},
    "premium_notice": false
  },
  "comparison": {
    "type": "COVERAGE_TABLE",
    "columns": [...],
    "rows": [...]
  },
  "notes": [...],
  "limitations": [...]
}
```

## Next Steps (for fixture alignment)

### Option A: Update Fixtures to Match Contract (Recommended)

1. Transform `apps/mock-api/fixtures/*.json` to match STEP NEXT-9 schema
2. Re-run tests: `pytest tests/test_api_contract.py -v`
3. All 21 tests should pass

### Option B: Update Contract to Match Existing Fixtures

1. Modify `docs/api/schema/compare_response_view_model.schema.json`
2. Update `docs/api/STEP_NEXT_9_API_CONTRACT.md`
3. This reverses the "contract lock" intent

## Production Deployment (Future)

When moving to real API:

1. Replace `server.py` with actual backend implementation
2. Remove `debug.force_example` from requests
3. Connect to DB/retrieval/evidence system
4. Keep same request/response contract
5. UI works without changes (API contract is stable)

## Debugging

### CORS Issues

If UI shows CORS errors:
- Check server logs: Mock API should show CORS middleware enabled
- Verify `allow_origins` includes `http://localhost:8000`

### API Not Found

If UI shows "Failed to fetch":
- Check Mock API is running on port 8001
- Check network tab in browser DevTools
- Verify `API_BASE_URL = 'http://localhost:8001'` in `index.html`

### Schema Validation Errors

```bash
# Test specific schema
python -c "import json; from jsonschema import validate; \
  schema=json.load(open('docs/api/schema/compare_request.schema.json')); \
  data=json.load(open('test_request.json')); \
  validate(data, schema); print('PASS')"
```

## Forbidden Phrases Found

Current fixtures contain forbidden phrases:
- example1, example2, example3: "추천" found
- These should be removed in fixture updates

## File Structure

```
apps/mock-api/
├── server.py              # FastAPI server
├── requirements.txt       # Dependencies
├── README.md             # Quick reference
├── RUNBOOK.md            # This file
└── fixtures/             # Response fixtures (STEP NEXT-5 format)
    ├── example1_premium.json
    ├── example2_coverage_compare.json
    ├── example3_product_summary.json
    └── example4_ox.json
```

## Contact

For schema questions: See `docs/api/STEP_NEXT_9_API_CONTRACT.md`
