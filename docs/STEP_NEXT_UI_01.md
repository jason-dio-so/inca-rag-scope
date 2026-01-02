# STEP NEXT-UI-01: ChatGPT UI Implementation (LLM OFF)

**Date**: 2026-01-01
**Purpose**: Implement customer examples 1-4 in ChatGPT-style UI with 100% LLM OFF deterministic rendering
**Status**: ✅ COMPLETE

---

## 📋 목표 (Goal)

기존 결정론적 파이프라인 (STEP NEXT-61~63) 산출물을 사용하여
고객 예제 1~4를 ChatGPT 스타일 UI로 100% 재현 (LLM OFF 기본)

---

## 🏗️ 아키텍처 (Architecture)

```
┌───────────────────────────────────────────────┐
│ Frontend (Future: Next.js)                    │
│ - Sidebar categories (①②④⑤⑥)                 │
│ - Chat input                                   │
│ - Result cards                                 │
└──────────────┬────────────────────────────────┘
               │ POST /chat
               │ {selected_category, message, llm_mode}
               ↓
┌───────────────────────────────────────────────┐
│ API Layer (FastAPI)                           │
│ apps/api/server.py                            │
├───────────────────────────────────────────────┤
│ IntentRouter (Category-based)                 │
│ - Priority 1: selected_category               │
│ - Priority 2: FAQ template                    │
│ - Priority 3: Keyword matching                │
├───────────────────────────────────────────────┤
│ Handler Dispatcher                            │
│ - LLM OFF → Deterministic Handlers (Step8)   │
│ - LLM ON  → Legacy Handlers (optional)        │
└──────────────┬────────────────────────────────┘
               ↓
┌───────────────────────────────────────────────┐
│ Step8 Render Engine (Deterministic)           │
│ pipeline/step8_render_deterministic/          │
│ - PremiumComparer                             │
│ - CoverageLimitComparer                       │
│ - TwoInsurerComparer                          │
│ - SubtypeEligibilityChecker                   │
└──────────────┬────────────────────────────────┘
               ↓
┌───────────────────────────────────────────────┐
│ Data Sources (SSOT)                           │
│ - data/scope_v3/*_step2_canonical_scope*.jsonl│
│ - data/compare/*_coverage_cards.jsonl         │
│ - data/evidence_text/*                        │
└───────────────────────────────────────────────┘
```

---

## 🎯 카테고리 매핑 (Category Mapping)

| 카테고리 | Example | Handler | Step8 Engine |
|---------|---------|---------|-------------|
| ① 단순보험료 비교 | 예제 1 | Example1HandlerDeterministic | PremiumComparer |
| ④ 상품/담보 설명 | 예제 2 | Example2HandlerDeterministic | CoverageLimitComparer |
| ⑤ 상품 비교 | 예제 3 | Example3HandlerDeterministic | TwoInsurerComparer |
| ⑤ 상품 비교 (subtype) | 예제 4 | Example4HandlerDeterministic | SubtypeEligibilityChecker |
| ⑥ 보험 상식 | - | (Future RAG) | - |

---

## 🔧 구현 내용 (Implementation)

### 1. Category-Based Routing (`chat_intent.py`)

**Added**:
```python
CATEGORY_MAPPING: Dict[str, MessageKind] = {
    "단순보험료 비교": "EX1_PREMIUM_DISABLED",
    "상품/담보 설명": "EX2_DETAIL",
    "상품 비교": "EX3_INTEGRATED",
    "보험 상식": "KNOWLEDGE_BASE"
}
```

**Routing Priority**:
1. `selected_category` (sidebar click) → 100% deterministic
2. FAQ template → 100% deterministic
3. Keyword patterns → fallback

### 2. ChatRequest Extension (`chat_vm.py`)

**Added fields**:
```python
selected_category: Optional[str] = None  # Category from sidebar
llm_mode: Literal["OFF", "ON"] = "OFF"   # Default: LLM OFF
```

### 3. Deterministic Handlers (`chat_handlers_deterministic.py`)

**New handlers** (all LLM OFF):
- `Example1HandlerDeterministic`: Uses `PremiumComparer` from Step8
- `Example2HandlerDeterministic`: Uses `CoverageLimitComparer` from Step8
- `Example3HandlerDeterministic`: Uses `TwoInsurerComparer` from Step8
- `Example4HandlerDeterministic`: Uses `SubtypeEligibilityChecker` from Step8

**Key features**:
- ✅ Zero LLM calls
- ✅ Forbidden phrase validation
- ✅ Evidence references in all outputs
- ✅ Gate enforcement (join_rate, evidence_fill_rate)

### 4. Handler Dispatcher Update (`chat_intent.py`)

```python
# STEP NEXT-UI-01: Use deterministic handlers by default
if request.llm_mode == "OFF":
    from apps.api.chat_handlers_deterministic import HandlerRegistryDeterministic
    handler = HandlerRegistryDeterministic.get_handler(kind)
else:
    # LLM ON mode (optional)
    from apps.api.chat_handlers import HandlerRegistry
    handler = HandlerRegistry.get_handler(kind)
```

### 5. UI Configuration (`apps/ui_config.json`)

**Configuration includes**:
- Category definitions (①④⑤⑥)
- Available insurers (8개)
- Common coverages
- UI settings (LLM OFF default, evidence collapsed)

---

## 📊 Request/Response Flow

### Example Request (Category-based)

```json
POST /chat

{
  "message": "삼성화재와 메리츠화재 암진단비 비교해주세요",
  "selected_category": "상품 비교",
  "insurers": ["samsung", "meritz"],
  "coverage_names": ["암진단비(유사암제외)"],
  "llm_mode": "OFF"
}
```

