# Mock API Server

STEP NEXT-9: Fixture-based mock API for UI integration testing

## Purpose

- Test API contract without real backend
- Enable UI/backend parallel development
- Validate Request/Response schemas

## Absolute Rules

1. **NO DB connections**
2. **NO retrieval/search**
3. **NO LLM calls**
4. **Fixture-based responses only**

## Installation

```bash
cd apps/mock-api
pip install -r requirements.txt
```

## Running

```bash
# From apps/mock-api directory
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Server will start at: `http://localhost:8001`

## Endpoints

### GET /health

Health check

```bash
curl http://localhost:8001/health
```

### POST /compare

Main comparison endpoint

**Example Request**:
```bash
curl -X POST http://localhost:8001/compare \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "PRODUCT_SUMMARY",
    "insurers": ["SAMSUNG", "HANWHA"],
    "products": [
      {"insurer": "SAMSUNG", "product_name": "삼성화재 무배당 New 원더풀 암보험"},
      {"insurer": "HANWHA", "product_name": "한화생명 무배당 암보험"}
    ],
    "target_coverages": [],
    "debug": {
      "force_example": "example3_product_summary"
    }
  }'
```

## Fixtures

Located in `fixtures/`:
- `example1_premium.json` - 보험료 비교
- `example2_coverage_compare.json` - 담보 조건 차이
- `example3_product_summary.json` - 상품 종합 비교 (9개 담보)
- `example4_ox.json` - 보장 가능 여부 O/X

## Routing Logic

| Intent | Fixture |
|--------|---------|
| PRODUCT_SUMMARY | example3 |
| COVERAGE_CONDITION_DIFF | example2 |
| COVERAGE_AVAILABILITY | example4 |
| PREMIUM_REFERENCE | example1 |

Override with `debug.force_example` for testing.

## CORS

Enabled for:
- `http://localhost:8000` (web-prototype)
- `http://127.0.0.1:8000`

## Testing

```bash
# Health check
curl http://localhost:8001/health

# Example 3 (default)
curl -X POST http://localhost:8001/compare \
  -H "Content-Type: application/json" \
  -d '{"intent":"PRODUCT_SUMMARY","insurers":["SAMSUNG"],"products":[{"insurer":"SAMSUNG","product_name":"test"}]}'
```
