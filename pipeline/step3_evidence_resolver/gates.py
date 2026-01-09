"""
Evidence GATE Logic - STEP NEXT-67-GATE

Strengthens FOUND criteria to eliminate false positives.

GATES:
G1. Slot Structure Gate: keyword + structural signal (e.g., % for reduction)
G2. Coverage Anchoring Gate: evidence must link to specific coverage
G3. Document Conflict Gate: CONFLICT when values differ across doc_types
G4. Evidence Minimum Requirements: length, locator quality checks

Output statuses:
- FOUND: Coverage-specific + structure validated
- FOUND_GLOBAL: Valid evidence but global/product-level
- UNKNOWN: No evidence or failed gates
- CONFLICT: Conflicting values across documents
"""

import re
from typing import Dict, List, Optional, Tuple


class GateResult:
    """Result of gate validation"""
    def __init__(self, passed: bool, status: str, reason: Optional[str] = None):
        self.passed = passed
        self.status = status  # FOUND | FOUND_GLOBAL | UNKNOWN | CONFLICT
        self.reason = reason


class EvidenceGates:
    """GATE validators for evidence quality control"""

    # G1: Structural signals per slot type
    STRUCTURAL_SIGNALS = {
        "start_date": {
            "required_patterns": [
                r"계약일|보장개시일|책임개시",  # Time reference
                r"부터|이후|다음날|경과"  # Temporal indicator
            ],
            "min_patterns": 2
        },
        "exclusions": {
            "required_patterns": [
                r"면책|제외|보상하지|지급하지",  # Exclusion keyword
                r"않는|아니|해당|경우"  # Negative/conditional
            ],
            "min_patterns": 2
        },
        "payout_limit": {
            "required_patterns": [
                r"한도|지급|보험금|금액",  # Limit keyword
                r"\d+\s*원|\d+\s*회|\d+\s*배"  # Amount/count pattern
            ],
            "min_patterns": 2
        },
        "reduction": {
            "required_patterns": [
                r"감액|지급률|지급비율|삭감",  # Reduction keyword
                r"\d+\s*%|비율|기간|년"  # Percentage or period
            ],
            "min_patterns": 2
        },
        "entry_age": {
            "required_patterns": [
                r"가입연령|가입나이|피보험자",  # Age keyword
                r"만\s*\d+\s*세|\d+\s*세"  # Age pattern
            ],
            "min_patterns": 2
        },
        "waiting_period": {
            "required_patterns": [
                r"면책기간|대기기간|보장제외기간",  # Waiting period keyword
                r"\d+\s*일|\d+\s*개월|경과"  # Duration pattern
            ],
            "min_patterns": 2
        },
        # STEP NEXT-76-A: Extended slots structural signals
        "underwriting_condition": {
            "required_patterns": [
                r"유병자|고혈압|당뇨|인수|가입|건강고지|특별조건|할증",  # Underwriting keyword
                r"가능|제한|조건|병력|질환"  # Condition/restriction
            ],
            "min_patterns": 2
        },
        "mandatory_dependency": {
            "required_patterns": [
                r"주계약|필수|최소|동시|의무|단독",  # Dependency keyword
                r"가입|금액|특약|계약"  # Contract/coverage reference
            ],
            "min_patterns": 2
        },
        "payout_frequency": {
            "required_patterns": [
                r"1회한|최초|연간|평생|재발|재진단|반복|회수",  # Frequency keyword
                r"지급|제한|경과|기간|\d+\s*회"  # Count/period pattern
            ],
            "min_patterns": 2
        },
        "industry_aggregate_limit": {
            "required_patterns": [
                r"업계|타사|다른\s*보험사|통산|누적",  # Industry/other insurer keyword
                r"한도|합산|가입|전체"  # Limit/total keyword
            ],
            "min_patterns": 2
        },
        # STEP NEXT-80: benefit_day_range structural signals
        "benefit_day_range": {
            "required_patterns": [
                r"입원일당|입원일수|일당|보장일수|지급일수",  # Day/count keyword
                r"\d+\s*일|1일부터|최대|범위"  # Day pattern
            ],
            "min_patterns": 2
        },
        # STEP NEXT-81: subtype_coverage_map structural signals
        "subtype_coverage_map": {
            "required_patterns": [
                r"제자리암|상피내암|경계성종양|경계성신생물|CIS",  # Subtype keyword
                r"포함|보장|지급|제외|진단|수술|치료"  # Coverage/exclusion indicator
            ],
            "min_patterns": 2
        }
    }

    def __init__(self):
        pass

    # G1: Slot Structure Gate
    def gate_g1_structure(self, candidate: Dict, slot_key: str) -> GateResult:
        """
        G1: Slot Structure Gate

        Validates that evidence contains both keyword AND structural signals.

        Args:
            candidate: Evidence candidate with context
            slot_key: Evidence slot type

        Returns:
            GateResult with pass/fail and status
        """
        signals = self.STRUCTURAL_SIGNALS.get(slot_key)
        if not signals:
            # Unknown slot type - pass through
            return GateResult(True, "FOUND")

        context = candidate.get("context", "")
        line_text = candidate.get("line_text", "")
        combined_text = f"{line_text}\n{context}"

        # Check how many required patterns are present
        matched_patterns = 0
        for pattern in signals["required_patterns"]:
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched_patterns += 1

        min_required = signals.get("min_patterns", 1)

        if matched_patterns >= min_required:
            return GateResult(True, "FOUND")
        else:
            return GateResult(
                False,
                "UNKNOWN",
                f"G1: Only {matched_patterns}/{min_required} structural patterns found"
            )

    # G2: Coverage Anchoring Gate
    def gate_g2_anchoring(
        self,
        candidate: Dict,
        coverage_name: str,
        coverage_code: Optional[str] = None,
        anchor_window_lines: int = 10
    ) -> GateResult:
        """
        G2: Coverage Anchoring Gate

        Validates that evidence is anchored to the specific coverage.

        Args:
            candidate: Evidence candidate
            coverage_name: Coverage name to search for
            coverage_code: Optional coverage code
            anchor_window_lines: How many lines to search for anchor

        Returns:
            GateResult: FOUND if anchored, FOUND_GLOBAL if not
        """
        context = candidate.get("context", "")
        line_text = candidate.get("line_text", "")

        # Extract context window (±anchor_window_lines from match)
        context_lines = context.split('\n')

        # Clean coverage name for matching
        # e.g., "206. 다빈치로봇 암수술비(...)" -> "다빈치로봇 암수술비"
        coverage_title = self._extract_coverage_title(coverage_name)

        # Check for coverage name/code in context
        anchor_found = False

        for line in context_lines:
            # Check coverage title
            if coverage_title and coverage_title in line:
                anchor_found = True
                break

            # Check coverage code (e.g., "206.")
            if coverage_code and coverage_code in line:
                anchor_found = True
                break

        if anchor_found:
            return GateResult(True, "FOUND")
        else:
            return GateResult(
                True,  # Still valid evidence, just not coverage-specific
                "FOUND_GLOBAL",
                "G2: Evidence is global (no coverage anchor found)"
            )

    def _extract_coverage_title(self, coverage_name: str) -> str:
        """
        Extract clean coverage title from coverage_name_raw.

        Examples:
        - "206. 다빈치로봇 암수술비(갑상선암 및 전립선암 제외)(최초1회한)(갱신형)"
          -> "다빈치로봇 암수술비"
        - "1. 일반상해사망(기본)" -> "일반상해사망"
        """
        # Remove leading number and dot
        title = re.sub(r'^\d+\.\s*', '', coverage_name)

        # Remove parenthetical suffixes
        title = re.split(r'\(', title)[0].strip()

        return title

    # G3: Document Conflict Gate
    def gate_g3_conflict(
        self,
        evidences: List[Dict],
        slot_key: str
    ) -> GateResult:
        """
        G3: Document Conflict Gate

        Detects conflicts when different doc_types have different values.

        Args:
            evidences: List of evidence entries for a slot
            slot_key: Evidence slot type

        Returns:
            GateResult: CONFLICT if values differ, FOUND otherwise
        """
        if len(evidences) < 2:
            return GateResult(True, "FOUND")

        # For numeric slots, extract and compare values
        if slot_key in ["entry_age", "payout_limit", "reduction", "waiting_period"]:
            values_by_doc = {}

            for ev in evidences:
                doc_type = ev.get("doc_type")
                excerpt = ev.get("excerpt", "")

                # Extract numeric values
                nums = self._extract_numbers(excerpt)

                if nums:
                    values_by_doc[doc_type] = set(nums)

            # Check for conflicts
            if len(values_by_doc) > 1:
                unique_values = list(values_by_doc.values())
                # If any two doc types have completely different values
                for i in range(len(unique_values)):
                    for j in range(i + 1, len(unique_values)):
                        if not unique_values[i].intersection(unique_values[j]):
                            return GateResult(
                                False,
                                "CONFLICT",
                                f"G3: Conflicting values across documents: {values_by_doc}"
                            )

        return GateResult(True, "FOUND")

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract all numbers from text"""
        return re.findall(r'\d+', text)

    # G4: Evidence Minimum Requirements Gate
    def gate_g4_minimum(self, candidate: Dict) -> GateResult:
        """
        G4: Evidence Minimum Requirements

        Validates:
        - excerpt length >= 15 chars
        - locator is not just a single keyword
        - required fields present

        Args:
            candidate: Evidence candidate

        Returns:
            GateResult with pass/fail
        """
        # Check required fields
        required_fields = ["slot_key", "keyword", "context", "page"]
        missing_fields = [f for f in required_fields if f not in candidate]

        if missing_fields:
            return GateResult(
                False,
                "UNKNOWN",
                f"G4: Missing required fields: {missing_fields}"
            )

        # Check excerpt length
        excerpt = candidate.get("context", "")
        if len(excerpt.strip()) < 15:
            return GateResult(
                False,
                "UNKNOWN",
                f"G4: Excerpt too short ({len(excerpt)} chars)"
            )

        # Check that context is not just the keyword
        keyword = candidate.get("keyword", "")
        context = candidate.get("context", "")

        # Remove keyword and check remaining content
        context_without_keyword = context.replace(keyword, "").strip()
        if len(context_without_keyword) < 10:
            return GateResult(
                False,
                "UNKNOWN",
                "G4: Context is too sparse (only keyword present)"
            )

        return GateResult(True, "FOUND")

    # Combined gate validation
    def validate_candidate(
        self,
        candidate: Dict,
        slot_key: str,
        coverage_name: str,
        coverage_code: Optional[str] = None
    ) -> GateResult:
        """
        Run all gates on a candidate.

        Returns the most restrictive status:
        - If any gate fails with UNKNOWN -> UNKNOWN
        - If any gate returns FOUND_GLOBAL -> FOUND_GLOBAL
        - If all pass -> FOUND

        Args:
            candidate: Evidence candidate
            slot_key: Evidence slot type
            coverage_name: Coverage name for anchoring
            coverage_code: Optional coverage code

        Returns:
            Final GateResult
        """
        # G4: Minimum requirements (fail fast)
        g4_result = self.gate_g4_minimum(candidate)
        if not g4_result.passed:
            return g4_result

        # G1: Structure
        g1_result = self.gate_g1_structure(candidate, slot_key)
        if not g1_result.passed:
            return g1_result

        # G2: Anchoring
        g2_result = self.gate_g2_anchoring(
            candidate,
            coverage_name,
            coverage_code
        )

        # G2 can downgrade FOUND -> FOUND_GLOBAL
        if g2_result.status == "FOUND_GLOBAL":
            return g2_result

        return GateResult(True, "FOUND")

    def validate_evidences(
        self,
        evidences: List[Dict],
        slot_key: str
    ) -> GateResult:
        """
        Run multi-evidence gates (G3: conflict detection).

        Args:
            evidences: List of evidence entries
            slot_key: Evidence slot type

        Returns:
            GateResult
        """
        return self.gate_g3_conflict(evidences, slot_key)
