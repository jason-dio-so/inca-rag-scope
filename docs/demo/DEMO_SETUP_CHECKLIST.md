# Demo Setup Checklist
**STEP NEXT-38-E: Pre-Demo Verification**

Use this checklist **every time** before starting a customer demo.

---

## Pre-Demo (15 minutes before)

### 1. Environment Check
- [ ] Working directory: `/Users/cheollee/inca-rag-scope`
- [ ] Git branch: Confirm you're on a stable branch (not mid-development)
- [ ] No uncommitted critical changes in working tree
- [ ] Python version: 3.11+ (`python --version`)

### 2. Port Availability
- [ ] Port 8001 free (Mock API)
  ```bash
  lsof -i :8001
  # Should return empty. If occupied, kill process:
  # kill -9 <PID>
  ```
- [ ] Port 8000 free (Web UI)
  ```bash
  lsof -i :8000
  # Should return empty. If occupied, kill process:
  # kill -9 <PID>
  ```

### 3. Dependencies
- [ ] Mock API requirements installed
  ```bash
  cd apps/mock-api
  pip install -r requirements.txt
  # Expected: fastapi, uvicorn, pydantic
  ```

### 4. Fixture Integrity
- [ ] All 4 fixture files present:
  ```bash
  ls -1 apps/mock-api/fixtures/
  # Expected:
  # example1_premium.json
  # example2_coverage_compare.json
  # example3_product_summary.json
  # example4_ox.json
  ```
- [ ] Fixture files are valid JSON
  ```bash
  jq empty apps/mock-api/fixtures/*.json
  # Should return no errors
  ```

---

## Startup Sequence (5 minutes before)

### Step 1: Start Mock API
```bash
cd /Users/cheollee/inca-rag-scope/apps/mock-api
python -m uvicorn server:app --host 127.0.0.1 --port 8001 --log-level warning
```
Expected output:
```
INFO:     Started server process [PID]
INFO:     Uvicorn running on http://127.0.0.1:8001
```

- [ ] Mock API started successfully
- [ ] No error messages in console

### Step 2: Verify Mock API Health
In a **separate terminal**:
```bash
curl http://127.0.0.1:8001/health
```
Expected response:
```json
{"status":"ok","version":"mock-0.1.0","timestamp":"2025-XX-XXTXX:XX:XXZ"}
```

- [ ] Health check returns HTTP 200
- [ ] Status is "ok"
- [ ] Timestamp is current

### Step 3: Test Mock API Example
```bash
curl -X POST http://127.0.0.1:8001/compare \
  -H "Content-Type: application/json" \
  -d '{"intent":"PRODUCT_SUMMARY","insurers":["samsung"],"products":[{"insurer":"samsung","product_name":"test"}]}' \
  | jq '.meta.intent'
```
Expected: `"PRODUCT_SUMMARY"`

- [ ] API returns valid JSON response
- [ ] Intent field matches request

### Step 4: Start Web UI
In a **third terminal**:
```bash
cd /Users/cheollee/inca-rag-scope/apps/web-prototype
python -m http.server 8000
```
Expected output:
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

- [ ] Web server started successfully
- [ ] No error messages

### Step 5: Verify Web UI Load
Open browser:
```
http://127.0.0.1:8000/index.html
```

- [ ] Page loads without errors
- [ ] 4 example buttons visible:
  - [ ] "예제 1: 보험료 참고"
  - [ ] "예제 2: 담보 조건 비교"
  - [ ] "예제 3: 상품 요약 비교"
  - [ ] "예제 4: 보장 가능 여부 (O/X)"
- [ ] No JavaScript console errors (F12 → Console)

### Step 6: Test Example 3 (Core Demo)
Click **"예제 3: 상품 요약 비교"** button

