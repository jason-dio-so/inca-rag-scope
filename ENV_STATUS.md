# 🚀 Environment Status - STEP NEXT-UI-02

**Date**: 2026-01-01
**Status**: ✅ **RUNNING**

---

## 📍 Services

| Service | URL | Status |
|---------|-----|--------|
| **API Server** | http://localhost:8000 | ✅ Running |
| **API Docs** | http://localhost:8000/docs | ✅ Available |
| **Web UI** | http://localhost:3000 | ✅ Running |

---

## 🎯 Quick Access

### Web UI
```
http://localhost:3000
```

브라우저에서 위 주소를 열어 사용하세요.

### API Swagger Docs
```
http://localhost:8000/docs
```

API 문서 및 테스트 인터페이스

---

## 🔧 Control Commands

### Check Status
```bash
# API Health
curl http://localhost:8000/health

# Web UI
curl http://localhost:3000
```

### View Logs
```bash
# API Logs
tail -f /tmp/api-server.log

# Web UI Logs
tail -f /tmp/web-ui.log
```

### Stop Services
```bash
./stop-env.sh
```

Or manually:
```bash
# Stop API
pkill -f 'uvicorn apps.api.server'

# Stop Web UI
pkill -f 'next dev'
```

### Restart Services
```bash
# Stop first
./stop-env.sh

# Then start
./start-env-simple.sh
```

---

## 📋 Example Usage (Web UI)

### Example 1: Premium Comparison
1. Click "① 단순보험료 비교" in sidebar
2. Click "예시 실행" button
3. Click "전송"
4. Result appears on right panel

### Example 2: Coverage Detail
1. Click "④ 상품/담보 설명" in sidebar
2. Click "예시 실행" button
3. Insurers auto-selected: 삼성, 메리츠
4. Coverage auto-filled: 암진단비(유사암제외)
5. Click "전송"
6. Coverage limit table appears

### Example 3: Two-Insurer Comparison
1. Click "⑤ 상품 비교" in sidebar
2. Click "예시 실행" button
3. Click "전송"
4. Side-by-side comparison table appears

### Example 4: Subtype Eligibility
1. Click "⑤ 상품 비교" in sidebar
2. Select insurers (e.g., 삼성, 메리츠)
3. Type: "제자리암 보장되나요?"
4. Click "전송"
5. Eligibility matrix appears (O/X/△/Unknown)

---

## 🔍 Background Process IDs

Check running processes:
```bash
# Find API process
ps aux | grep 'uvicorn apps.api.server'

# Find Web UI process
ps aux | grep 'next dev'
```

---

## ⚠️ Troubleshooting

### API Not Responding
```bash
# Check if running
curl http://localhost:8000/health

# If not, restart
pkill -f 'uvicorn apps.api.server'
uvicorn apps.api.server:app --host 0.0.0.0 --port 8000 &
```

### Web UI Not Responding
```bash
# Check if running
curl http://localhost:3000

# If not, restart
pkill -f 'next dev'
cd /Users/cheollee/inca-rag-scope/apps/web && npm run dev &
```

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Find what's using port 3000
lsof -i :3000

# Kill specific process
kill -9 <PID>
```

---

## 📚 Documentation

- **UI Guide**: `docs/STEP_NEXT_UI_02_LOCAL.md`
- **API Guide**: `docs/STEP_NEXT_UI_01.md`
- **Web README**: `apps/web/README.md`

---

**END OF STATUS**
