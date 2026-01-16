# 🔒 PREMIUM LEGACY POLICY — DO NOT USE

## Status

**ACTIVE POLICY / ENFORCEMENT REQUIRED**

---

## 1. 목적 (Purpose)

본 문서는 보험료(Premium) 데이터와 관련하여
현재 운영 기준 SSOT와 레거시 자산을 명확히 분리하고,
잘못된 테이블/스키마 사용으로 인한 설계·구현 혼선 재발을 방지하기 위해 작성되었다.

---

## 2. 최종 결론 (One-Line Declaration)

**Q1 보험료 비교를 포함한 모든 Premium 기능은
DB2 SSOT(product_premium_quote_v2, coverage_premium_quote)만 사용한다.**

**premium_quote 및 관련 스키마/문서는 DEPRECATED이며 사용 금지이다.**

---

## 3. ACTIVE SSOT (사용 가능)

다음 테이블만이 공식 Premium SSOT이다.

### 3.1 Product-level Premium (Q1 SSOT)

**Table**: `product_premium_quote_v2`

**Purpose**:
- 상품 단위 보험료 (NO_REFUND / GENERAL)
- 연령(age) × 성별(sex) × 보험사 × 상품 기준

**Usage**:
- Q1 보험료 비교
- Q14 보험료 랭킹

**Rule**:
- DB-ONLY
- Evidence Mandatory
- as_of_date 기준 고정

### 3.2 Coverage-level Premium & Multiplier

**Table**: `coverage_premium_quote`

**Purpose**:
- 일반보험(GENERAL) 요율 배수 근거

**Usage**:
- Evidence Rail 전용

**Rule**:
- UI 본문 노출 금지
- 근거(evidence)로만 사용

---

## 4. DEPRECATED ASSETS (절대 사용 금지)

다음 자산은 레거시 샘플/초기 실험용이며,
운영·개발·테스트 어디에서도 사용해서는 안 된다.

### 4.1 Legacy Table

**Table**: `premium_quote`

**Status**: ❌ DEPRECATED

**Reason**:
- DB2 SSOT로 완전 대체됨
- 정책·검증·Evidence 체계 미충족

**Rule**:
- ❌ Q1/Q12/Q14에서 사용 금지
- ❌ 신규 쿼리/엔드포인트 연결 금지

### 4.2 Legacy Schema & Docs

**Files**:
- `/mnt/data/schema.sql`
- `/mnt/data/README.md`

**Status**: ❌ LEGACY SAMPLE

**Meaning**:
- 과거 premium_quote 기반 수집 예시
- 현재 SSOT와 무관

**Rule**:
- ❌ `psql -f schema.sql` 실행 금지
- ❌ 신규 환경에 적용 금지
- ❌ 설계 문서/구현 참고 금지

---

## 5. Enforcement Rules (강제 규칙)

다음 규칙은 리뷰/머지/배포 단계에서 강제 적용된다.

- ❌ `premium_quote`를 참조하는 코드 → 즉시 반려
- ❌ file-based premium(JSON/SQL) 로딩 → 즉시 반려
- ❌ 실시간 Premium API 호출을 Q1 경로에 연결 → 즉시 반려
- ❌ Evidence 없는 Premium 숫자 출력 → 즉시 반려

---

## 6. Audit & Verification Reference

**Policy Doc**: `docs/policy/PREMIUM_SSOT_POLICY.md`

**Audit Evidence**:
- `docs/audit/FINAL_Q1_Q12_Q14_DB_EVIDENCE_2025-11-26.md`
- `docs/audit/GENERAL_Q1_Q14_DB_EVIDENCE_2025-11-26.md`

**Verified Facts**:
- `product_premium_quote_v2`: ACTIVE, complete
- `coverage_premium_quote`: multiplier integrity verified (0 mismatch)
- `premium_quote`: explicitly deprecated

---

## 7. Impacted Components (Reference)

- Q1 Premium Comparison → `product_premium_quote_v2` ONLY
- Q14 Premium Ranking → `product_premium_quote_v2` ONLY
- Evidence Rail (GENERAL) → `coverage_premium_quote` ONLY

---

## 8. Revision History

| Date | Change |
|------|--------|
| 2026-01-16 | Initial creation — legacy premium assets formally deprecated |

---

## 🔥 Final Warning (Do Not Ignore)

이 문서를 본 이후에도 `premium_quote`를 사용하는 코드는
**"실수"가 아니라 "정책 위반"으로 간주된다.**
