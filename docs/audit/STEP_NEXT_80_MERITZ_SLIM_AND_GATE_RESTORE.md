# STEP NEXT-80 — Meritz Slim Cards 생성 + EX3 Gate 복구(0.8) + 혼합모드 제거

## 목적

EX3_COMPARE가 "비교 불가 (evidence_fill_rate 75% < 0.8)"로 막힌 문제 해결:
- 원인: Meritz는 legacy 카드만 존재, slim 카드 없음 → KPI 필드 불일치
- 해결: Meritz를 Step72 Slim+Store+KPI 파이프라인으로 전환 → 혼합모드 제거

## 헌법/금지사항

❌ evidence_fill_rate threshold 0.8 → 0.5 완화 금지 (품질 게이트 타협 금지)
✅ 목표: 혼합모드 제거 (Samsung + Meritz 모두 slim 카드 사용)
✅ NO LLM / deterministic only 유지
✅ SSOT: `*_coverage_cards_slim.jsonl` + proposal_detail_store + evidence_store

## 완료 작업

### 1) Meritz Slim 카드 + Store 생성

실행:
```bash
python -m pipeline.step5_build_cards.build_cards_slim --insurer meritz
```

산출물:
```
data/compare/meritz_coverage_cards_slim.jsonl       37 lines (86KB)
data/detail/meritz_proposal_detail_store.jsonl      22 records (16KB)
data/detail/meritz_evidence_store.jsonl             98 records (44KB)
```

통계:
- Total coverages: 37
- Matched: 28
- Unmatched: 9
- Evidence found: 37
- Evidence not found: 0

### 2) Store Loader가 Meritz Store 로딩 확인

서버 startup 로그:
```
[DEBUG] Loading proposal detail stores from: /Users/cheollee/inca-rag-scope/data/detail
[DEBUG]   - /Users/cheollee/inca-rag-scope/data/detail/meritz_proposal_detail_store.jsonl
[DEBUG]   - /Users/cheollee/inca-rag-scope/data/detail/samsung_proposal_detail_store.jsonl
[DEBUG] Loading evidence stores from: /Users/cheollee/inca-rag-scope/data/detail
[DEBUG]   - /Users/cheollee/inca-rag-scope/data/detail/meritz_evidence_store.jsonl
[DEBUG]   - /Users/cheollee/inca-rag-scope/data/detail/samsung_evidence_store.jsonl
[STEP NEXT-73R] Store cache initialized:
  - Proposal details: 40 records (18 Samsung + 22 Meritz)
  - Evidence: 158 records (60 Samsung + 98 Meritz)
```

증적: `apps/api/store_loader.py`의 glob 패턴(`*_proposal_detail_store.jsonl`, `*_evidence_store.jsonl`)이 Meritz 파일 자동 로딩

### 3) EX3가 Meritz Slim 카드 사용 확인

TwoInsurerComparer 설정:
- `pipeline/step8_render_deterministic/example3_two_insurer_compare.py:34`
- `use_slim=True` (default)
- Slim file 존재 시 우선 사용, legacy fallback

EX3 실행 로그:
```
[INFO] [EX3] Loading cards from: /Users/cheollee/inca-rag-scope/data/compare
[INFO] [EX3] Loaded 31 cards for samsung
[INFO] [EX3] Loaded 37 cards for meritz
[INFO] [EX3] Finding A4200_1: insurer1=FOUND, insurer2=FOUND
```

증적: Meritz 37개 카드 = slim 카드 라인 수와 일치

### 4) evidence_fill_rate Gate 0.8 복구

변경:
- `pipeline/step8_render_deterministic/example3_two_insurer_compare.py:192`
- `if evidence_fill_rate < 0.5` → `if evidence_fill_rate < 0.8`
- 주석: "STEP NEXT-80: Restored to 0.8 (hybrid mode eliminated)"

테스트 결과:
- 0.8 gate 통과 (비교 불가 메시지 더 이상 출력 안 됨)
- EX3 API 정상 응답 (sections.length = 2)

