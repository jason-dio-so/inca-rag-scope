# STEP 13.6 - Cancer Canonical Excel Row Proposals (A42 only)

## 기준
- STEP13_5_CANCER_EXCEL_OPERATION_RULES.md
- Canonical 단위 = 질병명이 아닌 지급 이벤트(Event Axis)
- 범위: 암 담보 (A42 계열) ONLY
- 목적: Excel 행 단위 Canonical 분리 설계

---

## A4200 - 암 진단 이벤트 (기존 유지)

coverage_code: A4200
canonical_name: 암진단비(유사암제외)
event_axis: DIAGNOSIS
trigger: 최초 암 진단 확정
include: 일반암
exclude: 유사암
reason: 최초 진단 시 1회 지급되는 단일 진단 이벤트이므로 Canonical 유지

---

## A4201 - 재진단 암 진단 이벤트 (신규)

coverage_code: A4201
canonical_name: 재진단암진단비
event_axis: RE_DIAGNOSIS
trigger: 재진단 확정
include: 재발암, 전이암
exclude: 최초암
reason: 최초 진단과 지급 트리거가 명확히 분리됨 (재진단 조건)

---

## A4202 - 암 치료 이벤트 (신규)

coverage_code: A4202
canonical_name: 암치료비
event_axis: TREATMENT
trigger: 항암치료 개시
include: 표적항암, 면역항암
exclude: 진단만으로 지급 불가
reason: 치료 행위 개시 자체가 지급 조건이며 진단과 분리 필요

---

## A4203 - 암 수술 이벤트 (신규)

coverage_code: A4203
canonical_name: 암수술비
event_axis: SURGERY
trigger: 암 수술 시행
include: 다빈치로봇수술, 개복수술
exclude: 치료, 입원
reason: 수술 1회당 지급 구조 → 진단/치료와 혼합 불가

---

## A4204 - 암 입원 이벤트 (신규)

coverage_code: A4204
canonical_name: 암입원일당
event_axis: HOSPITALIZATION
trigger: 암으로 입원
include: 입원일수 기준 지급
exclude: 외래
reason: 기간 기반 지급 이벤트로 단발성 이벤트와 분리 필요
