# STEP 6-δ.1 — KB 사업방법서 Snippet 품질 개선

**Date**: 2025-12-27
**Coverage**: A4200_1 (암진단비(유사암제외)) ONLY
**Insurer**: KB ONLY
**Doc Type**: 사업방법서 ONLY

---

## 목적

STEP 6-δ에서 KB 사업방법서 hit=1은 달성했으나, snippet이 A4200_1(암진단비·유사암제외) 근거 구간이 아닌 무관한 구간("보험료납입지원유사암진단")을 추출했다. 본 STEP은 snippet 선택 로직만 개선하여 A4200_1 근거 구간을 정확히 가리키도록 한다.

---

## 문제 정의

**STEP 6-δ snippet (BEFORE)**:
```
선택계약
 3)
구 분
보험기간
납입기간
가입나이
보험료납입지원유사암진단

(
)주2-1)
```

- "암진단비" 미포함
- "유사암제외" 미포함
- A4200_1 근거 구간이 아님

---

## 변경 규칙 (KB 전용)

### Snippet 후보 필수 토큰 (ALL REQUIRED)
1. "암진단비" 포함
2. "유사암" 포함
3. ("제외" 또는 "유사암제외") 포함

### 후보 점수화
```
score = (암진단비?1:0) + (유사암?1:0) + (제외/유사암제외?1:0) + (보험금/지급?1:0)
```
- score < 3: 폐기
- score 최대값 우선 선택

### Snippet 추출
- 선택된 라인 기준 위아래 4줄 (총 9줄)
- 원문 그대로 (요약 없음)
- 최대 1 snippet

---

## 구현

**변경 파일**: `pipeline/step4_evidence_search/search_evidence.py`

**변경 내용**: `_kb_bm_a4200_1_definition_hit()` 함수 로직 교체 (search_evidence.py:302-369)

**Before 로직**:
- 슬라이딩 윈도우 (10줄)
- 그룹별 키워드 2개 이상 hit 시 즉시 반환

**After 로직**:
- 라인별 필수 토큰 체크 (ALL REQUIRED)
- score >= 3인 후보만 수집
- 최고 점수 후보 선택

---

## Before / After

### KB A4200_1 사업방법서 Evidence

| Status | Page | Snippet Preview |
|--------|------|----------------|
| BEFORE | 3 | "보험료납입지원유사암진단..." (근거 무관) |
| AFTER | 5 | "암진단비유사암제외()" (근거 명확) |

### Token Verification (AFTER)
```
암진단비: True
유사암: True
제외/유사암제외: True
ALL REQUIRED: True
```

### Full Snippet (AFTER)
```
Ⅱ
부정맥질환
진단비
(I49)
암진단비유사암제외
(
)
유사암진단비
중증갑상선암진단비
```

---

## Validation

### KB A4200_1 Doc-Type Hits
| 약관 | 사업방법서 | 상품요약서 |
|------|-----------|----------|
| 3 | 1 | 0 |

✅ No change from STEP 6-δ

### Regression (Other 7 Insurers)
| Insurer | 약관 | 사업방법서 | 상품요약서 |
|---------|------|-----------|----------|
| samsung | 3 | 3 | 3 |
| meritz | 3 | 0 | 3 |
| db | 3 | 3 | 3 |
| hanwha | 3 | 3 | 3 |
| lotte | 3 | 3 | 3 |
| hyundai | 3 | 3 | 3 |
| heungkuk | 3 | 3 | 3 |

✅ No changes

### pytest
```
75 passed in 0.44s
```
✅ All tests pass

---

## 산출물

1. **Code**: `pipeline/step4_evidence_search/search_evidence.py` (snippet 선택 로직 개선)
2. **Evidence Pack**: ~~`data/evidence_pack/kb_evidence_pack.jsonl`~~ (REMOVED - integrated into coverage_cards)
3. **Coverage Cards**: `data/compare/kb_coverage_cards.jsonl` (✅ SSOT)
4. **Report**: ~~`reports/a4200_1_8insurers.md`~~ (REMOVED)

---

## DoD Checklist

- ✅ KB/A4200_1/사업방법서 hit = 1 (유지)
- ✅ snippet에 "암진단비" + "유사암" + "제외" 모두 포함
- ✅ 다른 7개 보험사 변화 0
- ✅ pytest 100% PASS
- ✅ A4200_1 근거 구간 정확히 추출

---

## 결론

KB 사업방법서 snippet이 A4200_1(암진단비·유사암제외) 근거 구간을 정확히 가리키도록 개선되었다. 필수 토큰 검증 및 점수화 로직으로 snippet 품질이 보장되며, 다른 보험사 및 담보에는 영향이 없음이 검증되었다.
