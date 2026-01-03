# 보험 상품 비교 도우미 — 웹 UI 테스트 가이드

**STEP NEXT-97 적용**: Customer Demo UX Stabilization

## 1. 백엔드 API 서버 실행

터미널 1에서:
```bash
cd /Users/cheollee/inca-rag-scope
python -m uvicorn apps.api.main:app --reload --port 8000
```

## 2. 프론트엔드 개발 서버 실행

터미널 2에서:
```bash
cd /Users/cheollee/inca-rag-scope/apps/web
npm run dev
```

## 3. 브라우저 접속

http://localhost:3000

---

## STEP NEXT-97: 새로운 UX Flow

### 초기 화면
- **좌측**: 카테고리 패널 접힘 (12px, 토글 버튼만 표시)
- **중앙**: 질문 중심 UX (예제 버튼 4개)
- **하단**: 보험사 선택 영역 활성화

### 질문 실행 후
- **좌측**: 카테고리 패널 접힘 유지 (확장 가능)
- **중앙**: 대화 말풍선 (사용자 질문 + AI 응답)
- **우측**: 결과 상세 도크 (자동 표시)
- **하단**: 보험사 선택 비활성화 + "현재 대화 조건" 표시

### 조건 변경 시
- "조건 변경" 버튼 클릭 → 확인 → 페이지 초기화
- 새로운 보험사 선택 가능

## 4. EX2_DETAIL 테스트 버튼

화면 중앙에 4개의 테스트 버튼이 표시됩니다:

### 🟣 예제2: 담보 설명 (EX2_DETAIL)
- **버튼**: "삼성화재 암진단비 상세 안내"
- **테스트 내용**:
  - ✅ 4-section bubble_markdown 출력
  - ✅ 핵심 요약 / 보장 요약 / 조건 요약 / 근거 안내
  - ✅ coverage_code 노출 0% (A4200_1 등 내부 코드 없음)
  - ✅ refs만 표시 (PD:/EV: prefix)
  - ✅ "표현 없음" / "근거 없음" 사용
  - ❌ 비교/추천/판단 문구 없음

### 🟣 예제2-B: 뇌출혈 설명 (EX2_DETAIL)
- **버튼**: "한화손보 뇌출혈진단비 상세 안내"
- **테스트 내용**:
  - 다른 담보로 동일한 EX2_DETAIL 패턴 검증

### 🔵 예제3: 2사 비교 (EX3_COMPARE)
- **버튼**: "삼성화재 vs 메리츠화재 암진단비"
- **비교**: EX2_DETAIL vs EX3_COMPARE 출력 차이 확인

### 🟢 예제4: 보장 여부 확인 (EX4_ELIGIBILITY)
- **버튼**: "제자리암 보장 가능 여부 + 종합평가"
- **비교**: EX2_DETAIL vs EX4_ELIGIBILITY 출력 차이 확인

## 5. 검증 체크리스트

### STEP NEXT-97: UX Flow 검증
- [ ] **초기 화면**: 좌측 패널 접힘 (12px)
- [ ] **토글 버튼**: 클릭 시 패널 확장/축소
- [ ] **질문 후**: 새 말풍선 자동 스크롤 (bottom 기준 100px 이내)
- [ ] **스크롤 방해 없음**: 과거 내용 보는 중 강제 이동 없음
- [ ] **보험사 선택 비활성화**: 질문 후 selector disabled
- [ ] **조건 표시**: "현재 대화 조건: 삼성화재 · 메리츠화재" 표시
- [ ] **조건 변경 버튼**: 클릭 → confirm → 페이지 초기화

### 버튼 클릭 시
1. ✅ 왼쪽 채팅 영역: bubble_markdown 표시 (4개 섹션)
2. ✅ 오른쪽 결과 도크: 상세 sections 표시
3. ✅ 자동 스크롤로 최신 말풍선 표시

### bubble_markdown 검증 (왼쪽 채팅 버블)
- [ ] "## 핵심 요약" 섹션 있음
- [ ] "## 보장 요약" 섹션 있음 (STEP NEXT-96: 보장금액 우선 표시)
- [ ] "## 조건 요약" 섹션 있음
- [ ] "## 근거 자료" 섹션 있음
- [ ] "A4200_1" 같은 coverage_code 노출 없음
- [ ] 근거 링크가 "[근거 보기](PD:samsung:...)" 형태
- [ ] "표현 없음" 또는 "근거 없음" 문구 사용
- [ ] "Unknown" 문구 없음

### sections 검증 (오른쪽 결과 도크)
- [ ] "보장 요약" 카드 표시 (limit_summary, payment_type)
- [ ] "조건 요약" 카드 표시 (감액, 대기기간, 면책, 갱신)
- [ ] "근거 자료" 아코디언 표시 (클릭 시 확장)

### EX2 vs EX3 비교
- [ ] EX2: 단일 보험사만, 설명 위주
- [ ] EX3: 2개 보험사, 비교 테이블
- [ ] EX4: 담보 군집화 (STEP NEXT-94: 진단/치료/기타)

### EX2 vs EX4 비교
- [ ] EX2: 담보 설명, KPI 요약
- [ ] EX4: O/X/△ 매트릭스, 종합평가, 담보 군집화

## 6. 문제 발생 시 디버깅

### Backend 로그 확인
```bash
# 터미널 1에서 API 서버 로그 확인
# composer, handler 실행 로그 출력됨
```

### Frontend 콘솔 확인
```bash
# 브라우저 개발자 도구 → Console
# Request payload 확인:
# - kind: "EX2_DETAIL"
# - insurers: ["samsung"]
# - coverage_names: ["암진단비(유사암제외)"]
```

### Response 검증
```bash
# 브라우저 개발자 도구 → Network → /chat
# Response:
# - message.kind: "EX2_DETAIL"
# - message.bubble_markdown: (4-section markdown)
# - message.sections: [보장요약, 조건요약, 근거자료]
```

## 7. 스크린샷 촬영 포인트

1. **초기 화면**: 4개 버튼 보이는 화면
2. **EX2 실행 후**: 왼쪽 bubble + 오른쪽 sections
3. **bubble 확대**: 4개 섹션 모두 보이도록
4. **근거 클릭**: 근거 자료 아코디언 확장 상태
5. **EX3와 비교**: EX2 vs EX3 화면 나란히

## 8. 성공 기준

- ✅ 버튼 클릭 시 에러 없이 응답
- ✅ bubble_markdown 4개 섹션 모두 렌더링
- ✅ coverage_code 노출 0%
- ✅ refs 클릭 가능 (링크 형태)
- ✅ EX3/EX4와 명확한 차이 (설명 vs 비교 vs 판단)

---

**준비 완료!** 터미널 2개 띄우고 서버 실행 → 브라우저 접속 → 버튼 클릭 → 검증
