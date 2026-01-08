# STEP NEXT-75: Recommendation Output Lock & Explanation Schema

**Status:** ✅ COMPLETED
**Date:** 2026-01-08
**Constitutional Compliance:** ✅ HARD LOCK (No LLM, No inference, 100% evidence traceability)

---

## 🎯 Objective

Lock STEP NEXT-74's rule_executor results into **customer-facing "Recommendation Card" format** with:
- ✅ LLM prohibited
- ✅ Inference prohibited
- ✅ 100% evidence traceability
- ✅ Deterministic reproducibility

---

## 📦 Input/Output SSOT

### Input
- `data/recommend_v1/recommend_results.jsonl` (STEP NEXT-74 output)
- `data/compare_v1/compare_rows_v1.jsonl` (for slot/evidence enrichment)
- `rules/rule_catalog.yaml` (for rule metadata)

### Output (NEW)
- `data/recommend_v1/recommend_cards_v1.jsonl` (25 cards)
- `data/recommend_v1/recommend_cards_summary_v1.json` (summary statistics)
- `data/recommend_v1/recommend_cards_fingerprint.txt` (deterministic hash)

---

## 🔒 Recommendation Card Schema (LOCKED)

### Core Fields
- `card_id`: Stable hash(rule_id + 4D identity + coverage_code + coverage_name_normalized)
- `generated_at`: ISO8601 timestamp
- `rule_id`, `rule_title`: From rule catalog
- `rank`: 1..N within rule
- `subject`: Template-based summary (NO free text)
- `identity`: 4D coverage identity (insurer/product/variant/coverage_code/coverage_title)
- `metrics`: Calculated metrics from rule (e.g., waiting_days: 1.0)
- `explanations[]`: Deterministic bullet points (max 6 slots)
- `evidences[]`: Top K=2 representative evidences
- `gates`: Gate results (has_conflict, has_unknown, evidence_count, anchored)

### Explanation Bullet Schema
Each bullet contains:
- `label`: Korean label (e.g., "면책기간", "감액", "가입나이")
- `value`: Direct from `slots.*.value` (NO reinterpretation)
- `status`: FOUND | FOUND_GLOBAL | CONFLICT | UNKNOWN
- `evidence_refs[]`: Top K=2 evidences for this slot

---

## 📋 Output Rules (LOCKED)

### Subject Templates
Fixed templates only (NO free text generation):
- Default: `"[{rule_title}] {coverage_title} — {metric_key} {metric_value}"`
- Conflict: `"{base_subject} (문서 상충)"`

### Explanation Generation (Deterministic)
Slot priority order (FIXED):
1. `waiting_period` (면책기간)
2. `reduction` (감액)
3. `payout_limit` (지급한도)
4. `exclusions` (제외사항)
5. `entry_age` (가입나이)
6. `start_date` (보장개시일)

Rules:
- Each slot: status from `slots.<name>.status` (NO interpretation)
- Value: `slots.<name>.value` AS-IS (NO new generation)
- Evidences: Top K=2 sorted by doc_priority (가입설계서 > 요약서 > 사업방법서 > 약관) then page asc
- UNKNOWN slots: Skip from explanations

### CONFLICT Handling (Fixed Rules)
- `gates.has_conflict = true`
- `subject` gets `(문서 상충)` suffix
- CONFLICT slot included in explanations
- Both conflicting evidences included (minimum 1 each)

---

## 🚦 Gates (HARD)

### G1. Evidence Gate (exit 2)
- All cards: `evidences >= 1` ✅
- All explanation bullets: `evidence_refs >= 1` (except UNKNOWN) ✅
- UNKNOWN bullets: `value` must be empty ✅

### G2. No-Inference Gate (exit 2)
- Card `metrics` keys match `recommend_results.metric` keys ✅
- NO new field generation/inference ✅
- All values from input files ONLY ✅

### G3. Deterministic Gate (exit 1)
- Same input → same `card_id` set ✅
- Same input → same `subject`/`explanations`/`metrics` ✅
- Fingerprint verification: `recommend_cards_fingerprint.txt` ✅

