#!/usr/bin/env python3
"""
Chat Intent Router for deterministic query classification
STEP NEXT-14: Chat UI Integration

DESIGN PRINCIPLES:
1. Deterministic rule-based routing (NO LLM classification)
2. Intent → MessageKind mapping is 1:1
3. Required slots validated before execution
4. NO premium estimation/calculation (EX1_DISABLED only)

INTENT FLOW:
1. Input: ChatRequest (message + optional FAQ template)
2. Intent Router: Classify → MessageKind
3. Slot Validator: Check required fields
4. Compiler: Build deterministic query
5. Handler: Execute + Build VM
"""

from typing import Optional, List, Dict, Any, Tuple
from apps.api.chat_vm import (
    ChatRequest,
    ChatResponse,
    MessageKind,
    FAQTemplateRegistry
)
import re


# ============================================================================
# Intent Detection (Rule-Based)
# ============================================================================

class IntentRouter:
    """
    Deterministic intent router

    CRITICAL RULES:
    1. NO LLM-based classification
    2. Rule-based pattern matching
    3. Category takes precedence over keywords
    4. FAQ template supported
    5. Unknown intent → ask for clarification
    """

    # STEP NEXT-UI-01: Category → Example mapping
    CATEGORY_MAPPING: Dict[str, MessageKind] = {
        "단순보험료 비교": "EX1_PREMIUM_DISABLED",
        "② 상품/담보 설명": "EX2_DETAIL_DIFF",
        "상품 비교": "EX3_INTEGRATED",  # Default for category
        "보험 상식": "KNOWLEDGE_BASE"  # Future RAG
    }

    # STEP NEXT-78: Disease subtypes for EX4 detection
    DISEASE_SUBTYPES = [
        "제자리암", "경계성종양", "유사암",
        "갑상선암", "기타피부암", "대장점막내암",
        "전립선암", "방광암"
    ]

    # Keyword patterns for each intent
    PATTERNS: Dict[MessageKind, List[str]] = {
        "EX2_LIMIT_FIND": [  # STEP NEXT-78: Renamed from EX2_DETAIL_DIFF
            r"보장한도.*다른",
            r"한도.*다른",
            r"한도.*차이",
            r"보장한도.*비교",
            r"조건.*다른",
            r"조건.*차이",
            r"면책.*다른",
            r"감액.*다른",
            r"지급유형.*다른"
        ],
        "EX2_DETAIL_DIFF": [  # LEGACY (backward compat)
            r"다른.*상품",
            r"다른.*찾",
            r"차이",
            r"상세",
            r"담보.*설명"
        ],
        "EX3_INTEGRATED": [
            r"통합.*비교",
            r"여러.*담보",
            r"전체.*비교",
            r"공통사항",
            r"유의사항"
        ],
        "EX4_ELIGIBILITY": [  # STEP NEXT-78: Strengthened with disease subtypes
            r"보장.*가능",
            r"보장.*여부",
            r"질병.*하위",
            r"경계.*조건",
            r"적용.*여부",
            r"제자리암",
            r"경계성종양",
            r"유사암",
            r"갑상선암",
            r"기타피부암"
        ],
        "EX1_PREMIUM_DISABLED": [
            r"보험료",
            r"납입",
            r"가격",
            r"비용",
            r"금액.*비교",
            r"정렬"
        ]
    }

    @staticmethod
    def detect_intent(request: ChatRequest) -> Tuple[MessageKind, float]:
        """
        Detect intent from ChatRequest

        Priority (STEP NEXT-80 LOCKED):
        1. Category (selectedCategory) → 100% confidence
        2. FAQ template (if provided) → 100% confidence
        3. Anti-confusion gates (EX2 vs EX4) → 100% confidence
        4. Keyword pattern matching → 0-100% confidence
        5. Unknown → 0% confidence

        NOTE: This method is ONLY called when request.kind is NOT provided.
        Explicit kind (request.kind) is handled in route() with ABSOLUTE priority.

        Returns:
            (MessageKind, confidence_score)
        """
        # Priority 1: Category-based routing
        if hasattr(request, 'selected_category') and request.selected_category:
            kind = IntentRouter.CATEGORY_MAPPING.get(request.selected_category)
            if kind:
                return (kind, 1.0)

        # Priority 2: FAQ template
        if request.faq_template_id:
            template = FAQTemplateRegistry.get_template(request.faq_template_id)
            if template:
                return (template.example_kind, 1.0)

        message_lower = request.message.lower()

        # STEP NEXT-78: Priority 3 - Anti-confusion gates
        # Gate 1: Disease subtype detection → EX4_ELIGIBILITY
        for subtype in IntentRouter.DISEASE_SUBTYPES:
            if subtype in message_lower:
                return ("EX4_ELIGIBILITY", 1.0)

        # Gate 2: Limit/condition comparison → EX2_LIMIT_FIND
        limit_patterns = [r"보장한도.*다른", r"한도.*다른", r"한도.*차이", r"조건.*다른", r"면책.*다른", r"감액.*다른"]
        for pattern in limit_patterns:
            if re.search(pattern, message_lower):
                return ("EX2_LIMIT_FIND", 1.0)

        # Priority 4: Pattern matching (fallback)
        scores: Dict[MessageKind, float] = {}

        for kind, patterns in IntentRouter.PATTERNS.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    match_count += 1

            # Score = matched / total patterns
            scores[kind] = match_count / len(patterns) if patterns else 0.0

        # Return highest scoring intent (if > 0.3 threshold)
        if scores:
            best_kind = max(scores, key=scores.get)
            best_score = scores[best_kind]

            if best_score >= 0.3:
                return (best_kind, best_score)

        # Unknown intent
        return ("EX2_LIMIT_FIND", 0.0)  # Default fallback (STEP NEXT-78: changed from EX2_DETAIL_DIFF)

    @staticmethod
    def route(request: ChatRequest) -> MessageKind:
        """
        Route request to MessageKind

        PRIORITY (STEP NEXT-80 LOCKED):
        1. Explicit `kind` from request → 100% priority (ABSOLUTE, NO OVERRIDE)
        2. detect_intent() → category/FAQ/gates/patterns (ONLY if kind is None)

        CRITICAL RULE:
        - If request.kind is provided, NEVER call detect_intent()
        - If request.kind is provided, NEVER apply anti-confusion gates
        - Explicit kind = UI contract guarantee (e.g., Example 3 button)

        Returns:
            MessageKind for handler dispatch
        """
        # STEP NEXT-80: Priority 1 - Explicit kind (ABSOLUTE, NO OVERRIDE)
        if request.kind is not None:
            return request.kind

        # Priority 2-5: Detect from category/FAQ/gates/patterns (ONLY if kind is None)
        kind, confidence = IntentRouter.detect_intent(request)
        return kind