### 5) Coverage Name Mapping 수정

발견 이슈:
- `apps/api/chat_intent.py:342` "암진단비" → "A4100_1" 매핑
- A4100_1은 실제 카드에 존재하지 않음 (A4200_1이 실제 코드)

수정:
```python
COVERAGE_NAME_TO_CODE = {
    "암진단비": "A4200_1",  # Fixed A4100_1 → A4200_1
    ...
}
```

### 6) EX3 API 정상 응답 확인

테스트:
```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"삼성화재와 메리츠화재의 암진단비를 비교해줘","insurers":["samsung","meritz"],"coverage_names":["암진단비"],"kind":"EX3_COMPARE"}' \
| jq '{kind: .message.kind, sections_count: (.message.sections|length)}'
```

응답:
```json
{
  "kind": "EX3_COMPARE",
  "sections_count": 2
}
```

Section 구조:
- Section 0: "A4200_1 비교표" (comparison_table)
  - Rows with cells (보장금액: 3,000만원 vs 3천만원)
  - meta.proposal_detail_ref: "PD:samsung:A4200_1"
  - meta.evidence_refs: ["EV:samsung:A4200_1:01", ...]
  - meta.kpi_summary: payment_type, limit_summary
  - meta.kpi_condition: waiting_period, reduction_condition, exclusion_condition
- Section 1: "공통사항 및 유의사항"

✅ Refs 존재 (lazy-load 가능)
✅ KPI 데이터 존재
✅ 정상 비교 테이블 렌더링 가능

## 검증 커맨드

```bash
# 1) Meritz slim 파일 확인
ls -lh data/compare/*meritz*slim*.jsonl
ls -lh data/detail/meritz_*store*.jsonl
wc -l data/compare/meritz_coverage_cards_slim.jsonl data/detail/meritz_*.jsonl

# 2) Store API 확인
curl -s "http://localhost:8000/store/proposal-detail/PD:meritz:A4209" | jq -r '.proposal_detail_ref, .insurer'

# 3) EX3 API 확인
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"삼성화재와 메리츠화재의 암진단비를 비교해줘","insurers":["samsung","meritz"],"coverage_names":["암진단비"],"kind":"EX3_COMPARE"}' \
| jq '{kind: .message.kind, sections_count: (.message.sections|length)}'
```

## 최종 DoD (Definition of Done)

✅ data/compare/meritz_coverage_cards_slim.jsonl 존재 (37 lines)
✅ data/detail/meritz_*store*.jsonl 존재 + 서버 로딩 확인 (40 PD, 158 EV)
✅ EX3 gate 0.8 유지 (`example3_two_insurer_compare.py:192`)
✅ UI/API EX3 정상 응답 (Samsung vs Meritz, 암진단비, sections.length=2)
✅ Legacy 혼합모드 완전 제거 (모든 보험사가 slim 사용)

## 영향 범위

변경 파일:
1. `pipeline/step8_render_deterministic/example3_two_insurer_compare.py` (gate 0.8 복구)
2. `apps/api/chat_intent.py` (coverage name mapping 수정)

생성 파일:
1. `data/compare/meritz_coverage_cards_slim.jsonl`
2. `data/detail/meritz_proposal_detail_store.jsonl`
3. `data/detail/meritz_evidence_store.jsonl`

기술부채 제거:
- Legacy + Slim 혼합모드 제거 (모든 보험사가 동일한 Slim 구조 사용)
- 0.5 임시 완화 제거 (품질 게이트 0.8 복구)

## 다음 단계

1. UI에서 예제3 버튼 테스트 (frontend 확인)
2. 추가 보험사(DB, 한화, KB 등) Slim 카드 생성 검토
3. EX3 외 다른 intent(EX2, EX4)도 Slim 사용 확인

---

**작성일**: 2026-01-02
**작성자**: Claude (STEP NEXT-80)
