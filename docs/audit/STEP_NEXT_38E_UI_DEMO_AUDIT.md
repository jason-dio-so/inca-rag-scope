# STEP NEXT-38E UI/Demo Audit — Evidence-Based Reuse Assessment

**Document Type**: Pre-Implementation Audit
**Created**: 2025-12-31
**Purpose**: Identify existing UI/demo assets to prevent duplicate work before STEP NEXT-38-E execution

---

## 1. Existing Assets Inventory

### 1.1 Core Documentation (Constitutional Level)

**Output Schema & View Model** (`docs/ui/`):
- `STEP_NEXT_2_RESPONSE_VIEW_MODEL_AND_UX.md` — 5-block Response View Model (meta, query_summary, comparison, notes, limitations)
- `STEP_NEXT_3_UI_SKELETON.md` — UI component structure mapped to View Model
- `STEP_NEXT_4_UI_MOCK.md` — ChatGPT-style UI mockup
- `STEP_NEXT_5_UI_PROTOTYPE_RUNBOOK.md` — Prototype execution guide

**API Contract** (`docs/api/`):
- `STEP_NEXT_9_API_CONTRACT.md` — CompareRequest/CompareResponse schemas (FINAL)
- `schema/compare_request.schema.json` — Request JSON schema
- `schema/compare_response_view_model.schema.json` — Response JSON schema
- `END_TO_END_FLOW.md` — Full pipeline flow (Query → Intent → SQL → Response)

**UX Policy** (`docs/ui/`):
- `CHAT_UX_SCENARIOS.md` — 4 example scenarios + forbidden responses
- `CHAT_UX_DOS_AND_DONTS.md` — Tone, phrasing rules
- `CHAT_VISUAL_DOS_AND_DONTS.md` — Visual design constraints
- `COMPARISON_EXPLANATION_RULES.md` — How to explain comparisons without recommendations
- `AMOUNT_PRESENTATION_RULES.md` — How to display amounts (CONFIRMED/UNCONFIRMED)

### 1.2 Working Prototype (`apps/`)

**HTML/JS Prototype** (`apps/web-prototype/`):
- `index.html` (850 lines) — Full working UI prototype
  - Response View Model 5-block renderer
  - 4 example buttons (premium, coverage_compare, product_summary, O/X)
  - Comparison table with evidence modal
  - ChatGPT-style chat stream layout
  - Premium notice banner
  - Responsive design (mobile-ready)

**Mock API Server** (`apps/mock-api/`):
- `server.py` — FastAPI mock server (no DB, fixture-based)
- `fixtures/` — 4 example response JSONs:
  - `example1_premium.json` — Premium comparison with warning
  - `example2_coverage_compare.json` — Coverage condition diff (5 conditions)
  - `example3_product_summary.json` — Product summary (9 coverages) ⭐
  - `example4_ox.json` — Coverage availability (O/X boolean)
- `RUNBOOK.md` — How to run mock server

**Real API** (`apps/api/`):
- `server.py` — Main FastAPI app (DB-connected)
- `chat_handlers.py` — Intent routing
- `dto.py` — Request/Response DTOs
- `chat_vm.py` — View Model construction
- `presentation_utils.py` — Formatting utilities
- `explanation_handler.py` — Notes/summary generation
- `policy/forbidden_language.py` — "추천", "권장" detection

### 1.3 Integration Mapping (`docs/ui/`)

**Customer Example → UI Mapping**:
- `CUSTOMER_EXAMPLE_SCREEN_MAPPING.md` — 4 examples mapped to components
- `FRONTEND_INTEGRATION_GUIDE.md` — How to integrate with real API

**Component Contract**:
- `CHAT_COMPONENT_CONTRACT.md` — Component interface specs
- `CHAT_LAYOUT_SPEC.md` — Chat stream layout rules

---

## 2. What is Already Solved

### 2.1 ✅ Output Schema (LOCKED)

**Status**: COMPLETE and IMMUTABLE

