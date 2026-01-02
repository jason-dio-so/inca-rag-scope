AGENTS.md

Purpose

이 문서는 inca-rag-scope 프로젝트에서 AI(Claude/ChatGPT 포함)가 반드시 따라야 할 행동 규칙을 정의한다.
본 문서는 코드와 동일한 효력을 가지는 행동 헌법이다.

Absolute Rules (위반 불가)
	1.	Step1~Step2의 기존 산출물과 로직은 명시적 지시 없이는 수정 금지
	2.	Canonical Source는 담보명mapping자료.xlsx 단일 출처만 허용
	3.	임기응변식 로직, 보험사별 if-else 하드코딩 금지
	4.	SSOT는 data/scope_v3/ ONLY
	5.	불확실하면 추정하지 말고 멈추고 보고
	6.	고객 의사결정 영역(Excel 수정 등)에 AI가 개입 금지

Allowed
	•	정규화 규칙의 일반화된 추가
	•	Gate / 검증 / 리포트 생성
	•	구조 문서화

Forbidden
	•	Step 경계 붕괴
	•	결과를 바꾸는 무단 재실행
	•	LLM 기반 Canonical 생성

## STEP NEXT-61 vs 61A Decision

- STEP NEXT-61: ACTIVE (Evidence-based comparison pipeline, Step3–7)
- STEP NEXT-61A: DEFERRED (Amount-first / NEW-RUN architecture)

Rationale:
Step1/Step2 are LOCKED and production-stable.
Current customer value is delivered via Step3–7 evidence comparison.
Structural refactors are postponed to v2.