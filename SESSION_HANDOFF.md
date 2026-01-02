# SESSION HANDOFF — Insurance Compare RAG

## Current Status (2026-01-02)

### ✅ Completed
- Slim coverage cards (STEP NEXT-72)
- Store separation (DETAIL / EVIDENCE)
- Lazy loading UI (STEP NEXT-73R)
- KPI Summary: 지급유형 / 한도 (STEP NEXT-74)
- KPI Condition: 면책 / 대기 / 감액 / 갱신 (STEP NEXT-76)
- All insurers KPI-1B = 100%

### 🔑 SSOT
- coverage_cards_slim.jsonl
- proposal_detail_store.jsonl
- evidence_store.jsonl

### ❌ Deprecated
- full coverage_cards.jsonl
- DB-centric /chat logic
- Vector-based extraction

---

## Known Pitfalls
- If UI shows old data → server cache reload needed
- If Claude mentions DB/full cards → baseline not applied
- “명시 없음” ≠ 실패 (can be structural)

---

## What To Do Next (Priority Order)

1. UI 시나리오별 판단 문장 정리
   - 예: “A사는 지급유형이 다릅니다”
2. 상품 추천 로직 설계 (비교 결과 기반)
3. 고객 데모 시나리오 고정 (Example 1~4)

---

## One-Line Reminder
Slim + Store + KPI is the only truth.

Current Status
	•	Step1: FIXED & LOCKED
	•	Step2: FIXED & LOCKED
	•	STEP NEXT-60-H 완료 (Hyundai fragment 정리)

Next Step
	•	STEP NEXT-61: Step3~7 비교 모델 재정의

Non-Goals
	•	Excel 수정 (고객 결정)
	•	Step1 재작업

Key Reminder

“의심되면 멈추고, 구조부터 문서로 고정한다.”