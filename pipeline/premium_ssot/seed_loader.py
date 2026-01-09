"""
STEP NEXT-O: Premium Quote Seed Loader
보험료 SSOT 적재 (API 응답 + 배수 → premium_quote 테이블)

Rules:
1. 무해지 = API 응답의 ①전체 (monthlyPremSum, totalPremSum)
2. 일반 = round(무해지 × (multiplier_percent / 100))
3. 배수 없으면 일반형은 NULL (표시하지 않음)
4. LLM 계산/추정/보정 절대 금지
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    from .multiplier_loader import (
        load_multiplier_excel,
        calculate_general_premium,
        get_multiplier
    )
except ImportError:
    from multiplier_loader import (
        load_multiplier_excel,
        calculate_general_premium,
        get_multiplier
    )


def load_api_response_json(json_path: str) -> Dict[str, Any]:
    """
    API 응답 JSON 파일 로드

    Expected format:
    {
      "insurer_key": "kb",
      "product_id": "kb__ci_insurance_2024",
      "quotes": [
        {
          "age": 30,
          "sex": "M",
          "smoke": "N",
          "pay_term_years": 20,
          "ins_term_years": 80,
          "monthly_prem_sum": 50000,
          "total_prem_sum": 12000000,
          "as_of_date": "2025-01-09"
        },
        ...
      ]
    }

    Args:
        json_path: API 응답 JSON 파일 경로

    Returns:
        Dict: API 응답 데이터

    Raises:
        FileNotFoundError: JSON 파일 없음
        ValueError: 필수 필드 누락
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ["insurer_key", "product_id", "quotes"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    return data


def generate_premium_quote_records(
    api_data: Dict[str, Any],
    multipliers: List[Dict[str, Any]],
    coverage_name: str = "전체"  # 담보명 (배수 조회용)
) -> List[Dict[str, Any]]:
    """
    premium_quote 테이블 레코드 생성

    Args:
        api_data: API 응답 데이터 (load_api_response_json 결과)
        multipliers: 배수 데이터 (load_multiplier_excel 결과)
        coverage_name: 배수 조회용 담보명 (기본값: "전체")

    Returns:
        List[Dict]: premium_quote 테이블 삽입용 레코드

    Raises:
        ValueError: 필수 필드 누락 또는 값 검증 실패
    """
    insurer_key = api_data["insurer_key"]
    product_id = api_data["product_id"]
    quotes = api_data["quotes"]

    records = []

    for quote in quotes:
        # Validate required fields
        required_quote_fields = [
            "age", "sex", "pay_term_years", "ins_term_years",
            "monthly_prem_sum", "total_prem_sum", "as_of_date"
        ]
        for field in required_quote_fields:
            if field not in quote:
                raise ValueError(f"Missing required quote field: {field}")

        age = quote["age"]
        sex = quote["sex"]
        smoke = quote.get("smoke", "NA")
        pay_term_years = quote["pay_term_years"]
        ins_term_years = quote["ins_term_years"]
        monthly_prem_no_refund = quote["monthly_prem_sum"]
        total_prem_no_refund = quote["total_prem_sum"]
        as_of_date = quote["as_of_date"]

        # Validate constraints
        if age not in [30, 40, 50]:
            raise ValueError(f"Invalid age: {age}. Must be 30, 40, or 50.")

        if sex not in ["M", "F", "UNISEX"]:
            raise ValueError(f"Invalid sex: {sex}. Must be M, F, or UNISEX.")

        if smoke not in ["Y", "N", "NA"]:
            raise ValueError(f"Invalid smoke: {smoke}. Must be Y, N, or NA.")

        if monthly_prem_no_refund <= 0 or total_prem_no_refund <= 0:
            raise ValueError(
                f"Invalid premium values: monthly={monthly_prem_no_refund}, "
                f"total={total_prem_no_refund}. Must be positive."
            )

        # NO_REFUND record (무해지)
        no_refund_record = {
            "insurer_key": insurer_key,
            "product_id": product_id,
            "plan_variant": "NO_REFUND",
            "age": age,
            "sex": sex,
            "smoke": smoke,
            "pay_term_years": pay_term_years,
            "ins_term_years": ins_term_years,
            "premium_monthly": monthly_prem_no_refund,
            "premium_total": total_prem_no_refund,
            "source_table_id": "api_response",
            "source_row_id": None,
            "as_of_date": as_of_date,
        }
        records.append(no_refund_record)

        # GENERAL record (일반형)
        # 배수 조회
        multiplier_percent = get_multiplier(insurer_key, coverage_name, multipliers)

        if multiplier_percent is not None:
            # 일반형 보험료 계산
            monthly_prem_general = calculate_general_premium(
                monthly_prem_no_refund, multiplier_percent
            )
            total_prem_general = calculate_general_premium(
                total_prem_no_refund, multiplier_percent
            )

            general_record = {
                "insurer_key": insurer_key,
                "product_id": product_id,
                "plan_variant": "GENERAL",
                "age": age,
                "sex": sex,
                "smoke": smoke,
                "pay_term_years": pay_term_years,
                "ins_term_years": ins_term_years,
                "premium_monthly": monthly_prem_general,
                "premium_total": total_prem_general,
                "source_table_id": f"calculated_from_no_refund_multiplier_{multiplier_percent}",
                "source_row_id": None,
                "as_of_date": as_of_date,
            }
            records.append(general_record)

        # 배수 없음 → GENERAL은 NULL (레코드 생성 안 함)

    return records


def write_premium_quote_jsonl(
    records: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    premium_quote 레코드를 JSONL로 저장

    Args:
        records: premium_quote 레코드
        output_path: 출력 JSONL 파일 경로
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"Written {len(records)} records to {output_path}")


if __name__ == "__main__":
    # Example: Load multipliers and generate sample records
    multiplier_excel = "/Users/cheollee/inca-rag-scope/data/sources/insurers/4. 일반보험요율예시.xlsx"
    multipliers = load_multiplier_excel(multiplier_excel)

    # Sample API response
    sample_api_data = {
        "insurer_key": "kb",
        "product_id": "kb__ci_insurance_2024",
        "quotes": [
            {
                "age": 30,
                "sex": "M",
                "smoke": "N",
                "pay_term_years": 20,
                "ins_term_years": 80,
                "monthly_prem_sum": 50000,
                "total_prem_sum": 12000000,
                "as_of_date": "2025-01-09"
            },
            {
                "age": 40,
                "sex": "F",
                "smoke": "N",
                "pay_term_years": 20,
                "ins_term_years": 80,
                "monthly_prem_sum": 70000,
                "total_prem_sum": 16800000,
                "as_of_date": "2025-01-09"
            }
        ]
    }

    # Generate records
    # NOTE: coverage_name="전체" for total premium multiplier
    # If API provides per-coverage premiums, use actual coverage names
    records = generate_premium_quote_records(
        sample_api_data,
        multipliers,
        coverage_name="전체"  # Adjust based on actual coverage
    )

    print(f"Generated {len(records)} premium_quote records")
    print("\nSample records:")
    for record in records[:4]:
        print(json.dumps(record, ensure_ascii=False, indent=2))
