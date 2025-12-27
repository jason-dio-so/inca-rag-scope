# STEP 13.5 - Cancer Canonical Excel Operation Rules

## Canonical 판단 단위 (LOCK)

암 담보는 **"질병명"이 아니라 "지급 이벤트"로 Canonical을 정의**한다.

## Canonical Event Axis (5개)

| Axis | 지급 트리거 | Code Pattern |
|---|---|---|
| 1. Diagnosis | 암 진단 시 1회 지급 | A4200_x |
| 2. Re-diagnosis | 재진단/재발/전이 시 지급 | A4200_Rx |
| 3. Treatment | 항암/표적/방사선 등 치료 행위 | A4200_Tx |
| 4. Surgery | 암 수술 (다빈치/로봇 포함) | A4200_Sx |
| 5. Hospitalization | 암 관련 입원 일당 | A4200_Hx |

## Excel 행 판단 규칙 (기계적)

### Rule 1. Diagnosis (A4200 계열)

**포함 키워드**:
- 암진단비, 암 진단, 진단확정

**제외 키워드**:
- 재진단, 치료, 수술, 입원

**지급 조건**:
- 최초 1회, 진단 확정 시

**➡️ A4200_x**

### Rule 2. Re-diagnosis

**포함 키워드**:
- 재진단, 재발, 전이, 계속받는암

**➡️ A4200_Rx (신규 또는 파생 코드)**

### Rule 3. Treatment

**포함 키워드**:
- 항암, 표적, 방사선, 약물치료

**진단 조건**: ❌

**➡️ A4200_Tx**

### Rule 4. Surgery

**포함 키워드**:
- 수술비, 다빈치, 로봇

**지급 트리거**: 수술 행위

**➡️ A4200_Sx**

### Rule 5. Hospitalization

**포함 키워드**:
- 입원, 입원일당

**➡️ A4200_Hx**

## Excel 컬럼 운영 규칙 (고정)

| Excel Column | 규칙 |
|---|---|
| `canonical_name` | 지급 이벤트 기준 명칭 사용 |
| `coverage_code` | Event Axis + suffix |
| `{insurer}_alias` | 원문 담보명 그대로 |
| `notes` | 판단 근거 키워드 1줄 |

## Excel 추가 판단 체크리스트 (행 단위)

각 신규 행마다 아래 질문에 **YES 하나만 허용**:

1. ☐ 지급 트리거가 **진단**인가?
2. ☐ 지급 트리거가 **재진단/재발**인가?
3. ☐ 지급 트리거가 **치료 행위**인가?
4. ☐ 지급 트리거가 **수술 행위**인가?
5. ☐ 지급 트리거가 **입원**인가?

**규칙**:
- 복수 YES ❌
- 애매하면 분리된 Canonical로 생성

## Event Axis 적용 예시

| 담보명 (raw) | Event Axis | Coverage Code | 판단 근거 |
|---|---|---|---|
| 암진단비(유사암제외) | Diagnosis | A4200_1 | 진단 확정 시 지급 |
| 암(4대특정암제외)진단비 | Diagnosis | A4200_2 | 진단 확정 시 지급 (조건 다름) |
| 신재진단암진단비 | Re-diagnosis | A4200_3 | 재진단 시 지급 |
| 항암방사선약물치료비 | Treatment | A9617_1 | 치료 행위 시 지급 |
| 암수술비(유사암제외) | Surgery | A5200 | 수술 행위 시 지급 |
| 암직접치료입원일당 | Hospitalization | A6200 | 입원 일당 지급 |

## Diagnosis 하위 분류 (A4200 내)

| 담보명 | Coverage Code | 분리 근거 |
|---|---|---|
| 암진단비(유사암제외) | A4200_1 | 기본 암 진단 |
| 암(4대특정암제외)진단비 | A4200_2 | 특정암 제외 조건 |
| 신재진단암진단비 | A4200_3 | 재진단 (Event Axis 다름) |
| 유사암진단비 | A4210 | 유사암 별도 분류 |
| 4대특정암진단비 | A4209 | 특정암 별도 분류 |

## 운영 절차 (사람 수행)

1. **Step 1**: 담보명 원문에서 지급 트리거 키워드 확인
2. **Step 2**: Event Axis 5개 중 하나만 선택
3. **Step 3**: 동일 Axis 내 기존 Canonical 존재 여부 확인
4. **Step 4**: 기존 있으면 alias 추가, 없으면 신규 row 생성
5. **Step 5**: Coverage Code에 Event Axis pattern 적용

## DO NOT (금지 사항)

- ❌ 질병코드 (ICD/KCD) 참조
- ❌ LLM / embedding / vector 유사도
- ❌ 매칭률 기준 Canonical 설계
- ❌ 복수 Event Axis 허용
- ❌ Suffix 무한 증식 (최대 _9)

## Policy Lock

본 문서는 Excel 행 추가/수정의 **유일한 운영 기준**이다.

- 사람이 Excel을 수정해도 결과 동일
- STEP 12 재실행 시 매칭률 상승 논리적으로 보장
- 질병코드 없이도 확장 가능
