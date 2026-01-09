"""
STEP NEXT-F: Coverage Attribution Gate (G5) - ALL Diagnosis Benefits

Registry-driven gate that prevents cross-coverage contamination.

Generalized from STEP NEXT-82-Q12-FIX-2 (cancer-only) to ALL diagnosis types.

HARD RULES:
1. Registry-only diagnosis benefits allowed for comparison
2. Evidence MUST mention target coverage
3. Evidence MUST NOT mention excluded coverages
4. Cross-coverage evidence → HARD demotion to UNKNOWN
5. NO Step1-3 changes (Step4/Step5 only)

Coverage Attribution Logic:
- Load diagnosis_coverage_registry.json (SSOT)
- For each coverage_code in registry:
  - Get exclusion_keywords from registry
  - Check all evidence excerpts
  - If excluded coverage detected → DEMOTE to UNKNOWN
  - If no target mention → DEMOTE to UNKNOWN
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class DiagnosisCoverageRegistry:
    """
    Diagnosis Coverage Registry Loader (SSOT)

    Loads registry and provides lookup methods for G5 gate.
    """

    def __init__(self, registry_path: Path = None):
        if registry_path is None:
            registry_path = Path(__file__).parent.parent.parent / "data" / "registry" / "diagnosis_coverage_registry.json"

        self.registry_path = registry_path
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load diagnosis coverage registry from JSON"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_diagnosis_coverage(self, coverage_code: str) -> bool:
        """Check if coverage_code is a registered diagnosis benefit"""
        if not coverage_code:
            return False
        return coverage_code in self.registry.get("coverage_entries", {})

    def get_coverage_entry(self, coverage_code: str) -> Optional[Dict]:
        """Get registry entry for coverage_code"""
        return self.registry.get("coverage_entries", {}).get(coverage_code)

    def get_exclusion_keywords(self, coverage_code: str) -> List[str]:
        """Get exclusion keywords for coverage_code"""
        entry = self.get_coverage_entry(coverage_code)
        if not entry:
            return []
        return entry.get("exclusion_keywords", [])

    def get_canonical_name(self, coverage_code: str) -> Optional[str]:
        """Get canonical name for coverage_code"""
        entry = self.get_coverage_entry(coverage_code)
        if not entry:
            return None
        return entry.get("canonical_name")

    def get_diagnosis_type(self, coverage_code: str) -> Optional[str]:
        """Get diagnosis_type for coverage_code"""
        entry = self.get_coverage_entry(coverage_code)
        if not entry:
            return None
        return entry.get("diagnosis_type")


class CoverageAttributionValidator:
    """
    G5: Coverage Attribution Gate (Registry-Driven)

    Ensures evidence excerpts are attributed to the TARGET coverage,
    preventing cross-coverage contamination for ALL diagnosis types.

    Generalized from STEP NEXT-82-Q12-FIX-2 (cancer-only).
    """

    def __init__(self, registry: DiagnosisCoverageRegistry = None):
        self.registry = registry or DiagnosisCoverageRegistry()

    def validate_attribution(
        self,
        excerpts: List[str],
        coverage_code: str,
        coverage_name: str = ""
    ) -> Dict[str, Any]:
        """
        Check if excerpts are attributed to target coverage.

        Args:
            excerpts: List of evidence excerpts
            coverage_code: Target coverage code (from Step2-b)
            coverage_name: Target coverage name (for display)

        Returns:
            {
                "valid": bool,
                "reason": str,
                "matched_exclusion": str|None,
                "diagnosis_type": str|None
            }
        """
        if not excerpts:
            return {
                "valid": False,
                "reason": "No excerpts",
                "matched_exclusion": None,
                "diagnosis_type": None
            }

        # Check if this is a registered diagnosis benefit
        if not self.registry.is_diagnosis_coverage(coverage_code):
            # Not a diagnosis benefit → skip G5 gate (PASS through)
            return {
                "valid": True,
                "reason": "Not a diagnosis benefit (G5 skip)",
                "matched_exclusion": None,
                "diagnosis_type": None
            }

        # Get registry entry
        entry = self.registry.get_coverage_entry(coverage_code)
        diagnosis_type = entry.get("diagnosis_type")
        canonical_name = entry.get("canonical_name", "")
        exclusion_keywords = entry.get("exclusion_keywords", [])

        # Build target patterns from canonical name
        target_patterns = self._build_target_patterns(canonical_name)

        # Build excluded patterns from registry keywords
        excluded_patterns = self._build_excluded_patterns(exclusion_keywords)

        # Check excerpts
        has_target = False
        has_excluded = False
        matched_exclusion = None

        for excerpt in excerpts:
            # Check for target coverage mention
            if any(re.search(pattern, excerpt, re.IGNORECASE) for pattern in target_patterns):
                has_target = True

            # Check for excluded coverages
            for keyword in exclusion_keywords:
                # Convert keyword to regex pattern (escape special chars)
                pattern = re.escape(keyword)
                # Allow flexible whitespace
                pattern = pattern.replace(r'\ ', r'\s*')

                if re.search(pattern, excerpt, re.IGNORECASE):
                    has_excluded = True
                    matched_exclusion = keyword
                    break

            if has_excluded:
                break

        # HARD RULE: If excluded coverage found, REJECT immediately
        if has_excluded:
            return {
                "valid": False,
                "reason": "다른 담보 값 혼입",
                "matched_exclusion": matched_exclusion,
                "diagnosis_type": diagnosis_type
            }

        # HARD RULE: Target coverage must be mentioned
        if not has_target:
            return {
                "valid": False,
                "reason": "담보 귀속 확인 불가",
                "matched_exclusion": None,
                "diagnosis_type": diagnosis_type
            }

        return {
            "valid": True,
            "reason": "Valid attribution",
            "matched_exclusion": None,
            "diagnosis_type": diagnosis_type
        }

    def _build_target_patterns(self, canonical_name: str) -> List[str]:
        """
        Build regex patterns for target coverage mention.

        Examples:
        - "암진단비(유사암제외)" → [r'암\s*진단\s*비.*유사\s*암\s*제외', r'암\s*\(유사\s*암\s*제외\)']
        - "뇌졸중진단비" → [r'뇌\s*졸\s*중\s*진단\s*비', r'뇌\s*졸\s*중']
        - "허혈성심장질환진단비" → [r'허혈성\s*심장\s*질환\s*진단\s*비', r'허혈성\s*심장\s*질환']
        """
        patterns = []

        # Add canonical name as-is (with flexible whitespace)
        pattern = re.escape(canonical_name)
        pattern = pattern.replace(r'\ ', r'\s*')
        patterns.append(pattern)

        # Special patterns for specific coverages
        if "암진단비" in canonical_name:
            if "유사암제외" in canonical_name or "유사암 제외" in canonical_name:
                patterns.extend([
                    r'암\s*진단\s*비.*유사\s*암\s*제외',
                    r'암\s*\(유사\s*암\s*제외\)',
                    r'일반\s*암\s*진단\s*비',
                ])
            elif "유사암" in canonical_name:
                patterns.extend([
                    r'유사\s*암\s*진단\s*비',
                    r'소액\s*암\s*진단\s*비',
                ])

        elif "뇌졸중" in canonical_name:
            patterns.extend([
                r'뇌\s*졸\s*중\s*진단\s*비',
                r'뇌\s*졸\s*중',
            ])

        elif "허혈성" in canonical_name:
            patterns.extend([
                r'허혈성\s*심장\s*질환\s*진단\s*비',
                r'허혈성\s*심장\s*질환',
            ])

        return patterns

    def _build_excluded_patterns(self, exclusion_keywords: List[str]) -> List[str]:
        """
        Build regex patterns from exclusion keywords.

        Each keyword is escaped and whitespace is made flexible.
        """
        patterns = []
        for keyword in exclusion_keywords:
            pattern = re.escape(keyword)
            pattern = pattern.replace(r'\ ', r'\s*')
            patterns.append(pattern)
        return patterns


class SlotGateValidator:
    """
    Slot-level gate validation for diagnosis benefits.

    Applies G5 Coverage Attribution Gate + additional slot-specific gates.
    """

    def __init__(self, registry: DiagnosisCoverageRegistry = None):
        self.registry = registry or DiagnosisCoverageRegistry()
        self.attribution_validator = CoverageAttributionValidator(self.registry)

    def validate_slot(
        self,
        slot_key: str,
        slot_data: Dict,
        coverage_code: str,
        coverage_name: str = ""
    ) -> Dict[str, Any]:
        """
        Validate slot value and apply gates.

        Returns:
            {
                "valid": bool,
                "gate_violation": str|None,
                "reason": str|None
            }
        """
        # Only validate slots with evidence
        status = slot_data.get("status", "UNKNOWN")
        if status not in ["FOUND", "FOUND_GLOBAL", "CONFLICT"]:
            return {"valid": True, "gate_violation": None, "reason": None}

        # Get evidence excerpts
        evidences = slot_data.get("evidences", [])
        excerpts = [ev.get("excerpt", "") for ev in evidences if ev.get("excerpt")]

        if not excerpts:
            return {"valid": True, "gate_violation": None, "reason": None}

        # Apply G5 Coverage Attribution Gate
        attribution = self.attribution_validator.validate_attribution(
            excerpts,
            coverage_code,
            coverage_name
        )

        if not attribution["valid"]:
            return {
                "valid": False,
                "gate_violation": "G5_attribution_failed",
                "reason": attribution["reason"],
                "matched_exclusion": attribution.get("matched_exclusion"),
                "diagnosis_type": attribution.get("diagnosis_type")
            }

        # Slot-specific gates (from FIX-2)
        if slot_key == "payout_limit":
            # payout_limit treatment amount filter (for cancer/expensive_cancer)
            diagnosis_type = attribution.get("diagnosis_type")
            if diagnosis_type in ["cancer", "cancer_expensive"]:
                value = slot_data.get("value")
                if isinstance(value, dict):
                    amount = value.get("amount")
                    if amount and amount <= 10_000_000:  # <= 1000만원
                        return {
                            "valid": False,
                            "gate_violation": "treatment_amount_suspected",
                            "reason": f"Amount {amount} <= 1000만원 (치료비 가능성)"
                        }

        elif slot_key == "reduction":
            # reduction HARD gate: BOTH period + rate required
            value = slot_data.get("value")
            if isinstance(value, dict):
                rate_pct = value.get("rate_pct")
                period_days = value.get("period_days")

                if rate_pct is None:
                    return {
                        "valid": False,
                        "gate_violation": "rate_pct_missing",
                        "reason": "감액률 누락"
                    }

                if period_days is None:
                    return {
                        "valid": False,
                        "gate_violation": "period_days_missing",
                        "reason": "감액 기간 누락"
                    }

        return {"valid": True, "gate_violation": None, "reason": None}


# ============================================================================
# STEP NEXT-I: G6 Slot Tier Enforcement Gate
# ============================================================================

class SlotTierPolicy:
    """
    Slot Tier Classification (SSOT)

    Reference: docs/SLOT_TIER_POLICY.md

    Tier-A: Coverage-Anchored Slots (require G5 PASS)
    Tier-B: Product-Level Slots (product-level attribution allowed)
    Tier-C: Descriptive/Conditional Slots (comparison/recommendation FORBIDDEN)
    """

    TIER_A_SLOTS = {
        "payout_limit",
        "waiting_period",
        "reduction",
        "exclusions"
    }

    TIER_B_SLOTS = {
        "entry_age",
        "start_date",
        "mandatory_dependency"
    }

    TIER_C_SLOTS = {
        "underwriting_condition",
        "payout_frequency",
        "industry_aggregate_limit"
    }

    @classmethod
    def get_tier(cls, slot_key: str) -> str:
        """
        Get tier classification for slot.

        Returns: "A", "B", "C", or "UNKNOWN"
        """
        if slot_key in cls.TIER_A_SLOTS:
            return "A"
        elif slot_key in cls.TIER_B_SLOTS:
            return "B"
        elif slot_key in cls.TIER_C_SLOTS:
            return "C"
        else:
            return "UNKNOWN"

    @classmethod
    def is_comparison_allowed(cls, slot_key: str) -> bool:
        """Check if slot can be shown in comparison table"""
        tier = cls.get_tier(slot_key)
        return tier in ["A", "B"]

    @classmethod
    def is_recommendation_allowed(cls, slot_key: str) -> bool:
        """Check if slot can be used in recommendation logic"""
        tier = cls.get_tier(slot_key)
        return tier == "A"  # Only Tier-A allowed


class SlotTierEnforcementGate:
    """
    G6: Slot Tier Enforcement Gate

    HARD RULES (ZERO TOLERANCE):
    1. Tier-C slots CANNOT be used in comparison/recommendation
    2. Tier-A slots with G5 FAIL CANNOT output values
    3. All numeric values MUST have attribution

    Violation → exit 2 (hard fail)
    """

    def __init__(self):
        self.policy = SlotTierPolicy()

    def validate_comparison_usage(self, slot_key: str) -> Dict[str, Any]:
        """
        Validate that slot can be used in comparison table.

        Returns:
            {
                "valid": bool,
                "reason": str | None
            }
        """
        if not self.policy.is_comparison_allowed(slot_key):
            tier = self.policy.get_tier(slot_key)
            return {
                "valid": False,
                "reason": f"Tier-{tier} slot '{slot_key}' cannot be used in comparison table"
            }

        return {"valid": True, "reason": None}

    def validate_recommendation_usage(self, slot_key: str) -> Dict[str, Any]:
        """
        Validate that slot can be used in recommendation logic.

        Returns:
            {
                "valid": bool,
                "reason": str | None
            }
        """
        if not self.policy.is_recommendation_allowed(slot_key):
            tier = self.policy.get_tier(slot_key)
            return {
                "valid": False,
                "reason": f"Tier-{tier} slot '{slot_key}' cannot be used in recommendation logic"
            }

        return {"valid": True, "reason": None}

    def validate_value_output(
        self,
        slot_key: str,
        slot_data: Dict,
        g5_result: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate that slot value can be displayed.

        Tier-A slots require G5 PASS.

        Args:
            slot_key: Slot name
            slot_data: Slot data (with value, status, etc.)
            g5_result: G5 validation result (if applicable)

        Returns:
            {
                "valid": bool,
                "reason": str | None,
                "display_value": str | Dict | None  # Safe output value
            }
        """
        tier = self.policy.get_tier(slot_key)
        status = slot_data.get("status", "UNKNOWN")
        value = slot_data.get("value")

        # Tier-C: NEVER output value in comparison table
        if tier == "C":
            return {
                "valid": False,
                "reason": "Tier-C slot cannot have value output in comparison",
                "display_value": None
            }

        # Tier-A: Require G5 PASS for value output
        if tier == "A":
            # If status is not FOUND/FOUND_GLOBAL, no value to validate
            if status not in ["FOUND", "FOUND_GLOBAL", "CONFLICT"]:
                return {
                    "valid": True,
                    "reason": None,
                    "display_value": "❓ 정보 없음"
                }

            # Check G5 result
            if g5_result and not g5_result.get("valid", False):
                # G5 FAIL → MUST NOT output value
                return {
                    "valid": True,  # Not a gate violation, just demotion
                    "reason": "G5 attribution failed",
                    "display_value": "❓ 정보 없음"
                }

            # G5 PASS → output value
            return {
                "valid": True,
                "reason": None,
                "display_value": value
            }

        # Tier-B: Product-level, add suffix
        if tier == "B":
            if status in ["FOUND", "FOUND_GLOBAL"]:
                # Add (상품 기준) suffix for display
                display_value = f"{value} (상품 기준)" if value else "❓ 정보 없음"
                return {
                    "valid": True,
                    "reason": None,
                    "display_value": display_value
                }
            else:
                return {
                    "valid": True,
                    "reason": None,
                    "display_value": "❓ 정보 없음"
                }

        # UNKNOWN tier: Allow but warn
        return {
            "valid": True,
            "reason": f"Unknown tier for slot '{slot_key}'",
            "display_value": value
        }

    def filter_comparison_slots(self, slot_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter slots for comparison table (exclude Tier-C).

        Args:
            slot_dict: Dict of slot_key -> slot_data

        Returns:
            Filtered dict with only Tier-A and Tier-B slots
        """
        filtered = {}
        for slot_key, slot_data in slot_dict.items():
            if self.policy.is_comparison_allowed(slot_key):
                filtered[slot_key] = slot_data

        return filtered


# ============================================================================
# STEP NEXT-K: Confidence Labeling
# ============================================================================

class ConfidenceLabeler:
    """
    Confidence Level Assignment (Rule-Based)

    Reference: docs/CONFIDENCE_LABEL_POLICY.md

    Assigns trust level to Tier-A slot values based on evidence document type.

    HARD RULES:
    1. Only HIGH/MEDIUM levels (no LOW, no percentages)
    2. Document type mapping only (no LLM, no scoring)
    3. Tier-A slots only (payout_limit, waiting_period, reduction, exclusions)
    4. UNKNOWN values get NO confidence
    """

    # Document type to confidence mapping (SSOT)
    DOC_TYPE_CONFIDENCE = {
        "가입설계서": "HIGH",
        "약관": "HIGH",
        "상품요약서": "MEDIUM",
        "사업방법서": "MEDIUM"
    }

    # Tier-A slots that get confidence labels
    TIER_A_SLOTS = {
        "payout_limit",
        "waiting_period",
        "reduction",
        "exclusions"
    }

    @classmethod
    def assign_confidence(
        cls,
        slot_key: str,
        slot_status: str,
        evidences: List[Dict]
    ) -> Optional[Dict[str, str]]:
        """
        Assign confidence level to slot value.

        Args:
            slot_key: Slot name
            slot_status: Slot status (FOUND, UNKNOWN, etc.)
            evidences: List of evidence dicts with doc_type field

        Returns:
            {
                "level": "HIGH" | "MEDIUM",
                "basis": "가입설계서" | "약관" | "상품요약서" | "사업방법서"
            }
            or None if no confidence should be assigned
        """
        # Rule 1: Only Tier-A slots
        if slot_key not in cls.TIER_A_SLOTS:
            return None

        # Rule 2: Only FOUND/FOUND_GLOBAL status
        if slot_status not in ["FOUND", "FOUND_GLOBAL"]:
            return None

        # Rule 3: Must have evidences
        if not evidences:
            return None

        # Rule 4: Get highest confidence from evidences
        confidence_levels = []
        basis_docs = []

        for evidence in evidences:
            doc_type = evidence.get("doc_type", "")
            if doc_type in cls.DOC_TYPE_CONFIDENCE:
                confidence_levels.append(cls.DOC_TYPE_CONFIDENCE[doc_type])
                basis_docs.append(doc_type)

        # No recognized document types
        if not confidence_levels:
            return None

        # Take highest confidence (HIGH > MEDIUM)
        if "HIGH" in confidence_levels:
            level = "HIGH"
            # Get first HIGH doc type
            basis = next(doc for doc, conf in zip(basis_docs, confidence_levels) if conf == "HIGH")
        else:
            level = "MEDIUM"
            basis = basis_docs[0]

        return {
            "level": level,
            "basis": basis
        }

    @classmethod
    def get_confidence_display(cls, confidence: Optional[Dict]) -> str:
        """
        Get customer-facing confidence display text.

        Args:
            confidence: Confidence dict with level/basis

        Returns:
            Display string (e.g., "신뢰도: 높음")
        """
        if not confidence:
            return ""

        level = confidence.get("level")
        if level == "HIGH":
            return "신뢰도: 높음"
        elif level == "MEDIUM":
            return "신뢰도: 보통"
        else:
            return ""


# ============================================================================
# STEP NEXT-R/V: G10 Premium SSOT Gate + Runtime Injection
# ============================================================================

class PremiumSSOTGate:
    """
    G10: Premium SSOT Gate

    HARD RULES (ZERO TOLERANCE):
    1. Premium values ONLY from product_premium_quote_v2 table
    2. NO LLM estimation/interpolation/averaging
    3. Q12 output FAILS if premium_monthly is missing for ANY insurer
    4. Premium output MUST include conditions + as_of_date + baseDt

    Reference: docs/PREMIUM_OUTPUT_POLICY.md
    """

    def __init__(self, db_conn=None):
        """
        Initialize gate with database connection.

        Args:
            db_conn: Database connection (psycopg2 connection or similar)
                     If None, gate will operate in validation-only mode
        """
        self.db_conn = db_conn

    def fetch_premium(
        self,
        insurer_key: str,
        product_id: str,
        age: int,
        sex: str,
        plan_variant: str,
        smoke: str = "NA",
        pay_term_years: int = None,
        ins_term_years: int = None
    ) -> Dict[str, Any]:
        """
        Fetch premium from SSOT table.

        Args:
            insurer_key: Insurer key (kb, samsung, etc.)
            product_id: Product ID (product_key format)
            age: Age (30, 40, 50)
            sex: Sex (M, F, UNISEX)
            plan_variant: GENERAL | NO_REFUND
            smoke: Y | N | NA
            pay_term_years: Payment term (optional filter)
            ins_term_years: Insurance term (optional filter)

        Returns:
            {
                "valid": bool,
                "premium_monthly": int | None,
                "premium_total": int | None,
                "source": {
                    "table": "product_premium_quote_v2",
                    "as_of_date": str,
                    "baseDt": str | None,
                    "api_calSubSeq": str | None
                },
                "conditions": {
                    "age": int,
                    "sex": str,
                    "smoke": str,
                    "plan_variant": str,
                    "pay_term_years": int | None,
                    "ins_term_years": int | None
                },
                "reason": str | None
            }
        """
        if not self.db_conn:
            return {
                "valid": False,
                "premium_monthly": None,
                "premium_total": None,
                "source": None,
                "conditions": None,
                "reason": "No database connection (validation-only mode)"
            }

        # Build query (DB-ONLY: product_premium_quote_v2)
        # premium_quote is DEPRECATED - use product_premium_quote_v2
        query = """
            SELECT
                premium_monthly_total as premium_monthly,
                premium_total_total as premium_total,
                as_of_date,
                source_table_id,
                source_row_id,
                pay_term_years,
                ins_term_years
            FROM product_premium_quote_v2
            WHERE insurer_key = %s
              AND product_id = %s
              AND age = %s
              AND sex = %s
              AND plan_variant = %s
              AND smoke = %s
        """

        params = [insurer_key, product_id, age, sex, plan_variant, smoke]

        # Optional filters
        if pay_term_years is not None:
            query += " AND pay_term_years = %s"
            params.append(pay_term_years)

        if ins_term_years is not None:
            query += " AND ins_term_years = %s"
            params.append(ins_term_years)

        # Execute query
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            # HARD RULE: Must have EXACTLY 1 row
            if len(rows) == 0:
                return {
                    "valid": False,
                    "premium_monthly": None,
                    "premium_total": None,
                    "source": None,
                    "conditions": {
                        "age": age,
                        "sex": sex,
                        "smoke": smoke,
                        "plan_variant": plan_variant,
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years
                    },
                    "reason": f"No premium data for {insurer_key}/{product_id}"
                }

            if len(rows) > 1:
                return {
                    "valid": False,
                    "premium_monthly": None,
                    "premium_total": None,
                    "source": None,
                    "conditions": {
                        "age": age,
                        "sex": sex,
                        "smoke": smoke,
                        "plan_variant": plan_variant,
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years
                    },
                    "reason": f"Multiple premium rows ({len(rows)}) for {insurer_key}/{product_id}"
                }

            # Extract data
            row = rows[0]
            premium_monthly = row[0]
            premium_total = row[1]
            as_of_date = row[2]
            source_table_id = row[3]
            source_row_id = row[4]
            actual_pay_term = row[5]
            actual_ins_term = row[6]

            # HARD RULE: premium_monthly must not be null
            if premium_monthly is None or premium_monthly <= 0:
                return {
                    "valid": False,
                    "premium_monthly": None,
                    "premium_total": None,
                    "source": None,
                    "conditions": {
                        "age": age,
                        "sex": sex,
                        "smoke": smoke,
                        "plan_variant": plan_variant,
                        "pay_term_years": pay_term_years,
                        "ins_term_years": ins_term_years
                    },
                    "reason": f"Invalid premium_monthly: {premium_monthly}"
                }

            # Build source reference
            source = {
                "table": "product_premium_quote_v2",
                "as_of_date": str(as_of_date) if as_of_date else None,
                "baseDt": source_table_id if source_table_id else None,
                "api_calSubSeq": source_row_id if source_row_id else None
            }

            # Build conditions
            conditions = {
                "age": age,
                "sex": sex,
                "smoke": smoke,
                "plan_variant": plan_variant,
                "pay_term_years": actual_pay_term,
                "ins_term_years": actual_ins_term
            }

            return {
                "valid": True,
                "premium_monthly": premium_monthly,
                "premium_total": premium_total,
                "source": source,
                "conditions": conditions,
                "reason": None
            }

        except Exception as e:
            return {
                "valid": False,
                "premium_monthly": None,
                "premium_total": None,
                "source": None,
                "conditions": None,
                "reason": f"Database error: {str(e)}"
            }

    def validate_q12_premium_requirement(
        self,
        insurer_premium_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that ALL insurers in Q12 have premium data.

        Q12 HARD RULE: If ANY insurer is missing premium, Q12 output FAILS.

        Args:
            insurer_premium_results: List of premium fetch results (one per insurer)

        Returns:
            {
                "valid": bool,
                "missing_insurers": List[str],
                "reason": str | None
            }
        """
        missing = []

        for result in insurer_premium_results:
            if not result.get("valid", False):
                insurer_key = result.get("conditions", {}).get("insurer_key", "unknown")
                missing.append(insurer_key)

        if missing:
            return {
                "valid": False,
                "missing_insurers": missing,
                "reason": f"Premium SSOT missing for {len(missing)} insurer(s): {', '.join(missing)}"
            }

        return {
            "valid": True,
            "missing_insurers": [],
            "reason": None
        }


# ============================================================================
# STEP NEXT-V: Runtime Premium Injection (G10 enforcement)
# ============================================================================

def inject_premium_for_q12_runtime(
    compare_rows: List[Dict[str, Any]],
    base_dt: str,
    age: int,
    sex: str,
    plan_variant: str = "NO_REFUND"
) -> Dict[str, Any]:
    """
    Runtime Premium Injection for Q12 with G10 gate enforcement

    STEP NEXT-V: Connects PremiumInjector to Q12 comparison flow

    Args:
        compare_rows: List of CompareRow dicts
        base_dt: YYYYMMDD
        age: 30 | 40 | 50
        sex: "M" | "F"
        plan_variant: "NO_REFUND" | "GENERAL"

    Returns:
        Dict with:
            - compare_rows: List[Dict] with premium_monthly injected
            - status: "SUCCESS" | "FAIL"
            - missing_insurers: List[str] (if G10 violation)
            - errors: List[str]

    Raises:
        GateViolationError: If G10 gate fails (ANY insurer missing premium)
    """
    from pipeline.step4_compare_model.premium_injector import PremiumInjector

    injector = PremiumInjector()

    result = injector.inject_premium_for_q12(
        compare_rows=compare_rows,
        base_dt=base_dt,
        age=age,
        sex=sex,
        plan_variant=plan_variant
    )

    # G10 GATE: If status FAIL, raise exception
    if result["status"] == "FAIL":
        error_msg = "\n".join(result["errors"])
        raise GateViolationError(
            f"G10 Premium SSOT Gate FAIL:\n{error_msg}"
        )

    return result


class GateViolationError(Exception):
    """Exception raised when a gate validation fails"""
    pass


# ============================================================================
# STEP NEXT-DB1: G11 Premium Schema Gate (DB Reality Lock)
# ============================================================================

class PremiumSchemaGate:
    """
    G11: Premium Schema Gate (ZERO TOLERANCE)

    HARD RULES (STEP NEXT-DB1):
    1. Premium SSOT tables MUST exist in DB before pipeline runs
    2. NO mock/fallback to file-based premium data
    3. FAIL FAST if tables missing (exit 2)
    4. Log DB connection evidence on every check

    Required Tables:
    - premium_quote
    - coverage_premium_quote
    - product_premium_quote_v2
    - q14_premium_ranking_v1

    Reference: docs/audit/STEP_NEXT_DB1_PREMIUM_DB_REALITY_LOCK.md
    """

    REQUIRED_TABLES = [
        "premium_quote",
        "coverage_premium_quote",
        "product_premium_quote_v2",
        "q14_premium_ranking_v1"
    ]

    def __init__(self, db_conn=None):
        """
        Initialize gate with database connection.

        Args:
            db_conn: Database connection (psycopg2 connection)
        """
        self.db_conn = db_conn

    def validate(self) -> Dict[str, Any]:
        """
        Validate that all required premium tables exist in DB.

        Returns:
            {
                "valid": bool,
                "missing_tables": List[str],
                "db_info": {
                    "database": str,
                    "host": str,
                    "port": int
                },
                "reason": str | None
            }

        Raises:
            GateViolationError: If validation fails (missing tables)
        """
        if not self.db_conn:
            raise GateViolationError(
                "G11 Premium Schema Gate FAIL: No database connection"
            )

        try:
            cursor = self.db_conn.cursor()

            # Get DB connection info for audit
            cursor.execute("""
                SELECT
                    current_database() as database,
                    inet_server_addr() as host,
                    inet_server_port() as port,
                    version() as pg_version
            """)
            db_info_row = cursor.fetchone()
            db_info = {
                "database": db_info_row[0],
                "host": str(db_info_row[1]) if db_info_row[1] else "localhost",
                "port": db_info_row[2],
                "pg_version": db_info_row[3].split(",")[0] if db_info_row[3] else "unknown"
            }

            # Check each required table
            missing_tables = []
            for table_name in self.REQUIRED_TABLES:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                """, (table_name,))
                exists = cursor.fetchone()[0]

                if not exists:
                    missing_tables.append(table_name)

            cursor.close()

            # HARD RULE: ALL tables must exist
            if missing_tables:
                error_msg = f"""
G11 Premium Schema Gate FAIL (STEP NEXT-DB1):

DATABASE: {db_info['database']} @ {db_info['host']}:{db_info['port']}
MISSING TABLES: {', '.join(missing_tables)}

REQUIRED TABLES:
{chr(10).join(f'  - {t}' for t in self.REQUIRED_TABLES)}

ACTION REQUIRED:
Apply schema migrations:
  psql $DATABASE_URL -f schema/020_premium_quote.sql
  psql $DATABASE_URL -f schema/040_coverage_premium_quote.sql
  psql $DATABASE_URL -f schema/050_q14_premium_ranking.sql
  psql $DATABASE_URL -f schema/030_product_comparison_v1.sql

POLICY: Premium SSOT is DB-ONLY. NO mock/fallback allowed.
                """.strip()

                raise GateViolationError(error_msg)

            # SUCCESS: All tables exist
            return {
                "valid": True,
                "missing_tables": [],
                "db_info": db_info,
                "reason": None
            }

        except GateViolationError:
            raise
        except Exception as e:
            raise GateViolationError(
                f"G11 Premium Schema Gate ERROR: {str(e)}"
            )
