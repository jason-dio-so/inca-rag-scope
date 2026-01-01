# STEP NEXT-61B — Meritz 단일 보험사 실행 로그

## 1. 실행 범위
- **보험사**: Meritz (단일)
- **단계**: Step3 (PDF text extraction) → Step4 (Evidence search) → Step5 (Coverage cards)
- **헌법**: Step1/Step2/Excel 수정 금지, SSOT 입력(`data/scope_v3/`) 강제, GATE 검증 필수

---

## 2. 실행 명령 및 로그

### Step3 — PDF Text Extraction
```bash
python -m pipeline.step3_extract_text.extract_pdf_text --insurer meritz
```
**로그**: `docs/audit/STEP_NEXT_61B_MERITZ_STEP3.log`

**GATE-3-1 결과**:
```
✓ GATE-3-1 passed: 1875 pages extracted (약관)
✓ GATE-3-1 passed: 452 pages extracted (사업방법서)
✓ GATE-3-1 passed: 167 pages extracted (상품요약서)
```

### Step4 — Evidence Search
```bash
python -m pipeline.step4_evidence_search.search_evidence --insurer meritz
```
**로그**: `docs/audit/STEP_NEXT_61B_MERITZ_STEP4.log`

**SSOT 입력 증명**:
```
[Step 4] Input SSOT: /Users/cheollee/inca-rag-scope/data/scope_v3/meritz_step2_canonical_scope_v1.jsonl
```

**결과**:
- Total coverages: 29
- Matched: 20
- Unmatched: 9

### Step5 — Coverage Cards Build
```bash
python -m pipeline.step5_build_cards.build_cards --insurer meritz
```
**로그**: `docs/audit/STEP_NEXT_61B_MERITZ_STEP5.log`

**GATE-5-2 결과**:
```
Join rate: 100.00%
✓ GATE-5-2 passed: Join rate 100.00% ≥ 95%
✓ GATE-5-1 passed: Coverage count matches (29)
```

---

## 3. 산출물 검증

### 3-1. 생성된 파일
| 파일 경로 | 라인수 | mtime |
|----------|--------|-------|
| `data/scope_v3/meritz_step4_unmatched_review.jsonl` | 9 | 2026-01-01 15:53 |
| `data/compare/meritz_coverage_cards.jsonl` | 29 | 2026-01-01 15:53 |
| `data/evidence_pack/meritz_evidence_pack.jsonl` | 30 | 2026-01-01 15:53 |

### 3-2. 재사용 방지 증명
**coverage_cards SHA256**:
```
3e900a00897ca1ed408352584de70f3e98b727131a2b37a88462f89d7a157e35  data/compare/meritz_coverage_cards.jsonl
```

---

## 4. DoD (Definition of Done)

### ✅ PASS 조건 달성
- [x] Step3 GATE-3-1 PASS (1875+452+167 pages)
- [x] Step4 SSOT 입력 확인 (`data/scope_v3/meritz_step2_canonical_scope_v1.jsonl`)
- [x] Step5 GATE-5-2 PASS (join rate 100% ≥ 95%)
- [x] 산출물 신규 생성 증명 (mtime: 2026-01-01 15:53)
- [x] Step1/Step2/Excel 변경 없음

### ❌ FAIL 조건 — 없음
- Step4가 legacy 경로(`data/scope/`) 읽지 않음 확인
- GATE 무력화 없음 확인

---

## 5. 결론
**Meritz 단일 보험사 실행 성공**

모든 GATE 통과, SSOT 준수, 산출물 신규 생성 확인.
다음 보험사(Hanwha/Heungkuk)는 새 STEP에서 실행.
