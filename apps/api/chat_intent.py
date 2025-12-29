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
    3. FAQ template takes precedence
    4. Unknown intent → ask for clarification
    """

    # Keyword patterns for each intent
    PATTERNS: Dict[MessageKind, List[str]] = {
        "EX2_DETAIL": [
            r"상세",
            r"보장.*비교",
            r"면책",
            r"감액",
            r"보장한도",
            r"보장기간",
            r"담보.*설명"
        ],
        "EX3_INTEGRATED": [
            r"통합.*비교",
            r"여러.*담보",
            r"전체.*비교",
            r"공통사항",
            r"유의사항"
        ],
        "EX4_ELIGIBILITY": [
            r"보장.*가능",
            r"보장.*여부",
            r"질병.*하위",
            r"경계.*조건",
            r"적용.*여부"
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

        Priority:
        1. FAQ template (if provided) → 100% confidence
        2. Keyword pattern matching → 0-100% confidence
        3. Unknown → 0% confidence

        Returns:
            (MessageKind, confidence_score)
        """
        # Priority 1: FAQ template
        if request.faq_template_id:
            template = FAQTemplateRegistry.get_template(request.faq_template_id)
            if template:
                return (template.example_kind, 1.0)

        # Priority 2: Pattern matching
        message_lower = request.message.lower()
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
        return ("EX2_DETAIL", 0.0)  # Default fallback

    @staticmethod
    def route(request: ChatRequest) -> MessageKind:
        """
        Route request to MessageKind

        PRIORITY (Production Hardening):
        1. Explicit `kind` from request → 100% deterministic (NO router)
        2. FAQ template → high confidence
        3. Keyword patterns → fallback (lower accuracy)

        Returns:
            MessageKind for handler dispatch
        """
        # Priority 1: Explicit kind (production flow)
        if request.kind is not None:
            return request.kind

        # Priority 2-3: Detect from FAQ/keywords
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
        "EX2_DETAIL": ["coverage_names", "insurers"],
        "EX3_INTEGRATED": ["coverage_names", "insurers"],
        "EX4_ELIGIBILITY": ["disease_name", "insurers"],
        "EX1_PREMIUM_DISABLED": []  # No slots required (immediate disabled response)
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
    def compile_coverage_names(raw_names: List[str]) -> List[str]:
        """
        Normalize coverage names to canonical form

        NOTE: This should use mapping table in production
        For now, pass-through (assume frontend sends canonical names)
        """
        return raw_names  # TODO: Add mapping table lookup

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
        if kind in ["EX2_DETAIL", "EX3_INTEGRATED"]:
            query["coverage_names"] = QueryCompiler.compile_coverage_names(
                request.coverage_names or []
            )
            query["insurers"] = QueryCompiler.compile_insurer_codes(
                request.insurers or []
            )

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

        # Step 4: Dispatch to handler (imported at runtime to avoid circular deps)
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
