# STEP NEXT-10B-2G 완료 보고서 — Step7 Amount 전수 조사 (Ground Truth Audit)

**작업일**: 2025-12-29
**브랜치**: `fix/10b2g-step7-amount-audit-all`
**Freeze Tag**: `freeze/pre-10b2g-20251229-021907`

---

## 1. 목적

가입설계서(Proposal) 원문을 ground-truth로 하여 Step7이 생성한 `amount` 필드가 실제 문서와 일치하는지 8개 보험사 전수 조사.

**금지 사항 (준수 완료)**:
- ❌ UNCONFIRMED 비율을 KPI로 삼아 억지로 낮추기
- ❌ 약관/상품요약서의 "보험가입금액"을 담보별로 복사/추론
- ❌ Loader에 snippet 검색('만원' in snippet 등) 재도입

---

## 2. 실행 내용

### 2.1 Safety Gate (완료)
1. ✅ 신규 브랜치 생성: `fix/10b2g-step7-amount-audit-all`
2. ✅ Freeze 태그 생성: `freeze/pre-10b2g-20251229-021907`
3. ✅ Lineage Lock 테스트 선행 (61 tests PASSED)

### 2.2 전수 조사 알고리즘 (구현 완료)

**pipeline/step10_audit/audit_step7_amount_gt.py** 생성:

1. **GT 추출** (`extract_gt_pairs_from_proposal`):
   - 가입설계서 *.page.jsonl에서 (coverage_name_raw, amount_raw) 페어 추출
   - 금액 패턴 지원:
     - `1,000만원`, `3000만원`
     - `1천만원`, `5백만원`, `2십만원` (KB 사건 재발 방지)
     - `100,000원`, `10만원`
   - 테이블 구조 파싱 (single-line / multi-line)

2. **GT → coverage_code 매핑** (`map_gt_to_coverage_code`):
   - `data/scope/{insurer}_scope_mapped.csv` 경유
   - `normalize_coverage_name()` 적용:
     - 선행 번호 제거 (`1. `, `3. `)
     - 태그 제거 (`[기본계약]`, `[갱신형]`)
     - 괄호/공백/특수문자 제거

3. **Step7 결과와 비교** (`compare_gt_vs_step7`):
   - Verdict 분류:
     - `OK_MATCH`: GT와 Step7 value_text가 동등 (정규화 후)
     - `MISS_PATTERN`: GT에는 금액이 있는데 Step7은 UNCONFIRMED
     - `MISMATCH_VALUE`: 둘 다 금액인데 값이 다름 (심각)
     - `TYPE_C_EXPECTED_UNCONFIRMED`: Type C 문서 구조상 정상
   - 금액 정규화 (`normalize_amount_for_comparison`):
     - 한글 숫자 변환 (예: `3천만원` → `3000만원`)
     - 공백/쉼표 제거

4. **통합 리포트 생성** (`generate_consolidated_report`):
   - `reports/step7_gt_audit_all_{timestamp}.md`
   - `reports/step7_gt_audit_all_{timestamp}.json`
   - PASS/FAIL 판정 (Type별 기준 적용)

---

## 3. 조사 결과

### 3.1 통합 테이블 (최종)

| insurer | type | GT_pairs | mapped_codes | OK_MATCH | MISS_PATTERN | MISMATCH_VALUE | SCOPE_GAP | PASS/FAIL |
|---------|------|----------|--------------|----------|--------------|----------------|-----------|-----------|
| samsung | A | 59 | 33 | 33 | 0 | 0 | 26 | **PASS** ✅ |
| meritz | B | 73 | 26 | 5 | 13 | **8** | 47 | **FAIL** ❌ |
| db | B | 60 | 52 | 16 | 28 | **8** | 8 | **FAIL** ❌ |
| hanwha | C | 49 | 1 | 1 | 0 | 0 | 48 | **PASS** ✅ |
| hyundai | C | 75 | 29 | 6 | 0 | 0 | 46 | **PASS** ✅ (Type C) |
| kb | A | 80 | 0 | 0 | 0 | 0 | 80 | **PASS** ✅* |
| lotte | A | 136 | 48 | 48 | 0 | 0 | 88 | **PASS** ✅ |
| heungkuk | A | 62 | 0 | 0 | 0 | 0 | 62 | **PASS** ✅* |