### G4. Schema Completeness Gate (exit 2)
- No missing required fields ✅
- `rank` is 1..N consecutive per rule_id ✅
- Identity 3D (insurer/product/variant) NOT empty ✅
- `coverage_title` nullable (for unmapped coverages) ✅
- `anchored` flag matches `coverage_code` presence ✅

**Result:** ✅ ALL GATES PASSED

---

## 📊 Execution Results

### Card Generation
```
Total cards: 25
Cards by rule:
  - R-001 (면책기간 없는 암진단비): 5 cards
  - R-002 (가입금액이 높은 암진단비): 5 cards
  - R-003 (지급횟수 제한 없는 담보): 5 cards
  - R-004 (감액 없는 담보): 5 cards
  - R-005 (가입연령 범위가 넓은 담보): 5 cards

Conflict cards: 8
Unknown slots: 0
Anchored: 23
Unanchored: 2

Slot status distribution:
  - FOUND: 95
  - FOUND_GLOBAL: 46
  - CONFLICT: 9
  - UNKNOWN: 0
```

### DoD Verification
- ✅ All cards have `evidences >= 1`
- ✅ All cards have minimum 3 FOUND/FOUND_GLOBAL slots
- ✅ CONFLICT cards have `(문서 상충)` suffix
- ✅ Fingerprint stability verified

---

## 📝 Sample Card

```json
{
  "card_id": "b560f4c0fcebf8c8",
  "generated_at": "2026-01-08T07:15:31.373942+00:00",
  "rule_id": "R-001",
  "rule_title": "면책기간 없는 암진단비 추천",
  "rank": 1,
  "subject": "[면책기간 없는 암진단비 추천] 재진단암Ⅲ진단비 — waiting_days 1.0",
  "identity": {
    "insurer_key": "heungkuk",
    "product_key": "heungkuk__무배당흥Good행복한파워종합보험",
    "variant_key": "default",
    "coverage_code": "A4299_1",
    "coverage_title": "재진단암Ⅲ진단비"
  },
  "metrics": {
    "waiting_days": 1.0
  },
  "explanations": [
    {
      "label": "면책기간",
      "value": "1, 20, 15",
      "status": "FOUND",
      "evidence_refs": [...]
    },
    {
      "label": "감액",
      "value": "1, 9, 90",
      "status": "FOUND",
      "evidence_refs": [...]
    },
    ...
  ],
  "evidences": [...],
  "gates": {
    "has_conflict": false,
    "has_unknown": false,
    "evidence_count": 2,
    "anchored": true
  }
}
```

---

## 🔧 Implementation

### New Files
- `pipeline/step5_recommendation/card_model.py` (schema definitions)
- `pipeline/step5_recommendation/card_builder.py` (deterministic card builder)
- `pipeline/step5_recommendation/validate_cards_gates.py` (4 gates)
- `pipeline/step5_recommendation/run_cards.py` (CLI)

### CLI Usage
```bash
# Generate cards
python3 -m pipeline.step5_recommendation.run_cards

# Validate gates
python3 -m pipeline.step5_recommendation.validate_cards_gates data/recommend_v1/recommend_cards_v1.jsonl
```

---

## ❌ Prohibited Actions

- ❌ LLM calls
- ❌ Free text generation (subject must use templates)
- ❌ Slot value reinterpretation/correction/estimation
- ❌ Modifying Step1~Step4 logic (STEP NEXT-75 is Step5 output layer ONLY)

---

## ✅ Constitutional Compliance

- ✅ NO LLM inference
- ✅ NO value generation (all from recommend_results/compare_rows)
- ✅ 100% evidence traceability (all bullets have evidence_refs)
- ✅ Deterministic (fingerprint verified)
- ✅ All gates PASS (G1/G2/G3/G4)

---

## 🎯 Next Steps

Cards are ready for:
1. Frontend UI integration (customer-facing cards)
2. API endpoints (recommendation service)
3. Further filtering/ranking (if needed)

**STEP NEXT-75 COMPLETE** ✅
