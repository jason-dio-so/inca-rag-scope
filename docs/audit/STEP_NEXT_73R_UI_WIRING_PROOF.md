# STEP NEXT-73R: Slim(Store) Lazy Loading UI 완전 연결 (Part 1: Backend Wiring)

**Date**: 2026-01-02
**Status**: ✅ PART 1 COMPLETED (Backend + API Client)

---

## 📌 목표

Step72의 Slim cards + Store 분리 저장소를 기존 ChatGPT-style Next.js UI에 완전 연결:
- `/chat` 응답은 Slim + refs(row.meta) 만 전달
- UI에서 "보장내용 보기 / 근거 보기" 클릭 시 Store API로 Lazy Load

---

## ✅ Part 1 구현 완료 (Backend + API Client)

### 1. Store Loader (In-Memory Cache)

**파일**: `apps/api/store_loader.py`

**기능**:
- `data/detail/*_proposal_detail_store.jsonl` 로딩
- `data/detail/*_evidence_store.jsonl` 로딩
- In-memory dict 캐싱:
  - `proposal_detail_ref -> record`
  - `evidence_ref -> record`

**함수**:
- `init_store_cache()`: 서버 시작 시 1회 로딩
- `get_proposal_detail(ref)`: 단건 조회
- `get_evidence(ref)`: 단건 조회
- `batch_get_evidence(refs)`: 배치 조회

**테스트 결과** (Samsung):
```
[STEP NEXT-73R] Store cache initialized:
  - Proposal details: 18 records
  - Evidence: 60 records

✓ Proposal detail found: PD:samsung:A4101
  Text preview: 보험기간 중 약관에 정한 뇌혈관질환(뇌졸중포함)으로 진단 확정된 경우 가...

✓ Evidence found: EV:samsung:A4101:01
  Snippet preview: 20년납 100세만기\nZD2779010\n뇌혈관질환 진단비(1년50%)\n1,000만원...
```

---

### 2. Store API Endpoints

**파일**: `apps/api/chat_server.py`

**엔드포인트**:
1. `GET /store/proposal-detail/{ref}`
   - 예: `GET /store/proposal-detail/PD:samsung:A4200_1`
   - 응답: `{proposal_detail_ref, insurer, coverage_code, doc_type, page, benefit_description_text, hash}`
   - 404: `{error: "Proposal detail not found", ref: ...}`

2. `GET /store/evidence/{ref}`
   - 예: `GET /store/evidence/EV:samsung:A4200_1:01`
   - 응답: `{evidence_ref, insurer, coverage_code, doc_type, page, snippet, match_keyword, hash}`
   - 404: `{error: "Evidence not found", ref: ...}`

3. `POST /store/evidence/batch`
   - Body: `{"refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"]}`
   - 응답: `{"EV:samsung:A4200_1:01": {...}, "EV:samsung:A4200_1:02": {...}}`

**Startup Event**:
```python
@app.on_event("startup")
def startup_event():
    """Load store cache into memory"""
    init_store_cache()
```

---

### 3. /chat 응답에 row.meta refs 추가

**파일**: `apps/api/chat_vm.py`

**TableRowMeta 추가**:
```python
class TableRowMeta(BaseModel):
    """STEP NEXT-73R: Row-level metadata for refs"""
    proposal_detail_ref: Optional[str] = None
    evidence_refs: Optional[List[str]] = None

class TableRow(BaseModel):
    """Table row (header or data)"""
    cells: List[TableCell]
    is_header: bool = False
    meta: Optional[TableRowMeta] = None  # STEP NEXT-73R
```

**파일**: `pipeline/step8_render_deterministic/example3_two_insurer_compare.py`

**TwoInsurerComparer 수정**:
- Slim cards 우선 로딩 (`use_slim=True` 기본)
- `comparison_table`에 `proposal_detail_ref`, `evidence_refs` 추가

**파일**: `apps/api/chat_handlers_deterministic.py`

**Example3HandlerDeterministic 수정**:
```python
TableRow(
    cells=[
        TableCell(text="보장금액"),
        TableCell(text=comparison_table[insurer1]["amount"]),
        TableCell(text=comparison_table[insurer2]["amount"])
    ],
    meta=TableRowMeta(
        proposal_detail_ref=comparison_table[insurer1].get("proposal_detail_ref"),
        evidence_refs=comparison_table[insurer1].get("evidence_refs", [])
    )
)
```

---

### 4. Frontend Types 확장

**파일**: `apps/web/lib/types.ts`

**TableRowMeta 추가**:
```typescript
// STEP NEXT-73R: Row-level metadata for refs
export interface TableRowMeta {
  proposal_detail_ref?: string;
  evidence_refs?: string[];
}

export interface TableRow {
  label?: string;       // Legacy
  values?: TableCell[]; // Legacy
  cells?: TableCell[];  // STEP NEXT-73R: Backend uses 'cells'
  is_header?: boolean;
  meta?: TableRowMeta;  // STEP NEXT-73R
}
```

**Store API 타입 추가**:
```typescript
export interface ProposalDetailStoreItem {
  proposal_detail_ref: string;
  insurer: string;
  coverage_code: string;
  doc_type: string;
  page: number;
  benefit_description_text: string;
  hash: string;
}

export interface EvidenceStoreItem {
  evidence_ref: string;
  insurer: string;
  coverage_code: string;
  doc_type: string;
  page: number;
  snippet: string;
  match_keyword: string;
  hash: string;
}
```

---

### 5. Frontend Store API Client