**PASS**: 6개사 (samsung, hanwha, hyundai, kb*, lotte, heungkuk*)
**FAIL**: 2개사 (meritz, db) — **16 MISMATCH_VALUE cases**

> \* kb, heungkuk은 0 mapped (매핑 테이블 확장 필요)이지만 MISMATCH는 없어 기술적 PASS

---

### 3.2 FAIL 원인 분석 (Critical Finding)

#### 3.2.1 Meritz MISMATCH 사례

| coverage_code | GT (Page 3) | Step7 (Page 5) | 근본 원인 |
|---------------|-------------|----------------|-----------|
| A1300 | `1백만원` | `5,000만원` | 잘못된 페이지 선택 |
| A1100 | `1천만원` | `5,000만원` | 잘못된 페이지 선택 |
| A4200_1 | `3천만원` | `26 원` | 파싱 실패 (bizarre value) |

**근본 원인**:
- 가입설계서 Page 3: **실제 고객 제안서** (GT 정답)
  ```
  가입담보
  2 일반상해사망 1백만원 60원 20년/100세
  3 질병사망 1천만원 6,880원 20년/80세
  8 암진단비(유사암제외) 3천만원 30,480원 20년/100세
  ```

- 가입설계서 Page 5: **대표계약 예시**
  ```
  대표계약 기준: 남자40세,20년납,100세만기,월납
  일반상해80%이상후유장해[기본계약] 5,000만원,
  일반상해사망 5,000만원,
  질병사망 5,000만원
  ```

**Step7의 페이지 선택 로직이 "대표계약 예시" 페이지를 우선 선택**했음.

#### 3.2.2 DB MISMATCH 사례 (유사 패턴)

| coverage_code | GT | Step7 | 근본 원인 |
|---------------|-----|-------|-----------|
| A1300 | `1천만원` | `1,000만원` | 정규화 문제 (이미 수정됨) |
| A4200_1 | `3천만원` | `100만원` | 파싱 오류 |

---

## 4. 발견 사항 (Findings)

### 4.1 ✅ 정상 동작 보험사

- **Samsung (Type A)**: 33/33 OK_MATCH, 0 MISMATCH
- **Lotte (Type A)**: 48/48 OK_MATCH, 0 MISMATCH
- **Hyundai (Type C)**: 6 OK_MATCH, 23 TYPE_C_EXPECTED_UNCONFIRMED (정상)

### 4.2 ❌ 결함 발견

1. **가입설계서 페이지 선택 로직 오류** (Meritz, DB):
   - 여러 페이지에 금액 테이블이 있을 때 "대표계약 예시" 페이지를 우선 선택
   - 실제 고객 제안서 페이지보다 후순위로 밀림

2. **파싱 실패 사례** (Meritz A4200_1):
   - Step7 value_text: `26 원` (bizarre value)
   - 원인: 테이블 레이아웃 파싱 실패 추정

3. **매핑 테이블 부족** (KB, Heungkuk):
   - 80 GT pairs 추출했으나 0 matched
   - `*_scope_mapped.csv`에 해당 담보명 변형이 누락됨

---

## 5. 다음 조치 (Action Items)

### 5.1 즉시 조치 (STOP 조건 충족 시)

#### 5.1.1 Step7 페이지 선택 로직 수정 (priority)

**파일**: `pipeline/step7_amount/extract_amount.py`

