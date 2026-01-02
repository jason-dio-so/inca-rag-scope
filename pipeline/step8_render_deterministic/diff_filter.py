"""
STEP NEXT-COMPARE-FILTER-01: Coverage Difference Filter

Deterministic rule-based difference detection (NO LLM)

DESIGN:
1. Detect diff query patterns ("다른", "차이", "상이", "~만 찾아줘")
2. Normalize field values for comparison
3. Group insurers by same/different values
4. Return structured diff results

FORBIDDEN:
- NO LLM usage
- NO new data extraction (uses existing coverage_cards only)
- NO Step1-5 re-execution
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DiffGroup:
    """Group of insurers with same value"""
    value: str
    value_normalized: Any
    insurers: List[str]

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "value_normalized": str(self.value_normalized),
            "insurers": self.insurers
        }


@dataclass
class CoverageDiffResult:
    """Difference detection result"""
    coverage_code: str
    field: str
    has_difference: bool
    diff_groups: List[DiffGroup]

    def to_dict(self) -> dict:
        return {
            "kind": "coverage_diff_result",
            "coverage_code": self.coverage_code,
            "field": self.field,
            "has_difference": self.has_difference,
            "diff_groups": [g.to_dict() for g in self.diff_groups]
        }

    def get_different_insurers(self) -> List[Dict[str, str]]:
        """Get insurers with different values (minority groups)"""
        if not self.has_difference:
            return []

        # Find majority group (largest group)
        majority_group = max(self.diff_groups, key=lambda g: len(g.insurers))

        # Return minority groups
        diff_insurers = []
        for group in self.diff_groups:
            if group != majority_group:
                for insurer in group.insurers:
                    diff_insurers.append({
                        "insurer": insurer,
                        "value": group.value
                    })

        return diff_insurers

    def get_same_insurers(self) -> List[Dict[str, str]]:
        """Get insurers with same value (majority group)"""
        if not self.has_difference:
            # All same
            return [{"insurer": ins, "value": self.diff_groups[0].value}
                    for ins in self.diff_groups[0].insurers]

        # Find majority group
        majority_group = max(self.diff_groups, key=lambda g: len(g.insurers))
        return [{"insurer": ins, "value": majority_group.value}
                for ins in majority_group.insurers]


class DiffPatternDetector:
    """Detect if query is asking for differences"""

    # Patterns indicating diff query
    DIFF_PATTERNS = [
        r'다른',
        r'차이',
        r'상이',
        r'다를',
        r'차이.*있',
        r'다르.*찾',
        r'만\s*찾',  # "~만 찾아줘"
    ]

    @classmethod
    def is_diff_query(cls, query: str) -> bool:
        """Check if query is asking for differences"""
        for pattern in cls.DIFF_PATTERNS:
            if re.search(pattern, query):
                return True
        return False


class ValueNormalizer:
    """Normalize field values for comparison"""

    @staticmethod
    def normalize_range(value: str) -> Optional[Tuple[int, int]]:
        """
        Normalize range string to (min, max) tuple

        Examples:
        - "1~120일" → (1, 120)
        - "1~180일" → (1, 180)
        - "120일" → (120, 120)
        """
        if not value:
            return None

        # Pattern: "1~120일"
        match = re.search(r'(\d+)\s*~\s*(\d+)', value)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        # Pattern: "120일" (single value)
        match = re.search(r'(\d+)', value)
        if match:
            num = int(match.group(1))
            return (num, num)

        return None

    @staticmethod
    def normalize_amount(value: str) -> Optional[int]:
        """
        Normalize amount string to integer (in 만원)

        Examples:
        - "3,000만원" → 3000
        - "5천만원" → 5000
        - "1억원" → 10000
        """
        if not value:
            return None

        # Pattern: "3,000만원"
        match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*만\s*원', value)
        if match:
            return int(match.group(1).replace(',', ''))

        # Pattern: "5천만원"
        match = re.search(r'(\d+)\s*천\s*만\s*원', value)
        if match:
            return int(match.group(1)) * 1000

        # Pattern: "1억원"
        match = re.search(r'(\d+)\s*억\s*원', value)
        if match:
            return int(match.group(1)) * 10000

        return None

    @staticmethod
    def normalize_value(value: str, field: str) -> Any:
        """
        Normalize value based on field type

        Args:
            value: Raw value string
            field: Field name (e.g., "보장한도", "보장금액")

        Returns:
            Normalized value for comparison
        """
        if not value:
            return None

        # Field-specific normalization
        if field in ["보장한도", "보장기간", "입원한도"]:
            # Try range normalization
            normalized = ValueNormalizer.normalize_range(value)
            if normalized:
                return normalized

        elif field in ["보장금액", "가입금액"]:
            # Try amount normalization
            normalized = ValueNormalizer.normalize_amount(value)
            if normalized:
                return normalized

        # Default: lowercase string comparison
        return value.lower().strip()


class CoverageDiffFilter:
    """Filter coverages by field differences (deterministic)"""

    @staticmethod
    def detect_differences(
        coverage_data: List[Dict[str, Any]],
        field: str
    ) -> CoverageDiffResult:
        """
        Detect differences in field values across insurers

        Args:
            coverage_data: List of {insurer, value} dicts
            field: Field name to compare

        Returns:
            CoverageDiffResult with grouping
        """
        if not coverage_data:
            return CoverageDiffResult(
                coverage_code="",
                field=field,
                has_difference=False,
                diff_groups=[]
            )

        # Normalize values and group
        value_groups: Dict[Any, DiffGroup] = {}

        for item in coverage_data:
            insurer = item["insurer"]
            raw_value = item["value"]

            # Normalize value
            normalized = ValueNormalizer.normalize_value(raw_value, field)

            # Create hashable key
            if isinstance(normalized, tuple):
                key = normalized
            elif isinstance(normalized, (int, float)):
                key = normalized
            elif isinstance(normalized, str):
                key = normalized
            else:
                key = str(normalized)

            # Group by normalized value
            if key not in value_groups:
                value_groups[key] = DiffGroup(
                    value=raw_value,
                    value_normalized=normalized,
                    insurers=[]
                )

            value_groups[key].insurers.append(insurer)

        # Convert to list
        diff_groups = list(value_groups.values())

        # Check if there's a difference
        has_difference = len(diff_groups) > 1

        # Get coverage_code from first item
        coverage_code = coverage_data[0].get("coverage_code", "")

        return CoverageDiffResult(
            coverage_code=coverage_code,
            field=field,
            has_difference=has_difference,
            diff_groups=diff_groups
        )

    @staticmethod
    def filter_by_difference(
        coverage_data: List[Dict[str, Any]],
        field: str,
        only_different: bool = True
    ) -> Dict[str, Any]:
        """
        Filter coverage data by field differences

        Args:
            coverage_data: List of {insurer, value, coverage_code} dicts
            field: Field to compare
            only_different: If True, return only different values

        Returns:
            {
                "status": "DIFF" | "ALL_SAME",
                "diff_result": CoverageDiffResult,
                "diff_insurers": [...],
                "same_insurers": [...]
            }
        """
        result = CoverageDiffFilter.detect_differences(coverage_data, field)

        if result.has_difference:
            return {
                "status": "DIFF",
                "diff_result": result.to_dict(),
                "diff_insurers": result.get_different_insurers(),
                "same_insurers": result.get_same_insurers()
            }
        else:
            return {
                "status": "ALL_SAME",
                "diff_result": result.to_dict(),
                "diff_insurers": [],
                "same_insurers": result.get_same_insurers()
            }


def main():
    """Test diff filter"""
    import json

    # Test case: 보장한도 difference
    coverage_data = [
        {"insurer": "삼성화재", "value": "1~120일", "coverage_code": "A4200_1"},
        {"insurer": "메리츠화재", "value": "1~180일", "coverage_code": "A4200_1"},
        {"insurer": "DB손해보험", "value": "1~180일", "coverage_code": "A4200_1"},
        {"insurer": "한화손해보험", "value": "1~120일", "coverage_code": "A4200_1"},
    ]

    result = CoverageDiffFilter.filter_by_difference(coverage_data, "보장한도")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
