"""
Coverage-specific profiles for context guard validation.
DB-only SSOT baseline.
"""

# A4200_1: 암진단비(유사암제외) (Cancer Diagnosis excluding Similar Cancer)
A4200_1_PROFILE = {
    "profile_id": "A4200_1_PROFILE_V1",
    "coverage_code": "A4200_1",
    "canonical_name": "암진단비(유사암제외)",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["암", "암진단", "암진단비", "암 진단", "암 진단비", "일반암"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률", "진단확정"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["제자리암", "상피내암", "전암", "경계성", "유사암", "소액암", "기타피부암", "갑상선암", "대장점막내암", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["암진단비", "일반암", "진단비", "진단확정", r"진단\s*확정", "지급사유", "보험금", "보험가입금액", "지급합니다", "지급함"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A4210: 유사암진단비 (Similar Cancer Diagnosis)
A4210_PROFILE = {
    "profile_id": "A4210_PROFILE_V1",
    "coverage_code": "A4210",
    "canonical_name": "유사암진단비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["유사암", "유사암진단", "유사암진단비", "유사 암", "유사암 진단", "유사암 진단비"],

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

# A5200: 암수술비(유사암제외)
A5200_PROFILE = {
    "profile_id": "A5200_PROFILE_V1",
    "coverage_code": "A5200",
    "canonical_name": "암수술비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["암", "암수술", "수술비", "암수술비", "암 수술", "암 수술비"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["제자리암", "상피내암", "전암", "경계성", "유사암", "소액암", "기타피부암", "갑상선암", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["암수술비", "수술비", "수술", "치료", "보험금", "보험가입금액", "지급합니다", "지급함", "지급사유"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A4104_1A: 특정심장질환진단비 (급성심근경색, 관상동맥질환 등)
A4104_1A_PROFILE = {
    "profile_id": "A4104_1A_PROFILE_V1",
    "coverage_code": "A4104_1A",
    "canonical_name": "특정심장질환진단비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["심장질환", "급성심근경색", "심근경색", "관상동맥", "허혈성", "심혈관"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률", "진단확정"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["급성심근경색", "심근경색", "심장질환", "허혈", "관상동맥", "심혈관", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["심장질환", "진단비", "진단확정", r"진단\s*확정", "지급사유", "보험금", "보험가입금액", "지급합니다", "지급함"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A4104_1B: 부정맥진단비 (I49 부정맥)
A4104_1B_PROFILE = {
    "profile_id": "A4104_1B_PROFILE_V1",
    "coverage_code": "A4104_1B",
    "canonical_name": "부정맥진단비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["부정맥", "I49", "심장리듬", "빈맥", "서맥", "심방세동"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률", "진단확정"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["부정맥", "I49", "심방세동", "심실세동", "빈맥", "서맥", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["부정맥", "진단비", "진단확정", r"진단\s*확정", "지급사유", "보험금", "보험가입금액", "지급합니다", "지급함"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A4102: 뇌출혈진단비
A4102_PROFILE = {
    "profile_id": "A4102_PROFILE_V1",
    "coverage_code": "A4102",
    "canonical_name": "뇌출혈진단비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["뇌출혈", "뇌졸중", "뇌혈관", "뇌출혈진단"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률", "진단확정"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["뇌출혈", "뇌졸중", "뇌경색", "뇌혈관", "허혈", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["뇌출혈진단비", "진단비", "진단확정", r"진단\s*확정", "지급사유", "보험금", "보험가입금액", "지급합니다", "지급함"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A5298_001: 유사암수술비 (Similar Cancer Surgery)
A5298_001_PROFILE = {
    "profile_id": "A5298_001_PROFILE_V1",
    "coverage_code": "A5298_001",
    "canonical_name": "유사암수술비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["유사암", "제자리암", "경계성종양", "갑상선암", "기타피부암", "수술", "수술비", "유사암수술", "유사암수술비", "유사 암", "유사암 수술"],

    "required_terms_by_slot": {
        "waiting_period": ["면책", "보장개시", "책임개시", "90일", r"\d+일", "감액", "지급률"],
        "exclusions": ["제외", "보장하지", "지급하지", "보상하지", "면책", r"보험금을\s*지급하지"],
        "subtype_coverage_map": ["제자리암", "상피내암", "전암", "경계성", "경계성종양", "유사암", "소액암", "기타피부암", "갑상선암", "대장점막내암", "정의", "범위"]
    },

    "hard_negative_terms_global": ["통원일당", "입원일당", "치료일당", "일당", "상급종합병원", r"연간\s*\d+\s*회한", r"\d+\s*회\s*한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["유사암수술비", "수술비", "수술", "치료", "보험금", "보험가입금액", "지급합니다", "지급함", "지급사유"],

    "slot_specific_negatives": {
        "subtype_coverage_map": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

# A6200: 암직접치료입원비 (Q11 전용 - 보장한도 차이 탐색)
A6200_Q11_PROFILE = {
    "profile_id": "A6200_Q11_PROFILE_V1",
    "coverage_code": "A6200",
    "canonical_name": "암직접치료입원비",
    "gate_version": "GATE_SSOT_V2_CONTEXT_GUARD",

    "anchor_keywords": ["암직접", "암 직접", "직접치료", "직접 치료", "입원일당", "입원 일당", "요양병원", "요양 병원"],

    "required_terms_by_slot": {
        "q11_limit_days": [r"1\s*[-~]\s*\d+", r"\d+\s*일\s*한도", r"최대\s*\d+\s*일", "1-180", "180일", "연간", "통산", "회한", "한도"],
        "q11_nursing_hospital_rule": ["요양병원 제외", "요양 병원 제외", "요양병원 포함", "요양 병원 포함", "요양병원제외", "요양제외"],
        "q11_min_admission_or_waiting": ["1일이상", "2일이상", "3일이상", "면책", "보장개시", "책임개시", "90일", "감액", "지급률"]
    },

    "hard_negative_terms_global": ["수술비", "진단비", "통원일당", "납입면제", "보험료납입지원", "상급종합병원", r"연간\s*\d+\s*회한", "100세만기", "90세만기"],

    "section_negative_terms_global": ["납입면제", r"보험료\s*납입면제", "보장보험료", r"차회\s*이후", r"면제\s*사유", r"납입을\s*면제"],

    "diagnosis_signal_terms_global": ["입원일당", "입원비", "직접치료", "보험금", "보험가입금액", "지급합니다", "지급함", "지급사유"],

    "slot_specific_negatives": {
        "q11_limit_days": ["납입면제", r"면제\s*사유", "보장보험료"],
        "q11_nursing_hospital_rule": ["납입면제", r"면제\s*사유", "보장보험료"],
        "q11_min_admission_or_waiting": ["납입면제", r"면제\s*사유", "보장보험료"]
    }
}

COVERAGE_PROFILES = {
    "A4200_1": A4200_1_PROFILE,
    "A4210": A4210_PROFILE,
    "A5200": A5200_PROFILE,
    "A5298_001": A5298_001_PROFILE,
    "A4104_1A": A4104_1A_PROFILE,
    "A4104_1B": A4104_1B_PROFILE,
    "A4102": A4102_PROFILE,
    "A6200": A6200_Q11_PROFILE
}

def get_profile(coverage_code: str) -> dict:
    return COVERAGE_PROFILES.get(coverage_code)