- [ ] API call triggered (check Network tab)
- [ ] Response rendered in UI
- [ ] 5 blocks visible:
  - [ ] Meta (Query ID, Timestamp, Intent)
  - [ ] Query Summary (Targets, Coverage scope)
  - [ ] Comparison Table (9 coverage rows)
  - [ ] Notes (7 notes)
  - [ ] Limitations (4 limitations)
- [ ] No "undefined" or "null" displayed in UI
- [ ] Evidence snippets display properly

---

## Browser Setup

### Recommended Browser
- [ ] Chrome or Firefox (latest version)
- [ ] Safari acceptable but test first

### Browser Settings
- [ ] Disable browser cache (F12 → Network → "Disable cache" checked)
- [ ] Zoom level: 100% (Cmd+0 / Ctrl+0)
- [ ] Full screen or large window (min 1280x800)

### Before Each Demo
- [ ] Clear browser cache: Cmd+Shift+R / Ctrl+Shift+R
- [ ] Close unnecessary tabs
- [ ] Bookmark http://127.0.0.1:8000/index.html for quick access

---

## Network & Connectivity

### Local-Only Demo (Recommended)
- [ ] Both servers running on localhost (127.0.0.1)
- [ ] No external network required
- [ ] Wi-Fi can be disabled (after confirming servers are running)

### If Network Issues Occur
- [ ] Check firewall settings (allow localhost connections)
- [ ] Check browser CORS errors (F12 → Console)
- [ ] Restart both servers if CORS errors appear

---

## Fallback Plans

### If Mock API Fails
**Option 1**: Restart Mock API
```bash
# Kill existing process
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Restart
cd apps/mock-api && python -m uvicorn server:app --host 127.0.0.1 --port 8001
```

**Option 2**: Use static fixtures
- UI can load fixtures directly from `apps/web-prototype/fixtures/` (if configured)

### If Web UI Fails
**Option 1**: Restart Web Server
```bash
# Kill existing process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Restart
cd apps/web-prototype && python -m http.server 8000
```

**Option 2**: Serve with alternative method
```bash
# Node.js (if available)
cd apps/web-prototype && npx http-server -p 8000
# Or PHP
cd apps/web-prototype && php -S 127.0.0.1:8000
```

### If Entire Demo Environment Fails
- [ ] Have PDF screenshots ready (backup)
- [ ] Prepare to walk through scenario scripts verbally
- [ ] Reschedule if necessary (better than buggy demo)

---

## Post-Demo Cleanup

### Stop Servers
```bash
# Find and kill processes
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill
```
- [ ] Port 8001 released
- [ ] Port 8000 released

### Reset Environment
- [ ] No changes made to fixture files
- [ ] No data/ files committed (if any edits occurred)
- [ ] Terminal logs saved if debugging needed

---

## Emergency Contacts & Resources

### Documentation
- Demo script: `docs/demo/DEMO_SCRIPT_SCENARIOS.md`
- FAQ: `docs/demo/DEMO_FAQ.md`
- API contract: `docs/api/STEP_NEXT_9_API_CONTRACT.md` (if exists)

### Quick Commands
```bash
# Full reset (if needed)
cd /Users/cheollee/inca-rag-scope
git status  # Check for uncommitted changes
pytest -q   # Verify tests pass (optional)

# Restart everything
lsof -i :8001,:8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
cd apps/mock-api && python -m uvicorn server:app --host 127.0.0.1 --port 8001 &
cd ../web-prototype && python -m http.server 8000 &
```

---

## Final Go/No-Go Check (2 minutes before demo)

- [ ] Mock API health: ✓
- [ ] Web UI loads: ✓
- [ ] Example 3 renders: ✓
- [ ] Demo script printed/accessible: ✓
- [ ] Confident in constitutional rules: ✓
  - No recommendations
  - Evidence-based only
  - Scope-limited
  - Read-only

**If all checked**: Proceed with demo ✓
**If any unchecked**: Troubleshoot or reschedule

---

**Last Updated**: 2025-12-31 (STEP NEXT-38-E)
**Owner**: Demo operator
**Review**: Before every customer demo