# ============================================================================
# Slot Validator
# ============================================================================

class SlotValidator:
    """
    Validate required slots for each MessageKind

    RULES:
    1. Each MessageKind has required slots
    2. Missing slots → need_more_info response
    3. Max 2 clarification questions
    4. Selection UI options provided (when possible)
    """

    # Required slots per MessageKind
    REQUIRED_SLOTS: Dict[MessageKind, List[str]] = {
        "EX2_DETAIL_DIFF": ["coverage_names", "insurers", "compare_field"],  # LEGACY
        "EX2_LIMIT_FIND": ["coverage_names", "insurers", "compare_field"],  # STEP NEXT-78
        "EX3_INTEGRATED": ["coverage_names", "insurers"],
        "EX3_COMPARE": ["coverage_names", "insurers"],  # STEP NEXT-77
        "EX4_ELIGIBILITY": ["disease_name", "insurers"],
        "EX1_PREMIUM_DISABLED": [],  # No slots required (immediate disabled response)
        "PREMIUM_COMPARE": []
    }

    @staticmethod
    def validate(request: ChatRequest, kind: MessageKind) -> Tuple[bool, List[str]]:
        """
        Validate required slots

        Returns:
            (is_valid, missing_slots)
        """
        required = SlotValidator.REQUIRED_SLOTS.get(kind, [])
        missing: List[str] = []

        for slot in required:
            value = getattr(request, slot, None)

            # Special handling for compare_field: default to "보장한도"
            if slot == "compare_field" and (value is None or value == ""):
                request.compare_field = "보장한도"
                continue

            if value is None or (isinstance(value, list) and len(value) == 0):
                missing.append(slot)

        return (len(missing) == 0, missing)

    @staticmethod
    def get_clarification_options(
        missing_slots: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Get selection options for missing slots

        Returns:
            Dict[slot_name, options_list]
        """
        # Default options (could be loaded from DB/config)
        DEFAULT_OPTIONS = {
            "coverage_names": [
                "암진단비",
                "뇌출혈진단비",
                "급성심근경색진단비",
                "상해사망",
                "질병사망"
            ],
            "insurers": [
                "삼성화재",
                "메리츠화재",
                "DB손해보험",
                "KB손해보험",
                "한화손해보험",
                "현대해상",
                "롯데손해보험",
                "흥국화재"
            ],
            "disease_name": [
                "암",
                "뇌출혈",
                "급성심근경색",
                "뇌졸중",
                "허혈성심장질환"
            ]
        }

        options = {}
        for slot in missing_slots:
            if slot in DEFAULT_OPTIONS:
                options[slot] = DEFAULT_OPTIONS[slot]

        return options


# ============================================================================
# Compiler (Deterministic Query Builder)
# ============================================================================

class QueryCompiler:
    """
    Compile ChatRequest → deterministic query

    CRITICAL RULES:
    1. NO LLM generation
    2. Rule-based transformation
    3. Canonical name mapping
    4. Insurer code normalization
    5. Log compiled query for reproducibility
    """

    @staticmethod
    def extract_compare_field(message: str) -> str:
        """
        Extract compare field from query text (STEP NEXT-COMPARE-FILTER)

        Returns:
            Field name for comparison (보장한도, 지급유형, etc.)
        """
        field_patterns = {
            "보장한도": [r"보장한도", r"한도", r"입원한도", r"보장기간"],
            "지급유형": [r"지급유형", r"지급방식", r"지급조건", r"지급형태"],
            "보장금액": [r"보장금액", r"가입금액", r"금액"],
            "조건": [r"조건", r"면책", r"감액"]
        }

        message_lower = message.lower()
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return field

        return "보장한도"  # Default

    # Coverage name → code mapping (STEP NEXT-80: Fixed to actual coverage codes)
    COVERAGE_NAME_TO_CODE = {
        "암진단비(유사암제외)": "A4200_1",
        "암진단비": "A4200_1",  # STEP NEXT-80: Fixed A4100_1 → A4200_1 (actual code in slim cards)
        "뇌출혈진단비": "A4300_1",
        "급성심근경색진단비": "A4400_1",
        "상해사망": "A1100_1",
        "질병사망": "A1200_1",
    }

    @staticmethod
    def compile_coverage_names(raw_names: List[str]) -> List[str]:
        """
        Normalize coverage names to canonical form

        NOTE: This should use mapping table in production
        For now, pass-through (assume frontend sends canonical names)
        """
        return raw_names  # TODO: Add mapping table lookup

    @staticmethod
    def map_coverage_name_to_code(coverage_name: str) -> str:
        """
        Map coverage name to code (STEP NEXT-80: Quick fix for EX3_COMPARE)

        Args:
            coverage_name: Human-readable name (e.g., "암진단비(유사암제외)")

        Returns:
            Coverage code (e.g., "A4200_1")
        """
        return QueryCompiler.COVERAGE_NAME_TO_CODE.get(coverage_name, coverage_name)

    @staticmethod
    def compile_insurer_codes(raw_insurers: List[str]) -> List[str]:
        """
        Normalize insurer names to internal codes

        Mapping:
        - 삼성화재 → samsung
        - 메리츠화재 → meritz
        - DB손해보험 → db
        - etc.
        """
        INSURER_MAPPING = {
            "삼성화재": "samsung",
            "메리츠화재": "meritz",
            "DB손해보험": "db",
            "KB손해보험": "kb",
            "한화손해보험": "hanwha",
            "현대해상": "hyundai",
            "롯데손해보험": "lotte",
            "흥국화재": "heungkuk"
        }

        codes = []
        for raw in raw_insurers:
            code = INSURER_MAPPING.get(raw)
            if code:
                codes.append(code)
            else:
                # Pass-through if already code format
                codes.append(raw.lower())

        return codes

    @staticmethod
    def compile(request: ChatRequest, kind: MessageKind) -> Dict[str, Any]:
        """
        Compile ChatRequest to deterministic query

        Returns:
            Compiled query dict (logged for reproducibility)
        """
        query = {
            "request_id": str(request.request_id),
            "kind": kind,
            "compiled_at": str(request.request_id),  # Use request timestamp
        }

        # Compile slots based on kind
        if kind in ["EX2_DETAIL_DIFF", "EX2_LIMIT_FIND", "EX3_INTEGRATED", "EX3_COMPARE"]:
            query["coverage_names"] = QueryCompiler.compile_coverage_names(
                request.coverage_names or []
            )
            query["insurers"] = QueryCompiler.compile_insurer_codes(
                request.insurers or []
            )
            if kind in ["EX2_DETAIL_DIFF", "EX2_LIMIT_FIND"]:
                # Auto-detect compare_field from message if not provided
                if not request.compare_field:
                    query["compare_field"] = QueryCompiler.extract_compare_field(request.message)
                else:
                    query["compare_field"] = request.compare_field
            # Add coverage_code for EX3_COMPARE
            if kind == "EX3_COMPARE":
                # Map coverage name to code (STEP NEXT-80)
                if query["coverage_names"]:
                    coverage_name = query["coverage_names"][0]
                    query["coverage_code"] = QueryCompiler.map_coverage_name_to_code(coverage_name)

        elif kind == "EX4_ELIGIBILITY":
            query["disease_name"] = request.disease_name
            query["insurers"] = QueryCompiler.compile_insurer_codes(
                request.insurers or []
            )

        elif kind == "EX1_PREMIUM_DISABLED":
            # No compilation needed (immediate disabled response)
            pass

        return query


# ============================================================================
# Intent Handler Dispatcher
# ============================================================================

class IntentDispatcher:
    """
    Dispatch intent to appropriate handler

    FLOW:
    1. Route → MessageKind
    2. Validate → check slots
    3. Compile → deterministic query
    4. Dispatch → handler execution
    """

    @staticmethod
    def dispatch(request: ChatRequest) -> ChatResponse:
        """
        Main dispatch entrypoint

        Returns:
            ChatResponse (either need_more_info or full VM)
        """
        # Step 1: Route intent
        kind = IntentRouter.route(request)

        # Step 2: Validate slots
        is_valid, missing_slots = SlotValidator.validate(request, kind)

        if not is_valid:
            # Return need_more_info response
            options = SlotValidator.get_clarification_options(missing_slots)
            return ChatResponse(
                request_id=request.request_id,
                need_more_info=True,
                missing_slots=missing_slots,
                clarification_options=options,
                message=None
            )

        # Step 3: Compile query
        compiled_query = QueryCompiler.compile(request, kind)

        # Step 4: Dispatch to handler
        # STEP NEXT-UI-01: Use deterministic handlers by default (LLM OFF)
        if request.llm_mode == "OFF":
            from apps.api.chat_handlers_deterministic import HandlerRegistryDeterministic
            handler = HandlerRegistryDeterministic.get_handler(kind)
        else:
            # LLM ON mode (optional, for text refinement only)
            from apps.api.chat_handlers import HandlerRegistry
            handler = HandlerRegistry.get_handler(kind)

        if handler is None:
            raise ValueError(f"No handler for kind: {kind}")

        # Execute handler
        message_vm = handler.execute(compiled_query, request)

        # Return full response
        return ChatResponse(
            request_id=request.request_id,
            need_more_info=False,
            missing_slots=None,
            clarification_options=None,
            message=message_vm
        )