**Evidence**:
- `STEP_NEXT_2_RESPONSE_VIEW_MODEL_AND_UX.md` (committed 9e7df7b)
- 5-block structure defined: `meta`, `query_summary`, `comparison`, `notes`, `limitations`
- JSON schemas in `docs/api/schema/`

**Key Decisions Already Made**:
- ❌ NO recommendations ("추천", "권장", "제안")
- ❌ NO premium calculation (only reference with `premium_notice=true`)
- ✅ Evidence required for all values ("확인 불가" if missing)
- ✅ Document-based facts only (no inference)

**Action**: REUSE AS-IS. Do NOT redesign schema.

### 2.2 ✅ UI Components (PROTOTYPE EXISTS)

**Status**: WORKING PROTOTYPE READY

**Evidence**:
- `apps/web-prototype/index.html` (850 lines, committed b8d33e7)
- Renders all 4 examples successfully
- Modal for evidence details
- Responsive table layout
- Premium warning banner

**Components Implemented**:
- `<IntroSection>` — System capabilities/limitations
- `<ExampleQuestions>` — 4 button examples
- `<QueryInput>` — (placeholder, can be added)
- `<ResponseArea>` — Renders 5-block View Model
  - `renderQuerySummary()` — Target products list
  - `renderComparison()` — Comparison table with evidence
  - `renderNotes()` — Summary + collapsible details
  - `renderLimitations()` — Collapsible warnings
- `<EvidenceModal>` — Shows document snippet (placeholder)

**Action**: EXTEND EXISTING. Do NOT rebuild from scratch.

### 2.3 ✅ Mock API Server (WORKING)

**Status**: FULLY FUNCTIONAL

**Evidence**:
- `apps/mock-api/server.py` (committed 8dc8616)
- 4 fixture files with realistic responses
- CORS enabled for localhost:8000
- Intent-based routing (PRODUCT_SUMMARY → example3)

**Endpoints**:
- `GET /health` — ✅ Working
- `POST /compare` — ✅ Working (fixture-based)

**Action**: REUSE FOR DEMO. No backend changes needed for static demo.

### 2.4 ✅ Demo Scenarios (DEFINED)

**Status**: 4 EXAMPLES READY

**Evidence**:
- `CHAT_UX_SCENARIOS.md` — Scenario definitions
- `fixtures/` — 4 realistic response JSONs

**Examples**:
1. **Premium comparison** (4 insurers) — ⚠️ Premium notice banner
2. **Coverage condition diff** (2 insurers, 5 conditions) — Detailed comparison table
3. **Product summary** (2 insurers, 9 coverages) ⭐ RECOMMENDED DEFAULT
4. **Coverage availability** (2 insurers, O/X boolean) — Simple yes/no

**Action**: USE EXAMPLE 3 as default demo. Add context-specific intro text.

### 2.5 ✅ API Contract (DB-AGNOSTIC)

**Status**: LOCKED, INDEPENDENT OF DB

**Evidence**:
- `STEP_NEXT_9_API_CONTRACT.md` — Request/Response schemas
- Contract enforces: `insurers`, `products`, `target_coverages` (canonical codes)

**Key Point**: API contract does NOT require specific DB schema.
- Frontend sends: insurer names + coverage codes
- Backend returns: View Model 5 blocks
- How backend fetches data (DB/file/hardcoded) is opaque to frontend

**Action**: Frontend can use mock API OR real API with identical interface.

---

## 3. Gaps to Reach Customer Demo

### 3.1 ❌ DB-Based API Connection (NOT DONE)

**Current State**:
- Mock API: ✅ Works with fixtures
- Real API (`apps/api/server.py`): ⚠️ Exists but needs DB queries

**Gap**:
- Real API `/compare` endpoint needs to:
  1. Query `coverage_standard`, `coverage_instance`, `evidence_ref`, `amount_fact` tables
  2. Join by `coverage_code` (canonical)
  3. Build Response View Model from DB rows

**Why Not Critical for Demo**:
- Mock API already provides realistic responses
- Demo can use fixtures OR switch to real API without UI changes

