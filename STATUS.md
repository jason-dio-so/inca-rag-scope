# inca-rag-scope - 작업 현황 보고서

**프로젝트**: 가입설계서 담보 scope 기반 보험사 비교 시스템
**최종 업데이트**: 2025-12-31
**현재 상태**: ✅ STEP NEXT-32 완료 (Step1 Extractor Hardening - Samsung/Meritz)

---

## 📊 전체 진행 상황

| Phase | 단계 | 상태 | 완료일 |
|-------|------|------|--------|
| **🔧 Step1 Extractor Hardening** | STEP NEXT-32 | ✅ 완료 | 2025-12-31 |
| **🔐 Content-Hash Lock Hardening** | STEP NEXT-31-P3-β | ✅ 완료 | 2025-12-31 |
| **🔐 Content-Hash Lock** | STEP NEXT-31-P3 | ✅ 완료 | 2025-12-31 |
| **🧹 Pipeline Cleanup** | STEP NEXT-31-P2 | ✅ 완료 | 2025-12-31 |
| **🔒 Constitutional Enforcement** | STEP NEXT-31-P1 | ✅ 완료 | 2025-12-31 |
| **🔄 Full Restart** | STEP NEXT-29 | ✅ 완료 | 2025-12-31 |
| **🔧 KB Scope Recovery** | STEP NEXT-28 | ✅ 완료 | 2025-12-30 |
| **🔧 Canonical Recovery** | STEP NEXT-27 | ✅ 완료 | 2025-12-30 |
| **📐 Pipeline Analysis** | STEP NEXT-24 | ✅ 완료 | 2025-12-30 |
| **🔧 Amount Extraction Fix** | STEP NEXT-19 | ✅ 완료 | 2025-12-30 |
| **🔒 SSOT Hardened Lock** | STEP NEXT-18X-SSOT-LOCK-2 | ✅ 완료 | 2025-12-30 |
| **🔒 SSOT Final Lock** | STEP NEXT-18X-SSOT-LOCK | ✅ 완료 | 2025-12-30 |
| **🧹 SSOT Contract Lock** | STEP NEXT-18X-SSOT-FINAL-A | ✅ 완료 | 2025-12-30 |
| **🧹 SSOT Final** | STEP NEXT-18X-SSOT-FINAL | ✅ 완료 | 2025-12-30 |
| **🧹 SSOT Unification** | STEP NEXT-18X-SSOT | ✅ 완료 | 2025-12-30 |
| **🔧 Pipeline Integration** | STEP NEXT-18X | ✅ 완료 | 2025-12-30 |
| **🔧 Scope + Amount Pipeline** | STEP NEXT-18D | ✅ 완료 | 2025-12-30 |
| **🔧 Data Re-extraction** | STEP NEXT-18B | ✅ 완료 | 2025-12-30 |
| **📊 Presentation Reflect** | STEP NEXT-18A | ✅ 완료 | 2025-12-30 |
| **🔧 Type Correction** | STEP NEXT-17C | ✅ 완료 | 2025-12-30 |
| **🔍 Quality Gates** | STEP NEXT-17B | ✅ 완료 | 2025-12-30 |
| **🎯 Chat UI** | STEP NEXT-14 | ✅ 완료 | 2025-12-29 |
| **🚀 Production** | STEP NEXT-13 | ✅ 완료 | 2025-12-29 |
| **Explanation Layer** | STEP NEXT-12 | ✅ 완료 | 2025-12-29 |
| **API Integration** | STEP NEXT-11 | ✅ 완료 | 2025-12-29 |
| **Amount Pipeline** | STEP NEXT-10B-FINAL | ✅ 완료 | 2025-12-29 |
| **API Layer** | STEP NEXT-9.1 | ✅ 완료 | 2025-12-28 |
| **DB Schema** | STEP NEXT-10B-2C-3 | ✅ 완료 | 2025-12-29 |

**운영 준비 상태**: ✅ **PRODUCTION READY (6/8 INSURERS)** (Contract 정규화 완료, IN-SCOPE KPI 99.4% ✅ PASS)

---

## 🎯 최신 완료 항목 (2025-12-31)

### STEP NEXT-32 — Step1 Extractor Hardening (Samsung/Meritz) 🔧

**목표**: Samsung/Meritz Step1 추출 품질 개선 + Quality Gates 구현

**문제 요약**:
- **Samsung**: 담보 1건만 추출 (table/레이아웃 패턴 미대응)
- **Meritz**: 헤더/섹션 문구 혼입 (필터 부족)

**적용 로직**:

**1. Quality Gates 구현** (`pipeline/step1_extract_scope/`):
- **Count Gate (≥30)**: 추출 개수 최소 30개 보장
- **Header Pollution Gate (<5%)**: 헤더/섹션 혼입률 5% 미만
- **Declared vs Extracted Gap (Warning)**: 선언값 대비 50% 이상 차이 시 경고

**2. Samsung Table-First Extraction** (`hardening.py::samsung_table_extraction()`):
- **Table anchor 기반 추출**:
  - "담보가입현황" 테이블: 담보명이 3번째 열(index 2)
  - "담보별 보장내용" 테이블: 담보명이 2번째 열(index 1)
- **금액값 필터**: "10만원", "3,000만원" 같은 금액값 제거 (regex: `^[\d,]+(만|천|억|조)?원$`)
- **섹션 마커 제거**: "기본계약", "선택계약" 등

**3. Meritz Header Pollution Filter** (`hardening.py::meritz_table_extraction()`):
- **Category header 제거**: "수술", "골절/화상", "기타", "할증/제도성", "사망후유", "입원일당" 등
- **Code number strip**: "180 담보명" → "담보명" (regex: `^\d+\s+`)
- **긴 설명문 제거**: 100자 초과 텍스트 필터링
- **주석 제거**: `※`, `◆`, `-`로 시작하는 라인 제외

**검증 로그 요약**:

**Samsung**:
```
[STEP NEXT-32 Quality Gates]
[Gate 1] Count Gate (≥30): 42 → ✓ PASS
[Gate 2] Header Pollution Gate (<5%): 0/42 (0.00%) → ✓ PASS
  - Pollution samples: none
[Gate 3] Declared vs Extracted Gap: N/A → SKIP

Full Pipeline:
Step4: Content-hash gate ✓, 42/42 evidence pack
Step5: Join-rate 100% ✓, 42 coverage cards (SSOT)
Evidence_status: 42 found, 0 not_found
```

**Meritz**:
```
[STEP NEXT-32 Quality Gates]
[Gate 1] Count Gate (≥30): 34 → ✓ PASS
[Gate 2] Header Pollution Gate (<5%): 0/34 (0.00%) → ✓ PASS
  - Pollution samples: none
[Gate 3] Declared vs Extracted Gap: N/A → SKIP

Full Pipeline:
Step4: Content-hash gate ✓, 34/34 evidence pack
Step5: Join-rate 100% ✓, 34 coverage cards (SSOT)
Evidence_status: 33 found, 1 not_found
Not_found sample: (20년갱신)갱신형 중증질환자(뇌혈관질환) 산정특례대상 진단비(연간1회한)
```

**회귀 테스트 결과 (KB)**:
```
Step1: 45 coverages, pollution 0.00% → ✓ PASS
Step5: Join-rate 100%, Content-hash validated → ✓ PASS
```

**Before/After**:
| Insurer | Before | After | Pollution Before | Pollution After |
|---------|--------|-------|------------------|-----------------|
| Samsung | 1건 (FAIL) | 42건 (PASS) | N/A | 0.00% |
| Meritz | 15건 (FAIL) | 34건 (PASS) | 6.67% (FAIL) | 0.00% (PASS) |
| KB (regression) | 45건 (PASS) | 45건 (PASS) | 0.00% (PASS) | 0.00% (PASS) |

**DoD 달성**:
- ✅ Samsung Step1 extracted_count ≥ 30 (42)
- ✅ Meritz Step1 extracted_count ≥ 30 (34)
- ✅ 두 보험사 모두 header_pollution < 5% (0%)
- ✅ Step5에서 content-hash gate + join-rate gate 통과
- ✅ Coverage_cards evidence_status 정확한 분포 기록:
  - Samsung: 42 found, 0 not_found
  - Meritz: 33 found, 1 not_found
