"""
STEP NEXT-O: Premium Multiplier Loader
일반형 보험요율 배수 적재 (Excel → DB)

Rules:
1. 엑셀 값은 퍼센트 배수 (116 → 1.16)
2. insurer_key ↔ 한글 보험사명 명시적 매핑
3. 담보명 문자열 괄호 포함 완전 일치
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# SSOT: 한글 보험사명 → insurer_key 매핑
INSURER_NAME_TO_KEY = {
    "한화손해보험": "hanwha",
    "삼성화재": "samsung",
    "롯데손해보험": "lotte",
    "현대해상화재": "hyundai",
    "메리츠화재": "meritz",
    "DB손해보험": "db",
    "KB손해보험": "kb",
    "흥국화재": "heungkuk",
}


def load_multiplier_excel(excel_path: str) -> List[Dict[str, Any]]:
    """
    일반보험요율예시.xlsx 파싱

    Args:
        excel_path: 엑셀 파일 경로

    Returns:
        List[Dict]: premium_multiplier 테이블 삽입용 레코드

    Raises:
        FileNotFoundError: 엑셀 파일 없음
        ValueError: 필수 컬럼 누락 또는 매핑 실패
    """
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    # Read Excel
    df = pd.read_excel(excel_path, sheet_name="sheet1")

    # 첫 행이 헤더 (담보명 / 보험사명들)
    # 첫 컬럼은 담보명
    coverage_col = df.columns[0]
    insurer_cols = df.columns[1:]

    # 첫 행에서 한글 보험사명 추출
    header_row = df.iloc[0]
    insurer_names = [str(header_row[col]) for col in insurer_cols]

    # 담보명 시작 (행 1부터)
    records = []

    for row_idx in range(1, len(df)):
        coverage_name = str(df.iloc[row_idx][coverage_col]).strip()

        if not coverage_name or coverage_name == "nan":
            continue

        for col_idx, insurer_col in enumerate(insurer_cols):
            insurer_name = insurer_names[col_idx].strip()

            # 보험사명 → insurer_key 매핑
            if insurer_name not in INSURER_NAME_TO_KEY:
                raise ValueError(
                    f"Unknown insurer name: '{insurer_name}'. "
                    f"Add to INSURER_NAME_TO_KEY in multiplier_loader.py"
                )

            insurer_key = INSURER_NAME_TO_KEY[insurer_name]

            # 배수 값
            raw_value = df.iloc[row_idx][insurer_col]

            # NaN 또는 빈 값 → 건너뜀 (배수 없음 = GENERAL은 NULL)
            if pd.isna(raw_value) or str(raw_value).strip() == "":
                continue

            try:
                multiplier_percent = float(raw_value)
            except ValueError:
                raise ValueError(
                    f"Invalid multiplier value at row {row_idx + 1}, "
                    f"insurer={insurer_name}, coverage={coverage_name}: {raw_value}"
                )

            # LOCKED: 배수는 퍼센트로 저장 (116 그대로, 계산 시 / 100)
            records.append({
                "insurer_key": insurer_key,
                "coverage_name": coverage_name,
                "multiplier_percent": multiplier_percent,
                "source_file": str(path),
                "source_row_id": row_idx + 1,  # Excel 행 번호 (1-based)
            })

    if not records:
        raise ValueError(f"No valid multiplier records found in {excel_path}")

    return records


def get_multiplier(
    insurer_key: str,
    coverage_name: str,
    multipliers: List[Dict[str, Any]]
) -> float | None:
    """
    특정 보험사 + 담보명의 배수 조회

    Args:
        insurer_key: 보험사 키
        coverage_name: 담보명 (괄호 포함 완전 일치)
        multipliers: load_multiplier_excel() 결과

    Returns:
        float: multiplier_percent (116.0) 또는 None (배수 없음)
    """
    for record in multipliers:
        if (record["insurer_key"] == insurer_key and
            record["coverage_name"] == coverage_name):
            return record["multiplier_percent"]

    return None


def calculate_general_premium(
    no_refund_premium: int,
    multiplier_percent: float | None
) -> int | None:
    """
    일반형 보험료 계산

    Rules:
    - GENERAL = round(NO_REFUND × (multiplier_percent / 100))
    - multiplier_percent 없으면 → None (GENERAL 표시 안 함)

    Args:
        no_refund_premium: 무해지 보험료 (원)
        multiplier_percent: 배수 (116.0)

    Returns:
        int: 일반형 보험료 (원) 또는 None (배수 없음)
    """
    if multiplier_percent is None:
        return None

    # LOCKED: 반올림 적용
    return round(no_refund_premium * (multiplier_percent / 100))


if __name__ == "__main__":
    # Test loader
    import json

    excel_path = "/Users/cheollee/inca-rag-scope/data/sources/insurers/4. 일반보험요율예시.xlsx"

    try:
        records = load_multiplier_excel(excel_path)
        print(f"Loaded {len(records)} multiplier records")
        print("\nFirst 5 records:")
        for record in records[:5]:
            print(json.dumps(record, ensure_ascii=False, indent=2))

        # Test lookup
        multiplier = get_multiplier("kb", "상해후유장해(3~100%)", records)
        print(f"\nKB 상해후유장해(3~100%) multiplier: {multiplier}")

        # Test calculation
        no_refund = 50000
        general = calculate_general_premium(no_refund, multiplier)
        print(f"NO_REFUND={no_refund} → GENERAL={general}")

    except Exception as e:
        print(f"Error: {e}")
        raise