**Recommendation**: ⏸️ DEFER real API implementation to post-demo. Use mock API for demo.

### 3.2 ❌ Fixed Demo Data (NOT LOCKED)

**Current State**:
- 4 example fixtures exist
- Data is realistic but may not match latest DB state

**Gap**:
- Fixtures may be outdated (created before STEP NEXT-35 A4999 deprecation)
- Coverage codes in fixtures (A4200_1, A4210, etc.) may need verification
- Evidence sources may not match current SSOT files

**Action Required**:
1. Verify fixture coverage codes match latest `*_coverage_cards.jsonl`
2. Update fixture evidence references to real file paths
3. Lock fixture versions for demo (snapshot as of 2025-12-31)

**Recommendation**: ✅ MINIMAL UPDATE. Verify example3 fixture only (default demo).

### 3.3 ❌ Demo Scenario Narrative (NOT WRITTEN)

**Current State**:
- UI exists, data exists, but NO demo script

**Gap**:
- No written scenario: "User asks X, system shows Y, presenter explains Z"
- No talking points for each example
- No failure scenario handling ("What if evidence not found?")

**Action Required**:
- Write 3 demo scenarios (1-2 pages each):
  1. **Example 3 (Product Summary)** — Default demo flow
  2. **Example 2 (Coverage Diff)** — Deep dive into conditions
  3. **Example 4 (O/X)** — Simple yes/no question

**Recommendation**: ✅ REQUIRED. Create `docs/demo/DEMO_SCRIPT_SCENARIOS.md`.

### 3.4 ⚠️ UI Polish (OPTIONAL)

**Current State**:
- Prototype is functional but minimal styling
- No loading states, error handling UI, or animations

**Gaps (Non-Critical)**:
- Loading spinner while API call pending
- Error banner if API fails
- Smooth scroll to response
- Keyboard shortcuts (Enter to submit)

**Action**: ⏸️ DEFER unless demo requires polish. Prototype is demo-ready as-is.

### 3.5 ⚠️ Evidence Modal Real Data (OPTIONAL)

**Current State**:
- Modal shows placeholder snippet text

**Gap**:
- No real evidence text from `data/evidence_text/{insurer}/약관/*.jsonl`
- No PDF page number link

**Action**: ⏸️ DEFER. Placeholder is acceptable for demo ("Future: click to see PDF").

---

## 4. Reuse Plan

### 4.1 Files to Use AS-IS (NO CHANGES)

| File | Purpose | Evidence Status |
|------|---------|-----------------|
| `docs/ui/STEP_NEXT_2_RESPONSE_VIEW_MODEL_AND_UX.md` | Output schema | ✅ LOCKED (constitutional) |
| `docs/api/STEP_NEXT_9_API_CONTRACT.md` | API contract | ✅ LOCKED |
| `apps/web-prototype/index.html` | UI prototype | ✅ WORKING (850 lines) |
| `apps/mock-api/server.py` | Mock API | ✅ WORKING |
| `apps/mock-api/fixtures/example3_product_summary.json` | Default demo data | ⚠️ VERIFY ONLY |

**Action**: Copy-paste ready. Zero code changes needed.

### 4.2 Files to Verify/Update (MINIMAL CHANGES)

| File | Required Update | Estimated Effort |
|------|----------------|------------------|
| `apps/mock-api/fixtures/example3_product_summary.json` | Verify coverage codes match DB | 15 min |
| `apps/mock-api/fixtures/example2_coverage_compare.json` | Verify coverage codes | 10 min |
| `apps/mock-api/fixtures/example4_ox.json` | Verify coverage codes | 10 min |
| `apps/web-prototype/index.html` (line 450-460) | Update example button text to match demo script | 5 min |

**Total Effort**: ~40 minutes

**Action**: Verification only, no redesign.

### 4.3 Files to Create (NEW, REQUIRED)