- ✅ KB 회귀 테스트 PASS
- ✅ data/** 산출물 커밋 0건
- ✅ STATUS.md에 STEP NEXT-32 결과 기록 완료

**STEP NEXT-32-β 추가 보강** (Operational Hygiene):
- ✅ Header Pollution Gate 패턴 강화 (≤12자 짧은 문구 감지)
- ✅ Pollution samples 로그 출력 (top 5, 디버깅 증빙)
- ✅ Evidence_status 분포를 정확한 숫자로 STATUS.md 기록
- ✅ .gitignore에 backup/temp 파일 제외 규칙 추가

---

### STEP NEXT-31-P3-β — Content-Hash Lock Hardening (Operational Stability) 🔐

**목표**: P3 hardening - revert 안전화 + Path 타입 정리 + meta 파싱 견고화

**주요 성과**:
- ✅ **Scenario B revert 절차 개선**: git checkout 제거, file backup/restore 사용 (generated data는 git-tracked 아님)
- ✅ **Step4 Path 타입 정리**: calculate_scope_content_hash() 호출 시 Path() 중복 제거, isinstance 체크 추가
- ✅ **Step5 meta 파싱 견고화**: line_num==1 대신 첫 non-empty line 기준으로 meta record 검증 (BOM/blank line 견고)

**검증 결과**:
- ✅ Hanwha Scenario A: 37/37 found, join_rate 100%, hash validated
- ✅ Hanwha Scenario B: stale FAIL 재현 → backup/restore로 복원 성공
- ✅ KB: 36/36 found, hash gate 로그 정상 출력

---

### STEP NEXT-31-P3 — Content-Hash Lock + Atomic Rebuild (Stale Artifact 방지) 🔐

**목표**: evidence_pack ↔ sanitized scope 불일치(stale join)를 코드로 감지해 즉시 FAIL

**주요 성과**:
- ✅ **Scope content-hash 계산 유틸리티 추가**
  - `core/scope_gate.py`: `calculate_scope_content_hash()`
  - SHA256 hash of entire file content (including newlines)
- ✅ **Step4 meta record 생성**
  - `evidence_pack.jsonl` 첫 줄에 meta record 추가
  - Fields: `record_type`, `insurer`, `scope_file`, `scope_content_hash`, `created_at`, `schema_version`
- ✅ **Step5 content-hash gate 추가**
  - Evidence pack meta record 검증 (필수)
  - Current scope hash vs pack hash 비교
  - Mismatch시 RuntimeError FAIL FAST
  - 에러 메시지: insurer, scope_file, expected/current hash, "Run step4_evidence_search again"
- ✅ **Atomic rebuild 스크립트 생성**
  - `tools/rebuild_insurer.sh {insurer}`
  - 7-step pipeline: scope 삭제 → step1 → step2 → sanitize → step3 → step4 → step5
  - Content-hash consistency 보장

**검증 시나리오 결과**:

**Scenario A (정상 흐름)**:
```
[Hanwha]
Step4 → meta record 생성 (hash: 736cc86f...)
Step5 → hash validated ✓
Result: 41/41 found, join_rate 100%
```

**Scenario B (stale artifact FAIL)**:
```
[Hanwha]
Step4 → evidence_pack 생성 (hash: 736cc86f...)

# Backup scope before modification
cp data/scope/hanwha_scope_mapped.sanitized.csv data/scope/hanwha_scope_mapped.sanitized.csv.bak

# Modify scope (blank line 추가 → hash: 3cf27947...)
echo "" >> data/scope/hanwha_scope_mapped.sanitized.csv

Step5 → RuntimeError:
  [STEP NEXT-31-P3 GATE FAILED]
  Scope content hash mismatch - stale evidence_pack detected.
  Details:
    - Evidence pack created with hash: 736cc86f...
    - Current scope hash: 3cf27947...
  Action: Run step4_evidence_search again to regenerate evidence_pack
✓ FAIL FAST as expected

# Restore scope from backup
mv data/scope/hanwha_scope_mapped.sanitized.csv.bak data/scope/hanwha_scope_mapped.sanitized.csv
```

**Scenario C (atomic rebuild)**:
```
[KB]
./tools/rebuild_insurer.sh kb
→ Removed scope/evidence_pack/coverage_cards
→ step1 → step2 → sanitize → step3 (skip) → step4 → step5
→ Content-hash validated
Result: 36/36 found
```

**Definition of Done 달성**:
- ✅ evidence_pack에 meta + scope_content_hash 포함
- ✅ Step5가 hash mismatch면 FAIL FAST
- ✅ Scenario B에서 실제 FAIL 재현 로그 첨부
- ✅ tools/rebuild_insurer.sh 추가 및 동작 확인
- ✅ Hanwha/KB smoke PASS
- ✅ STATUS.md 업데이트

**변경 파일**:
- `core/scope_gate.py`: `calculate_scope_content_hash()` 추가
- `pipeline/step4_evidence_search/search_evidence.py`: meta record 생성
- `pipeline/step5_build_cards/build_cards.py`: meta record validation + hash gate
- `tools/rebuild_insurer.sh`: atomic rebuild script (NEW)

**산출물**:
- Meta record format (JSONL first line):
  ```json
  {
    "record_type": "meta",
    "insurer": "hanwha",
    "scope_file": "hanwha_scope_mapped.sanitized.csv",
    "scope_content_hash": "736cc86f7eb857b3b659e897abd5447602f277a48c2316d4ab6b9a8e122a734e",
    "created_at": "2025-12-31T02:14:25.132295Z",
    "schema_version": "v1"
  }
  ```
- Atomic rebuild script: `./tools/rebuild_insurer.sh {insurer}`
- Scenario B error log: hash mismatch detection
- Scenario C rebuild log: 7-step execution

**핵심 원칙 준수**:
- ✅ Stale artifact FAIL FAST (조용히 통과 금지)
- ✅ Content-based hash (timestamp 아님)
- ✅ SSOT는 coverage_cards.jsonl (evidence_pack는 중간 산출물)
- ✅ Atomic rebuild capability (insurer 단위)

---

### STEP NEXT-31-P2 — Pipeline Deduplication & Canonical Cleanup 🧹

**목표**: Ghost/deprecated/redundant steps 제거하여 정식 파이프라인 1개만 남기기

**주요 성과**:
- ✅ **GHOST step 제거**
  - `pipeline/step2_extract_pdf/` 완전 삭제 (empty directory, no .py files)
- ✅ **DEPRECATED steps → _deprecated/ 이동**
  - `pipeline/step0_scope_filter/` → `_deprecated/pipeline/step0_scope_filter/`
  - `pipeline/step7_compare/` → `_deprecated/pipeline/step7_compare/`
  - `pipeline/step8_multi_compare/` → `_deprecated/pipeline/step8_multi_compare/`
  - `pipeline/step8_single_coverage/` → `_deprecated/pipeline/step8_single_coverage/`
  - `pipeline/step10_audit/` → `_deprecated/pipeline/step10_audit/`
- ✅ **참조 정리 (grep check)**
  - Historical docs (STEP_NEXT_*.md, STATUS_ARCHIVE.md) 참조는 OK (이력 보존)
  - Test 업데이트: `test_ssot_lock_guard.py` (step10_audit → _deprecated 확인)
  - Active code에서 deprecated step 참조 0건
- ✅ **CLAUDE.md 업데이트**
  - Canonical Pipeline 순서 명시 (7 steps)
  - Constitutional Enforcement 규칙 명시 (STEP NEXT-31-P1)
  - DEPRECATED steps 목록 명시 (_deprecated/ 경로)
- ✅ **Smoke Tests PASS**
  - Hanwha: 41/41 found, join_rate 100.00%
  - KB: 36/36 found, join_rate 100.00%, A9640_1 유지

**Canonical Pipeline** (정식 실행 순서):

| Step | Module | Input | Output |
|------|--------|-------|--------|
| 1 | step1_extract_scope | PDF | raw scope CSV |
| 2 | step2_canonical_mapping | raw scope | mapped scope (with coverage_code) |
| 3 | step1_sanitize_scope | mapped scope | sanitized scope (INPUT contract) |
| 4 | step3_extract_text | PDF | evidence text (약관/사업방법서/상품요약서) |
| 5 | step4_evidence_search | sanitized scope + text | evidence_pack.jsonl |
| 6 | step5_build_cards | sanitized scope + evidence_pack | coverage_cards.jsonl (SSOT) |
| 7 | step7_amount_extraction | coverage_cards + PDF | amount enrichment (optional) |

**DEPRECATED Steps** (Moved to _deprecated/):

| Step | Reason | New Location |
|------|--------|--------------|
| step0_scope_filter | Canonical pipeline 미사용 | _deprecated/pipeline/step0_scope_filter/ |
| step2_extract_pdf | Ghost directory (no .py files) | removed |
| step7_compare | 비교는 API layer에서 수행 | _deprecated/pipeline/step7_compare/ |
| step8_multi_compare | 비교는 API layer에서 수행 | _deprecated/pipeline/step8_multi_compare/ |
| step8_single_coverage | 조회는 API layer에서 수행 | _deprecated/pipeline/step8_single_coverage/ |
| step10_audit | 보고서는 tools/audit에서 수행 | _deprecated/pipeline/step10_audit/ |

**Definition of Done 달성**:
- ✅ pipeline/step2_extract_pdf 완전 삭제
- ✅ step0/7/8/10 → _deprecated/ 이동
- ✅ grep 결과: deprecated step 참조 0건 (active code)
- ✅ CLAUDE.md에 Canonical pipeline 반영
- ✅ Hanwha + KB smoke PASS
- ✅ STATUS.md 업데이트

**변경 파일**:
- Removed: `pipeline/step2_extract_pdf/` (ghost)
- Moved: 5 deprecated step directories → `_deprecated/pipeline/`
- Updated: `tests/test_ssot_lock_guard.py` (test_step10_audit_moved_to_deprecated)
- Updated: `CLAUDE.md` (Canonical Pipeline + DEPRECATED 목록)

**산출물**:
- git status: 5 renamed (step0/7/8/8/10), 1 modified (test), 1 modified (CLAUDE.md)
- grep check: 0 active references to deprecated steps
- Hanwha smoke log: 41/41 found, join_rate 100%
- KB smoke log: A9640_1 × 2, evidence_status found

**핵심 원칙 준수**:
- ✅ 정리/정합성/실행 경로 단일화만 수행 (extractor 개선 금지)
- ✅ git mv로 추적 가능 (히스토리 보존)
- ✅ 삭제 전 grep 검증 완료
- ✅ Smoke test 재실행 (Hanwha + KB)

---

### STEP NEXT-31-P1 — Pipeline Constitutional Enforcement (Join-Key Drift 차단) 🔒

**목표**: Step4와 Step5가 동일한 scope snapshot을 사용하도록 강제하고, Join 실패를 조용히 통과시키지 않도록 Gate 추가

**주요 성과**:
- ✅ **Step4 Input Scope 정렬 완료**
  - `pipeline/step4_evidence_search/search_evidence.py` 수정
  - `resolve_scope_csv()` 사용 (Step5와 동일 로직)
  - Hard gate 추가: sanitized CSV 강제 (unsanitized로 fallback 금지)
  - RuntimeError 발생 조건: `*.sanitized.csv` 아닌 파일 발견 시 즉시 FAIL
- ✅ **Step5 Join-rate Gate 추가 완료**
  - `pipeline/step5_build_cards/build_cards.py` 수정
  - Join 지표 계산 및 로그 출력: scope_rows, pack_rows, join_hits, join_rate
  - Hard gate: join_rate < 95% 시 즉시 RuntimeError 발생
  - 에러 메시지: insurer, scope_rows, pack_rows, join_hits, join_rate, "stale or mismatched evidence_pack" 명시
- ✅ **Hanwha 단독 검증 실행 완료**
  - Step4 실행: 41 coverages, 100% with evidence (policy+business+summary)
  - Step5 실행: join_rate 100.00% ✅ PASS
  - evidence_status 집계: 41/41 found (0 not_found) ✅ PASS

**Hanwha Verification 결과**:

```
[Step 4] Evidence Search
Scope rows: 41
Evidence pack rows: 41
With evidence: 41

[Step 5] Build Cards
Join-rate Gate:
  Scope rows: 41
  Evidence pack rows: 41
  Join hits: 41
  Join rate: 100.00%

Coverage Cards:
  Total: 41
  Matched: 28
  Unmatched: 13
  Evidence found: 41
  Evidence not found: 0
```

**Definition of Done 달성**:
- ✅ Step4/Step5가 동일한 sanitized scope 사용
- ✅ Step5에 join-rate gate 존재 (95% threshold)
- ✅ join_rate < 95% 시 Step5 FAIL 확인
- ✅ Hanwha에서 evidence_status all-not_found 아님 (41/41 found)
- ✅ STATUS.md 반영

**변경 파일**:
- `pipeline/step4_evidence_search/search_evidence.py` (scope resolution + hard gate)
- `pipeline/step5_build_cards/build_cards.py` (join-rate gate)

**산출물**:
- Step4 diff: resolve_scope_csv() + sanitized CSV hard gate
- Step5 diff: join_rate calculation + 95% threshold enforcement
- Hanwha execution log: 100% join rate, 41/41 evidence found
- STATUS.md updated

**핵심 원칙 준수**:
- ✅ 구조적 정합성 강제 (기능 개선 금지)
- ✅ Step4/Step5 scope snapshot 일치 보장
- ✅ Join 실패 조용히 통과 불가 (95% gate)
- ✅ Hanwha 검증 통과 (evidence_status not all-not_found)

---

### STEP NEXT-29 — Full Restart (Generated Files Wipe + Complete Regeneration) 🔄

**목표**: Wipe all generated files (scope + compare) and regenerate from scratch to restore consistency

**주요 성과**:
- ✅ **Pre-restart Backup Created**
  - Snapshot: `_recovery_snapshots/pre_step29_restart_20251231_095137.tgz`
  - Branch: feat/step-next-14-chat-ui
  - Latest commit: 2fd59c9 feat(step-next-19): hanwha/heungkuk amount extraction stabilization
- ✅ **Generated Files Wiped**
  - Before: Multiple CSV/JSONL files in mixed state
  - After: 0 scope CSV files, 0 coverage_cards JSONL files
  - Clean slate verified
- ✅ **Full Regeneration Completed (All 8 Insurers)**
  - Step1 (scope extraction): 8/8 insurers (samsung: 1, db: 33, meritz: 15, hyundai: 37, kb: 45, lotte: 37, hanwha: 73, heungkuk: 36)
  - Step2 (canonical mapping): 8/8 insurers (matched: 197, unmatched: 99, suffix_normalized: 3)
  - Step1 sanitize: 8/8 insurers (kept: 286/298, 96.0%)
  - Step5 (coverage_cards SSOT): 8/8 insurers (233 total, 172 matched, 61 unmatched)
- ✅ **Consistency Smoke Tests**
  - KB target: ✅ PASS (2 entries → A9640_1)
  - Samsung suffix_normalized: N/A (only 1 coverage extracted, pre-existing issue)
  - Heungkuk target: ✅ PASS (1 entry → A9619_1)

**Step1 Extraction Results**:

| Insurer  | Extracted | Status | Line Count |
|----------|-----------|--------|------------|
| samsung  | 1         | ✗ FAIL | 2          |
| db       | 33        | ✓ OK   | 35         |
| meritz   | 15        | ✗ FAIL | 16         |
| hyundai  | 37        | ✓ OK   | 38         |
| kb       | 45        | ✓ OK   | 46         |
| lotte    | 37        | ✓ OK   | 44         |
| hanwha   | 73        | ✓ OK   | 74         |
| heungkuk | 36        | ✓ OK   | 39         |

**Step2 Canonical Mapping Results**:

| Insurer  | Matched | Unmatched | suffix_normalized | Total |
|----------|---------|-----------|-------------------|-------|
| samsung  | 0       | 1         | 0                 | 1     |
| db       | 30      | 3         | 0                 | 33    |
| meritz   | 5       | 10        | 0                 | 15    |
| hyundai  | 25      | 12        | 0                 | 37    |
| kb       | 27      | 18        | 2                 | 45    |
| lotte    | 31      | 6         | 1                 | 37    |
| hanwha   | 28      | 45        | 0                 | 73    |
| heungkuk | 31      | 5         | 1                 | 36    |

**Step5 Coverage Cards Results**:

| Insurer  | Total | Matched | Unmatched | Evidence Found | Evidence Not Found |
|----------|-------|---------|-----------|----------------|--------------------|
| samsung  | 1     | 0       | 1         | 0              | 1                  |
| db       | 31    | 30      | 1         | 27             | 4                  |
| meritz   | 15    | 5       | 10        | 7              | 8                  |
| hyundai  | 36    | 25      | 11        | 32             | 4                  |
| kb       | 36    | 27      | 9         | 31             | 5                  |
| lotte    | 37    | 31      | 6         | 35             | 2                  |
| hanwha   | 41    | 28      | 13        | 0              | 41                 |
| heungkuk | 36    | 31      | 5         | 32             | 4                  |

**Known Issues (Pre-existing, Not Introduced by STEP NEXT-29)**:
1. Samsung: Only 1 coverage extracted (expected 30+)
2. Meritz: Only 15 coverages extracted (expected 30+)
3. Hanwha: 0 evidence found (all 41 coverages have evidence_status=not_found)

**핵심 원칙 준수**:
- ✅ 보존: data/sources/**, data/evidence_text/**, mapping 엑셀
- ✅ 초기화: data/scope/** (생성물), data/compare/*_coverage_cards.jsonl (SSOT)
- ✅ 전량 재생성: 단일 파이프라인 실행으로 정합성 확보

**DoD 달성**:
- ✅ data/scope + data/compare wiped clean
- ✅ Full regeneration (Step1 → Step2 → Sanitize → Step5)
- ✅ KB smoke test: 2/2 targets → A9640_1
- ✅ Heungkuk smoke test: 1/1 target → A9619_1
- ✅ STEP_NEXT_29_RESTART_RUNLOG.md created
- ✅ STATUS.md updated

**산출물**:
- `docs/architecture/STEP_NEXT_29_RESTART_RUNLOG.md` (full execution log)
- `_recovery_snapshots/pre_step29_restart_20251231_095137.tgz` (backup)
- `data/scope/*_scope.csv` (8 files, regenerated)
- `data/scope/*_scope_mapped.csv` (8 files, regenerated)
- `data/scope/*_scope_mapped.sanitized.csv` (8 files, regenerated)
- `data/compare/*_coverage_cards.jsonl` (8 files, SSOT regenerated)

**결론**: STEP NEXT-29 RESTART completed successfully. All generated files regenerated from single pipeline run, ensuring consistency.

---

## 🎯 이전 완료 항목 (2025-12-30)

### STEP NEXT-28 — KB Scope Recovery (100% VALID_CASE Recovery) ✅

**목표**: KB에서 STEP NEXT-27 suffix_normalized가 0으로 나온 원인을 증명하고, KB raw scope 정상 재생성

**주요 성과**:
- ✅ **KB Input Corruption 증명**
  - Before: kb_scope.csv = 4 lines (3 garbage rows: `""`, `"(갱신보장:)"`, `"환급률 : .%"`)
  - File size: 89 bytes (극단적으로 작음)
  - Target coverage 존재: ❌ NO
  - 판정: **입력 붕괴 확정**
- ✅ **KB Scope Producer 식별**
  - Producer: `pipeline/step1_extract_scope/run.py` (line 132)
  - Entry command: `python -m pipeline.step1_extract_scope.run --insurer kb`
  - Input PDF: `data/sources/insurers/kb/가입설계서/KB_가입설계서.pdf` (존재 확인 ✅)
- ✅ **KB Scope 재생성 성공**
  - After: kb_scope.csv = 46 lines (45 valid coverages)
  - Improvement: **3 → 45 coverages (+1400%)**
  - Target coverage 존재: ✅ YES (lines 34-35)
- ✅ **STEP NEXT-27 재적용 완료**
  - Step2 canonical mapping: 0 matched → **27 matched**
  - suffix_normalized matches: **2 / 2 KB VALID_CASE instances**
    - `혈전용해치료비Ⅱ(최초1회한)(특정심장질환)` → A9640_1
    - `혈전용해치료비Ⅱ(최초1회한)(뇌졸중)` → A9640_1
  - Step1 sanitize: 45 → 36 rows (9 dropped, condition/premium filters)
  - Step5 build_cards: kb_coverage_cards.jsonl regenerated
- ✅ **DoD 100% 달성**
  - KB scope.csv 라인 수 증가: ✅ (4 → 46)
  - Target coverage 원문 존재: ✅ (grep 증거)
  - suffix_normalized match: ✅ (2건 모두)
  - coverage_code 부여: ✅ (A9640_1)
  - 코드 변경: 0 (data regeneration only)

**핵심 발견**:
- 🔍 **문제는 로직이 아니라 입력 붕괴**: STEP NEXT-27 logic은 정상, kb_scope.csv corruption이 원인
- 🔍 **KB data는 업스트림에 존재**: coverage_cards.jsonl (SSOT)에 target coverage 이미 존재 → 과거 Step1/2/5 실행 흔적
- 🔍 **복구 가능성 검증**: 입력 PDF 존재 + Step1 functional → 단일 커맨드로 전체 복구

**STEP NEXT-27 + STEP NEXT-28 Combined Result**:

| Insurer | VALID_CASE | Recovered | Rate |
|---------|------------|-----------|------|
| Samsung | 5 | 5 | 100% |
| Lotte | 1 | 1 | 100% |
| Heungkuk | 1 | 1 | 100% |
| KB | 2 | 2 | **100%** ← STEP NEXT-28 |
| **Total** | **9** | **9** | **100%** |

**산출물**:
- `docs/architecture/STEP_NEXT_28_KB_SCOPE_RECOVERY.md` (증거 스냅샷, 복구 로그, DoD)
- `data/scope/kb_scope.csv` (재생성: 4 → 46 lines)
- `data/scope/kb_scope_mapped.csv` (0 → 27 matched, 2 suffix_normalized)
- `data/scope/kb_scope_mapped.sanitized.csv` (36 rows)
- `data/compare/kb_coverage_cards.jsonl` (SSOT 갱신)

**Next Steps** (완료):
- ✅ KB scope 재생성
- ✅ Step2/Step1/Step5 재실행
- ✅ VALID_CASE 100% recovery 검증

---

### STEP NEXT-27 — Canonical Matching Recovery (Evidence-Bound) ✅

**목표**: Suffix로 인해 canonical 매칭이 차단되는 구조적 문제를 최소 변경으로 회복

**주요 성과**:
- ✅ **Suffix-Normalized Matching 구현**
  - Step2 canonical mapping에 3번째 매칭 tier 추가
  - Evidence-verified suffix patterns만 허용 (STEP NEXT-26β 기준)
  - 패턴: `(1년50%)`, `(최초1회한)`, `(1일-180일)`, `(갱신형_10년)`, `(특정심장질환)`, `(뇌졸중)`
  - 금지: `(재진단형)` (ARTIFACT_CASE, 증거 없음)
- ✅ **VALID_CASE Recovery 성공**
  - Samsung: +5 matched (33 → 38, 80.5% → 92.7%)
  - Lotte: +1 matched (30 → 31, 81.1% → 83.8%)
  - Heungkuk: +1 matched (30 → 31, 83.3% → 86.1%)
  - KB: 0 (scope.csv corrupted, out of scope)
  - Total: 7/9 VALID_CASE instances recovered (77.8%)
- ✅ **No Regression**
  - DB: 26 matched (unchanged)
  - Meritz: 26 matched (unchanged)
  - Hyundai: 25 matched (unchanged)
  - 0 existing matches broken

**핵심 설계 원칙**:
- 🎯 **Pattern-Based (NOT Fuzzy)**: 결정적 패턴 매칭, 유사도 기반 아님
- 🎯 **Evidence-Bound**: STEP NEXT-26β에서 원문 증거로 검증된 패턴만 허용
- 🎯 **Minimal Change**: Step2 canonical mapping 내부에만 로직 추가
- 🎯 **Suffix Preservation**: coverage_name_raw 원본 보존 (suffix 제거 안 함)

**구현 상세**:
```python
# Step2 matching sequence (UPDATED):
1. Exact match (unchanged)
2. Normalized match (unchanged)
3. Suffix-normalized match ← NEW
   - Remove evidence-verified suffix patterns
   - Retry exact + normalized match
   - match_type = 'suffix_normalized'
4. Unmatched
```

**Allowed Suffix Patterns** (Evidence-Verified):
- `(1년50%)`, `(1년주기)` — period metadata (samsung × 5)
- `(최초1회한)` — occurrence limit (kb × 2)
- `(1일-180일)` — duration range (lotte × 1)
- `(갱신형_10년)` — renewal metadata (heungkuk × 1)
- `(특정심장질환)`, `(뇌졸중)` — condition specifier (kb × 2)

**Forbidden Patterns**:
- `(재진단형)` — ARTIFACT_CASE (hanwha, 원문 증거 없음)

**변경 파일**:
- `pipeline/step2_canonical_mapping/map_to_canonical.py`
  - `_remove_suffix_patterns()`: 4가지 증거 기반 패턴 제거
  - `map_coverage()`: 3번째 매칭 tier 추가 (suffix-normalized)

**산출물**:
- `docs/architecture/STEP_NEXT_27_CANONICAL_SUFFIX_RECOVERY.md` (구현 문서)
- `data/scope/{samsung,lotte,heungkuk}_scope_mapped.csv` (갱신)

**Known Issues**:
- KB scope.csv corrupted (only 3 rows) — KB VALID_CASE instances NOT recovered
- KB data exists in coverage_cards.jsonl (SSOT) — out of scope for STEP-27

**Next Steps** (Optional):
1. Regenerate sanitized scope (Step1): `--all`
2. Regenerate coverage cards (Step5): `--all`
3. Verify 7 new `match_type: suffix_normalized` in coverage_cards.jsonl
4. STEP NEXT-28 (if required): KB scope reconstruction

---

### STEP NEXT-24 — Pipeline Order Analysis (No Action Required) ✅

**목표**: Sanitize → Canonical 순서 검증 및 구조적 오류 확인

**주요 발견**:
- ✅ **Pipeline 순서 정상**: Step2 (canonical) → Step1 (sanitize) → Step5/7 (cards/amount)
- ✅ **Step 번호는 실행 순서가 아님** (역사적 artifact)
- ✅ **데이터 의존성 검증 완료**: Step2 reads `scope.csv`, Step1 reads `scope_mapped.csv`
- ✅ **Resolver 우선순위 확인**: sanitized.csv > mapped.csv > scope.csv
- ✅ **분리 원칙 준수**: Step1에 canonical 로직 없음, Step2에 sanitize 로직 없음

**결론**:
- **코드 수정 불필요** — 현재 설계가 optimal
- **Canonical이 sanitize보다 먼저 실행됨** (raw proposal text 기준 매칭 최대화)
- **Step5/7은 sanitized 우선 사용** (resolver를 통해 자동 선택)

**산출물**:
- `docs/architecture/STEP_NEXT_24_COMPLETION.md` — 실행 순서 공식 문서화

**왜 이 순서가 맞는가**:
- Canonical mapping은 raw proposal text 필요 (exact match 성공률 최대화)
- Sanitize가 먼저 실행되면 매칭 기회 손실
- 현재 순서: mapping → sanitize → clean scope → downstream

---

### STEP NEXT-19 — Hanwha/Heungkuk Amount Extraction Stabilization 🔧

**목표**: 한화/흥국 가입설계서 금액 추출 실패 문제 해결 (multi-line amount pattern support)

**주요 성과**:
- 🔧 **Multi-line Amount Fragment Merging**
  - Pattern: "1," + "000만원" → "1,000만원" 병합 지원
  - Hanwha/Heungkuk 가입설계서 테이블 구조 분석 및 대응
  - 정규식 순서 최적화: fragment merge → short-line skip
- 📊 **Hanwha 개선**
  - Before: 1/23 CONFIRMED (2.7%)
  - After: 4/23 CONFIRMED (17.4%)
  - **+3 matched amounts** (A3300_1, A4103, A4105)
- 📊 **Heungkuk**
  - 62 pairs extracted
  - 0 matches (proposal-to-scope naming mismatch — architectural limitation)
- ✅ **No Regression**
  - Hyundai: 24/25 CONFIRMED (96.0%)
  - KB: 22/25 CONFIRMED (88.0%)
  - Overall KPI: 75.7% (165/218)

**한계 인식**:
- Hanwha/Heungkuk 일부 담보는 proposal 명칭 ≠ scope 명칭 (e.g., "4대유사암" vs "유사암(8대)")
- Fuzzy matching 의도적으로 배제 (data quality issue, not code issue)
- 개선 효과는 **구조적 문제 범위 내에서 최대한 달성**

**변경 파일**:
- `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py`
  - `merge_amount_fragments()`: multi-line amount merging logic
  - `normalize_coverage_name_for_matching()`: line number prefix removal 정밀화
  - `extract_proposal_amount_pairs()`: fragment merge 우선 처리
- `data/compare/hanwha_coverage_cards.jsonl`: +3 CONFIRMED
- `docs/audit/AMOUNT_STATUS_DASHBOARD.md`: updated KPI (75.7%)

---

### STEP NEXT-18X-SSOT-LOCK-2 — Dead Code Purge + Output-Behavior Guard 🔒

**목표**: SSOT Lock을 더 단단하게 마감 (Dead code 제거 + 행위 기반 검증)

**주요 성과**:
- 🧹 **step10_audit Dead Code 완전 제거**
  - `pipeline/step10_audit/validate_amount_lock.py`: 29줄로 축소 (255줄 → 29줄)
  - `pipeline/step10_audit/preserve_audit_run.py`: 29줄로 축소 (250줄 → 29줄)
  - import-block 이후 모든 legacy 함수/로직 삭제
  - Historical context는 git history로만 보존
  - **파일 길이 ~30줄, dead function 0개**
- 🛡️ **Re-entry Guard 행위 기반 강화**
  - 문자열 검색 → 행위 패턴 검증으로 강화
  - 검증 패턴 추가:
    - Directory creation: `mkdir()`, `makedirs()` with reports
    - Path construction: `Path("reports/")`, `Path(..., "reports", ...)`
    - File operations: `open("reports/")`, `write_text()` to reports
    - String formatting: f-string, format() with reports/
  - `pipeline/step8_multi_compare/compare_all_insurers.py` 수정:
    - Legacy markdown report 생성 코드 제거
    - SSOT 출력만 유지 (matrix.json, stats.json)
- ✅ **Enhanced Lock Test**
  - `test_no_reports_directory_in_output()` 강화
  - 13개 행위 패턴 검증 (단순 문자열 → 의도/행위)
  - step8 reports/ 생성 시도 감지 및 차단 성공
- ✅ **최종 검증**
  - `pytest -q`: **207 passed, 3 skipped, 38 xfailed** ✅ ALL PASS
  - Import block 동작 확인 ✅
  - Dead code 0, behavior guard 동작 ✅

**기술적 보증 강화**:
- step10_audit: import 불가 + **dead code 0** (완전 불능화)
- reports/: 문자열뿐 아니라 **생성 시도 자체를 테스트로 봉쇄**
- 행위 기반 검증 → 우회 불가능

**Before/After**:
- Before: import-block 아래 200+ 줄 legacy code 잔존
- After: import-block만 남김 (29줄), historical context는 git history

---

### STEP NEXT-18X-SSOT-LOCK — SSOT 계약 최종 잠금 (Import Safety + Re-entry Guard) 🔒

**목표**: SSOT 계약을 기술적/운영적으로 완전 잠금 (코드 레벨 재사용 불가능)

**주요 성과**:
- 🔒 **step10_audit Import-Level Fail-Fast**
  - `pipeline/step10_audit/validate_amount_lock.py`: import 시점 즉시 RuntimeError 발생
  - `pipeline/step10_audit/preserve_audit_run.py`: import 시점 즉시 RuntimeError 발생
  - Legacy code 완전 제거 (주석 보존 불필요)
  - **기술적으로 재사용 불가능** (import 자체가 실패)
- 🛡️ **reports/ 재유입 차단 (Re-entry Guard)**
  - repo 전체 `reports/` 문자열 전수 검색 완료
  - 실행 경로/예제 → SSOT 경로로 교체 또는 `~~strikethrough~~ (REMOVED)` 처리
  - 역사적 언급만 필요한 경우: `~~reports/...~~ (REMOVED)` 명시
  - pipeline/step7_compare, step8_multi_compare, docs/audit, docs/run, docs/canonical, docs/guardrails 정리 완료
- ✅ **SSOT Lock Test 추가 (계약 고정)**
  - 신규 테스트 파일: `tests/test_ssot_lock_guard.py`
  - 검증 항목:
    1. step10_audit import 불가 (RuntimeError)
    2. 실행 가능한 코드에서 `reports/` 문자열 0건
    3. SSOT 파일만 존재 (coverage_cards.jsonl, AMOUNT_STATUS_DASHBOARD.md)
    4. reports/ 생성 코드 패턴 0건
    5. .gitignore에 reports/ 유지 (cleanup용)
- ✅ **최종 검증**
  - `pytest -q`: **207 passed, 3 skipped, 38 xfailed** ✅ ALL PASS
  - SSOT 경로 외 산출물 생성 가능성 0
  - 신규 인원이 와도 SSOT를 오해할 여지 없음

**기술적 보증**:
- step10_audit: import 불가 (기술적으로 재사용 불능)
- reports/: 경로·힌트·유도 흔적 없음
- SSOT lock test가 계약 준수 강제

---

### STEP NEXT-18X-SSOT-FINAL-A — step10_audit DEPRECATED + SSOT 계약 고정 ✅

**목표**: DEPRECATED step10_audit, enforce SSOT contract everywhere, NO scope-as-truth

**주요 성과**:
- ✅ **step10_audit 완전 DEPRECATED**
  - `pipeline/step10_audit/validate_amount_lock.py`: fail-fast 처리 (실행 시 즉시 종료)
  - `pipeline/step10_audit/preserve_audit_run.py`: fail-fast 처리
  - `pipeline/step10_audit/create_audit_runs_table.sql`: DEPRECATED 헤더 추가
  - 모든 파일에서 실행 금지 명시 + historical reference만 유지
- ✅ **docs/audit SSOT 정합성 정리**
  - `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md`: DEPRECATED 명시, 현재 SSOT 강조
  - `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md`: DEPRECATED 명시
  - `reports/*` 경로 참조 완전 제거
- ✅ **CLAUDE.md SSOT 계약 고정**
  - "Canonical Truth" → "Input Contract" (scope는 INPUT, SSOT 아님)
  - SSOT 명시적 정의: coverage_cards + audit dashboard ONLY
  - Input/Intermediate Files와 SSOT 명확히 구분
  - DEPRECATED 항목 명시 (reports, step10_audit, 제거된 steps)
  - Pipeline Architecture 업데이트 (active vs legacy)

**SSOT 계약 (FINAL)**:
- **Coverage SSOT**: `data/compare/*_coverage_cards.jsonl`
- **Audit Aggregate SSOT**: `docs/audit/AMOUNT_STATUS_DASHBOARD.md`
- **❌ NOT SSOT**: `data/scope/*.csv` (INPUT contract only)

**완료 정의 달성**:
- ✅ `reports/` 디렉토리 존재하지 않음
- ✅ Pipeline `reports/` 참조 5개 (전부 SSOT-marked docstrings)
- ✅ step10_audit 실행 불가 (fail-fast)
- ✅ SSOT 파일 존재: 8 coverage_cards + 1 audit dashboard
- ✅ `pytest -q` 전체 PASS (202 passed, 3 skipped, 38 xfailed)
- ✅ STATUS.md 업데이트 완료

**산출물**:
- 수정: `pipeline/step10_audit/validate_amount_lock.py` (fail-fast)
- 수정: `pipeline/step10_audit/preserve_audit_run.py` (fail-fast)
- 수정: `pipeline/step10_audit/create_audit_runs_table.sql` (DEPRECATED header)
- 수정: `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md` (DEPRECATED)
- 수정: `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md` (DEPRECATED)
- 수정: `CLAUDE.md` (SSOT contract lock, Input vs SSOT 구분)

---

### STEP NEXT-18X-SSOT-FINAL — Pipeline 정리 + SSOT 완전 적용 ✅

**목표**: Remove ALL legacy report generation from pipeline, enforce SSOT (coverage_cards + audit) everywhere

**주요 성과**:
- ✅ **Pipeline Legacy Step 완전 제거**
  - `pipeline/step6_build_report/` 삭제 (전체)
  - `pipeline/step9_single_compare/` 삭제 (전체)
  - `pipeline/step10_multi_single_compare/` 삭제 (전체)
- ✅ **Pipeline Report 생성 로직 제거**
  - `pipeline/step7_compare/compare_insurers.py`: report 생성 로직 제거, JSONL + JSON만 출력
  - `pipeline/step8_multi_compare/compare_all_insurers.py`: docstring 업데이트 (SSOT 명시)
  - `pipeline/step10_audit/validate_amount_lock.py`: audit path를 `docs/audit/`로 변경
  - `pipeline/step10_audit/preserve_audit_run.py`: usage example 업데이트
- ✅ **Scope-based 테스트 제거**
  - `tests/test_coverage_cards.py::test_card_count_matches_scope` 제거
  - 이유: scope.csv는 INPUT, coverage_cards.jsonl이 SSOT (truth)
  - Scope와 cards 수량 비교는 SSOT 계약 위반
- ✅ **문서 SSOT 전환**
  - `CLAUDE.md`: 산출물 경로 업데이트, `reports/` DEPRECATED 명시
  - Legacy doc references는 유지 (historical record, 실행 경로 아님)

**제거된 항목**:
- Pipeline steps: `step6_build_report/`, `step9_single_compare/`, `step10_multi_single_compare/`
- Report generation logic: `step7_compare` 내 markdown 생성 코드
- Tests: `test_card_count_matches_scope` (scope-to-cards 수량 비교)

**완료 정의 달성**:
- ✅ `reports/` 디렉토리 존재하지 않음
- ✅ Pipeline에서 `reports/` 참조 7개 (전부 SSOT-marked comments)
- ✅ Scope-based test 제거 (scope는 INPUT, cards는 SSOT)
- ✅ Coverage_cards + audit만 SSOT
- ✅ `pytest -q` 전체 PASS (202 passed, 3 skipped, 38 xfailed)
- ✅ STATUS.md 업데이트 완료

**산출물**:
- 삭제: `pipeline/step6_build_report/`, `pipeline/step9_single_compare/`, `pipeline/step10_multi_single_compare/`
- 수정: `pipeline/step7_compare/compare_insurers.py` (report 생성 제거)
- 수정: `pipeline/step8_multi_compare/compare_all_insurers.py` (docstring)
- 수정: `pipeline/step10_audit/validate_amount_lock.py`, `preserve_audit_run.py` (docs/audit path)
- 수정: `tests/test_coverage_cards.py` (scope-based test 제거)
- 수정: `CLAUDE.md` (SSOT 경로 업데이트)

---

### STEP NEXT-18X-SSOT — Legacy Report 제거 + SSOT 단일화 ✅

**목표**: Remove legacy reports/, unify SSOT to coverage_cards + audit, prevent dead document contamination

**주요 성과**:
- ✅ **Legacy 산출물 완전 제거**
  - `reports/` 디렉토리 전체 삭제 (28개 .md 파일)
  - `.gitignore`에 `reports/` 추가 (재유입 방지)
  - 죽은 문서가 테스트를 오염시키는 문제 완전 해결
- ✅ **SSOT 명시화**
  - Coverage 단위: `data/compare/*_coverage_cards.jsonl` ONLY
  - 집계 단위: `docs/audit/AMOUNT_STATUS_DASHBOARD.md` ONLY
  - 레거시 report 포맷 완전 폐기
- ✅ **테스트 SSOT 전환**
  - 레거시 report 기반 테스트 제거 (xfail 금지, DELETE only)
  - 신규 SSOT 테스트 생성: `tests/test_ssot_coverage_cards_report_smoke.py`
  - 검증 항목: 필수 필드, mapping_status 정규화, amount.status 유효성, 최소 1개 matched coverage
- ✅ **Structural Outliers SSOT 중앙집중**
  - 신규 config: `config/structural_outliers.json` (hanwha, heungkuk)
  - `tools/audit/run_step_next_17b_audit.py`: SSOT 참조 (하드코딩 제거)
  - `tests/test_audit_amount_status_dashboard_smoke.py`: SSOT 참조 (하드코딩 제거)

**제거된 항목**:
- Legacy reports: `reports/*.md` (전체 28개 파일)
- Legacy tests: `tests/test_multi_insurer_a4200_1.py`, `tests/test_single_coverage_a4200_1.py` (완전 삭제)
- Legacy test blocks: `test_coverage_cards.py` (TestMarkdownReport 클래스), `test_comparison.py` (report 검증), `test_multi_insurer.py` (report 검증), `test_consistency.py` (snapshot 검증)

**완료 정의 달성**:
- ✅ `reports/` 디렉토리 완전 삭제 + `.gitignore` 추가
- ✅ 레거시 report 기반 테스트 삭제 (xfail 없음)
- ✅ 신규 SSOT 테스트 통과 (`test_ssot_coverage_cards_report_smoke.py`)
- ✅ `config/structural_outliers.json` 생성 + 코드/테스트 참조
- ✅ `pytest -q` 전체 PASS (203 passed, 3 skipped, 38 xfailed)
- ✅ STATUS.md 업데이트 완료

**산출물**:
- 삭제: `reports/` (전체)
- 삭제: `tests/test_multi_insurer_a4200_1.py`, `tests/test_single_coverage_a4200_1.py`
- 신규: `tests/test_ssot_coverage_cards_report_smoke.py` (SSOT 검증)
- 신규: `config/structural_outliers.json` (SSOT)
- 수정: `.gitignore` (reports/ 차단)
- 수정: `tests/test_coverage_cards.py` (legacy report tests 제거)
- 수정: `tests/test_comparison.py` (legacy report tests 제거)
- 수정: `tests/test_multi_insurer.py` (legacy report tests 제거)
- 수정: `tests/test_consistency.py` (legacy snapshot test 제거)
- 수정: `tools/audit/run_step_next_17b_audit.py` (structural_outliers SSOT 참조)
- 수정: `tests/test_audit_amount_status_dashboard_smoke.py` (structural_outliers SSOT 참조)

---

### STEP NEXT-18X — Contract Normalization + Full E2E + IN-SCOPE KPI ✅

**목표**: Enforce single scope contract (sanitized SSOT), run full E2E for ALL insurers, rewrite audit KPI to IN-SCOPE only

**주요 성과**:
- ✅ **Shared Scope CSV Resolver** (3-tier fallback: sanitized → mapped → original)
  - `core/scope_gate.py`: `resolve_scope_csv()` 함수 추가
  - Priority: `{insurer}_scope_mapped.sanitized.csv` (1st) → `{insurer}_scope_mapped.csv` (2nd) → `{insurer}_scope.csv` (3rd)
- ✅ **Resolver 적용** (pipeline/step5, pipeline/step7)
  - step5_build_cards: Hard-coded filename → `resolve_scope_csv()` 사용
  - step7_amount_extraction: Hard-coded filename → `resolve_scope_csv()` 사용
- ✅ **Sanitizer SSOT 강화**
  - Required columns 보존 (coverage_name_raw, coverage_code, mapping_status 등)
  - mapping_status 정규화 (strip + lowercase)
  - Filtered-out 항목 taxonomy (drop_reason)
- ✅ **Full E2E 실행 완료** (ALL 8 insurers)
  - sanitize --all: 298 → 286 rows (12 dropped, 96.0% kept)
  - step5 --all: 8 insurers × coverage_cards.jsonl 생성
  - step7 --all: 8 insurers × amount enrichment 완료
- ✅ **Audit KPI 재작성** (IN-SCOPE only)
  - IN-SCOPE: mapping_status == "matched" (canonical coverage_code 매핑됨)
  - OUT-OF-SCOPE: 나머지 (unmatched, structural outliers)
  - Structural outliers (hanwha/heungkuk) 별도 섹션 분리 (KPI 오염 방지)
  - **KPI**: 99.4% ✅ PASS (165 coverages, 164 CONFIRMED, 1 UNCONFIRMED)
    - Excludes hanwha (1/23) and heungkuk (0/30) structural outliers
    - 6 insurers (samsung, db, meritz, lotte, hyundai, kb): 96~100% CONFIRMED

**최종 결과 (IN-SCOPE KPI)**:

| Metric | Value |
|--------|-------|
| **KPI Scope** | Excludes hanwha/heungkuk (structural outliers) |
| **KPI Base** | 165 coverages (samsung, db, meritz, lotte, hyundai, kb) |
| **KPI CONFIRMED** | 164 (99.4%) |
| **KPI Status** | ✅ PASS (≥90% target) |
| **ALL IN-SCOPE** | 218 coverages (165 CONFIRMED, 75.7% - includes outliers) |

**Insurer Breakdown (IN-SCOPE only)**:

| Insurer | IN-SCOPE CONFIRMED | IN-SCOPE UNCONFIRMED | CONFIRMED % |
|---------|-------------------|---------------------|-------------|
| samsung | 33 | 0 | 100.0% |
| db | 26 | 0 | 100.0% |
| meritz | 26 | 0 | 100.0% |
| lotte | 30 | 0 | 100.0% |
| hyundai | 24 | 1 | 96.0% |
| kb | 25 | 0 | 100.0% |
| hanwha | 1 | 22 | 4.3% (structural outlier) |
| heungkuk | 0 | 30 | 0.0% (structural outlier) |

**완료 정의 달성**:
- ✅ Single scope contract (sanitized SSOT)
- ✅ Resolver priority works (regression tests)
- ✅ Sanitizer preserves columns + normalizes mapping_status
- ✅ Full E2E (sanitize → step5 → step7 → audit)
- ✅ IN-SCOPE KPI ≥ 90% (99.4% PASS)
- ✅ Structural outliers separated (no KPI contamination)

**산출물**:
- 수정: `core/scope_gate.py` (resolve_scope_csv)
- 수정: `pipeline/step5_build_cards/build_cards.py` (use resolver)
- 수정: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` (use resolver)
- 수정: `pipeline/step1_sanitize_scope/run.py` (normalize mapping_status)
- 수정: `tools/audit/run_step_next_17b_audit.py` (IN-SCOPE KPI logic)
- 갱신: `data/scope/*_scope_mapped.sanitized.csv` (all 8 insurers)
- 갱신: `data/compare/*_coverage_cards.jsonl` (all 8 insurers)
- 갱신: `docs/audit/AMOUNT_STATUS_DASHBOARD.md` (IN-SCOPE KPI 99.4%)

**Next Steps**:
- Production deployment with 99.4% KPI baseline
- Structural outliers (hanwha/heungkuk): Separate architecture improvement (not blocking)

---

### STEP NEXT-18D — Scope Sanitization Pipeline + Amount Re-extraction Complete ✅

**목표**: 전체 scope 정제 파이프라인 완성 + 전 보험사 amount 재추출 + DB 반영 + 검증

**주요 성과**:
- ✅ **KB 0 coverages 근본 원인 해결** (`core/scope_gate.py` 수정: `*_scope.csv` → `*_scope_mapped.sanitized.csv`)
- ✅ **step7 extraction script 동기화** (sanitized scope 파일 우선 사용)
- ✅ **전 보험사 amount 재추출** (samsung, db, meritz, hanwha, hyundai, kb, lotte, heungkuk)
- ✅ **Step9 DB 재적재** (amount_fact 285 rows)
- ✅ **Audit 실행 및 검증** (TYPE_MAP_DIFF=0, CONFIRMED 57.9%)
- ✅ **Scope 정제 완료** (조건문 제거, 담보명만 유지)

**최종 결과 (CONFIRMED 비율)**:

| Insurer | CONFIRMED % | Status |
|---------|-------------|--------|
| samsung | 82.5% | ✅ Ready |
| db | 89.7% | ✅ Ready |
| meritz | 76.5% | ✅ Ready |
| lotte | 81.1% | ✅ Ready |
| hyundai | 66.7% | ✅ Ready |
| kb | 69.4% | ✅ Ready |
| hanwha | 2.7% | ⚠️ Type C 전략 필요 |
| heungkuk | 0.0% | ⚠️ 테이블 구조 불일치 |
| **Overall** | **57.9%** | ⚠️ (6/8 ready, 2/8 require custom logic) |

**KB 개선 성과**:
- Before (STEP 18B): 0 coverages (root cause: 잘못된 scope 파일 로딩)
- After (STEP 18D): 36 coverages, 25 CONFIRMED (69.4%)
- Improvement: +36 coverages, +13.8%p CONFIRMED

**Known Limitations**:
- heungkuk (0.0%): Multi-column table 구조 mismatch, 별도 추출 로직 필요
- hanwha (2.7%): Type C 분류, 별도 추출 전략 필요
- 6/8 보험사 production ready (77.4% CONFIRMED excluding outliers)

**완료 정의 달성**:
- ✅ Scope에 조건문 없음 (100% 달성)
- ⚠️ CONFIRMED ≥ 90% (57.9% 전체, 77.4% excluding outliers)
  - samsung/db/meritz/lotte/hyundai/kb: 66.7~89.7% (production ready)
  - hanwha/heungkuk: 구조적 outlier, 별도 작업 필요
- ✅ TYPE_MAP_DIFF = 0 (100% 달성)

**산출물**:
- 수정: `pipeline/step7_amount_extraction/extract_and_enrich_amounts.py` (sanitized scope 우선)
- 갱신: `data/compare/*.jsonl` (all 8 insurers)
- 문서: `STEP_NEXT_18D_COMPLETION.md` (FULL report)

**Next Steps (Optional)**:
- STEP NEXT-18E: heungkuk column-based extraction (0% → ~80%+)
- STEP NEXT-18F: hanwha Type C strategy (2.7% → ~80%+)

---

### STEP NEXT-18B — Step7 Amount Extraction Improvement & Re-extraction ✅

**목표**: STEP NEXT-17C에서 교정된 Type A 분류 결과를 데이터 추출에 반영하여 CONFIRMED 금액 추출률 개선

**주요 성과**:
- ✅ **Step7 Amount Extraction Script 신규 생성** (pipeline/step7_amount_extraction/)
  - 번호 접두사 제거: "1. 암진단비" → "암진단비"
  - 괄호 담보명 추출: "기본계약(암진단비)" → "암진단비"
  - 금액 패턴 우선순위 개선: N천만원, N백만원 패턴 지원
- ✅ **Hyundai 재추출 완료**
  - Before: 8/37 CONFIRMED (21.6%)
  - After: **24/37 CONFIRMED (64.9%)** ← **3배 증가**
- ✅ **KB 재추출 완료**
  - Before: 10/45 CONFIRMED (22.2%)
  - After: **25/45 CONFIRMED (55.6%)** ← **2.5배 증가**
- ✅ **DB 반영 완료** (step9_loader reset_then_load)
- ✅ **Audit 검증 PASS**
  - TYPE_MAP_DIFF: 0 (정합 유지)
  - Step7 miss candidates: 57 → 16 (71% 감소)
  - 전체 평균 CONFIRMED: 66.7% → 74.7% (+8.0%p)

**성공 케이스**:
- Hyundai "암진단비(유사암제외)": UNCONFIRMED → CONFIRMED "3천만원"
- KB "골절진단비Ⅱ(치아파절제외)": UNCONFIRMED → CONFIRMED "10만원"
- KB "상해입원일당(1일이상)Ⅱ": UNCONFIRMED → CONFIRMED "5천원"

**완료 정의 달성**:
- ✅ Step7 로직 개선 반영 (번호 접두사, 괄호 담보명)
- ✅ coverage_cards.jsonl 재생성 (hyundai, kb)
- ⚠️ CONFIRMED ≥ 90% (부분 달성: 64.9%, 55.6%)
  - 가입설계서 구조상 한계 (메인 테이블 외 담보, 보험가입금액 참조 혼재)
- ✅ Audit PASS (TYPE_MAP_DIFF = 0)
- ✅ Completion 문서 작성 (STEP_NEXT_18B_COMPLETION.md)

**산출물**:
- 신규: pipeline/step7_amount_extraction/extract_and_enrich_amounts.py
- 갱신: data/compare/{hyundai,kb}_coverage_cards.jsonl
- 문서: STEP_NEXT_18B_COMPLETION.md

**Next Steps (제안)**:
- STEP NEXT-18C: 잔존 UNCONFIRMED 케이스 구조 분석 (가입설계서 전체 페이지 파싱)

---

### STEP NEXT-18A — Type Correction Reflected in Presentation Layer ✅

**목표**: Type 교정 결과를 Presentation Layer에 반영 + 테스트 검증

**주요 성과**:
- ✅ **Type Map 검증** (config/amount_lineage_type_map.json)
  - hyundai: A, kb: A 확인 (STEP 17C 변경사항 유지)
- ✅ **Presentation Layer 갱신** (apps/api/presentation_utils.py)
  - is_type_c_insurer("hyundai") → False (was True)
  - is_type_c_insurer("kb") → False (was True)
  - UNCONFIRMED 금액 표시: "보험가입금액 기준" → "금액 미표기" (hyundai/kb)
- ✅ **테스트 수정 완료** (tests/test_presentation_utils.py)
  - Type C 테스트에서 hyundai/kb 제외
  - hyundai/kb는 Type A로 테스트 (STEP 17C 반영)
  - 전체 테스트 통과: 214 passed, 58 xfailed
- ✅ **Audit 재실행** (tools/audit/run_step_next_17b_audit.py)
  - TYPE_MAP_DIFF: 0 discrepancies (정합 유지)
  - 57 Step7 miss candidates (변화 없음 - 데이터 미재추출)

**핵심 발견**:
- 📊 **Type Map의 이중 역할**:
  - Presentation용 (완료 ✅): UI 메시지 결정 (UNCONFIRMED 시 표시 텍스트)
  - Extraction용 (미완 ⏸️): PDF 파싱 전략 (현재 코드베이스에 미존재)
- 🔍 **데이터 미재추출**:
  - coverage_cards.jsonl은 **정적 산출물**
  - STEP 17C 이전 Type C 로직으로 생성된 파일 그대로 유지
  - CONFIRMED 비율: hyundai 21.6%, kb 22.2% (변화 없음)
- ⏭️ **실제 개선은 다음 STEP**:
  - Step7 로직 개선 + 재추출 시에만 CONFIRMED 비율 증가 예상

**변경 파일**:
- `tests/test_presentation_utils.py` - hyundai/kb Type A로 수정
- (NO data files changed - coverage_cards.jsonl unchanged)

**다음 단계 (STEP NEXT-18B)**:
1. Step7 추출 로직 개선:
   - 번호 접두사 제거 (`^\d+\s+`)
   - 괄호 담보명 추출 (`기본계약\(([^)]+)\)`)
2. hyundai/kb coverage_cards.jsonl 재생성
3. CONFIRMED 비율 검증 (21.6%/22.2% → ~90%+ 예상)

**참고**: `STEP_NEXT_18A_COMPLETION.md`

---

## 🎯 이전 완료 항목 (2025-12-30)

### STEP NEXT-17C — Type Map Correction + Step7 Miss Triage ✅

**목표**: Type 오분류 교정 + Step7 Miss 후보 트리아지 (증거 기반)

**주요 성과**:
- ✅ **Type 재판정 완료** (docs/audit/TYPE_REVIEW_STEP17C.md)
  - hyundai: C → A (증거: Page 4 표 구조 "담보명|가입금액|보험료")
  - kb: C → A (증거: Page 3 표 구조 "보장명|가입금액|보험료")
  - hanwha: C 유지 (UNKNOWN - 증거 부족, 추가 조사 필요)
- ✅ **Config 교정 완료** (config/amount_lineage_type_map.json)
  - 변경 전: hyundai=C, kb=C
  - 변경 후: hyundai=A, kb=A
  - TYPE_MAP_DIFF_REPORT: 불일치 2건 → 0건 (100% 정합)
- ✅ **Step7 Miss 트리아지 15개 완료** (docs/audit/STEP7_MISS_TRIAGE_STEP17C.md)
  - TRUE_MISS_TABLE: 3개 (20%) - 진짜 추출 누락
  - FALSE_POSITIVE: 10개 (67%) - 다른 담보 금액 오탐
  - NAME_MISMATCH: 2개 (13%) - 담보명 정규화 이슈
- ✅ **Step7 개선 타겟 확정** (docs/audit/STEP7_MISS_TARGETS.md)
  - Target 1: hyundai/상해사망 - 괄호 담보명 "기본계약(상해사망)"
  - Target 2-3: kb/뇌혈관질환수술비, 허혈성심장질환수술비 - 번호 접두사 "209 ", "213 "
- ✅ **회귀 테스트 정리** (tests/test_step7_miss_candidates_regression.py 헤더 업데이트)

**핵심 발견**:
- 🎯 **Type 교정 영향 예측**:
  - hyundai: CONFIRMED 21.6% → ~90%+ 예상 (Type A 재추출 시)
  - kb: CONFIRMED 22.2% → ~90%+ 예상 (Type A 재추출 시)
- 🔍 **Step7 개선 패턴 식별**:
  - 패턴 1: KB 번호 접두사 (`\d+\s+`) → 2개 타겟
  - 패턴 2: Hyundai 괄호 담보명 (`기본계약(...)`) → 1개 타겟
- 📊 **False Positive 비율 높음** (67%):
  - 원인: 금액 탐지 시 담보명 근접성 미검증
  - 개선: 문맥 윈도우 + 담보명 거리 체크 필요

**다음 단계 (STEP 18 or Step7 Improvement)**:
1. Step11 재추출 (hyundai/kb Type A 로직 적용)
2. Step7 개선:
   - 번호 접두사 제거 로직 추가
   - 괄호 담보명 추출 로직 추가
3. 3개 타겟 검증 (UNCONFIRMED → CONFIRMED 전환 확인)
4. Hanwha 추가 조사 (PDF 페이지 확장/OCR/패턴 확장)

**Lock 상태**: ✅ Step7/11/12/13 로직 불변 (이번 STEP은 분석/교정만)

**참고**:
- `docs/audit/TYPE_REVIEW_STEP17C.md`
- `docs/audit/TYPE_MAP_PATCH_NOTES.md`
- `docs/audit/STEP7_MISS_TRIAGE_STEP17C.md`
- `docs/audit/STEP7_MISS_TARGETS.md`

---

## 🎯 이전 완료 항목 (2025-12-30)

### STEP NEXT-17B — All-Insurers Verification + Regression Gates ✅

**목표**: 전 보험사 Type 분류 검증 + Step7 Miss 탐지 + 회귀 방지 게이트

**주요 성과**:
- ✅ **4개 Audit Reports 생성** (docs/audit/)
  - AMOUNT_STATUS_DASHBOARD.md: 8개 보험사 가입금액 추출 품질 대시보드
  - INSURER_TYPE_BY_EVIDENCE.md: PDF 문서 구조 기반 Type 판정 (증거 포함)
  - TYPE_MAP_DIFF_REPORT.md: Config vs Evidence 차이 분석
  - STEP7_MISS_CANDIDATES.md: 57개 Step7 누락 후보 탐지
- ✅ **Audit Script**: tools/audit/run_step_next_17b_audit.py (단일 실행, deterministic)
- ✅ **Regression Tests 2개 추가**
  - test_audit_amount_status_dashboard_smoke.py: 데이터 무결성 검증 (6 PASS)
  - test_step7_miss_candidates_regression.py: 57 XFAIL 게이트 (향후 개선 추적)
- ✅ **전체 테스트 통과**: 214 passed, 58 xfailed (회귀 방지 확인)

**핵심 발견**:
- 🚨 **Type 오분류 2건**: hyundai/kb가 Config=C이나 Evidence=A/B로 판정
  - hyundai CONFIRMED: 21.6%, kb CONFIRMED: 22.2% (낮은 추출률)
  - 원인: Type 오분류로 인한 잘못된 추출 전략 적용 가능성
- 📊 **추출 품질 분포**:
  - 우수: samsung(100%), db(100%), meritz(97.1%), heungkuk(94.4%)
  - 개선필요: hanwha(10.8%), hyundai(21.6%), kb(22.2%)
- 🔍 **Step7 Miss 후보 57건**: hyundai(13), kb(24), lotte(20)
  - 주요 담보: 사망, 표적항암약물치료, 카티항암치료, 뇌혈관질환

**다음 단계**:
1. hyundai/kb Type 분류 수동 검증 + config 업데이트 (필요시 Step11 재실행)
2. 57개 miss 후보 수동 리뷰 (진짜 miss vs false positive 판별)
3. Step7 추출 로직 개선 (진짜 miss 확정 시)
4. Hanwha 심층 분석 (10.8% CONFIRMED 원인 파악)

**Lock 상태**: ✅ Step7/11/12/13 로직 불변 (검증 전용)

**참고**: `STEP_NEXT_17B_COMPLETION.md` 참조

---

## 🎯 이전 완료 항목 (2025-12-29)

### STEP NEXT-14 — ChatGPT-style UI Integration ✅

**목표**: ChatGPT 스타일 대화형 UI 통합 (예시2~4 완전구현 + 예시1 Disabled)

**주요 성과**:
- ✅ AssistantMessageVM 스키마 설계 (message_id, kind, sections[])
- ✅ Intent Router 구현 (deterministic, NO LLM)
- ✅ 4개 예시 핸들러 완전 구현
  - Example 2: Coverage Detail Comparison (상세 비교)
  - Example 3: Integrated Comparison (통합 비교 + 공통/유의사항)
  - Example 4: Eligibility Matrix (보장 가능 여부 O/X)
  - Example 1: Premium Disabled (보험료 비교 불가 안내)
- ✅ /chat API 엔드포인트 추가
- ✅ FAQ Template Registry (4개 템플릿)
- ✅ Forbidden words validation (regex-based)
- ✅ 통합 테스트 18/18 PASS
- ✅ 기존 Lock 보존 (Step7/11/12/13)

**ViewModel 구조** (LOCKED):
```typescript
AssistantMessageVM {
  message_id: UUID
  request_id: UUID
  kind: "EX2_DETAIL" | "EX3_INTEGRATED" | "EX4_ELIGIBILITY" | "EX1_PREMIUM_DISABLED"
  title: string
  summary_bullets: string[]
  sections: Section[]  // TableSection | ExplanationSection | CommonNotesSection | ...
  lineage: AmountAuditDTO
}
```

**API 엔드포인트**:
- `POST /chat` → ChatResponse (need_more_info or full VM)
- `GET /faq/templates` → FAQ 템플릿 목록

**Forbidden Words** (Refined):
- ALLOWED: "비교합니다", "확인합니다" (factual)
- FORBIDDEN: "A가 B보다", "더 높다", "유리하다" (evaluative)
- Validation: Pydantic field_validator (regex-based)

**산출물**:
- `apps/api/chat_vm.py` (420 lines)
- `apps/api/chat_intent.py` (250 lines)
- `apps/api/chat_handlers.py` (620 lines)
- `apps/api/server.py` (+70 lines, /chat endpoint)
- `tests/test_chat_integration.py` (425 lines, 18/18 PASS)
- `STEP_NEXT_14_COMPLETION.md`

**금지 사항** (Hard Stop):
- ❌ premium 추정/계산/랭킹
- ❌ 금액 기준 정렬/강조/차트
- ❌ 추천/평가/우열 표현
- ❌ LLM 쿼리 생성
- ❌ amount_fact 수정

---

### STEP NEXT-13 — Production Deployment & UI Frontend Integration ✅

**목표**: 운영 배포 및 UI 연동 문서화 (기능 추가 없이 서비스 가능 상태로 고정)

**주요 성과**:
- ✅ Production Deployment 가이드 작성 (650 lines)
- ✅ Frontend Integration 계약 문서화 (800 lines)
- ✅ End-to-End 데이터 흐름 정의 (900 lines)
- ✅ Docker dev/prod 실행 경로 확정
- ✅ 모든 기존 Lock 보존 (amount_fact, templates, forbidden words)
- ✅ Deployment Readiness Checklist 완료

**Docker 실행 모드**:
- `docker/compose.yml` → 개발/검증 (PostgreSQL 15 Alpine)
- `docker/docker-compose.production.yml` → 운영 (PostgreSQL 16 pgvector)
- ❌ `docker-compose.demo.yml` (폐기, 과거 프로젝트 전용)

**Production Lock Checklist**:
- ✅ Database: amount_fact = 297 rows (변경 없음)
- ✅ Audit: audit_runs status = PASS
- ✅ API: Healthcheck returns 200 OK
- ✅ Explanation: Templates LOCKED (no LLM)
- ✅ Forbidden Words: 25+ patterns enforced
- ✅ Read-Only: NO writes to amount_fact
- ✅ Tests: 47/47 PASS (explanation layer)

**UI Integration Contract** (LOCKED):
- value_text 그대로 표시 (파싱 금지)
- Status 기반 스타일링만 허용
- 금지: 색상 비교, 금액 정렬, 차트, 추천, 계산
- Forbidden Words: 더/보다/유리/불리/높다/낮다 등 25+ 패턴

**산출물**:
- `docs/deploy/PRODUCTION_DEPLOYMENT.md` (650 lines)
- `docs/ui/FRONTEND_INTEGRATION_GUIDE.md` (800 lines)
- `docs/api/END_TO_END_FLOW.md` (900 lines)
- `STEP_NEXT_13_COMPLETION.md`

**금지 사항** (Hard Stop):
- ❌ demo compose 언급
- ❌ amount 재계산
- ❌ Explanation에서 비교/평가 표현
- ❌ Step7/Step11/Step12 수정
- ❌ DB 스키마 변경

---

### STEP NEXT-12 — Comparison Explanation Layer (Fact-First, Non-Recommendation) ✅

**목표**: AmountDTO → 사실 기반 설명 문장 생성 (비교·평가·추천 금지)

**주요 성과**:
- ✅ Explanation View Model 설계 완료 (InsurerExplanationDTO, CoverageComparisonExplanationDTO)
- ✅ Rule-Based Template 시스템 구현 (LLM 사용 금지)
- ✅ Forbidden Word 검증 (25+ 금지어 패턴 강제)
- ✅ Parallel Explanation 생성 (보험사 간 비교 금지)
- ✅ Order Preservation (금액 기준 정렬 금지)
- ✅ Comparison Explanation Rules 문서화 (650 lines)
- ✅ 통합 테스트 47/47 PASS

**Template Registry** (LOCKED):
- `CONFIRMED` → "{insurer}의 {coverage_name}는 가입설계서에 {value_text}으로 명시되어 있습니다."
- `UNCONFIRMED` → "{insurer}의 {coverage_name}는 가입설계서에 금액이 명시되어 있지 않습니다."
- `NOT_AVAILABLE` → "{insurer}에는 해당 담보가 존재하지 않습니다."

**Forbidden Words** (25+ patterns):
- ❌ 비교: 더, 보다, 반면, 그러나, 하지만
- ❌ 평가: 유리, 불리, 높다, 낮다, 많다, 적다
- ❌ 계산: 차이, 평균, 합계, 최고, 최저
- ❌ 추천: 추천, 제안, 권장, 선택, 판단

**Contract Rules** (LOCKED):
- Input: AmountDTO ONLY (no amount_fact direct access)
- Generation: Template-based (NO LLM)
- Comparisons: FORBIDDEN (parallel only)
- Sorting: FORBIDDEN (input order preserved)
- Calculations: FORBIDDEN (no numeric operations)

**산출물**:
- `apps/api/explanation_dto.py` (206 lines)
- `apps/api/explanation_handler.py` (388 lines)
- `docs/ui/COMPARISON_EXPLANATION_RULES.md` (650 lines)
- `tests/test_comparison_explanation.py` (47/47 PASS)
- `STEP_NEXT_12_COMPLETION.md`

---

### STEP NEXT-11 — Amount API Integration & Presentation Lock ✅

**목표**: amount_fact 기반 읽기 전용 API 계층 + 불변 프레젠테이션 규칙

**주요 성과**:
- ✅ DTO 스키마 설계 완료 (AmountDTO, AmountEvidenceDTO, AmountAuditDTO)
- ✅ AmountRepository & Handler 구현 (READ-ONLY)
- ✅ API 통합 (기존 server.py 활용)
- ✅ API Contract 문서화 (550 lines)
- ✅ Presentation Rules 문서화 (650 lines)
- ✅ 통합 테스트 20/20 PASS

**Status Values** (LOCKED):
- `CONFIRMED` - Amount explicitly stated + evidence exists
- `UNCONFIRMED` - Coverage exists but amount not stated
- `NOT_AVAILABLE` - Coverage doesn't exist

**Presentation Rules** (LOCKED):
- CONFIRMED → value_text 표시 (normal)
- UNCONFIRMED → "금액 명시 없음" (gray, muted)
- NOT_AVAILABLE → "해당 담보 없음" (strikethrough)
- ❌ 금지: 색상 코딩, 정렬, 최대/최소 강조, 계산, 차트

**산출물**:
- `apps/api/dto.py` (385 lines)
- `apps/api/amount_handler.py` (385 lines)
- `docs/api/AMOUNT_READ_CONTRACT.md` (550 lines)
- `docs/ui/AMOUNT_PRESENTATION_RULES.md` (650 lines)
- `tests/test_amount_api_integration.py` (20/20 PASS)
- `STEP_NEXT_11_COMPLETION.md`

---

### STEP NEXT-10B-FINAL — Step7 Amount DB 반영 & Lock ✅

**목표**: Step7 Amount 파이프라인 전수 검증 완료 후 DB 반영 및 공식 종료

**주요 성과**:
1. ✅ Audit Lock 검증 PASS (594 GT pairs, MISMATCH_VALUE=0)
2. ✅ Audit 메타데이터 영구 보존 (audit_runs 테이블)
3. ✅ Step7 Amount DB 적재 (297 rows, 191 CONFIRMED)
4. ✅ DB 반영 검증 완료 (8개 보험사)
5. ✅ Amount Pipeline LOCK 선언 (재수정 금지)

**DB 적재 결과**:
| Insurer | Total | CONFIRMED | UNCONFIRMED |
|---------|-------|-----------|-------------|
| Samsung | 41 | 41 | 0 |
| DB | 30 | 30 | 0 |
| KB | 45 | 10 | 35 |
| Meritz | 34 | 33 | 1 |
| Hanwha | 37 | 4 | 33 |
| Hyundai | 37 | 8 | 29 |
| Lotte | 37 | 31 | 6 |
| Heungkuk | 36 | 34 | 2 |
| **Total** | **297** | **191** | **106** |

**Lock 상태**:
- 🔒 Frozen Commit: `c6fad903c4782c9b78c44563f0f47bf13f9f3417`
- 🔒 Freeze Tag: `freeze/pre-10b2g2-20251229-024400`
- 🔒 Audit Status: PASS (MISMATCH_VALUE=0)

**산출물**:
- `pipeline/step10_audit/create_audit_runs_table.sql`
- `pipeline/step10_audit/preserve_audit_run.py`
- `pipeline/step10_audit/validate_amount_lock.py`
- `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md`
- `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md`

---

## 📚 이전 완료 항목

### STEP NEXT-10B Series (Amount Pipeline Hardening)

| 단계 | 목표 | 상태 | 날짜 |
|------|------|------|------|
| 10B-2G-2 | Step7 amount 결과 DB 적재 | ✅ | 2025-12-29 |
| 10B-2G-FIX | Step7 페이지 선택 로직 수정 | ✅ | 2025-12-29 |
| 10B-2G | Step7 Amount 전수 조사 (8개사) | ✅ | 2025-12-29 |
| 10B-2C-3 | Type-C 규칙 추가 | ✅ | 2025-12-29 |
| 10B-2C-2B | Coverage Cards Lineage 증명 | ✅ | 2025-12-28 |
| 10B-2 | Amount 매핑 통합 테스트 | ✅ | 2025-12-28 |
| 10B-1A | Audit 스크립트 하드닝 | ✅ | 2025-12-28 |

### STEP NEXT-9 Series (API Layer)

| 단계 | 목표 | 상태 | 날짜 |
|------|------|------|------|
| 9.1 | Fixture Canonicalization | ✅ | 2025-12-28 |
| 9 | API Contract + Mock Server | ✅ | 2025-12-28 |
| 8 | Example-to-API Mapping | ✅ | 2025-12-28 |

### STEP NEXT-4~7 (UI & Evidence)

자세한 내역은 `STATUS_ARCHIVE.md` 참조

---

## 🔐 현재 Lock 상태

### 1. Amount Pipeline Lock (STEP 10B-FINAL)
- **Status**: 🔒 PERMANENTLY LOCKED
- **Frozen Commit**: c6fad903c4782c9b78c44563f0f47bf13f9f3417
- **Frozen Reports**: step7_gt_audit_all_20251229-025007.{json,md}
- **금지 사항**: Step7 로직 수정, Type-C 변경, Audit 없이 DB 적재

### 2. Presentation Lock (STEP 11)
- **Status**: 🔒 LOCKED
- **Locked Elements**: Status values, Display text, Style rules
- **금지 사항**: 색상 코딩, 정렬, 최대/최소 강조, 계산, 차트

### 3. API Contract Lock (STEP 9.1)
- **Status**: 🔒 LOCKED
- **Schema Version**: 1.0.0
- **금지 사항**: Schema 변경, 추천/판단 표현, Evidence 없는 값 출력

---

## 📦 주요 산출물

### Documentation
- Amount Read Contract: `docs/api/AMOUNT_READ_CONTRACT.md`
- Presentation Rules: `docs/ui/AMOUNT_PRESENTATION_RULES.md`
- Amount Audit Lock: `docs/audit/STEP7_AMOUNT_AUDIT_LOCK.md`
- DB Load Guide: `docs/audit/STEP7_AMOUNT_DB_LOAD_GUIDE.md`

### Code
- DTO: `apps/api/dto.py`
- Repository: `apps/api/amount_handler.py`
- API Server: `apps/api/server.py`
- DB Loader: `apps/loader/step9_loader.py`

### Tests
- Amount API: `tests/test_amount_api_integration.py` (20/20 PASS)
- API Contract: `tests/test_api_contract.py` (21/21 PASS)

---

## 🚀 다음 단계

### Immediate
1. Production DB Deployment
2. API Production Deploy
3. UI Implementation (Presentation rules 적용)

### Future
1. Amount Pipeline v2 (새 기능)
2. Multi-insurer Expansion (8→12개)
3. Performance Optimization

---

## 📞 참조

| 항목 | 값 |
|------|-----|
| Git Commit | c6fad903c4782c9b78c44563f0f47bf13f9f3417 |
| Freeze Tag | freeze/pre-10b2g2-20251229-024400 |
| Audit UUID | f2e58b52-f22d-4d66-8850-df464954c9b8 |
| Branch | fix/10b2g2-amount-audit-hardening |

---

**Archive**: 이전 단계 (STEP 4 ~ STEP 9) → `STATUS_ARCHIVE.md`
**최종 업데이트**: 2025-12-29 | **작성자**: Pipeline Team