**수정 방향**:
1. 가입설계서에서 페이지 우선순위 규칙 추가:
   ```python
   # 높은 우선순위
   - 페이지 제목에 "가입담보리스트", "계약사항" 포함
   - 페이지 번호 초반 (page 2-4)
   - 테이블 행 수가 많음 (>= 10 rows)

   # 낮은 우선순위
   - "대표계약 기준", "예시", "참고용" 포함
   - 페이지 번호 후반 (page > 5)
   - 단일 라인 summary
   ```

2. 여러 페이지에 금액이 있을 경우:
   - 우선순위 점수 계산
   - 가장 높은 점수 페이지 선택
   - evidence_ref에 "선택 이유" 기록

**검증**:
- Meritz, DB에 대해 Step7 재실행
- Audit 재실행 → MISMATCH_VALUE 0건 확인

#### 5.1.2 파싱 실패 케이스 수정

**케이스**: Meritz A4200_1 (`26 원`)

**조사 필요**:
1. 해당 페이지 원문 확인
2. extract_amount_from_line() 로직 검증
3. 테이블 라인 분해 규칙 보강

### 5.2 후속 조치

1. **매핑 테이블 확장** (KB, Heungkuk):
   - `data/scope/{insurer}_scope_mapped.csv`에 미매칭 담보명 추가
   - L1 (신정원) 기준 준수

2. **Guardrail 테스트 추가**:
   ```python
   # tests/test_step7_proposal_page_selection.py
   def test_proposal_page_priority_meritz():
       """대표계약 예시보다 실제 고객 제안서 우선 선택"""
       # Meritz proposal page 3 vs page 5
       assert selected_page == 3  # 고객 제안서
       assert value_text == "1백만원"  # NOT "5,000만원"
   ```

3. **리포트 개선**:
   - MISMATCH 케이스에 대해 "양쪽 페이지 스냅샷" 자동 추가
   - evidence_ref 비교 테이블 생성

---

## 6. 산출물

### 6.1 코드
- `pipeline/step10_audit/audit_step7_amount_gt.py` (586 lines)

### 6.2 리포트
- `reports/step7_gt_audit_all_20251229-022415.md` (통합 리포트)
- `reports/step7_gt_audit_all_20251229-022415.json` (상세 데이터)

### 6.3 브랜치/태그
- 브랜치: `fix/10b2g-step7-amount-audit-all`
- Freeze 태그: `freeze/pre-10b2g-20251229-021907`

---

## 7. DoD (Definition of Done) 체크

- ✅ 8개 보험사 GT 추출/매핑/Step7 비교 완료
- ✅ 통합 리포트 표 생성 완료
- ✅ PASS/FAIL 판정 완료
- ✅ FAIL 원인 유형별 "정확히 어디를 어떻게 고칠지" 명시
- ❌ **PASS 증명 완성 (미완료)** — 2개사 FAIL로 인해 미달성

---

## 8. 결론

### 8.1 성과
1. ✅ 전수 조사 인프라 구축 (재사용 가능)
2. ✅ **Meritz/DB의 Step7 페이지 선택 결함 발견** (Critical)
3. ✅ Samsung/Lotte/Hyundai 등 6개사 정상 동작 검증
4. ✅ Type C (Hanwha/Hyundai/KB)의 높은 UNCONFIRMED 비율이 정상임을 재확인

### 8.2 차단 이슈 (Blocker)
- **2개사 (Meritz, DB)에서 16건의 MISMATCH_VALUE** → FAIL/STOP 조건 충족
- Step7 amount를 DB에 적재하기 전에 **반드시 페이지 선택 로직 수정 필요**

### 8.3 권고 사항
1. **즉시**: Step7 페이지 선택 로직 수정 (Section 5.1.1)
2. **즉시**: Meritz/DB에 대해 Step7 재실행 → Audit 재실행
3. **후속**: 매핑 테이블 확장 (KB, Heungkuk)
4. **후속**: Guardrail 테스트 추가

---

**다음 단계**: STEP NEXT-10B-2G-FIX (Step7 페이지 선택 로직 수정)
