# A4210 PROFILE SPECIFICATION (V1)

**Profile ID:** A4210_PROFILE_V1
**Coverage:** 유사암진단비 (Similar Cancer Diagnosis)
**Gate Version:** GATE_SSOT_V2_CONTEXT_GUARD

## Profile Structure

### Anchor Keywords
```python
["유사암", "유사암진단", "유사암진단비"]
```

### Required Terms by Slot

**waiting_period:**
- 면책, 보장개시, 책임개시, 90일, \d+일, 감액, 지급률, 진단확정

**exclusions:**
- 제외, 보장하지, 지급하지, 보상하지, 면책, 보험금을\s*지급하지

**subtype_coverage_map:**
- 제자리암, 상피내암, 전암, 경계성, 경계성종양, 유사암, 소액암, 기타피부암, 갑상선암, 정의, 범위

### Hard-Negative Terms (Immediate DROP)
```
통원일당, 입원일당, 치료일당, 일당, 상급종합병원,
연간\s*\d+\s*회한, \d+\s*회\s*한, 100세만기, 90세만기
```

**Rationale:** Daily benefit coverages (A6200 series), not diagnosis benefits (A4210)

### Section-Negative Terms (Immediate DROP)
```
납입면제, 보험료\s*납입면제, 보장보험료,
차회\s*이후, 면제\s*사유, 납입을\s*면제
```

**Rationale:** Premium waiver section, not coverage content

### Diagnosis-Signal Terms (Required)
```
유사암진단비, 진단비, 진단확정, 진단\s*확정,
지급사유, 보험금, 보험가입금액, 지급합니다, 지급함
```

**Rationale:** All A4210 content must reference diagnosis benefits

## 7-Gate Validation Flow

1. Anchor in excerpt
2. Hard-negative check → DROP
3. Section-negative check → DROP
4. Diagnosis-signal required → DROP if missing
5. Coverage name lock → DROP if failed
6. Slot-specific keywords → FOUND if passed
7. Slot-specific negatives → DROP

## Usage

```python
from tools.coverage_profiles import get_profile

profile = get_profile("A4210")
gate_version = profile["gate_version"]  # GATE_SSOT_V2_CONTEXT_GUARD
```

## Testing

Unit tests: `tests/test_a4210_context_guard.py`
- 3 contamination cases (must DROP)
- 3 normal cases (must PASS)