| File | Purpose | Estimated Lines | Effort |
|------|---------|-----------------|--------|
| `docs/demo/DEMO_SCRIPT_SCENARIOS.md` | Demo talking points (3 scenarios) | ~300 | 2-3 hours |
| `docs/demo/DEMO_SETUP_CHECKLIST.md` | Pre-demo setup steps | ~100 | 30 min |
| `docs/demo/DEMO_FAQ.md` | Expected Q&A during demo | ~200 | 1 hour |

**Total Effort**: ~4 hours (documentation only, no code)

**Action**: ✅ REQUIRED for demo. No UI/API changes.

### 4.4 Files to Defer (NOT NEEDED FOR DEMO)

| File | Reason to Defer |
|------|-----------------|
| Real API DB integration | Mock API sufficient for demo |
| Evidence modal real snippets | Placeholder acceptable |
| Loading/error states | Not critical for controlled demo |
| Keyboard shortcuts | Nice-to-have |
| Mobile optimization | Demo likely on desktop |

**Action**: ⏸️ DEFER to post-demo polish phase.

---

## 5. Non-Impact Guarantee

### 5.1 Other Insurers (100% Isolated)

**Analysis**:
- Demo uses fixtures (NOT live DB queries)
- Fixture data hardcoded for Samsung, Hanwha, DB, Meritz
- No pipeline runs triggered by demo

**Guarantee**:
- ✅ Zero impact on pipeline data
- ✅ Zero impact on SSOT files (`*_coverage_cards.jsonl`)
- ✅ Zero impact on other insurers (KB, Lotte, Heungkuk, Hyundai)

**Verification**:
```bash
# Demo only touches these files:
apps/web-prototype/index.html        # Static HTML
apps/mock-api/server.py              # Fixture router
apps/mock-api/fixtures/*.json        # Hardcoded responses

# Demo does NOT touch:
data/**                               # ✅ No data changes
pipeline/**                           # ✅ No pipeline runs
apps/api/server.py                    # ⏸️ May use but read-only
```

### 5.2 Existing Work (Preservation)

**Analysis**:
- All existing documentation remains valid
- Prototype extends existing `index.html` (additive changes only)
- Mock API adds scenarios, no breaking changes

