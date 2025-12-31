# STEP NEXT-42: Port & Process Audit (READ-ONLY)

## 목적
Production API 실행 전, 8000/8001 포트 정체를 증거로 확정

---

## 1) Port 8000 — Static HTML Server

```bash
$ lsof -i :8000 -nP
COMMAND    PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
python3.1 4630 cheollee    4u  IPv6 0xce262cebfe6bd9e3      0t0  TCP *:8000 (LISTEN)
```

```bash
$ ps aux | grep 4630
cheollee  4630   0.0  0.1 435277888  15904   ??  SN    1:55PM   0:00.74 /Users/cheollee/.pyenv/versions/3.11.13/bin/python -m http.server 8000
```

```bash
$ curl -sS http://127.0.0.1:8000/ | head -40
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>보험 상품 비교 도우미 - UI Prototype</title>
```

**판정**: Port 8000 = `python -m http.server` serving static HTML prototype (web-prototype)

---

## 2) Port 8001 — Mock API

```bash
$ lsof -i :8001 -nP
COMMAND    PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
python3.1 3266 cheollee   10u  IPv4 0xf7efb0da5b715b05      0t0  TCP 127.0.0.1:8001 (LISTEN)
```

```bash
$ ps aux | grep 3266
cheollee  3266   0.0  0.2 435334672  25312   ??  SN    1:53PM   0:07.57 /Users/cheollee/.pyenv/versions/3.11.13/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8001 --log-level warning
```

```bash
$ curl -sS http://127.0.0.1:8001/
{"name":"Insurance Comparison Mock API","version":"mock-0.1.0","endpoints":{"health":"GET /health","compare":"POST /compare"},"note":"This is a mock API for testing. No real data processing."}
```

**판정**: Port 8001 = Mock API (`apps/mock-api/server.py`)
- 응답에 `"version":"mock-0.1.0"` 명시
- **이 포트는 본 STEP에서 사용 금지**

---

## 3) 결론

| Port | Process | Type | Status for STEP NEXT-42 |
|------|---------|------|-------------------------|
| 8000 | `python -m http.server` | Static HTML (web-prototype) | Out of scope |
| 8001 | `uvicorn server:app` | Mock API | **NO USE (mock)** |
| TBD  | Production API (`apps/api/server.py`) | Real DB-backed API | **Will run on different port** |

**Next**: Phase B will execute Production API on a clean port (not 8000/8001)
