"""
Coverage-specific profiles for context guard validation.
DB-only SSOT baseline.
"""

# A4210: 유사암진단비 (Similar Cancer Diagnosis)
A4210_PROFILE = {
    "profile_id": "A4210_PROFILE_V1",
    "coverage_code": "A4210",
    "canonical_name": "유사암진단비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["유사암", "유사암진단", "유사암진단비"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률", "진단확정"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["제자리암", "상피내암", "전암", "경계성", "경계성종양", "유사암", "소액암", "기타피부암", "갑상선암", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["유사암진단비", "진단비", "진단확정", r"진단\s*확정", "지급사유", "보험금", "보험가입금액", "지급합니다", "지급함"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

COVERAGE_PROFILES = {"A4210": A4210_PROFILE}

def get_profile(coverage_code: str) -> dict:
    return COVERAGE_PROFILES.get(coverage_code)