### Example Response (AssistantMessageVM)

```json
{
  "kind": "EX3_INTEGRATED",
  "title": "samsung vs meritz A4200_1 비교",
  "summary_bullets": [
    "금액: 상이 (3,000만원 / 2,000만원)",
    "지급유형: 동일 (정액)"
  ],
  "sections": [
    {
      "kind": "comparison_table",
      "table_kind": "INTEGRATED_COMPARE",
      "columns": ["구분", "samsung", "meritz"],
      "rows": [...]
    },
    {
      "kind": "common_notes",
      "groups": [
        {"title": "공통사항", "bullets": [...]},
        {"title": "유의사항", "bullets": [...]}
      ]
    }
  ],
  "lineage": {
    "handler": "Example3HandlerDeterministic",
    "llm_used": false,
    "deterministic": true,
    "gates": {"join_rate": 1.0, "evidence_fill_rate": 0.8}
  }
}
```

---

## ✅ 헌법 준수 (Constitutional Compliance)

| Rule | Status | Evidence |
|------|--------|----------|
| ❌ NO LLM (default) | ✅ PASS | `llm_mode="OFF"` default |
| ❌ NO Step1/2/Excel modification | ✅ PASS | Zero modifications |
| ❌ NO inference/recommendation | ✅ PASS | Forbidden phrase validation |
| ✅ Evidence-based only | ✅ PASS | All outputs have evidence refs |
| ✅ Deterministic | ✅ PASS | Step8 render engine |
| ✅ Category routing | ✅ PASS | `CATEGORY_MAPPING` |

---

## 🧪 테스트 (Tests)

### Test Suite: `tests/test_ui01_deterministic_handlers.py`

**Coverage**:
- Example 1: Premium comparison (disabled response)
- Example 2: Coverage limit comparison
- Example 3: Two-insurer comparison
- Example 4: Subtype eligibility
- Handler registry
- Forbidden phrase validation

**Run**:
```bash
pytest tests/test_ui01_deterministic_handlers.py -v
```

---

## 📦 산출물 (Deliverables)

### Code Files

| File | Purpose |
|------|---------|
| `apps/api/chat_handlers_deterministic.py` | Deterministic handlers (Step8 integration) |
| `apps/api/chat_intent.py` | Category-based routing |
| `apps/api/chat_vm.py` | ChatRequest extension (category + llm_mode) |
| `apps/ui_config.json` | UI configuration (categories, insurers, coverages) |

### Test Files

| File | Purpose |
|------|---------|
| `tests/test_ui01_deterministic_handlers.py` | Handler tests (LLM OFF) |

### Documentation

| File | Purpose |
|------|---------|
| `docs/STEP_NEXT_UI_01.md` | This file |

---

## 🚀 실행 방법 (How to Run)

### 1. Start API Server

```bash
cd /Users/cheollee/inca-rag-scope
python3 -m apps.api.server
```

Server runs at: `http://localhost:8000`

### 2. Test API Endpoint

```bash
# Example 2: Coverage limit comparison
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "암진단비 보장한도 알려주세요",
    "selected_category": "상품/담보 설명",
    "insurers": ["samsung", "meritz"],
    "coverage_names": ["암진단비(유사암제외)"],
    "llm_mode": "OFF"
  }'
```

### 3. Run Tests

```bash
pytest tests/test_ui01_deterministic_handlers.py -v
```

---

## 🎨 UI 레이아웃 (UI Layout)

```
┌──────────────────────────────────────────────────┐
│ 보험 상품 비교 도우미                             │
└──────────────────────────────────────────────────┘
┌─────────────┬────────────────────────────────────┐
│ Sidebar     │ Chat Area                          │
├─────────────┤                                    │
│ ① 단순보험료 │ User: 삼성화재와 메리츠 암진단비   │
│   비교      │       비교해주세요                  │
│             │                                    │
│ ④ 상품/담보  │ Assistant: [Summary Card]         │
│   설명      │            [Comparison Table]      │
│             │            [Common Notes]          │
│ ⑤ 상품 비교  │            [Evidence (Collapsed)] │
│             │                                    │
│ ⑥ 보험 상식  │                                    │
│   (준비중)   │                                    │
└─────────────┴────────────────────────────────────┘
```

---

## 📝 다음 단계 (Next Steps)

### STEP NEXT-UI-02 (제안): Next.js Frontend

**Scope**:
1. Next.js + TypeScript setup
2. Sidebar categories (⑥ categories)
3. Chat input/output components
4. Evidence viewer with toggle
5. ViewModel → React component mapping

**Tech Stack**:
- Next.js 14
- TypeScript
- Tailwind CSS
- SWR (API fetching)

---

## 🔒 헌법 체크리스트 (Constitutional Checklist)

- [x] ❌ NO LLM calls (LLM OFF default)
- [x] ❌ NO Step1/2/Excel modifications
- [x] ❌ NO inference/recommendation phrases
- [x] ✅ Evidence references in all outputs
- [x] ✅ Deterministic rendering (Step8)
- [x] ✅ Category-based routing
- [x] ✅ Forbidden phrase validation
- [x] ✅ Gates enforced (join_rate, evidence_fill_rate)

---

## 💡 핵심 성과 (Key Achievements)

1. **LLM OFF 기본값**: 모든 예제가 LLM 없이 100% 동작
2. **카테고리 라우팅**: 사이드바 클릭 → 100% 결정론적 분기
3. **Step8 통합**: Deterministic render engine을 Chat Handlers에 완전 통합
4. **Evidence 기반**: 모든 숫자/조건에 근거 문서 참조 존재
5. **Forbidden Phrase 검증**: 추천/우열 판단 문장 자동 차단

---

**END OF DOCUMENT**
