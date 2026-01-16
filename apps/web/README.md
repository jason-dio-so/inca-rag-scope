# Insurance Comparison UI (STEP NEXT-UI-02)

Local-first ChatGPT-style UI for insurance product comparison.

## Quick Start

### 1. Start API Server (Required)

```bash
# Terminal 1: API Server
cd /Users/cheollee/inca-rag-scope
python3 -m apps.api.server
```

API runs at: `http://localhost:8000`

### 2. Start Next.js UI

```bash
# Terminal 2: Next.js UI
cd /Users/cheollee/inca-rag-scope/apps/web
npm run dev
```

UI runs at: `http://localhost:3000`

## Features

- ✅ LLM OFF by default (deterministic rendering)
- ✅ 4 example categories with one-click execution
- ✅ Evidence references with toggle
- ✅ Multi-insurer comparison
- ✅ Coverage limit comparison

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- fetch API (SWR ready)

## Documentation

See: `docs/STEP_NEXT_UI_02_LOCAL.md`