**파일**: `apps/web/lib/api.ts`

**함수 추가**:
```typescript
// STEP NEXT-73R: Store API functions

export async function getProposalDetail(ref: string): Promise<ProposalDetailStoreItem | null>
export async function getEvidence(ref: string): Promise<EvidenceStoreItem | null>
export async function batchGetEvidence(refs: string[]): Promise<Record<string, EvidenceStoreItem>>
```

**에러 처리**:
- 404 → `null` 반환
- 네트워크 오류 → `console.error` + 빈 객체/null 반환 (크래시 방지)

---

## 📋 구현 완료 항목 (Part 1)

✅ **Backend**:
- Store Loader (`store_loader.py`) - 18 proposal details, 60 evidences 로딩 확인
- Store API endpoints (`chat_server.py`) - 3개 엔드포인트
- `/chat` 응답에 `row.meta` refs 추가
- `TwoInsurerComparer` Slim cards 지원

✅ **Frontend**:
- `types.ts` 확장 (TableRowMeta, Store types)
- `api.ts` Store client 함수 (getProposalDetail, getEvidence, batchGetEvidence)

---

## 🚧 Part 2 남은 작업 (UI Components)

### 1. EvidenceToggle 업그레이드
- `evidenceRefs?: string[]` prop 추가
- 펼칠 때 `batchGetEvidence(evidenceRefs)` 호출
- 로딩/에러/빈값 방어

### 2. TwoInsurerCompareCard "보장내용 보기" 버튼
- `row.meta.proposal_detail_ref` 있으면 버튼 표시
- 클릭 → `getProposalDetail(ref)` 호출
- Modal/Accordion으로 `benefit_description_text` 표시
- 간단한 캐시 (useState Map)

### 3. 통합 테스트
- 삼성 A4200_1 비교 화면
- 버튼 클릭 → 원문 표시 확인
- ref 없음 → 버튼 비활성/안전 처리

---

## 📊 검증 결과 (Part 1)

### Store Loader 테스트
```bash
$ python3 -c "..."
[STEP NEXT-73R] Store cache initialized:
  - Proposal details: 18 records
  - Evidence: 60 records

✓ Proposal detail found: PD:samsung:A4101
✓ Evidence found: EV:samsung:A4101:01
```

### API Endpoints (예상 동작)
```bash
# GET /store/proposal-detail/PD:samsung:A4200_1
{
  "proposal_detail_ref": "PD:samsung:A4200_1",
  "insurer": "samsung",
  "coverage_code": "A4200_1",
  "doc_type": "가입설계서",
  "page": 6,
  "benefit_description_text": "암으로 진단 확정 시 보험가입금액 지급...",
  "hash": "..."
}

# POST /store/evidence/batch
{
  "EV:samsung:A4200_1:01": {...},
  "EV:samsung:A4200_1:02": {...}
}
```

### /chat 응답 (row.meta refs 포함)
```json
{
  "sections": [
    {
      "kind": "comparison_table",
      "rows": [
        {
          "cells": [
            {"text": "보장금액"},
            {"text": "3,000만원"},
            {"text": "2,000만원"}
          ],
          "meta": {
            "proposal_detail_ref": "PD:samsung:A4200_1",
            "evidence_refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"]
          }
        }
      ]
    }
  ]
}
```

---

## 🔧 준수 사항 (Constitution)

✅ **준수 완료**:
- ❌ LLM/OCR/Vector 사용 금지 → 모두 deterministic fetch/cache
- ❌ Step1/Step2 재실행 금지 → 기존 outputs 그대로 사용
- ✅ Step72 산출물만 사용 → Slim cards + stores
- ✅ UI는 서버 값 그대로 표시 → 추론/추천/요약 생성 0

---

## 📂 파일 위치

### Backend
- `apps/api/store_loader.py` (NEW)
- `apps/api/chat_server.py` (수정: store endpoints + init)
- `apps/api/chat_vm.py` (수정: TableRowMeta)
- `apps/api/chat_handlers_deterministic.py` (수정: row.meta refs)
- `pipeline/step8_render_deterministic/example3_two_insurer_compare.py` (수정: Slim + refs)

### Frontend
- `apps/web/lib/types.ts` (수정: TableRowMeta, Store types)
- `apps/web/lib/api.ts` (수정: Store client 함수)

---

## 🎯 Part 1 성공 기준 (Exit)

✅ **Store cache 로딩 성공** (18 proposal details, 60 evidences)
✅ **Store API 3개 엔드포인트 구현** (단건/배치/404)
✅ **/chat 응답에 row.meta.refs 포함** (comparison_table)
✅ **Frontend Store API client 함수 준비** (getProposalDetail, getEvidence, batchGetEvidence)

---

## 📋 다음 단계 (Part 2)

**STEP NEXT-73R-P2: UI Component Integration**
1. EvidenceToggle refs 기반 lazy load
2. TwoInsurerCompareCard "보장내용 보기" 버튼 + modal
3. 삼성 A4200_1 통합 테스트
4. 전체 커밋 + STATUS 업데이트

**실행 명령** (Part 2):
```bash
# Backend 서버 시작
python apps/api/chat_server.py

# Frontend 서버 시작
cd apps/web && npm run dev

# 브라우저: http://localhost:3000
# 테스트: "삼성과 메리츠의 암진단비 비교해줘"
```

---

**실행일**: 2026-01-02
**담당**: Claude Code (STEP NEXT-73R)
**Status**: ✅ PART 1 COMPLETED