**Guarantee**:
- ✅ `STEP_NEXT_2` View Model: Unchanged
- ✅ `STEP_NEXT_9` API Contract: Unchanged
- ✅ Existing fixtures: Preserved (add new, don't modify)
- ✅ Git history: No force-push, all changes in new branch

### 5.3 Meritz-Specific Issues (Separation)

**Analysis**:
- Meritz `A4999_*` deprecation (STEP NEXT-35/36/37) is pipeline-level
- Demo uses fixtures OR DB queries
- Demo does NOT trigger canonical code changes

**Guarantee**:
- ✅ Demo can show Meritz data without affecting A4999 deprecation plan
- ✅ If demo uses mock API: Meritz data is fixture-based (frozen state)
- ✅ If demo uses real API: Read-only queries (no updates to mapping Excel)

**Caveat**:
- If demo uses real API + Meritz data:
  - Coverage cards may show `A4999_1` (pre-migration)
  - This is acceptable (demo shows "as-is" state)
  - Presenter notes: "This code will be migrated to A4303_1 per deprecation plan"

---

## 6. Next Step Recommendation

### 6.1 Decision Matrix

| Option | Approach | Effort | Risk | Recommended |
|--------|----------|--------|------|-------------|
| **A: Extend Existing Prototype** | Update fixtures + write demo script | 4 hours | ✅ LOW | ✅ **RECOMMENDED** |
| **B: Build New Demo from Scratch** | New HTML/JS/API | 40+ hours | ❌ HIGH | ❌ NO |
| **C: Use Mock API Only** | No DB connection, pure fixtures | 2 hours | ✅ LOW | ⚠️ FALLBACK |

### 6.2 Final Recommendation

**✅ EXTEND EXISTING (Option A)**

**Rationale**:
1. 850-line prototype already works (`apps/web-prototype/index.html`)
2. Mock API provides 4 realistic examples
3. Only gaps: demo script + fixture verification (~4 hours total)
4. Zero risk to pipeline/data (fixture-based)
5. Reuses constitutional docs (STEP_NEXT_2, STEP_NEXT_9)

**Implementation Path**:
```
STEP NEXT-38-E:
├─ Task 1: Verify fixtures (40 min)
│  └─ Update coverage codes if needed
├─ Task 2: Write demo script (3 hours)
│  ├─ Scenario 1: Product Summary (example3) — Default
│  ├─ Scenario 2: Coverage Diff (example2) — Deep dive
│  └─ Scenario 3: O/X Availability (example4) — Simple Q&A
├─ Task 3: Setup checklist (30 min)
│  └─ Pre-demo environment checks
└─ Task 4: FAQ document (1 hour)
   └─ Expected customer questions

Total: ~4.5 hours (documentation only, ZERO code changes)
```

**What to Avoid**:
- ❌ Redesigning Response View Model (already locked)
- ❌ Rebuilding UI components (prototype works)
- ❌ Implementing real API DB queries (defer to post-demo)
- ❌ Polishing UI (not critical for demo)

**Deliverables** (STEP NEXT-38-E):
1. `docs/demo/DEMO_SCRIPT_SCENARIOS.md` — 3 scenarios with talking points
2. `docs/demo/DEMO_SETUP_CHECKLIST.md` — Pre-demo setup steps
3. `docs/demo/DEMO_FAQ.md` — Expected Q&A
4. `apps/mock-api/fixtures/*.json` — Verified (coverage codes match DB)
5. `apps/web-prototype/index.html` — Minor text updates (example button labels)

**Success Criteria**:
- [ ] Demo runs on `http://localhost:8000` (web-prototype)
- [ ] Mock API runs on `http://localhost:8001`
- [ ] Example 3 (Product Summary) loads without errors
- [ ] Demo script covers 3 scenarios (10-15 min presentation)
- [ ] No data files committed (fixtures are config, not data)

---

## 7. Evidence Summary (Commit References)

| Asset | Commit | Date | Status |
|-------|--------|------|--------|
| Response View Model schema | 9e7df7b | 2025-12-28 | ✅ LOCKED |
| UI Skeleton mapping | 9e7df7b | 2025-12-28 | ✅ LOCKED |
| UI Prototype (850 lines) | b8d33e7 | 2025-12-28 | ✅ WORKING |
| Mock API + fixtures | 8dc8616 | 2025-12-28 | ✅ WORKING |
| API Contract (FINAL) | 8dc8616 | 2025-12-28 | ✅ LOCKED |
| ChatGPT-style integration | 86e412a | 2025-12-28 | ✅ COMPLETE |
| Customer demo pack | e426ef7 | 2025-12-28 | ✅ REFERENCE |

**All evidence verified via git log and file contents (no speculation).**

---

## 8. Action Items (STEP NEXT-38-E)

**Priority 1 (REQUIRED for demo)**:
- [ ] Verify `example3_product_summary.json` coverage codes match latest DB
- [ ] Write `docs/demo/DEMO_SCRIPT_SCENARIOS.md` (3 scenarios, 300 lines)
- [ ] Write `docs/demo/DEMO_SETUP_CHECKLIST.md` (setup steps, 100 lines)

**Priority 2 (RECOMMENDED)**:
- [ ] Write `docs/demo/DEMO_FAQ.md` (Q&A, 200 lines)
- [ ] Update example button text in `index.html` (5 min)

**Priority 3 (OPTIONAL)**:
- [ ] Verify `example2_coverage_compare.json` (coverage codes)
- [ ] Verify `example4_ox.json` (coverage codes)
- [ ] Add loading spinner to `index.html` (if time permits)

**NOT REQUIRED (DEFER)**:
- ~~Real API DB integration~~
- ~~Evidence modal real snippets~~
- ~~Error handling UI~~
- ~~Mobile optimization~~

---

**END OF AUDIT**

**Conclusion**: STEP NEXT-38-E should EXTEND existing prototype (Option A), NOT build from scratch. Total effort: ~4.5 hours (documentation only). Zero code risk, zero data impact.
